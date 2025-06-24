"""
enhanced_logger.py - Enhanced Logging Management System (v3.3.2)

Version: 3.3.2
Date: 2025-06-24
Author: FactSet Pipeline - v3.3.2 Simplified & Observable

v3.3.2 ENHANCEMENTS:
- ✅ Stage-specific dual output logging (console + file)
- ✅ Cross-platform safe console handling
- ✅ Automatic log rotation and cleanup
- ✅ Real-time log analysis and error detection
- ✅ Integration with existing v3.3.1 logging
- ✅ Performance monitoring and metrics
- ✅ Intelligent error recovery suggestions

Description:
    Comprehensive logging management for the Enhanced FactSet Pipeline v3.3.2:
    - Dual output: Concise console + Detailed file logging
    - Stage-specific log files with timestamps
    - Cross-platform encoding and path handling
    - Automatic error analysis and suggestions
    - Integration with v3.3.1 memory management
    - Real-time performance monitoring
    - Log aggregation and reporting
"""

import os
import sys
import logging
import logging.handlers
import platform
import traceback
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TextIO
from contextlib import contextmanager
import threading
import queue
import time

# Version Information - v3.3.2
__version__ = "3.3.2"
__date__ = "2025-06-24"
__author__ = "FactSet Pipeline - v3.3.2 Simplified & Observable"

# ============================================================================
# CROSS-PLATFORM SAFE CONSOLE HANDLER (v3.3.2)
# ============================================================================

class SafeConsoleHandler(logging.StreamHandler):
    """Cross-platform safe console handler with encoding protection"""
    
    def __init__(self, stream=None):
        super().__init__(stream)
        self.encoding = self._detect_safe_encoding()
        self._setup_stream()
    
    def _detect_safe_encoding(self) -> str:
        """Detect safest encoding for the platform"""
        if sys.platform == "win32":
            # Windows: Try UTF-8, fall back to cp1252
            try:
                "🚀".encode(sys.stdout.encoding or 'utf-8')
                return sys.stdout.encoding or 'utf-8'
            except (UnicodeEncodeError, AttributeError):
                return 'cp1252'
        else:
            # Linux/macOS: UTF-8 should work
            return sys.stdout.encoding or 'utf-8'
    
    def _setup_stream(self):
        """Setup stream with proper encoding"""
        if hasattr(self.stream, 'reconfigure') and sys.platform != "win32":
            try:
                self.stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
    
    def emit(self, record):
        """Safely emit log record with encoding protection"""
        try:
            msg = self.format(record)
            
            # Cross-platform safe encoding
            if sys.platform == "win32":
                # Windows: Replace problematic characters
                try:
                    msg.encode(self.encoding)
                except UnicodeEncodeError:
                    msg = msg.encode('ascii', errors='replace').decode('ascii')
            
            # Write with newline
            self.stream.write(msg + '\n')
            self.flush()
            
        except Exception as e:
            # Fallback for any encoding issues
            try:
                safe_msg = f"[LOG ERROR] {record.levelname}: {record.getMessage()}"
                self.stream.write(safe_msg + '\n')
                self.flush()
            except Exception:
                # Ultimate fallback
                pass
    
    def flush(self):
        """Safe flush with error handling"""
        try:
            if hasattr(self.stream, 'flush'):
                self.stream.flush()
        except Exception:
            pass

# ============================================================================
# ENHANCED LOG FORMATTERS (v3.3.2)
# ============================================================================

class ConsoleFormatter(logging.Formatter):
    """Concise console formatter with emoji and colors"""
    
    def __init__(self):
        super().__init__()
        self.use_emoji = self._test_emoji_support()
        self._setup_colors()
    
    def _test_emoji_support(self) -> bool:
        """Test if console supports emoji"""
        if sys.platform == "win32":
            try:
                "🚀".encode(sys.stdout.encoding or 'utf-8')
                return True
            except (UnicodeEncodeError, AttributeError):
                return False
        return True
    
    def _setup_colors(self):
        """Setup color codes for different platforms"""
        if sys.platform == "win32":
            # Windows: Basic color support
            self.colors = {
                'INFO': '',
                'WARNING': '',
                'ERROR': '',
                'DEBUG': '',
                'RESET': ''
            }
        else:
            # Linux/macOS: ANSI colors
            self.colors = {
                'INFO': '\033[94m',      # Blue
                'WARNING': '\033[93m',   # Yellow  
                'ERROR': '\033[91m',     # Red
                'DEBUG': '\033[90m',     # Gray
                'RESET': '\033[0m'       # Reset
            }
    
    def format(self, record):
        """Format console output with emoji and stage info"""
        # Get stage name from logger
        stage_name = self._extract_stage_name(record.name)
        
        # Format emoji and level
        if self.use_emoji:
            emoji_map = {
                'INFO': '✅',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'DEBUG': '🔍'
            }
            emoji = emoji_map.get(record.levelname, '📄')
        else:
            emoji = f"[{record.levelname}]"
        
        # Format message
        color = self.colors.get(record.levelname, '')
        reset = self.colors.get('RESET', '')
        
        if stage_name:
            formatted = f"{emoji} {color}[{stage_name.upper()}]{reset} {record.getMessage()}"
        else:
            formatted = f"{emoji} {color}{record.getMessage()}{reset}"
        
        return formatted
    
    def _extract_stage_name(self, logger_name: str) -> Optional[str]:
        """Extract stage name from logger name"""
        if 'factset_v332.' in logger_name:
            return logger_name.split('factset_v332.')[-1]
        return None

