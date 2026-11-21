# Root Cause Analysis: Retrieval and Ingestion Failure for Official PDF Documents

**Document Title**: Root Cause Analysis — SSR Official Document Ingestion & Retrieval Failure  
**Component**: Ingestion Pipeline, Table Extractor, Query Processor, Evidence Controller & Answer Generator  
**Document Tested**: `UPUNGN113496_SSR_BU.pdf` (Bennett University Self Study Report)  
**Failing Query**: `"what is total campus green spaces dedicated by campus"`  
**Observed Behavior**: System retrieved Page 8 mentioning restricted automobile entry, bicycles, pedestrian pathways, and plastic usage, but completely omitted the green-space acreage (over 12 acres).

---

## 1. Executive Summary

A comprehensive, stage-by-stage audit of the IndicRAG-QA ingestion and retrieval pipeline uncovered five interlocking root causes that together caused retrieval and answer failure on unstructured PDF documents like the Self Study Report (SSR):

1. **Table Extraction False-Positive Overreach (`table_extractor.py`)**: A coordinate-clustering heuristic falsely classified 52 out of 116 pages of prose narrative as multi-column Markdown tables (`| Col_1 | Col_2 | Col_3 | Col_4 |`). In `pdf_extractor.py`, the presence of any detected table completely bypassed sentence-boundary prose extraction, fragmenting sentences across dummy columns and corrupting textual coherence.
2. **Stale Duplicate Document Ingestion Artifacts in Vector & Lexical Stores**: Multiple ingestion runs resulted in duplicate documents (`document_id = "ac863c8b-c853-4041-b5e7-412067c12a85"` with 244 corrupted chunks alongside `"e569e7e9-6565-4edf-8d6e-965590657720"`). Stale chunks containing fragmented text competed with and depressed the rank of clean passages.
3. **Query Classifier Gap for Quantitative Queries (`processor.py`)**: The query classifier's regular expressions for `QuestionType.NUMERICAL` lacked patterns for `total`, `how much`, `area`, `acres`, `hectares`, `count`, etc. As a result, the query was categorized as `QuestionType.DIRECT`, preventing the generator from applying quantitative synthesis rules.
4. **Context Dilution & "Lost in the Middle" on Small Local LLM (`generator.py`)**: The generator previously formatted all 10 retrieved passages into the LLM prompt (~15,000 characters / 3,500+ tokens). On local 3B parameter models (`qwen2.5:3b`), this massive context diluted attention away from concise facts located on Page 102 and Page 8 toward earlier administrative sections.
5. **Prompt Negative Priming & Truncation Flaws (`generator.py`)**:
   - The user prompt template repeated `"If the answer cannot be determined from the evidence, output UNANSWERABLE"`, which induced negative priming in the 3B model, causing it to default to `UNANSWERABLE`.
   - `num_predict` in `_call_ollama` was hardcoded to `min(settings.generation_max_tokens, 256)`, truncating generation right while the model was writing citation tags (`[Source: passage_id=...`).
   - Windows CRLF (`\r\n`) line endings caused citation extraction regexes to miss newline-separated citations.

---

## 2. Stage-by-Stage Pipeline Trace

| Stage | Input | Expected Output | Actual Behavior (Before Fix) | Root Cause |
|---|---|---|---|---|
| **1. PDF Ingestion & Extraction** | `UPUNGN113496_SSR_BU.pdf` | Clean page-level text, headings, and tables | 52 of 116 pages converted into dummy 4-column tables (`Col_1..Col_4`). Sentence boundary splitting bypassed. | Flawed table heuristic in `table_extractor.py` and `if page.tables:` bypass in `pdf_extractor.py`. |
| **2. Chunking & Metadata** | Raw extracted pages | Child passages with parent section context, page numbers, clean text | Narrative paragraphs were chopped across dummy columns, separating numbers from nouns. | Table bypass prevented sentence boundary chunking. |
| **3. BM25 & FAISS Indexing** | Document chunks | Synchronized lexical and dense representations | Duplicate stale documents in SQLite and FAISS caused index bloat (957 passages vs clean 713). | Ingestion pipeline did not enforce single-instance document purging on re-upload. |
| **4. Query Classification** | `"what is total campus green spaces dedicated by campus"` | `QuestionType.NUMERICAL`, language: English | Classified as `QuestionType.DIRECT`. | `_NUMERICAL_PATTERNS` in `processor.py` omitted `total`, `area`, `acres`, `how much`. |
| **5. Hybrid Retrieval & Reranker** | Query + Upload Collection | Page 102 & Page 8 in top-k | Retrieved Page 102 (rank 1) and Page 8 (rank 7/10), but accompanied by 8 lengthy distractor passages. | Context bloat (10 passages = 3,500+ tokens). |
| **6. Evidence Controller (CECI)** | Retrieved passages | `SUFFICIENT` or `PARTIAL` decision | Correctly identified Stage 1 sufficiency, but CECI threshold `tau_insuff=0.35` narrowly rejected queries with `CECI=0.346`. | Rigid `tau_insuff` threshold. |
| **7. Answer Generation (Ollama)** | Evidence passages + User Prompt | Direct answer stating `"over 12 acres"` with citation | Outputted general summary of bicycle/pathway initiatives or defaulted to `UNANSWERABLE`. | Negative priming in prompt template, context dilution over 10 chunks, and token truncation. |
| **8. Citation Extraction** | LLM text with `[Source: ...]` | `[Citation(doc=SSR, page=102)]` | Truncated citation strings (`[Source: 2f8332fe...`) failed bracket regex, or fell back to lexical overlap without numerical weighting. | Regex required `\]`; fallback didn't score numerical overlap. |

