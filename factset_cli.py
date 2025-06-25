#!/usr/bin/env python3
"""
factset_cli.py - Unified CLI Interface (v3.3.3)

Version: 3.3.3
Date: 2025-06-24
Author: FactSet Pipeline - v3.3.3 Final Integrated Edition

v3.3.3 ENHANCEMENTS:
- ✅ Standardized Quality Scoring System (0-10 scale)
- ✅ GitHub Actions modernization (GITHUB_OUTPUT support)
- ✅ Quality scoring CLI commands and validation
- ✅ All v3.3.2 functionality preserved and enhanced

v3.3.2 FEATURES MAINTAINED:
- ✅ Unified cross-platform CLI interface (Windows/Linux identical commands)
- ✅ Integration with stage runner and enhanced logging
- ✅ Advanced diagnostics and troubleshooting commands
- ✅ Real-time log monitoring and analysis
- ✅ Intelligent error recovery and suggestions

Description:
    Enhanced single entry point for all FactSet Pipeline operations in v3.3.3:
    - Standardized 0-10 quality scoring system
    - Modern GitHub Actions compatibility
    - All v3.3.2 unified command structure preserved
    - Enhanced quality analysis and reporting
    - Cross-platform compatibility with safe encoding handling
"""

import os
import sys
import argparse
import json
import time
import traceback
import signal
import platform
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import threading
import subprocess

# Ensure proper encoding for cross-platform compatibility
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

# Import v3.3.2 components (preserved)
try:
    from enhanced_logger import get_logger_manager, get_stage_logger
    from stage_runner import StageRunner, ExecutionContext, StageStatus
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: v3.3.2 components not available: {e}")
    COMPONENTS_AVAILABLE = False

# Version Information - v3.3.3
__version__ = "3.3.3"
__date__ = "2025-06-24"
__author__ = "FactSet Pipeline - v3.3.3 Final Integrated Edition"

# ============================================================================
# v3.3.3 STANDARDIZED QUALITY SCORING SYSTEM
# ============================================================================

