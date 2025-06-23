"""
factset_pipeline.py - Complete Enhanced Production Pipeline (v3.3.0)

Version: 3.3.0
Date: 2025-06-22
Author: FactSet Pipeline - v3.3.0 Enhanced Architecture

v3.3.0 ENHANCEMENTS:
- ✅ Enhanced MD file processing with better financial data extraction
- ✅ Portfolio Summary: Proper aggregation of multiple MD files per company
- ✅ Detailed Data: One row per MD file with individual quality assessment
- ✅ Improved data deduplication for same data from different sources
- ✅ Enhanced company name matching with 觀察名單.csv integration
- ✅ Better date extraction and validation from MD files
- ✅ Immediate stop on 429 errors with intelligent fallback strategies
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
from datetime import datetime, timedelta
from pathlib import Path
import logging
import hashlib

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Version Information - v3.3.0
__version__ = "3.3.0"
__date__ = "2025-06-22"
__author__ = "FactSet Pipeline - v3.3.0 Enhanced Architecture"

# ============================================================================
# SAFE EMOJI HANDLING FOR WINDOWS (v3.3.0)
# ============================================================================

class SafeEmoji:
    """Enhanced emoji handler for v3.3.0 with better Windows support"""
    
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
# ENHANCED LOGGING SETUP (v3.3.0)
# ============================================================================

def setup_logging_v330():
    """Setup enhanced logging for v3.3.0"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            formatted = super().format(record)
            return emoji.safe(formatted)
    
    formatter = SafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('factset_pipeline_v330')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    # File handler
    log_file = log_dir / f"pipeline_v330_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# ============================================================================
# ENHANCED CONFIGURATION MANAGEMENT (v3.3.0)
# ============================================================================

