"""
config.py - Enhanced Configuration Management Module (v3.3.2)

Version: 3.3.2
Date: 2025-06-24
Author: Google Search FactSet Pipeline - v3.3.2 Simplified & Observable

v3.3.2 ENHANCEMENTS:
- ✅ Integration with enhanced logging system
- ✅ Stage-specific logging for configuration operations
- ✅ Cross-platform compatibility improvements
- ✅ Performance monitoring integration
- ✅ All v3.3.1/v3.3.0 functionality preserved

v3.3.1/v3.3.0 FEATURES (Maintained):
- ✅ Enhanced 觀察名單.csv downloading with better error handling
- ✅ Improved company validation and processing
- ✅ Better configuration structure for new features
- ✅ Enhanced environment variable management
- ✅ Configuration validation and verification
- ✅ Support for v3.3.0+ specific settings
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
from typing import Dict, List, Optional, Tuple, Any
import traceback

# v3.3.2: Enhanced logging integration
def get_v332_logger():
    """Get v3.3.2 enhanced logger with fallback"""
    try:
        from enhanced_logger import get_stage_logger
        return get_stage_logger("config")
    except ImportError:
        # Fallback to standard logging if v3.3.2 components not available
        import logging
        logger = logging.getLogger('factset_config')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

# Version Information - v3.3.2
__version__ = "3.3.2"
__date__ = "2025-06-24"
__author__ = "Google Search FactSet Pipeline - v3.3.2 Simplified & Observable"

# ============================================================================
# ENHANCED CONFIGURATION CONSTANTS (v3.3.2 - preserved from v3.3.0)
# ============================================================================

# Enhanced watchlist URL with fallback options
WATCHLIST_URLS = [
    "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv",
    "https://raw.githubusercontent.com/wenchiehlee/GoPublic/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"
]

# Enhanced default configuration for v3.3.2 (evolved from v3.3.0)
DEFAULT_CONFIG_V332 = {
    "version": "3.3.2",
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
        "improved_url_cleaning": True,       # v3.3.0: Better URL processing
        "cascade_failure_protection": True  # v3.3.1: Cascade failure protection
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
        "company_name_matching": True,       # v3.3.0: Better matching
        "memory_limit_mb": 2048,             # v3.3.1: Memory management
        "batch_size": 50                     # v3.3.1: Batch processing
    },
    "sheets": {
        "auto_backup": True,
        "create_missing_sheets": True,
        "update_frequency": "on_demand",
        "enhanced_formatting": True,         # v3.3.0: Better formatting
        "worksheet_names": [
            "Portfolio Summary v3.3.2",     # v3.3.2: Updated worksheet names
            "Detailed Data v3.3.2",
            "Statistics v3.3.2"
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
        "enhanced_error_handling": True,      # v3.3.0: Better error handling
        "cross_platform_compatibility": True # v3.3.2: Cross-platform support
    },
    "logging": {                             # v3.3.2: Enhanced logging configuration
        "level": "INFO",
        "stage_specific": True,
        "dual_output": True,
        "performance_monitoring": True,
        "auto_diagnosis": True
    }
}

# Enhanced company validation patterns (preserved from v3.3.0)
COMPANY_VALIDATION_PATTERNS = {
    "stock_code": r"^\d{4}$",
    "company_name": r"^[\u4e00-\u9fff\w\s\(\)]+$",
    "excluded_codes": ["0000", "9999"]
}

# ============================================================================
# ENHANCED WATCHLIST DOWNLOAD (v3.3.2 - with logging integration)
# ============================================================================

def download_target_companies_v332(config=None, force_refresh=False, logger=None):
    """Enhanced target companies download for v3.3.2 with logging integration"""
    if logger is None:
        logger = get_v332_logger()
    
    if config is None:
        config = DEFAULT_CONFIG_V332
    
    logger.info(f"Starting v3.3.2 enhanced watchlist download (force_refresh={force_refresh})")
    
    # Check for existing cached data
    cached_file = "cached_companies_v332.json"
    if os.path.exists(cached_file) and not force_refresh:
        try:
            with open(cached_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if cache is recent (less than 24 hours)
            cached_time = datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01'))
            if (datetime.now() - cached_time).total_seconds() < 86400:  # 24 hours
                logger.info(f"Using cached companies: {len(cached_data['companies'])} companies")
                return cached_data['companies']
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
    
    logger.info("Downloading target companies from 觀察名單.csv (v3.3.2 enhanced)...")
    
    # Enhanced download with multiple URL fallbacks
    companies = []
    for i, url in enumerate(WATCHLIST_URLS):
        try:
            logger.debug(f"Trying URL {i+1}/{len(WATCHLIST_URLS)}: {url}")
            
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
                logger.warning(f"Empty response from URL {i+1}")
                continue
            
            logger.info(f"Successfully downloaded from URL {i+1}")
            break
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"URL {i+1} failed: {e}")
            if i == len(WATCHLIST_URLS) - 1:
                logger.error("All URLs failed")
                return []
            continue
    else:
        logger.error("Failed to download from any URL")
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
        
        logger.info(f"Saved raw CSV: {raw_csv_file}")
        
        # Enhanced CSV parsing
        companies = parse_csv_companies_v332(response.text, logger=logger)
        
        if companies:
            # Cache the results
            cache_data = {
                "version": "3.3.2",
                "cached_at": datetime.now().isoformat(),
                "source_url": url,
                "companies": companies,
                "total_count": len(companies)
            }
            
            with open(cached_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Downloaded and cached {len(companies)} companies (v3.3.2)")
            return companies
        else:
            logger.error("No valid companies found in CSV")
            return []
            
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        return []

def parse_csv_companies_v332(csv_content, logger=None):
    """Enhanced CSV parsing for v3.3.2 with logging integration"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.debug("Starting v3.3.2 enhanced CSV parsing...")
    companies = []
    
    try:
        # Enhanced CSV reading with multiple delimiter support
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        if not rows:
            logger.warning("Empty CSV content")
            return []
        
        # Enhanced header detection
        header_row = rows[0]
        logger.debug(f"CSV headers: {header_row}")
        
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
                logger.info("Using first two columns as code and name")
            else:
                logger.error("Insufficient columns in CSV")
                return []
        
        logger.info(f"Using columns: code={code_col}, name={name_col}")
        
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
                if validate_company_data_v332(code, name, logger=logger):
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
                logger.warning(f"Error processing row {row_num}: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"CSV processing complete: {processed_count} processed, {skipped_count} skipped")
        
        # Enhanced validation summary
        if companies:
            # Detect potential duplicates
            codes = [c['code'] for c in companies]
            unique_codes = set(codes)
            if len(codes) != len(unique_codes):
                duplicates = len(codes) - len(unique_codes)
                logger.warning(f"Found {duplicates} potential duplicate codes")
            
            # Show sample companies
            logger.debug("Sample companies:")
            for company in companies[:5]:
                logger.debug(f"  {company['code']}: {company['name']}")
            if len(companies) > 5:
                logger.debug(f"  ... and {len(companies) - 5} more")
        
        return companies
        
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        return []

def validate_company_data_v332(code, name, logger=None):
    """Enhanced company data validation for v3.3.2 with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    try:
        # Enhanced code validation
        if not code or code == 'nan' or str(code).lower() in ['null', 'none', '']:
            logger.debug(f"Invalid code: {code}")
            return False
        
        # Check code format (4 digits)
        import re
        if not re.match(COMPANY_VALIDATION_PATTERNS["stock_code"], code):
            logger.debug(f"Code format invalid: {code}")
            return False
        
        # Check excluded codes
        if code in COMPANY_VALIDATION_PATTERNS["excluded_codes"]:
            logger.debug(f"Code in exclusion list: {code}")
            return False
        
        # Enhanced name validation
        if not name or name == 'nan' or str(name).lower() in ['null', 'none', '']:
            logger.debug(f"Invalid name: {name}")
            return False
        
        # Check name length
        if len(name) < 2 or len(name) > 50:
            logger.debug(f"Name length invalid: {len(name)}")
            return False
        
        # Check for valid characters (Chinese, English, numbers, some symbols)
        if not re.match(COMPANY_VALIDATION_PATTERNS["company_name"], name):
            logger.debug(f"Name contains invalid characters: {name}")
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Validation error for {code}, {name}: {e}")
        return False

# ============================================================================
# ENHANCED CONFIGURATION MANAGEMENT (v3.3.2 - with logging integration)
# ============================================================================

def load_config_v332(config_file=None, logger=None):
    """Enhanced configuration loading for v3.3.2 with logging integration"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info(f"Loading v3.3.2 enhanced configuration...")
    
    # Start with enhanced defaults
    config = DEFAULT_CONFIG_V332.copy()
    
    # Load from file if specified
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Deep merge with defaults
            config = deep_merge_config(config, file_config)
            logger.info(f"Loaded configuration from: {config_file}")
            
        except Exception as e:
            logger.warning(f"Error loading config file: {e}")
            logger.info("Using default configuration")
    
    # Load environment variable overrides
    config = load_env_overrides_v332(config, logger=logger)
    
    # Validate configuration
    if validate_config_v332(config, logger=logger):
        logger.info("Configuration validation passed")
    else:
        logger.warning("Configuration validation issues detected")
    
    # Download target companies if not present
    if not config.get('target_companies'):
        logger.info("Target companies not in config, downloading...")
        companies = download_target_companies_v332(config, logger=logger)
        config['target_companies'] = companies
    
    # Create necessary directories
    create_directories_v332(config, logger=logger)
    
    # Update last loaded timestamp
    config['last_loaded'] = datetime.now().isoformat()
    
    logger.info(f"Configuration loaded successfully: {len(config.get('target_companies', []))} companies")
    return config

def deep_merge_config(base_config, update_config):
    """Deep merge configuration dictionaries (preserved from v3.3.0)"""
    result = base_config.copy()
    
    for key, value in update_config.items():
        if (key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)):
            result[key] = deep_merge_config(result[key], value)
        else:
            result[key] = value
    
    return result

