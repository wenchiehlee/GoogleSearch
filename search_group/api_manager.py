"""
api_manager.py - API Management & Rate Limiting (v3.5.0)

Version: 3.5.0
Date: 2025-06-28
Author: FactSet Pipeline v3.5.0 - Modular Search Group

v3.5.0 API MANAGEMENT:
- Google Search API integration
- Intelligent rate limiting and backoff
- Error handling and quotas
- Search result caching
- Performance monitoring
"""

import os
import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    # Create a placeholder for type hints
    HttpError = Exception

__version__ = "3.5.0"

class QuotaExceededException(Exception):
    """Google API quota exceeded"""
    pass

class SearchAPIException(Exception):
    """General search API error"""
    pass

class RateLimiter:
    """Intelligent rate limiting for Google Search API"""
    
    def __init__(self, calls_per_second: float = 1.0, calls_per_day: int = 100):
        self.calls_per_second = calls_per_second
        self.calls_per_day = calls_per_day
        self.last_call_time = 0
        self.daily_calls = 0
        self.daily_reset_time = 0
        
        # Initialize daily reset time
        self._reset_daily_counter()
        
        self.logger = logging.getLogger('rate_limiter')
        self.logger.info(f"Rate limiter initialized: {calls_per_second} calls/sec, {calls_per_day} calls/day")
        
    def _reset_daily_counter(self):
        """Reset daily counter at midnight"""
        now = datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self.daily_reset_time = tomorrow.timestamp()
        self.daily_calls = 0
        
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        now = time.time()
        
        # Check daily reset
        if now >= self.daily_reset_time:
            self._reset_daily_counter()
            self.logger.info("Daily quota reset")
        
        # Check daily quota
        if self.daily_calls >= self.calls_per_day:
            remaining_time = self.daily_reset_time - now
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            raise QuotaExceededException(
                f"Daily quota of {self.calls_per_day} calls exceeded. "
                f"Resets in {hours}h {minutes}m"
            )
        
        # Check rate limiting
        time_since_last = now - self.last_call_time
        min_interval = 1.0 / self.calls_per_second
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
        self.daily_calls += 1
        
        remaining_quota = self.calls_per_day - self.daily_calls
        self.logger.debug(f"API call #{self.daily_calls}, {remaining_quota} remaining today")

