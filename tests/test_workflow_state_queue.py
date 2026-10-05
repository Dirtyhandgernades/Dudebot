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
