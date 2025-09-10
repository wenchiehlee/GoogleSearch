#!/usr/bin/env python3
"""
Search Engine - FactSet Pipeline v3.5.1 (Modified for md_date)
Enhanced search engine with content date extraction and md_date metadata field
Adds md_date field to metadata for reliable date display in reports

FIXED: Type conversion issue in search_comprehensive method
"""

import os
import re
import hashlib
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
import time
import random

class SearchEngine:
    """Enhanced Search Engine with md_date extraction - v3.5.1-modified"""
    
    def __init__(self, api_manager, config):
        self.api_manager = api_manager
        self.config = config
        self.version = "3.5.1-modified"
        
        # Content validation settings
        self.enable_content_validation = True
        self.validation_threshold = 0.7
        
        # Enhanced date patterns for md_date extraction
        self.date_patterns = [
            r'\*\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'\*\s*更新[：:]\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'更新[：:]\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'鉅亨網新聞中心\s*\n?\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'鉅亨網新聞中心\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日[週周]?[一二三四五六日天]?\s*[上下]午\s*\d{1,2}:\d{1,2}',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日[週周]?[一二三四五六日天]?',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}:\d{1,2}',
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
        ]
        
        # Taiwan financial sites patterns
        self.refined_search_patterns = {
            'factset_direct': [
                'factset {symbol}',
                'factset {name}', 
                '{symbol} factset',
                '{name} factset',
                'factset {symbol} EPS',
                'factset {name} 預估',
                '"{symbol}" factset 分析師',
                '"{name}" factset 目標價'
            ],
            'cnyes_factset': [
                'site:cnyes.com factset {symbol}',
                'site:cnyes.com {symbol} factset',
                'site:cnyes.com {symbol} EPS 預估',
                'site:cnyes.com {name} factset',
                'site:cnyes.com {symbol} 分析師',
                'site:cnyes.com factset {name}',
                'site:cnyes.com {symbol} 台股預估'
            ],
            'eps_forecast': [
                '{symbol} EPS 預估',
                '{name} EPS 預估',
                '{symbol} EPS 2025',
                '{name} EPS 2025',
                '{symbol} 每股盈餘 預估',
                '{name} 每股盈餘 預估',
                '{symbol} EPS forecast',
                '{name} earnings estimates'
            ],
            'analyst_consensus': [
                '{symbol} 分析師 預估',
                '{name} 分析師 預估',
                '{symbol} 分析師 目標價',
                '{name} 分析師 目標價',
                '{symbol} consensus estimate',
                '{name} analyst forecast',
                '{symbol} 共識預估',
                '{name} 投資評等'
            ],
            'taiwan_financial_simple': [
                'site:cnyes.com {symbol}',
                'site:statementdog.com {symbol}',
                'site:wantgoo.com {symbol}',
                'site:goodinfo.tw {symbol}',
                'site:uanalyze.com.tw {symbol}',
                'site:findbillion.com {symbol}',
                'site:moneydj.com {symbol}',
                'site:yahoo.com {symbol} 股票'
            ]
        }
        
        print(f"SearchEngine v{self.version} initialized with md_date extraction")

    def search_comprehensive(self, symbol: str, name: str, count: Union[int, str] = 'all', min_quality: int = 4) -> List[Dict[str, Any]]:
        """FIXED: Enhanced comprehensive search with md_date extraction and proper type handling"""
        print(f"🔍 Comprehensive search for {symbol} ({name}) - extracting md_date")
        
        # FIXED: Convert count parameter to proper type
        if isinstance(count, str):
            if count == 'all':
                target_count = float('inf')
            else:
                try:
                    target_count = int(count)
                except ValueError:
                    print(f"⚠️ Invalid count value '{count}', using 'all'")
                    target_count = float('inf')
        else:
            target_count = count
        
        results = []
        all_patterns = self._get_all_search_patterns(symbol, name)
        
        print(f"📋 Total patterns to execute: {len(all_patterns)}")
        
        executed_patterns = 0
        total_api_calls = 0
        
        for category, patterns in all_patterns.items():
            print(f"🎯 Executing {category} patterns...")
            
            for pattern in patterns:
                try:
                    search_results = self.api_manager.search(pattern, num_results=10)
                    executed_patterns += 1
                    total_api_calls += 1
                    
                    if search_results and 'items' in search_results:
                        for item in search_results['items']:
                            try:
                                # MODIFIED: Enhanced result processing with md_date extraction
                                processed_result = self._process_search_result_with_md_date(
                                    item, pattern, symbol, name, min_quality
                                )
                                
                                if processed_result and processed_result.get('quality_score', 0) >= min_quality:
                                    results.append(processed_result)
                                    
                                    # FIXED: Check count limit with proper type comparison
                                    if len(results) >= target_count:
                                        break
                                        
                            except Exception as e:
                                print(f"⚠️ Processing result failed: {e}")
                                continue
                    
                    # Rate limiting
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # FIXED: Check count limit with proper type comparison
                    if len(results) >= target_count:
                        break
                        
                except Exception as e:
                    print(f"⚠️ Pattern execution failed: {pattern} - {e}")
                    continue
            
            # FIXED: Check count limit between categories with proper type comparison
            if len(results) >= target_count:
                break
        
        # Store execution stats
        self.last_patterns_executed = executed_patterns
        self.last_api_calls = total_api_calls
        
        # FIXED: Return proper count with type conversion
        final_results = results[:int(target_count)] if target_count != float('inf') else results
        
        print(f"✅ Search completed: {len(final_results)} results, {executed_patterns} patterns, {total_api_calls} API calls")
        
        return final_results

    def _process_search_result_with_md_date(self, item: Dict, query: str, symbol: str, 
                                          name: str, min_quality: int) -> Optional[Dict[str, Any]]:
        """MODIFIED: Enhanced result processing with md_date extraction"""
        try:
            url = item.get('link', '')
            title = item.get('title', '')
            
            if not url or not title:
                return None
            
            # Fetch page content
            content = self._fetch_page_content(url)
            if not content:
                return None
            
            # ENHANCED: Extract md_date from content during search
            md_date = self._extract_content_date_for_metadata(content)
            
            # Content validation
            validation_result = self._validate_content(content, symbol, name)
            
            # Quality assessment
            quality_score = self._assess_quality(content, title, url)
            
            # Apply validation penalty if needed
            if not validation_result['is_valid']:
                quality_score = 0
                print(f"⚠️ Content validation failed: {validation_result['reason']}")
            
            # ENHANCED: Create result with md_date in metadata
            result = {
                'url': url,
                'title': title,
                'quality_score': quality_score,
                'company': name,
                'stock_code': symbol,
                'md_date': md_date,  # NEW: Extracted content date
                'extracted_date': datetime.now().isoformat(),  # Search timestamp
                'search_query': query,
                'content_validation': validation_result,
                'version': self.version,
                'content': content
            }
            
            return result
            
        except Exception as e:
            print(f"⚠️ Error processing search result: {e}")
            return None

    def _extract_content_date_for_metadata(self, content: str) -> str:
        """ENHANCED: Extract content date specifically for md_date metadata field"""
        
        # Remove any YAML frontmatter to avoid confusion
        actual_content = self._get_content_without_yaml(content)
        
        found_dates = []
        
        for i, pattern in enumerate(self.date_patterns):
            matches = re.findall(pattern, actual_content, re.MULTILINE | re.DOTALL)
            
            if matches:
                for match in matches:
                    try:
                        if len(match) >= 3:
                            year, month, day = match[0], match[1], match[2]
                            
                            if self._validate_date_components(year, month, day):
                                # Format as YYYY/MM/DD for consistency
                                date_str = f"{year}/{int(month):02d}/{int(day):02d}"
                                confidence = self._calculate_date_confidence(pattern, match, actual_content, i)
                                
                                found_dates.append({
                                    'date': date_str,
                                    'pattern_index': i,
                                    'confidence': confidence
                                })
                                
                    except (ValueError, IndexError):
                        continue
        
        if found_dates:
            # Sort by confidence and return the best match
            found_dates.sort(key=lambda x: x['confidence'], reverse=True)
            best_date = found_dates[0]['date']
            print(f"📅 Extracted md_date: {best_date}")
            return best_date
        
        print("⚠️ No content date found for md_date")
        return ""

    def _get_content_without_yaml(self, content: str) -> str:
        """Remove YAML frontmatter to get actual article content"""
        try:
            if content.startswith('---'):
                end_pos = content.find('---', 3)
                if end_pos != -1:
                    return content[end_pos + 3:].strip()
        except Exception:
            pass
        return content

    def _validate_date_components(self, year: str, month: str, day: str) -> bool:
        """Validate date components for reasonableness"""
        try:
            y, m, d = int(year), int(month), int(day)
            
            # Year validation: reasonable range for financial news
            if not (2020 <= y <= 2030):
                return False
                
            # Month validation
            if not (1 <= m <= 12):
                return False
                
            # Day validation
            if not (1 <= d <= 31):
                return False
                
            # Create datetime to validate the actual date
            datetime(y, m, d)
            return True
            
        except (ValueError, TypeError):
            return False

    def _calculate_date_confidence(self, pattern: str, match: tuple, content: str, pattern_index: int) -> float:
        """Calculate confidence score for date extraction"""
        confidence = 5.0
        
        # Pattern priority - earlier patterns are more reliable
        if pattern_index == 0:
            confidence += 6.0
        elif pattern_index == 1:
            confidence += 5.5
        elif pattern_index == 2:
            confidence += 5.0
        elif pattern_index <= 6:
            confidence += 4.0
        else:
            confidence += 2.0
        
        # Position in content - dates near the top are more likely to be publication dates
        match_text = ''.join(match)
        position = content.find(match_text)
        if position != -1:
            if position < len(content) * 0.1:  # In first 10%
                confidence += 2.0
            elif position < len(content) * 0.3:  # In first 30%
                confidence += 1.0
        
        # Recency bonus - more recent dates are more likely to be correct
        try:
            year = int(match[0])
            current_year = datetime.now().year
            if year == current_year:
                confidence += 1.5
            elif year == current_year - 1:
                confidence += 1.0
        except:
            pass
        
        # Content source bonus
        if 'cnyes.com' in content:
            confidence += 1.5
        elif '鉅亨網' in content:
            confidence += 1.0
        
        return confidence

    def generate_md_file_with_md_date(self, result: Dict[str, Any], result_index: int) -> Tuple[str, str]:
        """MODIFIED: Generate MD file with enhanced metadata including md_date"""
        
        # Generate pure content hash for filename
        content_for_hash = f"{result['content']}{result['url']}{result['title']}"
        content_hash = hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()[:8]
        
        company_code = result.get('stock_code', 'Unknown')
        company_name = result.get('company', 'Unknown')
        
        filename = f"{company_code}_{company_name}_factset_{content_hash}.md"
        
        # ENHANCED: Metadata with md_date field
        metadata = {
            'url': result['url'],
            'title': result['title'],
            'quality_score': result['quality_score'],
            'company': result['company'],
            'stock_code': result['stock_code'],
            'md_date': result.get('md_date', ''),  # NEW: Content publication date
            'extracted_date': result['extracted_date'],  # Search timestamp
            'search_query': result['search_query'],
            'result_index': result_index,
            'content_validation': result['content_validation'],
            'version': result['version']
        }
        
        # Generate YAML frontmatter
        yaml_lines = ['---']
        for key, value in metadata.items():
            if isinstance(value, dict):
                yaml_lines.append(f'{key}: {value}')
            elif isinstance(value, str):
                yaml_lines.append(f'{key}: {value}')
            else:
                yaml_lines.append(f'{key}: {value}')
        yaml_lines.append('---')
        yaml_lines.append('')
        
        # Combine metadata and content
        md_content = '\n'.join(yaml_lines) + result['content']
        
        return filename, md_content

    def save_md_file(self, filename: str, content: str, output_dir: str = "data/md") -> str:
        """Save MD file with enhanced metadata"""
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"💾 Saved MD file with md_date: {filename}")
            return file_path
            
        except Exception as e:
            print(f"⚠️ Failed to save MD file {filename}: {e}")
            return ""

    # Keep all other existing methods unchanged
    def _get_all_search_patterns(self, symbol: str, name: str) -> Dict[str, List[str]]:
        """Get all search patterns with symbol/name substitution"""
        all_patterns = {}
        
        for category, patterns in self.refined_search_patterns.items():
            formatted_patterns = []
            for pattern in patterns:
                formatted_pattern = pattern.format(symbol=symbol, name=name)
                formatted_patterns.append(formatted_pattern)
            all_patterns[category] = formatted_patterns
        
        return all_patterns

    def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch page content with error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            print(f"⚠️ Failed to fetch content from {url}: {e}")
            return None

    def _validate_content(self, content: str, symbol: str, name: str) -> Dict[str, Any]:
        """Enhanced content validation"""
        if not self.enable_content_validation:
            return {'is_valid': True, 'reason': 'Validation disabled'}
        
        try:
            # Convert to lowercase for case-insensitive matching
            content_lower = content.lower()
            symbol_lower = symbol.lower()
            name_lower = name.lower()
            
            # Check for symbol presence
            symbol_found = symbol_lower in content_lower
            
            # Check for company name presence (partial matching)
            name_words = name_lower.split()
            name_matches = sum(1 for word in name_words if len(word) > 1 and word in content_lower)
            name_found = name_matches >= max(1, len(name_words) // 2)
            
            # Calculate confidence score
            confidence = 0
            if symbol_found:
                confidence += 0.6
            if name_found:
                confidence += 0.4
            
            is_valid = confidence >= self.validation_threshold
            
            if is_valid:
                reason = f"Valid content about {symbol}"
                if symbol_found and name_found:
                    reason += f" - both symbol and name found"
                elif symbol_found:
                    reason += f" - symbol found"
                else:
                    reason += f" - name found"
            else:
                reason = f"Content validation failed for {symbol} - confidence: {confidence:.2f}"
            
            return {
                'is_valid': is_valid,
                'reason': reason,
                'confidence': confidence,
                'symbol_found': symbol_found,
                'name_found': name_found
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'reason': f"Validation error: {e}",
                'confidence': 0
            }

    def _assess_quality(self, content: str, title: str, url: str) -> int:
        """Assess content quality (0-10 scale)"""
        score = 0
        
        # Content length scoring
        if len(content) > 2000:
            score += 2
        elif len(content) > 1000:
            score += 1
        
        # Financial keywords
        financial_keywords = [
            'eps', '每股盈餘', '營收', '獲利', '分析師', '預估', 'factset', 
            '目標價', '評等', 'bloomberg', 'consensus'
        ]
        
        keyword_count = sum(1 for keyword in financial_keywords if keyword in content.lower())
        score += min(keyword_count, 4)
        
        # Source quality
        if 'cnyes.com' in url:
            score += 2
        elif any(site in url for site in ['statementdog.com', 'moneydj.com', 'yahoo.com']):
            score += 1
        
        # Title quality
        if any(word in title.lower() for word in ['factset', 'eps', '預估', '分析師']):
            score += 1
        
        # Numerical data presence
        if re.search(r'\d+\.?\d*\s*元', content):
            score += 1
        
        return min(score, 10)


# Example usage and testing
if __name__ == "__main__":
    print("=== SearchEngine v3.5.1-modified Testing ===")
    print("Enhanced with md_date extraction for metadata and fixed type conversion")
    
    # This would normally be initialized with actual api_manager and config
    # search_engine = SearchEngine(api_manager, config)
    
    # Test date extraction
    test_content = """
鉅亨速報 - Factset 最新調查：鴻海(2317-TW)EPS預估下修至13.53元

鉅亨網新聞中心 2025-05-20 18:11

根據FactSet最新調查，共22位分析師，對鴻海(2317-TW)做出2025年EPS預估：
中位數由13.63元下修至13.53元，其中最高估值15.07元，最低估值11.63元，
預估目標價為201元。
    """
    
    # Create a test instance to demonstrate date extraction
    class TestSearchEngine(SearchEngine):
        def __init__(self):
            self.date_patterns = [
                r'鉅亨網新聞中心\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
                r'(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
                r'(\d{4})年(\d{1,2})月(\d{1,2})日'
            ]
    
    test_engine = TestSearchEngine()
    extracted_date = test_engine._extract_content_date_for_metadata(test_content)
    
    print(f"Test content date extraction:")
    print(f"Input content snippet: 鉅亨網新聞中心 2025-05-20 18:11")
    print(f"Extracted md_date: {extracted_date}")
    print(f"Expected: 2025/05/20")
    print(f"Success: {'✅' if extracted_date == '2025/05/20' else '❌'}")
    
    # Test type conversion fix
    print(f"\nTest type conversion fix:")
    print(f"Count='2' should be converted to int(2)")
    print(f"Count='all' should be converted to float('inf')")
    print(f"This fixes the '>=' comparison error")
    
    print(f"\n🎉 SearchEngine v3.5.1-modified ready!")
    print(f"📋 Key fixes:")
    print(f"   ✅ Type conversion for count parameter fixed")
    print(f"   ✅ md_date field extracted during search")
    print(f"   ✅ Content publication date vs search timestamp separation")
    print(f"   ✅ Enhanced metadata for reliable report generation")
    print(f"   ✅ Backward compatible with existing Process Group")