"""Three real live-path smoke requests; saved separately from benchmark results."""
import json
import os
from pathlib import Path

from history import SUBJECTS, questions
from live import configuration, ensure_answer


def main():
    root = Path(__file__).parent / 'runs/hf-live-verification'
    root.mkdir(parents=True, exist_ok=True)
    report = root / 'report.json'
    if report.exists():
        raise SystemExit('Verification already recorded. Inspect it; do not repeat automatically.')
    values = dict(os.environ, LIVE_ENABLED='1')
    config = configuration(values.get)
    if config is None:
        raise SystemExit('Configure HF_TOKEN and valid live settings first.')
    state = {'answers': {}, 'model_answers': {}}
    records = []
    for subject in SUBJECTS:
        q = questions(subject)[0]
        state['answers'][q['id']] = 'B'
        answer = ensure_answer(state, q, config, root / 'allowance.json')
        before = (root / 'allowance.json').read_bytes()
        assert ensure_answer(state, q, config, root / 'allowance.json') is answer
        assert (root / 'allowance.json').read_bytes() == before
        records.append({'id': q['id'], **answer})
        report.write_text(json.dumps({'records': records, 'rerun_did_not_request': True}, indent=2) + '\n')
        print(q['id'], answer['status'], answer.get('finish_reason'), flush=True)
        if answer['status'] == 'error':
            raise SystemExit('Live request failed; inspect sanitized report.')
    if any(r['status'] != 'valid' or r.get('finish_reason') != 'stop' for r in records):
        raise SystemExit('Live responses are not all usable; keep live play disabled.')


if __name__ == '__main__':
    main()
