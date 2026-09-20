"""Jalankan server. Untuk dev: ``python run.py``. Dibundel jadi app.exe nanti.

Server bind ke 0.0.0.0 agar bisa diakses user lain di LAN:
    http://<ip-komputer-ini>:8000
"""
from __future__ import annotations

import socket

import uvicorn

from app import config


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main() -> None:
    config.ensure_dirs()
    ip = _lan_ip()
    print("=" * 56)
    print("  REZA BAA Generator")
    print(f"  Lokal  : http://localhost:{config.PORT}")
    print(f"  LAN    : http://{ip}:{config.PORT}")
    print(f"  Data   : {config.DATA_DIR}")
    print("  Login awal: admin / admin  (wajib ganti password)")
    print("=" * 56)
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=False)


if __name__ == "__main__":
    main()
