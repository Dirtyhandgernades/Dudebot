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
        self.http=http;self.repo=repo;self.branch=branch;self.sha=None
        self.headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    @property
    def url(self): return 'https://api.github.com/repos/'+self.repo+'/contents/runtime/state.sqlite'
    def restore(self,path):
        import base64
        from .transport import ProviderError
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
        from .transport import ProviderError
        root='https://api.github.com/repos/'+self.repo
        try: self.http.json(root+'/git/ref/heads/'+self.branch,headers=self.headers);return
        except ProviderError as exc:
            if exc.status!=404:raise
        repo=self.http.json(root,headers=self.headers)
        ref=self.http.json(root+'/git/ref/heads/'+repo['default_branch'],headers=self.headers)
        self.http.json(root+'/git/refs',method='POST',headers=self.headers,body={'ref':'refs/heads/'+self.branch,'sha':ref['object']['sha']})
    def checkpoint(self,store):
        import base64
        self.ensure_branch()
        body={'message':'Update SMG notifier state','branch':self.branch,'content':base64.b64encode(store.path.read_bytes()).decode()}
        if self.sha:body['sha']=self.sha
        data=self.http.json(self.url,method='PUT',headers=self.headers,body=body)
        self.sha=data['content']['sha']
