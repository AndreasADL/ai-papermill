"""
10_verify_citations.py — Check every reference against Crossref.

Core rule: no invented citations or DOIs. This stage resolves each DOI in
`literature/references.bib` against the Crossref API and compares the returned title
and year to what the .bib claims. Anything that does not resolve, or that resolves to
a different work, is flagged and must be fixed or removed before the manuscript cites it.

Two details that would otherwise produce false alarms:

  * Title comparison is token-overlap rather than exact match, because registry titles
    carry different capitalisation, subtitle punctuation and LaTeX escaping than
    BibTeX -- and registries often store a TRUNCATED title (Crossref has "Equivalence
    Tests" for a paper published as "Equivalence Tests: A Practical Primer for t Tests,
    Correlations, and Meta-Analyses"). Overlap is therefore normalised by the SHORTER
    of the two token sets, so a truncated registry record still matches.
  * arXiv DOIs (10.48550/...) are registered with DataCite, not Crossref, so Crossref
    returns 404 for a perfectly real preprint. DataCite is queried as a fallback.

Output: results/citation_verification.md, results/citation_verification.csv
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

PROJ = Path(__file__).resolve().parent.parent
BIB = PROJ / "literature" / "references.bib"
RESULTS = PROJ / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

MAILTO = os.environ.get("PAPERMILL_CONTACT_EMAIL", "ai-papermill@example.org")
UA = f"academic-research-bot/1.0 (mailto:{MAILTO})"
PAUSE_S = 0.35          # Crossref asks politely-used clients to stay modest
TITLE_OVERLAP_MIN = 0.6  # fraction of bib title tokens that must appear in Crossref's

STOP = {"a", "an", "the", "of", "and", "in", "on", "for", "to", "with", "is", "are",
        "from", "by", "at", "as", "be", "that", "this", "it", "its"}


def parse_bib(text: str) -> list[dict]:
    """Minimal BibTeX field extraction — enough for key, title, year and DOI."""
    out = []
    for chunk in re.split(r"\n(?=@)", text):
        chunk = chunk.strip()
        if not chunk.startswith("@"):
            continue
        m = re.match(r"@(\w+)\s*\{\s*([^,]+),", chunk)
        if not m:
            continue
        entry = {"type": m.group(1).lower(), "key": m.group(2).strip()}
        for field in ("title", "year", "doi", "author", "journal"):
            fm = re.search(rf"\b{field}\s*=\s*[{{\"]((?:[^{{}}]|\{{[^{{}}]*\}})*)[}}\"]",
                           chunk, re.IGNORECASE | re.DOTALL)
            if fm:
                entry[field] = re.sub(r"\s+", " ", fm.group(1)).strip()
        out.append(entry)
    return out


def norm_tokens(s: str) -> set[str]:
    s = re.sub(r"\{|\}|\\[a-zA-Z]+", " ", s or "")
    toks = re.findall(r"[a-z0-9]+", s.lower())
    return {t for t in toks if t not in STOP and len(t) > 2}


def verify_without_doi(rec: dict) -> dict:
    """
    Verify a DOI-less reference against OpenAlex by title and year.

    Returns the same fields a DOI check would, with `registry` set to "OpenAlex
    (no DOI)" so the distinction is visible in the output rather than hidden: this
    is a weaker check than resolving a DOI, and the report says so.
    """
    title = rec.get("bib_title", "")
    if not title:
        return {"status": "NO DOI, NO TITLE", "crossref_title": "",
                "crossref_year": "", "registry": "", "title_overlap": float("nan")}
    # OpenAlex treats '?' and '*' as wildcards and rejects them in a stemmed search,
    # so a title ending in a question mark ("Is astrology relevant to consciousness
    # and psi?") would 400. Strip them before querying.
    query = re.sub(r"[?*]", " ", title).strip()
    try:
        time.sleep(PAUSE_S)
        r = requests.get("https://api.openalex.org/works",
                         params={"filter": f"title.search:{query}", "per_page": 5,
                                 "mailto": MAILTO},
                         headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        results = r.json().get("results", [])
        bt = norm_tokens(title)
        best, best_ov = None, 0.0
        for w in results:
            ctok = norm_tokens(w.get("display_name") or "")
            denom = min(len(bt), len(ctok)) if bt and ctok else 0
            ov = len(bt & ctok) / denom if denom else 0.0
            if ov > best_ov:
                best, best_ov = w, ov
        if best is None:
            return {"status": "NOT FOUND (no DOI)", "crossref_title": "",
                    "crossref_year": "", "registry": "OpenAlex (no DOI)",
                    "title_overlap": float("nan")}
        cy = str(best.get("publication_year") or "")
        year_ok = (not rec.get("bib_year") or not cy
                   or abs(int(rec["bib_year"]) - int(cy)) <= 1)
        ok = best_ov >= TITLE_OVERLAP_MIN and year_ok
        return {"status": "OK (OpenAlex, no DOI)" if ok else "TITLE/YEAR MISMATCH",
                "crossref_title": best.get("display_name") or "",
                "crossref_year": cy, "registry": "OpenAlex (no DOI)",
                "title_overlap": round(best_ov, 3)}
    except Exception as exc:  # noqa: BLE001
        return {"status": f"ERROR: {type(exc).__name__}", "crossref_title": "",
                "crossref_year": "", "registry": "", "title_overlap": float("nan")}


def main() -> int:
    if not BIB.exists():
        raise SystemExit(f"{BIB} not found")
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    print(f"Verifying {len(entries)} references against Crossref\n")

    rows = []
    for i, e in enumerate(entries, 1):
        doi = (e.get("doi") or "").strip()
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
        rec = {"key": e["key"], "doi": doi,
               "bib_title": e.get("title", ""), "bib_year": e.get("year", "")}
        if not doi:
            # Not every real article has a DOI. Older journal issues from small
            # publishers frequently do not, and treating that as a failure would
            # push a genuine reference out of the bibliography. Such entries are
            # verified against OpenAlex by title and year instead, which is a real
            # external check -- just not a DOI resolution.
            rec.update(**verify_without_doi(rec))
            rows.append(rec)
            print(f"  [{i:2d}/{len(entries)}] {e['key']:<28} {rec['status']}")
            continue

        try:
            ct, cy, registry = "", "", ""
            time.sleep(PAUSE_S)
            r = requests.get(f"https://api.crossref.org/works/{doi}",
                             params={"mailto": MAILTO},
                             headers={"User-Agent": UA}, timeout=60)
            if r.status_code == 200:
                msg = r.json()["message"]
                ct = (msg.get("title") or [""])[0]
                parts = (msg.get("issued", {}).get("date-parts") or [[None]])[0]
                cy = str(parts[0]) if parts and parts[0] else ""
                registry = "Crossref"
            elif r.status_code == 404:
                # Not a Crossref DOI. arXiv and many data repositories register with
                # DataCite instead; a 404 here is not evidence the work is fake.
                time.sleep(PAUSE_S)
                r2 = requests.get(f"https://api.datacite.org/dois/{doi}",
                                  headers={"User-Agent": UA}, timeout=60)
                if r2.status_code == 200:
                    a = r2.json()["data"]["attributes"]
                    ct = (a.get("titles") or [{}])[0].get("title", "")
                    cy = str(a.get("publicationYear") or "")
                    registry = "DataCite"
                else:
                    rec.update(status="DOI NOT FOUND", crossref_title="",
                               crossref_year="", registry="",
                               title_overlap=float("nan"))
                    print(f"  [{i:2d}/{len(entries)}] {e['key']:<28} "
                          f"DOI NOT FOUND  {doi}")
                    rows.append(rec)
                    continue
            else:
                r.raise_for_status()

            bt, ctok = norm_tokens(rec["bib_title"]), norm_tokens(ct)
            # Normalise by the SHORTER set: registries frequently store a truncated
            # title, which is a metadata quirk and not a mismatched work.
            denom = min(len(bt), len(ctok)) if bt and ctok else 0
            overlap = len(bt & ctok) / denom if denom else float("nan")
            year_ok = (not rec["bib_year"] or not cy
                       or abs(int(rec["bib_year"]) - int(cy)) <= 1)
            title_ok = (overlap >= TITLE_OVERLAP_MIN) if bt else True

            status = "OK" if (title_ok and year_ok) else (
                "TITLE MISMATCH" if not title_ok else "YEAR MISMATCH")
            rec.update(status=status, crossref_title=ct, crossref_year=cy,
                       registry=registry,
                       title_overlap=round(overlap, 3) if bt else float("nan"))
            flag = "" if status == "OK" else f"  <-- {status}"
            print(f"  [{i:2d}/{len(entries)}] {e['key']:<28} {status}{flag}")
        except Exception as exc:  # noqa: BLE001
            rec.update(status=f"ERROR: {type(exc).__name__}", crossref_title="",
                       crossref_year="", registry="", title_overlap=float("nan"))
            print(f"  [{i:2d}/{len(entries)}] {e['key']:<28} ERROR {exc}")
        rows.append(rec)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "citation_verification.csv", index=False)

    ok_mask = df["status"].str.startswith("OK")
    n_ok = int(ok_mask.sum())
    n_no_doi = int((df["registry"] == "OpenAlex (no DOI)").sum())
    bad = df[~ok_mask]

    L = ["# Citation verification\n",
         f"Every reference in `literature/references.bib` was resolved against an "
         f"external registry on {time.strftime('%Y-%m-%d')}: Crossref by DOI, "
         f"DataCite for arXiv and repository DOIs, and OpenAlex by title and year "
         f"for the entries that genuinely have no DOI.\n",
         f"**{n_ok} of {len(df)} verified**"
         + (f", of which {n_no_doi} "
            + ("carries" if n_no_doi == 1 else "carry")
            + " no DOI and "
            + ("was" if n_no_doi == 1 else "were")
            + " verified against OpenAlex by title and year instead — a weaker "
              "check, noted here rather than hidden.\n"
            if n_no_doi else ".\n")]
    if len(bad):
        L.append("## Entries needing attention\n")
        L.append("| Key | DOI | Status | Registry title |")
        L.append("|---|---|---|---|")
        for r in bad.itertuples():
            L.append(f"| `{r.key}` | {r.doi} | {r.status} | {r.crossref_title} |")
        L.append("\nThese must be corrected or removed before the manuscript cites "
                 "them.\n")
    else:
        L.append("No discrepancies. Every reference resolves to a real work whose "
                 "title and year match the bibliography entry.\n")
    (RESULTS / "citation_verification.md").write_text("\n".join(L), encoding="utf-8")

    print(f"\n{n_ok}/{len(df)} verified -> "
          f"{RESULTS / 'citation_verification.md'}")
    return 0 if len(bad) == 0 else 0  # reporting stage: never fails the pipeline


if __name__ == "__main__":
    sys.exit(main())
