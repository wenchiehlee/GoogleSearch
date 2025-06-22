"""
factset_search.py - Enhanced Google Search Module with URL Parsing and Rate Limiting Protection

Version: 3.2.0-ENHANCED
Date: 2025-06-22
Author: Google Search FactSet Pipeline - Enhanced Architecture

MAJOR ENHANCEMENTS:
- ✅ Robust URL parsing and validation with error recovery
- ✅ Enhanced SSL error handling and fallback strategies
- ✅ Immediate rate limiting detection and response
- ✅ Comprehensive error recovery for malformed URLs
- ✅ Enhanced retry logic with exponential backoff
- ✅ Better handling of Google redirect URLs

Description:
    Enhanced Google search module for finding FactSet financial data:
    - Robust URL parsing and validation
    - Enhanced SSL error handling
    - Immediate rate limiting detection
    - Comprehensive error recovery
    - Anti-overwrite protection with unique naming
    - Improved company name extraction

Dependencies:
    - googlesearch-python
    - requests
    - beautifulsoup4
    - validators (optional)
    - markdownify
"""

import os
import re
import time
import json
import hashlib
import traceback
import requests
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, quote_plus, unquote
from typing import List, Dict, Optional, Tuple

# Enhanced imports
try:
    import validators
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False

try:
    from googlesearch import search
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    print("⚠️ googlesearch-python not installed. Install with: pip install googlesearch-python")
    GOOGLESEARCH_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    print("⚠️ beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
    BS4_AVAILABLE = False

try:
    from markdownify import markdownify as md
    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    print("⚠️ markdownify not installed. Install with: pip install markdownify")
    MARKDOWNIFY_AVAILABLE = False

# Import local modules
try:
    import utils
    import config as config_module
except ImportError as e:
    print(f"⚠️ Could not import local modules: {e}")

# Version Information
__version__ = "3.2.0-ENHANCED"
__date__ = "2025-06-22"
__author__ = "Google Search FactSet Pipeline - Enhanced URL Handling"

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

# Search patterns for different types
SEARCH_PATTERNS = {
    'factset': [
        '{company_name} factset EPS 預估',
        '{company_name} {stock_code} factset 分析師',
        '{company_name} factset 目標價',
        'site:factset.com {company_name}'
    ],
    'financial': [
        '{company_name} {stock_code} EPS 預估 2025',
        '{company_name} 財報 分析師 預估',
        '{company_name} 目標價 投資建議',
        '{company_name} {stock_code} 券商報告'
    ],
    'missing': [
        '{company_name} {stock_code} 財務數據',
        '{company_name} 股價 分析',
        '{company_name} 投資評等',
        '{company_name} 營收 獲利 預估'
    ]
}

# Domains to prioritize
PRIORITY_DOMAINS = [
    'factset.com',
    'moneydj.com',
    'cnyes.com',
    'yahoo.com',
    'investing.com',
    'marketwatch.com'
]

# Rate limiting settings
SEARCH_DELAY = 2  # seconds between searches
REQUEST_DELAY = 1  # seconds between requests
MAX_RETRIES = 3

# Enhanced error tracking
class RateLimitException(Exception):
    """Custom exception for rate limiting detection"""
    pass

# ============================================================================
# ENHANCED URL VALIDATION AND CLEANING
# ============================================================================

def is_valid_url(url):
    """Enhanced URL validation with comprehensive checks"""
    try:
        # Basic URL validation
        if not url or not isinstance(url, str):
            return False
        
        # Remove any extra whitespace
        url = url.strip()
        
        # Check if it starts with http or https
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check for obvious malformed patterns
        malformed_patterns = [
            r'https?://[^/]*google[^/]*/url\?.*url=.*url=',  # Double-encoded Google URLs
            r'https?://.*\s+https?://',  # Multiple URLs concatenated
            r'https?://[^/]*\?[^=]*=https?%3A%2F%2F.*%3Fq%3D',  # Complex Google redirects
        ]
        
        for pattern in malformed_patterns:
            if re.search(pattern, url):
                print(f"   ⚠️ Detected malformed URL pattern: {url[:100]}...")
                return False
        
        # Use validators library if available
        if VALIDATORS_AVAILABLE:
            try:
                return validators.url(url)
            except Exception:
                pass
        
        # Fallback validation using urlparse
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme and '.' in parsed.netloc)
        except Exception:
            return False
            
    except Exception as e:
        print(f"   ⚠️ URL validation error: {e}")
        return False

