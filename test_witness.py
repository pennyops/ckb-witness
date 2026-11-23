import io, os, contextlib, unittest, witness
class T(unittest.TestCase):
    def run_with(self, tips, hashes):
        def fake(url, method, params):
            if method == "get_tip_header": return {"number": hex(tips[url]), "hash": "0x00"}, 0.1
            if method == "get_indexer_tip": return {"number": "0x0", "block_number": hex(tips[url] - 2)}, 0.1
            if method == "get_block_by_number": return {"transactions": [{"hash": "0x" + "ab" * 32}]}, 0.1
            if method == "get_transaction": return {"tx_status": {"status": "committed", "block_hash": "0xcc"}}, 0.1
            return hashes[url], 0.1
        witness.rpc = fake
        out = io.StringIO()
        with contextlib.redirect_stdout(out): self.ok = witness.main("testnet")
        return out.getvalue()
    def test_agree(self):
        u = witness.EPS["testnet"]
        o = self.run_with({u[0]: 100, u[1]: 100}, {u[0]: "0xaa", u[1]: "0xaa"})
        self.assertIn("AGREE", o); self.assertNotIn("DISAGREE", o)
        self.assertIn("TXAGREE", o); self.assertIn("idxlag 2,2", o)
        self.assertTrue(self.ok)  # --check would exit 0
    def test_disagree_and_lag(self):
        u = witness.EPS["testnet"]
        o = self.run_with({u[0]: 100, u[1]: 97}, {u[0]: "0xaa", u[1]: "0xbb"})
        self.assertIn("DISAGREE", o); self.assertIn("lag=3", o)
        self.assertFalse(self.ok)  # --check would exit 1
    def test_endpoint_override(self):
        os.environ["CKB_WITNESS_ENDPOINTS"] = " https://a/rpc, https://b/rpc ,"
        try: self.assertEqual(witness.endpoints("mainnet"), ["https://a/rpc", "https://b/rpc"])
        finally: del os.environ["CKB_WITNESS_ENDPOINTS"]
        self.assertEqual(witness.endpoints("mainnet"), witness.EPS["mainnet"])
    def test_tx_mismatch(self):
        u = witness.EPS["testnet"]
        def fake(url, method, params):
            if method == "get_block_by_number": return {"transactions": [{"hash": "0x" + "ab" * 32}]}, 0.1
            st = "committed" if url == u[0] else "unknown"
            return {"tx_status": {"status": st, "block_hash": "0xcc" if st == "committed" else None}}, 0.1
        witness.rpc = fake
        out = io.StringIO()
        with contextlib.redirect_stdout(out): witness.txcheck(u, 100)
        self.assertIn("TXMISMATCH", out.getvalue())
if __name__ == "__main__": unittest.main()
