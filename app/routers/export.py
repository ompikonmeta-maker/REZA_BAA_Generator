"""Generate output: Excel (isi salinan template) & PDF."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from .. import config, db
from ..deps import audit, current_user, get_db
from ..services import excel as excel_svc
from ..services import pdf as pdf_svc

router = APIRouter(prefix="/api/export", tags=["export"])


def _gather_locations(conn: sqlite3.Connection, scope: str, loc_id: int | None) -> list[dict]:
    if scope == "all":
        rows = conn.execute("SELECT * FROM locations ORDER BY id").fetchall()
    else:
        if not loc_id:
            raise HTTPException(400, "loc_id wajib untuk scope 'one'")
        rows = conn.execute("SELECT * FROM locations WHERE id=?", (loc_id,)).fetchall()
    if not rows:
        raise HTTPException(404, "Tidak ada lokasi untuk diekspor")
    out = []
    for r in rows:
        inv = conn.execute(
            "SELECT nama_barang,merk_type,jumlah,sn_tagging,keterangan FROM inventory_items "
            "WHERE location_id=? ORDER BY sort_order,id", (r["id"],)).fetchall()
        photos = conn.execute(
            "SELECT category,path,ocr_serial FROM photos WHERE location_id=? ORDER BY id",
            (r["id"],)).fetchall()
        out.append({
            "id": r["id"], "code": r["code"], "name": r["name"],
            "data": json.loads(r["data_json"]),
            "inventory": [dict(i) for i in inv],
            "photos": [dict(p) for p in photos],
        })
    return out


def _stamp(prefix: str, ext: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return config.OUTPUT_DIR / f"{prefix}_{ts}.{ext}"


@router.get("/excel")
def export_excel(scope: str = Query("one"), loc_id: int | None = None,
                 conn: sqlite3.Connection = Depends(get_db), user=Depends(current_user)):
    tpl = conn.execute("SELECT * FROM templates WHERE active=1 ORDER BY id DESC LIMIT 1").fetchone()
    if not tpl:
        raise HTTPException(400, "Belum ada template aktif. Daftarkan template dulu di menu Template.")
    if not Path(tpl["path"]).exists():
        raise HTTPException(400, "File template hilang di server.")
    locs = _gather_locations(conn, scope, loc_id)
    tcfg = json.loads(tpl["config_json"]) if tpl["config_json"] else {}
    tcfg["sheet_log"] = tpl["sheet_log"]
    tcfg["sheet_detail"] = tpl["sheet_detail"]
    out = _stamp("BAA" if scope == "all" else (locs[0]["code"]), "xlsx")
    res = excel_svc.build_workbook(tpl["path"], tcfg, locs, str(out))
    audit(conn, user, "export_excel", "export", scope, out.name)
    resp = FileResponse(str(out), filename=out.name,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if res.get("warnings"):
        resp.headers["X-Export-Warnings"] = str(len(res["warnings"]))
    return resp


@router.get("/pdf")
def export_pdf(scope: str = Query("one"), loc_id: int | None = None,
               conn: sqlite3.Connection = Depends(get_db), user=Depends(current_user)):
    locs = _gather_locations(conn, scope, loc_id)
    cats = db.get_setting(conn, "photo_categories", [])
    title = db.get_setting(conn, "app_title", "Berita Acara Aktivasi")
    out = _stamp("BAA" if scope == "all" else (locs[0]["code"]), "pdf")
    pdf_svc.build_pdf(locs, cats, str(out), app_title=title)
    audit(conn, user, "export_pdf", "export", scope, out.name)
    return FileResponse(str(out), filename=out.name, media_type="application/pdf")
