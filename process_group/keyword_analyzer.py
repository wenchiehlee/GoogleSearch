# 測試功能
if __name__ == "__main__":
    analyzer = KeywordAnalyzer()
    
    print("=== 增強版查詢模式分析器測試 v3.6.1 ===")
    
    # 🆕 專門測試特殊後綴處理
    print("\n🧪 測試特殊後綴名稱變體生成:")
    test_names = ['奕力-KY', '創意-DR', '智擎 KY', '台新 DR']
    for name in test_names:
        variations = analyzer._get_company_name_variations_enhanced(name)
"""
Keyword Analyzer - FactSet Pipeline v3.6.1 (ENHANCED - Better Name Normalization)
專注於標準化查詢模式分析，增強公司名稱標準化
修正：完全過濾無效模式 + 增強公司名稱變體處理（如 奕力-KY）
"""

import os
import re
import yaml
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import Counter
import statistics

class KeywordAnalyzer:
    """查詢模式分析器 - v3.6.1 增強名稱標準化版"""
    
    def __init__(self):
        """初始化查詢模式分析器"""
        
        # 載入觀察名單進行驗證和標準化
        self.watchlist_mapping = self._load_watchlist_for_normalization()
        
        # 🆕 REFINED_SEARCH_PATTERNS 對應的模式分類
        self.refined_search_patterns = {
            'factset_direct': [
                'factset {symbol}', 'factset {name}', '{symbol} factset', '{name} factset',
                'factset {symbol} eps', 'factset {name} 預估', '"{symbol}" factset 分析師', 
                '"{name}" factset 目標價', '{name} {symbol} factset', '{symbol} {name} factset',
                '{name} factset eps', '{symbol} factset 分析師', '{name} factset 分析師',
                '{symbol} factset 目標價', '{name} {symbol} factset 分析師', 
                '{name} {symbol} factset eps', '{name} {symbol} factset 預估',
                '{name} {symbol} factset 目標價', '{name} factset 目標價'
            ],
            'cnyes_factset': [
                'site:cnyes.com factset {symbol}', 'site:cnyes.com {symbol} factset',
                'site:cnyes.com {symbol} eps 預估', 'site:cnyes.com {name} factset',
                'site:cnyes.com {symbol} 分析師', 'site:cnyes.com factset {name}',
                'site:cnyes.com {symbol} 台股預估', 'site:cnyes.com {name} {symbol}',
                'site:cnyes.com {symbol} factset eps', 'site:cnyes.com {name} factset eps'
            ],
            'eps_forecast': [
                '{symbol} eps 預估', '{name} eps 預估', '{symbol} eps 2025',
                '{name} eps 2025', '{symbol} 每股盈餘 預估', '{name} 每股盈餘 預估',
                '{symbol} eps forecast', '{name} earnings estimates',
                '{name} {symbol} eps', '{name} {symbol} eps 預估',
                '{name} {symbol} 2025 eps', '{name} {symbol} earnings'
            ],
            'analyst_consensus': [
                '{symbol} 分析師 預估', '{name} 分析師 預估', '{symbol} 分析師 目標價',
                '{name} 分析師 目標價', '{symbol} consensus estimate', '{name} analyst forecast',
                '{symbol} 共識預估', '{name} 投資評等', '{name} {symbol} 分析師',
                '{name} {symbol} 分析師 預估', '{name} {symbol} analyst',
                '{name} {symbol} consensus'
            ],
            'taiwan_financial_simple': [
                'site:cnyes.com {symbol}', 'site:statementdog.com {symbol}',
                'site:wantgoo.com {symbol}', 'site:goodinfo.tw {symbol}',
                'site:uanalyze.com.tw {symbol}', 'site:findbillion.com {symbol}',
                'site:moneydj.com {symbol}', 'site:yahoo.com {symbol} 股票',
                '{name} {symbol} 股票', '{name} {symbol} 股價'
            ]
        }
        
        # metadata 模式 - 用於提取 search_query
        self.metadata_patterns = {
            'search_query': r'search_query:\s*(.+?)(?:\n|$)',
            'keywords': r'keywords:\s*(.+?)(?:\n|$)',
            'search_terms': r'search_terms:\s*(.+?)(?:\n|$)'
        }
        
        # 🔧 增強的無效模式過濾器 - 完全過濾 result 相關模式
        self.invalid_pattern_filters = [
            # Result 相關模式 - 完全過濾
            r'^result[_\s]*\d*[?\w]*$',     # result_1, result_11, result_x, result_xx, result_?
            r'^result[_\s]*[a-z]*$',        # result_x, result_xx, result_abc
            r'^result[_\s]*[?]*$',          # result_?, result_??
            r'^result$',                    # 單純的 result
            
            # 其他無效模式
            r'^\d+$',                       # 純數字
            r'^[a-zA-Z]$',                  # 單一字母
            r'^.{1,2}$',                    # 太短的模式
            r'^test',                       # 測試模式
            r'^debug',                      # 調試模式
            r'^temp',                       # 臨時模式
            r'^none$',                      # none
            r'^null$',                      # null
            r'^undefined$',                 # undefined
        ]

    def _load_watchlist_for_normalization(self) -> Dict[str, str]:
        """🔧 修正版：載入觀察名單用於標準化"""
        mapping = {}
        
        possible_paths = [
            'StockID_TWSE_TPEX.csv',
            '../StockID_TWSE_TPEX.csv', 
            '../../StockID_TWSE_TPEX.csv',
            'data/StockID_TWSE_TPEX.csv',
            '../data/StockID_TWSE_TPEX.csv'
        ]
        
        for csv_path in possible_paths:
            if os.path.exists(csv_path):
                try:
                    # 使用多種編碼嘗試讀取
                    encodings = ['utf-8', 'utf-8-sig', 'big5', 'gbk', 'cp950']
                    df = None
                    
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(csv_path, header=None, names=['code', 'name'], encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if df is not None:
                        for idx, row in df.iterrows():
                            try:
                                code = str(row['code']).strip()
                                name = str(row['name']).strip()
                                
                                if (code.isdigit() and len(code) == 4 and 
                                    name not in ['nan', 'NaN', 'null', 'None', '']):
                                    mapping[code] = name
                                    # 🔧 同時建立名稱到代號的反向映射
                                    mapping[name] = code
                            except:
                                continue
                        
                        print(f"✅ 觀察名單載入: {len(mapping)//2} 家公司 (用於標準化)")
                        return mapping
                        
                except Exception as e:
                    print(f"⚠️ 載入觀察名單失敗: {e}")
                    continue
        
        print("⚠️ 觀察名單未載入，標準化可能不完整")
        return {}

    def analyze_query_patterns(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """🔧 修正版：分析標準化查詢模式"""
        try:
            print("🔍 開始標準化查詢模式分析 (增強名稱標準化版)...")
            
            # 提取所有查詢模式並標準化
            all_query_patterns = []
            pattern_quality_mapping = {}
            pattern_company_mapping = {}
            
            for company_data in processed_companies:
                company_code = company_data.get('company_code', '')
                company_name = company_data.get('company_name', '')
                quality_score = company_data.get('quality_score', 0)
                
                # 🔧 驗證公司是否在觀察名單中
                if not self._is_company_in_watchlist(company_code, company_name):
                    print(f"⚠️ 跳過非觀察名單公司: {company_name}({company_code})")
                    continue
                
                # 提取查詢模式
                original_patterns = self._extract_query_patterns_from_company_data(company_data)
                
                if original_patterns:
                    for original_pattern in original_patterns:
                        # 🔧 強化無效模式過濾
                        if self._is_invalid_pattern_enhanced(original_pattern):
                            print(f"⚠️ 過濾無效模式: {original_pattern}")
                            continue
                        
                        # 🔧 強化標準化查詢模式
                        normalized_pattern = self._normalize_query_pattern_enhanced(
                            original_pattern, company_name, company_code
                        )
                        
                        if normalized_pattern and self._is_valid_normalized_pattern(normalized_pattern):
                            # 收集標準化的查詢模式
                            all_query_patterns.append(normalized_pattern)
                            
                            # 建立標準化模式與品質評分的對應
                            if normalized_pattern not in pattern_quality_mapping:
                                pattern_quality_mapping[normalized_pattern] = []
                            pattern_quality_mapping[normalized_pattern].append(quality_score)
                            
                            # 建立標準化模式與公司的對應
                            if normalized_pattern not in pattern_company_mapping:
                                pattern_company_mapping[normalized_pattern] = set()
                            pattern_company_mapping[normalized_pattern].add(f"{company_name}({company_code})")
                        else:
                            print(f"⚠️ 標準化失敗: {original_pattern} -> {normalized_pattern}")
            
            # 統計標準化查詢模式使用頻率
            pattern_counter = Counter(all_query_patterns)
            
            # 🔧 顯示標準化結果統計
            print(f"📊 標準化結果:")
            print(f"   原始模式數: {len([p for sublist in [self._extract_query_patterns_from_company_data(c) for c in processed_companies] for p in sublist])}")
            print(f"   有效標準化模式: {len(pattern_counter)}")
            print(f"   總使用次數: {sum(pattern_counter.values())}")
            
            # 計算查詢模式統計
            pattern_stats = {}
            for pattern, count in pattern_counter.items():
                quality_scores = pattern_quality_mapping.get(pattern, [])
                
                if quality_scores:
                    pattern_stats[pattern] = {
                        'usage_count': count,
                        'avg_quality_score': round(statistics.mean(quality_scores), 2),
                        'max_quality_score': max(quality_scores),
                        'min_quality_score': min(quality_scores),
                        'quality_std': round(statistics.stdev(quality_scores), 2) if len(quality_scores) > 1 else 0,
                        'company_count': len(pattern_company_mapping.get(pattern, set())),
                        'related_companies': list(pattern_company_mapping.get(pattern, set())),
                        'category': self._categorize_search_pattern(pattern),
                        'effectiveness_score': self._calculate_pattern_effectiveness_score(count, quality_scores),
                        'pattern_type': self._identify_pattern_type(pattern)
                    }
            
            # 🔧 顯示前10個最常用的標準化模式
            print(f"\n📊 前10個最常用的標準化模式:")
            top_patterns = sorted(pattern_stats.items(), key=lambda x: x[1]['usage_count'], reverse=True)[:10]
            for i, (pattern, stats) in enumerate(top_patterns, 1):
                print(f"   {i:2d}. {pattern} (使用 {stats['usage_count']} 次, 品質 {stats['avg_quality_score']})")
            
            # 生成分析結果
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'version': '3.6.1_enhanced',
                'analysis_type': 'search_query_patterns_normalized',
                'total_companies_analyzed': len(processed_companies),
                'valid_companies_processed': len([c for c in processed_companies if self._is_company_in_watchlist(c.get('company_code', ''), c.get('company_name', ''))]),
                'total_query_patterns_found': len(all_query_patterns),
                'unique_query_patterns': len(pattern_stats),
                'pattern_stats': pattern_stats,  # 關鍵！用於 CSV 生成
                'pattern_type_summary': self._generate_pattern_type_summary(pattern_stats),
                'top_query_patterns': self._get_top_query_patterns(pattern_stats, 20),
                'effectiveness_analysis': self._analyze_pattern_effectiveness(pattern_stats),
                'quality_correlation': self._analyze_pattern_quality_correlation(pattern_stats)
            }
            
            print(f"✅ 標準化查詢模式分析完成:")
            print(f"   有效公司數: {analysis_result['valid_companies_processed']}")
            print(f"   總查詢模式數: {analysis_result['total_query_patterns_found']}")
            print(f"   唯一標準化查詢模式: {analysis_result['unique_query_patterns']}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ 查詢模式分析失敗: {e}")
            return {'error': str(e)}

    def _is_company_in_watchlist(self, company_code: str, company_name: str) -> bool:
        """🆕 檢查公司是否在觀察名單中"""
        if not self.watchlist_mapping:
            return True  # 如果沒有觀察名單，允許所有公司
        
        # 檢查代號或名稱是否在觀察名單中
        return (company_code in self.watchlist_mapping or 
                company_name in self.watchlist_mapping)

    def _is_invalid_pattern_enhanced(self, pattern: str) -> bool:
        """🔧 增強版：檢查是否為無效模式"""
        if not pattern or not pattern.strip():
            return True
        
        pattern_clean = pattern.strip().lower()
        
        # 🔧 增強的無效模式檢查 - 完全過濾 result 相關
        for filter_pattern in self.invalid_pattern_filters:
            if re.match(filter_pattern, pattern_clean, re.IGNORECASE):
                print(f"🚫 過濾無效模式 (regex): {pattern}")
                return True
        
        # 🔧 額外的 result 模式檢查
        if 'result' in pattern_clean:
            print(f"🚫 過濾 result 模式: {pattern}")
            return True
        
        # 額外檢查
        if len(pattern_clean) <= 2:  # 太短
            return True
        
        if pattern_clean.count(' ') == 0 and not any(char in pattern_clean for char in [':', '.']):  # 單詞且非網站
            if len(pattern_clean) <= 4:
                return True
        
        return False

    def _normalize_query_pattern_enhanced(self, pattern: str, company_name: str, company_code: str) -> str:
        """🔧 增強版標準化查詢模式 - 更好的名稱處理"""
        if not pattern or not pattern.strip():
            return ""
        
        normalized = pattern.strip()
        
        # 🔧 清理特殊字符
        normalized = re.sub(r'["\']', '', normalized)  # 移除引號
        normalized = re.sub(r'[+\-()]', ' ', normalized)  # 移除搜尋運算符
        
        # 🔧 處理site:前綴
        site_prefix = ""
        site_match = re.match(r'^(site:[^\s]+)\s+(.+)$', normalized)
        if site_match:
            site_prefix = site_match.group(1) + ' '
            normalized = site_match.group(2)
        
        # 🔧 強化：使用觀察名單進行精確替換
        normalized = self._replace_with_watchlist_enhanced(normalized, company_code, company_name)
        
        # 🔧 清理多餘空格
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # 🔧 重新加上site前綴
        if site_prefix:
            normalized = site_prefix + normalized
        
        return normalized

    def _replace_with_watchlist_enhanced(self, text: str, company_code: str, company_name: str) -> str:
        """🔧 增強版：使用觀察名單進行精確替換，處理 -KY 等特殊後綴"""
        result = text
        
        # 🔧 1. 替換公司代號
        if company_code and company_code.isdigit() and len(company_code) == 4:
            # 使用詞邊界確保精確匹配
            result = re.sub(rf'\b{re.escape(company_code)}\b', '{symbol}', result)
        
        # 🔧 2. 增強的公司名稱替換 - 處理觀察名單
        if self.watchlist_mapping and company_code in self.watchlist_mapping:
            # 從觀察名單取得標準名稱
            standard_name = self.watchlist_mapping[company_code]
            
            # 🆕 獲取增強的名稱變體（包含 -KY 處理）
            name_variations = self._get_company_name_variations_enhanced(standard_name)
            
            # 按長度排序，長的優先匹配
            name_variations.sort(key=len, reverse=True)
            
            for variation in name_variations:
                if variation and len(variation) >= 2:
                    # 使用詞邊界進行精確匹配
                    escaped_variation = re.escape(variation)
                    result = re.sub(rf'\b{escaped_variation}\b', '{name}', result, flags=re.IGNORECASE)
        
        # 🔧 3. 回退：替換檔案中的公司名稱
        if company_name and '{name}' not in result:
            # 🆕 處理檔案中的公司名稱（包含特殊後綴）
            name_variations = self._get_company_name_variations_enhanced(company_name)
            name_variations.sort(key=len, reverse=True)
            
            for variation in name_variations:
                if variation and len(variation) >= 2:
                    escaped_variation = re.escape(variation)
                    result = re.sub(rf'\b{escaped_variation}\b', '{name}', result, flags=re.IGNORECASE)
        
        # 🔧 4. 最後檢查：如果仍然沒有模板變數，嘗試智能推測
        if '{name}' not in result and '{symbol}' not in result:
            result = self._smart_detect_company_references(result, company_name, company_code)
        
        return result

    def _get_company_name_variations_enhanced(self, company_name: str) -> List[str]:
        """🆕 增強版：取得公司名稱的各種變化形式，包含特殊後綴處理"""
        variations = [company_name]
        
        # 🆕 完整處理特殊後綴（如 -KY, -DR 等外國企業標記）
        special_suffix_types = ['KY', 'DR', 'GDR', 'ADR']
        name_without_special = company_name
        
        # 🔧 系統性處理：為每個後綴類型生成所有可能的格式變體
        for suffix_type in special_suffix_types:
            possible_formats = [
                f'-{suffix_type}',     # 奕力-KY
                f' {suffix_type}',     # 奕力 KY  
                f'{suffix_type}',      # 奕力KY
            ]
            
            for format_suffix in possible_formats:
                if name_without_special.endswith(format_suffix):
                    base_name = name_without_special[:-len(format_suffix)].strip()
                    variations.append(base_name)  # 基本名稱：奕力
                    
                    # 🆕 為這個基本名稱生成所有格式變體
                    all_variations_for_base = [
                        base_name + f'-{suffix_type}',   # 奕力-KY
                        base_name + f' {suffix_type}',   # 奕力 KY
                        base_name + f'{suffix_type}',    # 奕力KY
                    ]
                    variations.extend(all_variations_for_base)
                    
                    # 🆕 更新基礎名稱
                    name_without_special = base_name
                    break  # 找到匹配後跳出內層循環
        
        # 移除常見企業後綴
        company_suffixes = ['股份有限公司', '有限公司', '公司', '集團', '控股', '科技', '電子', '工業']
        
        current_name = name_without_special
        for suffix in company_suffixes:
            if current_name.endswith(suffix):
                current_name = current_name[:-len(suffix)].strip()
                if current_name:  # 確保不是空字串
                    variations.append(current_name)
        
        # 🆕 特別處理中文公司名稱的常見縮寫
        name_aliases = {
            '台積電': ['台積', 'TSMC', '台灣積體電路'],
            '鴻海': ['鴻海精密', 'Foxconn', '富士康'],
            '聯發科': ['聯發', 'MediaTek', '聯發科技'],
            '台達電': ['台達', 'Delta', '台達電子'],
            '中華電信': ['中華電', '中華電信'],
            '奕力': ['奕力科技'],  # 🆕 針對您的例子
            '光焱': ['光焱科技'],
        }
        
        # 檢查是否有別名定義
        for name_part in variations:
            if name_part in name_aliases:
                variations.extend(name_aliases[name_part])
        
        # 🆕 自動生成可能的縮寫（針對中文公司名）
        if len(company_name) >= 3 and any('\u4e00' <= char <= '\u9fff' for char in company_name):
            # 如果是中文名稱，嘗試取前2-3個字作為縮寫
            if len(company_name) >= 4:
                variations.append(company_name[:3])  # 前3個字
            if len(company_name) >= 3:
                variations.append(company_name[:2])  # 前2個字
        
        # 去重並按長度排序（長的優先，避免誤替換）
        variations = list(set(v for v in variations if v and len(v.strip()) >= 2))
        variations.sort(key=len, reverse=True)
        
        return variations

    def _smart_detect_company_references(self, text: str, company_name: str, company_code: str) -> str:
        """🔧 增強版：智能檢測公司引用"""
        words = text.split()
        result_words = []
        
        for word in words:
            # 檢查是否為4位數字（可能是公司代號）
            if word.isdigit() and len(word) == 4:
                result_words.append('{symbol}')
            # 🆕 檢查是否包含中文且可能是公司名稱（包含特殊後綴）
            elif re.search(r'[\u4e00-\u9fff]', word) and 2 <= len(word) <= 10:
                # 檢查是否與已知公司名稱相似
                if self._is_likely_company_name_enhanced(word, company_name):
                    result_words.append('{name}')
                else:
                    result_words.append(word)
            else:
                result_words.append(word)
        
        return ' '.join(result_words)

    def _is_likely_company_name_enhanced(self, word: str, company_name: str) -> bool:
        """🆕 增強版：檢查單詞是否可能是公司名稱"""
        if not word or not company_name:
            return False
        
        # 🆕 處理特殊後綴
        word_clean = word
        company_clean = company_name
        
        special_suffixes = ['-KY', '-DR', ' KY', ' DR']
        for suffix in special_suffixes:
            word_clean = word_clean.replace(suffix, '').strip()
            company_clean = company_clean.replace(suffix, '').strip()
        
        # 如果觀察名單可用，檢查是否在其中
        if self.watchlist_mapping:
            for name in self.watchlist_mapping.values():
                if isinstance(name, str):
                    name_clean = name
                    for suffix in special_suffixes:
                        name_clean = name_clean.replace(suffix, '').strip()
                    
                    if (word_clean in name_clean or name_clean in word_clean or
                        word in name or name in word):
                        return True
        
        # 回退：基本相似性檢查
        if (word_clean in company_clean or company_clean in word_clean or
            word in company_name or company_name in word):
            return True
        
        # 檢查共同字符比例
        if len(word_clean) >= 2 and len(company_clean) >= 2:
            common_chars = set(word_clean) & set(company_clean)
            similarity = len(common_chars) / max(len(set(word_clean)), len(set(company_clean)))
            return similarity >= 0.6
        
        return False

    def _is_valid_normalized_pattern(self, pattern: str) -> bool:
        """🔧 檢查標準化模式是否有效"""
        if not pattern or not pattern.strip():
            return False
        
        # 必須包含至少一個模板變數
        if '{name}' not in pattern and '{symbol}' not in pattern:
            return False
        
        # 不應該只是模板變數
        pattern_clean = pattern.replace('{name}', '').replace('{symbol}', '').strip()
        if not pattern_clean:
            return False
        
        # 長度檢查
        if len(pattern) < 5:
            return False
        
        return True

    def _extract_query_patterns_from_company_data(self, company_data: Dict) -> List[str]:
        """從公司資料中提取查詢模式"""
        query_patterns = []
        
        # 1. 從 YAML metadata 中提取 search_query
        yaml_data = company_data.get('yaml_data', {})
        if yaml_data:
            search_query = yaml_data.get('search_query', '')
            if search_query and search_query.strip():
                cleaned_query = self._clean_query_pattern(search_query.strip())
                if cleaned_query:
                    query_patterns.append(cleaned_query)
        
        # 2. 從檔案內容中提取 metadata 中的查詢模式
        content = company_data.get('content', '')
        if content:
            metadata_patterns = self._extract_query_patterns_from_content_metadata(content)
            query_patterns.extend(metadata_patterns)
        
        # 去重但保持順序
        unique_patterns = []
        seen_patterns = set()
        for pattern in query_patterns:
            pattern_lower = pattern.lower()
            if pattern_lower not in seen_patterns:
                unique_patterns.append(pattern)
                seen_patterns.add(pattern_lower)
        
        return unique_patterns

    def _clean_query_pattern(self, query: str) -> str:
        """清理查詢模式但保持完整性"""
        if not query or query.strip() == '':
            return ''
        
        cleaned = query.strip()
        cleaned = re.sub(r'[+\-"()]', ' ', cleaned)  # 移除搜尋運算符
        cleaned = re.sub(r'\s+', ' ', cleaned)       # 合併多個空格
        cleaned = cleaned.strip()
        
        # 檢查長度
        if len(cleaned) < 3:
            return ''
        
        return cleaned

    def _extract_query_patterns_from_content_metadata(self, content: str) -> List[str]:
        """從內容的 metadata 中提取查詢模式"""
        patterns = []
        
        # 檢查是否有 YAML frontmatter
        if content.startswith('---'):
            try:
                end_pos = content.find('---', 3)
                if end_pos != -1:
                    yaml_content = content[3:end_pos].strip()
                    
                    # 使用正則表達式提取查詢相關欄位
                    for field_name, pattern in self.metadata_patterns.items():
                        matches = re.findall(pattern, yaml_content, re.MULTILINE | re.IGNORECASE)
                        for match in matches:
                            if match.strip():
                                cleaned_pattern = self._clean_query_pattern(match.strip())
                                if cleaned_pattern:
                                    patterns.append(cleaned_pattern)
            except Exception:
                pass
        
        return patterns

    # 保留其他現有方法...
    def _identify_pattern_type(self, pattern: str) -> str:
        """識別查詢模式類型"""
        pattern_lower = pattern.lower()
        
        # factset_direct 模式
        if 'factset' in pattern_lower and 'site:' not in pattern_lower:
            return 'factset_direct'
        
        # cnyes_factset 模式
        if 'site:cnyes.com' in pattern_lower:
            return 'cnyes_factset'
        
        # eps_forecast 模式
        if any(term in pattern_lower for term in ['eps', '每股盈餘']) and \
           any(term in pattern_lower for term in ['預估', '2025', '2026', '2027']):
            return 'eps_forecast'
        
        # analyst_consensus 模式
        if any(term in pattern_lower for term in ['分析師', 'analyst', 'consensus']):
            return 'analyst_consensus'
        
        # taiwan_financial_simple 模式
        taiwan_sites = ['cnyes.com', 'statementdog.com', 'wantgoo.com', 'goodinfo.tw']
        if any(site in pattern_lower for site in taiwan_sites):
            return 'taiwan_financial_simple'
        
        return 'other'

    def _categorize_search_pattern(self, pattern: str) -> str:
        """將搜尋模式分類"""
        pattern_type = self._identify_pattern_type(pattern)
        
        category_mapping = {
            'factset_direct': 'FactSet直接',
            'cnyes_factset': '鉅亨網FactSet',
            'eps_forecast': 'EPS預估',
            'analyst_consensus': '分析師共識',
            'taiwan_financial_simple': '台灣財經網站',
            'other': '其他'
        }
        
        return category_mapping.get(pattern_type, '其他')

    def _calculate_pattern_effectiveness_score(self, usage_count: int, quality_scores: List[float]) -> float:
        """計算查詢模式效果評分"""
        if not quality_scores:
            return 0.0
        
        avg_quality = statistics.mean(quality_scores)
        frequency_weight = min(usage_count / 10, 1.0)
        effectiveness = avg_quality * (0.7 + 0.3 * frequency_weight)
        
        return round(effectiveness, 2)

    def _generate_pattern_type_summary(self, pattern_stats: Dict) -> Dict[str, Any]:
        """生成查詢模式類型摘要"""
        type_summary = {}
        
        for pattern, stats in pattern_stats.items():
            pattern_type = stats.get('pattern_type', 'other')
            
            if pattern_type not in type_summary:
                type_summary[pattern_type] = {
                    'pattern_count': 0,
                    'total_usage': 0,
                    'quality_scores': [],
                    'patterns': []
                }
            
            type_summary[pattern_type]['pattern_count'] += 1
            type_summary[pattern_type]['total_usage'] += stats['usage_count']
            type_summary[pattern_type]['quality_scores'].append(stats['avg_quality_score'])
            type_summary[pattern_type]['patterns'].append(pattern)
        
        return type_summary

    def _get_top_query_patterns(self, pattern_stats: Dict, top_n: int = 20) -> List[Tuple[str, Dict]]:
        """取得效果最好的查詢模式"""
        sorted_patterns = sorted(pattern_stats.items(), 
                               key=lambda x: x[1]['effectiveness_score'], 
                               reverse=True)
        
        return sorted_patterns[:top_n]

    def _analyze_pattern_effectiveness(self, pattern_stats: Dict) -> Dict[str, Any]:
        """分析查詢模式效果"""
        effectiveness_scores = [stats['effectiveness_score'] for stats in pattern_stats.values()]
        
        if not effectiveness_scores:
            return {}
        
        return {
            'average_effectiveness': round(statistics.mean(effectiveness_scores), 2),
            'median_effectiveness': round(statistics.median(effectiveness_scores), 2)
        }

    def _analyze_pattern_quality_correlation(self, pattern_stats: Dict) -> Dict[str, Any]:
        """分析查詢模式與品質的關聯性"""
        correlations = []
        
        for pattern, stats in pattern_stats.items():
            if stats['usage_count'] >= 2:
                correlation_score = stats['avg_quality_score'] * (1 + min(stats['usage_count'] / 10, 0.5))
                correlations.append({
                    'pattern': pattern,
                    'correlation_score': round(correlation_score, 2)
                })
        
        correlations.sort(key=lambda x: x['correlation_score'], reverse=True)
        
        return {
            'strong_positive_correlation': correlations[:10],
            'recommended_patterns': [c['pattern'] for c in correlations[:5]]
        }

    def analyze_all_keywords(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """向下相容：自動轉換為查詢模式分析"""
        print("🔄 檢測到關鍵字分析請求，自動轉換為查詢模式分析...")
        return self.analyze_query_patterns(processed_companies)


# 測試功能
if __name__ == "__main__":
    analyzer = KeywordAnalyzer()
    
    print("=== 增強版查詢模式分析器測試 v3.6.1 ===")
    
    # 測試資料 - 包含您提到的案例
    test_companies = [
        {
            'company_code': '6962',
            'company_name': '奕力-KY',
            'quality_score': 8.5,
            'yaml_data': {
                'search_query': '6962,奕力-KY factset'  # 您的例子
            }
        },
        {
            'company_code': '3089',
            'company_name': '光焱科技',
            'quality_score': 7.5,
            'yaml_data': {
                'search_query': '光焱科技 factset 目標價'
            }
        },
        {
            'company_code': '2330',
            'company_name': '台積電',
            'quality_score': 9.5,
            'yaml_data': {
                'search_query': '台積電 2330 factset 分析師'
            }
        },
        {
            'company_code': '1234',
            'company_name': '測試公司',
            'quality_score': 5.0,
            'yaml_data': {
                'search_query': 'result_x'  # 無效模式 - 應該被過濾
            }
        },
        {
            'company_code': '5678',
            'company_name': '另一測試',
            'quality_score': 6.0,
            'yaml_data': {
                'search_query': 'result_xx'  # 無效模式 - 應該被過濾
            }
        }
    ]
    
    print(f"\n🧪 測試增強版標準化 (包含 -KY 處理和 result 過濾):")
    analysis_result = analyzer.analyze_query_patterns(test_companies)
    
    if 'error' not in analysis_result:
        print(f"\n📊 增強版分析結果:")
        pattern_stats = analysis_result['pattern_stats']
        
        print(f"\n✅ 標準化後的查詢模式:")
        for pattern, stats in list(pattern_stats.items())[:10]:
            print(f"   {pattern}: 使用 {stats['usage_count']} 次, 分類: {stats['category']}")
        
        # 驗證 -KY 處理
        ky_patterns = [p for p in pattern_stats.keys() if '{name}' in p and 'factset' in p]
        print(f"\n🔍 -KY 處理驗證:")
        print(f"   找到包含 {{name}} 的 factset 模式: {len(ky_patterns)}")
        for pattern in ky_patterns[:3]:
            print(f"   - {pattern}")
        
        # 驗證 result 過濾
        result_patterns = [p for p in pattern_stats.keys() if 'result' in p.lower()]
        print(f"\n🚫 Result 過濾驗證:")
        print(f"   找到包含 'result' 的模式: {len(result_patterns)} (應該為 0)")
        if result_patterns:
            print(f"   ❌ 發現未過濾的 result 模式: {result_patterns}")
        else:
            print(f"   ✅ 所有 result 模式已成功過濾")
        
    else:
        print(f"❌ 分析失敗: {analysis_result['error']}")
    
    print(f"\n✅ 增強版查詢模式分析器測試完成！")
    print(f"🆕 新功能: -KY 後綴處理、增強 result 過濾、智能名稱變體匹配")