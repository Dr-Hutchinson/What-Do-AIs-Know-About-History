import json

import pytest

from history import SUBJECTS, dataset_version, messages, parse_answer, published_runs, questions, score, summaries
from evaluate import config_for, run_evaluation


def test_dataset_and_prompt_separation():
    assert len(dataset_version()) == 64
    assert [len(questions(s)) for s in SUBJECTS] == [204, 165, 237]
    for subject in SUBJECTS:
        assert len(questions(subject, 'dev')) == 5
        q = questions(subject)[0]
        prompt = messages(q)[1]['content']
        assert prompt.endswith('Answer:')
        assert prompt.count('Answer:') == 6
        assert q['id'] not in {e['id'] for e in questions(subject, 'dev')}


@pytest.mark.parametrize('raw,expected', [(' A\n', 'A'), ('b', 'B'), ('Answer: A', ''), ('A or B', ''), ('A.', ''), ('', ''), ('The answer is C', '')])
def test_strict_scoring(raw, expected):
    assert parse_answer(raw) == expected


def test_invalids_stay_in_denominator():
    subject = next(iter(SUBJECTS))
    records = [dict(subject=subject, **score('A', 'A')), dict(subject=subject, **score('A or B', 'A'))]
    assert summaries(records)[0]['Accuracy'] == '50.0%'
    records.append(dict(subject=subject, status='error', correct=False))
    assert summaries(records)[0]['Accuracy'] == 'Incomplete'


def test_resume_failure_without_repeating_completed_answers(tmp_path):
    config = config_for('test-model', limit=1)
    calls = []
    def fail_second(prompt):
        calls.append(prompt)
        if len(calls) == 2:
            raise RuntimeError('simulated outage')
        return dict(raw='A', response_model='test-model', finish_reason='stop')
    run = run_evaluation(config, tmp_path, fail_second)
    assert run['status'] == 'incomplete'
    assert len(run['records']) == 2
    first = run['records'][0]
    resumed_calls = []
    def finish(prompt):
        resumed_calls.append(prompt)
        return dict(raw='B', response_model='test-model', finish_reason='stop')
    run = run_evaluation(config, tmp_path, finish)
    assert run['status'] == 'complete'
    assert len(resumed_calls) == 2
    assert run['records'][0] == first
    assert len(run['records'][1]['attempts']) == 2
    run_evaluation(config, tmp_path, lambda _: pytest.fail('completed run requested again'))
    with pytest.raises(ValueError, match='configuration changed'):
        run_evaluation({**config, 'model': 'other'}, tmp_path, finish)


def make_full_run():
    records = []
    for subject in SUBJECTS:
        for q in questions(subject):
            records.append(dict(id=q['id'], subject=subject, question=q['question'], options=q['options'], expected=q['answer'], messages=messages(q), raw='A', **score('A', q['answer'])))
    return dict(config=config_for('test-model'), status='complete', created_at='2026-01-01T00:00:00Z', records=records)


def test_publication_rejects_partial_duplicate_and_inconsistent_runs(tmp_path):
    directory = tmp_path / 'test-only'
    directory.mkdir()
    path = directory / 'run.json'
    run = make_full_run()
    path.write_text(json.dumps(run))
    assert len(published_runs(tmp_path)[0]) == 1
    run['records'][0]['correct'] = not run['records'][0]['correct']
    path.write_text(json.dumps(run))
    assert not published_runs(tmp_path)[0]
    run = make_full_run()
    run['records'][-1] = run['records'][0]
    path.write_text(json.dumps(run))
    assert not published_runs(tmp_path)[0]
    run = make_full_run()
    run['config']['limit_per_subject'] = 1
    path.write_text(json.dumps(run))
    assert not published_runs(tmp_path)[0]


def test_interruption_keeps_checkpoint_and_resumes(tmp_path):
    config = config_for('test-model', limit=1)
    calls = []
    def interrupt(prompt):
        calls.append(prompt)
        if len(calls) == 2:
            raise KeyboardInterrupt()
        return dict(raw='not a letter', response_model='test-model', finish_reason='stop')
    with pytest.raises(KeyboardInterrupt):
        run_evaluation(config, tmp_path, interrupt)
    saved = json.loads((tmp_path / 'run.json').read_text())
    assert len(saved['records']) == 1
    assert saved['status'] == 'incomplete'
    assert saved['records'][0]['status'] == 'invalid'
    resumed = []
    def finish(prompt):
        resumed.append(prompt)
        return dict(raw='C', response_model='test-model', finish_reason='stop')
    run = run_evaluation(config, tmp_path, finish)
    assert len(resumed) == 2  # Invalid answer is not retried to improve the score.
    assert run['status'] == 'complete'


def test_default_luna_dry_run_has_no_side_effects(tmp_path):
    import subprocess
    import sys
    result = subprocess.run([sys.executable, 'evaluate.py', '--output', str(tmp_path / 'unused'), '--dry-run'], capture_output=True, text=True, check=True)
    preview = json.loads(result.stdout)
    assert preview['config']['model'] == 'gpt-6-luna'
    assert preview['config']['reasoning_effort'] == 'none'
    assert not (tmp_path / 'unused').exists()


def test_luna_api_request_and_retry_with_mock_transport(tmp_path, monkeypatch):
    import httpx
    import openai
    import sys
    import evaluate
    original = openai.OpenAI
    payloads = []
    def respond(request):
        assert request.url.host == 'api.openai.com'
        payload = json.loads(request.content)
        payloads.append(payload)
        if len(payloads) == 1:
            return httpx.Response(429, json={'error': {'message': 'test rate limit', 'type': 'rate_limit_error'}})
        assert payload['model'] == 'gpt-6-luna'
        assert payload['reasoning_effort'] == 'none'
        assert 'temperature' not in payload
        assert 'tools' not in payload
        return httpx.Response(200, json={
            'id': 'test-response', 'object': 'chat.completion', 'created': 1,
            'model': 'gpt-6-luna', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': ' B\n'}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 1, 'total_tokens': 101}})
    monkeypatch.setattr(openai, 'OpenAI', lambda **kwargs: original(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond))))
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder-not-a-real-key')
    monkeypatch.setattr(evaluate.time, 'sleep', lambda _: None)
    monkeypatch.setattr(sys, 'argv', ['evaluate.py', '--output', str(tmp_path), '--limit', '1'])
    assert evaluate.main() == 0
    assert len(payloads) == 4
    run = json.loads((tmp_path / 'run.json').read_text())
    assert run['config']['reasoning_effort'] == 'none'
    assert run['config']['sdk_version'] == openai.__version__
    assert run['records'][0]['answer'] == 'B'
    assert run['records'][0]['usage']['total_tokens'] == 101
