"""CCF Recommended Conference/Journal Rankings for Computer Vision & AI.

CCF-A and CCF-B venues relevant to computer vision and image processing.
Only entries that overlap with the research topics this skill covers.
"""

# Venue name normalization: full name → standard abbreviation
VENUE_ALIASES = {
    # === CCF-A Conferences ===
    "computer vision and pattern recognition": "CVPR",
    "ieee/cvf conference on computer vision and pattern recognition": "CVPR",
    "ieee conference on computer vision and pattern recognition": "CVPR",
    "cvpr": "CVPR",
    "international conference on computer vision": "ICCV",
    "ieee international conference on computer vision": "ICCV",
    "iccv": "ICCV",
    "neural information processing systems": "NeurIPS",
    "advances in neural information processing systems": "NeurIPS",
    "neurips": "NeurIPS",
    "nips": "NeurIPS",
    "international conference on machine learning": "ICML",
    "icml": "ICML",
    "national conference on artificial intelligence": "AAAI",
    "aaai conference on artificial intelligence": "AAAI",
    "aaai": "AAAI",
    "international joint conference on artificial intelligence": "IJCAI",
    "ijcai": "IJCAI",
    "acm international conference on multimedia": "ACM MM",
    "acm multimedia": "ACM MM",
    "acm mm": "ACM MM",

    # === CCF-A Journals ===
    "ieee transactions on pattern analysis and machine intelligence": "IEEE TPAMI",
    "ieee trans. pattern anal. mach. intell.": "IEEE TPAMI",
    "tpami": "IEEE TPAMI",
    "international journal of computer vision": "IJCV",
    "ijcv": "IJCV",
    "ieee transactions on image processing": "IEEE TIP",
    "ieee trans. image process.": "IEEE TIP",
    "tip": "IEEE TIP",

    # === CCF-B Conferences ===
    "european conference on computer vision": "ECCV",
    "eccv": "ECCV",
    "ieee international conference on robotics and automation": "ICRA",
    "icra": "ICRA",
    "ieee international conference on image processing": "ICIP",
    "icip": "ICIP",
    "british machine vision conference": "BMVC",
    "bmvc": "BMVC",
    "international conference on 3d vision": "3DV",
    "3dv": "3DV",
    "int. conf. on 3d vision": "3DV",
    "intelligent robots and systems": "IROS",
    "ieee/rsj international conference on intelligent robots and systems": "IROS",
    "iros": "IROS",
    "international conference on acoustics, speech, and signal processing": "ICASSP",
    "icassp": "ICASSP",

    # === CCF-B Journals ===
    "ieee transactions on neural networks and learning systems": "IEEE TNNLS",
    "tnnls": "IEEE TNNLS",
    "computer vision and image understanding": "CVIU",
    "cviu": "CVIU",
    "ieee transactions on circuits and systems for video technology": "IEEE TCSVT",
    "t csvt": "IEEE TCSVT",
    "pattern recognition": "Pattern Recognition",
    "pattern recognit.": "Pattern Recognition",
    "ieee signal processing magazine": "IEEE SPM",
    "ieee transactions on visualization and computer graphics": "IEEE TVCG",
    "acm transactions on graphics": "ACM TOG",
}


def normalize_venue(raw_venue: str) -> str | None:
    """Normalize a raw venue string to a standard abbreviation."""
    if not raw_venue:
        return None
    normalized = raw_venue.strip().lower()
    # Remove trailing year like " (2024)" or "2024"
    normalized = normalized.rstrip("0123456789").rstrip(" (")
    normalized = normalized.strip()
    # Skip arXiv/CoRR — they are not real venues
    if normalized in ("corr", "arxiv", "computing research repository"):
        return None
    return VENUE_ALIASES.get(normalized, None)


# CCF-A venue abbreviations (normalized form)
CCF_A = {"CVPR", "ICCV", "NeurIPS", "ICML", "AAAI", "IJCAI", "ACM MM",
         "IEEE TPAMI", "IJCV", "IEEE TIP"}

# CCF-B venue abbreviations
CCF_B = {"ECCV", "ICRA", "ICIP", "BMVC", "3DV", "IROS", "ICASSP",
         "IEEE TNNLS", "CVIU", "IEEE TCSVT", "Pattern Recognition",
         "IEEE SPM", "IEEE TVCG", "ACM TOG"}

CCF_A_B = CCF_A | CCF_B


def is_ccf_a_b(venue_abbr: str) -> bool:
    """Check if a normalized venue abbreviation is CCF-A or CCF-B."""
    return venue_abbr in CCF_A_B


# Journal venues (as opposed to conferences) — for pre-print filtering
JOURNAL_VENUES = {"IEEE TPAMI", "IJCV", "IEEE TIP", "IEEE TNNLS", "CVIU",
                  "IEEE TCSVT", "Pattern Recognition", "IEEE SPM", "IEEE TVCG",
                  "ACM TOG"}
