# FactSet Pipeline v3.5.0 - Search Group Complete Implementation Guide

## 🎯 Version & Architecture Overview

**Version**: 3.5.0 - Modular Search Group  
**Release Type**: Simplified Modular Architecture with Multiple Results Support  
**Focus**: Search Group Implementation (Step 1 of 2-step pipeline)  
**Date**: 2025-06-28

### 🏗️ v3.5.0 Architecture Philosophy

```
v3.3.3 (Monolithic Integrated)          →          v3.5.0 (Modular Simplified)
├─ factset_cli.py (800+ lines)                    ├─ search_cli.py (~400 lines)
├─ factset_pipeline.py (600+ lines)               ├─ search_engine.py (~500 lines)  
├─ factset_search.py (500+ lines)                 ├─ api_manager.py (~400 lines)
├─ data_processor.py (400+ lines)                 └─ Total: ~1300 lines (50% reduction)
├─ sheets_uploader.py (350+ lines)
└─ Total: 2650+ lines complexity                  Next: process_group/ (separate)
```

### 🔄 v3.5.0 Two-Stage Pipeline

```
Stage 1: Search Group (This Implementation)    Stage 2: Process Group (Future)
┌─────────────────────────────────────────┐    ┌─────────────────────────────────────┐
│ 📥 觀察名單.csv (116+ Taiwan stocks)      │    │ 📁 data/md/*.md (MD files)         │
│          ↓                              │    │          ↓                         │
│ 🔍 Search Group                        │    │ 📊 Process Group                   │
│   ├─ search_cli.py                     │    │   ├─ process_cli.py                │
│   ├─ search_engine.py                  │    │   ├─ data_processor.py             │
│   └─ api_manager.py                    │    │   └─ report_generator.py           │
│          ↓                              │    │          ↓                         │
│ 💾 data/md/*.md (FactSet MD files)     │    │ 📈 Google Sheets Dashboard         │
└─────────────────────────────────────────┘    └─────────────────────────────────────┘
```

## 🚀 Quick Start Guide

### 📋 Prerequisites

1. **Python 3.8+** installed
2. **Google Search API Key** and **Custom Search Engine ID**
3. **觀察名單.csv** file with Taiwan stock symbols

### ⚡ 5-Minute Setup

```bash
# 1. Clone and navigate
cd your_project_directory

# 2. Install dependencies
pip install google-api-python-client requests beautifulsoup4 python-dotenv

# 3. Setup environment (copy your API keys to .env)
# Edit .env file with your Google API credentials

# 4. Validate setup
python search_group\search_cli.py validate

# 5. Test single company
python search_group\search_cli.py search --company 2330 --count 3

# 6. Search all companies
python search_group\search_cli.py search --all --count 2
```

## 📊 Search Group Component Specifications

### 1. search_cli.py (~400 lines) - CLI Interface & Orchestration

#### 🎯 Core Responsibilities
- **CLI Command Interface**: Single entry point for all search operations
- **Multiple Results Support**: Generate 1 to N MD files per company
- **Environment Loading**: Automatic .env file loading
- **Workflow Orchestration**: Coordinate search_engine and api_manager
- **Configuration Management**: Load settings and validate environment
- **Progress Monitoring**: Real-time feedback and logging
- **Error Handling**: Graceful failures and recovery options

#### 🔧 Key Features

```python
# Main CLI commands with multiple results support
python search_cli.py search --company 2330                    # 1 result (default)
python search_cli.py search --company 2330 --count 3          # 3 results
python search_cli.py search --company 2330 --count all        # All possible results
python search_cli.py search --all --count 2                   # All companies, 2 results each
python search_cli.py search --batch 2330,2454,6505 --count 5  # Batch with 5 results each
python search_cli.py search --resume --count all              # Resume with all results
```

#### 📁 File Structure Integration

