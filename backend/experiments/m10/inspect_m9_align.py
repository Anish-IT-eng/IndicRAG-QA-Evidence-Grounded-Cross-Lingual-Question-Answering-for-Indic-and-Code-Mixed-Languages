import csv
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
m9_claims = list(csv.DictReader(open(root / "backend/data/experiments/m9/claim_grounding_results.csv", encoding="utf-8")))
m9_cits = list(csv.DictReader(open(root / "backend/data/experiments/m9/citation_quality_results.csv", encoding="utf-8")))

print(f"M9 claims count: {len(m9_claims)}")
print(f"M9 citations count: {len(m9_cits)}")

# Check query IDs in claims
claim_qids = set(c["query_id"] for c in m9_claims)
cit_qids = set(c["query_id"] for c in m9_cits)
print(f"Claim QIDs: {len(claim_qids)}, Cit QIDs: {len(cit_qids)}")
print("QIDs in claims but not cits:", claim_qids - cit_qids)
print("QIDs in cits but not claims:", cit_qids - claim_qids)
