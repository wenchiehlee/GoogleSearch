#!/usr/bin/env python3
"""
search_cli.py - Search Group CLI Interface with API Key Rotation (v3.5.1)

Version: 3.5.1
Date: 2025-07-01
Author: FactSet Pipeline v3.5.1 - Enhanced with API Key Rotation

ENHANCED API KEY ROTATION SUPPORT:
- Multiple Google API key management (up to 7 keys)
- Automatic key rotation on quota exceeded
- Enhanced status reporting with key information
- Improved error handling and recovery

FIXED: SearchEngine initialization to include config parameter
"""

import os
import sys
import csv
import json
import time
import hashlib
import argparse
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    # If python-dotenv is not installed, try to load .env manually
    env_file = Path('.env')
    if env_file.exists():
        print("📄 Loading .env file manually...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key.strip()] = value
        print("✅ Loaded environment variables manually")
    else:
        print("⚠️ No .env file found")

# Version Information
__version__ = "3.5.1"
__date__ = "2025-07-01"

# Import search group components
try:
    from search_engine import SearchEngine
    from api_manager import APIManager
except ImportError as e:
    print(f"Error importing search components: {e}")
    print("Make sure search_engine.py and api_manager.py are in the same directory")
    sys.exit(1)

class SearchConfig:
    """Configuration management for search group with multiple API keys"""
    
    def __init__(self):
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load search configuration with multiple API key support"""
        return {
            "version": "3.5.1",
            "search": {
                "rate_limit_delay": float(os.getenv("SEARCH_RATE_LIMIT_PER_SECOND", "1.0")),
                "daily_quota": int(os.getenv("SEARCH_DAILY_QUOTA", "100")),
                "num_results_per_query": 10,
                "date_restrict": "y1",
                "language": "lang_zh-TW|lang_en",
                "safe_search": "off",
                "backoff_multiplier": 2.0,
                "max_backoff_seconds": 300,
                "enable_debug_logging": True,
                "comprehensive_search": True,
                "content_validation": True
            },
            "api": {
                # Primary API credentials
                "google_api_key": os.getenv("GOOGLE_SEARCH_API_KEY"),
                "google_cse_id": os.getenv("GOOGLE_SEARCH_CSE_ID"),
                
                # Additional API keys (1-6)
                "google_api_key1": os.getenv("GOOGLE_SEARCH_API_KEY1"),
                "google_api_key2": os.getenv("GOOGLE_SEARCH_API_KEY2"),
                "google_api_key3": os.getenv("GOOGLE_SEARCH_API_KEY3"),
                "google_api_key4": os.getenv("GOOGLE_SEARCH_API_KEY4"),
                "google_api_key5": os.getenv("GOOGLE_SEARCH_API_KEY5"),
                "google_api_key6": os.getenv("GOOGLE_SEARCH_API_KEY6"),
                
                # Additional CSE IDs (1-6)
                "google_cse_id1": os.getenv("GOOGLE_SEARCH_CSE_ID1"),
                "google_cse_id2": os.getenv("GOOGLE_SEARCH_CSE_ID2"),
                "google_cse_id3": os.getenv("GOOGLE_SEARCH_CSE_ID3"),
                "google_cse_id4": os.getenv("GOOGLE_SEARCH_CSE_ID4"),
                "google_cse_id5": os.getenv("GOOGLE_SEARCH_CSE_ID5"),
                "google_cse_id6": os.getenv("GOOGLE_SEARCH_CSE_ID6")
            },
            "quality": {
                "min_relevance_score": 2,
                "require_factset_content": False,
                "min_content_length": 100,
                "min_quality_threshold": int(os.getenv("MIN_QUALITY_THRESHOLD", "3"))
            },
            "validation": {
                "enabled": True,
                "strict_company_matching": True,
                "allow_cross_company_content": False,
                "log_validation_details": True,
                "enhanced_patterns": True
            },
            "caching": {
                "enabled": True,
                "max_age_hours": 24,
                "max_cache_size_mb": 100
            },
            "files": {
                "watchlist_path": "StockID_TWSE_TPEX.csv",
                "output_dir": "data/md/",
                "cache_dir": "cache/search/",
                "log_dir": "logs/search/"
            },
            "extraction": {
                "eps_years": ["2025", "2026", "2027"],
                "required_fields": ["symbol", "name"],
                "optional_fields": ["target_price", "analyst_count"]
            }
        }
    
    def _validate_config(self):
        """Validate configuration with multiple API key support"""
        errors = []
        
        # Count available API keys
        api_keys = []
        primary_key = self.config["api"]["google_api_key"]
        if primary_key and primary_key.strip():
            api_keys.append("Primary")
        
        for i in range(1, 7):
            key = self.config["api"][f"google_api_key{i}"]
            if key and key.strip():
                api_keys.append(f"Key{i}")
        
        # Count available CSE IDs
        cse_ids = []
        primary_cse = self.config["api"]["google_cse_id"]
        if primary_cse and primary_cse.strip():
            cse_ids.append("Primary")
        
        for i in range(1, 7):
            cse = self.config["api"][f"google_cse_id{i}"]
            if cse and cse.strip():
                cse_ids.append(f"CSE{i}")
        
        print(f"🔑 API Keys Found: {len(api_keys)} ({', '.join(api_keys) if api_keys else 'None'})")
        print(f"🔍 CSE IDs Found: {len(cse_ids)} ({', '.join(cse_ids) if cse_ids else 'None'})")
        print(f"🛡️  Content Validation: {'✅ Enabled' if self.config['validation']['enabled'] else '❌ Disabled'}")
        print(f"🚀 Comprehensive Search: {'✅ Enabled' if self.config['search']['comprehensive_search'] else '❌ Disabled'}")
        print(f"🔄 Key Rotation: {'✅ Enabled' if len(api_keys) > 1 else '❌ Single Key Only'}")
        
        if not api_keys:
            errors.append("No Google API keys found. At least GOOGLE_SEARCH_API_KEY is required.")
        
        if not cse_ids:
            errors.append("No Google CSE IDs found. At least GOOGLE_SEARCH_CSE_ID is required.")
        
        if errors:
            print("\n❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            print("\nPlease check your .env file. Example configuration:")
            print("  GOOGLE_SEARCH_API_KEY=your_primary_api_key")
            print("  GOOGLE_SEARCH_CSE_ID=your_primary_cse_id")
            print("  GOOGLE_SEARCH_API_KEY1=your_second_api_key")
            print("  GOOGLE_SEARCH_API_KEY2=your_third_api_key")
            print("  # ... up to GOOGLE_SEARCH_API_KEY6")
            sys.exit(1)
        
        if len(api_keys) > 1:
            print(f"🎉 Key rotation enabled with {len(api_keys)} keys!")
        else:
            print("⚠️ Single key mode - no rotation available")
    
    def get(self, key: str, default=None):
        """Get config value with dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

class SearchCLI:
    """v3.5.1 Search Group CLI with API Key Rotation Support"""
    
    def __init__(self):
        self.config = SearchConfig()
        self.api_manager = APIManager(self.config)
        # FIXED: Pass both api_manager and config to SearchEngine
        self.search_engine = SearchEngine(self.api_manager, self.config)
        self.logger = self._setup_logger()
        
        # Ensure directories exist
        self._ensure_directories()
        
        self.logger.info(f"Search CLI v{__version__} initialized with API key rotation support")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup enhanced logging with debug support"""
        log_dir = Path(self.config.get("files.log_dir"))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger('search_group')
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        # File handler
        log_file = log_dir / f"search_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler with enhanced formatting
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _ensure_directories(self):
        """Create necessary directories"""
        directories = [
            self.config.get("files.output_dir"),
            "data/csv/",
            self.config.get("files.cache_dir"),
            self.config.get("files.log_dir")
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _load_watchlist_csv(self) -> List[Dict[str, str]]:
        """Load StockID_TWSE_TPEX.csv with validation"""
        csv_path = self.config.get("files.watchlist_path")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"StockID_TWSE_TPEX.csv not found at {csv_path}")
        
        companies = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append({
                    'symbol': row['代號'].strip(),
                    'name': row['名稱'].strip(),
                    'search_completed': False
                })
        
        self.logger.info(f"Loaded {len(companies)} companies from watchlist")
        return companies
    
    def _generate_content_fingerprint(self, symbol: str, name: str, financial_data: Dict[str, Any]) -> str:
        """Generate pure content fingerprint - NO result index"""
        
        # Get stable content elements for fingerprint
        sources = financial_data.get('sources', [])
        if sources:
            source = sources[0]
            url = source.get('url', '')
            title = source.get('title', '')
            
            # Create fingerprint from truly stable content elements only
            fingerprint_elements = [
                symbol,                    # Stock symbol
                name,                     # Company name  
                url,                      # Source URL (the actual content source)
                title                     # Title (content identifier)
            ]
        else:
            # Fallback for no sources
            fingerprint_elements = [
                symbol,
                name,
                'no_source'
            ]
        
        # Join and hash stable elements only
        fingerprint_content = '|'.join(fingerprint_elements)
        content_hash = hashlib.md5(fingerprint_content.encode('utf-8')).hexdigest()[:8]
        
        return content_hash
    
    def _save_md_file_indexed(self, symbol: str, name: str, content: str, metadata: Dict, index: int) -> str:
        """Save search results with pure content-based filename and validation awareness"""
        
        # Generate pure content fingerprint (no result index)
        content_hash = self._generate_content_fingerprint(symbol, name, metadata)
        
        # Clean filename: just company + content hash
        filename = f"{symbol}_{name}_factset_{content_hash}.md"
        file_path = Path(self.config.get("files.output_dir")) / filename
        
        # Check validation status from metadata
        validation_info = metadata.get('content_validation', {})
        is_valid_content = validation_info.get('is_valid', True)
        quality_score = metadata.get('quality_score', 0)
        
        # Enhanced logging based on validation status and quality
        if file_path.exists():
            if is_valid_content:
                self.logger.info(f"📝 Updating VALID content: {filename} (Q:{quality_score}/10)")
            else:
                self.logger.warning(f"⚠️ Updating INVALID content: {filename} (Q:{quality_score}/10) - {validation_info.get('reason', 'unknown')}")
        else:
            if is_valid_content:
                self.logger.info(f"💾 Creating VALID content: {filename} (Q:{quality_score}/10)")
            else:
                self.logger.warning(f"⚠️ Creating INVALID content: {filename} (Q:{quality_score}/10) - {validation_info.get('reason', 'unknown')}")
        
        # Write the file (always overwrite for same content)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save MD file {filename}: {e}")
            return ""
    
    def _update_progress_multiple(self, symbol: str, filenames: List[str], results_data: List[Dict]):
        """Update search progress with key rotation tracking"""
        progress_file = Path("cache/search/progress.json")
        progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        progress = {}
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
            except:
                progress = {}
        
        # Calculate average quality score
        quality_scores = [data.get('quality_score', 0) for data in results_data]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Track content hashes from filenames
        content_hashes = []
        for filename in filenames:
            # Extract hash from new format: 2330_台積電_factset_7796efd2.md
            parts = filename.replace('.md', '').split('_')
            if len(parts) >= 4:
                content_hashes.append(parts[3])
        
        # Track comprehensive validation statistics
        validation_stats = {
            'valid_content': 0,
            'invalid_content': 0,
            'validation_reasons': [],
            'quality_scores_valid': [],
            'quality_scores_invalid': []
        }
        
        for data in results_data:
            validation_info = data.get('content_validation', {})
            quality_score = data.get('quality_score', 0)
            
            if validation_info.get('is_valid', True):
                validation_stats['valid_content'] += 1
                validation_stats['quality_scores_valid'].append(quality_score)
            else:
                validation_stats['invalid_content'] += 1
                validation_stats['quality_scores_invalid'].append(quality_score)
                validation_stats['validation_reasons'].append(validation_info.get('reason', 'Unknown'))
        
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
            'key_rotations_during_search': self.api_manager.stats.stats['key_rotations'],
            'api_keys_used': key_status['current_key_index'],
            'version': __version__
        }
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    
    def _is_already_processed(self, symbol: str) -> bool:
        """Check if company already has MD files"""
        output_dir = Path(self.config.get("files.output_dir"))
        pattern = f"{symbol}_*.md"
        existing_files = list(output_dir.glob(pattern))
        
        if len(existing_files) > 0:
            self.logger.debug(f"Found {len(existing_files)} existing files for {symbol}")
            return True
        
        return False
    
    def _record_failure(self, symbol: str, error: str):
        """Record search failure with key rotation context"""
        failures_file = Path("cache/search/failures.json")
        failures_file.parent.mkdir(parents=True, exist_ok=True)
        
        failures = {}
        if failures_file.exists():
            try:
                with open(failures_file, 'r', encoding='utf-8') as f:
                    failures = json.load(f)
            except:
                failures = {}
        
        # Get current key status
        key_status = self.api_manager.get_key_status()
        
        failures[symbol] = {
            'failed_at': datetime.now().isoformat(),
            'error': error,
            'key_status_at_failure': key_status,
            'version': __version__
        }
        
        with open(failures_file, 'w', encoding='utf-8') as f:
            json.dump(failures, f, indent=2, ensure_ascii=False)
    
    def validate_setup(self) -> bool:
        """Validate API keys and configuration with rotation support"""
        self.logger.info("Validating setup with key rotation support...")
        print("\n🔍 Validating Search Group Setup with API Key Rotation...")
        
        try:
            # Get key status first
            key_status = self.api_manager.get_key_status()
            print(f"🔑 API Key Status:")
            print(f"   📊 Total Keys: {key_status['total_keys']}")
            print(f"   ✅ Available Keys: {key_status['available_keys']}")
            print(f"   ❌ Exhausted Keys: {key_status['exhausted_keys']}")
            print(f"   🎯 Current Key: #{key_status['current_key_index']}")
            
            # Test API manager
            print("📡 Testing API connection with key rotation...")
            if not self.api_manager.validate_api_access():
                self.logger.error("API validation failed")
                print("❌ API validation failed")
                return False
            
            print("✅ API connection successful")
            
            # Show key details
            print("\n🔑 Key Details:")
            for key_detail in key_status['key_details']:
                status = "🟢 Active" if key_detail['is_current'] else ("🔴 Exhausted" if key_detail['is_exhausted'] else "🟡 Standby")
                print(f"   Key #{key_detail['key_number']}: {status} - {key_detail['calls_made']} calls, {key_detail['total_errors']} errors")
            
            # Check watchlist
            print("\n📋 Checking watchlist...")
            companies = self._load_watchlist_csv()
            if len(companies) == 0:
                self.logger.error("No companies in watchlist")
                print("❌ No companies in watchlist")
                return False
            
            print(f"✅ Found {len(companies)} companies in watchlist")
            
            # Check directories
            print("📁 Checking directories...")
            self._ensure_directories()
            print("✅ All directories created")
            
            self.logger.info("Setup validation passed with key rotation support")
            print(f"\n🎉 Setup validation passed! Ready for search with API key rotation.")
            print(f"🔄 Using pure content hash filenames (v{__version__})")
            print("🔗 Same content = same filename (no result index needed)")
            print("🚀 Comprehensive search enabled - all patterns will execute")
            print("🛡️  Content validation enabled - invalid content gets score 0")
            print("🔄 API key rotation enabled - automatic quota management")
            print("🛠️ Debug logging enabled - will show pattern execution details")
            return True
            
        except Exception as e:
            self.logger.error(f"Setup validation failed: {e}")
            print(f"❌ Setup validation failed: {e}")
            return False
    
    def cmd_search_company(self, symbol: str, result_count: str = '1', min_quality: int = None) -> bool:
        """Search specific company with key rotation support"""
        try:
            # Override config min quality if provided
            if min_quality is not None:
                self.config.config["quality"]["min_quality_threshold"] = min_quality
            
            # Find company in watchlist
            companies = self._load_watchlist_csv()
            company = next((c for c in companies if c['symbol'] == symbol), None)
            
            if not company:
                print(f"❌ Company {symbol} not found in watchlist")
                self.logger.error(f"Company {symbol} not found in watchlist")
                return False
            
            name = company['name']
            min_quality_threshold = self.config.get("quality.min_quality_threshold", 3)
            
            # Get initial key status
            key_status = self.api_manager.get_key_status()
            
            print(f"\n🔍 Comprehensive Search with Key Rotation: {symbol} {name}")
            print(f"📊 Saving {result_count} results, min quality: {min_quality_threshold}")
            print(f"🔑 Starting with API Key #{key_status['current_key_index']} ({key_status['available_keys']} available)")
            print(f"🚀 All search patterns will execute (no early stopping)")
            print(f"🛡️  Enhanced content validation enabled - detects wrong companies")
            print(f"⚠️  Invalid content (wrong companies) automatically gets score 0")
            
            self.logger.info(f"Starting comprehensive search with key rotation for {symbol} {name} (saving {result_count} results, min quality {min_quality_threshold})")
            
            # Search company and get multiple results
            search_results = self.search_engine.search_comprehensive(symbol, name, result_count, min_quality_threshold)
            
            if search_results and len(search_results) > 0:
                successful_files = []
                skipped_low_quality = 0
                skipped_invalid_content = 0
                updated_existing = 0
                
                for i, result_data in enumerate(search_results, 1):
                    quality_score = result_data.get('quality_score', 0)
                    validation_info = result_data.get('content_validation', {})
                    is_valid_content = validation_info.get('is_valid', True)
                    
                    # Check quality threshold
                    if quality_score < min_quality_threshold:
                        if not is_valid_content:
                            invalid_reason = validation_info.get('reason', 'Unknown validation issue')
                            print(f"❌ Result {i}: Quality {quality_score}/10 - INVALID CONTENT: {invalid_reason}")
                            skipped_invalid_content += 1
                        else:
                            print(f"⭐ Result {i}: Quality {quality_score}/10 - Skipped (below threshold {min_quality_threshold})")
                            skipped_low_quality += 1
                        
                        self.logger.info(f"Skipped result {i} for {symbol}: quality {quality_score} below threshold {min_quality_threshold}, valid={is_valid_content}")
                        continue
                    
                    # Generate MD content for this result
                    filename, md_content = self.search_engine.generate_md_file_with_md_date(result_data, i)
                    
                    # Save MD file with pure content hash filename
                    saved_filename = self._save_md_file_indexed(symbol, name, md_content, result_data, i)
                    
                    if saved_filename:
                        # Check if this filename already exists in our list (duplicate content)
                        if saved_filename in successful_files:
                            if is_valid_content:
                                print(f"🔄 Result {i}: Quality {quality_score}/10 - {saved_filename} (duplicate content merged)")
                            else:
                                print(f"⚠️ Result {i}: Quality {quality_score}/10 - {saved_filename} (INVALID content, duplicate merged)")
                            updated_existing += 1
                        else:
                            successful_files.append(saved_filename)
                            if is_valid_content:
                                print(f"✅ Result {i}: Quality {quality_score}/10 - {saved_filename}")
                            else:
                                invalid_reason = validation_info.get('reason', 'Unknown')
                                print(f"⚠️ Result {i}: Quality {quality_score}/10 - {saved_filename} (INVALID: {invalid_reason})")
                
                # Update progress with unique files only
                if successful_files:
                    high_quality_results = [r for r in search_results if r.get('quality_score', 0) >= min_quality_threshold]
                    self._update_progress_multiple(symbol, successful_files, high_quality_results)
                
                # Enhanced summary with key rotation stats
                total_found = len(search_results)
                total_processed = len([r for r in search_results if r.get('quality_score', 0) >= min_quality_threshold])
                unique_files = len(successful_files)
                
                # Get execution stats
                patterns_executed = getattr(self.search_engine, 'last_patterns_executed', 0)
                api_calls_made = getattr(self.search_engine, 'last_api_calls', 0)
                
                # Get final key status
                final_key_status = self.api_manager.get_key_status()
                key_rotations = self.api_manager.stats.stats['key_rotations']
                
                if unique_files > 0:
                    summary_parts = [f"Generated {unique_files} unique MD files"]
                    if total_processed > unique_files:
                        duplicates = total_processed - unique_files
                        summary_parts.append(f"({duplicates} duplicates merged)")
                    
                    skip_details = []
                    if skipped_low_quality > 0:
                        skip_details.append(f"{skipped_low_quality} low quality")
                    if skipped_invalid_content > 0:
                        skip_details.append(f"{skipped_invalid_content} invalid content")
                    
                    if skip_details:
                        summary_parts.append(f"(found {total_found}, skipped {' + '.join(skip_details)})")
                    else:
                        summary_parts.append(f"(found {total_found})")
                    
                    print(f"🎉 {symbol} completed - {' '.join(summary_parts)}")
                    print(f"📊 Search stats: {patterns_executed} patterns executed, {api_calls_made} API calls")
                    print(f"🔑 Key rotation: {key_rotations} rotations, ended with key #{final_key_status['current_key_index']}")
                    print(f"🛡️  Validation: {total_found - skipped_invalid_content} valid, {skipped_invalid_content} invalid content")
                    self.logger.info(f"✅ {symbol} completed - {unique_files} unique files from {total_found} results ({patterns_executed} patterns, {api_calls_made} API calls, {key_rotations} key rotations)")
                    return True
                else:
                    validation_msg = f", {skipped_invalid_content} invalid content" if skipped_invalid_content > 0 else ""
                    print(f"❌ {symbol} - found {total_found} results but all below quality threshold ({min_quality_threshold}){validation_msg}")
                    print(f"📊 Search stats: {patterns_executed} patterns executed, {api_calls_made} API calls")
                    print(f"🔑 Key rotation: {key_rotations} rotations, ended with key #{final_key_status['current_key_index']}")
                    print(f"💡 Suggestion: Try lower quality threshold (--min-quality 2 or 3)")
                    self.logger.warning(f"❌ {symbol} - {total_found} results found but all below quality threshold")
                    return False
            else:
                patterns_executed = getattr(self.search_engine, 'last_patterns_executed', 0)
                api_calls_made = getattr(self.search_engine, 'last_api_calls', 0)
                key_rotations = self.api_manager.stats.stats['key_rotations']
                final_key_status = self.api_manager.get_key_status()
                
                print(f"❌ {symbol} - no financial data found")
                print(f"📊 Search stats: {patterns_executed} patterns executed, {api_calls_made} API calls")
                print(f"🔑 Key rotation: {key_rotations} rotations, ended with key #{final_key_status['current_key_index']}")
                self.logger.warning(f"❌ {symbol} - no financial data found")
                return False
                
        except Exception as e:
            print(f"❌ Search company failed: {e}")
            self.logger.error(f"Search company failed: {e}")
            return False
    
    def cmd_search_batch(self, symbols: List[str], result_count: str = '1', min_quality: int = None) -> bool:
        """Search company batch with key rotation support"""
        key_status = self.api_manager.get_key_status()
        
        print(f"\n🔍 Comprehensive Batch Search with Key Rotation: {len(symbols)} companies")
        print(f"📊 Saving {result_count} results each, comprehensive pattern execution")
        print(f"🔑 Starting with API Key #{key_status['current_key_index']} ({key_status['available_keys']} available)")
        print(f"🛡️  Enhanced content validation enabled for all companies")
        self.logger.info(f"Starting comprehensive batch search with key rotation for {len(symbols)} companies")
        
        successful = 0
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
            if self.cmd_search_company(symbol, result_count, min_quality):
                successful += 1
        
        # Final key status
        final_key_status = self.api_manager.get_key_status()
        total_rotations = self.api_manager.stats.stats['key_rotations']
        
        print(f"\n📊 Batch completed: {successful}/{len(symbols)} successful")
        print(f"🔑 Total key rotations: {total_rotations}, final key: #{final_key_status['current_key_index']}")
        self.logger.info(f"Batch completed: {successful}/{len(symbols)} successful with {total_rotations} key rotations")
        return successful > 0
    
    def cmd_search_all(self, result_count: str = '1', min_quality: int = None) -> bool:
        """Search all companies with key rotation support"""
        try:
            companies = self._load_watchlist_csv()
            total = len(companies)
            key_status = self.api_manager.get_key_status()
            
            print(f"\n🚀 Comprehensive Search with Key Rotation: ALL {total} companies")
            print(f"📊 Saving {result_count} results each, all patterns execute")
            print(f"🔑 Starting with API Key #{key_status['current_key_index']} ({key_status['available_keys']} available)")
            print(f"🔄 Pure content hash filenames - no duplicate content files")
            print(f"🛡️  Enhanced content validation enabled - detects wrong companies")
            print(f"⚠️  Invalid content automatically gets score 0")
            print(f"🔄 Automatic key rotation on quota exceeded")
            
            self.logger.info(f"Starting comprehensive search with key rotation for {total} companies")
            
            successful = 0
            for i, company in enumerate(companies, 1):
                symbol = company['symbol']
                name = company['name']
                
                print(f"\n[{i}/{total}] 🔍 Comprehensive Search: {symbol} {name}...")
                self.logger.info(f"[{i}/{total}] Starting comprehensive search for {symbol} {name}...")
                
                try:
                    if self.cmd_search_company(symbol, result_count, min_quality):
                        successful += 1
                    
                except Exception as e:
                    print(f"❌ {symbol} failed: {e}")
                    self.logger.error(f"❌ {symbol} failed: {e}")
                    self._record_failure(symbol, str(e))
                
                # Progress update with key status
                if i % 10 == 0:
                    current_key_status = self.api_manager.get_key_status()
                    total_rotations = self.api_manager.stats.stats['key_rotations']
                    print(f"\n📊 Progress: {i}/{total} companies processed, {successful} successful")
                    print(f"🔑 Key status: #{current_key_status['current_key_index']} active, {total_rotations} rotations so far")
                    self.logger.info(f"Progress: {i}/{total} companies processed, {successful} successful, {total_rotations} key rotations")
            
            # Final summary
            final_key_status = self.api_manager.get_key_status()
            total_rotations = self.api_manager.stats.stats['key_rotations']
            
            print(f"\n🎉 Comprehensive search with key rotation completed! {successful}/{total} companies successful")
            print(f"🔑 Final key status: #{final_key_status['current_key_index']}, {total_rotations} total rotations")
            self.logger.info(f"Search completed: {successful}/{total} successful with {total_rotations} key rotations")
            return successful > 0
            
        except Exception as e:
            print(f"❌ Search all failed: {e}")
            self.logger.error(f"Search all failed: {e}")
            return False
    
    def cmd_search_resume(self, result_count: str = '1', min_quality: int = None) -> bool:
        """Resume interrupted search with key rotation support"""
        key_status = self.api_manager.get_key_status()
        
        print(f"\n🔄 Resuming comprehensive search with key rotation")
        print(f"📊 Saving {result_count} results each, all patterns execute")
        print(f"🔑 Current API Key: #{key_status['current_key_index']} ({key_status['available_keys']} available)")
        print(f"🛡️  Enhanced content validation enabled for all companies")
        self.logger.info(f"Resuming comprehensive search with key rotation")
        
        # Load progress to see what's already done
        progress_file = Path("cache/search/progress.json")
        completed = set()
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                completed = set(progress.keys())
                print(f"📋 Found {len(completed)} already completed companies")
                self.logger.info(f"Found {len(completed)} already completed companies")
            except:
                pass
        
        # Load companies and filter out completed ones
        companies = self._load_watchlist_csv()
        remaining = [c for c in companies if c['symbol'] not in completed]
        
        if not remaining:
            print("✅ All companies already completed")
            self.logger.info("All companies already completed")
            return True
        
        print(f"🚀 Resuming with {len(remaining)} remaining companies...")
        self.logger.info(f"Resuming with {len(remaining)} remaining companies...")
        
        # Process remaining companies
        successful = 0
        for i, company in enumerate(remaining, 1):
            symbol = company['symbol']
            name = company['name']
            
            print(f"\n[{i}/{len(remaining)}] 🔍 Comprehensive Search: {symbol} {name}...")
            self.logger.info(f"[{i}/{len(remaining)}] Starting comprehensive search for {symbol} {name}...")
            
            try:
                if self.cmd_search_company(symbol, result_count, min_quality):
                    successful += 1
                
            except Exception as e:
                print(f"❌ {symbol} failed: {e}")
                self.logger.error(f"❌ {symbol} failed: {e}")
                self._record_failure(symbol, str(e))
        
        # Final summary
        final_key_status = self.api_manager.get_key_status()
        total_rotations = self.api_manager.stats.stats['key_rotations']
        
        print(f"\n🎉 Resume with key rotation completed! {successful}/{len(remaining)} companies successful")
        print(f"🔑 Final key status: #{final_key_status['current_key_index']}, {total_rotations} total rotations")
        self.logger.info(f"Resume completed: {successful}/{len(remaining)} successful with {total_rotations} key rotations")
        return successful > 0
    
    def show_status(self):
        """Show current status with key rotation information"""
        print("\n📊 === Search Group Status with Key Rotation ===")
        self.logger.info("=== Search Group Status ===")
        print(f"🏷️  Version: {__version__} (Pure Content Hash + Comprehensive Search + Content Validation + Key Rotation)")
        self.logger.info(f"Version: {__version__}")
        
        # API and Key Status
        api_status = self.api_manager.get_api_status()
        status_emoji = {
            "ready": "🟢", 
            "operational": "🟡", 
            "quota_managed": "🟠", 
            "error_prone": "🔴", 
            "all_keys_exhausted": "💀"
        }.get(api_status, "❓")
        print(f"{status_emoji} API Status: {api_status}")
        self.logger.info(f"API Status: {api_status}")
        
        # Key rotation details
        key_status = self.api_manager.get_key_status()
        print(f"\n🔑 API Key Status:")
        print(f"   📊 Total Keys: {key_status['total_keys']}")
        print(f"   ✅ Available Keys: {key_status['available_keys']}")
        print(f"   ❌ Exhausted Keys: {key_status['exhausted_keys']}")
        print(f"   🎯 Current Key: #{key_status['current_key_index']}")
        
        # Individual key details
        print(f"\n🔑 Key Details:")
        for key_detail in key_status['key_details']:
            if key_detail['is_current']:
                status = "🟢 ACTIVE"
            elif key_detail['is_exhausted']:
                status = "🔴 EXHAUSTED"
            else:
                status = "🟡 STANDBY"
            
            print(f"   Key #{key_detail['key_number']}: {status}")
            print(f"      📞 Calls Made: {key_detail['calls_made']}")
            print(f"      ❌ Errors: {key_detail['total_errors']}")
            if key_detail['quota_exceeded_at']:
                print(f"      ⏰ Quota Exceeded: {key_detail['quota_exceeded_at']}")
            if key_detail['last_used']:
                print(f"      🕐 Last Used: {key_detail['last_used']}")
        
        # API statistics
        api_stats = self.api_manager.stats.get_summary()
        print(f"\n📞 API Statistics:")
        print(f"   📞 Total API Calls: {api_stats['api_calls']}")
        print(f"   💾 Cache Hit Rate: {api_stats['cache_hit_rate']}")
        print(f"   🔄 Key Rotations: {api_stats['key_rotations']}")
        print(f"   ✅ Success Rate: {api_stats['success_rate']}")
        
        # File counts
        output_dir = Path(self.config.get("files.output_dir"))
        if output_dir.exists():
            md_files = len(list(output_dir.glob("*.md")))
            print(f"   📄 MD Files Generated: {md_files}")
        
        # Progress with key rotation analysis
        progress_file = Path("cache/search/progress.json")
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                print(f"\n✅ Companies Completed: {len(progress)}")
                
                # Quality and validation statistics
                all_scores = []
                total_unique_files = 0
                total_patterns_executed = 0
                total_api_calls = 0
                total_key_rotations = 0
                total_valid_content = 0
                total_invalid_content = 0
                
                for company_data in progress.values():
                    scores = company_data.get('quality_scores', [])
                    all_scores.extend(scores)
                    total_unique_files += company_data.get('file_count', 0)
                    total_patterns_executed += company_data.get('total_patterns_executed', 0)
                    total_api_calls += company_data.get('total_api_calls', 0)
                    total_key_rotations += company_data.get('key_rotations_during_search', 0)
                    
                    validation_stats = company_data.get('validation_stats', {})
                    total_valid_content += validation_stats.get('valid_content', 0)
                    total_invalid_content += validation_stats.get('invalid_content', 0)
                
                if all_scores:
                    avg_score = sum(all_scores) / len(all_scores)
                    print(f"⭐ Average Quality Score: {avg_score:.1f}/10 (with validation filtering)")
                
                print(f"📁 Total Unique Files: {total_unique_files}")
                print(f"🎯 Pure Content Hash Efficiency: 100% - no duplicates by design")
                
                if total_patterns_executed > 0:
                    avg_patterns = total_patterns_executed / len(progress)
                    avg_api_calls = total_api_calls / len(progress)
                    avg_rotations = total_key_rotations / len(progress)
                    print(f"📍 Avg Patterns Executed: {avg_patterns:.1f}/company")
                    print(f"📡 Avg API Calls: {avg_api_calls:.1f}/company")
                    print(f"🔄 Avg Key Rotations: {avg_rotations:.1f}/company")
                
                # Enhanced validation statistics
                if total_valid_content + total_invalid_content > 0:
                    validation_rate = (total_valid_content / (total_valid_content + total_invalid_content)) * 100
                    print(f"🛡️  Content Validation: {validation_rate:.1f}% valid content")
                    print(f"✅ Valid Content: {total_valid_content}")
                    print(f"❌ Invalid Content: {total_invalid_content}")
                    
            except Exception as e:
                self.logger.warning(f"Error reading progress: {e}")
        
        # Watchlist info
        try:
            companies = self._load_watchlist_csv()
            print(f"\n📋 Total Companies in Watchlist: {len(companies)}")
        except:
            pass
    
    def clean_cache(self):
        """Clean temporary files"""
        cache_dir = Path(self.config.get("files.cache_dir"))
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            print("🧹 Cache cleaned")
            self.logger.info("Cache cleaned")
    
    def reset_all(self):
        """Reset all data"""
        # Clean cache
        self.clean_cache()
        
        # Remove output files
        output_dir = Path(self.config.get("files.output_dir"))
        if output_dir.exists():
            md_count = 0
            for file in output_dir.glob("*.md"):
                file.unlink()
                md_count += 1
            print(f"🗑️  Removed {md_count} output files")
            self.logger.info(f"Removed {md_count} output files")
        
        print("🔄 All data reset")
        self.logger.info("All data reset")

def create_argument_parser():
    """Create CLI argument parser with key rotation info"""
    parser = argparse.ArgumentParser(
        description=f"FactSet Search Group v{__version__} (Comprehensive Search + Pure Content Hash + Content Validation + API Key Rotation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search_cli.py search --all                         # Search all companies with key rotation
  python search_cli.py search --all --count 3               # Search all companies (3 results each)
  python search_cli.py search --company 2354                # Search specific company
  python search_cli.py search --company 2354 --count all    # Search specific company (all results)
  python search_cli.py search --batch 2330,2454,2354 --count 2  # Search batch with rotation
  python search_cli.py search --resume --count all          # Resume interrupted search
  
  python search_cli.py validate                             # Validate setup and key status
  python search_cli.py status                               # Show progress with key rotation info
  python search_cli.py clean                                # Clean cache

API KEY ROTATION FEATURES:
  - Automatic rotation on quota exceeded (429 errors)
  - Support for up to 7 API keys (GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_API_KEY1-6)
  - Intelligent key status tracking and monitoring
  - Enhanced error handling and recovery
  - Comprehensive key usage statistics
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search commands
    search_parser = subparsers.add_parser('search', help='Comprehensive search operations with key rotation')
    search_group = search_parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument('--all', action='store_true', help='Search all companies with key rotation')
    search_group.add_argument('--company', help='Search specific company by symbol')
    search_group.add_argument('--batch', help='Search batch (comma-separated symbols)')
    search_group.add_argument('--resume', action='store_true', help='Resume interrupted search')
    
    search_parser.add_argument('--count', default='1', 
                             help='Number of results to save (1, 2, 3, ... or "all")')
    
    search_parser.add_argument('--min-quality', type=int, default=None,
                             help='Minimum quality score to save (0-10, default: 3)')
    
    # Utility commands
    subparsers.add_parser('validate', help='Validate setup and key status')
    subparsers.add_parser('status', help='Show status with key rotation information')
    subparsers.add_parser('clean', help='Clean cache')
    subparsers.add_parser('reset', help='Reset all data')
    
    return parser

def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        cli = SearchCLI()
        
        if args.command == 'search':
            # Parse count parameter
            result_count = getattr(args, 'count', '1')
            min_quality = getattr(args, 'min_quality', None)
            
            if args.all:
                success = cli.cmd_search_all(result_count, min_quality)
            elif args.company:
                success = cli.cmd_search_company(args.company, result_count, min_quality)
            elif args.batch:
                symbols = [s.strip() for s in args.batch.split(',')]
                success = cli.cmd_search_batch(symbols, result_count, min_quality)
            elif args.resume:
                success = cli.cmd_search_resume(result_count, min_quality)
            else:
                parser.print_help()
                return 1
            
            return 0 if success else 1
            
        elif args.command == 'validate':
            success = cli.validate_setup()
            return 0 if success else 1
            
        elif args.command == 'status':
            cli.show_status()
            return 0
            
        elif args.command == 'clean':
            cli.clean_cache()
            return 0
            
        elif args.command == 'reset':
            cli.reset_all()
            return 0
            
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Search interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())