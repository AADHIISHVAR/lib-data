import requests
import os
from tenacity import retry, stop_after_attempt, wait_exponential

ISBNDB_KEY = os.getenv("ISBNDB_KEY", "")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch(isbn: str) -> dict:
    if not ISBNDB_KEY or not isbn: return {}
    
    url = f"https://api2.isbndb.com/book/{isbn.replace('-', '')}"
    headers = {"Authorization": ISBNDB_KEY}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            book = res.json().get("book", {})
            return {
                "overview": book.get("overview"),
                "synopsis": book.get("synopsis"),
                "subjects": book.get("subjects", []),
                "image": book.get("image")
            }
    except Exception as e:
        print(f"    [ISBNdb Error] {e}")
    return {}
