# FactSet Pipeline v3.5.1 - Search Group Complete Implementation Guide

## 🎯 Version & Architecture Overview

**Version**: 3.5.1 - API Key Rotation Enhanced + Content Validation + Pure Content Hash Architecture  
**Release Type**: Production-Ready with Automatic Quota Management  
**Focus**: Search Group Implementation with Enhanced Reliability (Step 1 of 2-step pipeline)  
**Date**: 2025-07-01

### 🏗️ v3.5.1 Architecture Philosophy

```
v3.5.0-validation-fixed    →    v3.5.1 (API Key Rotation Enhanced)
├─ Content validation      ├─ Content validation (maintained)
├─ Pure content hashes     ├─ Pure content hashes (maintained)
├─ Single API key only     ├─ Multiple API key support (NEW)
├─ Manual quota handling   ├─ Automatic key rotation (NEW)
└─ 100 searches/day limit  └─ 700+ searches/day with 7 keys (NEW)

Key Improvements in v3.5.1:           New Benefits:
✅ Multiple API key support (up to 7)  ✅ 700+ searches/day capacity
✅ Automatic quota management          ✅ Zero-downtime on quota exceeded
✅ Intelligent key rotation            ✅ Seamless failover between keys
✅ Enhanced error handling             ✅ Production-ready reliability
✅ Comprehensive key monitoring        ✅ Real-time rotation status
✅ All previous features preserved     ✅ No manual intervention needed
```

### 🔄 v3.5.1 Two-Stage Pipeline with Enhanced Reliability

```
Stage 1: Search Group (This Implementation)        Stage 2: Process Group (Future)
┌─────────────────────────────────────────────┐    ┌─────────────────────────────────────┐
│ 📥 觀察名單.csv (116+ Taiwan stocks)          │    │ 📁 data/md/*.md (Validated files)  │
│          ↓                                  │    │          ↓                         │
│ 🔍 Enhanced Search Group + Key Rotation    │    │ 📊 Process Group                   │
│   ├─ search_cli.py (rotation support)      │    │   ├─ process_cli.py                │
│   ├─ search_engine.py (content validation) │    │   ├─ data_processor.py             │
│   └─ api_manager.py (key rotation)         │    │   └─ report_generator.py           │
│          ↓                                  │    │          ↓                         │
│ 💾 data/md/*.md (Validated, high volume)   │    │ 📈 Google Sheets Dashboard         │
└─────────────────────────────────────────────┘    └─────────────────────────────────────┘
```

## 🚀 Quick Start Guide

### 📋 Prerequisites

1. **Python 3.8+** installed
2. **Multiple Google Search API Keys** (1-7 keys for quota rotation)
3. **Custom Search Engine ID(s)**
4. **觀察名單.csv** file with Taiwan stock symbols

### ⚡ 5-Minute Setup with Key Rotation

```bash
# 1. Clone and navigate
cd your_project_directory

# 2. Install dependencies
pip install google-api-python-client requests beautifulsoup4 python-dotenv

# 3. Setup environment with multiple API keys (see .env template below)
# Edit .env file with your multiple Google API credentials

# 4. Validate setup with key rotation
python search_group\search_cli.py validate

# 5. Test single company with key rotation support
python search_group\search_cli.py search --company 2330 --count 3 --min-quality 4

# 6. Search all companies with automatic quota management
python search_group\search_cli.py search --all --count 2 --min-quality 4
```

## 📊 Search Group Component Specifications

### 1. search_cli.py (~700 lines) - CLI Interface with API Key Rotation Support

#### 🎯 Core Responsibilities
- **CLI Command Interface**: Single entry point for all search operations
- **API Key Rotation Management**: Seamless handling of multiple API keys
- **Pure Content Hash Filenames**: Generate filenames based purely on content fingerprint
- **Content Validation Support**: Enhanced logging and reporting for validation results
- **Multiple Results Support**: Generate 1 to N MD files per company with perfect deduplication
- **Perfect Deduplication**: Same content = same filename = 100% efficiency by design
- **Environment Loading**: Automatic .env file loading with multiple key support
- **Workflow Orchestration**: Coordinate search_engine and enhanced api_manager
- **Configuration Management**: Load settings and validate multiple API credentials
- **Progress Monitoring**: Real-time feedback with key rotation status
- **Error Handling**: Graceful failures with automatic key rotation

#### 🔧 Key Features with Rotation

