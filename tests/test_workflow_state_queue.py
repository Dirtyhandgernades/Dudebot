from pathlib import Path
import yaml


def test_state_writers_share_a_serial_queue_that_preserves_pending_discovery_and_delivery():
    writers=['activate','broad-discover','cloudflare','discover','evidence-archive','noon','practice']
    for name in writers:
        workflow=yaml.safe_load((Path('.github/workflows')/(name+'.yml')).read_text())
        concurrency=workflow['concurrency']
        assert concurrency['group']=='smg-state-writer-v2'
        assert concurrency['queue']=='max'
        assert concurrency['cancel-in-progress'] is False


def test_independent_archive_and_ranked_steps_survive_legacy_failure():
    workflow=yaml.safe_load(Path('.github/workflows/evidence-archive.yml').read_text())
    independent={
        'Archive current market and borrow snapshot',
        'Enrich eight pending symbols with daily fundamentals and sentiment',
        'Publish newly qualified ranked firm signals and distinct research watches',
        'Backfill ten public halt and FINRA sessions',
        'Learn realized policy returns and squeeze losses without retuning live weights',
    }
    steps={step.get('name'):step for step in workflow['jobs']['archive']['steps']}
    for name in independent:
        assert '!cancelled()' in steps[name]['if']
        assert not steps[name].get('continue-on-error',False)
        assert 'workflow_dispatch' in steps[name]['if']