def load_env_overrides_v332(config, logger=None):
    """Enhanced environment variable overrides for v3.3.2 with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.debug("Loading environment variable overrides...")
    
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
        'FACTSET_MEMORY_LIMIT': ('processing', 'memory_limit_mb'),  # v3.3.1
        'FACTSET_BATCH_SIZE': ('processing', 'batch_size'),         # v3.3.1
        
        # v3.3.2 logging configuration
        'FACTSET_LOG_LEVEL': ('logging', 'level'),
        'FACTSET_ENABLE_PERFORMANCE_MONITORING': ('logging', 'performance_monitoring'),
        
        # General configuration
        'FACTSET_PIPELINE_DEBUG': ('debug', None),
        'FACTSET_WATCHLIST_URL': ('watchlist_url', None)
    }
    
    overrides_applied = 0
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
                if env_var in ['FACTSET_MAX_RESULTS', 'FACTSET_QUALITY_THRESHOLD', 
                              'FACTSET_RATE_LIMIT_DELAY', 'FACTSET_MEMORY_LIMIT', 'FACTSET_BATCH_SIZE']:
                    try:
                        config[section][key] = int(value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_var}: {value}")
                elif env_var in ['FACTSET_ENABLE_DEDUP', 'FACTSET_ENABLE_AGGREGATION', 
                                'FACTSET_ENHANCED_PARSING', 'FACTSET_ENABLE_PERFORMANCE_MONITORING']:
                    config[section][key] = value.lower() in ('true', '1', 'yes')
                else:
                    config[section][key] = value
            
            overrides_applied += 1
    
    if overrides_applied > 0:
        logger.info(f"Applied {overrides_applied} environment variable overrides")
    
    return config

def validate_config_v332(config, logger=None):
    """Enhanced configuration validation for v3.3.2 with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.debug("Starting configuration validation...")
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
    
    # Validate processing configuration (v3.3.1 additions)
    if 'processing' in config:
        processing_config = config['processing']
        
        # Memory validation (v3.3.1)
        if 'memory_limit_mb' in processing_config:
            try:
                limit = int(processing_config['memory_limit_mb'])
                if limit < 512 or limit > 16384:
                    issues.append("processing.memory_limit_mb should be between 512-16384")
            except (ValueError, TypeError):
                issues.append("processing.memory_limit_mb must be integer")
        
        boolean_fields = [
            'parse_md_files', 'deduplicate_data', 'aggregate_by_company',
            'individual_file_analysis', 'enhanced_date_extraction'
        ]
        
        for field in boolean_fields:
            if field in processing_config and not isinstance(processing_config[field], bool):
                issues.append(f"processing.{field} must be boolean")
    
    # v3.3.2: Validate logging configuration
    if 'logging' in config:
        logging_config = config['logging']
        if 'level' in logging_config:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
            if logging_config['level'].upper() not in valid_levels:
                issues.append(f"logging.level must be one of: {valid_levels}")
    
    if issues:
        logger.warning(f"Configuration validation issues found: {len(issues)}")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False
    
    logger.info("Configuration validation passed")
    return True

