---
name: literature-scan
description: Scan academic literature for a research question using free scholarly APIs (OpenAlex, Semantic Scholar, Crossref). Use at the start of any study, or when the user asks for related work, prior findings, or references.
---

# Literature Scan

Goal: a focused review of what is known about the research question, with verified references. Output goes to `literature/`.

## Procedure

1. **Derive 3–6 search queries** from the research question: synonyms, construct names, measurement instruments (e.g., "social media use depression", "screen time depressive symptoms adolescents").

2. **Query APIs** (all keyless; always include a mailto/User-Agent where supported; sleep ~1s between calls):

```python
import requests, time

# OpenAlex — best coverage + citation counts + open access links
r = requests.get("https://api.openalex.org/works",
    params={"search": QUERY, "per-page": 25, "sort": "cited_by_count:desc",
            "filter": "from_publication_date:2010-01-01",
            "mailto": "user@example.com"})
# fields: title, publication_year, cited_by_count, doi, abstract_inverted_index, authorships

# Semantic Scholar — good abstracts + TLDRs
r = requests.get("https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": QUERY, "limit": 20,
            "fields": "title,abstract,year,citationCount,externalIds,authors,venue"})

# Crossref — for verifying DOIs / metadata
r = requests.get("https://api.crossref.org/works", params={"query": QUERY, "rows": 10})
```

Note: OpenAlex returns abstracts as `abstract_inverted_index` — reconstruct by placing each word at its index positions.

3. **Select ~15–30 relevant papers.** Prioritize: meta-analyses and reviews first, then highly cited empirical studies, then recent (last 5 years) studies. Drop papers whose abstracts show they are off-topic.

4. **Write outputs:**
   - `literature/papers.json` — raw selected records (title, authors, year, venue, DOI, citations, abstract).
   - `literature/references.bib` — BibTeX for every selected paper. Fetch via content negotiation: `requests.get(f"https://doi.org/{doi}", headers={"Accept": "application/x-bibtex"})`. If a DOI fails to resolve, discard the reference — never hand-write BibTeX from memory.
   - `literature/lit_review.md` — structured review:
     - What is established (with effect size ranges if reported in abstracts)
     - Contested findings / heterogeneity
     - Common designs, measures, and typical confounders controlled for
     - Gaps the current study could address
     - Implications for our design (variables to include, expected effect direction/size)

## Rules
- Only cite papers found via the APIs. Every claim in `lit_review.md` needs an inline `[Author, Year, DOI]`.
- If abstracts are insufficient for a key paper, note that only the abstract was reviewed. Do not pretend to have read the full text.
- If the literature is thin (<5 relevant papers), say so — that itself is a finding.

## Verification
Before finishing: check `references.bib` parses (count `@` entries = papers.json entries) and spot-check 3 DOIs resolve (HTTP 200/302).