```python
# Multiple API key configuration loading
api_keys = []
primary_key = config.get('api.google_api_key')
if primary_key: api_keys.append(primary_key)

for i in range(1, 7):  # Support up to 7 keys total
    key = config.get(f'api.google_api_key{i}')
    if key: api_keys.append(key)

# Automatic rotation on quota exceeded
try:
    result = api_manager.search(query)
except QuotaExceededException:
    # System automatically rotates to next key
    # No manual intervention needed
    pass

# Enhanced status reporting with key information
def show_status():
    key_status = api_manager.get_key_status()
    print(f"🔑 Total Keys: {key_status['total_keys']}")
    print(f"✅ Available Keys: {key_status['available_keys']}")
    print(f"🎯 Current Key: #{key_status['current_key_index']}")
```

#### 📁 Enhanced File Structure with Key Rotation

```python
# Same pure content hash naming (unchanged)
2330_台積電_factset_7796efd2.md    # Hash from content + VALIDATED + high volume support
2330_台積電_factset_9c2b8e1a.md    # Different content = different hash + rotation enabled
2454_聯發科_factset_4f3a7d5c.md    # Each unique content gets unique hash + quota managed

# Enhanced directory structure
search_group/
├── search_cli.py              # CLI interface with key rotation support
├── search_engine.py           # Content validation + Taiwan-focused search (unchanged)
├── api_manager.py             # Enhanced with multiple API key management
data/
├── md/                        # Generated MD files (validated, high volume)
cache/
├── search/                    # Search cache and progress with rotation stats
logs/
├── search/                    # Enhanced logs with key rotation details
觀察名單.csv                    # Watchlist (root folder)
.env                           # Environment variables (multiple keys supported)
```

#### 🛡️ Enhanced Progress Tracking with Key Rotation

```python
def _update_progress_multiple(self, symbol: str, filenames: List[str], results_data: List[Dict]):
    """Update search progress with key rotation tracking"""
    
    # Get key rotation stats
    key_status = self.api_manager.get_key_status()
    
    progress[symbol] = {
        'completed_at': datetime.now().isoformat(),
        'filenames': filenames,
        'file_count': len(filenames),
        'quality_scores': quality_scores,
        'avg_quality_score': round(avg_quality, 1),
        'content_hashes': content_hashes,
        'unique_content_count': len(set(content_hashes)),
        'validation_stats': validation_stats,
        'total_patterns_executed': getattr(self.search_engine, 'last_patterns_executed', 0),
        'total_api_calls': getattr(self.search_engine, 'last_api_calls', 0),
        'key_rotations_during_search': self.api_manager.stats.stats['key_rotations'],  # NEW
        'api_keys_used': key_status['current_key_index'],  # NEW
        'version': __version__
    }
```

### 2. search_engine.py (~800 lines) - Content Validation Enhanced Search Engine (Unchanged)

#### 🎯 Core Responsibilities (Maintained from v3.5.0)
- **Content Validation**: Validate that search results actually match target company
- **Company Content Matching**: Check stock symbols and company names in content
- **Quality Score Override**: Set score to 0 for invalid content (wrong company)
- **Refined Search Patterns**: Proven patterns based on successful Taiwan financial data discovery
- **Taiwan Financial Site Focus**: Prioritize cnyes.com, statementdog.com, etc.
- **Enhanced Content Processing**: Extract and validate financial data with validation layer
- **Original Quality Assessment**: Preserved original quality scoring with validation enhancement
- **Web Scraping**: Fetch full page content from URLs
- **Data Extraction**: Parse EPS forecasts, analyst counts, target prices with Chinese support
- **Content Generation**: Generate v3.5.1 format MD files with validation metadata

*Note: search_engine.py remains unchanged from v3.5.0-validation-fixed as it focuses on content processing, not API management.*

### 3. api_manager.py (~600 lines) - Enhanced API Management with Key Rotation

#### 🎯 Core Responsibilities (Enhanced)
- **Multiple API Key Management**: Handle up to 7 Google Search API keys
- **Automatic Key Rotation**: Seamless rotation on quota exceeded (429 errors)
- **Intelligent Rate Limiting**: Per-key rate limiting and global coordination
- **Enhanced Error Handling**: Distinguish quota vs. rate limit vs. other API errors
- **Comprehensive Monitoring**: Track usage, rotations, and status per key
- **Search Result Caching**: Cache results to avoid duplicate API calls (unchanged)
- **Performance Monitoring**: Enhanced API usage tracking with rotation metrics

