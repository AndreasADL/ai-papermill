"""
Shared helpers for loading/cleaning raw data sources. Imported by 01_clean.py and
04_robustness.py so that department-code handling (Corsica 2A/2B aggregation,
mainland-only filtering, postal-code-to-department mapping) is implemented exactly
once and used identically everywhere it matters.

Not a pipeline step itself — no numeric prefix.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

# Mainland department codes as they appear in the OUTCOME (Odisse) data: integers
# 1-95, with Corsica unified as 20 (legacy pre-1976 coding). This is the "canonical"
# department-code space every other source is aggregated/mapped into.
MAINLAND_CODES_UNIFIED = [f"{i:02d}" for i in range(1, 96)]  # "01".."95", incl. "20"

# DOM prefixes to exclude wherever a source's postal/department code needs filtering.
DOM_DEPT_PREFIXES = ("971", "972", "973", "974", "975", "976")


def unify_corsica(df: pd.DataFrame, dept_col: str, value_cols: list, how: dict) -> pd.DataFrame:
    """
    Collapse rows with dept_col in {"2A", "2B"} into a single dept_col == "20" row,
    aggregating value_cols per the `how` dict ({"col": "sum"} or {"col": "mean"}).
    All other departments pass through unchanged.
    """
    is_corsica = df[dept_col].isin(["2A", "2B"])
    corsica = df[is_corsica]
    rest = df[~is_corsica].copy()

    if corsica.empty:
        return rest

    agg = {}
    for col in value_cols:
        method = how.get(col, "sum")
        agg[col] = corsica[col].sum() if method == "sum" else corsica[col].mean()
    corsica_row = {dept_col: "20", **agg}
    # carry through any other non-value columns (e.g. a name column) from the first row
    for col in df.columns:
        if col not in agg and col != dept_col:
            corsica_row.setdefault(col, corsica.iloc[0][col])
    rest = pd.concat([rest, pd.DataFrame([corsica_row])], ignore_index=True)
    return rest


def zero_pad_dept(x) -> str:
    s = str(x).strip()
    if s in ("2A", "2B"):
        return s
    return s.zfill(2)


# ---------------------------------------------------------------------------
# Outcome
# ---------------------------------------------------------------------------


def load_mortality() -> pd.DataFrame:
    """Primary outcome: age-standardized female breast cancer mortality, 2007-2014."""
    path = RAW / "odisse" / "mortality_femmes_sein_2007_2014.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for r in records:
        f = r["fields"]
        rows.append(
            {
                "dept": zero_pad_dept(f["dept"]),
                # Corsica (dept=20) is missing `libgeo` in this API's payload — a
                # source data quirk, not a download error (confirmed: every other
                # field for that record is present and well-formed).
                "dept_name": f.get("libgeo", "Corse" if f["dept"] == 20 else None),
                "mortality_rate_std": f["est"],
                "mortality_low": f.get("low"),
                "mortality_up": f.get("up"),
                "periode_mortality": f.get("periode"),
            }
        )
    df = pd.DataFrame(rows)
    df["is_dom"] = df["dept"].astype(str).str.len() > 2  # DOM codes are 3 digits (971 etc.)
    return df


def load_francim_incidence() -> pd.DataFrame:
    """Robustness outcome (E2): FRANCIM observed incidence, 2018-2022, registry zones."""
    path = RAW / "odisse" / "francim_incidence_femmes_sein_2018_2022.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for r in records:
        f = r["fields"]
        rows.append(
            {
                "dept": zero_pad_dept(f["dept"]),
                "zr": f.get("zr"),
                "incidence_rate_std": f.get("ratemonde"),
                "incidence_rate_inf": f.get("ratemonde_inf"),
                "incidence_rate_sup": f.get("ratemonde_sup"),
                "k_cases": f.get("k"),
                "pop_at_risk": f.get("pa"),
            }
        )
    df = pd.DataFrame(rows)
    df["is_dom"] = df["dept"].astype(str).str.len() > 2
    return df


# ---------------------------------------------------------------------------
# Exposure: BNV-D sales (VENTE_DPT_SUBSTANCE)
# ---------------------------------------------------------------------------


def load_bnvd_vente_totals(years: list) -> pd.DataFrame:
    """Sum kg active substance sold, mainland departments, Corsica unified to '20'."""
    frames = []
    for year in years:
        path = RAW / "bnvd_vente" / f"VENTE_DPT_SUBSTANCE_{year}.csv.gz"
        df = pd.read_csv(path, sep=";", encoding="utf-8", quotechar='"')
        frames.append(df[["code_departement", "quantite_substance"]])
    all_df = pd.concat(frames, ignore_index=True)
    all_df["code_departement"] = all_df["code_departement"].astype(str)
    all_df = all_df[~all_df["code_departement"].str.startswith(DOM_DEPT_PREFIXES)]

    totals = (
        all_df.groupby("code_departement", as_index=False)["quantite_substance"]
        .sum(min_count=1)
        .rename(columns={"code_departement": "dept", "quantite_substance": "pesticide_kg_total"})
    )
    totals = unify_corsica(totals, "dept", ["pesticide_kg_total"], {"pesticide_kg_total": "sum"})
    totals["n_years"] = len(years)
    return totals


# ---------------------------------------------------------------------------
# Exposure: BNV-D purchases (ACHAT_CP_SUBSTANCE) — E1 robustness
# ---------------------------------------------------------------------------


def postal_to_dept(cp: str) -> str:
    """Map a 5-digit French postal code to a department code, with the standard
    Corsica split correction. Returns None for DOM/unmappable codes."""
    cp = str(cp).strip().zfill(5)
    prefix3 = cp[:3]
    if prefix3 in DOM_DEPT_PREFIXES:
        return prefix3
    prefix2 = cp[:2]
    if prefix2 == "20":
        # Corsica: 20000-20199 -> 2A (Corse-du-Sud), 20200-20999 -> 2B (Haute-Corse)
        return "2A" if int(cp) < 20200 else "2B"
    return prefix2


def load_bnvd_achat_totals(years: list) -> pd.DataFrame:
    """Sum kg active substance purchased, mapped postal-code -> department, Corsica
    unified to '20'. Excludes foreign purchases (achat_etranger == 'Oui') and DOM."""
    frames = []
    for year in years:
        path = RAW / "bnvd_achat" / f"ACHAT_CP_SUBSTANCE_{year}.csv.gz"
        df = pd.read_csv(path, sep=";", encoding="utf-8", quotechar='"')
        df = df[df["achat_etranger"].astype(str).str.strip() != "Oui"]
        df["quantite_substance"] = pd.to_numeric(df["quantite_substance"], errors="coerce")
        frames.append(df[["code_postal_acheteur", "quantite_substance"]])
    all_df = pd.concat(frames, ignore_index=True)
    all_df["dept"] = all_df["code_postal_acheteur"].apply(postal_to_dept)
    all_df = all_df[~all_df["dept"].isin(DOM_DEPT_PREFIXES) & all_df["dept"].notna()]

    totals = (
        all_df.groupby("dept", as_index=False)["quantite_substance"]
        .sum(min_count=1)
        .rename(columns={"quantite_substance": "pesticide_kg_total_purchase"})
    )
    totals = unify_corsica(
        totals, "dept", ["pesticide_kg_total_purchase"], {"pesticide_kg_total_purchase": "sum"}
    )
    totals["n_years"] = len(years)
    return totals


# ---------------------------------------------------------------------------
# Normalizer / confounders (Observatoire des Territoires xlsx files)
# ---------------------------------------------------------------------------


def _load_obs_terr_xlsx(filename: str, value_col: str, year: int | None = None) -> pd.DataFrame:
    path = RAW / "confounders" / filename
    df = pd.read_excel(path, sheet_name="Data", header=4)
    df["codgeo"] = df["codgeo"].astype(str)
    df = df[~df["codgeo"].str.startswith(DOM_DEPT_PREFIXES)]
    if year is not None:
        df = df[df["an"] == year]
    df = df[["codgeo", value_col]].rename(columns={"codgeo": "dept"})
    return df


def load_sau() -> pd.DataFrame:
    df = _load_obs_terr_xlsx("sau2020_dep.xlsx", "sau2020", year=2020)
    df = df.rename(columns={"sau2020": "sau_ha"})
    df = unify_corsica(df, "dept", ["sau_ha"], {"sau_ha": "sum"})
    return df


def load_poverty(year: int = 2020) -> pd.DataFrame:
    df = _load_obs_terr_xlsx("poverty_tx_pauv_60_dep.xlsx", "tx_pauv_60", year=year)
    df = df.rename(columns={"tx_pauv_60": "poverty_rate"})
    df = unify_corsica(df, "dept", ["poverty_rate"], {"poverty_rate": "mean"})
    return df


def load_density(year: int = 2011) -> pd.DataFrame:
    df = _load_obs_terr_xlsx("density_dens_pop_dep.xlsx", "dens_pop", year=year)
    df = df.rename(columns={"dens_pop": "pop_density"})
    df = unify_corsica(df, "dept", ["pop_density"], {"pop_density": "mean"})
    return df
