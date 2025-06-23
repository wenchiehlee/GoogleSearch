"""
config.py - Enhanced Configuration Management Module (v3.3.0)

Version: 3.3.0
Date: 2025-06-22
Author: Google Search FactSet Pipeline - v3.3.0 Enhanced Configuration

v3.3.0 ENHANCEMENTS:
- ✅ Enhanced 觀察名單.csv downloading with better error handling
- ✅ Improved company validation and processing
- ✅ Better configuration structure for new features
- ✅ Enhanced environment variable management
- ✅ Configuration validation and verification
- ✅ Support for v3.3.0 specific settings
"""

import os
import io
import csv
import json
import argparse
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback

# Version Information - v3.3.0
__version__ = "3.3.0"
__date__ = "2025-06-22"
__author__ = "Google Search FactSet Pipeline - v3.3.0 Enhanced Configuration"

# ============================================================================
# ENHANCED CONFIGURATION CONSTANTS (v3.3.0)
# ============================================================================

# Enhanced watchlist URL with fallback options
WATCHLIST_URLS = [
    "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv",
    "https://raw.githubusercontent.com/wenchiehlee/GoPublic/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"
]

# Enhanced default configuration for v3.3.0
DEFAULT_CONFIG_V330 = {
    "version": "3.3.0",
    "created_at": datetime.now().isoformat(),
    "target_companies": [],
    "watchlist_url": WATCHLIST_URLS[0],
    "search": {
        "max_results": 10,
        "language": "zh-TW",
        "date_restrict": "y1",
        "safe": "active",
        "rate_limit_delay": 45,
        "max_retries": 3,
        "circuit_breaker_threshold": 1,
        "content_quality_threshold": 3,      # v3.3.0: Quality filtering
        "enhanced_patterns": True,           # v3.3.0: Enhanced search patterns
        "improved_url_cleaning": True        # v3.3.0: Better URL processing
    },
    "output": {
        "base_dir": "data",
        "csv_dir": "data/csv",
        "pdf_dir": "data/pdf",
        "md_dir": "data/md",
        "processed_dir": "data/processed",
        "logs_dir": "logs",
        "backups_dir": "backups",            # v3.3.0: Enhanced backups
        "temp_dir": "temp",                  # v3.3.0: Temporary processing
        "consolidated_csv": "data/processed/consolidated_factset.csv",
        "summary_csv": "data/processed/portfolio_summary.csv",
        "detailed_csv": "data/processed/detailed_data.csv",
        "stats_json": "data/processed/statistics.json"
    },
    "processing": {
        "parse_md_files": True,
        "deduplicate_data": True,            # v3.3.0: Data deduplication
        "aggregate_by_company": True,        # v3.3.0: Company aggregation
        "individual_file_analysis": True,   # v3.3.0: File-level analysis
        "enhanced_date_extraction": True,   # v3.3.0: Better date parsing
        "improved_financial_patterns": True, # v3.3.0: Enhanced patterns
        "quality_scoring": True,             # v3.3.0: Quality assessment
        "company_name_matching": True        # v3.3.0: Better matching
    },
    "sheets": {
        "auto_backup": True,
        "create_missing_sheets": True,
        "update_frequency": "on_demand",
        "enhanced_formatting": True,         # v3.3.0: Better formatting
        "worksheet_names": [
            "Portfolio Summary v3.3.0",
            "Detailed Data v3.3.0",
            "Statistics v3.3.0"
        ],
        "max_rows": {
            "portfolio": 150,
            "detailed": 1000,                # v3.3.0: Support more files
            "statistics": 100
        }
    },
    "validation": {
        "check_file_format": True,
        "validate_company_codes": True,
        "verify_data_quality": True,
        "enhanced_error_handling": True      # v3.3.0: Better error handling
    }
}

# Enhanced company validation patterns
COMPANY_VALIDATION_PATTERNS = {
    "stock_code": r"^\d{4}$",
    "company_name": r"^[\u4e00-\u9fff\w\s\(\)]+$",
    "excluded_codes": ["0000", "9999"]
}

# ============================================================================
# ENHANCED WATCHLIST DOWNLOAD (v3.3.0)
# ============================================================================

