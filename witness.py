#!/usr/bin/env python3
"""ckb-witness prototype: ask several public CKB RPC endpoints the same questions
and report lag / disagreement (single-provider dependence check)."""
import json, os, sys, time, urllib.request
EPS = {"mainnet": ["https://mainnet.ckb.dev/rpc", "https://mainnet.ckbapp.dev/rpc"],
       "testnet": ["https://testnet.ckb.dev/rpc", "https://testnet.ckbapp.dev/rpc"]}
def rpc(url, method, params):
    req = urllib.request.Request(url, json.dumps({"id":1,"jsonrpc":"2.0","method":method,"params":params}).encode(),
                                 {"content-type":"application/json","user-agent":"ckb-witness/0.1"})
    t=time.time(); r=json.load(urllib.request.urlopen(req, timeout=10)); return r.get("result"), time.time()-t
def endpoints(net):
    """CKB_WITNESS_ENDPOINTS=url1,url2 replaces the built-in list (point the monitor at your own/private RPCs)."""
    env=os.environ.get("CKB_WITNESS_ENDPOINTS","").strip()
    return [u.strip() for u in env.split(",") if u.strip()] if env else EPS[net]
def main(net):
    """Returns True when every reachable endpoint agrees (used by --check for a non-zero exit code)."""
    tips={}
    for u in endpoints(net):
        try: h,dt=rpc(u,"get_tip_header",[]); tips[u]=(int(h["number"],16),h["hash"],dt)
        except Exception as e: tips[u]=None; print("DOWN",u,e)
    ok={u:v for u,v in tips.items() if v}
    if not ok: return False
    lo=min(v[0] for v in ok.values()); hi=max(v[0] for v in ok.values())
    for u,v in ok.items(): print(f"{u} tip={v[0]} lag={hi-v[0]} rtt={v[2]:.2f}s")
    h=lo-12; hashes={}
    for u in ok:
        b,_=rpc(u,"get_block_hash",[hex(h)]); hashes[u]=b
    if net=="mainnet":
        try:
            req=urllib.request.Request(f"https://mainnet-api.explorer.nervos.org/api/v1/blocks/{h}",
                headers={"Accept":"application/vnd.api+json","Content-Type":"application/vnd.api+json","user-agent":"ckb-witness/0.1"})
            hashes["explorer"]=json.load(urllib.request.urlopen(req,timeout=10))["data"]["attributes"]["block_hash"]
        except Exception as e: print("explorer DOWN",e)
    agree=len(set(hashes.values()))==1
    print(f"height {h}: {'AGREE' if agree else 'DISAGREE'} {set(hashes.values())}")
    txok=txcheck(list(ok), h)
    idxcheck(ok)
    return agree and len(ok)==len(tips) and hi-lo<=2 and txok is not False
def idxcheck(ok):
    """Indexer lag: blocks between each endpoint's node tip and its indexer tip (stale indexer = wrong balances/cells)."""
    lags=[]
    for u,v in ok.items():
        try: r,_=rpc(u,"get_indexer_tip",[]); lags.append(str(max(0,v[0]-int(r["block_number"],16))))
        except Exception as e: lags.append("err")
    print("idxlag "+",".join(lags))
def txcheck(urls, h):
    """Pick the newest tx in block h and ask every endpoint for it: all should say committed in the same block."""
    try:
        blk,_=rpc(urls[0],"get_block_by_number",[hex(h)])
        txs=blk["transactions"]; txh=txs[-1]["hash"]
    except Exception as e: print("tx SKIP",type(e).__name__); return
    seen={}
    for u in urls:
        try:
            r,_=rpc(u,"get_transaction",[txh]); st=r["tx_status"]; seen[u]=(st["status"],st.get("block_hash"))
        except Exception as e: seen[u]=("error",type(e).__name__)
    same=len(set(seen.values()))==1 and all(v[0]=="committed" for v in seen.values())
    print(f"tx {txh[:18]} {'TXAGREE' if same else 'TXMISMATCH'} {sorted(set(v[0] for v in seen.values()))}")
    return same
if __name__=="__main__":
    args=[a for a in sys.argv[1:] if not a.startswith("--")]
    ok=main(args[0] if args else "mainnet")
    # --check: one-shot gate for CI/cron; exit 1 on any endpoint down, tip lag, hash or tx disagreement.
    if "--check" in sys.argv: sys.exit(0 if ok else 1)
