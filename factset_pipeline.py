"""
factset_pipeline.py - Complete Production-Ready FactSet Pipeline (Enhanced Version)

Version: 3.4.0-ENHANCED
Date: 2025-06-22
Author: FactSet Pipeline - Production Architecture

MAJOR ENHANCEMENTS:
- ✅ Immediate stop on 429 errors with fallback to data processing
- ✅ Enhanced URL parsing and error handling
- ✅ Smart fallback strategies when search fails
- ✅ Comprehensive error recovery workflows
- ✅ Better rate limiting detection and response

Production Features:
- Immediate stop and process strategy on rate limiting
- Robust URL validation and error handling
- Automatic fallback to existing data processing
- Comprehensive logging and status reporting
- Recovery workflows with intelligent retry logic
- Circuit breaker patterns for API protection
- Windows Command Prompt compatibility
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

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Version Information
__version__ = "3.4.0-ENHANCED"
__date__ = "2025-06-22"
__author__ = "FactSet Pipeline - Enhanced Production Architecture"

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
# CONFIGURATION MANAGEMENT
# ============================================================================

class ProductionConfig:
    """Production-ready configuration management"""
    
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
        """Load configuration with comprehensive defaults"""
        default_config = {
            "target_companies": [],
            "watchlist_url": "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv",
            "search": {
                "max_results": 10,
                "language": "zh-TW",
                "date_restrict": "y1",
                "safe": "active",
                "rate_limit_delay": 45,
                "max_retries": 3,
                "circuit_breaker_threshold": 1  # Stop immediately on first 429
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
# ENHANCED RATE LIMITING PROTECTION SYSTEM
# ============================================================================

class AdvancedRateLimitProtector:
    """Enhanced rate limiting protection with immediate stop and process strategy"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('factset_pipeline.rate_limiter')
        
        # Rate limiting state
        self.min_delay = config.get('search.rate_limit_delay', 45)
        self.max_delay = 600  # 10 minutes max
        self.current_delay = self.min_delay
        self.last_request_time = None
        self.consecutive_429s = 0
        self.consecutive_failures = 0
        self.circuit_breaker_threshold = config.get('search.circuit_breaker_threshold', 1)  # Stop immediately
        self.circuit_open = False
        self.circuit_open_time = None
        self.request_history = []
        
        # NEW: Immediate stop flag
        self.should_stop_searching = False
        self.stop_reason = None
        self.fallback_to_processing = False
    
    def check_circuit_breaker(self):
        """Check if circuit breaker should be opened"""
        if self.consecutive_429s >= self.circuit_breaker_threshold:
            if not self.circuit_open:
                self.circuit_open = True
                self.circuit_open_time = time.time()
                self.logger.error(emoji.safe(f"🚨 Circuit breaker OPENED after {self.consecutive_429s} consecutive 429 errors"))
            return True
        return False
    
    def should_wait(self):
        """Check if should wait before next request"""
        if self.circuit_open:
            # Check if circuit should be closed (after 30 minutes)
            if time.time() - self.circuit_open_time > 1800:  # 30 minutes
                self.circuit_open = False
                self.consecutive_429s = 0
                self.current_delay = self.min_delay
                self.logger.info(emoji.safe("🔄 Circuit breaker CLOSED - attempting to resume"))
            else:
                return True
        
        if self.last_request_time is None:
            return False
        
        time_since_last = time.time() - self.last_request_time
        return time_since_last < self.current_delay
    
    def wait_if_needed(self):
        """Wait if necessary with status updates"""
        if self.circuit_open:
            remaining_time = 1800 - (time.time() - self.circuit_open_time)
            if remaining_time > 0:
                self.logger.warning(emoji.safe(f"🚨 Circuit breaker OPEN - {remaining_time/60:.1f} minutes remaining"))
                return False
        
        if self.should_wait():
            wait_time = self.current_delay - (time.time() - self.last_request_time)
            if wait_time > 0:
                self.logger.info(emoji.safe(f"⏳ Rate limiting protection: waiting {wait_time:.1f} seconds..."))
                time.sleep(wait_time)
        
        return True
    
    def record_request(self):
        """Record that a request was made"""
        self.last_request_time = time.time()
        self.request_history.append(self.last_request_time)
        
        # Keep only last 100 requests
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]
    
    def record_429_error(self):
        """Record a 429 error and immediately trigger stop"""
        self.consecutive_429s += 1
        self.consecutive_failures += 1
        
        # Exponential backoff
        self.current_delay = min(
            self.max_delay,
            self.min_delay * (2 ** self.consecutive_429s)
        )
        
        self.logger.warning(emoji.safe(f"🚨 Rate limiting detected! (#{self.consecutive_429s}) Delay increased to {self.current_delay} seconds"))
        
        # NEW: Immediate stop after first 429 error
        if self.consecutive_429s >= 1:  # Stop immediately on first 429
            self.should_stop_searching = True
            self.fallback_to_processing = True
            self.stop_reason = f"Rate limiting detected ({self.consecutive_429s} consecutive 429 errors)"
            self.logger.error(emoji.safe(f"🛑 STOPPING SEARCH: {self.stop_reason}"))
            self.logger.info(emoji.safe("📄 Will process existing data instead"))
            return True
        
        return self.check_circuit_breaker()
    
    def record_success(self):
        """Record a successful request"""
        if self.consecutive_429s > 0:
            self.logger.info(emoji.safe(f"✅ Request successful! Rate limiting appears to be lifted"))
        
        self.consecutive_429s = 0
        self.consecutive_failures = 0
        self.current_delay = max(self.min_delay, self.current_delay * 0.8)  # Gradually reduce delay
    
    def record_other_error(self):
        """Record a non-429 error"""
        self.consecutive_failures += 1
        # Don't reset 429 count for other errors
    
    def should_stop_search_immediately(self):
        """Check if search should stop immediately"""
        return self.should_stop_searching
    
    def should_fallback_to_processing(self):
        """Check if should fallback to processing existing data"""
        return self.fallback_to_processing
    
    def get_stop_reason(self):
        """Get reason for stopping search"""
        return self.stop_reason or "Unknown"
    
    def get_status(self):
        """Get current rate limiting status"""
        return {
            "circuit_open": self.circuit_open,
            "consecutive_429s": self.consecutive_429s,
            "current_delay": self.current_delay,
            "last_request": self.last_request_time,
            "recent_requests": len([t for t in self.request_history if time.time() - t < 3600]),  # Last hour
            "should_stop": self.should_stop_searching,
            "fallback_to_processing": self.fallback_to_processing
        }

