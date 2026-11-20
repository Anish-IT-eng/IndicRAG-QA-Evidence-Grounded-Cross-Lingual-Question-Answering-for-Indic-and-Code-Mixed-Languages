"""
PDF text extraction with fallback support.

Primary: PyMuPDF (fitz) — tries v1.x API first, then v2.x API
Fallback: pypdf — pure Python, no native DLLs (install with: pip install pypdf)

If neither is available, raises ImportError with clear instructions.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging_config import logger


# ── PDF backend selection ──────────────────────────────────────────────────────

_PDF_BACKEND = None

def _get_pdf_backend():
    global _PDF_BACKEND
    if _PDF_BACKEND is not None:
        return _PDF_BACKEND

    preferred = getattr(settings, "pdf_backend", "pypdf").lower()
    if preferred == "pypdf":
        try:
            import pypdf  # type: ignore
            _PDF_BACKEND = "pypdf"
            logger.info("PDF backend: pypdf (pure-Python, table & relationship-preserving) %s", pypdf.__version__)
            return _PDF_BACKEND
        except ImportError:
            pass

    # Try PyMuPDF
    try:
        import fitz  # type: ignore
        _PDF_BACKEND = "fitz"
        logger.info("PDF backend: PyMuPDF (fitz) %s", fitz.__version__)
        return _PDF_BACKEND
    except (ImportError, ModuleNotFoundError) as e:
        logger.warning("PyMuPDF unavailable: %s. Trying pypdf…", e)

    # Fallback to pypdf
    try:
        import pypdf  # type: ignore
        _PDF_BACKEND = "pypdf"
        logger.info("PDF backend: pypdf %s", pypdf.__version__)
        return _PDF_BACKEND
    except ImportError:
        pass

    # Try pdfplumber
    try:
        import pdfplumber  # type: ignore
        _PDF_BACKEND = "pdfplumber"
        logger.info("PDF backend: pdfplumber")
        return _PDF_BACKEND
    except ImportError:
        pass

    raise ImportError(
        "No PDF extraction library available. "
        "Install one of: PyMuPDF==1.24.x, pypdf, or pdfplumber.\n"
        "  pip install pypdf"
    )


@dataclass
class RawPage:
    page_number: int          # 1-indexed
    text: str
    has_selectable_text: bool
    tables: list[dict] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class RawChunk:
    text: str
    page_number: Optional[int]
    section: Optional[str]
    heading: Optional[str]
    clause: Optional[str]
    table_ref: Optional[str]
    chunk_index: int
    is_parent: bool = False
    parent_chunk_index: Optional[int] = None


def compute_file_hash(path: Path) -> str:
    """SHA-256 of the file bytes."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha.update(block)
    return sha.hexdigest()


# ── Extraction via PyMuPDF ─────────────────────────────────────────────────────

def _extract_pages_fitz(pdf_path: Path) -> list[RawPage]:
    import fitz  # type: ignore
    pages: list[RawPage] = []
    with fitz.open(str(pdf_path)) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text", sort=True)
            has_sel = len(text.strip()) > 20

            # Table extraction (PyMuPDF 1.23+)
            tables = []
            try:
                tab_finder = page.find_tables()
                for tbl in tab_finder.tables:
                    try:
                        df = tbl.to_pandas()
                        tables.append({"headers": list(df.columns), "rows": df.values.tolist()})
                    except Exception:
                        # to_pandas may not be available; extract as lists
                        extracted = tbl.extract()
                        if extracted:
                            tables.append({"headers": extracted[0], "rows": extracted[1:]})
            except Exception as exc:
                logger.debug("Table extraction (fitz) skipped on page %d: %s", i + 1, exc)

            lines = text.splitlines()
            headings = [l.strip() for l in lines if _detect_heading(l)]
            pages.append(RawPage(
                page_number=i + 1,
                text=text,
                has_selectable_text=has_sel,
                tables=tables,
                headings=headings,
            ))
    return pages


# ── Extraction via pypdf ───────────────────────────────────────────────────────

