#!/usr/bin/env python3
"""Build feed.xml (Atom) listing anomaly events from measurements.log/testnet.log.
An event = block-hash DISAGREE / no result, tip lag > 0, endpoint down/error,
TXMISMATCH, or indexer lag > 0. Healthy runs produce no entries."""
import re, sys
from xml.sax.saxutils import escape

BASE = "https://pennyops.github.io/ckb-witness/"

def anomalies(line):
    ts, _, rest = line.partition(" ")
    parts = [p for p in rest.split("|") if p.strip()]
    out = []
    if not any(p.startswith("height") and "AGREE" in p and "DISAGREE" not in p for p in parts):
        out.append("block hash DISAGREE or no result")
    for p in parts:
        m = re.match(r"(\S+) tip=(\d+) lag=(\d+)", p)
        if m and int(m.group(3)) > 0:
            out.append(f"{m.group(1)} lag {m.group(3)} blocks")
        if p.startswith("DOWN") or p.startswith("explorer DOWN"):
            out.append(p[:160])
        if "TXMISMATCH" in p:
            out.append(p[:160])
        if p.startswith("idxlag"):
            if any(x not in ("0", "") for x in p[7:].split(",")):
                out.append("indexer " + p[:80])
    return ts, out

def build(logs, limit=50):
    entries = []
    for net, path in logs:
        try:
            lines = open(path).read().strip().splitlines()
        except FileNotFoundError:
            continue
        for line in lines:
            if not line.strip():
                continue
            ts, ev = anomalies(line)
            if ev:
                entries.append((ts, net, ev))
    entries.sort(reverse=True)
    entries = entries[:limit]
    updated = entries[0][0] if entries else "1970-01-01T00:00:00Z"
    x = ['<?xml version="1.0" encoding="utf-8"?>',
         '<feed xmlns="http://www.w3.org/2005/Atom">',
         '<title>ckb-witness anomalies</title>',
         f'<link href="{BASE}"/><id>{BASE}feed.xml</id><updated>{updated}</updated>',
         '<author><name>ckb-witness</name></author>']
    for ts, net, ev in entries:
        x.append(f'<entry><title>{escape(net)} {escape(ts)}: {escape(ev[0])}</title>'
                 f'<id>{BASE}#{net}-{escape(ts)}</id><updated>{escape(ts)}</updated>'
                 f'<link href="{BASE}"/><content type="text">{escape("; ".join(ev))}</content></entry>')
    x.append('</feed>')
    return "\n".join(x) + "\n"

if __name__ == "__main__":
    open(sys.argv[1] if len(sys.argv) > 1 else "feed.xml", "w").write(
        build([("mainnet", "measurements.log"), ("testnet", "testnet.log")]))
