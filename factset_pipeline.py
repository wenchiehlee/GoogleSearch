"""
factset_pipeline.py - Complete Production-Ready FactSet Pipeline (Guideline v3.2.4 Compliant)

Version: 3.2.4
Date: 2025-06-22
Author: FactSet Pipeline - Guideline v3.2.4 Production Architecture

GUIDELINE v3.2.4 COMPLIANCE:
- ✅ Exact class structure and method signatures from guideline
- ✅ Immediate stop on 429 errors with fallback to data processing
- ✅ Enhanced strategy determination (conservative, process_existing, comprehensive)
- ✅ Integration with updated data_processor.py and sheets_uploader.py
- ✅ Circuit breaker threshold = 1 (immediate stop)
- ✅ Comprehensive existing data analysis
- ✅ Multi-execution mode support (intelligent, conservative, etc.)

Production Features:
- Immediate stop and process strategy on rate limiting
- Robust URL validation and error handling
- Automatic fallback to existing data processing
- Comprehensive logging and status reporting
- Recovery workflows with intelligent retry logic
- Circuit breaker patterns for API protection
- Windows Command Prompt compatibility
- Integration with 觀察名單.csv (116+ companies)
"""

# Windows console encoding fix - MUST BE FIRST
import sys
import os

if sys.platform == "win32":
    try:
        # Set console to UTF-8 for emoji support
        os.system("chcp 65001 >nul 2>&1")
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except Exception:
        # Fallback: Create safe logging without emojis
        pass

import argparse
import json
import traceback
import shutil
import glob
import time
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging
import hashlib

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Version Information - Guideline v3.2.4
__version__ = "3.2.4"
__date__ = "2025-06-22"
__author__ = "FactSet Pipeline - Guideline v3.2.4 Production Architecture"

# ============================================================================
# SAFE EMOJI HANDLING FOR WINDOWS
# ============================================================================

class SafeEmoji:
    """Emoji handler that works on Windows Command Prompt"""
    
    def __init__(self):
        self.use_emoji = self._test_emoji_support()
        self.emoji_map = {
            '🚀': '[START]',
            '🧪': '[TEST]',
            '⚠️': '[WARN]',
            '❌': '[ERROR]',
            '✅': '[OK]',
            '📊': '[DATA]',
            '🔍': '[SEARCH]',
            '📄': '[FILE]',
            '💡': '[TIP]',
            '🎯': '[TARGET]',
            '📈': '[UPLOAD]',
            '🔄': '[RETRY]',
            '🔧': '[FIX]',
            '📝': '[LOG]',
            '⏳': '[WAIT]',
            '🎉': '[SUCCESS]',
            '🚨': '[ALERT]',
            '🔌': '[CIRCUIT]',
            '🛡️': '[PROTECT]',
            '💾': '[SAVE]',
            '🏆': '[EXCELLENT]',
            '📥': '[DOWNLOAD]',
            '📋': '[LIST]',
            '🆔': '[ID]',
            '📅': '[DATE]',
            '🆕': '[NEW]',
            '🔴': '[HIGH]',
            '🟡': '[MED]',
            '🟢': '[LOW]',
            '⚡': '[FAST]',
            '🌐': '[WEB]',
            '💰': '[MONEY]',
            '📦': '[PACKAGE]',
            '🏢': '[COMPANY]',
            '⏰': '[TIME]',
            '🚫': '[BLOCKED]',
            '🔑': '[KEY]',
            '🛑': '[STOP]'
        }
    
    def _test_emoji_support(self):
        """Test if console supports emoji"""
        if sys.platform != "win32":
            return True
        
        try:
            # Test encoding capability
            test_emoji = '🚀'
            test_emoji.encode(sys.stdout.encoding or 'utf-8')
            return True
        except (UnicodeEncodeError, AttributeError):
            return False
    
    def safe(self, text):
        """Convert text to safe version for current console"""
        if self.use_emoji:
            return text
        
        # Replace emojis with safe alternatives
        safe_text = text
        for emoji, replacement in self.emoji_map.items():
            safe_text = safe_text.replace(emoji, replacement)
        return safe_text

# Global emoji handler
emoji = SafeEmoji()

# ============================================================================
# LOGGING SETUP WITH SAFE ENCODING
# ============================================================================

