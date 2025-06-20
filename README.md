# GoogleSearch
Working space for GoogleSearch

## Version Information
- **Current Version**: v2.0.8
- **Last Updated**: 2025-06-19
- **Author**: Generated by ChatGPT based on instructions
- **License**: MIT

## Version History
| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | Initial | Basic Google search with single query support |
| v1.1.0 | - | Added PDF download functionality |
| v1.2.0 | - | Added Markitdown conversion support |
| v2.0.0 | 2025-06-19 | Multi-query support, enhanced error handling, improved structure |
| v2.0.1 | 2025-06-19 | Added FactSet search with 觀察名單 filtering, enhanced file detection |
| v2.0.2 | 2025-06-19 | Fixed FactSet search to process all content types, not skip non-PDFs |
| v2.0.3 | 2025-06-19 | Added web page download and conversion to PDF/MD for FactSet matches |
| v2.0.4 | 2025-06-19 | Added content parsing for FactSet data extraction into structured CSV columns |
| v2.0.5 | 2025-06-19 | Updated FactSet data extraction with Traditional Chinese column headers, fixed company name extraction regex |
| v2.0.6 | 2025-06-19 | Added configurable search parameters and individual search enable/disable options for better control |
| v2.0.7 | 2025-06-19 | Added release date extraction (日期) for FactSet content with multiple date format support |
| v2.0.8 | 2025-06-19 | Adjusted FactSet search parameters (360 days, Traditional Chinese) for better results coverage |

## Overview
This project implements a Google Custom Search solution that searches for specific documents, downloads them, and converts them to Markdown format using the Markitdown project. Version 2.0.8 adjusts FactSet search parameters for better results coverage while maintaining release date extraction, configurable search parameters, individual search enable/disable options, and comprehensive FactSet financial data extraction with Traditional Chinese column headers for enhanced usability.

## Features
- **Google Custom Search Integration**: Uses Google Custom Search JSON API to find documents
- **Intelligent Watch List Filtering**: Filters FactSet search results against 觀察名單 (watch list)
- **FactSet Data Extraction**: Automatically parses FactSet content to extract structured financial data (EPS estimates, target prices, revenue forecasts)
- **Traditional Chinese Headers**: User-friendly Traditional Chinese column headers for all extracted financial data
- **Improved Company Name Extraction**: Fixed regex patterns to properly extract company names without punctuation prefixes
- **Configurable Search Parameters**: Remove date/language/country restrictions for better search results
- **Individual Search Control**: Easy enable/disable configuration for each search type
- **Web Page Download & Conversion**: Downloads web pages and converts them to both PDF and Markdown formats
- **Flexible Content Type Handling**: Processes PDFs and web pages appropriately based on search type
- **Automated PDF Download**: Downloads PDF files from search results to a designated folder
- **PDF to Markdown Conversion**: Converts downloaded PDFs to Markdown format using Microsoft's Markitdown tool
- **CSV Results Tracking**: Maintains comprehensive CSV files with search results and file paths
- **Multi-query Support**: Supports multiple search queries with different filtering strategies
- **Enhanced File Detection**: Improved content-type checking for accurate PDF identification

## Current Search Queries
1. **Financial Documents**: `"得標統計表 T004 -公司債 filetype:pdf"` - Searches for bond-related financial statistics documents
2. **FactSet Documents**: `"FactSet"` - Searches for FactSet-related content that matches 觀察名單
   - **Watch List Source**: https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv
   - **Filtering Logic**: Results are filtered to include only items that mention companies/symbols from the watch list
   - **Data Extraction**: Automatically parses FactSet content to extract structured financial data
   - **Search Parameters**: Balanced restrictions (360 days, Traditional Chinese, worldwide) for optimal results coverage

## Quick Configuration
Edit these settings at the top of `main()` function in `GoogleSearch.py`:
```python
# ============================================================================
# QUICK CONFIGURATION - Edit these settings to enable/disable searches
# ============================================================================
ENABLE_FINANCIAL_SEARCH = False    # Set to True to enable 得標統計表 search
ENABLE_FACTSET_SEARCH = True       # Set to False to disable FactSet search
# ============================================================================
```

