#!/usr/bin/env python3
"""ckb-witness prototype: ask several public CKB RPC endpoints the same questions
and report lag / disagreement (single-provider dependence check)."""
import json, sys, time, urllib.request
EPS = {"mainnet": ["https://mainnet.ckb.dev/rpc", "https://mainnet.ckbapp.dev/rpc"],
       "testnet": ["https://testnet.ckb.dev/rpc", "https://testnet.ckbapp.dev/rpc"]}
def rpc(url, method, params):
    req = urllib.request.Request(url, json.dumps({"id":1,"jsonrpc":"2.0","method":method,"params":params}).encode(),
                                 {"content-type":"application/json","user-agent":"ckb-witness/0.1"})
    t=time.time(); r=json.load(urllib.request.urlopen(req, timeout=10)); return r.get("result"), time.time()-t
def main(net):
    tips={}
    for u in EPS[net]:
        try: h,dt=rpc(u,"get_tip_header",[]); tips[u]=(int(h["number"],16),h["hash"],dt)
        except Exception as e: tips[u]=None; print("DOWN",u,e)
    ok={u:v for u,v in tips.items() if v}
    if not ok: return
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
if __name__=="__main__": main(sys.argv[1] if len(sys.argv)>1 else "mainnet")
