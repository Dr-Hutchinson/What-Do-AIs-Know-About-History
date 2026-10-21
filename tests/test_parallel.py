import json
from threading import Barrier

import pytest

from evaluate import config_for
from evaluate_parallel import run_parallel


def test_parallel_drains_errors_and_preserves_completed_invalid(tmp_path):
    cfg = config_for('test', limit=1, provider='huggingface')
    barrier = Barrier(3)
    def request(prompt):
        barrier.wait(timeout=5)
        if 'U.S. History' in prompt[1]['content']:
            raise RuntimeError('do not print secret provider body')
        return {'raw': 'Answer: A', 'response_model': 'test', 'finish_reason': 'stop', 'usage': None}
    first = run_parallel(cfg, tmp_path, request, workers=3, ceiling_usd=1, input_price=.07, output_price=.18)
    assert first['status'] == 'incomplete'
    assert len(first['records']) == 3
    assert sum(r['status'] == 'invalid' for r in first['records']) == 2
    calls = []
    def retry(prompt):
        calls.append(prompt)
        return {'raw': 'A', 'response_model': 'test', 'finish_reason': 'stop', 'usage': None}
    second = run_parallel(cfg, tmp_path, retry, workers=3, ceiling_usd=1, input_price=.07, output_price=.18)
    assert second['status'] == 'complete'
    assert len(calls) == 1
    assert sum(r['status'] == 'invalid' for r in second['records']) == 2
    assert 'secret provider body' not in json.dumps(second)


def test_parallel_budget_and_corrupt_checkpoint_send_nothing(tmp_path):
    cfg = config_for('test', limit=1, provider='huggingface')
    def forbidden(prompt):
        pytest.fail('No request should be sent')
    with pytest.raises(ValueError, match='exceeds ceiling'):
        run_parallel(cfg, tmp_path, forbidden, ceiling_usd=.000001)
    assert not (tmp_path / 'run.json').exists()
    (tmp_path / 'run.json').write_text(json.dumps({'config': cfg, 'status': 'incomplete',
                                                 'records': [{'id': 'unknown'}]}))
    with pytest.raises(ValueError, match='unknown'):
        run_parallel(cfg, tmp_path, forbidden)