def download_target_companies_v330(config=None, force_refresh=False):
    """Enhanced target companies download for v3.3.0"""
    if config is None:
        config = DEFAULT_CONFIG_V330
    
    # Check for existing cached data
    cached_file = "cached_companies_v330.json"
    if os.path.exists(cached_file) and not force_refresh:
        try:
            with open(cached_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if cache is recent (less than 24 hours)
            cached_time = datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01'))
            if (datetime.now() - cached_time).total_seconds() < 86400:  # 24 hours
                print(f"✅ Using cached companies: {len(cached_data['companies'])} companies")
                return cached_data['companies']
        except Exception as e:
            print(f"⚠️ Error reading cache: {e}")
    
    print("📥 Downloading target companies from 觀察名單.csv (v3.3.0 enhanced)...")
    
    # Enhanced download with multiple URL fallbacks
    companies = []
    for i, url in enumerate(WATCHLIST_URLS):
        try:
            print(f"   🔄 Trying URL {i+1}/{len(WATCHLIST_URLS)}...")
            
            # Enhanced request with better headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/csv,text/plain,*/*',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache'
            }
            
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            
            if not response.text.strip():
                print(f"   ⚠️ Empty response from URL {i+1}")
                continue
            
            print(f"   ✅ Successfully downloaded from URL {i+1}")
            break
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ URL {i+1} failed: {e}")
            if i == len(WATCHLIST_URLS) - 1:
                print("❌ All URLs failed")
                return []
            continue
    else:
        print("❌ Failed to download from any URL")
        return []
    
    # Enhanced CSV processing
    try:
        # Save raw CSV with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_csv_file = f"觀察名單_raw_{timestamp}.csv"
        with open(raw_csv_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Also save as current version
        with open("觀察名單.csv", 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"   💾 Saved raw CSV: {raw_csv_file}")
        
        # Enhanced CSV parsing
        companies = parse_csv_companies_v330(response.text)
        
        if companies:
            # Cache the results
            cache_data = {
                "version": "3.3.0",
                "cached_at": datetime.now().isoformat(),
                "source_url": url,
                "companies": companies,
                "total_count": len(companies)
            }
            
            with open(cached_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Downloaded and cached {len(companies)} companies (v3.3.0)")
            return companies
        else:
            print("❌ No valid companies found in CSV")
            return []
            
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return []

def parse_csv_companies_v330(csv_content):
    """Enhanced CSV parsing for v3.3.0"""
    companies = []
    
    try:
        # Enhanced CSV reading with multiple delimiter support
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        if not rows:
            print("⚠️ Empty CSV content")
            return []
        
        # Enhanced header detection
        header_row = rows[0]
        print(f"   📋 CSV headers: {header_row}")
        
        # Determine column indices
        code_col = None
        name_col = None
        
        # Try to find columns by name
        for i, header in enumerate(header_row):
            header_lower = str(header).lower()
            if '代號' in header or 'code' in header_lower:
                code_col = i
            elif '名稱' in header or 'name' in header_lower:
                name_col = i
        
        # Fallback to first two columns
        if code_col is None or name_col is None:
            if len(header_row) >= 2:
                code_col = 0
                name_col = 1
                print("   🔄 Using first two columns as code and name")
            else:
                print("❌ Insufficient columns in CSV")
                return []
        
        print(f"   📊 Using columns: code={code_col}, name={name_col}")
        
        # Enhanced data processing
        processed_count = 0
        skipped_count = 0
        
        for row_num, row in enumerate(rows[1:], 2):  # Skip header
            try:
                if len(row) <= max(code_col, name_col):
                    skipped_count += 1
                    continue
                
                code = str(row[code_col]).strip()
                name = str(row[name_col]).strip()
                
                # Enhanced validation
                if validate_company_data_v330(code, name):
                    companies.append({
                        "code": code,
                        "name": name,
                        "stock_code": f"{code}-TW",
                        "row_number": row_num,
                        "validated": True
                    })
                    processed_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"   ⚠️ Error processing row {row_num}: {e}")
                skipped_count += 1
                continue
        
        print(f"   📈 Processed: {processed_count}, Skipped: {skipped_count}")
        
        # Enhanced validation summary
        if companies:
            # Detect potential duplicates
            codes = [c['code'] for c in companies]
            unique_codes = set(codes)
            if len(codes) != len(unique_codes):
                duplicates = len(codes) - len(unique_codes)
                print(f"   ⚠️ Found {duplicates} potential duplicate codes")
            
            # Show sample companies
            print("   📋 Sample companies:")
            for company in companies[:5]:
                print(f"      {company['code']}: {company['name']}")
            if len(companies) > 5:
                print(f"      ... and {len(companies) - 5} more")
        
        return companies
        
    except Exception as e:
        print(f"❌ Error parsing CSV: {e}")
        return []

def validate_company_data_v330(code, name):
    """Enhanced company data validation for v3.3.0"""
    try:
        # Enhanced code validation
        if not code or code == 'nan' or str(code).lower() in ['null', 'none', '']:
            return False
        
        # Check code format (4 digits)
        if not re.match(COMPANY_VALIDATION_PATTERNS["stock_code"], code):
            return False
        
        # Check excluded codes
        if code in COMPANY_VALIDATION_PATTERNS["excluded_codes"]:
            return False
        
        # Enhanced name validation
        if not name or name == 'nan' or str(name).lower() in ['null', 'none', '']:
            return False
        
        # Check name length
        if len(name) < 2 or len(name) > 50:
            return False
        
        # Check for valid characters (Chinese, English, numbers, some symbols)
        if not re.match(COMPANY_VALIDATION_PATTERNS["company_name"], name):
            return False
        
        return True
        
    except Exception:
        return False

# ============================================================================
# ENHANCED CONFIGURATION MANAGEMENT (v3.3.0)
# ============================================================================

def load_config_v330(config_file=None):
    """Enhanced configuration loading for v3.3.0"""
    print(f"🔧 Loading v3.3.0 configuration...")
    
    # Start with enhanced defaults
    config = DEFAULT_CONFIG_V330.copy()
    
    # Load from file if specified
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Deep merge with defaults
            config = deep_merge_config(config, file_config)
            print(f"✅ Loaded configuration from: {config_file}")
            
        except Exception as e:
            print(f"⚠️ Error loading config file: {e}")
            print("🔄 Using default configuration")
    
    # Load environment variable overrides
    config = load_env_overrides_v330(config)
    
    # Validate configuration
    if validate_config_v330(config):
        print("✅ Configuration validation passed")
    else:
        print("⚠️ Configuration validation issues detected")
    
    # Download target companies if not present
    if not config.get('target_companies'):
        companies = download_target_companies_v330(config)
        config['target_companies'] = companies
    
    # Create necessary directories
    create_directories_v330(config)
    
    # Update last loaded timestamp
    config['last_loaded'] = datetime.now().isoformat()
    
    return config

def deep_merge_config(base_config, update_config):
    """Deep merge configuration dictionaries"""
    result = base_config.copy()
    
    for key, value in update_config.items():
        if (key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)):
            result[key] = deep_merge_config(result[key], value)
        else:
            result[key] = value
    
    return result