class SearchCache:
    """Simple file-based search result cache"""
    
    def __init__(self, cache_dir: str = 'cache/search/', max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.max_age = max_age_hours * 3600
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('search_cache')
        self.logger.info(f"Cache initialized: {cache_dir}, max age {max_age_hours}h")
        
        # Clean old cache files on startup
        self._clean_old_cache()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result for query"""
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age < self.max_age:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                    self.logger.debug(f"Cache hit for query: {query[:50]}...")
                    return result
                except Exception as e:
                    self.logger.warning(f"Cache read error: {e}")
                    # Remove corrupted cache file
                    cache_file.unlink(missing_ok=True)
            else:
                self.logger.debug(f"Cache expired for query: {query[:50]}...")
                cache_file.unlink(missing_ok=True)
        
        self.logger.debug(f"Cache miss for query: {query[:50]}...")
        return None
    
    def set(self, query: str, result: Dict[str, Any]):
        """Cache search result"""
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            # Add cache metadata
            cached_result = {
                'query': query,
                'cached_at': datetime.now().isoformat(),
                'data': result
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_result, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.debug(f"Cached result for query: {query[:50]}...")
            
        except Exception as e:
            self.logger.warning(f"Failed to cache result: {e}")
    
    def _clean_old_cache(self):
        """Clean expired cache files"""
        try:
            current_time = time.time()
            cleaned_count = 0
            
            for cache_file in self.cache_dir.glob("*.json"):
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > self.max_age:
                    cache_file.unlink(missing_ok=True)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned {cleaned_count} expired cache files")
                
        except Exception as e:
            self.logger.warning(f"Cache cleanup error: {e}")
    
    def clear_all(self):
        """Clear all cache files"""
        try:
            cleared_count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)
                cleared_count += 1
            
            self.logger.info(f"Cleared {cleared_count} cache files")
            
        except Exception as e:
            self.logger.warning(f"Cache clear error: {e}")

class APIStats:
    """Track API usage statistics"""
    
    def __init__(self):
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'quota_exceeded': 0,
            'start_time': datetime.now().isoformat(),
            'last_call_time': None,
            'successful_calls': 0,
            'failed_calls': 0
        }
        
        self.logger = logging.getLogger('api_stats')
        self.logger.info("API statistics tracking initialized")
    
    def record_api_call(self, results_count: int):
        """Record successful API call"""
        self.stats['total_calls'] += 1
        self.stats['successful_calls'] += 1
        self.stats['cache_misses'] += 1
        self.stats['last_call_time'] = datetime.now().isoformat()
        self.stats['last_results_count'] = results_count
        
        self.logger.debug(f"API call recorded: {results_count} results")
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.stats['cache_hits'] += 1
        self.logger.debug("Cache hit recorded")
    
    def record_error(self, error: Exception):
        """Record error"""
        self.stats['errors'] += 1
        self.stats['failed_calls'] += 1
        
        error_str = str(error).lower()
        if 'quota' in error_str or 'quotaexceeded' in error_str:
            self.stats['quota_exceeded'] += 1
            
        self.logger.warning(f"API error recorded: {error}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get statistics summary"""
        total_requests = self.stats['total_calls'] + self.stats['cache_hits']
        cache_hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        success_rate = (self.stats['successful_calls'] / self.stats['total_calls'] * 100) if self.stats['total_calls'] > 0 else 0
        
        return {
            'total_requests': total_requests,
            'api_calls': self.stats['total_calls'],
            'successful_calls': self.stats['successful_calls'],
            'failed_calls': self.stats['failed_calls'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'success_rate': f"{success_rate:.1f}%",
            'errors': self.stats['errors'],
            'quota_exceeded': self.stats['quota_exceeded'],
            'uptime': self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> str:
        """Calculate uptime since start"""
        start = datetime.fromisoformat(self.stats['start_time'])
        uptime = datetime.now() - start
        return str(uptime).split('.')[0]  # Remove microseconds

class APIManager:
    """v3.5.0 Google Search API Management - Simplified & Robust"""
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.get('api.google_api_key')
        self.cse_id = config.get('api.google_cse_id')
        
        # Initialize components
        rate_limit = 1.0 / config.get('search.rate_limit_delay', 1.0)  # Convert delay to calls per second
        daily_quota = config.get('search.daily_quota', 100)
        self.rate_limiter = RateLimiter(rate_limit, daily_quota)
        
        cache_dir = config.get('files.cache_dir', 'cache/search/')
        cache_hours = config.get('caching.max_age_hours', 24)
        self.cache = SearchCache(cache_dir, cache_hours) if config.get('caching.enabled', True) else None
        
        self.stats = APIStats()
        
        self.logger = logging.getLogger('api_manager')
        
        # Validate API access
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API client not available. Install with: pip install google-api-python-client")
        
        if not self.api_key or not self.cse_id:
            raise ValueError("Google API key and CSE ID required")
        
        self.logger.info(f"API Manager v{__version__} initialized")
    
    def validate_api_access(self) -> bool:
        """Validate API credentials"""
        try:
            self.logger.info("Validating API access...")
            
            # Test with a simple query
            test_result = self.search("test factset", num_results=1)
            
            if test_result and 'items' in test_result:
                self.logger.info("API validation successful")
                return True
            else:
                self.logger.error("API validation failed: no results returned")
                return False
                
        except Exception as e:
            self.logger.error(f"API validation failed: {e}")
            return False
    
    def get_api_status(self) -> str:
        """Get current API status"""
        summary = self.stats.get_summary()
        
        if summary['quota_exceeded'] > 0:
            return "quota_exceeded"
        elif summary['errors'] > summary['api_calls'] * 0.5 and summary['api_calls'] > 0:
            return "error_prone"
        elif summary['api_calls'] > 0:
            return "operational"
        else:
            return "ready"
    
    def search(self, query: str, num_results: int = 10) -> Optional[Dict[str, Any]]:
        """Execute Google Custom Search with full protection"""
        
        # Check cache first (if enabled)
        if self.cache:
            cached_result = self.cache.get(query)
            if cached_result:
                self.stats.record_cache_hit()
                return cached_result.get('data', cached_result)  # Handle both old and new cache format
        
        # Optimize query for better results
        optimized_query = self._optimize_query(query)
        self.logger.debug(f"Optimized query: {optimized_query}")
        
        # Rate limiting protection
        try:
            self.rate_limiter.wait_if_needed()
        except QuotaExceededException as e:
            self.stats.record_error(e)
            raise
        
        try:
            # Execute actual API call
            service = build('customsearch', 'v1', developerKey=self.api_key)
            
            search_params = {
                'q': optimized_query,
                'cx': self.cse_id,
                'num': min(num_results, 10),  # Google API max is 10
                'dateRestrict': self.config.get('search.date_restrict', 'y1'),
                'lr': self.config.get('search.language', 'lang_zh-TW|lang_en'),
                'safe': self.config.get('search.safe_search', 'off'),
                'fields': 'items(title,snippet,link,displayLink),searchInformation(totalResults,searchTime)'
            }
            
            self.logger.debug(f"Executing search with params: {search_params}")
            
            result = service.cse().list(**search_params).execute()
            
            # Process results
            processed_result = self._process_search_result(result, query)
            
            # Cache result (if enabled)
            if self.cache:
                self.cache.set(query, processed_result)
            
            # Record stats
            items_count = len(processed_result.get('items', []))
            self.stats.record_api_call(items_count)
            
            self.logger.info(f"Search completed: {items_count} results for '{query[:50]}...'")
            
            return processed_result
            
        except Exception as e:
            self.stats.record_error(e)
            
            # Check if it's an HttpError (only if Google API is available)
            if GOOGLE_API_AVAILABLE and hasattr(e, 'resp'):
                if e.resp.status == 429 or 'quotaExceeded' in str(e):
                    raise QuotaExceededException(f"Google API quota exceeded: {e}")
                elif 'rateLimitExceeded' in str(e):
                    self.logger.warning(f"Rate limit exceeded: {e}")
                    self._handle_rate_limit_exceeded(e)
                    # Retry once after backoff
                    return self.search(query, num_results)
                else:
                    raise SearchAPIException(f"Search API error: {e}")
            else:
                # Handle as general exception if not HttpError
                if 'quota' in str(e).lower() or 'rate' in str(e).lower():
                    raise QuotaExceededException(f"API limit exceeded: {e}")
                else:
                    raise SearchAPIException(f"Unexpected search error: {e}")
    
    def batch_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple searches with rate limiting"""
        results = []
        
        self.logger.info(f"Starting batch search for {len(queries)} queries")
        
        for i, query in enumerate(queries, 1):
            try:
                self.logger.debug(f"Batch search {i}/{len(queries)}: {query[:50]}...")
                result = self.search(query)
                results.append(result)
                
            except QuotaExceededException:
                self.logger.warning(f"Quota exceeded at query {i}/{len(queries)}")
                break
            except Exception as e:
                self.logger.warning(f"Query {i} failed: {e}")
                results.append(None)
        
        successful = sum(1 for r in results if r is not None)
        self.logger.info(f"Batch search completed: {successful}/{len(queries)} successful")
        
        return results
    
    def _optimize_query(self, query: str) -> str:
        """Optimize query for better FactSet results"""
        
        # Don't modify if already optimized
        if 'site:' in query and ('factset' in query.lower() or 'OR' in query):
            return query
        
        # Add financial keywords if missing
        financial_keywords = ['eps', 'earnings', 'forecast', 'estimate', 'consensus', 'analyst']
        has_financial = any(keyword in query.lower() for keyword in financial_keywords)
        
        if not has_financial:
            query += ' earnings estimates'
        
        # Enhance with FactSet preference (but don't be too restrictive)
        if 'factset' not in query.lower():
            # Use OR to broaden search rather than restrict
            query = f'({query}) (factset OR "earnings estimate" OR "analyst consensus")'
        
        return query
    
    def _process_search_result(self, raw_result: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Process and clean search results"""
        processed = {
            'query_info': {
                'original_query': original_query,
                'total_results': raw_result.get('searchInformation', {}).get('totalResults', '0'),
                'search_time': raw_result.get('searchInformation', {}).get('searchTime', 0),
                'timestamp': datetime.now().isoformat()
            },
            'items': []
        }
        
        items = raw_result.get('items', [])
        self.logger.debug(f"Processing {len(items)} raw search results")
        
        for item in items:
            processed_item = {
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
                'url': item.get('link', ''),
                'domain': item.get('displayLink', ''),
                'relevance_score': self._calculate_relevance_score(item),
                'has_factset_content': self._has_factset_content(item),
                'has_financial_content': self._has_financial_content(item)
            }
            processed['items'].append(processed_item)
        
        # Sort by relevance score (highest first)
        processed['items'].sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Log top results for debugging
        if processed['items']:
            top_result = processed['items'][0]
            self.logger.debug(f"Top result: score={top_result['relevance_score']}, "
                            f"domain={top_result['domain']}, title={top_result['title'][:50]}...")
        
        return processed
    
    def _calculate_relevance_score(self, item: Dict[str, Any]) -> int:
        """Calculate relevance score for search result"""
        score = 0
        
        title = item.get('title', '').lower()
        snippet = item.get('snippet', '').lower()
        domain = item.get('displayLink', '').lower()
        
        # Domain scoring (high value for known financial sites)
        if 'factset.com' in domain:
            score += 10
        elif any(site in domain for site in ['bloomberg.com', 'reuters.com', 'marketwatch.com']):
            score += 8
        elif any(site in domain for site in ['cnyes.com', 'moneydj.com', 'wealth.com.tw']):
            score += 6
        elif any(site in domain for site in ['yahoo.com', 'investing.com']):
            score += 4
        
        # Content scoring (financial terms)
        high_value_terms = ['factset', 'eps', 'earnings forecast', 'consensus estimate', 'analyst']
        for term in high_value_terms:
            if term in title:
                score += 3
            if term in snippet:
                score += 2
        
        # Financial data indicators
        financial_indicators = ['2025', '2026', '2027', 'target price', 'price target', '目標價', '分析師']
        for indicator in financial_indicators:
            if indicator in snippet:
                score += 1
        
        # Taiwan-specific content
        taiwan_indicators = ['taiwan', 'tw', 'tse', '台股', '台灣']
        for indicator in taiwan_indicators:
            if indicator in title or indicator in snippet:
                score += 1
        
        return score
    
    def _has_factset_content(self, item: Dict[str, Any]) -> bool:
        """Check if item contains FactSet content"""
        title = item.get('title', '').lower()
        snippet = item.get('snippet', '').lower()
        domain = item.get('displayLink', '').lower()
        
        return ('factset' in title or 'factset' in snippet or 'factset.com' in domain)
    
    def _has_financial_content(self, item: Dict[str, Any]) -> bool:
        """Check if item contains financial content"""
        title = item.get('title', '').lower()
        snippet = item.get('snippet', '').lower()
        
        financial_terms = ['eps', 'earnings', 'analyst', 'target price', 'forecast', 
                          'estimate', 'consensus', '分析師', '目標價', '預估']
        
        return any(term in title or term in snippet for term in financial_terms)
    
    def _handle_rate_limit_exceeded(self, error: Union[Exception, "HttpError"]):
        """Handle rate limit exceeded errors"""
        backoff_seconds = min(
            self.config.get('search.max_backoff_seconds', 300),
            60  # Start with 1 minute
        )
        
        self.logger.warning(f"Rate limit exceeded, backing off for {backoff_seconds}s: {error}")
        time.sleep(backoff_seconds)