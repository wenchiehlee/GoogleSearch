"""
utils.py - Enhanced Shared Utilities Module (v3.3.0)

Version: 3.3.0
Date: 2025-06-22
Author: Google Search FactSet Pipeline - v3.3.0 Enhanced Architecture
License: MIT

v3.3.0 ENHANCEMENTS:
- ✅ Enhanced date parsing with multiple fallback strategies
- ✅ Improved file handling with better error recovery
- ✅ Enhanced text processing and validation utilities
- ✅ Better logging setup with safe encoding
- ✅ Data validation helpers for v3.3.0 features
- ✅ Company name matching and validation utilities
- ✅ Quality scoring and assessment functions
- ✅ Enhanced error handling and context management
- ✅ File metadata extraction and analysis
- ✅ Content quality assessment for v3.3.0

Description:
    Comprehensive utility functions for the Enhanced FactSet Pipeline v3.3.0:
    - Enhanced file operations with metadata extraction
    - Advanced date and time parsing with multiple formats
    - Robust text processing and validation
    - Safe logging setup with Windows compatibility
    - Data quality assessment and scoring
    - Company information extraction and validation
    - Error handling with context preservation
    - System diagnostics and performance monitoring

Key Features:
    - Cross-platform compatibility with enhanced Windows support
    - Robust date parsing with Chinese format support
    - Advanced text cleaning and validation
    - Safe emoji handling for different console types
    - Enhanced logging with structured output
    - Data quality scoring algorithms
    - Company name matching with fuzzy logic
    - File integrity checking and metadata extraction

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

# Version Information - v3.3.0
__version__ = "3.3.0"
__date__ = "2025-06-22"
__author__ = "Google Search FactSet Pipeline - v3.3.0 Enhanced Architecture"

# ============================================================================
# ENHANCED SYSTEM UTILITIES (v3.3.0)
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
    """Get comprehensive system information for v3.3.0"""
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
        "utils_version": __version__
    }

def setup_safe_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup enhanced safe logging for v3.3.0 with Windows compatibility"""
    
    # Create logs directory if needed
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
    logger = logging.getLogger('factset_pipeline_v330')
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
    
    logger.info(f"Enhanced logging setup complete (v{__version__})")
    return logger

# ============================================================================
# ENHANCED FILE OPERATIONS (v3.3.0)
# ============================================================================

def is_file_parsed(md_path: Union[str, Path]) -> bool:
    """Enhanced check if a Markdown file has been parsed"""
    try:
        md_path = Path(md_path)
        parsed_flag = md_path.with_suffix(".parsed")
        
        if parsed_flag.exists():
            # Check if parsed flag is newer than the source file
            if md_path.exists():
                return parsed_flag.stat().st_mtime >= md_path.stat().st_mtime
            return True
        return False
    except Exception:
        return False

