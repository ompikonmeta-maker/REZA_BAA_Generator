"""Autentikasi: hashing password (PBKDF2, stdlib) + sesi berbasis cookie.

Tanpa dependensi eksternal (bcrypt dll) supaya bundling exe ringan & portabel.
Fungsi sesi menerima koneksi sqlite dari pemanggil (hindari import melingkar).
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from . import config

_PBKDF2_ROUNDS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ROUNDS)
    return f"pbkdf2$sha256${_PBKDF2_ROUNDS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, digest, rounds, salt, hexhash = stored.split("$")
        dk = hashlib.pbkdf2_hmac(digest, password.encode(), salt.encode(), int(rounds))
        return hmac.compare_digest(dk.hex(), hexhash)
    except Exception:
        return False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = _utcnow()
    expires = now + timedelta(hours=config.SESSION_TTL_HOURS)
    conn.execute(
        "INSERT INTO sessions(token, user_id, created_at, expires_at) VALUES(?,?,?,?)",
        (token, user_id, now.isoformat(), expires.isoformat()),
    )
    conn.commit()
    return token


def get_session_user(conn: sqlite3.Connection, token: str | None):
    """Kembalikan row user jika sesi valid & belum kedaluwarsa, else None."""
    if not token:
        return None
    row = conn.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token = ? AND u.active = 1",
        (token,),
    ).fetchone()
    if not row:
        return None
    exp = conn.execute("SELECT expires_at FROM sessions WHERE token=?", (token,)).fetchone()
    if not exp or datetime.fromisoformat(exp["expires_at"]) < _utcnow():
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
        return None
    return row


def destroy_session(conn: sqlite3.Connection, token: str | None) -> None:
    if token:
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