def _extract_pages_pypdf(pdf_path: Path) -> list[RawPage]:
    import pypdf  # type: ignore
    from app.ingestion.table_extractor import extract_tables_from_pypdf_page, TableContext

    pages: list[RawPage] = []
    tbl_context: Optional[TableContext] = None

    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            has_sel = len(text.strip()) > 20
            lines = text.splitlines()
            headings = [l.strip() for l in lines if _detect_heading(l)]

            # Extract tables using pure-Python coordinate visitor
            page_tables = []
            try:
                extracted_tables, tbl_context = extract_tables_from_pypdf_page(
                    page, page_number=i + 1, context=tbl_context
                )
                for tr in extracted_tables:
                    page_tables.append({
                        "table_id": tr.table_id,
                        "headers": tr.headers,
                        "rows": tr.rows,
                        "cells": [c.__dict__ for c in tr.cells],
                        "confidence": tr.confidence,
                        "status": tr.status,
                        "structured_text": tr.structured_text,
                        "raw_markdown": tr.raw_markdown,
                        "metadata": tr.metadata,
                    })
            except Exception as exc:
                logger.debug("Table extraction failed on page %d: %s", i + 1, exc)

            pages.append(RawPage(
                page_number=i + 1,
                text=text,
                has_selectable_text=has_sel,
                tables=page_tables,
                headings=headings,
            ))
    return pages


def _events_match(ev1: str, ev2: str) -> bool:
    e1 = re.sub(r"\s+", " ", ev1.lower().strip())
    e2 = re.sub(r"\s+", " ", ev2.lower().strip())
    if not e1 or not e2:
        return False
    if e1 == e2 or e1 in e2 or e2 in e1:
        # Guard against false positives between distinct event types
        keywords = ["announcement", "re-appear", "reappear", "practical", "admit card", "vacation", "makeup", "make-up", "mid-term", "mid term", "submission"]
        for kw in keywords:
            if (kw in e1) != (kw in e2):
                return False
        return True
    return False


# ── Extraction via pdfplumber ──────────────────────────────────────────────────

def _extract_pages_pdfplumber(pdf_path: Path) -> list[RawPage]:
    import pdfplumber  # type: ignore
    pages: list[RawPage] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            has_sel = len(text.strip()) > 20

            tables = []
            try:
                raw_tables = page.extract_tables()
                for tbl in (raw_tables or []):
                    if tbl:
                        tables.append({"headers": tbl[0], "rows": tbl[1:]})
            except Exception as exc:
                logger.debug("Table extraction (pdfplumber) skipped: %s", exc)

            lines = text.splitlines()
            headings = [l.strip() for l in lines if _detect_heading(l)]
            pages.append(RawPage(
                page_number=i + 1,
                text=text,
                has_selectable_text=has_sel,
                tables=tables,
                headings=headings,
            ))
    return pages


# ── Heading detection ─────────────────────────────────────────────────────────

def _detect_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) < 80 and stripped.isupper():
        return True
    if re.match(r"^\d+(\.\d+)*[\s\.]", stripped) and len(stripped) < 100:
        return True
    return False


# ── Public interface ───────────────────────────────────────────────────────────

def _attempt_ocr_page_fitz(fitz_page) -> tuple[str, str]:
    """
    Attempt OCR on a single fitz page using RapidOCR or pytesseract.
    Returns (extracted_text, ocr_source).
    """
    # 1. Try RapidOCR (high accuracy ONNX-based, self-contained)
    try:
        import numpy as np  # type: ignore
        from rapidocr_onnxruntime import RapidOCR  # type: ignore

        engine = RapidOCR()
        mat = fitz_page.get_pixmap(dpi=300)
        img_np = np.frombuffer(mat.samples, dtype=np.uint8).reshape((mat.height, mat.width, mat.n))
        if mat.n == 4:
            img_np = img_np[:, :, :3]
        result, _ = engine(img_np)
        if result:
            text = "\n".join(line[1] for line in result)
            logger.info("RapidOCR extracted %d lines (%d chars) from page", len(result), len(text))
            return text, "rapidocr"
    except Exception as exc:
        logger.debug("RapidOCR failed or unavailable: %s", exc)

    # 2. Try pytesseract as fallback
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
        import io

        mat = fitz_page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(mat.tobytes("png")))
        text = pytesseract.image_to_string(img, lang="eng")
        logger.info("pytesseract extracted %d chars from page", len(text))
        return text, "pytesseract"
    except Exception as exc:
        logger.debug("pytesseract failed or unavailable: %s", exc)

    return "", ""