def mark_parsed_file(md_path: Union[str, Path], metadata: Optional[Dict] = None):
    """Enhanced marking of parsed files with metadata"""
    try:
        md_path = Path(md_path)
        parsed_flag = md_path.with_suffix(".parsed")
        
        # Create flag with metadata
        flag_data = {
            "parsed_at": datetime.now().isoformat(),
            "source_file": str(md_path),
            "source_size": md_path.stat().st_size if md_path.exists() else 0,
            "utils_version": __version__
        }
        
        if metadata:
            flag_data.update(metadata)
        
        with open(parsed_flag, 'w', encoding='utf-8') as f:
            json.dump(flag_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        if is_debug_mode():
            print(f"Warning: Could not mark file as parsed: {e}")

def read_md_file_enhanced(md_path: Union[str, Path]) -> Tuple[str, Dict]:
    """Enhanced MD file reading with metadata extraction"""
    md_path = Path(md_path)
    metadata = {
        "file_path": str(md_path),
        "file_size": 0,
        "read_at": datetime.now().isoformat(),
        "encoding_used": "utf-8",
        "read_success": False,
        "error": None
    }
    
    try:
        if not md_path.exists():
            metadata["error"] = "File does not exist"
            return "", metadata
        
        metadata["file_size"] = md_path.stat().st_size
        metadata["modified_time"] = datetime.fromtimestamp(md_path.stat().st_mtime).isoformat()
        
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
                return content, metadata
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, try with error handling
        with open(md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        metadata["encoding_used"] = "utf-8 (with errors replaced)"
        metadata["read_success"] = True
        metadata["content_length"] = len(content)
        return content, metadata
        
    except Exception as e:
        metadata["error"] = str(e)
        if is_debug_mode():
            logging.error(f"Failed to read {md_path}: {e}")
        return "", metadata

def get_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """Get file hash for integrity checking"""
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception:
        return ""

def extract_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Extract comprehensive file metadata"""
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
        "extracted_at": datetime.now().isoformat()
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
                metadata["file_hash"] = get_file_hash(file_path)
                
    except Exception as e:
        metadata["error"] = str(e)
    
    return metadata

# ============================================================================
# ENHANCED DATE PARSING (v3.3.0)
# ============================================================================

def parse_date_enhanced(date_text: str, default_year: Optional[int] = None) -> Optional[datetime]:
    """Enhanced date parsing with multiple format support including Chinese"""
    if not date_text or not isinstance(date_text, str):
        return None
    
    date_text = date_text.strip()
    if not date_text:
        return None
    
    # Default year fallback
    if default_year is None:
        default_year = datetime.now().year
    
    # Enhanced date patterns
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
                    return datetime(int(year), int(month), int(day))
                elif format_type == 'chinese_month':
                    year, month = match.groups()
                    return datetime(int(year), int(month), 1)
                elif format_type == 'english_month':
                    month_name, day, year = match.groups()
                    month_num = parse_month_name(month_name)
                    if month_num:
                        return datetime(int(year), month_num, int(day))
                elif format_type == 'english_month_reverse':
                    day, month_name, year = match.groups()
                    month_num = parse_month_name(month_name)
                    if month_num:
                        return datetime(int(year), month_num, int(day))
                elif format_type == 'compact':
                    year, month, day = match.groups()
                    return datetime(int(year), int(month), int(day))
                elif format_type == 'compact_reverse':
                    day, month, year = match.groups()
                    return datetime(int(year), int(month), int(day))
                else:
                    # Standard datetime parsing
                    parts = match.groups()
                    if len(parts) == 3:
                        if format_type.startswith('%Y'):
                            return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                        else:
                            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            except (ValueError, IndexError):
                continue
    
    # Fallback: try to extract any 4-digit year and use current date
    year_match = re.search(r'\b(\d{4})\b', date_text)
    if year_match:
        try:
            year = int(year_match.group(1))
            if 2000 <= year <= 2030:
                return datetime(year, 1, 1)
        except ValueError:
            pass
    
    return None

def parse_month_name(month_name: str) -> Optional[int]:
    """Parse month name to number"""
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
    """Safely format datetime object"""
    try:
        return date_obj.strftime(format_str)
    except Exception:
        return date_obj.isoformat().split('T')[0]

def calculate_date_range(dates: List[datetime]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Calculate date range from list of dates"""
    if not dates:
        return None, None
    
    valid_dates = [d for d in dates if d is not None]
    if not valid_dates:
        return None, None
    
    return min(valid_dates), max(valid_dates)

# ============================================================================
# ENHANCED TEXT PROCESSING (v3.3.0)
# ============================================================================

def clean_text_enhanced(text: str, preserve_chinese: bool = True) -> str:
    """Enhanced text cleaning with Chinese character preservation"""
    if not text:
        return ""
    
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
    
    return text

def extract_numbers_from_text(text: str) -> List[float]:
    """Extract numerical values from text"""
    if not text:
        return []
    
    # Enhanced number patterns
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
    
    return numbers

def validate_company_code(code: str) -> bool:
    """Enhanced company code validation"""
    if not code or not isinstance(code, str):
        return False
    
    code = code.strip()
    
    # Must be exactly 4 digits
    if not re.match(r'^\d{4}$', code):
        return False
    
    # Exclude invalid codes
    invalid_codes = {'0000', '9999'}
    if code in invalid_codes:
        return False
    
    # Taiwan stock codes typically start with 1-9
    if code.startswith('0'):
        return False
    
    return True

def validate_company_name(name: str) -> bool:
    """Enhanced company name validation"""
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # Check length
    if len(name) < 2 or len(name) > 50:
        return False
    
    # Allow Chinese characters, letters, numbers, and common business symbols
    if not re.match(r'^[\u4e00-\u9fff\w\s\(\)（）\-&\.\,]+$', name):
        return False
    
    # Exclude obviously invalid names
    invalid_names = {'null', 'none', 'unknown', '未知', 'n/a'}
    if name.lower() in invalid_names:
        return False
    
    return True

def normalize_company_name(name: str) -> str:
    """Normalize company name for matching"""
    if not name:
        return ""
    
    # Clean and normalize
    name = clean_text_enhanced(name)
    
    # Remove common suffixes
    suffixes = ['股份有限公司', '有限公司', '股份', '公司', 'Corporation', 'Corp', 'Inc', 'Ltd', 'Limited', 'Co']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    
    # Normalize spaces
    name = re.sub(r'\s+', '', name)
    
    return name

def fuzzy_match_company_names(name1: str, name2: str, threshold: float = 0.8) -> bool:
    """Fuzzy matching for company names"""
    if not name1 or not name2:
        return False
    
    # Normalize both names
    norm1 = normalize_company_name(name1)
    norm2 = normalize_company_name(name2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Check if one is contained in the other
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Simple similarity check
    shorter = min(norm1, norm2, key=len)
    longer = max(norm1, norm2, key=len)
    
    if len(shorter) > 0:
        similarity = len(shorter) / len(longer)
        if similarity >= threshold:
            return True
    
    return False

# ============================================================================
# ENHANCED DATA PARSING (v3.3.0)
# ============================================================================

def parse_md_file_enhanced(md_content: str) -> Dict[str, Any]:
    """Enhanced MD file parsing with comprehensive data extraction"""
    if not md_content:
        return {}
    
    data = {
        "parsing_timestamp": datetime.now().isoformat(),
        "content_length": len(md_content),
        "parsing_version": __version__
    }
    
    try:
        # Enhanced EPS patterns for multiple years
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
        
        # Enhanced revenue patterns
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
        
        # Enhanced target price patterns
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
        
        # Enhanced analyst count patterns
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
        
        # Calculate data quality score
        data['數據品質評分'] = calculate_data_quality_score(data)
        data['解析成功'] = True
        
    except Exception as e:
        data['解析錯誤'] = str(e)
        data['解析成功'] = False
        if is_debug_mode():
            logging.warning(f"Enhanced parse error: {e}")
    
    return data

def calculate_data_quality_score(data: Dict[str, Any]) -> int:
    """Calculate data quality score (1-4) based on extracted data"""
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
    
    return max(1, min(4, score))

def extract_company_info_from_content(content: str) -> Dict[str, Optional[str]]:
    """Extract company information from content"""
    info = {
        "company_name": None,
        "stock_code": None,
        "extracted_from": "content_analysis"
    }
    
    # Stock code patterns
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
            if validate_company_code(code):
                info["stock_code"] = code
                break
    
    # Company name patterns (Taiwan companies)
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
            if validate_company_name(name):
                info["company_name"] = name
                break
    
    return info

# ============================================================================
# ENHANCED ERROR HANDLING (v3.3.0)
# ============================================================================

def safe_execute(func, *args, default_return=None, log_errors=True, **kwargs):
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors and is_debug_mode():
            logging.error(f"Error in {func.__name__}: {e}")
            if is_debug_mode():
                logging.debug(traceback.format_exc())
        return default_return

def create_error_context(operation: str, **context) -> Dict[str, Any]:
    """Create error context for debugging"""
    return {
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "context": context,
        "system_info": get_system_info(),
        "debug_mode": is_debug_mode()
    }

def log_error_with_context(error: Exception, context: Dict[str, Any]):
    """Log error with comprehensive context"""
    if is_debug_mode():
        logging.error(f"Error in {context.get('operation', 'unknown')}: {error}")
        logging.debug(f"Context: {json.dumps(context, indent=2, default=str)}")
        logging.debug(f"Traceback: {traceback.format_exc()}")

# ============================================================================
# PERFORMANCE AND MONITORING (v3.3.0)
# ============================================================================

class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        if is_debug_mode():
            logging.debug(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            if is_debug_mode():
                logging.debug(f"Completed {self.operation_name} in {duration:.2f} seconds")
        else:
            logging.error(f"Failed {self.operation_name} after {duration:.2f} seconds: {exc_val}")
    
    @property
    def duration(self) -> Optional[float]:
        """Get duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

def monitor_memory_usage() -> Dict[str, Any]:
    """Monitor memory usage (if psutil is available)"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss,  # Resident Set Size
            "vms": memory_info.vms,  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available": psutil.virtual_memory().available,
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# LEGACY COMPATIBILITY (v3.3.0)
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
# MODULE INITIALIZATION
# ============================================================================

# Setup module-level logger
_logger = logging.getLogger(__name__)
_logger.info(f"Enhanced utilities module v{__version__} loaded")

# Export version information
__all__ = [
    '__version__', '__date__', '__author__',
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