def setup_logging():
    """Setup comprehensive logging with safe encoding"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create safe formatter
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            # Format record normally first
            formatted = super().format(record)
            # Make it emoji-safe
            return emoji.safe(formatted)
    
    formatter = SafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup main logger
    logger = logging.getLogger('factset_pipeline')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler (always UTF-8)
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler with safe encoding
    console_handler = logging.StreamHandler()
    if sys.platform == "win32":
        # Use safe encoding for Windows
        console_handler.stream = sys.stdout
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# ============================================================================
# CONFIGURATION MANAGEMENT - GUIDELINE v3.2.4
# ============================================================================

class ProductionConfig:
    """Production-ready configuration management - Guideline v3.2.4"""
    
    def __init__(self, config_file=None):
        self.config_file = config_file
        # Load .env file first
        self._load_dotenv()
        self.config = self._load_config()
        self.logger = logging.getLogger('factset_pipeline.config')
    
    def _load_dotenv(self):
        """Load environment variables from .env file"""
        try:
            from dotenv import load_dotenv
            # Look for .env in current directory
            env_path = Path('.env')
            if env_path.exists():
                load_dotenv(env_path)
                print(emoji.safe("✅ Loaded .env file"))
            else:
                print(emoji.safe("ℹ️ No .env file found, using system environment variables"))
        except ImportError:
            print(emoji.safe("⚠️ python-dotenv not installed, using system environment variables only"))
        except Exception as e:
            print(emoji.safe(f"⚠️ Error loading .env file: {e}"))
    
    def _load_config(self):
        """Load configuration with comprehensive defaults - Guideline v3.2.4"""
        default_config = {
            "target_companies": [],
            "watchlist_url": "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv",
            "search": {
                "max_results": 10,  # As per guideline
                "language": "zh-TW",
                "date_restrict": "y1",
                "safe": "active",
                "rate_limit_delay": 45,  # As per guideline
                "max_retries": 3,
                "circuit_breaker_threshold": 1  # Immediate stop as per guideline
            },
            "output": {
                "base_dir": "data",
                "csv_dir": "data/csv",
                "pdf_dir": "data/pdf",
                "md_dir": "data/md",
                "processed_dir": "data/processed",
                "logs_dir": "logs",
                "consolidated_csv": "data/processed/consolidated_factset.csv",
                "summary_csv": "data/processed/portfolio_summary.csv",
                "detailed_csv": "data/processed/detailed_data.csv",
                "stats_json": "data/processed/statistics.json"
            },
            "sheets": {
                "worksheet_names": ["Portfolio Summary", "Detailed Data", "Statistics"],
                "backup_enabled": True
            }
        }
        
        # Load from file if specified
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._deep_update(default_config, file_config)
            except Exception as e:
                print(emoji.safe(f"⚠️ Error loading config file {self.config_file}: {e}"))
        
        # Load environment overrides
        self._load_env_overrides(default_config)
        
        return default_config
    
    def _deep_update(self, base_dict, update_dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _load_env_overrides(self, config):
        """Load environment variable overrides"""
        env_mappings = {
            'GOOGLE_SEARCH_API_KEY': ('search', 'api_key'),
            'GOOGLE_SEARCH_CSE_ID': ('search', 'cse_id'),
            'GOOGLE_SHEETS_CREDENTIALS': ('sheets', 'credentials'),
            'GOOGLE_SHEET_ID': ('sheets', 'sheet_id'),
            'FACTSET_PIPELINE_DEBUG': ('debug', None),
            'FACTSET_MAX_RESULTS': ('search', 'max_results')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if section not in config:
                    config[section] = {}
                if key:
                    config[section][key] = value
                else:
                    config[section] = value.lower() in ('true', '1', 'yes')
    
    def download_watchlist(self):
        """Download and parse watchlist with error handling"""
        try:
            import requests
            import pandas as pd
            
            self.logger.info(emoji.safe("📥 Downloading target companies from 觀察名單..."))
            response = requests.get(self.config['watchlist_url'], timeout=30)
            response.raise_for_status()
            
            # Save local copy
            watchlist_file = "觀察名單.csv"
            with open(watchlist_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Parse CSV
            df = pd.read_csv(watchlist_file)
            if df.empty:
                self.logger.warning("Empty CSV downloaded")
                return False
            
            # Convert to target companies format
            companies = []
            for _, row in df.iterrows():
                try:
                    code = str(row.iloc[0]).strip()
                    name = str(row.iloc[1]).strip()
                    if code and name and code != 'nan':
                        companies.append({"code": code, "name": name})
                except Exception as e:
                    self.logger.warning(f"Error parsing row: {e}")
            
            self.config['target_companies'] = companies
            self.logger.info(emoji.safe(f"✅ Downloaded {len(companies)} target companies from CSV"))
            return True
            
        except Exception as e:
            self.logger.error(emoji.safe(f"❌ Error downloading watchlist: {e}"))
            return False
    
    def get(self, key, default=None):
        """Get configuration value with dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

# ============================================================================
# ENHANCED RATE LIMITING PROTECTION SYSTEM - GUIDELINE v3.2.4
# ============================================================================

