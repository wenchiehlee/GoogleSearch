#!/usr/bin/env python3
"""
search_cli.py - Search Group CLI Interface (v3.5.0) - FIXED VERSION

Version: 3.5.0
Date: 2025-06-28
Author: FactSet Pipeline v3.5.0 - Modular Search Group

FIXES:
- Fixed method signatures to properly handle min_quality parameter
- All search methods now accept optional min_quality parameter
- Properly override config min_quality_threshold when specified
"""

import os
import sys
import csv
import json
import time
import random
import string
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
        print("⚠️  No .env file found")

# Version Information
__version__ = "3.5.0"
__date__ = "2025-06-28"

# Import search group components
try:
    from search_engine import SearchEngine
    from api_manager import APIManager
except ImportError as e:
    print(f"Error importing search components: {e}")
    print("Make sure search_engine.py and api_manager.py are in the same directory")
    sys.exit(1)

class SearchConfig:
    """Configuration management for search group"""
    
    def __init__(self):
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load search configuration"""
        return {
            "version": "3.5.0",
            "search": {
                "rate_limit_delay": float(os.getenv("SEARCH_RATE_LIMIT_PER_SECOND", "1.0")),
                "daily_quota": int(os.getenv("SEARCH_DAILY_QUOTA", "100")),
                "num_results_per_query": 10,
                "date_restrict": "y1",
                "language": "lang_zh-TW|lang_en",
                "safe_search": "off",
                "backoff_multiplier": 2.0,
                "max_backoff_seconds": 300
            },
            "api": {
                "google_api_key": os.getenv("GOOGLE_SEARCH_API_KEY"),
                "google_cse_id": os.getenv("GOOGLE_SEARCH_CSE_ID")
            },
            "quality": {
                "min_relevance_score": 3,
                "require_factset_content": False,
                "min_content_length": 100,
                "min_quality_threshold": int(os.getenv("MIN_QUALITY_THRESHOLD", "5"))
            },
            "caching": {
                "enabled": True,
                "max_age_hours": 24,
                "max_cache_size_mb": 100
            },
            "files": {
                "watchlist_path": "觀察名單.csv",
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
        """Validate configuration"""
        errors = []
        
        api_key = self.config["api"]["google_api_key"]
        cse_id = self.config["api"]["google_cse_id"]
        
        print(f"🔑 API Key: {'✅ Found' if api_key else '❌ Missing'}")
        print(f"🔍 CSE ID: {'✅ Found' if cse_id else '❌ Missing'}")
        
        if not api_key:
            errors.append("GOOGLE_SEARCH_API_KEY not found in environment")
        
        if not cse_id:
            errors.append("GOOGLE_SEARCH_CSE_ID not found in environment")
        
        if errors:
            print("\n❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            print("\nPlease check your .env file or set environment variables:")
            print("  export GOOGLE_SEARCH_API_KEY=your_api_key")
            print("  export GOOGLE_SEARCH_CSE_ID=your_cse_id")
            sys.exit(1)
    
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
    """v3.5.0 Search Group CLI - Simplified Command Interface"""
    
    def __init__(self):
        self.config = SearchConfig()
        self.api_manager = APIManager(self.config)
        self.search_engine = SearchEngine(self.api_manager)
        self.logger = self._setup_logger()
        
        # Ensure directories exist
        self._ensure_directories()
        
        self.logger.info(f"Search CLI v{__version__} initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup simple logging"""
        log_dir = Path(self.config.get("files.log_dir"))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger('search_group')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # File handler
        log_file = log_dir / f"search_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
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
        """Load 觀察名單.csv with validation"""
        csv_path = self.config.get("files.watchlist_path")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"觀察名單.csv not found at {csv_path}")
        
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
    
    def _save_md_file_indexed(self, symbol: str, name: str, content: str, metadata: Dict, index: int) -> str:
        """Save search results as MD file with index"""
        timestamp = datetime.now().strftime('%m%d_%H%M')
        file_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        filename = f"{symbol}_{name}_factset_{file_id}_{timestamp}_{index:03d}.md"
        
        file_path = Path(self.config.get("files.output_dir")) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Saved MD file: {filename}")
        return filename
    
    def _update_progress_multiple(self, symbol: str, filenames: List[str], results_data: List[Dict]):
        """Update search progress for multiple files"""
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
        
        progress[symbol] = {
            'completed_at': datetime.now().isoformat(),
            'filenames': filenames,
            'file_count': len(filenames),
            'quality_scores': quality_scores,
            'avg_quality_score': round(avg_quality, 1)
        }
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    
    def _is_already_processed(self, symbol: str) -> bool:
        """Check if company already has MD files"""
        output_dir = Path(self.config.get("files.output_dir"))
        pattern = f"{symbol}_*.md"
        existing_files = list(output_dir.glob(pattern))
        return len(existing_files) > 0
    
    def _record_failure(self, symbol: str, error: str):
        """Record search failure"""
        failures_file = Path("cache/search/failures.json")
        failures_file.parent.mkdir(parents=True, exist_ok=True)
        
        failures = {}
        if failures_file.exists():
            try:
                with open(failures_file, 'r', encoding='utf-8') as f:
                    failures = json.load(f)
            except:
                failures = {}
        
        failures[symbol] = {
            'failed_at': datetime.now().isoformat(),
            'error': error
        }
        
        with open(failures_file, 'w', encoding='utf-8') as f:
            json.dump(failures, f, indent=2, ensure_ascii=False)
    
    def validate_setup(self) -> bool:
        """Validate API keys and configuration"""
        self.logger.info("Validating setup...")
        print("\n🔍 Validating Search Group Setup...")
        
        try:
            # Test API manager
            print("📡 Testing API connection...")
            if not self.api_manager.validate_api_access():
                self.logger.error("API validation failed")
                print("❌ API validation failed")
                return False
            
            print("✅ API connection successful")
            
            # Check watchlist
            print("📋 Checking watchlist...")
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
            
            self.logger.info("Setup validation passed")
            print("\n🎉 Setup validation passed! Ready to search.")
            return True
            
        except Exception as e:
            self.logger.error(f"Setup validation failed: {e}")
            print(f"❌ Setup validation failed: {e}")
            return False
    
    def cmd_search_company(self, symbol: str, result_count: str = '1', min_quality: int = None) -> bool:
        """Search specific company"""
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
            print(f"\n🔍 Searching {symbol} {name} (saving {result_count} results)...")
            self.logger.info(f"Searching {symbol} {name} (saving {result_count} results)...")
            
            # Search company and get multiple results
            search_results = self.search_engine.search_company_multiple(symbol, name, result_count)
            
            if search_results and len(search_results) > 0:
                successful_files = []
                skipped_low_quality = 0
                min_quality_threshold = self.config.get("quality.min_quality_threshold", 5)
                
                for i, result_data in enumerate(search_results, 1):
                    quality_score = result_data.get('quality_score', 0)
                    
                    # Check quality threshold
                    if quality_score < min_quality_threshold:
                        print(f"⏭️  Result {i}: Quality {quality_score}/10 - Skipped (below threshold {min_quality_threshold})")
                        self.logger.info(f"Skipped result {i} for {symbol}: quality {quality_score} below threshold {min_quality_threshold}")
                        skipped_low_quality += 1
                        continue
                    
                    # Generate MD content for this result
                    md_content = self.search_engine.generate_md_content(
                        symbol, name, result_data, {}, result_index=i
                    )
                    
                    # Save MD file with index
                    filename = self._save_md_file_indexed(symbol, name, md_content, result_data, i)
                    successful_files.append(filename)
                    
                    print(f"✅ Result {i}: Quality {quality_score}/10 - {filename}")
                
                # Update progress with all files
                if successful_files:
                    high_quality_results = [r for r in search_results if r.get('quality_score', 0) >= min_quality_threshold]
                    self._update_progress_multiple(symbol, successful_files, high_quality_results)
                
                # Summary
                total_found = len(search_results)
                total_saved = len(successful_files)
                
                if total_saved > 0:
                    print(f"🎉 {symbol} completed - Generated {total_saved} MD files (found {total_found}, skipped {skipped_low_quality} low quality)")
                    self.logger.info(f"✅ {symbol} completed - saved {total_saved}/{total_found} files (skipped {skipped_low_quality} low quality)")
                    return True
                else:
                    print(f"❌ {symbol} - found {total_found} results but all below quality threshold ({min_quality_threshold})")
                    self.logger.warning(f"❌ {symbol} - {total_found} results found but all below quality threshold")
                    return False
            else:
                print(f"❌ {symbol} - no financial data found")
                self.logger.warning(f"❌ {symbol} - no financial data found")
                return False
                
        except Exception as e:
            print(f"❌ Search company failed: {e}")
            self.logger.error(f"Search company failed: {e}")
            return False
    
    def cmd_search_batch(self, symbols: List[str], result_count: str = '1', min_quality: int = None) -> bool:
        """Search company batch"""
        print(f"\n🔍 Searching batch of {len(symbols)} companies (saving {result_count} results each)...")
        self.logger.info(f"Searching batch of {len(symbols)} companies (saving {result_count} results each)...")
        
        successful = 0
        for symbol in symbols:
            if self.cmd_search_company(symbol, result_count, min_quality):
                successful += 1
        
        print(f"\n📊 Batch completed: {successful}/{len(symbols)} successful")
        self.logger.info(f"Batch completed: {successful}/{len(symbols)} successful")
        return successful > 0
    
    def cmd_search_all(self, result_count: str = '1', min_quality: int = None) -> bool:
        """Search all companies in watchlist"""
        try:
            companies = self._load_watchlist_csv()
            total = len(companies)
            
            self.logger.info(f"Starting search for {total} companies (saving {result_count} results each)...")
            print(f"\n🚀 Starting search for {total} companies (saving {result_count} results each)...")
            
            successful = 0
            for i, company in enumerate(companies, 1):
                symbol = company['symbol']
                name = company['name']
                
                print(f"\n[{i}/{total}] 🔍 Searching {symbol} {name}...")
                self.logger.info(f"[{i}/{total}] Searching {symbol} {name}...")
                
                try:
                    # Check if already processed
                    if self._is_already_processed(symbol):
                        print(f"⏭️  Skipping {symbol} - already processed")
                        self.logger.info(f"Skipping {symbol} - already processed")
                        continue
                    
                    # Search company with multiple results
                    if self.cmd_search_company(symbol, result_count, min_quality):
                        successful += 1
                    
                except Exception as e:
                    print(f"❌ {symbol} failed: {e}")
                    self.logger.error(f"❌ {symbol} failed: {e}")
                    self._record_failure(symbol, str(e))
                
                # Progress update
                if i % 10 == 0:
                    print(f"\n📊 Progress: {i}/{total} companies processed, {successful} successful")
                    self.logger.info(f"Progress: {i}/{total} companies processed, {successful} successful")
            
            print(f"\n🎉 Search completed! {successful}/{total} companies successful")
            self.logger.info(f"🎉 Search completed! {successful}/{total} companies successful")
            return successful > 0
            
        except Exception as e:
            print(f"❌ Search all failed: {e}")
            self.logger.error(f"Search all failed: {e}")
            return False
    
    def cmd_search_resume(self, result_count: str = '1', min_quality: int = None) -> bool:
        """Resume interrupted search"""
        print(f"\n🔄 Resuming search from where it left off (saving {result_count} results each)...")
        self.logger.info(f"Resuming search from where it left off (saving {result_count} results each)...")
        
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
            
            print(f"\n[{i}/{len(remaining)}] 🔍 Searching {symbol} {name}...")
            self.logger.info(f"[{i}/{len(remaining)}] Searching {symbol} {name}...")
            
            try:
                # Search company with multiple results
                if self.cmd_search_company(symbol, result_count, min_quality):
                    successful += 1
                
            except Exception as e:
                print(f"❌ {symbol} failed: {e}")
                self.logger.error(f"❌ {symbol} failed: {e}")
                self._record_failure(symbol, str(e))
        
        print(f"\n🎉 Resume completed! {successful}/{len(remaining)} companies successful")
        self.logger.info(f"🎉 Resume completed! {successful}/{len(remaining)} companies successful")
        return successful > 0
    
    def show_status(self):
        """Show current status"""
        print("\n📊 === Search Group Status ===")
        self.logger.info("=== Search Group Status ===")
        print(f"🏷️  Version: {__version__}")
        self.logger.info(f"Version: {__version__}")
        
        # API status
        api_status = self.api_manager.get_api_status()
        status_emoji = {"ready": "🟢", "operational": "🟡", "error_prone": "🟠", "quota_exceeded": "🔴"}.get(api_status, "❓")
        print(f"{status_emoji} API Status: {api_status}")
        self.logger.info(f"API Status: {api_status}")
        
        # API statistics
        api_stats = self.api_manager.stats.get_summary()
        print(f"📞 API Calls: {api_stats['api_calls']}")
        print(f"💾 Cache Hit Rate: {api_stats['cache_hit_rate']}")
        self.logger.info(f"API Calls: {api_stats['api_calls']}")
        self.logger.info(f"Cache Hit Rate: {api_stats['cache_hit_rate']}")
        
        # File counts
        output_dir = Path(self.config.get("files.output_dir"))
        if output_dir.exists():
            md_files = len(list(output_dir.glob("*.md")))
            print(f"📄 MD Files Generated: {md_files}")
            self.logger.info(f"MD Files Generated: {md_files}")
        
        # Progress
        progress_file = Path("cache/search/progress.json")
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                print(f"✅ Companies Completed: {len(progress)}")
                self.logger.info(f"Companies Completed: {len(progress)}")
                
                # Quality statistics
                scores = [p.get('quality_score', 0) for p in progress.values()]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    print(f"⭐ Average Quality Score: {avg_score:.1f}/10")
                    self.logger.info(f"Average Quality Score: {avg_score:.1f}/10")
            except:
                pass
        
        # Watchlist info
        try:
            companies = self._load_watchlist_csv()
            print(f"📋 Total Companies in Watchlist: {len(companies)}")
            self.logger.info(f"Total Companies in Watchlist: {len(companies)}")
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
            for file in output_dir.glob("*.md"):
                file.unlink()
            print("🗑️  Output files removed")
            self.logger.info("Output files removed")
        
        print("🔄 All data reset")
        self.logger.info("All data reset")

