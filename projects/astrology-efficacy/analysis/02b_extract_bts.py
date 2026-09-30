"""
02b_extract_bts.py — Build the Study 2 daily flight-disruption series from BTS.

Source: US DOT Bureau of Transportation Statistics, "Reporting Carrier On-Time
Performance (1987-present)", direct PREZIP monthly zips (verified working; the
form-driven ASP interface is not needed).

DISK POLICY (a documented deviation from "data/raw is never modified"):
360 monthly zips total ~9.4 GB against 27 GB free on this machine. Each month is
therefore streamed, reduced to the four analysis columns, aggregated to a daily
series, and the zip is deleted -- UNLESS --keep-zips is passed. Reproducibility is
preserved by recording, per month, the source URL, SHA-256, byte size, and row count
in data/raw/bts/manifest.csv. Every raw file remains re-obtainable and hash-verifiable
from a stable public URL.

Output: data/processed/bts_daily.parquet  (one row per calendar day)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

PROJ = Path(__file__).resolve().parent.parent
RAW = PROJ / "data" / "raw" / "bts"
PROC = PROJ / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

CONTACT = os.environ.get("PAPERMILL_CONTACT_EMAIL", "ai-papermill@example.org")
UA = f"academic-research-bot/1.0 (mailto:{CONTACT})"
URL = ("https://transtats.bts.gov/PREZIP/"
       "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip")

# PREZIP coverage was probed directly: 1995-01 through 1999-12 return 404, 2000-01
# onward return 200. The span is set from that measurement, not from the BTS site's
# claimed "1987-present".
YEAR_START, YEAR_END = 2000, 2024
USECOLS = ["FlightDate", "ArrDelayMinutes", "Cancelled", "Diverted"]

# BTS drops connections when hit rapidly (an unthrottled first run got 299 straight
# DNS/connection failures after ~60 requests). Be a polite client.
REQUEST_PAUSE_S = 2.0
MAX_RETRIES = 4

# A flight is "delayed" if it arrives 15+ minutes late -- the BTS standard definition.
DELAY_THRESHOLD = 15.0


def month_frame(blob: bytes) -> pd.DataFrame:
    """Reduce one monthly zip to a daily aggregate."""
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(name) as fh:
            df = pd.read_csv(fh, usecols=USECOLS, low_memory=False,
                             encoding="latin-1")
    df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors="coerce")
    df = df.dropna(subset=["FlightDate"])
    df["Cancelled"] = pd.to_numeric(df["Cancelled"], errors="coerce").fillna(0)
    df["Diverted"] = pd.to_numeric(df["Diverted"], errors="coerce").fillna(0)
    df["ArrDelayMinutes"] = pd.to_numeric(df["ArrDelayMinutes"], errors="coerce")

    # Delay share is computed over flights that actually operated and arrived,
    # so cancellations are not silently counted as on-time.
    df["operated"] = ((df["Cancelled"] == 0) & (df["Diverted"] == 0)).astype(int)
    df["is_delayed"] = ((df["ArrDelayMinutes"] >= DELAY_THRESHOLD)
                        & (df["operated"] == 1)).astype(int)

    g = df.groupby("FlightDate")
    out = pd.DataFrame({
        "n_flights": g.size(),
        "n_operated": g["operated"].sum(),
        "n_cancelled": g["Cancelled"].sum(),
        "n_diverted": g["Diverted"].sum(),
        "n_delayed": g["is_delayed"].sum(),
        "mean_arr_delay": g["ArrDelayMinutes"].mean(),
    })
    return out.reset_index().rename(columns={"FlightDate": "date"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-zips", action="store_true",
                    help="retain raw monthly zips (~9.4 GB) instead of hashing and discarding")
    args = ap.parse_args()

    frames, manifest = [], []
    cache = PROC / "bts_monthly_cache"
    cache.mkdir(exist_ok=True)

    months = [(y, m) for y in range(YEAR_START, YEAR_END + 1) for m in range(1, 13)]
    for i, (year, month) in enumerate(months, 1):
        part = cache / f"{year}_{month:02d}.parquet"
        side = cache / f"{year}_{month:02d}.json"
        if part.exists():
            # Resume path. The cache makes the download restartable -- a standby,
            # a dropped connection or a crash costs at most the month in flight --
            # but the provenance record has to survive the resume too, otherwise
            # manifest.csv would only ever describe the final run's months.
            daily = pd.read_parquet(part)
            frames.append(daily)
            if side.exists():
                manifest.append(json.loads(side.read_text(encoding="utf-8")))
            else:
                # Cached by a version of this script that predates the sidecars.
                # Everything except the hash is recoverable from the cached file.
                manifest.append({
                    "year": year, "month": month,
                    "url": URL.format(year=year, month=month),
                    "sha256": "", "bytes": "",
                    "days": len(daily), "flights": int(daily["n_flights"].sum()),
                    "status": "ok (from cache; re-run with a cleared cache to "
                              "regenerate the source hash)"})
            continue

        url = URL.format(year=year, month=month)
        t0 = time.perf_counter()
        blob = None
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                time.sleep(REQUEST_PAUSE_S)
                r = requests.get(url, headers={"User-Agent": UA}, timeout=900)
                r.raise_for_status()
                blob = r.content
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                # A 404 is a real absence, not congestion: stop retrying it.
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status == 404:
                    break
                backoff = min(60, 5 * 2 ** (attempt - 1))
                print(f"       {year}-{month:02d} attempt {attempt}/{MAX_RETRIES} "
                      f"failed ({type(exc).__name__}); sleeping {backoff}s", flush=True)
                time.sleep(backoff)

        if blob is None:
            print(f"  [{i:3d}/{len(months)}] {year}-{month:02d} FAILED: {last_exc}",
                  flush=True)
            manifest.append({"year": year, "month": month, "url": url,
                             "status": f"FAILED: {last_exc}"})
            continue
        sha = hashlib.sha256(blob).hexdigest()
        try:
            daily = month_frame(blob)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i:3d}/{len(months)}] {year}-{month:02d} PARSE FAILED: {exc}",
                  flush=True)
            manifest.append({"year": year, "month": month, "url": url,
                             "sha256": sha, "status": f"PARSE FAILED: {exc}"})
            continue

        daily.to_parquet(part, index=False)
        frames.append(daily)
        rec = {"year": year, "month": month, "url": url, "sha256": sha,
               "bytes": len(blob), "days": len(daily),
               "flights": int(daily["n_flights"].sum()), "status": "ok"}
        manifest.append(rec)
        # Sidecar written with the cache file, so the provenance record survives a
        # resume (see the cache-hit branch above).
        side.write_text(json.dumps(rec), encoding="utf-8")
        if args.keep_zips:
            (RAW / f"ontime_{year}_{month:02d}.zip").write_bytes(blob)

        print(f"  [{i:3d}/{len(months)}] {year}-{month:02d}  "
              f"{len(blob) / 1024**2:5.1f} MB  {daily['n_flights'].sum():>8,} flights  "
              f"{time.perf_counter() - t0:5.1f}s", flush=True)

    if not frames:
        print("No data retrieved.")
        return 1

    all_daily = (pd.concat(frames, ignore_index=True)
                 .groupby("date", as_index=False).sum(numeric_only=True)
                 .sort_values("date"))
    all_daily["delay_share"] = all_daily["n_delayed"] / all_daily["n_operated"]
    all_daily["cancel_share"] = all_daily["n_cancelled"] / all_daily["n_flights"]
    all_daily.to_parquet(PROC / "bts_daily.parquet", index=False)
    pd.DataFrame(manifest).to_csv(RAW / "manifest.csv", index=False)

    print(f"\nDaily series: {len(all_daily):,} days, "
          f"{all_daily['date'].min().date()} .. {all_daily['date'].max().date()}")
    print(f"Total flights: {all_daily['n_flights'].sum():,}")
    print(f"Mean delay share:  {all_daily['delay_share'].mean():.4f}")
    print(f"Mean cancel share: {all_daily['cancel_share'].mean():.4f}")
    print(f"-> {PROC / 'bts_daily.parquet'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
