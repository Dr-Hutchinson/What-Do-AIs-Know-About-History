"""Run a documented five-shot history assessment; resume with the same arguments."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

from history import PROTOCOL, SUBJECTS, csv_bytes, dataset_version, messages, questions, score, summaries


def now():
    return datetime.now(timezone.utc).isoformat()


def save(run, directory):
    # Atomic replacement ensures an interruption cannot truncate the checkpoint.
    path = directory / "run.json"
    temporary = directory / "run.json.tmp"
    temporary.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)
    (directory / "answers.csv").write_bytes(csv_bytes(run["records"]))


def config_for(model, temperature=None, max_completion_tokens=2048, limit=None, reasoning_effort=None, provider="openai"):
    return {"model": model, "provider": {"openai": "OpenAI", "huggingface": "Hugging Face", "openrouter": "OpenRouter"}[provider], "endpoint": "chat.completions",
            "dataset_version": dataset_version(), "protocol": PROTOCOL,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "rules_sha256": hashlib.sha256(Path(__file__).with_name("history.py").read_bytes()).hexdigest(),
            "temperature": temperature, "max_completion_tokens": max_completion_tokens,
            "reasoning_effort": reasoning_effort,
            "limit_per_subject": limit, "subjects": list(SUBJECTS),
            "scoring": "Strip whitespace and uppercase; accept only a single A/B/C/D. Invalid answers count as unsuccessful.",
            "retry_policy": "At most three attempts per invocation for connection, timeout, rate-limit or server failures; resume retries failed items.",
            "tools": "none", "examples": "All five dev rows per subject in original order"}


def run_evaluation(config, directory, request):
    """request(messages) returns raw, response_model, finish_reason and usage."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "run.json"
    run = json.loads(path.read_text()) if path.exists() else {
        "config": config, "created_at": now(), "status": "incomplete", "records": []}
    if run["config"] != config:
        raise ValueError("Run configuration changed. Use a new output directory.")
    selected = [q for subject in SUBJECTS for q in questions(subject)[:config["limit_per_subject"]]]
    expected_ids = {q["id"] for q in selected}
    records = {r["id"]: r for r in run["records"]}
    if len(records) != len(run["records"]) or not set(records) <= expected_ids:
        raise ValueError("Checkpoint has duplicate or unknown question IDs")
    for q in selected:
        if q["id"] in records:
            old = records[q["id"]]
            if old["messages"] != messages(q) or old["expected"] != q["answer"]:
                raise ValueError("Checkpoint prompt or answer key changed")
            if old["status"] != "error":
                if any(old[k] != v for k, v in score(old["raw"], q["answer"]).items()):
                    raise ValueError("Checkpoint score is inconsistent")
                continue
        run["status"] = "incomplete"
        save(run, directory)
        record = {"id": q["id"], "subject": q["subject"], "question": q["question"],
                  "options": q["options"], "expected": q["answer"], "messages": messages(q),
                  "recorded_at": now(), "attempts": records.get(q["id"], {}).get("attempts", [])[:]}
        try:
            response = request(record["messages"])
            record.update(response)
            record.update(score(record["raw"], q["answer"]))
            record["attempts"].append({"at": record["recorded_at"], "status": "received"})
        except Exception as error:
            # Preserve the item as a failure and stop, avoiding hundreds of bad requests.
            record.update(raw="", answer="", correct=False, status="error",
                          error=type(error).__name__)
            record["attempts"].append({"at": record["recorded_at"], "status": "error", "type": type(error).__name__})
        records[q["id"]] = record
        run["records"] = [records[item["id"]] for item in selected if item["id"] in records]
        run["updated_at"] = now()
        save(run, directory)
        print(f"{len(records)}/{len(selected)} {q['id']}: {record['status']}", flush=True)
        if record["status"] == "error":
            print(f"Stopped after {record['error']}; check credentials/model/settings and resume with the same command.")
            return run
    run["status"] = "complete" if all(r["status"] != "error" for r in records.values()) else "incomplete"
    run["updated_at"] = now()
    save(run, directory)
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["openai", "huggingface", "openrouter"], default="openai")
    parser.add_argument("--model", help="Model ID; default depends on provider. Use a pinned version when available")
    parser.add_argument("--output", type=Path, required=True, help="Checkpoint directory; reuse to resume")
    parser.add_argument("--temperature", type=float, default=None, help="Omit for provider default; use 0 only when supported")
    parser.add_argument("--max-completion-tokens", type=int, default=2048)
    parser.add_argument("--reasoning-effort", choices=["none", "low", "medium", "high", "xhigh", "max"],
                        help="Defaults to none for gpt-6-luna, otherwise the provider default")
    parser.add_argument("--limit", type=int, help="First N questions per subject for a smoke run; not publishable")
    parser.add_argument("--dry-run", action="store_true", help="Print one exact prompt and configuration without API calls or output files")
    args = parser.parse_args()
    providers = {
        "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-6-luna"),
        "huggingface": ("HF_TOKEN", "https://router.huggingface.co/v1", "Qwen/Qwen3-8B"),
        "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "qwen/qwen3-8b"),
    }
    key_variable, base_url, default_model = providers[args.provider]
    args.model = args.model or default_model
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.max_completion_tokens < 1:
        parser.error("--max-completion-tokens must be positive")
    if args.temperature is not None and not 0 <= args.temperature <= 2:
        parser.error("--temperature must be between 0 and 2")
    effort = args.reasoning_effort
    if effort is None and args.model == "gpt-6-luna":
        effort = "none"
    config = config_for(args.model, args.temperature, args.max_completion_tokens, args.limit, effort, args.provider)
    config["base_url"] = base_url
    if args.dry_run:
        print(json.dumps({"config": config, "example_request": messages(questions(next(iter(SUBJECTS)))[0])}, indent=2))
        return 0
    if not os.environ.get(key_variable):
        parser.error(f"Set {key_variable} in your environment for this provider.")
    from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError
    import openai
    config["sdk_version"] = openai.__version__
    client = OpenAI(api_key=os.environ[key_variable], base_url=base_url, max_retries=0, timeout=60)

    def request(prompt):
        token_parameter = "max_completion_tokens" if args.provider == "openai" else "max_tokens"
        kwargs = {"model": args.model, "messages": prompt, token_parameter: args.max_completion_tokens}
        if args.temperature is not None:
            kwargs["temperature"] = args.temperature
        if effort is not None:
            kwargs["reasoning_effort"] = effort
        for attempt in range(3):
            try:
                response = client.chat.completions.create(**kwargs)
                choice = response.choices[0]
                return {"raw": choice.message.content or "", "response_model": response.model,
                        "finish_reason": choice.finish_reason, "response_id": response.id,
                        "usage": response.usage.model_dump() if response.usage else None}
            except (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    # Prevent concurrent invocations from corrupting a shared checkpoint.
    import fcntl
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / ".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Another evaluation is already writing to this output directory")
        try:
            run = run_evaluation(config, args.output, request)
        except ValueError as error:
            parser.error(str(error))
    print(json.dumps(summaries(run["records"]), indent=2))
    return 0 if run["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
