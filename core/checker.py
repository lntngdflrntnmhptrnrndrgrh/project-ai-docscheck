import difflib
from fuzzywuzzy import fuzz

def check_items(checklist_items, text_per_page, item_order):
    """
    Memeriksa item dengan metode pencocokan yang berbeda (title vs presence)
    untuk setiap jenis item checklist.
    """
    results = []

    for item_name in item_order:
        # Dapatkan konfigurasi untuk item saat ini
        config = checklist_items.get(item_name)
        if not config:
            results.append({"Item": item_name, "Status": "NOK", "Pages": []})
            continue

        keywords = config.get("keywords", [])
        method = config.get("method", "presence")
        found_pages = []

        if not keywords:
            results.append({"Item": item_name, "Status": "NOK", "Pages": []})
            continue

        # Loop melalui setiap halaman
        for i, page_text in enumerate(text_per_page):
            if not page_text:
                continue

            page_text_lower = page_text.lower()
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # --- LOGIKA PENCARIAN CERDAS ---
                match_found = False
                if method == "title":
                    # Untuk judul, cari per baris dengan kemiripan sangat tinggi
                    for line in page_text_lower.splitlines():
                        # fuzz.ratio membandingkan kemiripan seluruh string
                        if fuzz.ratio(keyword_lower, line.strip()) > 85:
                            match_found = True
                            break # Hentikan loop baris
                
                elif method == "presence":
                    # Untuk frasa, cukup cari keberadaannya di manapun dalam teks halaman
                    # Normalisasi dengan mengganti baris baru menjadi spasi
                    normalized_page_text = ' '.join(page_text_lower.split())
                    if keyword_lower in normalized_page_text:
                        match_found = True

                if match_found:
                    # Jika ditemukan di halaman ini, catat dan lanjut ke halaman berikutnya
                    if i + 1 not in found_pages:
                        found_pages.append(i + 1)
                    # Tidak break loop halaman, agar bisa menemukan di halaman lain juga jika ada
        
        result = {
            "Item": item_name,
            "Status": "OK" if found_pages else "NOK",
            "Pages": found_pages
        }
        results.append(result)

    return results