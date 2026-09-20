"""Entrypoint FastAPI: init DB, daftarkan router, sajikan frontend statis."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routers import (auth, export, locations, photos, settings, templates, users)

app = FastAPI(title="REZA BAA Generator", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    config.ensure_dirs()
    db.init_db()


for r in (auth.router, settings.router, templates.router, locations.router,
          photos.router, users.router, export.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    from .services import ocr
    return {"ok": True, "ocr_available": ocr.available()}


# --- Frontend statis ---
if config.WEB_DIR.exists():
    assets = config.WEB_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/")
    def index():
        idx = config.WEB_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))
        return JSONResponse({"ok": True, "msg": "Backend aktif. Frontend belum dipasang."})
