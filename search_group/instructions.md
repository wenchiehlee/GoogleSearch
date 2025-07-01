# FactSet Pipeline v3.5.0-validation-fixed - Search Group Complete Implementation Guide

## 🎯 Version & Architecture Overview

**Version**: 3.5.0-validation-fixed - Content Validation + Pure Content Hash Architecture  
**Release Type**: Content Validation Enhanced with Taiwan Financial Data Focus  
**Focus**: Search Group Implementation (Step 1 of 2-step pipeline)  
**Date**: 2025-07-01

### 🏗️ v3.5.0-validation-fixed Architecture Philosophy

```
v3.5.0-pure-hash (Pure Content Hash)    →    v3.5.0-validation-fixed (Validation Enhanced)
├─ 2330_台積電_factset_7796efd2.md      ├─ 2330_台積電_factset_7796efd2.md (validated content)
├─ 2454_聯發科_factset_9a3c5d7f.md      ├─ 2454_聯發科_factset_9a3c5d7f.md (validated content)
├─ 6505_台塑_factset_2b8e4f6a.md        ├─ 6505_台塑_factset_2b8e4f6a.md (validated content)
└─ Perfect deduplication by design      └─ PLUS: Content validation prevents wrong companies

Key Improvements in Validation-Fixed:       New Benefits:
✅ Company content validation layer        ✅ Wrong company content gets score 0 
✅ Validates stock symbol and name match   ✅ No more 6414 content in 2354 files
✅ Enhanced quality scoring with validation ✅ Automatic content verification
✅ Pure content hash filenames maintained  ✅ Validation metadata in YAML headers
✅ All original features preserved        ✅ Enhanced logging and reporting
```

### 🔄 v3.5.0-validation-fixed Two-Stage Pipeline

```
Stage 1: Search Group (This Implementation)        Stage 2: Process Group (Future)
┌─────────────────────────────────────────────┐    ┌─────────────────────────────────────┐
│ 📥 觀察名單.csv (116+ Taiwan stocks)          │    │ 📁 data/md/*.md (Validated files)  │
│          ↓                                  │    │          ↓                         │
│ 🔍 Pure Hash Search Group + Validation     │    │ 📊 Process Group                   │
│   ├─ search_cli.py (validation support)    │    │   ├─ process_cli.py                │
│   ├─ search_engine.py (content validation) │    │   ├─ data_processor.py             │
│   └─ api_manager.py (smart caching)        │    │   └─ report_generator.py           │
│          ↓                                  │    │          ↓                         │
│ 💾 data/md/*.md (Validated content hashes) │    │ 📈 Google Sheets Dashboard         │
└─────────────────────────────────────────────┘    └─────────────────────────────────────┘
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

# 5. Test single company with content validation
python search_group\search_cli.py search --company 2330 --count 3 --min-quality 4

# 6. Search all companies with validation
python search_group\search_cli.py search --all --count 2 --min-quality 4
```

## 📊 Search Group Component Specifications

### 1. search_cli.py (~600 lines) - CLI Interface with Content Validation Support

#### 🎯 Core Responsibilities
- **CLI Command Interface**: Single entry point for all search operations
- **Pure Content Hash Filenames**: Generate filenames based purely on content fingerprint
- **Content Validation Support**: Enhanced logging and reporting for validation results
- **Multiple Results Support**: Generate 1 to N MD files per company with perfect deduplication
- **Perfect Deduplication**: Same content = same filename = 100% efficiency by design
- **Environment Loading**: Automatic .env file loading
- **Workflow Orchestration**: Coordinate search_engine and api_manager
- **Configuration Management**: Load settings and validate environment
- **Progress Monitoring**: Real-time feedback and logging with validation stats
- **Error Handling**: Graceful failures and recovery options

#### 🔧 Key Features

```python
# Pure content hash-based filename generation (NO result index)
content_hash = self._generate_content_fingerprint(symbol, name, financial_data)
filename = f"{symbol}_{name}_factset_{content_hash}.md"
# Result: 2330_台積電_factset_7796efd2.md (validated content)

# Main CLI commands with content validation
python search_cli.py search --company 2330 --min-quality 4         # Validation enabled
python search_cli.py search --company 2330 --count 3 --min-quality 4  # 3 results, validated
python search_cli.py search --all --count 2 --min-quality 4        # All companies, validated
python search_cli.py status                                        # Shows validation stats
```

#### 📁 Pure Content Hash File Structure with Validation

