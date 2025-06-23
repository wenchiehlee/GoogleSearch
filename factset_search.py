"""
factset_search.py - Enhanced Google Search Module (v3.3.0)

Version: 3.3.0
Date: 2025-06-22
Author: Google Search FactSet Pipeline - v3.3.0 Enhanced Architecture

v3.3.0 ENHANCEMENTS:
- ✅ Improved filename generation to avoid conflicts
- ✅ Enhanced financial data extraction patterns
- ✅ Better date extraction and validation
- ✅ Immediate stop on 429 errors with improved fallback
- ✅ Enhanced company name matching with 觀察名單.csv
- ✅ Better content quality assessment
- ✅ Improved MD file organization by company code
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
    MARKDOWNIFY_AVAILABLE = False

# Import local modules
try:
    import utils
    import config as config_module
except ImportError as e:
    print(f"⚠️ Could not import local modules: {e}")

# Version Information - v3.3.0
__version__ = "3.3.0"
__date__ = "2025-06-22"
__author__ = "Google Search FactSet Pipeline - v3.3.0 Enhanced Architecture"

# ============================================================================
# ENHANCED SEARCH PATTERNS - v3.3.0
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
    'factset.com',
    'moneydj.com',
    'cnyes.com',
    'yahoo.com',
    'investing.com',
    'marketwatch.com',
    'wealth.com.tw',
    'businessweekly.com.tw',
    'commercial-times.com'
]

# Rate limiting settings
SEARCH_DELAY = 2
REQUEST_DELAY = 1
MAX_RETRIES = 3

class RateLimitException(Exception):
    """Custom exception for rate limiting detection"""
    pass

# ============================================================================
# ENHANCED FILENAME GENERATION - v3.3.0
# ============================================================================

def generate_unique_filename_v330(company_name: str, stock_code: str, url: str, 
                                 search_index: int, content_preview: str = "") -> str:
    """
    Generate unique filename with better organization - v3.3.0
    Format: {stock_code}_{company}_{domain}_{content_hash}_{timestamp}.md
    """
    # Clean components
    clean_company = clean_filename_component(company_name, 10)
    clean_stock = clean_filename_component(stock_code, 4) or 'XXXX'
    domain = extract_domain_info(url)
    
    # Create content-based hash for uniqueness
    content_identifier = f"{url}_{search_index}_{content_preview[:100]}"
    content_hash = hashlib.md5(content_identifier.encode()).hexdigest()[:6]
    
    # Add timestamp for better organization
    timestamp = datetime.now().strftime("%m%d_%H%M")
    
    # Build filename: stock_code first for better sorting
    filename = f"{clean_stock}_{clean_company}_{domain}_{content_hash}_{timestamp}.md"
    
    # Ensure reasonable length
    if len(filename) > 200:
        filename = f"{clean_stock}_{clean_company[:6]}_{domain[:6]}_{content_hash}_{timestamp}.md"
    
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
            'commercial-times.com': 'ctimes'
        }
        
        for full_domain, short_name in domain_map.items():
            if full_domain in domain:
                return short_name
        
        # Fallback to first part of domain
        return domain.split('.')[0][:8]
    except:
        return 'web'

# ============================================================================
# ENHANCED CONTENT QUALITY ASSESSMENT - v3.3.0
# ============================================================================

def assess_content_quality(content: str, title: str = "") -> int:
    """
    Assess content quality for financial relevance - v3.3.0
    Returns score 1-10 (10 being highest quality)
    """
    if not content:
        return 1
    
    content_lower = content.lower()
    title_lower = title.lower()
    combined_text = f"{title_lower} {content_lower}"
    
    score = 1  # Base score
    
    # High-value financial keywords
    factset_keywords = ['factset', 'eps', '每股盈餘', '目標價', 'target price']
    analyst_keywords = ['分析師', 'analyst', '券商', '投資', '評等']
    forecast_keywords = ['預估', '預測', 'forecast', '展望', '2025', '2026', '2027']
    
    # Score based on keyword presence
    for keyword in factset_keywords:
        if keyword in combined_text:
            score += 2
    
    for keyword in analyst_keywords:
        if keyword in combined_text:
            score += 1
    
    for keyword in forecast_keywords:
        if keyword in combined_text:
            score += 1
    
    # Check for numerical data (prices, percentages, etc.)
    numeric_patterns = [
        r'\d+\.\d+',  # Decimal numbers
        r'\$\d+',     # Dollar amounts
        r'\d+%',      # Percentages
        r'NT\$\d+',   # NT dollar amounts
    ]
    
    for pattern in numeric_patterns:
        if re.search(pattern, content):
            score += 1
    
    # Penalty for low-quality indicators
    low_quality_indicators = ['廣告', 'advertisement', '購物', 'shop', '404', 'error']
    for indicator in low_quality_indicators:
        if indicator in combined_text:
            score -= 2
    
    # Bonus for length (more comprehensive content)
    if len(content) > 2000:
        score += 1
    elif len(content) > 5000:
        score += 2
    
    return max(1, min(10, score))

# ============================================================================
# ENHANCED COMPANY EXTRACTION - v3.3.0
# ============================================================================

def extract_company_info_enhanced(title: str, url: str, snippet: str = "", 
                                 watchlist_df=None) -> Tuple[Optional[str], Optional[str]]:
    """
    Enhanced company name and stock code extraction - v3.3.0
    """
    company_name = None
    stock_code = None
    
    # Combine all available text
    text_to_analyze = f"{title} {snippet} {url}".lower()
    
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
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text_to_analyze)
        if match:
            # Take the first (usually Chinese) name
            company_name = match.group(1).split('|')[0]
            break
    
    # Use watchlist for validation if available
    if watchlist_df is not None and stock_code:
        try:
            match = watchlist_df[watchlist_df['代號'].astype(str) == stock_code]
            if not match.empty:
                watchlist_name = match.iloc[0]['名稱']
                if not company_name or len(watchlist_name) > len(company_name):
                    company_name = watchlist_name
        except Exception:
            pass
    
    # Fallback: stock code to company mapping
    if stock_code and not company_name:
        stock_to_company = {
            '2330': '台積電', '2454': '聯發科', '2881': '富邦金', '2317': '鴻海',
            '2308': '台達電', '2301': '光寶科', '2303': '聯電', '2382': '廣達',
            '2357': '華碩', '2353': '宏碁', '3231': '緯創', '2324': '仁寶',
            '4938': '和碩', '2311': '日月光', '2325': '矽品', '3037': '欣興',
            '2408': '南亞科', '8299': '群聯', '2379': '瑞昱', '1587': '吉茂',
            '1216': '統一', '2412': '中華電', '1301': '台塑', '2002': '中鋼',
            '2603': '長榮', '2609': '陽明'
        }
        company_name = stock_to_company.get(stock_code)
    
    return company_name, stock_code

# ============================================================================
# ENHANCED WEB CONTENT PROCESSING - v3.3.0
# ============================================================================

def download_webpage_content_enhanced(url: str, timeout: int = 30) -> Tuple[Optional[str], Optional[str], int]:
    """
    Enhanced webpage content download with quality assessment - v3.3.0
    Returns: (markdown_content, text_content, quality_score)
    """
    try:
        print(f"   📥 Downloading: {url[:60]}...")
        
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
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        # Enhanced rate limiting detection
        if response.status_code == 429:
            print(f"   🚨 Rate limiting detected (429)")
            raise RateLimitException("429 Too Many Requests")
        
        if 'rate limit' in response.text.lower() or 'too many requests' in response.text.lower():
            print(f"   🚨 Rate limiting detected in content")
            raise RateLimitException("Rate limiting in response content")
        
        response.raise_for_status()
        
        if not BS4_AVAILABLE:
            quality_score = assess_content_quality(response.text)
            return response.text, response.text, quality_score
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
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
            except Exception as e:
                print(f"   ⚠️ Markdown conversion failed: {e}")
                markdown_content = text_content
        else:
            markdown_content = text_content
        
        # Assess content quality
        quality_score = assess_content_quality(text_content, title)
        
        print(f"   ✅ Downloaded: {len(text_content)} chars, quality: {quality_score}/10")
        return markdown_content, text_content, quality_score
        
    except RateLimitException as e:
        print(f"   🚨 Rate limiting detected: {e}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None, None, 0
    except Exception as e:
        print(f"   ❌ Download error: {e}")
        return None, None, 0

# ============================================================================
# ENHANCED SEARCH EXECUTION - v3.3.0
# ============================================================================

def search_company_factset_data_v330(company_name: str, stock_code: str, 
                                    search_type: str = 'factset', 
                                    max_results: int = 10,
                                    watchlist_df=None) -> List[Dict]:
    """
    Enhanced search with immediate stop and better content filtering - v3.3.0
    """
    if not GOOGLESEARCH_AVAILABLE:
        print(f"❌ Google search not available for {company_name}")
        return []
    
    results = []
    patterns = ENHANCED_SEARCH_PATTERNS.get(search_type, ENHANCED_SEARCH_PATTERNS['factset'])
    
    max_results = max(1, min(20, int(max_results)))  # Ensure valid range
    
    for pattern_index, pattern in enumerate(patterns):
        try:
            # Format search query
            query = pattern.format(
                company_name=company_name,
                stock_code=stock_code or ''
            ).strip()
            
            print(f"   🔍 Search {pattern_index + 1}/{len(patterns)}: {query}")
            
            # Perform search with enhanced error handling
            try:
                num_results_per_pattern = min(5, max(1, max_results // len(patterns)))
                
                search_results = search(
                    query,
                    num_results=num_results_per_pattern,
                    lang='zh-TW',
                    sleep_interval=SEARCH_DELAY
                )
            except Exception as e:
                error_str = str(e).lower()
                
                # Enhanced 429 detection
                if any(keyword in error_str for keyword in [
                    "429", "too many requests", "blocked", "rate limit", 
                    "quota", "sorry/index", "temporarily unavailable"
                ]):
                    print(f"   🚨 RATE LIMITING DETECTED: {e}")
                    print(f"   🛑 IMMEDIATE STOP - All searches terminated")
                    raise RateLimitException(f"Search API rate limiting: {e}")
                else:
                    print(f"   ⚠️ Search error: {e}")
                    continue
            
            # Process results with enhanced validation
            for i, url in enumerate(search_results):
                try:
                    # Clean and validate URL
                    clean_url = clean_and_validate_url_v330(url)
                    if not clean_url:
                        print(f"   ⚠️ Invalid URL skipped: {url[:60]}...")
                        continue
                    
                    # Skip duplicates
                    if any(r['url'] == clean_url for r in results):
                        continue
                    
                    # Add delay between requests
                    if i > 0:
                        time.sleep(REQUEST_DELAY)
                    
                    # Download with quality assessment
                    try:
                        markdown_content, text_content, quality_score = download_webpage_content_enhanced(clean_url)
                    except RateLimitException as e:
                        print(f"   🚨 Rate limiting during download: {e}")
                        print(f"   🛑 STOPPING all searches immediately")
                        raise
                    except Exception as e:
                        print(f"   ⚠️ Failed to download: {e}")
                        continue
                    
                    # Only keep high-quality content
                    if quality_score < 3:
                        print(f"   📊 Low quality content skipped (score: {quality_score}/10)")
                        continue
                    
                    if markdown_content and text_content:
                        # Extract enhanced company info
                        detected_company, detected_stock = extract_company_info_enhanced(
                            clean_url, clean_url, text_content[:500], watchlist_df
                        )
                        
                        # Generate unique filename with content preview
                        filename = generate_unique_filename_v330(
                            detected_company or company_name,
                            detected_stock or stock_code,
                            clean_url,
                            i,
                            text_content[:200]
                        )
                        
                        results.append({
                            'title': clean_url[:100],  # Use URL as title fallback
                            'url': clean_url,
                            'snippet': text_content[:300],
                            'content': markdown_content,
                            'quality_score': quality_score,
                            'detected_company': detected_company or company_name,
                            'detected_stock_code': detected_stock or stock_code,
                            'filename': filename,
                            'query': query,
                            'search_type': search_type,
                            'content_length': len(text_content)
                        })
                        
                        print(f"   ✅ Quality content found: {filename} (score: {quality_score}/10)")
                    
                except RateLimitException:
                    print(f"   🛑 Rate limiting - stopping pattern processing")
                    raise
                except Exception as e:
                    print(f"   ⚠️ Error processing result: {e}")
                    continue
            
            # Delay between patterns
            time.sleep(SEARCH_DELAY)
            
        except RateLimitException:
            print(f"   🛑 Stopping all searches due to rate limiting")
            raise
        except Exception as e:
            print(f"   ❌ Pattern error: {e}")
            
            # Check for hidden rate limiting
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["429", "too many requests"]):
                print(f"   🚨 Hidden rate limiting detected")
                raise RateLimitException(f"Rate limiting in pattern: {e}")
            
            continue
    
    # Sort by quality score and return best results
    results.sort(key=lambda x: x['quality_score'], reverse=True)
    return results[:max_results]

def clean_and_validate_url_v330(url: str) -> Optional[str]:
    """Enhanced URL cleaning and validation for v3.3.0"""
    try:
        if not url:
            return None
        
        url = str(url).strip()
        
        # Handle Google redirects
        if 'google.com' in url and '/url?q=' in url:
            try:
                match = re.search(r'/url\?q=([^&]+)', url)
                if match:
                    actual_url = unquote(match.group(1))
                    url = actual_url
            except Exception:
                return None
        
        # Ensure proper protocol
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic validation
        if VALIDATORS_AVAILABLE:
            try:
                if not validators.url(url):
                    return None
            except Exception:
                return None
        
        return url
        
    except Exception:
        return None

# ============================================================================
# ENHANCED FILE SAVING - v3.3.0
# ============================================================================

def save_content_to_md_file_v330(content: str, filename: str, md_dir: str, 
                                 metadata: Dict = None) -> bool:
    """
    Save content to MD file with enhanced metadata - v3.3.0
    """
    try:
        os.makedirs(md_dir, exist_ok=True)
        filepath = os.path.join(md_dir, filename)
        
        # Prepare content with metadata header
        if metadata:
            header = "---\n"
            header += f"url: {metadata.get('url', '')}\n"
            header += f"title: {metadata.get('title', '')}\n"
            header += f"quality_score: {metadata.get('quality_score', 0)}\n"
            header += f"company: {metadata.get('company', '')}\n"
            header += f"stock_code: {metadata.get('stock_code', '')}\n"
            header += f"extracted_date: {datetime.now().isoformat()}\n"
            header += f"search_query: {metadata.get('query', '')}\n"
            header += "---\n\n"
            
            final_content = header + content
        else:
            final_content = content
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error saving file {filename}: {e}")
        return False

# ============================================================================
# ENHANCED BATCH PROCESSING - v3.3.0
# ============================================================================

def process_company_search_v330(company_data: Dict, config: Dict, 
                               search_type: str = 'factset',
                               watchlist_df=None) -> Dict:
    """
    Enhanced company search processing with v3.3.0 improvements
    """
    company_name = company_data.get('name', company_data.get('名稱', ''))
    stock_code = company_data.get('code', company_data.get('代號', ''))
    
    print(f"🔍 Searching {company_name} ({stock_code}) - v3.3.0")
    
    try:
        search_results = search_company_factset_data_v330(
            company_name, 
            stock_code, 
            search_type,
            config.get('search', {}).get('max_results', 10),
            watchlist_df
        )
    except RateLimitException as e:
        print(f"   🚨 Rate limiting for {company_name}: {e}")
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
        print(f"   ❌ No quality results found for {company_name}")
        return {
            'company': company_name,
            'stock_code': stock_code,
            'search_type': search_type,
            'results': [],
            'files_saved': 0,
            'success': False,
            'rate_limited': False
        }
    
    # Save content to MD files
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
                'query': result['query']
            }
            
            if save_content_to_md_file_v330(content, filename, md_dir, metadata):
                files_saved += 1
                print(f"   ✅ Saved: {filename}")
            
        except Exception as e:
            print(f"   ❌ Error saving result: {e}")
            continue
    
    success = files_saved > 0
    print(f"   📊 {company_name}: {files_saved} files saved")
    
    return {
        'company': company_name,
        'stock_code': stock_code,
        'search_type': search_type,
        'results': search_results,
        'files_saved': files_saved,
        'success': success,
        'rate_limited': False
    }

# ============================================================================
# MAIN ENHANCED SEARCH SUITE - v3.3.0
# ============================================================================

def run_enhanced_search_suite_v330(config: Dict, search_types: Optional[List[str]] = None, 
                                   priority_focus: str = "balanced") -> bool:
    """
    Enhanced search suite with v3.3.0 improvements
    """
    print(f"🚀 Enhanced Search Suite v{__version__} (v3.3.0)")
    print(f"📅 Date: {__date__}")
    print(f"🛑 Immediate stop on rate limiting with enhanced fallback")
    print("=" * 60)
    
    # Validate dependencies
    missing_deps = []
    if not GOOGLESEARCH_AVAILABLE:
        missing_deps.append('googlesearch-python')
    if not BS4_AVAILABLE:
        missing_deps.append('beautifulsoup4')
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        return False
    
    # Load target companies
    target_companies = config.get('target_companies', [])
    if not target_companies:
        print("❌ No target companies found in configuration")
        return False
    
    # Load watchlist for better company matching
    try:
        import pandas as pd
        watchlist_df = pd.read_csv('觀察名單.csv') if os.path.exists('觀察名單.csv') else None
    except Exception:
        watchlist_df = None
    
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
    os.makedirs(config['output']['md_dir'], exist_ok=True)
    os.makedirs(config['output']['csv_dir'], exist_ok=True)
    
    # Process companies with enhanced error handling
    total_files_saved = 0
    successful_companies = 0
    rate_limiting_detected = False
    
    for search_type in search_types:
        print(f"\n🔍 SEARCH TYPE: {search_type.upper()}")
        print("="*40)
        
        try:
            for i, company in enumerate(target_companies, 1):
                print(f"\n[{i}/{len(target_companies)}] Processing company...")
                
                try:
                    result = process_company_search_v330(
                        company, config, search_type, watchlist_df
                    )
                    
                    if result.get('rate_limited'):
                        print(f"   🚨 Rate limiting detected - STOPPING")
                        rate_limiting_detected = True
                        break
                    
                    if result['success']:
                        successful_companies += 1
                        total_files_saved += result['files_saved']
                    
                    # Rate limiting between companies
                    if i < len(target_companies):
                        time.sleep(SEARCH_DELAY)
                        
                except RateLimitException as e:
                    print(f"   🚨 Rate limiting at company {i}: {e}")
                    rate_limiting_detected = True
                    break
                except Exception as e:
                    print(f"   ❌ Error processing company {i}: {e}")
                    continue
            
            if rate_limiting_detected:
                break
                
        except Exception as e:
            print(f"❌ Search type {search_type} failed: {e}")
            continue
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 ENHANCED SEARCH SUITE SUMMARY (v3.3.0)")
    print("="*60)
    print(f"🎯 Companies processed: {successful_companies}/{len(target_companies)}")
    print(f"📄 Total MD files saved: {total_files_saved}")
    
    if rate_limiting_detected:
        print(f"🚨 Rate limiting detected - search stopped early")
        print(f"📄 Recommendation: Process existing {total_files_saved} files")
        return "rate_limited"
    elif total_files_saved > 0:
        print(f"✅ Search completed successfully")
        return True
    else:
        print(f"⚠️ No files saved - check search parameters")
        return False

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for v3.3.0 search"""
    print(f"🔍 Enhanced Search Module v{__version__} (v3.3.0)")
    
    try:
        config = config_module.load_config()
    except:
        config = {
            'target_companies': [],
            'output': {
                'csv_dir': 'data/csv',
                'md_dir': 'data/md'
            }
        }
    
    result = run_enhanced_search_suite_v330(config)
    
    if result == "rate_limited":
        print("🚨 Search stopped due to rate limiting")
        return "rate_limited"
    elif result:
        print("✅ Search completed successfully")
        return True
    else:
        print("❌ Search failed")
        return False

if __name__ == "__main__":
    main()