# ============================================================================
# COMPREHENSIVE WORKFLOW STATE MANAGEMENT
# ============================================================================

class ProductionWorkflowState:
    """Production-ready workflow state management with all required methods"""
    
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
            "ip_blocked": False,
            "retry_count": 0,
            "execution_mode": "standard",
            "search_stopped_early": False,
            "fallback_to_processing": False,
            "priority_stats": {
                "high_priority_processed": 0,
                "medium_priority_processed": 0,
                "low_priority_processed": 0,
                "high_priority_successful": 0,
                "medium_priority_successful": 0,
                "low_priority_successful": 0
            },
            "search_strategy": "balanced",
            "performance_metrics": {
                "search_duration": 0,
                "processing_duration": 0,
                "upload_duration": 0,
                "total_duration": 0
            }
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
    
    def start_workflow(self, search_strategy="balanced", execution_mode="standard"):
        """Start a new workflow with comprehensive initialization"""
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
            "rate_limiting_detected": False,
            "consecutive_failures": 0,
            "circuit_breaker_active": False,
            "retry_count": 0,
            "search_stopped_early": False,
            "fallback_to_processing": False,
            "priority_stats": {
                "high_priority_processed": 0,
                "medium_priority_processed": 0,
                "low_priority_processed": 0,
                "high_priority_successful": 0,
                "medium_priority_successful": 0,
                "low_priority_successful": 0
            },
            "performance_metrics": {
                "search_duration": 0,
                "processing_duration": 0,
                "upload_duration": 0,
                "total_duration": 0
            }
        })
        
        self.save_state()
        self.logger.info(emoji.safe(f"🚀 Started workflow: {workflow_id} (strategy: {search_strategy}, mode: {execution_mode})"))
    
    def mark_search_complete(self, files_generated=0, md_files=0, factset_files=0, priority_stats=None, duration=0, stopped_early=False):
        """Mark search phase as complete with comprehensive metrics"""
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
        
        if priority_stats:
            self.state["priority_stats"].update(priority_stats)
        
        self.state["performance_metrics"]["search_duration"] = duration
        
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
        
        self.state["performance_metrics"]["processing_duration"] = duration
        self.save_state()
        self.logger.info(emoji.safe(f"✅ Processing phase completed: {companies_found} companies"))
    
    def mark_upload_complete(self, duration=0):
        """Mark upload phase as complete"""
        self.state.update({
            "sheets_uploaded": True,
            "upload_timestamp": datetime.now().isoformat(),
            "success_count": 3
        })
        
        self.state["performance_metrics"]["upload_duration"] = duration
        
        # Calculate total duration
        if self.state.get("started_at"):
            start_time = datetime.fromisoformat(self.state["started_at"])
            total_duration = (datetime.now() - start_time).total_seconds()
            self.state["performance_metrics"]["total_duration"] = total_duration
        
        self.save_state()
        self.logger.info(emoji.safe("✅ Upload phase completed"))
    
    def mark_error(self, error_message, phase="unknown", error_type="general"):
        """Mark error in workflow state with detailed tracking"""
        error_info = {
            "message": error_message,
            "phase": phase,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            "retry_count": self.state.get("retry_count", 0)
        }
        
        self.state["last_error"] = error_info
        self.state["consecutive_failures"] += 1
        
        # Check for specific error types
        if "429" in error_message or "Too Many Requests" in error_message:
            self.state["rate_limiting_detected"] = True
            self.state["rate_limiting_timestamp"] = datetime.now().isoformat()
            self.state["fallback_to_processing"] = True
            self.logger.error(emoji.safe(f"🚨 Rate limiting detected: {error_message}"))
        elif "circuit breaker" in error_message.lower():
            self.state["circuit_breaker_active"] = True
            self.logger.error(emoji.safe(f"🔌 Circuit breaker activated: {error_message}"))
        elif any(keyword in error_message.lower() for keyword in ["ip", "blocked", "sorry"]):
            self.state["ip_blocked"] = True
            self.logger.error(emoji.safe(f"🚫 IP blocking detected: {error_message}"))
        
        self.save_state()
        self.logger.error(emoji.safe(f"❌ Error in {phase} ({error_type}): {error_message}"))
    
    def reset_workflow(self, preserve_learnings=True):
        """Reset workflow state with option to preserve rate limiting learnings"""
        self.logger.info(emoji.safe("🔄 Resetting workflow state..."))
        
        # Backup current state
        if os.path.exists(self.state_file):
            backup_file = f"{self.state_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                shutil.copy2(self.state_file, backup_file)
                self.logger.info(emoji.safe(f"📋 Backed up current state to: {backup_file}"))
            except Exception as e:
                self.logger.warning(emoji.safe(f"⚠️ Could not backup state: {e}"))
        
        # Preserve rate limiting information if requested
        preserved_data = {}
        if preserve_learnings and self.state:
            preserved_data = {
                "rate_limiting_detected": self.state.get("rate_limiting_detected", False),
                "rate_limiting_timestamp": self.state.get("rate_limiting_timestamp"),
                "circuit_breaker_active": self.state.get("circuit_breaker_active", False),
                "ip_blocked": self.state.get("ip_blocked", False),
                "last_successful_search": self.state.get("last_successful_search")
            }
        
        # Reset to default state
        self.state = self._load_state()
        
        # Apply preserved data
        if preserved_data:
            self.state.update(preserved_data)
            self.logger.info(emoji.safe("🧠 Preserved rate limiting learnings"))
        
        self.save_state()
        self.logger.info(emoji.safe("✅ Workflow state reset successfully"))
    
    def is_rate_limited(self):
        """Check if currently under rate limiting with intelligent detection"""
        # Check explicit rate limiting flag
        if not self.state.get("rate_limiting_detected"):
            return False
        
        # Check if enough time has passed since rate limiting
        rate_limit_time_str = self.state.get("rate_limiting_timestamp")
        if rate_limit_time_str:
            try:
                rate_limit_time = datetime.fromisoformat(rate_limit_time_str)
                time_since_limit = datetime.now() - rate_limit_time
                
                # Different timeouts based on severity
                if self.state.get("circuit_breaker_active"):
                    timeout_hours = 12  # Longer timeout for circuit breaker
                elif self.state.get("ip_blocked"):
                    timeout_hours = 24  # Even longer for IP blocking
                else:
                    timeout_hours = 4   # Standard rate limiting
                
                if time_since_limit > timedelta(hours=timeout_hours):
                    # Clear rate limiting flags
                    self.state["rate_limiting_detected"] = False
                    self.state["circuit_breaker_active"] = False
                    self.save_state()
                    self.logger.info(emoji.safe(f"✅ Rate limiting expired after {time_since_limit}"))
                    return False
            except Exception as e:
                self.logger.warning(f"Error parsing rate limit timestamp: {e}")
        
        return True
    
    def should_stop_on_failures(self):
        """Check if should stop due to consecutive failures"""
        failure_threshold = 5
        consecutive_failures = self.state.get("consecutive_failures", 0)
        
        if consecutive_failures >= failure_threshold:
            self.logger.warning(emoji.safe(f"⚠️ Stopping due to {consecutive_failures} consecutive failures"))
            return True
        
        return False
    
    def get_next_phase(self):
        """Get next phase to execute based on current state"""
        if not self.state["search_completed"]:
            return "search"
        elif not self.state["processing_completed"]:
            return "processing"
        elif not self.state["sheets_uploaded"]:
            return "upload"
        else:
            return "complete"
    
    def get_recommendations(self):
        """Get intelligent recommendations based on current state"""
        recommendations = []
        
        if self.is_rate_limited():
            if self.state.get("circuit_breaker_active"):
                recommendations.append(emoji.safe("🔌 Circuit breaker active - wait 12+ hours or change IP address"))
            elif self.state.get("ip_blocked"):
                recommendations.append(emoji.safe("🚫 IP blocked - change IP address or wait 24+ hours"))
            else:
                recommendations.append(emoji.safe("⏰ Rate limited - wait 4-6 hours before retry"))
            
            recommendations.append(emoji.safe("💡 Processing existing data while waiting"))
        
        if self.state.get("search_stopped_early"):
            recommendations.append(emoji.safe("🛑 Search stopped early due to rate limiting"))
            recommendations.append(emoji.safe("📄 Continue with existing data processing"))
        
        if self.state.get("consecutive_failures", 0) > 2:
            recommendations.append(emoji.safe("🔧 Multiple failures detected - check API credentials"))
            recommendations.append(emoji.safe("🎯 Try conservative mode with fewer companies"))
        
        if self.state.get("md_files_generated", 0) > 0:
            recommendations.append(emoji.safe("📄 Process existing MD files for immediate results"))
        
        next_phase = self.get_next_phase()
        if next_phase != "complete":
            recommendations.append(emoji.safe(f"🔄 Next recommended phase: {next_phase}"))
        
        return recommendations
    
    def print_comprehensive_status(self):
        """Print comprehensive workflow status with detailed metrics"""
        print(emoji.safe(f"\n📊 Comprehensive Workflow Status"))
        print("=" * 60)
        
        if self.state["workflow_id"]:
            print(emoji.safe(f"🆔 Workflow ID: {self.state['workflow_id']}"))
            print(emoji.safe(f"📅 Started: {self.state['started_at']}"))
            print(emoji.safe(f"🎯 Strategy: {self.state['search_strategy']}"))
            print(emoji.safe(f"🔧 Mode: {self.state['execution_mode']}"))
            print(emoji.safe(f"🔄 Progress: {self.state['success_count']}/{self.state['total_steps']} phases"))
        else:
            print(emoji.safe("🆕 No workflow started"))
            return
        
        # Rate limiting and error status
        if self.is_rate_limited():
            print(emoji.safe(f"🚨 Rate limiting: ACTIVE since {self.state.get('rate_limiting_timestamp', 'unknown')}"))
            if self.state.get("circuit_breaker_active"):
                print(emoji.safe("🔌 Circuit breaker: ACTIVE"))
            if self.state.get("ip_blocked"):
                print(emoji.safe("🚫 IP status: BLOCKED"))
        else:
            print(emoji.safe("✅ Rate limiting: CLEAR"))
        
        # Search status
        if self.state.get("search_stopped_early"):
            print(emoji.safe("🛑 Search: STOPPED EARLY (rate limiting)"))
        if self.state.get("fallback_to_processing"):
            print(emoji.safe("📄 Mode: PROCESSING EXISTING DATA"))
        
        # Failure tracking
        consecutive_failures = self.state.get("consecutive_failures", 0)
        if consecutive_failures > 0:
            print(emoji.safe(f"⚠️ Consecutive failures: {consecutive_failures}"))
        
        # Phase status with detailed metrics
        search_status = "✅" if self.state["search_completed"] else "⏳"
        processing_status = "✅" if self.state["processing_completed"] else "⏳"
        upload_status = "✅" if self.state["sheets_uploaded"] else "⏳"
        
        print(emoji.safe(f"\n📋 Phase Status:"))
        print(emoji.safe(f"   {search_status} Search: {self.state['md_files_generated']} MD files, {self.state['factset_files_generated']} FactSet"))
        print(emoji.safe(f"   {processing_status} Processing: {self.state['companies_found']} companies"))
        print(emoji.safe(f"   {upload_status} Upload: {'Complete' if self.state['sheets_uploaded'] else 'Pending'}"))
        
        # Performance metrics
        metrics = self.state.get("performance_metrics", {})
        if any(metrics.values()):
            print(emoji.safe(f"\n⏱️ Performance Metrics:"))
            for phase, duration in metrics.items():
                if duration > 0:
                    print(f"   {phase.replace('_', ' ').title()}: {duration:.1f} seconds")
        
        # Priority breakdown
        stats = self.state.get("priority_stats", {})
        if any(stats.values()):
            print(emoji.safe(f"\n🎯 Priority Statistics:"))
            print(emoji.safe(f"   🔴 High: {stats.get('high_priority_successful', 0)}/{stats.get('high_priority_processed', 0)} successful"))
            print(emoji.safe(f"   🟡 Medium: {stats.get('medium_priority_successful', 0)}/{stats.get('medium_priority_processed', 0)} successful"))
            print(emoji.safe(f"   🟢 Low: {stats.get('low_priority_successful', 0)}/{stats.get('low_priority_processed', 0)} successful"))
        
        # Recent error information
        if self.state.get("last_error"):
            error = self.state["last_error"]
            print(emoji.safe(f"\n❌ Last Error ({error.get('phase', 'unknown')}):"))
            print(f"   Type: {error.get('error_type', 'general')}")
            print(f"   Message: {error['message']}")
            print(f"   Time: {error['timestamp']}")
            if error.get('retry_count', 0) > 0:
                print(f"   Retries: {error['retry_count']}")
        
        # Recommendations
        recommendations = self.get_recommendations()
        if recommendations:
            print(emoji.safe(f"\n💡 Recommendations:"))
            for rec in recommendations:
                print(f"   {rec}")
        
        next_phase = self.get_next_phase()
        if next_phase != "complete":
            print(emoji.safe(f"\n🔄 Next Phase: {next_phase}"))
        else:
            print(emoji.safe(f"\n🎉 Workflow Complete!"))