## File Structure
```
GoogleSearch/
├── .github/
│   └── workflows/
│       └── Actions.yaml        # GitHub Actions workflow configuration
├── README.md                   # This documentation file
├── GoogleSearch.py             # Main search and processing script (v2.0.8)
├── requirements.txt            # Python dependencies list
├── .env                        # Environment variables (local development)
├── GoogleResults.csv           # Results for financial documents search
├── FactSetResults.csv          # Results for FactSet search with parsed financial data
├── PDF/                        # Downloaded PDF files and web pages
└── MD/                         # Converted Markdown files
```

## GoogleSearch.py Script Details

### Script Information
- **File**: `GoogleSearch.py`
- **Current Version**: v2.0.8 (2025-06-19)
- **Architecture**: Object-oriented with modular functions
- **Version Control**: Built-in version tracking with `__version__`, `__date__`, and `__author__` variables

### Script Features
- **Version Display**: Shows version information on startup
- **Modular Design**: Separate functions for search, download, conversion, and filtering processes
- **Watch List Integration**: Downloads and parses 觀察名單 CSV for intelligent filtering
- **FactSet Data Parsing**: Extracts structured financial data (EPS estimates, target prices, revenue forecasts) and release dates from FactSet content
- **Traditional Chinese Headers**: Uses user-friendly Chinese column names for extracted data
- **Improved Regex Patterns**: Fixed company name extraction to handle punctuation correctly (e.g., "玉晶光" instead of "：玉晶光")
- **Configurable Search Parameters**: Remove date/language/country restrictions per search query
- **Individual Search Control**: Easy enable/disable toggles for each search type
- **Web Page Processing**: Downloads and converts web pages to PDF and Markdown formats
- **Flexible Content Handling**: Configurable processing for PDF-only vs all content types
- **Error Handling**: Comprehensive error checking and graceful failure handling
- **Progress Tracking**: Real-time progress updates during batch processing
- **Multi-Query Support**: Handles multiple search queries with different filtering strategies
- **Enhanced File Detection**: Content-type validation for accurate PDF identification
- **Fallback Mechanisms**: Graceful degradation when optional tools unavailable

### Key Functions
- `google_search()`: Performs Google Custom Search API calls with configurable parameters
- `download_watch_list()`: Downloads and parses 觀察名單 CSV from GitHub
- `filter_results_by_watch_list()`: Filters search results against watch list items
- `parse_factset_content()`: Extracts structured financial data from FactSet content with Traditional Chinese headers
- `save_results_to_csv()`: Saves search results to CSV format with optional FactSet parsing columns
- `download_files_from_links_and_convert()`: Downloads files and converts PDFs to Markdown (supports pdf_only parameter and FactSet parsing)
- `download_web_page_as_pdf_and_md()`: Downloads web pages and converts them to both PDF and Markdown formats
- `process_search_query()`: Complete processing pipeline for a single query with optional filtering and configurable search parameters
- `is_markitdown_valid()`: Validates Markitdown tool availability
- `main()`: Main execution function with version display and search enable/disable configuration

## FactSet Data Extraction

### Overview
Version 2.0.4 introduced automated parsing of FactSet content to extract structured financial data. Version 2.0.5 enhanced this with Traditional Chinese column headers and improved company name extraction. Version 2.0.6 adds configurable search parameters for better results coverage.

### FactSetResults.csv Column Structure

#### Standard Columns
- **Title**: Document title from search results
- **Link**: Direct link to the FactSet content (web page)
- **Snippet**: Brief description/snippet from search results
- **File**: Local file path of downloaded content (in PDF/ folder as .txt file)
- **MD File**: Local file path of converted Markdown file (in MD/ folder)

#### Extracted Financial Data Columns (Traditional Chinese Headers)

##### Company Information
- **公司名稱** (Company Name): Company name extracted from content (e.g., "廣達", "玉晶光", "小鵬汽車")
- **股票代號** (Stock Symbol): Stock ticker symbol (e.g., "2382-TW", "3406-TW", "XPEV-US")
- **日期** (Release Date): Release date of this web page (e.g., "2025-06-18", "2025-06-19")
- **分析師數量** (Analyst Count): Number of analysts providing estimates (e.g., "35", "45")

