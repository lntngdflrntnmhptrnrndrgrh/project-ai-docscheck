# core/checker.py
import difflib
from fuzzywuzzy import fuzz
#def match_text_fuzzy(text_line, keyword, threshold=0.8):
#    """
#    Membandingkan string hanya berdasarkan skor kemiripan keseluruhan.
#    Aturan "kata pertama" dihapus agar lebih toleran terhadap kesalahan OCR.
#    """
#    clean_line = ' '.join(text_line.lower().split())
#    clean_keyword = ' '.join(keyword.lower().split())
#    
#    if not clean_line or not clean_keyword:
#        return False
#    
#    line_words = clean_line.split()
#    keyword_words = clean_keyword.split()
#
#    if line_words[0] != keyword_words[0]:
#        return False
#    
#    # Hanya menggunakan pengecekan similarity score
#    score = difflib.SequenceMatcher(None, clean_line, clean_keyword).ratio()
#    return score >= threshold
#
def check_items(checklist_items, text_per_page, item_order):
    """
    Memeriksa keberadaan item di semua halaman dan mengumpulkan semua halaman yang cocok.
    """
    results = []

    for item_name in item_order:
        keywords = checklist_items.get(item_name, [])
        found_pages = []
        
        if not keywords:
            results.append({
                "Item": item_name,
                "Status": "NOK",
                "Pages": []
            })
            continue

        for i, page_text in enumerate(text_per_page):
            if not page_text:
                continue
            
            normalized_page_text = page_text.replace('\n', ' ').lower()

            for keyword in keywords:
                if fuzz.partial_ratio(keyword.lower(), normalized_page_text) > 90:
                    found_pages.append(i + 1)
                    break
            #lines = page_text.splitlines()
            #for line in lines:
            #    if any(match_text_fuzzy(line.strip(), kw) for kw in keywords):
            #        found_pages.append(i + 1)
            #        break 
        
        result = {
            "Item": item_name,
            "Status": "OK" if found_pages else "NOK",
            "Pages": found_pages
        }
        results.append(result)

    return results