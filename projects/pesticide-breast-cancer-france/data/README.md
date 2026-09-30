# Data: mostly not included in the repository

Raw downloads for this study total about 200 MB and are **not committed**. What is committed:

| File | Why |
|---|---|
| [`provenance.md`](provenance.md) | Source URL, download date, licence and every transformation, per dataset |
| [`candidates.md`](candidates.md) | The data-scouting shortlist, including rejected candidates |
| [`processed/analysis_df.parquet`](processed/analysis_df.parquet) | The final 91-department analysis table (16 KB), so the models can be re-run without downloading anything |

`analysis_df.parquet` is derived from French public-sector open data published under the *Licence Ouverte / Etalab 2.0*, which permits redistribution with attribution. Sources: BNV-D pesticide sales (OFB / data.eaufrance.fr), Agreste agricultural census, INSEE via L'Observatoire des Territoires, and Santé publique France / Francim (Odissé). Department boundaries come from the MIT-licensed `france-geojson` project. Full citations are in `provenance.md`.

## Rebuilding from source

```bash
python analysis/00_download.py   # fetches all raw files into data/raw/
python analysis/run_all.py       # cleans, models, and writes results/
```
