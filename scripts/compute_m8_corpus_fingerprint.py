import hashlib
import sqlite3
import pandas as pd
from pathlib import Path

def compute_corpus_hash(db_path: Path) -> str:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT passage_id, text FROM passages WHERE parent_passage_id IS NOT NULL ORDER BY passage_id")
    rows = cursor.fetchall()
    conn.close()
    hasher = hashlib.sha256()
    for pid, text in rows:
        hasher.update(pid.encode("utf-8"))
        hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()

db_path = Path("backend/data/db/indicrag.db")
m8_corpus_hash = compute_corpus_hash(db_path)

# Verify frozen benchmark files
benchmarks = {
    "m3_final_verified": ("backend/data/dataset/final_verified_dataset.csv", "093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520"),
    "m6_expanded_benchmark": ("backend/data/dataset/m6_expanded_benchmark_n60.csv", "a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae"),
    "m6_qualification_ledger": ("backend/data/dataset/m6_benchmark_qualification.csv", "db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13"),
    "m6_phase3_negative": ("backend/data/dataset/m6_phase3_negative_candidates.csv", "492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa")
}

print(f"M8 Refresh Corpus SHA-256 Fingerprint: {m8_corpus_hash}")
print(f"Pre-refresh baseline Corpus SHA-256: 8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d")

all_frozen_intact = True
for name, (path_str, expected_hash) in benchmarks.items():
    with open(path_str, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    match = (actual_hash == expected_hash)
    if not match:
        all_frozen_intact = False
    print(f"[{'MATCH' if match else 'MISMATCH'}] {name}: {actual_hash} (Expected: {expected_hash})")

print(f"All frozen benchmarks intact: {all_frozen_intact}")

