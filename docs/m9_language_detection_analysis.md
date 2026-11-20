# Milestone M9: Language and Script Detection Evaluation & Analysis

**Milestone Identifier:** M9 (Phase C)  
**Role:** Senior Multilingual NLP Architect & Research Evaluation Auditor  
**Audit Timestamp:** 2026-11-16T19:20:00+05:30  
**Repository:** `C:\Users\anish\Desktop\IndicRAG-QA`  

---

## 1. Executive Summary

Phase C provides an independent, quantitative evaluation of IndicRAG-QA's Language Identification (LID) and Script Classification pipeline (`detect_language_and_script()` in `backend/app/query/processor.py`). 

The evaluation tested all **240 queries** of the M9 benchmark dataset across the four linguistic varieties:
- **English (EN)** [60 queries]
- **Hindi Devanagari (HI)** [60 queries]
- **Romanized Hindi (HI-Latn)** [60 queries]
- **Hinglish / Hindi-English Code-Mixed (EN-HI)** [60 queries]

### Key Quantitative Findings:
- **Script Classification Accuracy:** **100.00% (240/240)** — Zero script misclassifications across Latin, Devanagari, and Mixed text.
- **Combined Language Classification Accuracy:** **73.75% (177/240)**.
- **English & Devanagari Precision/Recall:** **1.0000 / 1.0000 (F1 = 1.0000)** for both pure English and Devanagari Hindi.
- **Zero Latin Leakage into English:** Not a single Romanized Hindi or Hinglish query was misclassified as English ($0/120$).
- **Romanized Hindi vs. Code-Mixed Boundary Confusion:** 51 of 60 Romanized Hindi queries were classified as `CODE_MIXED` due to the $\ge 0.25$ keyword density threshold. When evaluated on the coarse task of separating English vs. Devanagari vs. Indic-Latin text, accuracy is **100.00%**.

---

## 2. Quantitative Performance Metrics

### 2.1 Per-Language Evaluation Metrics Table

| Language Variety | Script | Total Support | True Positives | False Positives | False Negatives | Precision | Recall | F1 Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English (`en`)** | `LATIN` | 60 | 60 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** |
| **Hindi (`hi`)** | `DEVANAGARI` | 60 | 60 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** |
| **Romanized Hindi (`hi-Latn`)** | `LATIN` | 60 | 9 | 12 | 51 | **0.4286** | **0.1500** | **0.2222** |
| **Hinglish (`en-hi`)** | `LATIN` | 60 | 48 | 51 | 12 | **0.4848** | **0.8000** | **0.6038** |
| **Overall Strict Accuracy** | — | **240** | **177** | — | — | — | — | **73.75%** |
| **Script Accuracy** | — | **240** | **240** | 0 | 0 | **1.0000** | **1.0000** | **100.0%** |

### 2.2 Confusion Matrix (Rows = Ground Truth, Columns = Predicted)

| Expected \ Predicted | `pred_en` | `pred_hi` | `pred_hi-Latn` | `pred_en-hi` | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Expected `en`** | **60** | 0 | 0 | 0 | 60 |
| **Expected `hi`** | 0 | **60** | 0 | 0 | 60 |
| **Expected `hi-Latn`** | 0 | 0 | **9** | 51 | 60 |
| **Expected `en-hi`** | 0 | 0 | 12 | **48** | 60 |
| **Total Predicted** | 60 | 60 | 21 | 99 | 240 |

---

## 3. Failure Mode & Root Cause Analysis

### 3.1 Root Cause of Romanized Hindi Misclassification as Hinglish
In `backend/app/query/processor.py` (lines 88–96):
```python
hinglish_matches = len(_HINGLISH_RE.findall(text))
word_count = max(len(text.split()), 1)
hinglish_ratio = hinglish_matches / word_count

if hinglish_ratio >= 0.25:
    return QueryLanguage.CODE_MIXED, QueryScript.LATIN

if hinglish_ratio >= 0.10:
    return QueryLanguage.ROMANIZED_HINDI, QueryScript.LATIN
```

Because full Romanized Hindi sentences naturally consist almost entirely of Hindi tokens (e.g. `kya`, `ke`, `liye`, `mein`, `kitna`, `hona`, `chahiye`), the `hinglish_ratio` regularly exceeds 0.25 (often 0.40 to 0.70). Under the current heuristic, the pipeline treats a high ratio of Romanized Hindi function words as evidence of code-mixing rather than pure Romanized Hindi.

### 3.2 Systemic Impact on Downstream Retrieval & Routing
1. **Safety from English Fallback:** Crucially, zero Romanized Hindi or Hinglish queries fell through to the default English route. This prevents BM25 English lexical routing from failing on Indic vocabulary.
2. **Retrieval Route Assignment:**
   - Both `QueryLanguage.CODE_MIXED` and `QueryLanguage.ROMANIZED_HINDI` are routed to dense semantic retrieval and cross-lingual MQR by `AdaptiveRouter.route()`.
   - Consequently, the confusion between Romanized Hindi and Code-Mixed does **not** degrade retrieval routing: both categories trigger the dense multilingual embedding engine (`paraphrase-multilingual-MiniLM-L12-v2`).

### 3.3 Confidence Score Reporting Standard
In adherence to Section 5 ("Do not fabricate confidence values"):
- The current implementation in `processor.py` computes hard heuristic thresholds and does not output a probabilistic confidence score.
- The evaluation dataset explicitly records `"confidence_score": "NOT_SUPPORTED"` to maintain complete scientific integrity.

---

## 4. Deliverables Generated

1. **Itemized Classification Results:** [language_detection_results.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/language_detection_results.csv)
2. **Confusion Matrix:** [language_confusion_matrix.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/language_confusion_matrix.csv)