def clean_and_validate_url(url):
    """Enhanced URL cleaning with comprehensive error handling"""
    try:
        if not url:
            return None
            
        # Remove any extra whitespace and newlines
        url = str(url).strip().replace('\n', '').replace('\r', '').replace('\t', '')
        
        # Handle common Google search URL issues
        if 'google.com' in url and '/url?q=' in url:
            try:
                # Extract the actual URL from Google redirect
                match = re.search(r'/url\?q=([^&]+)', url)
                if match:
                    actual_url = unquote(match.group(1))
                    print(f"   🔄 Extracted from Google redirect: {actual_url[:60]}...")
                    url = actual_url
                else:
                    # Try alternative patterns
                    alt_patterns = [
                        r'[?&]url=([^&]+)',
                        r'[?&]q=([^&]+)',
                        r'/url\?.*?url=([^&]+)'
                    ]
                    
                    for pattern in alt_patterns:
                        match = re.search(pattern, url)
                        if match:
                            actual_url = unquote(match.group(1))
                            print(f"   🔄 Alternative extraction: {actual_url[:60]}...")
                            url = actual_url
                            break
                    else:
                        print(f"   ⚠️ Could not extract URL from Google redirect: {url[:100]}...")
                        return None
            except Exception as e:
                print(f"   ⚠️ Error extracting from Google URL: {e}")
                return None
        
        # Handle multiple concatenated URLs
        if url.count('http') > 1:
            # Take the first valid URL
            urls = re.findall(r'https?://[^\s]+', url)
            if urls:
                url = urls[0]
                print(f"   🔧 Fixed multiple URLs, using first: {url[:60]}...")
        
        # Handle encoded URLs
        if '%' in url:
            try:
                decoded_url = unquote(url)
                # Only use decoded version if it's still valid
                if is_valid_url(decoded_url):
                    url = decoded_url
                    print(f"   🔄 URL decoded successfully")
            except Exception as e:
                print(f"   ⚠️ URL decoding failed: {e}")
        
        # Ensure URL has proper protocol
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Clean up common issues
        url = url.replace(' ', '%20')  # Replace spaces
        url = re.sub(r'([^:])//+', r'\1/', url)  # Remove double slashes except after protocol
        
        # Final validation
        if not is_valid_url(url):
            print(f"   ❌ URL failed final validation: {url[:60]}...")
            return None
            
        return url
        
    except Exception as e:
        print(f"   ⚠️ URL cleaning error: {e}")
        return None

def safe_request_with_retries(url, max_retries=3, timeout=30):
    """Enhanced HTTP request with comprehensive error handling and retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    for attempt in range(max_retries):
        try:
            # Clean URL before request
            clean_url = clean_and_validate_url(url)
            if not clean_url:
                raise ValueError(f"Invalid URL after cleaning: {url}")
            
            print(f"   📡 Attempting request ({attempt + 1}/{max_retries}): {clean_url[:60]}...")
            
            response = requests.get(
                clean_url, 
                headers=headers, 
                timeout=timeout,
                allow_redirects=True,
                verify=True  # SSL verification
            )
            
            # Enhanced rate limiting detection
            if response.status_code == 429:
                print(f"   🚨 Rate limiting detected (429) for {clean_url[:60]}...")
                raise RateLimitException("429 Too Many Requests")
            
            # Check for rate limiting in response content
            if response.status_code == 503 or 'rate limit' in response.text.lower() or 'too many requests' in response.text.lower():
                print(f"   🚨 Rate limiting detected in content for {clean_url[:60]}...")
                raise RateLimitException("Rate limiting detected in response content")
            
            response.raise_for_status()
            print(f"   ✅ Request successful: {response.status_code}")
            return response
            
        except RateLimitException:
            # Don't retry rate limiting - raise immediately
            print(f"   🛑 Rate limiting detected - stopping requests")
            raise
            
        except requests.exceptions.SSLError as e:
            print(f"   🔒 SSL Error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Try without SSL verification as fallback
                try:
                    print(f"   🔄 Retrying without SSL verification...")
                    response = requests.get(
                        clean_url, 
                        headers=headers, 
                        timeout=timeout,
                        allow_redirects=True,
                        verify=False  # Disable SSL verification
                    )
                    
                    # Still check for rate limiting
                    if response.status_code == 429:
                        raise RateLimitException("429 Too Many Requests")
                    
                    response.raise_for_status()
                    print(f"   ⚠️ Connected without SSL verification")
                    return response
                except RateLimitException:
                    raise
                except Exception as ssl_fallback_error:
                    print(f"   ❌ SSL fallback also failed: {ssl_fallback_error}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            else:
                raise
                
        except requests.exceptions.HTTPError as e:
            print(f"   ❌ HTTP Error (attempt {attempt + 1}/{max_retries}): {e}")
            if e.response and e.response.status_code == 429:
                # Don't retry on rate limiting
                raise RateLimitException("429 Too Many Requests - HTTP Error")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise
                
        except requests.exceptions.Timeout as e:
            print(f"   ⏰ Timeout (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1 + attempt)
                continue
            else:
                raise
                
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 Connection Error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                raise
                
        except ValueError as e:
            print(f"   ❌ URL Error: {e}")
            # Don't retry on URL errors
            raise
                
        except Exception as e:
            print(f"   ❌ Unexpected error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                raise
    
    raise Exception(f"Failed to fetch URL after {max_retries} attempts")

# ============================================================================
# FILE NAMING AND ANTI-OVERWRITE PROTECTION
# ============================================================================

def clean_filename_component(text: str, max_length: int = 20) -> str:
    """Clean text for use in filename"""
    if not text:
        return "Unknown"
    
    # Keep Chinese characters, letters, numbers
    cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '', str(text))
    return cleaned[:max_length] if cleaned else "Unknown"

def extract_domain_info(url: str) -> str:
    """Extract meaningful domain information from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '').lower()
        
        # Map common domains to shorter names
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
            'sinotrade.com.tw': 'sinotrade'
        }
        
        for full_domain, short_name in domain_map.items():
            if full_domain in domain:
                return short_name
        
        # Fallback to first part of domain
        return domain.split('.')[0][:10]
    except:
        return 'webpage'

