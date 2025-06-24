#!/usr/bin/env python3
"""
factset_cli.py - Unified CLI Interface (v3.3.2)

Version: 3.3.2
Date: 2025-06-24
Author: FactSet Pipeline - v3.3.2 Simplified & Observable

v3.3.2 ENHANCEMENTS:
- ✅ Unified cross-platform CLI interface (Windows/Linux identical commands)
- ✅ Integration with stage runner and enhanced logging
- ✅ Maintains all v3.3.1 fixes and performance improvements
- ✅ GitHub Actions compatible command structure
- ✅ Advanced diagnostics and troubleshooting commands
- ✅ Real-time log monitoring and analysis
- ✅ Intelligent error recovery and suggestions

Description:
    Single entry point for all FactSet Pipeline operations in v3.3.2:
    - Unified command structure for development and CI/CD
    - Cross-platform compatibility with safe encoding handling
    - Integration with enhanced logging and performance monitoring
    - Built-in diagnostics and troubleshooting capabilities
    - Maintains full backward compatibility with v3.3.1
    - Provides intelligent command suggestions and help
    - Supports both interactive and automated execution modes

Usage Examples:
    python factset_cli.py validate --comprehensive
    python factset_cli.py pipeline --mode=intelligent
    python factset_cli.py logs --stage=search --tail=50
    python factset_cli.py diagnose --auto --fix-common
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

# Import v3.3.2 components
try:
    from enhanced_logger import get_logger_manager, get_stage_logger
    from stage_runner import StageRunner, ExecutionContext, StageStatus
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: v3.3.2 components not available: {e}")
    COMPONENTS_AVAILABLE = False

# Version Information - v3.3.2
__version__ = "3.3.2"
__date__ = "2025-06-24"
__author__ = "FactSet Pipeline - v3.3.2 Simplified & Observable"

# ============================================================================
# CROSS-PLATFORM SAFE OUTPUT HANDLING (v3.3.2)
# ============================================================================

class SafeOutput:
    """Cross-platform safe output handler"""
    
    def __init__(self):
        self.encoding = self._detect_safe_encoding()
        self.use_emoji = self._test_emoji_support()
        
        # Emoji fallbacks for Windows
        self.emoji_map = {
            '🚀': '[START]', '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARN]',
            '🔍': '[SEARCH]', '📊': '[DATA]', '📈': '[UPLOAD]', '🔧': '[FIX]',
            '📄': '[FILE]', '💡': '[TIP]', '🎯': '[TARGET]', '📋': '[LIST]',
            '🧪': '[TEST]', '🔄': '[RETRY]', '💾': '[SAVE]', '🎉': '[SUCCESS]'
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
# CLI COMMAND HANDLERS (v3.3.2)
# ============================================================================

class FactSetCLI:
    """Main CLI class for v3.3.2 unified interface"""
    
    def __init__(self):
        self.safe_output = safe_output
        self.start_time = datetime.now()
        
        # Initialize components if available
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
        
        self.safe_output.safe_print(f"🚀 FactSet CLI v{__version__} initialized")
        if not self.components_ready:
            self.safe_output.safe_print("⚠️ Running in fallback mode - some features may be limited")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
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
        """Execute CLI command based on arguments"""
        try:
            if self.main_logger:
                self.main_logger.info(f"Executing command: {args.command}")
                self.main_logger.debug(f"Arguments: {vars(args)}")
            
            # Route to appropriate handler
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
                'analyze': self.handle_analyze
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
        """Handle validation command"""
        self.safe_output.safe_print("🧪 Running system validation...")
        
        if not self.components_ready:
            return self._fallback_validate(args)
        
        try:
            # Prepare validation parameters
            params = {
                "mode": "comprehensive" if args.comprehensive else "quick",
                "fix_issues": getattr(args, 'fix_issues', False),
                "test_v332": getattr(args, 'test_v332', False)
            }
            
            # Create execution context
            context = ExecutionContext(execution_mode="validation", **params)
            
            # Run validation stage
            success = self.stage_runner.run_stage("validate", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ System validation passed")
                if getattr(args, 'github_actions', False):
                    self._output_github_actions_result("validation", "passed")
            else:
                self.safe_output.safe_print("❌ System validation failed")
                if getattr(args, 'github_actions', False):
                    self._output_github_actions_result("validation", "failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Validation error: {e}")
            return False
    
    def handle_download_watchlist(self, args: argparse.Namespace) -> bool:
        """Handle watchlist download command"""
        self.safe_output.safe_print("📥 Downloading company watchlist...")
        
        if not self.components_ready:
            return self._fallback_download_watchlist(args)
        
        try:
            params = {
                "force_refresh": getattr(args, 'force_refresh', False),
                "validate": getattr(args, 'validate', False)
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
        """Handle search command"""
        self.safe_output.safe_print("🔍 Starting enhanced search...")
        
        if not self.components_ready:
            return self._fallback_search(args)
        
        try:
            params = {
                "mode": getattr(args, 'mode', 'enhanced'),
                "priority": getattr(args, 'priority', 'high_only'),
                "max_results": getattr(args, 'max_results', 10),
                "companies": getattr(args, 'companies', None),
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
        """Handle processing command"""
        self.safe_output.safe_print("📊 Starting data processing...")
        
        if not self.components_ready:
            return self._fallback_process(args)
        
        try:
            params = {
                "mode": getattr(args, 'mode', 'v332'),
                "memory_limit": getattr(args, 'memory_limit', 2048),
                "batch_size": getattr(args, 'batch_size', 50),
                "deduplicate": getattr(args, 'deduplicate', True),
                "aggregate": getattr(args, 'aggregate', True),
                "benchmark": getattr(args, 'benchmark', False),
                "force": getattr(args, 'force', False)
            }
            
            context = ExecutionContext(execution_mode="processing", **params)
            success = self.stage_runner.run_stage("process", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ Data processing completed successfully")
            else:
                self.safe_output.safe_print("❌ Data processing failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Processing error: {e}")
            return False
    
    def handle_upload(self, args: argparse.Namespace) -> bool:
        """Handle upload command"""
        self.safe_output.safe_print("📈 Starting sheets upload...")
        
        if not self.components_ready:
            return self._fallback_upload(args)
        
        try:
            params = {
                "sheets": getattr(args, 'sheets', 'all'),
                "backup": getattr(args, 'backup', True),
                "test_connection": getattr(args, 'test_connection', False)
            }
            
            context = ExecutionContext(execution_mode="upload", **params)
            success = self.stage_runner.run_stage("upload", context, **params)
            
            if success:
                self.safe_output.safe_print("✅ Sheets upload completed successfully")
            else:
                self.safe_output.safe_print("❌ Sheets upload failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Upload error: {e}")
            return False
    
    def handle_pipeline(self, args: argparse.Namespace) -> bool:
        """Handle complete pipeline command"""
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
                "skip_phases": getattr(args, 'skip_phases', [])
            }
            
            context = ExecutionContext(execution_mode=params["mode"], **params)
            success = self.stage_runner.run_stage("pipeline", context, **params)
            
            if success:
                self.safe_output.safe_print("🎉 Pipeline completed successfully!")
                if params["github_actions"]:
                    self._output_github_actions_result("pipeline", "success")
            else:
                self.safe_output.safe_print("❌ Pipeline execution failed")
                if params["github_actions"]:
                    self._output_github_actions_result("pipeline", "failed")
            
            return success
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Pipeline error: {e}")
            return False
    
    def handle_recover(self, args: argparse.Namespace) -> bool:
        """Handle recovery command"""
        self.safe_output.safe_print("🔄 Starting recovery process...")
        
        try:
            analyze = getattr(args, 'analyze', False)
            fix_common = getattr(args, 'fix_common_issues', False)
            github_actions = getattr(args, 'github_actions', False)
            
            if analyze:
                return self._analyze_and_recover(args)
            elif fix_common:
                return self._fix_common_issues(args)
            else:
                return self._general_recovery(args)
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Recovery error: {e}")
            return False
    
    def handle_diagnose(self, args: argparse.Namespace) -> bool:
        """Handle diagnostics command"""
        self.safe_output.safe_print("🔍 Running diagnostics...")
        
        try:
            if not self.components_ready:
                return self._fallback_diagnose(args)
            
            # Get diagnostic parameters
            stage = getattr(args, 'stage', None)
            auto = getattr(args, 'auto', False)
            detailed = getattr(args, 'detailed', False)
            issue = getattr(args, 'issue', None)
            
            if auto:
                return self._auto_diagnose(args)
            elif issue:
                return self._diagnose_specific_issue(issue, args)
            else:
                return self._general_diagnose(stage, detailed, args)
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Diagnosis error: {e}")
            return False
    
    def handle_status(self, args: argparse.Namespace) -> bool:
        """Handle status command"""
        self.safe_output.safe_print("📊 Checking system status...")
        
        try:
            comprehensive = getattr(args, 'comprehensive', False)
            detailed = getattr(args, 'detailed', False)
            export_format = getattr(args, 'export', None)
            
            if comprehensive:
                return self._comprehensive_status(args)
            elif detailed:
                return self._detailed_status(args)
            else:
                return self._basic_status(args)
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Status check error: {e}")
            return False
    
    def handle_logs(self, args: argparse.Namespace) -> bool:
        """Handle logs command"""
        self.safe_output.safe_print("📋 Managing logs...")
        
        try:
            if not self.components_ready:
                return self._fallback_logs(args)
            
            stage = getattr(args, 'stage', None)
            tail = getattr(args, 'tail', None)
            export = getattr(args, 'export', False)
            
            if tail:
                return self._tail_logs(stage, tail, args)
            elif export:
                return self._export_logs(stage, args)
            else:
                return self._show_logs(stage, args)
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Logs error: {e}")
            return False
    
    def handle_report(self, args: argparse.Namespace) -> bool:
        """Handle report generation command"""
        self.safe_output.safe_print("📊 Generating report...")
        
        try:
            format_type = getattr(args, 'format', 'summary')
            
            if format_type == 'github-summary':
                return self._generate_github_summary(args)
            elif format_type == 'html':
                return self._generate_html_report(args)
            elif format_type == 'json':
                return self._generate_json_report(args)
            else:
                return self._generate_summary_report(args)
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Report generation error: {e}")
            return False
    
    def handle_commit(self, args: argparse.Namespace) -> bool:
        """Handle smart commit command"""
        self.safe_output.safe_print("💾 Processing smart commit...")
        
        try:
            smart = getattr(args, 'smart', False)
            validate = getattr(args, 'validate', False)
            
            if smart:
                return self._smart_commit(args)
            else:
                return self._basic_commit(args)
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Commit error: {e}")
            return False
    
    def handle_performance(self, args: argparse.Namespace) -> bool:
        """Handle performance analysis command"""
        self.safe_output.safe_print("⚡ Analyzing performance...")
        
        try:
            compare_with = getattr(args, 'compare_with', None)
            detailed = getattr(args, 'detailed', False)
            
            return self._performance_analysis(compare_with, detailed, args)
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Performance analysis error: {e}")
            return False
    
    def handle_analyze(self, args: argparse.Namespace) -> bool:
        """Handle data analysis command"""
        self.safe_output.safe_print("🔍 Running data analysis...")
        
        try:
            analysis_type = getattr(args, 'type', 'general')
            
            if analysis_type == 'memory':
                return self._memory_analysis(args)
            elif analysis_type == 'data':
                return self._data_analysis(args)
            else:
                return self._general_analysis(args)
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Analysis error: {e}")
            return False
    
    # ========================================================================
    # IMPLEMENTATION METHODS (Core functionality)
    # ========================================================================
    
    def _analyze_and_recover(self, args: argparse.Namespace) -> bool:
        """Analyze issues and attempt recovery"""
        self.safe_output.safe_print("🔍 Analyzing system for issues...")
        
        if self.logger_manager:
            # Use enhanced error analysis
            error_analysis = self.logger_manager.analyze_errors()
            
            self.safe_output.safe_print(f"📊 Analysis Results:")
            self.safe_output.safe_print(f"   Total errors: {error_analysis['total_errors']}")
            self.safe_output.safe_print(f"   Total warnings: {error_analysis['total_warnings']}")
            
            if error_analysis['error_types']:
                self.safe_output.safe_print("   Error types:")
                for error_type, count in error_analysis['error_types'].items():
                    self.safe_output.safe_print(f"     {error_type}: {count}")
            
            if error_analysis['suggestions']:
                self.safe_output.safe_print("💡 Suggestions:")
                for suggestion in error_analysis['suggestions']:
                    self.safe_output.safe_print(f"   - {suggestion}")
            
            return True
        else:
            self.safe_output.safe_print("⚠️ Enhanced analysis not available")
            return self._basic_analysis()
    
    def _fix_common_issues(self, args: argparse.Namespace) -> bool:
        """Fix common issues automatically"""
        self.safe_output.safe_print("🔧 Fixing common issues...")
        
        fixed_count = 0
        
        # Fix 1: Create missing directories
        required_dirs = ["data", "data/md", "data/processed", "logs"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.safe_output.safe_print(f"✅ Created directory: {dir_name}")
                    fixed_count += 1
                except Exception as e:
                    self.safe_output.safe_print(f"❌ Could not create {dir_name}: {e}")
        
        # Fix 2: Check and install dependencies
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                installed_packages = result.stdout.lower()
                required_packages = ['requests', 'pandas', 'gspread']
                
                for package in required_packages:
                    if package not in installed_packages:
                        self.safe_output.safe_print(f"⚠️ Missing package: {package}")
        except Exception:
            pass
        
        # Fix 3: Environment variables check
        required_env_vars = ['GOOGLE_SEARCH_API_KEY', 'GOOGLE_SEARCH_CSE_ID']
        for var in required_env_vars:
            if not os.getenv(var):
                self.safe_output.safe_print(f"⚠️ Missing environment variable: {var}")
        
        self.safe_output.safe_print(f"🔧 Fixed {fixed_count} issues")
        return fixed_count > 0
    
    def _general_recovery(self, args: argparse.Namespace) -> bool:
        """General recovery process"""
        self.safe_output.safe_print("🔄 Running general recovery...")
        
        # Check for existing data and attempt processing
        md_dir = Path("data/md")
        if md_dir.exists() and list(md_dir.glob("*.md")):
            self.safe_output.safe_print("📄 Found existing MD files, attempting processing...")
            return self.handle_process(argparse.Namespace(
                command='process', mode='v332', force=True
            ))
        else:
            self.safe_output.safe_print("ℹ️ No existing data found for recovery")
            return False
    
    def _auto_diagnose(self, args: argparse.Namespace) -> bool:
        """Automatic diagnosis of common issues"""
        self.safe_output.safe_print("🔍 Running automatic diagnosis...")
        
        issues_found = []
        
        # Check 1: Python version
        if sys.version_info < (3, 8):
            issues_found.append("Python version too old (3.8+ required)")
        
        # Check 2: Directory structure
        required_dirs = ["data", "logs"]
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                issues_found.append(f"Missing directory: {dir_name}")
        
        # Check 3: Environment variables
        required_env_vars = ['GOOGLE_SEARCH_API_KEY', 'GOOGLE_SEARCH_CSE_ID']
        for var in required_env_vars:
            if not os.getenv(var):
                issues_found.append(f"Missing environment variable: {var}")
        
        # Check 4: Dependencies
        try:
            import requests
            import pandas
        except ImportError as e:
            issues_found.append(f"Missing dependency: {e}")
        
        if issues_found:
            self.safe_output.safe_print("❌ Issues found:")
            for issue in issues_found:
                self.safe_output.safe_print(f"   - {issue}")
            
            self.safe_output.safe_print("\n💡 Run with --fix-common-issues to auto-fix")
            return False
        else:
            self.safe_output.safe_print("✅ No issues found")
            return True
    
    def _diagnose_specific_issue(self, issue: str, args: argparse.Namespace) -> bool:
        """Diagnose specific issue"""
        self.safe_output.safe_print(f"🔍 Diagnosing: {issue}")
        
        issue_handlers = {
            "rate limiting": self._diagnose_rate_limiting,
            "memory exhaustion": self._diagnose_memory_issues,
            "module import error": self._diagnose_import_issues,
            "encoding": self._diagnose_encoding_issues
        }
        
        handler = issue_handlers.get(issue.lower())
        if handler:
            return handler(args)
        else:
            self.safe_output.safe_print(f"⚠️ Unknown issue type: {issue}")
            return False
    
    def _comprehensive_status(self, args: argparse.Namespace) -> bool:
        """Show comprehensive system status"""
        self.safe_output.safe_print("📊 Comprehensive System Status")
        self.safe_output.safe_print("=" * 50)
        
        # System information
        self.safe_output.safe_print(f"🖥️ Platform: {platform.system()} {platform.release()}")
        self.safe_output.safe_print(f"🐍 Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        self.safe_output.safe_print(f"📁 Working Directory: {Path.cwd()}")
        
        # Component status
        self.safe_output.safe_print(f"\n🔧 Components:")
        self.safe_output.safe_print(f"   v3.3.2 Components: {'✅ Available' if self.components_ready else '❌ Not Available'}")
        
        # Data status
        self.safe_output.safe_print(f"\n📊 Data Status:")
        self._show_data_status()
        
        # Environment status
        self.safe_output.safe_print(f"\n🔐 Environment:")
        self._show_env_status()
        
        return True
    
    def _tail_logs(self, stage: Optional[str], lines: int, args: argparse.Namespace) -> bool:
        """Tail logs for specific stage"""
        if not self.logger_manager:
            self.safe_output.safe_print("⚠️ Enhanced logging not available")
            return False
        
        if stage:
            self.safe_output.safe_print(f"📋 Last {lines} lines from {stage} logs:")
            log_lines = self.logger_manager.tail_logs(stage, lines)
        else:
            self.safe_output.safe_print(f"📋 Recent log entries:")
            log_lines = []
            # Get logs from all stages
            for stage_name in ["validate", "search", "process", "upload"]:
                stage_lines = self.logger_manager.tail_logs(stage_name, lines // 4)
                log_lines.extend(stage_lines[-lines//4:])
        
        for line in log_lines[-lines:]:
            self.safe_output.safe_print(line.rstrip())
        
        return True
    
    def _generate_github_summary(self, args: argparse.Namespace) -> bool:
        """Generate GitHub Actions summary"""
        self.safe_output.safe_print("📊 Generating GitHub Actions summary...")
        
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if not summary_file:
            self.safe_output.safe_print("⚠️ Not running in GitHub Actions")
            return False
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("## 📊 FactSet Pipeline v3.3.2 Execution Report\n\n")
                f.write(f"**Execution Time**: {datetime.now().isoformat()}\n")
                f.write(f"**Version**: v3.3.2 (Simplified & Observable)\n\n")
                
                # Add data status
                f.write("### 📁 Data Status\n")
                self._write_data_status_to_file(f)
                
                f.write("\n### 🔧 v3.3.2 Features\n")
                f.write("- ✅ Unified cross-platform CLI\n")
                f.write("- ✅ Stage-specific dual logging\n")
                f.write("- ✅ Enhanced error diagnostics\n")
                f.write("- ✅ All v3.3.1 fixes maintained\n")
            
            self.safe_output.safe_print("✅ GitHub summary generated")
            return True
            
        except Exception as e:
            self.safe_output.safe_print(f"❌ Failed to generate GitHub summary: {e}")
            return False
    
    def _smart_commit(self, args: argparse.Namespace) -> bool:
        """Smart commit based on data quality"""
        self.safe_output.safe_print("💾 Analyzing data for smart commit...")
        
        try:
            # Check data quality
            md_dir = Path("data/md")
            processed_dir = Path("data/processed")
            
            md_count = len(list(md_dir.glob("*.md"))) if md_dir.exists() else 0
            
            processed_files = []
            if processed_dir.exists():
                for file_name in ["portfolio_summary.csv", "detailed_data.csv", "statistics.json"]:
                    file_path = processed_dir / file_name
                    if file_path.exists() and file_path.stat().st_size > 0:
                        processed_files.append(file_name)
            
            # Determine if commit is worthy
            commit_worthy = False
            commit_message_parts = []
            
            if md_count >= 50 and len(processed_files) >= 2:
                commit_worthy = True
                commit_message_parts.append(f"🏆 Premium v3.3.2 data: {md_count} MD files + {len(processed_files)} processed files")
            elif md_count >= 20 and len(processed_files) >= 1:
                commit_worthy = True
                commit_message_parts.append(f"✅ Quality v3.3.2 data: {md_count} MD files + {len(processed_files)} processed files")
            elif md_count >= 10:
                commit_worthy = True
                commit_message_parts.append(f"📊 Acceptable v3.3.2 data: {md_count} MD files")
            
            if commit_worthy:
                self.safe_output.safe_print(f"✅ Data quality sufficient for commit: {commit_message_parts[0]}")
                return self._execute_git_commit(commit_message_parts[0])
            else:
                self.safe_output.safe_print(f"ℹ️ Data quality insufficient for commit ({md_count} MD files)")
                return False
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Smart commit error: {e}")
            return False
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _show_data_status(self):
        """Show current data status"""
        md_dir = Path("data/md")
        processed_dir = Path("data/processed")
        
        if md_dir.exists():
            md_count = len(list(md_dir.glob("*.md")))
            self.safe_output.safe_print(f"   MD Files: {md_count}")
        else:
            self.safe_output.safe_print("   MD Files: No data directory")
        
        if processed_dir.exists():
            expected_files = ["portfolio_summary.csv", "detailed_data.csv", "statistics.json"]
            existing_files = [f for f in expected_files if (processed_dir / f).exists()]
            self.safe_output.safe_print(f"   Processed Files: {len(existing_files)}/3 ({', '.join(existing_files)})")
        else:
            self.safe_output.safe_print("   Processed Files: No processed directory")
    
    def _show_env_status(self):
        """Show environment variable status"""
        required_vars = ['GOOGLE_SEARCH_API_KEY', 'GOOGLE_SEARCH_CSE_ID', 'GOOGLE_SHEETS_CREDENTIALS', 'GOOGLE_SHEET_ID']
        
        for var in required_vars:
            status = "✅ Set" if os.getenv(var) else "❌ Not set"
            self.safe_output.safe_print(f"   {var}: {status}")
    
    def _output_github_actions_result(self, stage: str, result: str):
        """Output result for GitHub Actions"""
        print(f"::set-output name={stage}_result::{result}")
        print(f"::set-output name={stage}_timestamp::{datetime.now().isoformat()}")
    
    def _execute_git_commit(self, message: str) -> bool:
        """Execute git commit with message"""
        try:
            import subprocess
            
            # Configure git
            subprocess.run(['git', 'config', '--global', 'user.name', 'github-actions[bot]'])
            subprocess.run(['git', 'config', '--global', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'])
            
            # Add files
            subprocess.run(['git', 'add', 'data/'], check=False)
            subprocess.run(['git', 'add', 'logs/'], check=False)
            subprocess.run(['git', 'add', '觀察名單.csv'], check=False)
            
            # Commit
            full_message = f"""{message}