def load_env_overrides_v330(config):
    """Enhanced environment variable overrides for v3.3.0"""
    env_mappings = {
        # Search configuration
        'GOOGLE_SEARCH_API_KEY': ('search', 'api_key'),
        'GOOGLE_SEARCH_CSE_ID': ('search', 'cse_id'),
        'FACTSET_MAX_RESULTS': ('search', 'max_results'),
        'FACTSET_QUALITY_THRESHOLD': ('search', 'content_quality_threshold'),
        'FACTSET_RATE_LIMIT_DELAY': ('search', 'rate_limit_delay'),
        
        # Sheets configuration
        'GOOGLE_SHEETS_CREDENTIALS': ('sheets', 'credentials'),
        'GOOGLE_SHEET_ID': ('sheets', 'sheet_id'),
        
        # Processing configuration
        'FACTSET_ENABLE_DEDUP': ('processing', 'deduplicate_data'),
        'FACTSET_ENABLE_AGGREGATION': ('processing', 'aggregate_by_company'),
        'FACTSET_ENHANCED_PARSING': ('processing', 'enhanced_date_extraction'),
        
        # General configuration
        'FACTSET_PIPELINE_DEBUG': ('debug', None),
        'FACTSET_WATCHLIST_URL': ('watchlist_url', None)
    }
    
    for env_var, (section, key) in env_mappings.items():
        value = os.environ.get(env_var)
        if value:
            if section == 'debug':
                config[section] = value.lower() in ('true', '1', 'yes')
            elif section == 'watchlist_url':
                config[section] = value
            else:
                if section not in config:
                    config[section] = {}
                
                # Type conversion for specific values
                if env_var in ['FACTSET_MAX_RESULTS', 'FACTSET_QUALITY_THRESHOLD', 'FACTSET_RATE_LIMIT_DELAY']:
                    try:
                        config[section][key] = int(value)
                    except ValueError:
                        print(f"⚠️ Invalid integer value for {env_var}: {value}")
                elif env_var in ['FACTSET_ENABLE_DEDUP', 'FACTSET_ENABLE_AGGREGATION', 'FACTSET_ENHANCED_PARSING']:
                    config[section][key] = value.lower() in ('true', '1', 'yes')
                else:
                    config[section][key] = value
    
    return config

