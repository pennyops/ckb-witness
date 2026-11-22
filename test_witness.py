import io, contextlib, unittest, witness
class T(unittest.TestCase):
    def run_with(self, tips, hashes):
        def fake(url, method, params):
            if method == "get_tip_header": return {"number": hex(tips[url]), "hash": "0x00"}, 0.1
            return hashes[url], 0.1
        witness.rpc = fake
        out = io.StringIO()
        with contextlib.redirect_stdout(out): witness.main("testnet")
        return out.getvalue()
    def test_agree(self):
        u = witness.EPS["testnet"]
        o = self.run_with({u[0]: 100, u[1]: 100}, {u[0]: "0xaa", u[1]: "0xaa"})
        self.assertIn("AGREE", o); self.assertNotIn("DISAGREE", o)
    def test_disagree_and_lag(self):
        u = witness.EPS["testnet"]
        o = self.run_with({u[0]: 100, u[1]: 97}, {u[0]: "0xaa", u[1]: "0xbb"})
        self.assertIn("DISAGREE", o); self.assertIn("lag=3", o)
if __name__ == "__main__": unittest.main()