##### Current Estimates
- **當前EPS預估** (Current EPS Estimate): Current EPS forecast in local currency (e.g., "21.39")
- **先前EPS預估** (Previous EPS Estimate): Previous EPS forecast for comparison (e.g., "20.49")
- **目標價** (Target Price): Analyst target price for the stock (e.g., "400", "135")

##### EPS Forecasts by Year (2025-2027)
- **2025EPS最高值** (2025 EPS High): Highest EPS estimate for 2025
- **2025EPS最低值** (2025 EPS Low): Lowest EPS estimate for 2025
- **2025EPS平均值** (2025 EPS Average): Average EPS estimate for 2025
- **2025EPS中位數** (2025 EPS Median): Median EPS estimate for 2025
- **2026EPS最高值/最低值/平均值/中位數**: Same structure for 2026
- **2027EPS最高值/最低值/平均值/中位數**: Same structure for 2027

##### Revenue Forecasts by Year (2025-2027)
- **2025營收最高值** (2025 Revenue High): Highest revenue estimate for 2025 (in millions)
- **2025營收最低值** (2025 Revenue Low): Lowest revenue estimate for 2025
- **2025營收平均值** (2025 Revenue Average): Average revenue estimate for 2025
- **2025營收中位數** (2025 Revenue Median): Median revenue estimate for 2025
- **2026營收最高值/最低值/平均值/中位數**: Same structure for 2026
- **2027營收最高值/最低值/平均值/中位數**: Same structure for 2027

### Example Data Row
```csv
Title,Link,Snippet,File,MD File,公司名稱,股票代號,日期,分析師數量,當前EPS預估,先前EPS預估,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2025EPS中位數,...
"鉅亨速報 - Factset 最新調查：玉晶光(3406-TW)目標價調降至400元","https://tw.stock.yahoo.com/news/...","FactSet 最新調查：玉晶光(3406-TW)目標價調降，最高估值、最低估值、中位數、綜合評級...","PDF/webpage1.txt","MD/webpage1.md","玉晶光","3406-TW","2025-06-18","12","21.39","20.49","400","22.5","19.8","21.1","21.39",...
```

### Extraction Process
1. **Content Analysis**: Analyzes Markdown content from downloaded FactSet web pages
2. **Pattern Matching**: Uses improved regex patterns to extract company names and financial data
3. **Company Identification**: Extracts company names and stock symbols with multiple fallback strategies
4. **Date Extraction**: Extracts release dates from content using multiple date format patterns (Chinese and Western formats)
5. **Financial Data Extraction**: Extracts EPS estimates, target prices, and revenue forecasts from structured content
6. **Data Validation**: Validates extracted data for consistency and accuracy
7. **CSV Integration**: Automatically populates Traditional Chinese column headers with extracted financial data
8. **Error Handling**: Graceful handling of extraction failures with detailed logging

### Improved Company Name Extraction (v2.0.5)
Multiple regex patterns to handle different content formats:
- **Pattern 1**: `對廣達([2382-TW])` format
- **Pattern 2**: `：玉晶光(3406-TW)` format (now extracts "玉晶光" correctly, not "：玉晶光")
- **Pattern 3**: General company name before stock code
- **Pattern 4**: Markdown link format extraction

### Release Date Extraction (v2.0.7)
Supports multiple date formats commonly found in financial content:
- **Chinese Format**: `2025年6月18日` → `2025-06-18`
- **ISO Format**: `2025-06-18` → `2025-06-18`
- **Slash Format**: `2025/06/18` or `06/18/2025` → `2025-06-18`
- **Dot Format**: `2025.06.18` → `2025-06-18`
- **Context-based**: Searches for dates near keywords like "發布", "更新", "時間", "日期"
- **Article timestamps**: Extracts publication dates from article metadata

## Requirements

### Prerequisites
1. **Google Custom Search API**:
   - Valid Google API key (`GOOGLE_SEARCH_API_KEY`)
   - Custom Search Engine ID (`GOOGLE_SEARCH_CSE_ID`)