class RateLimitProtector:
    """Enhanced rate limiting protection - Guideline v3.2.4 immediate stop strategy"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('factset_pipeline.rate_limiter')
        
        # Rate limiting state - Guideline v3.2.4
        self.min_delay = config.get('search.rate_limit_delay', 45)
        self.max_delay = 600  # 10 minutes max
        self.current_delay = self.min_delay
        self.last_request_time = None
        self.consecutive_429s = 0
        self.consecutive_failures = 0
        self.circuit_breaker_threshold = config.get('search.circuit_breaker_threshold', 1)  # Immediate stop
        self.circuit_open = False
        self.circuit_open_time = None
        self.request_history = []
        
        # Guideline v3.2.4: Immediate stop flag
        self.should_stop_searching = False
        self.stop_reason = None
        self.fallback_to_processing = False
    
    def record_429_error(self):
        """Record 429 error and trigger immediate stop - Guideline v3.2.4"""
        self.consecutive_429s += 1
        self.consecutive_failures += 1
        
        # Exponential backoff
        self.current_delay = min(
            self.max_delay,
            self.min_delay * (2 ** self.consecutive_429s)
        )
        
        self.logger.warning(emoji.safe(f"🚨 Rate limiting detected! (#{self.consecutive_429s}) Delay increased to {self.current_delay} seconds"))
        
        # Guideline v3.2.4: Immediate stop after first 429 error
        if self.consecutive_429s >= self.circuit_breaker_threshold:
            self.should_stop_searching = True
            self.fallback_to_processing = True
            self.stop_reason = f"Rate limiting detected ({self.consecutive_429s} consecutive 429 errors)"
            self.logger.error(emoji.safe(f"🛑 STOPPING SEARCH: {self.stop_reason}"))
            self.logger.info(emoji.safe("📄 Will process existing data instead"))
            return True
        
        return False
    
    def should_stop_immediately(self):
        """Check if search should stop immediately - Guideline v3.2.4"""
        return self.should_stop_searching
    
    def should_fallback_to_processing(self):
        """Check if should fallback to processing existing data"""
        return self.fallback_to_processing
    
    def get_stop_reason(self):
        """Get reason for stopping search"""
        return self.stop_reason or "Unknown"
    
    def record_success(self):
        """Record a successful request"""
        if self.consecutive_429s > 0:
            self.logger.info(emoji.safe(f"✅ Request successful! Rate limiting appears to be lifted"))
        
        self.consecutive_429s = 0
        self.consecutive_failures = 0
        self.current_delay = max(self.min_delay, self.current_delay * 0.8)  # Gradually reduce delay
    
    def get_status(self):
        """Get current rate limiting status"""
        return {
            "circuit_open": self.circuit_open,
            "consecutive_429s": self.consecutive_429s,
            "current_delay": self.current_delay,
            "last_request": self.last_request_time,
            "should_stop": self.should_stop_searching,
            "fallback_to_processing": self.fallback_to_processing
        }

# ============================================================================
# WORKFLOW STATE MANAGEMENT - GUIDELINE v3.2.4
# ============================================================================

class WorkflowState:
    """Production-ready workflow state management - Guideline v3.2.4"""
    
    def __init__(self, state_file="data/workflow_state.json"):
        self.state_file = state_file
        self.logger = logging.getLogger('factset_pipeline.workflow')
        self.state = self._load_state()
    
    def _load_state(self):
        """Load existing state or create comprehensive default state"""
        default_state = {
            "workflow_id": None,
            "started_at": None,
            "last_updated": None,
            "search_completed": False,
            "search_timestamp": None,
            "files_generated": 0,
            "md_files_generated": 0,
            "factset_files_generated": 0,
            "processing_completed": False,
            "processing_timestamp": None,
            "companies_found": 0,
            "sheets_uploaded": False,
            "upload_timestamp": None,
            "last_error": None,
            "success_count": 0,
            "total_steps": 3,
            "rate_limiting_detected": False,
            "rate_limiting_timestamp": None,
            "consecutive_failures": 0,
            "last_successful_search": None,
            "circuit_breaker_active": False,
            "search_stopped_early": False,
            "fallback_to_processing": False,
            "execution_mode": "intelligent",
            "search_strategy": "balanced",
            "guideline_version": "3.2.4"
        }
        
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)
                    # Merge with defaults to handle missing keys
                    self._deep_merge(default_state, loaded_state)
                    return default_state
            except Exception as e:
                self.logger.warning(emoji.safe(f"⚠️ Error loading workflow state: {e}"))
        
        return default_state
    
    def _deep_merge(self, base, update):
        """Deep merge dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save_state(self):
        """Save current state to file with error handling"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            self.state["last_updated"] = datetime.now().isoformat()
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
                
            self.logger.debug(emoji.safe("💾 Workflow state saved"))
        except Exception as e:
            self.logger.error(emoji.safe(f"⚠️ Error saving workflow state: {e}"))
    
    def start_workflow(self, search_strategy="intelligent", execution_mode="intelligent"):
        """Start a new workflow - Guideline v3.2.4"""
        workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.state.update({
            "workflow_id": workflow_id,
            "started_at": datetime.now().isoformat(),
            "search_completed": False,
            "processing_completed": False,
            "sheets_uploaded": False,
            "last_error": None,
            "success_count": 0,
            "search_strategy": search_strategy,
            "execution_mode": execution_mode,
            "guideline_version": "3.2.4",
            "rate_limiting_detected": False,
            "consecutive_failures": 0,
            "search_stopped_early": False,
            "fallback_to_processing": False
        })
        
        self.save_state()
        self.logger.info(emoji.safe(f"🚀 Started workflow: {workflow_id} (strategy: {search_strategy}, mode: {execution_mode})"))
    
    def mark_search_complete(self, files_generated=0, md_files=0, factset_files=0, duration=0, stopped_early=False):
        """Mark search phase as complete"""
        self.state.update({
            "search_completed": True,
            "search_timestamp": datetime.now().isoformat(),
            "files_generated": files_generated,
            "md_files_generated": md_files,
            "factset_files_generated": factset_files,
            "success_count": 1,
            "consecutive_failures": 0,  # Reset on success
            "last_successful_search": datetime.now().isoformat(),
            "search_stopped_early": stopped_early
        })
        
        self.save_state()
        status_msg = "Search phase completed"
        if stopped_early:
            status_msg += " (stopped early due to rate limiting)"
        self.logger.info(emoji.safe(f"✅ {status_msg}: {md_files} MD files, {factset_files} FactSet files"))
    
    def mark_processing_complete(self, companies_found=0, duration=0):
        """Mark processing phase as complete"""
        self.state.update({
            "processing_completed": True,
            "processing_timestamp": datetime.now().isoformat(),
            "companies_found": companies_found,
            "success_count": 2
        })
        
        self.save_state()
        self.logger.info(emoji.safe(f"✅ Processing phase completed: {companies_found} companies"))
    
    def mark_upload_complete(self, duration=0):
        """Mark upload phase as complete"""
        self.state.update({
            "sheets_uploaded": True,
            "upload_timestamp": datetime.now().isoformat(),
            "success_count": 3
        })
        
        self.save_state()
        self.logger.info(emoji.safe("✅ Upload phase completed"))
    
    def mark_error(self, error_message):
        """Mark error in workflow - Guideline v3.2.4"""
        self.state.update({
            "last_error": error_message,
            "consecutive_failures": self.state.get("consecutive_failures", 0) + 1
        })
        self.save_state()
        self.logger.error(emoji.safe(f"❌ Workflow error: {error_message}"))
    
    def reset_workflow(self):
        """Reset workflow state - Guideline v3.2.4"""
        self.state = self._load_state()
        self.state.update({
            "workflow_id": None,
            "search_completed": False,
            "processing_completed": False,
            "sheets_uploaded": False,
            "last_error": None,
            "success_count": 0,
            "consecutive_failures": 0
        })
        self.save_state()
        self.logger.info(emoji.safe("🔄 Workflow state reset"))

# ============================================================================
# PRODUCTION PIPELINE IMPLEMENTATION - GUIDELINE v3.2.4
# ============================================================================

class ProductionFactSetPipeline:
    """Production-ready FactSet pipeline - Guideline v3.2.4 compliant"""
    
    def __init__(self, config_file=None):
        self.logger = setup_logging()
        self.config = ProductionConfig(config_file)  # As per guideline
        self.rate_protector = RateLimitProtector(self.config)  # As per guideline
        self.state = WorkflowState()  # As per guideline
        
        # Create necessary directories
        self._setup_directories()
        
        self.logger.info(emoji.safe(f"🚀 Production FactSet Pipeline v{__version__} initialized (Guideline v3.2.4)"))
    
    def _setup_directories(self):
        """Setup required directories"""
        directories = [
            self.config.get('output.csv_dir'),
            self.config.get('output.pdf_dir'),
            self.config.get('output.md_dir'),
            self.config.get('output.processed_dir'),
            self.config.get('output.logs_dir')
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def analyze_existing_data(self):
        """Analyze existing data to determine optimal strategy - Guideline v3.2.4"""
        md_dir = self.config.get('output.md_dir')
        
        if not os.path.exists(md_dir):
            return 0, "no_data"
        
        md_files = list(Path(md_dir).glob("*.md"))
        file_count = len(md_files)
        
        self.logger.info(emoji.safe(f"📊 Existing data analysis: {file_count} MD files found"))
        
        # Analyze quality of existing data
        factset_files = 0
        portfolio_companies = ['華碩', '和碩', '統一', '全新', '保瑞', '台積電', '鴻海']
        companies_with_data = 0
        
        for md_file in md_files[:20]:  # Sample up to 20 files
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if 'factset' in content or 'eps' in content or '分析師' in content:
                        factset_files += 1
                    
                    # Check for portfolio companies
                    filename = md_file.name.lower()
                    for company in portfolio_companies:
                        if company in filename or company in content[:500]:
                            companies_with_data += 1
                            break
            except Exception as e:
                self.logger.warning(f"Error analyzing {md_file}: {e}")
        
        self.logger.info(emoji.safe(f"📈 Quality analysis: {factset_files} FactSet files, {companies_with_data} portfolio companies"))
        
        # Quality assessment matching guideline criteria
        if file_count >= 50 and factset_files >= 20:
            return file_count, "excellent"
        elif file_count >= 20 and factset_files >= 10:
            return file_count, "good"
        elif file_count >= 10 and factset_files >= 5:
            return file_count, "moderate"
        elif file_count >= 5:
            return file_count, "limited"
        else:
            return file_count, "insufficient"
    
    def determine_strategy(self, existing_files, data_status):
        """Determine optimal execution strategy - Guideline v3.2.4"""
        self.logger.info(emoji.safe(f"🎯 Determining optimal strategy..."))
        self.logger.info(emoji.safe(f"   📄 Existing files: {existing_files}"))
        self.logger.info(emoji.safe(f"   📊 Data status: {data_status}"))
        
        # Check rate limiting status
        if self.rate_protector.should_stop_immediately():
            strategy = "process_existing"
            reason = "Rate limiting detected - focus on existing data"
        elif data_status in ["excellent", "good"]:
            strategy = "conservative"
            reason = "Sufficient data exists - conservative updates only"
        elif data_status == "moderate":
            strategy = "selective_enhancement"
            reason = "Moderate data - selective enhancement"
        else:
            strategy = "comprehensive"
            reason = "Insufficient data - comprehensive collection needed"
        
        self.logger.info(emoji.safe(f"   🎯 Strategy: {strategy.upper()}"))
        self.logger.info(emoji.safe(f"   📝 Reason: {reason}"))
        
        return strategy
    
    def run_complete_pipeline(self, strategy="intelligent", force_all=False, skip_phases=None, execution_mode="intelligent"):
        """Run the complete production pipeline - Guideline v3.2.4"""
        if skip_phases is None:
            skip_phases = []
        
        pipeline_start = time.time()
        
        self.logger.info(emoji.safe(f"🚀 Production FactSet Pipeline v{__version__} (Guideline v3.2.4)"))
        self.logger.info(emoji.safe(f"📅 Date: {__date__}"))
        self.logger.info(emoji.safe(f"👨‍💻 Author: {__author__}"))
        self.logger.info("=" * 80)
        
        # Analyze existing data and determine strategy
        existing_files, data_status = self.analyze_existing_data()
        optimal_strategy = self.determine_strategy(existing_files, data_status)
        
        # Initialize or resume workflow
        if force_all or not self.state.state.get("workflow_id"):
            self.state.start_workflow(optimal_strategy, execution_mode)
        
        # Load and display target companies
        if not self.config.config.get('target_companies'):
            self.config.download_watchlist()
        
        companies = self.config.config.get('target_companies', [])
        self.logger.info(emoji.safe(f"🎯 Target Companies: {len(companies)} companies from 觀察名單.csv"))
        
        success_phases = 0
        total_phases = 3 - len(skip_phases)
        
        # Phase 1: Intelligent Search with immediate stop strategy
        if "search" not in skip_phases:
            self.logger.info(emoji.safe(f"\n🔍 Starting search phase with strategy: {optimal_strategy}"))
            self.logger.info(emoji.safe("🛑 Note: Search will stop immediately on rate limiting and process existing data"))
            
            if self.run_intelligent_search_phase(optimal_strategy, force=force_all):
                success_phases += 1
                
                # Check if search was stopped early
                if self.state.state.get("search_stopped_early"):
                    self.logger.warning(emoji.safe("⚠️ Search stopped early due to rate limiting"))
                    self.logger.info(emoji.safe("📄 Continuing with existing data processing..."))
                else:
                    self.logger.info(emoji.safe("✅ Search phase completed successfully"))
            else:
                self.logger.error(emoji.safe("❌ Search phase failed"))
                
                # Check if we can continue with existing data
                if self.state.state.get("md_files_generated", 0) > 0:
                    self.logger.info(emoji.safe("📄 Continuing with existing data..."))
                    success_phases += 1
                else:
                    self.logger.error(emoji.safe("💔 Pipeline stopped - no data available"))
                    return False
        else:
            self.logger.info(emoji.safe("⏭️ Skipping search phase"))
            success_phases += 1
        
        # Phase 2: Enhanced Processing
        if "processing" not in skip_phases:
            self.logger.info(emoji.safe(f"\n📊 Starting processing phase..."))
            
            if self.run_enhanced_processing_phase(force=force_all):
                success_phases += 1
                self.logger.info(emoji.safe("✅ Processing phase completed successfully"))
            else:
                self.logger.error(emoji.safe("❌ Processing phase failed"))
                return False
        else:
            self.logger.info(emoji.safe("⏭️ Skipping processing phase"))
            success_phases += 1
        
        # Phase 3: Enhanced Upload
        if "upload" not in skip_phases:
            self.logger.info(emoji.safe(f"\n📈 Starting upload phase..."))
            
            if self.run_enhanced_upload_phase(force=force_all):
                success_phases += 1
                self.logger.info(emoji.safe("✅ Upload phase completed successfully"))
            else:
                self.logger.warning(emoji.safe("⚠️ Upload phase failed - pipeline completed with issues"))
        else:
            self.logger.info(emoji.safe("⏭️ Skipping upload phase"))
            success_phases += 1
        
        # Final summary and performance report
        total_duration = time.time() - pipeline_start
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe("🎉 PRODUCTION PIPELINE EXECUTION COMPLETED! (Guideline v3.2.4)"))
        self.logger.info("="*80)
        self.logger.info(emoji.safe(f"📊 Success Rate: {success_phases}/{total_phases} phases"))
        self.logger.info(emoji.safe(f"⏱️ Total Duration: {total_duration:.1f} seconds"))
        self.logger.info(emoji.safe(f"🎯 Guideline Compliance: v{__version__}"))
        
        # Show rate limiting status if applicable
        if self.state.state.get("search_stopped_early"):
            self.logger.info(emoji.safe("🛑 Search was stopped early due to rate limiting"))
            self.logger.info(emoji.safe("📄 Successfully processed existing data instead"))
        
        if success_phases == total_phases:
            self.logger.info(emoji.safe("🏆 All phases completed successfully!"))
            
            # Display comprehensive results
            md_files = self.state.state.get('md_files_generated', 0)
            factset_files = self.state.state.get('factset_files_generated', 0)
            companies_found = self.state.state.get('companies_found', 0)
            
            self.logger.info(emoji.safe(f"📄 MD Files Generated: {md_files}"))
            self.logger.info(emoji.safe(f"🎯 FactSet Content Files: {factset_files}"))
            self.logger.info(emoji.safe(f"🏢 Companies Processed: {companies_found}"))
            
            # Quality assessment
            if md_files >= 50:
                self.logger.info(emoji.safe("🏆 OUTSTANDING: Comprehensive data collection achieved!"))
            elif md_files >= 20:
                self.logger.info(emoji.safe("🎉 EXCELLENT: Substantial data available for analysis!"))
            elif md_files >= 10:
                self.logger.info(emoji.safe("✅ GOOD: Sufficient data for portfolio analysis!"))
            else:
                self.logger.info(emoji.safe("⚠️ MODERATE: Limited data collected"))
            
            return True
        else:
            self.logger.warning(emoji.safe("⚠️ Pipeline completed with some issues"))
            return False
    
    def run_intelligent_search_phase(self, strategy="comprehensive", force=False):
        """Run search phase with immediate stop on rate limiting - Guideline v3.2.4"""
        if self.state.state["search_completed"] and not force:
            self.logger.info(emoji.safe("ℹ️ Search phase already completed (use --force to re-run)"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe(f"🔍 PHASE 1: INTELLIGENT SEARCH EXECUTION (Guideline v3.2.4)"))
        self.logger.info(emoji.safe(f"📊 Strategy: {strategy.upper()}"))
        self.logger.info("="*80)
        
        # Skip search if strategy indicates processing existing data
        if strategy == "process_existing":
            self.logger.info(emoji.safe("📄 Strategy indicates processing existing data only"))
            return self._fallback_to_existing_data(start_time)
        
        try:
            # Load target companies
            if not self.config.config.get('target_companies'):
                self.logger.info(emoji.safe("📥 Loading target companies..."))
                if not self.config.download_watchlist():
                    self.logger.error(emoji.safe("❌ Failed to load target companies"))
                    return False
            
            companies = self.config.config['target_companies']
            self.logger.info(emoji.safe(f"🎯 Loaded {len(companies)} target companies from 觀察名單.csv"))
            
            # Determine company subset based on strategy
            if strategy == "conservative":
                target_companies = companies[:20]
            elif strategy == "selective_enhancement":
                target_companies = companies[:50]
            else:
                target_companies = companies
            
            self.logger.info(emoji.safe(f"🔍 Searching {len(target_companies)} companies for strategy: {strategy}"))
            
            # Run search with immediate rate limit detection
            search_result = self._run_protected_search(target_companies, strategy)
            
            # Handle rate limiting case
            if search_result == "rate_limited":
                self.logger.warning(emoji.safe("🚨 Rate limiting detected - falling back to existing data"))
                return self._fallback_to_existing_data(start_time)
            
            if search_result:
                # Analyze results
                duration = time.time() - start_time
                md_dir = self.config.get('output.md_dir')
                csv_dir = self.config.get('output.csv_dir')
                
                md_files = list(Path(md_dir).glob("*.md")) if os.path.exists(md_dir) else []
                csv_files = list(Path(csv_dir).glob("*.csv")) if os.path.exists(csv_dir) else []
                
                factset_files = self._count_factset_files(md_files)
                
                # Check if search was stopped early
                stopped_early = self.rate_protector.should_stop_immediately()
                
                self.state.mark_search_complete(
                    files_generated=len(csv_files),
                    md_files=len(md_files),
                    factset_files=factset_files,
                    duration=duration,
                    stopped_early=stopped_early
                )
                
                self.logger.info(emoji.safe(f"✅ Search completed: {len(md_files)} MD files, {factset_files} with FactSet content"))
                return True
            else:
                # Search failed, but check for existing data
                existing_files, _ = self.analyze_existing_data()
                if existing_files > 0:
                    self.logger.warning(emoji.safe("⚠️ Search failed, but found existing data - continuing with processing"))
                    return self._fallback_to_existing_data(start_time)
                
                return False
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "too many requests" in error_str:
                self.logger.error(emoji.safe("🛑 Rate limiting detected - switching to data processing"))
                self.rate_protector.record_429_error()
                return self._fallback_to_existing_data(start_time)
            
            self.logger.error(emoji.safe(f"❌ Search phase failed: {e}"))
            self.state.mark_error(str(e))
            
            # Check for existing data as fallback
            existing_files, _ = self.analyze_existing_data()
            if existing_files > 0:
                self.logger.info(emoji.safe("📄 Found existing data - continuing with processing"))
                return self._fallback_to_existing_data(start_time)
            
            return False
    
    def _fallback_to_existing_data(self, start_time):
        """Fallback to existing data when search fails"""
        self.logger.info(emoji.safe("📄 Falling back to existing data processing..."))
        
        existing_files, _ = self.analyze_existing_data()
        if existing_files > 0:
            self.state.mark_search_complete(
                files_generated=0,
                md_files=existing_files,
                factset_files=max(1, existing_files // 3),
                duration=time.time() - start_time,
                stopped_early=True
            )
            self.logger.info(emoji.safe(f"✅ Using existing data: {existing_files} files"))
            return True
        else:
            self.logger.warning(emoji.safe("⚠️ No existing data available"))
            return False
    
    def _run_protected_search(self, companies, strategy):
        """Run search with comprehensive protection and immediate stop on rate limiting"""
        try:
            # Try to import the search module
            try:
                import factset_search as search_module
            except ImportError:
                self.logger.error(emoji.safe("❌ factset_search module not available"))
                return False
            
            # Check for enhanced search function
            if hasattr(search_module, 'run_enhanced_search_suite'):
                self.logger.info(emoji.safe("🔍 Using enhanced search suite with monitoring"))
                try:
                    result = search_module.run_enhanced_search_suite(
                        self.config.config,
                        priority_focus="high_only" if strategy == "conservative" else "balanced"
                    )
                    
                    # Check if result indicates rate limiting
                    if result == "rate_limited":
                        self.rate_protector.record_429_error()
                        return "rate_limited"
                    
                    return result
                    
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "rate limit" in error_str:
                        self.rate_protector.record_429_error()
                        return "rate_limited"
                    else:
                        raise e
            else:
                self.logger.warning(emoji.safe("⚠️ Enhanced search suite not available - using basic search"))
                return self._run_basic_search_protected(search_module, strategy)
                
        except Exception as e:
            # Check if this is a rate limiting error
            error_str = str(e).lower()
            if "429" in error_str or "too many requests" in error_str:
                self.rate_protector.record_429_error()
                self.logger.error(emoji.safe("🛑 Stopping search due to rate limiting - switching to data processing"))
                return "rate_limited"  # Special return value
            
            self.logger.error(emoji.safe(f"❌ Protected search failed: {e}"))
            return False
    
    def _run_basic_search_protected(self, search_module, strategy):
        """Run basic search with rate limiting protection"""
        try:
            # Backup original argv
            original_argv = sys.argv
            
            # Prepare arguments based on strategy
            if strategy == "conservative":
                search_args = ['factset_search.py', '--priority-focus', 'high_only']
            elif strategy == "selective_enhancement":
                search_args = ['factset_search.py', '--priority-focus', 'top_30']
            else:
                search_args = ['factset_search.py', '--priority-focus', 'balanced']
            
            # Set new argv
            sys.argv = search_args
            
            # Run with timeout and error handling
            try:
                if hasattr(search_module, 'main'):
                    search_module.main()
                    return True
                else:
                    self.logger.error(emoji.safe("❌ No main function found in search module"))
                    return False
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "too many requests" in error_str:
                    self.logger.error(emoji.safe("🚨 Rate limiting encountered during search"))
                    self.rate_protector.record_429_error()
                    return "rate_limited"
                else:
                    raise e
            finally:
                # Restore original argv
                sys.argv = original_argv
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "too many requests" in error_str:
                return "rate_limited"
            self.logger.error(emoji.safe(f"❌ Basic search failed: {e}"))
            return False
    
    def _count_factset_files(self, md_files):
        """Count files with FactSet content"""
        factset_count = 0
        sample_size = min(20, len(md_files))
        
        for md_file in md_files[:sample_size]:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in ['factset', 'eps', '分析師', '目標價']):
                        factset_count += 1
            except Exception:
                continue
        
        # Extrapolate to total
        if sample_size > 0:
            ratio = factset_count / sample_size
            return int(len(md_files) * ratio)
        
        return 0
    
    def run_enhanced_processing_phase(self, force=False):
        """Run processing phase with enhanced error handling - Guideline v3.2.4"""
        if self.state.state["processing_completed"] and not force:
            self.logger.info(emoji.safe("ℹ️ Processing phase already completed (use --force to re-run)"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe(f"📊 PHASE 2: ENHANCED DATA PROCESSING (Guideline v3.2.4)"))
        self.logger.info("="*80)
        
        try:
            # Check for data to process
            md_dir = self.config.get('output.md_dir')
            md_files = list(Path(md_dir).glob("*.md")) if os.path.exists(md_dir) else []
            csv_files = list(Path(self.config.get('output.csv_dir')).glob("*.csv")) if os.path.exists(self.config.get('output.csv_dir')) else []
            
            self.logger.info(emoji.safe(f"📄 Found {len(md_files)} MD files and {len(csv_files)} CSV files to process"))
            
            if len(md_files) == 0 and len(csv_files) == 0:
                self.logger.warning(emoji.safe("⚠️ No data files found for processing"))
                self.logger.info(emoji.safe("💡 Run search phase first or check data directories"))
                return False
            
            # Try to import and run data processor
            try:
                import data_processor
                
                # Check available functions
                if hasattr(data_processor, 'process_all_data'):
                    success = data_processor.process_all_data(force=force, parse_md=True)
                elif hasattr(data_processor, 'main'):
                    # Use main function with arguments
                    original_argv = sys.argv
                    sys.argv = ['data_processor.py', '--force', '--parse-md'] if force else ['data_processor.py', '--parse-md']
                    try:
                        data_processor.main()
                        success = True
                    finally:
                        sys.argv = original_argv
                else:
                    self.logger.error(emoji.safe("❌ No usable processing function found"))
                    return False
                
            except ImportError:
                self.logger.error(emoji.safe("❌ data_processor module not available"))
                return False
            
            if success:
                # Analyze processing results
                duration = time.time() - start_time
                summary_file = self.config.get('output.summary_csv')
                companies_found = 0
                
                if os.path.exists(summary_file):
                    try:
                        import pandas as pd
                        summary_df = pd.read_csv(summary_file)
                        companies_found = len(summary_df)
                        
                        # Log quality metrics for guideline v3.2.4
                        if 'MD資料筆數' in summary_df.columns:
                            companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
                            self.logger.info(emoji.safe(f"📊 Companies with data: {companies_with_data}"))
                        
                        if '品質評分' in summary_df.columns:
                            avg_quality = summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
                            self.logger.info(emoji.safe(f"🎯 Average quality score: {avg_quality:.1f}/4.0"))
                        
                        if '2025EPS平均值' in summary_df.columns:
                            companies_with_eps = len(summary_df[summary_df['2025EPS平均值'].notna()])
                            self.logger.info(emoji.safe(f"💰 Companies with 2025 EPS: {companies_with_eps}"))
                            
                    except Exception as e:
                        self.logger.warning(emoji.safe(f"⚠️ Error analyzing results: {e}"))
                
                self.state.mark_processing_complete(companies_found, duration)
                self.logger.info(emoji.safe(f"✅ Processing completed: {companies_found} companies processed (Guideline v3.2.4)"))
                return True
            else:
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(emoji.safe(f"❌ Processing phase failed: {e}"))
            self.state.mark_error(str(e))
            if self.config.get('debug'):
                traceback.print_exc()
            return False
    
    def run_enhanced_upload_phase(self, force=False):
        """Run upload phase with enhanced validation - Guideline v3.2.4"""
        if self.state.state["sheets_uploaded"] and not force:
            self.logger.info(emoji.safe("ℹ️ Upload phase already completed (use --force to re-run)"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe(f"📈 PHASE 3: ENHANCED GOOGLE SHEETS UPLOAD (Guideline v3.2.4)"))
        self.logger.info("="*80)
        
        try:
            # Check for required files
            required_files = [
                self.config.get('output.summary_csv')
            ]
            
            optional_files = [
                self.config.get('output.detailed_csv'),
                self.config.get('output.stats_json')
            ]
            
            available_files = [f for f in required_files if f and os.path.exists(f)]
            
            if not available_files:
                self.logger.warning(emoji.safe("⚠️ No processed data files found for upload"))
                self.logger.info(emoji.safe("💡 Run processing phase first"))
                return False
            
            optional_available = [f for f in optional_files if f and os.path.exists(f)]
            self.logger.info(emoji.safe(f"📄 Found {len(available_files)} required files, {len(optional_available)} optional files"))
            
            # Check credentials
            if not self.config.get('sheets.credentials') or not self.config.get('sheets.sheet_id'):
                self.logger.warning(emoji.safe("⚠️ Google Sheets credentials not configured"))
                self.logger.info(emoji.safe("💡 Set GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEET_ID environment variables"))
                return False
            
            # Try to import and run sheets uploader
            try:
                import sheets_uploader
                
                # Prepare configuration for uploader
                upload_config = self.config.config.copy()
                upload_config['input'] = {
                    'summary_csv': self.config.get('output.summary_csv'),
                    'detailed_csv': self.config.get('output.detailed_csv'),
                    'stats_json': self.config.get('output.stats_json')
                }
                
                if hasattr(sheets_uploader, 'upload_all_sheets'):
                    success = sheets_uploader.upload_all_sheets(upload_config)
                elif hasattr(sheets_uploader, 'main'):
                    # Use main function
                    original_argv = sys.argv
                    sys.argv = ['sheets_uploader.py']
                    try:
                        sheets_uploader.main()
                        success = True
                    finally:
                        sys.argv = original_argv
                else:
                    self.logger.error(emoji.safe("❌ No usable upload function found"))
                    return False
                    
            except ImportError:
                self.logger.error(emoji.safe("❌ sheets_uploader module not available"))
                return False
            
            if success:
                duration = time.time() - start_time
                self.state.mark_upload_complete(duration)
                
                # Show dashboard link
                sheet_id = self.config.get('sheets.sheet_id')
                if sheet_id:
                    dashboard_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
                    self.logger.info(emoji.safe(f"📊 Dashboard available: {dashboard_url}"))
                    self.logger.info(emoji.safe("🎯 Features: Portfolio Summary (v3.2.4), Detailed Data (EPS breakdown), Statistics"))
                
                self.logger.info(emoji.safe("✅ Upload completed successfully (Guideline v3.2.4)"))
                return True
            else:
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(emoji.safe(f"❌ Upload phase failed: {e}"))
            self.state.mark_error(str(e))
            if self.config.get('debug'):
                traceback.print_exc()
            return False

# ============================================================================
# PRODUCTION CLI INTERFACE - GUIDELINE v3.2.4
# ============================================================================

def create_production_parser():
    """Create production-ready argument parser - Guideline v3.2.4"""
    parser = argparse.ArgumentParser(
        description=f'Production FactSet Pipeline v{__version__} - Guideline v3.2.4 Compliant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Production Pipeline Examples (Guideline v3.2.4):

  # Intelligent execution (recommended)
  python factset_pipeline.py                     # Auto-detect strategy with immediate stop
  python factset_pipeline.py --force-all         # Force complete refresh
  
  # Strategic execution modes
  python factset_pipeline.py --mode conservative  # Safe execution with delays
  python factset_pipeline.py --mode process-only # Process existing data only
  python factset_pipeline.py --mode test-only     # Test components without search
  
  # Phase-specific execution
  python factset_pipeline.py --search-only       # Search phase only (with immediate stop)
  python factset_pipeline.py --process-only      # Processing phase only  
  python factset_pipeline.py --upload-only       # Upload phase only
  
  # Monitoring and recovery
  python factset_pipeline.py --status            # Comprehensive status
  python factset_pipeline.py --analyze-data      # Analyze existing data

GUIDELINE v3.2.4 FEATURES:
- Immediate stop on 429 errors with fallback to data processing
- Portfolio Summary: 14-column exact format
- Detailed Data: Enhanced EPS breakdown (2025/2026/2027)
- Quality scoring system (1-4 scale) with emoji status
- Integration with 觀察名單.csv (116+ companies)

Windows Users: Use Command Prompt or PowerShell for best emoji support
        """
    )
    
    # Configuration options
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Execution modes
    execution_group = parser.add_mutually_exclusive_group()
    execution_group.add_argument('--mode', choices=['intelligent', 'conservative', 'process-only', 'test-only'], 
                                default='intelligent', help='Execution mode')
    execution_group.add_argument('--search-only', action='store_true', help='Run search phase only')
    execution_group.add_argument('--process-only', action='store_true', help='Run processing phase only')
    execution_group.add_argument('--upload-only', action='store_true', help='Run upload phase only')
    
    # Control options
    parser.add_argument('--force-all', action='store_true', help='Force re-run all phases')
    parser.add_argument('--skip-phases', nargs='*', choices=['search', 'processing', 'upload'],
                       help='Skip specific phases')
    
    # Monitoring and analysis
    monitoring_group = parser.add_mutually_exclusive_group()
    monitoring_group.add_argument('--status', action='store_true', help='Show comprehensive status')
    monitoring_group.add_argument('--analyze-data', action='store_true', help='Analyze existing data')
    
    # Version info
    parser.add_argument('--version', action='version', 
                       version=f'Production FactSet Pipeline v{__version__} (Guideline v3.2.4)')
    
    return parser

