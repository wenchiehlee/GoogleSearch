"""
api_manager.py - API Management & Rate Limiting with Key Rotation (v3.5.1)

Version: 3.5.1
Date: 2025-07-01
Author: FactSet Pipeline v3.5.1 - Enhanced with API Key Rotation

v3.5.1 ENHANCEMENTS:
- Multiple Google Search API key support (up to 7 keys)
- Automatic key rotation on quota exceeded (429 errors)
- Enhanced error handling and recovery
- Key status tracking and monitoring
- Intelligent fallback and retry logic
"""

import os
import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    # Create a placeholder for type hints
    HttpError = Exception

__version__ = "3.5.1"

class QuotaExceededException(Exception):
    """Google API quota exceeded"""
    pass

class AllKeysExhaustedException(Exception):
    """All available API keys have been exhausted"""
    pass

class SearchAPIException(Exception):
    """General search API error"""
    pass

class APIKeyManager:
    """Manages multiple Google API keys and automatic rotation"""
    
    def __init__(self, api_keys: List[str], cse_ids: List[str]):
        self.api_keys = api_keys
        self.cse_ids = cse_ids
        self.current_key_index = 0
        self.exhausted_keys = set()
        self.key_stats = {}
        
        # Initialize stats for each key
        for i, key in enumerate(api_keys):
            self.key_stats[i] = {
                'calls_made': 0,
                'quota_exceeded_at': None,
                'last_used': None,
                'total_errors': 0,
                'is_exhausted': False
            }
        
        self.logger = logging.getLogger('api_key_manager')
        self.logger.info(f"API Key Manager initialized with {len(api_keys)} keys")
        
        # Validate we have at least one key
        if not api_keys or not any(key.strip() for key in api_keys):
            raise ValueError("At least one valid API key is required")
    
    def get_current_credentials(self) -> Tuple[str, str]:
        """Get current API key and CSE ID"""
        if self.current_key_index >= len(self.api_keys):
            raise AllKeysExhaustedException("All API keys have been exhausted")
        
        api_key = self.api_keys[self.current_key_index]
        cse_id = self.cse_ids[self.current_key_index] if self.current_key_index < len(self.cse_ids) else self.cse_ids[0]
        
        return api_key, cse_id
    
    def mark_key_exhausted(self, error_details: str = ""):
        """Mark current key as exhausted and rotate to next"""
        self.exhausted_keys.add(self.current_key_index)
        self.key_stats[self.current_key_index].update({
            'quota_exceeded_at': datetime.now().isoformat(),
            'is_exhausted': True,
            'total_errors': self.key_stats[self.current_key_index]['total_errors'] + 1
        })
        
        old_index = self.current_key_index
        self.logger.warning(f"Key {old_index + 1} exhausted: {error_details}")
        
        # Find next available key
        available_keys = [i for i in range(len(self.api_keys)) if i not in self.exhausted_keys]
        
        if not available_keys:
            self.logger.error("All API keys have been exhausted!")
            raise AllKeysExhaustedException(
                f"All {len(self.api_keys)} API keys have exceeded their quota. "
                f"Please wait for quota reset or add more keys."
            )
        
        self.current_key_index = available_keys[0]
        self.logger.info(f"Rotated from key {old_index + 1} to key {self.current_key_index + 1}")
        self.logger.info(f"Remaining keys: {len(available_keys)}")
    
    def record_successful_call(self):
        """Record a successful API call"""
        self.key_stats[self.current_key_index].update({
            'calls_made': self.key_stats[self.current_key_index]['calls_made'] + 1,
            'last_used': datetime.now().isoformat()
        })
    
    def record_error(self):
        """Record an API error"""
        self.key_stats[self.current_key_index]['total_errors'] += 1
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status of all API keys"""
        available_keys = len(self.api_keys) - len(self.exhausted_keys)
        
        summary = {
            'total_keys': len(self.api_keys),
            'available_keys': available_keys,
            'exhausted_keys': len(self.exhausted_keys),
            'current_key_index': self.current_key_index + 1,  # Human readable (1-based)
            'key_details': []
        }
        
        for i, key in enumerate(self.api_keys):
            stats = self.key_stats[i]
            key_summary = {
                'key_number': i + 1,
                'api_key_preview': f"{key[:10]}...{key[-4:]}" if len(key) > 14 else key,
                'calls_made': stats['calls_made'],
                'total_errors': stats['total_errors'],
                'is_exhausted': stats['is_exhausted'],
                'is_current': i == self.current_key_index,
                'quota_exceeded_at': stats['quota_exceeded_at'],
                'last_used': stats['last_used']
            }
            summary['key_details'].append(key_summary)
        
        return summary

class RateLimiter:
    """Intelligent rate limiting for Google Search API with key rotation support"""
    
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
        
        # Check rate limiting (but not daily quota - let key rotation handle that)
        time_since_last = now - self.last_call_time
        min_interval = 1.0 / self.calls_per_second
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
        self.daily_calls += 1
        
        # Log progress but don't enforce daily limit (key rotation handles this)
        self.logger.debug(f"API call #{self.daily_calls}")

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
    """Track API usage statistics with key rotation support"""
    
    def __init__(self):
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'quota_exceeded': 0,
            'key_rotations': 0,
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
    
    def record_key_rotation(self):
        """Record key rotation event"""
        self.stats['key_rotations'] += 1
        self.logger.info("Key rotation recorded")
    
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
            'key_rotations': self.stats['key_rotations'],
            'uptime': self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> str:
        """Calculate uptime since start"""
        start = datetime.fromisoformat(self.stats['start_time'])
        uptime = datetime.now() - start
        return str(uptime).split('.')[0]  # Remove microseconds

class APIManager:
    """v3.5.1 Google Search API Management with Automatic Key Rotation"""
    
    def __init__(self, config):
        # Initialize logger FIRST before any operations that might use it
        self.logger = logging.getLogger('api_manager')
        
        self.config = config
        
        # Load multiple API keys and CSE IDs
        api_keys, cse_ids = self._load_multiple_credentials()
        
        # Initialize key manager
        self.key_manager = APIKeyManager(api_keys, cse_ids)
        
        # Initialize components
        rate_limit = 1.0 / config.get('search.rate_limit_delay', 1.0)
        daily_quota = config.get('search.daily_quota', 100)
        self.rate_limiter = RateLimiter(rate_limit, daily_quota)
        
        cache_dir = config.get('files.cache_dir', 'cache/search/')
        cache_hours = config.get('caching.max_age_hours', 24)
        self.cache = SearchCache(cache_dir, cache_hours) if config.get('caching.enabled', True) else None
        
        self.stats = APIStats()
        
        # Validate API access
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API client not available. Install with: pip install google-api-python-client")
        
        self.logger.info(f"API Manager v{__version__} initialized with {len(api_keys)} API keys")
    
    def _load_multiple_credentials(self) -> Tuple[List[str], List[str]]:
        """Load multiple API keys and CSE IDs from config"""
        api_keys = []
        cse_ids = []
        
        # Load primary credentials
        primary_key = self.config.get('api.google_api_key')
        primary_cse = self.config.get('api.google_cse_id')
        
        if primary_key and primary_key.strip():
            api_keys.append(primary_key.strip())
            if primary_cse and primary_cse.strip():
                cse_ids.append(primary_cse.strip())
        
        # Load additional keys (1-6)
        for i in range(1, 7):
            key = self.config.get(f'api.google_api_key{i}')
            cse = self.config.get(f'api.google_cse_id{i}')
            
            if key and key.strip():
                api_keys.append(key.strip())
                if cse and cse.strip():
                    cse_ids.append(cse.strip())
        
        # Ensure we have at least one CSE ID (can reuse if needed)
        if not cse_ids and primary_cse:
            cse_ids.append(primary_cse.strip())
        
        # Validate we have credentials
        if not api_keys:
            raise ValueError("No valid Google API keys found. Check your environment variables.")
        
        if not cse_ids:
            raise ValueError("No valid Google CSE IDs found. Check your environment variables.")
        
        # Use print instead of logger since logger isn't initialized yet
        print(f"✅ Loaded {len(api_keys)} API keys and {len(cse_ids)} CSE IDs for rotation")
        return api_keys, cse_ids
    
    def validate_api_access(self) -> bool:
        """Validate API credentials"""
        try:
            self.logger.info("Validating API access with key rotation support...")
            
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
        key_status = self.key_manager.get_status_summary()
        
        if key_status['available_keys'] == 0:
            return "all_keys_exhausted"
        elif summary['quota_exceeded'] > 0:
            return "quota_managed"  # We have key rotation to handle this
        elif summary['errors'] > summary['api_calls'] * 0.5 and summary['api_calls'] > 0:
            return "error_prone"
        elif summary['api_calls'] > 0:
            return "operational"
        else:
            return "ready"
    
    def search(self, query: str, num_results: int = 10) -> Optional[Dict[str, Any]]:
        """Execute Google Custom Search with automatic key rotation"""
        
        # Check cache first (if enabled)
        if self.cache:
            cached_result = self.cache.get(query)
            if cached_result:
                self.stats.record_cache_hit()
                return cached_result.get('data', cached_result)
        
        # Optimize query for better results
        optimized_query = self._optimize_query(query)
        self.logger.debug(f"Optimized query: {optimized_query}")
        
        # Rate limiting protection
        try:
            self.rate_limiter.wait_if_needed()
        except QuotaExceededException as e:
            self.stats.record_error(e)
            raise
        
        # Retry logic with automatic key rotation
        max_retries = min(3, self.key_manager.get_status_summary()['available_keys'])
        
        for attempt in range(max_retries):
            try:
                # Get current credentials
                api_key, cse_id = self.key_manager.get_current_credentials()
                
                # Execute API call
                service = build('customsearch', 'v1', developerKey=api_key)
                
                search_params = {
                    'q': optimized_query,
                    'cx': cse_id,
                    'num': min(num_results, 10),
                    'dateRestrict': self.config.get('search.date_restrict', 'y1'),
                    'lr': self.config.get('search.language', 'lang_zh-TW|lang_en'),
                    'safe': self.config.get('search.safe_search', 'off'),
                    'fields': 'items(title,snippet,link,displayLink),searchInformation(totalResults,searchTime)'
                }
                
                self.logger.debug(f"Executing search with key {self.key_manager.current_key_index + 1}: {search_params}")
                
                result = service.cse().list(**search_params).execute()
                
                # Process results
                processed_result = self._process_search_result(result, query)
                
                # Record successful call
                self.key_manager.record_successful_call()
                
                # Cache result (if enabled)
                if self.cache:
                    self.cache.set(query, processed_result)
                
                # Record stats
                items_count = len(processed_result.get('items', []))
                self.stats.record_api_call(items_count)
                
                current_key = self.key_manager.current_key_index + 1
                self.logger.info(f"Search completed with key {current_key}: {items_count} results for '{query[:50]}...'")
                
                return processed_result
                
            except Exception as e:
                self.stats.record_error(e)
                self.key_manager.record_error()
                
                # Check if it's a quota exceeded error (429)
                if GOOGLE_API_AVAILABLE and hasattr(e, 'resp'):
                    if (e.resp.status == 429 or 
                        'quotaExceeded' in str(e) or 
                        'Quota exceeded' in str(e)):
                        
                        self.logger.warning(f"Quota exceeded on key {self.key_manager.current_key_index + 1}, attempting rotation...")
                        
                        try:
                            # Mark current key as exhausted and rotate
                            self.key_manager.mark_key_exhausted(str(e))
                            self.stats.record_key_rotation()
                            
                            # Continue to next attempt with new key
                            self.logger.info(f"Retrying with key {self.key_manager.current_key_index + 1} (attempt {attempt + 1}/{max_retries})")
                            continue
                            
                        except AllKeysExhaustedException as all_keys_error:
                            self.logger.error("All API keys exhausted!")
                            raise QuotaExceededException(str(all_keys_error))
                    
                    elif 'rateLimitExceeded' in str(e):
                        self.logger.warning(f"Rate limit exceeded: {e}")
                        self._handle_rate_limit_exceeded(e)
                        # Retry with same key after backoff
                        continue
                    else:
                        # Other API error
                        if attempt == max_retries - 1:  # Last attempt
                            raise SearchAPIException(f"Search API error: {e}")
                        else:
                            self.logger.warning(f"API error on attempt {attempt + 1}: {e}")
                            continue
                else:
                    # Handle as general exception
                    if 'quota' in str(e).lower() or 'rate' in str(e).lower():
                        if attempt == max_retries - 1:
                            raise QuotaExceededException(f"API limit exceeded: {e}")
                        else:
                            continue
                    else:
                        if attempt == max_retries - 1:
                            raise SearchAPIException(f"Unexpected search error: {e}")
                        else:
                            continue
        
        # If we get here, all retries failed
        raise SearchAPIException(f"Search failed after {max_retries} attempts")
    
    def batch_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple searches with key rotation support"""
        results = []
        
        self.logger.info(f"Starting batch search for {len(queries)} queries with key rotation")
        
        for i, query in enumerate(queries, 1):
            try:
                self.logger.debug(f"Batch search {i}/{len(queries)}: {query[:50]}...")
                result = self.search(query)
                results.append(result)
                
            except AllKeysExhaustedException:
                self.logger.error(f"All keys exhausted at query {i}/{len(queries)}")
                break
            except QuotaExceededException:
                self.logger.warning(f"Quota management failed at query {i}/{len(queries)}")
                break
            except Exception as e:
                self.logger.warning(f"Query {i} failed: {e}")
                results.append(None)
        
        successful = sum(1 for r in results if r is not None)
        self.logger.info(f"Batch search completed: {successful}/{len(queries)} successful")
        
        return results
    
    def get_key_status(self) -> Dict[str, Any]:
        """Get comprehensive key status"""
        return self.key_manager.get_status_summary()
    
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
                'timestamp': datetime.now().isoformat(),
                'api_key_used': self.key_manager.current_key_index + 1
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
        
        # Log top result for debugging
        if processed['items']:
            top_result = processed['items'][0]
            current_key = self.key_manager.current_key_index + 1
            self.logger.debug(f"Top result (key {current_key}): score={top_result['relevance_score']}, "
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