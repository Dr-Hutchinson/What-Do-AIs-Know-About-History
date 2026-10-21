"""Bounded parallel execution of the existing five-shot assessment protocol."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from evaluate import config_for, now, save
from history import SUBJECTS, messages, questions, score, summaries


def run_parallel(config, directory, request, workers=3, ceiling_usd=2,
                 input_price=10, output_price=10):
    """Save every received response; after an error drain only in-flight work."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'run.json'
    run = json.loads(path.read_text()) if path.exists() else {
        'config': config, 'created_at': now(), 'status': 'incomplete', 'records': []}
    if run['config'] != config:
        raise ValueError('Run configuration changed. Use a new output directory.')
    selected = [q for s in SUBJECTS for q in questions(s)[:config['limit_per_subject']]]
    by_id = {q['id']: q for q in selected}
    records = {r['id']: r for r in run['records']}
    if len(records) != len(run['records']) or not set(records) <= set(by_id):
        raise ValueError('Checkpoint has duplicate or unknown question IDs')
    for item_id, old in records.items():
        q = by_id[item_id]
        if old['messages'] != messages(q) or old['expected'] != q['answer']:
            raise ValueError('Checkpoint prompt or answer key changed')
        if old['status'] != 'error' and any(old[k] != v for k, v in score(old['raw'], q['answer']).items()):
            raise ValueError('Checkpoint score is inconsistent')
    pending = [q for q in selected if q['id'] not in records or records[q['id']]['status'] == 'error']
    # Reserve the whole remaining run before sending anything. Each prompt byte is
    # treated as one token and the full output cap is charged at observed prices.
    reservation = 3 * sum((sum(len(m['content'].encode()) for m in messages(q)) + 512) * input_price
                          + config['max_completion_tokens'] * output_price for q in pending) / 1_000_000
    if reservation > ceiling_usd:
        raise ValueError(f'Remaining reservation ${reservation:.4f} exceeds ceiling ${ceiling_usd:.2f}')
    execution = {'started_at': now(), 'workers': workers, 'input_usd_per_million': input_price,
                 'output_usd_per_million': output_price, 'reservation_usd': reservation,
                 'ceiling_usd': ceiling_usd, 'reserved_attempts_per_item': 3,
                 'executor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    run.setdefault('executions', []).append(execution)
    run['status'] = 'incomplete'
    save(run, directory)

    def receive(q):
        record = {'id': q['id'], 'subject': q['subject'], 'question': q['question'],
                  'options': q['options'], 'expected': q['answer'], 'messages': messages(q),
                  'recorded_at': now(), 'attempts': records.get(q['id'], {}).get('attempts', [])[:]}
        try:
            record.update(request(record['messages']))
            record.update(score(record['raw'], q['answer']))
            record['attempts'].append({'at': record['recorded_at'], 'status': 'received'})
        except Exception as error:
            record.update(raw='', answer='', correct=False, status='error', error=type(error).__name__)
            if isinstance(getattr(error, 'status_code', None), int):
                record['http_status'] = error.status_code
            record['attempts'].append({'at': record['recorded_at'], 'status': 'error', 'type': type(error).__name__})
        return record

    queue = iter(pending)
    halted = False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        active = {}
        def submit_next():
            q = next(queue, None)
            if q:
                active[pool.submit(receive, q)] = q['id']
        for _ in range(workers):
            submit_next()
        while active:
            finished, _ = wait(active, return_when=FIRST_COMPLETED)
            received = []
            for future in finished:
                active.pop(future)
                record = future.result()
                records[record['id']] = record
                halted = halted or record['status'] == 'error'
                received.append(record)
            run['records'] = [records[q['id']] for q in selected if q['id'] in records]
            run['updated_at'] = now()
            save(run, directory)
            for record in received:
                print(f"{len(records)}/{len(selected)} {record['id']}: {record['status']}", flush=True)
            if not halted:
                for _ in finished:
                    submit_next()
    run['status'] = 'complete' if len(records) == len(selected) and all(r['status'] != 'error' for r in records.values()) else 'incomplete'
    execution['finished_at'] = now()
    run['updated_at'] = now()
    save(run, directory)
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--ceiling-usd', type=float, default=2)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4 or not 0 < args.ceiling_usd <= 10:
        parser.error('Use 1–4 workers and a positive ceiling no greater than $10')
    if not os.environ.get('HF_TOKEN'):
        parser.error('Configure HF_TOKEN first')
    model, separator, provider = args.model.partition(':')
    if separator != ':' or provider != 'nscale':
        parser.error('This execution path requires an explicit nscale route')
    import urllib.request
    with urllib.request.urlopen('https://router.huggingface.co/v1/models', timeout=30) as response:
        catalog = json.load(response)['data']
    entry = next(m for m in catalog if m['id'] == model)
    route = next(p for p in entry['providers'] if p['provider'] == provider and p['status'] == 'live')
    pricing = route['pricing']
    import openai
    from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError
    config = config_for(args.model, provider='huggingface')
    config.update(base_url='https://router.huggingface.co/v1', sdk_version=openai.__version__)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / '.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another evaluation is writing to this output directory')
        with OpenAI(api_key=os.environ['HF_TOKEN'], base_url=config['base_url'], max_retries=0, timeout=60) as client:
            def request(prompt):
                for attempt in range(3):
                    try:
                        response = client.chat.completions.create(model=args.model, messages=prompt, max_tokens=2048)
                        choice = response.choices[0]
                        return {'raw': choice.message.content or '', 'response_model': response.model,
                                'finish_reason': choice.finish_reason, 'response_id': response.id,
                                'usage': response.usage.model_dump() if response.usage else None}
                    except (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError):
                        if attempt == 2:
                            raise
                        time.sleep(2 ** attempt)
            try:
                run = run_parallel(config, args.output, request, args.workers,
                                   args.ceiling_usd, pricing['input'], pricing['output'])
            except ValueError as error:
                parser.error(str(error))
    print(json.dumps(summaries(run['records']), indent=2))
    return 0 if run['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
