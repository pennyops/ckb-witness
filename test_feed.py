import unittest, feed
OK="2026-11-22T23:00:25Z https://a/rpc tip=5 lag=0 rtt=0.2s|https://b/rpc tip=5 lag=0 rtt=0.3s|height 3: AGREE {'0x1'}|tx 0x1 TXAGREE ['committed']|idxlag 0,0|"
BAD="2026-11-22T23:30:00Z https://a/rpc tip=5 lag=0 rtt=0.2s|https://b/rpc tip=3 lag=2 rtt=0.3s|height 3: DISAGREE {'0x1','0x2'}|idxlag 0,4|"
class T(unittest.TestCase):
    def test_ok_no_events(self): self.assertEqual(feed.anomalies(OK)[1], [])
    def test_bad_events(self):
        ev = feed.anomalies(BAD)[1]
        self.assertEqual(len(ev), 3); self.assertIn("lag 2", ev[1])
if __name__ == "__main__": unittest.main()
