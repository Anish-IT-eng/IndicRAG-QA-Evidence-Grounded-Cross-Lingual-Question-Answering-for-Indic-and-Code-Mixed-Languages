import re
import sqlite3

def test_get_event_details(event_name_or_date: str):
    conn = sqlite3.connect('backend/data/db/indicrag.db')
    conn.row_factory = sqlite3.Row
    query = """
        SELECT DISTINCT
            r1.subject_id as event_name,
            r1.object_value as event_date,
            r2.object_value as event_day,
            r3.object_value as event_type,
            r1.source_page as page_number,
            r1.source_document_id,
            r1.source_table_id,
            r1.source_row_id
        FROM document_relationships r1
        LEFT JOIN document_relationships r2
            ON r1.source_table_id = r2.source_table_id
            AND r1.source_row_id = r2.source_row_id
            AND r2.predicate = 'EVENT_HAS_DAY'
        LEFT JOIN document_relationships r3
            ON r1.source_table_id = r3.source_table_id
            AND r1.source_row_id = r3.source_row_id
            AND r3.predicate = 'EVENT_HAS_TYPE'
        WHERE r1.predicate = 'EVENT_HAS_DATE'
          AND (r1.subject_id LIKE ? OR r1.object_value LIKE ?)
          AND r1.source_document_id = '0c174816-3d23-4e47-aef4-8b8579b801d6'
        ORDER BY r1.source_page ASC, CAST(r1.source_row_id AS INTEGER) ASC
    """
    search_param = f"%{event_name_or_date}%"
    rows = conn.execute(query, (search_param, search_param)).fetchall()

    grouped = {}
    for r in rows:
        ev_raw = r["event_name"] or ""
        ev_norm = re.sub(r"\s+", " ", ev_raw).strip()
        page = r["page_number"]
        key = (ev_norm, page)
        if key not in grouped:
            grouped[key] = {
                "event_name": ev_norm,
                "page_number": page,
                "source_document_id": r["source_document_id"],
                "source_table_id": r["source_table_id"],
                "event_type": r["event_type"],
                "dates": [],
                "days": {},
                "rows": [],
            }
        dt = r["event_date"]
        if dt and dt not in grouped[key]["dates"]:
            grouped[key]["dates"].append(dt)
            grouped[key]["days"][dt] = r["event_day"]
        if r["source_row_id"] is not None and r["source_row_id"] not in grouped[key]["rows"]:
            grouped[key]["rows"].append(r["source_row_id"])

    results = []
    for (ev_name, page), data in grouped.items():
        dates = data["dates"]
        start_date = dates[0] if dates else ""
        end_date = dates[-1] if dates else ""
        start_day = data["days"].get(start_date, "")
        end_day = data["days"].get(end_date, "")
        date_range = f"{start_date} to {end_date}" if len(dates) > 1 and start_date != end_date else start_date

        results.append({
            "event_name": ev_name,
            "event_date": start_date,
            "event_day": start_day,
            "start_date": start_date,
            "end_date": end_date,
            "start_day": start_day,
            "end_day": end_day,
            "date_range": date_range,
            "individual_dates": dates,
            "event_type": data["event_type"],
            "page_number": page,
            "source_document_id": data["source_document_id"],
            "source_table_id": data["source_table_id"],
            "source_row_id": data["rows"][0] if data["rows"] else None,
            "source_rows": data["rows"],
        })
    return results

for term in ['End Semester Examination', '18-01-2027', 'Make-up Examination']:
    print(f"\n==================== SEARCH TERM: {term} ====================")
    res = test_get_event_details(term)
    for ev in res:
        print(f"Event: {ev['event_name']} (Page {ev['page_number']})")
        print(f"  Start: {ev['start_date']} ({ev['start_day']}) | End: {ev['end_date']} ({ev['end_day']})")
        print(f"  Date Range: {ev['date_range']}")
        print(f"  Dates: {ev['individual_dates']}")
        print(f"  Rows: {ev['source_rows']}")
