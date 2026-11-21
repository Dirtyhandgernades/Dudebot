import unittest
from datetime import datetime,timezone
from backtest.obsidian_shadow_rank import rank_symbols,prior_sessions
from smg.risk_model import FEATURES

NOW=datetime(2026,11,20,20,0,tzinfo=timezone.utc)
class ShadowRankTests(unittest.TestCase):
    def inputs(self):
        days=prior_sessions(NOW)
        bars=[dict(t=d+'T14:30:00Z',o=10,h=20,l=9,c=10+i*.1,v=1000) for i,d in enumerate(days)]
        model=dict(features=list(FEATURES),weights=[0]*7,mean=[0]*7,scale=[1]*7,bias=0)
        return bars,dict(model=model,training_last_label_date='2024-12-05',thresholds={'top_half':.4})
    def test_complete_prior_data_scores_without_probability_claim(self):
        bars,doc=self.inputs();r=rank_symbols(['AAA'],{'AAA':bars},{'AAA':bars},NOW,doc)['AAA']
        self.assertEqual(r['score'],.5);self.assertFalse(r['score_is_calibrated_probability'])
        self.assertEqual(r['last_complete_feature_session'],'2026-11-19')
        self.assertFalse(r['model_validated_for_live_use'])
    def test_missing_duplicate_future_and_unmatured_model(self):
        bars,doc=self.inputs()
        for bad in (bars[:-1],bars+[bars[0]],bars+[dict(bars[0],t='2027-01-01T00:00:00Z')]):
            self.assertIsNone(rank_symbols(['AAA'],{'AAA':bad},{'AAA':bars},NOW,doc)['AAA']['score'])
        doc['training_last_label_date']='2026-11-20'
        with self.assertRaises(ValueError):rank_symbols(['AAA'],{'AAA':bars},{'AAA':bars},NOW,doc)
if __name__=='__main__':unittest.main()


class FeatureQualityTests(unittest.TestCase):
    inputs=ShadowRankTests.inputs
    def test_nan_and_contradictory_daily_bars_quarantined(self):
        for patch in ({'v':float('nan')},{'h':1}):
            bars,doc=self.inputs();bars[0].update(patch)
            self.assertIsNone(rank_symbols(['AAA'],{'AAA':bars},{'AAA':bars},NOW,doc)['AAA']['score'])
