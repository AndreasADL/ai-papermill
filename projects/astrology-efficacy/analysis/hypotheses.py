"""
hypotheses.py — The pre-registered astrological predictions, in executable form.

THIS MODULE IS THE HYPOTHESIS. It is frozen at GATE 1. Every mapping below is
traceable to a quoted passage of a named source; nothing here may be edited on the
basis of anything seen in the outcome data. Post-hoc changes make a result
exploratory and must be labelled so in every output.

PRIMARY SOURCE
--------------
Claudius Ptolemy, *Tetrabiblos* (2nd c. CE), Book IV Chapter 4, "Of the Quality of
Action" (Loeb/Robbins translation, via penelope.uchicago.edu).

Ptolemy names EXACTLY THREE planets as significators of occupation:

    "The quality of the action is to be discerned from the character of the three
     planets, Mars, Venus, and Mercury, and from that of the signs through which
     they happen to be passing."

This is why there is no Sun hypothesis in the confirmatory set (see DEVIATION note
at the bottom of this file). We test the three planets the source names, and no more.

Occupational significations, quoted verbatim:

  MERCURY: "scribes, men of business, calculators, teachers, merchants, bankers,
           soothsayers, astrologers, sacrificers, and in general those who perform
           their functions by means of documents, interpretation, and giving and
           taking."

  VENUS:   "persons whose activities lie among the perfumes of flowers or of
           unguents, in wine, colours, dyes, spices, or adornments, as, for example,
           sellers of unguents, weavers of chaplets, innkeepers, wine-merchants,
           druggists, weavers, dealers in spices, painters, dyers, sellers of
           clothing."

  MARS:    "those who use fire in their crafts, such as cooks, moulders, cauterizers,
           smiths, workers in mines; ... those who work with iron, such as
           shipbuilders, carpenters, farmers, quarrymen, stone-dressers, jewellers,
           splitters of wood, and their subordinate workers."

Note that the assignments are NOT the modern-intuitive ones. Ptolemy puts *cooks*,
*farmers* and *jewellers* under Mars, not Venus; *bankers* and *accountants* under
Mercury. We follow the text, not intuition -- that is the point of preregistration.

ESSENTIAL DIGNITY
-----------------
Domicile ("house") rulerships, *Tetrabiblos* I.17: each planet governs two signs,
one solar-side and one lunar-side. Detriment is the sign opposite the domicile.
These depend only on the planet's SIGN, which is why they are testable without a
birth time -- unlike Ptolemy's own "lord of action" procedure, which requires the
planet's morning appearance or culmination and therefore an unknown birth hour.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Essential dignity (Tetrabiblos I.17)
# ---------------------------------------------------------------------------
DOMICILE = {
    "mercury": ["Gemini", "Virgo"],
    "venus": ["Taurus", "Libra"],
    "mars": ["Aries", "Scorpio"],
}

DETRIMENT = {
    "mercury": ["Sagittarius", "Pisces"],
    "venus": ["Scorpio", "Aries"],
    "mars": ["Libra", "Taurus"],
}

# ---------------------------------------------------------------------------
# Occupation classes (Tetrabiblos IV.4)
# ---------------------------------------------------------------------------
# Matched case-insensitively as whole-word substrings against the English Wikidata
# P106 label. Keyword choice is deliberately conservative: each term is defensibly a
# modern instance of a category Ptolemy names. Terms that would be a stretch are
# omitted rather than argued for.

OCCUPATION_KEYWORDS: dict[str, list[str]] = {
    # "documents, interpretation, and giving and taking"
    "mercury": [
        "writer", "author", "journalist", "translator", "interpreter", "editor",
        "teacher", "lecturer", "professor", "educator", "tutor",
        "accountant", "banker", "merchant", "trader", "businessperson",
        "bookkeeper", "clerk", "scribe", "notary", "publisher", "librarian",
        "mathematician", "statistician", "economist", "astrologer",
        "linguist", "philologist", "lexicographer", "stenographer",
    ],
    # "perfumes ... wine, colours, dyes, spices, or adornments"
    "venus": [
        "painter", "dyer", "weaver", "textile", "tailor", "dressmaker",
        "fashion designer", "costume designer", "milliner", "couturier",
        "perfumer", "florist", "innkeeper", "restaurateur", "publican",
        "winemaker", "vintner", "sommelier", "brewer", "distiller",
        "cosmetologist", "hairdresser", "spice", "apothecary", "druggist",
    ],
    # "use fire in their crafts" / "work with iron"
    "mars": [
        "blacksmith", "smith", "metalworker", "ironworker", "farrier",
        "miner", "quarryman", "stonemason", "mason", "stonecutter",
        "cook", "chef", "baker", "butcher",
        "shipbuilder", "shipwright", "carpenter", "joiner", "woodworker",
        "farmer", "agriculturalist", "rancher", "forester", "logger",
        "jeweller", "jeweler", "goldsmith", "silversmith", "watchmaker",
        "foundry", "welder", "machinist", "gunsmith", "armourer", "armorer",
    ],
}

# Labels that a keyword would otherwise capture but which do not belong to the
# category. Matched as substrings (these are disqualifiers, so being liberal is safe).
#
# Word-boundary matching already removes the large class of accidental hits
# ("exaMINEr", "freeMASON", "deterMINEr"). What remains are genuine homographs,
# chiefly the French/organisational "chef" meaning chief rather than cook.
OCCUPATION_EXCLUSIONS: dict[str, list[str]] = {
    "mercury": [
        # "writer" occurs inside these, but they are performance/creative roles
        # that Ptolemy assigns elsewhere or not at all.
        "songwriter", "screenwriter", "playwright", "scriptwriter", "lyricist",
        "typewriter", "ghostwriter",
    ],
    "venus": [
        "painter-etcher",  # printmaking, nearer Mars's engraving crafts
    ],
    "mars": [
        "locksmith",        # ambiguous between iron-work and the security trade
        "wordsmith",
        "farm worker",      # a labourer, not the "farmer" Ptolemy names
        # "chef" as chief/head, not cook:
        "chef de", "chef d'", "chef superieur", "chef supérieur", "chef de mission",
        "sous chef de", "chef operator",
        # organisational/decorative uses of craft words:
        "master of the mint", "mine owner", "mining engineer",
    ],
}

# Labels that are not occupations at all. Wikidata P106 values include a handful of
# maintenance categories and disambiguation stubs.
STRUCTURAL_EXCLUSIONS = ("category:", "wikimedia", "list of", "template:",
                         "disambiguation")


def _compile(keywords: "list[str]"):
    import re
    # \b on both sides: "miner" must not match "examiner"; "mason" must not match
    # "freemason". Multi-word keywords ("fashion designer") work unchanged.
    return re.compile(
        r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b", re.IGNORECASE
    )


_PATTERNS = {p: _compile(kw) for p, kw in OCCUPATION_KEYWORDS.items()}


def build_occupation_classes(
    labels: "dict[str, str]", audit_path=None
) -> "dict[str, set[str]]":
    """
    Map Wikidata occupation QIDs to Ptolemaic planet classes.

    Uses WORD-BOUNDARY matching, not substring matching. Naive substring matching
    put "Certified Fraud Examiner" under Mars (via "miner") and "Chef de Mission"
    under Mars (via "chef") -- errors that would have silently corrupted the
    outcome variable.

    Parameters
    ----------
    labels : mapping of occupation QID -> English label
    audit_path : optional path; if given, every matched (planet, qid, label) triple
        is written there so the mapping can be inspected by hand. The mapping is the
        hypothesis, so it must be auditable.

    Returns
    -------
    mapping of planet -> set of occupation QIDs
    """
    out: dict[str, set[str]] = {p: set() for p in OCCUPATION_KEYWORDS}
    rows = []
    for qid, label in labels.items():
        if not isinstance(label, str):
            continue
        low = label.lower().strip()
        if any(s in low for s in STRUCTURAL_EXCLUSIONS):
            continue
        for planet, pattern in _PATTERNS.items():
            if any(bad in low for bad in OCCUPATION_EXCLUSIONS.get(planet, [])):
                continue
            m = pattern.search(low)
            if m:
                out[planet].add(qid)
                rows.append({"planet": planet, "occ_qid": qid,
                             "label": label, "matched_on": m.group(0)})
    if audit_path is not None:
        import pandas as pd

        (pd.DataFrame(rows)
           .sort_values(["planet", "matched_on", "label"])
           .to_csv(audit_path, index=False, encoding="utf-8"))
    return out


# ---------------------------------------------------------------------------
# Directional predictions
# ---------------------------------------------------------------------------
def predicted_direction(planet: str, cusp_from: str, cusp_to: str) -> int:
    """
    The pre-registered sign of the expected discontinuity at one cusp.

    Returns +1 if crossing this cusp moves the planet INTO a sign of its domicile
    (dignity rising -> its occupations should become MORE common), -1 if the
    crossing moves it OUT of domicile or INTO detriment, and 0 if the crossing is
    dignity-neutral (excluded from the primary pooled estimate).

    Signing each cusp by its predicted direction before looking at outcomes is what
    lets the 12 cutoffs be pooled into a single estimate without cancelling to zero.
    """
    dom = DOMICILE[planet]
    det = DETRIMENT[planet]

    into_dom = cusp_to in dom
    out_of_dom = cusp_from in dom
    into_det = cusp_to in det
    out_of_det = cusp_from in det

    score = 0
    if into_dom:
        score += 1
    if out_of_dom:
        score -= 1
    if into_det:
        score -= 1
    if out_of_det:
        score += 1

    return max(-1, min(1, score))


# ---------------------------------------------------------------------------
# Study 3 — Mayo, White & Eysenck (1978)
# ---------------------------------------------------------------------------
# "extraversion is related to being born under the odd numbered zodiacal signs,
#  and introversion to being born under the even numbered zodiacal signs"
# Mayo, J., White, O., & Eysenck, H. J. (1978). An empirical study of the relation
# between astrological factors and personality. J. Soc. Psych., 105, 229-236.

POSITIVE_SIGNS = ["Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"]
NEGATIVE_SIGNS = ["Taurus", "Cancer", "Virgo", "Scorpio", "Capricorn", "Pisces"]
WATER_SIGNS = ["Cancer", "Scorpio", "Pisces"]  # predicted higher emotionality

# GSS zodiac coding is 1=Aries .. 12=Pisces (verified in the cumulative codebook).
GSS_ZODIAC_CODES = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo",
    7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn",
    11: "Aquarius", 12: "Pisces",
}

# Pre-specified extraversion composite (GSS variable names).
GSS_SOCIABILITY_ITEMS = ["socfrend", "socommun", "socrel", "socbar"]


# ---------------------------------------------------------------------------
# DEVIATION FROM THE GATE 1 PLAN — logged, not silent
# ---------------------------------------------------------------------------
# The approved plan listed a fourth confirmatory hypothesis, H1-Su (Sun in Leo ->
# leadership occupations). On close reading of the primary source, Ptolemy names
# only THREE planets as significators of occupation -- "Mars, Venus, and Mercury" --
# and gives the Sun no occupational signification in IV.4 at all. H1-Su therefore had
# no basis in the cited source.
#
# Rather than substitute a weaker source to keep the count at four, H1-Su is DROPPED
# from the confirmatory family. The Sun-sign occupational analysis is retained as
# EXPLORATORY and must be labelled as such wherever it appears.
#
# Effect: the primary family shrinks from 8 tests to 7
# (3 Study 1 planets + 2 Study 2 flight outcomes + 2 Study 3 tests).
# This makes the test of astrology stricter on its own terms, not looser.
DROPPED_FROM_CONFIRMATORY = {
    "H1-Su": "Ptolemy IV.4 assigns occupation to Mars, Venus and Mercury only; "
             "the Sun has no occupational signification in the cited source. "
             "Retained as exploratory."
}
