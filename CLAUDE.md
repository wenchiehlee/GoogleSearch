# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FactSet Pipeline v3.6.1** is a production two-stage system that automates collection and analysis of FactSet financial data for Taiwan stock market companies. The system operates through file-based communication between two independent groups.

### Architecture

```
Stage 0: Watchlist Update (Daily 18:00 UTC)
├─ Get觀察名單.py → Updates stock lists

Stage 1: Search Group (v3.6.0) → Stage 2: Process Group (v3.6.1)
├─ Searches with API key rotation    ├─ Analyzes MD files
├─ Validates content                  ├─ Scores quality
├─ Generates MD files                 ├─ Generates reports
└─ Output: data/md/*.md              └─ Output: CSV + Google Sheets
```

**Communication Pattern**: File-based via `data/md/` directory. No direct API calls between stages.

## Common Commands

### Search Group (Data Collection)

**Note**: All commands run from project root

```bash
# Validate API keys and setup
python search_group/search_cli.py validate

# Search specific company
python search_group/search_cli.py search --company 2330 --count 3 --min-quality 4

# Search all companies (uses API key rotation)
python search_group/search_cli.py search --all --count 2 --min-quality 4

# Resume interrupted searches
python search_group/search_cli.py search --resume --min-quality 4

# Check status (API key rotation, quota, cache)
python search_group/search_cli.py status
```

### Process Group (Analysis & Reporting)

**Note**: All commands run from project root

```bash
# Validate components
python process_group/process_cli.py validate

# Full processing with all analysis + upload to Google Sheets
python process_group/process_cli.py process

# Process recent files only (incremental updates)
python process_group/process_cli.py process-recent --hours=24

# Process single company
python process_group/process_cli.py process-single --company 2330

# Generate specific reports (without upload)
python process_group/process_cli.py keyword-summary --no-upload
python process_group/process_cli.py watchlist-summary --no-upload

# Analysis only
python process_group/process_cli.py analyze-quality
python process_group/process_cli.py analyze-keywords
python process_group/process_cli.py analyze-watchlist
```

### Watchlist Update

```bash
# Update stock lists from GitHub source
python Get觀察名單.py
```

## Key Architectural Patterns

### 1. Two-Stage Separation

**Search Group** and **Process Group** are completely independent:
- Search Group: I/O-bound, external API-dependent, handles quota/rotation
- Process Group: CPU-bound, local file analysis, no external dependencies
- Communication: Deterministic filenames in `data/md/` based on content hash

### 2. Content Hash Filenames

Files use pure content-based naming for perfect deduplication:
```
2330_台積電_factset_7796efd2.md
```
Format: `{stock_code}_{company_name}_{source}_{content_hash}.md`

Same content = same hash = automatic deduplication

### 3. API Key Rotation (Search Group)

Supports up to 7 Google API keys for quota management:
- Primary: `GOOGLE_SEARCH_API_KEY`
- Additional: `GOOGLE_SEARCH_API_KEY1` through `GOOGLE_SEARCH_API_KEY6`
- Automatic failover on 429 (quota exceeded)
- ~700 searches/day capacity with 7 keys

### 4. Multi-Layer Content Validation (Search Group v3.6.0)

Prevents false positives where search results mention the company in sidebar/ads but the article is about a different company. Uses 4-layer validation:

**Layer 1: Title Validation** (Highest Priority)
- Extracts company code from HTML `<title>` and `og:title` meta tags
- **Immediately rejects** if title mentions different company code
- Example: Search for "2454 聯發科" but title shows "欣興(3037-TW)" → rejected
- Confidence: 0 (rejected) or continues to next layer

**Layer 2: Combined Pattern Matching**
- Looks for symbol and name appearing together in common patterns:
  - `聯發科(2454-TW)` or `(2454-TW) 聯發科`
  - `2454-TW 聯發科` within 20 characters
  - `代號: 2454 聯發科`
- Strong signal that content is genuinely about the company
- Confidence: 1.2 (high)

**Layer 3: Proximity Check**
- Verifies symbol "2454" and name "聯發科" appear within 200 characters
- Prevents false matches from sidebar/recommended articles
- Confidence: 0.8-1.0 (based on distance, closer = higher)

**Layer 4: Context-Aware Fallback**
- Original validation logic with stricter thresholds
- Checks symbol in proper stock code contexts (e.g., "2330-TW", not "2330元")
- Detects false positives where symbol appears as price (e.g., "目標價2330元")
- Confidence: Reduced weights (0.5 for symbol, 0.3 for name)
- Threshold: 0.7 (stricter than previous 0.8)

**Benefits:**
- Eliminates false positives from cross-company page references
- Scan of 115 files found 5 false positives, all would be caught by Layer 1
- Provides validation_layer field in response for debugging

### 5. Quality Scoring System

Standardized 0-10 scale used throughout:
- **9-10** (🟢 完整): EPS 90%+, 20+ analysts, ≤7 days
- **8** (🟡 良好): EPS 70%+, 10+ analysts, ≤30 days
- **3-7** (🟠 部分): EPS 30%+, 5+ analysts, ≤90 days
- **0-2** (🔴 不足): Limited/missing data

### 6. Graceful Degradation (Process Group)

Process CLI uses "graceful degradation" - if optional modules fail to load, core functionality continues. Critical modules (md_scanner, md_parser) must load successfully.

## File Structure & Key Components