```python
# Pure content hash naming with validation (perfect deterministic)
2330_台積電_factset_7796efd2.md    # Hash from content + VALIDATED content
2330_台積電_factset_9c2b8e1a.md    # Different content = different hash + VALIDATED
2454_聯發科_factset_4f3a7d5c.md    # Each unique content gets unique hash + VALIDATED

# NO files with wrong company content - validation prevents this

# Directory structure
search_group/
├── search_cli.py              # CLI interface with validation support
├── search_engine.py           # Content validation + Taiwan-focused search
├── api_manager.py             # Smart API management
data/
├── md/                        # Generated MD files (validated content only)
cache/
├── search/                    # Search cache and progress
logs/
├── search/                    # Search logs with validation details
觀察名單.csv                    # Watchlist (root folder)
.env                           # Environment variables
```

#### 🛡️ Content Validation Features

```python
def _save_md_file_indexed(self, symbol: str, name: str, content: str, metadata: Dict, index: int) -> str:
    """Save search results with content validation awareness"""
    
    # Generate pure content fingerprint (no result index)
    content_hash = self._generate_content_fingerprint(symbol, name, metadata)
    
    # Clean filename: just company + content hash
    filename = f"{symbol}_{name}_factset_{content_hash}.md"
    file_path = Path(self.config.get("files.output_dir")) / filename
    
    # Check validation status from metadata
    validation_info = metadata.get('content_validation', {})
    is_valid_content = validation_info.get('is_valid', True)
    
    # Enhanced logging based on validation status
    if file_path.exists():
        if is_valid_content:
            self.logger.info(f"📝 Updating content: {filename}")
        else:
            self.logger.warning(f"⚠️  Updating INVALID content: {filename}")
    else:
        if is_valid_content:
            self.logger.info(f"💾 Creating new content: {filename}")
        else:
            self.logger.warning(f"⚠️  Creating INVALID content: {filename}")
    
    return filename
```

### 2. search_engine.py (~800 lines) - Content Validation Enhanced Search Engine

#### 🎯 Core Responsibilities
- **Content Validation**: Validate that search results actually match target company
- **Company Content Matching**: Check stock symbols and company names in content
- **Quality Score Override**: Set score to 0 for invalid content (wrong company)
- **Refined Search Patterns**: Proven patterns based on successful Taiwan financial data discovery
- **Taiwan Financial Site Focus**: Prioritize cnyes.com, statementdog.com, etc.
- **Enhanced Content Processing**: Extract and validate financial data with validation layer
- **Original Quality Assessment**: Preserved original quality scoring with validation enhancement
- **Web Scraping**: Fetch full page content from URLs
- **Data Extraction**: Parse EPS forecasts, analyst counts, target prices with Chinese support
- **Content Generation**: Generate v3.5.0 format MD files with validation metadata

#### 🛡️ Content Validation Implementation

```python
class CompanyContentValidator:
    """Validates that search result content actually matches the target company"""
    
    def validate_content_matches_company(self, target_symbol: str, target_name: str, financial_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that the content actually matches the target company
        
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        try:
            # Get all content sources
            sources = financial_data.get('sources', [])
            all_content = ""
            
            for source in sources:
                title = source.get('title', '')
                snippet = source.get('snippet', '')
                content = f"{title} {snippet}"
                all_content += content + " "
            
            # Check for wrong companies in content
            wrong_companies = self._find_wrong_companies_in_content(target_symbol, target_name, all_content)
            
            if wrong_companies:
                reason = f"Content mentions wrong companies: {', '.join(wrong_companies)}"
                return False, reason
            
            # Check if content mentions the target company at all
            target_mentions = self._find_target_company_mentions(target_symbol, target_name, all_content)
            
            if not target_mentions:
                reason = f"Content does not mention target company {target_symbol} {target_name}"
                return False, reason
            
            # Validation passed
            return True, f"Valid content about {target_symbol}"
            
        except Exception as e:
            return False, f"Validation error: {e}"

class RefinedQualityScorer:
    """ORIGINAL quality assessment with added company content validation"""
    
    def calculate_score(self, financial_data: Dict[str, Any], target_symbol: str = None, target_name: str = None) -> int:
        """Calculate quality score 0-10 with company content validation"""
        
        # FIRST: Validate that content actually matches the target company
        if target_symbol and target_name:
            is_valid, validation_reason = self.validator.validate_content_matches_company(
                target_symbol, target_name, financial_data
            )
            
            if not is_valid:
                # Set validation info in financial_data for debugging
                financial_data['content_validation'] = {
                    'is_valid': False,
                    'reason': validation_reason,
                    'score_override': 0
                }
                return 0  # Invalid content = score 0
            else:
                financial_data['content_validation'] = {
                    'is_valid': True,
                    'reason': validation_reason
                }
        
        # SECOND: Apply ORIGINAL quality scoring logic (completely unchanged)
        # ... (original scoring logic preserved exactly as before)
        
        return final_score
```

