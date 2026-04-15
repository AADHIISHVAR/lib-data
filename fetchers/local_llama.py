import requests, os, time, json
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# --- LOCAL CONFIGURATION ---
# Default for Ollama: http://localhost:11434/v1/chat/completions
# Default for LM Studio: http://localhost:1234/v1/chat/completions
API_URL = os.getenv("LOCAL_AI_URL", "http://localhost:11434/v1/chat/completions")
MODEL_NAME = os.getenv("LOCAL_AI_MODEL", "llama3.1:8b-instruct-q4_K_M") # Optimized for 6GB VRAM

def flatten_json_to_text(data):
    """Converts complex nested JSON into a readable academic paragraph."""
    if isinstance(data, str): return data
    lines = []
    if isinstance(data, dict):
        for key, value in data.items():
            k = key.replace("_", " ").title()
            if isinstance(value, (dict, list)):
                lines.append(f"{k}: {flatten_json_to_text(value)}")
            else:
                lines.append(f"{k}: {value}")
    elif isinstance(data, list):
        return ", ".join([flatten_json_to_text(i) for i in data])
    return " ".join(lines)

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_fixed(5), 
)
def generate(title: str, author: str, subject: str, keywords: str, dept: str, look_under: str, token: str = "") -> dict:
    subj = subject if subject and subject not in ("-","0","None") else "Academic Research"
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system", 
                "content": "You are a world-class academic librarian. Provide an EXHAUSTIVE technical analysis (400 words). Focus on theoretical frameworks and curriculum value. Return ONLY valid JSON."
            },
            {
                "role": "user", 
                "content": f"Provide a 400-word deep-dive scholarly analysis for:\nBOOK: '{title}'\nAUTHOR: {author}\nFIELD: {subj}\nKEYWORDS: {keywords}\n\nReturn JSON with keys: 'description', 'key_topics' (list), 'target_audience'."
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
        "response_format": { "type": "json_object" }
    }

    try:
        print(f"    [LOCAL-AI] Requesting {MODEL_NAME} at {API_URL}...")
        res = requests.post(API_URL, json=payload, timeout=300) # Longer timeout for local inference
        
        if res.status_code == 200:
            content = res.json()['choices'][0]['message']['content']
            # Clean possible markdown markers if not strictly JSON
            content = content.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(content)
            
            desc_raw = parsed.get("description") or parsed.get("analysis") or parsed.get("scholarly_analysis") or parsed
            description_text = flatten_json_to_text(desc_raw)
            
            topics = parsed.get("key_topics") or parsed.get("topics") or []
            audience = parsed.get("target_audience") or "Academic / Research"
            
            return {
                "description": description_text,
                "key_topics": ", ".join(topics) if isinstance(topics, list) else str(topics),
                "target_audience": str(audience)
            }
        else:
            print(f"    [LOCAL-AI ERR] Status {res.status_code}: {res.text}")
            return None
    except Exception as e:
        print(f"    [LOCAL-AI ERR] {str(e)}")
        return None
