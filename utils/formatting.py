"""Value formatters for UI display. Handle nulls, bad types, and placeholder values."""

import pandas as pd


def fmt_money(v):
    try:
        return f"${int(float(v)):,}" if pd.notna(v) and float(v) > 0 else "N/A"
    except (TypeError, ValueError):
        return "N/A"


def fmt_text(v, default="-"):
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan"):
        return default
    return str(v).strip()


def fmt_year(v):
    try:
        y = int(float(v))
        return str(y) if 1700 < y < 9999 else "-"
    except (TypeError, ValueError):
        return "-"


def fmt_int(val, prefix="", suffix="", na="N/A"):
    """Format a numeric value as a comma-separated integer with optional prefix/suffix."""
    if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() in ("", "nan", "None"):
        return na
    try:
        return f"{prefix}{int(float(val)):,}{suffix}"
    except (ValueError, TypeError):
        return na


def fmt_val(val, prefix="", suffix="", na="N/A"):
    """Pass-through formatter with null handling and optional prefix/suffix."""
    if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() in ("", "nan", "None"):
        return na
    return f"{prefix}{val}{suffix}"


def flag_yn(v):
    """Returns 'Yes' if v is truthy (1), else 'No'. For plain text display."""
    try:
        return "Yes" if int(float(v)) == 1 else "No"
    except (TypeError, ValueError):
        return "No"


def flag_yn_colored(val):
    """Returns colored HTML Yes/No for use inside unsafe_allow_html markdown."""
    try:
        v = int(float(val))
        return (
            '<span style="color:#c0392b;font-weight:600;">Yes</span>'
            if v == 1
            else '<span style="color:#1e8449;font-weight:600;">No</span>'
        )
    except (ValueError, TypeError):
        return fmt_val(val)
