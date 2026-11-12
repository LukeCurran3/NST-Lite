"""Parcel ID and street name helpers shared by search features."""

import re


STREET_SUFFIXES = {
    "AVE", "AVENUE", "ST", "STREET", "BLVD", "BOULEVARD", "RD", "ROAD",
    "DR", "DRIVE", "LN", "LANE", "CT", "COURT", "PL", "PLACE",
    "PKWY", "PARKWAY", "WAY", "CIR", "CIRCLE", "TER", "TERRACE",
    "TRAIL", "CRES", "CRESCENT", "HWY", "HIGHWAY",
}


def strip_suffix(query):
    """Drop a trailing street suffix token (e.g. "123 PEARL ST" -> "123 PEARL")."""
    tokens = query.upper().split()
    if len(tokens) > 1 and tokens[-1] in STREET_SUFFIXES:
        return " ".join(query.split()[:-1])
    return query


def normalize_parcel(s):
    """If s looks like a dashless parcel (8 digits), reformat as NNN-NN-NNN. Else None."""
    digits = re.sub(r'\D', '', s)
    if len(digits) == 8:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return None
