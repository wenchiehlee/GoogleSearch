# FactSet Pipeline v3.6.1 - Two-Stage Architecture

[![Pipeline Status](https://img.shields.io/badge/Pipeline-v3.6.1-brightgreen)](https://github.com/your-repo/factset-pipeline)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/your-repo/factset-pipeline)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Search Group](https://img.shields.io/badge/Search%20Group-v3.5.1-orange)](https://github.com/your-repo/factset-pipeline/tree/main/search_group)
[![Process Group](https://img.shields.io/badge/Process%20Group-v3.6.1-blue)](https://github.com/your-repo/factset-pipeline/tree/main/process_group)

## 🎯 Overview

**FactSet Pipeline v3.6.1** is a production-ready two-stage system that automates the collection and analysis of FactSet financial data for Taiwan stock market companies, featuring **API key rotation**, **content validation**, **query pattern analysis**, and **watchlist management**.

### 🏗️ Two-Stage Architecture

```
Stage 1: Search Group (v3.5.1)          Stage 2: Process Group (v3.6.1)
┌─────────────────────────────────────┐    ┌──────────────────────────────────┐
│ 📥 StockID_TWSE_TPEX.csv (116+ Taiwan stocks) │    │ 📁 data/md/*.md (Validated files) │
│          ↓                          │    │          ↓                       │
│ 🔍 Enhanced Search + Key Rotation   │    │ 📊 Analysis & Report Generation  │
│   ├─ API Key Rotation (up to 7)     │    │   ├─ Quality Analysis            │
│   ├─ Content Validation             │    │   ├─ Query Pattern Analysis      │
│   ├─ Pure Content Hash Filenames    │    │   ├─ Watchlist Coverage Analysis │
│   └─ REFINED_SEARCH_PATTERNS        │    │   └─ Report Generation           │
│          ↓                          │    │          ↓                       │
│ 💾 data/md/*.md (High quality)      │────│ 📈 Google Sheets Dashboard      │
└─────────────────────────────────────┘    └──────────────────────────────────┘
```

### 🌟 Key Features

#### Search Group (v3.5.1)
- **🔄 API Key Rotation**: Support up to 7 Google API keys with automatic rotation
- **🛡️ Content Validation**: Validate search results match target company
- **🔗 Pure Content Hash**: Deterministic filenames based on content fingerprint
- **🎯 REFINED_SEARCH_PATTERNS**: Optimized Taiwan financial data search patterns
- **📊 Production-Ready**: 700+ searches/day capacity with automatic quota management

#### Process Group (v3.6.1)
- **📋 Query Pattern Analysis**: Analyze search effectiveness with REFINED_SEARCH_PATTERNS
- **📊 Watchlist Management**: Complete coverage analysis of StockID_TWSE_TPEX.csv companies
- **📈 Quality Scoring**: Standardized 0-10 quality scoring with visual indicators
- **📁 Multiple Report Types**: Portfolio, detailed, query pattern, and watchlist reports
- **☁️ Google Sheets Integration**: Automated upload with formatted worksheets

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-repo/factset-pipeline.git
cd factset-pipeline

# Install dependencies
pip install -r requirements.txt

# Setup environment variables (multiple API keys supported)
cp .env.example .env
# Edit .env with your API keys (see Configuration section)
```

### 2. Two-Stage Usage

#### Stage 1: Search Group
```bash
# Navigate to search group
cd search_group

# Validate setup with API key rotation
python search_cli.py validate

# Search all companies with automatic quota management
python search_cli.py search --all --count 2 --min-quality 4

# Check search results
python search_cli.py status
```

#### Stage 2: Process Group
```bash
# Navigate to process group  
cd process_group

# Process all MD files with full analysis
python process_cli.py process

# Generate specific reports
python process_cli.py keyword-summary     # Query pattern analysis
python process_cli.py watchlist-summary   # Watchlist coverage analysis

# Analyze quality only
python process_cli.py analyze-quality
```

### 3. View Results

- **📊 Google Sheets Dashboard**: Multi-worksheet dashboard with all reports
- **📁 Local CSV Files**: `data/reports/` with standardized formats
- **🔗 MD File Access**: Direct GitHub Raw URLs for immediate file viewing
- **📈 Analytics**: Quality distribution, pattern effectiveness, watchlist coverage

## 📊 System Architecture

### File Structure

```
FactSet-Pipeline/
├── search_group/                      # 🔍 Search Group (v3.5.1)
│   ├── search_cli.py                 # CLI with key rotation support
│   ├── search_engine.py              # Content validation + Taiwan search
│   ├── api_manager.py                # Multiple API key management
│   └── README.md                     # Search group documentation
├── process_group/                     # 📊 Process Group (v3.6.1)
│   ├── process_cli.py                # Processing CLI interface
│   ├── md_scanner.py                 # File system interface
│   ├── md_parser.py                  # MD content + metadata parsing
│   ├── quality_analyzer.py           # Quality scoring system
│   ├── keyword_analyzer.py           # Query pattern analysis
│   ├── watchlist_analyzer.py         # Watchlist coverage analysis
│   ├── report_generator.py           # Multi-format report generation
│   ├── sheets_uploader.py            # Google Sheets integration
│   └── README.md                     # Process group documentation
├── data/                             # 📁 Data Directory
│   ├── md/                          # Generated MD files (Search → Process)
│   ├── reports/                     # Generated CSV reports
│   └── cache/                       # Search cache and progress
├── StockID_TWSE_TPEX.csv                      # Input watchlist (116+ companies)
├── requirements.txt                  # Python dependencies
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

### Communication Pattern

```
Search Group                Process Group
     ↓                           ↑
data/md/*.md ←──────────────────┘
(File-based communication - no direct API calls)
```

## 🔧 Configuration

### Enhanced Environment Variables

```bash
# MULTIPLE API KEYS FOR ROTATION (Search Group)
GOOGLE_SEARCH_API_KEY=your_primary_api_key_here
GOOGLE_SEARCH_CSE_ID=your_custom_search_engine_id_here

# ADDITIONAL KEYS FOR ROTATION (up to 6 more)
GOOGLE_SEARCH_API_KEY1=your_second_api_key_here
GOOGLE_SEARCH_API_KEY2=your_third_api_key_here
GOOGLE_SEARCH_API_KEY3=your_fourth_api_key_here
GOOGLE_SEARCH_API_KEY4=your_fifth_api_key_here
GOOGLE_SEARCH_API_KEY5=your_sixth_api_key_here
GOOGLE_SEARCH_API_KEY6=your_seventh_api_key_here

# GOOGLE SHEETS INTEGRATION (Process Group)
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}

# PERFORMANCE TUNING
SEARCH_RATE_LIMIT_PER_SECOND=1.0
MIN_QUALITY_THRESHOLD=4
LOG_LEVEL=INFO
```

## 📈 Search Group (v3.5.1) Features

### API Key Rotation
- **Multiple Keys**: Support up to 7 Google Search API keys
- **Automatic Rotation**: Seamless failover on quota exceeded (429 errors)
- **Production Capacity**: 700+ searches/day (100 per key × 7 keys)
- **Zero Downtime**: Continuous operation with intelligent key management

### Content Validation
- **Company Matching**: Validate search results match target company
- **Quality Override**: Automatic score 0 for wrong company content
- **Enhanced Patterns**: REFINED_SEARCH_PATTERNS optimized for Taiwan financial sites

### Pure Content Hash Filenames
```bash
# Deterministic naming based on content fingerprint
2330_台積電_factset_7796efd2.md    # Content hash ensures perfect deduplication
2330_台積電_factset_9c2b8e1a.md    # Different content = different hash
2454_聯發科_factset_4f3a7d5c.md    # Each unique content gets unique filename
```

### Search Commands
```bash
# Single company with rotation
python search_cli.py search --company 2330 --count 3 --min-quality 4

# All companies with quota management
python search_cli.py search --all --count 2 --min-quality 4

# Resume interrupted searches
python search_cli.py search --resume --min-quality 4

# Check key rotation status
python search_cli.py status
```

## 📊 Process Group (v3.6.1) Features

### Query Pattern Analysis
- **REFINED_SEARCH_PATTERNS Integration**: Analyze effectiveness of standardized search patterns
- **Pattern Normalization**: Convert queries to `{name} {symbol}` format
- **Effectiveness Scoring**: Rate pattern performance with quality correlation
- **Pattern Categories**: FactSet direct, cnyes.com, EPS forecast, analyst consensus

### Watchlist Management
- **Coverage Analysis**: Track processing status of all StockID_TWSE_TPEX.csv companies
- **Status Categories**: Processed, not found, validation failed, low quality, multiple files
- **Missing Company Reports**: Identify companies needing search attention
- **Quality Statistics**: Average scores, distribution analysis per company

### Report Generation
Four comprehensive report types:

1. **Portfolio Summary** (14 columns): High-level investment overview
2. **Detailed Report** (22 columns): Complete data with validation status
3. **Query Pattern Summary** (10 columns): Search effectiveness analysis
4. **Watchlist Summary** (12 columns): Company coverage and status

### Process Commands
```bash
# Complete processing with all analysis
python process_cli.py process

# Specific analysis types
python process_cli.py analyze-keywords      # Query pattern analysis
python process_cli.py analyze-watchlist    # Watchlist coverage analysis
python process_cli.py analyze-quality      # Quality distribution analysis

# Generate specific reports
python process_cli.py keyword-summary      # Query pattern effectiveness
python process_cli.py watchlist-summary    # Company coverage status

# Processing options
python process_cli.py process-recent --hours=12    # Recent files only
python process_cli.py process-single --company=2330 # Single company
```

## 📋 Report Formats

### 1. Portfolio Summary (14 columns)
```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
2330,台積電,2330-TW,2025/06/24,2025/06/24,1,42,650.5,46.00,23.56,23.56,10,🟢 完整,2025-06-24 10:45:00
```

### 2. Query Pattern Summary (10 columns)
```csv
Query pattern,使用次數,平均品質評分,最高品質評分,最低品質評分,相關公司數量,品質狀態,分類,效果評級,更新日期
{name} {symbol} factset 分析師,30,7.89,8.7,4.3,15,🟡 良好,FactSet直接,良好 ⭐⭐,2025-06-30 13:32:00
```

### 3. Watchlist Summary (12 columns)
```csv
公司代號,公司名稱,MD檔案數量,處理狀態,平均品質評分,最高品質評分,搜尋關鍵字數量,主要關鍵字,關鍵字平均品質,最新檔案日期,驗證狀態,更新日期
2330,台積電,3,✅ 已處理,9.2,10.0,4,台積電 factset eps 預估,8.5,2025-06-24,✅ 驗證通過,2025-06-24 10:45:00
```

## 🎯 Quality Scoring System

### Standardized 0-10 Scale

| Score Range | Indicator | Description | Criteria |
|-------------|-----------|-------------|----------|
| **9-10** | 🟢 完整 | Complete | EPS data 90%+, 20+ analysts, data ≤7 days |
| **8** | 🟡 良好 | Good | EPS data 70%+, 10+ analysts, data ≤30 days |
| **3-7** | 🟠 部分 | Partial | EPS data 30%+, 5+ analysts, data ≤90 days |
| **0-2** | 🔴 不足 | Insufficient | Limited or missing data |

## 🚨 Troubleshooting

### Search Group Issues

```bash
# All API keys exhausted
python search_cli.py status  # Check key rotation status

# Content validation issues  
python search_cli.py search --company 2330 --count 1  # Test single company

# API connection problems
python search_cli.py validate  # Test all keys
```

### Process Group Issues

```bash
# Module loading problems
python process_cli.py validate  # Check all components

# Missing watchlist
# Ensure StockID_TWSE_TPEX.csv exists in root directory

# Google Sheets connection
# Check GOOGLE_SHEETS_CREDENTIALS in .env
```

### Common Solutions

| Issue | Solution |
|-------|----------|
| 429 Quota Exceeded | Add more API keys to .env file |
| Wrong Company Content | Content validation automatically filters these |
| Missing MD Files | Run Search Group first to generate files |
| Watchlist Not Found | Place StockID_TWSE_TPEX.csv in project root |
| Sheets Upload Failed | Verify Google Sheets credentials |

## 📈 Performance Metrics

### Search Group Performance
- **Throughput**: 300-700 companies/hour (with 7 keys)
- **Success Rate**: > 70% companies with quality 4+ data
- **Cache Hit Rate**: > 25% for repeated searches
- **Rotation Efficiency**: < 2 second delay per key rotation
- **Quota Utilization**: 95%+ across all keys

### Process Group Performance
- **Processing Speed**: ~50 MD files/minute
- **Report Generation**: < 30 seconds for all reports
- **Quality Analysis**: 100% validation coverage
- **Memory Usage**: < 200MB peak for 1000+ files
- **Upload Speed**: < 60 seconds to Google Sheets

## 🤝 Contributing

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-repo/factset-pipeline.git
cd factset-pipeline

# Install development dependencies
pip install -r requirements-dev.txt

# Test Search Group
cd search_group
python search_cli.py validate

# Test Process Group
cd process_group  
python process_cli.py validate
```

### Testing Workflow

```bash
# 1. Test Search Group independently
cd search_group
python search_cli.py search --company 2330 --count 1

# 2. Verify MD file generation
ls ../data/md/2330*.md

# 3. Test Process Group independently
cd process_group
python process_cli.py process-single --company 2330

# 4. Verify reports generation
ls ../data/reports/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Documentation Links

- **🔍 Search Group Guide**: [search_group/README.md](search_group/README.md)
- **📊 Process Group Guide**: [process_group/README.md](process_group/README.md)
- **📈 Live Dashboard**: [Google Sheets Dashboard](https://docs.google.com/spreadsheets/d/your_sheet_id/edit)
- **🛠️ API Reference**: [API Documentation](docs/api.md)
- **❓ Troubleshooting**: [Troubleshooting Guide](docs/troubleshooting.md)

---

**FactSet Pipeline v3.6.1 - Two-Stage Architecture**

*A production-ready financial data automation system featuring API key rotation, content validation, query pattern analysis, and comprehensive watchlist management for Taiwan stock market analysis.*

For questions or support, please [open an issue](https://github.com/your-repo/factset-pipeline/issues) or contact the development team.