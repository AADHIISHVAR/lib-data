"""
Librarian AI - Local Enrichment Pipeline (v1.0-Windows)
Optimized for NVIDIA RTX 3050 (6GB VRAM)
"""

import sqlite3
import time
import os
import sys
import json
import re
import requests
from datetime import datetime
from fetchers import open_library, google_books, local_llama, isbn_search, isbndb

DB_PATH = "uniqueBooks.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_schema():
    conn = get_conn()
    cols = [
        ("description", "TEXT"), 
        ("cover_url", "TEXT"), 
        ("enrich_source", "TEXT"), 
        ("key_topics", "TEXT"), 
        ("target_audience", "TEXT"), 
        ("ai_keywords", "TEXT"), 
        ("index_data", "TEXT")
    ]
    for c, t in cols:
        try:
            conn.execute(f"ALTER TABLE unique_books ADD COLUMN {c} {t}")
        except:
            pass
    conn.commit()
    conn.close()

def clean_and_merge(text_list):
    sentences = []
    seen = set()
    for text in text_list:
        if not text: continue
        # Split by sentence markers but keep them
        parts = re.split(r'(?<=[.!?]) +', str(text))
        for s in parts:
            c = s.strip().lower()
            if c and len(c) > 15 and c not in seen:
                sentences.append(s.strip())
                seen.add(c)
    return " ".join(sentences)

def enrichment_job():
    setup_schema()
    
    conn = get_conn()
    # Find books that need enrichment
    pending = conn.execute("SELECT * FROM unique_books WHERE (description IS NULL OR length(description) < 200)").fetchall()
    conn.close()
    
    total = len(pending)
    print(f"\n[START] Processing {total} books locally.\n")
    
    for idx, row in enumerate(pending):
        acc_no, title, author, isbn = row['acc_no'], row['title'], row['author'], row['isbn']
        isbn_clean = str(isbn).replace("-", "").strip() if isbn else ""
        
        print(f"\n─── BOOK {idx+1}/{total}: {title} ───")
        
        # 1. Fetch Basic Meta (API)
        all_descs, meta, sources = [], {"cover": ""}, []
        
        # Google Books
        try:
            gb = google_books.fetch(title, author, isbn_clean)
            if gb:
                if gb.get("description"): 
                    all_descs.append(gb["description"])
                    sources.append("Google")
                if gb.get("cover_url"): meta["cover"] = gb["cover_url"]
        except: pass

        # Open Library
        try:
            ol = open_library.fetch(title, author, isbn_clean)
            if ol:
                if ol.get("description_raw"):
                    d = ol["description_raw"]
                    desc = d.get("value", d) if isinstance(d, dict) else d
                    all_descs.append(desc)
                    sources.append("OpenLibrary")
                if ol.get("cover_url") and not meta["cover"]: 
                    meta["cover"] = ol["cover_url"]
        except: pass

        # ISBN Search (Scraper)
        try:
            s = isbn_search.fetch_data(isbn_clean)
            if s and s.get("cover_url") and not meta["cover"]: 
                meta["cover"] = s["cover_url"]
                sources.append("ISBNSearch")
        except: pass

        merged_desc = clean_and_merge(all_descs)
        
        # 2. AI DEEPENING (Local Llama)
        # Even if we have a description, we want the AI's "Deep Dive" scholarly analysis
        print(f"    [AI] Requesting scholarly analysis from local Llama...")
        ai_data = local_llama.generate(title, author, row['subject'], row['keywords'], str(row['dept_no']), row['look_under'])
        
        if ai_data and len(ai_data.get("description", "")) > 300:
            if len(merged_desc) < 150: 
                merged_desc = ai_data["description"]
            else: 
                merged_desc = clean_and_merge([merged_desc, ai_data["description"]])
            sources.append("Local-Llama-GPU")
        else:
            print(f"    [WARN] AI generation failed or was too short.")
            ai_data = {"key_topics": "", "target_audience": "Academic"}

        # 3. Save to DB
        if len(merged_desc) > 100:
            # Placeholder cover if still missing
            if not meta["cover"]:
                letter = title[0].upper() if title else "B"
                meta["cover"] = f"https://via.placeholder.com/300x450/1a1a1f/c8a96e?text={letter}"

            try:
                conn = get_conn()
                conn.execute(
                    "UPDATE unique_books SET description=?, cover_url=?, enrich_source=?, key_topics=?, target_audience=? WHERE acc_no=?", 
                    (merged_desc, meta['cover'], ", ".join(set(sources)), ai_data.get("key_topics", ""), ai_data.get("target_audience", "Academic"), acc_no)
                )
                conn.commit()
                conn.close()
                print(f"    [OK] Saved. Sources: {', '.join(set(sources))}")
            except Exception as e:
                print(f"    [ERR] DB update failed: {e}")
        else:
            print(f"    [SKIP] Could not gather enough data for this book.")

def main():
    banner = """
    ==================================================
       LIBRARIAN AI - WINDOWS LOCAL ENRICHER v1.0
       Target: NVIDIA RTX 3050 (6GB VRAM)
    ==================================================
    """
    print(banner)
    if not os.path.exists(DB_PATH):
        print(f"[FATAL] Database file '{DB_PATH}' not found in current directory.")
        sys.exit(1)
    
    enrichment_job()

if __name__ == "__main__":
    main()