2. **Markitdown Installation**:
   - Microsoft Markitdown tool must be installed and accessible in system PATH
   - Install via: `pip install markitdown`

3. **wkhtmltopdf Installation (Optional)**:
   - Required for web page to PDF conversion
   - Install on Ubuntu/Debian: `sudo apt-get install wkhtmltopdf`
   - Install on macOS: `brew install wkhtmltopdf`
   - Install on Windows: Download from https://wkhtmltopdf.org/downloads.html
   - Note: If not available, web pages will be saved as text files instead

4. **Python Dependencies**:
   - `requests`
   - `python-dotenv`
   - `csv` (built-in)
   - `os` (built-in)
   - `subprocess` (built-in)
   - `re` (built-in)

5. **Dependencies File**:
   - `requirements.txt` containing all necessary Python packages
   - Install via: `pip install -r requirements.txt`

### Requirements.txt Contents
The `requirements.txt` file should contain:
```txt
requests>=2.31.0
python-dotenv>=1.0.0
markitdown>=0.0.1a2
```

**Optional System Dependencies**:
- `wkhtmltopdf` for web page to PDF conversion
- Install separately based on your operating system

### Environment Setup

#### Local Development
Create a `.env` file in the project root with:
```
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_CSE_ID=your_custom_search_engine_id_here
```

#### GitHub Actions (Automated Execution)
Set up the following repository secrets in GitHub:
- `GOOGLE_SEARCH_API_KEY`: Your Google API key
- `GOOGLE_SEARCH_CSE_ID`: Your Custom Search Engine ID

## GitHub Actions Automation

### Workflow Configuration
The project includes `.github/workflows/Actions.yaml` for automated execution via GitHub Actions:

**File Location**: `GoogleSearch/.github/workflows/Actions.yaml`

```yaml
name: Google Search On GitHub Action
on:
  push:
    branches:
      - main
  workflow_dispatch:
  schedule:
    - cron: "10 2 * * *"     # Runs every day at 2:10 AM UTC
```

### Automation Features
- **🔄 Automatic Triggers**:
  - Runs on every push to the `main` branch
  - Daily scheduled execution at 2:10 AM UTC
  - Manual trigger via GitHub workflow dispatch

- **🏗️ Environment Setup**:
  - Ubuntu latest runner
  - Python 3.10 installation
  - System dependencies: wkhtmltopdf for web page to PDF conversion
  - Automatic dependency installation from `requirements.txt`
  - Markitdown tool installation

- **🔐 Secure Credential Management**:
  - Uses GitHub repository secrets for API keys
  - No hardcoded credentials in the workflow

- **📋 Automated Workflow Steps**:
  1. **Repository Checkout**: Fetches latest code
  2. **Python Setup**: Configures Python 3.10 environment
  3. **Package Installation**: Installs all dependencies
  4. **Script Execution**: Runs GoogleSearch.py with environment variables
  5. **Results Commit**: Automatically commits and pushes generated files

- **📁 Automated File Management**:
  - Commits all CSV result files (`*.csv`) with FactSet parsed data in Traditional Chinese
  - Commits all downloaded PDF files (`PDF/*.pdf`)
  - Commits all downloaded text files (`PDF/*.txt`) - fallback for web pages
  - Commits all converted Markdown files (`MD/*.md`)
  - Uses `github-actions[bot]` for automated commits
  - Handles missing directories gracefully

### GitHub Actions Benefits
- **🕒 Scheduled Execution**: Daily automated searches ensure up-to-date financial data
- **🔄 Continuous Integration**: Automatically processes new searches on code changes
- **📊 Result Tracking**: All results and parsed financial data are automatically committed to the repository
- **🚀 Zero-Maintenance**: Runs without manual intervention
- **📈 Audit Trail**: Complete history of automated executions in GitHub Actions logs

## Web Page Processing

### Overview
Version 2.0.3 introduces comprehensive web page download and conversion capabilities for FactSet searches. Version 2.0.4+ adds financial data extraction from the downloaded content. Version 2.0.6 improves search coverage with configurable parameters. When a FactSet search result matches a company from the 觀察名單, the system downloads the complete web page content, converts it to both PDF and Markdown formats, and extracts structured financial data.

