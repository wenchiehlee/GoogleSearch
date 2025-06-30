#!/usr/bin/env python3
"""
Report Generator - FactSet Pipeline v3.6.1 (新增觀察名單統計報告)
生成投資組合報告、查詢模式統計報告和觀察名單統計報告
"""

import os
import re
import pandas as pd
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
import pytz

class ReportGenerator:
    """報告生成器 v3.6.1 - 支援標準化查詢模式報告"""
    
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main"):
        self.github_repo_base = github_repo_base
        self.output_dir = "data/reports"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 設定台北時區
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        
        # 投資組合摘要欄位 (14 欄位)
        self.portfolio_summary_columns = [
            '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
            '分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值',
            '品質評分', '狀態', '更新日期'
        ]

        # 詳細報告欄位 (22 欄位 - 包含驗證狀態)
        self.detailed_report_columns = [
            '代號', '名稱', '股票代號', 'MD日期', '分析師數量', '目標價',
            '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
            '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
            '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
            '品質評分', '狀態', '驗證狀態', 'MD File', '更新日期'
        ]

        # 關鍵字報告欄位 (10 欄位) - 保留傳統關鍵字分析用
        self.keyword_summary_columns = [
            '關鍵字', '使用次數', '平均品質評分', '最高品質評分', '最低品質評分',
            '相關公司數量', '品質狀態', '分類', '效果評級', '更新日期'
        ]
        
        # 🆕 查詢模式報告欄位 (10 欄位) - 新增標準化查詢模式
        self.query_pattern_summary_columns = [
            'Query pattern', '使用次數', '平均品質評分', '最高品質評分', '最低品質評分',
            '相關公司數量', '品質狀態', '分類', '效果評級', '更新日期'
        ]
        
        # 🆕 觀察名單報告欄位 (12 欄位) - v3.6.1 新增
        self.watchlist_summary_columns = [
            '公司代號', '公司名稱', 'MD檔案數量', '處理狀態', '平均品質評分', '最高品質評分',
            '搜尋關鍵字數量', '主要關鍵字', '關鍵字平均品質', '最新檔案日期', '驗證狀態', '更新日期'
        ]

    def _get_taipei_time(self) -> str:
        """取得台北時間的字串格式"""
        taipei_time = datetime.now(self.taipei_tz)
        return taipei_time.strftime('%Y-%m-%d %H:%M:%S')

    def _should_include_in_report_v351(self, company_data: Dict[str, Any]) -> bool:
        """判斷是否應該將此資料包含在報告中"""
        
        # 檢查 1: 基本資料完整性
        company_code = company_data.get('company_code')
        company_name = company_data.get('company_name')
        
        if not company_code or company_code == 'Unknown':
            return False
        
        if not company_name or company_name == 'Unknown':
            return False
        
        # 檢查 2: 驗證結果檢查
        validation_result = company_data.get('validation_result', {})
        validation_status = validation_result.get('overall_status', 'unknown')
        
        if validation_status == 'error':
            return False
        
        # 檢查 3: content_validation_passed 字段
        validation_passed = company_data.get('content_validation_passed', True)
        if not validation_passed:
            return False
        
        # 檢查 4: 檢查關鍵驗證錯誤
        validation_errors = company_data.get('validation_errors', [])
        if validation_errors:
            critical_error_keywords = [
                '不在觀察名單中',
                '公司名稱不符觀察名單',
                '觀察名單顯示應為',
                '愛派司.*愛立信',
                '愛立信.*愛派司',
                '公司代號格式無效'
            ]
            
            for error in validation_errors:
                error_str = str(error)
                if any(re.search(keyword, error_str, re.IGNORECASE) for keyword in critical_error_keywords):
                    return False
        
        # 檢查 5: 品質評分為 0 且有 ❌ 驗證失敗狀態
        quality_score = company_data.get('quality_score', 0)
        quality_status = company_data.get('quality_status', '')
        
        if quality_score == 0 and '❌ 驗證失敗' in quality_status:
            return False
        
        return True

    def generate_portfolio_summary(self, processed_companies: List[Dict], filter_invalid=True) -> pd.DataFrame:
        """生成投資組合摘要 (14 欄位)"""
        try:
            # 過濾邏輯
            if filter_invalid:
                original_count = len(processed_companies)
                valid_companies = [c for c in processed_companies if self._should_include_in_report_v351(c)]
                filtered_count = original_count - len(valid_companies)
                
                print(f"📊 投資組合摘要過濾結果:")
                print(f"   原始公司數: {original_count}")
                print(f"   保留公司數: {len(valid_companies)}")
                print(f"   過濾公司數: {filtered_count}")
            else:
                valid_companies = processed_companies
                print(f"📊 投資組合摘要：未啟用過濾，包含所有 {len(valid_companies)} 家公司")
            
            # 按公司分組，取得每家公司的最佳品質資料
            company_summary = {}
            
            for company_data in valid_companies:
                company_code = company_data.get('company_code', 'Unknown')
                
                if company_code not in company_summary:
                    company_summary[company_code] = {
                        'files': [],
                        'best_quality_data': None
                    }
                
                company_summary[company_code]['files'].append(company_data)
                
                # 選擇最佳品質資料
                current_best = company_summary[company_code]['best_quality_data']
                
                if current_best is None:
                    company_summary[company_code]['best_quality_data'] = company_data
                else:
                    current_quality = company_data.get('quality_score', 0)
                    best_quality = current_best.get('quality_score', 0)
                    
                    if current_quality > best_quality:
                        company_summary[company_code]['best_quality_data'] = company_data
            
            # 生成摘要資料
            summary_rows = []
            
            for company_code, company_info in company_summary.items():
                best_data = company_info['best_quality_data']
                all_files = company_info['files']
                
                # 計算日期範圍
                oldest_date, newest_date = self._calculate_date_range_content_date_only(all_files)
                
                # 使用最佳品質資料生成摘要
                clean_code = self._clean_stock_code_for_display(company_code)
                
                summary_row = {
                    '代號': clean_code,
                    '名稱': best_data.get('company_name', 'Unknown'),
                    '股票代號': f"{clean_code}-TW",
                    'MD最舊日期': oldest_date,
                    'MD最新日期': newest_date,
                    'MD資料筆數': len(all_files),
                    '分析師數量': best_data.get('analyst_count', 0),
                    '目標價': best_data.get('target_price', ''),
                    '2025EPS平均值': self._format_eps_value(best_data.get('eps_2025_avg')),
                    '2026EPS平均值': self._format_eps_value(best_data.get('eps_2026_avg')),
                    '2027EPS平均值': self._format_eps_value(best_data.get('eps_2027_avg')),
                    '品質評分': best_data.get('quality_score', 0),
                    '狀態': best_data.get('quality_status', '🔴 不足'),
                    '更新日期': self._get_taipei_time()
                }
                
                summary_rows.append(summary_row)
            
            # 建立 DataFrame
            df = pd.DataFrame(summary_rows, columns=self.portfolio_summary_columns)
            df = df.sort_values('代號')
            
            print("✅ 投資組合摘要已使用最佳品質資料生成")
            
            return df
            
        except Exception as e:
            print(f"❌ 生成投資組合摘要失敗: {e}")
            return pd.DataFrame(columns=self.portfolio_summary_columns)

    def generate_detailed_report(self, processed_companies: List[Dict], filter_invalid=True) -> pd.DataFrame:
        """生成詳細報告 (22 欄位)"""
        try:
            detailed_rows = []
            filtered_count = 0
            
            for company_data in processed_companies:
                # 檢查是否應該過濾此資料
                if filter_invalid and not self._should_include_in_report_v351(company_data):
                    filtered_count += 1
                    continue
                
                # 生成驗證狀態標記
                validation_status = self._generate_validation_status_marker_v351(company_data)
                
                # 處理 MD 檔案連結
                md_file_url = self._format_md_file_url_with_warning(company_data)
                
                detailed_row = {
                    '代號': company_data.get('company_code', 'Unknown'),
                    '名稱': company_data.get('company_name', 'Unknown'),
                    '股票代號': f"{company_data.get('company_code', 'Unknown')}-TW",
                    'MD日期': self._get_content_date_only(company_data),
                    '分析師數量': company_data.get('analyst_count', 0),
                    '目標價': company_data.get('target_price', ''),
                    '2025EPS最高值': self._format_eps_value(company_data.get('eps_2025_high')),
                    '2025EPS最低值': self._format_eps_value(company_data.get('eps_2025_low')),
                    '2025EPS平均值': self._format_eps_value(company_data.get('eps_2025_avg')),
                    '2026EPS最高值': self._format_eps_value(company_data.get('eps_2026_high')),
                    '2026EPS最低值': self._format_eps_value(company_data.get('eps_2026_low')),
                    '2026EPS平均值': self._format_eps_value(company_data.get('eps_2026_avg')),
                    '2027EPS最高值': self._format_eps_value(company_data.get('eps_2027_high')),
                    '2027EPS最低值': self._format_eps_value(company_data.get('eps_2027_low')),
                    '2027EPS平均值': self._format_eps_value(company_data.get('eps_2027_avg')),
                    '品質評分': company_data.get('quality_score', 0),
                    '狀態': company_data.get('quality_status', '🔴 不足'),
                    '驗證狀態': validation_status,
                    'MD File': md_file_url,
                    '更新日期': self._get_taipei_time()
                }
                
                detailed_rows.append(detailed_row)
            
            # 建立 DataFrame
            df = pd.DataFrame(detailed_rows, columns=self.detailed_report_columns)
            df = df.sort_values(['代號', 'MD日期'], ascending=[True, False])
            
            if filter_invalid and filtered_count > 0:
                print(f"📊 詳細報告過濾了 {filtered_count} 筆驗證失敗的資料")
            
            print(f"📊 詳細報告包含 {len(detailed_rows)} 筆有效資料")
            
            return df
            
        except Exception as e:
            print(f"❌ 生成詳細報告失敗: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(columns=self.detailed_report_columns)

    def generate_keyword_summary(self, keyword_analysis: Dict[str, Any]) -> pd.DataFrame:
        """🔧 生成關鍵字/查詢模式統計報告（支援標準化查詢模式）"""
        try:
            # 檢查是否為查詢模式分析
            analysis_type = keyword_analysis.get('analysis_type', 'keywords')
            
            if analysis_type in ['search_query_patterns_normalized', 'search_query_patterns']:
                return self._generate_query_pattern_summary(keyword_analysis)
            else:
                return self._generate_traditional_keyword_summary(keyword_analysis)
                
        except Exception as e:
            print(f"❌ 生成關鍵字/查詢模式報告失敗: {e}")
            return pd.DataFrame(columns=self.keyword_summary_columns)

    def _generate_query_pattern_summary(self, pattern_analysis: Dict[str, Any]) -> pd.DataFrame:
        """🆕 生成標準化查詢模式統計報告"""
        pattern_data = []
        pattern_stats = pattern_analysis.get('pattern_stats', {})
        
        for pattern, stats in pattern_stats.items():
            # 計算效果評級
            avg_score = stats['avg_quality_score']
            if avg_score >= 9:
                effect_rating = "優秀 ⭐⭐⭐"
            elif avg_score >= 7:
                effect_rating = "良好 ⭐⭐"
            elif avg_score >= 5:
                effect_rating = "普通 ⭐"
            else:
                effect_rating = "需改善"
            
            # 品質狀態
            quality_status = self._get_quality_status_by_score(avg_score)
            
            # 模式類型轉換為中文
            pattern_type = stats.get('pattern_type', 'other')
            category_mapping = {
                'factset_direct': 'FactSet直接',
                'cnyes_factset': '鉅亨網FactSet',
                'eps_forecast': 'EPS預估',
                'analyst_consensus': '分析師共識',
                'taiwan_financial_simple': '台灣財經',
                'other': '其他'
            }
            category_display = category_mapping.get(pattern_type, 'other')
            
            pattern_data.append({
                'Query pattern': pattern,  # 🔧 關鍵欄位名稱
                '使用次數': stats['usage_count'],
                '平均品質評分': round(avg_score, 2),
                '最高品質評分': stats['max_quality_score'],
                '最低品質評分': stats['min_quality_score'],
                '相關公司數量': stats['company_count'],
                '品質狀態': quality_status,
                '分類': category_display,
                '效果評級': effect_rating,
                '更新日期': self._get_taipei_time()
            })
        
        # 按平均品質評分排序
        pattern_data.sort(key=lambda x: x['平均品質評分'], reverse=True)
        
        return pd.DataFrame(pattern_data, columns=self.query_pattern_summary_columns)

    def _generate_traditional_keyword_summary(self, keyword_analysis: Dict[str, Any]) -> pd.DataFrame:
        """生成傳統關鍵字統計報告（保持原有功能）"""
        keyword_data = []
        keyword_stats = keyword_analysis.get('keyword_stats', {})
        
        for keyword, stats in keyword_stats.items():
            # 計算效果評級
            avg_score = stats['avg_quality_score']
            if avg_score >= 9:
                effect_rating = "優秀 ⭐⭐⭐"
            elif avg_score >= 7:
                effect_rating = "良好 ⭐⭐"
            elif avg_score >= 5:
                effect_rating = "普通 ⭐"
            else:
                effect_rating = "需改善"
            
            # 品質狀態
            quality_status = self._get_quality_status_by_score(avg_score)
            
            keyword_data.append({
                '關鍵字': keyword,
                '使用次數': stats['usage_count'],
                '平均品質評分': round(avg_score, 2),
                '最高品質評分': stats['max_quality_score'],
                '最低品質評分': stats['min_quality_score'],
                '相關公司數量': stats['company_count'],
                '品質狀態': quality_status,
                '分類': stats['category'],
                '效果評級': effect_rating,
                '更新日期': self._get_taipei_time()
            })
        
        # 按平均品質評分排序
        keyword_data.sort(key=lambda x: x['平均品質評分'], reverse=True)
        
        return pd.DataFrame(keyword_data, columns=self.keyword_summary_columns)

    def generate_watchlist_summary(self, watchlist_analysis: Dict[str, Any]) -> pd.DataFrame:
        """🆕 v3.6.1 生成觀察名單統計報告"""
        try:
            watchlist_data = []
            company_processing_status = watchlist_analysis.get('company_processing_status', {})
            search_pattern_analysis = watchlist_analysis.get('search_pattern_analysis', {})
            keyword_quality_correlation = search_pattern_analysis.get('keyword_quality_correlation', {})
            
            # 處理狀態中文化映射
            status_mapping = {
                'processed': '✅ 已處理',
                'not_found': '❌ 未找到',
                'validation_failed': '🚫 驗證失敗',
                'low_quality': '🔴 品質過低',
                'multiple_files': '📄 多個檔案'
            }
            
            for company_code, status_info in company_processing_status.items():
                # 計算主要關鍵字
                company_keywords = status_info.get('search_keywords', [])
                main_keywords = ', '.join(company_keywords[:3]) if company_keywords else ''
                
                # 計算關鍵字平均品質
                keyword_avg_quality = 0
                if company_keywords:
                    keyword_qualities = [keyword_quality_correlation.get(kw, 0) for kw in company_keywords]
                    keyword_avg_quality = sum(keyword_qualities) / len(keyword_qualities) if keyword_qualities else 0
                
                # 處理狀態顯示
                status_display = status_mapping.get(status_info['status'], status_info['status'])
                
                # 格式化最新檔案日期
                latest_file_date = status_info.get('latest_file_date', '')
                if latest_file_date:
                    # 統一日期格式
                    if '/' in latest_file_date:
                        try:
                            parts = latest_file_date.split('/')
                            if len(parts) == 3:
                                year, month, day = parts
                                latest_file_date = f"{year}-{int(month):02d}-{int(day):02d}"
                        except:
                            pass
                
                watchlist_data.append({
                    '公司代號': company_code,
                    '公司名稱': status_info.get('company_name', ''),
                    'MD檔案數量': status_info.get('file_count', 0),
                    '處理狀態': status_display,
                    '平均品質評分': round(status_info.get('average_quality_score', 0), 2),
                    '最高品質評分': status_info.get('max_quality_score', 0),
                    '搜尋關鍵字數量': len(company_keywords),
                    '主要關鍵字': main_keywords,
                    '關鍵字平均品質': round(keyword_avg_quality, 2),
                    '最新檔案日期': latest_file_date,
                    '驗證狀態': self._get_validation_status_display(status_info),
                    '更新日期': self._get_taipei_time()
                })
            
            # 按處理狀態和品質評分排序
            watchlist_data.sort(key=lambda x: (
                x['處理狀態'] == '✅ 已處理',  # 已處理的排在前面
                x['平均品質評分']             # 然後按品質評分排序
            ), reverse=True)
            
            df = pd.DataFrame(watchlist_data, columns=self.watchlist_summary_columns)
            
            print(f"📊 觀察名單統計報告已生成: {len(watchlist_data)} 家公司")
            
            return df
            
        except Exception as e:
            print(f"❌ 生成觀察名單統計報告失敗: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(columns=self.watchlist_summary_columns)

    def save_keyword_summary(self, keyword_df: pd.DataFrame) -> str:
        """🔧 儲存關鍵字/查詢模式統計報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 根據第一欄的名稱決定檔案名稱
        if len(keyword_df.columns) > 0 and keyword_df.columns[0] == 'Query pattern':
            keyword_path = os.path.join(self.output_dir, f'query_pattern_summary_{timestamp}.csv')
            latest_keyword_path = os.path.join(self.output_dir, 'query_pattern_summary_latest.csv')
            report_type = "查詢模式"
        else:
            keyword_path = os.path.join(self.output_dir, f'keyword_summary_{timestamp}.csv')
            latest_keyword_path = os.path.join(self.output_dir, 'keyword_summary_latest.csv')
            report_type = "關鍵字"
        
        try:
            keyword_df_clean = keyword_df.replace('', pd.NA)
            keyword_df_clean.to_csv(keyword_path, index=False, encoding='utf-8-sig')
            keyword_df_clean.to_csv(latest_keyword_path, index=False, encoding='utf-8-sig')
            
            print(f"📁 {report_type}統計報告已儲存: {keyword_path}")
            return keyword_path
            
        except Exception as e:
            print(f"❌ 儲存{report_type}報告失敗: {e}")
            return ""

    def save_all_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                        keyword_df: pd.DataFrame = None, watchlist_df: pd.DataFrame = None) -> Dict[str, str]:
        """🔧 v3.6.1 儲存所有報告為 CSV - 包含查詢模式和觀察名單報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 檔案路徑
        portfolio_path = os.path.join(self.output_dir, f'portfolio_summary_v361_{timestamp}.csv')
        detailed_path = os.path.join(self.output_dir, f'detailed_report_v361_{timestamp}.csv')
        latest_portfolio_path = os.path.join(self.output_dir, 'portfolio_summary_latest.csv')
        latest_detailed_path = os.path.join(self.output_dir, 'detailed_report_latest.csv')
        
        try:
            # 確保空字符串在 CSV 中正確處理
            portfolio_df_clean = portfolio_df.copy().replace('', pd.NA)
            detailed_df_clean = detailed_df.copy().replace('', pd.NA)
            
            # 儲存主要報告
            portfolio_df_clean.to_csv(portfolio_path, index=False, encoding='utf-8-sig')
            detailed_df_clean.to_csv(detailed_path, index=False, encoding='utf-8-sig')
            portfolio_df_clean.to_csv(latest_portfolio_path, index=False, encoding='utf-8-sig')
            detailed_df_clean.to_csv(latest_detailed_path, index=False, encoding='utf-8-sig')
            
            saved_files = {
                'portfolio_summary': portfolio_path,
                'detailed_report': detailed_path,
                'portfolio_summary_latest': latest_portfolio_path,
                'detailed_report_latest': latest_detailed_path
            }
            
            # 🆕 儲存關鍵字/查詢模式報告
            if keyword_df is not None and not keyword_df.empty:
                # 檢查是否為查詢模式報告
                if len(keyword_df.columns) > 0 and keyword_df.columns[0] == 'Query pattern':
                    pattern_path = os.path.join(self.output_dir, f'query_pattern_summary_v361_{timestamp}.csv')
                    latest_pattern_path = os.path.join(self.output_dir, 'query_pattern_summary_latest.csv')
                    report_key = 'query_pattern_summary'
                    latest_key = 'query_pattern_summary_latest'
                else:
                    pattern_path = os.path.join(self.output_dir, f'keyword_summary_v361_{timestamp}.csv')
                    latest_pattern_path = os.path.join(self.output_dir, 'keyword_summary_latest.csv')
                    report_key = 'keyword_summary'
                    latest_key = 'keyword_summary_latest'
                
                keyword_df_clean = keyword_df.replace('', pd.NA)
                keyword_df_clean.to_csv(pattern_path, index=False, encoding='utf-8-sig')
                keyword_df_clean.to_csv(latest_pattern_path, index=False, encoding='utf-8-sig')
                
                saved_files[report_key] = pattern_path
                saved_files[latest_key] = latest_pattern_path
            
            # 🆕 儲存觀察名單報告
            if watchlist_df is not None and not watchlist_df.empty:
                watchlist_path = os.path.join(self.output_dir, f'watchlist_summary_v361_{timestamp}.csv')
                latest_watchlist_path = os.path.join(self.output_dir, 'watchlist_summary_latest.csv')
                
                watchlist_df_clean = watchlist_df.replace('', pd.NA)
                watchlist_df_clean.to_csv(watchlist_path, index=False, encoding='utf-8-sig')
                watchlist_df_clean.to_csv(latest_watchlist_path, index=False, encoding='utf-8-sig')
                
                saved_files['watchlist_summary'] = watchlist_path
                saved_files['watchlist_summary_latest'] = latest_watchlist_path
            
            print(f"📁 v3.6.1 報告已儲存:")
            print(f"   投資組合摘要: {portfolio_path}")
            print(f"   詳細報告: {detailed_path}")
            if keyword_df is not None:
                report_type = "查詢模式" if 'query_pattern_summary' in saved_files else "關鍵字"
                print(f"   {report_type}報告: {saved_files.get('query_pattern_summary', saved_files.get('keyword_summary', 'N/A'))}")
            if watchlist_df is not None:
                print(f"   觀察名單報告: {saved_files.get('watchlist_summary', 'N/A')}")
            
            return saved_files
            
        except Exception as e:
            print(f"❌ 儲存報告失敗: {e}")
            return {}

    def save_watchlist_summary(self, watchlist_df: pd.DataFrame) -> str:
        """🆕 v3.6.1 單獨儲存觀察名單統計報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        watchlist_path = os.path.join(self.output_dir, f'watchlist_summary_{timestamp}.csv')
        latest_watchlist_path = os.path.join(self.output_dir, 'watchlist_summary_latest.csv')
        
        try:
            watchlist_df_clean = watchlist_df.replace('', pd.NA)
            watchlist_df_clean.to_csv(watchlist_path, index=False, encoding='utf-8-sig')
            watchlist_df_clean.to_csv(latest_watchlist_path, index=False, encoding='utf-8-sig')
            
            print(f"📁 觀察名單統計報告已儲存: {watchlist_path}")
            return watchlist_path
            
        except Exception as e:
            print(f"❌ 儲存觀察名單報告失敗: {e}")
            return ""

    def generate_statistics_report(self, processed_companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """🔧 v3.6.1 生成統計報告 - 包含觀察名單統計"""
        total_companies = len(processed_companies)
        
        if total_companies == 0:
            return {
                'total_companies': 0,
                'companies_with_data': 0,
                'success_rate': 0
            }
        
        # 基本統計
        companies_with_data = len([c for c in processed_companies if c.get('quality_score', 0) > 0])
        success_rate = (companies_with_data / total_companies) * 100
        
        # 品質分析
        quality_scores = [c.get('quality_score', 0) for c in processed_companies]
        
        # content_date 提取分析
        companies_with_content_date = len([c for c in processed_companies if self._get_content_date_only(c)])
        content_date_success_rate = (companies_with_content_date / total_companies) * 100
        
        # 驗證統計
        validation_passed = 0
        validation_failed = 0
        validation_disabled = 0
        
        for company in processed_companies:
            validation_result = company.get('validation_result', {})
            validation_method = validation_result.get('validation_method', 'unknown')
            
            if validation_method == 'disabled':
                validation_disabled += 1
            elif self._should_include_in_report_v351(company):
                validation_passed += 1
            else:
                validation_failed += 1
        
        validation_success_rate = (validation_passed / total_companies) * 100
        
        # 過濾統計
        companies_included_in_report = len([c for c in processed_companies if self._should_include_in_report_v351(c)])
        inclusion_rate = (companies_included_in_report / total_companies) * 100
        
        # 🆕 觀察名單關聯統計
        watchlist_companies = len([c for c in processed_companies 
                                 if c.get('company_code', '') and 
                                 self._is_watchlist_company(c.get('company_code', ''))])
        
        statistics = {
            'version': '3.6.1',
            'report_type': 'comprehensive_with_watchlist',
            'timestamp': datetime.now().isoformat(),
            
            # 基本統計
            'total_companies': total_companies,
            'companies_with_data': companies_with_data,
            'success_rate': round(success_rate, 1),
            'companies_with_content_date': companies_with_content_date,
            'content_date_success_rate': round(content_date_success_rate, 1),
            
            # 驗證統計
            'validation_statistics': {
                'validation_passed': validation_passed,
                'validation_failed': validation_failed,
                'validation_disabled': validation_disabled,
                'validation_success_rate': round(validation_success_rate, 1),
                'companies_included_in_report': companies_included_in_report,
                'inclusion_rate': round(inclusion_rate, 1),
                'filtered_out': total_companies - companies_included_in_report
            },
            
            # 品質分析
            'quality_analysis': {
                'average_quality_score': round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0,
                'highest_quality_score': max(quality_scores) if quality_scores else 0,
                'lowest_quality_score': min(quality_scores) if quality_scores else 0
            },
            
            # 🆕 觀察名單相關統計
            'watchlist_statistics': {
                'watchlist_companies_in_data': watchlist_companies,
                'watchlist_coverage_in_data': round((watchlist_companies / total_companies) * 100, 1) if total_companies > 0 else 0
            }
        }
        
        return statistics

    def save_statistics_report(self, statistics: Dict[str, Any]) -> str:
        """儲存統計報告為 JSON 檔案"""
        import json
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_path = os.path.join(self.output_dir, f'statistics_v361_{timestamp}.json')
        latest_stats_path = os.path.join(self.output_dir, 'statistics_latest.json')
        
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2, default=str)
            
            with open(latest_stats_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📊 v3.6.1 統計報告已儲存: {stats_path}")
            
            # 顯示重要統計
            validation_stats = statistics.get('validation_statistics', {})
            watchlist_stats = statistics.get('watchlist_statistics', {})
            
            print(f"📊 驗證成功率: {validation_stats.get('validation_success_rate', 0)}%")
            print(f"📊 報告包含率: {validation_stats.get('inclusion_rate', 0)}%")
            print(f"📊 觀察名單覆蓋: {watchlist_stats.get('watchlist_coverage_in_data', 0)}%")
            
            return stats_path
            
        except Exception as e:
            print(f"❌ 儲存統計報告失敗: {e}")
            return ""

    # 輔助方法
    def _is_watchlist_company(self, company_code: str) -> bool:
        """🆕 v3.6.1 檢查是否為觀察名單公司（簡化檢查）"""
        # 這裡可以加載觀察名單進行檢查，或者根據代號範圍進行簡單判斷
        if company_code and company_code.isdigit() and len(company_code) == 4:
            return True
        return False

    def _get_validation_status_display(self, status_info: Dict) -> str:
        """🆕 v3.6.1 取得驗證狀態顯示"""
        validation_passed = status_info.get('validation_passed', True)
        validation_errors = status_info.get('validation_errors', [])
        
        if not validation_passed:
            if validation_errors:
                main_error = str(validation_errors[0])
                if "不在觀察名單" in main_error:
                    return "🚫 不在觀察名單"
                elif "名稱不符" in main_error:
                    return "📝 名稱不符"
                else:
                    return "❌ 驗證失敗"
            else:
                return "❌ 驗證失敗"
        else:
            return "✅ 驗證通過"

    def _clean_stock_code_for_display(self, code):
        """清理股票代號，確保顯示為純數字（無引號）"""
        if pd.isna(code) or code is None or code == '':
            return ''
        
        code_str = str(code).strip()
        
        if code_str.startswith("'"):
            code_str = code_str[1:]
        
        if code_str.isdigit():
            return code_str
        
        return code_str

    def _format_md_file_url_with_warning(self, company_data: Dict[str, Any]) -> str:
        """格式化 MD 檔案連結"""
        filename = company_data.get('filename', '')
        
        if not filename:
            return ""
        
        if not filename.endswith('.md'):
            filename += '.md'
        
        encoded_filename = urllib.parse.quote(filename, safe='')
        raw_url = f"{self.github_repo_base}/data/md/{encoded_filename}"
        
        return raw_url

    def _get_content_date_only(self, company_data: Dict[str, Any]) -> str:
        """絕對只使用 content_date，無任何 fallback"""
        content_date = company_data.get('content_date')
        
        if content_date and str(content_date).strip() and str(content_date).strip().lower() != 'none':
            try:
                if isinstance(content_date, str) and '/' in content_date:
                    parts = content_date.split('/')
                    if len(parts) == 3:
                        year, month, day = parts
                        if (year.isdigit() and month.isdigit() and day.isdigit() and
                            1900 <= int(year) <= 2100 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31):
                            return f"{year}-{int(month):02d}-{int(day):02d}"
                
                elif isinstance(content_date, datetime):
                    return content_date.strftime('%Y-%m-%d')
                    
            except Exception as e:
                pass
        
        return ""

    def _calculate_date_range_content_date_only(self, all_files: List[Dict]) -> tuple:
        """計算日期範圍 - 只考慮有 content_date 的檔案"""
        valid_dates = []
        
        for file_data in all_files:
            content_date = self._get_content_date_only(file_data)
            if content_date:
                valid_dates.append(content_date)
        
        if valid_dates:
            valid_dates.sort()
            return valid_dates[0], valid_dates[-1]
        
        return "", ""

    def _format_eps_value(self, eps_value) -> str:
        """格式化 EPS 數值"""
        if eps_value is None or eps_value == '':
            return ''
        try:
            eps = float(eps_value)
            return f"{eps:.2f}"
        except (ValueError, TypeError):
            return str(eps_value)

    def _generate_validation_status_marker_v351(self, company_data: Dict[str, Any]) -> str:
        """生成驗證狀態標記"""
        validation_result = company_data.get('validation_result', {})
        validation_status = validation_result.get('overall_status', 'unknown')
        validation_method = validation_result.get('validation_method', 'unknown')
        validation_passed = company_data.get('content_validation_passed', True)
        validation_errors = company_data.get('validation_errors', [])
        validation_warnings = company_data.get('validation_warnings', [])
        validation_enabled = company_data.get('validation_enabled', False)
        
        # 多層驗證狀態判斷
        if validation_status == 'error' or not validation_passed:
            if validation_errors:
                main_error = str(validation_errors[0])
                if "不在觀察名單" in main_error:
                    return "🚫 不在觀察名單"
                elif "公司名稱不符觀察名單" in main_error:
                    return "📝 名稱不符"
                elif "愛派司" in main_error or "愛立信" in main_error:
                    return "🔄 名稱混亂"
                else:
                    return "❌ 驗證失敗"
            else:
                return "❌ 驗證失敗"
        
        elif validation_method == 'disabled' or not validation_enabled:
            return "⚠️ 驗證停用"
        
        elif validation_warnings:
            return "⚠️ 有警告"
        
        else:
            return "✅ 通過"

    def _get_quality_status_by_score(self, score: float) -> str:
        """取得品質狀態指標"""
        if score >= 9:
            return "🟢 優秀"
        elif score >= 7:
            return "🟡 良好"
        elif score >= 5:
            return "🟠 普通"
        else:
            return "🔴 需改善"


# 測試功能
if __name__ == "__main__":
    generator = ReportGenerator()
    
    print("=== 🆕 v3.6.1 標準化查詢模式報告生成器測試 ===")
    
    # 測試標準化查詢模式分析數據
    test_pattern_analysis = {
        'analysis_type': 'search_query_patterns_normalized',
        'pattern_stats': {
            '{name} {symbol} factset 分析師': {
                'usage_count': 30,
                'avg_quality_score': 7.89,
                'max_quality_score': 8.7,
                'min_quality_score': 4.3,
                'company_count': 15,
                'pattern_type': 'factset_direct'
            },
            '{name} {symbol} factset eps': {
                'usage_count': 25,
                'avg_quality_score': 8.5,
                'max_quality_score': 9.2,
                'min_quality_score': 7.1,
                'company_count': 12,
                'pattern_type': 'factset_direct'
            },
            'site:cnyes.com {symbol} factset': {
                'usage_count': 18,
                'avg_quality_score': 7.2,
                'max_quality_score': 8.1,
                'min_quality_score': 6.3,
                'company_count': 10,
                'pattern_type': 'cnyes_factset'
            }
        }
    }
    
    print("測試 1: 生成標準化查詢模式報告")
    pattern_summary = generator.generate_keyword_summary(test_pattern_analysis)
    
    print(f"   生成的查詢模式報告包含 {len(pattern_summary)} 個模式")
    print("   前幾行數據:")
    for i, row in pattern_summary.head().iterrows():
        pattern = row['Query pattern']
        usage = row['使用次數']
        quality = row['平均品質評分']
        category = row['分類']
        print(f"     {pattern}: 使用 {usage} 次, 平均品質 {quality}, 分類: {category}")
    
    print("\n測試 2: 儲存查詢模式 CSV")
    csv_file = generator.save_keyword_summary(pattern_summary)
    if csv_file:
        print(f"   ✅ 查詢模式 CSV 已儲存: {csv_file}")
    
    print(f"\n🎉 v3.6.1 標準化查詢模式報告生成器測試完成!")
    print(f"✅ 生成標準化查詢模式統計報告 (Query pattern 欄位)")
    print(f"✅ 支援 {{name}} {{symbol}} 格式的模式聚合")
    print(f"✅ 按模式類型分類和品質評分排序")
    print(f"✅ 完整的 CSV 儲存功能")