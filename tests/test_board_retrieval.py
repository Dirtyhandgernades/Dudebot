import pytest
import io
import zipfile
import json
import hashlib

from backtest.obsidian_board_retrieval import validate_run, REPO, BRANCH
from backtest import obsidian_board_retrieval as retrieval


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


def test_download_resume_and_tamper_detection(tmp_path, monkeypatch):
    raw = json.dumps(dict(requested_symbols=['TEST'], finished_at='2026-11-20T20:20:00+00:00')).encode()
    board = dict(source_packet_sha256=hashlib.sha256(raw).hexdigest(),
                 source_packet_at='2026-11-20T20:20:00+00:00',
                 created_at='2026-11-20T20:21:00+00:00',
                 denominator=1, requested_symbols=['TEST'], rows=[dict(ticker='TEST')])
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('outputs/backtest/free-quant-1.json', raw)
        archive.writestr('outputs/backtest/free-quant-board-1.json', json.dumps(board))
    data = stream.getvalue()
    calls = []
    def api(path):
        calls.append(path)
        if path.endswith('/zip'):
            return data
        if path.endswith('/artifacts'):
            return json.dumps(dict(artifacts=[dict(id=2, name='obsidian-free-quant-1', expired=False,
                digest='sha256:' + hashlib.sha256(data).hexdigest())])).encode()
        return json.dumps(fixture()).encode()
    monkeypatch.setattr(retrieval, 'api', api)
    first = retrieval.retrieve(1, 'intent', tmp_path)
    again = retrieval.retrieve(1, 'intent', tmp_path)
    assert first == again
    assert calls.count('actions/artifacts/2/zip') == 1
    (tmp_path / 'artifact-2.zip').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='HASH'):
        retrieval.retrieve(1, 'intent', tmp_path)
