import sys, os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.abspath("backend"))

print("Importing modules...", flush=True)
from app.query.processor import process_query
from app.retrieval.engine import retrieve, get_official_index
from app.models.schemas import DocumentSource

print("Getting official index...", flush=True)
idx = get_official_index()
print(f"Official index ready? {idx.is_ready()}, Passages in index: {len(idx.passage_ids)}", flush=True)

print("Processing query...", flush=True)
qa = process_query("What is the minimum attendance required?")
print("Running retrieve...", flush=True)
res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5)
print(f"Retrieve finished! Got {len(res.retrieved_passages)} passages.", flush=True)
for p in res.retrieved_passages:
    print(f" - [{p.passage_id}] p.{p.page_number} ({p.document_id})", flush=True)
