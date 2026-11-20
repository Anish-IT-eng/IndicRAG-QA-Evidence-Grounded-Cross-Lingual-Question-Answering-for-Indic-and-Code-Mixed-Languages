import sqlite3
import json

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

print("=== PASSAGES IN OFFICIAL DOCUMENTS CONTAINING MEDICAL, ILLNESS, RELAXATION, CONDONATION ===")
passages = conn.execute("""
    SELECT p.passage_id, p.document_id, d.filename, p.page_number, p.section, p.heading, p.clause, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE d.source_type = 'official'
      AND (p.text LIKE '%medical%' OR p.text LIKE '%illness%' OR p.text LIKE '%relaxation%' OR p.text LIKE '%condon%')
""").fetchall()

print(f"Total matching official passages: {len(passages)}")
for p in passages:
    print(f"\n[PASSAGE ID]: {p['passage_id']}")
    print(f"  Document: {p['filename']} (ID: {p['document_id']})")
    print(f"  Page: {p['page_number']} | Clause: {p['clause']} | Heading: {p['heading']} | Section: {p['section']}")
    print(f"  Text excerpt: {p['text']}")

print("\n=== RELATIONSHIPS IN OFFICIAL DOCUMENTS FOR MEDICAL, ILLNESS, RELAXATION ===")
rels = conn.execute("""
    SELECT r.relationship_id, r.subject_id, r.predicate, r.object_value, r.source_document_id, d.filename,
           r.source_passage_id, r.source_page, r.cohort_scope, r.programme_scope, r.metadata
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE d.source_type = 'official'
      AND (r.subject_id LIKE '%medical%' OR r.subject_id LIKE '%illness%' OR r.subject_id LIKE '%relax%'
           OR r.object_value LIKE '%medical%' OR r.object_value LIKE '%illness%' OR r.object_value LIKE '%relax%'
           OR r.object_value LIKE '%10%' OR r.predicate LIKE '%EXCEPTION%')
""").fetchall()

print(f"Total matching official relationships: {len(rels)}")
for r in rels:
    print(f"\n[REL ID]: {r['relationship_id']}")
    print(f"  Doc: {r['filename']} (ID: {r['source_document_id']}) | Page: {r['source_page']}")
    print(f"  Subject: {r['subject_id']}")
    print(f"  Predicate: {r['predicate']}")
    print(f"  Object: {r['object_value']}")
    print(f"  Passage ID: {r['source_passage_id']}")
    print(f"  Cohort Scope: {r['cohort_scope']} | Programme Scope: {r['programme_scope']}")
