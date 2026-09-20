"""Generate PDF Berita Acara per lokasi (mandiri, tidak terikat layout Excel).

Menyusun: judul, data lokasi, tabel inventory, dan galeri foto berlabel kategori.
Reliabel & offline (reportlab). Cocok untuk lampiran/print.
"""
from __future__ import annotations

from pathlib import Path


def build_pdf(locations: list[dict], categories: list[dict], out_path: str,
              app_title: str = "Berita Acara Aktivasi") -> dict:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, Image as RLImage, PageBreak)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=15, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11,
                        textColor=colors.HexColor("#006a6a"))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8,
                           textColor=colors.grey)

    cat_label = {c["key"]: c["label"] for c in (categories or [])}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=15 * mm,
                            bottomMargin=15 * mm, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []

    for li, loc in enumerate(locations):
        data = loc.get("data", {})
        story.append(Paragraph(app_title, h1))
        story.append(Paragraph(
            f"{data.get('nama_lokasi','') or loc.get('name','')} &nbsp; · &nbsp; {loc.get('code','')}",
            styles["Normal"]))
        story.append(Spacer(1, 6))

        # Data lokasi
        info_rows = [[k, str(v)] for k, v in data.items() if v]
        if info_rows:
            t = Table(info_rows, colWidths=[45 * mm, 120 * mm])
            t.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#3f4948")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        # Inventory
        inv = loc.get("inventory", [])
        story.append(Paragraph("Form Inventory", h2))
        head = ["Nama Barang", "Merk/Type", "Jml", "SN/Tagging", "Keterangan"]
        body = [[i.get("nama_barang", ""), i.get("merk_type", ""), i.get("jumlah", ""),
                 i.get("sn_tagging", ""), i.get("keterangan", "")] for i in inv] or [["-"] * 5]
        it = Table([head] + body, colWidths=[38 * mm, 34 * mm, 12 * mm, 40 * mm, 42 * mm])
        it.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cce8e7")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bec9c8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(it)
        story.append(Spacer(1, 10))

        # Foto berlabel
        story.append(Paragraph("Lampiran Foto", h2))
        photos = loc.get("photos", [])
        cells = []
        for p in photos:
            path = p.get("path")
            if not path or not Path(path).exists():
                continue
            label = cat_label.get(p.get("category"), p.get("category", ""))
            serial = p.get("ocr_serial")
            cap = label + (f" — SN: {serial}" if serial else "")
            try:
                img = RLImage(path, width=58 * mm, height=44 * mm, kind="proportional")
            except Exception:
                continue
            cells.append([img, Paragraph(cap, small)])
        # susun grid 3 kolom
        if cells:
            rows, buf = [], []
            for c in cells:
                inner = Table([[c[0]], [c[1]]], colWidths=[58 * mm])
                inner.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                           ("TOPPADDING", (0, 1), (0, 1), 2)]))
                buf.append(inner)
                if len(buf) == 3:
                    rows.append(buf); buf = []
            if buf:
                while len(buf) < 3:
                    buf.append("")
                rows.append(buf)
            grid = Table(rows, colWidths=[60 * mm] * 3)
            grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                      ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
            story.append(grid)
        else:
            story.append(Paragraph("Belum ada foto.", small))

        if li < len(locations) - 1:
            story.append(PageBreak())

    doc.build(story)
    return {"path": out_path}