def extract_pages(pdf_path: Path, attempt_ocr: bool = True) -> list[RawPage]:
    """
    Extract pages from a PDF using the best available backend.

    For pages with no selectable text (scanned images), attempts OCR via
    pytesseract if available. Pages that remain empty after OCR are returned
    with has_selectable_text=False and metadata['ocr_required']=True so the
    pipeline can handle them honestly.

    Raises ImportError if no backend is available.
    """
    pdf_path = Path(pdf_path)
    backend = _get_pdf_backend()
    logger.info("Extracting %s with backend=%s", pdf_path.name, backend)

    if backend == "fitz":
        pages = _extract_pages_fitz(pdf_path)
    elif backend == "pypdf":
        pages = _extract_pages_pypdf(pdf_path)
    elif backend == "pdfplumber":
        pages = _extract_pages_pdfplumber(pdf_path)
    else:
        raise ImportError(f"Unknown PDF backend: {backend}")

    # OCR pass: try to recover text from scanned pages
    scanned_count = 0
    ocr_recovered = 0
    for page in pages:
        if not page.has_selectable_text:
            scanned_count += 1
            page.metadata["ocr_required"] = True
            if attempt_ocr:
                try:
                    import fitz  # type: ignore
                    with fitz.open(str(pdf_path)) as doc:
                        fitz_page = doc[page.page_number - 1]
                        ocr_text, ocr_source = _attempt_ocr_page_fitz(fitz_page)
                    if ocr_text.strip():
                        page.text = ocr_text
                        page.has_selectable_text = True
                        page.metadata["ocr_source"] = ocr_source or "ocr"
                        page.metadata.pop("ocr_required", None)
                        lines = ocr_text.splitlines()
                        page.headings = [l.strip() for l in lines if _detect_heading(l)]
                        ocr_recovered += 1
                except Exception as exc:
                    logger.debug("OCR attempt skipped: %s", exc)

    if scanned_count:
        logger.warning(
            "%s: %d/%d pages have no selectable text; OCR recovered %d.",
            pdf_path.name, scanned_count, len(pages), ocr_recovered,
        )

    logger.info("Extracted %d pages from %s", len(pages), pdf_path.name)
    return pages


# ── Chunking ───────────────────────────────────────────────────────────────────

def _approx_tokens(text: str) -> int:
    return len(text.split())


