"""
factset_search.py - Enhanced Google Search Module (v3.3.3)

Version: 3.3.3
Date: 2025-06-24
Author: Google Search FactSet Pipeline - v3.3.3 Final Integrated Edition

v3.3.3 ENHANCEMENTS:
- ✅ Integration with StandardizedQualityScorer (0-10 scale)
- ✅ Quality scoring integration across all search functions
- ✅ All v3.3.2 functionality preserved and enhanced

v3.3.2 FEATURES MAINTAINED:
- ✅ Integration with enhanced logging system (stage-specific dual output)
- ✅ Stage runner compatibility for unified CLI interface
- ✅ Cross-platform safe output handling
- ✅ Enhanced performance monitoring integration
- ✅ All v3.3.1 fixes and functionality preserved

v3.3.1 FEATURES MAINTAINED:
- ✅ FIXED #1: Search cascade failure - proper error isolation per company/URL
- ✅ FIXED #3: Rate limiting logic - unified rate limiter integration  
- ✅ FIXED #4: Module import issues - removed circular dependencies
- ✅ FIXED #6: Filename conflicts - enhanced unique generation with content hash
- ✅ FIXED #9: Memory management - streaming and batching support
"""

import os
import re
import time
import json
import hashlib
import traceback
import requests
import gc
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, quote_plus, unquote, quote
from typing import List, Dict, Optional, Tuple, Any

# Version Information - v3.3.3
__version__ = "3.3.3"
__date__ = "2025-06-24"
__author__ = "Google Search FactSet Pipeline - v3.3.3 Final Integrated Edition"

# ============================================================================
# v3.3.3 LOGGING INTEGRATION
# ============================================================================

def get_v333_logger(module_name: str = "search"):
    """Get v3.3.3 enhanced logger with fallback"""
    try:
        from enhanced_logger import get_stage_logger
        return get_stage_logger(module_name)
    except ImportError:
        # Fallback to standard logging if v3.3.3 components not available
        import logging
        logger = logging.getLogger(f'factset_v333.{module_name}')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def get_performance_monitor(stage_name: str = "search"):
    """Get v3.3.3 performance monitor with fallback"""
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

# ============================================================================
# v3.3.3 STANDARDIZED QUALITY SCORING INTEGRATION
# ============================================================================

def get_quality_scorer():
    """Get v3.3.3 standardized quality scorer"""
    try:
        from factset_cli import StandardizedQualityScorer
        return StandardizedQualityScorer()
    except ImportError:
        # Fallback quality scorer
        return FallbackQualityScorer()

class FallbackQualityScorer:
    """Fallback quality scorer when StandardizedQualityScorer not available"""
    
    def __init__(self):
        self.scoring_version = "3.3.3-fallback"
    
    def calculate_score(self, data_metrics: Dict[str, Any]) -> int:
        """Calculate 0-10 fallback quality score"""
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
        if 9 <= score <= 10:
            return '🟢 完整'
        elif score == 8:
            return '🟡 良好'
        elif 3 <= score <= 7:
            return '🟠 部分'
        else:
            return '🔴 不足'

# ============================================================================
# FIXED #4: Proper module imports without circular dependencies
# ============================================================================

class LazyImporter:
    """Lazy module importer to avoid circular dependencies"""
    def __init__(self):
        self._modules = {}
    
    def get_module(self, name):
        if name not in self._modules:
            try:
                self._modules[name] = __import__(name)
            except ImportError as e:
                logger = get_v333_logger()
                logger.warning(f"Module {name} not available: {e}")
                self._modules[name] = None
        return self._modules[name]

# Global lazy importer
lazy_modules = LazyImporter()

# Enhanced imports with fallbacks
try:
    import validators
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False

