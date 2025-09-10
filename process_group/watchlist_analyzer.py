#!/usr/bin/env python3
"""
Watchlist Analyzer - FactSet Pipeline v3.6.1 (Refined)
新增觀察名單處理統計分析功能 - 增強版本
"""

import os
import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter  # 🔧 修復：添加 Counter 導入
import statistics
import json

class WatchlistAnalyzer:
    """觀察名單分析器 - v3.6.1 增強版本"""
    
    def __init__(self):
        """初始化觀察名單分析器"""
        
        # 載入觀察名單
        self.watchlist_mapping = self._load_watchlist()
        self.validation_enabled = len(self.watchlist_mapping) > 0
        
        # 停用詞
        self.stop_words = {
            '的', '和', '與', '或', '及', '在', '為', '是', '有', '此', '將', '會',
            'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for'
        }
        
        # 觀察名單狀態分類
        self.status_categories = {
            'processed': '已處理',
            'not_found': '未找到MD檔案',
            'validation_failed': '驗證失敗',
            'low_quality': '品質過低',
            'multiple_files': '多個檔案'
        }
        
        # 關鍵字分類
        self.keyword_categories = {
            'company': ['公司', '企業', '集團', 'corp', 'company', 'group'],
            'financial': ['eps', '營收', '獲利', '股價', '目標價', 'revenue', 'profit'],
            'analysis': ['分析', '預估', '評估', '展望', 'analysis', 'forecast', 'estimate'],
            'source': ['factset', 'bloomberg', '券商', '投顧', 'analyst']
        }
        
        # 品質評分閾值
        self.quality_thresholds = {
            'excellent': 8.0,
            'good': 6.0,
            'average': 4.0,
            'poor': 0.0
        }

    def _load_watchlist(self) -> Dict[str, str]:
        """載入StockID_TWSE_TPEX.csv - 增強版本"""
        mapping = {}
        
        possible_paths = [
            'StockID_TWSE_TPEX.csv',
            '../StockID_TWSE_TPEX.csv',
            '../../StockID_TWSE_TPEX.csv',
            'data/StockID_TWSE_TPEX.csv',
            '../data/StockID_TWSE_TPEX.csv',
            'watchlist.csv',
            '../watchlist.csv'
        ]
        
        for csv_path in possible_paths:
            if os.path.exists(csv_path):
                try:
                    print(f"🔍 載入觀察名單: {csv_path}")
                    
                    # 使用多種編碼嘗試讀取
                    encodings = ['utf-8', 'utf-8-sig', 'big5', 'gbk', 'cp950']
                    df = None
                    
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(csv_path, header=None, names=['code', 'name'], encoding=encoding)
                            print(f"✅ 成功使用 {encoding} 編碼讀取")
                            break
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            print(f"⚠️ 使用 {encoding} 編碼讀取失敗: {e}")
                            continue
                    
                    if df is None:
                        print(f"❌ 無法使用任何編碼讀取 {csv_path}")
                        continue
                    
                    # 驗證和清理數據
                    valid_count = 0
                    invalid_count = 0
                    duplicate_count = 0
                    
                    for idx, row in df.iterrows():
                        try:
                            code = str(row['code']).strip()
                            name = str(row['name']).strip()
                            
                            # 驗證公司代號格式
                            if not self._is_valid_company_code(code):
                                invalid_count += 1
                                continue
                                
                            # 驗證公司名稱
                            if not self._is_valid_company_name(name):
                                invalid_count += 1
                                continue
                            
                            # 檢查重複
                            if code in mapping:
                                duplicate_count += 1
                                print(f"⚠️ 重複公司代號: {code}")
                                continue
                            
                            mapping[code] = name
                            valid_count += 1
                            
                        except Exception as e:
                            invalid_count += 1
                            print(f"❌ 處理第{idx+1}行時發生錯誤: {e}")
                            continue
                    
                    print(f"📊 觀察名單載入統計:")
                    print(f"   檔案: {csv_path}")
                    print(f"   總行數: {len(df)}")
                    print(f"   有效數據: {valid_count}")
                    print(f"   無效數據: {invalid_count}")
                    print(f"   重複數據: {duplicate_count}")
                    print(f"   成功率: {valid_count/len(df)*100:.1f}%")
                    
                    # 驗證載入的資料品質
                    self._validate_watchlist_quality(mapping)
                    
                    return mapping
                    
                except Exception as e:
                    print(f"❌ 讀取觀察名單失敗 {csv_path}: {e}")
                    continue
        
        print("❌ 所有觀察名單載入嘗試均失敗")
        print("💡 請確保StockID_TWSE_TPEX.csv檔案存在且格式正確")
        return {}

    def _validate_watchlist_quality(self, mapping: Dict[str, str]):
        """驗證觀察名單品質"""
        if not mapping:
            return
            
        # 檢查代號範圍分布
        code_ranges = {'1000-2999': 0, '3000-5999': 0, '6000-8999': 0, '9000+': 0}
        
        for code in mapping.keys():
            try:
                code_num = int(code)
                if 1000 <= code_num <= 2999:
                    code_ranges['1000-2999'] += 1
                elif 3000 <= code_num <= 5999:
                    code_ranges['3000-5999'] += 1
                elif 6000 <= code_num <= 8999:
                    code_ranges['6000-8999'] += 1
                else:
                    code_ranges['9000+'] += 1
            except ValueError:
                continue
        
        print(f"📊 觀察名單代號分布:")
        for range_name, count in code_ranges.items():
            print(f"   {range_name}: {count} 家")
        
        # 檢查是否有知名公司
        famous_companies = {
            '2330': '台積電', '2317': '鴻海', '2454': '聯發科',
            '2882': '國泰金', '2891': '中信金', '2412': '中華電'
        }
        
        found_famous = 0
        for code, expected_name in famous_companies.items():
            if code in mapping:
                actual_name = mapping[code]
                if expected_name in actual_name or actual_name in expected_name:
                    found_famous += 1
                    print(f"✅ 找到知名公司: {code} - {actual_name}")
        
        if found_famous == 0:
            print("⚠️ 未找到任何知名公司，請檢查觀察名單內容")

    def _is_valid_company_code(self, code: str) -> bool:
        """驗證公司代號格式 - 增強版本"""
        if not code or code in ['nan', 'NaN', 'null', 'None', '', 'NULL']:
            return False
        
        clean_code = code.strip().strip('\'"')
        
        # 檢查是否為數字
        if not clean_code.isdigit():
            return False
            
        # 檢查長度
        if len(clean_code) != 4:
            return False
        
        # 檢查數字範圍（台股代號範圍）
        try:
            code_num = int(clean_code)
            if not (1000 <= code_num <= 9999):
                return False
        except ValueError:
            return False
        
        return True

    def _is_valid_company_name(self, name: str) -> bool:
        """驗證公司名稱 - 增強版本"""
        if not name or name in ['nan', 'NaN', 'null', 'None', '', 'NULL']:
            return False
        
        clean_name = name.strip()
        
        # 檢查長度
        if len(clean_name) < 1 or len(clean_name) > 30:
            return False
        
        # 檢查是否包含無效字符
        invalid_chars = ['|', '\t', '\n', '\r', '\x00']
        if any(char in clean_name for char in invalid_chars):
            return False
        
        # 檢查是否為明顯無效的名稱
        invalid_names = ['test', 'example', '測試', '範例', '123', 'abc']
        if clean_name.lower() in invalid_names:
            return False
        
        return True

    def analyze_watchlist_coverage(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """分析觀察名單覆蓋情況 - 增強版本"""
        if not self.validation_enabled:
            return {
                'error': '觀察名單未載入',
                'total_watchlist_companies': 0,
                'companies_with_md_files': 0,
                'coverage_rate': 0.0,
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        try:
            print("📊 開始觀察名單覆蓋分析...")
            
            # 建立公司處理狀態對應
            company_processing_status = self.analyze_company_processing_status(processed_companies)
            
            # 基本統計
            total_watchlist = len(self.watchlist_mapping)
            companies_with_files = len([c for c in company_processing_status.values() if c['file_count'] > 0])
            companies_processed = len([c for c in company_processing_status.values() if c['status'] == 'processed'])
            
            coverage_rate = (companies_with_files / total_watchlist) * 100 if total_watchlist > 0 else 0
            success_rate = (companies_processed / total_watchlist) * 100 if total_watchlist > 0 else 0
            
            # 狀態分佈統計
            status_counts = {}
            for status_info in company_processing_status.values():
                status = status_info['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # 品質統計
            quality_scores = [c['average_quality_score'] for c in company_processing_status.values() 
                             if c['average_quality_score'] > 0]
            
            quality_stats = self._calculate_quality_statistics(quality_scores)
            
            # 檔案統計
            file_stats = self._calculate_file_statistics(company_processing_status)
            
            # 搜尋模式分析
            search_pattern_analysis = self.analyze_search_patterns(processed_companies)
            
            # 關鍵字效果分析
            keyword_effectiveness = self.calculate_keyword_effectiveness_by_company(processed_companies)
            
            # 缺失公司分析
            missing_companies_analysis = self._analyze_missing_companies(company_processing_status)
            
            analysis_result = {
                'analysis_timestamp': datetime.now().isoformat(),
                'version': '3.6.1',
                'analysis_type': 'watchlist_coverage_enhanced',
                
                # 基本統計
                'total_watchlist_companies': total_watchlist,
                'companies_with_md_files': companies_with_files,
                'companies_processed_successfully': companies_processed,
                'coverage_rate': round(coverage_rate, 1),
                'success_rate': round(success_rate, 1),
                
                # 詳細分析
                'company_status_summary': status_counts,
                'company_processing_status': company_processing_status,
                'quality_statistics': quality_stats,
                'file_statistics': file_stats,
                'search_pattern_analysis': search_pattern_analysis,
                'keyword_effectiveness_analysis': keyword_effectiveness,
                'missing_companies_analysis': missing_companies_analysis,
                
                # 健康度指標
                'health_indicators': self._calculate_health_indicators(
                    total_watchlist, companies_processed, quality_scores, coverage_rate
                )
            }
            
            print(f"✅ 觀察名單覆蓋分析完成:")
            print(f"   觀察名單公司數: {total_watchlist}")
            print(f"   有MD檔案公司數: {companies_with_files}")
            print(f"   覆蓋率: {coverage_rate:.1f}%")
            print(f"   成功處理率: {success_rate:.1f}%")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ 觀察名單覆蓋分析失敗: {e}")
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat(),
                'total_watchlist_companies': len(self.watchlist_mapping) if self.watchlist_mapping else 0
            }

    def analyze_company_processing_status(self, processed_companies: List[Dict]) -> Dict[str, Dict]:
        """分析每家公司的處理狀態 - 增強版本"""
        company_status = {}
        
        # 初始化所有觀察名單公司
        for company_code, company_name in self.watchlist_mapping.items():
            company_status[company_code] = {
                'company_name': company_name,
                'file_count': 0,
                'files': [],
                'status': 'not_found',
                'average_quality_score': 0.0,
                'max_quality_score': 0.0,
                'min_quality_score': 0.0,
                'search_keywords': [],
                'latest_file_date': '',
                'earliest_file_date': '',
                'validation_passed': True,
                'validation_errors': [],
                'data_sources': set(),
                'analysis_coverage': {
                    'has_eps_data': False,
                    'has_target_price': False,
                    'has_analyst_info': False
                }
            }
        
        # 處理已有資料的公司
        for company_data in processed_companies:
            company_code = company_data.get('company_code', '')
            
            if company_code in company_status:
                company_status[company_code]['files'].append(company_data)
                company_status[company_code]['file_count'] += 1
                
                # 收集搜尋關鍵字
                search_keywords = company_data.get('search_keywords', [])
                if search_keywords:
                    existing_keywords = set(company_status[company_code]['search_keywords'])
                    new_keywords = set(search_keywords)
                    company_status[company_code]['search_keywords'] = list(existing_keywords | new_keywords)
                
                # 更新日期範圍
                content_date = company_data.get('content_date', '')
                if content_date:
                    if not company_status[company_code]['latest_file_date'] or content_date > company_status[company_code]['latest_file_date']:
                        company_status[company_code]['latest_file_date'] = content_date
                    
                    if not company_status[company_code]['earliest_file_date'] or content_date < company_status[company_code]['earliest_file_date']:
                        company_status[company_code]['earliest_file_date'] = content_date
                
                # 收集資料來源
                data_source = company_data.get('data_source', '')
                if data_source:
                    company_status[company_code]['data_sources'].add(data_source)
                
                # 分析數據覆蓋度
                analysis_coverage = company_status[company_code]['analysis_coverage']
                if company_data.get('has_eps_data', False):
                    analysis_coverage['has_eps_data'] = True
                if company_data.get('has_target_price', False):
                    analysis_coverage['has_target_price'] = True
                if company_data.get('analyst_count', 0) > 0:
                    analysis_coverage['has_analyst_info'] = True
                
                # 收集驗證狀態
                if not company_data.get('content_validation_passed', True):
                    company_status[company_code]['validation_passed'] = False
                    validation_errors = company_data.get('validation_errors', [])
                    company_status[company_code]['validation_errors'].extend(validation_errors)
        
        # 計算每家公司的狀態和品質統計
        for company_code, status_info in company_status.items():
            files = status_info['files']
            
            if files:
                # 計算品質統計
                quality_scores = [f.get('quality_score', 0) for f in files]
                status_info['average_quality_score'] = round(statistics.mean(quality_scores), 2)
                status_info['max_quality_score'] = max(quality_scores)
                status_info['min_quality_score'] = min(quality_scores)
                
                # 確定處理狀態
                status_info['status'] = self._categorize_company_status(company_code, files)
                
                # 轉換資料來源集合為列表
                status_info['data_sources'] = list(status_info['data_sources'])
            else:
                status_info['status'] = 'not_found'
                status_info['data_sources'] = []
        
        return company_status

    def _calculate_quality_statistics(self, quality_scores: List[float]) -> Dict[str, Any]:
        """計算品質統計"""
        if not quality_scores:
            return {
                'average_quality_score': 0,
                'median_quality_score': 0,
                'companies_above_8': 0,
                'companies_above_6': 0,
                'companies_below_3': 0,
                'zero_score_companies': 0,
                'quality_distribution': {}
            }
        
        quality_distribution = {
            'excellent': len([s for s in quality_scores if s >= self.quality_thresholds['excellent']]),
            'good': len([s for s in quality_scores if self.quality_thresholds['good'] <= s < self.quality_thresholds['excellent']]),
            'average': len([s for s in quality_scores if self.quality_thresholds['average'] <= s < self.quality_thresholds['good']]),
            'poor': len([s for s in quality_scores if s < self.quality_thresholds['average']])
        }
        
        return {
            'average_quality_score': round(statistics.mean(quality_scores), 2),
            'median_quality_score': round(statistics.median(quality_scores), 2),
            'companies_above_8': len([s for s in quality_scores if s >= 8.0]),
            'companies_above_6': len([s for s in quality_scores if s >= 6.0]),
            'companies_below_3': len([s for s in quality_scores if s <= 3.0]),
            'zero_score_companies': len([s for s in quality_scores if s == 0]),
            'quality_distribution': quality_distribution,
            'quality_std': round(statistics.stdev(quality_scores), 2) if len(quality_scores) > 1 else 0
        }

    def _calculate_file_statistics(self, company_processing_status: Dict) -> Dict[str, Any]:
        """計算檔案統計"""
        file_counts = [c['file_count'] for c in company_processing_status.values() if c['file_count'] > 0]
        companies_with_multiple = len([c for c in company_processing_status.values() if c['file_count'] > 1])
        
        # 找出檔案最多的公司
        max_files_company = max(company_processing_status.items(), 
                              key=lambda x: x[1]['file_count'], default=(None, {'file_count': 0}))
        
        # 資料來源統計
        all_sources = set()
        for status_info in company_processing_status.values():
            all_sources.update(status_info.get('data_sources', []))
        
        return {
            'total_md_files': sum(file_counts),
            'files_per_company_avg': round(statistics.mean(file_counts), 2) if file_counts else 0,
            'companies_with_multiple_files': companies_with_multiple,
            'most_files_company': max_files_company[1].get('company_name', ''),
            'most_files_count': max_files_company[1]['file_count'],
            'unique_data_sources': list(all_sources),
            'data_source_count': len(all_sources)
        }

    def _analyze_missing_companies(self, company_processing_status: Dict) -> Dict[str, Any]:
        """分析缺失公司"""
        missing_companies = []
        low_quality_companies = []
        
        for company_code, status_info in company_processing_status.items():
            if status_info['status'] == 'not_found':
                missing_companies.append({
                    'company_code': company_code,
                    'company_name': status_info['company_name'],
                    'priority': self._calculate_missing_priority(company_code, status_info['company_name'])
                })
            elif status_info['status'] == 'low_quality':
                low_quality_companies.append({
                    'company_code': company_code,
                    'company_name': status_info['company_name'],
                    'average_quality': status_info['average_quality_score']
                })
        
        # 按優先級排序
        missing_companies.sort(key=lambda x: x['priority'], reverse=True)
        low_quality_companies.sort(key=lambda x: x['average_quality'])
        
        return {
            'missing_companies': missing_companies,
            'missing_count': len(missing_companies),
            'low_quality_companies': low_quality_companies,
            'low_quality_count': len(low_quality_companies),
            'improvement_suggestions': self._generate_improvement_suggestions(missing_companies, low_quality_companies)
        }

    def _calculate_health_indicators(self, total_companies: int, processed_companies: int, 
                                   quality_scores: List[float], coverage_rate: float) -> Dict[str, Any]:
        """計算健康度指標"""
        if total_companies == 0:
            return {'overall_health': 0, 'health_grade': 'F'}
        
        # 覆蓋率健康度 (40%)
        coverage_health = coverage_rate / 100 * 40
        
        # 處理成功率健康度 (30%)
        success_rate = (processed_companies / total_companies) * 100
        success_health = success_rate / 100 * 30
        
        # 品質健康度 (30%)
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            quality_health = (avg_quality / 10) * 30
        else:
            quality_health = 0
        
        overall_health = coverage_health + success_health + quality_health
        
        # 健康度等級
        if overall_health >= 90:
            health_grade = 'A+'
        elif overall_health >= 80:
            health_grade = 'A'
        elif overall_health >= 70:
            health_grade = 'B'
        elif overall_health >= 60:
            health_grade = 'C'
        elif overall_health >= 50:
            health_grade = 'D'
        else:
            health_grade = 'F'
        
        return {
            'overall_health': round(overall_health, 1),
            'health_grade': health_grade,
            'coverage_health': round(coverage_health, 1),
            'success_health': round(success_health, 1),
            'quality_health': round(quality_health, 1),
            'health_components': {
                'coverage_rate': coverage_rate,
                'success_rate': success_rate,
                'average_quality': round(statistics.mean(quality_scores), 2) if quality_scores else 0
            }
        }

    def analyze_search_patterns(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """分析搜尋關鍵字模式 - 增強版本"""
        # 提取所有關鍵字
        all_keywords = []
        keyword_quality_scores = {}
        keyword_company_mapping = {}
        
        for company_data in processed_companies:
            search_keywords = company_data.get('search_keywords', [])
            quality_score = company_data.get('quality_score', 0)
            company_code = company_data.get('company_code', '')
            company_name = company_data.get('company_name', '')
            
            # 只處理觀察名單中的公司
            if company_code in self.watchlist_mapping:
                for keyword in search_keywords:
                    if keyword and keyword.lower() not in self.stop_words:
                        all_keywords.append(keyword)
                        
                        if keyword not in keyword_quality_scores:
                            keyword_quality_scores[keyword] = []
                        keyword_quality_scores[keyword].append(quality_score)
                        
                        if keyword not in keyword_company_mapping:
                            keyword_company_mapping[keyword] = set()
                        keyword_company_mapping[keyword].add(f"{company_name}({company_code})")
        
        # 統計最常用關鍵字
        keyword_counts = Counter(all_keywords)
        most_common_keywords = keyword_counts.most_common(20)
        
        # 計算關鍵字與品質的關聯
        keyword_quality_correlation = {}
        for keyword, scores in keyword_quality_scores.items():
            if scores:
                keyword_quality_correlation[keyword] = round(statistics.mean(scores), 2)
        
        # 按關鍵字數量分組公司
        companies_by_keyword_count = self._group_companies_by_keyword_count(processed_companies)
        
        # 找出效果最好的搜尋模式
        effective_patterns = self._identify_effective_patterns(keyword_quality_correlation, keyword_counts)
        
        # 關鍵字分類統計
        keyword_category_stats = self._analyze_keyword_categories(keyword_counts, keyword_quality_correlation)
        
        return {
            'most_common_keywords': most_common_keywords,
            'keyword_quality_correlation': keyword_quality_correlation,
            'companies_by_keyword_count': companies_by_keyword_count,
            'effective_search_patterns': effective_patterns,
            'keyword_category_statistics': keyword_category_stats,
            'total_unique_keywords': len(keyword_counts),
            'average_keywords_per_company': round(len(all_keywords) / len([c for c in processed_companies if c.get('company_code') in self.watchlist_mapping]), 2) if processed_companies else 0
        }

    def _group_companies_by_keyword_count(self, processed_companies: List[Dict]) -> Dict[str, List[str]]:
        """按關鍵字數量分組公司"""
        companies_by_keyword_count = {'0': [], '1-2': [], '3-5': [], '6+': []}
        
        for company_code in self.watchlist_mapping.keys():
            # 找到該公司的關鍵字
            company_keywords = []
            company_name = self.watchlist_mapping[company_code]
            
            for company_data in processed_companies:
                if company_data.get('company_code') == company_code:
                    company_keywords.extend(company_data.get('search_keywords', []))
            
            keyword_count = len(set(company_keywords))
            
            if keyword_count == 0:
                companies_by_keyword_count['0'].append(company_name)
            elif keyword_count <= 2:
                companies_by_keyword_count['1-2'].append(company_name)
            elif keyword_count <= 5:
                companies_by_keyword_count['3-5'].append(company_name)
            else:
                companies_by_keyword_count['6+'].append(company_name)
        
        return companies_by_keyword_count

    def _identify_effective_patterns(self, keyword_quality_correlation: Dict, keyword_counts: Counter) -> List[str]:
        """識別效果最好的搜尋模式"""
        effective_patterns = []
        
        for keyword, avg_score in keyword_quality_correlation.items():
            usage_count = keyword_counts[keyword]
            
            # 效果好且使用頻率適中的關鍵字
            if avg_score >= 7.0 and usage_count >= 2:
                effectiveness_score = avg_score * (1 + min(usage_count / 10, 0.5))
                effective_patterns.append({
                    'pattern': keyword,
                    'avg_quality': avg_score,
                    'usage_count': usage_count,
                    'effectiveness_score': round(effectiveness_score, 2)
                })
        
        # 按效果評分排序
        effective_patterns.sort(key=lambda x: x['effectiveness_score'], reverse=True)
        
        return [f"{p['pattern']} (品質: {p['avg_quality']}, 使用: {p['usage_count']}次)" 
                for p in effective_patterns[:10]]

    def _analyze_keyword_categories(self, keyword_counts: Counter, keyword_quality_correlation: Dict) -> Dict[str, Any]:
        """分析關鍵字分類統計"""
        category_stats = {}
        
        for category, keywords in self.keyword_categories.items():
            matching_keywords = []
            
            for keyword in keyword_counts.keys():
                keyword_lower = keyword.lower()
                if any(cat_keyword in keyword_lower for cat_keyword in keywords):
                    matching_keywords.append(keyword)
            
            if matching_keywords:
                total_usage = sum(keyword_counts[k] for k in matching_keywords)
                avg_quality = statistics.mean([keyword_quality_correlation.get(k, 0) for k in matching_keywords])
                
                category_stats[category] = {
                    'keyword_count': len(matching_keywords),
                    'total_usage': total_usage,
                    'average_quality': round(avg_quality, 2),
                    'keywords': matching_keywords[:5]  # 只保留前5個
                }
        
        return category_stats

    def _categorize_company_status(self, company_code: str, company_files: List[Dict]) -> str:
        """分類公司處理狀態 - 增強版本"""
        if not company_files:
            return 'not_found'
        
        # 檢查驗證狀態
        validation_failed = any(not f.get('content_validation_passed', True) for f in company_files)
        if validation_failed:
            return 'validation_failed'
        
        # 檢查品質評分
        quality_scores = [f.get('quality_score', 0) for f in company_files]
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0
        
        if avg_quality < 3.0:
            return 'low_quality'
        
        # 檢查檔案數量
        if len(company_files) > 1:
            return 'multiple_files'
        
        return 'processed'

    def calculate_keyword_effectiveness_by_company(self, processed_companies: List[Dict]) -> Dict[str, Dict]:
        """計算每家公司的關鍵字效果 - 增強版本"""
        company_keyword_effectiveness = {}
        
        for company_data in processed_companies:
            company_code = company_data.get('company_code', '')
            company_name = company_data.get('company_name', '')
            
            if company_code in self.watchlist_mapping:
                search_keywords = company_data.get('search_keywords', [])
                quality_score = company_data.get('quality_score', 0)
                
                if company_code not in company_keyword_effectiveness:
                    company_keyword_effectiveness[company_code] = {
                        'company_name': company_name,
                        'keywords': [],
                        'quality_scores': [],
                        'avg_effectiveness': 0,
                        'keyword_diversity': 0,
                        'best_keywords': [],
                        'improvement_suggestions': []
                    }
                
                effectiveness_data = company_keyword_effectiveness[company_code]
                effectiveness_data['keywords'].extend(search_keywords)
                effectiveness_data['quality_scores'].append(quality_score)
        
        # 計算效果統計
        for company_code, effectiveness_data in company_keyword_effectiveness.items():
            quality_scores = effectiveness_data['quality_scores']
            keywords = effectiveness_data['keywords']
            
            if quality_scores:
                effectiveness_data['avg_effectiveness'] = round(statistics.mean(quality_scores), 2)
                effectiveness_data['keyword_diversity'] = len(set(keywords))
                
                # 找出最佳關鍵字組合
                if keywords:
                    keyword_counter = Counter(keywords)
                    effectiveness_data['best_keywords'] = [k for k, count in keyword_counter.most_common(3)]
                
                # 生成改進建議
                effectiveness_data['improvement_suggestions'] = self._generate_keyword_improvement_suggestions(
                    company_code, effectiveness_data
                )
        
        return company_keyword_effectiveness

    def _generate_keyword_improvement_suggestions(self, company_code: str, effectiveness_data: Dict) -> List[str]:
        """生成關鍵字改進建議"""
        suggestions = []
        avg_effectiveness = effectiveness_data['avg_effectiveness']
        keyword_diversity = effectiveness_data['keyword_diversity']
        
        if avg_effectiveness < 5.0:
            suggestions.append("建議增加更多高品質關鍵字")
            suggestions.append("考慮使用 'factset' 或 'eps' 等高效關鍵字")
        
        if keyword_diversity < 3:
            suggestions.append("建議增加關鍵字多樣性")
            suggestions.append("可嘗試添加產業相關或分析相關關鍵字")
        
        # 基於公司代號的建議
        try:
            code_num = int(company_code)
            if code_num <= 3000:
                suggestions.append("大型股建議使用: 分析師, 目標價, 預估")
            elif code_num <= 6000:
                suggestions.append("中型股建議使用: 營收, 獲利, 展望")
            else:
                suggestions.append("小型股建議使用: 產業, 趨勢, 成長")
        except ValueError:
            pass
        
        return suggestions[:3]  # 限制建議數量

    def generate_missing_companies_report(self, processed_companies: List[Dict]) -> List[Dict]:
        """生成缺失公司報告 - 增強版本"""
        processed_codes = set()
        for company_data in processed_companies:
            company_code = company_data.get('company_code', '')
            if company_code:
                processed_codes.add(company_code)
        
        missing_companies = []
        for company_code, company_name in self.watchlist_mapping.items():
            if company_code not in processed_codes:
                priority = self._calculate_missing_priority(company_code, company_name)
                suggested_keywords = self._suggest_search_keywords(company_code, company_name)
                
                missing_companies.append({
                    'company_code': company_code,
                    'company_name': company_name,
                    'status': '缺失MD檔案',
                    'priority': priority,
                    'priority_level': self._get_priority_level(priority),
                    'suggested_keywords': suggested_keywords,
                    'search_strategy': self._generate_search_strategy(company_code, company_name),
                    'estimated_difficulty': self._estimate_search_difficulty(company_code, company_name)
                })
        
        # 按優先級排序
        missing_companies.sort(key=lambda x: x['priority'], reverse=True)
        
        return missing_companies

    def _calculate_missing_priority(self, company_code: str, company_name: str) -> int:
        """計算缺失公司的優先級 (1-10) - 增強版本"""
        priority = 5  # 基準分數
        
        # 公司代號越小，通常越重要 (大型股)
        try:
            code_num = int(company_code)
            if code_num <= 1500:
                priority += 4  # 超大型股
            elif code_num <= 2500:
                priority += 3  # 大型股
            elif code_num <= 4000:
                priority += 2  # 中大型股
            elif code_num <= 6000:
                priority += 1  # 中型股
            # 小型股不加分
        except ValueError:
            priority -= 1
        
        # 知名公司名稱關鍵字
        important_keywords = [
            '台積', '鴻海', '聯發', '台達', '中華電', '兆豐', '第一金',
            '國泰', '富邦', '中信', '玉山', '永豐', '元大', '台新'
        ]
        
        if any(keyword in company_name for keyword in important_keywords):
            priority += 2
        
        # 特殊產業關鍵字
        tech_keywords = ['科技', '電子', '半導體', '光電', '通訊']
        finance_keywords = ['金', '銀', '保險', '證券', '投信']
        
        if any(keyword in company_name for keyword in tech_keywords):
            priority += 1
        elif any(keyword in company_name for keyword in finance_keywords):
            priority += 1
        
        return min(10, max(1, priority))

    def _get_priority_level(self, priority: int) -> str:
        """取得優先級等級"""
        if priority >= 9:
            return "極高"
        elif priority >= 7:
            return "高"
        elif priority >= 5:
            return "中"
        elif priority >= 3:
            return "低"
        else:
            return "極低"

    def _suggest_search_keywords(self, company_code: str, company_name: str) -> List[str]:
        """建議搜尋關鍵字 - 增強版本"""
        keywords = []
        
        # 公司名稱 (必須)
        keywords.append(company_name)
        
        # 公司代號
        keywords.append(company_code)
        
        # 基於公司代號的建議
        try:
            code_num = int(company_code)
            if code_num <= 3000:
                keywords.extend(['factset', 'eps', '目標價', '分析師'])
            elif code_num <= 6000:
                keywords.extend(['factset', '營收', '獲利', '預估'])
            else:
                keywords.extend(['factset', '預估', '展望'])
        except ValueError:
            keywords.extend(['factset', 'eps'])
        
        # 基於公司名稱的建議
        if '科技' in company_name or '電子' in company_name:
            keywords.extend(['半導體', '技術'])
        elif '金' in company_name or '銀' in company_name:
            keywords.extend(['金融', '銀行'])
        elif '生技' in company_name or '醫' in company_name:
            keywords.extend(['生技', '醫療'])
        
        # 去重並限制數量
        unique_keywords = list(dict.fromkeys(keywords))[:8]
        
        return unique_keywords

    def _generate_search_strategy(self, company_code: str, company_name: str) -> str:
        """生成搜尋策略建議"""
        strategies = []
        
        try:
            code_num = int(company_code)
            if code_num <= 2000:
                strategies.append("建議優先搜尋大型券商研究報告")
            elif code_num <= 4000:
                strategies.append("建議搜尋 FactSet 和 Bloomberg 資料")
            else:
                strategies.append("建議擴大搜尋範圍，包含產業報告")
        except ValueError:
            strategies.append("建議使用多重關鍵字組合搜尋")
        
        if len(company_name) <= 3:
            strategies.append("公司名稱較短，建議加入代號搜尋")
        
        return "; ".join(strategies)

    def _estimate_search_difficulty(self, company_code: str, company_name: str) -> str:
        """估計搜尋難度"""
        try:
            code_num = int(company_code)
            if code_num <= 2000:
                return "容易"
            elif code_num <= 4000:
                return "中等"
            elif code_num <= 6000:
                return "困難"
            else:
                return "非常困難"
        except ValueError:
            return "未知"

    def _generate_improvement_suggestions(self, missing_companies: List[Dict], 
                                        low_quality_companies: List[Dict]) -> List[str]:
        """生成改進建議"""
        suggestions = []
        
        if missing_companies:
            high_priority_missing = [c for c in missing_companies if c['priority'] >= 7]
            if high_priority_missing:
                suggestions.append(f"優先處理 {len(high_priority_missing)} 家高優先級缺失公司")
        
        if low_quality_companies:
            suggestions.append(f"改善 {len(low_quality_companies)} 家低品質公司的搜尋關鍵字")
        
        if len(missing_companies) > len(self.watchlist_mapping) * 0.3:
            suggestions.append("覆蓋率偏低，建議檢查搜尋系統運作狀況")
        
        suggestions.append("定期更新觀察名單，確保涵蓋重要公司")
        suggestions.append("考慮使用多樣化的關鍵字組合提高搜尋效果")
        
        return suggestions


# 測試功能
if __name__ == "__main__":
    analyzer = WatchlistAnalyzer()
    
    print("=== 觀察名單分析器測試 v3.6.1 (增強版) ===")
    print(f"📋 觀察名單載入: {len(analyzer.watchlist_mapping)} 家公司")
    print(f"🔧 驗證功能: {'啟用' if analyzer.validation_enabled else '停用'}")
    
    if analyzer.validation_enabled:
        # 測試資料
        test_companies = [
            {
                'company_code': '2330',
                'company_name': '台積電',
                'search_keywords': ['台積電', 'factset', 'eps', '預估', '半導體'],
                'quality_score': 9.5,
                'content_validation_passed': True,
                'content_date': '2025/6/24',
                'has_eps_data': True,
                'has_target_price': True,
                'analyst_count': 42,
                'data_source': 'factset'
            },
            {
                'company_code': '6462', 
                'company_name': '神盾',
                'search_keywords': ['神盾', 'factset', '目標價', '指紋辨識'],
                'quality_score': 7.2,
                'content_validation_passed': True,
                'content_date': '2025/6/23',
                'has_eps_data': False,
                'has_target_price': True,
                'analyst_count': 8,
                'data_source': 'factset'
            },
            {
                'company_code': '2317',
                'company_name': '鴻海',
                'search_keywords': ['鴻海', 'factset', '代工', 'eps'],
                'quality_score': 8.1,
                'content_validation_passed': True,
                'content_date': '2025/6/22',
                'has_eps_data': True,
                'has_target_price': False,
                'analyst_count': 35,
                'data_source': 'bloomberg'
            }
        ]
        
        print(f"\n🧪 測試觀察名單覆蓋分析 (增強版):")
        coverage_analysis = analyzer.analyze_watchlist_coverage(test_companies)
        
        if 'error' not in coverage_analysis:
            print(f"✅ 分析成功完成")
            print(f"   觀察名單公司總數: {coverage_analysis['total_watchlist_companies']}")
            print(f"   有MD檔案公司數: {coverage_analysis['companies_with_md_files']}")
            print(f"   覆蓋率: {coverage_analysis['coverage_rate']}%")
            print(f"   成功處理率: {coverage_analysis['success_rate']}%")
            
            # 顯示健康度指標
            health_indicators = coverage_analysis['health_indicators']
            print(f"\n🏥 系統健康度:")
            print(f"   整體健康度: {health_indicators['overall_health']} ({health_indicators['health_grade']})")
            print(f"   覆蓋率健康度: {health_indicators['coverage_health']}")
            print(f"   成功率健康度: {health_indicators['success_health']}")
            print(f"   品質健康度: {health_indicators['quality_health']}")
            
            # 顯示品質統計
            quality_stats = coverage_analysis['quality_statistics']
            print(f"\n📊 增強品質統計:")
            print(f"   平均品質評分: {quality_stats['average_quality_score']}")
            print(f"   品質標準差: {quality_stats['quality_std']}")
            quality_dist = quality_stats['quality_distribution']
            print(f"   品質分布: 優秀 {quality_dist['excellent']}, 良好 {quality_dist['good']}, 普通 {quality_dist['average']}, 差 {quality_dist['poor']}")
            
            # 顯示搜尋模式分析
            search_analysis = coverage_analysis['search_pattern_analysis']
            print(f"\n🔍 增強搜尋模式分析:")
            print(f"   唯一關鍵字數: {search_analysis['total_unique_keywords']}")
            print(f"   平均關鍵字數/公司: {search_analysis['average_keywords_per_company']}")
            
            # 顯示缺失公司分析
            missing_analysis = coverage_analysis['missing_companies_analysis']
            print(f"\n❌ 缺失公司分析:")
            print(f"   缺失公司數: {missing_analysis['missing_count']}")
            print(f"   低品質公司數: {missing_analysis['low_quality_count']}")
            
        else:
            print(f"❌ 分析失敗: {coverage_analysis['error']}")
    
    else:
        print("⚠️ 觀察名單分析已停用")
    
    print(f"\n✅ v3.6.1 增強版觀察名單分析器測試完成！")
    print(f"🆕 增強功能: 健康度指標、詳細品質統計、改進建議、搜尋策略")