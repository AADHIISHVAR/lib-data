import requests
from tenacity import retry, stop_after_attempt, wait_exponential

class RateLimitError(Exception): pass

BASE  = "https://openlibrary.org"
COVER = "https://covers.openlibrary.org/b"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch(title: str, author: str, isbn: str = "") -> dict:
    result = {}
    try:
        params = {"limit": 1}
        if isbn and isbn not in ("-", "None", "0", "", "NULL"):
            isbn_clean = str(isbn).replace("-", "").strip()
            params["isbn"] = isbn_clean
        else:
            params["title"] = title
            if author: params["author"] = author

        res = requests.get(f"{BASE}/search.json", params=params, timeout=30)
        if res.status_code == 429: raise RateLimitError()
        res.raise_for_status()
            
        docs = res.json().get("docs", [])
        if docs:
            doc = docs[0]
            result = {
                "title": doc.get("title"),
                "subtitle": doc.get("subtitle"),
                "first_publish_year": doc.get("first_publish_year"),
                "number_of_pages_median": doc.get("number_of_pages_median"),
                "publisher": doc.get("publisher", []),
                "isbn": doc.get("isbn", []),
                "subjects": doc.get("subject", []),
                "ratings_average": doc.get("ratings_average"),
                "ratings_count": doc.get("ratings_count"),
                "language": doc.get("language", []),
                "key": doc.get("key"),
                "author_name": doc.get("author_name", [])
            }
            
            if doc.get("cover_i"):
                result["cover_url"] = f"{COVER}/id/{doc.get('cover_i')}-L.jpg"
            
            # Fetch deeper data from Books API if key exists
            work_key = doc.get("key")
            if work_key:
                work = requests.get(f"{BASE}{work_key}.json", timeout=15).json()
                result["description_raw"] = work.get("description")
                result["toc"] = work.get("table_of_contents", [])
                result["excerpts"] = work.get("excerpts", [])

    except RateLimitError: raise
    except requests.exceptions.RequestException as e:
        # Re-raise to trigger tenacity retry
        raise e
    except Exception as e: 
        print(f"    [OL Error] {e}")
    return result
