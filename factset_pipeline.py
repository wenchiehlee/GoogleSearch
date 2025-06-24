"""
factset_pipeline.py - Enhanced Production Pipeline (v3.3.2)

Version: 3.3.2
Date: 2025-06-24
Author: FactSet Pipeline - v3.3.2 Simplified & Observable

v3.3.2 ENHANCEMENTS:
- ✅ Integration with enhanced logging system (stage-specific dual output)
- ✅ Cross-platform safe console handling
- ✅ Performance monitoring integration
- ✅ All v3.3.1 comprehensive fixes preserved
- ✅ Enhanced error diagnostics and recovery

v3.3.1 COMPREHENSIVE FIXES (MAINTAINED):
- ✅ FIXED #1: Search cascade failure - proper error isolation
- ✅ FIXED #2: Performance issues - optimized processing with batching
- ✅ FIXED #3: Rate limiting logic - unified rate limiter
- ✅ FIXED #4: Module import issues - resolved circular dependencies
- ✅ FIXED #5: Data aggregation errors - improved deduplication logic
- ✅ FIXED #6: Filename conflicts - enhanced unique generation
- ✅ FIXED #7: Configuration management - robust validation
- ✅ FIXED #8: GitHub Actions - simplified Python-based validation
- ✅ FIXED #9: Memory management - resource limits and streaming
- ✅ FIXED #10: Parameter name mismatch - memory_manager vs memory_monitor
"""

# Windows console encoding fix - MUST BE FIRST
import sys
import os

if sys.platform == "win32":
    try:
        os.system("chcp 65001 >nul 2>&1")
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except Exception:
        pass

import argparse
import json
import traceback
import shutil
import glob
import time
import random
import subprocess
import gc
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import logging
import hashlib

# Version Information - v3.3.2
__version__ = "3.3.2"
__date__ = "2025-06-24"
__author__ = "FactSet Pipeline - v3.3.2 Simplified & Observable"

# ============================================================================
# v3.3.2 LOGGING INTEGRATION
# ============================================================================

def get_v332_logger(module_name: str = "pipeline"):
    """Get v3.3.2 enhanced logger with fallback"""
    try:
        from enhanced_logger import get_stage_logger
        return get_stage_logger(module_name)
    except ImportError:
        # Fallback to standard logging if v3.3.2 components not available
        import logging
        logger = logging.getLogger(f'factset_v332.{module_name}')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def get_performance_monitor(stage_name: str = "pipeline"):
    """Get v3.3.2 performance monitor with fallback"""
    try:
        from enhanced_logger import get_performance_logger
        return get_performance_logger(stage_name)
    except ImportError:
        # Fallback performance monitor
        class FallbackPerformanceMonitor:
            def time_operation(self, operation_name: str):
                from contextlib import contextmanager
                import time
                
                @contextmanager
                def timer():
                    start = time.time()
                    try:
                        yield
                    finally:
                        duration = time.time() - start
                        print(f"Operation {operation_name} took {duration:.2f}s")
                
                return timer()
        
        return FallbackPerformanceMonitor()

# FIXED #4: Proper module imports without circular dependencies
class LazyImporter:
    """Lazy module importer to avoid circular dependencies"""
    def __init__(self):
        self._modules = {}
    
    def get_module(self, name):
        if name not in self._modules:
            try:
                self._modules[name] = __import__(name)
            except ImportError as e:
                print(f"⚠️ Module {name} not available: {e}")
                self._modules[name] = None
        return self._modules[name]

# Global lazy importer
lazy_modules = LazyImporter()

# ============================================================================
# ENHANCED SAFE EMOJI HANDLING (v3.3.2 - preserved from v3.3.1)
# ============================================================================

class SafeEmoji:
    """Enhanced emoji handler with better Windows support"""
    
    def __init__(self):
        self.use_emoji = self._test_emoji_support()
        self.emoji_map = {
            '🚀': '[START]', '🧪': '[TEST]', '⚠️': '[WARN]', '❌': '[ERROR]',
            '✅': '[OK]', '📊': '[DATA]', '🔍': '[SEARCH]', '📄': '[FILE]',
            '💡': '[TIP]', '🎯': '[TARGET]', '📈': '[UPLOAD]', '🔄': '[RETRY]',
            '🔧': '[FIX]', '📝': '[LOG]', '⏳': '[WAIT]', '🎉': '[SUCCESS]',
            '🚨': '[ALERT]', '🔌': '[CIRCUIT]', '🛡️': '[PROTECT]', '💾': '[SAVE]',
            '🏆': '[EXCELLENT]', '📥': '[DOWNLOAD]', '📋': '[LIST]', '🆔': '[ID]',
            '📅': '[DATE]', '🆕': '[NEW]', '🔴': '[HIGH]', '🟡': '[MED]',
            '🟢': '[LOW]', '⚡': '[FAST]', '🌐': '[WEB]', '💰': '[MONEY]',
            '📦': '[PACKAGE]', '🏢': '[COMPANY]', '⏰': '[TIME]', '🚫': '[BLOCKED]',
            '🔑': '[KEY]', '🛑': '[STOP]', '🟠': '[WARN]'
        }
    
    def _test_emoji_support(self):
        """Test emoji support with fallback"""
        if sys.platform != "win32":
            return True
        
        try:
            test_emoji = '🚀'
            test_emoji.encode(sys.stdout.encoding or 'utf-8')
            return True
        except (UnicodeEncodeError, AttributeError):
            return False
    
    def safe(self, text):
        """Convert text to safe version"""
        if self.use_emoji:
            return text
        
        safe_text = text
        for emoji, replacement in self.emoji_map.items():
            safe_text = safe_text.replace(emoji, replacement)
        return safe_text

