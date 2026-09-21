"""OCR area terpilih (ROI). Frontend mengirim potongan gambar, server membaca teks."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, File, UploadFile

from ..deps import current_user, get_db
from ..services import ocr as ocr_svc

router = APIRouter(prefix="/api", tags=["ocr"])


@router.post("/ocr")
def ocr_region(file: UploadFile = File(...),
               conn: sqlite3.Connection = Depends(get_db), user=Depends(current_user)):
    data = file.file.read()
    text = ocr_svc.read_bytes(data)
    cands = ocr_svc.candidates(text)
    return {"available": ocr_svc.available(), "text": text,
            "candidates": cands, "serial": cands[0] if cands else ""}
