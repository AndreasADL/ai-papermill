"""
01_clean.py

Builds the primary analysis dataset (department grain, mainland France) by merging:
  - outcome: age-standardized female breast cancer mortality rate, 2007-2014 (Odisse)
  - exposure: BNV-D pesticide sales (active substance, kg), summed 2008-2014,
    normalized by Agreste RA2020 SAU (hectares) -> kg/ha/year
  - confounders: poverty rate (FiLoSoFi, 2020 vintage) and population density
    (INSEE, 2011 vintage)

Applies plan.md SS2's inclusion/exclusion criteria (mainland only, exclude DOM,
exclude suppressed/missing), builds the exact variables specified in plan.md SS2
(log pesticide intensity, poverty rate %, log population density), asserts expected
ranges/dtypes (fail loudly on violations), and logs every row-count change to
results/sample_flow.md (assembled into results/results.md by run_all.py at the end
of the pipeline).

Output: data/processed/analysis_df.parquet
"""

import numpy as np
import pandas as pd

from _common import (
    PROCESSED,
    RESULTS,
    load_bnvd_vente_totals,
    load_density,
    load_mortality,
    load_poverty,
    load_sau,
)

SEED = 42
np.random.seed(SEED)

VENTE_YEARS_PRIMARY = [2008, 2009, 2010, 2011, 2012, 2013, 2014]
POVERTY_YEAR = 2020
DENSITY_YEAR = 2011

log_lines = []


def log(msg: str):
    print(msg)
    log_lines.append(msg)