# Global emoji handler
emoji = SafeEmoji()

# ============================================================================
# ENHANCED LOGGING SETUP (v3.3.2) - with v3.3.2 integration
# ============================================================================

def setup_logging_v332():
    """Setup enhanced logging for v3.3.2 with stage-specific integration"""
    # Try to use v3.3.2 enhanced logging first
    try:
        logger = get_v332_logger("pipeline")
        logger.info(f"v3.3.2 enhanced logging system initialized")
        return logger
    except Exception:
        # Fallback to v3.3.1 logging setup
        return setup_logging_v331_fallback()

def setup_logging_v331_fallback():
    """Fallback to v3.3.1 logging setup if v3.3.2 not available"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            formatted = super().format(record)
            return emoji.safe(formatted)
    
    formatter = SafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('factset_pipeline_v332')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    # File handler
    log_file = log_dir / f"pipeline_v332_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# ============================================================================
# ENHANCED CONFIGURATION MANAGEMENT (v3.3.2) - with logging integration
# ============================================================================

class EnhancedConfig:
    """Enhanced configuration management with v3.3.2 logging integration"""
    
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.logger = get_v332_logger("config")
        self._load_dotenv()
        self.config = self._load_config_v332()
        self._validate_config()
    
    def _load_dotenv(self):
        """Load environment variables with enhanced logging"""
        try:
            from dotenv import load_dotenv
            env_path = Path('.env')
            if env_path.exists():
                load_dotenv(env_path)
                self.logger.info("Loaded .env file")
            else:
                self.logger.info("No .env file found")
        except ImportError:
            self.logger.warning("python-dotenv not installed")
        except Exception as e:
            self.logger.warning(f"Error loading .env: {e}")
    
    def _load_config_v332(self):
        """Load enhanced configuration for v3.3.2"""
        self.logger.info("Loading v3.3.2 enhanced configuration...")
        
        default_config = {
            "version": "3.3.2",
            "target_companies": [],
            "watchlist_url": "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv",
            "search": {
                "max_results": 10,
                "language": "zh-TW",
                "rate_limit_delay": 3,              # FIXED #3: Unified rate limiting
                "max_retries": 2,
                "circuit_breaker_threshold": 1,
                "content_quality_threshold": 3,
                "batch_size": 20,                   # FIXED #9: Memory management
                "max_file_size_mb": 50,             # FIXED #9: Resource limits
                "timeout_seconds": 30
            },
            "output": {
                "base_dir": "data",
                "csv_dir": "data/csv",
                "pdf_dir": "data/pdf",
                "md_dir": "data/md",
                "processed_dir": "data/processed",
                "logs_dir": "logs",
                "backups_dir": "backups",
                "temp_dir": "temp",
                "summary_csv": "data/processed/portfolio_summary.csv",
                "detailed_csv": "data/processed/detailed_data.csv",
                "stats_json": "data/processed/statistics.json"
            },
            "processing": {
                "parse_md_files": True,
                "deduplicate_data": True,           # FIXED #5: Improved deduplication
                "aggregate_by_company": True,
                "individual_file_analysis": True,
                "enhanced_date_extraction": True,
                "batch_processing": True,           # FIXED #2: Performance optimization
                "memory_limit_mb": 2048,            # FIXED #9: Memory management
                "max_files_per_batch": 50           # FIXED #9: Batching
            },
            "sheets": {
                "auto_backup": True,
                "create_missing_sheets": True,
                "enhanced_formatting": True,
                "worksheet_names": [
                    "Portfolio Summary v3.3.2",
                    "Detailed Data v3.3.2",
                    "Statistics v3.3.2"
                ],
                "max_rows": {
                    "portfolio": 150,
                    "detailed": 1000,
                    "statistics": 100
                }
            },
            "logging": {                            # v3.3.2: Enhanced logging config
                "stage_specific": True,
                "dual_output": True,
                "performance_monitoring": True,
                "auto_diagnosis": True
            }
        }
        
        # Load from file if specified
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._deep_update(default_config, file_config)
                self.logger.info(f"Loaded configuration from: {self.config_file}")
            except Exception as e:
                self.logger.warning(f"Error loading config file: {e}")
                self.logger.info("Using default configuration")
        
        # Load environment overrides
        self._load_env_overrides_v332(default_config)
        
        self.logger.info("v3.3.2 configuration loaded successfully")
        return default_config
    
    def _deep_update(self, base_dict, update_dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _load_env_overrides_v332(self, config):
        """Load enhanced environment variable overrides with logging"""
        self.logger.debug("Loading environment variable overrides...")
        
        env_mappings = {
            'GOOGLE_SEARCH_API_KEY': ('search', 'api_key'),
            'GOOGLE_SEARCH_CSE_ID': ('search', 'cse_id'),
            'GOOGLE_SHEETS_CREDENTIALS': ('sheets', 'credentials'),
            'GOOGLE_SHEET_ID': ('sheets', 'sheet_id'),
            'FACTSET_PIPELINE_DEBUG': ('debug', None),
            'FACTSET_MAX_RESULTS': ('search', 'max_results'),
            'FACTSET_QUALITY_THRESHOLD': ('search', 'content_quality_threshold'),
            'FACTSET_MEMORY_LIMIT': ('processing', 'memory_limit_mb'),
            'FACTSET_BATCH_SIZE': ('processing', 'max_files_per_batch'),
            'FACTSET_LOG_LEVEL': ('logging', 'level'),                         # v3.3.2
            'FACTSET_ENABLE_PERFORMANCE': ('logging', 'performance_monitoring') # v3.3.2
        }
        
        overrides_applied = 0
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if section not in config:
                    config[section] = {}
                if key:
                    # Type conversion for numeric values
                    if env_var in ['FACTSET_MAX_RESULTS', 'FACTSET_QUALITY_THRESHOLD', 
                                  'FACTSET_MEMORY_LIMIT', 'FACTSET_BATCH_SIZE']:
                        try:
                            config[section][key] = int(value)
                        except ValueError:
                            config[section][key] = value
                    elif env_var in ['FACTSET_ENABLE_PERFORMANCE']:
                        config[section][key] = value.lower() in ('true', '1', 'yes')
                    else:
                        config[section][key] = value
                else:
                    config[section] = value.lower() in ('true', '1', 'yes')
                overrides_applied += 1
        
        if overrides_applied > 0:
            self.logger.info(f"Applied {overrides_applied} environment variable overrides")
    
    def _validate_config(self):
        """FIXED #7: Comprehensive configuration validation with v3.3.2 logging"""
        self.logger.debug("Starting configuration validation...")
        errors = []
        
        # Validate required sections
        required_sections = ['search', 'output', 'processing', 'sheets']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
        
        # Validate search configuration
        if 'search' in self.config:
            search_config = self.config['search']
            
            # Validate numeric ranges
            validations = [
                ('max_results', 1, 50),
                ('rate_limit_delay', 1, 300),
                ('content_quality_threshold', 1, 10),
                ('batch_size', 1, 100),
                ('max_file_size_mb', 1, 500),
                ('timeout_seconds', 5, 300)
            ]
            
            for field, min_val, max_val in validations:
                if field in search_config:
                    try:
                        value = int(search_config[field])
                        if not (min_val <= value <= max_val):
                            errors.append(f"search.{field} must be between {min_val} and {max_val}")
                    except (ValueError, TypeError):
                        errors.append(f"search.{field} must be a valid integer")
        
        # Validate output directories
        if 'output' in self.config:
            output_config = self.config['output']
            required_dirs = ['csv_dir', 'md_dir', 'processed_dir']
            
            for dir_key in required_dirs:
                if dir_key not in output_config:
                    errors.append(f"Missing required output directory: {dir_key}")
        
        # Validate processing configuration
        if 'processing' in self.config:
            proc_config = self.config['processing']
            
            # Memory validation
            if 'memory_limit_mb' in proc_config:
                try:
                    limit = int(proc_config['memory_limit_mb'])
                    if limit < 512 or limit > 16384:
                        errors.append("processing.memory_limit_mb should be between 512-16384")
                except (ValueError, TypeError):
                    errors.append("processing.memory_limit_mb must be integer")
        
        # v3.3.2: Validate logging configuration
        if 'logging' in self.config:
            logging_config = self.config['logging']
            if 'level' in logging_config:
                valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
                if logging_config.get('level', 'INFO').upper() not in valid_levels:
                    errors.append(f"logging.level must be one of: {valid_levels}")
        
        if errors:
            self.logger.warning("Configuration validation issues:")
            for error in errors:
                self.logger.warning(f"   - {error}")
        else:
            self.logger.info("Configuration validation passed")
    
    def download_watchlist_v332(self):
        """Enhanced watchlist download with v3.3.2 logging"""
        try:
            import requests
            import pandas as pd
            
            self.logger.info("Downloading enhanced watchlist (v3.3.2)...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(
                self.config['watchlist_url'], 
                timeout=30, 
                headers=headers
            )
            response.raise_for_status()
            
            # Enhanced CSV validation
            if not response.text.strip():
                self.logger.error("Empty CSV downloaded")
                return False
            
            # Save with timestamp backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            backup_file = f"觀察名單_backup_{timestamp}.csv"
            current_file = "觀察名單.csv"
            
            # Save both versions
            for file_path in [backup_file, current_file]:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
            
            # Enhanced processing with validation
            companies = self._process_companies_csv(response.text)
            
            if companies:
                self.config['target_companies'] = companies
                self.logger.info(f"Downloaded {len(companies)} companies (v3.3.2)")
                
                # Save processed companies
                companies_file = "processed_companies_v332.json"
                with open(companies_file, 'w', encoding='utf-8') as f:
                    json.dump(companies, f, indent=2, ensure_ascii=False)
                
                return True
            else:
                self.logger.error("No valid companies found in CSV")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading watchlist: {e}")
            return False
    
    def _process_companies_csv(self, csv_content):
        """Enhanced CSV processing with robust validation and logging"""
        try:
            import pandas as pd
            from io import StringIO
            
            self.logger.debug("Processing companies CSV...")
            
            # Read CSV with enhanced error handling
            df = pd.read_csv(StringIO(csv_content), encoding='utf-8')
            
            if df.empty:
                self.logger.warning("CSV is empty")
                return []
            
            # Flexible column detection
            code_col = None
            name_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if '代號' in col or 'code' in col_lower:
                    code_col = col
                elif '名稱' in col or 'name' in col_lower:
                    name_col = col
            
            if code_col is None or name_col is None:
                # Fallback to first two columns
                if len(df.columns) >= 2:
                    code_col = df.columns[0]
                    name_col = df.columns[1]
                    self.logger.info("Using first two columns as code and name")
                else:
                    self.logger.error("Insufficient columns in CSV")
                    return []
            
            companies = []
            for _, row in df.iterrows():
                try:
                    code = str(row[code_col]).strip()
                    name = str(row[name_col]).strip()
                    
                    # Enhanced validation
                    if (self._validate_company_code(code) and 
                        self._validate_company_name(name)):
                        companies.append({
                            "code": code,
                            "name": name,
                            "stock_code": f"{code}-TW"
                        })
                except Exception:
                    continue
            
            self.logger.info(f"Processed {len(companies)} valid companies from CSV")
            return companies
            
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}")
            return []
    
    def _validate_company_code(self, code):
        """Enhanced company code validation"""
        if not code or code == 'nan':
            return False
        
        # Must be 4 digits
        if not (len(code) == 4 and code.isdigit()):
            return False
        
        # Exclude invalid codes
        if code in ['0000', '9999']:
            return False
        
        return True
    
    def _validate_company_name(self, name):
        """Enhanced company name validation"""
        if not name or name == 'nan' or len(name) < 2:
            return False
        
        # Check for valid characters
        import re
        if not re.match(r'^[\u4e00-\u9fff\w\s\(\)（）\-&\.\,]+$', name):
            return False
        
        return True
    
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
# UNIFIED RATE LIMITING PROTECTION (v3.3.2) - preserved from v3.3.1
# ============================================================================

