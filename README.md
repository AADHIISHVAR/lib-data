# Librarian AI - Windows Local Enrichment

This folder contains a modified version of the enrichment pipeline designed to run on a local Windows machine using a local Llama instance (via Ollama or LM Studio) to leverage your NVIDIA RTX 3050 (6GB VRAM).

## Prerequisites

1.  **Python 3.10+**: Install Python on Windows.
2.  **Local AI Server**: 
    *   **Option A (Ollama - Recommended)**: Install Ollama and run `ollama run llama3.1:8b-instruct-q4_K_M`.
    *   **Option B (LM Studio)**: Download LM Studio, load a Llama 3.1 8B model (GGUF), and start the local server.
3.  **Database**: Place your `uniqueBooks.db` inside this folder.

## Setup

1.  Open PowerShell/CMD in this folder.
2.  Create a virtual environment:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  Install dependencies:
    ```powershell
    pip install -r requirements.txt
    ```

## Running

1.  Ensure your local AI server is running.
2.  Run the enricher:
    ```powershell
    python local_enrich.py
    ```

## Customization

You can change the AI server URL or Model by setting environment variables or editing `fetchers/local_llama.py`:

*   `LOCAL_AI_URL`: Default is `http://localhost:11434/v1/chat/completions` (Ollama).
*   `LOCAL_AI_MODEL`: Default is `llama3.1:8b-instruct-q4_K_M`.

## Why Local?
- **Unlimited Usage**: No Hugging Face API limits.
- **Privacy**: Data stays on your machine.
- **GPU Speed**: Your RTX 3050 is significantly faster than CPU-only inference.