class EnhancedConfig:
    """Enhanced configuration management for v3.3.0"""
    
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.logger = logging.getLogger('factset_pipeline_v330.config')
        self._load_dotenv()
        self.config = self._load_config_v330()
    
    def _load_dotenv(self):
        """Load environment variables"""
        try:
            from dotenv import load_dotenv
            env_path = Path('.env')
            if env_path.exists():
                load_dotenv(env_path)
                print(emoji.safe("✅ Loaded .env file"))
            else:
                print(emoji.safe("ℹ️ No .env file found"))
        except ImportError:
            print(emoji.safe("⚠️ python-dotenv not installed"))
        except Exception as e:
            print(emoji.safe(f"⚠️ Error loading .env: {e}"))
    
    def _load_config_v330(self):
        """Load enhanced configuration for v3.3.0"""
        default_config = {
            "target_companies": [],
            "watchlist_url": "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv",
            "search": {
                "max_results": 10,
                "language": "zh-TW",
                "rate_limit_delay": 45,
                "max_retries": 3,
                "circuit_breaker_threshold": 1,  # Immediate stop
                "content_quality_threshold": 3   # v3.3.0: Only keep quality content
            },
            "output": {
                "base_dir": "data",
                "csv_dir": "data/csv",
                "pdf_dir": "data/pdf",
                "md_dir": "data/md",
                "processed_dir": "data/processed",
                "logs_dir": "logs",
                "summary_csv": "data/processed/portfolio_summary.csv",
                "detailed_csv": "data/processed/detailed_data.csv",
                "stats_json": "data/processed/statistics.json"
            },
            "processing": {
                "parse_md_files": True,
                "deduplicate_data": True,          # v3.3.0: Enable deduplication
                "aggregate_by_company": True,      # v3.3.0: Company-level aggregation
                "individual_file_analysis": True, # v3.3.0: File-level analysis
                "enhanced_date_extraction": True  # v3.3.0: Better date parsing
            },
            "sheets": {
                "worksheet_names": [
                    "Portfolio Summary v3.3.0", 
                    "Detailed Data v3.3.0", 
                    "Statistics v3.3.0"
                ],
                "backup_enabled": True,
                "enhanced_formatting": True        # v3.3.0: Better formatting
            }
        }
        
        # Load from file if specified
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._deep_update(default_config, file_config)
            except Exception as e:
                print(emoji.safe(f"⚠️ Error loading config file: {e}"))
        
        # Load environment overrides
        self._load_env_overrides_v330(default_config)
        
        return default_config
    
    def _deep_update(self, base_dict, update_dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _load_env_overrides_v330(self, config):
        """Load enhanced environment variable overrides"""
        env_mappings = {
            'GOOGLE_SEARCH_API_KEY': ('search', 'api_key'),
            'GOOGLE_SEARCH_CSE_ID': ('search', 'cse_id'),
            'GOOGLE_SHEETS_CREDENTIALS': ('sheets', 'credentials'),
            'GOOGLE_SHEET_ID': ('sheets', 'sheet_id'),
            'FACTSET_PIPELINE_DEBUG': ('debug', None),
            'FACTSET_MAX_RESULTS': ('search', 'max_results'),
            'FACTSET_QUALITY_THRESHOLD': ('search', 'content_quality_threshold')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if section not in config:
                    config[section] = {}
                if key:
                    # Type conversion for numeric values
                    if env_var in ['FACTSET_MAX_RESULTS', 'FACTSET_QUALITY_THRESHOLD']:
                        try:
                            config[section][key] = int(value)
                        except ValueError:
                            config[section][key] = value
                    else:
                        config[section][key] = value
                else:
                    config[section] = value.lower() in ('true', '1', 'yes')
    
    def download_watchlist_v330(self):
        """Enhanced watchlist download for v3.3.0"""
        try:
            import requests
            import pandas as pd
            
            self.logger.info(emoji.safe("📥 Downloading enhanced watchlist (v3.3.0)..."))
            
            # Enhanced request with better error handling
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(
                self.config['watchlist_url'], 
                timeout=30, 
                headers=headers
            )
            response.raise_for_status()
            
            # Save local copy with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            watchlist_file = f"觀察名單_{timestamp}.csv"
            backup_file = "觀察名單.csv"
            
            # Save both timestamped and current versions
            for file_path in [watchlist_file, backup_file]:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
            
            # Enhanced CSV parsing
            df = pd.read_csv(backup_file)
            if df.empty:
                self.logger.warning("Empty CSV downloaded")
                return False
            
            # Enhanced company processing
            companies = []
            for _, row in df.iterrows():
                try:
                    # Support both column formats
                    if '代號' in df.columns and '名稱' in df.columns:
                        code = str(row['代號']).strip()
                        name = str(row['名稱']).strip()
                    else:
                        # Fallback to first two columns
                        code = str(row.iloc[0]).strip()
                        name = str(row.iloc[1]).strip()
                    
                    # Enhanced validation
                    if (code and name and 
                        code != 'nan' and name != 'nan' and
                        len(code) == 4 and code.isdigit()):
                        companies.append({
                            "code": code, 
                            "name": name,
                            "stock_code": f"{code}-TW"
                        })
                except Exception as e:
                    self.logger.warning(f"Error parsing row: {e}")
            
            self.config['target_companies'] = companies
            self.logger.info(emoji.safe(f"✅ Downloaded {len(companies)} companies (v3.3.0 enhanced)"))
            
            # Save processed companies list
            companies_file = "processed_companies_v330.json"
            with open(companies_file, 'w', encoding='utf-8') as f:
                json.dump(companies, f, indent=2, ensure_ascii=False)
            
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
# ENHANCED RATE LIMITING PROTECTION (v3.3.0)
# ============================================================================

class EnhancedRateLimitProtector:
    """Enhanced rate limiting protection for v3.3.0"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('factset_pipeline_v330.rate_limiter')
        
        # Enhanced rate limiting state
        self.min_delay = config.get('search.rate_limit_delay', 45)
        self.max_delay = 600
        self.current_delay = self.min_delay
        self.last_request_time = None
        self.consecutive_429s = 0
        self.circuit_breaker_threshold = config.get('search.circuit_breaker_threshold', 1)
        
        # v3.3.0 enhancements
        self.should_stop_searching = False
        self.stop_reason = None
        self.fallback_to_processing = False
        self.quality_threshold = config.get('search.content_quality_threshold', 3)
        self.low_quality_count = 0
    
    def record_429_error(self):
        """Enhanced 429 error handling for v3.3.0"""
        self.consecutive_429s += 1
        
        # Exponential backoff
        self.current_delay = min(
            self.max_delay,
            self.min_delay * (2 ** self.consecutive_429s)
        )
        
        self.logger.warning(emoji.safe(
            f"🚨 Rate limiting detected! (#{self.consecutive_429s}) "
            f"Delay: {self.current_delay}s"
        ))
        
        # v3.3.0: Immediate stop after first 429
        if self.consecutive_429s >= self.circuit_breaker_threshold:
            self.should_stop_searching = True
            self.fallback_to_processing = True
            self.stop_reason = f"Rate limiting: {self.consecutive_429s} consecutive 429s"
            
            self.logger.error(emoji.safe(f"🛑 STOPPING SEARCH: {self.stop_reason}"))
            self.logger.info(emoji.safe("📄 Fallback: Process existing data"))
            return True
        
        return False
    
    def record_low_quality_content(self):
        """v3.3.0: Track low quality content"""
        self.low_quality_count += 1
        
        # If too much low quality content, suggest stopping
        if self.low_quality_count > 10:
            self.logger.warning(emoji.safe(
                f"⚠️ High low-quality content count: {self.low_quality_count}"
            ))
            return True
        
        return False
    
    def record_success(self, quality_score=None):
        """Enhanced success recording with quality tracking"""
        if self.consecutive_429s > 0:
            self.logger.info(emoji.safe("✅ Request successful - rate limiting lifted"))
        
        self.consecutive_429s = 0
        self.current_delay = max(self.min_delay, self.current_delay * 0.8)
        
        # v3.3.0: Track content quality
        if quality_score and quality_score >= self.quality_threshold:
            self.low_quality_count = max(0, self.low_quality_count - 1)
    
    def should_stop_immediately(self):
        """Check if should stop immediately"""
        return self.should_stop_searching
    
    def should_fallback_to_processing(self):
        """Check if should fallback to processing"""
        return self.fallback_to_processing
    
    def get_stop_reason(self):
        """Get stop reason"""
        return self.stop_reason or "Unknown"
    
    def get_status_v330(self):
        """Enhanced status for v3.3.0"""
        return {
            "version": "3.3.0",
            "consecutive_429s": self.consecutive_429s,
            "current_delay": self.current_delay,
            "should_stop": self.should_stop_searching,
            "fallback_to_processing": self.fallback_to_processing,
            "low_quality_count": self.low_quality_count,
            "quality_threshold": self.quality_threshold
        }

# ============================================================================
# ENHANCED WORKFLOW STATE MANAGEMENT (v3.3.0)
# ============================================================================

class EnhancedWorkflowState:
    """Enhanced workflow state management for v3.3.0"""
    
    def __init__(self, state_file="data/workflow_state_v330.json"):
        self.state_file = state_file
        self.logger = logging.getLogger('factset_pipeline_v330.workflow')
        self.state = self._load_state_v330()
    
    def _load_state_v330(self):
        """Load enhanced state for v3.3.0"""
        default_state = {
            "version": "3.3.0",
            "workflow_id": None,
            "started_at": None,
            "last_updated": None,
            
            # Search phase (enhanced)
            "search_completed": False,
            "search_timestamp": None,
            "md_files_generated": 0,
            "quality_files_generated": 0,  # v3.3.0: Track quality files
            "search_stopped_early": False,
            "rate_limiting_detected": False,
            
            # Processing phase (enhanced)
            "processing_completed": False,
            "processing_timestamp": None,
            "companies_processed": 0,
            "files_aggregated": 0,          # v3.3.0: Aggregated files
            "individual_files_analyzed": 0, # v3.3.0: Individual analysis
            
            # Upload phase
            "sheets_uploaded": False,
            "upload_timestamp": None,
            "sheets_updated": [],           # v3.3.0: Track updated sheets
            
            # Enhanced error tracking
            "last_error": None,
            "success_count": 0,
            "total_steps": 3,
            "consecutive_failures": 0,
            "execution_mode": "intelligent",
            "search_strategy": "balanced",
            
            # v3.3.0 specific
            "data_deduplication_enabled": True,
            "enhanced_parsing_enabled": True,
            "quality_threshold": 3
        }
        
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)
                    self._deep_merge(default_state, loaded_state)
                    return default_state
            except Exception as e:
                self.logger.warning(emoji.safe(f"⚠️ Error loading state: {e}"))
        
        return default_state
    
    def _deep_merge(self, base, update):
        """Deep merge dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save_state(self):
        """Save enhanced state"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            self.state["last_updated"] = datetime.now().isoformat()
            self.state["version"] = "3.3.0"
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
                
            self.logger.debug(emoji.safe("💾 v3.3.0 workflow state saved"))
        except Exception as e:
            self.logger.error(emoji.safe(f"⚠️ Error saving state: {e}"))
    
    def start_workflow_v330(self, search_strategy="intelligent", execution_mode="intelligent"):
        """Start enhanced workflow for v3.3.0"""
        workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.state.update({
            "version": "3.3.0",
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
            "search_stopped_early": False,
            "data_deduplication_enabled": True,
            "enhanced_parsing_enabled": True
        })
        
        self.save_state()
        self.logger.info(emoji.safe(
            f"🚀 Started v3.3.0 workflow: {workflow_id} "
            f"(strategy: {search_strategy}, mode: {execution_mode})"
        ))
    
    def mark_search_complete_v330(self, md_files=0, quality_files=0, stopped_early=False):
        """Mark enhanced search completion"""
        self.state.update({
            "search_completed": True,
            "search_timestamp": datetime.now().isoformat(),
            "md_files_generated": md_files,
            "quality_files_generated": quality_files,
            "search_stopped_early": stopped_early,
            "success_count": 1
        })
        
        self.save_state()
        status = "Search completed"
        if stopped_early:
            status += " (stopped early due to rate limiting)"
        
        self.logger.info(emoji.safe(
            f"✅ {status}: {md_files} MD files, {quality_files} quality files"
        ))
    
    def mark_processing_complete_v330(self, companies=0, aggregated_files=0, individual_files=0):
        """Mark enhanced processing completion"""
        self.state.update({
            "processing_completed": True,
            "processing_timestamp": datetime.now().isoformat(),
            "companies_processed": companies,
            "files_aggregated": aggregated_files,
            "individual_files_analyzed": individual_files,
            "success_count": 2
        })
        
        self.save_state()
        self.logger.info(emoji.safe(
            f"✅ Processing completed: {companies} companies, "
            f"{aggregated_files} aggregated, {individual_files} individual"
        ))
    
    def mark_upload_complete_v330(self, sheets_updated):
        """Mark enhanced upload completion"""
        self.state.update({
            "sheets_uploaded": True,
            "upload_timestamp": datetime.now().isoformat(),
            "sheets_updated": sheets_updated,
            "success_count": 3
        })
        
        self.save_state()
        self.logger.info(emoji.safe(f"✅ Upload completed: {len(sheets_updated)} sheets"))

# ============================================================================
# ENHANCED PRODUCTION PIPELINE (v3.3.0)
# ============================================================================

class EnhancedFactSetPipeline:
    """Enhanced production pipeline for v3.3.0"""
    
    def __init__(self, config_file=None):
        self.logger = setup_logging_v330()
        self.config = EnhancedConfig(config_file)
        self.rate_protector = EnhancedRateLimitProtector(self.config)
        self.state = EnhancedWorkflowState()
        
        # Create directories
        self._setup_directories_v330()
        
        self.logger.info(emoji.safe(
            f"🚀 Enhanced FactSet Pipeline v{__version__} initialized"
        ))
    
    def _setup_directories_v330(self):
        """Setup enhanced directories for v3.3.0"""
        directories = [
            self.config.get('output.csv_dir'),
            self.config.get('output.pdf_dir'),
            self.config.get('output.md_dir'),
            self.config.get('output.processed_dir'),
            self.config.get('output.logs_dir'),
            "backups",  # v3.3.0: Enhanced backup directory
            "temp"      # v3.3.0: Temporary processing directory
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def analyze_existing_data_v330(self):
        """Enhanced existing data analysis for v3.3.0"""
        md_dir = Path(self.config.get('output.md_dir'))
        
        if not md_dir.exists():
            return 0, "no_data"
        
        md_files = list(md_dir.glob("*.md"))
        file_count = len(md_files)
        
        self.logger.info(emoji.safe(f"📊 v3.3.0 data analysis: {file_count} MD files"))
        
        # Enhanced quality analysis
        quality_files = 0
        companies_with_data = set()
        date_range = {"oldest": None, "newest": None}
        
        # Sample analysis (limit to avoid performance issues)
        sample_files = md_files[:50] if len(md_files) > 50 else md_files
        
        for md_file in sample_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check content quality
                if any(keyword in content.lower() for keyword in [
                    'factset', 'eps', '分析師', '目標價', '預估'
                ]):
                    quality_files += 1
                
                # Extract company from filename
                filename = md_file.name
                company_match = re.search(r'(\d{4})_', filename)
                if company_match:
                    companies_with_data.add(company_match.group(1))
                
                # Track file dates
                mod_time = datetime.fromtimestamp(md_file.stat().st_mtime)
                if date_range["oldest"] is None or mod_time < date_range["oldest"]:
                    date_range["oldest"] = mod_time
                if date_range["newest"] is None or mod_time > date_range["newest"]:
                    date_range["newest"] = mod_time
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing {md_file}: {e}")
        
        # Enhanced quality assessment
        quality_ratio = quality_files / len(sample_files) if sample_files else 0
        companies_count = len(companies_with_data)
        
        self.logger.info(emoji.safe(
            f"📈 Quality analysis: {quality_files}/{len(sample_files)} files "
            f"({quality_ratio:.1%}), {companies_count} companies"
        ))
        
        # v3.3.0 enhanced criteria
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
    
    def determine_strategy_v330(self, existing_files, data_status):
        """Enhanced strategy determination for v3.3.0"""
        self.logger.info(emoji.safe("🎯 Determining v3.3.0 strategy..."))
        self.logger.info(emoji.safe(f"   📄 Files: {existing_files}, Status: {data_status}"))
        
        # Check rate limiting status first
        if self.rate_protector.should_stop_immediately():
            strategy = "process_existing"
            reason = "Rate limiting active - process existing data only"
        elif data_status == "excellent":
            strategy = "conservative_enhancement"
            reason = "Excellent data - conservative enhancement only"
        elif data_status == "good":
            strategy = "selective_update"
            reason = "Good data - selective updates for gaps"
        elif data_status == "moderate":
            strategy = "balanced_expansion"
            reason = "Moderate data - balanced expansion needed"
        else:
            strategy = "comprehensive_collection"
            reason = "Insufficient data - comprehensive collection required"
        
        self.logger.info(emoji.safe(f"   🎯 Strategy: {strategy.upper()}"))
        self.logger.info(emoji.safe(f"   📝 Reason: {reason}"))
        
        return strategy
    
    def run_complete_pipeline_v330(self, strategy="intelligent", force_all=False, 
                                  skip_phases=None, execution_mode="intelligent"):
        """Run enhanced complete pipeline for v3.3.0"""
        if skip_phases is None:
            skip_phases = []
        
        pipeline_start = time.time()
        
        self.logger.info(emoji.safe(f"🚀 Enhanced FactSet Pipeline v{__version__}"))
        self.logger.info(emoji.safe(f"📅 Date: {__date__}"))
        self.logger.info(emoji.safe(f"👨‍💻 Author: {__author__}"))
        self.logger.info("=" * 80)
        
        # Enhanced data analysis and strategy determination
        existing_files, data_status = self.analyze_existing_data_v330()
        optimal_strategy = self.determine_strategy_v330(existing_files, data_status)
        
        # Initialize workflow
        if force_all or not self.state.state.get("workflow_id"):
            self.state.start_workflow_v330(optimal_strategy, execution_mode)
        
        # Load enhanced target companies
        if not self.config.config.get('target_companies'):
            self.config.download_watchlist_v330()
        
        companies = self.config.config.get('target_companies', [])
        self.logger.info(emoji.safe(f"🎯 Target Companies: {len(companies)} (v3.3.0 enhanced)"))
        
        success_phases = 0
        total_phases = 3 - len(skip_phases)
        
        # Phase 1: Enhanced Search
        if "search" not in skip_phases:
            self.logger.info(emoji.safe(f"\n🔍 Enhanced Search Phase (v3.3.0)"))
            self.logger.info(emoji.safe(f"📊 Strategy: {optimal_strategy}"))
            
            if self.run_enhanced_search_phase_v330(optimal_strategy, force=force_all):
                success_phases += 1
                
                if self.state.state.get("search_stopped_early"):
                    self.logger.warning(emoji.safe("⚠️ Search stopped early - continuing with existing data"))
                else:
                    self.logger.info(emoji.safe("✅ Search phase completed successfully"))
            else:
                self.logger.error(emoji.safe("❌ Search phase failed"))
                
                # Check for fallback to existing data
                if existing_files > 0:
                    self.logger.info(emoji.safe("📄 Continuing with existing data..."))
                    success_phases += 1
                else:
                    return False
        else:
            success_phases += 1
        
        # Phase 2: Enhanced Processing
        if "processing" not in skip_phases:
            self.logger.info(emoji.safe(f"\n📊 Enhanced Processing Phase (v3.3.0)"))
            
            if self.run_enhanced_processing_phase_v330(force=force_all):
                success_phases += 1
                self.logger.info(emoji.safe("✅ Processing phase completed"))
            else:
                self.logger.error(emoji.safe("❌ Processing phase failed"))
                return False
        else:
            success_phases += 1
        
        # Phase 3: Enhanced Upload
        if "upload" not in skip_phases:
            self.logger.info(emoji.safe(f"\n📈 Enhanced Upload Phase (v3.3.0)"))
            
            if self.run_enhanced_upload_phase_v330(force=force_all):
                success_phases += 1
                self.logger.info(emoji.safe("✅ Upload phase completed"))
            else:
                self.logger.warning(emoji.safe("⚠️ Upload phase failed"))
        else:
            success_phases += 1
        
        # Enhanced final summary
        total_duration = time.time() - pipeline_start
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe("🎉 ENHANCED PIPELINE EXECUTION COMPLETED! (v3.3.0)"))
        self.logger.info("="*80)
        self.logger.info(emoji.safe(f"📊 Success Rate: {success_phases}/{total_phases} phases"))
        self.logger.info(emoji.safe(f"⏱️ Total Duration: {total_duration:.1f} seconds"))
        
        # Enhanced result display
        if success_phases == total_phases:
            self.logger.info(emoji.safe("🏆 All phases completed successfully!"))
            
            # Display v3.3.0 specific metrics
            md_files = self.state.state.get('md_files_generated', 0)
            quality_files = self.state.state.get('quality_files_generated', 0)
            companies_processed = self.state.state.get('companies_processed', 0)
            
            self.logger.info(emoji.safe(f"📄 MD Files: {md_files} (Quality: {quality_files})"))
            self.logger.info(emoji.safe(f"🏢 Companies: {companies_processed}"))
            
            # v3.3.0 quality assessment
            if quality_files >= 50:
                self.logger.info(emoji.safe("🏆 OUTSTANDING: High-quality data collection!"))
            elif quality_files >= 20:
                self.logger.info(emoji.safe("🎉 EXCELLENT: Substantial quality data!"))
            elif quality_files >= 10:
                self.logger.info(emoji.safe("✅ GOOD: Sufficient quality data!"))
            else:
                self.logger.info(emoji.safe("⚠️ MODERATE: Limited quality data"))
            
            return True
        else:
            self.logger.warning(emoji.safe("⚠️ Pipeline completed with issues"))
            return False
    
    def run_enhanced_search_phase_v330(self, strategy="comprehensive", force=False):
        """Run enhanced search phase for v3.3.0"""
        if self.state.state["search_completed"] and not force:
            self.logger.info(emoji.safe("ℹ️ Search already completed (use --force to re-run)"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe(f"🔍 ENHANCED SEARCH EXECUTION (v3.3.0)"))
        self.logger.info(emoji.safe(f"📊 Strategy: {strategy.upper()}"))
        self.logger.info("="*80)
        
        # Skip search if strategy indicates processing only
        if strategy == "process_existing":
            self.logger.info(emoji.safe("📄 Strategy: Process existing data only"))
            return self._fallback_to_existing_data_v330(start_time)
        
        try:
            # Load target companies
            companies = self.config.config.get('target_companies', [])
            if not companies:
                self.logger.info(emoji.safe("📥 Loading target companies..."))
                if not self.config.download_watchlist_v330():
                    self.logger.error(emoji.safe("❌ Failed to load companies"))
                    return False
                companies = self.config.config['target_companies']
            
            self.logger.info(emoji.safe(f"🎯 Loaded {len(companies)} companies"))
            
            # Determine company subset based on strategy
            if strategy == "conservative_enhancement":
                target_companies = companies[:15]
            elif strategy == "selective_update":
                target_companies = companies[:30]
            elif strategy == "balanced_expansion":
                target_companies = companies[:60]
            else:
                target_companies = companies
            
            self.logger.info(emoji.safe(f"🔍 Processing {len(target_companies)} companies"))
            
            # Run enhanced search
            search_result = self._run_protected_search_v330(target_companies, strategy)
            
            # Handle rate limiting
            if search_result == "rate_limited":
                self.logger.warning(emoji.safe("🚨 Rate limiting - fallback to existing data"))
                return self._fallback_to_existing_data_v330(start_time)
            
            if search_result:
                # Enhanced result analysis
                duration = time.time() - start_time
                md_dir = Path(self.config.get('output.md_dir'))
                
                md_files = list(md_dir.glob("*.md")) if md_dir.exists() else []
                
                # Enhanced quality assessment
                quality_files = self._count_quality_files_v330(md_files)
                
                stopped_early = self.rate_protector.should_stop_immediately()
                
                self.state.mark_search_complete_v330(
                    md_files=len(md_files),
                    quality_files=quality_files,
                    stopped_early=stopped_early
                )
                
                self.logger.info(emoji.safe(
                    f"✅ Search completed: {len(md_files)} files, {quality_files} quality"
                ))
                return True
            else:
                # Search failed, check for existing data
                existing_files, _ = self.analyze_existing_data_v330()
                if existing_files > 0:
                    self.logger.warning(emoji.safe("⚠️ Search failed, using existing data"))
                    return self._fallback_to_existing_data_v330(start_time)
                
                return False
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str:
                self.logger.error(emoji.safe("🛑 Rate limiting - switching to processing"))
                self.rate_protector.record_429_error()
                return self._fallback_to_existing_data_v330(start_time)
            
            self.logger.error(emoji.safe(f"❌ Search phase failed: {e}"))
            self.state.mark_error(str(e))
            
            # Fallback to existing data
            existing_files, _ = self.analyze_existing_data_v330()
            if existing_files > 0:
                return self._fallback_to_existing_data_v330(start_time)
            
            return False
    
    def _fallback_to_existing_data_v330(self, start_time):
        """Enhanced fallback to existing data for v3.3.0"""
        self.logger.info(emoji.safe("📄 v3.3.0 fallback: Processing existing data..."))
        
        existing_files, _ = self.analyze_existing_data_v330()
        if existing_files > 0:
            # Enhanced quality assessment
            md_dir = Path(self.config.get('output.md_dir'))
            md_files = list(md_dir.glob("*.md")) if md_dir.exists() else []
            quality_files = self._count_quality_files_v330(md_files)
            
            self.state.mark_search_complete_v330(
                md_files=existing_files,
                quality_files=quality_files,
                stopped_early=True
            )
            
            self.logger.info(emoji.safe(f"✅ Using existing: {existing_files} files, {quality_files} quality"))
            return True
        else:
            self.logger.warning(emoji.safe("⚠️ No existing data available"))
            return False
    
    def _count_quality_files_v330(self, md_files):
        """Enhanced quality file counting for v3.3.0"""
        quality_count = 0
        quality_threshold = self.config.get('search.content_quality_threshold', 3)
        
        sample_size = min(50, len(md_files))
        
        for md_file in md_files[:sample_size]:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Enhanced quality assessment
                score = 0
                quality_keywords = [
                    'factset', 'eps', '分析師', '目標價', '預估', 
                    '2025', '2026', '2027', 'analyst', 'forecast'
                ]
                
                for keyword in quality_keywords:
                    if keyword in content.lower():
                        score += 1
                
                # Check for numerical data
                if re.search(r'\d+\.\d+', content):
                    score += 1
                
                if score >= quality_threshold:
                    quality_count += 1
                    
            except Exception:
                continue
        
        # Extrapolate to total
        if sample_size > 0:
            ratio = quality_count / sample_size
            return int(len(md_files) * ratio)
        
        return 0
    
    def _run_protected_search_v330(self, companies, strategy):
        """Run enhanced protected search for v3.3.0"""
        try:
            try:
                # Try to import the enhanced search module
                import factset_search as search_module
            except ImportError:
                self.logger.error(emoji.safe("❌ factset_search module not available"))
                return False
            
            # Check for v3.3.0 enhanced search function
            if hasattr(search_module, 'run_enhanced_search_suite_v330'):
                self.logger.info(emoji.safe("🔍 Using v3.3.0 enhanced search suite"))
                try:
                    result = search_module.run_enhanced_search_suite_v330(
                        self.config.config,
                        priority_focus="high_only" if strategy.startswith("conservative") else "balanced"
                    )
                    
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
                self.logger.warning(emoji.safe("⚠️ v3.3.0 search not available - using fallback"))
                return self._run_fallback_search(search_module, strategy)
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str:
                self.rate_protector.record_429_error()
                return "rate_limited"
            
            self.logger.error(emoji.safe(f"❌ Protected search failed: {e}"))
            return False
    
    def run_enhanced_processing_phase_v330(self, force=False):
        """Run enhanced processing phase for v3.3.0"""
        if self.state.state["processing_completed"] and not force:
            self.logger.info(emoji.safe("ℹ️ Processing already completed"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe("📊 ENHANCED DATA PROCESSING (v3.3.0)"))
        self.logger.info("="*80)
        
        try:
            # Check for data to process
            md_dir = Path(self.config.get('output.md_dir'))
            md_files = list(md_dir.glob("*.md")) if md_dir.exists() else []
            
            self.logger.info(emoji.safe(f"📄 Found {len(md_files)} MD files for processing"))
            
            if len(md_files) == 0:
                self.logger.warning(emoji.safe("⚠️ No MD files found"))
                return False
            
            # Import and run enhanced data processor
            try:
                import data_processor
                
                # Check for v3.3.0 enhanced function
                if hasattr(data_processor, 'process_all_data_v330'):
                    success = data_processor.process_all_data_v330(force=force, parse_md=True)
                else:
                    # Fallback to standard function
                    self.logger.warning(emoji.safe("⚠️ Using standard data processor"))
                    success = data_processor.process_all_data(force=force, parse_md=True)
                    
            except ImportError:
                self.logger.error(emoji.safe("❌ data_processor module not available"))
                return False
            
            if success:
                # Enhanced result analysis
                duration = time.time() - start_time
                
                # Count processed data
                summary_file = self.config.get('output.summary_csv')
                detailed_file = self.config.get('output.detailed_csv')
                
                companies_processed = 0
                aggregated_files = 0
                individual_files = 0
                
                if os.path.exists(summary_file):
                    try:
                        import pandas as pd
                        summary_df = pd.read_csv(summary_file)
                        companies_processed = len(summary_df)
                        aggregated_files = summary_df['MD資料筆數'].sum() if 'MD資料筆數' in summary_df.columns else 0
                    except Exception:
                        pass
                
                if os.path.exists(detailed_file):
                    try:
                        import pandas as pd
                        detailed_df = pd.read_csv(detailed_file)
                        individual_files = len(detailed_df)
                    except Exception:
                        pass
                
                self.state.mark_processing_complete_v330(
                    companies=companies_processed,
                    aggregated_files=int(aggregated_files),
                    individual_files=individual_files
                )
                
                # Enhanced logging
                self.logger.info(emoji.safe(
                    f"✅ Processing completed: {companies_processed} companies, "
                    f"{individual_files} individual files analyzed"
                ))
                
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(emoji.safe(f"❌ Processing phase failed: {e}"))
            self.state.mark_error(str(e))
            return False
    
    def run_enhanced_upload_phase_v330(self, force=False):
        """Run enhanced upload phase for v3.3.0"""
        if self.state.state["sheets_uploaded"] and not force:
            self.logger.info(emoji.safe("ℹ️ Upload already completed"))
            return True
        
        start_time = time.time()
        
        self.logger.info(emoji.safe(f"\n{'='*80}"))
        self.logger.info(emoji.safe("📈 ENHANCED GOOGLE SHEETS UPLOAD (v3.3.0)"))
        self.logger.info("="*80)
        
        try:
            # Check for required files
            required_files = [
                self.config.get('output.summary_csv')
            ]
            
            available_files = [f for f in required_files if f and os.path.exists(f)]
            
            if not available_files:
                self.logger.warning(emoji.safe("⚠️ No processed data files found"))
                return False
            
            # Check credentials
            if not self.config.get('sheets.credentials') or not self.config.get('sheets.sheet_id'):
                self.logger.warning(emoji.safe("⚠️ Google Sheets credentials not configured"))
                return False
            
            # Import and run enhanced sheets uploader
            try:
                import sheets_uploader
                
                # Prepare enhanced configuration
                upload_config = self.config.config.copy()
                upload_config['input'] = {
                    'summary_csv': self.config.get('output.summary_csv'),
                    'detailed_csv': self.config.get('output.detailed_csv'),
                    'stats_json': self.config.get('output.stats_json')
                }
                
                if hasattr(sheets_uploader, 'upload_all_sheets_v330'):
                    success = sheets_uploader.upload_all_sheets_v330(upload_config)
                else:
                    # Fallback to standard uploader
                    self.logger.warning(emoji.safe("⚠️ Using standard sheets uploader"))
                    success = sheets_uploader.upload_all_sheets(upload_config)
                    
            except ImportError:
                self.logger.error(emoji.safe("❌ sheets_uploader module not available"))
                return False
            
            if success:
                duration = time.time() - start_time
                
                # Enhanced sheets tracking
                sheets_updated = [
                    "Portfolio Summary v3.3.0",
                    "Detailed Data v3.3.0", 
                    "Statistics v3.3.0"
                ]
                
                self.state.mark_upload_complete_v330(sheets_updated)
                
                # Show enhanced dashboard info
                sheet_id = self.config.get('sheets.sheet_id')
                if sheet_id:
                    dashboard_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
                    self.logger.info(emoji.safe(f"📊 v3.3.0 Dashboard: {dashboard_url}"))
                    self.logger.info(emoji.safe("🎯 Enhanced Features:"))
                    self.logger.info(emoji.safe("   - Portfolio Summary: Aggregated MD data"))
                    self.logger.info(emoji.safe("   - Detailed Data: Individual file analysis"))
                    self.logger.info(emoji.safe("   - Statistics: Enhanced metrics"))
                
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(emoji.safe(f"❌ Upload phase failed: {e}"))
            self.state.mark_error(str(e))
            return False

# ============================================================================
# ENHANCED CLI INTERFACE (v3.3.0)
# ============================================================================

def create_enhanced_parser_v330():
    """Create enhanced argument parser for v3.3.0"""
    parser = argparse.ArgumentParser(
        description=f'Enhanced FactSet Pipeline v{__version__} - v3.3.0 Compliant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Enhanced Pipeline Examples (v3.3.0):

  # Intelligent execution (recommended)
  python factset_pipeline.py                     # Auto-detect strategy
  python factset_pipeline.py --force-all         # Force complete refresh
  
  # Enhanced execution modes
  python factset_pipeline.py --mode conservative  # Safe with enhanced parsing
  python factset_pipeline.py --mode process-only  # v3.3.0 processing only
  python factset_pipeline.py --mode enhanced      # v3.3.0 full features
  
  # Quality-focused execution
  python factset_pipeline.py --quality-threshold 4  # High quality only
  python factset_pipeline.py --enable-dedup        # Enhanced deduplication
  
  # Analysis and monitoring
  python factset_pipeline.py --analyze-v330        # v3.3.0 data analysis
  python factset_pipeline.py --status-v330         # Enhanced status

v3.3.0 ENHANCED FEATURES:
- Portfolio Summary: Proper aggregation of multiple MD files per company
- Detailed Data: One row per MD file with individual quality assessment
- Enhanced MD parsing: Better financial data extraction patterns
- Data deduplication: Handle same data from different sources
- Improved company matching: Better 觀察名單.csv integration
- Enhanced date extraction: Multiple fallback strategies
- Quality assessment: Content quality scoring and filtering

Windows Users: Enhanced emoji support and error handling
        """
    )
    
    # Configuration options
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Execution modes
    execution_group = parser.add_mutually_exclusive_group()
    execution_group.add_argument('--mode', 
                                choices=['intelligent', 'conservative', 'process-only', 'enhanced', 'test-only'], 
                                default='intelligent', help='Execution mode')
    execution_group.add_argument('--search-only', action='store_true', help='Enhanced search only')
    execution_group.add_argument('--process-only', action='store_true', help='v3.3.0 processing only')
    execution_group.add_argument('--upload-only', action='store_true', help='Enhanced upload only')
    
    # Control options
    parser.add_argument('--force-all', action='store_true', help='Force re-run all phases')
    parser.add_argument('--skip-phases', nargs='*', choices=['search', 'processing', 'upload'],
                       help='Skip specific phases')
    
    # v3.3.0 specific options
    parser.add_argument('--quality-threshold', type=int, choices=[1, 2, 3, 4], default=3,
                       help='Content quality threshold (1-4)')
    parser.add_argument('--enable-dedup', action='store_true', help='Enable enhanced deduplication')
    parser.add_argument('--disable-aggregation', action='store_true', help='Disable company aggregation')
    
    # Enhanced monitoring
    monitoring_group = parser.add_mutually_exclusive_group()
    monitoring_group.add_argument('--status-v330', action='store_true', help='Enhanced v3.3.0 status')
    monitoring_group.add_argument('--analyze-v330', action='store_true', help='v3.3.0 data analysis')
    
    # Version info
    parser.add_argument('--version', action='version', 
                       version=f'Enhanced FactSet Pipeline v{__version__} (v3.3.0)')
    
    return parser

def main():
    """Enhanced main entry point for v3.3.0"""
    parser = create_enhanced_parser_v330()
    args = parser.parse_args()
    
    # Setup enhanced logging
    logger = setup_logging_v330()
    
    # Set debug mode
    if args.debug:
        os.environ['FACTSET_PIPELINE_DEBUG'] = 'true'
        logging.getLogger('factset_pipeline_v330').setLevel(logging.DEBUG)
    
    try:
        # Initialize enhanced pipeline
        pipeline = EnhancedFactSetPipeline(args.config)
        logger.info(emoji.safe(f"🚀 Enhanced FactSet Pipeline v{__version__} started"))
        
        # Handle enhanced monitoring requests
        if args.status_v330:
            print(emoji.safe("📊 Enhanced Pipeline Status (v3.3.0):"))
            print(f"   Version: {__version__}")
            print(f"   Configuration: Enhanced")
            print(f"   Rate Protector: v3.3.0 Enhanced")
            print(f"   Workflow State: v3.3.0 Enhanced")
            print(f"   Quality Threshold: {args.quality_threshold}")
            return
        
        if args.analyze_v330:
            existing_files, data_status = pipeline.analyze_existing_data_v330()
            strategy = pipeline.determine_strategy_v330(existing_files, data_status)
            print(emoji.safe(f"\n💡 v3.3.0 Recommended action:"))
            if strategy == "process_existing":
                print("   python factset_pipeline.py --mode process-only")
            elif strategy.startswith("conservative"):
                print("   python factset_pipeline.py --mode conservative")
            else:
                print("   python factset_pipeline.py --mode enhanced")
            return
        
        # Apply v3.3.0 specific settings
        if args.quality_threshold:
            pipeline.config.config['search']['content_quality_threshold'] = args.quality_threshold
        
        if args.enable_dedup:
            pipeline.config.config['processing']['deduplicate_data'] = True
        
        if args.disable_aggregation:
            pipeline.config.config['processing']['aggregate_by_company'] = False
        
        # Handle execution requests
        success = False
        
        if args.search_only:
            existing_files, data_status = pipeline.analyze_existing_data_v330()
            strategy = pipeline.determine_strategy_v330(existing_files, data_status)
            success = pipeline.run_enhanced_search_phase_v330(strategy, force=args.force_all)
            
        elif args.process_only:
            success = pipeline.run_enhanced_processing_phase_v330(force=args.force_all)
            
        elif args.upload_only:
            success = pipeline.run_enhanced_upload_phase_v330(force=args.force_all)
            
        else:
            # Full enhanced pipeline execution
            skip_phases = args.skip_phases or []
            
            if args.mode == "process-only":
                skip_phases.append("search")
            elif args.mode == "test-only":
                skip_phases.extend(["search", "upload"])
            
            success = pipeline.run_complete_pipeline_v330(
                force_all=args.force_all,
                skip_phases=skip_phases,
                execution_mode=args.mode
            )
        
        # Enhanced guidance on failure
        if not success:
            logger.error(emoji.safe("\n💡 v3.3.0 Troubleshooting suggestions:"))
            logger.error("1. Analyze data: python factset_pipeline.py --analyze-v330")
            logger.error("2. Try enhanced mode: python factset_pipeline.py --mode enhanced")
            logger.error("3. Process existing: python factset_pipeline.py --mode process-only")
            logger.error("4. Adjust quality: python factset_pipeline.py --quality-threshold 2")
        else:
            logger.info(emoji.safe("🎉 Enhanced Pipeline completed successfully! (v3.3.0)"))
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning(emoji.safe("\n⚠️ Enhanced pipeline interrupted"))
        sys.exit(130)
        
    except Exception as e:
        logger.error(emoji.safe(f"❌ Enhanced pipeline execution failed: {e}"))
        if args.debug:
            logger.error("Debug traceback:", exc_info=True)
        
        logger.error(emoji.safe("\n💡 v3.3.0 Recovery options:"))
        logger.error("1. Check --analyze-v330 for current state")
        logger.error("2. Try --mode process-only if search fails")
        logger.error("3. Use --debug for detailed error analysis")
        logger.error("4. Adjust --quality-threshold for better results")
        
        sys.exit(1)

if __name__ == "__main__":
    main()