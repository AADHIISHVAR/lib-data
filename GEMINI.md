# Librarian AI — Project Context

A comprehensive library assistant system that combines vector-based semantic search with Large Language Models (LLMs) to help students discover books in a college library system.

## 🏗️ Architecture Overview

The project follows a **Dual-Frontend Architecture** with the modern Svelte UI as the primary interface:

1.  **Primary UI (Svelte):** A lightning-fast, Vanilla JS-based frontend.
    *   **Deployment:** Built into the Docker image for **Hugging Face Spaces** and also hosted on **GitHub Pages**.
    *   **Optimization:** Zero WASM overhead, hardware-accelerated scrolling, and optimized for mobile touch targets.
    *   **Live URL:** `https://AADHIISHVAR.github.io/librarian-ui/`
2.  **Legacy UI (Leptos):** A Rust-based WebAssembly (WASM) SPA.
    *   **Role:** Maintained as source-code fallback.
3.  **Backend (Axum):** Optimized Rust web server acting as the central API Gateway.
    *   **Unified Serving:** Serves Svelte static files from `/app/frontend/dist` and provides the REST API at `/api/*`.
    *   **Security:** Implements hardened CORS, manual origin verification, and per-IP rate limiting.
4.  **Sidecar (Python FastAPI):** Machine learning service for embeddings and LLM generation.
    *   **Database Retrieval:** Handles semantic vector search via `sqlite-vec`.
    *   **Scale:** Catalog search limits increased to **1000 results** per query.

## 🛠️ Technology Stack

*   **Frontends:** Svelte 4 (JS), Leptos (Rust/WASM).
*   **Backend:** Axum (Rust), Tokio (Runtime).
*   **AI Sidecar:** FastAPI (Python), PyTorch (CPU-optimized).
*   **Database:** SQLite with `sqlite-vec`.
*   **Hosting:** GitHub Pages (UI), Hugging Face Spaces (API & Sidecar).

## 🚀 Deployment & Running

### Cloud Hosting (Unified Deployment)
The application is deployed to **Hugging Face Spaces** using a multi-stage `Dockerfile`:
1.  **Frontend Build:** Builds the Svelte production bundle using Node.js.
2.  **Backend Build:** Compiles the Axum binary with size optimizations.
3.  **Final Image:** 
    *   Uses `python:3.11-slim`.
    *   Forces **CPU-only PyTorch** to reduce image size.
    *   **Manual Step:** `library_database.db` must be uploaded via the HF Web UI (Files tab) because it exceeds the 10MB Git push limit.

### Svelte UI Deployment (GitHub Pages)
The Svelte UI is hosted on the `gh-pages` branch.
1.  Navigate to `frontend-svelte/`.
2.  Build: `npm run build`.
3.  Deploy: `npx gh-pages -d dist --repo https://github.com/AADHIISHVAR/librarian-ui.git`.
    *   *Note:* Requires a Personal Access Token (PAT) for authentication.

## 🎨 UI Features & Beta Notice (v1.3.0)

### Global Beta Banner
A persistent notification banner is implemented in `App.svelte` to inform users about the application's status.
*   **Content:** Developer note regarding beta status, data availability, and pipeline updates.
*   **Behavior:** Visible on every page reload; can be temporarily dismissed (×) for the current session.
*   **Styling:** Non-intrusive `rgba(200, 169, 110, 0.1)` background with high-visibility icon.

### Search Hero Beta Tag
A "Beta Version" tag is prominently displayed in the `AISearchView.svelte` hero section to ensure context is clear during discovery.

## 📂 Key Files & Directories

*   `/frontend-svelte/`: The mobile-optimized Svelte source code.
*   `/backend/src/main.rs`: Axum router with hardened security middleware and static file mapping.
*   `/sidecar/db.py`: Core database logic with vector search capabilities.
*   `/start_hf.sh`: Production startup script that coordinates the Sidecar and Axum backend.

## 🛡️ Security & API Protection (Implemented v1.2.2)

To prevent unauthorized scraping and abuse of the Hugging Face AI token, the following security layers are active:

### Layer 1: Hardened CORS & Origin Locking
The backend strictly enforces origin verification to prevent unauthorized websites from calling the API.
*   **Implementation:** Manual origin verification in middleware (status: `403 Forbidden` for mismatches).
*   **Whitelisted Origins:** `AADHIISHVAR.github.io`, `aadhiishvar.github.io`, and the Hugging Face Space domain.

