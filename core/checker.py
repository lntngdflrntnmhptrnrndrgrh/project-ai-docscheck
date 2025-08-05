import difflib
from fuzzywuzzy import fuzz
import re

def check_items(checklist_items, text_per_page, item_order):
    results = []

    for item_name in item_order:
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

        if isinstance(method, str):
            method = [method]

        for i, page_text in enumerate(text_per_page):
            if not page_text:
                continue

            page_text_lower = page_text.lower()
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                match_found = False
                if 'title' in method:
                    for line in page_text_lower.splitlines():
                        if fuzz.ratio(keyword_lower, line.strip()) > 85:
                            match_found = True
                            break

                if not match_found and 'regex' in method:
                    if re.search(keyword, page_text, re.IGNORECASE):
                        match_found = True

                if not match_found and 'presence' in method:
                    normalized_page_text = ' '.join(page_text_lower.split())
                    if keyword_lower in normalized_page_text:
                        match_found = True

                if match_found and (i + 1) not in found_pages:
                    found_pages.append(i + 1)
        
        result = {
            "Item": item_name,
            "Status": "OK" if found_pages else "NOK",
            "Pages": found_pages
        }
        results.append(result)

    return results