---

## 3. Detailed Technical Breakdown of Root Causes

### Root Cause 1: Table Detection False-Positive Overreach (`table_extractor.py`)
In `table_extractor.py`, text blocks were projected onto the horizontal X-axis and clustered using `centers = [g[0] for g in groups]`. If `len(centers) >= 3`, the algorithm declared the page a 3- or 4-column table, even if the page was ordinary narrative text with indented paragraphs, bullet points, or wide margins. Furthermore, `TableContext` carried over across pages without validating whether column positions aligned.

In `pdf_extractor.py`:
```python
# Before:
if page.tables:
    for table in page.tables:
        chunks.append(table_chunk)
    # Prose extraction was completely skipped!
```
Because of this, 52 pages of the SSR—including Criterion 7.1.4 on Page 102—were rendered as dummy tables:
```markdown
| Col_1 | Col_2 | Col_3 | Col_4 |
| --- | --- | --- | --- |
| Self Study Report of BENNETT UNIVERSITY | | | |
| Describe the Green campus initiative... | | | |
```
This shredded sentences across columns and destroyed semantic coherence.

### Root Cause 2: Query Classification Omission (`processor.py`)
In `processor.py`, `_NUMERICAL_PATTERNS` only matched:
- `\bhow\s+(many|much)\b`
- `\bpercentage\b`, `\bpercent\b`, `\bmarks\b`, `\bcredits?\b`
- `\bminimum\s+attendance\b`

Questions such as:
- `what is total campus green spaces dedicated by campus`
- `what is the total green space on campus`
- `what is the area allocated to campus landscaping`

did not match any pattern and defaulted to `QuestionType.DIRECT`. Consequently, the prompt did not instruct the LLM to lead with the quantitative figure.

### Root Cause 3: Prompt Negative Priming on Small LLMs (`generator.py`)
Small 3B models (`qwen2.5:3b`) are susceptible to negative prompt priming. When the prompt repeated:
`"If the requested numerical fact or measurement is not stated in the evidence, output UNANSWERABLE."`
alongside:
`"If the answer cannot be determined from the evidence, output UNANSWERABLE."`
the model often defaulted to `UNANSWERABLE` even when the evidence was present in the context.

### Root Cause 4: Generation Truncation & Citation Dropping (`generator.py`)
In `_call_ollama`, token prediction was capped at `min(settings.generation_max_tokens, 256)`. Because the evidence summary took ~220 tokens, the generation was cut off right as the model was emitting the source marker:
`... facilitating seamless cross-collaboration and knowledge sharing. [Source: 2f8332fe-db18-4f3c-8e9b-38c`
Because the closing bracket `]` was never generated, standard regexes failed to match the citation.

---

## 4. Verification of Document Evidence in SSR

Inspection of the raw text extracted from `UPUNGN113496_SSR_BU.pdf` confirms the ground-truth facts:
- **Page 8 (Executive Summary, Best Practice 2)**:
  > *"BU champions the cause for environmental sustainability with green coverage of over 12 acres and 2,000+ geo-tagged trees. The University promotes pedestrian pathways, usage of e-golf carts and restricts automobile use on campus."*
- **Page 102 (Criterion 7.1.4: Institutional Values and Best Practices - Green Campus Initiatives)**:
  > *"BU campus boasts over 12 acres of green space dedicated to greenery. This includes over 2,000 fully grown trees, with many geo-tagged."*

Both pages explicitly verify that the campus dedicates **over 12 acres** to green spaces and has **over 2,000 geo-tagged / fully grown trees**.
