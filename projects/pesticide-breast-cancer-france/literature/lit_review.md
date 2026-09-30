# Literature Review: Pesticide Use and Female Breast Cancer Mortality — Department-Level, Mainland France

Scan date: 2026-08-08. Sources: OpenAlex, Semantic Scholar, Crossref (all keyless APIs). 28 papers selected
and verified (title/venue/year/DOI cross-checked against Crossref and/or Semantic Scholar records; every DOI
below resolves — confirmed via Crossref lookup and, for a spot-check subset, via HTTP redirect from
`doi.org`). Full records: `literature/papers.json`; citations: `literature/references.bib`.

**Important caveat on this scan's process**: the automated search/summarization step (via a web-fetch tool)
was unreliable on first pass — several early API calls returned generic, high-citation but topically
irrelevant papers (e.g., Global Burden of Disease reports, heavy-metal toxicology reviews) that appear to
have been substituted by the summarizing layer rather than genuinely returned by the query. One entry
("Tranexamic acid for traumatic brain injury", claimed DOI `10.1016/s0140-6736`) was caught and discarded
specifically because the DOI was incomplete/malformed and unrelated to the query. Every paper kept below was
individually re-verified with a direct Crossref `works/{doi}` lookup (a small, deterministic response, much
less prone to this failure mode) before inclusion. Readers should treat this scan as a solid but not
exhaustive sample of the literature, assembled with an extra verification pass precisely because of this
observed unreliability.

## 1. What is established

**Individual-level (biomarker) studies of organochlorine pesticides and breast cancer show a real, but
modest and inconsistent, positive association, concentrated in DDT/DDE.** The most current and
methodologically careful synthesis found is a 2024 systematic review and meta-analysis of serum/adipose DDT
metabolite concentrations and female breast cancer [Ugalde-Resano et al., 2024, 10.1515/reveh-2024-0021]:
prospective nested case-control studies with >10 years of follow-up showed p,p′-DDT summary OR = 1.41 (95%
CI 1.06–1.88); retrospective case-control studies showed p,p′-DDE sOR = 1.15 (95% CI 1.02–1.30) and, at high
serum concentrations (>100 ng/g), p,p′-DDT sOR = 1.33 (95% CI 1.25–1.41); o,p′-DDT showed a larger sOR = 2.24
(95% CI 2.15–2.34). These are individual-level, biomarker-based effect sizes — not directly transferable to
an ecological (area-level use intensity) design, but they set a plausible upper bound for what a true
underlying association might look like if fully captured.

A broader review of environmental chemicals and breast cancer [Rodgers et al., 2018, 10.1016/j.envres.2017.08.045]
reports comparable risk-estimate ranges (2.14–5.0) for DDT, dioxins, PFOSA, and air pollution specifically
when exposure occurred during biologically sensitive windows of breast development (in utero, puberty,
pregnancy) — and emphasizes that most epidemiological studies do *not* capture exposure timing, which is a
major source of heterogeneity in the literature.

The mechanistic case for a pesticide–breast-cancer link rests on the xenoestrogen hypothesis: several
organochlorines, PAHs, and triazine herbicides are estrogenically active and induce mammary carcinogenesis
experimentally, and established individual risk factors explain at best ~30% of breast cancer cases [Davis,
Bradlow & Wolff, 1993, 10.1289/ehp.93101372]. A broader review of pesticide exposure and cancer burden
generally (not breast-specific) concludes that epidemiological and molecular evidence supports excess cancer
risk among pesticide applicators and others exposed [Alavanja, Ross & Bonner, 2013, 10.3322/caac.21170].

## 2. Contested findings / heterogeneity

The literature is genuinely mixed, and this matters directly for expectation-setting on our study:

- A classic review of DDT/DDE/dieldrin and breast cancer found that **early descriptive studies and one
  cohort study showed a strong positive association, but most later case-control and nested case-control
  studies did not replicate it** [Snedeker, 2001, 10.1289/ehp.01109s135].
- A large NHANES-based cross-sectional study found **no association between serum organochlorine pesticide
  concentrations and breast cancer prevalence** (while finding significant associations for prostate cancer)
  [Xu et al., 2009, 10.1289/ehp.0900919].
- Most importantly for our design: the one study in this scan closest in spirit to an area/exposure-proxy
  design — GIS-based residential proximity to agricultural pesticide applications in the California Teachers
  Study cohort (114,835 women, 1,552 incident cases) — **found no association** between proximity-based
  pesticide exposure and breast cancer incidence, across probable/likely carcinogens (HR 1.07, 95% CI
  0.86–1.32), mammary carcinogens (HR 1.15, 95% CI 0.90–1.48), and endocrine disruptors (HR 1.03, 95% CI
  0.86–1.25), with no dose-response trend [Reynolds et al., 2004, 10.1016/j.envres.2004.03.001].
- A large prospective cohort of licensed pesticide applicators found **no association between glyphosate use
  and cancer overall**, with only a non-statistically-significant elevated signal for acute myeloid leukemia
  at the highest exposure level [Andreotti et al., 2018, 10.1093/jnci/djx233].

