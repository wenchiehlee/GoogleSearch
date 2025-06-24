"""
utils.py - Enhanced Shared Utilities Module (v3.3.2)

Version: 3.3.2
Date: 2025-06-24
Author: Google Search FactSet Pipeline - v3.3.2 Simplified & Observable
License: MIT

v3.3.2 ENHANCEMENTS (Added to v3.3.1):
- ✅ Integration with enhanced logging system
- ✅ v3.3.2 stage logger helpers
- ✅ Cross-platform CLI compatibility functions
- ✅ Enhanced performance monitoring integration
- ✅ All v3.3.1 functionality preserved

v3.3.1 FEATURES (Maintained):
- ✅ Enhanced date parsing with multiple fallback strategies
- ✅ Improved file handling with better error recovery
- ✅ Enhanced text processing and validation utilities
- ✅ Better logging setup with safe encoding
- ✅ Data validation helpers for v3.3.1 features
- ✅ Company name matching and validation utilities
- ✅ Quality scoring and assessment functions
- ✅ Enhanced error handling and context management
- ✅ File metadata extraction and analysis
- ✅ Content quality assessment for v3.3.1

Description:
    Comprehensive utility functions for the Enhanced FactSet Pipeline v3.3.2:
    - Enhanced file operations with metadata extraction
    - Advanced date and time parsing with multiple formats
    - Robust text processing and validation
    - Safe logging setup with Windows compatibility
    - Data quality assessment and scoring
    - Company information extraction and validation
    - Error handling with context preservation
    - System diagnostics and performance monitoring
    - v3.3.2 CLI integration helpers

Key Features:
    - Cross-platform compatibility with enhanced Windows support
    - Robust date parsing with Chinese format support
    - Advanced text cleaning and validation
    - Safe emoji handling for different console types
    - Enhanced logging with structured output
    - Data quality scoring algorithms
    - Company name matching with fuzzy logic
    - File integrity checking and metadata extraction
    - v3.3.2 stage logger integration

Dependencies:
    - os, pathlib, re, logging, datetime
    - hashlib, json, platform, sys
    - typing (for type hints)
"""

import os
import re
import json
import logging
import hashlib
import platform
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import traceback

# Version Information - v3.3.2
__version__ = "3.3.2"
__date__ = "2025-06-24"
__author__ = "Google Search FactSet Pipeline - v3.3.2 Simplified & Observable"

# ============================================================================
# v3.3.2 LOGGING INTEGRATION
# ============================================================================

def get_v332_logger(module_name: str):
    """Get v3.3.2 stage logger with fallback to standard logging"""
    try:
        from enhanced_logger import get_stage_logger
        return get_stage_logger(module_name)
    except ImportError:
        # Fallback to standard logging if v3.3.2 components not available
        import logging
        return logging.getLogger(f'factset_v332.{module_name}')

def get_performance_monitor(stage_name: str):
    """Get v3.3.2 performance monitor with fallback"""
    try:
        from enhanced_logger import get_performance_logger
        return get_performance_logger(stage_name)
    except ImportError:
        # Fallback performance monitor
        return FallbackPerformanceMonitor(stage_name)

class FallbackPerformanceMonitor:
    """Fallback performance monitor when v3.3.2 components not available"""
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.start_time = None
    
    def time_operation(self, operation_name: str):
        """Fallback context manager for timing operations"""
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

# ============================================================================
# ENHANCED SYSTEM UTILITIES (v3.3.2 - with logging integration)
# ============================================================================

def is_debug_mode() -> bool:
    """Enhanced debug mode detection with multiple sources"""
    debug_sources = [
        os.getenv("DEBUG", "0"),
        os.getenv("FACTSET_PIPELINE_DEBUG", "0"),
        os.getenv("FACTSET_DEBUG", "0")
    ]
    
    return any(source.lower() in ('1', 'true', 'yes', 'on') for source in debug_sources)

def get_system_info() -> Dict[str, str]:
    """Get comprehensive system information for v3.3.2"""
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "architecture": platform.architecture()[0],
        "machine": platform.machine(),
        "processor": platform.processor(),
        "encoding": sys.stdout.encoding or "unknown",
        "file_system_encoding": sys.getfilesystemencoding(),
        "working_directory": str(Path.cwd()),
        "script_directory": str(Path(__file__).parent),
        "utils_version": __version__,
        "v332_features_available": _check_v332_features()
    }

def _check_v332_features() -> bool:
    """Check if v3.3.2 enhanced features are available"""
    try:
        import enhanced_logger
        import stage_runner
        return True
    except ImportError:
        return False

