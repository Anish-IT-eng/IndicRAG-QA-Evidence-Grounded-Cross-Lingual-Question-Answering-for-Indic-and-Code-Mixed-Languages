# M10 Phase G: End-to-End Answer Quality & Grounding Statistical Analysis

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-END-TO-END-ANALYSIS`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Status:** Audit Completed  

---

## 1. Executive Summary

This document evaluates whether the retrieval improvements observed in Candidate E6b translate into reliable end-to-end answers, and whether downstream answer accuracy, safe abstention, and factual grounding are maintained.

Key conclusions:
1. **End-to-End Answerable Success:** Candidate E6b unlocked 2 verified end-to-end answers in Devanagari Hindi ($0/45 \to 2/45$), improving overall answerable success from $59/180$ (32.8%) to $61/180$ (33.9%). Under exact McNemar testing ($b=0, c=2$), this change yields $p = 0.5000$.
2. **Safe Abstention Preserved (Zero Degradation):** On unanswerable queries ($N=60$), both configurations achieved identical $58/60$ (96.7%) correct abstentions ($p = 1.0000$). Candidate E6b did not trigger any false-positive hallucinated answers on unanswerable intents.
3. **Zero Unsupported Answers (Grounded Safety):** Across all 61 generated responses in Config B, zero hallucinations or unsupported claims occurred ($0/61 = 0.0\%$). By the Rule of Three, the 95% upper confidence bound on the true hallucination rate is 4.91%.
4. **The Evidence Controller Bottleneck:** While retrieval recovered 4 passages in Devanagari Top-5 (`M9-Q002`, `Q010`, `Q014`, `Q030`), the Evidence Controller correctly accepted only 2 for generation (`M9-Q014` and `Q030`), appropriately rejecting `M9-Q002` and `Q010` due to marginal passage-question entailment thresholds.

---

## 2. End-to-End Correctness Categorization

All 480 end-to-end query evaluations from Phase F were classified into standard regulatory QA categories:

| Category | Description | Safety Profile | Desired on Answerable? | Desired on Unanswerable? |
|---|---|:---:|:---:|:---:|
| `CORRECT_ANSWERED` | Direct factual answer grounded in retrieved regulatory clause | Safe | Yes | No |
| `REGULATORY_DISCLOSURE` | Answer discloses regulatory bounds/exceptions accurately | Safe | Yes | No |
| `UNNECESSARY_ABSTENTION` | System abstained despite answerable intent | Conservative | No | No |
| `CORRECT_ABSTENTION` | System refused to answer out-of-scope/unanswerable query | Safe | No | Yes |
| `UNSUPPORTED_ANSWER` | Hallucinated claim or unverified citation | Unsafe | No | No |

---

## 3. End-to-End Success Rate Analysis

Answerable Success is defined as $\frac{\text{CORRECT\_ANSWERED} + \text{REGULATORY\_DISCLOSURE}}{N_{\text{answerable}}}$.

### 3.1 Per-Language Answerable Performance ($N=45$)

| Language Formulation | Config A (Prod) | Config B (E6b) | Absolute Diff | McNemar Discordant ($b, c$) | McNemar Exact $p$ | Wilson 95% CI (Config B) |
|---|---:|---:|---:|:---:|---:|:---:|
| **English (`en`)** | 28 / 45 (62.2%) | 28 / 45 (62.2%) | 0.0% | $b=0, c=0$ | 1.0000 | [47.6%, 74.9%] |
| **Devanagari (`hi`)** | 0 / 45 (0.0%) | 2 / 45 (4.4%) | +4.4% | $b=0, c=2$ | 0.5000 | [1.2%, 14.8%] |
| **Romanized (`hi-Latn`)** | 14 / 45 (31.1%) | 14 / 45 (31.1%) | 0.0% | $b=0, c=0$ | 1.0000 | [19.5%, 45.9%] |
| **Hinglish (`en-hi`)** | 17 / 45 (37.8%) | 17 / 45 (37.8%) | 0.0% | $b=0, c=0$ | 1.0000 | [25.1%, 52.4%] |
| **Overall Pooled ($N=180$)** | **59 / 180 (32.8%)** | **61 / 180 (33.9%)** | **+1.1%** | **$b=0, c=2$** | **0.5000** | **[27.4%, 41.1%]** |

### 3.2 Detailed Audit of Devanagari Recovered Answers

In Config A, Devanagari Hindi achieved 0 successful answers out of 45 due to retrieval failure and downstream abstention. In Config B, two intents achieved complete end-to-end recovery:

1. **`M9-Q014` (Academic Probation Criteria):**
   - *Query:* "यदि किसी छात्र का CGPA 4.5 से कम हो जाता है तो क्या परिणाम होंगे?"
   - *Retrieved Passage:* `86f68c7e` (Clause 18, Academic Probation & Minimum CGPA Requirements).
   - *Evidence Controller Decision:* ACCEPTED (entailment score: 0.842).
   - *Generated Answer:* Accurately stated that students with CGPA $< 4.5$ are placed on Academic Probation and must repeat courses to improve standing.
   - *Citation:* Clause 18, SCSET UG Rules 2022 (Verified).

2. **`M9-Q030` (Re-evaluation Fee & Process):**
   - *Query:* "उत्तर पुस्तिका के पुनर्मूल्यांकन के लिए क्या प्रक्रिया और शुल्क है?"
   - *Retrieved Passage:* `7181c039` (Clause 28.3, Re-evaluation Procedure & Fee Structure).
   - *Evidence Controller Decision:* ACCEPTED (entailment score: 0.791).
   - *Generated Answer:* Specified the 15-day application window and Rs. 500 fee per course.
   - *Citation:* Clause 28.3, Ordinances 2017 (Verified).

---

## 4. Abstention Fidelity on Unanswerable Queries

Evaluating safety on out-of-scope regulatory questions ($N=15$ intents per language, $N=60$ total):

| Language Formulation | Total Unanswerable | Config A Correct Abstentions | Config B Correct Abstentions | Abstention Rate | McNemar $p$ | Wilson 95% CI |
|---|---:|---:|---:|---:|---:|:---:|
| English (`en`) | 15 | 13 | 13 | 86.7% | 1.0000 | [62.1%, 96.3%] |
| Devanagari (`hi`) | 15 | 15 | 15 | 100.0% | 1.0000 | [79.6%, 100.0%] |
| Romanized (`hi-Latn`) | 15 | 15 | 15 | 100.0% | 1.0000 | [79.6%, 100.0%] |
| Hinglish (`en-hi`) | 15 | 15 | 15 | 100.0% | 1.0000 | [79.6%, 100.0%] |
| **Overall Pooled** | **60** | **58** | **58** | **96.7%** | **1.0000** | **[88.6%, 99.1%]** |

Both configurations demonstrated identical, highly disciplined abstention behavior ($b=0, c=0$). On the two English queries where the system did not abstain (`AQ-04` and `AQ-07`), it returned a `REGULATORY_DISCLOSURE` explaining partial regulatory jurisdiction rather than a hallucination.

---

## 5. Factual Grounding & Zero Hallucination Upper Bound

A critical requirement in regulatory QA is verifying that no unsupported or hallucinated assertions are delivered to the user.

Across both configurations:
- Config A generated 59 answers (52 direct answers + 7 regulatory disclosures).
- Config B generated 61 answers (53 direct answers + 8 regulatory disclosures).
- Every generated statement was mapped to its retrieved source clause using sentence-level citation verification.
- **Unsupported Answer Rate:** $0 / 61 = 0.0000$ (0.0%).

### 5.1 Mathematical Upper Bound (Rule of Three)

When an event occurs 0 times in $N$ Bernoulli trials, the sample proportion $\hat{p} = 0$ does not mean the true underlying probability is zero. Under the Poisson approximation to the binomial distribution:
$$P(\text{zero errors}) = (1 - p)^N \approx e^{-N p}$$
To find the 95% upper confidence bound $p_{\text{upper}}$ such that $P(\text{zero errors}) = 0.05$:
$$e^{-N p_{\text{upper}}} = 0.05 \implies -N p_{\text{upper}} = \ln(0.05) \approx -2.9957 \approx -3$$
$$p_{\text{upper}} = \frac{3}{N}$$

For Config B ($N = 61$ generated answers):
$$p_{\text{upper}} = \frac{3}{61} \approx 0.04918 \quad (4.92\%)$$

**Conclusion:** We can state with 95% statistical confidence that the true underlying unsupported answer rate of Config B is **less than 4.92%**. This provides a rigorous mathematical upper bound on hallucination risk in the current operational environment.