Taken together: biomarker-based (internal dose) studies show weak-to-moderate positive associations for
some DDT-family compounds under some designs; area- or proximity-based exposure-proxy studies — the design
family our study belongs to — have tended to find null results. This is an important, sobering prior for
our department-level analysis.

## 3. Common designs, measures, and typical confounders controlled for

- **Exposure measures used in the literature**: serum/adipose organochlorine concentrations (most common in
  breast-cancer-specific studies); GIS-based residential proximity to reported pesticide applications
  (California); self-reported lifetime pesticide-use days combined with a crop-exposure matrix (AGRICAN's
  PESTIMAT, France) [Piel et al., 2019, 10.1016/j.envint.2019.05.070; Pouchieu et al., 2018, 10.1093/ije/dyx225].
  We found **no prior study using aggregate department-level pesticide sales data (BNVD-type) as an exposure
  proxy for any cancer outcome**; the only France-specific paper on spatializing pesticide sales data
  addresses methodology for environmental-policy monitoring, not health outcomes [Martin et al., 2023,
  10.1016/j.jclepro.2023.136880].
- **Typical confounders adjusted for**: age (via standardization or as a covariate), race/ethnicity,
  socioeconomic status/deprivation, menopausal status, family history, reproductive history, and — in the
  California and AGRICAN studies — education and smoking. County/area-level US studies confirm that
  **socioeconomic deprivation and rural-urban/urbanization status are independently associated with cancer
  mortality, with deprivation showing the stronger effect and steeper socioeconomic gradients in
  non-metropolitan areas** [Singh et al., 2011, 10.1155/2011/107497] — directly supporting the plan to
  include both deprivation and urbanization/density as separate, non-collapsed confounders.
- **Spatial/ecological methodology**: small-area cancer analyses face a large random component in rates
  (addressable via Bayesian smoothing), reduced power to detect small-area effects, and confounding
  particularly by socioeconomic factors [Elliott & Wartenberg, 2004, 10.1289/ehp.6735]. An empirical example
  from Saudi Arabia found **statistically significant positive spatial autocorrelation (Moran's I) for
  female breast cancer incidence at the city level**, i.e., breast cancer rates cluster geographically
  [Al-Ahmadi & Al-Zahrani, 2013, 10.3390/ijerph10127207] — a strong methodological argument for testing and,
  if present, modeling spatial autocorrelation in our department-level regression rather than relying on
  naive OLS with independent errors.
- **Ecological fallacy**: the standard caution is that individual-level and ecological-level associations can
  diverge and area-level correlations cannot support individual-causal claims [Loney & Nagelkerke, 2014,
  10.1186/1742-7622-11-18; Blakely & Woodward, 2000, 10.1136/jech.54.5.367]. A widely cited critical review
  further found that **contextual (area-level) effects on health outcomes are generally modest relative to
  compositional (individual-level) effects** [Pickett & Pearl, 2001, 10.1136/jech.55.2.111] — another reason
  to expect a modest ecological signal even if an individual-level relationship exists.

## 4. French-specific literature found

This is where the literature is thinnest, and that thinness is itself a finding.

- **No study was found linking mainland-France department-level agricultural pesticide use/sales to breast
  cancer incidence or mortality.** This appears to be a genuine gap, not just a search-coverage artifact —
  multiple query variants (pesticide + breast cancer + France; BNVD; department-level ecological pesticide
  cancer) turned up either off-topic results or the adjacent literature described below.
- The **AGRICAN cohort** (French agricultural workers, ~182,000 participants, individual-level exposure via
  the PESTIMAT crop-exposure matrix) has produced pesticide-cancer findings for central nervous system tumors
  [Piel et al., 2019, 10.1016/j.envint.2019.05.070] and Parkinson's disease [Pouchieu et al., 2018,
  10.1093/ije/dyx225], but no AGRICAN breast-cancer paper surfaced in this scan.
- **Chlordecone in Martinique/Guadeloupe** (French overseas territories, not mainland France) is the
  best-documented pesticide-cancer story involving French populations, but the outcome is **prostate**
  cancer, not breast cancer [Multigner et al., 2010, 10.1200/jco.2009.27.2153; Multigner et al., 2015,
  10.1007/s11356-015-4621-5]. A mechanistic review argues chlordecone and other organochlorines could
  plausibly drive both prostate and breast cancer via shared estrogenic pathways [Landau-Ossondo et al.,
  2009, 10.1016/j.biopha.2009.04.043], but this is a hypothesis paper about a different (legacy,
  organochlorine-specific, overseas-territory) exposure context, not direct evidence for mainland
  agricultural-sales-based exposure.
- **CONSTANCES**, a large general-purpose French cohort with occupational/environmental focus and mortality
  linkage, exists as potential future individual-level infrastructure but was not used in any
  pesticide-breast-cancer study identified here [Goldberg et al., 2016, 10.1136/oemed-2016-103678].
