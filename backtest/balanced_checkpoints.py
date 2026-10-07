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
    p.add_argument('--out',default='reports/balanced/checkpoints')
    p.add_argument('--controls',action='store_true',help='Separate corpus changes from training-window changes')
    a=p.parse_args()
    client=SymbolBars('backtest/runtime/balanced-minutes');prime='COMPLETE'
    client.provider.max_requests=0
    try:
        # Original candidate queries reproduce the warm batch-cache keys.
        # Publish no legacy study; use it only to export cached bars by symbol.
        run(json.loads(gzip.decompress(Path(a.base).read_bytes())),client,
            Path(a.out).parent/'controls/original-expanding' if a.controls else Path('backtest/runtime/legacy-prime-output'))
    except RuntimeError as exc:
        if str(exc)!='REQUEST_BUDGET':raise
        prime='PARTIAL_LEGACY_CACHE'
    client.provider.max_requests=500
    report=run(json.loads(gzip.decompress(Path(a.packet).read_bytes())),client,Path(a.out),train_window_years=2)
    report['legacy_cache_seed']=prime;report['new_provider_requests']=client.requests
    (Path(a.out)/'summary.json').write_text(json.dumps(report,indent=2))
    if a.controls:
        # These are diagnostics, not new tunable policies. Retain all four
        # cells rather than choosing a different winner for each year.
        root=Path(a.out).parent/'controls'
        run(json.loads(gzip.decompress(Path(a.base).read_bytes())),client,root/'original-two-year',train_window_years=2)
        run(json.loads(gzip.decompress(Path(a.packet).read_bytes())),client,root/'expanded-expanding')
        rows=[]
        for corpus,window,folder in [('original','expanding',root/'original-expanding'),
                                     ('original','two-year',root/'original-two-year'),
                                     ('expanded','expanding',root/'expanded-expanding'),
                                     ('expanded','two-year',Path(a.out))]:
            summary=json.loads((folder/'summary.json').read_text())
            for row in summary['results']:
                rows.append({'corpus':corpus,'training_window':window,**row})
        (root/'summary.json').write_text(json.dumps({'status':'CORPUS_AND_LOOKBACK_CONTROLS',
            'results':rows,'provider_requests_total':client.requests,'live_changed':False,
            'limits':['Inspected historical diagnostics, not untouched validation',
                      'Expanded corpus also adds early prices and dated source evidence',
                      'No historical borrow or eligibility facts are inferred']},indent=2))


if __name__=='__main__':main()
