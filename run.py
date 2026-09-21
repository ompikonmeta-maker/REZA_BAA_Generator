"""Jalankan server. Untuk dev: ``python run.py``. Dibundel jadi app.exe nanti.

Server bind ke 0.0.0.0 agar bisa diakses user lain di LAN:
    http://<ip-komputer-ini>:8000
"""
from __future__ import annotations

import os
import socket
import threading
import webbrowser

import uvicorn

from app import config
from app.main import app


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
    print("  BAA Generator")
    print(f"  Lokal  : http://localhost:{config.PORT}")
    print(f"  LAN    : http://{ip}:{config.PORT}")
    print(f"  Data   : {config.DATA_DIR}")
    print("  Login awal: admin / admin  (wajib ganti password)")
    print("=" * 56)
    # Buka browser otomatis ke localhost (set REZA_BAA_NO_BROWSER=1 untuk nonaktif)
    if os.environ.get("REZA_BAA_NO_BROWSER") != "1":
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{config.PORT}")).start()
    # Objek app langsung (bukan import string) supaya aman saat dibundel exe
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=False)


if __name__ == "__main__":
    main()
