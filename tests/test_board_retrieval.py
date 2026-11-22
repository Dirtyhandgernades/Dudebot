import pytest

from backtest.obsidian_board_retrieval import validate_run, REPO, BRANCH


def fixture():
    return dict(id=1, display_title='intent', head_branch=BRANCH, event='workflow_dispatch',
                path='.github/workflows/obsidian-free-quant-feed.yml',
                repository=dict(full_name=REPO), status='completed', conclusion='success')


@pytest.mark.parametrize('field', ['id', 'display_title', 'head_branch', 'event', 'path', 'repository'])
def test_wrong_run_identity_rejected(field):
    run = fixture()
    run[field] = 'wrong'
    with pytest.raises(ValueError):
        validate_run(run, 1, 'intent')


def test_pending_and_failed_run_are_distinct():
    run = fixture()
    assert validate_run(run, 1, 'intent')
    run['status'] = 'in_progress'
    assert not validate_run(run, 1, 'intent')
    run.update(status='completed', conclusion='failure')
    with pytest.raises(ValueError, match='FAILED'):
        validate_run(run, 1, 'intent')