def _split_into_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?।])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_pages(
    pages: list[RawPage],
    chunk_size: int = settings.chunk_size_tokens,
    overlap: int = settings.chunk_overlap_tokens,
    parent_size: int = settings.parent_chunk_size_tokens,
) -> list[RawChunk]:
    """
    Create overlapping child chunks and larger parent chunks.
    Child chunks are the retrieval unit; parents carry context for generation (PDR).
    """
    child_chunks: list[RawChunk] = []
    parent_chunks: list[RawChunk] = []

    current_heading: Optional[str] = None
    current_section: Optional[str] = None
    parent_buffer: list[str] = []
    parent_page: Optional[int] = None
    parent_idx = 0
    chunk_idx = 0

    for page in pages:
        if not page.text.strip():
            continue

        if page.headings:
            current_heading = page.headings[0]
            m = re.match(r"^(\d+(\.\d+)*)", current_heading)
            if m:
                current_section = m.group(0)

        if page.tables:
            # Table-protected chunking: preserve row records, column headers, and relationships
            for tidx, table in enumerate(page.tables):
                headers = table.get("headers", [])
                rows = table.get("rows", [])
                st_lines = table.get("structured_text", "").splitlines()
                tid = table.get("table_id") or f"table_p{page.page_number}_{tidx+1}"

                # Batch rows into blocks of 10-12 rows to preserve semantic cohesion and optimal retrieval density
                batch_size = 12
                batches = [rows[i:i+batch_size] for i in range(0, len(rows), batch_size)] if len(rows) > batch_size else [rows]

                for b_idx, r_batch in enumerate(batches):
                    md_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                    batch_dates = set()
                    for r in r_batch:
                        md_lines.append("| " + " | ".join(r.get(h, "") for h in headers) + " |")
                        if "Date" in r and r["Date"]:
                            batch_dates.add(r["Date"])

                    relevant_st = []
                    batch_events = [r.get("Event", "").strip().lower() for r in r_batch if r.get("Event")]

                    for l in st_lines:
                        if l.startswith("Event Schedule:"):
                            parts = l.split(". Start Date:")
                            sched_ev = parts[0].replace("Event Schedule:", "")
                            if any(_events_match(ev, sched_ev) for ev in batch_events):
                                relevant_st.append(l)
                        elif any(d in l for d in batch_dates if d) and not l.startswith("Event Schedule:"):
                            relevant_st.append(l)

                    chunk_body = "\n".join(relevant_st) if relevant_st else ("[Structured Table View]:\n" + "\n".join(md_lines))

                    part_ref = f"{tid}_part{b_idx+1}" if len(batches) > 1 else tid
                    child_chunks.append(RawChunk(
                        text=chunk_body.strip(),
                        page_number=page.page_number,
                        section=current_section,
                        heading=current_heading,
                        clause=None,
                        table_ref=part_ref,
                        chunk_index=chunk_idx,
                        is_parent=False,
                        parent_chunk_index=parent_idx,
                    ))
                    chunk_idx += 1
                    parent_buffer.append(chunk_body.strip())
        else:
            # Normal prose chunking (sentence boundary preservation for narrative text)
            sentences = _split_into_sentences(page.text)
            buffer: list[str] = []
            buf_tokens = 0

            def flush_child():
                nonlocal chunk_idx
                if not buffer:
                    return
                text = " ".join(buffer).strip()
                if len(text) < 30:
                    return
                child_chunks.append(RawChunk(
                    text=text,
                    page_number=page.page_number,
                    section=current_section,
                    heading=current_heading,
                    clause=None,
                    table_ref=None,
                    chunk_index=chunk_idx,
                    is_parent=False,
                    parent_chunk_index=parent_idx,
                ))
                chunk_idx += 1  # type: ignore[assignment]

            for sent in sentences:
                stok = _approx_tokens(sent)
                if buf_tokens + stok > chunk_size and buffer:
                    flush_child()
                    overlap_carry = buffer[-max(1, overlap // max(stok, 1)):]
                    buffer = list(overlap_carry)
                    buf_tokens = sum(_approx_tokens(s) for s in buffer)
                buffer.append(sent)
                buf_tokens += stok

                parent_buffer.append(sent)
                if parent_page is None:
                    parent_page = page.page_number
                if _approx_tokens(" ".join(parent_buffer)) >= parent_size:
                    parent_chunks.append(RawChunk(
                        text=" ".join(parent_buffer).strip(),
                        page_number=parent_page,
                        section=current_section,
                        heading=current_heading,
                        clause=None,
                        table_ref=None,
                        chunk_index=parent_idx,
                        is_parent=True,
                    ))
                    parent_idx += 1
                    parent_buffer = []
                    parent_page = None

            flush_child()

    if parent_buffer:
        parent_chunks.append(RawChunk(
            text=" ".join(parent_buffer).strip(),
            page_number=parent_page,
            section=current_section,
            heading=current_heading,
            clause=None,
            table_ref=None,
            chunk_index=parent_idx,
            is_parent=True,
        ))

    all_chunks = parent_chunks + child_chunks
    logger.info(
        "Chunking complete: %d parent + %d child chunks",
        len(parent_chunks), len(child_chunks)
    )
    return all_chunks


def _table_to_text(table: dict) -> str:
    st = table.get("structured_text")
    md = table.get("raw_markdown", "")
    if st and st.strip():
        if md and md.strip():
            return f"{st.strip()}\n\n[Structured Table View]:\n{md.strip()}"
        return st.strip()
    if md and md.strip():
        return md.strip()

    headers = table.get("headers", [])
    rows = table.get("rows", [])
    lines = []
    if headers:
        lines.append(" | ".join(str(h) for h in headers))
        lines.append("-" * 40)
    for row in rows:
        lines.append(" | ".join(str(c) for c in row))
    return "\n".join(lines)