```python
# Indexed file naming for multiple results
5203_訊連_factset_abc123_0628_1430_001.md    # 1st result
5203_訊連_factset_abc123_0628_1430_002.md    # 2nd result  
5203_訊連_factset_abc123_0628_1430_003.md    # 3rd result

# Directory structure
search_group/
├── search_cli.py              # CLI interface
├── search_engine.py           # Core search logic
├── api_manager.py             # API management
data/
├── md/                        # Generated MD files
├── csv/                       # Input files (optional)
cache/
├── search/                    # Search cache and progress
logs/
├── search/                    # Search logs
觀察名單.csv                    # Watchlist (root folder)
.env                           # Environment variables
```

### 2. search_engine.py (~500 lines) - Core Search Logic

#### 🎯 Core Responsibilities
- **Search Strategy**: Implement intelligent search patterns for FactSet data
- **Multiple Results Processing**: Handle 1 to N search results per company
- **Content Processing**: Extract and validate financial data from search results  
- **Web Scraping**: Fetch full page content from URLs
- **Data Extraction**: Parse EPS forecasts, analyst counts, target prices
- **Quality Assessment**: Basic quality scoring for found data
- **Content Generation**: Generate v3.3.x format MD files

#### 🔍 Search Strategy Implementation

```python
# Search patterns for FactSet data discovery
SEARCH_PATTERNS = {
    'primary': [
        'factset {symbol} taiwan earnings estimates',
        'factset {name} eps forecast consensus',
        '{symbol} taiwan factset analyst estimates',
        'site:factset.com {symbol} taiwan',
        'factset {name} {symbol} financial data'
    ],
    'secondary': [
        '{symbol} tw factset target price',
        '{name} taiwan earnings consensus factset', 
        'factset {symbol} financial estimates',
        '{symbol} taiwan analyst forecast 2025',
        '{name} eps consensus estimates'
    ],
    'fallback': [
        '{symbol} taiwan eps estimates 2025 2026',
        '{name} analyst consensus earnings forecast',
        '{symbol} tw target price analyst',
        '{symbol} taiwan financial outlook',
        '{name} earnings guidance forecast'
    ]
}
```

#### 📊 Multiple Results Processing

```python
def search_company_multiple(self, symbol: str, name: str, result_count: str = '1'):
    """
    Search single company and return multiple results
    
    Args:
        symbol: Stock symbol (e.g., '2330')
        name: Company name (e.g., '台積電')
        result_count: '1', '2', '3', ... or 'all'
    
    Returns:
        List of search results, each as separate MD file
    """
```

#### 📝 v3.3.x MD File Generation

```python
# Generated MD format (same as v3.3.x)
---
url: https://example.com/5203
title: 訊連科技財務資訊
quality_score: 8
company: 訊連
stock_code: 5203
extracted_date: 2025-06-28T14:30:25.123456
search_query: 訊連 5203 factset EPS 預估
result_index: 1
version: v3.5.0
---

[Full HTML/text content from scraped website here...]
```

### 3. api_manager.py (~400 lines) - API Management & Rate Limiting

#### 🎯 Core Responsibilities
- **Google Search API**: Manage Google Custom Search API calls
- **Rate Limiting**: Implement intelligent rate limiting and backoff
- **Error Handling**: Handle API errors, quotas, and network issues
- **Caching**: Cache search results to avoid duplicate API calls
- **Performance Monitoring**: Track API usage and performance

#### ⚡ Rate Limiting Implementation

```python
class RateLimiter:
    """Intelligent rate limiting for Google Search API"""
    
    def __init__(self, calls_per_second: float = 1.0, calls_per_day: int = 100):
        self.calls_per_second = calls_per_second      # Conservative 1 call/second
        self.calls_per_day = calls_per_day            # Daily limit
        # Auto-reset at midnight
        # Graceful quota handling
```

#### 🔍 Google Search API Integration

```python
def search(self, query: str, num_results: int = 10):
    """Execute Google Custom Search with full protection"""
    # ✅ Cache checking
    # ✅ Rate limiting
    # ✅ API call execution
    # ✅ Error handling
    # ✅ Result processing
    # ✅ Quality scoring
```

## 📊 Configuration & Environment Setup

