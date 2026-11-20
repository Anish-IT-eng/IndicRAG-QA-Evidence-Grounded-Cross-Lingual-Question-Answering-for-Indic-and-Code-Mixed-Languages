import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row
doc_id = '0c174816-3d23-4e47-aef4-8b8579b801d6'

cells = conn.execute("""
    SELECT c.row_index, c.col_index, c.header, c.cell_value
    FROM table_cells c
    WHERE c.document_id = ? AND c.page_number = 5
    ORDER BY c.row_index, c.col_index
""", (doc_id,)).fetchall()

rows = {}
for c in cells:
    r = c['row_index']
    if r not in rows:
        rows[r] = {}
    rows[r][c['header']] = c['cell_value']

print("=== PAGE 5 ROWS ===")
for r in sorted(rows.keys()):
    row = rows[r]
    date = row.get('Date', '')
    day = row.get('Day', '')
    typ = row.get('Type', '')
    event = row.get('Event', '')
    if any(k in event.lower() for k in ['make-up', 'makeup', 'date sheet', 'declaration of results', 'rechecking', '18-01', '25-01', '30-01']):
        print(f"Row {r:2d} | Date: {date:10s} | Day: {day:9s} | Type: {typ:15s} | Event: {event}")
