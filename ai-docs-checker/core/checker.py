from fuzzywuzzy import fuzz

def check_items(checklist, text_per_page):
    results = []
    for i, (label, keyword) in enumerate(checklist.items(), 1):
        found = False
        page_index = "-"
        for idx, page_text in enumerate(text_per_page):
            if keyword.lower() in page_text.lower():
                found = True
                page_index = idx + 1
                break
        results.append({
            "No": i,
            "Item yg Diperiksa": label,
            "OK/NOK": "OK" if found else "NOK",
            "Keterangan": f"ADA di Hal. {page_index}" if found else "TIDAK ADA"
        })
    return results
