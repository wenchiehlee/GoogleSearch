#!/usr/bin/env python3
"""
Report Generator - FactSet Pipeline v3.5.0 (Enhanced with Validation Filtering)
過濾驗證失敗的資料，標記需要人工確認的項目
"""

import os
import re
import pandas as pd
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional

class ReportGenerator:
    """報告生成器 - 驗證過濾增強版"""
    
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main"):
        self.github_repo_base = github_repo_base
        self.output_dir = "data/reports"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 投資組合摘要欄位 (14 欄位)
        self.portfolio_summary_columns = [
            '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
            '分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值',
            '品質評分', '狀態', '更新日期'
        ]
        
        # 🆕 擴展詳細報告欄位 (22 欄位 - 新增驗證狀態)
        self.detailed_report_columns = [
            '代號', '名稱', '股票代號', 'MD日期', '分析師數量', '目標價',
            '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
            '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
            '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
            '品質評分', '狀態', '驗證狀態', 'MD File', '更新日期'  # 🆕 新增驗證狀態欄位
        ]

    def generate_detailed_report(self, processed_companies: List[Dict], filter_invalid=True) -> pd.DataFrame:
        """生成詳細報告 - 🆕 默認過濾無效資料"""
        try:
            detailed_rows = []
            filtered_count = 0
            
            for company_data in processed_companies:
                # 🆕 檢查是否應該過濾此資料
                if filter_invalid and not self._should_include_in_report(company_data):
                    filtered_count += 1
                    continue
                
                # 原有的報告生成邏輯
                md_date = self._get_content_date_only(company_data)
                
                # 🆕 生成驗證狀態標記
                validation_status = self._generate_validation_status_marker(company_data)
                
                # 🆕 處理有問題的 MD 檔案連結
                md_file_url = self._format_md_file_url_with_warning(company_data)
                
                detailed_row = {
                    '代號': company_data.get('company_code', 'Unknown'),
                    '名稱': company_data.get('company_name', 'Unknown'),
                    '股票代號': f"{company_data.get('company_code', 'Unknown')}-TW",
                    'MD日期': md_date,
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
                    '驗證狀態': validation_status,  # 🆕 新增驗證狀態欄位
                    'MD File': md_file_url,
                    '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                detailed_rows.append(detailed_row)
            
            # 建立 DataFrame
            df = pd.DataFrame(detailed_rows, columns=self.detailed_report_columns)
            df = df.sort_values(['代號', 'MD日期'], ascending=[True, False])
            
            # 🆕 記錄過濾統計
            if filter_invalid and filtered_count > 0:
                print(f"📊 過濾了 {filtered_count} 筆驗證失敗的資料")
            
            return df
            
        except Exception as e:
            print(f"❌ 生成詳細報告失敗: {e}")
            return pd.DataFrame(columns=self.detailed_report_columns)

    def generate_portfolio_summary(self, processed_companies: List[Dict], filter_invalid=True) -> pd.DataFrame:
        """生成投資組合摘要 - 🆕 可選擇過濾無效資料"""
        try:
            # 🆕 先過濾無效資料
            if filter_invalid:
                valid_companies = [c for c in processed_companies if self._should_include_in_report(c)]
                print(f"📊 投資組合摘要：保留 {len(valid_companies)}/{len(processed_companies)} 筆有效資料")
            else:
                valid_companies = processed_companies
            
            # 按公司分組，取得每家公司的最新資料
            company_summary = {}
            
            for company_data in valid_companies:
                company_code = company_data.get('company_code', 'Unknown')
                
                if company_code not in company_summary:
                    company_summary[company_code] = {
                        'files': [],
                        'latest_data': None
                    }
                
                company_summary[company_code]['files'].append(company_data)
                
                # 更新最新資料
                if (company_summary[company_code]['latest_data'] is None or
                    self._is_more_recent_content_date_only(company_data, company_summary[company_code]['latest_data'])):
                    company_summary[company_code]['latest_data'] = company_data
            
            # 生成摘要資料
            summary_rows = []
            
            for company_code, company_info in company_summary.items():
                latest_data = company_info['latest_data']
                all_files = company_info['files']
                
                best_content_date = self._get_content_date_only(latest_data)
                
                # 計算日期範圍（只考慮有 content_date 的檔案）
                oldest_date, newest_date = self._calculate_date_range_content_date_only(all_files)
                
                summary_row = {
                    '代號': company_code,
                    '名稱': latest_data.get('company_name', 'Unknown'),
                    '股票代號': f"{company_code}-TW",
                    'MD最舊日期': oldest_date or best_content_date,
                    'MD最新日期': newest_date or best_content_date,
                    'MD資料筆數': len(all_files),
                    '分析師數量': latest_data.get('analyst_count', 0),
                    '目標價': latest_data.get('target_price', ''),
                    '2025EPS平均值': self._format_eps_value(latest_data.get('eps_2025_avg')),
                    '2026EPS平均值': self._format_eps_value(latest_data.get('eps_2026_avg')),
                    '2027EPS平均值': self._format_eps_value(latest_data.get('eps_2027_avg')),
                    '品質評分': latest_data.get('quality_score', 0),
                    '狀態': latest_data.get('quality_status', '🔴 不足'),
                    '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                summary_rows.append(summary_row)
            
            # 建立 DataFrame
            df = pd.DataFrame(summary_rows, columns=self.portfolio_summary_columns)
            df = df.sort_values('代號')
            
            return df
            
        except Exception as e:
            print(f"❌ 生成投資組合摘要失敗: {e}")
            return pd.DataFrame(columns=self.portfolio_summary_columns)

    def _should_include_in_report(self, company_data: Dict[str, Any]) -> bool:
        """🆕 判斷是否應該將此資料包含在報告中 - 只排除真正嚴重的問題"""
        
        # 🚨 只有真正嚴重的驗證錯誤才排除
        validation_errors = company_data.get('validation_errors', [])
        
        # 🆕 嚴重錯誤類型：
        # 1. 愛派司/愛立信問題
        # 2. 觀察名單不符問題
        # 移除了對 "Oops, something went wrong" 的檢查 - 這很常見，不需要特別處理
        critical_error_keywords = [
            r'愛派司.*愛立信', 
            r'愛立信.*愛派司', 
            r'company_mismatch',
            r'公司名稱不符觀察名單',  
            r'觀察名單顯示應為'
        ]
        
        has_critical_error = any(
            any(re.search(keyword, str(error), re.IGNORECASE) for keyword in critical_error_keywords)
            for error in validation_errors
        )
        
        if has_critical_error:
            print(f"🚨 排除嚴重驗證錯誤: {company_data.get('company_name', 'Unknown')} - {validation_errors[0][:50]}...")
            return False
        
        # 檢查基本資料完整性 - 更寬鬆的條件
        company_code = company_data.get('company_code')
        company_name = company_data.get('company_name')
        
        if not company_code or company_code == 'Unknown':
            print(f"📝 排除缺少公司代號的資料: {company_name}")
            return False
        
        if not company_name or company_name == 'Unknown':
            print(f"📝 排除缺少公司名稱的資料: {company_code}")
            return False
        
        # 🔧 移除過於嚴格的條件：
        # - 不再因為品質評分低而排除
        # - 不再因為內容短而排除
        # - 不再因為一般驗證警告而排除
        
        return True

    def _generate_validation_status_marker(self, company_data: Dict[str, Any]) -> str:
        """🆕 生成驗證狀態標記"""
        validation_passed = company_data.get('content_validation_passed', True)
        validation_errors = company_data.get('validation_errors', [])
        validation_warnings = company_data.get('validation_warnings', [])
        
        if not validation_passed and validation_errors:
            # 檢查是否為嚴重錯誤
            critical_keywords = ['愛派司', '愛立信', 'company_mismatch']
            has_critical = any(
                any(keyword in str(error) for keyword in critical_keywords)
                for error in validation_errors
            )
            
            if has_critical:
                return "🚨 嚴重錯誤"
            else:
                return "❌ 驗證失敗"
        
        elif validation_warnings:
            return "⚠️ 有警告"
        
        else:
            return "✅ 通過"

    def _format_md_file_url_with_warning(self, company_data: Dict[str, Any]) -> str:
        """格式化 MD 檔案連結 - 移除警告標記，保持 URL 乾淨"""
        filename = company_data.get('filename', '')
        
        if not filename:
            return ""
        
        # 確保檔案名稱有 .md 副檔名
        if not filename.endswith('.md'):
            filename += '.md'
        
        # URL 編碼檔案名稱
        encoded_filename = urllib.parse.quote(filename, safe='')
        raw_url = f"{self.github_repo_base}/data/md/{encoded_filename}"
        
        # 🔧 移除警告標記 - 保持 URL 乾淨
        return raw_url

    # 🆕 新增：生成驗證報告
    def generate_validation_report(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """🆕 生成專門的驗證報告"""
        try:
            validation_rows = []
            
            for company_data in processed_companies:
                validation_result = company_data.get('validation_result', {})
                
                validation_row = {
                    '代號': company_data.get('company_code', 'Unknown'),
                    '名稱': company_data.get('company_name', 'Unknown'),
                    '檔案名稱': company_data.get('filename', ''),
                    '驗證狀態': validation_result.get('overall_status', 'unknown'),
                    '信心分數': validation_result.get('confidence_score', 0),
                    '錯誤數量': len(company_data.get('validation_errors', [])),
                    '警告數量': len(company_data.get('validation_warnings', [])),
                    '品質評分': company_data.get('quality_score', 0),
                    '包含在報告': self._should_include_in_report(company_data),
                    '主要問題': self._get_main_validation_issue(company_data),
                    '檢查時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                validation_rows.append(validation_row)
            
            # 建立 DataFrame
            validation_columns = [
                '代號', '名稱', '檔案名稱', '驗證狀態', '信心分數', '錯誤數量', 
                '警告數量', '品質評分', '包含在報告', '主要問題', '檢查時間'
            ]
            
            df = pd.DataFrame(validation_rows, columns=validation_columns)
            df = df.sort_values(['驗證狀態', '信心分數'], ascending=[True, False])
            
            return df
            
        except Exception as e:
            print(f"❌ 生成驗證報告失敗: {e}")
            return pd.DataFrame()

    def _get_main_validation_issue(self, company_data: Dict[str, Any]) -> str:
        """🆕 取得主要驗證問題"""
        validation_errors = company_data.get('validation_errors', [])
        validation_warnings = company_data.get('validation_warnings', [])
        
        if validation_errors:
            # 取得第一個錯誤，截斷過長的訊息
            main_error = str(validation_errors[0])[:80]
            return main_error + "..." if len(str(validation_errors[0])) > 80 else main_error
        
        elif validation_warnings:
            main_warning = str(validation_warnings[0])[:80]
            return main_warning + "..." if len(str(validation_warnings[0])) > 80 else main_warning
        
        else:
            return "無問題"

    # 原有方法保持不變
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

    def _is_more_recent_content_date_only(self, data1: Dict, data2: Dict) -> bool:
        """比較兩筆資料的新舊 - 只用 content_date"""
        date1 = self._get_content_date_only(data1)
        date2 = self._get_content_date_only(data2)
        
        if not date1 and not date2:
            return True
        
        if date1 and not date2:
            return True
        if date2 and not date1:
            return False
        
        try:
            dt1 = datetime.strptime(date1, '%Y-%m-%d')
            dt2 = datetime.strptime(date2, '%Y-%m-%d')
            return dt1 > dt2
        except:
            return True

    def _format_eps_value(self, eps_value) -> str:
        """格式化 EPS 數值"""
        if eps_value is None or eps_value == '':
            return ''
        try:
            eps = float(eps_value)
            return f"{eps:.2f}"
        except (ValueError, TypeError):
            return str(eps_value)

    def save_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, validation_df: pd.DataFrame = None) -> Dict[str, str]:
        """儲存報告為 CSV - 🆕 可選包含驗證報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 檔案路徑
        portfolio_path = os.path.join(self.output_dir, f'portfolio_summary_{timestamp}.csv')
        detailed_path = os.path.join(self.output_dir, f'detailed_report_{timestamp}.csv')
        latest_portfolio_path = os.path.join(self.output_dir, 'portfolio_summary_latest.csv')
        latest_detailed_path = os.path.join(self.output_dir, 'detailed_report_latest.csv')
        
        try:
            # 確保空字符串在 CSV 中正確處理
            portfolio_df_clean = portfolio_df.copy()
            detailed_df_clean = detailed_df.copy()
            
            portfolio_df_clean = portfolio_df_clean.replace('', pd.NA)
            detailed_df_clean = detailed_df_clean.replace('', pd.NA)
            
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
            
            # 🆕 儲存驗證報告
            if validation_df is not None and not validation_df.empty:
                validation_path = os.path.join(self.output_dir, f'validation_report_{timestamp}.csv')
                latest_validation_path = os.path.join(self.output_dir, 'validation_report_latest.csv')
                
                validation_df_clean = validation_df.replace('', pd.NA)
                validation_df_clean.to_csv(validation_path, index=False, encoding='utf-8-sig')
                validation_df_clean.to_csv(latest_validation_path, index=False, encoding='utf-8-sig')
                
                saved_files['validation_report'] = validation_path
                saved_files['validation_report_latest'] = latest_validation_path
            
            print(f"📁 報告已儲存:")
            print(f"   投資組合摘要: {portfolio_path}")
            print(f"   詳細報告: {detailed_path}")
            if validation_df is not None:
                print(f"   驗證報告: {saved_files.get('validation_report', 'N/A')}")
            
            # 檢查空日期處理
            empty_dates = detailed_df_clean[detailed_df_clean['MD日期'].isna()]
            if len(empty_dates) > 0:
                print(f"📊 檢測到 {len(empty_dates)} 個空日期條目")
            
            return saved_files
            
        except Exception as e:
            print(f"❌ 儲存報告失敗: {e}")
            return {}

    def generate_statistics_report(self, processed_companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成統計報告 - 🆕 包含驗證統計"""
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
        
        # 🆕 驗證統計
        validation_passed = len([c for c in processed_companies if c.get('content_validation_passed', True)])
        validation_failed = total_companies - validation_passed
        validation_success_rate = (validation_passed / total_companies) * 100
        
        # 🆕 過濾統計
        companies_included_in_report = len([c for c in processed_companies if self._should_include_in_report(c)])
        inclusion_rate = (companies_included_in_report / total_companies) * 100
        
        # 🆕 關鍵問題統計
        critical_issues = 0
        for company in processed_companies:
            validation_errors = company.get('validation_errors', [])
            if any('愛派司' in str(error) and '愛立信' in str(error) for error in validation_errors):
                critical_issues += 1
        
        statistics = {
            'version': '3.5.0_validation_enhanced',
            'report_type': 'content_validation_filtered',
            'timestamp': datetime.now().isoformat(),
            
            # 基本統計
            'total_companies': total_companies,
            'companies_with_data': companies_with_data,
            'success_rate': round(success_rate, 1),
            'companies_with_content_date': companies_with_content_date,
            'content_date_success_rate': round(content_date_success_rate, 1),
            
            # 🆕 驗證統計
            'validation_statistics': {
                'validation_passed': validation_passed,
                'validation_failed': validation_failed,
                'validation_success_rate': round(validation_success_rate, 1),
                'critical_issues': critical_issues,
                'companies_included_in_report': companies_included_in_report,
                'inclusion_rate': round(inclusion_rate, 1),
                'filtered_out': total_companies - companies_included_in_report
            },
            
            # 品質分析
            'quality_analysis': {
                'average_quality_score': round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0,
                'highest_quality_score': max(quality_scores) if quality_scores else 0,
                'lowest_quality_score': min(quality_scores) if quality_scores else 0
            }
        }
        
        return statistics

    def save_statistics_report(self, statistics: Dict[str, Any]) -> str:
        """儲存統計報告為 JSON 檔案"""
        import json
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_path = os.path.join(self.output_dir, f'statistics_{timestamp}.json')
        latest_stats_path = os.path.join(self.output_dir, 'statistics_latest.json')
        
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2, default=str)
            
            with open(latest_stats_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📊 統計報告已儲存: {stats_path}")
            
            # 顯示重要統計
            validation_stats = statistics.get('validation_statistics', {})
            print(f"📊 驗證成功率: {validation_stats.get('validation_success_rate', 0)}%")
            print(f"📊 報告包含率: {validation_stats.get('inclusion_rate', 0)}%")
            if validation_stats.get('critical_issues', 0) > 0:
                print(f"🚨 關鍵問題: {validation_stats['critical_issues']} 個")
            
            return stats_path
            
        except Exception as e:
            print(f"❌ 儲存統計報告失敗: {e}")
            return ""


# 測試功能
if __name__ == "__main__":
    generator = ReportGenerator()
    
    print("=== 🔒 驗證過濾增強版報告生成器測試 ===")
    
    # 測試數據 - 包含正常和有問題的資料
    test_companies = [
        # 正常資料
        {
            'company_name': '台積電',
            'company_code': '2330',
            'filename': '2330_台積電_factset_abc123.md',
            'content_date': '2025/6/24',
            'analyst_count': 42,
            'target_price': 650.5,
            'eps_2025_avg': 46.00,
            'quality_score': 10.0,
            'quality_status': '🟢 完整',
            'content_validation_passed': True,
            'validation_errors': [],
            'validation_warnings': [],
            'content_length': 5000
        },
        
        # 愛派司/愛立信錯誤資料
        {
            'company_name': '愛派司',
            'company_code': '6918',
            'filename': '6918_愛派司_yahoo_def456.md',
            'content_date': '2025/6/19',
            'analyst_count': 18,
            'target_price': 8.6,
            'eps_2025_avg': 6.00,
            'quality_score': 2.0,  # 低分
            'quality_status': '🔴 不足',
            'content_validation_passed': False,
            'validation_errors': ['檔案標示為愛派司(6918)但內容包含愛立信相關資訊'],
            'validation_warnings': [],
            'validation_result': {
                'overall_status': 'error',
                'confidence_score': 0.0
            },
            'content_length': 2000
        },
        
        # 一般品質較低資料
        {
            'company_name': '測試公司',
            'company_code': '1234',
            'filename': '1234_測試公司_yahoo_ghi789.md',
            'content_date': None,  # 沒有內容日期
            'analyst_count': 0,
            'target_price': None,
            'eps_2025_avg': None,
            'quality_score': 3.5,
            'quality_status': '🟠 部分',
            'content_validation_passed': True,
            'validation_errors': [],
            'validation_warnings': ['內容過短'],
            'content_length': 800
        }
    ]
    
    print("測試 1: 生成詳細報告 (過濾無效資料)")
    detailed_df = generator.generate_detailed_report(test_companies, filter_invalid=True)
    print(f"   原始資料: {len(test_companies)} 筆")
    print(f"   報告包含: {len(detailed_df)} 筆")
    print(f"   過濾結果: {'✅ 正確過濾愛派司錯誤' if len(detailed_df) == 2 else '❌ 過濾異常'}")
    
    print("\n測試 2: 生成投資組合摘要")
    portfolio_df = generator.generate_portfolio_summary(test_companies, filter_invalid=True)
    print(f"   摘要包含: {len(portfolio_df)} 家公司")
    
    print("\n測試 3: 生成驗證報告")
    validation_df = generator.generate_validation_report(test_companies)
    print(f"   驗證報告: {len(validation_df)} 筆記錄")
    
    # 檢查驗證狀態欄位
    if not detailed_df.empty:
        print(f"\n驗證狀態欄位測試:")
        for idx, row in detailed_df.iterrows():
            company = row['名稱']
            validation_status = row['驗證狀態']
            print(f"   {company}: {validation_status}")
    
    print(f"\n✅ 預期結果:")
    print(f"   台積電: ✅ 通過")
    print(f"   測試公司: ⚠️ 有警告")
    print(f"   愛派司: 應被過濾 (不出現在報告中)")
    
    print(f"\n🎉 測試完成!")