- One paper directly addresses **modelling the spatialisation of French pesticide sales data** for
  environmental-policy monitoring, confirming BNVD-type data has been used for department/commune-level
  spatial modeling in France — but for environmental, not health, outcomes [Martin et al., 2023,
  10.1016/j.jclepro.2023.136880].

**Bottom line: no prior ecological or individual-level study was found that directly parallels our planned
analysis (mainland France, department-level, agricultural pesticide sales/use vs. female breast cancer
mortality).** This should be stated plainly in the study's framing as both a gap the study addresses and a
reason to keep expectations about effect size modest and language strictly associational.

## 5. Gaps this study could address

- No department-level ecological analysis of pesticide use and breast cancer mortality exists for mainland
  France, despite BNVD sales data and CépiDc mortality data both existing at that level.
- No study in this scan combines a department-level pesticide exposure proxy with *both* a deprivation index
  *and* an urbanization/density measure as co-adjusted confounders for breast cancer specifically — the
  county-level US literature does this for cancer generally [Singh et al., 2011, 10.1155/2011/107497] but not
  for pesticide exposure specifically.
- Spatial autocorrelation of breast cancer rates has been demonstrated elsewhere [Al-Ahmadi & Al-Zahrani,
  2013] but not tested in a French department-level pesticide context.

## 6. Implications for our design

1. **Set modest effect-size expectations, and treat a null finding as informative, not a failure.** The
   closest methodological analog to our ecological design (residential-proximity/area-based pesticide
   exposure, not biomarkers) found null results in a large, well-powered cohort [Reynolds et al., 2004].
   Individual-level biomarker meta-analyses show real but modest associations (sOR ≈ 1.15–2.24 depending on
   compound and study design) [Ugalde-Resano et al., 2024]. A department-level ecological analysis, several
   steps further removed from individual dose, should be expected to detect an attenuated signal at best.
2. **Include socioeconomic deprivation and urbanization/density as separate, co-adjusted confounders**, as
   currently planned — supported directly by evidence that both are independently associated with cancer
   mortality, with deprivation the stronger driver and gradients steeper in rural areas [Singh et al., 2011].
   Since agricultural pesticide-use intensity likely correlates with rurality, and rurality correlates with
   both deprivation and screening access, failing to separate these will risk confounding by the urban-rural
   gradient rather than a pesticide-specific effect.
3. **Explicitly test for and, if present, model spatial autocorrelation** (e.g., Moran's I on regression
   residuals; spatial-lag/error models or at minimum spatially-robust/cluster standard errors) rather than
   assuming independent errors across departments — supported by direct evidence of breast-cancer spatial
   clustering elsewhere [Al-Ahmadi & Al-Zahrani, 2013] and general small-area epidemiology guidance [Elliott
   & Wartenberg, 2004].
4. **State the latency/exposure-timing limitation explicitly.** Several key findings (DDT-family effects,
   window-of-susceptibility findings) depend on exposure timing decades before diagnosis, often during
   in-utero, pubertal, or pregnancy windows [Rodgers et al., 2018]. Current/recent-year BNVD sales data cannot
   capture this; the study should frame current pesticide-use intensity as a proxy for a department's
   longer-run agricultural-exposure profile, not a measure of the biologically relevant exposure window, and
   flag this as a limitation on interpretation (in addition to the already-planned ecological-fallacy caveat).
5. **Keep language strictly associational throughout** — reinforced by the ecological-fallacy methodology
   literature [Loney & Nagelkerke, 2014; Blakely & Woodward, 2000] and by the finding that contextual
   (area-level) effects are usually modest relative to individual-level/compositional effects [Pickett &
   Pearl, 2001], which further argues against any causal over-interpretation of a department-level
   correlation.

## Verification notes

- 28 papers selected (within the skill's 15–30 target range).
- 1 candidate dropped because its DOI (`10.7916/d8k35sd4`) returned HTTP 404 on Crossref lookup — never
  included in outputs.
- 1 candidate dropped mid-scan because it was a clear hallucination/tool artifact (fabricated/truncated DOI,
  off-topic title) — never included in outputs.
- Every included paper's title/venue/year/author(s) was independently re-verified via a direct
  `api.crossref.org/works/{doi}` lookup; a subset was additionally spot-checked via `doi.org/{doi}` HTTP
  redirect (all returned 302 to a live publisher page: EHP/ACS, Springer, Elsevier ScienceDirect, JNCI/OUP,
  SAGE, JCO — confirmed for `10.1289/ehp.0900919`, `10.1023/a:1008824131727`, `10.1016/j.scitotenv.2015.03.045`,
  `10.1289/ehp.01109s135`, `10.1093/jnci/92.9.750`, `10.1177/1010428317699114`).
- `references.bib` count of `@article{` entries = 28 = `papers.json` array length.
- Where an abstract was not returned by either API (Crossref or Semantic Scholar), the paper is retained with
  title/venue/year/DOI only, and `papers.json` flags it with a `note` field stating the abstract was
  unavailable — no abstract content was invented for these entries.
