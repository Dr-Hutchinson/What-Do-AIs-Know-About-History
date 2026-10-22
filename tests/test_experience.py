import json
from pathlib import Path

import httpx
from openai import OpenAI
import pytest
from streamlit.testing.v1 import AppTest

from experience import ISSUES, session_json, visitor_questions
from history import SUBJECTS, messages, questions
from live import LiveConfig, LimitReached, ensure_answer, request_once, reserve


def config(**overrides):
    return LiveConfig(**{'provider': 'huggingface', 'model': 'Qwen/Qwen3-8B', 'key': 'test-placeholder',
                         'base_url': 'https://router.huggingface.co/v1', **overrides})


def test_curation_preserves_canonical_dataset():
    assert len(questions('high_school_us_history')) == 204
    assert len(visitor_questions('high_school_us_history')) == 188
    assert not ISSUES.keys() & {q['id'] for s in SUBJECTS for q in visitor_questions(s)}
    assert len(visitor_questions('high_school_world_history')) == 235
    assert len(visitor_questions('high_school_european_history')) == 164
    assert len(ISSUES) == 19


def test_live_answer_is_locked_and_not_repeated(tmp_path):
    q = questions('high_school_us_history')[0]
    state = {'answers': {}, 'model_answers': {}}
    calls = []
    def requester(*args):
        calls.append(args)
        return {'status': 'invalid', 'answer': '', 'correct': False, 'raw': 'Answer: A'}
    with pytest.raises(ValueError):
        ensure_answer(state, q, config(), tmp_path / 'budget.json', requester)
    assert not calls
    state['answers'][q['id']] = 'B'
    first = ensure_answer(state, q, config(), tmp_path / 'budget.json', requester)
    assert ensure_answer(state, q, config(), tmp_path / 'budget.json', requester) == first
    assert len(calls) == 1
    state['model_answers'].clear()
    def interrupted(*args):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        ensure_answer(state, q, config(), tmp_path / 'budget.json', interrupted)
    assert ensure_answer(state, q, config(), tmp_path / 'budget.json', requester)['status'] == 'error'
    assert len(calls) == 1


def test_shared_allowance_and_corrupt_ledger_fail_closed(tmp_path):
    ledger = tmp_path / 'budget.json'
    prompt = messages(questions('high_school_us_history')[0])
    reserve(config(daily_requests=1), prompt, ledger)
    with pytest.raises(LimitReached):
        reserve(config(daily_requests=1), prompt, ledger)
    ledger.write_text('broken')
    result = request_once(config(), questions('high_school_us_history')[0], ledger,
                          client_factory=lambda **kwargs: pytest.fail('must not contact provider'))
    assert result['status'] == 'error'
    ledger.unlink()
    result = request_once(config(daily_usd=0.000001), questions('high_school_us_history')[0], ledger,
                          client_factory=lambda **kwargs: pytest.fail('budget exceeded'))
    assert result['status'] == 'error'


def test_huggingface_payload_and_failure_privacy(tmp_path):
    q = questions('high_school_us_history')[0]
    calls = []
    def respond(request):
        calls.append(json.loads(request.content))
        assert request.url.host == 'router.huggingface.co'
        assert calls[-1]['messages'] == messages(q)
        assert calls[-1]['max_tokens'] == 2048
        assert 'tools' not in calls[-1]
        return httpx.Response(200, json={'id': 'test', 'object': 'chat.completion', 'created': 1,
            'model': 'Qwen/Qwen3-8B', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': ' b\n'}, 'finish_reason': 'stop'}]})
    def factory(**kwargs):
        assert kwargs['max_retries'] == 0
        return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond)))
    result = request_once(config(), q, tmp_path / 'budget.json', factory)
    assert result['answer'] == 'B'
    assert result['messages'] == messages(q)
    assert len(calls) == 1
    def broken(**kwargs):
        raise RuntimeError('a-provider-error-containing-a-secret')
    result = request_once(config(), q, tmp_path / 'budget.json', broken)
    assert result['status'] == 'error'
    assert 'secret' not in json.dumps(result)


def test_critique_reveal_and_session_export():
    app = AppTest.from_string('from views import critique; critique()').run()
    assert not app.exception
    assert not app.warning
    next(b for b in app.button if b.label == 'Reveal the source problem').click().run()
    assert 'Samuel Thomas' in app.warning[0].value
    assert not app.exception
    q = visitor_questions('high_school_us_history')[0]
    state = {'opponent': {'mode': 'Solo practice'}, 'questions': [q], 'answers': {q['id']: 'B'}, 'model_answers': {}}
    exported = json.loads(session_json(state))
    assert exported['items'][0]['id'] == q['id']
    assert exported['items'][0]['your_answer'] == 'B'


def test_live_ui_reruns_do_not_request_twice(monkeypatch, tmp_path):
    import views
    cfg = config()
    monkeypatch.setattr(views, 'live_config', lambda: cfg)
    calls = []
    def fake(state, q, cfg, ledger):
        def answer(*args):
            calls.append(q['id'])
            return {'raw': 'A', 'answer': 'A', 'correct': q['answer'] == 'A', 'status': 'valid'}
        return ensure_answer(state, q, cfg, tmp_path / 'budget.json', answer)
    monkeypatch.setattr(views, 'ensure_answer', fake)
    app = AppTest.from_string('from views import quiz; quiz()').run()
    assert not app.exception
    assert not calls
    app.radio[0].set_value('B')
    next(b for b in app.button if b.label == 'Submit answer').click().run()
    assert not app.exception
    assert len(calls) == 1
    app.run()
    assert len(calls) == 1
    # A reflection rerun must preserve the model response.
    app.radio[0].set_value('Prior historical knowledge').run()
    assert len(calls) == 1
    assert app.session_state['quiz_state']['reflections']