### Layer 2: Dual-Header API Authentication
Requires a secure client key for all API requests to block automated bots.
*   **Implementation:** Supports both `Authorization: Bearer <KEY>` (Standard) and `x-librarian-key: <KEY>` (Custom).
*   **Result:** Requests without a valid key are rejected with `401 Unauthorized`.

### Layer 3: Per-IP Rate Limiting (Usage Throttling)
Protects against flood attacks and protects Hugging Face usage credits.
*   **Policy:** **15 requests per minute** per user IP address.
*   **Implementation:** Custom middleware using the `governor` crate with robust `X-Forwarded-For` IP extraction.
*   **Result:** Exceeding the limit returns `429 Too Many Requests`.

## 🗄️ Database Optimizations (v1.4.0 - Deep Enrichment)

We have transformed the raw `combined-library.db` into a production-grade `uniqueBooks.db` specifically optimized for **Deep Semantic Embeddings**.

### 1. Advanced Deduplication & Normalization
*   **Smart Grouping:** Records are merged using a prioritized key (Normalized ISBN-10/13 -> Fallback to Title + Author).
*   **Completeness Selection:** When duplicates exist, the system algorithmically selects the "Master" record based on a completeness score (least empty fields).
*   **Data Aggregation:** Multiple physical copies are consolidated into `total_copies` and `available_copies` columns, with a JSON-ready `all_acc_nos` list.

### 2. The "Deep Data" Schema
To enable high-precision AI search, we added the following high-signal columns:
*   **`description`**: Full academic synopsis (up to 5,000 chars) from Google Books, Open Library, or Llama-3.1.
*   **`key_topics`**: AI-extracted core concepts and fields of study.
*   **`target_audience`**: Categorization by academic level (Undergraduate, Researcher, etc.).
*   **`ai_keywords`**: Specialized search terms generated via LLM analysis.
*   **`cover_url`**: High-resolution image mapping via ISBNSearch.org and Open Library ID.

### 3. Search Performance (Peak Optimization)
*   **`search_blob`**: A unified, lowercase text field containing Title, Author, Subject, Keywords, and Accession numbers. This allows for lightning-fast `LIKE` queries before the vector search even triggers.
*   **Type Integrity:** All columns have been restored to their original SQLite types (INTEGER, REAL, TEXT) to reduce storage overhead and improve indexing speed.

### 4. Enrichment Pipeline (v8.2 - Intelligent Omni-AI)
A robust, multi-stage "Waterfall" pipeline optimized for extreme reliability and high-signal academic data:
1.  **Multi-API Metadata Fetching:**
    *   **Google Books API:** Primary source for academic metadata and initial descriptions.
    *   **Open Library API:** Secondary fallback for descriptions and Table of Contents (TOC).
    *   **ISBN Search Scraper:** High-priority fetching of high-resolution front covers (1.2s delay to prevent blocks).
    *   **ISBNdb:** Bonus metadata aggregator for detailed synopses.
2.  **Omni-AI Deepening (The Waterfall):**
    *   **Primary:** **Qwen-2.5-7B-Instruct** via Hugging Face Router (Native JSON Mode).
    *   **Secondary:** **Phi-3.5-mini-instruct** (High-speed technical analysis).
    *   **Tertiary:** **Llama-3.2-3B-Instruct** (Reliable fallback).
    *   **Final AI:** **Mistral-7B-Instruct-v0.3** (Maximum availability).
3.  **Intelligent Response Handling:**
    *   **Flattening Engine:** Automatically converts complex nested AI JSON responses (like chapter lists) into readable, professional academic paragraphs.
    *   **Librarian's Overview Fallback:** A metadata-driven template engine that generates a ~100-word scholarly introduction using Book Title, Author, Subject, and Department if all AI services are unavailable.
4.  **Stability & Monitoring:**
    *   **Real-time Hardware Tracking:** Per-book logging of CPU and RAM usage to detect memory leaks or resource exhaustion.
    *   **Patient "Wake Up" Logic:** 60-second retry loops for `503` (Cold Start) and `429` (Rate Limit) errors.
    *   **Direct REST Implementation:** Uses standard HTTPS requests to `router.huggingface.co` to bypass SDK versioning conflicts.