### 🔧 Environment Variables (.env file)

```bash
# Required API credentials
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_CSE_ID=your_custom_search_engine_id_here

# Optional performance tuning
SEARCH_RATE_LIMIT_PER_SECOND=1.0
SEARCH_DAILY_QUOTA=100

# Logging configuration
LOG_LEVEL=INFO
```

### ⚙️ Automatic .env Loading

The v3.5.0 system automatically loads your `.env` file:

```python
# Automatic .env loading with fallback
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    # Manual loading if python-dotenv not available
    # Parses .env file manually
```

## 📁 File Formats & Data Structures

### 📥 Input Format: 觀察名單.csv

```csv
代號,名稱
1101,台泥
1102,亞泥
1216,統一
1301,台塑
1303,南亞
2330,台積電
2454,聯發科
2881,富邦金
6505,台塑化
...
```

### 📤 Output Format: Multiple MD Files (v3.3.x Compatible)

#### Single Result (--count 1)
```
5203_訊連_factset_abc123_0628_1430_001.md
```

#### Multiple Results (--count 3)
```
5203_訊連_factset_abc123_0628_1430_001.md
5203_訊連_factset_abc123_0628_1430_002.md
5203_訊連_factset_abc123_0628_1430_003.md
```

#### MD File Content Structure
```markdown
---
url: https://winvest.tw/Stock/Symbol/Comment/5203
title: 訊連 (5203) 可以買嗎？EPS、營收、配息
quality_score: 8
company: 訊連
stock_code: 5203
extracted_date: 2025-06-28T14:30:25.123456
search_query: 訊連 5203 factset EPS 預估
result_index: 1
version: v3.5.0
---

訊連 (5203) 可以買嗎？EPS、營收、配息、合理價一次看懂 - 雲投資

##### 雲投資 官方 Line 好友綁定
## 1. 加入 LIne 好友
[Full scraped website content continues...]
```

## 🚀 Usage Examples & Command Reference

### 📋 Complete Command Reference

```bash
# === SEARCH COMMANDS ===

# Single company searches
python search_cli.py search --company 2330                    # 1 result (default)
python search_cli.py search --company 2330 --count 3          # 3 results
python search_cli.py search --company 2330 --count all        # All possible results

# Batch searches
python search_cli.py search --batch 2330,2454,6505            # 1 result each
python search_cli.py search --batch 2330,2454,6505 --count 5  # 5 results each
python search_cli.py search --batch 2330,2454,6505 --count all # All results each

# Full watchlist searches
python search_cli.py search --all                             # 1 result per company
python search_cli.py search --all --count 2                   # 2 results per company
python search_cli.py search --all --count all                 # All results per company

# Resume interrupted searches
python search_cli.py search --resume                          # Resume with 1 result
python search_cli.py search --resume --count 3                # Resume with 3 results
python search_cli.py search --resume --count all              # Resume with all results

# === UTILITY COMMANDS ===

# Setup and validation
python search_cli.py validate                                 # Validate API setup
python search_cli.py status                                   # Show current status
python search_cli.py clean                                    # Clean cache
python search_cli.py reset                                    # Reset all data
```

### 🔄 Typical Workflow Examples

#### Example 1: Test Single Company
```bash
# 1. Validate setup
python search_cli.py validate

# 2. Test with popular stock (get 3 results)
python search_cli.py search --company 2330 --count 3

# 3. Check generated files
ls data/md/2330_*.md
```

#### Example 2: Batch Processing
```bash
# 1. Search specific companies with multiple results
python search_cli.py search --batch 2330,2454,2881,6505 --count 5

# 2. Check progress
python search_cli.py status

# 3. Review generated files
ls data/md/
```

#### Example 3: Full Pipeline
```bash
# 1. Search all companies (conservative - 2 results each)
python search_cli.py search --all --count 2

# 2. If interrupted, resume
python search_cli.py search --resume --count 2

# 3. Check final status
python search_cli.py status
```

## 🔧 Installation & Dependencies

### 📦 Required Dependencies

