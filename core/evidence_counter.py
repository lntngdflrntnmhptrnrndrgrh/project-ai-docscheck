# core/evidence_counter.py
import pytesseract
import re
import pandas as pd

# Kamus ini memetakan Designator dari BOQ ke pola teks yang ada di label foto
LABEL_MAP = {
    "PU-S9.0-140": "TN9",
    "PU-S7.0-400NM": r"TN7\s*2S", # Menggunakan regex untuk menangani spasi
    "PU-ASDE--50/70": "PU-AS-DE",
    "PU-AS-SC": "PU-AS-SC",
    "Label Kabel Distribusi (KU FO)": "LABEL KABEL",
    "Slack Support HH": "SLACK SUPPORT",
    "ODP Solid-PB-8 AS": "ODP-SRR-FK", # Asumsi berdasarkan foto ODP
    # Designator lain bisa ditambahkan di sini jika memiliki bukti foto
}

def parse_label_number(label_part):
    """
    Menghitung jumlah dari label seperti '1', '2&3' (dihitung 2), atau '15&16' (dihitung 2).
    """
    if '&' in label_part:
        return 2 # Asumsi format X&Y selalu dihitung 2
    elif label_part.isdigit():
        return 1
    return 0

def count_evidence(images):
    """
    Memindai semua gambar, melakukan OCR, dan menghitung jumlah bukti
    berdasarkan LABEL_MAP.
    """
    evidence_counts = {designator: 0 for designator in LABEL_MAP.keys()}
    
    for image in images:
        try:
            page_text = pytesseract.image_to_string(image, lang="ind+eng", config="--psm 3")
            lines = page_text.splitlines()
            
            for line in lines:
                for designator, pattern in LABEL_MAP.items():
                    # Cari pola label di setiap baris
                    if re.search(pattern, line, re.IGNORECASE):
                        # Jika pola ditemukan, coba ekstrak nomor setelahnya
                        # Contoh: mencari angka setelah "PU-AS-DE -"
                        label_parts = re.findall(r'-\s*([\d&]+)', line)
                        if label_parts:
                            for part in label_parts:
                                evidence_counts[designator] += parse_label_number(part)
                        else:
                            # Jika tidak ada format nomor (seperti SLACK SUPPORT), hitung 1 per kemunculan
                            evidence_counts[designator] += 1
                        break # Pindah ke baris selanjutnya setelah menemukan kecocokan
        except Exception:
            continue
            
    # Ubah hasil hitungan menjadi DataFrame
    counted_df = pd.DataFrame(
        list(evidence_counts.items()),
        columns=['DESIGNATOR', 'JUMLAH_BUKTI']
    )
    return counted_df