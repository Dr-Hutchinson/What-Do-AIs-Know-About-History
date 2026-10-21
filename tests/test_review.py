import pytest

from review_assessments import review
from test_history import make_full_run


def reviewed_fixture():
    run = make_full_run()
    run['name'] = 'test-only'
    run['config']['model'] = 'Qwen/Qwen3-8B:nscale'
    run['executions'] = [{'input_usd_per_million': .07, 'output_usd_per_million': .18}]
    for r in run['records']:
        r.update(response_model='Qwen/Qwen3-8B', finish_reason='stop',
                 usage={'prompt_tokens': 100, 'completion_tokens': 2})
    return run


def test_review_refuses_model_substitution_and_missing_usage():
    run = reviewed_fixture()
    run['records'][0]['response_model'] = 'a-different-model'
    with pytest.raises(ValueError, match='identity differs'):
        review(run)
    run['records'][0]['response_model'] = 'Qwen/Qwen3-8B'
    run['records'][0]['usage'] = None
    with pytest.raises(ValueError, match='token usage'):
        review(run)


def test_review_preserves_known_defects_and_uses_reported_tokens():
    result = review(reviewed_fixture())
    assert result['questions'] == 606
    assert len(result['known_defective_items']) == 3
    assert result['estimated_token_cost_usd'] == pytest.approx((60600*.07+1212*.18)/1_000_000)
