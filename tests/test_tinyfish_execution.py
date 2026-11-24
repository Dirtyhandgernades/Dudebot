import json
import subprocess
from types import SimpleNamespace

import pytest

from smg.tinyfish_execution import TinyFishCLI, action_fields


def test_cli_request_is_scoped_durable_and_uses_no_shell(tmp_path):
    calls = []
    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(dict(status='COMPLETED', run_id='synthetic-run',
                               result={'authenticated': True})), stderr='')
    adapter = TinyFishCLI(['synthetic-node', 'synthetic-cli.js'], 'synthetic-profile', 'synthetic-vault-uri', tmp_path, runner)
    result = adapter.request('TEST_ONLY', 'Synthetic non-submitting test', {'type': 'object'})
    args, options = calls[0]
    assert args[args.index('--profile-id')+1] == 'synthetic-profile'
    assert args[args.index('--credential-item-id')+1] == 'synthetic-vault-uri'
    assert options['shell'] is False
    assert 'TINYFISH_DEBUG' not in options['env']
    assert '--max-steps' not in args
    saved = json.loads((tmp_path/result['request']['request_id']/'request.json').read_text())
    assert saved['backend'] == 'TINYFISH_PERSONAL_CLI'
    assert saved['status'] == 'RESULT_RECEIVED'


def test_timeout_is_not_retried_and_retains_request_identity(tmp_path):
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        raise subprocess.TimeoutExpired('synthetic-cli', 285)
    adapter = TinyFishCLI(['synthetic-node'], 'synthetic-profile', 'synthetic-vault-uri', tmp_path, runner)
    with pytest.raises(subprocess.TimeoutExpired):
        adapter.preview(dict(ticker='TEST', side='COVER', shares=1))
    saved = json.loads((tmp_path/adapter.last_request_id/'request.json').read_text())
    assert len(calls) == 1
    assert saved['status'] == 'UNKNOWN_DO_NOT_RETRY'


@pytest.mark.parametrize('action', [dict(ticker='TEST; submit again', side='COVER', shares=1),
                                    dict(ticker='TEST', side='COVER', shares=True),
                                    dict(ticker='TEST', side='COVER', shares=0)])
def test_unexpected_ticket_text_never_reaches_browser(action):
    with pytest.raises(ValueError): action_fields(action)