class FileFormatter(logging.Formatter):
    """Detailed file formatter with comprehensive context"""
    
    def __init__(self):
        format_string = (
            '%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)s - '
            '%(funcName)s:%(lineno)d - %(message)s'
        )
        super().__init__(format_string, datefmt='%Y-%m-%d %H:%M:%S')
    
    def format(self, record):
        """Format detailed file output with context"""
        formatted = super().format(record)
        
        # Add exception info if present
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
        
        # Add stack info if available
        if hasattr(record, 'stack_info') and record.stack_info:
            formatted += '\nStack (most recent call last):\n' + record.stack_info
        
        return formatted

# ============================================================================
# STAGE-SPECIFIC LOG MANAGER (v3.3.2)
# ============================================================================

class StageLogManager:
    """Manages stage-specific logging with dual output"""
    
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = Path(base_log_dir)
        self.stage_loggers = {}
        self.log_session = datetime.now().strftime("%Y%m%d")
        self.session_dir = self.base_log_dir / self.log_session
        self.latest_dir = self.base_log_dir / "latest"
        
        # Setup directory structure
        self._setup_directories()
        
        # Thread-safe logger creation
        self._lock = threading.Lock()
    
    def _setup_directories(self):
        """Setup enhanced directory structure"""
        directories = [
            self.session_dir,
            self.latest_dir,
            self.base_log_dir / "reports",
            self.base_log_dir / "archives"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_stage_logger(self, stage_name: str) -> logging.Logger:
        """Get or create stage-specific logger with dual output"""
        with self._lock:
            if stage_name not in self.stage_loggers:
                self.stage_loggers[stage_name] = self._create_stage_logger(stage_name)
            return self.stage_loggers[stage_name]
    
    def _create_stage_logger(self, stage_name: str) -> logging.Logger:
        """Create stage-specific logger with dual output"""
        logger_name = f"factset_v332.{stage_name}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.propagate = False
        
        # File handler - detailed logging
        timestamp = datetime.now().strftime("%H%M%S")
        log_file = self.session_dir / f"{stage_name}_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())
        
        # Console handler - concise logging
        console_handler = SafeConsoleHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ConsoleFormatter())
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Create latest symlink (Unix) or copy (Windows)
        self._create_latest_link(stage_name, log_file)
        
        # Log creation
        logger.info(f"v3.3.2 stage logger initialized: {stage_name}")
        logger.debug(f"Log file: {log_file}")
        
        return logger
    
    def _create_latest_link(self, stage_name: str, log_file: Path):
        """Create latest log link/copy for easy access"""
        latest_file = self.latest_dir / f"{stage_name}.log"
        
        try:
            if latest_file.exists():
                latest_file.unlink()
            
            if sys.platform == "win32":
                # Windows: Copy file
                import shutil
                shutil.copy2(log_file, latest_file)
            else:
                # Unix: Create symlink
                latest_file.symlink_to(log_file.resolve())
                
        except Exception as e:
            # If linking fails, just continue
            pass
    
    def get_log_files(self, stage_name: Optional[str] = None) -> List[Path]:
        """Get log files for a stage or all stages"""
        if stage_name:
            pattern = f"{stage_name}_*.log"
        else:
            pattern = "*.log"
        
        return list(self.session_dir.glob(pattern))
    
    def tail_logs(self, stage_name: str, lines: int = 50) -> List[str]:
        """Get last N lines from stage logs"""
        log_files = self.get_log_files(stage_name)
        if not log_files:
            return []
        
        # Get most recent log file
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception:
            return []
    
    def analyze_errors(self, stage_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze errors in log files"""
        log_files = self.get_log_files(stage_name)
        
        error_analysis = {
            "total_errors": 0,
            "total_warnings": 0,
            "error_types": {},
            "recent_errors": [],
            "suggestions": []
        }
        
        error_patterns = {
            "rate_limiting": [r"429", r"rate limit", r"too many requests"],
            "memory_error": [r"memory", r"out of memory", r"memoryerror"],
            "network_error": [r"connection", r"timeout", r"network"],
            "import_error": [r"importerror", r"modulenotfounderror"],
            "encoding_error": [r"unicode", r"encoding", r"decode"]
        }
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # Count errors and warnings
                error_analysis["total_errors"] += content.count("[error]")
                error_analysis["total_warnings"] += content.count("[warning]")
                
                # Categorize errors
                for error_type, patterns in error_patterns.items():
                    count = sum(len(re.findall(pattern, content)) for pattern in patterns)
                    if count > 0:
                        error_analysis["error_types"][error_type] = count
                
            except Exception:
                continue
        
        # Generate suggestions
        error_analysis["suggestions"] = self._generate_error_suggestions(error_analysis)
        
        return error_analysis
    
    def _generate_error_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on error analysis"""
        suggestions = []
        
        error_types = analysis.get("error_types", {})
        
        if "rate_limiting" in error_types:
            suggestions.append("Consider using --mode=conservative or increasing rate_limit_delay")
        
        if "memory_error" in error_types:
            suggestions.append("Try reducing --memory-limit or --batch-size parameters")
        
        if "network_error" in error_types:
            suggestions.append("Check internet connection and retry with --max-retries")
        
        if "import_error" in error_types:
            suggestions.append("Run: pip install -r requirements.txt to fix missing dependencies")
        
        if "encoding_error" in error_types:
            suggestions.append("Set PYTHONIOENCODING=utf-8 environment variable")
        
        if not error_types and analysis["total_errors"] > 0:
            suggestions.append("Run with --log-level=debug for more detailed error information")
        
        return suggestions

# ============================================================================
# PERFORMANCE MONITORING INTEGRATION (v3.3.2)
# ============================================================================

class PerformanceLogger:
    """Performance monitoring with logging integration"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
        self.performance_data = []
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        start_time = time.time()
        self.start_times[operation_name] = start_time
        
        try:
            self.logger.debug(f"Starting operation: {operation_name}")
            yield
            
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            self.performance_data.append({
                "operation": operation_name,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"Completed {operation_name} in {duration:.2f}s")
            
            if duration > 30:  # Slow operation warning
                self.logger.warning(f"Slow operation detected: {operation_name} took {duration:.2f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.performance_data:
            return {}
        
        total_time = sum(item["duration"] for item in self.performance_data)
        slowest = max(self.performance_data, key=lambda x: x["duration"])
        
        return {
            "total_operations": len(self.performance_data),
            "total_time": total_time,
            "average_time": total_time / len(self.performance_data),
            "slowest_operation": slowest,
            "operations": self.performance_data
        }

# ============================================================================
# ENHANCED LOGGER MANAGER (v3.3.2 MAIN CLASS)
# ============================================================================

class EnhancedLoggerManager:
    """Main enhanced logger manager for v3.3.2"""
    
    def __init__(self, base_log_dir: str = "logs", enable_performance: bool = True):
        self.stage_manager = StageLogManager(base_log_dir)
        self.enable_performance = enable_performance
        self.performance_loggers = {}
        
        # Setup main logger
        self.main_logger = self._setup_main_logger()
        
        # Cleanup old logs
        self._cleanup_old_logs()
    
    def _setup_main_logger(self) -> logging.Logger:
        """Setup main application logger"""
        logger = logging.getLogger("factset_v332.main")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.propagate = False
        
        # Console handler only for main logger
        console_handler = SafeConsoleHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)
        
        return logger
    
    def get_stage_logger(self, stage_name: str) -> logging.Logger:
        """Get stage-specific logger"""
        return self.stage_manager.get_stage_logger(stage_name)
    
    def get_performance_logger(self, stage_name: str) -> PerformanceLogger:
        """Get performance logger for stage"""
        if not self.enable_performance:
            return None
        
        if stage_name not in self.performance_loggers:
            stage_logger = self.get_stage_logger(stage_name)
            self.performance_loggers[stage_name] = PerformanceLogger(stage_logger)
        
        return self.performance_loggers[stage_name]
    
    def tail_logs(self, stage_name: str, lines: int = 50) -> List[str]:
        """Tail logs for a specific stage"""
        return self.stage_manager.tail_logs(stage_name, lines)
    
    def analyze_errors(self, stage_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze errors across stages"""
        return self.stage_manager.analyze_errors(stage_name)
    
    def generate_session_report(self) -> Dict[str, Any]:
        """Generate comprehensive session report"""
        report = {
            "session_id": self.stage_manager.log_session,
            "generated_at": datetime.now().isoformat(),
            "version": __version__,
            "log_files": [],
            "error_analysis": {},
            "performance_summary": {}
        }
        
        # Collect log files
        for log_file in self.stage_manager.session_dir.glob("*.log"):
            report["log_files"].append({
                "name": log_file.name,
                "size": log_file.stat().st_size,
                "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
            })
        
        # Error analysis
        report["error_analysis"] = self.analyze_errors()
        
        # Performance summary
        if self.enable_performance:
            perf_summary = {}
            for stage_name, perf_logger in self.performance_loggers.items():
                perf_summary[stage_name] = perf_logger.get_performance_summary()
            report["performance_summary"] = perf_summary
        
        return report
    
    def _cleanup_old_logs(self, days_to_keep: int = 7):
        """Cleanup old log directories"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for item in self.stage_manager.base_log_dir.iterdir():
                if item.is_dir() and item.name.isdigit() and len(item.name) == 8:
                    try:
                        item_date = datetime.strptime(item.name, "%Y%m%d")
                        if item_date < cutoff_date:
                            # Move to archives instead of deleting
                            archive_dir = self.stage_manager.base_log_dir / "archives" / item.name
                            if not archive_dir.exists():
                                import shutil
                                shutil.move(str(item), str(archive_dir))
                    except (ValueError, OSError):
                        continue
        except Exception:
            # If cleanup fails, just continue
            pass
    
    def export_logs(self, stage_name: Optional[str] = None, 
                   format: str = "txt") -> Optional[Path]:
        """Export logs in specified format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format == "json":
                export_file = self.stage_manager.base_log_dir / "reports" / f"logs_export_{timestamp}.json"
                report = self.generate_session_report()
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                    
            else:  # txt format
                export_file = self.stage_manager.base_log_dir / "reports" / f"logs_export_{timestamp}.txt"
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    f.write(f"FactSet Pipeline v3.3.2 Log Export\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    log_files = self.stage_manager.get_log_files(stage_name)
                    for log_file in log_files:
                        f.write(f"\n--- {log_file.name} ---\n")
                        try:
                            with open(log_file, 'r', encoding='utf-8') as lf:
                                f.write(lf.read())
                        except Exception:
                            f.write("[Error reading log file]\n")
            
            return export_file
            
        except Exception as e:
            self.main_logger.error(f"Failed to export logs: {e}")
            return None

# ============================================================================
# INTEGRATION WITH EXISTING v3.3.1 LOGGING
# ============================================================================

def integrate_with_v331_logging():
    """Integrate v3.3.2 logging with existing v3.3.1 setup"""
    # Redirect existing loggers to v3.3.2 system
    existing_loggers = [
        "factset_pipeline_v331",
        "factset_pipeline_v330",
        "factset_search",
        "data_processor"
    ]
    
    logger_manager = EnhancedLoggerManager()
    
    for logger_name in existing_loggers:
        existing_logger = logging.getLogger(logger_name)
        if existing_logger.handlers:
            # Replace handlers with v3.3.2 system
            existing_logger.handlers.clear()
            
            # Add stage logger handler
            stage_name = logger_name.split('.')[-1] if '.' in logger_name else logger_name
            new_logger = logger_manager.get_stage_logger(stage_name)
            
            for handler in new_logger.handlers:
                existing_logger.addHandler(handler)

# ============================================================================
# MAIN FUNCTIONS AND EXPORTS
# ============================================================================

# Global logger manager instance
_global_logger_manager = None

def get_logger_manager() -> EnhancedLoggerManager:
    """Get global logger manager instance"""
    global _global_logger_manager
    if _global_logger_manager is None:
        _global_logger_manager = EnhancedLoggerManager()
    return _global_logger_manager

def get_stage_logger(stage_name: str) -> logging.Logger:
    """Convenience function to get stage logger"""
    return get_logger_manager().get_stage_logger(stage_name)

def get_performance_logger(stage_name: str) -> PerformanceLogger:
    """Convenience function to get performance logger"""
    return get_logger_manager().get_performance_logger(stage_name)

# Module exports
__all__ = [
    'EnhancedLoggerManager',
    'StageLogManager', 
    'PerformanceLogger',
    'SafeConsoleHandler',
    'ConsoleFormatter',
    'FileFormatter',
    'get_logger_manager',
    'get_stage_logger',
    'get_performance_logger',
    'integrate_with_v331_logging'
]

# Initialize integration on import
if __name__ != "__main__":
    try:
        integrate_with_v331_logging()
    except Exception:
        # If integration fails, continue silently
        pass