#### 🔄 Key Rotation Implementation

```python
class APIKeyManager:
    """Manages multiple Google API keys and automatic rotation"""
    
    def __init__(self, api_keys: List[str], cse_ids: List[str]):
        self.api_keys = api_keys
        self.cse_ids = cse_ids
        self.current_key_index = 0
        self.exhausted_keys = set()
        self.key_stats = {}  # Track usage per key
    
    def mark_key_exhausted(self, error_details: str = ""):
        """Mark current key as exhausted and rotate to next"""
        self.exhausted_keys.add(self.current_key_index)
        
        available_keys = [i for i in range(len(self.api_keys)) if i not in self.exhausted_keys]
        if not available_keys:
            raise AllKeysExhaustedException("All API keys exhausted")
        
        old_index = self.current_key_index
        self.current_key_index = available_keys[0]
        logger.info(f"Rotated from key {old_index + 1} to key {self.current_key_index + 1}")

class APIManager:
    """Enhanced Google Search API Management with Automatic Key Rotation"""
    
    def search(self, query: str, num_results: int = 10) -> Optional[Dict[str, Any]]:
        """Execute search with automatic key rotation on quota exceeded"""
        
        max_retries = min(3, self.key_manager.get_status_summary()['available_keys'])
        
        for attempt in range(max_retries):
            try:
                api_key, cse_id = self.key_manager.get_current_credentials()
                service = build('customsearch', 'v1', developerKey=api_key)
                
                result = service.cse().list(**search_params).execute()
                
                # Success - record and return
                self.key_manager.record_successful_call()
                return self._process_search_result(result, query)
                
            except Exception as e:
                if (hasattr(e, 'resp') and e.resp.status == 429 or 
                    'quotaExceeded' in str(e) or 'Quota exceeded' in str(e)):
                    
                    # Quota exceeded - rotate key and retry
                    try:
                        self.key_manager.mark_key_exhausted(str(e))
                        self.stats.record_key_rotation()
                        continue  # Retry with new key
                    except AllKeysExhaustedException:
                        raise QuotaExceededException("All API keys exhausted")
                else:
                    # Other error - handle normally
                    if attempt == max_retries - 1:
                        raise SearchAPIException(f"Search failed: {e}")
```

## 📊 Configuration & Environment Setup

### 🔧 Enhanced Environment Variables (.env file)

```bash
# PRIMARY API CREDENTIALS (Required)
GOOGLE_SEARCH_API_KEY=your_primary_api_key_here
GOOGLE_SEARCH_CSE_ID=your_custom_search_engine_id_here

# ADDITIONAL API KEYS FOR ROTATION (Optional, up to 6 more)
GOOGLE_SEARCH_API_KEY1=your_second_api_key_here
GOOGLE_SEARCH_API_KEY2=your_third_api_key_here
GOOGLE_SEARCH_API_KEY3=your_fourth_api_key_here
GOOGLE_SEARCH_API_KEY4=your_fifth_api_key_here
GOOGLE_SEARCH_API_KEY5=your_sixth_api_key_here
GOOGLE_SEARCH_API_KEY6=your_seventh_api_key_here

# ADDITIONAL CSE IDs (Optional - can reuse primary)
GOOGLE_SEARCH_CSE_ID1=your_cse_id_here
GOOGLE_SEARCH_CSE_ID2=your_cse_id_here
GOOGLE_SEARCH_CSE_ID3=your_cse_id_here
GOOGLE_SEARCH_CSE_ID4=your_cse_id_here
GOOGLE_SEARCH_CSE_ID5=your_cse_id_here
GOOGLE_SEARCH_CSE_ID6=your_cse_id_here

# PERFORMANCE TUNING
SEARCH_RATE_LIMIT_PER_SECOND=1.0
SEARCH_DAILY_QUOTA=100

# QUALITY THRESHOLD (invalid content always gets 0)
MIN_QUALITY_THRESHOLD=4

# LOGGING CONFIGURATION
LOG_LEVEL=INFO
```

### ⚙️ Enhanced Configuration with Key Rotation