### Processing Methods

#### Markdown Conversion
1. **Direct URL Processing**: Attempts to use Markitdown directly with the URL
2. **HTML Download Fallback**: Downloads HTML content and processes it through Markitdown
3. **Text Fallback**: If conversion fails, saves raw HTML content as structured text

#### PDF Conversion
1. **wkhtmltopdf**: Primary method using wkhtmltopdf tool for high-quality PDF generation
2. **Text Fallback**: If PDF conversion unavailable, creates a text file placeholder

#### FactSet Data Extraction
1. **Content Parsing**: Analyzes Markdown content for FactSet financial data
2. **Company Identification**: Extracts company names and stock symbols with improved regex patterns
3. **Financial Data Extraction**: Extracts EPS estimates, target prices, and revenue forecasts
4. **CSV Population**: Automatically populates Traditional Chinese column headers with extracted data

### File Naming Convention
- **Web page PDFs**: `webpage1.pdf`, `webpage2.pdf`, etc.
- **Web page Markdown**: `webpage1.md`, `webpage2.md`, etc.
- **Text fallbacks**: `webpage1.txt`, `webpage2.txt`, etc.

### Supported Content Types
- **FactSet news articles** (with financial data extraction)
- **Financial reports and analysis**
- **Company announcements**
- **Any web-based content mentioning 觀察名單 companies**

## Watch List Integration (觀察名單)

### Overview
Version 2.0.1 introduces intelligent filtering for FactSet searches using a dynamically downloaded watch list (觀察名單) from GitHub.

### Watch List Source
- **URL**: https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv
- **Format**: CSV file containing company names and symbols
- **Update**: Downloaded fresh for each execution

### Filtering Process
1. **Download**: Watch list CSV is downloaded from GitHub repository
2. **Parse**: CSV content is parsed to extract company names/symbols
3. **Filter**: Search results are filtered to include only items mentioning watch list companies
4. **Match**: Matching occurs across title, snippet, and link content

### Filtering Logic
```python
# Example filtering process
for result in search_results:
    title = result.get('title', '').lower()
    snippet = result.get('snippet', '').lower()
    link = result.get('link', '').lower()
    
    for watch_item in watch_list:
        if watch_item.lower() in (title or snippet or link):
            filtered_results.append(result)
            break
```

## Search Configuration (v2.0.6)

### Configurable Search Parameters
Each search can now have custom parameters:

#### FactSet Search (Balanced for Results)
```python
"search_params": {
    "last_days": 360,           # Last 360 days (ensures recent content)
    "language": "lang_zh-TW",   # Traditional Chinese content
    "country": None             # No country restriction (worldwide results)
}
```

#### Financial Documents Search (Focused Results)
```python
"search_params": {
    "last_days": 360,           # Last 360 days only
    "language": "lang_zh-TW",   # Traditional Chinese content
    "country": "countryTW"      # Taiwan-focused results
}
```

### Enable/Disable Configuration
Quick toggles at the top of `main()` function:

#### Configuration Options
1. **FactSet Only** (Default):
   ```python
   ENABLE_FINANCIAL_SEARCH = False
   ENABLE_FACTSET_SEARCH = True
   ```

2. **Financial Documents Only**:
   ```python
   ENABLE_FINANCIAL_SEARCH = True
   ENABLE_FACTSET_SEARCH = False
   ```

3. **Both Searches**:
   ```python
   ENABLE_FINANCIAL_SEARCH = True
   ENABLE_FACTSET_SEARCH = True
   ```

4. **Disable All** (for testing):
   ```python
   ENABLE_FINANCIAL_SEARCH = False
   ENABLE_FACTSET_SEARCH = False
   # Will show error and exit
   ```

## Process Flow

### Financial Documents Search (得標統計表 T004)
1. **Search Execution**: Performs Google Custom Search for PDF documents with restrictions
2. **Results Collection**: Gathers up to 500 search results with date restrictions (360 days)
3. **CSV Generation**: Creates initial CSV file with search results metadata
4. **PDF Download**: Downloads PDF files from valid links to PDF/ folder
5. **Markdown Conversion**: Converts each PDF to Markdown using Markitdown tool
6. **CSV Update**: Updates CSV file with local file paths