#### 📄 Enhanced MD File Content with Validation

```markdown
---
url: https://news.cnyes.com/news/id/5839654
title: 鉅亨速報 - Factset 最新調查：台積電(2330-TW)EPS預估上修至59.66元
quality_score: 8
company: 台積電
stock_code: 2330
extracted_date: 2025-07-01T14:30:25.123456
search_query: 台積電 2330 factset EPS 預估
result_index: 1
content_validation: {"is_valid": true, "reason": "Valid content about 2330"}
version: v3.5.0-validation-fixed
---

根據FactSet最新調查，共42位分析師，對台積電(2330-TW)做出2025年EPS預估：
中位數由59.34元上修至59.66元，其中最高估值65.9元，最低估值51.84元，
預估目標價為1394元。

[Full scraped content continues...]
```

### 3. api_manager.py (~400 lines) - Smart API Management (Unchanged)

#### 🎯 Core Responsibilities (Same as before)
- **Google Search API**: Manage Google Custom Search API calls
- **Rate Limiting**: Implement intelligent rate limiting and backoff
- **Error Handling**: Handle API errors, quotas, and network issues
- **Caching**: Cache search results to avoid duplicate API calls
- **Performance Monitoring**: Track API usage and performance

## 📊 Configuration & Environment Setup

### 🔧 Environment Variables (.env file)

```bash
# Required API credentials
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_CSE_ID=your_custom_search_engine_id_here

# Performance tuning
SEARCH_RATE_LIMIT_PER_SECOND=1.0
SEARCH_DAILY_QUOTA=100

# Quality threshold (invalid content always gets 0)
MIN_QUALITY_THRESHOLD=4

# Logging configuration
LOG_LEVEL=INFO
```

### ⚙️ Default Configuration Changes

```python
# In SearchConfig._load_config()
"validation": {
    "enabled": True,
    "strict_company_matching": True,
    "allow_cross_company_content": False,
    "log_validation_details": True
},
"quality": {
    "min_relevance_score": 2,
    "require_factset_content": False,
    "min_content_length": 100,
    "min_quality_threshold": int(os.getenv("MIN_QUALITY_THRESHOLD", "3"))  # Invalid content = 0 regardless
}
```

## 📁 File Formats & Data Structures

### 📥 Input Format: 觀察名單.csv (Unchanged)

```csv
代號,名稱
1101,台泥
2330,台積電
2454,聯發科
...
```

### 📤 Output Format: Validated Pure Content Hash MD Files

#### Pure Content Hash Filename Examples with Validation
```
# Pure content hash naming with validation - perfect deterministic
2330_台積電_factset_7796efd2.md    # Hash from content + VALIDATED for 2330
2330_台積電_factset_9c2b8e1a.md    # Different content = different hash + VALIDATED for 2330
2454_聯發科_factset_4f3a7d5c.md    # Each company gets unique validated content

# Re-running same search with same results
2330_台積電_factset_7796efd2.md    # EXACT same filename + content validated

# NO files with wrong company content - validation prevents 6414 content in 2354 files
```

#### MD File Content Structure (Enhanced with Validation)
```markdown
---
url: https://news.cnyes.com/news/id/5839654
title: 鉅亨速報 - Factset 最新調查：台積電(2330-TW)EPS預估上修至59.66元
quality_score: 8
company: 台積電
stock_code: 2330
extracted_date: 2025-07-01T14:30:25.123456
search_query: 台積電 2330 factset EPS 預估
result_index: 1
content_validation: {"is_valid": true, "reason": "Valid content about 2330"}
version: v3.5.0-validation-fixed
---

根據FactSet最新調查，共42位分析師，對台積電(2330-TW)做出2025年EPS預估：
中位數由59.34元上修至59.66元，其中最高估值65.9元，最低估值51.84元，
預估目標價為1394元。

[Full scraped content continues...]
```

