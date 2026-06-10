"""ATS-compliant resume PDF rendering.

Turns a resume's structured_data into a single-column, text-flowing PDF using
ReportLab Platypus. The output deliberately avoids multi-column layouts, text
boxes, images, and layout tables -- the structures that defeat applicant
tracking systems -- so the document parses back as clean, ordered text.
"""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate

_DARK = HexColor("#1a1a1a")
_GREY = HexColor("#555555")
_RULE = HexColor("#999999")

_NAME = ParagraphStyle(
    "Name", fontName="Helvetica-Bold", fontSize=18, leading=22,
    textColor=_DARK, spaceAfter=2,
)
_CONTACT = ParagraphStyle(
    "Contact", fontName="Helvetica", fontSize=9, leading=12, textColor=_GREY,
)
_SECTION = ParagraphStyle(
    "Section", fontName="Helvetica-Bold", fontSize=11, leading=14,
    textColor=_DARK, spaceBefore=12, spaceAfter=2,
)
_ENTRY_TITLE = ParagraphStyle(
    "EntryTitle", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
    textColor=_DARK, spaceBefore=6,
)
_ENTRY_META = ParagraphStyle(
    "EntryMeta", fontName="Helvetica-Oblique", fontSize=9, leading=12,
    textColor=_GREY, spaceAfter=2,
)
_BODY = ParagraphStyle(
    "Body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=_DARK,
)
_BULLET = ParagraphStyle(
    "Bullet", fontName="Helvetica", fontSize=9.5, leading=13, textColor=_DARK,
    leftIndent=14, bulletIndent=3, bulletFontName="Helvetica", bulletFontSize=8,
    spaceBefore=1,
)


def _clean(value) -> str:
    return str(value).strip()


def _contact_line(contact: dict) -> str:
    """Join present contact fields into one escaped, pipe-separated line."""
    fields = ["email", "phone", "location", "linkedin", "github", "website"]
    parts = [_clean(contact.get(f, "")) for f in fields]
    return "  |  ".join(escape(p) for p in parts if p)


def _section_heading(title: str) -> list:
    return [
        Paragraph(escape(title), _SECTION),
        HRFlowable(width="100%", thickness=0.5, color=_RULE, spaceBefore=1, spaceAfter=4),
    ]


def _entry_header(primary: str, secondary: str) -> list:
    bits = [b for b in (primary, secondary) if b]
    if not bits:
        return []
    return [Paragraph(escape("  -  ".join(bits)), _ENTRY_TITLE)]


def _entry_meta(*values: str) -> list:
    bits = [v for v in values if v]
    if not bits:
        return []
    return [Paragraph(escape("  |  ".join(bits)), _ENTRY_META)]


def _experience_flowables(experience: list) -> list:
    story: list = []
    for item in experience:
        story += _entry_header(_clean(item.get("job_title", "")), _clean(item.get("company", "")))

        start, end = _clean(item.get("start_date", "")), _clean(item.get("end_date", ""))
        dates = " - ".join(d for d in (start, end) if d)
        story += _entry_meta(dates, _clean(item.get("location", "")))

        for resp in item.get("responsibilities", []):
            text = _clean(resp)
            if text:
                story.append(Paragraph(escape(text), _BULLET, bulletText="\u2022"))
    return story


def _education_flowables(education: list) -> list:
    story: list = []
    for item in education:
        story += _entry_header(_clean(item.get("degree", "")), _clean(item.get("institution", "")))

        start, end = _clean(item.get("start_date", "")), _clean(item.get("end_date", ""))
        dates = " - ".join(d for d in (start, end) if d)
        story += _entry_meta(dates, _clean(item.get("details", "")))
    return story


def render_resume_pdf(structured_data: dict) -> bytes:
    """Render structured resume data into an ATS-compliant PDF.

    Returns the PDF as bytes. Empty sections are omitted, so a sparse resume
    still produces a clean document.
    """
    contact = structured_data.get("contact", {}) or {}
    summary = _clean(structured_data.get("summary", ""))
    skills = [_clean(s) for s in structured_data.get("skills", []) if _clean(s)]
    experience = structured_data.get("experience", []) or []
    education = structured_data.get("education", []) or []

    story: list = []

    name = _clean(contact.get("full_name", "")) or "Resume"
    story.append(Paragraph(escape(name), _NAME))
    contact_line = _contact_line(contact)
    if contact_line:
        story.append(Paragraph(contact_line, _CONTACT))

    if summary:
        story += _section_heading("Summary")
        story.append(Paragraph(escape(summary), _BODY))

    if skills:
        story += _section_heading("Skills")
        story.append(Paragraph(escape(", ".join(skills)), _BODY))

    if experience:
        story += _section_heading("Experience")
        story += _experience_flowables(experience)

    if education:
        story += _section_heading("Education")
        story += _education_flowables(education)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=name,
    )
    doc.build(story)
    return buffer.getvalue()