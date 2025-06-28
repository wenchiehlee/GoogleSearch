"""
search_engine.py - Core Search Logic (v3.5.0)

Version: 3.5.0
Date: 2025-06-28
Author: FactSet Pipeline v3.5.0 - Modular Search Group

v3.5.0 CORE SEARCH ENGINE:
- Intelligent search patterns for FactSet data
- Content processing and data extraction
- Quality assessment and MD file generation (v3.3.x format)
- Integration with api_manager for search execution
- Multiple results support
"""

import re
import json
import hashlib
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup

__version__ = "3.5.0"

# Search patterns for FactSet data discovery
SEARCH_PATTERNS = {
    'primary': [
        'factset {symbol} taiwan earnings estimates',
        'factset {name} eps forecast consensus',
        '{symbol} taiwan factset analyst estimates',
        'site:factset.com {symbol} taiwan',
        'factset {name} {symbol} financial data'
    ],
    'secondary': [
        '{symbol} tw factset target price',
        '{name} taiwan earnings consensus factset', 
        'factset {symbol} financial estimates',
        '{symbol} taiwan analyst forecast 2025',
        '{name} eps consensus estimates'
    ],
    'fallback': [
        '{symbol} taiwan eps estimates 2025 2026',
        '{name} analyst consensus earnings forecast',
        '{symbol} tw target price analyst',
        '{symbol} taiwan financial outlook',
        '{name} earnings guidance forecast'
    ]
}

# Enhanced EPS and financial data patterns
EPS_PATTERNS = [
    r'2025.*?EPS.*?(\d+\.?\d*)',
    r'2026.*?EPS.*?(\d+\.?\d*)', 
    r'2027.*?EPS.*?(\d+\.?\d*)',
    r'2025.*?earnings per share.*?(\d+\.?\d*)',
    r'2026.*?earnings per share.*?(\d+\.?\d*)',
    r'2027.*?earnings per share.*?(\d+\.?\d*)',
    r'EPS.*?2025.*?(\d+\.?\d*)',
    r'EPS.*?2026.*?(\d+\.?\d*)',
    r'EPS.*?2027.*?(\d+\.?\d*)',
    r'consensus.*?eps.*?(\d+\.?\d*)',
    r'forecast.*?eps.*?(\d+\.?\d*)',
    r'estimate.*?eps.*?(\d+\.?\d*)'
]

TARGET_PRICE_PATTERNS = [
    r'target price.*?(\d+\.?\d*)',
    r'price target.*?(\d+\.?\d*)',
    r'fair value.*?(\d+\.?\d*)',
    r'target.*?NT\$(\d+\.?\d*)',
    r'目標價.*?(\d+\.?\d*)',
    r'合理價.*?(\d+\.?\d*)'
]

ANALYST_COUNT_PATTERNS = [
    r'(\d+)\s*analysts?',
    r'consensus of (\d+)',
    r'(\d+)\s*estimates?',
    r'(\d+)\s*分析師',
    r'(\d+)\s*analysts?\s*covering',
    r'based on (\d+) estimates'
]

class BasicQualityScorer:
    """Basic quality assessment for search results"""
    
    def calculate_score(self, financial_data: Dict[str, Any]) -> int:
        """Calculate quality score 0-10"""
        score = 0
        
        # Data completeness (40% weight)
        eps_years = ['2025_eps_avg', '2026_eps_avg', '2027_eps_avg']
        eps_available = sum(1 for year in eps_years if financial_data.get(year))
        score += (eps_available / 3) * 4
        
        # Analyst count (30% weight)
        analyst_count = financial_data.get('analyst_count', 0)
        if analyst_count >= 20:
            score += 3
        elif analyst_count >= 10:
            score += 2
        elif analyst_count >= 5:
            score += 1
        
        # Target price availability (20% weight)
        if financial_data.get('target_price'):
            score += 2
        
        # Data source quality (10% weight)
        source_quality = financial_data.get('source_quality', '')
        if source_quality == 'factset_direct':
            score += 1
        elif source_quality == 'factset_indirect':
            score += 0.5
        
        return min(10, max(0, int(score)))
    
    def get_quality_indicator(self, score: int) -> str:
        """Get quality indicator for score"""
        if score >= 9:
            return '🟢 優秀'
        elif score >= 7:
            return '🟡 良好'
        elif score >= 5:
            return '🟠 普通'
        elif score >= 3:
            return '🔴 不佳'
        else:
            return '⚫ 極差'

