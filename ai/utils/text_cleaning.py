"""
PakLaw AI — Text Cleaning Utilities

Removes duplicate white spaces, normalizes special characters,
and clean scanned OCR text anomalies.
"""

import re


def clean_text(text: str) -> str:
    """Clean raw extracted or OCR text."""
    if not text:
        return ""

    # Replace windows line endings
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

    # Mask redundant spaces/newlines
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Clean character anomalies typical in OCR
    cleaned = cleaned.strip()

    return cleaned


def extract_sections_from_text(text: str) -> list[dict]:
    """
    Attempt to extract section titles and numbers from Pakistani legal document text.
    Matches patterns like 'Section 4. Title' or '4. Title'.
    """
    sections = []
    lines = text.split("\n")

    # Section pattern: 'Section 4' or '4.' or 'SECTION 4A'
    pattern = re.compile(r"^\s*(?:Section|SECTION)\s*([0-9A-Za-z]+)\.?\s*(.*)$")
    alternative_pattern = re.compile(r"^\s*([0-9]+)\.?\s+([A-Z][a-zA-Z\s,]{3,50})$")

    current_section_num = None
    current_section_title = None
    section_buffer = []

    for line in lines:
        match = pattern.match(line) or alternative_pattern.match(line)
        if match:
            # Save previous section if it exists
            if current_section_num and section_buffer:
                sections.append(
                    {
                        "section_number": current_section_num,
                        "section_title": current_section_title,
                        "content": "\n".join(section_buffer).strip(),
                    }
                )
                section_buffer = []

            current_section_num = match.group(1).strip()
            current_section_title = match.group(2).strip() or None
        else:
            section_buffer.append(line)

    # Append remaining
    if current_section_num and section_buffer:
        sections.append(
            {
                "section_number": current_section_num,
                "section_title": current_section_title,
                "content": "\n".join(section_buffer).strip(),
            }
        )

    return sections
