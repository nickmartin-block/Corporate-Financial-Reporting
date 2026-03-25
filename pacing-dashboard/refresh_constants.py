#!/usr/bin/env python3
"""Reads Constants deck slide 2 (TL;DR) and generates constants_data.js."""

import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLIDES_JSON = "/tmp/constants_slides.json"
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "constants_data.js")
DECK_ID = "1Yt6WwNtNn53E5U0_iRgN6-eacen52ClndnZDbyAN3z0"
DECK_URL = f"https://docs.google.com/presentation/d/{DECK_ID}/edit"

KNOWN_SECTIONS = ["SELLERS/SQUARE", "INDIVIDUALS/CASH", "ANYTHING INTERESTING?"]


def parse_tldr(text):
    """Parse the TL;DR text into sections with bullet items."""
    # Ensure section headers have newlines around them
    for header in KNOWN_SECTIONS:
        text = text.replace(header, "\n" + header + "\n")

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    sections = []
    current = None

    for line in lines:
        if line in KNOWN_SECTIONS:
            if current:
                sections.append(current)
            current = {"title": line, "items": []}
        elif current is not None:
            current["items"].append(line)

    if current:
        sections.append(current)

    # Fix concatenated items (e.g., "in MarchMR:" → split into two items)
    for section in sections:
        fixed = []
        for item in section["items"]:
            parts = re.split(r"(?<=[a-z])(?=[A-Z]{2,}:)", item)
            fixed.extend([p.strip() for p in parts if p.strip()])
        section["items"] = fixed

    return sections


def main():
    if not os.path.exists(SLIDES_JSON):
        print("No slides data found at", SLIDES_JSON)
        return

    with open(SLIDES_JSON) as f:
        data = json.load(f)

    slides = data.get("slides", [])
    if len(slides) < 2:
        print("Not enough slides")
        return

    # Slide 1 (index 0): title with data-through dates
    title_slide = slides[0]
    data_thru = ""
    for t in title_slide.get("texts", []):
        txt = t.get("text", "")
        if "data thru" in txt.lower() or "CONSTANTS" in txt:
            data_thru = txt.strip()

    # Slide 2 (index 1): TL;DR
    tldr_slide = slides[1]
    tldr_text = ""
    as_of_text = ""
    for t in tldr_slide.get("texts", []):
        txt = t.get("text", "")
        if txt.strip().upper().startswith("TL"):
            as_of_text = txt.strip()
        elif len(txt) > len(tldr_text):
            tldr_text = txt.strip()

    # Extract date
    date_match = re.search(r"(\d{8})", as_of_text or data_thru)
    as_of = date_match.group(1) if date_match else ""

    # Parse data-through line from title
    thru_lines = []
    for line in data_thru.split("\n"):
        line = line.strip()
        if "data thru" in line.lower() or "thru" in line.lower():
            thru_lines.append(line)

    sections = parse_tldr(tldr_text)

    result = {
        "as_of": as_of,
        "data_thru": " | ".join(thru_lines) if thru_lines else "",
        "sections": sections,
        "deck_url": DECK_URL,
    }

    js = (
        f"// Constants data — auto-refreshed from deck\n"
        f"var DASHBOARD_CONSTANTS = {json.dumps(result, indent=2)};\n"
    )
    with open(OUTPUT_PATH, "w") as f:
        f.write(js)

    print(f"✓ constants_data.js — {len(sections)} sections, as of {as_of}")


if __name__ == "__main__":
    main()