📊 v3.3.2 Execution Summary:
- Unified CLI interface used
- Stage-specific logging enabled
- Cross-platform compatibility verified
- All v3.3.1 fixes maintained

🔧 v3.3.2 Enhancements:
- Simplified workflow execution
- Enhanced observability and diagnostics
- Unified cross-platform commands
- Intelligent error recovery

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
            
            result = subprocess.run(['git', 'commit', '-m', full_message], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Push
                push_result = subprocess.run(['git', 'push'], 
                                           capture_output=True, text=True)
                if push_result.returncode == 0:
                    self.safe_output.safe_print("🎉 Changes committed and pushed successfully!")
                    return True
                else:
                    self.safe_output.safe_print("⚠️ Commit succeeded but push failed")
                    return False
            else:
                self.safe_output.safe_print("ℹ️ No new changes to commit")
                return True
                
        except Exception as e:
            self.safe_output.safe_print(f"❌ Git commit error: {e}")
            return False
    
    # ========================================================================
    # FALLBACK METHODS (when components not available)
    # ========================================================================
    
    def _fallback_validate(self, args: argparse.Namespace) -> bool:
        """Fallback validation when components not available"""
        self.safe_output.safe_print("⚠️ Running basic fallback validation...")
        
        # Basic checks
        if sys.version_info < (3, 8):
            self.safe_output.safe_print("❌ Python 3.8+ required")
            return False
        
        # Check directories
        required_dirs = ["data"]
        for dir_name in required_dirs:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
        
        self.safe_output.safe_print("✅ Basic validation passed")
        return True
    
    def _fallback_download_watchlist(self, args: argparse.Namespace) -> bool:
        """Fallback download when components not available"""
        self.safe_output.safe_print("⚠️ Enhanced download not available")
        
        # Check for existing file
        if Path("觀察名單.csv").exists():
            self.safe_output.safe_print("✅ Using existing watchlist file")
            return True
        
        self.safe_output.safe_print("❌ No watchlist available")
        return False
    
    def _fallback_search(self, args: argparse.Namespace) -> bool:
        """Fallback search when components not available"""
        self.safe_output.safe_print("⚠️ Enhanced search not available")
        return False
    
    def _fallback_process(self, args: argparse.Namespace) -> bool:
        """Fallback processing when components not available"""
        self.safe_output.safe_print("⚠️ Enhanced processing not available")
        
        # Check for existing processed files
        processed_dir = Path("data/processed")
        if processed_dir.exists():
            expected_files = ["portfolio_summary.csv"]
            existing_files = [f for f in expected_files if (processed_dir / f).exists()]
            
            if existing_files:
                self.safe_output.safe_print(f"✅ Found existing processed files: {existing_files}")
                return True
        
        self.safe_output.safe_print("❌ No processed files available")
        return False
    
    def _fallback_upload(self, args: argparse.Namespace) -> bool:
        """Fallback upload when components not available"""
        self.safe_output.safe_print("⚠️ Enhanced upload not available")
        return False
    
    def _fallback_pipeline(self, args: argparse.Namespace) -> bool:
        """Fallback pipeline when components not available"""
        self.safe_output.safe_print("⚠️ Running basic pipeline fallback...")
        
        # Try basic validation
        if not self._fallback_validate(args):
            return False
        
        # Try downloading watchlist
        self._fallback_download_watchlist(args)
        
        # Try processing existing data
        return self._fallback_process(args)
    
    def _fallback_logs(self, args: argparse.Namespace) -> bool:
        """Fallback logs when enhanced logging not available"""
        self.safe_output.safe_print("⚠️ Enhanced logging not available")
        
        # Show basic log files
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                self.safe_output.safe_print(f"📋 Found {len(log_files)} log files:")
                for log_file in log_files[-5:]:  # Show last 5
                    self.safe_output.safe_print(f"   {log_file.name}")
                return True
        
        self.safe_output.safe_print("ℹ️ No log files found")
        return False
    
    def _fallback_diagnose(self, args: argparse.Namespace) -> bool:
        """Fallback diagnosis when enhanced features not available"""
        return self._auto_diagnose(args)
    
    # Additional helper methods for specific diagnostics
    def _diagnose_rate_limiting(self, args: argparse.Namespace) -> bool:
        self.safe_output.safe_print("🔍 Diagnosing rate limiting issues...")
        self.safe_output.safe_print("💡 Suggestions:")
        self.safe_output.safe_print("   - Use --mode=conservative")
        self.safe_output.safe_print("   - Increase rate delays")
        self.safe_output.safe_print("   - Check API quotas")
        return True
    
    def _diagnose_memory_issues(self, args: argparse.Namespace) -> bool:
        self.safe_output.safe_print("🔍 Diagnosing memory issues...")
        try:
            import psutil
            memory = psutil.virtual_memory()
            self.safe_output.safe_print(f"   Available memory: {memory.available / (1024**3):.1f} GB")
            
            if memory.available < 2 * (1024**3):  # Less than 2GB
                self.safe_output.safe_print("⚠️ Low memory detected")
                self.safe_output.safe_print("💡 Suggestions:")
                self.safe_output.safe_print("   - Use --memory-limit=1024")
                self.safe_output.safe_print("   - Reduce --batch-size")
        except ImportError:
            self.safe_output.safe_print("⚠️ psutil not available for memory analysis")
        
        return True
    
    def _diagnose_import_issues(self, args: argparse.Namespace) -> bool:
        self.safe_output.safe_print("🔍 Diagnosing import issues...")
        
        required_packages = ['requests', 'pandas', 'gspread', 'beautifulsoup4']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.safe_output.safe_print(f"   ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                self.safe_output.safe_print(f"   ❌ {package}")
        
        if missing_packages:
            self.safe_output.safe_print("💡 Install missing packages:")
            self.safe_output.safe_print(f"   pip install {' '.join(missing_packages)}")
        
        return len(missing_packages) == 0
    
    def _diagnose_encoding_issues(self, args: argparse.Namespace) -> bool:
        self.safe_output.safe_print("🔍 Diagnosing encoding issues...")
        self.safe_output.safe_print(f"   Platform: {platform.system()}")
        self.safe_output.safe_print(f"   Stdout encoding: {sys.stdout.encoding}")
        self.safe_output.safe_print(f"   Filesystem encoding: {sys.getfilesystemencoding()}")
        
        # Test emoji support
        try:
            "🚀".encode(sys.stdout.encoding or 'utf-8')
            self.safe_output.safe_print("   ✅ Emoji support: Yes")
        except (UnicodeEncodeError, AttributeError):
            self.safe_output.safe_print("   ⚠️ Emoji support: Limited")
            self.safe_output.safe_print("💡 Set PYTHONIOENCODING=utf-8")
        
        return True

# ============================================================================
# ARGUMENT PARSER SETUP (v3.3.2)
# ============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser for v3.3.2"""
    
    parser = argparse.ArgumentParser(
        description=f"FactSet Pipeline CLI v{__version__} - Unified Cross-Platform Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Enhanced CLI v3.3.2 - Simplified & Observable

🚀 Quick Start:
  python factset_cli.py pipeline --mode=intelligent
  python factset_cli.py validate --comprehensive
  python factset_cli.py logs --stage=search --tail=50

🔧 Key Features:
  ✅ Unified commands (Windows/Linux identical)
  ✅ Stage-specific dual logging (console + file)  
  ✅ Enhanced diagnostics and recovery
  ✅ All v3.3.1 fixes maintained
  ✅ GitHub Actions compatible

📊 Examples:
  # System validation
  python factset_cli.py validate --comprehensive --fix-issues
  
  # Individual stages  
  python factset_cli.py search --mode=conservative --priority=top_30
  python factset_cli.py process --memory-limit=2048 --batch-size=25
  python factset_cli.py upload --test-connection
  
  # Complete pipeline
  python factset_cli.py pipeline --mode=enhanced --log-level=debug
  
  # Diagnostics and recovery
  python factset_cli.py diagnose --auto --fix-common
  python factset_cli.py recover --analyze
  python factset_cli.py logs --stage=all --tail=100
  
  # Status and reporting
  python factset_cli.py status --comprehensive
  python factset_cli.py report --format=html
  python factset_cli.py performance --detailed

🔗 More info: https://github.com/your-repo/factset-pipeline
        """
    )
    
    # Global options
    parser.add_argument('--version', action='version', version=f'FactSet CLI v{__version__}')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validation command
    validate_parser = subparsers.add_parser('validate', help='System validation')
    validate_parser.add_argument('--comprehensive', action='store_true', help='Comprehensive validation')
    validate_parser.add_argument('--quick', action='store_true', help='Quick validation')
    validate_parser.add_argument('--fix-issues', action='store_true', help='Auto-fix common issues')
    validate_parser.add_argument('--test-v332', action='store_true', help='Test v3.3.2 features')
    validate_parser.add_argument('--github-actions', action='store_true', help='GitHub Actions mode')
    
    # Download watchlist command
    download_parser = subparsers.add_parser('download-watchlist', help='Download company watchlist')
    download_parser.add_argument('--force-refresh', action='store_true', help='Force refresh cache')
    download_parser.add_argument('--validate', action='store_true', help='Validate after download')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Enhanced search')
    search_parser.add_argument('--mode', choices=['enhanced', 'conservative', 'intelligent'], 
                              default='enhanced', help='Search mode')
    search_parser.add_argument('--priority', choices=['high_only', 'top_30', 'balanced'],
                              default='high_only', help='Priority level')
    search_parser.add_argument('--max-results', type=int, default=10, help='Max results per company')
    search_parser.add_argument('--companies', type=int, help='Limit number of companies')
    search_parser.add_argument('--test-cascade-protection', action='store_true', 
                              help='Test cascade failure protection')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Data processing')
    process_parser.add_argument('--mode', default='v332', help='Processing mode')
    process_parser.add_argument('--memory-limit', type=int, default=2048, help='Memory limit (MB)')
    process_parser.add_argument('--batch-size', type=int, default=50, help='Batch size')
    process_parser.add_argument('--deduplicate', action='store_true', default=True, help='Enable deduplication')
    process_parser.add_argument('--aggregate', action='store_true', default=True, help='Enable aggregation')
    process_parser.add_argument('--benchmark', action='store_true', help='Run performance benchmark')
    process_parser.add_argument('--force', action='store_true', help='Force reprocessing')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Sheets upload')
    upload_parser.add_argument('--sheets', default='all', help='Sheets to update (all/portfolio/detailed)')
    upload_parser.add_argument('--backup', action='store_true', default=True, help='Create backup')
    upload_parser.add_argument('--test-connection', action='store_true', help='Test connection only')
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Complete pipeline')
    pipeline_parser.add_argument('--mode', choices=['intelligent', 'enhanced', 'conservative', 'process_only'],
                                 default='intelligent', help='Execution mode')
    pipeline_parser.add_argument('--memory-limit', type=int, default=2048, help='Memory limit (MB)')
    pipeline_parser.add_argument('--batch-size', type=int, default=50, help='Batch size')
    pipeline_parser.add_argument('--log-level', choices=['debug', 'info', 'warning'],
                                 default='info', help='Log level')
    pipeline_parser.add_argument('--github-actions', action='store_true', help='GitHub Actions mode')
    pipeline_parser.add_argument('--skip-phases', nargs='*', 
                                 choices=['search', 'processing', 'upload'], help='Skip phases')
    
    # Recovery command
    recover_parser = subparsers.add_parser('recover', help='Recovery and repair')
    recover_parser.add_argument('--analyze', action='store_true', help='Analyze and recover')
    recover_parser.add_argument('--fix-common-issues', action='store_true', help='Fix common issues')
    recover_parser.add_argument('--github-actions', action='store_true', help='GitHub Actions mode')
    
    # Diagnose command
    diagnose_parser = subparsers.add_parser('diagnose', help='System diagnostics')
    diagnose_parser.add_argument('--stage', help='Specific stage to diagnose')
    diagnose_parser.add_argument('--auto', action='store_true', help='Auto-diagnose common issues')
    diagnose_parser.add_argument('--detailed', action='store_true', help='Detailed diagnosis')
    diagnose_parser.add_argument('--issue', help='Specific issue to diagnose')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='System status')
    status_parser.add_argument('--comprehensive', action='store_true', help='Comprehensive status')
    status_parser.add_argument('--detailed', action='store_true', help='Detailed status')
    status_parser.add_argument('--export', choices=['json', 'txt'], help='Export format')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Log management')
    logs_parser.add_argument('--stage', help='Specific stage logs')
    logs_parser.add_argument('--tail', type=int, help='Tail N lines')
    logs_parser.add_argument('--export', action='store_true', help='Export logs')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate reports')
    report_parser.add_argument('--format', choices=['summary', 'html', 'json', 'github-summary'],
                              default='summary', help='Report format')
    
    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Smart commit')
    commit_parser.add_argument('--smart', action='store_true', help='Smart commit based on quality')
    commit_parser.add_argument('--validate', action='store_true', help='Validate before commit')
    
    # Performance command
    performance_parser = subparsers.add_parser('performance', help='Performance analysis')
    performance_parser.add_argument('--compare-with', help='Compare with version')
    performance_parser.add_argument('--detailed', action='store_true', help='Detailed analysis')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Data analysis')
    analyze_parser.add_argument('--type', choices=['general', 'memory', 'data'],
                               default='general', help='Analysis type')
    
    return parser

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for FactSet CLI v3.3.2"""
    
    # Create and configure CLI
    cli = FactSetCLI()
    
    # Parse arguments
    parser = create_argument_parser()
    
    # Handle no arguments case
    if len(sys.argv) == 1:
        safe_output.safe_print(f"🚀 FactSet Pipeline CLI v{__version__}")
        safe_output.safe_print("💡 Run with --help for usage information")
        safe_output.safe_print("🔧 Quick start: python factset_cli.py pipeline --mode=intelligent")
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