"""
Official document source registry for IndicRAG-QA.

This file lists the known official Bennett University / SCSET documents.
Entries are manually curated and verified.

DO NOT:
- Add a document unless its provenance and content have been verified.
- Mark a document as current without checking whether it has been superseded.
- Invent URLs, dates, or effective periods.

Each entry has:
  filename      : The local PDF filename (must be placed in data/official/)
  title         : Official document title
  description   : Short description of what the document covers
  source_url    : Canonical URL where the document was obtained (record only)
  version_info  : Effective date, academic year, program applicability, etc.
  verified      : Whether provenance has been manually confirmed
  notes         : Any caveats about this document's scope or status
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceEntry:
    filename: str
    title: str
    description: str
    source_url: Optional[str] = None
    effective_date: Optional[str] = None
    academic_year: Optional[str] = None
    program_applicability: list[str] = field(default_factory=list)
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    is_current: Optional[bool] = None
    verified: bool = False
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# All entries below have been manually verified against official Bennett
# University sources. Provenance confirmed: bennett.edu.in and its CDN.
# Verified: 2026-11-02.
# ─────────────────────────────────────────────────────────────────────────────

OFFICIAL_SOURCES: list[SourceEntry] = [
    SourceEntry(
        filename="Academic-Rules-for-SCSET_UG.pdf",
        title="Academic Rules for Undergraduate Programs — SCSET",
        description=(
            "Official academic rules for B.Tech UG programs under SCSET at Bennett "
            "University. Covers attendance requirements, examination eligibility, grading "
            "scheme, promotion criteria, back-paper policy, and related regulations."
        ),
        source_url=(
            "https://www.bennett.edu.in/wp-content/uploads/2022/03/"
            "Academic-Rules-for-SCSET_UG.pdf"
        ),
        effective_date=None,          # Not stated explicitly on the document cover
        academic_year="2022-23",      # Inferred from URL upload date: March 2022
        program_applicability=["B.Tech"],
        is_current=None,              # Cannot confirm without checking for newer version
        verified=True,
        notes=(
            "Downloaded 2026-11-02 from official bennett.edu.in. 20 pages. "
            "No explicit effective date on cover page. "
            "is_current=None — verify whether a newer SCSET UG rules document exists."
        ),
    ),
    SourceEntry(
        filename="Notification-Minimum-Attendance.pdf",
        title="Notification for Minimum Attendance for Students (Ref No: BU/RO/Notification/307/2022)",
        description=(
            "Official university notification establishing the 75% minimum attendance criteria "
            "to appear in the End Semester Examination with effect from AY 2022-23 (odd semester onwards). "
            "Reviewed in the 13th Academic Council Meeting (29 July 2022) in consonance with UGC Regulations 2003."
        ),
        source_url=(
            "https://www.bennett.edu.in/wp-content/uploads/2022/09/"
            "Notification-for-Minimum-Attendance-for-Students.pdf"
        ),
        effective_date="2022-09-08",
        academic_year="2022-23 onwards",
        program_applicability=["B.Tech", "Undergraduate", "All Students"],
        is_current=True,
        verified=True,
        notes=(
            "Single-page scanned official notification. Text extracted and validated via RapidOCR. "
            "Sets minimum 75% attendance threshold for End Semester Examination eligibility. "
            "Signed by Col Guljit Singh Chadha, Retd (Registrar). Downloaded from official bennett.edu.in."
        ),
    ),
    SourceEntry(
        filename="Academic-Calendar-2026-27.pdf",
        title="Academic Calendar for A.Y. 2026-27",
        description=(
            "Bennett University official academic calendar for academic year 2026-27. "
            "Covers semester start/end dates, examination periods, registration deadlines, "
            "and holiday schedule. Applicable to all students."
        ),
        source_url=(
            "https://d2xwywryb7yxbo.cloudfront.net/s3bucket-images/"
            "Academic-Calendar-2026-27.pdf"
        ),
        effective_date="2026-07-01",  # Calendar period begins July 2026
        academic_year="2026-27",
        program_applicability=["B.Tech"],  # Document states 'Applicable to All Students'
        is_current=True,
        verified=True,
        notes=(
            "Confirmed current: explicitly covers A.Y. 2026-27. "
            "Downloaded 2026-11-02 from Bennett University CloudFront CDN. 9 pages."
        ),
    ),
    SourceEntry(
        filename="SEAS-Ordinance-Rules-Regulations-2017.pdf",
        title="Ordinances, Rules and Regulations for UG Engineering Programs — 2017 Onwards",
        description=(
            "Historical founding ordinances for Bennett University undergraduate "
            "engineering programs (SEAS). 81 pages. Covers program structure, examination "
            "rules, promotion criteria, grading, and disciplinary regulations as of 2017. "
            "May have been partially or fully superseded by later SCSET UG rules."
        ),
        source_url=(
            "https://www.bennett.edu.in/wp-content/uploads/2017/08/"
            "SEAS-Ord_Rules-Reg_01-Nov.pdf"
        ),
        effective_date="2017-11-01",  # From filename: 01-Nov
        academic_year="2017-18",
        program_applicability=["B.Tech"],
        superseded_by=None,           # Unknown — check if SCSET UG rules supersede this
        is_current=False,
        verified=True,
        notes=(
            "Historical document from 2017. Marked is_current=False. "
            "Likely partially superseded by 'Academic-Rules-for-SCSET_UG.pdf'. "
            "Supersession status unconfirmed — superseded_by=None until verified. "
            "Downloaded 2026-11-02 from official bennett.edu.in. 81 pages."
        ),
    ),
    SourceEntry(
        filename="Students-Discipline-Conduct-Rules-2024.pdf",
        title="Students' Discipline and Conduct Rules (2024)",
        description=(
            "Official rules of discipline and conduct for students of Bennett University "
            "approved by the Vice Chancellor under Bennett University Statutes. Covers "
            "proctorial board functions, acts of indiscipline, inquiry procedures, penalties, "
            "punishments, and hostel rules across all schools."
        ),
        source_url=(
            "https://www.bennett.edu.in/wp-content/uploads/2024/03/"
            "STUDENTS-DISCIPLINE-AND-CONDUCT-RULES_compressed.pdf"
        ),
        effective_date="2024-03-01",
        academic_year="2023-24 onwards",
        program_applicability=["All Students", "B.Tech", "Undergraduate", "Postgraduate"],
        is_current=True,
        verified=True,
        notes=(
            "Published March 2024 on official bennett.edu.in. 23 pages digital text. "
            "Approved by Vice Chancellor under Bennett University Statutes. "
            "Applies university-wide across all schools and cohorts."
        ),
    ),
    SourceEntry(
        filename="BU-First-Ordinance-2016.pdf",
        title="First Ordinances of Bennett University (U.P. Act No 24 of 2016)",
        description=(
            "Statutory First Ordinances of Bennett University framed under clause 29 of "
            "UP Act No 24 of 2016. Covers admissions, enrolment, programs of study "
            "(B.Tech, MBA, PhD), medium of instructions, conditions for award of degrees, "
            "examinations, medals, and student fees."
        ),
        source_url=(
            "https://www.bennett.edu.in/wp-content/uploads/2024/05/"
            "BU-First-Ordinance-2016.pdf"
        ),
        effective_date="2016-09-01",
        academic_year="2016-17 onwards",
        program_applicability=["All Programs", "B.Tech", "MBA", "PhD"],
        is_current=True,
        verified=True,
        notes=(
            "Statutory foundational ordinance re-hosted on official bennett.edu.in in May 2024. "
            "55 pages digital text. Covers university-wide statutory requirements."
        ),
    ),
    SourceEntry(
        filename="UFM-Guidelines-2024.pdf",
        title="Instructions and Penalty for Use of Unfair Means (UFM)",
        description=(
            "Official Examination Department regulations governing conduct in examination "
            "halls and penalties for unfair means at Bennett University. Details categories "
            "2.1 through 2.6 of UFM offences, disciplinary committee procedures, penalties, "
            "and standard reporting forms."
        ),
        source_url=(
            "https://www.bennett.edu.in/wp-content/uploads/2024/05/UFM.pdf"
        ),
        effective_date="2017-12-11",
        academic_year="2017-18 onwards",
        program_applicability=["All Students", "B.Tech", "Undergraduate", "Postgraduate"],
        is_current=True,
        verified=True,
        notes=(
            "Official examination discipline regulations published by Bennett University "
            "Examination Department, re-hosted May 2024. 7 pages, OCR extracted via RapidOCR. "
            "Prescribes mandatory penalties for exam malpractice."
        ),
    ),
]


def get_verified_sources() -> list[SourceEntry]:
    """Return only manually verified source entries."""
    return [s for s in OFFICIAL_SOURCES if s.verified]


def get_all_sources() -> list[SourceEntry]:
    """Return all registered sources including unverified placeholders."""
    return list(OFFICIAL_SOURCES)