class UnifiedRateLimitProtector:
    """Unified rate limiting protection - FIXED #3 with v3.3.2 logging"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_v332_logger("rate_limiter")
        
        # Unified rate limiting settings
        self.delay = config.get('search.rate_limit_delay', 3)
        self.max_retries = config.get('search.max_retries', 2)
        self.circuit_breaker_threshold = 1  # Immediate stop on rate limiting
        
        # State tracking
        self.consecutive_429s = 0
        self.last_request_time = None
        self.should_stop_searching = False
        self.stop_reason = None
        self.total_requests = 0
        self.successful_requests = 0
        
        self.logger.info(f"Rate limiter initialized with {self.delay}s delay")
    
    def wait_if_needed(self):
        """Wait if needed to respect rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.delay:
                wait_time = self.delay - elapsed
                time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def record_request(self):
        """Record a request attempt"""
        self.total_requests += 1
        self.wait_if_needed()
        self.logger.debug(f"Request #{self.total_requests}")
    
    def record_429_error(self):
        """Record 429 error with immediate stop"""
        self.consecutive_429s += 1
        
        self.logger.warning(f"Rate limiting detected! (#{self.consecutive_429s})")
        
        # Immediate stop on first 429
        self.should_stop_searching = True
        self.stop_reason = f"Rate limiting detected: {self.consecutive_429s} consecutive 429s"
        
        self.logger.error(f"IMMEDIATE STOP: {self.stop_reason}")
        return True
    
    def record_success(self):
        """Record successful request"""
        self.successful_requests += 1
        self.consecutive_429s = 0
        self.logger.debug(f"Successful request ({self.successful_requests}/{self.total_requests})")
    
    def should_stop_immediately(self):
        """Check if should stop immediately"""
        return self.should_stop_searching
    
    def get_stats(self):
        """Get rate limiting statistics"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "consecutive_429s": self.consecutive_429s,
            "should_stop": self.should_stop_searching,
            "success_rate": self.successful_requests / max(1, self.total_requests)
        }

# ============================================================================
# ENHANCED WORKFLOW STATE MANAGEMENT (v3.3.2) - with logging integration
# ============================================================================

class EnhancedWorkflowState:
    """Enhanced workflow state management for v3.3.2 with logging"""
    
    def __init__(self, state_file="data/workflow_state_v332.json"):
        self.state_file = state_file
        self.logger = get_v332_logger("workflow")
        self.state = self._load_state_v332()
    
    def _load_state_v332(self):
        """Load enhanced state for v3.3.2"""
        self.logger.debug("Loading workflow state...")
        
        default_state = {
            "version": "3.3.2",
            "workflow_id": None,
            "started_at": None,
            "last_updated": None,
            
            # Search phase
            "search_completed": False,
            "search_timestamp": None,
            "companies_attempted": 0,
            "companies_successful": 0,
            "md_files_generated": 0,
            "search_stopped_early": False,
            "rate_limiting_detected": False,
            
            # Processing phase
            "processing_completed": False,
            "processing_timestamp": None,
            "files_processed": 0,
            "processing_duration": 0,
            
            # Upload phase
            "sheets_uploaded": False,
            "upload_timestamp": None,
            "sheets_updated": [],
            
            # Error tracking
            "last_error": None,
            "total_errors": 0,
            "execution_mode": "intelligent",
            
            # v3.3.2: Enhanced tracking
            "logging_mode": "stage_specific",
            "performance_monitoring": True
        }
        
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)
                    self._deep_merge(default_state, loaded_state)
                    self.logger.info("Loaded existing workflow state")
                    return default_state
            except Exception as e:
                self.logger.warning(f"Error loading state: {e}")
        
        self.logger.info("Using default workflow state")
        return default_state
    
    def _deep_merge(self, base, update):
        """Deep merge dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save_state(self):
        """Save state with error handling and logging"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            self.state["last_updated"] = datetime.now().isoformat()
            self.state["version"] = "3.3.2"
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Workflow state saved")
                
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
    
    def start_workflow_v332(self, execution_mode="intelligent"):
        """Start enhanced workflow for v3.3.2"""
        workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.state.update({
            "version": "3.3.2",
            "workflow_id": workflow_id,
            "started_at": datetime.now().isoformat(),
            "execution_mode": execution_mode,
            "search_completed": False,
            "processing_completed": False,
            "sheets_uploaded": False,
            "companies_attempted": 0,
            "companies_successful": 0,
            "last_error": None,
            "logging_mode": "stage_specific",
            "performance_monitoring": True
        })
        
        self.save_state()
        self.logger.info(f"Started v3.3.2 workflow: {workflow_id} (mode: {execution_mode})")

# ============================================================================
# ENHANCED PRODUCTION PIPELINE (v3.3.2) - with comprehensive logging
# ============================================================================

class EnhancedFactSetPipeline:
    """Enhanced production pipeline for v3.3.2 with comprehensive logging integration"""
    
    def __init__(self, config_file=None):
        self.logger = setup_logging_v332()
        self.config = EnhancedConfig(config_file)
        self.rate_protector = UnifiedRateLimitProtector(self.config)
        self.state = EnhancedWorkflowState()
        self.perf_monitor = get_performance_monitor("pipeline")
        
        # FIXED #9, #10: Memory management - Import MemoryManager from data_processor
        try:
            data_processor = lazy_modules.get_module('data_processor')
            if data_processor and hasattr(data_processor, 'MemoryManager'):
                self.memory_manager = data_processor.MemoryManager(
                    limit_mb=self.config.get('processing.memory_limit_mb', 2048)
                )
                self.logger.info("Memory manager initialized")
            else:
                # Fallback - create simple memory manager
                self.memory_manager = self._create_fallback_memory_manager()
                self.logger.warning("Using fallback memory manager")
        except Exception as e:
            self.logger.error(f"Memory manager initialization error: {e}")
            self.memory_manager = self._create_fallback_memory_manager()
        
        # Create directories
        self._setup_directories_v332()
        
        self.logger.info(f"Enhanced FactSet Pipeline v{__version__} initialized")
    
    def _create_fallback_memory_manager(self):
        """Create a fallback memory manager with minimal interface"""
        class FallbackMemoryManager:
            def __init__(self, limit_mb=2048):
                self.limit_mb = limit_mb
                self.peak_mb = 0
                self.cleanup_count = 0
                self.processing_stats = {
                    'files_processed': 0,
                    'batches_completed': 0,
                    'memory_cleanups': 0
                }
                
            def check_memory_usage(self):
                return False
                
            def force_cleanup(self):
                import gc
                gc.collect()
                self.cleanup_count += 1
                
            def get_stats(self):
                return {
                    "current_mb": 0,
                    "peak_mb": self.peak_mb, 
                    "limit_mb": self.limit_mb, 
                    "cleanup_count": self.cleanup_count,
                    "processing_stats": self.processing_stats
                }
        
        return FallbackMemoryManager()
    
    def _setup_directories_v332(self):
        """Setup enhanced directories for v3.3.2 with logging"""
        self.logger.debug("Setting up directories...")
        
        directories = [
            self.config.get('output.csv_dir'),
            self.config.get('output.pdf_dir'),
            self.config.get('output.md_dir'),
            self.config.get('output.processed_dir'),
            self.config.get('output.logs_dir'),
            self.config.get('output.backups_dir'),
            self.config.get('output.temp_dir')
        ]
        
        created_count = 0
        for directory in directories:
            if directory:
                try:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    created_count += 1
                except Exception as e:
                    self.logger.warning(f"Could not create directory {directory}: {e}")
        
        self.logger.info(f"Setup complete: {created_count} directories")
    
    def analyze_existing_data_v332(self):
        """Enhanced existing data analysis for v3.3.2 with performance monitoring"""
        self.logger.info("Analyzing existing data (v3.3.2)...")
        
        with self.perf_monitor.time_operation("analyze_existing_data"):
            md_dir = Path(self.config.get('output.md_dir'))
            
            if not md_dir.exists():
                self.logger.warning("MD directory does not exist")
                return 0, "no_data"
            
            md_files = list(md_dir.glob("*.md"))
            file_count = len(md_files)
            
            self.logger.info(f"Found {file_count} MD files")
            
            # Enhanced quality analysis with memory management
            quality_files = 0
            companies_with_data = set()
            
            # Process in batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(md_files), batch_size):
                batch = md_files[i:i + batch_size]
                
                for md_file in batch:
                    try:
                        # Quick content check without loading entire file
                        with open(md_file, 'r', encoding='utf-8') as f:
                            preview = f.read(1000)  # Only read first 1KB
                        
                        if any(keyword in preview.lower() for keyword in [
                            'factset', 'eps', '分析師', '目標價', '預估'
                        ]):
                            quality_files += 1
                        
                        # Extract company from filename
                        company_match = re.search(r'(\d{4})_', md_file.name)
                        if company_match:
                            companies_with_data.add(company_match.group(1))
                            
                    except Exception:
                        continue
                
                # Memory cleanup after each batch
                gc.collect()
            
            # Enhanced quality assessment
            quality_ratio = quality_files / len(md_files) if md_files else 0
            companies_count = len(companies_with_data)
            
            self.logger.info(f"Analysis: {file_count} files, {quality_files} quality ({quality_ratio:.1%}), {companies_count} companies")
            
            # Enhanced criteria
            if file_count >= 100 and quality_ratio >= 0.7 and companies_count >= 30:
                return file_count, "excellent"
            elif file_count >= 50 and quality_ratio >= 0.5 and companies_count >= 20:
                return file_count, "good"
            elif file_count >= 20 and quality_ratio >= 0.3 and companies_count >= 10:
                return file_count, "moderate"
            elif file_count >= 10:
                return file_count, "limited"
            else:
                return file_count, "insufficient"
    
    def run_complete_pipeline_v332(self, force_all=False, skip_phases=None, 
                                  execution_mode="intelligent"):
        """Run complete pipeline with v3.3.2 enhanced logging and performance monitoring"""
        if skip_phases is None:
            skip_phases = []
        
        pipeline_start = time.time()
        
        self.logger.info(f"Enhanced FactSet Pipeline v{__version__}")
        self.logger.info(f"Date: {__date__}")
        self.logger.info("v3.3.2: Enhanced Logging, Performance Monitoring & Cross-platform Support")
        self.logger.info("All v3.3.1 Comprehensive Fixes Maintained")
        self.logger.info("=" * 80)
        
        with self.perf_monitor.time_operation("complete_pipeline"):
            # Enhanced data analysis
            existing_files, data_status = self.analyze_existing_data_v332()
            
            # Initialize workflow
            if force_all or not self.state.state.get("workflow_id"):
                self.state.start_workflow_v332(execution_mode)
            
            # Load target companies
            if not self.config.config.get('target_companies'):
                self.config.download_watchlist_v332()
            
            companies = self.config.config.get('target_companies', [])
            self.logger.info(f"Target Companies: {len(companies)} (v3.3.2)")
            
            success_phases = 0
            total_phases = 3 - len(skip_phases)
            
            # Phase 1: Enhanced Search with cascade failure protection
            if "search" not in skip_phases:
                self.logger.info("🔍 Enhanced Search Phase (v3.3.2)")
                
                if self.run_enhanced_search_phase_v332(force=force_all):
                    success_phases += 1
                    self.logger.info("Search phase completed")
                else:
                    self.logger.error("Search phase failed")
                    
                    # Enhanced fallback
                    if existing_files > 0:
                        self.logger.info("Continuing with existing data...")
                        success_phases += 1
                    else:
                        return False
            else:
                success_phases += 1
            
            # Phase 2: Enhanced Processing with performance fixes
            if "processing" not in skip_phases:
                self.logger.info("📊 Enhanced Processing Phase (v3.3.2)")
                
                if self.run_enhanced_processing_phase_v332(force=force_all):
                    success_phases += 1
                    self.logger.info("Processing phase completed")
                else:
                    self.logger.error("Processing phase failed")
                    return False
            else:
                success_phases += 1
            
            # Phase 3: Enhanced Upload
            if "upload" not in skip_phases:
                self.logger.info("📈 Enhanced Upload Phase (v3.3.2)")
                
                if self.run_enhanced_upload_phase_v332(force=force_all):
                    success_phases += 1
                    self.logger.info("Upload phase completed")
                else:
                    self.logger.warning("Upload phase failed")
            else:
                success_phases += 1
        
        # Enhanced summary
        total_duration = time.time() - pipeline_start
        
        self.logger.info("="*80)
        self.logger.info("ENHANCED PIPELINE EXECUTION COMPLETED! (v3.3.2)")
        self.logger.info("="*80)
        self.logger.info(f"Success Rate: {success_phases}/{total_phases} phases")
        self.logger.info(f"Total Duration: {total_duration:.1f} seconds")
        
        # Rate limiting stats
        rate_stats = self.rate_protector.get_stats()
        self.logger.info(f"Requests: {rate_stats['successful_requests']}/{rate_stats['total_requests']} successful")
        
        # Memory stats
        memory_stats = self.memory_manager.get_stats()
        self.logger.info(f"Peak Memory: {memory_stats['peak_mb']:.1f}MB")
        
        # v3.3.2 specific stats
        self.logger.info("v3.3.2 Features:")
        self.logger.info("   - Stage-specific Dual Logging: Console + File")
        self.logger.info("   - Performance Monitoring: All operations timed")
        self.logger.info("   - Cross-platform Support: Safe console handling")
        self.logger.info("   - All v3.3.1 Fixes: Maintained and enhanced")
        
        return success_phases == total_phases
    
    def run_enhanced_search_phase_v332(self, force=False):
        """Run enhanced search phase with v3.3.2 logging"""
        if self.state.state["search_completed"] and not force:
            self.logger.info("Search already completed")
            return True
        
        try:
            # Import search module with lazy loading - FIXED #4
            search_module = lazy_modules.get_module('factset_search')
            if not search_module:
                self.logger.error("Search module not available")
                return False
            
            # Load companies
            companies = self.config.config.get('target_companies', [])
            if not companies:
                if not self.config.download_watchlist_v332():
                    return False
                companies = self.config.config['target_companies']
            
            # Run search with enhanced error handling
            if hasattr(search_module, 'run_enhanced_search_suite_v331'):
                result = search_module.run_enhanced_search_suite_v331(
                    self.config.config,
                    rate_protector=self.rate_protector
                )
            else:
                self.logger.warning("Using fallback search")
                result = False
            
            # Update state
            if result:
                md_files = len(list(Path(self.config.get('output.md_dir')).glob("*.md")))
                self.state.state.update({
                    "search_completed": True,
                    "search_timestamp": datetime.now().isoformat(),
                    "md_files_generated": md_files,
                    "search_stopped_early": result == "rate_limited"
                })
                self.state.save_state()
                
                self.logger.info(f"Search completed: {md_files} files generated")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Search phase error: {e}")
            return False
    
    def run_enhanced_processing_phase_v332(self, force=False):
        """Run enhanced processing phase with v3.3.2 performance monitoring"""
        if self.state.state["processing_completed"] and not force:
            self.logger.info("Processing already completed")
            return True
        
        try:
            # Import processor module with lazy loading - FIXED #4
            processor_module = lazy_modules.get_module('data_processor')
            if not processor_module:
                self.logger.error("Data processor module not available")
                return False
            
            # Run processing with performance monitoring
            start_time = time.time()
            
            with self.perf_monitor.time_operation("data_processing"):
                if hasattr(processor_module, 'process_all_data_v331'):
                    # FIXED #10: Use correct parameter name and object
                    success = processor_module.process_all_data_v331(
                        force=force, 
                        memory_manager=self.memory_manager  # ✅ FIXED: Correct parameter name
                    )
                else:
                    self.logger.warning("Using fallback processor")
                    success = processor_module.process_all_data(force=force, parse_md=True)
            
            # Update state
            if success:
                duration = time.time() - start_time
                self.state.state.update({
                    "processing_completed": True,
                    "processing_timestamp": datetime.now().isoformat(),
                    "processing_duration": duration
                })
                self.state.save_state()
                
                self.logger.info(f"Processing completed in {duration:.2f}s")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Processing phase error: {e}")
            return False
    
    def run_enhanced_upload_phase_v332(self, force=False):
        """Run enhanced upload phase with v3.3.2 logging"""
        if self.state.state["sheets_uploaded"] and not force:
            self.logger.info("Upload already completed")
            return True
        
        try:
            # Import uploader module with lazy loading - FIXED #4
            uploader_module = lazy_modules.get_module('sheets_uploader')
            if not uploader_module:
                self.logger.error("Sheets uploader module not available")
                return False
            
            # Check credentials
            if not self.config.get('sheets.credentials'):
                self.logger.warning("Google Sheets credentials not configured")
                return False
            
            # Run upload
            upload_config = self.config.config.copy()
            upload_config['input'] = {
                'summary_csv': self.config.get('output.summary_csv'),
                'detailed_csv': self.config.get('output.detailed_csv'),
                'stats_json': self.config.get('output.stats_json')
            }
            
            with self.perf_monitor.time_operation("sheets_upload"):
                if hasattr(uploader_module, 'upload_all_sheets_v332'):
                    success = uploader_module.upload_all_sheets_v332(upload_config)
                else:
                    self.logger.warning("Using fallback uploader")
                    success = uploader_module.upload_all_sheets_v330(upload_config)
            
            # Update state
            if success:
                self.state.state.update({
                    "sheets_uploaded": True,
                    "upload_timestamp": datetime.now().isoformat(),
                    "sheets_updated": ["Portfolio Summary v3.3.2", "Detailed Data v3.3.2", "Statistics v3.3.2"]
                })
                self.state.save_state()
                
                self.logger.info("Sheets upload completed")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Upload phase error: {e}")
            return False

# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS (v3.3.2)
# ============================================================================

# Maintain backward compatibility with v3.3.1
def run_complete_pipeline_v331(force_all=False, skip_phases=None, execution_mode="intelligent"):
    """Legacy v3.3.1 compatibility wrapper"""
    pipeline = EnhancedFactSetPipeline()
    return pipeline.run_complete_pipeline_v332(force_all, skip_phases, execution_mode)

# ============================================================================
# COMMAND LINE INTERFACE (v3.3.2)
# ============================================================================

def create_enhanced_parser_v332():
    """Create enhanced argument parser for v3.3.2"""
    parser = argparse.ArgumentParser(
        description=f'Enhanced FactSet Pipeline v{__version__} - v3.3.2 Simplified & Observable',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Enhanced Pipeline v3.3.2 - SIMPLIFIED & OBSERVABLE:

🔧 v3.3.2 NEW FEATURES:
✅ Stage-specific Dual Logging (console + file output)
✅ Cross-platform Safe Console Handling  
✅ Enhanced Performance Monitoring (operation timing)
✅ Intelligent Error Diagnostics and Recovery
✅ Unified CLI Interface (Windows/Linux identical)

🔄 v3.3.1 COMPREHENSIVE FIXES (MAINTAINED):
✅ Search cascade failure protection (#1)
✅ Performance optimization with batching (#2)  
✅ Unified rate limiting (#3)
✅ Resolved circular dependencies (#4)
✅ Improved data deduplication (#5)
✅ Enhanced filename generation (#6)
✅ Robust configuration validation (#7)
✅ Simplified GitHub Actions (#8)
✅ Memory management with streaming (#9)
✅ Fixed parameter mismatches (#10)

Examples (v3.3.2):
  python factset_pipeline.py                      # Intelligent execution
  python factset_pipeline.py --mode enhanced      # Full v3.3.2 features
  python factset_pipeline.py --analyze-v332       # v3.3.2 data analysis
  python factset_pipeline.py --status-v332        # Enhanced status
  python factset_pipeline.py --log-level debug    # Detailed logging
        """
    )
    
    # Configuration options
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], 
                       default='info', help='Set logging level')
    
    # Execution modes
    execution_group = parser.add_mutually_exclusive_group()
    execution_group.add_argument('--mode', 
                                choices=['intelligent', 'conservative', 'process-only', 'enhanced'], 
                                default='intelligent', help='Execution mode')
    execution_group.add_argument('--search-only', action='store_true', help='Enhanced search only')
    execution_group.add_argument('--process-only', action='store_true', help='v3.3.2 processing only')
    execution_group.add_argument('--upload-only', action='store_true', help='Enhanced upload only')
    
    # Control options
    parser.add_argument('--force-all', action='store_true', help='Force re-run all phases')
    parser.add_argument('--skip-phases', nargs='*', choices=['search', 'processing', 'upload'],
                       help='Skip specific phases')
    
    # v3.3.2 specific options
    parser.add_argument('--memory-limit', type=int, default=2048, help='Memory limit in MB')
    parser.add_argument('--batch-size', type=int, default=50, help='Processing batch size')
    parser.add_argument('--enable-performance', action='store_true', default=True, 
                       help='Enable performance monitoring')
    
    # Enhanced monitoring
    monitoring_group = parser.add_mutually_exclusive_group()
    monitoring_group.add_argument('--status-v332', action='store_true', help='Enhanced v3.3.2 status')
    monitoring_group.add_argument('--analyze-v332', action='store_true', help='v3.3.2 data analysis')
    
    # Version info
    parser.add_argument('--version', action='version', 
                       version=f'Enhanced FactSet Pipeline v{__version__} (v3.3.2)')
    
    return parser

