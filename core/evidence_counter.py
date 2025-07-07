# core/evidence_counter.py
import pytesseract
import re
import pandas as pd

# Kamus ini memetakan Designator ke pola teks yang ada di label foto
LABEL_MAP = {
    "SC-OF-SM-24": "JOIN CLOSURE",
    "ODP Solid-PB-8 AS": "ODP-SRR-FK",
    "PU-S9.0-140": "TN9",
    "Slack Support HH": "SLACK SUPPORT",
    "Label Kabel Distribusi (KU FO)": "LABEL KABEL",
    "PU-S7.0-400NM": r"TN7\s*2S",
    "PU-ASDE--50/70": "PU-AS-DE",
    "PU-AS-SC": "PU-AS-SC",
}

def collect_evidence(images, verified_boq_df):
    """
    Mengumpulkan semua halaman gambar yang relevan untuk setiap designator di BOQ.
    """
    evidence_galleries = {row["DESIGNATOR"]: [] for index, row in verified_boq_df.iterrows()}
    
    # Proses setiap halaman satu per satu
    for i, image in enumerate(images):
        # Lewati halaman-halaman awal yang tidak mungkin berisi bukti
        if i < 7:
            continue
            
        try:
            page_text = pytesseract.image_to_string(image, lang="ind+eng", config="--psm 3")
        except Exception:
            continue

        # Untuk setiap designator, cek apakah buktinya ada di halaman ini
        for designator, pattern in LABEL_MAP.items():
            if re.search(pattern, page_text, re.IGNORECASE):
                # Jika ditemukan, tambahkan gambar halaman ini ke galeri designator tersebut
                if designator in evidence_galleries:
                    evidence_galleries[designator].append(image)
                # Hentikan pencarian di halaman ini untuk designator lain agar tidak tumpang tindih
                break
                
    return evidence_galleries