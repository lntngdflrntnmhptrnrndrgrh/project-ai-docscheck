from fuzzywuzzy import fuzz

def check_items(items, doc_text):
    results = []
    for item in items:
        found = False
        page_index = None
        for idx, page in enumerate(doc_text):
            if fuzz.partial_ratio(item.lower(), page.lower()) > 80:
                found = True
                page_index = idx + 1  # halaman mulai dari 1
                break
        results.append({
            "Item yg Diperiksa": item,
            "Status": "OK" if found else "NOK",
            "Keterangan": f"ADA di halaman {page_index}" if found else "TIDAK ADA"
        })
    return results