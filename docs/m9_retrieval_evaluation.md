# Milestone M9: Cross-Lingual Retrieval Evaluation & Evidence Consistency

**Milestone Identifier:** M9 (Phase E)  
**Role:** Senior Multilingual Information Retrieval Specialist & Evaluation Auditor  
**Audit Timestamp:** 2026-11-16T19:30:00+05:30  
**Repository:** `C:\Users\anish\Desktop\IndicRAG-QA`  

---

## 1. Executive Summary

Phase E evaluates the cross-lingual retrieval effectiveness and evidence consistency of IndicRAG-QA across the 240 benchmark queries (60 semantic intents $\times$ 4 language variants).

The primary research questions addressed in Phase E are:
1. *Does multilingual retrieval retrieve the same relevant evidence across different query languages?*
2. *Does code-mixing reduce retrieval accuracy?*
3. *Does Hindi in Devanagari script perform comparably to English when querying an English-language academic corpus?*

### Key Quantitative Findings:
- **Document-Level Consensus Across Languages:** **88.89% (40/45 answerable intents)** — In nearly 9 out of 10 intent groups, all four language variants (English, Devanagari Hindi, Romanized Hindi, and Hinglish) successfully retrieved passages from the exact same authoritative target document.
- **Passage-Level Top-5 Agreement Rate:** **22.22% (10/45)** — All four language variants retrieved the exact canonical passage within their top-5 ranked candidates simultaneously in 22.22% of intents.
- **Cross-Lingual Ranking Similarity:**
  - Hinglish (`en-hi`) achieved the highest MRR (**0.2222**) and Hit@5 (**0.2889**), closely followed by Romanized Hindi (`hi-Latn`) (MRR **0.2185**, Hit@5 **0.2889**), and English (MRR **0.2074**, Hit@5 **0.2889**).
  - Devanagari Hindi (`hi`) exhibited slightly lower retrieval accuracy (Hit@5 **0.2222**, MRR **0.1556**).
- **Mean Top-5 Jaccard Evidence Overlap:** **0.1042** across all four language variants for the same semantic intent.

---

## 2. Quantitative Retrieval Metrics by Language

The table below summarizes retrieval metrics calculated over the **45 answerable semantic intent groups** (180 total answerable queries):

| Language Variety | Script | Queries (Ans / Unans) | Hit@1 | Hit@3 | Hit@5 | MRR | nDCG@5 | Avg Latency (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English (`en`)** | `LATIN` | 45 / 15 | **0.1333** | **0.2889** | **0.2889** | **0.2074** | **0.2286** | 1,864.9 ms |
| **Hindi (`hi`)** | `DEVANAGARI` | 45 / 15 | **0.1111** | **0.2222** | **0.2222** | **0.1556** | **0.1725** | 1,155.2 ms |
| **Romanized Hindi (`hi-Latn`)** | `LATIN` | 45 / 15 | **0.1556** | **0.2889** | **0.2889** | **0.2185** | **0.2368** | 1,770.4 ms |
| **Hinglish (`en-hi`)** | `LATIN` | 45 / 15 | **0.1556** | **0.2889** | **0.2889** | **0.2222** | **0.2397** | 1,758.4 ms |

### Latency Observation:
Hindi Devanagari retrieval showed lower latency (1,155 ms vs ~1,800 ms) because BM25 lexical search returns zero candidates on Devanagari text against the English corpus, resulting in smaller candidate lists prior to RRF fusion.

---

## 3. Cross-Lingual Evidence Consistency Analysis

Cross-lingual consistency measures the stability of retrieved evidence across the four parallel language formulations of the same underlying information need.

```
                              Semantic Intent Group (e.g. M9-INT-01)
                                                 │
          ┌──────────────────────┬───────────────┴───────────────┬──────────────────────┐
          ▼                      ▼                               ▼                      ▼
    English Query          Hindi Query                 Romanized Hindi Query        Hinglish Query
  (Top-5 Candidates)     (Top-5 Candidates)           (Top-5 Candidates)          (Top-5 Candidates)
          │                      │                               │                      │
          └──────────────────────┴───────────────┬───────────────┴──────────────────────┘
                                                 │
                                                 ▼
                       Evidence Intersection: Jaccard Overlap = 0.1042
                       Document-Level Agreement: 88.89% (40/45 intents)
```

### 3.1 Key Consistency Findings:
1. **Document-Level Robustness:** In 88.89% of cases, the multilingual dense embedding model (`paraphrase-multilingual-MiniLM-L12-v2`) identifies the correct document cluster (e.g., routing discipline queries to `Students-Discipline-Conduct-Rules-2024.pdf` and attendance queries to `Notification-Minimum-Attendance.pdf` or `Academic-Rules-for-SCSET_UG.pdf`) regardless of query language or script.
2. **Passage Dispersal within Target Documents:** While the correct document is identified, different language formulations frequently surface adjacent or related child passages within the same section. This explains why document consensus is 88.89% while exact passage top-5 intersection is 22.22%.
3. **PDR (Parent Document Retrieval) Mitigation:** The Parent Document Retrieval mechanism implemented in `engine.py` expands retrieved child passages to include parent sections (`expand_to_parents()`), ensuring that generation receives the full contextual envelope even when child passage ranks disperse.

---

## 4. Deliverables Generated

1. **Retrieval Metrics by Language:** [retrieval_metrics_by_language.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/retrieval_metrics_by_language.csv)
2. **Cross-Lingual Evidence Consistency Matrix:** [cross_lingual_evidence_consistency.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/cross_lingual_evidence_consistency.csv)
