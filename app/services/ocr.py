"""Wrapper OCR (Tesseract via pytesseract) dengan degradasi anggun.

Jika Tesseract/pytesseract/Pillow tidak tersedia, fungsi mengembalikan hasil
kosong dan ``available()`` bernilai False — app tetap jalan (OCR opsional).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

try:
    import pytesseract
    from PIL import Image, ImageOps, ImageFilter
    _IMPORT_OK = True
except Exception:  # pragma: no cover
    _IMPORT_OK = False


def _configure_tesseract() -> None:
    """Cari binary Tesseract secara portabel (tanpa install admin).

    Prioritas: env REZA_BAA_TESSERACT > folder ``tesseract/`` di samping exe/app
    > biarkan PATH sistem yang menentukan.
    """
    if not _IMPORT_OK:
        return
    from .. import config
    candidates = []
    env = os.environ.get("REZA_BAA_TESSERACT")
    if env:
        candidates.append(Path(env))
    for name in ("tesseract.exe", "tesseract"):
        candidates.append(config.BASE_DIR / "tesseract" / name)
    for cand in candidates:
        if cand and cand.exists():
            pytesseract.pytesseract.tesseract_cmd = str(cand)
            return


if _IMPORT_OK:
    _configure_tesseract()

# Pola serial: token alfanumerik cukup panjang, boleh mengandung - .
_SERIAL_RE = re.compile(r"\b[A-Z0-9][A-Z0-9\-\.]{5,}[A-Z0-9]\b")


def available() -> bool:
    if not _IMPORT_OK:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _preprocess(img):
    """Grayscale + autokontras + upscale ringan untuk teks serial."""
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    w, h = img.size
    if max(w, h) < 1600:
        scale = 1600 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    img = img.filter(ImageFilter.SHARPEN)
    return img


def read_text(image_path: str | Path) -> str:
    if not available():
        return ""
    try:
        with Image.open(image_path) as img:
            proc = _preprocess(img)
            return pytesseract.image_to_string(proc) or ""
    except Exception:
        return ""


def extract_serial(text: str) -> str:
    """Ambil kandidat serial terbaik: token dengan campuran huruf+angka & terpanjang."""
    if not text:
        return ""
    candidates = _SERIAL_RE.findall(text.upper())
    scored = []
    for c in candidates:
        has_alpha = any(ch.isalpha() for ch in c)
        has_digit = any(ch.isdigit() for ch in c)
        if has_alpha and has_digit:
            scored.append(c)
    if not scored:
        scored = candidates
    if not scored:
        return ""
    return max(scored, key=len)


def candidates(text: str) -> list[str]:
    """Semua token mirip-serial (huruf+angka, cukup panjang), unik, terpanjang dulu."""
    if not text:
        return []
    out, seen = [], set()
    for c in _SERIAL_RE.findall(text.upper()):
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    out.sort(key=lambda x: (-(any(ch.isalpha() for ch in x) and any(ch.isdigit() for ch in x)), -len(x)))
    return out


def read_serial(image_path: str | Path) -> tuple[str, str]:
    """Kembalikan (serial, raw_text)."""
    text = read_text(image_path)
    return extract_serial(text), text


def read_bytes(data: bytes) -> str:
    """OCR dari bytes gambar (mis. region crop dari client)."""
    if not available():
        return ""
    try:
        from io import BytesIO
        with Image.open(BytesIO(data)) as img:
            return pytesseract.image_to_string(_preprocess(img)) or ""
    except Exception:
        return ""
