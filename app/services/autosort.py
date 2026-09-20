"""Auto-sort foto ke kategori berdasarkan konvensi nama file / subfolder.

Cocokkan kata kunci (dari settings ``photo_categories``) terhadap nama file dan
nama folder asal. Kategori pertama yang cocok menang. Tidak cocok => 'uncategorized'.
"""
from __future__ import annotations

import re
from typing import Iterable

_norm_re = re.compile(r"[^a-z0-9]+")


def _normalize(text: str) -> str:
    return _norm_re.sub(" ", (text or "").lower()).strip()


def match_category(
    filename: str,
    categories: Iterable[dict],
    folder: str = "",
) -> tuple[str, str]:
    """Kembalikan (category_key, matched_by).

    matched_by: 'folder' | 'filename' | '' (tak cocok).
    Folder diprioritaskan agar penempatan per-subfolder lebih kuat.
    """
    fname = _normalize(filename)
    fdir = _normalize(folder)

    # 1) cocokkan berdasar folder dulu
    for cat in categories:
        for kw in cat.get("keywords", []):
            k = _normalize(kw)
            if k and k in fdir:
                return cat["key"], "folder"
    # 2) lalu nama file
    for cat in categories:
        for kw in cat.get("keywords", []):
            k = _normalize(kw)
            if k and k in fname:
                return cat["key"], "filename"
    return "uncategorized", ""


def category_needs_ocr(category_key: str, categories: Iterable[dict]) -> bool:
    for cat in categories:
        if cat["key"] == category_key:
            return bool(cat.get("ocr"))
    return False
