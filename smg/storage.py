import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone

class Store:
    """Durable SQLite record. GitHub backend below persists it before outbound sends."""
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=DELETE')
        self.db.execute('CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        self.db.execute('''CREATE TABLE IF NOT EXISTS observations (
            kind TEXT NOT NULL,
            subject TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            source TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (kind, subject, observed_at)
        )''')
        self.db.execute('CREATE INDEX IF NOT EXISTS observations_lookup ON observations(kind,subject,observed_at DESC)')
        self.db.commit()
    def get(self,key,default=None):
        row=self.db.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default
    def put(self,key,value):
        self.db.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',(key,json.dumps(value,allow_nan=False)))
        self.db.commit()
    def delete(self,key):
        self.db.execute('DELETE FROM kv WHERE key=?',(key,));self.db.commit()
    def delete_prefix(self,prefix):
        self.db.execute('DELETE FROM kv WHERE key LIKE ?',(prefix+'%',));self.db.commit()
    def items(self,prefix):
        return [(key,json.loads(value)) for key,value in self.db.execute('SELECT key,value FROM kv WHERE key LIKE ?',(prefix+'%',)).fetchall()]
    def observe(self,kind,subject,observed_at,source,value):
        """Append an immutable, timestamped provider observation.

        Replaying the same observation is idempotent. A provider correction must
        carry a new observation time instead of silently rewriting history.
        """
        stamp=observed_at.isoformat() if hasattr(observed_at,'isoformat') else str(observed_at)
        self.db.execute('INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?)',
            (kind,subject.upper(),stamp,source,json.dumps(value,allow_nan=False,sort_keys=True)))
        self.db.commit()
    def observations(self,kind,subject=None,start=None,end=None):
        sql='SELECT subject,observed_at,source,value FROM observations WHERE kind=?';args=[kind]
        if subject is not None:sql+=' AND subject=?';args.append(subject.upper())
        if start is not None:sql+=' AND observed_at>=?';args.append(start.isoformat() if hasattr(start,'isoformat') else str(start))
        if end is not None:sql+=' AND observed_at<=?';args.append(end.isoformat() if hasattr(end,'isoformat') else str(end))
        sql+=' ORDER BY observed_at,subject'
        return [dict(subject=s,observed_at=t,source=u,value=json.loads(v)) for s,t,u,v in self.db.execute(sql,args)]
    def latest_observation(self,kind,subject):
        row=self.db.execute('SELECT observed_at,source,value FROM observations WHERE kind=? AND subject=? ORDER BY observed_at DESC LIMIT 1',
            (kind,subject.upper())).fetchone()
        return dict(observed_at=row[0],source=row[1],value=json.loads(row[2])) if row else None

class GitHubState:
    """GitHub contents API with SHA guards. Never catches a conflicting write and overwrites."""
    def __init__(self,http,repo,token,branch='smg-state'):
        if not repo or '/' not in repo: raise ValueError('GITHUB_REPOSITORY is required')
        self.http=http;self.repo=repo;self.branch=branch;self.sha=None;self.branch_exists=False;self.checkpoint_error=None
        self.headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Cache-Control':'no-cache'}
    @property
    def url(self): return 'https://api.github.com/repos/'+self.repo+'/contents/runtime/state.sqlite'
    def remember_local(self,path):
        import os
        run=os.environ.get('GITHUB_RUN_ID')
        if run:
            Path(path).with_suffix('.remote.json').write_text(json.dumps({'run':run,'repo':self.repo,'branch':self.branch,'sha':self.sha}))
    def restore(self,path):
        import base64
        import os
        from .transport import ProviderError
        local=Path(path);memo=local.with_suffix('.remote.json');run=os.environ.get('GITHUB_RUN_ID')
        if run and local.exists() and memo.exists():
            try:cached=json.loads(memo.read_text())
            except (ValueError,OSError):cached={}
            if (cached.get('run'),cached.get('repo'),cached.get('branch'))==(run,self.repo,self.branch) and cached.get('sha')==self.blob_sha(local.read_bytes()):
                # Serialized state-writer workflow commands share the last
                # successful checkpoint. The next write still uses its SHA
                # and rejects a concurrent external update before any send.
                self.sha=cached['sha'];self.branch_exists=True;return
        if hasattr(self.http,'response'):
            expected=None;read_url=self.url;params={'ref':self.branch}
            try:
                if hasattr(self.http,'json'):
                    # Resolve a small object first, then fetch its immutable
                    # blob rather than a potentially stale moving-branch body.
                    metadata=self.http.json(self.url,params=params,headers={**self.headers,'Accept':'application/vnd.github.object+json'})
                    expected=metadata['sha']
                    import re
                    if not re.fullmatch('[a-f0-9]{40}',expected):raise ValueError('Invalid state blob SHA')
                    read_url='https://api.github.com/repos/'+self.repo+'/git/blobs/'+expected;params=None
                r=self.http.response(read_url,params=params,headers={**self.headers,'Accept':'application/vnd.github.raw+json'})
            except ProviderError as exc:
                if exc.status!=404:raise
                return
            content=r.content
            if not content.startswith(b'SQLite format 3\x00'):raise ValueError('GitHub state is not a SQLite database')
            if expected and self.blob_sha(content)!=expected:raise ValueError('GitHub state blob checksum mismatch')
            self.sha=self.blob_sha(content);self.branch_exists=True
            Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(content)
            self.remember_local(path)
            return
        # Preserve compatibility with json-only provider adapters.
        try: data=self.http.json(self.url,params={'ref':self.branch},headers=self.headers)
        except ProviderError as exc:
            if exc.status!=404: raise
            return
        if data.get('encoding')!='base64':
            data=self.http.json('https://api.github.com/repos/'+self.repo+'/git/blobs/'+data['sha'],headers=self.headers)
        if data.get('encoding')!='base64':raise ValueError('Unsupported state encoding')
        content=base64.b64decode(data['content']);self.sha=data['sha']
        Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(content)
    def ensure_branch(self):
        if self.branch_exists:return
        from .transport import ProviderError
        root='https://api.github.com/repos/'+self.repo
        try: self.http.json(root+'/git/ref/heads/'+self.branch,headers=self.headers);self.branch_exists=True;return
        except ProviderError as exc:
            if exc.status!=404:raise
        repo=self.http.json(root,headers=self.headers)
        ref=self.http.json(root+'/git/ref/heads/'+repo['default_branch'],headers=self.headers)
        self.http.json(root+'/git/refs',method='POST',headers=self.headers,body={'ref':'refs/heads/'+self.branch,'sha':ref['object']['sha']})
        self.branch_exists=True
    @staticmethod
    def blob_sha(content):
        import hashlib
        return hashlib.sha1(b'blob '+str(len(content)).encode()+b'\x00'+content).hexdigest()
    def checkpoint(self,store):
        import base64
        from .transport import ProviderError
        if self.checkpoint_error:raise self.checkpoint_error
        content=store.path.read_bytes()
        if self.sha==self.blob_sha(content):return
        self.ensure_branch()
        body={'message':'Update SMG notifier state','branch':self.branch,'content':base64.b64encode(content).decode()}
        if self.sha:body['sha']=self.sha
        desired=self.blob_sha(content)
        try:
            data=self.http.json(self.url,method='PUT',headers=self.headers,body=body)
        except ProviderError as exc:
            # Read-only reconciliation is not a blind mutation retry. A lost
            # acknowledgement may already have committed EXACTLY these bytes.
            # Otherwise retry a409 once only when the remote blob is still the
            # SAME expected snapshot; retain its SHA guard. Never adopt a
            # different writer's SHA to overwrite their state.
            try:
                remote=self.http.json(self.url,params={'ref':self.branch},
                    headers={**self.headers,'Accept':'application/vnd.github.object+json'})
                actual=remote.get('sha') if isinstance(remote,dict) else None
                if actual==desired:
                    self.sha=desired;self.remember_local(store.path);return
                if exc.status==409 and self.sha and actual==self.sha:
                    data=self.http.json(self.url,method='PUT',headers=self.headers,body=body)
                else:raise exc
            except ProviderError as final:
                self.checkpoint_error=final;raise
        self.sha=data['content']['sha']
        self.remember_local(store.path)
