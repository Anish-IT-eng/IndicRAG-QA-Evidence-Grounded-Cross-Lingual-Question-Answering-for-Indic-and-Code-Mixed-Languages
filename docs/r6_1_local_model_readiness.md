# IndicRAG-QA — R6.1 Local Model Readiness and Hardware Audit

**Audit Date:** 2026-11-19  
**Auditor Role:** Runtime Systems & LLM Infrastructure Auditor  
**Milestone:** R6 Task 1.1 Benchmark Integrity and Runtime Readiness Correction  
**Determination:** **RUNTIME_HARDWARE_AND_MODELS_CONFIRMED**  

---

## 1. Executive Summary

In R6 Task 1, the evaluation design proposed testing `qwen2.5:7b-instruct` and `llama3.1:8b` as primary and comparator models. An audit of the local Ollama runtime and host hardware reveals that **neither 7B nor 8B models are installed locally**, and downloading new models is strictly prohibited by evaluation constraints.

Furthermore, host hardware profiling demonstrates that the machine has **4.03 GB of available RAM** (out of 15.69 GB total, 74.3% utilized). Attempting to execute a 7B or 8B model (which requires 5.5–8.5 GB of resident memory plus Ollama runtime buffers) would induce severe out-of-memory (OOM) failures or crippling page thrashing.

The local Ollama environment possesses three fully installed, healthy models: **`qwen2.5:3b`**, **`llama3.2:3b`**, and **`gemma:2b`**. Notably, `backend/app/core/config.py` is **already pre-configured to use `qwen2.5:3b`** as its default production model. Therefore, R6 execution will be executed using **`qwen2.5:3b`** as the primary production generator, with **`llama3.2:3b`** available for optional comparative analysis.

---

## 2. Ollama Model Inventory & Availability Status

The local Ollama daemon (`http://localhost:11434`) was queried directly via `ollama list` and `GET /api/tags`:

### A. Confirmed Installed Models

| Model Tag | Digest | Format | Parameters | Quantization | Context Window | File Size | Readiness Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`qwen2.5:3b`** (latest) | `357c53fb659c...` | GGUF | 3.1B | Q4_K_M | 32,768 tokens | 1.93 GB | **CONFIRMED INSTALLED (Primary)** |
| **`llama3.2:3b`** (latest) | `a80c4f17ced5...` | GGUF | 3.2B | Q4_K_M | 131,072 tokens | 2.01 GB | **CONFIRMED INSTALLED (Comparator)** |
| **`gemma:2b`** (latest) | `b50d6c999e33...` | GGUF | 3.0B | Q4_0 | 8,192 tokens | 1.68 GB | **CONFIRMED INSTALLED (Fallback)** |

### B. Proposed but Unavailable Models

| Proposed Model Name | Status in Local Runtime | Requirement to Obtain | Viability under Constraints |
| :--- | :--- | :--- | :--- |
| **`qwen2.5:7b-instruct`** | **NOT INSTALLED** | `ollama pull qwen2.5:7b` (4.7 GB download) | **STRICTLY PROHIBITED** (Violates zero-download rule; exceeds available RAM) |
| **`llama3.1:8b`** | **NOT INSTALLED** | `ollama pull llama3.1:8b` (4.9 GB download) | **STRICTLY PROHIBITED** (Violates zero-download rule; exceeds available RAM) |

---

## 3. Host Hardware Profile and Resource Constraints

System resource telemetry gathered via `psutil` on the execution host:

| Resource Parameter | Measured Value | Operational Implications for LLM Inference |
| :--- | :--- | :--- |
| **OS** | Windows 11 Pro (x64) | PowerShell execution environment |
| **CPU Architecture** | 12 Physical Cores, 16 Logical Threads | Excellent multi-threaded CPU inference capability for 3B models |
| **Total System RAM** | 15.69 GB (16,071 MB) | Host workstation memory |
| **Available RAM** | **4.03 GB (4,128 MB)** | Current free memory headroom after OS and active processes |
| **Memory Utilization** | **74.3%** | Moderate host memory pressure |
| **GPU / Acceleration** | Standard Direct3D/Intel/Integrated | Ollama operates in CPU mode with thread parallelism |

### Memory Budget Analysis: Why 3B is the Only Viable Architecture
- **Memory footprint of `qwen2.5:3b`:**
  - Model weights: 1.93 GB.
  - KV-cache & context buffers (up to 4,096 tokens): ~0.35 GB.
  - Total resident working set: **~2.28 GB**.
  - Fits comfortably within the **4.03 GB** available headroom with ~1.75 GB safety buffer.
- **Memory footprint of a 7B / 8B model:**
  - Model weights: ~4.7–5.2 GB.
  - KV-cache: ~0.8 GB.
  - Total resident working set: **~5.5–6.0 GB**.
  - **Deficit:** Exceeds the 4.03 GB available RAM by >1.5 GB. Running 7B/8B on this host would immediately cause Windows pagefile thrashing, extreme latencies (>120s timeouts), or outright Out-Of-Memory termination.

---

## 4. Application Configuration Alignment

Inspection of `backend/app/core/config.py` confirms that the production codebase is already engineered for the installed local environment:

```python
# backend/app/core/config.py
class Settings(BaseSettings):
  ollama_model: str = "qwen2.5:3b"
  ollama_base_url: str = "http://localhost:11434"
  ollama_timeout: float = 120.0
  embedding_model_name: str = (
      "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  )
  rerank_strategy: str = "production"
  cross_encoder_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
```

1. **Model Alignment:** `settings.ollama_model` defaults to `"qwen2.5:3b"`, which is physically installed and operational.
2. **Timeout Headroom:** `settings.ollama_timeout = 120.0` provides ample margin for 3B generations on a 16-thread CPU (typical completion latency is 6–12 seconds).
3. **No Codebase Modification Required:** Running R6 with `qwen2.5:3b` requires zero configuration patching, preserving production invariants.

---

## 5. Formal Recommendations for R6 Evaluation

1. **Primary Production Model:** Standardize all R6 generation tasks (Smoke test Stage 2, Grounding Stage 6, Multilingual Stage 7, Abstention Stage 8, Feedback Stage 9) on **`qwen2.5:3b`**.
2. **Cross-Model Comparator (Optional):** If comparative evaluation is required, use **`llama3.2:3b`**, which is confirmed installed, has a 131k context window, and fits within the memory budget.
3. **Strict Invariants Enforced:**
   - **Zero downloads:** No calls to `ollama pull` or Hugging Face hub.
   - **Zero paid APIs:** No dependencies on OpenAI, Anthropic, or external cloud LLMs.
   - **Zero config tampering:** Maintain `settings.rerank_strategy == "production"`.
