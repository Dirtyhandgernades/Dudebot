"""Operate the deployed clock without exposing the existing webhook credential."""
import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request

ENDPOINT = 'https://dudebot-dispatch.dudebot-dirtyhandgernades.workers.dev'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['pause', 'resume', 'status'])
    args = parser.parse_args()
    webhook = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook:
        raise SystemExit('DISCORD_WEBHOOK_URL is missing')
    key = hashlib.sha256(('dudebot-dispatch-v1:' + webhook).encode()).hexdigest()
    opener = urllib.request.build_opener(NoRedirect())
    paths = ['/clock', '/status'] if args.action == 'status' else ['/' + args.action]
    results = {}
    for path in paths:
        request = urllib.request.Request(
            ENDPOINT + path, data=None if args.action == 'status' else b'{}',
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with opener.open(request, timeout=30) as response:
                results[path] = json.load(response)
        except urllib.error.HTTPError as exc:
            raise SystemExit('Hosted control rejected the request: HTTP ' + str(exc.code)) from None
        except (urllib.error.URLError, TimeoutError):
            raise SystemExit('Hosted control response is uncertain; run status to inspect it') from None
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
