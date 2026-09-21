"""Statistik dashboard (role-aware).

Admin  : agregat seluruh lokasi + leaderboard + aktivitas global.
Operator: agregat di-scope ke lokasi miliknya (created_by = user) + streak.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends

from .. import db
from ..deps import current_user, get_db

router = APIRouter(prefix="/api", tags=["stats"])

_EMPTY_INV = (
    "TRIM(COALESCE(i.nama_barang,''))='' OR TRIM(COALESCE(i.merk_type,''))='' OR "
    "TRIM(COALESCE(i.jumlah,''))='' OR TRIM(COALESCE(i.sn_tagging,''))='' OR "
    "TRIM(COALESCE(i.keterangan,''))=''"
)


def _day_series(rows: dict, days: int) -> list[int]:
    """Kembalikan list hitungan per hari (lama -> baru) untuk `days` terakhir."""
    today = date.today()
    return [rows.get((today - timedelta(days=days - 1 - i)).isoformat(), 0) for i in range(days)]


@router.get("/stats")
def stats(conn: sqlite3.Connection = Depends(get_db), user=Depends(current_user)):
    is_admin = user["role"] == "admin"
    uid = user["id"]
    scope = "" if is_admin else " AND l.created_by = :uid"
    p = {"uid": uid}

    # --- ringkasan lokasi ---
    tot = conn.execute(
        f"SELECT COUNT(*) c, "
        f"SUM(CASE WHEN status='selesai' THEN 1 ELSE 0 END) done "
        f"FROM locations l WHERE 1=1{scope}", p
    ).fetchone()
    total = tot["c"] or 0
    done = tot["done"] or 0
    draft = total - done
    pct = round(done / total * 100) if total else 0

    photos = conn.execute(
        f"SELECT COUNT(*) c FROM photos ph WHERE 1=1" +
        ("" if is_admin else " AND ph.location_id IN (SELECT id FROM locations WHERE created_by=:uid)"), p
    ).fetchone()["c"] or 0

    users_active = conn.execute("SELECT COUNT(*) c FROM users WHERE active=1").fetchone()["c"] or 0
    template_active = conn.execute("SELECT COUNT(*) c FROM templates WHERE active=1").fetchone()["c"] or 0
    inv_items = conn.execute(
        f"SELECT COUNT(*) c FROM inventory_items i WHERE 1=1" +
        ("" if is_admin else " AND i.location_id IN (SELECT id FROM locations WHERE created_by=:uid)"), p
    ).fetchone()["c"] or 0

    # --- butuh perhatian (draft, terlama dulu) ---
    attn_rows = conn.execute(
        f"""SELECT l.id,l.code,l.name,l.data_json,
              (SELECT GROUP_CONCAT(DISTINCT category) FROM photos p WHERE p.location_id=l.id) photo_cats,
              (SELECT COUNT(*) FROM inventory_items i WHERE i.location_id=l.id) inv_count,
              (SELECT COUNT(*) FROM inventory_items i WHERE i.location_id=l.id AND ({_EMPTY_INV})) inv_bad
            FROM locations l WHERE l.status!='selesai'{scope}
            ORDER BY l.updated_at ASC LIMIT 8""", p
    ).fetchall()
    attention = [{
        "id": r["id"], "code": r["code"], "name": r["name"],
        "data": json.loads(r["data_json"]),
        "photo_cats": (r["photo_cats"].split(",") if r["photo_cats"] else []),
        "inv_ok": r["inv_count"] > 0 and r["inv_bad"] == 0,
    } for r in attn_rows]

    # --- leaderboard (admin) ---
    leaderboard = []
    if is_admin:
        for r in conn.execute(
            "SELECT COALESCE(NULLIF(u.full_name,''),u.username) nm, COUNT(l.id) total, "
            "SUM(CASE WHEN l.status='selesai' THEN 1 ELSE 0 END) done "
            "FROM users u JOIN locations l ON l.created_by=u.id "
            "GROUP BY u.id HAVING total>0 ORDER BY done DESC, total DESC LIMIT 6"
        ).fetchall():
            leaderboard.append({"name": r["nm"], "total": r["total"], "done": r["done"] or 0})

    # --- aktivitas terbaru ---
    feed_scope = "" if is_admin else " WHERE user_id=:uid"
    feed = [dict(r) for r in conn.execute(
        f"SELECT username,action,entity,entity_id,detail,created_at FROM audit_log{feed_scope} "
        f"ORDER BY id DESC LIMIT 8", p
    ).fetchall()]

    # --- tren: lokasi selesai per hari (14 hari) ---
    cutoff14 = (date.today() - timedelta(days=13)).isoformat()
    trend_rows = {r["d"]: r["c"] for r in conn.execute(
        f"SELECT date(updated_at) d, COUNT(*) c FROM locations l "
        f"WHERE status='selesai' AND date(updated_at)>=:c14{scope} GROUP BY d",
        {**p, "c14": cutoff14}
    ).fetchall()}
    trend = _day_series(trend_rows, 14)

    # --- heatmap: aktivitas per hari (126 hari = 18 minggu, rolling) dari audit ---
    cutoff56 = (date.today() - timedelta(days=125)).isoformat()
    heat_scope = " AND user_id=:uid" if not is_admin else ""
    heat_rows = {r["d"]: r["c"] for r in conn.execute(
        f"SELECT date(created_at) d, COUNT(*) c FROM audit_log "
        f"WHERE date(created_at)>=:c56{heat_scope} GROUP BY d",
        {**p, "c56": cutoff56}
    ).fetchall()}
    heat = _day_series(heat_rows, 126)

    out = {
        "role": user["role"],
        "name": user["full_name"] or user["username"],
        "totals": {"locations": total, "done": done, "draft": draft, "photos": photos,
                   "users_active": users_active, "template_active": template_active,
                   "inv_items": inv_items},
        "pct": pct,
        "attention": attention,
        "leaderboard": leaderboard,
        "feed": feed,
        "trend": trend,
        "heat": heat,
    }

    # --- streak + minggu ini (operator) ---
    if not is_admin:
        act_days = {r["d"] for r in conn.execute(
            "SELECT DISTINCT date(created_at) d FROM audit_log WHERE user_id=:uid", p
        ).fetchall()}
        streak = 0
        cur = date.today()
        while cur.isoformat() in act_days:
            streak += 1
            cur -= timedelta(days=1)
        week = [1 if (date.today() - timedelta(days=6 - i)).isoformat() in act_days else 0 for i in range(7)]
        out["streak"] = streak
        out["week"] = week

    return out