def create_argument_parser():
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        description=f"FactSet Search Group v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search_cli.py search --all                         # Search all companies (1 result each)
  python search_cli.py search --all --count 3               # Search all companies (3 results each)
  python search_cli.py search --company 2330                # Search specific company (1 result)
  python search_cli.py search --company 2330 --count all    # Search specific company (all results)
  python search_cli.py search --batch 2330,2454,6505 --count 2  # Search batch (2 results each)
  python search_cli.py search --resume --count all          # Resume interrupted search (all results)
  
  python search_cli.py validate                             # Validate setup
  python search_cli.py status                               # Show progress
  python search_cli.py clean                                # Clean cache
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search commands
    search_parser = subparsers.add_parser('search', help='Search operations')
    search_group = search_parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument('--all', action='store_true', help='Search all companies')
    search_group.add_argument('--company', help='Search specific company by symbol')
    search_group.add_argument('--batch', help='Search batch (comma-separated symbols)')
    search_group.add_argument('--resume', action='store_true', help='Resume interrupted search')
    
    # Add count parameter for controlling number of results
    search_parser.add_argument('--count', default='1', 
                             help='Number of results to save (1, 2, 3, ... or "all")')
    
    # Add quality threshold parameter
    search_parser.add_argument('--min-quality', type=int, default=None,
                             help='Minimum quality score to save (0-10, default: 5)')
    
    # Utility commands
    subparsers.add_parser('validate', help='Validate setup')
    subparsers.add_parser('status', help='Show status')
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
        print("\n⚠️  Search interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())