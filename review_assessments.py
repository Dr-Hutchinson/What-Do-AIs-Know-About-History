"""Validate complete requested runs, prepare a review, optionally copy locally."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from experience import ISSUES
from history import published_runs, summaries

ROOT = Path(__file__).resolve().parent


def review(run):
    canonical = run['config']['model'].split(':', 1)[0]
    identities = Counter(r.get('response_model') for r in run['records'])
    if set(identities) != {canonical}:
        raise ValueError(f"{run['name']}: returned model identity differs from the requested model")
    usage = [r.get('usage') for r in run['records']]
    if any(not u or not all(isinstance(u.get(k), int) and u[k] >= 0
                           for k in ('prompt_tokens', 'completion_tokens')) for u in usage):
        raise ValueError(f"{run['name']}: missing or malformed token usage")
    input_tokens = sum(u['prompt_tokens'] for u in usage)
    output_tokens = sum(u['completion_tokens'] for u in usage)
    execution = run.get('executions', [])[-1] if run.get('executions') else None
    estimate = None
    if execution:
        estimate = (input_tokens * execution['input_usd_per_million']
                    + output_tokens * execution['output_usd_per_million']) / 1_000_000
    return {'name': run['name'], 'requested_model': run['config']['model'],
            'questions': len(run['records']), 'correct': sum(r['correct'] for r in run['records']),
            'invalid': sum(r['status'] == 'invalid' for r in run['records']),
            'finish_reasons': dict(Counter(r.get('finish_reason') for r in run['records'])),
            'invalid_output_categories': dict(Counter(
                'empty response' if not r['raw'].strip() else
                'truncated text' if r.get('finish_reason') == 'length' else 'non-letter output'
                for r in run['records'] if r['status'] == 'invalid')),
            'response_models': dict(identities), 'input_tokens': input_tokens,
            'output_tokens': output_tokens, 'estimated_token_cost_usd': estimate,
            'subjects': summaries(run['records']),
            'known_defective_items': [{k: r[k] for k in ('id', 'answer', 'expected', 'correct', 'status')}
                                      for r in run['records'] if r['id'] in ISSUES]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', required=True, help='Directory names under runs/')
    parser.add_argument('--publish-local', action='store_true', help='Copy only validated full runs into local results/')
    args = parser.parse_args()
    validated, problems = published_runs(ROOT / 'runs')
    available = {run['name']: run for run in validated}
    missing = set(args.runs) - set(available)
    if missing:
        relevant = [p for p in problems if p.split(':', 1)[0] in missing]
        raise SystemExit('Requested runs are not complete and valid: ' + ', '.join(sorted(missing))
                         + ('\n' + '\n'.join(relevant) if relevant else ''))
    runs = [available[name] for name in args.runs]
    reviews = [review(run) for run in runs]
    created = datetime.now(timezone.utc).isoformat()
    pairs = []
    for i, left in enumerate(runs):
        for right in runs[i+1:]:
            by_id = {r['id']: r for r in right['records']}
            pairs.append({'left': left['name'], 'right': right['name'],
                          'different_parsed_answers': sum(r['answer'] != by_id[r['id']]['answer'] for r in left['records']),
                          'both_correct': sum(r['correct'] and by_id[r['id']]['correct'] for r in left['records']),
                          'left_only_correct': sum(r['correct'] and not by_id[r['id']]['correct'] for r in left['records']),
                          'right_only_correct': sum(not r['correct'] and by_id[r['id']]['correct'] for r in left['records'])})
    report = {'reviewed_at': created, 'runs': reviews, 'pairwise': pairs,
              'limitations': 'One run per model; provider-default sampling. 4B Instruct 2507 has different post-training and supports only non-thinking mode. Known canonical defects retained. Invalid outputs count as unsuccessful. Token-cost estimates exclude unsaved interrupted requests and are not account billing records.'}
    directory = ROOT / 'data'
    (directory / 'ASSESSMENT_REVIEW_2026-09-30.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Qwen3 history assessments', '', f'Reviewed: {created}', '',
             'All listed runs contain the unchanged 606 canonical test questions and exact five-shot prompts.', '',
             '| Model / route | U.S. | European | World | Overall | Invalid | Truncated | Estimated token cost |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for item in reviews:
        subjects = ' | '.join(s['Accuracy'] for s in item['subjects'])
        cost = f"${item['estimated_token_cost_usd']:.4f}" if item['estimated_token_cost_usd'] is not None else 'Unavailable'
        lines.append(f"| {item['requested_model']} | {subjects} | {item['correct']/item['questions']:.1%} | {item['invalid']} | {item['finish_reasons'].get('length', 0)} | {cost} |")
    lines += ['', report['limitations'], '',
              'Raw answers, prompts, keys, usage, and response identities remain inspectable in each `run.json`. The explorer shows per-subject results and question disagreements. These are three-subject history results, not full MMLU scores or isolated measurements of model size.', '',
              'The three known U.S. passage/question defects remain in full assessments and are excluded only from visitor sampling. See `VALIDATION_2026-09-30.md`.', '']
    lines += ['## Output validity', '']
    for item in reviews:
        categories = ', '.join(f'{count} {category}' for category, count in item['invalid_output_categories'].items()) or 'No invalid outputs'
        lines.append(f"- {item['requested_model']}: {categories}.")
    lines += ['', 'A normally finished response such as `Answer: B` or a letter followed by an explanation is invalid under the unchanged single-letter rule. No letter is extracted from prose and no completed response is retried to improve its score.', '']
    (directory / 'ASSESSMENT_RESULTS_2026-09-30.md').write_text('\n'.join(lines))
    if args.publish_local:
        for run in runs:
            target = ROOT / 'results' / run['name']
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'runs' / run['name'] / 'run.json', target / 'run.json')
        published, errors = published_runs()
        if errors or not set(args.runs) <= {r['name'] for r in published}:
            raise SystemExit('Local publication validation failed: ' + '; '.join(errors))
    print(json.dumps(reviews, indent=2))


if __name__ == '__main__':
    main()