# ============================================================================
# PRODUCTION PIPELINE IMPLEMENTATION
# ============================================================================

class ProductionFactSetPipeline:
    """Production-ready FactSet pipeline with enhanced error handling and immediate stop strategy"""
    
    def __init__(self, config_file=None):
        self.logger = setup_logging()
        self.config = ProductionConfig(config_file)
        self.state = ProductionWorkflowState()
        self.rate_protector = AdvancedRateLimitProtector(self.config)
        
        # Create necessary directories
        self._setup_directories()
        
        self.logger.info(emoji.safe(f"🚀 Production FactSet Pipeline v{__version__} initialized"))
    
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
        """Analyze existing data to determine optimal strategy"""
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
    
    def determine_optimal_strategy(self, existing_files, data_status):
        """Determine optimal execution strategy"""
        self.logger.info(emoji.safe(f"🎯 Determining optimal strategy..."))
        self.logger.info(emoji.safe(f"   📄 Existing files: {existing_files}"))
        self.logger.info(emoji.safe(f"   📊 Data status: {data_status}"))
        
        # Check rate limiting status
        if self.state.is_rate_limited():
            strategy = "process_existing"
            reason = "Rate limiting detected - focus on existing data"
        elif data_status in ["excellent", "good"]:
            strategy = "maintenance"
            reason = "Sufficient data exists - maintenance updates only"
        elif data_status == "moderate":
            strategy = "selective_enhancement"
            reason = "Moderate data - selective enhancement"
        else:
            strategy = "comprehensive_collection"
            reason = "Insufficient data - comprehensive collection needed"
        
        self.logger.info(emoji.safe(f"   🎯 Strategy: {strategy.upper()}"))
        self.logger.info(emoji.safe(f"   📝 Reason: {reason}"))
        
        return strategy
    
    def test_search_availability(self):
        """Test if search API is currently available"""
        self.logger.info(emoji.safe("🧪 Testing search API availability..."))
        
        try:
            api_key = self.config.get('search.api_key')
            cse_id = self.config.get('search.cse_id')
            
            if not api_key or not cse_id:
                self.logger.warning(emoji.safe("⚠️ Search API credentials not configured"))
                return False
            
            import requests
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cse_id,
                'q': 'test search',
                'num': 1
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(emoji.safe("✅ Search API is accessible"))
                return True
            elif response.status_code == 429:
                self.logger.warning(emoji.safe("🚨 Search API is rate limited"))
                self.state.mark_error("API rate limiting detected", "search", "rate_limiting")
                return False
            else:
                self.logger.warning(emoji.safe(f"⚠️ Search API returned {response.status_code}"))
                return False
                
        except Exception as e:
            self.logger.error(emoji.safe(f"❌ Search API test failed: {e}"))
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
    
    def run_intelligent_search_phase(self, strategy="comprehensive_collection", force=False):
        """Run search phase with immediate stop on rate limiting"""
        if self.state.state["search_completed"] and not force:
            self.logger.info(emoji.safe("ℹ️ Search phase already completed (use --force to re-run)"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe(f"🔍 PHASE 1: INTELLIGENT SEARCH EXECUTION"))
        self.logger.info(emoji.safe(f"📊 Strategy: {strategy.upper()}"))
        self.logger.info("="*80)
        
        # Skip search if strategy indicates processing existing data
        if strategy == "process_existing":
            self.logger.info(emoji.safe("📄 Strategy indicates processing existing data only"))
            return self._fallback_to_existing_data(start_time)
        
        # Test search availability before proceeding
        if not self.test_search_availability():
            self.logger.warning(emoji.safe("🚨 Search API not available - switching to existing data processing"))
            return self._fallback_to_existing_data(start_time)
        
        try:
            # Load target companies
            if not self.config.config.get('target_companies'):
                self.logger.info(emoji.safe("📥 Loading target companies..."))
                if not self.config.download_watchlist():
                    self.logger.error(emoji.safe("❌ Failed to load target companies"))
                    return False
            
            companies = self.config.config['target_companies']
            self.logger.info(emoji.safe(f"🎯 Loaded {len(companies)} target companies"))
            
            # Determine company subset based on strategy
            if strategy == "maintenance":
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
                stopped_early = self.rate_protector.should_stop_search_immediately()
                
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
                
                self.state.mark_error("Search execution failed", "search")
                return False
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "too many requests" in error_str:
                self.logger.error(emoji.safe("🛑 Rate limiting detected - switching to data processing"))
                self.state.mark_error(f"Rate limiting: {e}", "search", "rate_limiting")
                return self._fallback_to_existing_data(start_time)
            
            duration = time.time() - start_time
            self.state.mark_error(f"Search phase error: {e}", "search")
            self.logger.error(emoji.safe(f"❌ Search phase failed: {e}"))
            
            # Check for existing data as fallback
            existing_files, _ = self.analyze_existing_data()
            if existing_files > 0:
                self.logger.info(emoji.safe("📄 Found existing data - continuing with processing"))
                return self._fallback_to_existing_data(start_time)
            
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
            
            # Wrap search execution with rate limit monitoring
            original_search = getattr(search_module, 'search_company_factset_data', None)
            if not original_search:
                self.logger.error(emoji.safe("❌ search_company_factset_data function not found"))
                return False
            
            # Create a wrapper that monitors for 429 errors
            def monitored_search(*args, **kwargs):
                try:
                    # Check if we should stop before each search
                    if self.rate_protector.should_stop_search_immediately():
                        self.logger.warning(emoji.safe("🛑 Search stopped - rate limiting detected"))
                        return []
                    
                    return original_search(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "too many requests" in error_str or "rate limit" in error_str:
                        self.rate_protector.record_429_error()
                        self.state.mark_error(f"Rate limiting: {e}", "search", "rate_limiting")
                        self.logger.error(emoji.safe("🛑 IMMEDIATE STOP: Rate limiting detected"))
                        # Return empty results to stop gracefully
                        return []
                    else:
                        raise e
            
            # Replace the original function
            search_module.search_company_factset_data = monitored_search
            
            # Also wrap the batch processing if it exists
            if hasattr(search_module, 'process_batch_search'):
                original_batch = search_module.process_batch_search
                
                def monitored_batch_search(*args, **kwargs):
                    try:
                        # Check rate limiting before each batch
                        if self.rate_protector.should_stop_search_immediately():
                            self.logger.warning(emoji.safe("🛑 Batch search stopped - rate limiting detected"))
                            return []
                        
                        return original_batch(*args, **kwargs)
                    except Exception as e:
                        error_str = str(e).lower()
                        if "429" in error_str or "too many requests" in error_str:
                            self.rate_protector.record_429_error()
                            self.state.mark_error(f"Rate limiting in batch: {e}", "search", "rate_limiting")
                            return []
                        else:
                            raise e
                
                search_module.process_batch_search = monitored_batch_search
            
            # Check for enhanced search function
            if hasattr(search_module, 'run_enhanced_search_suite'):
                self.logger.info(emoji.safe("🔍 Using enhanced search suite with monitoring"))
                return search_module.run_enhanced_search_suite(
                    self.config.config,
                    priority_focus="high_only" if strategy == "maintenance" else "balanced"
                )
            elif hasattr(search_module, 'main'):
                self.logger.info(emoji.safe("🔍 Using basic search with protection"))
                return self._run_basic_search_protected(search_module, strategy)
            else:
                self.logger.error(emoji.safe("❌ No usable search function found"))
                return False
                
        except Exception as e:
            # Check if this is a rate limiting error
            error_str = str(e).lower()
            if "429" in error_str or "too many requests" in error_str:
                self.rate_protector.record_429_error()
                self.state.mark_error(f"Rate limiting: {e}", "search", "rate_limiting")
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
            if strategy == "maintenance":
                search_args = ['factset_search.py', '--priority-focus', 'high_only']
            elif strategy == "selective_enhancement":
                search_args = ['factset_search.py', '--priority-focus', 'top_30']
            else:
                search_args = ['factset_search.py', '--priority-focus', 'balanced']
            
            # Set new argv
            sys.argv = search_args
            
            # Run with timeout and error handling
            try:
                search_module.main()
                return True
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "too many requests" in error_str:
                    self.logger.error(emoji.safe("🚨 Rate limiting encountered during search"))
                    self.state.mark_error(f"Rate limiting: {e}", "search", "rate_limiting")
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
        """Run processing phase with enhanced error handling"""
        if self.state.state["processing_completed"] and not force:
            self.logger.info(emoji.safe("ℹ️ Processing phase already completed (use --force to re-run)"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe(f"📊 PHASE 2: ENHANCED DATA PROCESSING"))
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
                        
                        # Log quality metrics
                        if '當前EPS預估' in summary_df.columns:
                            companies_with_eps = len(summary_df[summary_df['當前EPS預估'].notna()])
                            self.logger.info(emoji.safe(f"💰 Companies with EPS data: {companies_with_eps}"))
                        
                        if '目標價' in summary_df.columns:
                            companies_with_targets = len(summary_df[summary_df['目標價'].notna()])
                            self.logger.info(emoji.safe(f"🎯 Companies with target prices: {companies_with_targets}"))
                            
                    except Exception as e:
                        self.logger.warning(emoji.safe(f"⚠️ Error analyzing results: {e}"))
                
                self.state.mark_processing_complete(companies_found, duration)
                self.logger.info(emoji.safe(f"✅ Processing completed: {companies_found} companies processed"))
                return True
            else:
                self.state.mark_error("Data processing failed", "processing")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.state.mark_error(f"Processing phase error: {e}", "processing")
            self.logger.error(emoji.safe(f"❌ Processing phase failed: {e}"))
            if self.config.get('debug'):
                traceback.print_exc()
            return False
    
    def run_enhanced_upload_phase(self, force=False):
        """Run upload phase with enhanced validation"""
        if self.state.state["sheets_uploaded"] and not force:
            self.logger.info(emoji.safe("ℹ️ Upload phase already completed (use --force to re-run)"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe(f"📈 PHASE 3: ENHANCED GOOGLE SHEETS UPLOAD"))
        self.logger.info("="*80)
        
        try:
            # Check for required files
            required_files = [
                self.config.get('output.summary_csv'),
                self.config.get('output.consolidated_csv')
            ]
            
            available_files = [f for f in required_files if f and os.path.exists(f)]
            
            if not available_files:
                self.logger.warning(emoji.safe("⚠️ No processed data files found for upload"))
                self.logger.info(emoji.safe("💡 Run processing phase first"))
                return False
            
            self.logger.info(emoji.safe(f"📄 Found {len(available_files)} files ready for upload"))
            
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
                    'consolidated_csv': self.config.get('output.consolidated_csv'),
                    'summary_csv': self.config.get('output.summary_csv'),
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
                
                self.logger.info(emoji.safe("✅ Upload completed successfully"))
                return True
            else:
                self.state.mark_error("Google Sheets upload failed", "upload")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.state.mark_error(f"Upload phase error: {e}", "upload")
            self.logger.error(emoji.safe(f"❌ Upload phase failed: {e}"))
            if self.config.get('debug'):
                traceback.print_exc()
            return False
    
    def run_complete_production_pipeline(self, force_all=False, skip_phases=None, execution_mode="intelligent"):
        """Run the complete production pipeline with intelligent orchestration and immediate stop strategy"""
        if skip_phases is None:
            skip_phases = []
        
        pipeline_start = time.time()
        
        self.logger.info(emoji.safe(f"🚀 Production FactSet Pipeline v{__version__}"))
        self.logger.info(emoji.safe(f"📅 Date: {__date__}"))
        self.logger.info(emoji.safe(f"👨‍💻 Author: {__author__}"))
        self.logger.info("=" * 80)
        
        # Analyze existing data and determine strategy
        existing_files, data_status = self.analyze_existing_data()
        optimal_strategy = self.determine_optimal_strategy(existing_files, data_status)
        
        # Initialize or resume workflow
        if force_all or not self.state.state.get("workflow_id"):
            self.state.start_workflow(optimal_strategy, execution_mode)
        
        # Load and display target companies
        if not self.config.config.get('target_companies'):
            self.config.download_watchlist()
        
        companies = self.config.config.get('target_companies', [])
        self.logger.info(emoji.safe(f"🎯 Target Companies: {len(companies)} companies loaded"))
        
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
        self.logger.info(emoji.safe("🎉 PRODUCTION PIPELINE EXECUTION COMPLETED!"))
        self.logger.info("="*80)
        self.logger.info(emoji.safe(f"📊 Success Rate: {success_phases}/{total_phases} phases"))
        self.logger.info(emoji.safe(f"⏱️ Total Duration: {total_duration:.1f} seconds"))
        
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
            self.state.print_comprehensive_status()
            return False
    
    def recover_workflow(self):
        """Intelligent workflow recovery with multiple strategies"""
        self.logger.info(emoji.safe("🔄 Attempting intelligent workflow recovery..."))
        
        # Display current status
        self.state.print_comprehensive_status()
        
        # Get recommendations
        recommendations = self.state.get_recommendations()
        if recommendations:
            self.logger.info(emoji.safe("💡 Recovery recommendations:"))
            for rec in recommendations:
                self.logger.info(emoji.safe(f"   {rec}"))
        
        # Determine recovery strategy
        if self.state.is_rate_limited():
            self.logger.warning(emoji.safe("🚨 Rate limiting detected - limited recovery options"))
            return self._recover_from_rate_limiting()
        
        if self.state.should_stop_on_failures():
            self.logger.warning(emoji.safe("⚠️ Too many consecutive failures"))
            return self._recover_from_failures()
        
        # Try to continue from where we left off
        next_phase = self.state.get_next_phase()
        self.logger.info(emoji.safe(f"🔄 Resuming from phase: {next_phase}"))
        
        if next_phase == "search":
            return self.run_intelligent_search_phase()
        elif next_phase == "processing":
            return self.run_enhanced_processing_phase()
        elif next_phase == "upload":
            return self.run_enhanced_upload_phase()
        else:
            self.logger.info(emoji.safe("✅ Workflow already complete"))
            return True
    
    def _recover_from_rate_limiting(self):
        """Recovery strategy for rate limiting scenarios"""
        self.logger.info(emoji.safe("🚨 Implementing rate limiting recovery strategy..."))
        
        # Try to process existing data
        existing_files, data_status = self.analyze_existing_data()
        
        if existing_files > 0:
            self.logger.info(emoji.safe(f"📄 Found {existing_files} existing files - processing available data"))
            
            # Run processing and upload phases only
            success = True
            
            if not self.state.state["processing_completed"]:
                success &= self.run_enhanced_processing_phase()
            
            if success and not self.state.state["sheets_uploaded"]:
                success &= self.run_enhanced_upload_phase()
            
            if success:
                self.logger.info(emoji.safe("✅ Successfully processed existing data during rate limiting"))
                return True
        
        self.logger.warning(emoji.safe("⚠️ No existing data available for processing"))
        self.logger.info(emoji.safe("💡 Wait for rate limiting to clear, then retry search"))
        return False
    
    def _recover_from_failures(self):
        """Recovery strategy for multiple failures"""
        self.logger.info(emoji.safe("🔧 Implementing failure recovery strategy..."))
        
        # Reset error counts
        self.state.state["consecutive_failures"] = 0
        self.state.save_state()
        
        # Try conservative approach
        self.logger.info(emoji.safe("🎯 Switching to conservative recovery mode"))
        
        return self.run_complete_production_pipeline(
            skip_phases=["search"],  # Skip problematic search
            execution_mode="recovery"
        )

# ============================================================================
# PRODUCTION CLI INTERFACE
# ============================================================================

def create_production_parser():
    """Create production-ready argument parser"""
    parser = argparse.ArgumentParser(
        description=f'Production FactSet Pipeline v{__version__} - Enhanced Rate Limiting Protection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Production Pipeline Examples:

  # Intelligent execution (recommended)
  python factset_pipeline.py                     # Auto-detect strategy with immediate stop
  python factset_pipeline.py --force-all         # Force complete refresh
  
  # Strategic execution modes
  python factset_pipeline.py --mode conservative  # Safe execution with delays
  python factset_pipeline.py --mode existing-only # Process existing data only
  python factset_pipeline.py --mode test-only     # Test components without search
  
  # Phase-specific execution
  python factset_pipeline.py --search-only       # Search phase only (with immediate stop)
  python factset_pipeline.py --process-only      # Processing phase only  
  python factset_pipeline.py --upload-only       # Upload phase only
  
  # Monitoring and recovery
  python factset_pipeline.py --status            # Comprehensive status
  python factset_pipeline.py --recover           # Intelligent recovery
  python factset_pipeline.py --reset             # Reset workflow state
  
  # Production operations
  python factset_pipeline.py --test-api          # Test API availability
  python factset_pipeline.py --analyze-data      # Analyze existing data

ENHANCED FEATURES:
- Immediate stop on 429 errors with fallback to data processing
- Robust URL parsing and error handling
- Smart fallback strategies when search fails

Windows Users: Use Command Prompt or PowerShell for best emoji support
        """
    )
    
    # Configuration options
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Execution modes
    execution_group = parser.add_mutually_exclusive_group()
    execution_group.add_argument('--mode', choices=['intelligent', 'conservative', 'existing-only', 'test-only'], 
                                default='intelligent', help='Execution mode')
    execution_group.add_argument('--search-only', action='store_true', help='Run search phase only')
    execution_group.add_argument('--process-only', action='store_true', help='Run processing phase only')
    execution_group.add_argument('--upload-only', action='store_true', help='Run upload phase only')
    
    # Control options
    parser.add_argument('--force-all', action='store_true', help='Force re-run all phases')
    parser.add_argument('--skip-phases', nargs='*', choices=['search', 'processing', 'upload'],
                       help='Skip specific phases')
    
    # Monitoring and recovery
    monitoring_group = parser.add_mutually_exclusive_group()
    monitoring_group.add_argument('--status', action='store_true', help='Show comprehensive status')
    monitoring_group.add_argument('--recover', action='store_true', help='Intelligent recovery')
    monitoring_group.add_argument('--reset', action='store_true', help='Reset workflow state')
    monitoring_group.add_argument('--test-api', action='store_true', help='Test API availability')
    monitoring_group.add_argument('--analyze-data', action='store_true', help='Analyze existing data')
    
    # Version info
    parser.add_argument('--version', action='version', 
                       version=f'Production FactSet Pipeline v{__version__}')
    
    return parser

def main():
    """Production main entry point with comprehensive error handling"""
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
        logger.info(emoji.safe(f"🚀 Production FactSet Pipeline v{__version__} started"))
        
        # Handle monitoring requests
        if args.status:
            pipeline.state.print_comprehensive_status()
            return
        
        if args.test_api:
            available = pipeline.test_search_availability()
            print(emoji.safe(f"🧪 API Status: {'✅ Available' if available else '❌ Unavailable/Rate Limited'}"))
            return
        
        if args.analyze_data:
            existing_files, data_status = pipeline.analyze_existing_data()
            strategy = pipeline.determine_optimal_strategy(existing_files, data_status)
            print(emoji.safe(f"\n💡 Recommended action based on analysis:"))
            if strategy == "process_existing":
                print("   python factset_pipeline.py --mode existing-only")
            elif strategy == "maintenance":
                print("   python factset_pipeline.py --mode conservative")
            else:
                print("   python factset_pipeline.py --mode intelligent")
            return
        
        if args.reset:
            preserve = not args.force_all  # Don't preserve if force-all
            pipeline.state.reset_workflow(preserve_learnings=preserve)
            return
        
        if args.recover:
            success = pipeline.recover_workflow()
            sys.exit(0 if success else 1)
        
        # Handle execution requests
        success = False
        
        if args.search_only:
            existing_files, data_status = pipeline.analyze_existing_data()
            strategy = pipeline.determine_optimal_strategy(existing_files, data_status)
            success = pipeline.run_intelligent_search_phase(strategy, force=args.force_all)
            
        elif args.process_only:
            success = pipeline.run_enhanced_processing_phase(force=args.force_all)
            
        elif args.upload_only:
            success = pipeline.run_enhanced_upload_phase(force=args.force_all)
            
        else:
            # Full pipeline execution
            skip_phases = args.skip_phases or []
            
            # Map execution mode to strategy
            if args.mode == "existing-only":
                skip_phases.append("search")
            elif args.mode == "test-only":
                skip_phases.extend(["search", "upload"])
            
            success = pipeline.run_complete_production_pipeline(
                force_all=args.force_all,
                skip_phases=skip_phases,
                execution_mode=args.mode
            )
        
        # Provide helpful guidance on failure
        if not success:
            logger.error(emoji.safe("\n💡 Troubleshooting suggestions:"))
            logger.error("1. Check status: python factset_pipeline.py --status")
            logger.error("2. Test API access: python factset_pipeline.py --test-api")
            logger.error("3. Analyze data: python factset_pipeline.py --analyze-data")
            logger.error("4. Try conservative mode: python factset_pipeline.py --mode conservative")
            logger.error("5. Process existing data: python factset_pipeline.py --mode existing-only")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning(emoji.safe("\n⚠️ Pipeline interrupted by user"))
        logger.info(emoji.safe("💡 Use --recover to resume from where you left off"))
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(emoji.safe(f"❌ Pipeline execution failed: {e}"))
        if args.debug:
            logger.error("Debug traceback:", exc_info=True)
        else:
            logger.error("Run with --debug for detailed error information")
        
        try:
            # Try to log error to workflow state
            pipeline = ProductionFactSetPipeline(args.config)
            pipeline.state.mark_error(str(e), "pipeline", "system_error")
        except:
            pass  # Don't fail on logging failure
        
        logger.error(emoji.safe("\n💡 Recovery options:"))
        logger.error("1. Use --recover for intelligent recovery")
        logger.error("2. Check --status for current state")
        logger.error("3. Try --mode existing-only if search fails")
        
        sys.exit(1)

if __name__ == "__main__":
    main()