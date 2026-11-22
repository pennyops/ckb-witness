# ckb-witness (prototype)

Wallets and dApps on Nervos CKB usually trust a single RPC endpoint. If that endpoint lags,
forks off, or silently drops data, the user cannot tell.

ckb-witness asks several independent sources the same question and reports:
- tip lag between sources
- block-hash agreement at a recent height (tip - 12)
- indexer lag (node tip minus get_indexer_tip) per endpoint
- tx visibility: the newest tx of that block must be reported `committed` in the same block by every endpoint

Sources today (mainnet): mainnet.ckb.dev, mainnet.ckbapp.dev, CKB Explorer API.
Observation: these are the only two keyless public mainnet JSON-RPC endpoints found (Nov 2026).

Run: `python3 witness.py mainnet` (or `testnet`). Python 3 stdlib only.

Live status page (hourly via GitHub Actions): https://pennyops.github.io/ckb-witness/
Raw logs: measurements.log (mainnet), testnet.log (testnet, from Nov 22)

Status: early prototype. Planned: own light client as a witness, indexer (get_cells) consistency checks, alerts (RSS/Nostr).
License: MIT
