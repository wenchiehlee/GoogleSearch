# Gemini Context: FactSet Pipeline

This `GEMINI.md` provides context for the FactSet Pipeline project, a two-stage system for automating the collection and analysis of FactSet financial data for Taiwan stock market companies.

## 📂 Project Overview

**FactSet Pipeline** is a Python-based system designed to scrape, validate, analyze, and report on financial data for Taiwan stocks. It operates in stages:
0.  **Watchlist Update:** Automatically downloads the latest stock lists (`StockID_TWSE_TPEX.csv` and `StockID_TWSE_TPEX_focus.csv`) daily.
1.  **Search Group (v3.5.1):** Fetches data using Google Search API (with key rotation), validates content, and saves it as Markdown.
2.  **Process Group (v3.6.1):** Analyzes the Markdown files, scores quality, analyzes query patterns, tracks watchlist coverage, and generates reports (CSV & Google Sheets).

### Key Directories & Files
*   **`search_group/`**: Contains logic for data collection.
    *   `search_cli.py`: CLI entry point for searching.
    *   `search_engine.py`: Core logic for searching and content validation.
    *   `api_manager.py`: Manages Google API key rotation.
*   **`process_group/`**: Contains logic for data analysis and reporting.
    *   `process_cli.py`: CLI entry point for processing.
    *   `md_parser.py`, `quality_analyzer.py`, `report_generator.py`: Core processing modules.
*   **`data/`**: Data storage.
    *   `md/`: Stores scraped and validated Markdown files (Output of Search, Input of Process).
    *   `reports/`: Stores generated CSV reports.
*   **`StockID_TWSE_TPEX.csv`**: Input watchlist of companies (Format: `代號,名稱`).
*   **`.env`**: Configuration file for API keys and settings.

## 🚀 Usage

### 1. Environment Setup
Ensure a `.env` file exists in the root with necessary API keys:
```env
GOOGLE_SEARCH_API_KEY=...
GOOGLE_SEARCH_CSE_ID=...
GOOGLE_SHEET_ID=...
# ... other keys
```

### 2. Search Group (Data Collection)
Navigate to `search_group/` to run search commands.
```bash
cd search_group

# Validate API keys
python search_cli.py validate

# Search all companies (managed quota)
python search_cli.py search --all --count 2 --min-quality 4

# Search a specific company
python search_cli.py search --company 2330 --count 3
```

### 3. Process Group (Analysis & Reporting)
Navigate to `process_group/` to run processing commands.
```bash
cd process_group

# Process all files and generate reports
python process_cli.py process

# Analyze recent files only (e.g., last 24 hours)
python process_cli.py process-recent --hours=24

# Generate specific summaries without uploading to Sheets
python process_cli.py keyword-summary --no-upload
python process_cli.py watchlist-summary --no-upload
```

## 🛠️ Development Conventions

*   **Architecture:** Modular design splitting "Search" (IO-bound, external APIs) and "Process" (CPU-bound, local analysis).
*   **Communication:** File-based via `data/md/` using deterministic filenames (Content Hash).
*   **Error Handling:** "Graceful degradation" in `process_cli.py` allows partial functionality if modules fail to load.
*   **Versioning:** Explicit version tracking in CLI headers and logic (e.g., `v3.5.1`, `v3.6.1`).
*   **Data Validation:** Strong emphasis on "Quality Scoring" (0-10 scale) to filter irrelevant or poor-quality data.

## 📝 File Formats

*   **Input CSV (`StockID_TWSE_TPEX.csv` & `StockID_TWSE_TPEX_focus.csv`):**
    ```csv
    代號,名稱
    2301,光寶科
    ...
    ```
*   **Markdown Metadata (YAML Frontmatter):**
    Files in `data/md/` contain metadata headers like `search_query`, `quality_score`, `company`, etc., used by the Process Group.