class SearchEngine:
    """v3.5.0 Core Search Logic - FactSet Data Discovery"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.search_patterns = SEARCH_PATTERNS
        self.quality_scorer = BasicQualityScorer()
        self.logger = logging.getLogger('search_engine')
    
    def search_company(self, symbol: str, name: str) -> Optional[Dict[str, Any]]:
        """Search single company for financial data (single result)"""
        try:
            self.logger.info(f"Starting search for {symbol} {name}")
            
            # Build search queries
            queries = self._build_search_queries(symbol, name)
            self.logger.debug(f"Built {len(queries)} search queries")
            
            # Execute search cascade
            all_results = self._execute_search_cascade(queries)
            
            if not all_results:
                self.logger.warning(f"No search results found for {symbol}")
                return None
            
            # Extract financial data from results
            financial_data = self._extract_financial_data_from_results(all_results)
            
            # Assess quality
            quality_score = self.quality_scorer.calculate_score(financial_data)
            financial_data['quality_score'] = quality_score
            
            quality_indicator = self.quality_scorer.get_quality_indicator(quality_score)
            self.logger.info(f"Extracted data for {symbol}: quality {quality_score}/10 {quality_indicator}")
            
            return financial_data
            
        except Exception as e:
            self.logger.error(f"Error searching {symbol}: {e}")
            return None
    
    def search_company_multiple(self, symbol: str, name: str, result_count: str = '1') -> List[Dict[str, Any]]:
        """Search single company and return multiple results"""
        try:
            self.logger.info(f"Starting search for {symbol} {name} (requesting {result_count} results)")
            
            # Build search queries
            queries = self._build_search_queries(symbol, name)
            self.logger.debug(f"Built {len(queries)} search queries")
            
            # Execute search cascade
            all_results = self._execute_search_cascade(queries)
            
            if not all_results:
                self.logger.warning(f"No search results found for {symbol}")
                return []
            
            # Determine how many results to return
            if result_count.lower() == 'all':
                max_results = len(all_results)
            else:
                try:
                    max_results = int(result_count)
                except ValueError:
                    max_results = 1
            
            # Take top results up to max_results
            selected_results = all_results[:max_results]
            
            # Process each result separately
            processed_results = []
            for i, result in enumerate(selected_results):
                # Create individual result data
                result_data = self._extract_financial_data_from_single_result(result)
                
                # Assess quality
                quality_score = self.quality_scorer.calculate_score(result_data)
                result_data['quality_score'] = quality_score
                result_data['result_index'] = i + 1
                result_data['total_requested'] = max_results
                
                processed_results.append(result_data)
            
            self.logger.info(f"Processed {len(processed_results)} results for {symbol}")
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error searching {symbol}: {e}")
            return []
    
    def _extract_financial_data_from_single_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from a single search result"""
        financial_data = {}
        
        # Get content from single result
        snippet = result.get('snippet', '')
        title = result.get('title', '')
        content = f"{title} {snippet}"
        
        # Extract financial data
        eps_data = self._extract_eps_forecasts(content)
        financial_data.update(eps_data)
        
        analyst_count = self._extract_analyst_count(content)
        if analyst_count > 0:
            financial_data['analyst_count'] = analyst_count
        
        target_price = self._extract_target_price(content)
        if target_price:
            financial_data['target_price'] = target_price
        
        # Add source info for this single result
        source_info = [{
            'title': title,
            'url': result.get('url', ''),
            'snippet': snippet[:200],
            'content_type': result.get('content_type', 'unknown'),
            'relevance_score': result.get('relevance_score', 0)
        }]
        
        financial_data['sources'] = source_info
        financial_data['extraction_timestamp'] = datetime.now().isoformat()
        financial_data['total_sources'] = 1
        
        # Determine source quality
        content_type = result.get('content_type', 'unknown')
        if content_type == 'factset_direct':
            financial_data['source_quality'] = 'factset_direct'
        elif 'factset' in snippet.lower() or 'factset' in title.lower():
            financial_data['source_quality'] = 'factset_indirect'
        else:
            financial_data['source_quality'] = 'general'
        
        return financial_data
    
    def _build_search_queries(self, symbol: str, name: str) -> List[Dict[str, Any]]:
        """Create search queries for company"""
        queries = []
        
        # Primary FactSet queries (highest priority)
        for pattern in self.search_patterns['primary']:
            query = pattern.format(symbol=symbol, name=name)
            queries.append({
                'query': query,
                'priority': 'high',
                'expected_content': 'factset_direct'
            })
        
        # Secondary queries if primary fails
        for pattern in self.search_patterns['secondary']:
            query = pattern.format(symbol=symbol, name=name)
            queries.append({
                'query': query, 
                'priority': 'medium',
                'expected_content': 'factset_indirect'
            })
        
        # Fallback general queries
        for pattern in self.search_patterns['fallback']:
            query = pattern.format(symbol=symbol, name=name)
            queries.append({
                'query': query,
                'priority': 'low', 
                'expected_content': 'general_estimates'
            })
        
        return queries
    
    def _execute_search_cascade(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute search queries with cascade logic"""
        all_results = []
        
        for query_group in ['high', 'medium', 'low']:
            group_queries = [q for q in queries if q['priority'] == query_group]
            
            self.logger.debug(f"Executing {len(group_queries)} {query_group} priority queries")
            
            for query_info in group_queries:
                try:
                    results = self.api_manager.search(query_info['query'])
                    filtered = self._filter_relevant_results(results)
                    
                    if filtered:
                        self.logger.debug(f"Query returned {len(filtered)} relevant results")
                        all_results.extend(filtered)
                    
                except Exception as e:
                    self.logger.warning(f"Query failed: {query_info['query']} - {e}")
                    continue
        
        self.logger.info(f"Cascade completed with {len(all_results)} total results")
        return all_results
    
    def _filter_relevant_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter for FactSet and relevant content"""
        if not results or 'items' not in results:
            return []
        
        filtered = []
        for item in results['items']:
            # Check for relevant content
            snippet = item.get('snippet', '').lower()
            title = item.get('title', '').lower()
            domain = item.get('domain', '').lower()
            url = item.get('url', '').lower()
            
            # Priority 1: Direct FactSet content
            if ('factset' in snippet or 'factset' in title or 
                'factset.com' in domain or 'factset.com' in url):
                item['content_type'] = 'factset_direct'
                filtered.append(item)
                continue
            
            # Priority 2: Financial data content
            financial_keywords = ['eps', 'earnings', 'analyst', 'target price', 
                                '目標價', '分析師', 'consensus', 'estimate', 'forecast']
            if any(keyword in snippet or keyword in title for keyword in financial_keywords):
                item['content_type'] = 'financial_data'
                filtered.append(item)
                continue
            
            # Priority 3: Taiwan stock content
            taiwan_keywords = ['taiwan', 'tw', 'tse', '台股', '台灣']
            if any(keyword in snippet or keyword in title or keyword in domain 
                   for keyword in taiwan_keywords):
                item['content_type'] = 'taiwan_stock'
                filtered.append(item)
        
        # Sort by content type priority
        content_priority = {'factset_direct': 3, 'financial_data': 2, 'taiwan_stock': 1}
        filtered.sort(key=lambda x: content_priority.get(x.get('content_type', ''), 0), reverse=True)
        
        return filtered
    
    def _has_sufficient_data(self, filtered_results: List[Dict[str, Any]]) -> bool:
        """Check if we have sufficient quality data"""
        if len(filtered_results) < 2:
            return False
        
        # Check for FactSet direct content
        has_factset = any(r.get('content_type') == 'factset_direct' for r in filtered_results)
        
        # Check for multiple financial data sources
        financial_sources = sum(1 for r in filtered_results 
                              if r.get('content_type') in ['factset_direct', 'financial_data'])
        
        return has_factset or financial_sources >= 3
    
    def _extract_financial_data_from_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract financial data from search results"""
        financial_data = {}
        
        # Combine all content for extraction
        all_content = ""
        source_info = []
        
        for result in results:
            snippet = result.get('snippet', '')
            title = result.get('title', '')
            content = f"{title} {snippet}"
            all_content += content + " "
            
            source_info.append({
                'title': title,
                'url': result.get('url', ''),
                'snippet': snippet[:200],
                'content_type': result.get('content_type', 'unknown'),
                'relevance_score': result.get('relevance_score', 0)
            })
        
        # Extract EPS forecasts
        eps_data = self._extract_eps_forecasts(all_content)
        financial_data.update(eps_data)
        
        # Extract analyst count
        analyst_count = self._extract_analyst_count(all_content)
        if analyst_count > 0:
            financial_data['analyst_count'] = analyst_count
        
        # Extract target price
        target_price = self._extract_target_price(all_content)
        if target_price:
            financial_data['target_price'] = target_price
        
        # Add metadata
        financial_data['sources'] = source_info
        financial_data['extraction_timestamp'] = datetime.now().isoformat()
        financial_data['total_sources'] = len(results)
        
        # Determine overall source quality
        has_factset_direct = any(r.get('content_type') == 'factset_direct' for r in results)
        has_factset_indirect = any('factset' in r.get('snippet', '').lower() for r in results)
        
        if has_factset_direct:
            financial_data['source_quality'] = 'factset_direct'
        elif has_factset_indirect:
            financial_data['source_quality'] = 'factset_indirect'
        else:
            financial_data['source_quality'] = 'general'
        
        return financial_data
    
    def _extract_eps_forecasts(self, content: str) -> Dict[str, Any]:
        """Extract EPS forecasts for multiple years"""
        eps_data = {}
        
        for pattern in EPS_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.group(1))
                    
                    # Skip unreasonable values
                    if value < 0 or value > 1000:
                        continue
                    
                    # Determine year from context
                    context = content[max(0, match.start()-100):match.end()+100]
                    
                    if '2025' in context:
                        eps_data.setdefault('2025_values', []).append(value)
                    elif '2026' in context:
                        eps_data.setdefault('2026_values', []).append(value)
                    elif '2027' in context:
                        eps_data.setdefault('2027_values', []).append(value)
                    else:
                        # If no specific year mentioned, assume current year + 1
                        current_year = datetime.now().year
                        next_year = current_year + 1
                        if next_year in [2025, 2026, 2027]:
                            eps_data.setdefault(f'{next_year}_values', []).append(value)
                        
                except (ValueError, IndexError):
                    continue
        
        # Calculate consensus (average) for each year
        consensus = {}
        for year in ['2025', '2026', '2027']:
            values_key = f'{year}_values'
            if values_key in eps_data and eps_data[values_key]:
                values = eps_data[values_key]
                
                # Remove outliers (values more than 2 standard deviations from mean)
                if len(values) > 2:
                    import statistics
                    mean = statistics.mean(values)
                    stdev = statistics.stdev(values)
                    values = [v for v in values if abs(v - mean) <= 2 * stdev]
                
                if values:
                    consensus[f'{year}_eps_avg'] = round(sum(values) / len(values), 2)
                    consensus[f'{year}_eps_high'] = round(max(values), 2)
                    consensus[f'{year}_eps_low'] = round(min(values), 2)
                    consensus[f'{year}_eps_count'] = len(values)
        
        return consensus
    
    def _extract_analyst_count(self, content: str) -> int:
        """Extract number of analysts providing estimates"""
        max_count = 0
        
        for pattern in ANALYST_COUNT_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    count = int(match.group(1))
                    # Reasonable range for analyst count
                    if 1 <= count <= 100:
                        max_count = max(max_count, count)
                except (ValueError, IndexError):
                    continue
        
        return max_count
    
    def _extract_target_price(self, content: str) -> Optional[float]:
        """Extract analyst target price"""
        target_prices = []
        
        for pattern in TARGET_PRICE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.group(1))
                    # Reasonable range for Taiwan stock prices
                    if 1 <= price <= 10000:
                        target_prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        if target_prices:
            # Return median target price to avoid outliers
            target_prices.sort()
            n = len(target_prices)
            if n % 2 == 0:
                return round((target_prices[n//2-1] + target_prices[n//2]) / 2, 2)
            else:
                return round(target_prices[n//2], 2)
        
        return None
    
    def generate_md_content(self, symbol: str, name: str, financial_data: Dict[str, Any], metadata: Dict[str, Any], result_index: int = 1) -> str:
        """Generate MD file content in v3.3.x format (YAML + raw content)"""
        
        # Get the source for content
        sources = financial_data.get('sources', [])
        if not sources:
            return self._generate_no_content_md(symbol, name, financial_data, result_index)
        
        # Use the source (should be only one for individual results)
        source = sources[0]
        url = source.get('url', '')
        title = source.get('title', url)
        snippet = source.get('snippet', '')
        
        # Try to fetch full content from the URL
        full_content = self._fetch_page_content(url)
        if not full_content:
            full_content = snippet
        
        # Calculate quality score
        quality_score = financial_data.get('quality_score', 0)
        
        # Generate file ID
        file_id = hashlib.md5(f"{symbol}_{datetime.now().isoformat()}_{result_index}".encode()).hexdigest()[:8]
        
        # Generate search query for metadata
        search_query = f"{name} {symbol} factset EPS 預估"
        if result_index > 1:
            search_query += f" result_{result_index}"
        
        # Create YAML header
        yaml_header = f"""---
url: {url}
title: {title}
quality_score: {quality_score}
company: {name}
stock_code: {symbol}
extracted_date: {datetime.now().isoformat()}
search_query: {search_query}
result_index: {result_index}
version: v3.5.0
---"""
        
        # Combine YAML header with content
        md_content = yaml_header + "\n\n" + full_content
        
        return md_content
    
    def _fetch_page_content(self, url: str) -> str:
        """Fetch full page content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML and extract text content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text_content
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch content from {url}: {e}")
            return ""
    
    def _generate_no_content_md(self, symbol: str, name: str, financial_data: Dict[str, Any], result_index: int = 1) -> str:
        """Generate MD file when no content is available"""
        quality_score = financial_data.get('quality_score', 0)
        file_id = hashlib.md5(f"{symbol}_{datetime.now().isoformat()}_{result_index}".encode()).hexdigest()[:8]
        search_query = f"{name} {symbol} factset EPS 預估"
        if result_index > 1:
            search_query += f" result_{result_index}"
        
        yaml_header = f"""---
url: 
title: No content found
quality_score: {quality_score}
company: {name}
stock_code: {symbol}
extracted_date: {datetime.now().isoformat()}
search_query: {search_query}
result_index: {result_index}
version: v3.5.0
---"""
        
        content = f"""# {symbol} {name} - No FactSet Data Found (Result {result_index})

Search completed but no suitable content was found for this company.

## Search Information
- **Search Query**: {search_query}
- **Quality Score**: {quality_score}/10
- **Total Sources Searched**: {financial_data.get('total_sources', 0)}
- **Result Index**: {result_index}

## Financial Data Extracted
```json
{json.dumps(financial_data, indent=2, ensure_ascii=False, default=str)}
```
"""
        
        return yaml_header + "\n\n" + content
    
    def assess_data_quality(self, financial_data: Dict[str, Any]) -> int:
        """Assess data quality on 0-10 scale"""
        return self.quality_scorer.calculate_score(financial_data)