def create_directories_v332(config, logger=None):
    """Enhanced directory creation for v3.3.2 with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.debug("Creating/verifying directories...")
    
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
    
    # Additional v3.3.0+ directories
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
                logger.warning(f"Error creating directory {directory}: {e}")
    
    logger.info(f"Created/verified {created_count} directories")

# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS (v3.3.2)
# ============================================================================

# Maintain v3.3.1/v3.3.0 compatibility
def download_target_companies_v330(config=None, force_refresh=False):
    """Legacy v3.3.0 compatibility wrapper"""
    return download_target_companies_v332(config, force_refresh)

def load_config_v330(config_file=None):
    """Legacy v3.3.0 compatibility wrapper"""
    return load_config_v332(config_file)

def load_config_v331(config_file=None):
    """v3.3.1 compatibility wrapper"""
    return load_config_v332(config_file)

# ============================================================================
# CONFIGURATION UTILITIES (v3.3.2 - with logging integration)
# ============================================================================

def save_config_v332(config, config_file="config_v332.json", logger=None):
    """Save enhanced configuration to file with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info(f"Saving configuration to {config_file}...")
    
    try:
        # Add metadata
        config_to_save = config.copy()
        config_to_save.update({
            "version": "3.3.2",
            "saved_at": datetime.now().isoformat(),
            "config_file": config_file
        })
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Configuration saved successfully: {config_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def show_config_status_v332(config, logger=None):
    """Show enhanced configuration status with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    print(f"\n{'='*60}")
    print("📊 ENHANCED CONFIGURATION STATUS (v3.3.2)")
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
    print(f"   Cascade protection: {search_config.get('cascade_failure_protection', False)}")  # v3.3.1
    
    # Processing configuration
    processing_config = config.get('processing', {})
    print(f"\n📊 Processing Configuration:")
    print(f"   Deduplicate data: {processing_config.get('deduplicate_data', False)}")
    print(f"   Aggregate by company: {processing_config.get('aggregate_by_company', False)}")
    print(f"   Individual file analysis: {processing_config.get('individual_file_analysis', False)}")
    print(f"   Enhanced date extraction: {processing_config.get('enhanced_date_extraction', False)}")
    print(f"   Memory limit: {processing_config.get('memory_limit_mb', 'Not set')}MB")      # v3.3.1
    print(f"   Batch size: {processing_config.get('batch_size', 'Not set')}")              # v3.3.1
    
    # v3.3.2 Logging configuration
    logging_config = config.get('logging', {})
    print(f"\n📋 Logging Configuration (v3.3.2):")
    print(f"   Level: {logging_config.get('level', 'INFO')}")
    print(f"   Stage-specific: {logging_config.get('stage_specific', True)}")
    print(f"   Dual output: {logging_config.get('dual_output', True)}")
    print(f"   Performance monitoring: {logging_config.get('performance_monitoring', True)}")
    print(f"   Auto diagnosis: {logging_config.get('auto_diagnosis', True)}")
    
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
    
    logger.info("Configuration status displayed")

def test_configuration_v332(config, logger=None):
    """Test enhanced configuration functionality with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Testing v3.3.2 configuration...")
    
    tests = []
    
    # Test 1: Directory creation
    try:
        create_directories_v332(config, logger=logger)
        tests.append(("Directory creation", True, ""))
    except Exception as e:
        tests.append(("Directory creation", False, str(e)))
    
    # Test 2: Company data download
    try:
        companies = download_target_companies_v332(config, force_refresh=True, logger=logger)
        if companies:
            tests.append(("Company download", True, f"{len(companies)} companies"))
        else:
            tests.append(("Company download", False, "No companies found"))
    except Exception as e:
        tests.append(("Company download", False, str(e)))
    
    # Test 3: Configuration validation
    try:
        valid = validate_config_v332(config, logger=logger)
        tests.append(("Configuration validation", valid, ""))
    except Exception as e:
        tests.append(("Configuration validation", False, str(e)))
    
    # Test 4: File permissions
    try:
        test_file = "test_permissions_v332.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        tests.append(("File permissions", True, ""))
    except Exception as e:
        tests.append(("File permissions", False, str(e)))
    
    # Test 5: v3.3.2 logging system
    try:
        test_logger = get_v332_logger()
        test_logger.info("v3.3.2 logging test")
        tests.append(("v3.3.2 Logging system", True, ""))
    except Exception as e:
        tests.append(("v3.3.2 Logging system", False, str(e)))
    
    # Display results
    logger.info("Test Results:")
    passed = 0
    for test_name, result, message in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
        if message:
            logger.info(f"    {message}")
        if result:
            passed += 1
    
    logger.info(f"Summary: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

# ============================================================================
# COMMAND LINE INTERFACE (v3.3.2)
# ============================================================================

def main():
    """Enhanced main function for v3.3.2 configuration management"""
    parser = argparse.ArgumentParser(description=f'Enhanced Configuration Manager v{__version__}')
    parser.add_argument('--download-csv', action='store_true', help='Download 觀察名單.csv')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh cached data')
    parser.add_argument('--show-config', action='store_true', help='Show configuration status')
    parser.add_argument('--test-config', action='store_true', help='Test configuration')
    parser.add_argument('--save-config', type=str, help='Save configuration to file')
    parser.add_argument('--load-config', type=str, help='Load configuration from file')
    parser.add_argument('--validate', action='store_true', help='Validate configuration only')
    parser.add_argument('--create-dirs', action='store_true', help='Create directories only')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logger with specified level
    logger = get_v332_logger()
    
    print(f"🔧 Enhanced Configuration Manager v{__version__}")
    print("="*60)
    
    # Load configuration
    config = load_config_v332(args.load_config, logger=logger)
    
    # Handle specific actions
    if args.download_csv:
        companies = download_target_companies_v332(config, force_refresh=args.force_refresh, logger=logger)
        if companies:
            logger.info(f"Downloaded {len(companies)} companies")
            config['target_companies'] = companies
        else:
            logger.error("Failed to download companies")
    
    if args.show_config:
        show_config_status_v332(config, logger=logger)
    
    if args.test_config:
        success = test_configuration_v332(config, logger=logger)
        if success:
            logger.info("All configuration tests passed")
        else:
            logger.error("Some configuration tests failed")
    
    if args.validate:
        if validate_config_v332(config, logger=logger):
            logger.info("Configuration is valid")
        else:
            logger.error("Configuration validation failed")
    
    if args.create_dirs:
        create_directories_v332(config, logger=logger)
        logger.info("Directories created/verified")
    
    if args.save_config:
        if save_config_v332(config, args.save_config, logger=logger):
            logger.info(f"Configuration saved to {args.save_config}")
        else:
            logger.error("Failed to save configuration")
    
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