### FactSet Documents Search (Enhanced with Data Extraction)
1. **Watch List Download**: Downloads 觀察名單 CSV from GitHub repository
2. **Search Execution**: Performs Google Custom Search for FactSet content (all types, no restrictions)
3. **Results Filtering**: Filters results against watch list companies/symbols
4. **CSV Generation**: Creates CSV file with filtered search results metadata and Traditional Chinese parsing columns
5. **Content Download & Conversion**: 
   - **PDF files**: Downloads and converts to Markdown using Markitdown
   - **Web pages**: Downloads HTML content and converts to both PDF (via wkhtmltopdf) and Markdown (via Markitdown)
   - **Fallback**: If PDF conversion fails, saves as text file
6. **FactSet Data Extraction**: Parses Markdown content to extract structured financial data with improved regex patterns
7. **CSV Update**: Updates CSV file with local file paths AND extracted financial data in Traditional Chinese columns

## Search Parameters by Version

### v2.0.8 (Current) - Balanced Parameters for Results
- **FactSet Search**: Balanced restrictions (360 days + Traditional Chinese, worldwide) → **Better Results**
- **Financial Search**: Restricted (Taiwan, Chinese, 360 days) → **Focused Results**
- **Individual Control**: Easy enable/disable for each search

### v2.0.6-2.0.7 - Configurable Parameters
- **FactSet Search**: No restrictions (worldwide, all languages, all dates) → **Sometimes No Results**
- **Financial Search**: Restricted (Taiwan, Chinese, 360 days) → **Focused Results**
- **Individual Control**: Easy enable/disable for each search

### Previous Versions (v2.0.1-2.0.5)
- **Both Searches**: Restricted to Taiwan, Chinese, 360 days → **Limited Results**

## Enhanced Error Handling
- **Watch List Failures**: Graceful fallback when watch list cannot be downloaded
- **File Type Validation**: Content-type checking for accurate PDF identification
- **Content Type Flexibility**: Appropriate handling of both PDF and non-PDF content based on search type
- **FactSet Parsing Failures**: Individual parsing failures don't stop batch processing
- **Company Name Extraction**: Multiple regex patterns with fallback strategies for improved accuracy
- **Search Parameter Validation**: Handles None values and missing parameters gracefully
- **Markitdown Availability**: Continues processing without conversion if Markitdown unavailable
- **HTTP Errors**: Comprehensive error handling during file downloads
- **PDF Conversion Failures**: Individual file failures don't stop batch processing
- **Progress Tracking**: Real-time status updates during batch processing

## Usage

### Manual Execution (Local Development)
Run the script directly on your local machine:
```bash
python GoogleSearch.py
```

### Automated Execution (GitHub Actions)
The script runs automatically via GitHub Actions in the following scenarios:

1. **📅 Daily Schedule**: Every day at 2:10 AM UTC
2. **🔄 Code Push**: Automatically when changes are pushed to the `main` branch  
3. **▶️ Manual Trigger**: Use GitHub's "Run workflow" button in the Actions tab

