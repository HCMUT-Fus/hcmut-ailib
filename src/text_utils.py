"""Text utilities for Vietnamese language handling, accent removal and author names."""

from __future__ import annotations

import unicodedata

# 35 most common Vietnamese family names (both with and without diacritics)
VIETNAMESE_SURNAMES = frozenset([
    "nguyen", "tran", "le", "pham", "hoang", "huynh", "phan", "vu", "vo", "dang",
    "bui", "do", "ho", "ngo", "duong", "ly", "dinh", "doan", "lam", "trinh",
    "mai", "dao", "cao", "ha", "luong", "thai", "chau", "ta", "phung", "quach",
    "to", "luu", "vuong", "tang", "truong", "mac", "giap", "chu",
])


def strip_accents(text: str) -> str:
    """Remove Vietnamese accents and diacritics, returning lowercase ASCII text.

    Examples:
        >>> strip_accents("Nguyễn Văn An")
        'nguyen van an'
        >>> strip_accents("Đỗ Đình Đồng")
        'do dinh dong'
    """
    if not text:
        return ""
    # Explicitly map Vietnamese 'đ' / 'Đ' before decomposing
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def is_vietnamese_surname(token: str) -> bool:
    """Check if the given word corresponds to a common Vietnamese surname."""
    return strip_accents(token) in VIETNAMESE_SURNAMES