#### Invalid Content Example (Quality Score = 0)
```markdown
---
url: https://news.cnyes.com/news/id/5788381
title: 鉅亨速報- Factset 最新調查：樺漢(6414-TW)EPS預估下修至18.28元
quality_score: 0
company: 鴻準
stock_code: 2354
extracted_date: 2025-07-01T14:30:25.123456
search_query: 鴻準 2354 factset EPS 預估
result_index: 1
content_validation: {"is_valid": false, "reason": "Content mentions wrong companies: 樺漢(6414)", "score_override": 0}
version: v3.5.0-validation-fixed
---

⚠️ **CONTENT VALIDATION WARNING**: Content mentions wrong companies: 樺漢(6414)
This content may be about a different company than 2354 鴻準.

根據FactSet最新調查，共7位分析師，對樺漢(6414-TW)做出2024年EPS預估：
[Content about wrong company - automatically flagged]
```

## 🚀 Usage Examples & Command Reference

### 📋 Complete Command Reference (Updated for Validation)

```bash
# === SEARCH COMMANDS (with content validation enabled) ===

# Single company searches
python search_cli.py search --company 2330 --min-quality 4        # Validation enabled
python search_cli.py search --company 2330 --count 3 --min-quality 4  # 3 results, validated
python search_cli.py search --company 2330 --count all --min-quality 4 # All results, validated

# Batch searches  
python search_cli.py search --batch 2330,2454,6505 --min-quality 4     # Validation for each
python search_cli.py search --batch 2330,2454,6505 --count 5 --min-quality 4  # 5 results each, validated

# Full watchlist searches
python search_cli.py search --all --min-quality 4                      # All companies, validated
python search_cli.py search --all --count 2 --min-quality 4            # 2 results per company, validated
python search_cli.py search --all --count all --min-quality 4          # All results per company, validated

# Resume interrupted searches
python search_cli.py search --resume --min-quality 4                   # Resume with validation

# === UTILITY COMMANDS ===

# Setup and validation
python search_cli.py validate                                 # Validate API setup + content validation
python search_cli.py status                                   # Show status + validation statistics
python search_cli.py clean                                    # Clean cache
python search_cli.py reset                                    # Reset all data
```

### 🔄 Typical Workflow Examples

#### Example 1: Test Content Validation
```bash
# 1. Validate setup
python search_cli.py validate

# 2. Test with problematic company (2354) using content validation
python search_cli.py search --company 2354 --count 3 --min-quality 4

# 3. Check generated files (validation info in YAML headers)
ls data/md/2354_*.md
# Expected: Files with content_validation metadata showing validation results
```

#### Example 2: Content Validation Results Analysis
```bash
# 1. Search company that had wrong content issues
python search_cli.py search --company 2354 --count 3 --min-quality 4

# 2. Check status for validation statistics
python search_cli.py status
# Expected output includes:
# 🛡️  Content Validation: 85.7% valid content
# ✅ Valid Content: 6
# ❌ Invalid Content: 1
# ⚠️  Invalid content automatically gets score 0
```

#### Example 3: Full Pipeline with Content Validation
```bash
# 1. Search all companies with validation
python search_cli.py search --all --count 2 --min-quality 4

# 2. Check status for comprehensive validation results
python search_cli.py status

# Expected: High validation success rate, automatic filtering of wrong company content
```

## 🔧 Installation & Dependencies (Unchanged)

### 📦 Required Dependencies

```bash
pip install google-api-python-client requests beautifulsoup4 python-dotenv
```

## 🧪 Testing & Validation

### 🔬 Validation Checklist (Updated for Content Validation)

```bash
# Pre-run validation with content validation enabled
python search_cli.py validate

# Expected output:
# ✅ Loaded environment variables from .env file
# 🔑 API Key: ✅ Found
# 🔍 CSE ID: ✅ Found
# 🛡️  Content Validation: ✅ Enabled
# 📡 Testing API connection...
# ✅ API connection successful
# 📋 Checking watchlist...
# ✅ Found 116 companies in watchlist
# 📁 Checking directories...
# ✅ All directories created
# 🎉 Setup validation passed! Ready for comprehensive search with content validation.
# 📄 Using pure content hash filenames (v3.5.0-validation-fixed)
# 🔗 Same content = same filename (no result index needed)
# 🚀 Comprehensive search enabled - all patterns will execute
# 🛡️  Content validation enabled - invalid content gets score 0
# 🐛 Debug logging enabled - will show pattern execution details
```