### Expected Output (v2.0.8)
```
GoogleSearch.py v2.0.8 - Multi-Query PDF Search and Conversion Tool
Date: 2025-06-19 | Author: Generated by ChatGPT
Platform: Windows
================================================================================

Tool Availability Check:
- Markitdown: ✓ Available
- wkhtmltopdf: ✗ Not Available

🎯 Running 1 of 2 configured searches:
   ✅ FactSet Documents Search
   ⏸️  Financial Documents Search (得標統計表 T004) (disabled)

============================================================
Starting FactSet Documents Search
Query: FactSet
Output file: FactSetResults.csv
Content type: ALL (PDFs and web pages)
FactSet content parsing: ENABLED
Search restrictions: {'last_days': 360, 'language': 'lang_zh-TW', 'country': None}
============================================================
🔍 Search parameters: days=360, lang=lang_zh-TW, country=None
Retrieved 10 results (total: 10)
Retrieved 10 results (total: 20)
...
Retrieved 5 results (total: 45)
No more results.
Found 45 initial results for FactSet Documents Search
Saved search results to FactSetResults.csv
Platform: Windows
Markitdown available: True
wkhtmltopdf available: False
Warning: wkhtmltopdf is not available. Web pages will be saved as text files instead of PDFs.
Total rows to process for FactSetResults.csv: 45
Processing web page: https://tw.stock.yahoo.com/news/鉅亨速報-factset-最新調查-玉晶光-3406...
Converting web page to Markdown using markitdown: https://tw.stock.yahoo.com/news/...
Successfully converted web page to Markdown: MD/webpage1.md
Parsing FactSet content from: MD/webpage1.md
Pattern 2 matched: '玉晶光' (3406-TW)
Date extracted: 2025-06-18 using pattern: (\d{4})年(\d{1,2})月(\d{1,2})日
Successfully parsed: 玉晶光 (3406-TW)
Extracted data: Company=玉晶光, Symbol=3406-TW, Date=2025-06-18, EPS=21.39
...

============================================================
All enabled search queries completed!
Generated files:
- FactSetResults.csv
  └─ Includes parsed FactSet data columns (Traditional Chinese)
- PDF/ (downloaded PDF files and web pages)
- MD/ (converted Markdown files)
============================================================
GoogleSearch.py v2.0.8 - Process completed successfully!
```

The script will automatically:
1. Execute only enabled searches (FactSet by default)
2. Download all found web pages with NO search restrictions
3. Convert them to Markdown format
4. Extract structured financial data from FactSet content
5. Generate CSV files with Traditional Chinese headers
6. Show detailed progress and extraction results

## Version Control Guidelines

### Updating Version Information
When modifying `GoogleSearch.py`, update the following variables at the top of the script:
```python
__version__ = "X.Y.Z"  # Semantic versioning
__date__ = "YYYY-MM-DD"  # Last modification date
__author__ = "Author Name"  # Script author/modifier
```

### Version Numbering Convention
- **Major (X.0.0)**: Breaking changes, major feature additions, architecture changes
- **Minor (X.Y.0)**: New features, significant enhancements, backward compatible
- **Patch (X.Y.Z)**: Bug fixes, minor improvements, documentation updates

### Change Documentation
1. Update the version history table in README.md
2. Update the docstring version history in GoogleSearch.py
3. Update the `__version__`, `__date__`, and `__author__` variables
4. Document changes in commit messages

## GitHub Actions Monitoring

### Workflow Status
- **📊 Actions Tab**: Monitor workflow executions in the GitHub repository's Actions tab
- **✅ Success Indicators**: Green checkmarks indicate successful executions
- **❌ Failure Alerts**: Red X marks indicate failed executions with detailed logs
- **📈 Execution History**: Complete history of all automated runs

### Troubleshooting Common Issues

#### API Quota Exceeded
- **Symptom**: HTTP 403 errors in workflow logs
- **Solution**: Check Google API quota limits and upgrade if necessary
- **Monitoring**: Review daily API usage in Google Cloud Console

#### Limited Search Results (0 instead of expected)
- **Symptom**: FactSet search returns no results or very few results
- **Solution**: Check Custom Search Engine configuration
- **v2.0.8 Fix**: Balanced search parameters (360 days + Traditional Chinese) ensure results while maintaining relevance
- **Verify**: CSE should have "Search the entire web" enabled

#### Watch List Download Failures
- **Symptom**: "Failed to download watch list" messages
- **Solution**: Check GitHub repository accessibility and CSV file availability
- **Fallback**: Script continues without filtering if watch list unavailable

#### FactSet Parsing Issues (v2.0.4+)
- **Symptom**: "Could not extract company name from content" warnings
- **Solution**: Review regex patterns and content format changes
- **Debug**: Check extracted content preview in logs for pattern matching issues
- **v2.0.5 Fix**: Improved regex patterns handle punctuation correctly

#### wkhtmltopdf Installation Issues
- **Symptom**: "PDF conversion failed" messages for web pages
- **Solution**: Install wkhtmltopdf system package
- **Ubuntu/Debian**: `sudo apt-get install wkhtmltopdf`
- **macOS**: `brew install wkhtmltopdf`
- **Fallback**: Script continues with text file creation if PDF conversion unavailable