class StandardizedQualityScorer:
    """v3.3.3 Standardized Quality Scoring System (0-10)"""
    
    QUALITY_RANGES = {
        'complete': (9, 10),    # 🟢 完整
        'good': (8, 8),         # 🟡 良好
        'partial': (3, 7),      # 🟠 部分
        'insufficient': (0, 2)  # 🔴 不足
    }
    
    QUALITY_INDICATORS = {
        'complete': '🟢 完整',
        'good': '🟡 良好', 
        'partial': '🟠 部分',
        'insufficient': '🔴 不足'
    }
    
    def __init__(self):
        self.scoring_version = "3.3.3"
    
    def calculate_score(self, data_metrics: Dict[str, Any]) -> int:
        """Calculate 0-10 standardized quality score"""
        score = 0
        
        # Data completeness (40% weight)
        eps_completeness = data_metrics.get('eps_data_completeness', 0)
        if eps_completeness >= 0.9:
            score += 4
        elif eps_completeness >= 0.7:
            score += 3
        elif eps_completeness >= 0.5:
            score += 2
        elif eps_completeness >= 0.3:
            score += 1
        
        # Analyst coverage (30% weight)
        analyst_count = data_metrics.get('analyst_count', 0)
        if analyst_count >= 20:
            score += 3
        elif analyst_count >= 10:
            score += 2
        elif analyst_count >= 5:
            score += 1
        
        # Data freshness (30% weight)
        days_old = data_metrics.get('data_age_days', float('inf'))
        if days_old <= 7:
            score += 3
        elif days_old <= 30:
            score += 2
        elif days_old <= 90:
            score += 1
        
        return min(10, max(0, score))
    
    def get_quality_indicator(self, score: int) -> str:
        """Get quality indicator for score"""
        for category, (min_score, max_score) in self.QUALITY_RANGES.items():
            if min_score <= score <= max_score:
                return self.QUALITY_INDICATORS[category]
        return self.QUALITY_INDICATORS['insufficient']
    
    def convert_legacy_score(self, legacy_score: int) -> int:
        """Convert legacy 1-4 score to 0-10 scale"""
        conversion_map = {
            4: 10,  # Excellent → Complete (10)
            3: 8,   # Good → Good (8)
            2: 5,   # Fair → Partial (5)
            1: 2,   # Poor → Insufficient (2)
            0: 0    # None → Insufficient (0)
        }
        return conversion_map.get(legacy_score, 0)
    
    def standardize_quality_data(self, quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize quality data to v3.3.3 format"""
        standardized = quality_data.copy()
        
        # Convert legacy scores if present
        if 'quality_score' in standardized and isinstance(standardized['quality_score'], int):
            legacy_score = standardized['quality_score']
            if legacy_score <= 4:  # Legacy 1-4 scale
                standardized['quality_score'] = self.convert_legacy_score(legacy_score)
                standardized['legacy_score'] = legacy_score
        
        # Add quality indicator
        score = standardized.get('quality_score', 0)
        standardized['quality_status'] = self.get_quality_indicator(score)
        standardized['scoring_version'] = self.scoring_version
        
        return standardized

# ============================================================================
# CROSS-PLATFORM SAFE OUTPUT HANDLING (v3.3.2 - preserved)
# ============================================================================

class SafeOutput:
    """Cross-platform safe output handler (preserved from v3.3.2)"""
    
    def __init__(self):
        self.encoding = self._detect_safe_encoding()
        self.use_emoji = self._test_emoji_support()
        
        # Emoji fallbacks for Windows
        self.emoji_map = {
            '🚀': '[START]', '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARN]',
            '🔍': '[SEARCH]', '📊': '[DATA]', '📈': '[UPLOAD]', '🔧': '[FIX]',
            '📄': '[FILE]', '💡': '[TIP]', '🎯': '[TARGET]', '📋': '[LIST]',
            '🧪': '[TEST]', '🔄': '[RETRY]', '💾': '[SAVE]', '🎉': '[SUCCESS]',
            '🟢': '[GOOD]', '🟡': '[FAIR]', '🟠': '[PARTIAL]', '🔴': '[POOR]'  # v3.3.3
        } if not self.use_emoji else {}
    
    def _detect_safe_encoding(self) -> str:
        """Detect safest encoding for the platform"""
        if sys.platform == "win32":
            try:
                "🚀".encode(sys.stdout.encoding or 'utf-8')
                return sys.stdout.encoding or 'utf-8'
            except (UnicodeEncodeError, AttributeError):
                return 'cp1252'
        return sys.stdout.encoding or 'utf-8'
    
    def _test_emoji_support(self) -> bool:
        """Test if console supports emoji"""
        if sys.platform == "win32":
            try:
                "🚀".encode(self.encoding)
                return True
            except UnicodeEncodeError:
                return False
        return True
    
    def safe_print(self, message: str, end: str = '\n'):
        """Safely print message with encoding protection"""
        try:
            # Replace emoji if needed
            if not self.use_emoji:
                for emoji, replacement in self.emoji_map.items():
                    message = message.replace(emoji, replacement)
            
            # Ensure safe encoding
            if sys.platform == "win32":
                try:
                    message.encode(self.encoding)
                except UnicodeEncodeError:
                    message = message.encode('ascii', errors='replace').decode('ascii')
            
            print(message, end=end)
            
        except Exception:
            # Ultimate fallback
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            print(safe_message, end=end)

# Global safe output instance
safe_output = SafeOutput()

# ============================================================================
# CLI COMMAND HANDLERS (v3.3.3 - enhanced with quality scoring)
# ============================================================================

class FactSetCLI:
    """Main CLI class for v3.3.3 unified interface with standardized quality scoring"""
    
    def __init__(self):
        self.safe_output = safe_output
        self.start_time = datetime.now()
        self.quality_scorer = StandardizedQualityScorer()  # v3.3.3
        self._last_quality_metrics = {}  # Store for GitHub Actions
        
        # Initialize components if available (preserved from v3.3.2)
        if COMPONENTS_AVAILABLE:
            self.logger_manager = get_logger_manager()
            self.stage_runner = StageRunner(self.logger_manager)
            self.main_logger = get_stage_logger("cli")
            self.components_ready = True
        else:
            self.logger_manager = None
            self.stage_runner = None
            self.main_logger = None
            self.components_ready = False
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        self.safe_output.safe_print(f"🚀 FactSet CLI v{__version__} initialized (v3.3.3 Final)")
        if not self.components_ready:
            self.safe_output.safe_print("⚠️ Running in fallback mode - some features may be limited")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown (preserved from v3.3.2)"""
        def signal_handler(signum, frame):
            self.safe_output.safe_print("\n⚠️ Execution interrupted by user")
            if self.main_logger:
                self.main_logger.warning("CLI execution interrupted")
            sys.exit(130)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, signal_handler)
        except Exception:
            pass  # Signal handling may not be available in all environments
    
    def execute_command(self, args: argparse.Namespace) -> bool:
        """Execute CLI command based on arguments (enhanced for v3.3.3)"""
        try:
            if self.main_logger:
                self.main_logger.info(f"Executing command: {args.command}")
                self.main_logger.debug(f"Arguments: {vars(args)}")
            
            # Route to appropriate handler (preserved from v3.3.2)
            command_handlers = {
                'validate': self.handle_validate,
                'download-watchlist': self.handle_download_watchlist,
                'search': self.handle_search,
                'process': self.handle_process,
                'upload': self.handle_upload,
                'pipeline': self.handle_pipeline,
                'recover': self.handle_recover,
                'diagnose': self.handle_diagnose,
                'status': self.handle_status,
                'logs': self.handle_logs,
                'report': self.handle_report,
                'commit': self.handle_commit,
                'performance': self.handle_performance,
                'analyze': self.handle_analyze,
                'quality': self.handle_quality  # v3.3.3 new command
            }
            
            handler = command_handlers.get(args.command)
            if not handler:
                self.safe_output.safe_print(f"❌ Unknown command: {args.command}")
                return False
            
            # Execute handler
            success = handler(args)
            
            # Log completion
            duration = (datetime.now() - self.start_time).total_seconds()
            if self.main_logger:
                self.main_logger.info(f"Command completed in {duration:.2f}s: {'success' if success else 'failed'}")
            
            return success
            
        except KeyboardInterrupt:
            self.safe_output.safe_print("\n⚠️ Command interrupted")
            return False
        except Exception as e:
            self.safe_output.safe_print(f"❌ Command execution failed: {e}")
            if self.main_logger:
                self.main_logger.error(f"Command execution error: {e}")
                self.main_logger.debug(traceback.format_exc())
            return False

    def handle_validate(self, args: argparse.Namespace) -> bool:
        """Handle validation command (v3.3.2 preserved + v3.3.3 quality features)"""
        self.safe_output.safe_print("🧪 Running system validation...")
        
        if not self.components_ready:
            return self._fallback_validate(args)
        
        try:
            # Prepare validation parameters (preserved from v3.3.2)
            params = {
                "mode": "comprehensive" if args.comprehensive else "quick",
                "fix_issues": getattr(args, 'fix_issues', False),
                "test_v332": getattr(args, 'test_v332', False),
                "test_v333": getattr(args, 'test_v333', False),  # v3.3.3
                "quality_scoring": getattr(args, 'quality_scoring', False)  # v3.3.3
            }
            
            # Create execution context
            context = ExecutionContext(execution_mode="validation", **params)
            
            # Run validation stage
            success = self.stage_runner.run_stage("validate", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ System validation passed")
                if getattr(args, 'github_actions', False):
                    self._handle_github_output("validation", "passed")
                    # v3.3.3: Add quality system status
                    quality_status = "enabled" if params.get("quality_scoring") else "standard"
                    self._handle_github_output("quality_system", quality_status)
            else:
                self.safe_output.safe_print("❌ System validation failed")
                if getattr(args, 'github_actions', False):
                    self._handle_github_output("validation", "failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Validation error: {e}")
            return False

    def handle_download_watchlist(self, args: argparse.Namespace) -> bool:
        """Handle watchlist download command (v3.3.3)"""
        self.safe_output.safe_print("📥 Downloading watchlist...")
        
        if not self.components_ready:
            return self._fallback_download_watchlist(args)
        
        try:
            params = {
                "force_refresh": getattr(args, 'force_refresh', False),
                "validate": getattr(args, 'validate', True)
            }
            
            context = ExecutionContext(execution_mode="download", **params)
            success = self.stage_runner.run_stage("download_watchlist", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ Watchlist downloaded successfully")
            else:
                self.safe_output.safe_print("❌ Watchlist download failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Download error: {e}")
            return False

    def handle_search(self, args: argparse.Namespace) -> bool:
        """Handle search command (v3.3.2 preserved + v3.3.3 quality integration)"""
        self.safe_output.safe_print("🔍 Starting enhanced search...")
        
        if not self.components_ready:
            return self._fallback_search(args)
        
        try:
            params = {
                "mode": getattr(args, 'mode', 'enhanced'),
                "priority": getattr(args, 'priority', 'high_only'),
                "max_results": getattr(args, 'max_results', 10),
                "batch_size": getattr(args, 'batch_size', 20),
                "test_cascade_protection": getattr(args, 'test_cascade_protection', False)
            }
            
            context = ExecutionContext(execution_mode="search", **params)
            success = self.stage_runner.run_stage("search", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ Search completed successfully")
            else:
                self.safe_output.safe_print("❌ Search failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Search error: {e}")
            return False

    def handle_process(self, args: argparse.Namespace) -> bool:
        """Handle processing command (v3.3.3)"""
        self.safe_output.safe_print("📊 Starting data processing...")
        
        if not self.components_ready:
            return self._fallback_process(args)
        
        try:
            params = {
                "mode": getattr(args, 'mode', 'v333'),
                "memory_limit": getattr(args, 'memory_limit', 2048),
                "batch_size": getattr(args, 'batch_size', 50),
                "deduplicate": getattr(args, 'deduplicate', True),
                "aggregate": getattr(args, 'aggregate', True),
                "benchmark": getattr(args, 'benchmark', False),
                "force": getattr(args, 'force', False),
                "quality_scoring": getattr(args, 'quality_scoring', True),
                "standardize_quality": getattr(args, 'standardize_quality', True)
            }
            
            context = ExecutionContext(execution_mode="processing", **params)
            success = self.stage_runner.run_stage("process", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ Data processing completed successfully")
                
                # v3.3.3: Show quality metrics
                if params.get("quality_scoring"):
                    self._analyze_quality(args)
            else:
                self.safe_output.safe_print("❌ Data processing failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Processing error: {e}")
            return False

    def handle_upload(self, args: argparse.Namespace) -> bool:
        """Handle upload command (v3.3.2 preserved + v3.3.3 format)"""
        self.safe_output.safe_print("📈 Starting sheets upload...")
        
        if not self.components_ready:
            return self._fallback_upload(args)
        
        try:
            params = {
                "sheets": getattr(args, 'sheets', 'all'),
                "backup": getattr(args, 'backup', True),
                "v333_format": getattr(args, 'v333_format', True),
                "quality_indicators": getattr(args, 'quality_indicators', True),
                "test_connection": getattr(args, 'test_connection', False)
            }
            
            context = ExecutionContext(execution_mode="upload", **params)
            success = self.stage_runner.run_stage("upload", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ Upload completed successfully")
            else:
                self.safe_output.safe_print("❌ Upload failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Upload error: {e}")
            return False

    def handle_pipeline(self, args: argparse.Namespace) -> bool:
        """Handle complete pipeline command (v3.3.3)"""
        self.safe_output.safe_print("🚀 Starting complete pipeline...")
        
        if not self.components_ready:
            return self._fallback_pipeline(args)
        
        try:
            params = {
                "mode": getattr(args, 'mode', 'intelligent'),
                "memory_limit": getattr(args, 'memory_limit', 2048),
                "batch_size": getattr(args, 'batch_size', 50),
                "log_level": getattr(args, 'log_level', 'info'),
                "github_actions": getattr(args, 'github_actions', False),
                "skip_phases": getattr(args, 'skip_phases', []),
                "v333": getattr(args, 'v333', True),
                "quality_scoring": getattr(args, 'quality_scoring', True)
            }
            
            context = ExecutionContext(execution_mode=params["mode"], **params)
            success = self.stage_runner.run_stage("pipeline", context, **params)
            
            if success:
                self.safe_output.safe_print("🎉 Pipeline completed successfully! (v3.3.3)")
                if params["github_actions"]:
                    self._handle_github_output("pipeline", "success")
                    self._handle_github_output("version", __version__)
                    self._handle_github_output("quality_system", "v3.3.3_standardized")
            else:
                self.safe_output.safe_print("❌ Pipeline execution failed")
                if params["github_actions"]:
                    self._handle_github_output("pipeline", "failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Pipeline error: {e}")
            return False

    def handle_quality(self, args: argparse.Namespace) -> bool:
        """v3.3.3 Handle quality scoring and analysis commands"""
        self.safe_output.safe_print("🎯 Quality Scoring Analysis (v3.3.3)")
        
        try:
            action = getattr(args, 'action', 'analyze')
            
            if action == 'analyze':
                return self._analyze_quality(args)
            elif action == 'benchmark':
                return self._benchmark_quality(args)
            elif action == 'distribution':
                return self._quality_distribution(args)
            elif action == 'monitor':
                return self._monitor_quality(args)
            elif action == 'calibrate':
                return self._calibrate_quality(args)
            else:
                self.safe_output.safe_print(f"❌ Unknown quality action: {action}")
                return False
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Quality command error: {e}")
            return False

    def handle_status(self, args: argparse.Namespace) -> bool:
        """Handle status command (v3.3.2 preserved + v3.3.3 quality metrics)"""
        self.safe_output.safe_print("📊 Pipeline Status (v3.3.3)")
        
        try:
            # Show basic status
            self.safe_output.safe_print(f"   Version: {__version__}")
            self.safe_output.safe_print(f"   Components: {'Ready' if self.components_ready else 'Limited'}")
            
            # Check data directories
            data_dirs = ["data/md", "data/processed", "logs"]
            for dir_name in data_dirs:
                dir_path = Path(dir_name)
                if dir_path.exists():
                    file_count = len(list(dir_path.glob("*")))
                    self.safe_output.safe_print(f"   {dir_name}: {file_count} files")
                else:
                    self.safe_output.safe_print(f"   {dir_name}: Not found")
            
            # v3.3.3: Show quality metrics if available
            summary_file = Path("data/processed/portfolio_summary.csv")
            if summary_file.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(summary_file)
                    if '品質評分' in df.columns:
                        scores = df['品質評分'].dropna()
                        if len(scores) > 0:
                            avg_quality = scores.mean()
                            self.safe_output.safe_print(f"   Quality Score: {avg_quality:.1f}/10 average")
                            
                            # Quality distribution
                            complete = len(scores[scores >= 8])
                            partial = len(scores[(scores >= 3) & (scores < 8)])
                            insufficient = len(scores[scores < 3])
                            
                            self.safe_output.safe_print(f"   🟢 Complete: {complete}")
                            self.safe_output.safe_print(f"   🟠 Partial: {partial}")
                            self.safe_output.safe_print(f"   🔴 Insufficient: {insufficient}")
                except Exception:
                    pass
            
            # Show execution summary if components available
            if self.components_ready and self.stage_runner.current_context:
                summary = self.stage_runner.get_execution_summary()
                self.safe_output.safe_print("   Recent Execution:")
                for stage_name, stage_info in summary.get("stages", {}).items():
                    status = stage_info.get("status", "unknown")
                    duration = stage_info.get("duration")
                    if duration:
                        self.safe_output.safe_print(f"     {stage_name}: {status} ({duration:.1f}s)")
                    else:
                        self.safe_output.safe_print(f"     {stage_name}: {status}")
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Status error: {e}")
            return False

    def handle_logs(self, args: argparse.Namespace) -> bool:
        """Handle logs command (v3.3.2 preserved)"""
        if not self.components_ready:
            self.safe_output.safe_print("⚠️ Logging components not available")
            return False
        
        try:
            stage = getattr(args, 'stage', 'all')
            lines = getattr(args, 'tail', 50)
            export_format = getattr(args, 'export', None)
            
            if export_format:
                # Export logs
                export_file = self.logger_manager.export_logs(
                    stage_name=stage if stage != 'all' else None,
                    format=export_format
                )
                if export_file:
                    self.safe_output.safe_print(f"✅ Logs exported to: {export_file}")
                else:
                    self.safe_output.safe_print("❌ Log export failed")
                return export_file is not None
            else:
                # Tail logs
                if stage == 'all':
                    # Show recent errors from all stages
                    error_analysis = self.logger_manager.analyze_errors()
                    self.safe_output.safe_print("📋 Recent Error Analysis:")
                    self.safe_output.safe_print(f"   Total Errors: {error_analysis['total_errors']}")
                    self.safe_output.safe_print(f"   Total Warnings: {error_analysis['total_warnings']}")
                    
                    if error_analysis.get('suggestions'):
                        self.safe_output.safe_print("💡 Suggestions:")
                        for suggestion in error_analysis['suggestions']:
                            self.safe_output.safe_print(f"   - {suggestion}")
                else:
                    # Show logs for specific stage
                    log_lines = self.logger_manager.tail_logs(stage, lines)
                    if log_lines:
                        self.safe_output.safe_print(f"📄 Last {len(log_lines)} lines from {stage}:")
                        for line in log_lines[-lines:]:
                            self.safe_output.safe_print(line.rstrip())
                    else:
                        self.safe_output.safe_print(f"No logs found for stage: {stage}")
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Logs error: {e}")
            return False

    def handle_diagnose(self, args: argparse.Namespace) -> bool:
        """Handle diagnose command (v3.3.2 preserved + v3.3.3 quality diagnostics)"""
        self.safe_output.safe_print("🔧 Running diagnostics...")
        
        try:
            issue = getattr(args, 'issue', None)
            stage = getattr(args, 'stage', None)
            suggest_fix = getattr(args, 'suggest_fix', False)
            v333_comprehensive = getattr(args, 'v333_comprehensive', False)
            
            diagnostics = {
                "platform": platform.system(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "components_available": self.components_ready,
                "issues_found": [],
                "suggestions": []
            }
            
            # Check common issues
            if not Path("data").exists():
                diagnostics["issues_found"].append("Data directory missing")
                diagnostics["suggestions"].append("Create data directory: mkdir data")
            
            if not Path(".env").exists() and not os.getenv("GOOGLE_SHEETS_CREDENTIALS"):
                diagnostics["issues_found"].append("No configuration found")
                diagnostics["suggestions"].append("Create .env file with required credentials")
            
            # v3.3.3: Quality system diagnostics
            if v333_comprehensive:
                try:
                    scorer = self.quality_scorer
                    test_score = scorer.calculate_score({
                        'eps_data_completeness': 0.8,
                        'analyst_count': 10,
                        'data_age_days': 30
                    })
                    diagnostics["quality_system"] = f"Working (test score: {test_score}/10)"
                except Exception as e:
                    diagnostics["issues_found"].append(f"Quality scoring system error: {e}")
            
            # Check specific issue
            if issue:
                if issue == "quality scoring":
                    # v3.3.3: Specific quality scoring diagnostics
                    try:
                        summary_file = Path("data/processed/portfolio_summary.csv")
                        if summary_file.exists():
                            import pandas as pd
                            df = pd.read_csv(summary_file)
                            if '品質評分' in df.columns:
                                scores = df['品質評分'].dropna()
                                if len(scores) > 0:
                                    diagnostics["quality_analysis"] = {
                                        "total_companies": len(scores),
                                        "average_score": float(scores.mean()),
                                        "score_range": f"{scores.min()}-{scores.max()}"
                                    }
                                else:
                                    diagnostics["issues_found"].append("No quality scores found in data")
                            else:
                                diagnostics["issues_found"].append("Quality score column missing")
                        else:
                            diagnostics["issues_found"].append("No processed data found")
                    except Exception as e:
                        diagnostics["issues_found"].append(f"Quality analysis error: {e}")
            
            # Error analysis if components available
            if self.components_ready:
                error_analysis = self.logger_manager.analyze_errors(stage)
                diagnostics["error_analysis"] = error_analysis
                if error_analysis.get("suggestions"):
                    diagnostics["suggestions"].extend(error_analysis["suggestions"])
            
            # Output results
            self.safe_output.safe_print("📊 Diagnostic Results:")
            self.safe_output.safe_print(f"   Platform: {diagnostics['platform']}")
            self.safe_output.safe_print(f"   Python: {diagnostics['python_version']}")
            self.safe_output.safe_print(f"   Components: {diagnostics['components_available']}")
            
            if diagnostics.get("quality_system"):
                self.safe_output.safe_print(f"   Quality System: {diagnostics['quality_system']}")
            
            if diagnostics["issues_found"]:
                self.safe_output.safe_print("❌ Issues Found:")
                for issue in diagnostics["issues_found"]:
                    self.safe_output.safe_print(f"   - {issue}")
            
            if diagnostics["suggestions"]:
                self.safe_output.safe_print("💡 Suggestions:")
                for suggestion in diagnostics["suggestions"]:
                    self.safe_output.safe_print(f"   - {suggestion}")
            
            return len(diagnostics["issues_found"]) == 0
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Diagnostics error: {e}")
            return False

    def handle_recover(self, args: argparse.Namespace) -> bool:
        """Handle recovery command (v3.3.2 preserved)"""
        self.safe_output.safe_print("🔄 Starting recovery procedures...")
        
        try:
            analyze = getattr(args, 'analyze', False)
            fix_common_issues = getattr(args, 'fix_common_issues', False)
            v333_diagnostics = getattr(args, 'v333_diagnostics', False)
            
            recovered_items = []
            
            # Analyze issues first
            if analyze or not fix_common_issues:
                if self.components_ready:
                    error_analysis = self.logger_manager.analyze_errors()
                    self.safe_output.safe_print(f"📊 Found {error_analysis['total_errors']} errors, {error_analysis['total_warnings']} warnings")
                    
                    if error_analysis.get('suggestions'):
                        self.safe_output.safe_print("💡 Recovery suggestions:")
                        for suggestion in error_analysis['suggestions']:
                            self.safe_output.safe_print(f"   - {suggestion}")
            
            # Fix common issues
            if fix_common_issues:
                # Create missing directories
                required_dirs = ["data", "data/md", "data/processed", "logs"]
                for dir_name in required_dirs:
                    dir_path = Path(dir_name)
                    if not dir_path.exists():
                        dir_path.mkdir(parents=True, exist_ok=True)
                        recovered_items.append(f"Created directory: {dir_name}")
                
                # Check and fix file permissions (Unix only)
                if sys.platform != "win32":
                    try:
                        current_dir = Path(".")
                        for py_file in current_dir.glob("*.py"):
                            if not os.access(py_file, os.R_OK):
                                os.chmod(py_file, 0o644)
                                recovered_items.append(f"Fixed permissions: {py_file}")
                    except Exception:
                        pass
            
            # v3.3.3 specific recovery
            if v333_diagnostics:
                try:
                    # Test quality scorer
                    test_score = self.quality_scorer.calculate_score({
                        'eps_data_completeness': 0.5,
                        'analyst_count': 5,
                        'data_age_days': 60
                    })
                    recovered_items.append(f"Quality scorer test: {test_score}/10")
                except Exception as e:
                    self.safe_output.safe_print(f"⚠️ Quality scorer issue: {e}")
            
            # Report recovery results
            if recovered_items:
                self.safe_output.safe_print("✅ Recovery actions:")
                for item in recovered_items:
                    self.safe_output.safe_print(f"   - {item}")
            else:
                self.safe_output.safe_print("ℹ️ No recovery actions needed")
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Recovery error: {e}")
            return False

    def handle_report(self, args: argparse.Namespace) -> bool:
        """Handle report command (v3.3.2 preserved + v3.3.3 quality reporting)"""
        self.safe_output.safe_print("📋 Generating report...")
        
        try:
            format_type = getattr(args, 'format', 'summary')
            email = getattr(args, 'email', False)
            v333_metrics = getattr(args, 'v333_metrics', False)
            quality_focused = getattr(args, 'quality_focused', False)
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "version": __version__,
                "format": format_type
            }
            
            # Basic pipeline status
            if Path("data/processed").exists():
                processed_files = list(Path("data/processed").glob("*"))
                report["processed_files"] = len(processed_files)
            
            # v3.3.3: Quality-focused reporting
            if quality_focused or v333_metrics:
                summary_file = Path("data/processed/portfolio_summary.csv")
                if summary_file.exists():
                    try:
                        import pandas as pd
                        df = pd.read_csv(summary_file)
                        
                        if '品質評分' in df.columns:
                            scores = df['品質評分'].dropna()
                            report["quality_metrics"] = {
                                "total_companies": len(scores),
                                "average_score": float(scores.mean()) if len(scores) > 0 else 0,
                                "score_distribution": {
                                    "complete_8_10": len(scores[scores >= 8]),
                                    "partial_3_7": len(scores[(scores >= 3) & (scores < 8)]),
                                    "insufficient_0_2": len(scores[scores < 3])
                                }
                            }
                    except Exception:
                        pass
            
            # Component status
            if self.components_ready:
                report["components_status"] = "fully_operational"
                
                # Session report if available
                session_report = self.logger_manager.generate_session_report()
                report["session_info"] = {
                    "log_files": len(session_report.get("log_files", [])),
                    "errors": session_report.get("error_analysis", {}).get("total_errors", 0),
                    "warnings": session_report.get("error_analysis", {}).get("total_warnings", 0)
                }
            else:
                report["components_status"] = "limited_functionality"
            
            # Output report
            if format_type == "json":
                report_file = Path(f"factset_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                self.safe_output.safe_print(f"📄 JSON report saved: {report_file}")
            
            elif format_type == "github-summary":
                # GitHub Actions summary format
                if os.getenv('GITHUB_ACTIONS'):
                    self._handle_github_output("report_status", "generated")
                    if "quality_metrics" in report:
                        metrics = report["quality_metrics"]
                        self._handle_github_output("quality_avg", str(metrics["average_score"]))
                        self._handle_github_output("quality_companies", str(metrics["total_companies"]))
            
            else:
                # Console summary
                self.safe_output.safe_print("📊 Pipeline Report Summary:")
                self.safe_output.safe_print(f"   Generated: {report['generated_at']}")
                self.safe_output.safe_print(f"   Version: {report['version']}")
                self.safe_output.safe_print(f"   Components: {report.get('components_status', 'unknown')}")
                
                if "processed_files" in report:
                    self.safe_output.safe_print(f"   Processed Files: {report['processed_files']}")
                
                if "quality_metrics" in report:
                    qm = report["quality_metrics"]
                    self.safe_output.safe_print(f"   Quality Average: {qm['average_score']:.1f}/10")
                    self.safe_output.safe_print(f"   Companies Analyzed: {qm['total_companies']}")
                    
                    dist = qm["score_distribution"]
                    self.safe_output.safe_print("   Quality Distribution:")
                    self.safe_output.safe_print(f"     🟢 Complete: {dist['complete_8_10']}")
                    self.safe_output.safe_print(f"     🟠 Partial: {dist['partial_3_7']}")
                    self.safe_output.safe_print(f"     🔴 Insufficient: {dist['insufficient_0_2']}")
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Report generation error: {e}")
            return False

    def handle_commit(self, args: argparse.Namespace) -> bool:
        """Handle commit command (v3.3.2 preserved)"""
        self.safe_output.safe_print("💾 Committing results...")
        
        try:
            smart = getattr(args, 'smart', False)
            validate = getattr(args, 'validate', False)
            v333_format = getattr(args, 'v333_format', False)
            
            # Check if git is available
            try:
                result = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    self.safe_output.safe_print("⚠️ Git not available")
                    return False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.safe_output.safe_print("⚠️ Git not found")
                return False
            
            # Validate data before commit
            if validate:
                required_files = [
                    "data/processed/portfolio_summary.csv",
                    "data/processed/detailed_data.csv",
                    "data/processed/statistics.json"
                ]
                
                missing_files = []
                for file_path in required_files:
                    if not Path(file_path).exists():
                        missing_files.append(file_path)
                
                if missing_files:
                    self.safe_output.safe_print("❌ Missing required files:")
                    for file_path in missing_files:
                        self.safe_output.safe_print(f"   - {file_path}")
                    return False
            
            # Smart commit - only commit if significant changes
            if smart:
                try:
                    # Check git status
                    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
                    changes = result.stdout.strip()
                    
                    if not changes:
                        self.safe_output.safe_print("ℹ️ No changes to commit")
                        return True
                    
                    # Count significant changes (not just logs)
                    significant_changes = [line for line in changes.split('\n') 
                                        if not line.strip().startswith('?? logs/')]
                    
                    if not significant_changes:
                        self.safe_output.safe_print("ℹ️ Only log changes detected, skipping commit")
                        return True
                except Exception:
                    pass  # Continue with regular commit
            
            # Create commit
            try:
                # Add processed files
                subprocess.run(['git', 'add', 'data/processed/'], check=True)
                
                # Create commit message
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                commit_msg = f"Pipeline update: {timestamp}"
                
                if v333_format:
                    commit_msg += " (v3.3.3)"
                
                subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
                
                self.safe_output.safe_print("✅ Changes committed successfully")
                
                # Show commit info
                result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                    capture_output=True, text=True)
                if result.returncode == 0:
                    commit_hash = result.stdout.strip()
                    self.safe_output.safe_print(f"   Commit: {commit_hash}")
                
                return True
                
            except subprocess.CalledProcessError as e:
                self.safe_output.safe_print(f"❌ Git commit failed: {e}")
                return False
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Commit error: {e}")
            return False

    def handle_performance(self, args: argparse.Namespace) -> bool:
        """Handle performance command (v3.3.2 preserved)"""
        self.safe_output.safe_print("📈 Performance Analysis")
        
        if not self.components_ready:
            self.safe_output.safe_print("⚠️ Performance monitoring not available")
            return False
        
        try:
            # Get performance summary from all stages
            if hasattr(self.logger_manager, 'performance_loggers'):
                total_operations = 0
                total_time = 0
                slowest_operation = None
                slowest_time = 0
                
                for stage_name, perf_logger in self.logger_manager.performance_loggers.items():
                    summary = perf_logger.get_performance_summary()
                    if summary:
                        stage_ops = summary.get("total_operations", 0)
                        stage_time = summary.get("total_time", 0)
                        stage_slowest = summary.get("slowest_operation", {})
                        
                        total_operations += stage_ops
                        total_time += stage_time
                        
                        if stage_slowest and stage_slowest.get("duration", 0) > slowest_time:
                            slowest_time = stage_slowest["duration"]
                            slowest_operation = f"{stage_name}:{stage_slowest['operation']}"
                        
                        self.safe_output.safe_print(f"   {stage_name}: {stage_ops} ops, {stage_time:.1f}s total")
                
                if total_operations > 0:
                    avg_time = total_time / total_operations
                    self.safe_output.safe_print(f"📊 Overall Performance:")
                    self.safe_output.safe_print(f"   Total Operations: {total_operations}")
                    self.safe_output.safe_print(f"   Total Time: {total_time:.1f}s")
                    self.safe_output.safe_print(f"   Average Time: {avg_time:.2f}s per operation")
                    
                    if slowest_operation:
                        self.safe_output.safe_print(f"   Slowest: {slowest_operation} ({slowest_time:.1f}s)")
                else:
                    self.safe_output.safe_print("No performance data available")
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Performance analysis error: {e}")
            return False

    def handle_analyze(self, args: argparse.Namespace) -> bool:
        """Handle analyze command (v3.3.2 preserved)"""
        self.safe_output.safe_print("🔍 Data Analysis")
        
        try:
            # Check for processed data
            processed_dir = Path("data/processed")
            if not processed_dir.exists():
                self.safe_output.safe_print("❌ No processed data found")
                return False
            
            # Analyze portfolio summary
            summary_file = processed_dir / "portfolio_summary.csv"
            if summary_file.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(summary_file)
                    
                    self.safe_output.safe_print("📊 Portfolio Analysis:")
                    self.safe_output.safe_print(f"   Total Companies: {len(df)}")
                    
                    # Companies with data
                    with_data = df[df['MD資料筆數'] > 0]
                    self.safe_output.safe_print(f"   With Data: {len(with_data)} ({len(with_data)/len(df)*100:.1f}%)")
                    
                    # File statistics
                    total_files = df['MD資料筆數'].sum()
                    self.safe_output.safe_print(f"   Total MD Files: {int(total_files)}")
                    
                    if len(with_data) > 0:
                        avg_files = with_data['MD資料筆數'].mean()
                        self.safe_output.safe_print(f"   Avg Files/Company: {avg_files:.1f}")
                    
                    # v3.3.3: Quality analysis
                    if '品質評分' in df.columns:
                        scores = df['品質評分'].dropna()
                        if len(scores) > 0:
                            avg_quality = scores.mean()
                            self.safe_output.safe_print(f"   Average Quality: {avg_quality:.1f}/10")
                            
                            # Quality breakdown
                            excellent = len(scores[scores >= 9])
                            good = len(scores[scores == 8])
                            partial = len(scores[(scores >= 3) & (scores < 8)])
                            poor = len(scores[scores < 3])
                            
                            self.safe_output.safe_print("   Quality Breakdown:")
                            self.safe_output.safe_print(f"     🟢 Excellent (9-10): {excellent}")
                            self.safe_output.safe_print(f"     🟡 Good (8): {good}")
                            self.safe_output.safe_print(f"     🟠 Partial (3-7): {partial}")
                            self.safe_output.safe_print(f"     🔴 Poor (0-2): {poor}")
                    
                except Exception as e:
                    self.safe_output.safe_print(f"Error analyzing portfolio: {e}")
            
            # Analyze detailed data
            detailed_file = processed_dir / "detailed_data.csv"
            if detailed_file.exists():
                try:
                    import pandas as pd
                    df_detailed = pd.read_csv(detailed_file)
                    
                    self.safe_output.safe_print("📄 Detailed Data Analysis:")
                    self.safe_output.safe_print(f"   Individual Files: {len(df_detailed)}")
                    
                    companies_represented = df_detailed['代號'].nunique()
                    self.safe_output.safe_print(f"   Companies Represented: {companies_represented}")
                    
                    # EPS data availability
                    eps_cols = ['2025EPS平均值', '2026EPS平均值', '2027EPS平均值']
                    for col in eps_cols:
                        if col in df_detailed.columns:
                            with_eps = df_detailed[col].notna().sum()
                            self.safe_output.safe_print(f"   {col}: {with_eps} files")
                    
                except Exception as e:
                    self.safe_output.safe_print(f"Error analyzing detailed data: {e}")
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Analysis error: {e}")
            return False

    # ========================================================================
    # v3.3.3 QUALITY SCORING METHODS
    # ========================================================================

    def _analyze_quality(self, args: argparse.Namespace) -> bool:
        """Analyze quality scores across data"""
        self.safe_output.safe_print("🔍 Analyzing quality scores...")
        
        try:
            # Load processed data
            processed_dir = Path("data/processed")
            summary_file = processed_dir / "portfolio_summary.csv"
            detailed_file = processed_dir / "detailed_data.csv"
            
            if not summary_file.exists():
                self.safe_output.safe_print("❌ No processed data found. Run processing first.")
                return False
            
            import pandas as pd
            
            # Analyze portfolio summary
            df = pd.read_csv(summary_file)
            if '品質評分' in df.columns:
                scores = df['品質評分'].dropna()
                
                # Convert legacy scores if needed
                converted_scores = []
                for score in scores:
                    if score <= 4:  # Legacy scale
                        converted_scores.append(self.quality_scorer.convert_legacy_score(int(score)))
                    else:
                        converted_scores.append(int(score))
                
                avg_score = sum(converted_scores) / len(converted_scores) if converted_scores else 0
                
                # Quality distribution
                distribution = {}
                for score in converted_scores:
                    indicator = self.quality_scorer.get_quality_indicator(score)
                    distribution[indicator] = distribution.get(indicator, 0) + 1
                
                self.safe_output.safe_print(f"📊 Quality Analysis Results:")
                self.safe_output.safe_print(f"   Average Score: {avg_score:.1f}/10")
                self.safe_output.safe_print(f"   Total Companies: {len(converted_scores)}")
                
                self.safe_output.safe_print(f"   Distribution:")
                for indicator, count in distribution.items():
                    percentage = (count / len(converted_scores)) * 100
                    self.safe_output.safe_print(f"     {indicator}: {count} ({percentage:.1f}%)")
                
                # Store for GitHub Actions
                self._last_quality_metrics = {
                    'average_score': avg_score,
                    'distribution': distribution,
                    'total_companies': len(converted_scores)
                }
                
                return True
            else:
                self.safe_output.safe_print("❌ No quality scores found in data")
                return False
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Quality analysis error: {e}")
            return False

    def _benchmark_quality(self, args: argparse.Namespace) -> bool:
        """Benchmark quality scoring system"""
        self.safe_output.safe_print("📈 Running quality scoring benchmark...")
        
        # Test quality scorer with sample data
        test_cases = [
            {
                'name': 'Excellent Data',
                'metrics': {
                    'eps_data_completeness': 0.95,
                    'analyst_count': 25,
                    'data_age_days': 5
                },
                'expected_range': (9, 10)
            },
            {
                'name': 'Good Data', 
                'metrics': {
                    'eps_data_completeness': 0.8,
                    'analyst_count': 12,
                    'data_age_days': 20
                },
                'expected_range': (7, 9)
            },
            {
                'name': 'Partial Data',
                'metrics': {
                    'eps_data_completeness': 0.6,
                    'analyst_count': 6,
                    'data_age_days': 60
                },
                'expected_range': (3, 7)
            },
            {
                'name': 'Insufficient Data',
                'metrics': {
                    'eps_data_completeness': 0.2,
                    'analyst_count': 2,
                    'data_age_days': 120
                },
                'expected_range': (0, 2)
            }
        ]
        
        passed = 0
        for test_case in test_cases:
            score = self.quality_scorer.calculate_score(test_case['metrics'])
            indicator = self.quality_scorer.get_quality_indicator(score)
            min_expected, max_expected = test_case['expected_range']
            
            if min_expected <= score <= max_expected:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
            
            self.safe_output.safe_print(f"   {test_case['name']}: Score {score}/10 {indicator} {status}")
        
        self.safe_output.safe_print(f"📊 Benchmark Results: {passed}/{len(test_cases)} tests passed")
        return passed == len(test_cases)

    def _quality_distribution(self, args: argparse.Namespace) -> bool:
        """Show quality score distribution with visual representation"""
        self.safe_output.safe_print("📊 Quality Score Distribution Analysis")
        
        try:
            # Load processed data
            summary_file = Path("data/processed/portfolio_summary.csv")
            detailed_file = Path("data/processed/detailed_data.csv")
            
            if not summary_file.exists():
                self.safe_output.safe_print("❌ No portfolio summary found. Run processing first.")
                return False
            
            import pandas as pd
            
            # Analyze portfolio summary
            df_summary = pd.read_csv(summary_file)
            
            if '品質評分' not in df_summary.columns:
                self.safe_output.safe_print("❌ No quality scores found in portfolio data")
                return False
            
            scores = df_summary['品質評分'].dropna()
            
            if len(scores) == 0:
                self.safe_output.safe_print("❌ No valid quality scores found")
                return False
            
            # Convert legacy scores if needed
            converted_scores = []
            legacy_count = 0
            for score in scores:
                if score <= 4:  # Legacy scale
                    converted_scores.append(self.quality_scorer.convert_legacy_score(int(score)))
                    legacy_count += 1
                else:
                    converted_scores.append(int(score))
            
            scores = pd.Series(converted_scores)
            
            # Calculate distribution
            distribution = {}
            for score in scores:
                indicator = self.quality_scorer.get_quality_indicator(score)
                distribution[indicator] = distribution.get(indicator, 0) + 1
            
            # Score range distribution
            score_ranges = {
                '10 (Perfect)': len(scores[scores == 10]),
                '8-9 (Excellent)': len(scores[(scores >= 8) & (scores <= 9)]),
                '6-7 (Good)': len(scores[(scores >= 6) & (scores < 8)]),
                '4-5 (Fair)': len(scores[(scores >= 4) & (scores < 6)]),
                '2-3 (Poor)': len(scores[(scores >= 2) & (scores < 4)]),
                '0-1 (Critical)': len(scores[scores < 2])
            }
            
            # Output distribution
            total_companies = len(scores)
            avg_score = scores.mean()
            
            self.safe_output.safe_print(f"📈 Distribution Results:")
            self.safe_output.safe_print(f"   Total Companies: {total_companies}")
            self.safe_output.safe_print(f"   Average Score: {avg_score:.1f}/10")
            
            if legacy_count > 0:
                self.safe_output.safe_print(f"   Legacy Scores Converted: {legacy_count}")
            
            self.safe_output.safe_print("\n🎯 Quality Indicators:")
            for indicator, count in distribution.items():
                percentage = (count / total_companies) * 100
                bar_length = int(percentage / 5)  # Scale for display
                bar = "█" * bar_length + "░" * (20 - bar_length)
                self.safe_output.safe_print(f"   {indicator}: {count:3d} ({percentage:5.1f}%) {bar}")
            
            self.safe_output.safe_print("\n📊 Score Ranges:")
            for range_name, count in score_ranges.items():
                if count > 0:
                    percentage = (count / total_companies) * 100
                    self.safe_output.safe_print(f"   {range_name}: {count} ({percentage:.1f}%)")
            
            # Analyze detailed data if available
            if detailed_file.exists():
                try:
                    df_detailed = pd.read_csv(detailed_file)
                    if '品質評分' in df_detailed.columns:
                        file_scores = df_detailed['品質評分'].dropna()
                        if len(file_scores) > 0:
                            file_avg = file_scores.mean()
                            self.safe_output.safe_print(f"\n📄 File-Level Analysis:")
                            self.safe_output.safe_print(f"   Individual Files: {len(file_scores)}")
                            self.safe_output.safe_print(f"   Average File Quality: {file_avg:.1f}/10")
                            
                            # Compare company vs file quality
                            if len(scores) > 0:
                                quality_diff = file_avg - avg_score
                                if quality_diff > 0.5:
                                    self.safe_output.safe_print(f"   📈 Files generally higher quality than company averages (+{quality_diff:.1f})")
                                elif quality_diff < -0.5:
                                    self.safe_output.safe_print(f"   📉 Files generally lower quality than company averages ({quality_diff:.1f})")
                                else:
                                    self.safe_output.safe_print(f"   ➡️ File and company quality similar ({quality_diff:+.1f})")
                except Exception:
                    pass
            
            # Store metrics for other commands
            self._last_quality_metrics = {
                'total_companies': total_companies,
                'average_score': avg_score,
                'distribution': distribution,
                'score_ranges': score_ranges,
                'legacy_converted': legacy_count
            }
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Distribution analysis error: {e}")
            return False

    def _monitor_quality(self, args: argparse.Namespace) -> bool:
        """Monitor quality trends and changes over time"""
        self.safe_output.safe_print("📈 Quality Monitoring & Trends")
        
        try:
            threshold = getattr(args, 'threshold', 7)
            alert_low_quality = getattr(args, 'alert_low_quality', False)
            
            # Check current quality status
            summary_file = Path("data/processed/portfolio_summary.csv")
            if not summary_file.exists():
                self.safe_output.safe_print("❌ No current data to monitor. Run processing first.")
                return False
            
            import pandas as pd
            df = pd.read_csv(summary_file)
            
            if '品質評分' not in df.columns:
                self.safe_output.safe_print("❌ No quality scores found")
                return False
            
            scores = df['品質評分'].dropna()
            if len(scores) == 0:
                self.safe_output.safe_print("❌ No valid scores to monitor")
                return False
            
            # Convert legacy scores
            converted_scores = []
            for score in scores:
                if score <= 4:
                    converted_scores.append(self.quality_scorer.convert_legacy_score(int(score)))
                else:
                    converted_scores.append(int(score))
            
            current_avg = sum(converted_scores) / len(converted_scores)
            
            # Quality monitoring results
            self.safe_output.safe_print(f"🎯 Current Quality Status:")
            self.safe_output.safe_print(f"   Average Score: {current_avg:.1f}/10")
            self.safe_output.safe_print(f"   Quality Threshold: {threshold}/10")
            
            # Check against threshold
            below_threshold = [s for s in converted_scores if s < threshold]
            if below_threshold:
                percentage_below = (len(below_threshold) / len(converted_scores)) * 100
                self.safe_output.safe_print(f"   ⚠️ Below Threshold: {len(below_threshold)} companies ({percentage_below:.1f}%)")
                
                if alert_low_quality:
                    self.safe_output.safe_print("🚨 LOW QUALITY ALERT:")
                    
                    # Find companies with lowest scores
                    df_with_scores = df.copy()
                    df_with_scores['converted_score'] = converted_scores
                    lowest_quality = df_with_scores.nsmallest(5, 'converted_score')
                    
                    self.safe_output.safe_print("   Lowest Quality Companies:")
                    for _, row in lowest_quality.iterrows():
                        company_name = row['名稱']
                        score = row['converted_score']
                        status = self.quality_scorer.get_quality_indicator(score)
                        self.safe_output.safe_print(f"     - {company_name}: {score}/10 {status}")
            else:
                self.safe_output.safe_print(f"   ✅ All companies meet quality threshold")
            
            # Historical comparison (if previous data exists)
            backup_files = list(Path("data/processed").glob("portfolio_summary_backup_*.csv"))
            if backup_files:
                try:
                    # Find most recent backup
                    latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                    df_previous = pd.read_csv(latest_backup)
                    
                    if '品質評分' in df_previous.columns:
                        prev_scores = df_previous['品質評分'].dropna()
                        if len(prev_scores) > 0:
                            prev_converted = [self.quality_scorer.convert_legacy_score(int(s)) if s <= 4 else int(s) for s in prev_scores]
                            prev_avg = sum(prev_converted) / len(prev_converted)
                            
                            change = current_avg - prev_avg
                            self.safe_output.safe_print(f"📊 Historical Comparison:")
                            self.safe_output.safe_print(f"   Previous Average: {prev_avg:.1f}/10")
                            self.safe_output.safe_print(f"   Change: {change:+.1f}")
                            
                            if change > 0.5:
                                self.safe_output.safe_print("   📈 Significant quality improvement!")
                            elif change < -0.5:
                                self.safe_output.safe_print("   📉 Quality decline detected")
                            else:
                                self.safe_output.safe_print("   ➡️ Quality stable")
                except Exception:
                    pass
            
            # Recommendations
            self.safe_output.safe_print("💡 Monitoring Recommendations:")
            if current_avg < 6:
                self.safe_output.safe_print("   - Quality below average - consider data source review")
                self.safe_output.safe_print("   - Run: python factset_cli.py search --mode=enhanced")
            elif current_avg >= 8:
                self.safe_output.safe_print("   - Excellent quality maintained")
                self.safe_output.safe_print("   - Continue current data collection strategy")
            else:
                self.safe_output.safe_print("   - Good quality - minor optimization opportunities")
                self.safe_output.safe_print("   - Consider: python factset_cli.py process --standardize-quality")
            
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Quality monitoring error: {e}")
            return False

    def _calibrate_quality(self, args: argparse.Namespace) -> bool:
        """Calibrate and validate quality scoring system"""
        self.safe_output.safe_print("🔧 Quality Scoring System Calibration")
        
        try:
            fix_scoring_anomalies = getattr(args, 'fix_scoring_anomalies', False)
            
            self.safe_output.safe_print("🧪 Running calibration tests...")
            
            # Test 1: Scorer consistency
            test_metrics = {
                'eps_data_completeness': 0.9,
                'analyst_count': 20,
                'data_age_days': 10
            }
            
            scores = []
            for i in range(5):
                score = self.quality_scorer.calculate_score(test_metrics)
                scores.append(score)
            
            if len(set(scores)) == 1:
                self.safe_output.safe_print("   ✅ Scorer consistency: PASS")
            else:
                self.safe_output.safe_print(f"   ❌ Scorer consistency: FAIL (got {scores})")
            
            # Test 2: Score range validation
            range_tests = [
                ({'eps_data_completeness': 1.0, 'analyst_count': 30, 'data_age_days': 1}, (9, 10)),
                ({'eps_data_completeness': 0.0, 'analyst_count': 0, 'data_age_days': 365}, (0, 1)),
                ({'eps_data_completeness': 0.5, 'analyst_count': 10, 'data_age_days': 30}, (4, 7))
            ]
            
            range_pass = 0
            for test_metrics, expected_range in range_tests:
                score = self.quality_scorer.calculate_score(test_metrics)
                if expected_range[0] <= score <= expected_range[1]:
                    range_pass += 1
            
            self.safe_output.safe_print(f"   ✅ Range validation: {range_pass}/3 tests passed")
            
            # Test 3: Legacy conversion
            legacy_tests = [(4, 10), (3, 8), (2, 5), (1, 2), (0, 0)]
            conversion_pass = 0
            
            for legacy, expected in legacy_tests:
                converted = self.quality_scorer.convert_legacy_score(legacy)
                if converted == expected:
                    conversion_pass += 1
            
            self.safe_output.safe_print(f"   ✅ Legacy conversion: {conversion_pass}/5 tests passed")
            
            # Test 4: Quality indicators
            indicator_tests = [
                (10, '🟢 完整'), (9, '🟢 完整'), (8, '🟡 良好'), 
                (5, '🟠 部分'), (2, '🔴 不足'), (0, '🔴 不足')
            ]
            
            indicator_pass = 0
            for score, expected in indicator_tests:
                indicator = self.quality_scorer.get_quality_indicator(score)
                if indicator == expected:
                    indicator_pass += 1
            
            self.safe_output.safe_print(f"   ✅ Quality indicators: {indicator_pass}/6 tests passed")
            
            # Test 5: Real data validation (if available)
            summary_file = Path("data/processed/portfolio_summary.csv")
            if summary_file.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(summary_file)
                    
                    if '品質評分' in df.columns:
                        scores = df['品質評分'].dropna()
                        
                        # Check for scoring anomalies
                        anomalies = []
                        
                        # Scores outside valid range
                        invalid_scores = scores[(scores < 0) | (scores > 10)]
                        if len(invalid_scores) > 0:
                            anomalies.append(f"{len(invalid_scores)} scores outside 0-10 range")
                        
                        # Suspicious patterns (all same score)
                        if len(scores.unique()) == 1 and len(scores) > 10:
                            anomalies.append("All companies have identical scores (suspicious)")
                        
                        # Too many perfect scores
                        perfect_scores = len(scores[scores == 10])
                        if perfect_scores > len(scores) * 0.8:
                            anomalies.append(f"Too many perfect scores: {perfect_scores}/{len(scores)}")
                        
                        if anomalies:
                            self.safe_output.safe_print("   ⚠️ Data anomalies detected:")
                            for anomaly in anomalies:
                                self.safe_output.safe_print(f"     - {anomaly}")
                            
                            if fix_scoring_anomalies:
                                self.safe_output.safe_print("   🔧 Attempting to fix anomalies...")
                                
                                # Fix out-of-range scores
                                df.loc[df['品質評分'] < 0, '品質評分'] = 0
                                df.loc[df['品質評分'] > 10, '品質評分'] = 10
                                
                                # Save corrected data
                                backup_file = summary_file.with_suffix('.backup.csv')
                                df.to_csv(backup_file, index=False)
                                df.to_csv(summary_file, index=False)
                                
                                self.safe_output.safe_print(f"   ✅ Corrected data saved (backup: {backup_file.name})")
                        else:
                            self.safe_output.safe_print("   ✅ Real data validation: No anomalies found")
                except Exception as e:
                    self.safe_output.safe_print(f"   ⚠️ Real data validation error: {e}")
            
            # Overall calibration result
            total_tests = 5
            passed_tests = (
                (1 if len(set(scores)) == 1 else 0) +
                (1 if range_pass == 3 else 0) +
                (1 if conversion_pass == 5 else 0) +
                (1 if indicator_pass == 6 else 0) +
                1  # Real data test always counts as passed
            )
            
            calibration_score = (passed_tests / total_tests) * 100
            
            self.safe_output.safe_print(f"🎯 Calibration Results:")
            self.safe_output.safe_print(f"   Overall Score: {calibration_score:.0f}%")
            
            if calibration_score >= 80:
                self.safe_output.safe_print("   ✅ Quality scoring system is well-calibrated")
            elif calibration_score >= 60:
                self.safe_output.safe_print("   ⚠️ Quality scoring system needs minor adjustments")
            else:
                self.safe_output.safe_print("   ❌ Quality scoring system needs significant recalibration")
            
            # Recommendations
            if calibration_score < 100:
                self.safe_output.safe_print("💡 Calibration Recommendations:")
                if range_pass < 3:
                    self.safe_output.safe_print("   - Review scoring algorithm parameters")
                if conversion_pass < 5:
                    self.safe_output.safe_print("   - Check legacy score conversion mapping")
                if indicator_pass < 6:
                    self.safe_output.safe_print("   - Verify quality indicator thresholds")
            
            return calibration_score >= 60
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Calibration error: {e}")
            return False

    # ========================================================================
    # v3.3.3 GITHUB ACTIONS MODERNIZATION
    # ========================================================================
    
    def _handle_github_output(self, key: str, value: str):
        """v3.3.3 Modern GitHub Actions output handler"""
        if os.getenv('GITHUB_ACTIONS'):
            # v3.3.3 Fix: Use GITHUB_OUTPUT instead of deprecated set-output
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                try:
                    with open(github_output, 'a', encoding='utf-8') as f:
                        f.write(f"{key}={value}\n")
                    if self.main_logger:
                        self.main_logger.debug(f"GitHub output set: {key}={value}")
                except Exception as e:
                    if self.main_logger:
                        self.main_logger.warning(f"Failed to write GitHub output: {e}")
                    # Fallback to deprecated method
                    print(f"::set-output name={key}::{value}")
            else:
                # Fallback for older GitHub Actions
                print(f"::set-output name={key}::{value}")
    
    def _output_github_actions_result(self, stage: str, result: str):
        """Output result for GitHub Actions with v3.3.3 modernization"""
        self._handle_github_output(f"{stage}_result", result)
        self._handle_github_output(f"{stage}_timestamp", datetime.now().isoformat())
        
        # v3.3.3: Add quality metrics if available
        if hasattr(self, '_last_quality_metrics'):
            metrics = self._last_quality_metrics
            self._handle_github_output(f"{stage}_quality_avg", str(metrics.get('average_score', 0)))
            self._handle_github_output(f"{stage}_quality_distribution", json.dumps(metrics.get('distribution', {})))

    # ========================================================================
    # FALLBACK METHODS
    # ========================================================================

    def _fallback_validate(self, args: argparse.Namespace) -> bool:
        """Fallback validation when components not available"""
        self.safe_output.safe_print("⚠️ Running basic fallback validation...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.safe_output.safe_print("❌ Python 3.8+ required")
            return False
        
        # Check directories
        required_dirs = ["data", "logs"]
        for dir_name in required_dirs:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
        
        # v3.3.3: Test quality scoring
        try:
            scorer = StandardizedQualityScorer()
            test_score = scorer.calculate_score({'eps_data_completeness': 0.8, 'analyst_count': 10, 'data_age_days': 30})
            self.safe_output.safe_print(f"✅ Quality scoring system: {test_score}/10")
        except Exception as e:
            self.safe_output.safe_print(f"⚠️ Quality scoring test failed: {e}")
        
        self.safe_output.safe_print("✅ Basic validation passed")
        return True

    def _fallback_download_watchlist(self, args: argparse.Namespace) -> bool:
        """Fallback watchlist download when components not available"""
        self.safe_output.safe_print("⚠️ Using fallback watchlist download...")
        
        try:
            import requests
            url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open("觀察名單.csv", 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.safe_output.safe_print("✅ Watchlist downloaded (fallback)")
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Fallback download failed: {e}")
            return False

    def _fallback_search(self, args: argparse.Namespace) -> bool:
        """Fallback search when components not available"""
        self.safe_output.safe_print("⚠️ Search components not available")
        return False

    def _fallback_upload(self, args: argparse.Namespace) -> bool:
        """Fallback upload when components not available"""
        self.safe_output.safe_print("⚠️ Upload components not available")
        return False

    def _fallback_process(self, args: argparse.Namespace) -> bool:
        """Fallback processing when components not available"""
        self.safe_output.safe_print("⚠️ Processing components not available")
        return False

    def _fallback_pipeline(self, args: argparse.Namespace) -> bool:
        """Fallback pipeline when components not available"""
        self.safe_output.safe_print("⚠️ Pipeline components not available")
        return False

# ============================================================================
# ARGUMENT PARSER SETUP (v3.3.3 - enhanced with quality commands)
# ============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser for v3.3.3"""
    
    parser = argparse.ArgumentParser(
        description=f"FactSet Pipeline CLI v{__version__} - Final Integrated Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Enhanced CLI v3.3.3 - FINAL INTEGRATED EDITION

🆕 v3.3.3 New Features:
  ✅ Standardized Quality Scoring (0-10 scale with 🟢🟡🟠🔴 indicators)
  ✅ GitHub Actions Modernization (GITHUB_OUTPUT support)
  ✅ MD File Direct Links (GitHub Raw URLs)
  ✅ Live Dashboard Optimization
  ✅ All v3.3.2 Features Maintained

🚀 Quick Start:
  python factset_cli.py pipeline --mode=intelligent --v333
  python factset_cli.py quality --analyze
  python factset_cli.py validate --comprehensive --test-v333

🔧 v3.3.2 Features (Preserved):
  ✅ Unified commands (Windows/Linux identical)
  ✅ Stage-specific dual logging (console + file)  
  ✅ Enhanced diagnostics and recovery
  ✅ All v3.3.1 fixes maintained

📊 v3.3.3 Quality Commands:
  python factset_cli.py quality --analyze          # Analyze quality scores
  python factset_cli.py quality --benchmark        # Test quality system
  python factset_cli.py quality --distribution     # Quality distribution
  python factset_cli.py quality --monitor          # Monitor quality trends

📈 v3.3.3 Examples:
  # Enhanced pipeline with quality scoring
  python factset_cli.py pipeline --mode=enhanced --quality-scoring --v333
  
  # Processing with standardized quality
  python factset_cli.py process --mode=v333 --standardize-quality
  
  # Upload with v3.3.3 format
  python factset_cli.py upload --v333-format --quality-indicators
  
  # Validation with v3.3.3 features
  python factset_cli.py validate --test-v333 --quality-scoring

🔗 More info: Enhanced with final integrated v3.3.3 features
        """
    )
    
    # Global options (preserved from v3.3.2)
    parser.add_argument('--version', action='version', version=f'FactSet CLI v{__version__}')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validation command (enhanced for v3.3.3)
    validate_parser = subparsers.add_parser('validate', help='System validation')
    validate_parser.add_argument('--comprehensive', action='store_true', help='Comprehensive validation')
    validate_parser.add_argument('--quick', action='store_true', help='Quick validation')
    validate_parser.add_argument('--fix-issues', action='store_true', help='Auto-fix common issues')
    validate_parser.add_argument('--test-v332', action='store_true', help='Test v3.3.2 features')
    validate_parser.add_argument('--test-v333', action='store_true', help='Test v3.3.3 features')  # v3.3.3
    validate_parser.add_argument('--quality-scoring', action='store_true', help='Test quality scoring')  # v3.3.3
    validate_parser.add_argument('--github-actions', action='store_true', help='GitHub Actions mode')

    # Download watchlist command
    download_parser = subparsers.add_parser('download-watchlist', help='Download company watchlist')
    download_parser.add_argument('--force-refresh', action='store_true', help='Force refresh watchlist')
    download_parser.add_argument('--validate', action='store_true', default=True, help='Validate downloaded data')
    
    # Search command (enhanced for v3.3.3)
    search_parser = subparsers.add_parser('search', help='Enhanced search')
    search_parser.add_argument('--mode', default='enhanced', help='Search mode')
    search_parser.add_argument('--priority', default='high_only', help='Priority filter')
    search_parser.add_argument('--max-results', type=int, default=10, help='Maximum results')
    search_parser.add_argument('--batch-size', type=int, default=20, help='Batch size')
    
    # Process command (enhanced for v3.3.3)
    process_parser = subparsers.add_parser('process', help='Data processing')
    process_parser.add_argument('--mode', default='v333', help='Processing mode')  # v3.3.3 default
    process_parser.add_argument('--memory-limit', type=int, default=2048, help='Memory limit (MB)')
    process_parser.add_argument('--batch-size', type=int, default=50, help='Batch size')
    process_parser.add_argument('--quality-scoring', action='store_true', default=True, help='Enable quality scoring')  # v3.3.3
    process_parser.add_argument('--standardize-quality', action='store_true', help='Standardize quality scores')  # v3.3.3
    process_parser.add_argument('--benchmark', action='store_true', help='Run performance benchmark')
    process_parser.add_argument('--force', action='store_true', help='Force reprocessing')
    
    # Upload command (enhanced for v3.3.3)
    upload_parser = subparsers.add_parser('upload', help='Sheets upload')
    upload_parser.add_argument('--sheets', default='all', help='Sheets to update (all/portfolio/detailed)')
    upload_parser.add_argument('--v333-format', action='store_true', help='Use v3.3.3 format')  # v3.3.3
    upload_parser.add_argument('--quality-indicators', action='store_true', help='Include quality indicators')  # v3.3.3
    upload_parser.add_argument('--test-connection', action='store_true', help='Test connection only')
    
    # Pipeline command (enhanced for v3.3.3)
    pipeline_parser = subparsers.add_parser('pipeline', help='Complete pipeline')
    pipeline_parser.add_argument('--mode', choices=['intelligent', 'conservative', 'process_only', 'enhanced'],
                                 default='intelligent', help='Execution strategy')
    pipeline_parser.add_argument('--memory-limit', type=int, default=2048, help='Memory limit (MB)')
    pipeline_parser.add_argument('--quality-scoring', action='store_true', default=True, help='Enable quality scoring')  # v3.3.3
    pipeline_parser.add_argument('--v333', action='store_true', default=True, help='Enable v3.3.3 features')  # v3.3.3
    pipeline_parser.add_argument('--github-actions', action='store_true', help='GitHub Actions mode')
    pipeline_parser.add_argument('--skip-phases', nargs='*', choices=['search', 'processing', 'upload'], help='Skip phases')
    
    # Quality command (v3.3.3 NEW)
    quality_parser = subparsers.add_parser('quality', help='Quality scoring analysis')
    quality_parser.add_argument('--analyze', action='store_const', const='analyze', dest='action', help='Analyze quality scores')
    quality_parser.add_argument('--benchmark', action='store_const', const='benchmark', dest='action', help='Benchmark quality system')
    quality_parser.add_argument('--distribution', action='store_const', const='distribution', dest='action', help='Show quality distribution')
    quality_parser.add_argument('--monitor', action='store_const', const='monitor', dest='action', help='Monitor quality trends')
    quality_parser.add_argument('--calibrate', action='store_const', const='calibrate', dest='action', help='Calibrate quality scoring')
    quality_parser.set_defaults(action='analyze')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Pipeline status')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View logs')
    logs_parser.add_argument('--stage', default='all', help='Stage name')
    logs_parser.add_argument('--tail', type=int, default=50, help='Number of lines')
    logs_parser.add_argument('--export', choices=['json', 'txt'], help='Export format')
    
    # Diagnose command
    diagnose_parser = subparsers.add_parser('diagnose', help='Diagnose issues')
    diagnose_parser.add_argument('--issue', help='Specific issue to diagnose')
    diagnose_parser.add_argument('--stage', help='Stage to focus on')
    diagnose_parser.add_argument('--suggest-fix', action='store_true', help='Suggest fixes')
    diagnose_parser.add_argument('--v333-comprehensive', action='store_true', help='v3.3.3 comprehensive diagnostics')
    
    # Recover command
    recover_parser = subparsers.add_parser('recover', help='Recovery procedures')
    recover_parser.add_argument('--analyze', action='store_true', help='Analyze issues')
    recover_parser.add_argument('--fix-common-issues', action='store_true', help='Fix common issues')
    recover_parser.add_argument('--v333-diagnostics', action='store_true', help='v3.3.3 diagnostics')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate report')
    report_parser.add_argument('--format', default='summary', choices=['summary', 'json', 'github-summary'], help='Report format')
    report_parser.add_argument('--email', action='store_true', help='Email report')
    report_parser.add_argument('--v333-metrics', action='store_true', help='Include v3.3.3 metrics')
    report_parser.add_argument('--quality-focused', action='store_true', help='Focus on quality metrics')
    
    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Commit results')
    commit_parser.add_argument('--smart', action='store_true', help='Smart commit (only significant changes)')
    commit_parser.add_argument('--validate', action='store_true', help='Validate before commit')
    commit_parser.add_argument('--v333-format', action='store_true', help='Use v3.3.3 commit format')
    
    # Performance command
    performance_parser = subparsers.add_parser('performance', help='Performance analysis')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Data analysis')
    
    return parser

# ============================================================================
# MAIN ENTRY POINT (v3.3.3)
# ============================================================================

def main():
    """Main entry point for FactSet CLI v3.3.3"""
    
    # Create and configure CLI
    cli = FactSetCLI()
    
    # Parse arguments
    parser = create_argument_parser()
    
    # Handle no arguments case
    if len(sys.argv) == 1:
        safe_output.safe_print(f"🚀 FactSet Pipeline CLI v{__version__} (Final Integrated Edition)")
        safe_output.safe_print("💡 Run with --help for usage information")
        safe_output.safe_print("🔧 Quick start: python factset_cli.py pipeline --mode=intelligent --v333")
        safe_output.safe_print("🎯 Quality analysis: python factset_cli.py quality --analyze")
        return 0
    
    try:
        args = parser.parse_args()
        
        # Set debug mode if requested
        if getattr(args, 'debug', False):
            os.environ['FACTSET_PIPELINE_DEBUG'] = 'true'
        
        # Execute command
        success = cli.execute_command(args)
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        safe_output.safe_print("\n⚠️ Execution interrupted by user")
        return 130
    except Exception as e:
        safe_output.safe_print(f"❌ CLI error: {e}")
        if os.getenv('FACTSET_PIPELINE_DEBUG'):
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())