```python
# In SearchConfig._load_config()
"api": {
    # Primary credentials
    "google_api_key": os.getenv("GOOGLE_SEARCH_API_KEY"),
    "google_cse_id": os.getenv("GOOGLE_SEARCH_CSE_ID"),
    
    # Additional keys for rotation
    "google_api_key1": os.getenv("GOOGLE_SEARCH_API_KEY1"),
    "google_api_key2": os.getenv("GOOGLE_SEARCH_API_KEY2"),
    "google_api_key3": os.getenv("GOOGLE_SEARCH_API_KEY3"),
    "google_api_key4": os.getenv("GOOGLE_SEARCH_API_KEY4"),
    "google_api_key5": os.getenv("GOOGLE_SEARCH_API_KEY5"),
    "google_api_key6": os.getenv("GOOGLE_SEARCH_API_KEY6"),
    
    # Additional CSE IDs
    "google_cse_id1": os.getenv("GOOGLE_SEARCH_CSE_ID1"),
    "google_cse_id2": os.getenv("GOOGLE_SEARCH_CSE_ID2"),
    "google_cse_id3": os.getenv("GOOGLE_SEARCH_CSE_ID3"),
    "google_cse_id4": os.getenv("GOOGLE_SEARCH_CSE_ID4"),
    "google_cse_id5": os.getenv("GOOGLE_SEARCH_CSE_ID5"),
    "google_cse_id6": os.getenv("GOOGLE_SEARCH_CSE_ID6")
},
"rotation": {
    "enabled": True,
    "max_retries_per_key": 3,
    "backoff_on_rotation": 2.0,
    "track_key_performance": True
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

### 📤 Output Format: Enhanced MD Files with Key Rotation Metadata

#### Pure Content Hash Filename Examples (Unchanged)
```
# Same naming scheme - content validation + high volume support
2330_台積電_factset_7796efd2.md    # Hash from content + VALIDATED + rotation enabled
2330_台積電_factset_9c2b8e1a.md    # Different content = different hash + quota managed
2454_聯發科_factset_4f3a7d5c.md    # Each company gets unique validated content
```

#### Enhanced MD File Content Structure
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
api_key_used: 2
version: v3.5.1
---

根據FactSet最新調查，共42位分析師，對台積電(2330-TW)做出2025年EPS預估：
中位數由59.34元上修至59.66元，其中最高估值65.9元，最低估值51.84元，
預估目標價為1394元。

[Full scraped content continues...]
```

## 🚀 Usage Examples & Command Reference

### 📋 Complete Command Reference (Updated for Key Rotation)

```bash
# === SEARCH COMMANDS (with automatic key rotation) ===

# Single company searches with rotation support
python search_cli.py search --company 2330 --min-quality 4        # Auto rotation enabled
python search_cli.py search --company 2330 --count 3 --min-quality 4  # 3 results, rotation
python search_cli.py search --company 2330 --count all --min-quality 4 # All results, rotation

# Batch searches with quota management  
python search_cli.py search --batch 2330,2454,6505 --min-quality 4     # Rotation for each
python search_cli.py search --batch 2330,2454,6505 --count 5 --min-quality 4  # 5 results each

# Full watchlist searches with high capacity
python search_cli.py search --all --min-quality 4                      # All companies, auto rotation
python search_cli.py search --all --count 2 --min-quality 4            # 2 results per company
python search_cli.py search --all --count all --min-quality 4          # All results, full quota

# Resume interrupted searches with rotation
python search_cli.py search --resume --min-quality 4                   # Resume with rotation

# === UTILITY COMMANDS (Enhanced) ===

# Setup and validation with key status
python search_cli.py validate                                 # Validate all API keys + rotation
python search_cli.py status                                   # Show status + key rotation info
python search_cli.py clean                                    # Clean cache
python search_cli.py reset                                    # Reset all data
```

### 🔄 Typical Workflow Examples with Key Rotation

#### Example 1: Validate Multiple API Keys
```bash
# 1. Validate setup with all keys
python search_cli.py validate

# Expected output:
# 🔑 API Keys Found: 4 (Primary, Key1, Key2, Key3)
# 🔍 CSE IDs Found: 1 (Primary)
# 🔄 Key Rotation: ✅ Enabled
# 📡 Testing API connection with key rotation...
# ✅ API connection successful
# 🎉 Setup validation passed! Ready for search with API key rotation.
```