### 📊 Content Validation Testing

```bash
# Test with company that previously had wrong content (2354)
python search_cli.py search --company 2354 --count 3 --min-quality 4

# Expected output with validation:
# 🔍 Building search queries for 2354 鴻準:
# 🛡️  Content validation: ENABLED - will verify results match 2354
# 
# 🚀 Executing comprehensive search - ALL 40 patterns will run:
# 🎯 Comprehensive search completed:
#    📊 40 patterns executed
#    📡 15 API calls made
#    📄 8 unique results found
#    🛡️  Content validation will check each result
#
# ✅ Result 1: Quality 6/10 - 2354_鴻準_factset_7796efd2.md
# ❌ Result 2: Quality 0/10 - INVALID CONTENT: Content mentions wrong companies: 樺漢(6414)
# ✅ Result 3: Quality 5/10 - 2354_鴻準_factset_9c2b8e1a.md
#
# 🎉 2354 completed - Generated 2 unique MD files (found 8, skipped 1 low quality + 5 invalid content)
# 📊 Search stats: 40 patterns executed, 15 API calls
# 🛡️  Validation: 3 valid, 5 invalid content
```

## 📈 Performance & Optimization

### ⚡ Performance Targets (Updated for Validation)

- **🎯 Throughput**: 50-100 companies per hour (with validation overhead)
- **📊 Success Rate**: > 70% companies with quality 4+ data (improved with validation)
- **🔄 Cache Hit Rate**: > 25% for repeated searches  
- **⏱️ Response Time**: < 10 seconds per search query (slight increase due to validation)
- **💾 Memory Usage**: < 120MB peak memory (increased for validation processing)
- **📁 Deduplication**: 100% perfect deduplication with pure hash filenames
- **🛡️ Validation Accuracy**: > 95% correct company content matching

### 🔧 Content Validation Performance

```bash
# Performance comparison with content validation
--count 1    # ~1.2 minutes per company, deterministic filenames, validation enabled
--count 3    # ~2.5-3.5 minutes per company, perfect deduplication, validation enabled
--count all  # ~3.5-6 minutes per company, maximum unique validated content

# Recommended settings for Taiwan market with validation
--count 2 --min-quality 4    # Best balance: 2 diverse sources, validated content
```

## 🔧 Error Handling & Recovery (Enhanced for Validation)

### 🚨 Common Issues & Solutions (Updated)

#### Issue 1: Wrong Company Content (SOLVED)
```bash
# Old problem: "Search results contain content about different companies"
# Solution: Content validation automatically detects and scores as 0

# Before: 2354_鴻準_factset_abc123.md containing 6414 樺漢 content with quality 7/10
# After:  2354_鴻準_factset_abc123.md flagged as invalid content with quality 0/10

# Content validation output:
# ❌ Result 2: Quality 0/10 - INVALID CONTENT: Content mentions wrong companies: 樺漢(6414)
```

#### Issue 2: Low Quality Scores Due to Wrong Content (SOLVED)
```bash
# Old problem: "Good quality content gets low scores because it's about wrong company"
# Solution: Content validation separates content quality from company matching

# Before: Mixed evaluation of content quality and company relevance
# After:  Clear separation - content about wrong company = automatic score 0
#         Content about right company = normal quality evaluation
```

#### Issue 3: Duplicate Content Files (ALREADY SOLVED)
```bash
# Maintained from previous version: Pure content hash filenames

# Same content = same filename = perfect deduplication
# Pure hash = 100% deduplication efficiency
```

## 📊 Monitoring & Logging (Enhanced for Validation)

### 📊 Status Monitoring (Updated for Validation)

```bash
python search_cli.py status

# Enhanced output with content validation statistics:
# 📊 === Search Group Status ===
# 🏷️  Version: 3.5.0-validation-fixed (Pure Content Hash + Comprehensive Search + Content Validation)
# 🟢 API Status: operational
# 📞 API Calls: 145
# 💾 Cache Hit Rate: 28.5%
# 📄 MD Files Generated: 189
# ✅ Companies Completed: 82
# ⭐ Average Quality Score: 6.2/10 (with validation filtering)
# 📝 Total Unique Files: 189
# 🎯 Pure Content Hash Efficiency: 100% - no duplicates by design
# 🛡️  Content Validation: 91.3% valid content
# ✅ Valid Content: 168
# ❌ Invalid Content: 16
# ⚠️  Invalid content automatically gets score 0
# 🔍 Avg Patterns Executed: 38.5/company
# 📡 Avg API Calls: 14.2/company
# 🚀 Comprehensive Search: Enabled
# 📋 Total Companies in Watchlist: 116
```