def setup_safe_logging(log_level: str = "INFO", log_file: Optional[str] = None, 
                      use_v332: bool = True) -> logging.Logger:
    """Setup enhanced safe logging for v3.3.2 with fallback to v3.3.1"""
    
    if use_v332:
        try:
            # Try v3.3.2 enhanced logging
            logger = get_v332_logger("utils")
            logger.info(f"Enhanced v3.3.2 logging setup complete (v{__version__})")
            return logger
        except Exception:
            # Fall back to v3.3.1 logging
            pass
    
    # v3.3.1 fallback logging setup (preserved from original)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"factset_pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Enhanced formatter with safe encoding
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            formatted = super().format(record)
            # Ensure safe encoding for Windows
            if sys.platform == "win32":
                try:
                    formatted.encode(sys.stdout.encoding or 'utf-8')
                except UnicodeEncodeError:
                    # Replace problematic characters
                    formatted = formatted.encode('ascii', errors='replace').decode('ascii')
            return formatted
    
    formatter = SafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Setup logger
    logger = logging.getLogger('factset_pipeline_v332')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    
    # File handler with UTF-8 encoding
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    # Console handler with safe encoding
    console_handler = logging.StreamHandler()
    if sys.platform == "win32":
        # Use a stream that handles encoding safely on Windows
        console_handler.setFormatter(formatter)
    else:
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    logger.info(f"v3.3.1 fallback logging setup complete (v{__version__})")
    return logger

# ============================================================================
# ENHANCED FILE OPERATIONS (v3.3.2 - with integrated logging)
# ============================================================================

