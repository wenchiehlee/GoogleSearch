"""
search_engine.py - Core Search Logic (v3.5.0) - COMPLETE WITH CONTENT VALIDATION FIX

Version: 3.5.0-validation-fixed-complete
Date: 2025-07-01
Author: FactSet Pipeline v3.5.0 - Modular Search Group

COMPLETE CONTENT VALIDATION FIX:
- Fixed validation patterns to properly detect wrong companies like 聯亞(3081)
- Enhanced regex patterns for comprehensive company detection
- Proper quality score override (0) for invalid content
- Detailed logging and validation metadata
- All original quality scoring logic preserved
"""

import re
import json
import hashlib
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup

__version__ = "3.5.0-validation-fixed-complete"

# REFINED search patterns based on successful content discovery
REFINED_SEARCH_PATTERNS = {
    'factset_direct': [
        # Simple FactSet patterns (highest success rate)
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
        # cnyes.com is the #1 source for FactSet data in Taiwan
        'site:cnyes.com factset {symbol}',
        'site:cnyes.com {symbol} factset',
        'site:cnyes.com {symbol} EPS 預估',
        'site:cnyes.com {name} factset',
        'site:cnyes.com {symbol} 分析師',
        'site:cnyes.com factset {name}',
        'site:cnyes.com {symbol} 台股預估'
    ],
    'eps_forecast': [
        # Direct EPS forecast searches
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
        # Analyst and consensus patterns
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
        # Simple Taiwan financial site searches
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

# Priority order for search execution
SEARCH_PRIORITY_ORDER = [
    'factset_direct',      # Highest priority - direct FactSet
    'cnyes_factset',       # Second highest - cnyes.com FactSet content  
    'eps_forecast',        # Third - EPS forecasts
    'analyst_consensus',   # Fourth - analyst data
    'taiwan_financial_simple'  # Last - general Taiwan financial
]

# Enhanced EPS and financial data patterns for Taiwan context
EPS_PATTERNS = [
    # FactSet specific patterns (from successful example)
    r'中位數.*?(\d+\.?\d*)元',
    r'平均值.*?(\d+\.?\d*).*?元',
    r'最高.*?值.*?(\d+\.?\d*).*?元',
    r'最低.*?值.*?(\d+\.?\d*).*?元',
    r'預估.*?(\d+\.?\d*)元',
    
    # Year-specific patterns (Chinese)
    r'2025.*?EPS.*?預估.*?(\d+\.?\d*)',
    r'2026.*?EPS.*?預估.*?(\d+\.?\d*)',
    r'2027.*?EPS.*?預估.*?(\d+\.?\d*)',
    r'2025.*?每股盈餘.*?(\d+\.?\d*)',
    r'2026.*?每股盈餘.*?(\d+\.?\d*)',
    r'2027.*?每股盈餘.*?(\d+\.?\d*)',
    
    # Year-specific patterns (English)
    r'2025.*?EPS.*?(\d+\.?\d*)',
    r'2026.*?EPS.*?(\d+\.?\d*)', 
    r'2027.*?EPS.*?(\d+\.?\d*)',
    r'2025.*?earnings per share.*?(\d+\.?\d*)',
    r'2026.*?earnings per share.*?(\d+\.?\d*)',
    r'2027.*?earnings per share.*?(\d+\.?\d*)',
    
    # Reverse patterns (number first)
    r'EPS.*?2025.*?(\d+\.?\d*)',
    r'EPS.*?2026.*?(\d+\.?\d*)',
    r'EPS.*?2027.*?(\d+\.?\d*)',
    r'每股盈餘.*?2025.*?(\d+\.?\d*)',
    r'每股盈餘.*?2026.*?(\d+\.?\d*)',
    r'每股盈餘.*?2027.*?(\d+\.?\d*)',
    
    # General patterns
    r'consensus.*?eps.*?(\d+\.?\d*)',
    r'forecast.*?eps.*?(\d+\.?\d*)',
    r'estimate.*?eps.*?(\d+\.?\d*)',
    r'預估.*?EPS.*?(\d+\.?\d*)',
    r'共識.*?EPS.*?(\d+\.?\d*)',
    r'分析師.*?EPS.*?(\d+\.?\d*)'
]

TARGET_PRICE_PATTERNS = [
    r'預估目標價.*?(\d+\.?\d*)元',
    r'目標價為.*?(\d+\.?\d*)元',
    r'目標價.*?(\d+\.?\d*)元',
    r'合理價.*?(\d+\.?\d*)元',
    r'target price.*?(\d+\.?\d*)',
    r'price target.*?(\d+\.?\d*)',
    r'fair value.*?(\d+\.?\d*)',
    r'target.*?NT\$(\d+\.?\d*)',
    r'股價目標.*?(\d+\.?\d*)',
    r'合理股價.*?(\d+\.?\d*)',
    r'目標.*?價位.*?(\d+\.?\d*)'
]

ANALYST_COUNT_PATTERNS = [
    r'共.*?(\d+).*?位分析師',
    r'(\d+)位.*?分析師',
    r'(\d+).*?分析師',
    r'(\d+)\s*analysts?',
    r'consensus of (\d+)',
    r'(\d+)\s*estimates?',
    r'(\d+)\s*analysts?\s*covering',
    r'based on (\d+) estimates',
    r'(\d+)家.*?投信',
    r'(\d+)間.*?券商',
    r'(\d+).*?家券商'
]

class CompanyContentValidator:
    """Validates that search result content actually matches the target company - FIXED VERSION"""
    
    def __init__(self):
        self.logger = logging.getLogger('content_validator')
    
    def validate_content_matches_company(self, target_symbol: str, target_name: str, financial_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that the content actually matches the target company - COMPREHENSIVE FIX
        
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        try:
            # Get all content sources
            sources = financial_data.get('sources', [])
            if not sources:
                return False, "No sources to validate"
            
            all_content = ""
            
            for source in sources:
                title = source.get('title', '')
                snippet = source.get('snippet', '')
                content = f"{title} {snippet}"
                all_content += content + " "
            
            # STEP 1: Check for wrong companies in content (MOST IMPORTANT)
            wrong_companies = self._find_wrong_companies_in_content(target_symbol, target_name, all_content)
            
            # Debug logging
            self.logger.debug(f"Content validation for {target_symbol}:")
            self.logger.debug(f"  Content preview: {all_content[:200]}...")
            self.logger.debug(f"  Wrong companies found: {wrong_companies}")
            
            # If we find ANY wrong company mentions, validation fails immediately
            if wrong_companies:
                reason = f"Content mentions wrong companies: {', '.join(wrong_companies)}"
                self.logger.warning(f"❌ Content validation failed for {target_symbol}: {reason}")
                return False, reason
            
            # STEP 2: Check if content mentions the target company at all
            target_mentions = self._find_target_company_mentions(target_symbol, target_name, all_content)
            
            # Debug logging
            self.logger.debug(f"  Target mentions found: {target_mentions}")
            
            # If content doesn't mention target company, validation fails
            if not target_mentions:
                reason = f"Content does not mention target company {target_symbol} {target_name}"
                self.logger.warning(f"❌ Content validation failed for {target_symbol}: {reason}")
                return False, reason
            
            # STEP 3: Both checks passed - validation successful
            self.logger.info(f"✅ Content validation passed for {target_symbol}: mentions target company, no wrong companies")
            return True, f"Valid content about {target_symbol}"
            
        except Exception as e:
            self.logger.error(f"Content validation error for {target_symbol}: {e}")
            return False, f"Validation error: {e}"
    
    def _find_wrong_companies_in_content(self, target_symbol: str, target_name: str, content: str) -> List[str]:
        """Find mentions of wrong companies in content - COMPREHENSIVE FIXED VERSION"""
        wrong_companies = []
        
        # Pattern 1: Find company names with stock codes: 公司名稱(NNNN-TW)
        # This catches: 聯亞(3081-TW), 樺漢(6414-TW), etc.
        pattern_with_tw = r'([^(]*?)\((\d{4})-TW\)'
        matches_tw = re.findall(pattern_with_tw, content)
        
        self.logger.debug(f"  Pattern 1 (Company(NNNN-TW)): {matches_tw}")
        
        for company_name, stock_code in matches_tw:
            company_name = company_name.strip()
            if stock_code != target_symbol:
                wrong_companies.append(f"{company_name}({stock_code})")
        
        # Pattern 2: Find company names with stock codes: 公司名稱(NNNN) - without -TW
        # This catches: 聯亞(3081), 樺漢(6414), etc.
        pattern_without_tw = r'([^(]*?)\((\d{4})\)'
        matches_without_tw = re.findall(pattern_without_tw, content)
        
        self.logger.debug(f"  Pattern 2 (Company(NNNN)): {matches_without_tw}")
        
        for company_name, stock_code in matches_without_tw:
            company_name = company_name.strip()
            # Only add if it's a 4-digit code and not the target, and not already found with -TW
            if (stock_code != target_symbol and 
                len(stock_code) == 4 and 
                not any(stock_code in wc for wc in wrong_companies)):
                wrong_companies.append(f"{company_name}({stock_code})")
        
        # Pattern 3: Find standalone stock codes: NNNN-TW
        # This catches standalone: 3081-TW, 6414-TW, etc.
        standalone_pattern_tw = r'(\d{4})-TW'
        standalone_matches_tw = re.findall(standalone_pattern_tw, content)
        
        self.logger.debug(f"  Pattern 3 (NNNN-TW standalone): {standalone_matches_tw}")
        
        for stock_code in standalone_matches_tw:
            if stock_code != target_symbol:
                # Check if already captured in company(code) format
                already_found = any(stock_code in wc for wc in wrong_companies)
                if not already_found:
                    wrong_companies.append(f"Unknown({stock_code})")
        
        # Pattern 4: Be careful with standalone 4-digit numbers to avoid false positives
        # Only flag as potential stock codes if in financial context
        standalone_digits = r'\b(\d{4})\b'
        digit_matches = re.findall(standalone_digits, content)
        
        for digits in digit_matches:
            # Only consider as stock code if:
            # 1. Not the target symbol
            # 2. Not already found in other patterns  
            # 3. Not obviously a year (2020-2030 range)
            # 4. Appears in financial context
            if (digits != target_symbol and 
                not any(digits in wc for wc in wrong_companies) and
                not (2020 <= int(digits) <= 2030)):
                
                # Check if it appears in a financial context
                digit_pos = content.find(digits)
                context = content[max(0, digit_pos-30):digit_pos+30] if digit_pos >= 0 else ""
                
                # Only flag if it has financial context indicators
                if any(term in context for term in ['股', '公司', '營收', '股價', '投資', '股票', '上市', '台股', 'TW']):
                    # Additional check: avoid common non-stock numbers
                    if not re.search(r'\d+\.\d+|元|億|萬|%|月|年|日|時|分', context):
                        wrong_companies.append(f"PossibleStock({digits})")
        
        self.logger.debug(f"  Final wrong companies detected: {wrong_companies}")
        return wrong_companies
    
    def _find_target_company_mentions(self, target_symbol: str, target_name: str, content: str) -> List[str]:
        """Find mentions of the target company in content - ENHANCED VERSION"""
        mentions = []
        
        # Look for target symbol in various formats
        if target_symbol in content:
            mentions.append(f"symbol_{target_symbol}")
        
        # Look for target name
        if target_name in content:
            mentions.append(f"name_{target_name}")
        
        # Look for target symbol with -TW format
        if f"{target_symbol}-TW" in content:
            mentions.append(f"formatted_{target_symbol}-TW")
        
        # Look for target company in (NNNN) format
        if f"({target_symbol})" in content:
            mentions.append(f"parenthesis_{target_symbol}")
        
        # Look for target company in (NNNN-TW) format  
        if f"({target_symbol}-TW)" in content:
            mentions.append(f"parenthesis_{target_symbol}-TW")
        
        # Look for company name with target symbol: 公司名稱(NNNN)
        target_with_name_pattern = rf'{re.escape(target_name)}\s*\(\s*{target_symbol}\s*\)'
        if re.search(target_with_name_pattern, content):
            mentions.append(f"name_with_symbol_{target_name}({target_symbol})")
        
        # Look for company name with target symbol -TW: 公司名稱(NNNN-TW)
        target_with_name_tw_pattern = rf'{re.escape(target_name)}\s*\(\s*{target_symbol}-TW\s*\)'
        if re.search(target_with_name_tw_pattern, content):
            mentions.append(f"name_with_symbol_tw_{target_name}({target_symbol}-TW)")
        
        return mentions

class RefinedQualityScorer:
    """ORIGINAL quality assessment with added company content validation - COMPLETE"""
    
    def __init__(self):
        self.validator = CompanyContentValidator()
        self.logger = logging.getLogger('quality_scorer')
    
    def calculate_score(self, financial_data: Dict[str, Any], target_symbol: str = None, target_name: str = None) -> int:
        """Calculate quality score 0-10 with company content validation - FIXED"""
        
        # FIRST: Validate that content actually matches the target company
        if target_symbol and target_name:
            is_valid, validation_reason = self.validator.validate_content_matches_company(
                target_symbol, target_name, financial_data
            )
            
            if not is_valid:
                self.logger.warning(f"❌ Content validation failed for {target_symbol}: {validation_reason}")
                # Set validation info in financial_data for debugging
                financial_data['content_validation'] = {
                    'is_valid': False,
                    'reason': validation_reason,
                    'score_override': 0
                }
                return 0  # Invalid content = score 0
            else:
                self.logger.info(f"✅ Content validation passed for {target_symbol}: {validation_reason}")
                financial_data['content_validation'] = {
                    'is_valid': True,
                    'reason': validation_reason
                }
        
        # SECOND: Apply ORIGINAL quality scoring logic (completely unchanged)
        score = 0.0
        
        # 1. FactSet mention = automatic high score (35% weight)
        sources = financial_data.get('sources', [])
        has_factset_mention = False
        factset_quality = 0
        
        for source in sources:
            content = f"{source.get('title', '')} {source.get('snippet', '')}".lower()
            if 'factset' in content:
                has_factset_mention = True
                # Different levels of FactSet quality
                if 'factset最新調查' in content or 'factset調查' in content:
                    factset_quality = 3.5  # Perfect FactSet content
                elif 'factset' in content and ('分析師' in content or 'analyst' in content):
                    factset_quality = 3.0  # Good FactSet content
                else:
                    factset_quality = 2.0  # Basic FactSet mention
                break
        
        score += factset_quality
        
        # 2. Analyst count with Taiwan-realistic thresholds (25% weight)
        analyst_count = financial_data.get('analyst_count', 0)
        if analyst_count >= 40:      # Like the 42 analysts example
            score += 2.5
        elif analyst_count >= 30:
            score += 2.2
        elif analyst_count >= 20:
            score += 2.0
        elif analyst_count >= 15:
            score += 1.5
        elif analyst_count >= 10:
            score += 1.2
        elif analyst_count >= 5:
            score += 0.8
        elif analyst_count >= 1:
            score += 0.4
        
        # 3. EPS forecast completeness (25% weight)
        eps_years = ['2025_eps_avg', '2026_eps_avg', '2027_eps_avg']
        eps_count = sum(1 for year in eps_years if financial_data.get(year))
        if eps_count >= 3:           # Like the example with 2025-2028
            score += 2.5
        elif eps_count >= 2:
            score += 2.0
        elif eps_count >= 1:
            score += 1.5
        
        # 4. Target price (10% weight)
        if financial_data.get('target_price'):
            score += 1.0
        
        # 5. Source credibility (5% weight)
        source_bonus = 0
        for source in sources:
            url = source.get('url', '').lower()
            title = source.get('title', '').lower()
            snippet = source.get('snippet', '').lower()
            
            if 'cnyes.com' in url:
                source_bonus = 0.5  # cnyes.com is proven high-quality
                break
            elif 'statementdog.com' in url:
                source_bonus = 0.4
            elif any(site in url for site in ['wantgoo.com', 'goodinfo.tw', 'uanalyze.com.tw']):
                source_bonus = 0.3
            elif any(site in url for site in ['findbillion.com', 'moneydj.com']):
                source_bonus = 0.2
        
        score += source_bonus
        
        # Bonus: Premium content indicators (like the successful example)
        bonus = 0
        
        # FactSet + high analyst coverage + multi-year EPS (like successful example)
        if has_factset_mention and eps_count >= 2 and analyst_count >= 20:
            bonus += 0.5
        
        # Structured data indicators (tables, organized presentation)
        for source in sources:
            content = f"{source.get('title', '')} {source.get('snippet', '')}".lower()
            if any(indicator in content for indicator in ['表', 'table', '最高值', '最低值', '中位數', '平均值']):
                bonus += 0.3
                break
        
        # Financial terminology richness
        financial_terms = ['eps', '每股盈餘', '分析師', 'analyst', '預估', 'forecast', 
                          '目標價', 'target price', 'consensus', '共識', '投資評等']
        term_count = 0
        for source in sources:
            content = f"{source.get('title', '')} {source.get('snippet', '')}".lower()
            term_count += sum(1 for term in financial_terms if term in content)
        
        if term_count >= 5:
            bonus += 0.3
        elif term_count >= 3:
            bonus += 0.2
        
        score += bonus
        
        final_score = min(10, max(0, int(score)))
        
        # Log validation and scoring results
        validation_info = financial_data.get('content_validation', {})
        if validation_info.get('is_valid', True):
            self.logger.info(f"✅ Quality score for {target_symbol}: {final_score}/10 (content validated)")
        else:
            self.logger.warning(f"❌ Quality score for {target_symbol}: {final_score}/10 (content validation failed)")
        
        return final_score
    
    def get_quality_indicator(self, score: int) -> str:
        """Get quality indicator for score"""
        if score >= 8:
            return '🟢 優秀'
        elif score >= 6:
            return '🟡 良好'
        elif score >= 4:
            return '🟠 普通'
        elif score >= 2:
            return '🔴 可用'
        else:
            return '⚫ 極差'

class SearchEngine:
    """v3.5.0 Core Search Logic - COMPLETE WITH CONTENT VALIDATION FIX"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.search_patterns = REFINED_SEARCH_PATTERNS
        self.search_priority_order = SEARCH_PRIORITY_ORDER
        self.quality_scorer = RefinedQualityScorer()
        self.logger = logging.getLogger('search_engine')
        
        # Track execution stats
        self.last_patterns_executed = 0
        self.last_api_calls = 0
    
    def search_company(self, symbol: str, name: str) -> Optional[Dict[str, Any]]:
        """Search single company for financial data (single result)"""
        try:
            self.logger.info(f"Starting search for {symbol} {name}")
            
            # Build search queries with refined patterns
            queries = self._build_refined_search_queries(symbol, name)
            self.logger.debug(f"Built {len(queries)} refined search queries")
            
            # Execute comprehensive search cascade
            all_results = self._execute_comprehensive_search_cascade(queries)
            
            if not all_results:
                self.logger.warning(f"No search results found for {symbol}")
                return None
            
            # Extract financial data from results
            financial_data = self._extract_financial_data_from_results(all_results)
            
            # Assess quality with ORIGINAL scorer + validation
            quality_score = self.quality_scorer.calculate_score(financial_data, symbol, name)
            financial_data['quality_score'] = quality_score
            
            quality_indicator = self.quality_scorer.get_quality_indicator(quality_score)
            self.logger.info(f"Extracted data for {symbol}: quality {quality_score}/10 {quality_indicator}")
            
            return financial_data
            
        except Exception as e:
            self.logger.error(f"Error searching {symbol}: {e}")
            return None
    
    def search_company_multiple(self, symbol: str, name: str, result_count: str = '1') -> List[Dict[str, Any]]:
        """Search single company and return multiple results - WITH VALIDATION"""
        try:
            self.logger.info(f"Starting comprehensive search for {symbol} {name} (requesting {result_count} results)")
            
            # Build refined search queries
            queries = self._build_refined_search_queries(symbol, name)
            self.logger.debug(f"Built {len(queries)} refined search queries")
            
            # Execute comprehensive search cascade (ALL PATTERNS)
            all_results = self._execute_comprehensive_search_cascade(queries)
            
            if not all_results:
                self.logger.warning(f"No search results found for {symbol}")
                return []
            
            # Determine how many results to return
            if result_count.lower() == 'all':
                max_results = min(len(all_results), 20)  # Cap at 20 for performance
            else:
                try:
                    max_results = int(result_count)
                except ValueError:
                    max_results = 1
            
            # Take top results up to max_results
            selected_results = all_results[:max_results]
            
            # Process each result separately WITH VALIDATION
            processed_results = []
            for i, result in enumerate(selected_results):
                # Create individual result data
                result_data = self._extract_financial_data_from_single_result(result)
                
                # Assess quality with ORIGINAL scorer + VALIDATION
                quality_score = self.quality_scorer.calculate_score(result_data, symbol, name)
                result_data['quality_score'] = quality_score
                result_data['result_index'] = i + 1
                result_data['total_requested'] = max_results
                
                # Log validation results
                validation_info = result_data.get('content_validation', {})
                if not validation_info.get('is_valid', True):
                    self.logger.warning(f"Result {i+1} for {symbol}: INVALID CONTENT - {validation_info.get('reason', 'unknown')}")
                
                processed_results.append(result_data)
            
            self.logger.info(f"Processed {len(processed_results)} results for {symbol} (executed {self.last_patterns_executed} patterns)")
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error searching {symbol}: {e}")
            return []
    
    def _build_refined_search_queries(self, symbol: str, name: str) -> List[Dict[str, Any]]:
        """Create refined search queries based on successful patterns"""
        queries = []
        
        print(f"\n🔍 Building search queries for {symbol} {name}:")
        print(f"📋 Available pattern groups: {list(self.search_patterns.keys())}")
        
        # Execute in strict priority order
        for priority_group in self.search_priority_order:
            patterns = self.search_patterns[priority_group]
            print(f"  📝 {priority_group}: {len(patterns)} patterns")
            
            for pattern in patterns:
                query = pattern.format(symbol=symbol, name=name)
                queries.append({
                    'query': query,
                    'priority_group': priority_group,
                    'expected_content': self._get_expected_content_type(priority_group)
                })
        
        print(f"🎯 Total queries to execute: {len(queries)}")
        print(f"🛡️  Content validation: ENABLED - will verify results match {symbol}")
        self.last_patterns_executed = len(queries)
        return queries
    
    def _get_expected_content_type(self, priority_group: str) -> str:
        """Map priority group to expected content type"""
        mapping = {
            'factset_direct': 'factset_direct',
            'cnyes_factset': 'cnyes_factset',
            'eps_forecast': 'eps_forecast',
            'analyst_consensus': 'analyst_consensus',
            'taiwan_financial_simple': 'taiwan_financial'
        }
        return mapping.get(priority_group, 'general')
    
    def _execute_comprehensive_search_cascade(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute search with comprehensive pattern execution - NO EARLY STOPPING"""
        all_results = []
        results_by_priority = {}
        api_calls_made = 0
        
        print(f"\n🚀 Executing comprehensive search - ALL {len(queries)} patterns will run:")
        
        # Group queries by priority
        for query_info in queries:
            priority_group = query_info['priority_group']
            if priority_group not in results_by_priority:
                results_by_priority[priority_group] = []
        
        # Execute in priority order - NO EARLY STOPPING
        for priority_group in self.search_priority_order:
            group_queries = [q for q in queries if q['priority_group'] == priority_group]
            
            print(f"\n📋 Executing {len(group_queries)} {priority_group} patterns...")
            self.logger.debug(f"Executing {len(group_queries)} {priority_group} patterns")
            
            group_results = []
            for i, query_info in enumerate(group_queries, 1):
                try:
                    query = query_info['query']
                    print(f"  {i:2d}/{len(group_queries)} 🔍 {query}")
                    
                    results = self.api_manager.search(query)
                    api_calls_made += 1
                    
                    if results and 'items' in results:
                        raw_count = len(results['items'])
                        filtered = self._filter_for_quality_content_permissive(results['items'], priority_group)
                        filtered_count = len(filtered)
                        
                        print(f"     → Found {raw_count} raw results, {filtered_count} after filter")
                        
                        if filtered:
                            group_results.extend(filtered)
                            self.logger.debug(f"Query '{query}' found {len(filtered)} quality results")
                    else:
                        print(f"     → No results found")
                        
                except Exception as e:
                    print(f"     → ERROR: {e}")
                    self.logger.warning(f"Query failed: {query_info['query']} - {e}")
                    continue
            
            # Add group results - NO EARLY STOPPING CHECK
            if group_results:
                # Remove duplicates within group
                unique_group_results = self._remove_duplicate_results(group_results)
                all_results.extend(unique_group_results)
                results_by_priority[priority_group] = unique_group_results
                
                print(f"✅ {priority_group} completed: {len(unique_group_results)} unique results")
            else:
                print(f"❌ {priority_group} completed: 0 results")
            
            # REMOVED: Early stopping logic - continue with ALL pattern groups
        
        # Final deduplication and sorting
        final_results = self._remove_duplicate_results(all_results)
        final_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        self.last_api_calls = api_calls_made
        
        print(f"\n🎯 Comprehensive search completed:")
        print(f"   📊 {len(queries)} patterns executed")
        print(f"   📡 {api_calls_made} API calls made")
        print(f"   📄 {len(final_results)} unique results found")
        print(f"   🛡️  Content validation will check each result")
        
        self.logger.info(f"Comprehensive search completed with {len(final_results)} unique results from {len(queries)} patterns")
        return final_results
    
    def _filter_for_quality_content_permissive(self, items: List[Dict], priority_group: str) -> List[Dict]:
        """Filter search results with LOWERED thresholds to allow quality scoring"""
        quality_results = []
        
        for item in items:
            title = item.get('title', '').lower()
            snippet = item.get('snippet', '').lower()
            url = item.get('url', '').lower()
            
            # Score each result based on content quality
            relevance_score = 0
            
            # FactSet content = highest priority (like successful example)
            if 'factset' in title or 'factset' in snippet:
                relevance_score += 25
                if 'factset最新調查' in snippet or 'factset調查' in snippet:
                    relevance_score += 10  # Perfect FactSet content
            
            # cnyes.com = proven high-quality source for Taiwan financial data
            if 'cnyes.com' in url:
                relevance_score += 20
                if priority_group == 'cnyes_factset':
                    relevance_score += 5  # Bonus for cnyes FactSet content
            
            # Other Taiwan financial sites
            taiwan_sites = ['statementdog.com', 'wantgoo.com', 'goodinfo.tw', 
                           'uanalyze.com.tw', 'findbillion.com', 'moneydj.com']
            for site in taiwan_sites:
                if site in url:
                    relevance_score += 15
                    break
            
            # Financial keywords (weighted by importance)
            high_value_terms = ['eps', '每股盈餘', '分析師', 'analyst', '預估', 'forecast']
            medium_value_terms = ['目標價', 'target price', 'consensus', '共識', '投資評等']
            basic_terms = ['營收', 'revenue', '財報', 'earnings', '股價', 'stock price']
            
            high_matches = sum(1 for term in high_value_terms if term in title or term in snippet)
            medium_matches = sum(1 for term in medium_value_terms if term in title or term in snippet)
            basic_matches = sum(1 for term in basic_terms if term in title or term in snippet)
            
            relevance_score += high_matches * 5 + medium_matches * 3 + basic_matches * 1
            
            # Year mentions (forward-looking content)
            future_years = ['2025', '2026', '2027', '2028']
            year_mentions = sum(1 for year in future_years if year in title or year in snippet)
            relevance_score += year_mentions * 3
            
            # Structured data indicators (like successful example)
            structure_indicators = ['表', 'table', '最高值', '最低值', '中位數', '平均值']
            if any(indicator in snippet for indicator in structure_indicators):
                relevance_score += 5
            
            # LOWERED minimum relevance thresholds to allow quality scoring
            min_thresholds = {
                'factset_direct': 8,         # Lowered from 15
                'cnyes_factset': 6,          # Lowered from 12
                'eps_forecast': 4,           # Lowered from 10
                'analyst_consensus': 3,      # Lowered from 8
                'taiwan_financial_simple': 2 # Lowered from 6
            }
            
            min_threshold = min_thresholds.get(priority_group, 2)
            
            if relevance_score >= min_threshold:
                item['relevance_score'] = relevance_score
                item['content_type'] = self._determine_content_type(title, snippet, url)
                quality_results.append(item)
        
        # Sort by relevance (highest first)
        quality_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return quality_results
    
    def _determine_content_type(self, title: str, snippet: str, url: str) -> str:
        """Determine content type for result"""
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        url_lower = url.lower()
        
        # FactSet content types
        if 'factset' in snippet_lower or 'factset' in title_lower:
            if 'factset最新調查' in snippet_lower or 'factset調查' in snippet_lower:
                return 'factset_premium'
            else:
                return 'factset_direct'
        
        # cnyes.com content
        if 'cnyes.com' in url_lower:
            return 'cnyes_financial'
        
        # Other Taiwan financial sites
        taiwan_sites = ['statementdog.com', 'wantgoo.com', 'goodinfo.tw', 
                       'uanalyze.com.tw', 'findbillion.com', 'moneydj.com']
        if any(site in url_lower for site in taiwan_sites):
            return 'taiwan_financial'
        
        # General financial content
        financial_terms = ['eps', '每股盈餘', '分析師', 'analyst', 'forecast', '預估']
        if any(term in title_lower or term in snippet_lower for term in financial_terms):
            return 'general_financial'
        
        return 'general'
    
    def _remove_duplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _extract_financial_data_from_single_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from a single search result"""
        financial_data = {}
        
        # Get content from single result
        snippet = result.get('snippet', '')
        title = result.get('title', '')
        url = result.get('url', '')
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
            'url': url,
            'snippet': snippet[:300],  # Increased snippet length
            'content_type': result.get('content_type', 'unknown'),
            'relevance_score': result.get('relevance_score', 0)
        }]
        
        financial_data['sources'] = source_info
        financial_data['extraction_timestamp'] = datetime.now().isoformat()
        financial_data['total_sources'] = 1
        
        # Determine source quality
        financial_data['source_quality'] = result.get('content_type', 'unknown')
        
        return financial_data
    
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
                'snippet': snippet[:300],
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
        
        # Determine overall source quality (best available)
        best_content_type = 'general'
        for result in results:
            content_type = result.get('content_type', 'general')
            if content_type == 'factset_premium':
                best_content_type = 'factset_premium'
                break
            elif content_type == 'factset_direct' and best_content_type != 'factset_premium':
                best_content_type = 'factset_direct'
            elif content_type == 'cnyes_financial' and best_content_type not in ['factset_premium', 'factset_direct']:
                best_content_type = 'cnyes_financial'
            elif content_type == 'taiwan_financial' and best_content_type == 'general':
                best_content_type = 'taiwan_financial'
        
        financial_data['source_quality'] = best_content_type
        
        return financial_data
    
    def _extract_eps_forecasts(self, content: str) -> Dict[str, Any]:
        """Extract EPS forecasts for multiple years with improved patterns"""
        eps_data = {}
        
        for pattern in EPS_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.group(1))
                    
                    # Skip unreasonable values (reasonable range for Taiwan stocks)
                    if value < 0 or value > 2000:
                        continue
                    
                    # Determine year from context (expanded context window)
                    context = content[max(0, match.start()-200):match.end()+200]
                    
                    if '2025' in context:
                        eps_data.setdefault('2025_values', []).append(value)
                    elif '2026' in context:
                        eps_data.setdefault('2026_values', []).append(value)
                    elif '2027' in context:
                        eps_data.setdefault('2027_values', []).append(value)
                    elif '2028' in context:
                        eps_data.setdefault('2028_values', []).append(value)
                    else:
                        # If no specific year mentioned, assume next year
                        current_year = datetime.now().year
                        next_year = current_year + 1
                        if next_year in [2025, 2026, 2027, 2028]:
                            eps_data.setdefault(f'{next_year}_values', []).append(value)
                        
                except (ValueError, IndexError):
                    continue
        
        # Calculate consensus (average) for each year
        consensus = {}
        for year in ['2025', '2026', '2027', '2028']:
            values_key = f'{year}_values'
            if values_key in eps_data and eps_data[values_key]:
                values = eps_data[values_key]
                
                # Remove outliers (values more than 2 standard deviations from mean)
                if len(values) > 3:
                    import statistics
                    try:
                        mean = statistics.mean(values)
                        stdev = statistics.stdev(values)
                        filtered_values = [v for v in values if abs(v - mean) <= 2 * stdev]
                        if filtered_values:  # Use filtered values if any remain
                            values = filtered_values
                    except:
                        pass  # Keep original values if calculation fails
                
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
                    if 1 <= count <= 200:
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
                    if 1 <= price <= 50000:
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
        """Generate MD file content in v3.5.0 format (YAML + raw content) with validation info"""
        
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
        
        # Get validation info
        validation_info = financial_data.get('content_validation', {})
        
        # Generate search query for metadata (actual pattern used, NO result suffix)
        search_query = f"{name} {symbol} factset EPS 預估"
        
        # Create YAML header with validation info
        yaml_header = f"""---
url: {url}
title: {title}
quality_score: {quality_score}
company: {name}
stock_code: {symbol}
extracted_date: {datetime.now().isoformat()}
search_query: {search_query}
result_index: {result_index}
content_validation: {json.dumps(validation_info, ensure_ascii=False)}
version: v3.5.0-validation-fixed-complete
---"""
        
        # Add validation warning if content is invalid
        validation_warning = ""
        if not validation_info.get('is_valid', True):
            validation_warning = f"""
⚠️ **CONTENT VALIDATION WARNING**: {validation_info.get('reason', 'Unknown validation issue')}
This content may be about a different company than {symbol} {name}.

"""
        
        # Combine YAML header with validation warning and content
        md_content = yaml_header + "\n\n" + validation_warning + full_content
        
        return md_content
    
    def _fetch_page_content(self, url: str) -> str:
        """Fetch full page content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML and extract text content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
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
        search_query = f"{name} {symbol} factset EPS 預估"
        
        # Get validation info
        validation_info = financial_data.get('content_validation', {})
        
        yaml_header = f"""---
url: 
title: Financial data extracted from search
quality_score: {quality_score}
company: {name}
stock_code: {symbol}
extracted_date: {datetime.now().isoformat()}
search_query: {search_query}
result_index: {result_index}
content_validation: {json.dumps(validation_info, ensure_ascii=False)}
version: v3.5.0-validation-fixed-complete
---"""
        
        # Add validation warning if content is invalid
        validation_warning = ""
        if not validation_info.get('is_valid', True):
            validation_warning = f"""
⚠️ **CONTENT VALIDATION WARNING**: {validation_info.get('reason', 'Unknown validation issue')}
This content may be about a different company than {symbol} {name}.

"""
        
        content = f"""# {symbol} {name} - Financial Data (Result {result_index})

{validation_warning}
Financial data extracted from comprehensive search results with content validation.

## Search Information
- **Search Query**: {search_query}
- **Quality Score**: {quality_score}/10 (ORIGINAL scoring + validation)
- **Total Sources**: {financial_data.get('total_sources', 0)}
- **Result Index**: {result_index}
- **Source Quality**: {financial_data.get('source_quality', 'unknown')}
- **Content Validation**: {validation_info}

## Extracted Financial Data
```json
{json.dumps(financial_data, indent=2, ensure_ascii=False, default=str)}
```
"""
        
        return yaml_header + "\n\n" + content
    
    def assess_data_quality(self, financial_data: Dict[str, Any], symbol: str = None, name: str = None) -> int:
        """Assess data quality on 0-10 scale using ORIGINAL logic + validation"""
        return self.quality_scorer.calculate_score(financial_data, symbol, name)