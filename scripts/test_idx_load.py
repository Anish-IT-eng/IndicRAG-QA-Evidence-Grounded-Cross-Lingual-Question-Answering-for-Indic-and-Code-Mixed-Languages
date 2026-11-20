import sys
sys.path.insert(0, 'backend')
from app.core.config import settings
from app.retrieval.engine import get_official_index

idx = get_official_index()
print("idx.index_dir:", idx.index_dir)
print("faiss exists:", (idx.index_dir / "faiss.index").exists())
print("meta exists:", (idx.index_dir / "meta.pkl").exists())
print("idx.is_ready():", idx.is_ready())
print("passage_ids count:", len(idx.passage_ids))
print("bm25 is not None:", idx.bm25 is not None)
print("faiss_index is not None:", idx.faiss_index is not None)