def test_charts_render_real_run_schema_and_known_size(monkeypatch):
    import views
    from test_history import make_full_run
    run = make_full_run()
    run['name'] = 'test-fixture'
    run['config']['model'] = 'Qwen/Qwen3-8B:nscale'
    monkeypatch.setattr(views, 'published_runs', lambda: ([run], []))
    app = AppTest.from_string('from views import results; results()').run()
    assert not app.exception
    assert len(app.get('plotly_chart')) == 4
    assert len(app.dataframe[0].value) == 3


def test_session_download_hides_unanswered_keys_and_recorded_responses():
    q = visitor_questions('high_school_us_history')[0]
    state = {'opponent': {'mode': 'Recorded model'}, 'questions': [q], 'answers': {},
             'model_answers': {q['id']: {'answer': 'A', 'raw': 'A'}}}
    item = json.loads(session_json(state))['items'][0]
    assert 'answer' not in item
    assert item['model_response'] is None


def test_live_requires_explicit_enable_and_valid_limits():
    from live import configuration
    values = {'HF_TOKEN': 'test-placeholder'}
    assert configuration(values.get) is None
    values['LIVE_ENABLED'] = '1'
    assert configuration(values.get).provider == 'huggingface'
    assert configuration(values.get).model == 'Qwen/Qwen3-8B:nscale'
    assert configuration(values.get).max_output_tokens == 2048
    values['LIVE_MAX_OUTPUT_TOKENS'] = '4097'
    assert configuration(values.get) is None
    values['LIVE_MAX_OUTPUT_TOKENS'] = '256'
    assert configuration(values.get).max_output_tokens == 256
    values['LIVE_DAILY_USD'] = 'nan'
    assert configuration(values.get) is None


def test_huggingface_evaluator_dry_run(tmp_path):
    import subprocess
    import sys
    result = subprocess.run([sys.executable, 'evaluate.py', '--provider', 'huggingface',
        '--output', str(tmp_path / 'unused'), '--limit', '1', '--dry-run'], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload['config']['model'] == 'Qwen/Qwen3-8B'
    assert payload['config']['provider'] == 'Hugging Face'
    assert payload['config']['base_url'] == 'https://router.huggingface.co/v1'
    assert not (tmp_path / 'unused').exists()


def test_registered_page_navigation():
    app = AppTest.from_file('app.py').run()
    next(b for b in app.button if b.label == 'Take the history challenge').click().run()
    assert not app.exception
    assert app.title[0].value == 'You versus the model'


def test_all_reviewed_defects_are_inspectable_without_scoring():
    app = AppTest.from_string('from views import critique; critique()').run()
    assert not app.exception
    assert set(app.selectbox[0].options) == {
        f"{item_id} · {issue['title']}" for item_id, issue in ISSUES.items()}
    for item_id, issue in ISSUES.items():
        app.selectbox[0].set_value(item_id).run()
        assert not app.exception
        assert not app.metric
        # An unseen item's explanation must not inherit another item's reveal state.
        assert not app.warning
        next(b for b in app.button if b.label == 'Reveal the source problem').click().run()
        assert not app.exception
        assert app.warning[0].value == issue['explanation']
        subject = item_id.split(':')[0]
        q = next(q for q in questions(subject) if q['id'] == item_id)
        assert any(q['question'].splitlines()[-1] in m.value for m in app.markdown)
        assert any(f"original benchmark key is {q['answer']}:" in m.value for m in app.markdown)


def test_existing_quiz_drops_newly_excluded_item(monkeypatch):
    import views
    monkeypatch.setattr(views, 'live_config', lambda: None)
    app = AppTest.from_string('from views import quiz; quiz()').run()
    assert not app.exception
    state = app.session_state['quiz_state']
    state['questions'][0] = questions('high_school_us_history')[32]
    state['answers'][state['questions'][0]['id']] = 'A'
    old_nonce = state['nonce']
    app.run()
    assert not app.exception
    new_state = app.session_state['quiz_state']
    assert new_state['nonce'] != old_nonce
    assert not new_state['answers']
    assert not ISSUES.keys() & {q['id'] for q in new_state['questions']}
    exported = json.loads(session_json(new_state))
    assert '19 reviewed structurally defective items' in exported['selection']


def test_audit_ledger_covers_every_test_item():
    import csv
    from history import dataset_version
    from experience import AUDIT_PATH
    audit = json.loads(AUDIT_PATH.read_text())
    assert audit['dataset_version'] == dataset_version()
    all_ids = {q['id'] for subject in SUBJECTS for q in questions(subject)}
    with AUDIT_PATH.with_suffix('.csv').open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(all_ids) == 606
    assert {r['id'] for r in rows} == all_ids
    assert {r['id'] for r in rows if r['disposition'] == 'excluded_from_visitor_quiz'} == set(ISSUES)
    # Preserve the exact originally observed mismatches and the new missing-reference cases.
    for row in (18, 22, 33, 44, 49, 71, 97, 105, 117, 119, 127, 130, 171, 176, 188, 195):
        assert f'high_school_us_history:test:{row:03}' in ISSUES
    assert 'high_school_european_history:test:153' in ISSUES
    assert 'high_school_world_history:test:037' in ISSUES
    assert 'high_school_world_history:test:062' in ISSUES
