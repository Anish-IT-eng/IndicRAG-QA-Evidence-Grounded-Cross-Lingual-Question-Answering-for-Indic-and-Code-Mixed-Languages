import sqlite3
import json

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

doc_id = '0c174816-3d23-4e47-aef4-8b8579b801d6'

target_events = [
    'End Semester Examination for All Students  (Odd Semester 2026-27)',
    'End Semester Examination for All Students (Odd Semester 2026-27)',
    'Display of Date Sheet of Odd Semester Make-up Examinations',
    'Odd Semester Make-up Examinations - Start Date',
    'Odd Semester Make-up Examinations - End Date',
    'Announcement of End Semester Examination Schedule (Odd Semester 2026-27)',
    'Mid Term Examination for All Students (Odd Semester 2026-27)',
]

print("================================================================================")
print("VERIFIED RELATIONSHIP RECORDS FOR ACADEMIC CALENDAR EVENTS")
print("================================================================================")

for ev in target_events:
    rels = conn.execute("""
        SELECT relationship_id, subject_id, predicate, object_id, object_value, source_page, source_row_id, temporal_anchor
        FROM document_relationships
        WHERE source_document_id = ? AND (subject_id = ? OR object_value = ?)
        ORDER BY source_page, CAST(source_row_id AS INTEGER), predicate
    """, (doc_id, ev, ev)).fetchall()
    
    if not rels:
        continue
    
    print(f"\n>>> EVENT: {ev}")
    dates = []
    days = []
    types = []
    row_ids = sorted(list(set(r['source_row_id'] for r in rels if r['source_row_id'] is not None)), key=lambda x: int(x))
    pages = sorted(list(set(r['source_page'] for r in rels if r['source_page'] is not None)))
    
    for r in rels:
        if r['predicate'] == 'EVENT_HAS_DATE' and r['object_value']:
            dates.append((r['source_row_id'], r['object_value']))
        if r['predicate'] == 'EVENT_HAS_DAY' and r['object_value']:
            days.append((r['source_row_id'], r['object_value']))
        if r['predicate'] == 'EVENT_HAS_TYPE' and r['object_value']:
            types.append((r['source_row_id'], r['object_value']))
    
    print(f"  Pages: {pages}")
    print(f"  Source Rows: {row_ids}")
    print(f"  Total Relationships: {len(rels)}")
    print(f"  Dates: {dates}")
    print(f"  Days: {days}")
    print(f"  Types: {types}")
    print("  Detailed Relationship IDs:")
    for r in rels:
        print(f"    [{r['relationship_id']}] p.{r['source_page']} row {r['source_row_id']} | {r['predicate']} -> {r['object_value']} (anchor: {r['temporal_anchor']})")
