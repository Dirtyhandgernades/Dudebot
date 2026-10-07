"""Seed symbol caches from prior batch responses before an expanded replay."""
import argparse,gzip,json,hashlib
from pathlib import Path
from smg.intraday_replay import Bars
from backtest.intraday_checkpoint_study import run


class SymbolBars:
    def __init__(self,cache,max_requests=500):
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.provider=Bars('backtest/runtime/checkpoint-bars',max_requests=max_requests)
    @property
    def requests(self):return self.provider.requests
    def get(self,symbols,opened,cutoff,mode):
        paths={t:self.cache/(hashlib.sha256(json.dumps([t,opened.isoformat(),cutoff.isoformat(),mode,'sip','5Min','asof-']).encode()).hexdigest()+'.json') for t in symbols}
        found={};missing=[]
        for ticker,path in paths.items():
            if path.exists():found[ticker]=json.loads(path.read_text())
            else:missing.append(ticker)
        if missing:
            data=self.provider.get(symbols if self.provider.max_requests==0 else missing,opened,cutoff,mode)
            for ticker in missing:
                rows=data.get(ticker,[]);paths[ticker].write_text(json.dumps(rows));found[ticker]=rows
        return found


def main():
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--packet',required=True)
    p.add_argument('--out',default='reports/balanced/checkpoints');a=p.parse_args()
    client=SymbolBars('backtest/runtime/balanced-minutes');prime='COMPLETE'
    client.provider.max_requests=0
    try:
        # Original candidate queries reproduce the warm batch-cache keys.
        # Publish no legacy study; use it only to export cached bars by symbol.
        run(json.loads(gzip.decompress(Path(a.base).read_bytes())),client,Path('backtest/runtime/legacy-prime-output'))
    except RuntimeError as exc:
        if str(exc)!='REQUEST_BUDGET':raise
        prime='PARTIAL_LEGACY_CACHE'
    client.provider.max_requests=500
    report=run(json.loads(gzip.decompress(Path(a.packet).read_bytes())),client,Path(a.out),train_window_years=2)
    report['legacy_cache_seed']=prime;report['new_provider_requests']=client.requests
    (Path(a.out)/'summary.json').write_text(json.dumps(report,indent=2))


if __name__=='__main__':main()
