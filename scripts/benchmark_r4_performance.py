import sys
import time
import json
import statistics
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path("backend").resolve()))

from app.query.processor import process_query
from app.retrieval.multi_hop_reasoner import MultiHopReasoner
from app.generation.generator import generate_answer

def run_performance_benchmark(n_samples=10):
    reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)
    query_str = "What are the attendance rules and medical relaxation guidelines?"
    
    retrieval_times = []
    reasoning_times = []
    total_times = []
    
    print(f"Running Performance Benchmark ({n_samples} warm iterations)...")
    for i in range(n_samples):
        qa = process_query(query_str)
        ev_set = reasoner.reason(qa)
        retrieval_times.append(ev_set.retrieval_ms)
        reasoning_times.append(ev_set.reasoning_ms)
        total_times.append(ev_set.total_ms)
        print(f"  Run {i+1}: Retrieval={ev_set.retrieval_ms:.2f}ms, Reasoning={ev_set.reasoning_ms:.2f}ms, Total={ev_set.total_ms:.2f}ms")

    def calc_stats(arr):
        s = sorted(arr)
        p50 = statistics.median(s)
        p95_idx = int(0.95 * len(s))
        p95 = s[min(p95_idx, len(s)-1)]
        return {
            "mean": statistics.mean(arr),
            "std": statistics.stdev(arr) if len(arr) > 1 else 0.0,
            "min": min(arr),
            "max": max(arr),
            "p50": p50,
            "p95": p95,
        }

    return {
        "sample_count": n_samples,
        "retrieval_stats": calc_stats(retrieval_times),
        "reasoning_stats": calc_stats(reasoning_times),
        "total_stats": calc_stats(total_times),
        "mean_reasoning_overhead": (statistics.mean(reasoning_times) / statistics.mean(total_times)) * 100,
    }

if __name__ == "__main__":
    bench = run_performance_benchmark(5)
    print("\nBENCHMARK RESULTS:")
    print(json.dumps(bench, indent=2))
