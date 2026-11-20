"""
IndicRAG-QA Academic PDF Styling Framework
Provides professional typography, NumberedCanvas (two-pass Page X of Y),
consistent corporate/academic palette, and custom layout flowables.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple, Any

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)

# ── Color Palette ─────────────────────────────────────────────────────────────
NAVY_PRIMARY = HexColor("#1A365D")      # Deep Academic Navy
TEAL_SECONDARY = HexColor("#2B7A78")    # Sub-heading Teal
CHARCOAL_DARK = HexColor("#2D3748")     # Primary Body Text
SLATE_GRAY = HexColor("#718096")        # Caption & Running Header
LIGHT_BG = HexColor("#F7FAFC")          # Table Alternating Rows & Callout BG
ACCENT_BLUE = HexColor("#3182CE")       # Hyperlinks & Accents
BORDER_COLOR = HexColor("#E2E8F0")      # Subtle Table & Card Borders
ALERT_AMBER = HexColor("#D69E2E")       # Caution / Limitation Accent
ALERT_RED = HexColor("#E53E3E")         # Warning / Defect Accent
SUCCESS_GREEN = HexColor("#38A169")     # Verification Pass Accent

# ── Font Registration ─────────────────────────────────────────────────────────
FONT_BASE = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_OBLIQUE = "Helvetica-Oblique"
FONT_DEVA = "Nirmala"

_fonts_registered = False

def init_fonts():
    global FONT_BASE, FONT_BOLD, FONT_OBLIQUE, FONT_DEVA, _fonts_registered
    if _fonts_registered:
        return
    win_fonts = Path("C:/Windows/Fonts")
    if (win_fonts / "arial.ttf").exists():
        try:
            pdfmetrics.registerFont(TTFont("Arial", str(win_fonts / "arial.ttf")))
            FONT_BASE = "Arial"
        except Exception:
            pass
    if (win_fonts / "arialbd.ttf").exists():
        try:
            pdfmetrics.registerFont(TTFont("Arial-Bold", str(win_fonts / "arialbd.ttf")))
            FONT_BOLD = "Arial-Bold"
        except Exception:
            pass
    if (win_fonts / "Nirmala.ttc").exists():
        try:
            pdfmetrics.registerFont(TTFont("Nirmala", str(win_fonts / "Nirmala.ttc"), subfontIndex=0))
            FONT_DEVA = "Nirmala"
        except Exception:
            FONT_DEVA = FONT_BASE
    _fonts_registered = True

init_fonts()


# ── Two-Pass Numbered Canvas for "Page X of Y" & Running Headers ───────────────
class AcademicNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        # Omit headers and footers on cover page (page 1)
        if self._pageNumber == 1:
            return

        page_w, page_h = A4
        left_margin = 54  # 0.75 in
        right_margin = page_w - 54

        # ── Running Header ──
        doc_title = getattr(self, "doc_title", "IndicRAG-QA Academic Documentation")
        self.saveState()
        self.setFont(FONT_BASE, 8)
        self.setFillColor(SLATE_GRAY)
        self.drawString(left_margin, page_h - 36, doc_title)
        self.drawRightString(right_margin, page_h - 36, "Academic Research Prototype — Final Submission")

        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.75)
        self.line(left_margin, page_h - 42, right_margin, page_h - 42)

        # ── Running Footer ──
        self.line(left_margin, 46, right_margin, 46)
        self.drawString(left_margin, 32, "Confidential & Authoritative Academic Review Candidate")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(right_margin, 32, page_str)
        self.restoreState()


# ── Stylesheet Builder ────────────────────────────────────────────────────────
def get_academic_stylesheet():
    init_fonts()
    styles = getSampleStyleSheet()

    # Document Title (Cover)
    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=24,
        leading=30,
        textColor=NAVY_PRIMARY,
        spaceAfter=12,
        alignment=0,
    ))

    # Document Subtitle (Cover)
    styles.add(ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName=FONT_BASE,
        fontSize=12,
        leading=16,
        textColor=TEAL_SECONDARY,
        spaceAfter=24,
        alignment=0,
    ))

    # Meta Block (Cover)
    styles.add(ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName=FONT_BASE,
        fontSize=9.5,
        leading=14,
        textColor=CHARCOAL_DARK,
        spaceAfter=6,
    ))

    # Heading 1 (Numbered Section)
    styles.add(ParagraphStyle(
        "Heading1_Numbered",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=15,
        leading=19,
        textColor=NAVY_PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True,
    ))

    # Heading 2 (Numbered Subsection)
    styles.add(ParagraphStyle(
        "Heading2_Numbered",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=16,
        textColor=TEAL_SECONDARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    ))

    # Heading 3 (Numbered Sub-subsection)
    styles.add(ParagraphStyle(
        "Heading3_Numbered",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        textColor=CHARCOAL_DARK,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    ))

    # Body Text
    styles.add(ParagraphStyle(
        "AcademicBody",
        parent=styles["Normal"],
        fontName=FONT_BASE,
        fontSize=9.5,
        leading=13.5,
        textColor=CHARCOAL_DARK,
        spaceAfter=6,
        alignment=4,  # Justified
    ))

    # Body Text (Bold)
    styles.add(ParagraphStyle(
        "AcademicBodyBold",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=13.5,
        textColor=CHARCOAL_DARK,
        spaceAfter=6,
    ))

    # Bullet Text
    styles.add(ParagraphStyle(
        "AcademicBullet",
        parent=styles["Normal"],
        fontName=FONT_BASE,
        fontSize=9.5,
        leading=13.5,
        textColor=CHARCOAL_DARK,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    ))

    # Hindi / Indic Paragraph Style (Uses Nirmala)
    styles.add(ParagraphStyle(
        "IndicText",
        parent=styles["Normal"],
        fontName=FONT_DEVA,
        fontSize=9.5,
        leading=14,
        textColor=CHARCOAL_DARK,
        spaceAfter=4,
    ))

    # Code / Monospace Text
    styles.add(ParagraphStyle(
        "MonospaceBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11.5,
        textColor=CHARCOAL_DARK,
    ))

    # Table Header Cell
    styles.add(ParagraphStyle(
        "TableHeaderCell",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=11.5,
        textColor=colors.white,
        alignment=1,  # Center
    ))

    # Table Body Cell
    styles.add(ParagraphStyle(
        "TableBodyCell",
        parent=styles["Normal"],
        fontName=FONT_BASE,
        fontSize=8.5,
        leading=11.5,
        textColor=CHARCOAL_DARK,
    ))

    # Table Body Cell Bold
    styles.add(ParagraphStyle(
        "TableBodyCellBold",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8.5,
        leading=11.5,
        textColor=CHARCOAL_DARK,
    ))

    # Callout Box Text
    styles.add(ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName=FONT_BASE,
        fontSize=9,
        leading=13,
        textColor=CHARCOAL_DARK,
    ))

    # TOC Item
    styles.add(ParagraphStyle(
        "TOCItem",
        parent=styles["Normal"],
        fontName=FONT_BASE,
        fontSize=9.5,
        leading=15,
        textColor=CHARCOAL_DARK,
    ))

    return styles


def wrap_indic(text: str) -> str:
    """If text contains Devanagari characters, wrap with font tag for Nirmala."""
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        return f"<font name='{FONT_DEVA}'>{text}</font>"
    return text


# ── Helper: Callout Box Flowable ──────────────────────────────────────────────
def make_callout(
    text: str,
    title: str = "IMPORTANT NOTE",
    accent_color: HexColor = TEAL_SECONDARY,
    bg_color: HexColor = LIGHT_BG,
    styles: Any = None,
) -> Table:
    if styles is None:
        styles = get_academic_stylesheet()
    
    hex_code = f"#{accent_color.hexval()[2:]}" if hasattr(accent_color, 'hexval') else str(accent_color)
    content = [
        Paragraph(f"<b><font color='{hex_code}'>{title}</font></b>", styles["CalloutText"]),
        Spacer(1, 3),
        Paragraph(text, styles["CalloutText"]),
    ]
    t = Table([[content]], colWidths=[A4[0] - 108])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, accent_color),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


# ── Helper: Styled Data Table ─────────────────────────────────────────────────
def make_styled_table(
    headers: List[str],
    rows: List[List[Any]],
    col_widths: List[float],
    styles: Any = None,
) -> Table:
    if styles is None:
        styles = get_academic_stylesheet()

    table_data = []
    # Header row
    hdr_row = [Paragraph(f"<b>{h}</b>", styles["TableHeaderCell"]) for h in headers]
    table_data.append(hdr_row)

    # Data rows
    for r in rows:
        row_cells = []
        for cell in r:
            if isinstance(cell, str):
                cell_text = wrap_indic(cell)
                row_cells.append(Paragraph(cell_text, styles["TableBodyCell"]))
            else:
                row_cells.append(cell)
        table_data.append(row_cells)

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ]))
    return t