def main():
    log("# Sample flow — 01_clean.py\n")
    log(f"Run parameters: SEED={SEED}, sales years={VENTE_YEARS_PRIMARY}, "
        f"poverty vintage={POVERTY_YEAR}, density vintage={DENSITY_YEAR}.\n")

    # -- 1. Outcome --------------------------------------------------------
    mortality = load_mortality()
    n0 = len(mortality)
    log(f"1. Outcome (Odisse mortality, Femmes/Mortalité/Sein, 2007-2014): "
        f"N = {n0} (all departments incl. DOM).")

    mortality_mainland = mortality[~mortality["is_dom"]].drop(columns=["is_dom"])
    n1 = len(mortality_mainland)
    log(f"   -> after excluding DOM (mainland-only inclusion criterion): N = {n1} "
        f"(dropped {n0 - n1}).")
    assert n1 == 95, f"expected 95 mainland departments (01-95, Corsica unified as 20), got {n1}"

    # -- 2. Exposure ---------------------------------------------------------
    vente = load_bnvd_vente_totals(VENTE_YEARS_PRIMARY)
    log(f"\n2. Exposure (BNV-D VENTE_DPT_SUBSTANCE, summed {VENTE_YEARS_PRIMARY[0]}-"
        f"{VENTE_YEARS_PRIMARY[-1]}, mainland only, Corsica 2A+2B summed to '20'): "
        f"N = {len(vente)} departments with at least one non-suppressed sales record.")
    missing_vente = set(mortality_mainland["dept"]) - set(vente["dept"])
    if missing_vente:
        log(f"   -> departments with NO sales record at all across "
            f"{VENTE_YEARS_PRIMARY}: {sorted(missing_vente)} "
            f"(would indicate full-department suppression; none expected per "
            f"provenance check).")
    else:
        log("   -> every mainland department has at least one non-suppressed sales "
            "record across 2008-2014 (no full-department suppression found).")

    # -- 3. Normalizer -------------------------------------------------------
    sau = load_sau()
    log(f"\n3. Normalizer (Agreste RA2020 SAU, mainland, Corsica summed): "
        f"N = {len(sau)} departments.")

    # -- 4. Confounders --------------------------------------------------------
    poverty = load_poverty(POVERTY_YEAR)
    log(f"\n4a. Confounder (FiLoSoFi poverty rate, vintage {POVERTY_YEAR}, mainland, "
        f"Corsica averaged): N = {len(poverty)} departments.")

    density = load_density(DENSITY_YEAR)
    log(f"4b. Confounder (INSEE population density, vintage {DENSITY_YEAR}, mainland, "
        f"Corsica averaged): N = {len(density)} departments.")

    # -- 5. Merge --------------------------------------------------------------
    df = mortality_mainland.merge(vente, on="dept", how="left")
    log(f"\n5. Merge outcome + exposure: N = {len(df)} "
        f"(left join on mortality mainland N={n1}; "
        f"{df['pesticide_kg_total'].isna().sum()} unmatched on exposure).")

    df = df.merge(sau, on="dept", how="left")
    log(f"   + SAU: N = {len(df)} ({df['sau_ha'].isna().sum()} unmatched on SAU).")

    df = df.merge(poverty, on="dept", how="left")
    log(f"   + poverty rate: N = {len(df)} "
        f"({df['poverty_rate'].isna().sum()} unmatched on poverty).")

    df = df.merge(density, on="dept", how="left")
    log(f"   + population density: N = {len(df)} "
        f"({df['pop_density'].isna().sum()} unmatched on density).")

    # -- 5b. Non-agricultural SAU-denominator exclusion (DEVIATION, logged) -----
    # Discovered when building pesticide_intensity: SAU for depts 75 (Paris, 1 ha),
    # 92 (Hauts-de-Seine, 5 ha), 93 (Seine-Saint-Denis, 526 ha) and 94 (Val-de-Marne,
    # 1,039 ha) is near zero (these are the fully urbanized inner Paris ring, with
    # essentially no farmland), while BNV-D still records nonzero distributor sales
    # there (consistent with the documented sales-recorded-at-distributor's-department
    # caveat in data/candidates.md — national wholesalers/distributor head offices are
    # disproportionately located in the Paris region). Dividing by near-zero SAU
    # produces implausible "intensity" values (up to ~21,000 kg/ha/year, vs. a next-
    # highest value of ~19.8 kg/ha/year for a genuine agricultural department) that
    # are pure denominator artifacts, not agricultural intensity. There is a clean,
    # large natural gap in the SAU distribution (1 / 5 / 526 / 1,039 ha for these four
    # vs. 19,689 ha for the next-smallest, genuinely rural, department), so a fixed
    # SAU < 10,000 ha threshold — chosen from this gap, without reference to outcome
    # values (the filter below reads only sau_ha, never mortality_rate_std, though
    # the outcome column is already merged into `df` by this point in the script) —
    # identifies exactly these four departments and nothing else. This is
    # a plan.md SS2 deviation (the plan only anticipated "suppressed/missing" BNV-D
    # exclusions, not non-agricultural-denominator artifacts) and is logged in
    # plan.md's Deviations section and results.md accordingly.
    nonag = df[df["sau_ha"] < 10_000]
    if not nonag.empty:
        log(f"\n5b. DEVIATION: excluding {len(nonag)} department(s) with SAU < 10,000 ha "
            f"(non-agricultural denominator, sales-location artifact — see plan.md "
            f"Deviations): "
            f"{nonag[['dept', 'dept_name', 'sau_ha']].to_dict('records')}.")
        df = df[df["sau_ha"] >= 10_000].copy()
        log(f"    -> N = {len(df)} after this exclusion.")

    # -- 6. Missing-data assessment (plan.md SS3) -------------------------------
    key_cols = ["mortality_rate_std", "pesticide_kg_total", "sau_ha", "poverty_rate", "pop_density"]
    missing_mask = df[key_cols].isna().any(axis=1)
    n_missing = int(missing_mask.sum())
    pct_missing = 100 * n_missing / len(df)
    log(f"\n6. Missing-data check across the four analysis variables (outcome, "
        f"exposure/normalizer, poverty, density): {n_missing}/{len(df)} departments "
        f"({pct_missing:.1f}%) have at least one missing value.")
    if n_missing > 0:
        log(f"   Departments with missing data: "
            f"{df.loc[missing_mask, ['dept', 'dept_name']].to_dict('records')}")
    if pct_missing < 5:
        log("   Missingness < 5% threshold (plan.md SS3): complete-case analysis used, "
            "excluded departments listed above/below.")
    else:
        log("   Missingness >= 5% threshold (plan.md SS3): flagging for the "
            "MAR-vs-MNAR comparison specified in the plan (surfaced at GATE 2, "
            "not resolved silently here).")

    df_complete = df.loc[~missing_mask].copy()
    n_final_precheck = len(df_complete)
    log(f"\n7. Complete-case dataset: N = {n_final_precheck}.")

    # -- 8. Build analysis variables (plan.md SS2) ------------------------------
    df_complete["pesticide_intensity"] = (
        df_complete["pesticide_kg_total"] / len(VENTE_YEARS_PRIMARY) / df_complete["sau_ha"]
    )
    df_complete["log_pesticide_intensity"] = np.log(df_complete["pesticide_intensity"])
    df_complete["log_pop_density"] = np.log(df_complete["pop_density"])

    # -- 9. Assertions: dtypes and expected ranges (fail loudly) ----------------
    checks = {
        "mortality_rate_std": (0, 60),          # per 100,000, age-standardized
        "pesticide_intensity": (0, 200),        # kg active substance / ha / year
        "poverty_rate": (0, 100),               # %
        "pop_density": (0, 25000),               # inhab/km2
    }
    for col, (lo, hi) in checks.items():
        assert df_complete[col].dtype.kind in "fi", f"{col} is not numeric: {df_complete[col].dtype}"
        bad = df_complete[(df_complete[col] < lo) | (df_complete[col] > hi)]
        assert bad.empty, (
            f"{col} has {len(bad)} values outside expected range [{lo}, {hi}]: "
            f"{bad[['dept', col]].to_dict('records')}"
        )
    assert df_complete["dept"].is_unique, "duplicate department codes in final dataset"
    log(f"\n8. Range/dtype assertions passed for: {list(checks.keys())}.")

    # -- 10. Save -----------------------------------------------------------
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED / "analysis_df.parquet"
    keep_cols = [
        "dept", "dept_name",
        "mortality_rate_std", "mortality_low", "mortality_up",
        "pesticide_kg_total", "pesticide_intensity", "log_pesticide_intensity",
        "sau_ha",
        "poverty_rate",
        "pop_density", "log_pop_density",
    ]
    df_complete[keep_cols].to_parquet(out_path, index=False)
    log(f"\n9. FINAL analysis dataset saved to {out_path.relative_to(PROCESSED.parent.parent)}: "
        f"N = {len(df_complete)} mainland departments.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "sample_flow.md").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\n[ok] wrote {RESULTS / 'sample_flow.md'}")


if __name__ == "__main__":
    main()