```bash
# Core dependencies
pip install google-api-python-client    # Google Search API
pip install requests                     # HTTP requests
pip install beautifulsoup4              # Web scraping
pip install python-dotenv              # .env file loading (optional)
```

### 🛠️ Complete Setup Process

```bash
# 1. Setup directory structure
mkdir -p data/md data/csv logs/search cache/search

# 2. Install dependencies
pip install google-api-python-client requests beautifulsoup4 python-dotenv

# 3. Create .env file with your API keys
# GOOGLE_SEARCH_API_KEY=your_key_here
# GOOGLE_SEARCH_CSE_ID=your_cse_id_here

# 4. Place 觀察名單.csv in root folder

# 5. Create search_group/ folder with the 3 Python files:
#    - search_cli.py
#    - search_engine.py  
#    - api_manager.py

# 6. Validate setup
python search_group\search_cli.py validate

# 7. Test with single company
python search_group\search_cli.py search --company 2330 --count 3

# 8. Run full pipeline when ready
python search_group\search_cli.py search --all --count 2
```

## 🧪 Testing & Validation

### 🔬 Validation Checklist

```bash
# Pre-run validation
python search_cli.py validate

# Expected output:
# ✅ Loaded environment variables from .env file
# 🔑 API Key: ✅ Found
# 🔍 CSE ID: ✅ Found
# 📡 Testing API connection...
# ✅ API connection successful
# 📋 Checking watchlist...
# ✅ Found 116 companies in watchlist
# 📁 Checking directories...
# ✅ All directories created
# 🎉 Setup validation passed! Ready to search.
```

### 📊 Performance Testing

```bash
# Test API rate limiting
python search_cli.py search --batch 2330,2454,2881 --count 1

# Test multiple results
python search_cli.py search --company 2330 --count 5

# Test quality assessment
python search_cli.py status
```

## 📈 Performance & Optimization

### ⚡ Performance Targets

- **🎯 Throughput**: 50-100 companies per hour (with 1 call/sec rate limit)
- **💾 Memory Usage**: < 100MB peak memory
- **🔄 Cache Hit Rate**: > 20% for repeated searches  
- **⏱️ Response Time**: < 10 seconds per search query
- **📊 Success Rate**: > 80% companies with usable data

### 🔧 Multiple Results Impact

```bash
# Performance comparison
--count 1    # ~1 minute per company  (1 API call)
--count 3    # ~3 minutes per company (3 API calls)  
--count all  # ~5-10 minutes per company (5-10 API calls)

# Recommended settings
--count 2    # Good balance: 2 diverse sources, ~2 minutes each
```

## 🔧 Error Handling & Recovery

### 🚨 Common Issues & Solutions

#### Issue 1: API Quota Exceeded
```bash
# Error: "Daily quota of 100 calls exceeded"
# Solution 1: Wait for daily reset (midnight)
# Solution 2: Increase quota in Google Cloud Console
# Solution 3: Use cache more effectively
python search_cli.py clean  # Clear cache if needed
```

#### Issue 2: Rate Limiting
```bash
# Error: "Rate limit exceeded"
# Solution: System automatically handles with backoff
# Just wait - it will retry automatically
```

#### Issue 3: Network Issues
```bash
# Error: "Failed to fetch content from URL: 403 Forbidden"
# This is normal - some sites block scrapers
# The system continues with snippet content
```

#### Issue 4: No Results Found
```bash
# Error: "No financial data found"
# Try different count values:
python search_cli.py search --company 5203 --count all
```

### 🔄 Resume Capability

```bash
# If search is interrupted
python search_cli.py search --resume --count 3

# System automatically:
# ✅ Loads previous progress
# ✅ Skips completed companies  
# ✅ Continues from where it left off
# ✅ Maintains same result count
```

## 📊 Monitoring & Logging

### 📝 Log Files

```bash
# Log locations
logs/search/search_20250628.log         # Daily search logs
cache/search/progress.json              # Progress tracking
cache/search/failures.json              # Failed searches
cache/search/*.json                     # Search result cache
```