#### Example 2: High-Volume Search with Automatic Rotation
```bash
# 1. Search all companies with quota management
python search_cli.py search --all --count 3 --min-quality 4

# Expected console output:
# 🚀 Comprehensive Search with Key Rotation: ALL 116 companies
# 🔑 Starting with API Key #1 (4 available)
# 
# [15/116] 🔍 Comprehensive Search: 2330 台積電...
# ⚠️  Quota exceeded on key 1, attempting rotation...
# 🔄 Rotated from key 1 to key 2
# ✅ Retrying with key 2 (attempt 1/3)
# 🎉 2330 completed - Generated 3 unique MD files
# 🔑 Key rotation: 1 rotations, ended with key #2
```

#### Example 3: Monitor Key Status During Operation
```bash
# 1. Check key status
python search_cli.py status

# Expected output:
# 🔑 API Key Status:
#    📊 Total Keys: 4
#    ✅ Available Keys: 3
#    ❌ Exhausted Keys: 1
#    🎯 Current Key: #2
#
# 🔑 Key Details:
#    Key #1: 🔴 EXHAUSTED - 100 calls, quota exceeded at 2025-07-01T14:30:25
#    Key #2: 🟢 ACTIVE - 45 calls, 0 errors
#    Key #3: 🟡 STANDBY - 0 calls
#    Key #4: 🟡 STANDBY - 0 calls
#
# 📞 API Statistics:
#    🔄 Key Rotations: 1
#    ✅ Success Rate: 98.5%
```

## 🧪 Testing & Validation

### 🔬 Enhanced Validation Checklist

```bash
# Pre-run validation with key rotation
python search_cli.py validate

# Expected output:
# ✅ Loaded environment variables from .env file
# 🔑 API Keys Found: 4 (Primary, Key1, Key2, Key3)
# 🔍 CSE IDs Found: 1 (Primary)
# 🛡️  Content Validation: ✅ Enabled
# 🚀 Comprehensive Search: ✅ Enabled
# 🔄 Key Rotation: ✅ Enabled
# 📡 Testing API connection with key rotation...
# ✅ API connection successful
# 📋 Checking watchlist...
# ✅ Found 116 companies in watchlist
# 📁 Checking directories...
# ✅ All directories created
# 🎉 Setup validation passed! Ready for search with API key rotation.
# 📄 Using pure content hash filenames (v3.5.1)
# 🔗 Same content = same filename (no result index needed)
# 🚀 Comprehensive search enabled - all patterns will execute
# 🛡️  Content validation enabled - invalid content gets score 0
# 🔄 API key rotation enabled - automatic quota management
# 🐛 Debug logging enabled - will show pattern execution details
```

### 📊 Key Rotation Testing

```bash
# Test rotation behavior with high-volume company
python search_cli.py search --company 2330 --count all --min-quality 3

# Expected behavior:
# 1. Starts with Key #1
# 2. When quota exceeded, automatically rotates to Key #2
# 3. Continues search seamlessly
# 4. Reports rotation statistics
# 5. Shows final key status
```

## 📈 Performance & Optimization

### ⚡ Enhanced Performance Targets

- **🎯 Throughput**: 300-700 companies per hour (with 7 keys, 100 quota each)
- **📊 Success Rate**: > 70% companies with quality 4+ data (maintained)
- **🔄 Cache Hit Rate**: > 25% for repeated searches (maintained)
- **⏱️ Response Time**: < 10 seconds per search query (maintained)
- **💾 Memory Usage**: < 150MB peak memory (slight increase for key management)
- **📁 Deduplication**: 100% perfect deduplication with pure hash filenames (maintained)
- **🛡️ Validation Accuracy**: > 95% correct company content matching (maintained)
- **🔄 Rotation Efficiency**: < 2 second delay per key rotation
- **📊 Quota Utilization**: 95%+ utilization across all available keys

### 🔧 Key Rotation Performance

```bash
# Capacity calculation with multiple keys
--count 1    # ~0.3 minutes per company with 7 keys (700 daily quota)
--count 3    # ~0.8 minutes per company with rotation support
--count all  # ~1.2 minutes per company with automatic quota management

# Recommended settings for production with key rotation
--count 2 --min-quality 4    # Optimal balance: 2 sources, validated, high volume
--count all --min-quality 3  # Maximum data collection with quota management
```

## 🔧 Error Handling & Recovery (Enhanced)

### 🚨 Common Issues & Solutions (Updated)

