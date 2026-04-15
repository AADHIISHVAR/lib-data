import requests
import re
import time
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def fetch_data(isbn: str) -> dict:
    """
    Scrapes isbnsearch.org for cover and full index/description.
    """
    result = {"cover_url": "", "index_data": ""}
    if not isbn or len(str(isbn).replace("-", "").strip()) < 10:
        return result

    isbn_clean = str(isbn).replace("-", "").strip()
    url = f"https://isbnsearch.org/isbn/{isbn_clean}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        time.sleep(1.2) 
        res = requests.get(url, headers=headers, timeout=25)
        res.raise_for_status()
        
        if res.status_code == 200:
            match_img = re.search(r'<div class="image">\s*<img src="([^"]+)"', res.text)
            if match_img and "no-image" not in match_img.group(1):
                result["cover_url"] = match_img.group(1)
            
            match_desc = re.search(r'<h2>Book Description</h2>\s*<p>(.*?)</p>', res.text, re.DOTALL)
            if match_desc:
                clean_text = re.sub('<[^<]+?>', '', match_desc.group(1))
                result["index_data"] = clean_text.strip()
                
    except requests.exceptions.RequestException as e:
        raise e
    except Exception as e:
        print(f"    [ISBNSearch Error] {e}")
        
    return result