### 🛡️ Validation Logging Examples

```bash
# Debug logs showing validation process
# 2025-07-01 14:30:25 - INFO - ✅ Content validation passed for 2330: Valid content about 2330
# 2025-07-01 14:30:26 - WARNING - ❌ Content validation failed for 2354: Content mentions wrong companies: 樺漢(6414)
# 2025-07-01 14:30:27 - INFO - ✅ Quality score for 2330: 8/10 (content validated)
# 2025-07-01 14:30:28 - WARNING - ❌ Quality score for 2354: 0/10 (content validation failed)
```

## 🎯 Success Criteria & Quality Metrics (Updated for Validation)

### 📊 Functional Requirements
- ✅ Process 116+ Taiwan stock companies from 觀察名單.csv
- ✅ Generate pure content hash filenames (perfect deduplication)
- ✅ Achieve 4+ quality scores for 70%+ of Taiwan financial content
- ✅ Support Taiwan financial sites (cnyes.com, statementdog.com, etc.)
- ✅ Perfect content deduplication with pure hash approach
- ✅ Predictable, deterministic filename generation
- ✅ Clean filename format without result indices
- ✅ 100% deduplication efficiency by design
- ✅ **NEW**: Content validation prevents wrong company content
- ✅ **NEW**: Automatic quality score = 0 for invalid content
- ✅ **NEW**: Enhanced logging and reporting with validation statistics

### 📈 Content Validation Benefits
- **Wrong Company Detection**: Automatically identifies content about different companies
- **Quality Score Override**: Invalid content always gets score 0, regardless of financial quality
- **Enhanced Logging**: Clear validation status in logs and file headers
- **Validation Metadata**: Detailed validation information in YAML headers
- **Statistics Tracking**: Comprehensive validation success/failure statistics
- **Preserved Original Logic**: All original quality scoring logic maintained

## 🔄 Version Evolution Summary

```
v3.3.3 (Monolithic)    →    v3.5.0-pure-hash (Pure Hash)    →    v3.5.0-validation-fixed (Validation Enhanced)
├─ Complex monolith     ├─ Perfect content deduplication   ├─ Content validation layer added
├─ Manual deduplication ├─ Pure hash filenames             ├─ Wrong company content filtered
├─ Unpredictable names  ├─ Fully predictable names         ├─ Validation metadata in headers
├─ Wrong company issues ├─ Still had wrong company issues  ├─ Wrong company issues SOLVED
└─ High maintenance     └─ Minimal complexity              └─ Validation-enhanced reliability

Final Result: Clean, efficient, perfectly deduplicated Taiwan financial data search system
              with robust content validation preventing wrong company content issues.
```

## 🛡️ Content Validation Technical Details

### 🔍 Validation Algorithm

```python
def validate_content_matches_company(self, target_symbol: str, target_name: str, financial_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Multi-step validation process:
    
    1. Extract all content from sources (title + snippet)
    2. Search for wrong company mentions using patterns:
       - Stock codes: NNNN-TW format
       - Company names with stock codes: 公司名稱(NNNN-TW)
    3. Check if target company is mentioned at all
    4. Return validation result with detailed reason
    """
    
    # Pattern examples:
    # ❌ Invalid: Content mentions "樺漢(6414-TW)" when searching for 2354
    # ❌ Invalid: Content mentions "6414-TW" when searching for 2354  
    # ✅ Valid: Content mentions "鴻準(2354-TW)" when searching for 2354
    # ✅ Valid: Content mentions "2354-TW" when searching for 2354
```

### 🏗️ Integration Architecture

```
Search Flow with Validation:
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Search API  │───▶│ Extract Content  │───▶│ Validate Match  │───▶│ Score & Save │
│ Results     │    │ (title+snippet)  │    │ (company check) │    │ (0 if invalid)│
└─────────────┘    └──────────────────┘    └─────────────────┘    └──────────────┘
                                                     │
                                                     ▼
                                           ┌─────────────────┐
                                           │ Log Validation  │
                                           │ Results         │
                                           └─────────────────┘
```

This enhanced version now provides robust content validation while maintaining all the benefits of the pure content hash architecture, ensuring that search results actually match the target companies.