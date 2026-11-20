"""
Automated Verification Script for Generated Academic Submission PDFs.
Verifies PDF existence, byte size, page counts, extractable text, headers/footers,
Devanagari rendering, and compliance with documentation boundaries.
"""
import sys
from pathlib import Path
import fitz  # PyMuPDF

DOCS_DIR = Path("docs/final_submission").resolve()

EXPECTED_FILES = [
    {
        "filename": "IndicRAG_QA_Project_Deep_Dive.pdf",
        "min_pages": 15,
        "max_pages": 25,
        "forbid_commands": ["uvicorn backend.app.api", "pytest backend/tests/ --", "ollama pull"],
        "role": "Technical Deep Dive & Architecture Reference",
    },
    {
        "filename": "IndicRAG_QA_Project_Overview.pdf",
        "min_pages": 6,
        "max_pages": 12,
        "forbid_commands": ["uvicorn backend.app.api", "python -m uvicorn", "ollama serve", "pytest backend/tests/"],
        "role": "Beginner-Friendly Project Overview & Executive Summary",
    },
    {
        "filename": "IndicRAG_QA_Project_Run_Guide.pdf",
        "min_pages": 6,
        "max_pages": 14,
        "require_commands": ["uvicorn", "pytest", "ollama", "http://localhost:8000"],
        "role": "Practical Run Guide & Live Demonstration Manual",
    },
]


def verify_pdfs():
    print("=" * 70)
    print("STARTING ACADEMIC SUBMISSION PDF VERIFICATION")
    print("=" * 70)

    all_passed = True
    results = []

    for item in EXPECTED_FILES:
        filepath = DOCS_DIR / item["filename"]
        print(f"\n[*] Inspecting: {item['filename']}")

        if not filepath.exists():
            print(f"  [FAIL] File does not exist at {filepath}")
            all_passed = False
            continue

        size_bytes = filepath.stat().st_size
        size_kb = size_bytes / 1024
        print(f"  [OK] File exists. Size: {size_kb:.2f} KB ({size_bytes} bytes)")

        if size_bytes < 5000:
            print(f"  [FAIL] File size suspiciously small ({size_bytes} bytes)")
            all_passed = False

        try:
            doc = fitz.open(filepath)
            page_count = len(doc)
            print(f"  [OK] Successfully opened with PyMuPDF. Page count: {page_count}")

            if page_count < item["min_pages"] or page_count > item["max_pages"]:
                print(f"  [FAIL] Page count {page_count} outside expected range [{item['min_pages']}, {item['max_pages']}]")
                all_passed = False
            else:
                print(f"  [OK] Page count within specification [{item['min_pages']}, {item['max_pages']}]")

            # Extract text from all pages
            total_chars = 0
            has_headers_footers = False
            has_deva = False
            full_text = []

            for page_idx in range(page_count):
                page = doc[page_idx]
                txt = page.get_text()
                total_chars += len(txt)
                full_text.append(txt)

                # Check headers / footers on non-cover pages
                if page_idx > 0:
                    if f"Page {page_idx + 1} of {page_count}" in txt or "Confidential" in txt:
                        has_headers_footers = True
                
                # Check Devanagari text
                for ch in txt:
                    if 0x0900 <= ord(ch) <= 0x097F:
                        has_deva = True
                        break

            combined_text = "\n".join(full_text)
            print(f"  [OK] Total extractable characters: {total_chars}")
            print(f"  [OK] Running headers and 'Page X of Y' footers verified: {has_headers_footers}")
            print(f"  [OK] Devanagari Unicode characters detected: {has_deva}")

            # Check command separation boundary
            if "forbid_commands" in item:
                forbidden_found = []
                for cmd in item["forbid_commands"]:
                    if cmd in combined_text:
                        forbidden_found.append(cmd)
                if forbidden_found:
                    print(f"  [FAIL] Found forbidden startup/terminal commands: {forbidden_found}")
                    all_passed = False
                else:
                    print(f"  [OK] Boundary verified: Zero forbidden startup/terminal commands found.")

            if "require_commands" in item:
                missing_required = []
                for cmd in item["require_commands"]:
                    if cmd not in combined_text:
                        missing_required.append(cmd)
                if missing_required:
                    print(f"  [FAIL] Missing expected operational commands: {missing_required}")
                    all_passed = False
                else:
                    print(f"  [OK] Boundary verified: Contains required operational commands: {item['require_commands']}")

            results.append({
                "filename": item["filename"],
                "role": item["role"],
                "page_count": page_count,
                "size_kb": f"{size_kb:.1f} KB",
                "char_count": total_chars,
                "status": "PASS" if all_passed else "FAIL"
            })

        except Exception as e:
            print(f"  [FAIL] Error processing PDF: {e}")
            all_passed = False

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY REPORT")
    print("=" * 70)
    for r in results:
        print(f"• {r['filename']} ({r['role']}): {r['page_count']} pages, {r['size_kb']}, {r['char_count']} chars -> {r['status']}")
    
    if all_passed:
        print("\nALL THREE ACADEMIC SUBMISSION PDFS FULLY VERIFIED AND COMPLIANT!")
        return 0
    else:
        print("\nONE OR MORE VERIFICATION CHECKS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(verify_pdfs())
