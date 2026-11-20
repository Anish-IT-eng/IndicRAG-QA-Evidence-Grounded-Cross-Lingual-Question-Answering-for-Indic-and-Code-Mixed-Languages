import sys
import sqlite3
import hashlib
from pathlib import Path

# Run preflight hash checks
sys.path.insert(0, str(Path('backend').resolve()))
from scripts.preflight_phase2c import compute_corpus_hash

db_path = Path('backend/data/db/indicrag.db')
corpus_hash = compute_corpus_hash(db_path)
print(f"Corpus SHA-256: {corpus_hash} (Match: {corpus_hash == '8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d'})")

with open('backend/data/dataset/final_verified_dataset.csv', 'rb') as f:
    m3_hash = hashlib.sha256(f.read()).hexdigest()
print(f"M3 Frozen SHA-256: {m3_hash} (Match: {m3_hash == '093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520'})")

with open('backend/data/dataset/m6_expanded_benchmark_n60.csv', 'rb') as f:
    m6_hash = hashlib.sha256(f.read()).hexdigest()
print(f"M6 Bench SHA-256: {m6_hash} (Match: {m6_hash == 'a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae'})")

with open('backend/data/dataset/m6_benchmark_qualification.csv', 'rb') as f:
    qual_hash = hashlib.sha256(f.read()).hexdigest()
print(f"Qual Ledger SHA-256: {qual_hash} (Match: {qual_hash == 'db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13'})")

