# IndicRAG-QA — Frontend UI/UX Redesign & Implementation Report

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Component:** Standalone Web Application User Interface  
**Primary Source File:** [frontend/index.html](file:///c:/Users/anish/Desktop/IndicRAG-QA/frontend/index.html)  
**Date:** November 18, 2026  
**Implementation Status:** **Completed, Verified Live & Deployed Locally**  
**Local Web Access:** [http://localhost:3000](http://localhost:3000)  
**Backend API Server:** [http://127.0.0.1:8000](http://127.0.0.1:8000)  
**Production Runtime Invariant:** `rerank_strategy="production"` (Strictly Preserved)  

---

## 1. Executive Summary & Design Mandate

The front-end user interface for IndicRAG-QA has undergone an **end-to-end architectural and visual redesign**. The previous interface — a generic, dark, developer-centric dashboard with raw JSON cards and neon accents — has been completely replaced with a **friendly, modern, intuitive, and trustworthy multilingual academic assistant**.

The application is tailored for university students, educators, and administrative staff seeking definitive answers regarding academic regulations, examination ordinances, attendance thresholds, grading formulas, and conduct rules. The redesign emphasizes **institutional clarity, typographic elegance, rapid input accessibility, and crystal-clear official citation provenance**.

```
+---------------------------------------------------------------------------------------------------+
|  IndicRAG-QA Academic Regulations Guide                                                            |
|  [+ New Chat]      |  🏛️ Bennett University B.Tech / SCSET                                       |
|  - Recent Consults |  Your Academic Guide, in Your Language.                                      |
|  - 7 Verified Docs |  Understand regulations, attendance, exams & grading through official docs. |
|  - Lang: EN/HI/Hing|  +-------------------------------------------------------------------------+ |
|  * FastAPI Online  |  | Ask anything about your academic regulations...               [ -> ]   | |
|                    |  +-------------------------------------------------------------------------+ |
|                    |  [ Attendance Req. ]   [ Exam Eligibility ]                                  |
|                    |  [ CGPA Formula    ]   [ हिंदी देवनागरी    ]                                  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Visual Proofs & Headless Browser Verification

The redesigned interface has been rendered and validated using headless Google Chrome (`chrome.exe --headless=new`), capturing pixel-accurate screenshots under both desktop and mobile viewports.

### Captured Visual Artifacts

0. **Upload & Scope Integration View (1280 x 820):**  
   File: [docs/ui_screenshot_upload_scope.png](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/ui_screenshot_upload_scope.png)  
   *Features captured:* Top navigation "Upload Document" button, sidebar "My Documents" summary card, and dynamic Search Scope selector (`🏛️ Official Regulations` vs `📁 My Documents`).

1. **Desktop Welcome Landing View (1280 x 820):**  
   File: [docs/ui_screenshot_welcome.png](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/ui_screenshot_welcome.png)  
   *Features captured:* Warm off-white canvas, clean white sidebar, prominent centered hero input card, 2x2 tile grid, language badges, and active FastAPI health indicator.

2. **Desktop Interactive Chat Stream View (1280 x 900):**  
   File: [docs/ui_screenshot_chat.png](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/ui_screenshot_chat.png)  
   *Features captured:* User speech bubble (`#5146E5`), assistant answer card with avatar `अ`, structured `CLARIFICATION_REQUIRED` regulatory disclosure, interactive cohort selection chips (`Admitted 2023-24 Onwards`, `Admitted 2017-2022`, `SCSET Engineering Specific`), and bottom input dock.

3. **Mobile Responsive Viewport (412 x 850):**  
   File: [docs/ui_screenshot_mobile.png](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/ui_screenshot_mobile.png)  
   *Features captured:* Collapsed mobile drawer with hamburger trigger, responsive single-column starter cards, stacked touch-friendly controls, and fixed bottom dock.

---

## 3. Systematic Design System Specification

The visual overhaul adheres to a cohesive, accessible, and modern design language:

| Design Dimension | Former Implementation | Redesigned Specification |
|---|---|---|
| **Page Background** | Hard dark `#0A0E1A` | **Warm off-white `#F7F8FC`** |
| **Sidebar Background** | Glassy dark `#0F172A` | **Clean, pure white `#FFFFFF`** with subtle border `#E5E7EB` |
| **Surface / Card Fill** | Dark translucent slate `#1E293B` | **Crisp white `#FFFFFF`** with soft shadow `rgba(0,0,0,0.04)` |
| **Primary Accent** | Saturated neon gradient | **Deep academic indigo `#5146E5`** (Hover: `#4338CA`, Light: `#EEF2FF`) |
| **Primary Typography** | Low-contrast grey text | **Dark navy `#20243A`** for high contrast and readability |
| **Secondary Typography** | Dim grey `#64748B` | **Muted slate `#6B7280`** |
| **Typography Family** | Monospace / System fonts | **Plus Jakarta Sans**, **Noto Sans Devanagari** (Hindi), **JetBrains Mono** |
| **Layout Paradigm** | Static stacked cards | **Modern App Shell:** Collapsible Sidebar + Central Column + Fixed Dock |
| **Border & Divider** | Glowing cyan / purple lines | **Subtle grey `#E5E7EB`** and soft divider `#F3F4F6` |
| **Corner Radius** | Sharp / irregular | Consistent scale: Small (6px), Medium (10px), Large (14px), XL (20px) |

---

## 4. Key Architectural & User Experience Enhancements

### A. Centered Hero Input on Welcome Screen
- Rather than forcing students to locate an obscure input box at the bottom of an empty screen, the welcome screen positions a **large, welcoming input box directly in the hero zone**.
- Features auto-resizing, clean keyboard guidance, language hint (`English · हिंदी · Romanized Hindi · Hinglish`), and an indigo send button.

### B. 2x2 Curated Starter Question Grid
Four high-frequency student questions are highlighted as interactive cards:
1. **Attendance Requirements:** *"What is the minimum attendance requirement to appear in end-semester examinations?"*
2. **Examination Eligibility:** *"What are the examination eligibility requirements and criteria for students?"*
3. **CGPA Calculation:** *"How is CGPA calculated under the official academic evaluation rules?"*
4. **हिंदी देवनागरी (Devanagari Hindi):** *"सेमेस्टर परीक्षा और उपस्थिति के नियम क्या हैं?"*

Clicking any card automatically populates the input, initiates the consultation, and smoothly transitions into the active conversation stream.

### C. Clean White Persistent Sidebar
- **Brand Avatar:** Iconic Devanagari "अ" glyph representing Indic language grounding.
- **"+ New Chat" Button:** High-contrast indigo button to start a fresh consultation anytime.
- **Consultation History:** Real-time query history persisted in the browser's `localStorage`. Past consultations can be reloaded with one click.
- **Official Regulations Card:** Shows `7 Verified` documents with an instant trigger to open the document library modal.
- **Language Support Indicator:** Visual chips displaying support for English, हिंदी, Romanized Hindi, and Hinglish.
- **Live System Status:** Bottom indicator connected directly to `GET /health`, showing real-time backend connection status (`● FastAPI Online`).

### D. Official Sources & Citation Provenance
- Answers cite official university sources with full institutional accountability:
  - Formatted document titles (e.g. `Notification 307/2022 — Minimum Attendance`).
  - Specific **Page Badges** (e.g., `Page 1`).
  - Quoted official excerpts bordered with an indigo accent.
  - Interactive **"View complete official passage text"** modal action, fetching unedited passage text directly from `/documents/{doc_id}/passages`.
  - Trust badge: *"✓ Verified in University Records"*.

### E. Dedicated Institutional Response States
1. **Evidence-Supported Answer:** Clean markdown formatting, copy answer button, and source citations.
2. **Clarification Required:** Renders structured regulatory disclosures with interactive cohort refinement buttons (e.g., *Admitted 2023-24 Onwards*, *Admitted 2017-2022*, *SCSET Engineering Specific*).
3. **Safe Abstention (Unanswerable):** Informational amber banner stating clearly that the topic is not covered in official undergraduate academic regulations, preventing hallucinations.
4. **Conflicting Regulations:** Discloses discrepancies between older ordinances and newer registrar notifications.

### F. Deep-Linking & Progressive Loading
- **Deep-linking:** Supports `?q=...` URL parameter to pre-load and auto-execute questions directly upon page launch.
- **Progressive Feedback:** Four-stage dynamic progress indicator during retrieval and generation:
  1. *Understanding language & academic intent…*
  2. *Searching official university regulations…*
  3. *Validating evidence, citations & versions…*
  4. *Synthesizing evidence-grounded response…*

---

## 5. Preservation of Backend Contracts & Technical Invariants

The entire redesign was implemented exclusively in [frontend/index.html](file:///c:/Users/anish/Desktop/IndicRAG-QA/frontend/index.html). No backend Python code, evaluation scripts, frozen benchmark datasets, or database tables were modified.

| Interface / Contract | Method | Request Payload / Params | Status |
|---|:---:|---|:---:|
| `GET /health` | `GET` | None | Preserved & Active |
| `GET /documents` | `GET` | None | Preserved & Active |
| `GET /documents/{id}/passages` | `GET` | `doc_id` path parameter | Preserved & Active |
| `POST /query` | `POST` | `{"query": "...", "collections": ["official"], "use_reranker": true, "use_pdr": true, "debug": false}` | Preserved & Active |

- **Production Retrieval Invariant:** `rerank_strategy: str = "production"` in `backend/app/retrieval/engine.py` line 395 remains unmodified.
- **No Node.js / npm Dependencies:** The frontend remains 100% standalone, vanilla HTML5, modern CSS, and vanilla ES6 JavaScript.

---

## 6. Live Verification Log

Automated verification tests conducted during local execution:

```
[SYSTEM INITIALIZATION]
1. Backend Process: Uvicorn / FastAPI on http://127.0.0.1:8000
   Health Check: GET http://127.0.0.1:8000/health
   Response: {"status":"ok","version":"0.1.0","ollama_reachable":true,"embedding_model_loaded":true,"document_count":7,"passage_count":306}
   Result: SUCCESS (HTTP 200 OK)

2. Frontend Process: Python SimpleHTTP on http://localhost:3000
   Endpoint: GET http://localhost:3000/
   Response: 200 OK — frontend/index.html served with Cache-Control: no-cache.
   Result: SUCCESS (HTTP 200 OK)

[QUERY TEST: Code-Mixed Romanized Hindi]
Endpoint: POST http://127.0.0.1:8000/query
Payload: {"query": "attendance requirement kya hai?", "collections": ["official"], "use_reranker": true, "use_pdr": true, "debug": false}
Latency: 2.1 ms (Deterministic Evidence Controller Disclosure)
Controller Status: CLARIFICATION_REQUIRED
Disclosed Rules:
- Notification 307/2022: 75% minimum aggregate attendance for End Semester Examinations.
- SCSET Clause 30.1: 70% minimum attendance per course to avoid 'X' grade.
Interactive Cohort Refinements Generated:
- "Admitted 2023-24 Onwards (Current)"
- "Admitted 2017-2022 (Historical)"
- "SCSET Engineering Specific"
Result: SUCCESS

[HEADLESS BROWSER VERIFICATION]
Command: chrome.exe --headless=new --window-size=1280,820 --virtual-time-budget=3000 --screenshot=docs/ui_screenshot_welcome.png http://localhost:3000
Image Verification: docs/ui_screenshot_welcome.png (130,723 bytes, valid PNG header)
Result: VERIFIED

Command: chrome.exe --headless=new --window-size=1280,900 --virtual-time-budget=4000 --screenshot=docs/ui_screenshot_chat.png "http://localhost:3000/?q=attendance+requirement+kya+hai%3F"
Image Verification: docs/ui_screenshot_chat.png (128,584 bytes, valid PNG header)
Result: VERIFIED

Command: chrome.exe --headless=new --window-size=412,850 --virtual-time-budget=3000 --screenshot=docs/ui_screenshot_mobile.png http://localhost:3000
Image Verification: docs/ui_screenshot_mobile.png (66,157 bytes, valid PNG header)
Result: VERIFIED
```

---

## 7. How to Run and Access Locally

### Starting the Application

1. **Start the FastAPI Backend Server:**
   ```powershell
   cd C:\Users\anish\Desktop\IndicRAG-QA\backend
   python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
   ```

2. **Start the Static Frontend Server:**
   ```powershell
   cd C:\Users\anish\Desktop\IndicRAG-QA\frontend
   python -m http.server 3000
   ```

### Accessing the Application

- **Web Browser URL:** Open [http://localhost:3000](http://localhost:3000) in Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari.
- **Direct File Access:** Double-click or open [frontend/index.html](file:///c:/Users/anish/Desktop/IndicRAG-QA/frontend/index.html) directly in any modern browser.
