# Data: not included in the repository

The raw and processed data for this study total about 1.3 GB. Some files exceed GitHub's size limit, and all of them are freely re-downloadable, so they are **not committed**. What is committed:

| File | Why |
|---|---|
| [`provenance.md`](provenance.md) | Source URL, access date, licence and every transformation, per dataset |
| [`candidates.md`](candidates.md) | The data-scouting shortlist, including the datasets that were rejected and why |
| [`raw/bts/manifest.csv`](raw/bts/manifest.csv) | Source URL, SHA-256, byte size and row count for all 300 monthly BTS flight files, so every raw file is hash-verifiable |

## Sources

| Dataset | Licence | Fetched by |
|---|---|---|
| Wikidata (via QLever SPARQL) | CC0 1.0 | `analysis/02_extract_wikidata.py`; citizenship by `02c_extract_citizenship.py` (run it manually, see below) |
| US DOT BTS On-Time Performance, 2000–2024 | Public domain (US federal) | `analysis/02b_extract_bts.py` |
| General Social Survey 1972–2024 (NORC) | Free public use | `analysis/00_verify_sources.py`, then `04_extract_gss.py` |
| JPL DE440s ephemeris | Public domain (NASA/JPL) | downloaded automatically by `skyfield` on first run |
| Laouenan et al. (2022) notable people (reference only) | CC BY-SA 4.0 | see `provenance.md` §2 |

## Rebuilding

```bash
python analysis/02c_extract_citizenship.py   # not yet a run_all stage (see ERRATA.md)
python analysis/run_all.py
```

The first run downloads everything. BTS alone is about 3 hours at the polite request rate, and later runs reuse the cache. Set `PAPERMILL_CONTACT_EMAIL` so API operators can reach you if your client misbehaves.