try:
    from googlesearch import search
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    logger = get_v333_logger()
    logger.warning("googlesearch-python not installed. Install with: pip install googlesearch-python")
    GOOGLESEARCH_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    logger = get_v333_logger()
    logger.warning("beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
    BS4_AVAILABLE = False

try:
    from markdownify import markdownify as md
    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    MARKDOWNIFY_AVAILABLE = False

# ============================================================================
# ENHANCED SEARCH PATTERNS (v3.3.1) - Pre-compiled for performance
# ============================================================================

ENHANCED_SEARCH_PATTERNS = {
    'factset': [
        '{company_name} factset EPS 預估',
        '{company_name} {stock_code} factset 分析師',
        '{company_name} factset 目標價',
        '{company_name} factset 財報',
        'site:factset.com {company_name}'
    ],
    'financial': [
        '{company_name} {stock_code} EPS 預估 2025',
        '{company_name} 財報 分析師 預估',
        '{company_name} 目標價 投資建議',
        '{company_name} {stock_code} 券商報告',
        '{company_name} 每股盈餘 預測',
        '{company_name} 分析師 評等'
    ],
    'comprehensive': [
        '{company_name} {stock_code} 財務數據',
        '{company_name} 股價 分析',
        '{company_name} 投資評等',
        '{company_name} 營收 獲利 預估',
        '{company_name} 業績 展望',
        '{company_name} 財務 表現'
    ]
}

# Priority domains for better content quality
PRIORITY_DOMAINS = [
    'factset.com', 'moneydj.com', 'cnyes.com', 'yahoo.com',
    'investing.com', 'marketwatch.com', 'wealth.com.tw',
    'businessweekly.com.tw', 'commercial-times.com'
]

# Rate limiting exception for unified handling - FIXED #3
class RateLimitException(Exception):
    """Unified rate limiting exception for v3.3.3"""
    pass

# ============================================================================
# ENHANCED FILENAME GENERATION (v3.3.1) - FIXED #6
# ============================================================================

def generate_unique_filename_v331(company_name: str, stock_code: str, url: str, 
                                 search_index: int, content_preview: str = "", logger=None) -> str:
    """
    FIXED #6: Enhanced unique filename generation with collision prevention
    Format: {stock_code}_{company}_{domain}_{content_hash}_{timestamp}.md
    """
    if logger is None:
        logger = get_v333_logger()
    
    logger.debug(f"Generating filename for {company_name} ({stock_code})")
    
    # Clean components
    clean_company = clean_filename_component(company_name, 12)
    clean_stock = clean_filename_component(stock_code, 4) or 'XXXX'
    domain = extract_domain_info(url)
    
    # FIXED #6: Enhanced content-based hash for uniqueness
    content_identifier = f"{url}_{search_index}_{content_preview[:500]}_{datetime.now().microsecond}"
    content_hash = hashlib.sha256(content_identifier.encode()).hexdigest()[:8]  # Longer hash
    
    # Enhanced timestamp with microseconds for uniqueness
    timestamp = datetime.now().strftime("%m%d_%H%M%S_%f")[:15]  # Include microseconds
    
    # Build filename: stock_code first for better organization
    filename = f"{clean_stock}_{clean_company}_{domain}_{content_hash}_{timestamp}.md"
    
    # Ensure reasonable length
    if len(filename) > 200:
        filename = f"{clean_stock}_{clean_company[:6]}_{domain[:6]}_{content_hash}_{timestamp}.md"
    
    logger.debug(f"Generated filename: {filename}")
    return filename

def clean_filename_component(text: str, max_length: int = 15) -> str:
    """Clean text for use in filename with better Chinese support"""
    if not text:
        return "Unknown"
    
    # Keep Chinese characters, letters, numbers, and some symbols
    cleaned = re.sub(r'[^\w\u4e00-\u9fff\-]', '', str(text))
    return cleaned[:max_length] if cleaned else "Unknown"

def extract_domain_info(url: str) -> str:
    """Extract meaningful domain information from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '').lower()
        
        # Enhanced domain mapping
        domain_map = {
            'factset.com': 'factset',
            'moneydj.com': 'moneydj',
            'cnyes.com': 'cnyes',
            'yahoo.com': 'yahoo',
            'finance.yahoo.com': 'yahoo',
            'tw.stock.yahoo.com': 'yahoo',
            'investing.com': 'investing',
            'marketwatch.com': 'marketwatch',
            'reuters.com': 'reuters',
            'bloomberg.com': 'bloomberg',
            'wealth.com.tw': 'wealth',
            'businessweekly.com.tw': 'bw',
            'commercial-times.com': 'ctimes',
            'statementdog.com': 'statemen',
            'histock.tw': 'histock'
        }
        
        for full_domain, short_name in domain_map.items():
            if full_domain in domain:
                return short_name
        
        # Fallback to first part of domain
        return domain.split('.')[0][:8]
    except:
        return 'web'

# ============================================================================
# ENHANCED CONTENT QUALITY ASSESSMENT (v3.3.3) - Updated to 0-10 scale
# ============================================================================

def assess_content_quality_v333(content: str, title: str = "", logger=None) -> int:
    """
    v3.3.3: Enhanced content quality assessment using StandardizedQualityScorer
    Returns score 0-10 (10 being highest quality)
    """
    if logger is None:
        logger = get_v333_logger()
    
    if not content:
        return 0
    
    try:
        content_lower = content.lower()
        title_lower = title.lower()
        combined_text = f"{title_lower} {content_lower}"
        
        # Build quality metrics for StandardizedQualityScorer
        quality_metrics = {
            'eps_data_completeness': 0,
            'analyst_count': 0,
            'data_age_days': 0,
            'content_quality_factors': 0
        }
        
        # Assess EPS data completeness
        eps_indicators = ['eps', '每股盈餘', 'earnings per share', '2025', '2026', '2027']
        eps_found = sum(1 for indicator in eps_indicators if indicator in combined_text)
        quality_metrics['eps_data_completeness'] = min(1.0, eps_found / 6)
        
        # Assess analyst coverage indicators
        analyst_indicators = ['分析師', 'analyst', '券商', '研究報告', 'research']
        analyst_found = sum(1 for indicator in analyst_indicators if indicator in combined_text)
        quality_metrics['analyst_count'] = min(50, analyst_found * 10)  # Estimate
        
        # Assess data freshness (newer content gets better score)
        current_year = datetime.now().year
        year_indicators = [str(current_year), str(current_year - 1)]
        recent_mentions = sum(combined_text.count(year) for year in year_indicators)
        quality_metrics['data_age_days'] = max(1, 30 - (recent_mentions * 5))  # Estimate
        
        # Additional content quality factors
        quality_keywords = ['factset', 'target price', '目標價', 'forecast', '預測', 'estimate']
        quality_found = sum(1 for keyword in quality_keywords if keyword in combined_text)
        
        # Bonus for numerical data
        numeric_patterns = [r'\d+\.\d+', r'\$\d+', r'\d+%', r'NT\$\d+']
        numeric_found = sum(len(re.findall(pattern, content)) for pattern in numeric_patterns)
        
        # Penalty for low-quality content
        low_quality_indicators = ['廣告', 'advertisement', '購物', 'shop', '404', 'error']
        penalties = sum(1 for indicator in low_quality_indicators if indicator in combined_text)
        
        # Use StandardizedQualityScorer for final calculation
        quality_scorer = get_quality_scorer()
        
        # Adjust metrics based on content analysis
        if quality_found >= 3:
            quality_metrics['eps_data_completeness'] = min(1.0, quality_metrics['eps_data_completeness'] + 0.3)
        if numeric_found >= 5:
            quality_metrics['analyst_count'] = min(50, quality_metrics['analyst_count'] + 15)
        if len(content) > 2000:
            quality_metrics['data_age_days'] = max(1, quality_metrics['data_age_days'] - 10)
        
        # Apply penalties
        if penalties > 0:
            quality_metrics['eps_data_completeness'] = max(0, quality_metrics['eps_data_completeness'] - 0.2 * penalties)
        
        final_score = quality_scorer.calculate_score(quality_metrics)
        logger.debug(f"v3.3.3 content quality assessed: {final_score}/10")
        return final_score
        
    except Exception as e:
        logger.warning(f"Content quality assessment error: {e}")
        return 5  # Default middle score if assessment fails

# Legacy compatibility function
def assess_content_quality_v331(content: str, title: str = "", logger=None) -> int:
    """Legacy v3.3.1 compatibility - converts to v3.3.3 scale"""
    v333_score = assess_content_quality_v333(content, title, logger)
    # Convert 0-10 scale back to 1-10 for legacy compatibility
    return max(1, v333_score)

# ============================================================================
# ENHANCED URL VALIDATION (v3.3.1) - FIXED #1
# ============================================================================

def clean_and_validate_url_v331(url: str, logger=None) -> Optional[str]:
    """FIXED #1: Enhanced URL cleaning and validation with robust error handling"""
    if logger is None:
        logger = get_v333_logger()
    
    try:
        if not url or not isinstance(url, str):
            logger.debug(f"Invalid URL type: {type(url)}")
            return None
        
        url = str(url).strip()
        
        # FIXED #1: Length check first to prevent issues
        if len(url) > 2000:
            logger.warning(f"URL too long ({len(url)} chars), skipping")
            return None
        
        # Handle Google redirects
        if 'google.com' in url and '/url?q=' in url:
            try:
                match = re.search(r'/url\?q=([^&]+)', url)
                if match:
                    actual_url = unquote(match.group(1))
                    url = actual_url
                    logger.debug(f"Decoded Google redirect URL")
            except Exception as e:
                logger.warning(f"Google redirect handling failed: {e}")
                return None
        
        # Ensure proper protocol
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # FIXED #1: Enhanced URL encoding safety check
        try:
            # Test if URL can be encoded/decoded safely
            test_encode = quote(url, safe=':/?#[]@!$&\'()*+,;=')
            if len(test_encode) > 2000:
                logger.warning("URL too long after encoding, skipping")
                return None
        except Exception as e:
            logger.warning(f"URL encoding test failed: {e}")
            return None
        
        # Basic URL pattern validation
        if not re.match(r'https?://[^\s/$.?#].[^\s]*$', url):
            logger.warning("Invalid URL pattern, skipping")
            return None
        
        # Basic validation with validators if available
        if VALIDATORS_AVAILABLE:
            try:
                if not validators.url(url):
                    logger.debug("URL failed validators check")
                    return None
            except Exception:
                # If validation fails, continue anyway
                pass
        
        logger.debug(f"URL validated successfully: {url[:60]}...")
        return url
        
    except Exception as e:
        logger.warning(f"URL validation error: {e}")
        return None

# ============================================================================
# ENHANCED WEB CONTENT PROCESSING (v3.3.1) - FIXED #1
# ============================================================================

def download_webpage_content_enhanced_v331(url: str, timeout: int = 30, logger=None) -> Tuple[Optional[str], Optional[str], int]:
    """
    FIXED #1: Enhanced webpage content download with robust error handling
    Prevents single bad URL from killing entire search
    """
    if logger is None:
        logger = get_v333_logger()
    
    try:
        logger.debug(f"Downloading: {url[:60]}...")
        
        # FIXED #1: URL length check
        if len(url) > 2000:
            logger.warning(f"URL too long, skipping: {len(url)} chars")
            return None, None, 0
        
        # Enhanced headers for better access
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Request with timeout
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        # FIXED #3: Enhanced rate limiting detection for unified handling
        if response.status_code == 429:
            logger.warning("Rate limiting detected (429)")
            raise RateLimitException("429 Too Many Requests")
        
        if 'rate limit' in response.text.lower() or 'too many requests' in response.text.lower():
            logger.warning("Rate limiting detected in content")
            raise RateLimitException("Rate limiting in response content")
        
        response.raise_for_status()
        
        # FIXED #1: CRITICAL FIX - Robust character encoding handling
        content = None
        encoding_used = 'unknown'
        
        try:
            # Strategy 1: Use response encoding
            if response.encoding:
                try:
                    content = response.content.decode(response.encoding, errors='replace')
                    encoding_used = response.encoding
                except (UnicodeDecodeError, LookupError):
                    content = None
            
            # Strategy 2: Try apparent encoding
            if content is None and hasattr(response, 'apparent_encoding') and response.apparent_encoding:
                try:
                    content = response.content.decode(response.apparent_encoding, errors='replace')
                    encoding_used = response.apparent_encoding
                except (UnicodeDecodeError, LookupError):
                    content = None
            
            # Strategy 3: UTF-8 with replacement
            if content is None:
                try:
                    content = response.content.decode('utf-8', errors='replace')
                    encoding_used = 'utf-8'
                except UnicodeDecodeError:
                    content = None
            
            # Strategy 4: Latin-1 (last resort - always works)
            if content is None:
                content = response.content.decode('latin-1', errors='replace')
                encoding_used = 'latin-1'
                logger.warning("Using latin-1 encoding as fallback")
            
            if '�' in content:
                logger.warning(f"Some characters replaced due to encoding issues ({encoding_used})")
            
        except Exception as encoding_error:
            logger.error(f"Critical encoding error: {encoding_error}")
            return None, None, 0
        
        # Content validation
        if not content or len(content) < 100:
            logger.warning(f"Content too short: {len(content) if content else 0} chars")
            return None, None, 0
        
        # HTML processing with enhanced error handling
        if not BS4_AVAILABLE:
            quality_score = assess_content_quality_v333(content, logger=logger)
            return content, content, quality_score
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Enhanced content extraction
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "advertisement"]):
                element.decompose()
            
            # Extract title for quality assessment
            title = soup.title.string if soup.title else ""
            
            # Get main content
            text_content = soup.get_text()
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)  # Clean whitespace
            text_content = text_content.strip()
            
            # Convert to markdown if available
            if MARKDOWNIFY_AVAILABLE:
                try:
                    markdown_content = md(str(soup), heading_style="ATX")
                except Exception as md_error:
                    logger.warning(f"Markdown conversion failed: {md_error}")
                    markdown_content = text_content
            else:
                markdown_content = text_content
            
            # v3.3.3: Assess content quality using new scoring system
            quality_score = assess_content_quality_v333(text_content, title, logger=logger)
            
            logger.info(f"Downloaded: {len(text_content)} chars, quality: {quality_score}/10")
            return markdown_content, text_content, quality_score
            
        except Exception as html_error:
            logger.warning(f"HTML processing error: {html_error}")
            # Fallback to raw content
            quality_score = assess_content_quality_v333(content, logger=logger)
            return content, content, quality_score
        
    except RateLimitException:
        # Re-raise rate limiting exceptions for unified handling
        raise
    except requests.exceptions.Timeout:
        logger.warning(f"Download timeout: {url[:60]}")
        return None, None, 0
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error: {url[:60]}")
        return None, None, 0
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error: {e}")
        return None, None, 0
    except Exception as e:
        logger.warning(f"Unexpected download error: {e}")
        return None, None, 0

