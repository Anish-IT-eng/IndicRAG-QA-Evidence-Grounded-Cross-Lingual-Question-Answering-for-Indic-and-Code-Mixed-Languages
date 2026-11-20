import time

def test_import(mod):
    t0 = time.perf_counter()
    __import__(mod)
    print(f"Imported {mod} in {time.perf_counter()-t0:.2f}s", flush=True)

test_import("json")
test_import("numpy")
test_import("faiss")
test_import("rank_bm25")
test_import("torch")
test_import("sentence_transformers")
