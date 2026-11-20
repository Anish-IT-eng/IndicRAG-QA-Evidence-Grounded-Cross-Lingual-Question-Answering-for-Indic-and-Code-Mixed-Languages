import sqlite3

conn = sqlite3.connect("backend/data/db/indicrag.db")
c = conn.cursor()

pids = [
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

for idx, pid in enumerate(pids, 7):
    r = c.execute("SELECT text FROM passages WHERE passage_id = ?", (pid,)).fetchone()
    print(f"=== #{idx}: {pid} ===")
    print(repr(r[0][:250]))
    print()

conn.close()