# ============================================================================
# ENHANCED COMPANY EXTRACTION (v3.3.1)
# ============================================================================

def extract_company_info_enhanced_v331(title: str, url: str, snippet: str = "", 
                                      watchlist_df=None, logger=None) -> Tuple[Optional[str], Optional[str]]:
    """Enhanced company name and stock code extraction for v3.3.1"""
    if logger is None:
        logger = get_v333_logger()
    
    company_name = None
    stock_code = None
    
    # Combine all available text
    text_to_analyze = f"{title} {snippet} {url}".lower()
    logger.debug(f"Extracting company info from: {text_to_analyze[:100]}...")
    
    # Enhanced stock code patterns
    stock_patterns = [
        r'\((\d{4})\)',      # (2330)
        r'(\d{4})\.tw',      # 2330.tw
        r'(\d{4})-tw',       # 2330-tw
        r'(\d{4})\.tpe',     # 2330.tpe
        r'/(\d{4})/',        # /2330/ in URL
        r'stock/(\d{4})',    # stock/2330
        r'code[=:](\d{4})',  # code=2330
    ]
    
    for pattern in stock_patterns:
        match = re.search(pattern, text_to_analyze)
        if match:
            code = match.group(1)
            if len(code) == 4 and code.isdigit():
                stock_code = code
                logger.debug(f"Extracted stock code: {code}")
                break
    
    # Enhanced company name patterns with more Taiwan companies
    company_patterns = [
        r'(台積電|台灣積體電路|tsmc)',
        r'(聯發科|mediatek|mtk)',
        r'(富邦金|fubon)',
        r'(鴻海|hon hai|foxconn)',
        r'(台達電|delta)',
        r'(光寶科|lite-on)',
        r'(聯電|umc)',
        r'(廣達|quanta)',
        r'(華碩|asus)',
        r'(宏碁|acer)',
        r'(緯創|wistron)',
        r'(仁寶|compal)',
        r'(和碩|pegatron)',
        r'(日月光|ase)',
        r'(矽品|spil)',
        r'(欣興|unimicron)',
        r'(南亞科|nanya)',
        r'(群聯|phison)',
        r'(瑞昱|realtek)',
        r'(吉茂)',
        r'(統一|uni-president)',
        r'(中華電|chunghwa telecom)',
        r'(台塑|formosa)',
        r'(中鋼|china steel)',
        r'(長榮|evergreen)',
        r'(陽明|yang ming)',
        r'(所羅門)',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text_to_analyze)
        if match:
            # Take the first (usually Chinese) name
            company_name = match.group(1).split('|')[0]
            logger.debug(f"Extracted company name: {company_name}")
            break
    
    # Use watchlist for validation if available
    if watchlist_df is not None and stock_code:
        try:
            match = watchlist_df[watchlist_df['代號'].astype(str) == stock_code]
            if not match.empty:
                watchlist_name = match.iloc[0]['名稱']
                if not company_name or len(watchlist_name) > len(company_name):
                    company_name = watchlist_name
                    logger.debug(f"Company name updated from watchlist: {company_name}")
        except Exception as e:
            logger.warning(f"Error accessing watchlist: {e}")
    
    # Fallback: stock code to company mapping
    if stock_code and not company_name:
        stock_to_company = {
            '2330': '台積電', '2454': '聯發科', '2881': '富邦金', '2317': '鴻海',
            '2308': '台達電', '2301': '光寶科', '2303': '聯電', '2382': '廣達',
            '2357': '華碩', '2353': '宏碁', '3231': '緯創', '2324': '仁寶',
            '4938': '和碩', '2311': '日月光', '2325': '矽品', '3037': '欣興',
            '2408': '南亞科', '8299': '群聯', '2379': '瑞昱', '1587': '吉茂',
            '1216': '統一', '2412': '中華電', '1301': '台塑', '2002': '中鋼',
            '2603': '長榮', '2609': '陽明', '2359': '所羅門'
        }
        company_name = stock_to_company.get(stock_code)
        if company_name:
            logger.debug(f"Company name from fallback mapping: {company_name}")
    
    return company_name, stock_code

