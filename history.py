"""Shared dataset, prompting and scoring rules. No network calls or UI dependencies."""
import csv
import hashlib
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PUBLISHED = ROOT / "results"
SUBJECTS = {
    "high_school_us_history": "U.S. History",
    "high_school_european_history": "European History",
    "high_school_world_history": "World History",
}
LETTERS = "ABCD"
PROTOCOL = "history-mmlu-five-shot-v1"
INSTRUCTION = "Answer the multiple-choice question. Return only one letter: A, B, C, or D."


def dataset_version():
    manifest = json.loads((DATA / "manifest.json").read_text())
    for name, entry in manifest["files"].items():
        if hashlib.sha256((DATA / name).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Dataset checksum mismatch: {name}")
    return hashlib.sha256(json.dumps(manifest["files"], sort_keys=True).encode()).hexdigest()


def questions(subject, split="test"):
    if subject not in SUBJECTS or split not in ("dev", "test"):
        raise ValueError("Unknown subject or split")
    result = []
    with (DATA / f"{subject}_{split}.csv").open(newline="", encoding="utf-8") as handle:
        for index, row in enumerate(csv.reader(handle), 1):
            if len(row) != 6 or row[5] not in LETTERS or not all(row):
                raise ValueError(f"Invalid question: {subject}/{split}/{index}")
            result.append(dict(id=f"{subject}:{split}:{index:03}", subject=subject,
                               question=row[0], options=row[1:5], answer=row[5]))
    return result


def question_text(q):
    return q["question"] + "\n" + "\n".join(f"{letter}. {text}" for letter, text in zip(LETTERS, q["options"])) + "\nAnswer:"


def messages(q):
    examples = questions(q["subject"], "dev")
    if len(examples) != 5:
        raise ValueError("Protocol requires exactly five development examples")
    body = f"The following are multiple-choice questions about {SUBJECTS[q['subject']]}.\n\n"
    body += "\n\n".join(question_text(e) + " " + e["answer"] for e in examples)
    body += "\n\n" + question_text(q)
    return [{"role": "system", "content": INSTRUCTION}, {"role": "user", "content": body}]


def parse_answer(raw):
    # Strict normalization: never guess a letter from explanatory prose.
    text = raw.strip().upper()
    return text if re.fullmatch(r"[ABCD]", text) else ""


def score(raw, expected):
    letter = parse_answer(raw)
    return {"answer": letter, "status": "valid" if letter else "invalid", "correct": letter == expected}


def summaries(records):
    rows = []
    for subject, label in SUBJECTS.items():
        selected = [r for r in records if r["subject"] == subject]
        if not selected:
            continue
        correct = sum(r["correct"] for r in selected)
        errors = sum(r["status"] == "error" for r in selected)
        rows.append({"Subject": label, "Correct": correct, "Questions": len(selected),
                     "Accuracy": f"{correct / len(selected):.1%}" if not errors else "Incomplete",
                     "Invalid answers": sum(r["status"] == "invalid" for r in selected), "API failures": errors})
    return rows


def csv_bytes(records):
    output = io.StringIO(newline="")
    fields = ["id", "subject", "question", "A", "B", "C", "D", "expected", "answer", "correct", "status", "raw", "recorded_at", "response_model", "finish_reason"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        row = dict(record)
        row.update(dict(zip(LETTERS, row.get("options", []))))
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def published_runs(directory=PUBLISHED):
    """Only verified complete full-history runs can supply public comparisons."""
    runs, problems = [], []
    version = dataset_version()
    expected = {q["id"]: q for subject in SUBJECTS for q in questions(subject)}
    for path in sorted(directory.glob("*/run.json")):
        try:
            run = json.loads(path.read_text())
            config = run["config"]
            if (run["status"] != "complete" or config["dataset_version"] != version
                    or config["protocol"] != PROTOCOL or config["limit_per_subject"] is not None):
                raise ValueError("Requires a complete full-history run using the current dataset and protocol")
            records = run["records"]
            if len(records) != len(expected) or {r["id"] for r in records} != set(expected):
                raise ValueError("Missing or duplicate test questions")
            for r in records:
                q = expected[r["id"]]
                if (r["subject"] != q["subject"] or r["expected"] != q["answer"]
                        or r["question"] != q["question"] or r["options"] != q["options"]
                        or r["messages"] != messages(q)):
                    raise ValueError("Question or prompt does not match the dataset/protocol")
                if any(r[key] != value for key, value in score(r["raw"], q["answer"]).items()):
                    raise ValueError("Recorded score does not match raw response")
            run["name"] = path.parent.name
            runs.append(run)
        except (ValueError, KeyError, TypeError, OSError) as error:
            problems.append(f"{path.parent.name}: {error}")
    return runs, problems
