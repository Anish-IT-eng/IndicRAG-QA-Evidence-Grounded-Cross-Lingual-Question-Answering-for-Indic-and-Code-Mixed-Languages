"""
Evaluates the Language Identification (LID) and Script Detection pipeline
against the 240 queries in the M9 evaluation dataset.
Outputs:
- backend/data/experiments/m9/language_detection_results.csv
- backend/data/experiments/m9/language_confusion_matrix.csv
"""
import json
import csv
import sys
import os

# Ensure backend in path
sys.path.insert(0, os.path.abspath("backend"))

from app.query.processor import detect_language_and_script
from app.models.schemas import QueryLanguage, QueryScript

# Load dataset
queries = []
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            queries.append(json.loads(line))

lang_map = {
    "en": QueryLanguage.ENGLISH,
    "hi": QueryLanguage.HINDI,
    "hi-Latn": QueryLanguage.ROMANIZED_HINDI,
    "en-hi": QueryLanguage.CODE_MIXED,
}

script_map = {
    "LATIN": QueryScript.LATIN,
    "DEVANAGARI": QueryScript.DEVANAGARI,
    "MIXED": QueryScript.MIXED,
}

results = []
confusion = {
    "en": {"en": 0, "hi": 0, "hi-Latn": 0, "en-hi": 0},
    "hi": {"en": 0, "hi": 0, "hi-Latn": 0, "en-hi": 0},
    "hi-Latn": {"en": 0, "hi": 0, "hi-Latn": 0, "en-hi": 0},
    "en-hi": {"en": 0, "hi": 0, "hi-Latn": 0, "en-hi": 0},
}

rev_lang_map = {
    QueryLanguage.ENGLISH: "en",
    QueryLanguage.HINDI: "hi",
    QueryLanguage.ROMANIZED_HINDI: "hi-Latn",
    QueryLanguage.CODE_MIXED: "en-hi",
    QueryLanguage.UNKNOWN: "unknown",
}

for q in queries:
    qid = q["query_id"]
    text = q["query_text"]
    exp_lang = q["query_language"]
    exp_script = q["script"]
    
    pred_lang_obj, pred_script_obj = detect_language_and_script(text)
    pred_lang = rev_lang_map.get(pred_lang_obj, "unknown")
    pred_script = pred_script_obj.value if hasattr(pred_script_obj, "value") else str(pred_script_obj)
    
    lang_correct = (pred_lang == exp_lang)
    script_correct = (pred_script.upper() == exp_script.upper())
    
    failure_reason = ""
    if not lang_correct:
        failure_reason = f"Language misclassified as {pred_lang} instead of {exp_lang}"
    elif not script_correct:
        failure_reason = f"Script misclassified as {pred_script} instead of {exp_script}"
        
    if exp_lang in confusion and pred_lang in confusion[exp_lang]:
        confusion[exp_lang][pred_lang] += 1
        
    results.append({
        "query_id": qid,
        "intent_id": q["intent_id"],
        "query_text": text,
        "expected_language": exp_lang,
        "predicted_language": pred_lang,
        "expected_script": exp_script,
        "predicted_script": pred_script,
        "language_correct": lang_correct,
        "script_correct": script_correct,
        "overall_correct": (lang_correct and script_correct),
        "confidence_score": "NOT_SUPPORTED",  # Honest documentation: heuristic produces no confidence
        "failure_reason": failure_reason,
    })

# Write results CSV
with open("backend/data/experiments/m9/language_detection_results.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "query_id", "intent_id", "query_text", "expected_language", "predicted_language",
        "expected_script", "predicted_script", "language_correct", "script_correct",
        "overall_correct", "confidence_score", "failure_reason"
    ])
    writer.writeheader()
    writer.writerows(results)

# Write Confusion Matrix CSV
with open("backend/data/experiments/m9/language_confusion_matrix.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["expected_language", "pred_en", "pred_hi", "pred_hi-Latn", "pred_en-hi"])
    for el in ["en", "hi", "hi-Latn", "en-hi"]:
        writer.writerow([el, confusion[el]["en"], confusion[el]["hi"], confusion[el]["hi-Latn"], confusion[el]["en-hi"]])

# Calculate Metrics
total = len(results)
correct_lang = sum(1 for r in results if r["language_correct"])
correct_script = sum(1 for r in results if r["script_correct"])
overall_correct = sum(1 for r in results if r["overall_correct"])

print(f"Total Queries Evaluated: {total}")
print(f"Language Accuracy: {correct_lang}/{total} ({correct_lang/total*100:.2f}%)")
print(f"Script Accuracy: {correct_script}/{total} ({correct_script/total*100:.2f}%)")
print(f"Combined Strict Accuracy: {overall_correct}/{total} ({overall_correct/total*100:.2f}%)")

print("\nPer-Language Breakdown:")
for lang in ["en", "hi", "hi-Latn", "en-hi"]:
    tp = confusion[lang][lang]
    fp = sum(confusion[other][lang] for other in confusion if other != lang)
    fn = sum(confusion[lang][other] for other in confusion[lang] if other != lang)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    print(f"  {lang:7s} | Support: {tp+fn} | TP: {tp:2d} | FP: {fp:2d} | FN: {fn:2d} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f}")

print("\nConfusion Matrix (Rows=Expected, Cols=Predicted):")
print("          pred_en  pred_hi  pred_hi-Latn  pred_en-hi")
for el in ["en", "hi", "hi-Latn", "en-hi"]:
    print(f"  {el:7s}   {confusion[el]['en']:7d}  {confusion[el]['hi']:7d}       {confusion[el]['hi-Latn']:7d}      {confusion[el]['en-hi']:7d}")