# ============================================================================
# ENHANCED FILE SAVING (v3.3.1)
# ============================================================================

def save_content_to_md_file_v331(content: str, filename: str, md_dir: str, 
                                metadata: Dict = None, logger=None) -> bool:
    """Save content to MD file with enhanced metadata for v3.3.1"""
    if logger is None:
        logger = get_v333_logger()
    
    try:
        os.makedirs(md_dir, exist_ok=True)
        filepath = os.path.join(md_dir, filename)
        
        # FIXED #6: Check if file already exists with same content hash
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # Compare content hash to prevent true duplicates
                existing_hash = hashlib.md5(existing_content.encode()).hexdigest()
                new_hash = hashlib.md5(content.encode()).hexdigest()
                
                if existing_hash == new_hash:
                    logger.info(f"Identical content exists: {filename}")
                    return True  # Don't overwrite identical content
            except Exception:
                pass  # If we can't read existing file, proceed with save
        
        # Prepare content with enhanced metadata header
        if metadata:
            header = "---\n"
            header += f"url: {metadata.get('url', '')}\n"
            header += f"title: {metadata.get('title', '')}\n"
            header += f"quality_score: {metadata.get('quality_score', 0)}\n"
            header += f"company: {metadata.get('company', '')}\n"
            header += f"stock_code: {metadata.get('stock_code', '')}\n"
            header += f"extracted_date: {datetime.now().isoformat()}\n"
            header += f"search_query: {metadata.get('query', '')}\n"
            header += f"version: v3.3.3\n"
            header += "---\n\n"
            
            final_content = header + content
        else:
            final_content = content
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        logger.debug(f"Saved MD file: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving file {filename}: {e}")
        return False

