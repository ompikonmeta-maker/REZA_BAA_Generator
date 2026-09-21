"""Tulis data ke SALINAN template Excel (format asli dipertahankan).

Pendekatan config-driven: mapping kolom LOG, anchor tabel inventory, dan anchor
foto per-kategori diambil dari ``template.config_json`` (fallback ke DEFAULT yang
diturunkan dari Template_BAA.xlsx). Anchor foto bisa dikalibrasi lewat Pengaturan
tanpa mengubah kode.
"""
from __future__ import annotations

import copy
from pathlib import Path

# Default mapping untuk Template_BAA.xlsx (bisa dioverride per template)
DEFAULT_CONFIG = {
    "log": {
        "start_row": 3,
        "columns": {
            "no": "A", "lokasi": "B", "nama_barang": "C", "merk_type": "D",
            "jumlah": "E", "sn_tagging": "F", "keterangan": "G", "foto_lengkap": "H",
        },
    },
    "detail": {
        # sel judul lokasi (opsional) — diisi nama lokasi
        "location_cells": {},
        "inventory": {
            "start_row": 32, "max_rows": 5,
            "cols": {"nama_barang": "B", "merk_type": "C", "jumlah": "E",
                     "sn_tagging": "F", "keterangan": "H"},
        },
        # anchor sel kiri-atas tiap kategori foto (default utk Template_BAA;
        # sesuaikan di menu Mapping bila template berbeda)
        "photos": {
            "dashboard": "B27", "tampak_depan": "B74", "teknisi": "B91",
            "outdoor": "K26", "indoor": "K43", "sn_kit": "K74", "sn_router": "K91",
            "sn_ap": "T24", "ping": "T43", "speed": "T74", "simkopdes": "T91",
        },
        "photo_max_w": 320, "photo_max_h": 240,
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _fit(img_w: int, img_h: int, max_w: int, max_h: int) -> tuple[int, int]:
    if img_w <= 0 or img_h <= 0:
        return max_w, max_h
    r = min(max_w / img_w, max_h / img_h, 1.0)
    return int(img_w * r), int(img_h * r)


def build_workbook(template_path: str, template_config: dict, locations: list[dict],
                   out_path: str) -> dict:
    """locations: list of dict {code,name,data,inventory:[...],photos:[{category,path,...}]}"""
    import openpyxl
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.utils import column_index_from_string

    cfg = _merge(DEFAULT_CONFIG, template_config or {})
    wb = openpyxl.load_workbook(template_path)

    # Nama sheet log & detail dari config_json (disimpan saat registrasi)
    sheet_log = template_config.get("sheet_log") if template_config else None
    sheet_detail = template_config.get("sheet_detail") if template_config else None
    sheet_log = sheet_log or ("LOG" if "LOG" in wb.sheetnames else wb.sheetnames[0])
    sheet_detail = sheet_detail or (wb.sheetnames[1] if len(wb.sheetnames) > 1 else wb.sheetnames[0])

    log_ws = wb[sheet_log]
    detail_tpl = wb[sheet_detail]
    # Ganti nama sheet template detail agar salinan tak bentrok namanya
    _tpl_title = "__tpl_detail__"
    detail_tpl.title = _tpl_title

    warnings = []
    log_row = cfg["log"]["start_row"]
    log_cols = cfg["log"]["columns"]

    for i, loc in enumerate(locations, start=1):
        data = loc.get("data", {})
        inv = loc.get("inventory", [])
        photos = loc.get("photos", [])
        first = inv[0] if inv else {}

        # --- baris ringkasan di LOG ---
        def _set(col_key, value):
            col = log_cols.get(col_key)
            if col:
                log_ws[f"{col}{log_row}"] = value
        _set("no", i)
        _set("lokasi", data.get("nama_lokasi") or loc.get("name") or loc.get("code"))
        _set("nama_barang", first.get("nama_barang", ""))
        _set("merk_type", first.get("merk_type", ""))
        _set("jumlah", first.get("jumlah", ""))
        _set("sn_tagging", "; ".join(x.get("sn_tagging", "") for x in inv if x.get("sn_tagging")))
        _set("keterangan", first.get("keterangan", ""))
        _set("foto_lengkap", "Ya" if len(photos) >= 1 else "Belum")
        log_row += 1

        # --- sheet detail per lokasi (duplikasi template) ---
        ws = wb.copy_worksheet(detail_tpl)
        ws.title = loc.get("code", f"Lokasi_{i:04d}")[:31]

        for cell, field in cfg["detail"].get("location_cells", {}).items():
            try:
                ws[cell] = data.get(field, "")
            except Exception:
                pass

        invc = cfg["detail"]["inventory"]
        r0 = invc["start_row"]
        for r_off, item in enumerate(inv[: invc.get("max_rows", 999)]):
            r = r0 + r_off
            for field, col in invc["cols"].items():
                try:
                    ws[f"{col}{r}"] = item.get(field, "")
                except Exception:
                    pass

        # --- foto per kategori ---
        photo_anchors = cfg["detail"].get("photos", {})
        by_cat: dict[str, list] = {}
        for p in photos:
            by_cat.setdefault(p.get("category", "uncategorized"), []).append(p)
        for cat, plist in by_cat.items():
            anchor = photo_anchors.get(cat)
            if not anchor or not plist:
                if not anchor:
                    warnings.append(f"{ws.title}: anchor foto '{cat}' belum dikalibrasi")
                continue
            p = plist[0]
            path = p.get("path")
            if not path or not Path(path).exists():
                continue
            try:
                xi = XLImage(path)
                xi.width, xi.height = _fit(xi.width, xi.height,
                                           cfg["detail"]["photo_max_w"],
                                           cfg["detail"]["photo_max_h"])
                ws.add_image(xi, anchor)
            except Exception as e:
                warnings.append(f"{ws.title}: gagal sisip foto '{cat}': {e}")

    # Hapus sheet template detail (yang sudah diganti nama) bila sudah ada salinan
    if locations and _tpl_title in wb.sheetnames and len(wb.sheetnames) > 1:
        try:
            del wb[_tpl_title]
        except Exception:
            pass
    else:
        # tak ada lokasi -> kembalikan nama sheet detail seperti semula
        wb[_tpl_title].title = sheet_detail

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return {"path": out_path, "warnings": warnings}
