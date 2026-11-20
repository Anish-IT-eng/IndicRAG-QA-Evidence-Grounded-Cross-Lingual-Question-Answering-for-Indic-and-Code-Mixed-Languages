import sqlite3
import json

conn = sqlite3.connect("backend/data/db/indicrag.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

def get_passage(pid):
    r = c.execute("SELECT passage_id, parent_passage_id, document_id, page_number, section, heading, text FROM passages WHERE passage_id = ?", (pid,)).fetchone()
    return dict(r) if r else None

passages_to_check = [
    "ee63431f-398b-4717-aa04-8c456a3ab928",
    "124457f2-1670-4208-88d5-84808860454c",
    "4fb20336-4a76-4e21-8422-f3d9e08a4c27",
    "cfb81e36-8477-4083-aa37-f671c6202263",
    "c4d08811-efad-4c12-8f9a-3a7c7938ff28",
    "5fce6f7d-77a5-4f39-a240-072d84c12334",
    "380bfc8e-cd43-4343-8db3-11fd7c5b400b",
    "7de500cb-6f25-49bc-8e53-5f3415b2c054",
    "29bf25f8-7683-45da-8dea-f1c4c5815b74",
    "664e460c-3448-49bf-b051-e050a597d3ee",
    "505e552e-35e0-4b5d-98ba-10dff85f4eab",
    "dc9034e1-88aa-4a45-ad01-34fd28c21411",
    "dab03ad7-0094-481e-82d9-98260bc33caf",
    "5f9028f1-69ee-4e2d-9aa0-68ca2f510deb",
    "278fa408-518b-4c53-9cc2-c49ac347c87a",
    "c22770f9-e383-480d-9f9c-925d0eeffff3",
    "5fd38f8d-e1ec-406e-aa70-06317b4e3d72",
    "9bbbab01-3fe3-4864-99ab-57128db19748",
    "f6d95cc5-2c08-4aee-ba5c-72429cbef467",
    "232928ea-fe34-4563-8c67-6f714317a64d",
    "53ed3206-b2a4-4ebe-aad2-3ab9a646264a",
    "e58d460e-7817-44ac-9f2c-628791b338b2",
    "9773d6a7-12e2-4b0e-9b5f-45a8be226a95",
    "0280358a-ff3c-4964-88ab-419a9147b1f0",
    "f88ec726-74ba-426f-a01f-4b9665c1a8b8",
    "bbaac776-23eb-4535-85f9-6f181b238d3f",
    "23db7904-2f93-4c62-a74d-f159a5d11acd",
]

print(f"Total passages to check: {len(passages_to_check)}")
for pid in passages_to_check:
    p = get_passage(pid)
    if not p:
        print(f"ERROR: {pid} not found!")
    else:
        print(f"OK: {pid} | Doc: {p['document_id']} | Page: {p['page_number']} | Heading: {p['heading']}")

conn.close()