#### Issue 1: All Keys Exhausted (NEW)
```bash
# Problem: "All API keys have been exhausted"
# Solution: Enhanced quota management

# Before: Single key = 100 searches/day limit
# After:  7 keys = 700 searches/day with automatic rotation

# Error handling:
# ❌ All API keys have been exhausted!
# 💡 Solutions:
#    1. Wait for quota reset (midnight UTC)
#    2. Add more API keys to .env file
#    3. Monitor usage in Google Cloud Console
```

#### Issue 2: Key Rotation Delays (NEW)
```bash
# Problem: "Slight delays during key rotation"
# Solution: Optimized rotation logic

# Rotation process:
# 1. Detect 429 quota exceeded error
# 2. Mark current key as exhausted  
# 3. Select next available key
# 4. Retry request with new key
# 5. Continue seamlessly

# Typical delay: < 2 seconds per rotation
```

#### Issue 3: Wrong Company Content (SOLVED - maintained from v3.5.0)
```bash
# Solution: Content validation (maintained)
# ❌ Content about wrong company = automatic score 0
# ✅ Enhanced validation patterns detect all major issues
```

#### Issue 4: Network and API Errors (ENHANCED)
```bash
# Enhanced error classification:
# - Quota errors (429) → Automatic key rotation
# - Rate limit errors → Backoff with same key
# - Network errors → Retry with same key
# - Other API errors → Escalate after retries

# Smart retry logic:
# - Up to 3 attempts per key
# - Automatic rotation on quota exceeded
# - Exponential backoff for rate limits
# - Clear error messaging and logging
```

## 📊 Monitoring & Logging (Enhanced)

### 📊 Enhanced Status Monitoring

```bash
python search_cli.py status

# Enhanced output with key rotation statistics:
# 📊 === Search Group Status with Key Rotation ===
# 🏷️  Version: 3.5.1 (Pure Content Hash + Comprehensive Search + Content Validation + Key Rotation)
# 🟡 API Status: quota_managed
# 
# 🔑 API Key Status:
#    📊 Total Keys: 4
#    ✅ Available Keys: 3  
#    ❌ Exhausted Keys: 1
#    🎯 Current Key: #2
#
# 🔑 Key Details:
#    Key #1: 🔴 EXHAUSTED
#       📞 Calls Made: 100
#       ❌ Errors: 1
#       ⏰ Quota Exceeded: 2025-07-01T14:30:25
#    Key #2: 🟢 ACTIVE  
#       📞 Calls Made: 45
#       ❌ Errors: 0
#       🕐 Last Used: 2025-07-01T15:45:12
#    Key #3: 🟡 STANDBY
#       📞 Calls Made: 0
#    Key #4: 🟡 STANDBY
#       📞 Calls Made: 0
#
# 📞 API Statistics:
#    📞 Total API Calls: 145
#    💾 Cache Hit Rate: 28.5%
#    🔄 Key Rotations: 1
#    ✅ Success Rate: 98.5%
#    📄 MD Files Generated: 189
#    ✅ Companies Completed: 82
#    ⭐ Average Quality Score: 6.2/10 (with validation filtering)
#    📝 Total Unique Files: 189
#    🎯 Pure Content Hash Efficiency: 100% - no duplicates by design
#    🛡️  Enhanced Content Validation: 91.3% valid content
#    ✅ Valid Content: 168
#    ❌ Invalid Content: 16
#    ⚠️  Invalid content automatically gets score 0
#    🔍 Avg Patterns Executed: 38.5/company
#    📡 Avg API Calls: 14.2/company
#    🔄 Avg Key Rotations: 0.3/company
#    🚀 Comprehensive Search: Enabled
#    📋 Total Companies in Watchlist: 116
```

### 🛡️ Enhanced Logging with Key Rotation

```bash
# Debug logs showing key rotation process
# 2025-07-01 14:30:25 - INFO - Starting search with API Key #1
# 2025-07-01 14:30:26 - WARNING - Quota exceeded on key 1: rateLimitExceeded
# 2025-07-01 14:30:26 - INFO - Rotating from key 1 to key 2
# 2025-07-01 14:30:27 - INFO - Retrying search with API Key #2
# 2025-07-01 14:30:28 - INFO - Search successful with key 2: 8 results found
# 2025-07-01 14:30:29 - INFO - Key rotation completed in 1.2 seconds
```

## 🎯 Success Criteria & Quality Metrics (Enhanced)