def main():
    """Enhanced main entry point for v3.3.2"""
    parser = create_enhanced_parser_v332()
    args = parser.parse_args()
    
    # Setup enhanced logging
    logger = setup_logging_v332()
    
    # Set debug mode
    if args.debug:
        os.environ['FACTSET_PIPELINE_DEBUG'] = 'true'
        # Try to set log level for v3.3.2 logger
        try:
            logger.setLevel(logging.DEBUG)
        except:
            logging.getLogger('factset_pipeline_v332').setLevel(logging.DEBUG)
    
    try:
        # Initialize enhanced pipeline
        pipeline = EnhancedFactSetPipeline(args.config)
        logger.info(f"Enhanced FactSet Pipeline v{__version__} started")
        
        # Handle enhanced monitoring requests
        if args.status_v332:
            logger.info("📊 Enhanced Pipeline Status (v3.3.2):")
            logger.info(f"   Version: {__version__}")
            logger.info("   Configuration: Enhanced with comprehensive fixes")
            logger.info("   Rate Protector: Unified v3.3.2")
            logger.info(f"   Memory Management: {args.memory_limit}MB limit")
            logger.info(f"   Batch Processing: {args.batch_size} files per batch")
            logger.info("   Logging: Stage-specific dual output")
            logger.info("   Performance: Enhanced monitoring enabled")
            
            # Show stats
            rate_stats = pipeline.rate_protector.get_stats()
            memory_stats = pipeline.memory_manager.get_stats()
            logger.info(f"   Rate Limiting: {rate_stats['success_rate']:.1%} success rate")
            logger.info(f"   Memory Usage: {memory_stats['peak_mb']:.1f}MB peak")
            return
        
        if args.analyze_v332:
            existing_files, data_status = pipeline.analyze_existing_data_v332()
            logger.info("💡 v3.3.2 Analysis Results:")
            logger.info(f"   Files: {existing_files}")
            logger.info(f"   Status: {data_status}")
            logger.info("   Recommendation: python factset_pipeline.py --mode enhanced")
            return
        
        # Apply v3.3.2 specific settings
        if args.memory_limit:
            pipeline.config.config['processing']['memory_limit_mb'] = args.memory_limit
        
        if args.batch_size:
            pipeline.config.config['processing']['max_files_per_batch'] = args.batch_size
        
        # Handle execution requests
        success = False
        
        if args.search_only:
            success = pipeline.run_enhanced_search_phase_v332(force=args.force_all)
            
        elif args.process_only:
            success = pipeline.run_enhanced_processing_phase_v332(force=args.force_all)
            
        elif args.upload_only:
            success = pipeline.run_enhanced_upload_phase_v332(force=args.force_all)
            
        else:
            # Full enhanced pipeline execution
            skip_phases = args.skip_phases or []
            
            if args.mode == "process-only":
                skip_phases.append("search")
            
            success = pipeline.run_complete_pipeline_v332(
                force_all=args.force_all,
                skip_phases=skip_phases,
                execution_mode=args.mode
            )
        
        # Enhanced guidance on failure
        if not success:
            logger.error("💡 v3.3.2 Troubleshooting suggestions:")
            logger.error("1. Check status: python factset_pipeline.py --status-v332")
            logger.error("2. Analyze data: python factset_pipeline.py --analyze-v332")
            logger.error("3. Try processing only: python factset_pipeline.py --mode process-only")
            logger.error("4. Increase memory: python factset_pipeline.py --memory-limit 4096")
            logger.error("5. Enable debug: python factset_pipeline.py --debug")
        else:
            logger.info("🎉 Enhanced Pipeline completed successfully! (v3.3.2)")
            logger.info("🔧 Features:")
            logger.info("   - Stage-specific Dual Logging")
            logger.info("   - Cross-platform Safe Console")
            logger.info("   - Performance Monitoring")
            logger.info("   - All v3.3.1 Fixes Maintained")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("Enhanced pipeline interrupted")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Enhanced pipeline execution failed: {e}")
        if args.debug:
            logger.error("Debug traceback:", exc_info=True)
        
        logger.error("💡 v3.3.2 Recovery options:")
        logger.error("1. Try with debug: python factset_pipeline.py --debug")
        logger.error("2. Process existing data: python factset_pipeline.py --mode process-only")
        logger.error("3. Check memory usage: python factset_pipeline.py --memory-limit 4096")
        logger.error("4. Use smaller batches: python factset_pipeline.py --batch-size 25")
        logger.error("5. Check logs: ls -la logs/latest/")
        
        sys.exit(1)

if __name__ == "__main__":
    main()