### 📊 Status Monitoring

```bash
python search_cli.py status

# Output example:
# 📊 === Search Group Status ===
# 🏷️  Version: 3.5.0
# 🟢 API Status: operational
# 📞 API Calls: 45
# 💾 Cache Hit Rate: 23.5%
# 📄 MD Files Generated: 89
# ✅ Companies Completed: 42
# ⭐ Average Quality Score: 6.2/10
# 📋 Total Companies in Watchlist: 116
```

## 🎯 Success Criteria & Quality Metrics

### 📊 Functional Requirements
- ✅ Process 116+ Taiwan stock companies from 觀察名單.csv
- ✅ Generate multiple MD files per company (1 to N results)
- ✅ Maintain v3.3.x MD format compatibility
- ✅ Extract financial data and metadata
- ✅ Implement quality scoring system (0-10)
- ✅ Handle API rate limits and errors gracefully
- ✅ Provide comprehensive CLI interface
- ✅ Support resume capability for interrupted searches

### ⚡ Performance Requirements
- ✅ Process 50-100 companies per hour (single result mode)
- ✅ Process 20-50 companies per hour (multiple results mode)
- ✅ Memory usage < 100MB peak
- ✅ Success rate > 80% for usable data
- ✅ Cache hit rate > 20% for efficiency
- ✅ Graceful handling of API quota limits

### 🔧 Technical Requirements
- ✅ Modular architecture (~1300 lines total)
- ✅ Comprehensive error handling and recovery
- ✅ Detailed logging and monitoring
- ✅ Resume capability for interrupted searches
- ✅ Multiple results support with indexed filenames
- ✅ Integration ready for process_group
- ✅ Cross-platform compatibility (Windows/Linux/macOS)

## 🆚 Comparison: v3.3.3 vs v3.5.0

| Feature | v3.3.3 | v3.5.0 |
|---------|---------|---------|
| **Architecture** | Monolithic (2650+ lines) | Modular (1300 lines) |
| **Files Generated** | 1 per company | 1 to N per company |
| **API Management** | Basic | Advanced with caching |
| **Error Handling** | Limited | Comprehensive |
| **Resume Support** | Basic | Full progress tracking |
| **Configuration** | Manual | Auto .env loading |
| **Rate Limiting** | Simple | Intelligent with backoff |
| **Quality Scoring** | None | 0-10 scoring system |
| **MD Format** | v3.3.x YAML + content | Same (compatible) |
| **Web Scraping** | Limited | Full page content |
| **Logging** | Basic | Comprehensive |
| **CLI Interface** | Complex | Simple and intuitive |

## 🚀 Next Steps & Roadmap

### 📅 Immediate Next Steps
1. **Test the complete system** with your watchlist
2. **Fine-tune search patterns** based on actual results
3. **Optimize result count** settings for your needs
4. **Monitor API usage** and adjust quotas if needed

### 🔮 Future Enhancements (Process Group)
1. **Data Processing Module**: Parse MD files and extract structured data
2. **Google Sheets Integration**: Upload results to dashboard
3. **Analytics Dashboard**: Visualize trends and insights
4. **Alert System**: Notify on significant changes
5. **ML Integration**: Improve search and extraction accuracy

### 🎯 Recommended Usage Patterns

#### For Testing & Development
```bash
# Start small
python search_cli.py search --company 2330 --count 3
python search_cli.py search --batch 2330,2454,2881 --count 2
```

#### For Production Use
```bash
# Conservative approach
python search_cli.py search --all --count 2

# Comprehensive approach  
python search_cli.py search --all --count all
```

---

**FactSet Pipeline v3.5.0 Search Group - Complete Implementation Guide**

*This document provides comprehensive specifications for the fully implemented v3.5.0 search group module. The modular design reduces complexity by 50% while adding powerful new features like multiple results support, advanced API management, and comprehensive error handling.*

**Current Status**: ✅ **IMPLEMENTED & TESTED** - Ready for production use with 觀察名單.csv and Google Search API.

**Last Updated**: 2025-06-28