### 📊 Functional Requirements (Enhanced)
- ✅ Process 116+ Taiwan stock companies from 觀察名單.csv
- ✅ Generate pure content hash filenames (perfect deduplication)
- ✅ Achieve 4+ quality scores for 70%+ of Taiwan financial content
- ✅ Support Taiwan financial sites (cnyes.com, statementdog.com, etc.)
- ✅ Perfect content deduplication with pure hash approach
- ✅ Predictable, deterministic filename generation
- ✅ Clean filename format without result indices
- ✅ 100% deduplication efficiency by design
- ✅ Content validation prevents wrong company content
- ✅ Automatic quality score = 0 for invalid content
- ✅ Enhanced logging and reporting with validation statistics
- ✅ **NEW**: Multiple API key support (up to 7 keys)
- ✅ **NEW**: Automatic key rotation on quota exceeded
- ✅ **NEW**: Production-ready reliability with quota management
- ✅ **NEW**: Zero-downtime search operations
- ✅ **NEW**: 700+ searches/day capacity with 7 keys

### 📈 Enhanced Performance Benefits
- **Quota Management**: Automatic rotation eliminates manual quota monitoring
- **High Capacity**: 700+ searches/day vs. 100 with single key
- **Zero Downtime**: Seamless failover between exhausted keys
- **Production Ready**: Robust error handling for enterprise use
- **Enhanced Monitoring**: Real-time key status and rotation tracking
- **Intelligent Recovery**: Smart retry logic with proper error classification

## 🔄 Version Evolution Summary

```
v3.3.3 (Monolithic)    →    v3.5.0-validation-fixed    →    v3.5.1 (API Key Rotation)
├─ Complex monolith     ├─ Content validation layer    ├─ Multiple API key support
├─ Manual deduplication ├─ Pure hash filenames         ├─ Automatic quota management  
├─ Unpredictable names  ├─ Wrong company detection     ├─ Seamless key rotation
├─ Single API key       ├─ Enhanced quality scoring    ├─ Production-ready reliability
├─ Manual quota limits  ├─ Validation metadata         ├─ Zero-downtime operations
└─ High maintenance     └─ Reliable content validation └─ Enterprise-grade quota handling

Final Result: Production-ready Taiwan financial data search system with automatic
              quota management, content validation, and perfect deduplication.
```

## 🛡️ API Key Rotation Technical Details

### 🔍 Rotation Algorithm

```python
def search_with_rotation(self, query: str) -> Dict[str, Any]:
    """
    Multi-key search with automatic rotation:
    
    1. Use current active API key
    2. Execute Google Custom Search API call
    3. On success: record usage and return results
    4. On 429 quota exceeded:
       a. Mark current key as exhausted
       b. Select next available key
       c. Retry search with new key
       d. Record rotation statistics
    5. On other errors: apply appropriate retry logic
    6. If all keys exhausted: raise AllKeysExhaustedException
    """
    
    max_retries = min(3, available_key_count)
    
    for attempt in range(max_retries):
        try:
            api_key, cse_id = self.key_manager.get_current_credentials()
            result = self._execute_search(api_key, cse_id, query)
            return result
        except QuotaExceededException:
            self.key_manager.mark_key_exhausted()
            continue  # Retry with new key
        except AllKeysExhaustedException:
            raise  # All keys exhausted
        except Exception as e:
            # Handle other errors appropriately
            if attempt == max_retries - 1:
                raise SearchAPIException(f"Search failed: {e}")
```

### 🏗️ Integration Architecture

```
Enhanced Search Flow with Key Rotation:
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Search      │───▶│ Key Manager      │───▶│ Google API      │───▶│ Result       │
│ Request     │    │ (Select Key)     │    │ (With Key)      │    │ Processing   │
└─────────────┘    └──────────────────┘    └─────────────────┘    └──────────────┘
                            │                        │
                            ▼                        ▼
                   ┌─────────────────┐    ┌─────────────────┐
                   │ Error Handler   │    │ Quota Monitor   │
                   │ (Classify)      │    │ (429 Detection) │
                   └─────────────────┘    └─────────────────┘
                            │                        │
                            ▼                        ▼
                   ┌─────────────────┐    ┌─────────────────┐
                   │ Retry Logic     │    │ Key Rotation    │
                   │ (Smart Retry)   │    │ (Auto Switch)   │
                   └─────────────────┘    └─────────────────┘
```

This enhanced version provides enterprise-grade reliability with automatic quota management while maintaining all the content validation and deduplication benefits from previous versions.