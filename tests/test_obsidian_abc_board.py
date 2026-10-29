import copy
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from backtest.obsidian_abc_board import build, write


class BoardTests(unittest.TestCase):
    def packet(self):
        return dict(cutoff_at='2026-10-29T14:20:00-05:00',exchange_session_verified=True,
                    calendar_receipt='fixture-calendar',universe=['AAPL','MSFT'],universe_receipt='fixture-roster',
                    rows=[dict(ticker=x,classification='BLOCKED',observed_at='2026-10-29T14:19:00-05:00',
                               source_receipts=['fixture'],source_latency_verified=True) for x in ['AAPL','MSFT']])
    def now(self):return datetime.fromisoformat('2026-10-29T14:21:00-05:00')
    def test_complete_denominator_and_no_delivery_claim(self):
        result=build(self.packet(),self.now())
        self.assertEqual(result['counts'],{'BLOCKED':2})
        self.assertEqual(result['denominator'],2)
        self.assertFalse(result['delivery_verified'])
        self.assertIsNone(result['outcomes'])
    def test_future_stale_missing_and_universe_omissions(self):
        packet=self.packet();packet['rows'].pop()
        with self.assertRaises(ValueError):build(packet,self.now())
        packet=self.packet();packet['rows'][0]['observed_at']='2026-10-29T14:21:00-05:00'
        with self.assertRaises(ValueError):build(packet,self.now())
        packet=self.packet();packet['rows'][0].update(classification='A',observed_at='2026-10-29T13:00:00-05:00')
        result=build(packet,self.now())
        self.assertEqual(result['rows'][0]['classification'],'BLOCKED')
        self.assertIn('STALE_OBSERVATION',result['rows'][0]['blockers'])
    def test_no_backfill_or_unverified_session(self):
        with self.assertRaises(ValueError):build(self.packet(),datetime.fromisoformat('2026-10-30T14:21:00-05:00'))
        packet=self.packet();packet['exchange_session_verified']=False
        with self.assertRaises(ValueError):build(packet,self.now())
    def test_write_once(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'packet.json';source.write_text(json.dumps(self.packet()))
            out=Path(folder)/'board.json';write(source,out,self.now());raw=out.read_bytes()
            with self.assertRaises(FileExistsError):write(source,out,self.now())
            self.assertEqual(raw,out.read_bytes())