#### Markitdown Installation Failures  
- **Symptom**: "markitdown command not found" errors
- **Solution**: Verify `requirements.txt` includes all necessary dependencies
- **Check**: Ensure `pip install markitdown` step completes successfully

#### Repository Secrets Configuration
- **Required Secrets**:
  - `GOOGLE_SEARCH_API_KEY`
  - `GOOGLE_SEARCH_CSE_ID`
- **Setup Location**: Repository Settings → Secrets and variables → Actions

#### File Commit Issues
- **Symptom**: No new files appear after workflow execution
- **Check**: Verify workflow has write permissions to the repository
- **Solution**: Ensure `contents: write` permission is set in Actions.yaml if needed

### Workflow Customization
To modify the automation schedule, edit the cron expression in `.github/workflows/Actions.yaml`:
```yaml
schedule:
  - cron: "10 2 * * *"  # Current: Daily at 2:10 AM UTC
  # Examples:
  # - cron: "0 */6 * * *"    # Every 6 hours
  # - cron: "0 9 * * 1"     # Every Monday at 9 AM UTC
  # - cron: "30 1 1 * *"    # First day of each month at 1:30 AM UTC
```

### GitHub Actions Setup Instructions

1. **Create Workflow Directory**:
   ```bash
   mkdir -p .github/workflows
   ```

2. **Place Actions.yaml**: 
   - Copy `Actions.yaml` to `.github/workflows/Actions.yaml`
   - Ensure proper YAML formatting and indentation

3. **Configure Repository Secrets**:
   - Go to Repository Settings → Secrets and variables → Actions
   - Add `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_CSE_ID`

4. **Test Workflow**:
   - Push to main branch or use manual trigger
   - Monitor execution in the Actions tab

## Output Files

### Main Output Files
- **`GoogleResults.csv`**: Results and file paths for financial documents search (when enabled)
- **`FactSetResults.csv`**: Results and file paths for FactSet search with parsed financial data in Traditional Chinese columns
- **`PDF/`**: Directory containing all downloaded PDF files and converted web pages (PDF or TXT format)
- **`MD/`**: Directory containing all converted Markdown files from PDFs and web pages

### FactSetResults.csv Content Summary
- **Standard columns**: Title, Link, Snippet, File paths
- **34 additional Traditional Chinese columns** with extracted financial data:
  - Company information (公司名稱, 股票代號, 日期, 分析師數量)
  - Current estimates (當前EPS預估, 先前EPS預估, 目標價)
  - EPS forecasts for 2025-2027 (最高值, 最低值, 平均值, 中位數)
  - Revenue forecasts for 2025-2027 (最高值, 最低值, 平均值, 中位數)

## Complete Project Files

### Core Files
- **`GoogleSearch.py`** (v2.0.8): Main search and processing script with configurable parameters, individual search control, watch list integration, web page download capabilities, FactSet data extraction with Traditional Chinese headers, and release date extraction
- **`README.md`**: Comprehensive project documentation
- **`.github/workflows/Actions.yaml`**: GitHub Actions workflow configuration
- **`requirements.txt`**: Python dependencies specification
- **`.env`**: Environment variables (local development only, not committed)

### Generated Files (Auto-created)
- **`GoogleResults.csv`**: Financial documents search results and file paths (when enabled)
- **`FactSetResults.csv`**: FactSet documents search results and file paths with parsed financial data in Traditional Chinese columns
- **`PDF/`**: Directory with downloaded PDF files and converted web pages
- **`MD/`**: Directory with converted Markdown files from all content types

### External Dependencies
- **觀察名單 CSV**: Dynamically downloaded from GitHub repository during FactSet search execution
- **Google Custom Search API**: External service for search functionality
- **Markitdown Tool**: External tool for PDF to Markdown conversion and FactSet content parsing

### GitHub Integration
- **GitHub Secrets**: Secure storage for API credentials
- **GitHub Actions Logs**: Execution history and debugging information for FactSet parsing and search parameter effects
- **Automated Commits**: Bot-generated commits with search results and parsed financial data
- **Watch List Repository**: External GitHub repository for 觀察名單 CSV file