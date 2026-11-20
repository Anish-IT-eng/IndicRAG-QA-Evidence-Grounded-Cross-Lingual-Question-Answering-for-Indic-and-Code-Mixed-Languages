import sys
sys.path.insert(0, 'backend')

from app.generation.generator import _extract_and_validate_citations, _format_evidence
from app.models.schemas import Passage

# Let's inspect with a mock passage
p = Passage(
    passage_id="b8e1e508-6a9c-46b0-a8cd-42ce1fc4bcda",
    document_id="0c174816-3d23-4e47-aef4-8b8579b801d6",
    text="10-12-2026 Thursday Examination End Semester Examination for All Students (Odd Semester 2026-27)",
    page_number=4,
    source_type="official"
)
passages = [p]
raw_output = "The Odd Semester End Semester Examinations for all students will start on 10-12-2026 (December 10, 2026). [Source: 1, page 4]"

cits, cleaned, claims = _extract_and_validate_citations(
    generated_text=raw_output,
    passages=passages,
    document_filenames={"0c174816-3d23-4e47-aef4-8b8579b801d6": "Academic-Calendar-2026-27.pdf"}
)
print("Citations count without patch:", len(cits))
