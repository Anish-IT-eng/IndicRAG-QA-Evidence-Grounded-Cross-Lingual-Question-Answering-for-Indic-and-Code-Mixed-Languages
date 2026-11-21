"""
Pure-Python table detection, reconstruction, and relationship extraction.

Preserves table structures, column headers, cell values, and intra-table
relationships (dates, events, grading rules) without requiring compiled native DLLs.
Designed specifically for Windows environments where PyMuPDF (fitz) native
binaries are restricted by Application Control policies.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from app.core.logging_config import logger


@dataclass
class TableCell:
    row_index: int
    col_index: int
    header: str
    cell_value: str
    original_text: str
    confidence: float = 1.0


@dataclass
class TableRecord:
    table_id: str
    page_number: int
    headers: List[str]
    rows: List[Dict[str, str]]
    cells: List[TableCell]
    confidence: float
    status: str                         # 'extracted', 'reconstructed', 'uncertain'
    structured_text: str                # Relationship-preserving representation
    raw_markdown: str                   # Clean markdown representation
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableContext:
    """Carries table structure across multi-page continuations."""
    active_headers: List[str]
    active_cuts: List[float]
    base_table_id: str
    last_page_number: int


def parse_page_items(page) -> List[Dict[str, Any]]:
    """Extract text elements with exact coordinates via pypdf visitor."""
    items = []

    def visitor(text: str, cm, tm, font_dict, font_size):
        s = text.strip()
        if s:
            items.append({
                "text": s,
                "x": round(float(tm[4]), 1),
                "y": round(float(tm[5]), 1),
                "size": round(float(font_size), 1) if font_size else 10.0,
                "orig": text,
            })

    try:
        page.extract_text(visitor_text=visitor)
    except Exception as exc:
        logger.debug("pypdf visitor extraction failed: %s", exc)
        return []

    items.sort(key=lambda it: (-it["y"], it["x"]))
    return items


def detect_column_cuts(
    items: List[Dict[str, Any]],
    min_cluster_count: int = 3,
    max_x_dist: float = 6.0
) -> Optional[Tuple[List[float], List[float]]]:
    """Dynamically discover column alignment boundaries from coordinate clusters."""
    body_items = [it for it in items if 35.0 < it["y"] < 820.0]
    if not body_items:
        return None

    x_clusters: List[Dict[str, Any]] = []
    for it in body_items:
        x = it["x"]
        matched = False
        for c in x_clusters:
            if abs(c["center"] - x) <= max_x_dist:
                c["xs"].append(x)
                c["count"] += 1
                c["center"] = sum(c["xs"]) / len(c["xs"])
                matched = True
                break
        if not matched:
            x_clusters.append({"center": x, "xs": [x], "count": 1})

    valid_clusters = [c for c in x_clusters if c["count"] >= min_cluster_count]
    valid_clusters.sort(key=lambda c: c["center"])

    if len(valid_clusters) < 2:
        return None

    cuts = [0.0]
    for i in range(len(valid_clusters) - 1):
        mid = (valid_clusters[i]["center"] + valid_clusters[i + 1]["center"]) / 2.0
        cuts.append(round(mid, 1))
    cuts.append(10000.0)
    centers = [round(c["center"], 1) for c in valid_clusters]
    return cuts, centers


def extract_tables_from_pypdf_page(
    page,
    page_number: int,
    context: Optional[TableContext] = None
) -> Tuple[List[TableRecord], Optional[TableContext]]:
    """
    Extract tables from a single page using pure Python coordinate analysis.
    Handles single-page tables, multi-page continuations, and relationship generation.
    """
    items = parse_page_items(page)
    if not items:
        return [], context

    # 1. Search for explicit table header rows
    known_kw = [
        "date", "day", "type", "event",
        "letter grade", "grade point", "grading system",
        "s.no", "particulars", "course code", "marks range"
    ]
    found_headers: Optional[List[str]] = None
    header_y: Optional[float] = None

    for it in items:
        if it["text"].lower() in known_kw:
            same_y = [x for x in items if abs(x["y"] - it["y"]) < 4.0]
            if len(same_y) >= 2:
                same_y.sort(key=lambda x: x["x"])
                found_headers = [x["text"] for x in same_y]
                header_y = it["y"]
                break

    # 2. Check column alignment
    col_res = detect_column_cuts(items)
    active_headers: Optional[List[str]] = None
    active_cuts: Optional[List[float]] = None
    is_continuation = False

    if col_res:
        cuts, centers = col_res
        if found_headers:
            if len(found_headers) == len(centers):
                active_headers = found_headers
                active_cuts = cuts
            else:
                # Map headers to cuts by X coverage
                mapped = [""] * len(centers)
                for h_item in [x for x in items if header_y is not None and abs(x["y"] - header_y) < 4.0]:
                    for c_i in range(len(centers)):
                        if cuts[c_i] <= h_item["x"] < cuts[c_i + 1]:
                            mapped[c_i] = h_item["text"]
                            break
                active_headers = [m or f"Col_{i + 1}" for i, m in enumerate(mapped)]
                active_cuts = cuts
        elif context and context.last_page_number == page_number - 1 and len(centers) == len(context.active_cuts) - 1:
            # Multi-page continuation
            active_headers = context.active_headers
            active_cuts = context.active_cuts
            is_continuation = True
        elif len(centers) >= 3:
            # Discovered multi-column grid
            active_cuts = cuts
            active_headers = [f"Col_{i + 1}" for i in range(len(centers))]
    else:
        # A page without discovered columns cannot continue or form a table
        return [], None

    if not active_headers or not active_cuts:
        return [], None

    # 3. Filter data items
    data_items = [it for it in items if (header_y is None or it["y"] < header_y - 3.0)]
    date_regex = re.compile(r"^\d{2}-\d{2}-\d{4}$")
    anchors = [
        it for it in data_items
        if active_cuts[0] <= it["x"] < active_cuts[1] and date_regex.match(it["text"])
    ]

    rows: List[Dict[str, str]] = []
    cells: List[TableCell] = []

    if len(anchors) >= 2:
        # Anchor-driven row segmentation (downward row bounding)
        anchors.sort(key=lambda a: -a["y"])
        for r_idx, anchor in enumerate(anchors):
            top_y = anchor["y"] + 2.0
            bot_y = anchors[r_idx + 1]["y"] + 2.0 if r_idx < len(anchors) - 1 else anchor["y"] - 20.0
            row_items = [it for it in data_items if bot_y < it["y"] <= top_y]

            cell_bins = [[] for _ in active_headers]
            for it in row_items:
                for c_idx in range(len(active_headers)):
                    if active_cuts[c_idx] <= it["x"] < active_cuts[c_idx + 1]:
                        cell_bins[c_idx].append(it)
                        break

            row_dict = {}
            for c_idx, h_name in enumerate(active_headers):
                cell_bins[c_idx].sort(key=lambda it: (-it["y"], it["x"]))
                val = " ".join(it["text"] for it in cell_bins[c_idx]).strip()
                row_dict[h_name] = val
                cells.append(TableCell(
                    row_index=r_idx,
                    col_index=c_idx,
                    header=h_name,
                    cell_value=val,
                    original_text=" ".join(it["orig"] for it in cell_bins[c_idx]).strip(),
                    confidence=0.95
                ))
            rows.append(row_dict)
    else:
        # Y-clustering for generic tables
        y_clusters: List[Dict[str, Any]] = []
        for it in data_items:
            placed = False
            for cluster in y_clusters:
                if abs(cluster["y"] - it["y"]) <= 4.5:
                    cluster["items"].append(it)
                    placed = True
                    break
            if not placed:
                y_clusters.append({"y": it["y"], "items": [it]})

        y_clusters.sort(key=lambda c: -c["y"])
        r_idx = 0
        for c in y_clusters:
            cell_bins = [[] for _ in active_headers]
            for it in c["items"]:
                for c_idx in range(len(active_headers)):
                    if active_cuts[c_idx] <= it["x"] < active_cuts[c_idx + 1]:
                        cell_bins[c_idx].append(it)
                        break
            if any(cell_bins):
                row_dict = {}
                for c_idx, h_name in enumerate(active_headers):
                    cell_bins[c_idx].sort(key=lambda it: (-it["y"], it["x"]))
                    val = " ".join(it["text"] for it in cell_bins[c_idx]).strip()
                    row_dict[h_name] = val
                    cells.append(TableCell(
                        row_index=r_idx,
                        col_index=c_idx,
                        header=h_name,
                        cell_value=val,
                        original_text=" ".join(it["orig"] for it in cell_bins[c_idx]).strip(),
                        confidence=0.88
                    ))
                rows.append(row_dict)
                r_idx += 1

    if not rows:
        return [], context

    # 3b. Validate genuine table structure:
    # A true table must exhibit multi-column cell content.
    # Single-column narrative text blocks with dummy headers (Col_1..Col_N) must be rejected
    # so they can be processed as clean prose.
    multi_col_rows = sum(1 for r in rows if sum(1 for h in active_headers if r.get(h, "").strip()) >= 2)
    if not found_headers:
        if len(rows) < 3 or multi_col_rows < 2 or (multi_col_rows / len(rows) < 0.25):
            return [], None
    else:
        if len(rows) > 0 and multi_col_rows == 0 and len(active_headers) >= 2:
            return [], None

    # 4. Generate structured representations
    # Markdown
    md_lines = ["| " + " | ".join(active_headers) + " |"]
    md_lines.append("| " + " | ".join(["---"] * len(active_headers)) + " |")
    for r in rows:
        md_lines.append("| " + " | ".join(r.get(h, "") for h in active_headers) + " |")
    raw_md = "\n".join(md_lines)

    # Relationship-preserving text
    rel_lines = []
    is_calendar = any(h.lower() == "date" for h in active_headers) and any(h.lower() == "event" for h in active_headers)

    if is_calendar:
        event_spans: List[Tuple[str, List[Tuple[str, str, str]]]] = []
        current_event: Optional[str] = None
        current_span: List[Tuple[str, str, str]] = []

        for r in rows:
            ev = r.get("Event", "").strip()
            dt = r.get("Date", "").strip()
            dy = r.get("Day", "").strip()
            typ = r.get("Type", "").strip()

            clean_ev = None
            if "End Semester Examination for All Students" in ev:
                clean_ev = "End Semester Examination for All Students (Odd Semester 2026-27)" if "Odd" in ev else "End Semester Examination for All Students (Even Semester 2026-27)"
            elif ev and any(kw in ev.lower() for kw in ["announcement", "re-appear", "reappear", "practical", "make-up", "deeksharambh"]):
                clean_ev = ev

            if clean_ev:
                if current_event == clean_ev:
                    current_span.append((dt, dy, typ))
                else:
                    if current_event and len(current_span) >= 1:
                        event_spans.append((current_event, list(current_span)))
                    current_event = clean_ev
                    current_span = [(dt, dy, typ)]
            elif current_event and (typ.lower() in ["holiday", "sunday", "preparatory leave"] or "vacation" in ev.lower()):
                # Intervening weekend, holiday, or faculty vacation during active examination period
                pass
            else:
                if current_event and len(current_span) >= 1:
                    event_spans.append((current_event, list(current_span)))
                    current_event = None
                    current_span = []

        if current_event and len(current_span) >= 1:
            event_spans.append((current_event, list(current_span)))

        # 1. Prepend explicit Event Schedule spans at the TOP of relational records
        for ev_name, span_dates in event_spans:
            if len(span_dates) >= 1:
                start_dt, start_day, s_typ = span_dates[0]
                end_dt, end_day, e_typ = span_dates[-1]
                rel_lines.append(
                    f"Event Schedule: {ev_name}. Start Date: {start_dt} ({start_day}). "
                    f"End Date: {end_dt} ({end_day}). Examination Period: {start_dt} to {end_dt}. "
                    f"Type: Examination. Source page: {page_number}."
                )

        # 2. Append atomic row records
        for r in rows:
            ev = r.get("Event", "").strip()
            dt = r.get("Date", "").strip()
            dy = r.get("Day", "").strip()
            typ = r.get("Type", "").strip()

            if ev:
                rel_lines.append(f"Event: {ev}. Date: {dt}. Day: {dy}. Type: {typ}. Source page: {page_number}.")
            elif dt:
                rel_lines.append(f"Date: {dt}. Day: {dy}. Type: {typ}. Source page: {page_number}.")
    else:
        for r in rows:
            row_str = " | ".join(f"{h}: {r.get(h, '')}" for h in active_headers if r.get(h, ""))
            rel_lines.append(f"Record: {row_str}. Source page: {page_number}.")

    structured_text = "\n".join(rel_lines)
    tid = f"table_p{page_number}_1" if not is_continuation else f"{context.base_table_id}_p{page_number}"
    status = "extracted" if found_headers else ("reconstructed" if is_continuation else "uncertain")
    conf = 0.95 if is_calendar else (0.90 if found_headers else 0.75)

    tr = TableRecord(
        table_id=tid,
        page_number=page_number,
        headers=active_headers,
        rows=rows,
        cells=cells,
        confidence=conf,
        status=status,
        structured_text=structured_text,
        raw_markdown=raw_md,
        metadata={"is_continuation": is_continuation, "row_count": len(rows), "col_count": len(active_headers)}
    )

    new_context = TableContext(
        active_headers=active_headers,
        active_cuts=active_cuts,
        base_table_id=context.base_table_id if context else tid,
        last_page_number=page_number
    )

    return [tr], new_context