def is_file_parsed(md_path: Union[str, Path], logger=None) -> bool:
    """Enhanced check if a Markdown file has been parsed"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    try:
        md_path = Path(md_path)
        parsed_flag = md_path.with_suffix(".parsed")
        
        if parsed_flag.exists():
            # Check if parsed flag is newer than the source file
            if md_path.exists():
                result = parsed_flag.stat().st_mtime >= md_path.stat().st_mtime
                logger.debug(f"File {md_path.name} parsed status: {result}")
                return result
            return True
        logger.debug(f"No parsed flag found for {md_path.name}")
        return False
    except Exception as e:
        if logger:
            logger.warning(f"Error checking parsed status for {md_path}: {e}")
        return False

def mark_parsed_file(md_path: Union[str, Path], metadata: Optional[Dict] = None, logger=None):
    """Enhanced marking of parsed files with metadata"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    try:
        md_path = Path(md_path)
        parsed_flag = md_path.with_suffix(".parsed")
        
        # Create flag with metadata
        flag_data = {
            "parsed_at": datetime.now().isoformat(),
            "source_file": str(md_path),
            "source_size": md_path.stat().st_size if md_path.exists() else 0,
            "utils_version": __version__,
            "v332_enhanced": True
        }
        
        if metadata:
            flag_data.update(metadata)
        
        with open(parsed_flag, 'w', encoding='utf-8') as f:
            json.dump(flag_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Marked file as parsed: {md_path.name}")
            
    except Exception as e:
        if logger and is_debug_mode():
            logger.warning(f"Could not mark file as parsed: {e}")

def read_md_file_enhanced(md_path: Union[str, Path], logger=None) -> Tuple[str, Dict]:
    """Enhanced MD file reading with metadata extraction and v3.3.2 logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    md_path = Path(md_path)
    metadata = {
        "file_path": str(md_path),
        "file_size": 0,
        "read_at": datetime.now().isoformat(),
        "encoding_used": "utf-8",
        "read_success": False,
        "error": None,
        "v332_enhanced": True
    }
    
    try:
        if not md_path.exists():
            metadata["error"] = "File does not exist"
            logger.error(f"File does not exist: {md_path}")
            return "", metadata
        
        metadata["file_size"] = md_path.stat().st_size
        metadata["modified_time"] = datetime.fromtimestamp(md_path.stat().st_mtime).isoformat()
        
        logger.debug(f"Reading MD file: {md_path.name} ({metadata['file_size']} bytes)")
        
        # Try multiple encodings
        encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(md_path, "r", encoding=encoding) as f:
                    content = f.read()
                metadata["encoding_used"] = encoding
                metadata["read_success"] = True
                metadata["content_length"] = len(content)
                metadata["line_count"] = content.count('\n') + 1
                
                logger.debug(f"Successfully read {md_path.name} with {encoding} encoding")
                return content, metadata
            except UnicodeDecodeError:
                logger.debug(f"Failed to read {md_path.name} with {encoding} encoding")
                continue
        
        # If all encodings fail, try with error handling
        with open(md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        metadata["encoding_used"] = "utf-8 (with errors replaced)"
        metadata["read_success"] = True
        metadata["content_length"] = len(content)
        
        logger.warning(f"Read {md_path.name} with character replacement")
        return content, metadata
        
    except Exception as e:
        metadata["error"] = str(e)
        logger.error(f"Failed to read {md_path}: {e}")
        return "", metadata

def get_file_hash(file_path: Union[str, Path], algorithm: str = "md5", logger=None) -> str:
    """Get file hash for integrity checking with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    try:
        logger.debug(f"Computing {algorithm} hash for {Path(file_path).name}")
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        hash_value = hash_obj.hexdigest()
        logger.debug(f"Hash computed: {hash_value[:8]}...")
        return hash_value
    except Exception as e:
        if logger:
            logger.warning(f"Failed to compute hash for {file_path}: {e}")
        return ""

def extract_file_metadata(file_path: Union[str, Path], logger=None) -> Dict[str, Any]:
    """Extract comprehensive file metadata with v3.3.2 enhancements"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    file_path = Path(file_path)
    
    metadata = {
        "file_name": file_path.name,
        "file_stem": file_path.stem,
        "file_suffix": file_path.suffix,
        "file_size": 0,
        "created_time": None,
        "modified_time": None,
        "accessed_time": None,
        "is_file": False,
        "is_readable": False,
        "file_hash": "",
        "extracted_at": datetime.now().isoformat(),
        "v332_enhanced": True
    }
    
    try:
        if file_path.exists():
            stat = file_path.stat()
            metadata.update({
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_file": file_path.is_file(),
                "is_readable": os.access(file_path, os.R_OK),
            })
            
            logger.debug(f"Extracted metadata for {file_path.name}")
            
            # Get creation time (platform dependent)
            try:
                if hasattr(stat, 'st_birthtime'):  # macOS
                    metadata["created_time"] = datetime.fromtimestamp(stat.st_birthtime).isoformat()
                elif platform.system() == 'Windows':
                    metadata["created_time"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            except Exception:
                pass
            
            # Get file hash for small files
            if stat.st_size < 10 * 1024 * 1024:  # Less than 10MB
                metadata["file_hash"] = get_file_hash(file_path, logger=logger)
        else:
            logger.warning(f"File does not exist: {file_path}")
                
    except Exception as e:
        metadata["error"] = str(e)
        logger.error(f"Error extracting metadata for {file_path}: {e}")
    
    return metadata

# ============================================================================
# ENHANCED DATE PARSING (v3.3.2 - with logging integration)
# ============================================================================

def parse_date_enhanced(date_text: str, default_year: Optional[int] = None, 
                       logger=None) -> Optional[datetime]:
    """Enhanced date parsing with multiple format support including Chinese and v3.3.2 logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not date_text or not isinstance(date_text, str):
        return None
    
    date_text = date_text.strip()
    if not date_text:
        return None
    
    logger.debug(f"Parsing date: '{date_text}'")
    
    # Default year fallback
    if default_year is None:
        default_year = datetime.now().year
    
    # Enhanced date patterns (preserved from v3.3.1)
    date_patterns = [
        # ISO formats
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
        (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%d-%m-%Y'),
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),
        
        # Chinese formats
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', 'chinese'),
        (r'(\d{4})年(\d{1,2})月', 'chinese_month'),
        
        # English formats
        (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', 'english_month'),
        (r'(\d{1,2})\s+(\w+)\s+(\d{4})', 'english_month_reverse'),
        
        # Timestamp formats
        (r'(\d{4})(\d{2})(\d{2})', 'compact'),
        (r'(\d{2})(\d{2})(\d{4})', 'compact_reverse'),
    ]
    
    # Try each pattern
    for pattern, format_type in date_patterns:
        match = re.search(pattern, date_text)
        if match:
            try:
                if format_type == 'chinese':
                    year, month, day = match.groups()
                    result = datetime(int(year), int(month), int(day))
                    logger.debug(f"Parsed Chinese date: {result}")
                    return result
                elif format_type == 'chinese_month':
                    year, month = match.groups()
                    result = datetime(int(year), int(month), 1)
                    logger.debug(f"Parsed Chinese month: {result}")
                    return result
                elif format_type == 'english_month':
                    month_name, day, year = match.groups()
                    month_num = parse_month_name(month_name)
                    if month_num:
                        result = datetime(int(year), month_num, int(day))
                        logger.debug(f"Parsed English date: {result}")
                        return result
                elif format_type == 'english_month_reverse':
                    day, month_name, year = match.groups()
                    month_num = parse_month_name(month_name)
                    if month_num:
                        result = datetime(int(year), month_num, int(day))
                        logger.debug(f"Parsed reverse English date: {result}")
                        return result
                elif format_type == 'compact':
                    year, month, day = match.groups()
                    result = datetime(int(year), int(month), int(day))
                    logger.debug(f"Parsed compact date: {result}")
                    return result
                elif format_type == 'compact_reverse':
                    day, month, year = match.groups()
                    result = datetime(int(year), int(month), int(day))
                    logger.debug(f"Parsed reverse compact date: {result}")
                    return result
                else:
                    # Standard datetime parsing
                    parts = match.groups()
                    if len(parts) == 3:
                        if format_type.startswith('%Y'):
                            result = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                        else:
                            result = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                        logger.debug(f"Parsed standard date: {result}")
                        return result
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse with pattern {format_type}: {e}")
                continue
    
    # Fallback: try to extract any 4-digit year and use current date
    year_match = re.search(r'\b(\d{4})\b', date_text)
    if year_match:
        try:
            year = int(year_match.group(1))
            if 2000 <= year <= 2030:
                result = datetime(year, 1, 1)
                logger.debug(f"Parsed year only: {result}")
                return result
        except ValueError:
            pass
    
    logger.debug(f"Failed to parse date: '{date_text}'")
    return None

def parse_month_name(month_name: str) -> Optional[int]:
    """Parse month name to number (preserved from v3.3.1)"""
    month_mapping = {
        # English
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
        'november': 11, 'nov': 11, 'december': 12, 'dec': 12,
        
        # Chinese
        '一月': 1, '二月': 2, '三月': 3, '四月': 4, '五月': 5, '六月': 6,
        '七月': 7, '八月': 8, '九月': 9, '十月': 10, '十一月': 11, '十二月': 12
    }
    
    return month_mapping.get(month_name.lower())

def format_date_safe(date_obj: datetime, format_str: str = '%Y/%m/%d') -> str:
    """Safely format datetime object (preserved from v3.3.1)"""
    try:
        return date_obj.strftime(format_str)
    except Exception:
        return date_obj.isoformat().split('T')[0]

def calculate_date_range(dates: List[datetime]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Calculate date range from list of dates (preserved from v3.3.1)"""
    if not dates:
        return None, None
    
    valid_dates = [d for d in dates if d is not None]
    if not valid_dates:
        return None, None
    
    return min(valid_dates), max(valid_dates)

# ============================================================================
# ENHANCED TEXT PROCESSING (v3.3.2 - with logging integration)
# ============================================================================

def clean_text_enhanced(text: str, preserve_chinese: bool = True, logger=None) -> str:
    """Enhanced text cleaning with Chinese character preservation and logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not text:
        return ""
    
    original_length = len(text)
    logger.debug(f"Cleaning text: {original_length} characters")
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[-]{2,}', '--', text)
    
    # Preserve Chinese characters and common punctuation
    if preserve_chinese:
        # Keep Chinese characters, letters, numbers, basic punctuation
        text = re.sub(r'[^\u4e00-\u9fff\w\s.,;:!?()[\]{}""''（）【】｛｝，。；：！？\-]', '', text)
    else:
        # Keep only ASCII alphanumeric and basic punctuation
        text = re.sub(r'[^\w\s.,;:!?()[\]{}\-]', '', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    cleaned_length = len(text)
    logger.debug(f"Text cleaned: {original_length} → {cleaned_length} characters")
    
    return text

def extract_numbers_from_text(text: str, logger=None) -> List[float]:
    """Extract numerical values from text with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not text:
        return []
    
    logger.debug(f"Extracting numbers from text: {len(text)} characters")
    
    # Enhanced number patterns (preserved from v3.3.1)
    number_patterns = [
        r'\b\d+\.\d+\b',           # Decimal numbers
        r'\b\d+,\d{3}(?:,\d{3})*\.\d+\b',  # Comma-separated decimals
        r'\b\d+,\d{3}(?:,\d{3})*\b',       # Comma-separated integers
        r'\b\d+\b'                # Simple integers
    ]
    
    numbers = []
    for pattern in number_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Remove commas and convert to float
                clean_number = match.replace(',', '')
                numbers.append(float(clean_number))
            except ValueError:
                continue
    
    logger.debug(f"Extracted {len(numbers)} numbers")
    return numbers

def validate_company_code(code: str, logger=None) -> bool:
    """Enhanced company code validation with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not code or not isinstance(code, str):
        logger.debug(f"Invalid company code type: {type(code)}")
        return False
    
    code = code.strip()
    
    # Must be exactly 4 digits
    if not re.match(r'^\d{4}$', code):
        logger.debug(f"Company code format invalid: {code}")
        return False
    
    # Exclude invalid codes
    invalid_codes = {'0000', '9999'}
    if code in invalid_codes:
        logger.debug(f"Company code in exclusion list: {code}")
        return False
    
    # Taiwan stock codes typically start with 1-9
    if code.startswith('0'):
        logger.debug(f"Company code starts with 0: {code}")
        return False
    
    logger.debug(f"Company code valid: {code}")
    return True

def validate_company_name(name: str, logger=None) -> bool:
    """Enhanced company name validation with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not name or not isinstance(name, str):
        logger.debug(f"Invalid company name type: {type(name)}")
        return False
    
    name = name.strip()
    
    # Check length
    if len(name) < 2 or len(name) > 50:
        logger.debug(f"Company name length invalid: {len(name)}")
        return False
    
    # Allow Chinese characters, letters, numbers, and common business symbols
    if not re.match(r'^[\u4e00-\u9fff\w\s\(\)（）\-&\.\,]+$', name):
        logger.debug(f"Company name contains invalid characters: {name}")
        return False
    
    # Exclude obviously invalid names
    invalid_names = {'null', 'none', 'unknown', '未知', 'n/a'}
    if name.lower() in invalid_names:
        logger.debug(f"Company name in exclusion list: {name}")
        return False
    
    logger.debug(f"Company name valid: {name}")
    return True

def normalize_company_name(name: str, logger=None) -> str:
    """Normalize company name for matching with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not name:
        return ""
    
    original_name = name
    
    # Clean and normalize
    name = clean_text_enhanced(name, logger=logger)
    
    # Remove common suffixes
    suffixes = ['股份有限公司', '有限公司', '股份', '公司', 'Corporation', 'Corp', 'Inc', 'Ltd', 'Limited', 'Co']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    
    # Normalize spaces
    name = re.sub(r'\s+', '', name)
    
    logger.debug(f"Normalized company name: '{original_name}' → '{name}'")
    return name

def fuzzy_match_company_names(name1: str, name2: str, threshold: float = 0.8, 
                             logger=None) -> bool:
    """Fuzzy matching for company names with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not name1 or not name2:
        return False
    
    # Normalize both names
    norm1 = normalize_company_name(name1, logger=logger)
    norm2 = normalize_company_name(name2, logger=logger)
    
    logger.debug(f"Fuzzy matching: '{norm1}' vs '{norm2}'")
    
    # Exact match after normalization
    if norm1 == norm2:
        logger.debug("Exact match found")
        return True
    
    # Check if one is contained in the other
    if norm1 in norm2 or norm2 in norm1:
        logger.debug("Substring match found")
        return True
    
    # Simple similarity check
    shorter = min(norm1, norm2, key=len)
    longer = max(norm1, norm2, key=len)
    
    if len(shorter) > 0:
        similarity = len(shorter) / len(longer)
        logger.debug(f"Similarity score: {similarity:.2f}")
        if similarity >= threshold:
            logger.debug("Similarity threshold met")
            return True
    
    logger.debug("No match found")
    return False

# ============================================================================
# ENHANCED DATA PARSING (v3.3.2 - with logging integration)
# ============================================================================

def parse_md_file_enhanced(md_content: str, logger=None) -> Dict[str, Any]:
    """Enhanced MD file parsing with comprehensive data extraction and v3.3.2 logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if not md_content:
        return {}
    
    logger.debug(f"Parsing MD content: {len(md_content)} characters")
    
    data = {
        "parsing_timestamp": datetime.now().isoformat(),
        "content_length": len(md_content),
        "parsing_version": __version__,
        "v332_enhanced": True
    }
    
    try:
        # Enhanced EPS patterns for multiple years (preserved from v3.3.1)
        eps_patterns = {
            '2025': [
                r'2025.*?EPS.*?([0-9]+\.?[0-9]*)',
                r'2025年.*?每股盈餘.*?([0-9]+\.?[0-9]*)',
                r'FY25.*?EPS.*?([0-9]+\.?[0-9]*)',
                r'E2025.*?([0-9]+\.?[0-9]*)'
            ],
            '2026': [
                r'2026.*?EPS.*?([0-9]+\.?[0-9]*)',
                r'2026年.*?每股盈餘.*?([0-9]+\.?[0-9]*)',
                r'FY26.*?EPS.*?([0-9]+\.?[0-9]*)',
                r'E2026.*?([0-9]+\.?[0-9]*)'
            ],
            '2027': [
                r'2027.*?EPS.*?([0-9]+\.?[0-9]*)',
                r'2027年.*?每股盈餘.*?([0-9]+\.?[0-9]*)',
                r'FY27.*?EPS.*?([0-9]+\.?[0-9]*)',
                r'E2027.*?([0-9]+\.?[0-9]*)'
            ]
        }
        
        # Extract EPS data for each year
        for year, patterns in eps_patterns.items():
            eps_values = []
            for pattern in patterns:
                matches = re.findall(pattern, md_content, re.IGNORECASE)
                for match in matches:
                    try:
                        value = float(match)
                        if 0.1 <= value <= 1000:  # Reasonable EPS range
                            eps_values.append(value)
                    except ValueError:
                        continue
            
            if eps_values:
                data[f'{year}EPS中位數'] = round(sum(eps_values) / len(eps_values), 2)
                data[f'{year}EPS最高值'] = round(max(eps_values), 2)
                data[f'{year}EPS最低值'] = round(min(eps_values), 2)
                data[f'{year}EPS值數量'] = len(eps_values)
                logger.debug(f"Found {len(eps_values)} EPS values for {year}")
        
        # Enhanced revenue patterns (preserved from v3.3.1)
        revenue_patterns = [
            r'營收.*?([0-9]+\.?[0-9]*)',
            r'Revenue.*?([0-9]+\.?[0-9]*)',
            r'銷售額.*?([0-9]+\.?[0-9]*)',
            r'收入.*?([0-9]+\.?[0-9]*)'
        ]
        
        revenue_values = []
        for pattern in revenue_patterns:
            matches = re.findall(pattern, md_content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match)
                    if value > 0:
                        revenue_values.append(value)
                except ValueError:
                    continue
        
        if revenue_values:
            data['營收預估'] = round(sum(revenue_values) / len(revenue_values), 2)
            logger.debug(f"Found {len(revenue_values)} revenue values")
        
        # Enhanced target price patterns (preserved from v3.3.1)
        target_price_patterns = [
            r'目標價.*?([0-9]+\.?[0-9]*)',
            r'Target.*?Price.*?([0-9]+\.?[0-9]*)',
            r'合理價值.*?([0-9]+\.?[0-9]*)',
            r'Fair.*?Value.*?([0-9]+\.?[0-9]*)'
        ]
        
        target_prices = []
        for pattern in target_price_patterns:
            matches = re.findall(pattern, md_content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match)
                    if 1 <= value <= 10000:  # Reasonable price range
                        target_prices.append(value)
                except ValueError:
                    continue
        
        if target_prices:
            data['目標價'] = round(sum(target_prices) / len(target_prices), 2)
            logger.debug(f"Found {len(target_prices)} target price values")
        
        # Enhanced analyst count patterns (preserved from v3.3.1)
        analyst_patterns = [
            r'分析師.*?([0-9]+)',
            r'Analyst.*?([0-9]+)',
            r'([0-9]+).*?分析師',
            r'([0-9]+).*?analyst'
        ]
        
        analyst_counts = []
        for pattern in analyst_patterns:
            matches = re.findall(pattern, md_content, re.IGNORECASE)
            for match in matches:
                try:
                    value = int(match)
                    if 1 <= value <= 50:  # Reasonable analyst count
                        analyst_counts.append(value)
                except ValueError:
                    continue
        
        if analyst_counts:
            data['分析師數量'] = max(analyst_counts)  # Take the highest count
            logger.debug(f"Found {len(analyst_counts)} analyst count values")
        
        # Calculate data quality score
        data['數據品質評分'] = calculate_data_quality_score(data, logger=logger)
        data['解析成功'] = True
        
        logger.info(f"MD parsing completed: quality score {data['數據品質評分']}")
        
    except Exception as e:
        data['解析錯誤'] = str(e)
        data['解析成功'] = False
        logger.error(f"Enhanced parse error: {e}")
    
    return data

def calculate_data_quality_score(data: Dict[str, Any], logger=None) -> int:
    """Calculate data quality score (1-4) based on extracted data with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    score = 1  # Base score
    
    # Check for EPS data
    eps_years = ['2025', '2026', '2027']
    eps_found = sum(1 for year in eps_years if f'{year}EPS中位數' in data)
    
    if eps_found >= 3:
        score = 4  # Excellent - all 3 years
    elif eps_found >= 2:
        score = 3  # Good - 2 years
    elif eps_found >= 1:
        score = 2  # Fair - 1 year
    
    # Bonus for additional data
    if '目標價' in data:
        score = min(4, score + 1)
    
    if '分析師數量' in data:
        score = min(4, score + 1)
    
    if '營收預估' in data:
        score = min(4, score + 1)
    
    final_score = max(1, min(4, score))
    logger.debug(f"Quality score calculated: {final_score} (EPS years: {eps_found})")
    
    return final_score

def extract_company_info_from_content(content: str, logger=None) -> Dict[str, Optional[str]]:
    """Extract company information from content with logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    logger.debug(f"Extracting company info from {len(content)} characters")
    
    info = {
        "company_name": None,
        "stock_code": None,
        "extracted_from": "content_analysis",
        "v332_enhanced": True
    }
    
    # Stock code patterns (preserved from v3.3.1)
    stock_patterns = [
        r'\((\d{4})\)',      # (2330)
        r'(\d{4})\.TW',      # 2330.TW
        r'(\d{4})-TW',       # 2330-TW
        r'代號.*?(\d{4})',    # 代號: 2330
        r'股票代號.*?(\d{4})', # 股票代號: 2330
    ]
    
    for pattern in stock_patterns:
        match = re.search(pattern, content)
        if match:
            code = match.group(1)
            if validate_company_code(code, logger=logger):
                info["stock_code"] = code
                logger.debug(f"Found stock code: {code}")
                break
    
    # Company name patterns (Taiwan companies) (preserved from v3.3.1)
    company_patterns = [
        r'(台積電|台灣積體電路)',
        r'(聯發科|MediaTek)',
        r'(鴻海|Hon Hai)',
        r'(廣達|Quanta)',
        r'(華碩|ASUS)',
        r'(宏碁|Acer)',
        r'(台達電|Delta)',
        r'(聯電|UMC)',
        r'(緯創|Wistron)',
        r'(仁寶|Compal)',
        r'(和碩|Pegatron)',
        r'(統一|Uni-President)',
        r'(富邦金|Fubon)',
        r'(中華電|Chunghwa)',
        r'(吉茂)',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            name = match.group(1).split('|')[0]  # Take Chinese name
            if validate_company_name(name, logger=logger):
                info["company_name"] = name
                logger.debug(f"Found company name: {name}")
                break
    
    return info

# ============================================================================
# ENHANCED ERROR HANDLING (v3.3.2 - with logging integration)
# ============================================================================

def safe_execute(func, *args, default_return=None, log_errors=True, logger=None, **kwargs):
    """Safely execute function with error handling and v3.3.2 logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    try:
        logger.debug(f"Executing function: {func.__name__}")
        result = func(*args, **kwargs)
        logger.debug(f"Function {func.__name__} completed successfully")
        return result
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {e}")
            if is_debug_mode():
                logger.debug(traceback.format_exc())
        return default_return

def create_error_context(operation: str, logger=None, **context) -> Dict[str, Any]:
    """Create error context for debugging with v3.3.2 enhancements"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    error_context = {
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "context": context,
        "system_info": get_system_info(),
        "debug_mode": is_debug_mode(),
        "v332_enhanced": True
    }
    
    logger.debug(f"Created error context for operation: {operation}")
    return error_context

def log_error_with_context(error: Exception, context: Dict[str, Any], logger=None):
    """Log error with comprehensive context and v3.3.2 integration"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    if is_debug_mode():
        logger.error(f"Error in {context.get('operation', 'unknown')}: {error}")
        logger.debug(f"Context: {json.dumps(context, indent=2, default=str)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")

# ============================================================================
# PERFORMANCE AND MONITORING (v3.3.2 - enhanced integration)
# ============================================================================

class PerformanceTimer:
    """Context manager for timing operations with v3.3.2 integration"""
    
    def __init__(self, operation_name: str, logger=None):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.logger = logger or get_v332_logger("utils")
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        
        # Try to use v3.3.2 performance monitor
        try:
            self.perf_monitor = get_performance_monitor("utils")
            if hasattr(self.perf_monitor, 'time_operation'):
                self.perf_context = self.perf_monitor.time_operation(self.operation_name)
                self.perf_context.__enter__()
        except Exception:
            self.perf_monitor = None
            self.perf_context = None
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation_name} in {duration:.2f} seconds")
        else:
            self.logger.error(f"Failed {self.operation_name} after {duration:.2f} seconds: {exc_val}")
        
        # Exit performance monitor if available
        if self.perf_context:
            try:
                self.perf_context.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass
    
    @property
    def duration(self) -> Optional[float]:
        """Get duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

def monitor_memory_usage(logger=None) -> Dict[str, Any]:
    """Monitor memory usage with v3.3.2 logging"""
    if logger is None:
        logger = get_v332_logger("utils")
    
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        memory_data = {
            "rss": memory_info.rss,  # Resident Set Size
            "vms": memory_info.vms,  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available": psutil.virtual_memory().available,
            "timestamp": datetime.now().isoformat(),
            "v332_enhanced": True
        }
        
        logger.debug(f"Memory usage: {memory_data['percent']:.1f}% ({memory_data['rss'] / 1024 / 1024:.1f}MB)")
        return memory_data
        
    except ImportError:
        logger.warning("psutil not available for memory monitoring")
        return {"error": "psutil not available", "v332_enhanced": True}
    except Exception as e:
        logger.error(f"Error monitoring memory: {e}")
        return {"error": str(e), "v332_enhanced": True}

# ============================================================================
# LEGACY COMPATIBILITY (v3.3.2 - maintained for v3.3.1)
# ============================================================================

def read_md_file(md_path: str) -> str:
    """Legacy function - maintained for compatibility"""
    content, _ = read_md_file_enhanced(md_path)
    return content

def parse_md_file(md_content: str) -> dict:
    """Legacy function - maintained for compatibility"""
    enhanced_data = parse_md_file_enhanced(md_content)
    
    # Convert to legacy format
    legacy_data = {}
    
    # Map new format to legacy format
    if '2025EPS中位數' in enhanced_data:
        legacy_data['2025EPS中位數'] = enhanced_data['2025EPS中位數']
    if '2026EPS中位數' in enhanced_data:
        legacy_data['2026EPS中位數'] = enhanced_data['2026EPS中位數']
    if '2027EPS中位數' in enhanced_data:
        legacy_data['2027EPS中位數'] = enhanced_data['2027EPS中位數']
    
    if '營收預估' in enhanced_data:
        legacy_data['2025營收中位數'] = enhanced_data['營收預估']
        legacy_data['2026營收中位數'] = enhanced_data['營收預估']
        legacy_data['2027營收中位數'] = enhanced_data['營收預估']
    
    return legacy_data

# ============================================================================
# v3.3.2 CLI INTEGRATION HELPERS
# ============================================================================

def get_cli_safe_output():
    """Get CLI-safe output handler for cross-platform compatibility"""
    try:
        from factset_cli import SafeOutput
        return SafeOutput()
    except ImportError:
        # Fallback safe output
        class FallbackSafeOutput:
            def safe_print(self, message: str, end: str = '\n'):
                try:
                    print(message, end=end)
                except UnicodeEncodeError:
                    safe_message = message.encode('ascii', errors='replace').decode('ascii')
                    print(safe_message, end=end)
        return FallbackSafeOutput()

def is_github_actions() -> bool:
    """Check if running in GitHub Actions environment"""
    return bool(os.getenv('GITHUB_ACTIONS'))

def is_windows_platform() -> bool:
    """Check if running on Windows platform"""
    return sys.platform == "win32"

# ============================================================================
# MODULE INITIALIZATION (v3.3.2)
# ============================================================================

# Setup module-level logger with v3.3.2 integration
try:
    _logger = get_v332_logger("utils")
    _logger.info(f"Enhanced utilities module v{__version__} loaded (v3.3.2)")
except Exception:
    # Fallback to standard logging
    _logger = logging.getLogger(__name__)
    _logger.info(f"Utilities module v{__version__} loaded (fallback mode)")

# Export version information and enhanced functions
__all__ = [
    '__version__', '__date__', '__author__',
    
    # v3.3.2 new functions
    'get_v332_logger', 'get_performance_monitor', 'get_cli_safe_output',
    'is_github_actions', 'is_windows_platform',
    
    # v3.3.1 preserved functions
    'is_debug_mode', 'get_system_info', 'setup_safe_logging',
    'is_file_parsed', 'mark_parsed_file', 'read_md_file_enhanced', 
    'get_file_hash', 'extract_file_metadata',
    'parse_date_enhanced', 'format_date_safe', 'calculate_date_range',
    'clean_text_enhanced', 'extract_numbers_from_text', 
    'validate_company_code', 'validate_company_name', 'normalize_company_name',
    'fuzzy_match_company_names', 'parse_md_file_enhanced', 
    'calculate_data_quality_score', 'extract_company_info_from_content',
    'safe_execute', 'create_error_context', 'log_error_with_context',
    'PerformanceTimer', 'monitor_memory_usage',
    'read_md_file', 'parse_md_file'  # Legacy compatibility
]