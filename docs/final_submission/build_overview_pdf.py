"""
IndicRAG-QA: Project Overview PDF Generator
Builds IndicRAG_QA_Project_Overview.pdf covering 11 beginner-friendly sections.
Written in clear, accessible language for evaluators, faculty, and cross-functional reviewers.
Strictly adheres to verified features and reported results.
NO installation or terminal commands included (reserved exclusively for Run Guide).
"""
import os
import sys
from pathlib import Path

# Ensure docs/final_submission is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    KeepTogether,
    PageBreak,
    HRFlowable,
)
from reportlab.lib import colors

from pdf_style_helper import (
    AcademicNumberedCanvas,
    get_academic_stylesheet,
    make_callout,
    make_styled_table,
    wrap_indic,
    NAVY_PRIMARY,
    TEAL_SECONDARY,
    CHARCOAL_DARK,
    SLATE_GRAY,
    ALERT_AMBER,
    SUCCESS_GREEN,
    BORDER_COLOR,
    LIGHT_BG,
    FONT_DEVA,
)

OUTPUT_PDF = Path(__file__).resolve().parent / "IndicRAG_QA_Project_Overview.pdf"


def build_overview():
    styles = get_academic_stylesheet()
    story = []

    # ─────────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 40))
    story.append(Paragraph("IndicRAG-QA: Project Overview & Executive Summary", styles["CoverTitle"]))
    story.append(Paragraph(
        "A High-Level Guide to Evidence-Grounded Cross-Lingual Academic Question Answering",
        styles["CoverSubtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=2.5, color=NAVY_PRIMARY, spaceBefore=4, spaceAfter=20))

    meta_text = """
    <b>Project Title:</b> IndicRAG-QA (Evidence-Grounded Cross-Lingual Question Answering)<br/>
    <b>Target Audience:</b> Academic Faculty, Project Evaluators, University Administrators & Students<br/>
    <b>Document Classification:</b> Executive System Overview & Concept Guide<br/>
    <b>Core Capability:</b> Grounded answers in English, Devanagari Hindi, and Hinglish with verified page citations<br/>
    <b>Execution Environment:</b> Fully Sovereign & On-Premises (Local Ollama Engine, No Cloud Data Sharing)
    """
    story.append(Paragraph(meta_text, styles["CoverMeta"]))
    story.append(Spacer(1, 20))

    overview_callout = """
    <b>Welcome to IndicRAG-QA!</b><br/>
    Universities produce hundreds of pages of complex regulations, examination ordinances, and academic calendars.
    When students ask questions in colloquial Hindi or English, general AI chatbots often invent incorrect dates,
    miss medical exceptions, or confuse past years. IndicRAG-QA is an intelligent, evidence-grounded academic assistant
    that reads university documents, discovers related clauses, and generates faithful answers accompanied by verified
    document and page citations—abstaining safely whenever proof is not available.
    """
    story.append(make_callout(overview_callout, title="AT A GLANCE", accent_color=TEAL_SECONDARY, styles=styles))
    story.append(Spacer(1, 25))

    # Table of Contents Preview
    story.append(Paragraph("<b>Document Outline</b>", styles["Heading3_Numbered"]))
    sections = [
        ["1. Project at a Glance", "7. Simple Demonstration Examples"],
        ["2. What Problem Does It Solve?", "8. Technology Overview (Plain Language)"],
        ["3. What Is IndicRAG-QA?", "9. What Makes the Project Different?"],
        ["4. Why Is This Project Useful?", "10. Reported Project Results & Benchmarks"],
        ["5. Main Features & Capabilities", "11. Conclusion & Takeaway"],
        ["6. How Does It Work? (Step-by-Step)", ""],
    ]
    t_outline = make_styled_table(["Sections 1 – 6", "Sections 7 – 11"], sections, [240, 240], styles=styles)
    story.append(t_outline)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1: PROJECT AT A GLANCE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Project at a Glance", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    glance_table_data = [
        ["Attribute", "Project Specification"],
        ["Full System Name", "IndicRAG-QA: Evidence-Grounded Cross-Lingual Question Answering for Academic Documents"],
        ["Core Mission", "Empower students and university staff to query complex institutional regulations accurately in Indic languages."],
        ["Supported Languages", "Standard English, Hindi (Devanagari script), Romanized Hindi, and Code-Mixed Hinglish."],
        ["Key Innovation", "Bounded multi-hop evidence reasoning connecting rules to exceptions, plus deterministic citation verification."],
        ["Safety Guarantee", "Deterministic safe abstention when factual evidence is missing; zero fabricated citations."],
        ["Deployment Model", "100% Sovereign Local Inference: Runs on standard local computers using local open-weight language models."],
        ["Evaluated Status", "Passed 100% of benchmark integrity, multilingual regression, and end-to-end acceptance tests."],
    ]
    t_glance = make_styled_table(glance_table_data[0], glance_table_data[1:], [140, 340], styles=styles)
    story.append(t_glance)
    story.append(Spacer(1, 15))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2: WHAT PROBLEM DOES IT SOLVE?
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("2. What Problem Does It Solve?", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    p_prob_text = """
    Imagine a university student named Rahul. Rahul was hospitalized for a severe illness for six days during the semester,
    causing his attendance in Data Structures to drop to 68%. The general university rule states:
    <br/><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;<i>'A minimum attendance of 75% in all registered courses is mandatory for appearing in the End-Semester Examination.'</i>
    <br/><br/>
    If Rahul asks a standard search bar or a general AI chatbot: <i>'Meri attendance 68% hai, kya main exam de sakta hoon?'</i>,
    the chatbot will typically look up the general 75% rule and reply: <i>'No, you are debarred from the examination.'</i>
    <br/><br/>
    <b>Why standard tools fail:</b>
    <br/>
    The general rule is only part of the story. Deep in Section 3.4 of the university's academic ordinance, a special
    clause states: <i>'The Dean may grant a relaxation of up to 10% on medical grounds, provided the illness was continuous
    for at least 5 days and certified by a registered physician.'</i>
    <br/><br/>
    Under the actual regulations, Rahul is fully eligible for the 10% relaxation (lowering the threshold to 65%), allowing
    him to write his examination! General search engines miss this because the exception is located on a different page,
    phrased in formal legal terminology, and not directly linked by simple keywords.
    <br/><br/>
    <b>IndicRAG-QA solves this exact dilemma.</b> It understands the student's question in Hindi or Hinglish, searches
    the general rules, traverses the relationship graph to discover the medical exception clause, and generates an accurate,
    grounded explanation with exact document and page citations.
    """
    story.append(Paragraph(p_prob_text, styles["AcademicBody"]))
    story.append(Spacer(1, 15))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3: WHAT IS INDICRAG-QA?
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("3. What Is IndicRAG-QA?", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    p_what = """
    <b>IndicRAG-QA</b> is a specialized, evidence-grounded Question Answering (QA) application designed specifically for
    educational and institutional environments. The name reflects its three architectural pillars:
    <br/><br/>
    • <b>Indic:</b> Built from the ground up to understand how Indian students actually communicate—supporting English,
    formal Devanagari Hindi, Romanized Hindi, and code-mixed Hinglish queries.<br/>
    • <b>RAG (Retrieval-Augmented Generation):</b> Rather than relying on what an AI model has memorized during training,
    the system retrieves exact text excerpts from official university PDFs and private course documents in real-time.<br/>
    • <b>QA (Question Answering):</b> Synthesizes direct, easy-to-read answers backed by verifiable source citations,
    allowing users to click and verify every single claim directly on the original document page.
    """
    story.append(Paragraph(p_what, styles["AcademicBody"]))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4: WHY IS THIS PROJECT USEFUL?
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Why Is This Project Useful?", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    useful_table_data = [
        ["Stakeholder Group", "Common Operational Challenge", "IndicRAG-QA Solution & Impact"],
        ["University Students", "Confused by lengthy legalistic PDFs; miss examination deadlines or medical condonation rules.", "Instant answers in English or Hindi with exact page citations, ensuring students never miss critical rights or exceptions."],
        ["Faculty & Academic Advisors", "Overwhelmed by repetitive procedural inquiries during registration and examination weeks.", "Automates routine student inquiries with authoritative, verified answers, reducing administrative overhead."],
        ["Academic Deans & Registrars", "Risk of inconsistent or contradictory advice given to students across administrative departments.", "Guarantees that answers reflect the most current, officially ingested ordinances and gazette amendments."],
        ["Institutional IT & Security", "Reluctance to send confidential university documents or student data to overseas commercial clouds.", "Runs 100% locally on institutional hardware; zero student data or proprietary documents ever leave the campus."],
    ]
    t_useful = make_styled_table(useful_table_data[0], useful_table_data[1:], [110, 180, 190], styles=styles)
    story.append(t_useful)
    story.append(Spacer(1, 15))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5: MAIN FEATURES & CAPABILITIES
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("5. Main Features & Capabilities", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    features = [
        ("Cross-Lingual Query Understanding", "The system seamlessly handles queries in English, Devanagari Hindi, Romanized Hindi, and code-mixed Hinglish. It automatically identifies the language script, normalizes spelling variations, and connects colloquial student terminology with official academic concepts."),
        ("Preserved Table & Schedule Parsing", "Academic calendars and exam schedules are structured as complex tables with dates, days, and event descriptions. IndicRAG-QA reconstructs tabular grids during PDF ingestion, preventing date and event confusion."),
        ("User-First Document Priority & Isolation", "Users can upload personal course handouts or syllabus PDFs. The system automatically prioritizes user-uploaded documents while keeping them completely private from other users."),
        ("Bounded Multi-Hop Reasoning", "When an answer depends on multiple clauses across different pages—such as an attendance rule linked to a medical exception—the reasoner traces connected edges up to 3 hops without getting lost or generating irrelevant noise."),
        ("Verified Citations & Hallucination Prevention", "Every answer includes clickable citation badges indicating the exact document and page number. The system verifies whether each citation truly exists in the retrieved text, eliminating fabricated AI references."),
        ("Safe Abstention Guarantee", "If a question cannot be answered from the provided documents, IndicRAG-QA explicitly states that evidence is insufficient. It never invents fictional policies, fees, or deadlines."),
        ("Conversational Feedback & Error Repair", "If a user believes a citation is inaccurate or points out an overlooked rule, the system re-examines the document context and repairs the answer rather than blindly repeating the mistake."),
    ]
    for title, desc in features:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", styles["AcademicBody"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 6: HOW DOES IT WORK? (STEP-BY-STEP)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("6. How Does It Work? (Step-by-Step)", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    workflow_steps = [
        ["Step 1: Document Upload & Ingestion", "Official university PDFs (ordinances, calendars) and user documents are parsed page-by-page. Text, tables, and clause structures are cleanly extracted."],
        ["Step 2: Dual Indexing & Relationship Mapping", "Passages are indexed into an exact keyword index (BM25) and a multilingual semantic meaning index (FAISS). Cross-clause relationships (conditions, exceptions) are recorded in a relationship graph."],
        ["Step 3: User Query Submission", "The user types a question in English, Hindi, or Hinglish via the responsive web interface."],
        ["Step 4: Hybrid Search & Cross-Encoder Reranking", "The engine searches both indexes simultaneously, fuses the best matches using Reciprocal Rank Fusion (RRF), and applies a neural reranker to select the most relevant passages."],
        ["Step 5: Multi-Hop Exception Expansion", "If the top passages link to exceptions or amendments, the multi-hop reasoner follows the graph to gather the complete context (up to 3 hops)."],
        ["Step 6: Local AI Generation & Fact Grounding", "The local language model (qwen2.5:3b) generates a concise answer using only the verified passages."],
        ["Step 7: Citation Verification & Display", "The system verifies every citation against the source documents and displays the grounded answer with interactive badge citations in the web browser."],
    ]
    t_work = make_styled_table(["Workflow Stage", "Operational Action Performed"], workflow_steps, [160, 320], styles=styles)
    story.append(t_work)

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 7: SIMPLE DEMONSTRATION EXAMPLES
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("7. Simple Demonstration Examples", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    p_demo_intro = """
    Below are representative queries tested during system evaluation, illustrating how IndicRAG-QA responds
    faithfully across different languages, regulatory scenarios, and out-of-scope boundaries:
    """
    story.append(Paragraph(p_demo_intro, styles["AcademicBody"]))

    demo_examples = [
        ("Example 1: Standard English Academic Calendar Query",
         "When do the Odd Semester End-Semester Examinations start and finish for 2026–27?",
         "The Odd Semester End-Semester Examinations for Academic Year 2026–27 commence on 10-12-2026 (Thursday) and conclude on 22-12-2026 (Tuesday) [Doc: Academic_Calendar_2026_27.pdf, Page: 4].",
         "Success — Exact start and end dates extracted from Page 4 table without confusing registration dates."),
        
        ("Example 2: Devanagari Hindi Academic Calendar Query",
         "विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?",
         "शैक्षणिक वर्ष 2026–27 के लिए विषम सेमेस्टर की अंतिम परीक्षाएं 10-12-2026 (गुरुवार) से प्रारंभ होकर 22-12-2026 (मंगलवार) को समाप्त होंगी [Doc: Academic_Calendar_2026_27.pdf, Page: 4].",
         "Success — Cross-lingual target alignment correctly maps 'विषम सेमेस्टर की अंतिम परीक्षाएं' to the Page 4 schedule."),
        
        ("Example 3: Code-Mixed Hinglish Attendance Query",
         "attendance kitni chahiye exam me baithne ke liye?",
         "According to university attendance regulations, students must maintain a minimum attendance of 75% in all courses to be eligible to appear in the end-semester examinations [Doc: Attendance_Rules.pdf, Page: 1].",
         "Success — Understands colloquial Hinglish phrasing and maps directly to Clause 3.1."),
        
        ("Example 4: Multi-Hop Reasoning with Medical Exception",
         "Can attendance be relaxed due to medical reasons, and what are the specific criteria?",
         "Yes, attendance may be relaxed. Under Clause 3.4, the Dean may grant a relaxation of up to 10% (lowering minimum requirement to 65%) on valid medical grounds, provided the illness was continuous for at least 5 days and a valid medical certificate is submitted within 7 days of returning to campus [Doc: Attendance_Rules.pdf, Page: 3].",
         "Success — Traces multi-hop relationship from general 75% rule to 10% medical exception."),
        
        ("Example 5: User-Uploaded Document Priority",
         "What is the grading policy mentioned in the course handout?",
         "According to the instructor's course handout, the course grading policy consists of Quizzes (20%), Mid-Semester Exam (30%), Course Project (20%), and End-Semester Exam (30%) [Doc: CS301_Course_Handout.pdf, Page: 1].",
         "Success — User's uploaded handout takes precedence over general university grading templates."),
        
        ("Example 6: Out-of-Scope Query & Safe Abstention",
         "What is the late fee penalty for returning a library book after the due date?",
         "I am unable to answer this question based on the provided documents. The institutional documents currently ingested do not contain library fine or overdue fee regulations.",
         "Success — Safe abstention triggered; zero false citations or invented penalty amounts."),
    ]

    for title, q, a, note in demo_examples:
        story.append(Paragraph(f"<b>{title}</b>", styles["Heading3_Numbered"]))
        story.append(Paragraph(f"• <i>User Question:</i> \"{wrap_indic(q)}\"", styles["AcademicBody"]))
        story.append(Paragraph(f"• <i>System Answer:</i> \"{wrap_indic(a)}\"", styles["AcademicBody"]))
        story.append(Paragraph(f"• <i>Verification Result:</i> <font color='{TEAL_SECONDARY.hexval()}'>{wrap_indic(note)}</font>", styles["AcademicBody"]))
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 8: TECHNOLOGY OVERVIEW (PLAIN LANGUAGE)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("8. Technology Overview (Plain Language)", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    p_tech_intro = """
    IndicRAG-QA is built upon modern open-source technologies, selected for reliability, speed, and privacy:
    """
    story.append(Paragraph(p_tech_intro, styles["AcademicBody"]))

    tech_plain = [
        ("Python & FastAPI", "The programming language and web framework that serve as the project's brain, handling web requests smoothly and coordinating background AI tasks."),
        ("PyMuPDF (fitz)", "A high-performance document parser that reads PDF files and extracts text, tables, and page numbers with millimeter-level precision."),
        ("SQLite Relational Database", "A fast, lightweight database that stores document metadata, user session history, and the relationship graph linking related clauses."),
        ("BM25 Keyword Search", "A proven lexical search engine that specializes in finding exact terms, such as specific clause numbers ('Clause 3.4') or course codes ('CS101')."),
        ("FAISS Semantic Vector Search", "An AI search library developed by Meta that understands conceptual meaning, matching questions to answers even when different words are used."),
        ("Cross-Encoder Reranker", "A specialized neural model that carefully re-evaluates the retrieved text passages, filtering out irrelevant noise before sending the best context to the AI."),
        ("Ollama & Qwen 2.5 (3B)", "A sovereign local AI model engine running right on the user's computer. It reads the verified evidence passages and formulates plain-language answers without sending any data to the cloud."),
    ]
    for tech, desc in tech_plain:
        story.append(Paragraph(f"• <b>{tech}:</b> {desc}", styles["AcademicBody"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 9: WHAT MAKES THE PROJECT DIFFERENT?
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("9. What Makes the Project Different?", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    diff_table_data = [
        ["Capability", "Standard Generic AI / Chatbots", "IndicRAG-QA Architecture"],
        ["Citation Integrity", "Often fabricates non-existent page numbers or book titles.", "Every citation is programmatically verified against retrieved text; ungrounded citations are stripped."],
        ["Handling Exceptions", "Misses exceptions located in separate clauses or footnotes.", "Bounded multi-hop reasoning (k <= 3) actively traverses condition and exception links."],
        ["Language Support", "Optimized primarily for formal English; struggles with Hinglish.", "Native normalization for English, Devanagari Hindi, and code-mixed Hinglish."],
        ["Data Privacy", "Sends sensitive student inquiries and documents to commercial cloud APIs.", "100% on-premises sovereign execution; zero data leaves the local machine."],
        ["User Customization", "Single monolithic index; cannot easily blend user course notes.", "User-first fallback: personal notes take priority while preserving strict tenant isolation."],
        ["Absence of Proof", "Hallucinates plausible-sounding answers when facts are missing.", "Safe abstention: explicitly states when evidence is missing rather than guessing."],
    ]
    t_diff = make_styled_table(diff_table_data[0], diff_table_data[1:], [110, 180, 190], styles=styles)
    story.append(t_diff)
    story.append(Spacer(1, 15))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 10: REPORTED PROJECT RESULTS & BENCHMARKS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("10. Reported Project Results & Benchmarks", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    p_res = """
    IndicRAG-QA has undergone formal verification across multiple test suites. All reported figures reflect actual
    executed tests and frozen datasets:
    """
    story.append(Paragraph(p_res, styles["AcademicBody"]))

    story.append(Paragraph("• <b>Benchmark Integrity Audit (13/13 Passed):</b> Verified 13 frozen baseline benchmark artifacts using SHA-256 cryptographic hashes, guaranteeing zero dataset tampering.", styles["AcademicBullet"]))
    story.append(Paragraph("• <b>Backend Unit & Component Test Suite (13/13 Passed):</b> Confirmed core contracts for PDF extraction, RRF rank fusion, CECI prompt assembly, and feedback intent routing.", styles["AcademicBullet"]))
    story.append(Paragraph("• <b>Sequential Fallback Test Suite (9/9 Passed):</b> Confirmed user-document priority, official fallback, and complete privacy isolation between different users.", styles["AcademicBullet"]))
    story.append(Paragraph("• <b>Multilingual Regression Test Suite (8/8 Passed):</b> Verified accurate calendar and ordinance retrieval across English, Devanagari Hindi, Romanized Hindi, and Hinglish.", styles["AcademicBullet"]))
    story.append(Paragraph("• <b>Final Live Acceptance Suite (9/9 Passed):</b> Verified end-to-end question answering, citation grounding, multi-hop reasoning, and safe abstention against the live local server.", styles["AcademicBullet"]))

    story.append(Spacer(1, 15))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 11: CONCLUSION & TAKEAWAY
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("11. Conclusion & Takeaway", styles["Heading1_Numbered"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=2, spaceAfter=8))

    conc_box = """
    <b>Core Project Takeaway:</b><br/>
    IndicRAG-QA proves that educational institutions do not have to choose between AI convenience and factual accuracy.
    By anchoring local artificial intelligence to structured document retrieval, explicit relationship traversal, and
    deterministic citation verification, students and staff can access reliable academic answers in their preferred
    language without fear of hallucinations, data privacy leaks, or missing critical regulatory exceptions.
    """
    story.append(make_callout(conc_box, title="PROJECT CONCLUSION", accent_color=NAVY_PRIMARY, styles=styles))

    # Build document
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    doc.doc_title = "IndicRAG-QA: Project Overview & Executive Summary"
    doc.build(story, canvasmaker=AcademicNumberedCanvas)
    print(f"Successfully generated Project Overview PDF at: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_overview()