def generate_unique_filename(company_name: str, stock_code: str, url: str, 
                           search_index: int, file_type: str = 'md') -> str:
    """
    Generate unique filename to prevent overwrites
    Format: {company}_{stock_code}_{domain}_{hash}.{ext}
    """
    # Clean components
    clean_company = clean_filename_component(company_name, 15)
    clean_stock = clean_filename_component(stock_code, 6) or 'XXXX'
    domain = extract_domain_info(url)
    
    # Create content hash for uniqueness
    content_identifier = f"{url}_{search_index}_{company_name}_{stock_code}"
    content_hash = hashlib.md5(content_identifier.encode()).hexdigest()[:6]
    
    # Build filename
    filename = f"{clean_company}_{clean_stock}_{domain}_{content_hash}.{file_type}"
    
    # Ensure reasonable length
    if len(filename) > 200:
        filename = f"{clean_company[:8]}_{clean_stock}_{domain[:8]}_{content_hash}.{file_type}"
    
    return filename

def safe_file_save(content: str, filepath: str, backup_existing: bool = True) -> bool:
    """
    Safely save file with optional backup of existing file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Backup existing file if requested
        if os.path.exists(filepath) and backup_existing:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{filepath}.backup_{timestamp}"
            try:
                import shutil
                shutil.copy2(filepath, backup_path)
                print(f"   📋 Backed up existing file: {os.path.basename(backup_path)}")
            except Exception as e:
                print(f"   ⚠️ Could not backup existing file: {e}")
        
        # Save new content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"   ❌ Error saving file {filepath}: {e}")
        return False

# ============================================================================
# COMPANY NAME EXTRACTION
# ============================================================================

def extract_company_info_from_search_result(title: str, url: str, snippet: str = "") -> Tuple[Optional[str], Optional[str]]:
    """
    Extract company name and stock code from search result
    """
    company_name = None
    stock_code = None
    
    # Combine title and snippet for analysis
    text_to_analyze = f"{title} {snippet}".lower()
    
    # Extract stock code patterns
    stock_patterns = [
        r'\((\d{4})\)',      # (2454)
        r'(\d{4})\.tw',      # 2454.tw
        r'(\d{4})-tw',       # 2454-tw
        r'(\d{4})\.tpe',     # 2454.tpe
    ]
    
    for pattern in stock_patterns:
        match = re.search(pattern, text_to_analyze)
        if match:
            stock_code = match.group(1)
            break
    
    # Extract known Taiwan company names
    company_patterns = [
        r'(台積電|台灣積體電路)',
        r'(聯發科|mediatek)',
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
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text_to_analyze)
        if match:
            # Take the first (usually Chinese) name
            company_name = match.group(1).split('|')[0]
            break
    
    # If we found stock code but no company name, try reverse lookup
    if stock_code and not company_name:
        stock_to_company = {
            '2330': '台積電',
            '2454': '聯發科',
            '2881': '富邦金',
            '2317': '鴻海',
            '2308': '台達電',
            '2301': '光寶科',
            '2303': '聯電',
            '2382': '廣達',
            '2357': '華碩',
            '2353': '宏碁',
            '3231': '緯創',
            '2324': '仁寶',
            '4938': '和碩',
            '2311': '日月光',
            '2325': '矽品',
            '3037': '欣興',
            '2408': '南亞科',
            '8299': '群聯',
            '2379': '瑞昱',
            '1587': '吉茂',
        }
        company_name = stock_to_company.get(stock_code)
    
    return company_name, stock_code

# ============================================================================
# ENHANCED WEB CONTENT DOWNLOADING
# ============================================================================

def download_webpage_content(url: str, timeout: int = 30) -> Tuple[Optional[str], Optional[str]]:
    """
    Enhanced webpage content download with comprehensive error handling
    Returns: (markdown_content, text_content)
    """
    try:
        print(f"   📥 Downloading content from: {url[:60]}...")
        
        # Use enhanced request function
        response = safe_request_with_retries(url, timeout=timeout)
        
        if not BS4_AVAILABLE:
            # Fallback to plain text
            print(f"   ✅ Downloaded as plain text ({len(response.text)} chars)")
            return response.text, response.text
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Get text content
        text_content = soup.get_text()
        text_content = re.sub(r'\n\s*\n', '\n\n', text_content)  # Clean up whitespace
        
        # Convert to markdown if available
        if MARKDOWNIFY_AVAILABLE:
            try:
                markdown_content = md(str(soup), heading_style="ATX")
            except Exception as e:
                print(f"   ⚠️ Markdown conversion failed: {e}")
                markdown_content = text_content
        else:
            markdown_content = text_content
        
        print(f"   ✅ Content downloaded successfully ({len(text_content)} chars)")
        return markdown_content, text_content
        
    except RateLimitException as e:
        print(f"   🚨 Rate limiting detected while downloading: {e}")
        # Re-raise to be caught by higher level
        raise
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error for {url[:60]}...: {e}")
        return None, None
    except Exception as e:
        print(f"   ❌ Error downloading {url[:60]}...: {e}")
        return None, None

# ============================================================================
# ENHANCED SEARCH EXECUTION
# ============================================================================

# Quick fix for the type error in factset_search.py
# Replace the search_company_factset_data function with this corrected version:

def search_company_factset_data(company_name: str, stock_code: str, 
                               search_type: str = 'factset', 
                               max_results: int = 10) -> List[Dict]:
    """
    Enhanced search with IMMEDIATE stop on 429 errors
    """
    if not GOOGLESEARCH_AVAILABLE:
        print(f"❌ Google search not available for {company_name}")
        return []
    
    results = []
    patterns = SEARCH_PATTERNS.get(search_type, SEARCH_PATTERNS['factset'])
    
    # Fix: Ensure max_results is an integer
    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 10
    
    for pattern_index, pattern in enumerate(patterns):
        try:
            # Format search query
            query = pattern.format(
                company_name=company_name,
                stock_code=stock_code or ''
            ).strip()
            
            print(f"   🔍 Searching: {query}")
            
            # Perform search with enhanced error handling
            try:
                # Fix: Ensure both operands are integers and reasonable size
                num_results_per_pattern = min(5, max(1, max_results // len(patterns)))
                
                search_results = search(
                    query,
                    num_results=num_results_per_pattern,
                    lang='zh-TW',
                    sleep_interval=SEARCH_DELAY
                )
            except Exception as e:
                error_str = str(e).lower()
                
                # CRITICAL FIX: Check for 429 errors more thoroughly
                if any(keyword in error_str for keyword in ["429", "too many requests", "blocked", "rate limit", "quota", "sorry/index"]):
                    print(f"   🚨 RATE LIMITING DETECTED in search: {e}")
                    print(f"   🛑 IMMEDIATE STOP - No more search attempts")
                    # Raise exception to stop ALL searching immediately
                    raise RateLimitException(f"Search API rate limiting: {e}")
                else:
                    print(f"   ⚠️ Search error: {e}")
                    continue  # Only continue for non-rate-limiting errors
            
            # Process results with enhanced URL handling
            for i, url in enumerate(search_results):
                try:
                    # Clean and validate URL first
                    clean_url = clean_and_validate_url(url)
                    if not clean_url:
                        print(f"   ⚠️ Invalid URL skipped: {url[:60]}...")
                        continue
                    
                    # Skip if already have this URL
                    if any(r['url'] == clean_url for r in results):
                        continue
                    
                    # Add delay between requests
                    if i > 0:
                        time.sleep(REQUEST_DELAY)
                    
                    # Download page with enhanced error handling
                    try:
                        response = safe_request_with_retries(clean_url, timeout=10)
                    except RateLimitException as e:
                        print(f"   🚨 Rate limiting in URL processing: {e}")
                        print(f"   🛑 STOPPING all searches immediately")
                        # Re-raise to stop the entire search
                        raise
                    except Exception as e:
                        print(f"   ⚠️ Failed to download {clean_url[:60]}...: {e}")
                        continue
                    
                    if response and response.status_code == 200 and BS4_AVAILABLE:
                        try:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            title = soup.title.string if soup.title else clean_url
                            
                            # Get meta description as snippet
                            meta_desc = soup.find('meta', attrs={'name': 'description'})
                            snippet = meta_desc.get('content', '') if meta_desc else ''
                            
                            # Extract company info from search result
                            detected_company, detected_stock = extract_company_info_from_search_result(
                                title, clean_url, snippet
                            )
                            
                            results.append({
                                'title': title.strip()[:200],
                                'url': clean_url,
                                'snippet': snippet.strip()[:300],
                                'query': query,
                                'search_type': search_type,
                                'detected_company': detected_company or company_name,
                                'detected_stock_code': detected_stock or stock_code,
                                'priority_score': calculate_priority_score(clean_url, title, snippet)
                            })
                            
                            print(f"   ✅ Found: {title[:50]}...")
                        except Exception as e:
                            print(f"   ⚠️ Error parsing result content: {e}")
                            continue
                    
                except RateLimitException:
                    # CRITICAL: Re-raise rate limiting exceptions immediately
                    print(f"   🛑 Rate limiting detected - stopping ALL patterns")
                    raise
                except Exception as e:
                    print(f"   ⚠️ Error processing result {clean_url[:60]}...: {e}")
                    continue
            
            # Rate limiting between different search patterns
            time.sleep(SEARCH_DELAY)
            
        except RateLimitException:
            # CRITICAL FIX: Stop all searches immediately on rate limiting
            print(f"   🛑 Stopping all searches due to rate limiting")
            raise  # Re-raise to stop the parent function
        except Exception as e:
            print(f"   ❌ Search error for pattern '{pattern}': {e}")
            
            # ADDITIONAL CHECK: Even in general exceptions, check for rate limiting
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["429", "too many requests", "sorry/index"]):
                print(f"   🚨 Rate limiting detected in general exception: {e}")
                print(f"   🛑 STOPPING immediately")
                raise RateLimitException(f"Rate limiting in pattern processing: {e}")
            
            continue  # Only continue for non-rate-limiting errors
    
    # Sort by priority score
    results.sort(key=lambda x: x['priority_score'], reverse=True)
    return results[:max_results]

def calculate_priority_score(url: str, title: str, snippet: str) -> int:
    """
    Calculate priority score for search results
    Higher score = higher priority
    """
    score = 0
    text = f"{title} {snippet}".lower()
    
    # Domain scoring
    for domain in PRIORITY_DOMAINS:
        if domain in url.lower():
            score += 100
            break
    
    # Content scoring
    factset_terms = ['factset', 'eps', '預估', '目標價', '分析師', '財報']
    for term in factset_terms:
        if term in text:
            score += 10
    
    # Negative scoring for irrelevant content
    negative_terms = ['廣告', 'ad', 'advertisement', '購物', 'shop']
    for term in negative_terms:
        if term in text:
            score -= 20
    
    return score

# ============================================================================
# ENHANCED BATCH PROCESSING
# ============================================================================

def process_company_search(company_data: Dict, config: Dict, search_type: str = 'factset') -> Dict:
    """
    Enhanced company search processing with immediate rate limiting detection
    """
    company_name = company_data.get('名稱', company_data.get('name', ''))
    stock_code = company_data.get('代號', company_data.get('code', ''))
    
    print(f"🔍 Searching for {company_name} ({stock_code})")
    
    # Search for results with rate limiting detection
    try:
        search_results = search_company_factset_data(
            company_name, 
            stock_code, 
            search_type,
            config.get('search', {}).get('max_results', 10)
        )
    except RateLimitException as e:
        print(f"   🚨 Rate limiting detected for {company_name}: {e}")
        # Return special result indicating rate limiting
        return {
            'company': company_name,
            'stock_code': stock_code,
            'search_type': search_type,
            'results': [],
            'files_saved': 0,
            'success': False,
            'rate_limited': True,
            'error': str(e)
        }
    
    if not search_results:
        print(f"   ❌ No results found for {company_name}")
        return {
            'company': company_name,
            'stock_code': stock_code,
            'search_type': search_type,
            'results': [],
            'files_saved': 0,
            'success': False,
            'rate_limited': False
        }
    
    # Set up output directories
    md_dir = config['output']['md_dir']
    pdf_dir = config['output']['pdf_dir']
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Download and save content
    files_saved = 0
    processed_results = []
    
    for i, result in enumerate(search_results):
        try:
            print(f"   📥 Downloading: {result['title'][:50]}...")
            
            # Download content with rate limiting detection
            try:
                markdown_content, text_content = download_webpage_content(result['url'])
            except RateLimitException as e:
                print(f"   🚨 Rate limiting during download: {e}")
                # Return partial results with rate limiting flag
                return {
                    'company': company_name,
                    'stock_code': stock_code,
                    'search_type': search_type,
                    'results': processed_results,
                    'files_saved': files_saved,
                    'success': files_saved > 0,
                    'rate_limited': True,
                    'error': str(e)
                }
            
            if markdown_content and text_content:
                # Generate unique filenames
                md_filename = generate_unique_filename(
                    result['detected_company'],
                    result['detected_stock_code'],
                    result['url'],
                    i,
                    'md'
                )
                
                txt_filename = generate_unique_filename(
                    result['detected_company'],
                    result['detected_stock_code'],
                    result['url'],
                    i,
                    'txt'
                )
                
                md_filepath = os.path.join(md_dir, md_filename)
                txt_filepath = os.path.join(pdf_dir, txt_filename)
                
                # Save files
                if safe_file_save(markdown_content, md_filepath):
                    print(f"   ✅ Saved MD: {md_filename}")
                    files_saved += 1
                
                if safe_file_save(text_content, txt_filepath):
                    print(f"   ✅ Saved TXT: {txt_filename}")
                
                # Add file info to result
                result['md_file'] = md_filename
                result['txt_file'] = txt_filename
                result['md_filepath'] = md_filepath
                result['txt_filepath'] = txt_filepath
                
            else:
                print(f"   ❌ Failed to download content")
                result['md_file'] = None
                result['txt_file'] = None
            
            processed_results.append(result)
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
            
        except RateLimitException:
            # Stop processing and return partial results
            print(f"   🛑 Stopping processing due to rate limiting")
            return {
                'company': company_name,
                'stock_code': stock_code,
                'search_type': search_type,
                'results': processed_results,
                'files_saved': files_saved,
                'success': files_saved > 0,
                'rate_limited': True,
                'error': "Rate limiting during processing"
            }
        except Exception as e:
            print(f"   ❌ Error processing result {i}: {e}")
            if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
                traceback.print_exc()
            continue
    
    success = files_saved > 0
    print(f"   📊 Results: {len(processed_results)} found, {files_saved} files saved")
    
    return {
        'company': company_name,
        'stock_code': stock_code,
        'search_type': search_type,
        'results': processed_results,
        'files_saved': files_saved,
        'success': success,
        'rate_limited': False
    }

def process_batch_search(companies: List[Dict], config: Dict, search_type: str = 'factset') -> List[Dict]:
    """
    Enhanced batch search processing with immediate stop on rate limiting
    """
    batch_results = []
    total_companies = len(companies)
    
    print(f"🚀 Processing batch of {total_companies} companies ({search_type} search)")
    print(f"🛑 Will stop immediately on rate limiting and process existing data")
    
    for i, company in enumerate(companies, 1):
        try:
            print(f"\n[{i}/{total_companies}] Processing company...")
            
            result = process_company_search(company, config, search_type)
            batch_results.append(result)
            
            # Check for rate limiting
            if result.get('rate_limited', False):
                print(f"   🚨 Rate limiting detected at company {i} - STOPPING BATCH")
                print(f"   📄 Processed {i}/{total_companies} companies before stopping")
                
                # Add metadata about early termination
                for batch_result in batch_results:
                    batch_result['batch_stopped_early'] = True
                    batch_result['batch_stop_reason'] = 'rate_limiting'
                    batch_result['batch_completion'] = f"{i}/{total_companies}"
                
                break
            
            # Progress update
            success_count = sum(1 for r in batch_results if r['success'])
            print(f"   📊 Batch progress: {success_count}/{i} successful")
            
            # Rate limiting between companies
            if i < total_companies:
                time.sleep(SEARCH_DELAY)
        
        except KeyboardInterrupt:
            print(f"\n⚠️ Search interrupted by user at company {i}")
            break
        except RateLimitException as e:
            print(f"\n🚨 Rate limiting exception at company {i}: {e}")
            # Add error result and stop
            batch_results.append({
                'company': company.get('名稱', company.get('name', 'Unknown')),
                'stock_code': company.get('代號', company.get('code', '')),
                'search_type': search_type,
                'results': [],
                'files_saved': 0,
                'success': False,
                'rate_limited': True,
                'error': str(e)
            })
            break
        except Exception as e:
            print(f"   ❌ Error processing company {i}: {e}")
            if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
                traceback.print_exc()
            continue
    
    return batch_results

# ============================================================================
# CSV OUTPUT AND TRACKING
# ============================================================================

def save_search_results_to_csv(batch_results: List[Dict], output_file: str) -> bool:
    """
    Enhanced CSV saving with rate limiting information
    """
    try:
        import pandas as pd
        
        # Flatten results for CSV
        csv_data = []
        
        for company_result in batch_results:
            company_name = company_result['company']
            stock_code = company_result['stock_code']
            search_type = company_result['search_type']
            rate_limited = company_result.get('rate_limited', False)
            batch_stopped = company_result.get('batch_stopped_early', False)
            
            if company_result['results']:
                for result in company_result['results']:
                    csv_data.append({
                        'Title': result['title'],
                        'Link': result['url'],
                        'Snippet': result['snippet'],
                        'File': result.get('txt_file', ''),
                        'MD File': result.get('md_file', ''),
                        '公司名稱': result.get('detected_company', company_name),
                        '股票代號': result.get('detected_stock_code', stock_code),
                        'Search_Type': search_type,
                        'Query': result['query'],
                        'Priority_Score': result['priority_score'],
                        'Downloaded': result.get('md_file') is not None,
                        'Rate_Limited': rate_limited,
                        'Batch_Stopped': batch_stopped,
                        'Processed_Time': datetime.now().isoformat()
                    })
            else:
                # Add empty row for companies with no results
                csv_data.append({
                    'Title': '',
                    'Link': '',
                    'Snippet': '',
                    'File': '',
                    'MD File': '',
                    '公司名稱': company_name,
                    '股票代號': stock_code,
                    'Search_Type': search_type,
                    'Query': '',
                    'Priority_Score': 0,
                    'Downloaded': False,
                    'Rate_Limited': rate_limited,
                    'Batch_Stopped': batch_stopped,
                    'Error': company_result.get('error', ''),
                    'Processed_Time': datetime.now().isoformat()
                })
        
        # Save to CSV
        df = pd.DataFrame(csv_data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Summary statistics
        total_records = len(csv_data)
        rate_limited_count = len(df[df['Rate_Limited'] == True])
        downloaded_count = len(df[df['Downloaded'] == True])
        
        print(f"✅ Search results saved: {output_file}")
        print(f"   📊 Total records: {total_records}")
        print(f"   📥 Downloaded: {downloaded_count}")
        if rate_limited_count > 0:
            print(f"   🚨 Rate limited: {rate_limited_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving search results to CSV: {e}")
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            traceback.print_exc()
        return False

# ============================================================================
# ENHANCED MAIN SEARCH SUITE
# ============================================================================

def run_enhanced_search_suite(config: Dict, search_types: Optional[List[str]] = None, priority_focus: str = "balanced") -> bool:
    """
    Enhanced search suite with immediate rate limiting detection and stop
    """
    print(f"🚀 Enhanced Google Search Suite v{__version__}")
    print(f"📅 Date: {__date__} | Author: {__author__}")
    print(f"🛑 Enhanced with immediate rate limiting detection and stop")
    print("=" * 60)
    
    # Validate dependencies
    missing_deps = []
    if not GOOGLESEARCH_AVAILABLE:
        missing_deps.append('googlesearch-python')
    if not BS4_AVAILABLE:
        missing_deps.append('beautifulsoup4')
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("💡 Install with: pip install " + ' '.join(missing_deps))
        return False
    
    # Load target companies
    target_companies = config.get('target_companies', [])
    if not target_companies:
        print("❌ No target companies found in configuration")
        return False
    
    # Apply priority focus
    if priority_focus == "high_only":
        target_companies = target_companies[:10]
        print(f"🎯 High priority focus: {len(target_companies)} companies")
    elif priority_focus == "top_30":
        target_companies = target_companies[:30]
        print(f"🎯 Top 30 focus: {len(target_companies)} companies")
    else:
        print(f"🎯 Balanced approach: {len(target_companies)} companies")
    
    # Set up search types
    if search_types is None:
        search_types = ['factset', 'financial']
    
    # Create output directories
    output_dirs = ['csv_dir', 'md_dir', 'pdf_dir']
    for dir_key in output_dirs:
        os.makedirs(config['output'][dir_key], exist_ok=True)
    
    # Process each search type
    all_success = True
    total_files_saved = 0
    rate_limiting_detected = False
    
    for search_type in search_types:
        print(f"\n{'='*60}")
        print(f"🔍 SEARCH TYPE: {search_type.upper()}")
        print("="*60)
        
        try:
            # Process companies in batches
            batch_size = config.get('search', {}).get('batch_size', 20)
            
            for i in range(0, len(target_companies), batch_size):
                batch_companies = target_companies[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(target_companies) + batch_size - 1) // batch_size
                
                print(f"\n📦 Batch {batch_num}/{total_batches}: {len(batch_companies)} companies")
                
                # Process batch with enhanced error handling
                try:
                    batch_results = process_batch_search(batch_companies, config, search_type)
                except RateLimitException as e:
                    print(f"   🚨 Rate limiting in batch processing: {e}")
                    rate_limiting_detected = True
                    all_success = False
                    break
                
                # Check for rate limiting in results
                rate_limited_results = [r for r in batch_results if r.get('rate_limited', False)]
                if rate_limited_results:
                    print(f"   🚨 Rate limiting detected in {len(rate_limited_results)} results")
                    rate_limiting_detected = True
                    all_success = False
                
                # Save results to CSV
                csv_filename = f"FactSet_Batch_{batch_num}.csv"
                csv_filepath = os.path.join(config['output']['csv_dir'], csv_filename)
                
                if save_search_results_to_csv(batch_results, csv_filepath):
                    files_saved = sum(r['files_saved'] for r in batch_results)
                    total_files_saved += files_saved
                    success_count = sum(1 for r in batch_results if r['success'])
                    
                    print(f"✅ Batch {batch_num} completed:")
                    print(f"   📊 Success rate: {success_count}/{len(batch_companies)} companies")
                    print(f"   📄 Files saved: {files_saved}")
                    
                    if rate_limited_results:
                        print(f"   🚨 Rate limiting detected - stopping search")
                        break
                else:
                    print(f"❌ Failed to save batch {batch_num} results")
                    all_success = False
                
                # Check if any batch was stopped early
                early_stop = any(r.get('batch_stopped_early', False) for r in batch_results)
                if early_stop:
                    print(f"   🛑 Batch stopped early due to rate limiting")
                    rate_limiting_detected = True
                    break
                
                # Rate limiting between batches
                if i + batch_size < len(target_companies):
                    print(f"⏳ Waiting {SEARCH_DELAY * 2} seconds before next batch...")
                    time.sleep(SEARCH_DELAY * 2)
        
        except KeyboardInterrupt:
            print(f"\n⚠️ Search interrupted for type {search_type}")
            all_success = False
            break
        except RateLimitException as e:
            print(f"\n🚨 Rate limiting detected for search type {search_type}: {e}")
            rate_limiting_detected = True
            all_success = False
            break
        except Exception as e:
            print(f"❌ Error in {search_type} search: {e}")
            if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
                traceback.print_exc()
            all_success = False
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 ENHANCED SEARCH SUITE SUMMARY")
    print("="*60)
    print(f"🎯 Companies processed: {len(target_companies)}")
    print(f"📄 Total files saved: {total_files_saved}")
    
    if rate_limiting_detected:
        print(f"🚨 Rate limiting detected - search stopped early")
        print(f"📄 Recommendation: Process existing data and retry later")
        print(f"✅ Partial success: Some data collected before rate limiting")
        return "rate_limited"  # Special return value
    elif all_success:
        print(f"✅ Overall success: Complete")
        return True
    else:
        print(f"⚠️ Overall success: Partial/Failed")
        return False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_search_config(config: Dict) -> bool:
    """
    Validate search configuration
    """
    required_keys = ['output', 'target_companies']
    
    for key in required_keys:
        if key not in config:
            print(f"❌ Missing required config key: {key}")
            return False
    
    required_output_keys = ['csv_dir', 'md_dir', 'pdf_dir']
    
    for key in required_output_keys:
        if key not in config['output']:
            print(f"❌ Missing required output config key: {key}")
            return False
    
    return True

def get_search_stats(csv_dir: str) -> Dict:
    """
    Enhanced search statistics including rate limiting information
    """
    try:
        import pandas as pd
        
        stats = {
            'total_files': 0,
            'total_companies': 0,
            'total_results': 0,
            'files_with_results': 0,
            'success_rate': 0.0,
            'rate_limited_files': 0,
            'rate_limited_companies': 0
        }
        
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
        stats['total_files'] = len(csv_files)
        
        all_companies = set()
        total_results = 0
        files_with_results = 0
        rate_limited_files = 0
        rate_limited_companies = set()
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(os.path.join(csv_dir, csv_file))
                
                # Count unique companies
                companies_in_file = df['公司名稱'].dropna().unique()
                all_companies.update(companies_in_file)
                
                # Count results
                results_in_file = len(df[df['Title'].notna() & (df['Title'] != '')])
                total_results += results_in_file
                
                if results_in_file > 0:
                    files_with_results += 1
                
                # Check for rate limiting
                if 'Rate_Limited' in df.columns:
                    rate_limited_count = len(df[df['Rate_Limited'] == True])
                    if rate_limited_count > 0:
                        rate_limited_files += 1
                        rate_limited_companies.update(df[df['Rate_Limited'] == True]['公司名稱'].dropna())
                    
            except Exception as e:
                print(f"⚠️ Error reading {csv_file}: {e}")
        
        stats['total_companies'] = len(all_companies)
        stats['total_results'] = total_results
        stats['files_with_results'] = files_with_results
        stats['success_rate'] = (files_with_results / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
        stats['rate_limited_files'] = rate_limited_files
        stats['rate_limited_companies'] = len(rate_limited_companies)
        
        return stats
        
    except Exception as e:
        print(f"❌ Error calculating search stats: {e}")
        return {}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """
    Enhanced main entry point with rate limiting detection
    """
    print(f"🔍 Enhanced Google Search Module v{__version__}")
    
    # Load config
    try:
        config = config_module.load_config()
    except:
        # Fallback config
        config = {
            'target_companies': [],
            'output': {
                'csv_dir': 'data/csv',
                'md_dir': 'data/md',
                'pdf_dir': 'data/pdf'
            }
        }
    
    if not validate_search_config(config):
        print("❌ Invalid configuration")
        return False
    
    # Run enhanced search suite
    try:
        result = run_enhanced_search_suite(config)
        
        if result == "rate_limited":
            print("🚨 Search stopped due to rate limiting")
            print("📄 Some data was collected before stopping")
            print("💡 Process existing data and retry search later")
            return "rate_limited"
        elif result:
            print("✅ Search suite completed successfully")
        else:
            print("❌ Search suite completed with errors")
        
        # Show stats
        stats = get_search_stats(config['output']['csv_dir'])
        if stats:
            print(f"📊 Final statistics:")
            print(f"   Files: {stats['total_files']}")
            print(f"   Companies: {stats['total_companies']}")
            print(f"   Results: {stats['total_results']}")
            print(f"   Success rate: {stats['success_rate']:.1f}%")
            if stats.get('rate_limited_companies', 0) > 0:
                print(f"   Rate limited companies: {stats['rate_limited_companies']}")
        
        return result
        
    except RateLimitException as e:
        print(f"🚨 Rate limiting detected in main: {e}")
        print("📄 Some data may have been collected before stopping")
        return "rate_limited"
    except Exception as e:
        print(f"❌ Search suite failed: {e}")
        return False

if __name__ == "__main__":
    main()