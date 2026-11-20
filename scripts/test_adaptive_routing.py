import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

from app.models.schemas import QueryAnalysis, QueryLanguage, QueryScript, DocumentSource
from app.query.processor import process_query
from app.retrieval.engine import get_official_index, retrieve, get_embedding_model

def test_routing():
    root = Path(__file__).resolve().parent.parent
    idx = get_official_index()
    if not idx.is_ready():
        idx.load()
    
    test_cases = [
        # (id, query, expected_routing, category)
        ("T-01", "What is the minimum attendance required for exams?", "cross_encoder", "pure_english"),
        ("T-02", "एंड सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम कितनी उपस्थिति आवश्यक है?", "bi_encoder", "pure_devanagari"),
        ("T-03", "End semester exam mein baithne ke liye minimum kitni attendance chahiye?", "cross_encoder", "romanized_hindi"),
        ("T-04", "End sem exam dene ke liye minimum attendance requirement kya hai?", "cross_encoder", "hinglish_code_mixed"),
        ("T-05", "उपस्थिति 70% attendance", "bi_encoder", "mixed_script_devanagari_dominant"),
        ("T-06", "70% attendance required?", "cross_encoder", "numeric_percentage"),
        ("T-07", "Notification 307 Clause 30.1(v)", "cross_encoder", "technical_regulatory"),
        ("T-08", "   ", "cross_encoder", "whitespace_empty"),
    ]
    
    trace_rows = []
    print(f"{'ID':<6} | {'Category':<25} | {'Detected Lang':<12} | {'Script':<10} | {'Expected':<14} | {'Actual Route':<14} | {'Match'}")
    print("-" * 100)
    
    for tid, q, exp_route, cat in test_cases:
        qa = process_query(q)
        
        # Routing rule check
        is_devanagari = (
            getattr(qa, "detected_script", None) == QueryScript.DEVANAGARI
            or (
                getattr(qa, "detected_language", None) == QueryLanguage.HINDI
                and getattr(qa, "detected_script", None) != QueryScript.MIXED
            )
            or any("\u0900" <= ch <= "\u097f" for ch in (qa.original_query or ""))
        )
        actual_route = "bi_encoder" if is_devanagari else "cross_encoder"
        match = (actual_route == exp_route)
        
        print(f"{tid:<6} | {cat:<25} | {qa.detected_language.value:<12} | {qa.detected_script.value:<10} | {exp_route:<14} | {actual_route:<14} | {match}")
        
        trace_rows.append({
            "test_id": tid,
            "category": cat,
            "query_text": q,
            "detected_language": qa.detected_language.value,
            "detected_script": qa.detected_script.value,
            "expected_routing": exp_route,
            "actual_routing": actual_route,
            "routing_match": match
        })
        
    # Check on all 240 M9 queries
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    print(f"\nEvaluating routing on all {len(m9_queries)} M9 queries...")
    routing_counts = {"en": {}, "hi": {}, "hi-Latn": {}, "en-hi": {}}
    
    for item in m9_queries:
        lang = item["query_language"]
        q_text = item["query_text"]
        qa = process_query(q_text)
        is_devanagari = (
            getattr(qa, "detected_script", None) == QueryScript.DEVANAGARI
            or (
                getattr(qa, "detected_language", None) == QueryLanguage.HINDI
                and getattr(qa, "detected_script", None) != QueryScript.MIXED
            )
            or any("\u0900" <= ch <= "\u097f" for ch in (qa.original_query or ""))
        )
        route = "bi_encoder" if is_devanagari else "cross_encoder"
        routing_counts[lang][route] = routing_counts[lang].get(route, 0) + 1
        
        trace_rows.append({
            "test_id": item["query_id"],
            "category": f"m9_{lang}",
            "query_text": q_text,
            "detected_language": qa.detected_language.value,
            "detected_script": qa.detected_script.value,
            "expected_routing": "bi_encoder" if lang == "hi" else "cross_encoder",
            "actual_routing": route,
            "routing_match": (route == ("bi_encoder" if lang == "hi" else "cross_encoder"))
        })
        
    for lang, counts in routing_counts.items():
        print(f"Lang {lang}: {counts}")
        
    # Save routing trace CSV
    out_csv = root / "backend" / "data" / "experiments" / "m10" / "m10_phase_f_routing_trace.csv"
    import csv
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "test_id", "category", "query_text", "detected_language",
            "detected_script", "expected_routing", "actual_routing", "routing_match"
        ])
        writer.writeheader()
        writer.writerows(trace_rows)
    print(f"\nWrote routing trace to {out_csv}")

if __name__ == "__main__":
    test_routing()
