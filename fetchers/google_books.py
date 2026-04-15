import requests
from tenacity import retry, stop_after_attempt, wait_exponential

class RateLimitError(Exception): pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch(title: str, author: str, isbn: str = "") -> dict:
    result = {}
    try:
        if isbn and isbn not in ("-", "None", "0", "", "NULL"):
            query = f"isbn:{str(isbn).replace('-','').strip()}"
        else:
            query = f'intitle:"{title}"'
            if author: query += f' inauthor:"{author}"'

        res = requests.get("https://www.googleapis.com/books/v1/volumes",
                           params={"q": query, "maxResults": 1}, timeout=30)
        
        if res.status_code == 429: raise RateLimitError()
        res.raise_for_status()
        
        items = res.json().get("items", [])
        if not items: return result

        info = items[0].get("volumeInfo", {})
        
        result = {
            "title": info.get("title"),
            "subtitle": info.get("subtitle"),
            "authors": info.get("authors", []),
            "publisher": info.get("publisher"),
            "publishedDate": info.get("publishedDate"),
            "description": info.get("description"),
            "pageCount": info.get("pageCount"),
            "categories": info.get("categories", []),
            "averageRating": info.get("averageRating"),
            "ratingsCount": info.get("ratingsCount"),
            "language": info.get("language"),
            "previewLink": info.get("previewLink"),
            "infoLink": info.get("infoLink"),
            "printType": info.get("printType"),
            "dimensions": info.get("dimensions", {}),
            "imageLinks": info.get("imageLinks", {})
        }
        
        imgs = info.get("imageLinks", {})
        url = imgs.get("extraLarge") or imgs.get("large") or imgs.get("medium") or imgs.get("small") or imgs.get("thumbnail")
        if url: result["cover_url"] = url.replace("http://", "https://")

    except RateLimitError: raise
    except requests.exceptions.RequestException as e:
        # Re-raise to trigger tenacity retry
        raise e
    except Exception as e: 
        print(f"    [GB Error] {e}")
    return result
