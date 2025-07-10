# core/evidence_counter.py
import pytesseract
import re

LABEL_MAP = {
    "SC-OF-SM-24": "JOIN CLOSURE",
    "ODP Solid-PB-8 AS": "ODP-SRR-FK",
    "PU-S9.0-140": "TN9",
    "Slack Support HH": "SLACK SUPPORT",
    "Label Kabel Distribusi (KU FO)": "LABEL KABEL",
    "PU-S7.0-400NM": r"TN7\s*2S",
    "PU-AS-DE-50/70": "PU-AS-DE",
    "PU-AS-SC": "PU-AS-SC",
}

def collect_evidence(images, verified_boq_df, text_per_page, boq_page_index):
    evidence_galleries = {row["DESIGNATOR"]: [] for index, row in verified_boq_df.iterrows()}
    found_pages_for_designator = {designator: set() for designator in evidence_galleries.keys()}

    for i, image in enumerate(images):
        if (i < len(text_per_page) and not text_per_page[i]) or i == boq_page_index:
            continue
            
        try:
            page_text_ocr = pytesseract.image_to_string(image, lang="ind+eng", config="--psm 3")
        except Exception:
            continue

        for designator, pattern in LABEL_MAP.items():
            if designator in evidence_galleries and re.search(pattern, page_text_ocr, re.IGNORECASE):
                if i not in found_pages_for_designator[designator]:
                    evidence_galleries[designator].append(image)
                    found_pages_for_designator[designator].add(i)
    return evidence_galleries