```
GoogleSearch/
├── search_group/              # Stage 1: Data Collection
│   ├── search_cli.py         # CLI with rotation support (~700 lines)
│   ├── search_engine.py      # Core search + content validation (~600 lines)
│   ├── api_manager.py        # Multi-key rotation manager (~800 lines)
│   └── instructions.md       # Detailed search implementation guide
│
├── process_group/            # Stage 2: Analysis & Reporting
│   ├── process_cli.py        # Processing CLI (~800 lines)
│   ├── md_scanner.py         # File system interface (~400 lines)
│   ├── md_parser.py          # MD + metadata parsing (~900 lines)
│   ├── quality_analyzer.py   # Quality scoring (~400 lines)
│   ├── keyword_analyzer.py   # Query pattern analysis (~600 lines)
│   ├── watchlist_analyzer.py # Watchlist coverage (~800 lines)
│   ├── report_generator.py   # Multi-format reports (~600 lines)
│   ├── sheets_uploader.py    # Google Sheets integration (~900 lines)
│   └── instructions.md       # Detailed process implementation guide
│
├── data/
│   ├── md/                   # MD files (Search → Process communication)
│   ├── reports/              # Generated CSV reports
│   └── quarantine/           # Files with validation issues
│
├── .github/workflows/
│   ├── Actions-update-lists.yaml  # Daily watchlist update (18:00 UTC)
│   ├── Actions-search.yaml        # Daily search execution (18:30 UTC)
│   └── Actions-process.yaml       # Daily processing
│
├── StockID_TWSE_TPEX.csv         # Main watchlist (116+ companies)
├── StockID_TWSE_TPEX_focus.csv   # Focus watchlist subset
├── Get觀察名單.py                # Watchlist updater
└── .env                           # Configuration (not in git)
```

## Environment Configuration

Create `.env` file in project root:

```bash
# Search Group - Multiple API keys for rotation (up to 7)
GOOGLE_SEARCH_API_KEY=primary_key_here
GOOGLE_SEARCH_CSE_ID=custom_search_engine_id_here
GOOGLE_SEARCH_API_KEY1=second_key_here
GOOGLE_SEARCH_API_KEY2=third_key_here
# ... up to GOOGLE_SEARCH_API_KEY6

# Process Group - Google Sheets integration
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}

# Performance tuning
SEARCH_RATE_LIMIT_PER_SECOND=1.0
MIN_QUALITY_THRESHOLD=4
LOG_LEVEL=INFO
```

## MD File Metadata Format

Search Group outputs MD files with YAML frontmatter:

```yaml
---
search_query: 台積電 2330 factset EPS 預估
quality_score: 8
company: 台積電
stock_code: 2330
content_validation: {"is_valid": true, "reason": "...", "validation_layer": "combined_pattern"}
version: v3.6.0
---
[Content continues...]
```

Process Group reads these metadata fields for analysis.

## REFINED_SEARCH_PATTERNS Integration

Process Group analyzes search effectiveness by normalizing queries to `{name} {symbol}` format and categorizing into:
- `factset_direct`: FactSet-specific patterns (highest success)
- `cnyes_factset`: cnyes.com FactSet searches (#1 Taiwan source)
- `eps_forecast`: Direct EPS forecast patterns
- `analyst_consensus`: Analyst/consensus patterns
- `taiwan_financial_simple`: Taiwan financial site searches

## Report Types (Process Group)

1. **Portfolio Summary** (14 columns): Investment overview
2. **Detailed Report** (22 columns): Complete data + GitHub Raw URLs
3. **Query Pattern Summary** (10 columns): Search effectiveness analysis
4. **Watchlist Summary** (12 columns): Company coverage status

All reports generated in `data/reports/` as CSV and uploaded to Google Sheets.

## Version Tracking

Current versions:
- Search Group: v3.6.0 (Multi-Layer Validation + API key rotation)
- Process Group: v3.6.1 (watchlist analysis + query patterns)
- Overall Pipeline: v3.6.1

Components are backward compatible within major version.

## Workflow Execution Patterns

### Complete Pipeline Run
```bash
# 1. Update watchlists
python Get觀察名單.py

# 2. Search (data collection)
python search_group/search_cli.py search --all --count 2 --min-quality 4

# 3. Process (analysis)
python process_group/process_cli.py process

# 4. Verify
ls data/md/*.md | wc -l
ls data/reports/*.csv
```

### Testing Individual Components
```bash
# Test Search Group only
python search_group/search_cli.py search --company 2330 --count 1

# Test Process Group only
python process_group/process_cli.py process-single --company 2330 --no-upload
```

### Incremental Updates
```bash
# Search new companies only (resume)
python search_group/search_cli.py search --resume

# Process recent files only (last 24 hours)
python process_group/process_cli.py process-recent --hours=24
```

## Troubleshooting

### "All API keys exhausted"
Add more API keys (GOOGLE_SEARCH_API_KEY1-6) to `.env`

### "觀察名單未載入"
Ensure `StockID_TWSE_TPEX.csv` exists in project root with format: `代號,名稱`

### "No MD files found"
Run Search Group first to generate MD files in `data/md/`

### Google Sheets upload fails
Check `GOOGLE_SHEETS_CREDENTIALS` JSON format in `.env`

### Content validation issues
Check Search Group logs for validation details. Invalid content gets quality_score=0.

## GitHub Actions Automation

Three daily workflows:
1. **Update Lists** (18:00 UTC): Downloads latest stock lists
2. **Search** (18:30 UTC): Executes searches with quota management
3. **Process** (after Search): Analyzes and uploads reports

Workflows split work into parallel batches for efficiency.

## Important Notes

- All commands run from project root (e.g., `python search_group/search_cli.py ...`)
- All generated data (MD files, reports) stored in `data/` directory (project root)
- Search Group quota is ~100 searches per API key per day
- MD files use UTF-8 encoding with BOM for Chinese characters
- Quality threshold of 4+ is recommended for production
- Content hash ensures perfect deduplication - same content = same filename
- Process Group can handle 1000+ MD files efficiently (<200MB memory)
- All dates in reports use Taiwan timezone (UTC+8)