# ============================================================================
# ENHANCED SEARCH EXECUTION (v3.3.1) - FIXED #1
# ============================================================================

def search_company_factset_data_v331(company_name: str, stock_code: str, 
                                    search_type: str = 'factset', 
                                    max_results: int = 10,
                                    watchlist_df=None,
                                    rate_protector=None,
                                    logger=None) -> List[Dict]:
    """
    FIXED #1: Enhanced search with proper error isolation per URL
    Prevents single bad URL from killing entire company search
    """
    if logger is None:
        logger = get_v333_logger()
    
    if not GOOGLESEARCH_AVAILABLE:
        logger.error(f"Google search not available for {company_name}")
        return []
    
    results = []
    patterns = ENHANCED_SEARCH_PATTERNS.get(search_type, ENHANCED_SEARCH_PATTERNS['factset'])
    
    max_results = max(1, min(20, int(max_results)))
    
    # v3.3.3 Performance monitoring
    perf_monitor = get_performance_monitor()
    
    with perf_monitor.time_operation(f"search_company_{company_name}"):
        for pattern_index, pattern in enumerate(patterns):
            try:
                # Format search query
                query = pattern.format(
                    company_name=company_name,
                    stock_code=stock_code or ''
                ).strip()
                
                logger.info(f"Search {pattern_index + 1}/{len(patterns)}: {query}")
                
                # FIXED #3: Use rate protector if available
                if rate_protector:
                    rate_protector.record_request()
                
                # Perform search with enhanced error handling
                try:
                    num_results_per_pattern = min(5, max(1, max_results // len(patterns)))
                    
                    search_results = search(
                        query,
                        num_results=num_results_per_pattern,
                        lang='zh-TW',
                        sleep_interval=1
                    )
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # FIXED #3: Enhanced rate limiting detection for unified handling
                    if any(keyword in error_str for keyword in [
                        "429", "too many requests", "blocked", "rate limit", 
                        "quota", "sorry/index", "temporarily unavailable"
                    ]):
                        logger.warning(f"RATE LIMITING DETECTED: {e}")
                        if rate_protector:
                            rate_protector.record_429_error()
                        raise RateLimitException(f"Search API rate limiting: {e}")
                    else:
                        logger.warning(f"Search error for pattern: {e}")
                        continue  # FIXED #1: Skip this pattern, continue with others
                
                # FIXED #1: Process results with individual URL error handling
                for i, url in enumerate(search_results):
                    try:
                        # Clean and validate URL
                        clean_url = clean_and_validate_url_v331(url, logger=logger)
                        if not clean_url:
                            logger.debug(f"Invalid URL skipped: {url[:60]}...")
                            continue  # FIXED #1: Skip this URL, continue with others
                        
                        # Skip duplicates
                        if any(r['url'] == clean_url for r in results):
                            continue
                        
                        # Add delay between requests
                        if i > 0:
                            time.sleep(1)
                        
                        # FIXED #1: Download with individual error handling
                        try:
                            markdown_content, text_content, quality_score = download_webpage_content_enhanced_v331(
                                clean_url, logger=logger
                            )
                        except RateLimitException as e:
                            logger.warning("Rate limiting during download")
                            if rate_protector:
                                rate_protector.record_429_error()
                            raise  # Re-raise rate limiting for unified handling
                        except Exception as download_error:
                            logger.warning(f"Download failed: {clean_url[:60]} - {download_error}")
                            continue  # FIXED #1: Skip this download, continue with others
                        
                        # v3.3.3: Updated quality threshold for 0-10 scale
                        if not markdown_content or not text_content or quality_score < 3:
                            logger.debug(f"Low quality content skipped (score: {quality_score}/10)")
                            continue
                        
                        # Extract enhanced company info
                        detected_company, detected_stock = extract_company_info_enhanced_v331(
                            clean_url, clean_url, text_content[:500], watchlist_df, logger=logger
                        )
                        
                        # FIXED #6: Generate enhanced unique filename
                        filename = generate_unique_filename_v331(
                            detected_company or company_name,
                            detected_stock or stock_code,
                            clean_url,
                            i,
                            text_content[:200],
                            logger=logger
                        )
                        
                        results.append({
                            'title': clean_url[:100],
                            'url': clean_url,
                            'snippet': text_content[:300],
                            'content': markdown_content,
                            'quality_score': quality_score,
                            'detected_company': detected_company or company_name,
                            'detected_stock_code': detected_stock or stock_code,
                            'filename': filename,
                            'query': query,
                            'search_type': search_type,
                            'content_length': len(text_content),
                            'v333_scored': True  # v3.3.3 marker
                        })
                        
                        logger.info(f"Quality content found: {filename} (score: {quality_score}/10)")
                        
                        # FIXED #3: Record success with rate protector
                        if rate_protector:
                            rate_protector.record_success()
                        
                    except Exception as url_error:
                        logger.warning(f"URL processing error: {url_error}")
                        continue  # FIXED #1: Skip this URL, continue with others
                
                # Delay between patterns
                time.sleep(2)
                
            except RateLimitException:
                logger.warning("Rate limiting - stopping search for this company")
                break  # Stop searching for this company due to rate limiting
            except Exception as pattern_error:
                logger.warning(f"Pattern error: {pattern_error}")
                continue  # FIXED #1: Skip this pattern, continue with others
    
    # Sort by quality score and return best results
    results.sort(key=lambda x: x['quality_score'], reverse=True)
    final_results = results[:max_results]
    logger.info(f"Search completed for {company_name}: {len(final_results)} quality results")
    return final_results

# ============================================================================
# ENHANCED BATCH PROCESSING (v3.3.1) - FIXED #1
# ============================================================================

def process_company_search_v331(company_data: Dict, config: Dict, 
                               search_type: str = 'factset',
                               watchlist_df=None,
                               rate_protector=None,
                               logger=None) -> Dict:
    """
    FIXED #1: Enhanced company search processing with proper error isolation
    Each company failure is isolated and doesn't affect other companies
    """
    if logger is None:
        logger = get_v333_logger()
    
    company_name = company_data.get('name', company_data.get('名稱', ''))
    stock_code = company_data.get('code', company_data.get('代號', ''))
    
    logger.info(f"Searching {company_name} ({stock_code}) - v3.3.3")
    
    try:
        search_results = search_company_factset_data_v331(
            company_name, 
            stock_code, 
            search_type,
            config.get('search', {}).get('max_results', 10),
            watchlist_df,
            rate_protector,
            logger
        )
    except RateLimitException as e:
        logger.warning(f"Rate limiting for {company_name}: {e}")
        return {
            'company': company_name,
            'stock_code': stock_code,
            'search_type': search_type,
            'results': [],
            'files_saved': 0,
            'success': False,
            'rate_limited': True,
            'error': str(e),
            'v333_processed': True
        }
    except Exception as e:
        logger.error(f"Search error for {company_name}: {e}")
        return {
            'company': company_name,
            'stock_code': stock_code,
            'search_type': search_type,
            'results': [],
            'files_saved': 0,
            'success': False,
            'rate_limited': False,
            'error': str(e),
            'v333_processed': True
        }
    
    if not search_results:
        logger.warning(f"No quality results found for {company_name}")
        return {
            'company': company_name,
            'stock_code': stock_code,
            'search_type': search_type,
            'results': [],
            'files_saved': 0,
            'success': False,
            'rate_limited': False,
            'v333_processed': True
        }
    
    # Save content to MD files with enhanced error handling
    md_dir = config['output']['md_dir']
    files_saved = 0
    
    for result in search_results:
        try:
            filename = result['filename']
            content = result['content']
            
            metadata = {
                'url': result['url'],
                'title': result.get('title', ''),
                'quality_score': result['quality_score'],
                'company': result['detected_company'],
                'stock_code': result['detected_stock_code'],
                'query': result['query'],
                'v333_scored': True
            }
            
            if save_content_to_md_file_v331(content, filename, md_dir, metadata, logger=logger):
                files_saved += 1
                logger.info(f"Saved: {filename}")
            
        except Exception as e:
            logger.warning(f"Error saving result: {e}")
            continue  # FIXED #1: Continue with other files even if one save fails
    
    success = files_saved > 0
    logger.info(f"{company_name}: {files_saved} files saved")
    
    return {
        'company': company_name,
        'stock_code': stock_code,
        'search_type': search_type,
        'results': search_results,
        'files_saved': files_saved,
        'success': success,
        'rate_limited': False,
        'v333_processed': True
    }

# ============================================================================
# MAIN ENHANCED SEARCH SUITE (v3.3.1) - FIXED #1, #3, #9
# ============================================================================

def run_enhanced_search_suite_v331(config: Dict, search_types: Optional[List[str]] = None, 
                                  priority_focus: str = "balanced",
                                  rate_protector=None,
                                  logger=None) -> bool:
    """
    FIXED #1: Enhanced search suite with proper error isolation
    FIXED #3: Unified rate limiting integration
    FIXED #9: Memory management with batching
    v3.3.3: Enhanced logging integration + quality scoring
    """
    if logger is None:
        logger = get_v333_logger()
    
    logger.info(f"Enhanced Search Suite v{__version__} (v3.3.3)")
    logger.info(f"Date: {__date__}")
    logger.info("FIXED: #1 Cascade failures, #3 Rate limiting, #9 Memory management")
    logger.info("v3.3.3: Enhanced logging, CLI integration, and standardized quality scoring")
    logger.info("=" * 80)
    
    # v3.3.3 Performance monitoring
    perf_monitor = get_performance_monitor()
    
    with perf_monitor.time_operation("enhanced_search_suite"):
        # Validate dependencies
        missing_deps = []
        if not GOOGLESEARCH_AVAILABLE:
            missing_deps.append('googlesearch-python')
        if not BS4_AVAILABLE:
            missing_deps.append('beautifulsoup4')
        
        if missing_deps:
            logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
            return False
        
        # Load target companies
        target_companies = config.get('target_companies', [])
        if not target_companies:
            logger.error("No target companies found in configuration")
            return False
        
        # Load watchlist for better company matching
        try:
            import pandas as pd
            watchlist_df = pd.read_csv('觀察名單.csv') if os.path.exists('觀察名單.csv') else None
            if watchlist_df is not None:
                logger.info(f"Loaded watchlist: {len(watchlist_df)} companies")
        except Exception as e:
            logger.warning(f"Could not load watchlist: {e}")
            watchlist_df = None
        
        # Apply priority focus
        if priority_focus == "high_only":
            target_companies = target_companies[:10]
            logger.info(f"High priority focus: {len(target_companies)} companies")
        elif priority_focus == "top_30":
            target_companies = target_companies[:30]
            logger.info(f"Top 30 focus: {len(target_companies)} companies")
        else:
            logger.info(f"Balanced approach: {len(target_companies)} companies")
        
        # Set up search types
        if search_types is None:
            search_types = ['factset', 'financial']
        
        # Create output directories
        os.makedirs(config['output']['md_dir'], exist_ok=True)
        os.makedirs(config['output']['csv_dir'], exist_ok=True)
        
        # FIXED #9: Process companies with memory management and batching
        total_files_saved = 0
        successful_companies = 0
        rate_limiting_detected = False
        quality_scores = []  # v3.3.3: Track quality scores
        
        # FIXED #9: Process in batches to manage memory
        batch_size = config.get('search', {}).get('batch_size', 20)
        
        for search_type in search_types:
            logger.info(f"SEARCH TYPE: {search_type.upper()}")
            logger.info("="*40)
            
            try:
                # FIXED #9: Process companies in batches
                for batch_start in range(0, len(target_companies), batch_size):
                    batch_end = min(batch_start + batch_size, len(target_companies))
                    batch_companies = target_companies[batch_start:batch_end]
                    
                    logger.info(f"Processing batch {batch_start//batch_size + 1}: companies {batch_start+1}-{batch_end}")
                    
                    for i, company in enumerate(batch_companies):
                        company_index = batch_start + i + 1
                        logger.info(f"[{company_index}/{len(target_companies)}] Processing company...")
                        
                        try:
                            result = process_company_search_v331(
                                company, config, search_type, watchlist_df, rate_protector, logger
                            )
                            
                            # FIXED #1: Check for rate limiting but don't stop entire batch
                            if result.get('rate_limited'):
                                logger.warning("Rate limiting detected - STOPPING SEARCH")
                                rate_limiting_detected = True
                                break
                            
                            if result['success']:
                                successful_companies += 1
                                total_files_saved += result['files_saved']
                                
                                # v3.3.3: Collect quality scores
                                for search_result in result.get('results', []):
                                    if 'quality_score' in search_result:
                                        quality_scores.append(search_result['quality_score'])
                            else:
                                logger.warning(f"Company {company.get('name', 'Unknown')} failed - continuing")
                            
                            # Rate limiting between companies
                            if company_index < len(target_companies):
                                time.sleep(2)
                                
                        except RateLimitException as e:
                            logger.warning(f"Rate limiting at company {company_index}: {e}")
                            rate_limiting_detected = True
                            break
                        except Exception as e:
                            logger.error(f"Error processing company {company_index}: {e}")
                            continue  # FIXED #1: Continue with next company
                    
                    # FIXED #9: Memory cleanup after each batch
                    gc.collect()
                    logger.info(f"Batch {batch_start//batch_size + 1} completed, memory cleaned")
                    
                    if rate_limiting_detected:
                        break
                
                if rate_limiting_detected:
                    break
                    
            except Exception as e:
                logger.error(f"Search type {search_type} failed: {e}")
                continue  # FIXED #1: Continue with next search type
    
    # Enhanced summary with v3.3.3 quality metrics
    logger.info("="*80)
    logger.info("ENHANCED SEARCH SUITE SUMMARY (v3.3.3)")
    logger.info("="*80)
    logger.info(f"Companies processed: {successful_companies}/{len(target_companies)}")
    logger.info(f"Total MD files saved: {total_files_saved}")
    
    # v3.3.3: Quality analysis
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        quality_scorer = get_quality_scorer()
        quality_distribution = {}
        
        for score in quality_scores:
            indicator = quality_scorer.get_quality_indicator(score)
            quality_distribution[indicator] = quality_distribution.get(indicator, 0) + 1
        
        logger.info(f"Average quality score: {avg_quality:.1f}/10")
        logger.info("Quality distribution:")
        for indicator, count in quality_distribution.items():
            logger.info(f"   {indicator}: {count}")
    
    if rate_limiting_detected:
        logger.warning("Rate limiting detected - search stopped early")
        logger.info(f"Recommendation: Process existing {total_files_saved} files")
        return "rate_limited"
    elif total_files_saved > 0:
        logger.info("Search completed successfully")
        return True
    else:
        logger.warning("No files saved - check search parameters")
        return False

# ============================================================================
# v3.3.3 CLI INTEGRATION FUNCTIONS
# ============================================================================

def run_enhanced_search_v333(config: Dict, **kwargs) -> bool:
    """v3.3.3 CLI integration function for enhanced search"""
    logger = get_v333_logger()
    
    # Extract CLI parameters
    mode = kwargs.get('mode', 'enhanced')
    priority = kwargs.get('priority', 'high_only')
    max_results = kwargs.get('max_results', 10)
    
    logger.info(f"Starting v3.3.3 enhanced search - mode: {mode}, priority: {priority}")
    
    # Create rate protector
    try:
        # Import and create unified rate protector
        factset_pipeline = lazy_modules.get_module('factset_pipeline')
        if factset_pipeline and hasattr(factset_pipeline, 'UnifiedRateLimitProtector'):
            rate_protector = factset_pipeline.UnifiedRateLimitProtector(config)
        else:
            rate_protector = None
    except Exception as e:
        logger.warning(f"Could not create rate protector: {e}")
        rate_protector = None
    
    # Update config with CLI parameters
    search_config = config.copy()
    search_config.setdefault('search', {})
    search_config['search']['max_results'] = max_results
    
    # Run enhanced search
    try:
        result = run_enhanced_search_suite_v331(
            search_config,
            search_types=['factset', 'financial'] if mode == 'enhanced' else ['factset'],
            priority_focus=priority,
            rate_protector=rate_protector,
            logger=logger
        )
        
        if result == "rate_limited":
            logger.warning("Search stopped due to rate limiting")
            return "rate_limited"
        elif result:
            logger.info("Enhanced search completed successfully")
            return True
        else:
            logger.error("Enhanced search failed")
            return False
            
    except Exception as e:
        logger.error(f"Enhanced search error: {e}")
        return False

# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ============================================================================

# Maintain backward compatibility with v3.3.2
def run_enhanced_search_v332(config: Dict, **kwargs) -> bool:
    """Legacy v3.3.2 compatibility wrapper"""
    return run_enhanced_search_v333(config, **kwargs)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for v3.3.3 search with comprehensive fixes"""
    logger = get_v333_logger()
    logger.info(f"Enhanced Search Module v{__version__} (v3.3.3)")
    logger.info("COMPREHENSIVE FIXES:")
    logger.info("   ✅ #1 Cascade failure protection")
    logger.info("   ✅ #3 Unified rate limiting")  
    logger.info("   ✅ #6 Enhanced filename generation")
    logger.info("   ✅ #9 Memory management with batching")
    logger.info("   ✅ v3.3.3 Standardized quality scoring (0-10)")
    logger.info("   ✅ v3.3.3 Enhanced logging integration")
    
    try:
        # FIXED #4: Lazy import config to avoid circular dependencies
        config_module = lazy_modules.get_module('config')
        if config_module and hasattr(config_module, 'load_config_v332'):
            config = config_module.load_config_v332()
        else:
            # Fallback configuration
            config = {
                'target_companies': [],
                'output': {
                    'csv_dir': 'data/csv',
                    'md_dir': 'data/md'
                },
                'search': {
                    'max_results': 10,
                    'batch_size': 20
                }
            }
    except Exception as e:
        logger.warning(f"Config loading error: {e}")
        return False
    
    # FIXED #3: Create unified rate protector
    try:
        factset_pipeline = lazy_modules.get_module('factset_pipeline')
        if factset_pipeline and hasattr(factset_pipeline, 'UnifiedRateLimitProtector'):
            rate_protector = factset_pipeline.UnifiedRateLimitProtector(config)
        else:
            rate_protector = None
    except Exception as e:
        logger.warning(f"Rate protector creation error: {e}")
        rate_protector = None
    
    result = run_enhanced_search_suite_v331(config, rate_protector=rate_protector, logger=logger)
    
    if result == "rate_limited":
        logger.warning("Search stopped due to rate limiting")
        return "rate_limited"
    elif result:
        logger.info("Search completed successfully")
        return True
    else:
        logger.error("Search failed")
        return False

if __name__ == "__main__":
    main()