def validate_config_v330(config):
    """Enhanced configuration validation for v3.3.0"""
    issues = []
    
    # Validate required sections
    required_sections = ['search', 'output', 'processing', 'sheets']
    for section in required_sections:
        if section not in config:
            issues.append(f"Missing required section: {section}")
    
    # Validate search configuration
    if 'search' in config:
        search_config = config['search']
        
        # Check numeric values
        numeric_fields = {
            'max_results': (1, 50),
            'rate_limit_delay': (1, 300),
            'content_quality_threshold': (1, 10)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in search_config:
                try:
                    value = int(search_config[field])
                    if not (min_val <= value <= max_val):
                        issues.append(f"search.{field} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    issues.append(f"search.{field} must be a valid integer")
    
    # Validate output directories
    if 'output' in config:
        output_config = config['output']
        required_dirs = ['csv_dir', 'md_dir', 'processed_dir']
        
        for dir_key in required_dirs:
            if dir_key not in output_config:
                issues.append(f"Missing required output directory: {dir_key}")
    
    # Validate processing configuration
    if 'processing' in config:
        processing_config = config['processing']
        boolean_fields = [
            'parse_md_files', 'deduplicate_data', 'aggregate_by_company',
            'individual_file_analysis', 'enhanced_date_extraction'
        ]
        
        for field in boolean_fields:
            if field in processing_config and not isinstance(processing_config[field], bool):
                issues.append(f"processing.{field} must be boolean")
    
    if issues:
        print("⚠️ Configuration validation issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    return True

def create_directories_v330(config):
    """Enhanced directory creation for v3.3.0"""
    directories = []
    
    # Extract all directory paths from config
    if 'output' in config:
        output_config = config['output']
        for key, value in output_config.items():
            if key.endswith('_dir'):
                directories.append(value)
            elif key.endswith('_csv') or key.endswith('_json'):
                # Extract directory from file paths
                directories.append(os.path.dirname(value))
    
    # Additional v3.3.0 directories
    additional_dirs = ['logs', 'backups', 'temp']
    directories.extend(additional_dirs)
    
    # Create directories
    created_count = 0
    for directory in directories:
        if directory:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                created_count += 1
            except Exception as e:
                print(f"⚠️ Error creating directory {directory}: {e}")
    
    print(f"📁 Created/verified {created_count} directories")

# ============================================================================
# CONFIGURATION UTILITIES (v3.3.0)
# ============================================================================

def save_config_v330(config, config_file="config_v330.json"):
    """Save enhanced configuration to file"""
    try:
        # Add metadata
        config_to_save = config.copy()
        config_to_save.update({
            "version": "3.3.0",
            "saved_at": datetime.now().isoformat(),
            "config_file": config_file
        })
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuration saved: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def show_config_status_v330(config):
    """Show enhanced configuration status"""
    print(f"\n{'='*60}")
    print("📊 ENHANCED CONFIGURATION STATUS (v3.3.0)")
    print("="*60)
    
    # Version and basic info
    print(f"Version: {config.get('version', 'Unknown')}")
    print(f"Last loaded: {config.get('last_loaded', 'Unknown')}")
    print(f"Target companies: {len(config.get('target_companies', []))}")
    
    # Search configuration
    search_config = config.get('search', {})
    print(f"\n🔍 Search Configuration:")
    print(f"   Max results: {search_config.get('max_results', 'Not set')}")
    print(f"   Quality threshold: {search_config.get('content_quality_threshold', 'Not set')}")
    print(f"   Rate limit delay: {search_config.get('rate_limit_delay', 'Not set')}s")
    print(f"   Enhanced patterns: {search_config.get('enhanced_patterns', False)}")
    
    # Processing configuration
    processing_config = config.get('processing', {})
    print(f"\n📊 Processing Configuration:")
    print(f"   Deduplicate data: {processing_config.get('deduplicate_data', False)}")
    print(f"   Aggregate by company: {processing_config.get('aggregate_by_company', False)}")
    print(f"   Individual file analysis: {processing_config.get('individual_file_analysis', False)}")
    print(f"   Enhanced date extraction: {processing_config.get('enhanced_date_extraction', False)}")
    
    # Output configuration
    output_config = config.get('output', {})
    print(f"\n📁 Output Configuration:")
    print(f"   MD directory: {output_config.get('md_dir', 'Not set')}")
    print(f"   Processed directory: {output_config.get('processed_dir', 'Not set')}")
    print(f"   Portfolio summary: {output_config.get('summary_csv', 'Not set')}")
    
    # Sheets configuration
    sheets_config = config.get('sheets', {})
    print(f"\n📈 Sheets Configuration:")
    print(f"   Auto backup: {sheets_config.get('auto_backup', False)}")
    print(f"   Enhanced formatting: {sheets_config.get('enhanced_formatting', False)}")
    worksheets = sheets_config.get('worksheet_names', [])
    print(f"   Worksheets: {len(worksheets)}")
    for ws in worksheets:
        print(f"      - {ws}")
    
    # Environment variables
    env_vars = [
        'GOOGLE_SEARCH_API_KEY', 'GOOGLE_SEARCH_CSE_ID',
        'GOOGLE_SHEETS_CREDENTIALS', 'GOOGLE_SHEET_ID'
    ]
    print(f"\n🔐 Environment Variables:")
    for var in env_vars:
        status = "✅ Set" if os.environ.get(var) else "❌ Not set"
        print(f"   {var}: {status}")

def test_configuration_v330(config):
    """Test enhanced configuration functionality"""
    print(f"\n🧪 Testing v3.3.0 configuration...")
    
    tests = []
    
    # Test 1: Directory creation
    try:
        create_directories_v330(config)
        tests.append(("Directory creation", True, ""))
    except Exception as e:
        tests.append(("Directory creation", False, str(e)))
    
    # Test 2: Company data download
    try:
        companies = download_target_companies_v330(config, force_refresh=True)
        if companies:
            tests.append(("Company download", True, f"{len(companies)} companies"))
        else:
            tests.append(("Company download", False, "No companies found"))
    except Exception as e:
        tests.append(("Company download", False, str(e)))
    
    # Test 3: Configuration validation
    try:
        valid = validate_config_v330(config)
        tests.append(("Configuration validation", valid, ""))
    except Exception as e:
        tests.append(("Configuration validation", False, str(e)))
    
    # Test 4: File permissions
    try:
        test_file = "test_permissions_v330.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        tests.append(("File permissions", True, ""))
    except Exception as e:
        tests.append(("File permissions", False, str(e)))
    
    # Display results
    print(f"\n📋 Test Results:")
    passed = 0
    for test_name, result, message in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if message:
            print(f"      {message}")
        if result:
            passed += 1
    
    print(f"\n📊 Summary: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

# ============================================================================
# COMMAND LINE INTERFACE (v3.3.0)
# ============================================================================

def main():
    """Enhanced main function for v3.3.0 configuration management"""
    parser = argparse.ArgumentParser(description=f'Enhanced Configuration Manager v{__version__}')
    parser.add_argument('--download-csv', action='store_true', help='Download 觀察名單.csv')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh cached data')
    parser.add_argument('--show-config', action='store_true', help='Show configuration status')
    parser.add_argument('--test-config', action='store_true', help='Test configuration')
    parser.add_argument('--save-config', type=str, help='Save configuration to file')
    parser.add_argument('--load-config', type=str, help='Load configuration from file')
    parser.add_argument('--validate', action='store_true', help='Validate configuration only')
    parser.add_argument('--create-dirs', action='store_true', help='Create directories only')
    
    args = parser.parse_args()
    
    print(f"🔧 Enhanced Configuration Manager v{__version__}")
    print("="*60)
    
    # Load configuration
    config = load_config_v330(args.load_config)
    
    # Handle specific actions
    if args.download_csv:
        companies = download_target_companies_v330(config, force_refresh=args.force_refresh)
        if companies:
            print(f"✅ Downloaded {len(companies)} companies")
            config['target_companies'] = companies
        else:
            print("❌ Failed to download companies")
    
    if args.show_config:
        show_config_status_v330(config)
    
    if args.test_config:
        success = test_configuration_v330(config)
        if success:
            print("✅ All configuration tests passed")
        else:
            print("❌ Some configuration tests failed")
    
    if args.validate:
        if validate_config_v330(config):
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration validation failed")
    
    if args.create_dirs:
        create_directories_v330(config)
        print("✅ Directories created/verified")
    
    if args.save_config:
        if save_config_v330(config, args.save_config):
            print(f"✅ Configuration saved to {args.save_config}")
        else:
            print("❌ Failed to save configuration")
    
    # If no specific action, show status
    if not any([args.download_csv, args.show_config, args.test_config, 
               args.validate, args.create_dirs, args.save_config]):
        print("💡 Use --help for available options")
        print("💡 Common commands:")
        print("   python config.py --download-csv     # Download companies")
        print("   python config.py --show-config      # Show configuration")
        print("   python config.py --test-config      # Test everything")

if __name__ == "__main__":
    import re  # Add this import for the regex patterns
    main()