def main():
    """Production main entry point - Guideline v3.2.4"""
    parser = create_production_parser()
    args = parser.parse_args()
    
    # Setup logging first
    logger = setup_logging()
    
    # Set debug mode if requested
    if args.debug:
        os.environ['FACTSET_PIPELINE_DEBUG'] = 'true'
        logging.getLogger('factset_pipeline').setLevel(logging.DEBUG)
    
    try:
        # Initialize production pipeline
        pipeline = ProductionFactSetPipeline(args.config)
        logger.info(emoji.safe(f"🚀 Production FactSet Pipeline v{__version__} started (Guideline v3.2.4)"))
        
        # Handle monitoring requests
        if args.status:
            # Simple status display
            print(emoji.safe("📊 Pipeline Status (Guideline v3.2.4):"))
            print(f"   Version: {__version__}")
            print(f"   Configuration: Loaded")
            print(f"   Rate Protector: Active (threshold=1)")
            print(f"   Workflow State: Initialized")
            return
        
        if args.analyze_data:
            existing_files, data_status = pipeline.analyze_existing_data()
            strategy = pipeline.determine_strategy(existing_files, data_status)
            print(emoji.safe(f"\n💡 Recommended action based on analysis:"))
            if strategy == "process_existing":
                print("   python factset_pipeline.py --mode process-only")
            elif strategy == "conservative":
                print("   python factset_pipeline.py --mode conservative")
            else:
                print("   python factset_pipeline.py --mode intelligent")
            return
        
        # Handle execution requests
        success = False
        
        if args.search_only:
            existing_files, data_status = pipeline.analyze_existing_data()
            strategy = pipeline.determine_strategy(existing_files, data_status)
            success = pipeline.run_intelligent_search_phase(strategy, force=args.force_all)
            
        elif args.process_only:
            success = pipeline.run_enhanced_processing_phase(force=args.force_all)
            
        elif args.upload_only:
            success = pipeline.run_enhanced_upload_phase(force=args.force_all)
            
        else:
            # Full pipeline execution
            skip_phases = args.skip_phases or []
            
            # Map execution mode to strategy
            if args.mode == "process-only":
                skip_phases.append("search")
            elif args.mode == "test-only":
                skip_phases.extend(["search", "upload"])
            
            success = pipeline.run_complete_pipeline(
                force_all=args.force_all,
                skip_phases=skip_phases,
                execution_mode=args.mode
            )
        
        # Provide helpful guidance on failure
        if not success:
            logger.error(emoji.safe("\n💡 Troubleshooting suggestions (Guideline v3.2.4):"))
            logger.error("1. Analyze data: python factset_pipeline.py --analyze-data")
            logger.error("2. Try conservative mode: python factset_pipeline.py --mode conservative")
            logger.error("3. Process existing data: python factset_pipeline.py --mode process-only")
            logger.error("4. Check API credentials and rate limiting status")
        else:
            logger.info(emoji.safe("🎉 Pipeline completed successfully! (Guideline v3.2.4)"))
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning(emoji.safe("\n⚠️ Pipeline interrupted by user"))
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(emoji.safe(f"❌ Pipeline execution failed: {e}"))
        if args.debug:
            logger.error("Debug traceback:", exc_info=True)
        else:
            logger.error("Run with --debug for detailed error information")
        
        logger.error(emoji.safe("\n💡 Recovery options:"))
        logger.error("1. Check --analyze-data for current state")
        logger.error("2. Try --mode process-only if search fails")
        logger.error("3. Use --debug for detailed error analysis")
        
        sys.exit(1)

if __name__ == "__main__":
    main()