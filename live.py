"""Bounded hosted open-model requests. No automatic retries or answer leakage."""
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import time

from history import messages, score


@dataclass(frozen=True)
class LiveConfig:
    provider: str
    model: str
    key: str
    base_url: str
    daily_requests: int = 30
    daily_usd: float = 1.0
    input_usd_per_million: float = 10.0
    output_usd_per_million: float = 10.0
    max_output_tokens: int = 2048


def configuration(get=None):
    get = get or os.environ.get
    if get('LIVE_ENABLED', '0') != '1':
        return None
    provider = get('LIVE_PROVIDER', 'huggingface')
    defaults = {
        'huggingface': ('HF_TOKEN', 'https://router.huggingface.co/v1', 'Qwen/Qwen3-8B:nscale'),
        'openrouter': ('OPENROUTER_API_KEY', 'https://openrouter.ai/api/v1', 'qwen/qwen3-8b'),
    }
    if provider not in defaults:
        return None
    variable, endpoint, model = defaults[provider]
    key = get(variable)
    if not key:
        return None
    try:
        config = LiveConfig(provider, get('LIVE_MODEL', model), key, endpoint,
                            int(get('LIVE_DAILY_REQUESTS', '30')),
                            float(get('LIVE_DAILY_USD', '1')),
                            float(get('LIVE_INPUT_USD_PER_MILLION', '10')),
                            float(get('LIVE_OUTPUT_USD_PER_MILLION', '10')),
                            int(get('LIVE_MAX_OUTPUT_TOKENS', '2048')))
        if not 1 <= config.max_output_tokens <= 4096 or config.daily_requests < 1 or any(not math.isfinite(v) or v <= 0 for v in
                (config.daily_usd, config.input_usd_per_million, config.output_usd_per_million)):
            return None
        return config
    except (ValueError, TypeError):
        return None


class LimitReached(Exception):
    pass


def reserve(config, prompt, ledger):
    # UTF-8 bytes + framing allowance is a conservative token estimate for this prompt.
    input_bound = sum(len(m['content'].encode('utf-8')) for m in prompt) + 512
    if input_bound > 24000:
        raise LimitReached('This question exceeds the live prompt limit.')
    ceiling = (input_bound * config.input_usd_per_million +
               config.max_output_tokens * config.output_usd_per_million) / 1_000_000
    ledger.parent.mkdir(parents=True, exist_ok=True)
    # Lock the ledger itself; never replace its inode while holding the lock.
    with ledger.open('a+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        text = handle.read()
        current = json.loads(text) if text else {}
        day = datetime.now(timezone.utc).date().isoformat()
        if current.get('day') != day:
            current = {'day': day, 'requests': 0, 'reserved_usd': 0}
        if current['requests'] >= config.daily_requests or current['reserved_usd'] + ceiling > config.daily_usd:
            raise LimitReached('The shared live allowance has been reached. Recorded or solo mode is still available.')
        current['requests'] += 1
        current['reserved_usd'] += ceiling
        handle.seek(0)
        handle.truncate()
        json.dump(current, handle)
        handle.flush()
        os.fsync(handle.fileno())


def request_once(config, question, ledger, client_factory=None):
    prompt = messages(question)
    try:
        reserve(config, prompt, ledger)
    except LimitReached as error:
        return {'status': 'error', 'reason': str(error), 'answer': '', 'correct': False}
    except (OSError, ValueError, KeyError, TypeError):
        return {'status': 'error', 'reason': 'The live allowance could not be checked. No request was sent.', 'answer': '', 'correct': False}
    if client_factory is None:
        from openai import OpenAI
        client_factory = OpenAI
    start = time.monotonic()
    try:
        with client_factory(api_key=config.key, base_url=config.base_url, timeout=35, max_retries=0) as client:
            response = client.chat.completions.create(model=config.model, messages=prompt,
                                                     max_tokens=config.max_output_tokens)
        choice = response.choices[0]
        raw = choice.message.content or ''
        return {**score(raw, question['answer']), 'raw': raw, 'messages': prompt,
                'response_model': response.model, 'requested_model': config.model,
                'provider': config.provider, 'latency_seconds': round(time.monotonic() - start, 2),
                'max_output_tokens': config.max_output_tokens,
                'response_id': response.id,
                'recorded_at': datetime.now(timezone.utc).isoformat(),
                'finish_reason': choice.finish_reason,
                'usage': response.usage.model_dump() if response.usage else None}
    except Exception:
        # Do not disclose provider exception bodies, which may contain credentials or request details.
        return {'status': 'error', 'reason': 'The model service did not return an answer. This is an API failure, not an incorrect benchmark answer.',
                'answer': '', 'correct': False}


def ensure_answer(state, question, config, ledger, requester=request_once):
    """Lock human answer first; retain first response/error across reruns."""
    item_id = question['id']
    if item_id not in state['answers']:
        raise ValueError('A visitor answer must be locked before the model request')
    if item_id not in state['model_answers']:
        # Mark in progress before network I/O: interruption must not trigger a repeated charge.
        state['model_answers'][item_id] = {'status': 'error', 'reason': 'The request was interrupted. It will not be repeated automatically.', 'answer': '', 'correct': False}
        state['model_answers'][item_id] = requester(config, question, ledger)
    return state['model_answers'][item_id]
