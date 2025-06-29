#!/usr/bin/env python3
"""
Report Generator - FactSet Pipeline v3.5.1 (Fixed - Complete Implementation)
修正 detailed_report_columns 屬性定義位置錯誤
修正觀察名單驗證過濾邏輯，準確識別需要排除的資料
完整實作版本，包含所有必要功能
"""

import os
import re
import pandas as pd
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
import pytz

class ReportGenerator:
    """報告生成器 v3.5.1 - 修正觀察名單驗證過濾完整版"""
    
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

        # 🔧 修正：詳細報告欄位 (22 欄位 - 包含驗證狀態) - 移動到 __init__ 方法中
        self.detailed_report_columns = [
            '代號', '名稱', '股票代號', 'MD日期', '分析師數量', '目標價',
            '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
            '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
            '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
            '品質評分', '狀態', '驗證狀態', 'MD File', '更新日期'
        ]

    def _get_taipei_time(self) -> str:
        """取得台北時間的字串格式"""
        taipei_time = datetime.now(self.taipei_tz)
        return taipei_time.strftime('%Y-%m-%d %H:%M:%S')

    def _should_include_in_report(self, company_data: Dict[str, Any]) -> bool:
        """🔧 向下相容性：舊方法名稱的別名"""
        return self._should_include_in_report_v351(company_data)

    def generate_portfolio_summary(self, processed_companies: List[Dict], filter_invalid=True) -> pd.DataFrame:
        """🔧 v3.5.1 生成投資組合摘要 - 修正過濾邏輯"""
        try:
            # 🔧 過濾邏輯修正
            if filter_invalid:
                original_count = len(processed_companies)
                valid_companies = [c for c in processed_companies if self._should_include_in_report_v351(c)]
                filtered_count = original_count - len(valid_companies)
                
                print(f"📊 投資組合摘要過濾結果:")
                print(f"   原始公司數: {original_count}")
                print(f"   保留公司數: {len(valid_companies)}")
                print(f"   過濾公司數: {filtered_count}")
                
                # 🔧 顯示過濾詳情
                if filtered_count > 0:
                    filtered_companies = [c for c in processed_companies if not self._should_include_in_report_v351(c)]
                    print(f"   過濾原因分析:")
                    
                    filter_reasons = {}
                    for company in filtered_companies:
                        reason = self._get_filter_reason(company)
                        filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
                    
                    for reason, count in filter_reasons.items():
                        print(f"     {reason}: {count} 家")
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
                        print(f"🔄 {company_code} 更新最佳品質資料: {best_quality:.1f} → {current_quality:.1f}")
                    elif current_quality == best_quality:
                        if self._is_more_recent_content_date_only(company_data, current_best):
                            company_summary[company_code]['best_quality_data'] = company_data
                            print(f"🔄 {company_code} 品質相同({current_quality:.1f})，使用較新日期")
            
            # 生成摘要資料
            summary_rows = []
            
            for company_code, company_info in company_summary.items():
                best_data = company_info['best_quality_data']
                all_files = company_info['files']
                
                # 顯示選擇的資料資訊
                selected_date = self._get_content_date_only(best_data)
                selected_quality = best_data.get('quality_score', 0)
                print(f"📊 {company_code}: 選擇品質 {selected_quality:.1f} 的資料 (日期: {selected_date})")
                
                # 計算日期範圍
                oldest_date, newest_date = self._calculate_date_range_content_date_only(all_files)
                
                # 使用最佳品質資料生成摘要
                clean_code = self._clean_stock_code_for_display(company_code)
                
                summary_row = {
                    '代號': clean_code,
                    '名稱': best_data.get('company_name', 'Unknown'),
                    '股票代號': f"{clean_code}-TW",
                    'MD最舊日期': oldest_date or selected_date,
                    'MD最新日期': newest_date or selected_date,
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
        """🔧 v3.5.1 生成詳細報告 - 修正過濾邏輯"""
        try:
            detailed_rows = []
            filtered_count = 0
            
            for company_data in processed_companies:
                # 🔧 檢查是否應該過濾此資料
                if filter_invalid and not self._should_include_in_report_v351(company_data):
                    filtered_count += 1
                    print(f"🚫 過濾掉: {company_data.get('company_name', 'Unknown')}({company_data.get('company_code', 'Unknown')}) - 驗證失敗")
                    continue
                
                # 原有的報告生成邏輯
                md_date = self._get_content_date_only(company_data)
                
                # 生成驗證狀態標記
                validation_status = self._generate_validation_status_marker_v351(company_data)
                
                # 處理 MD 檔案連結
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
                    '驗證狀態': validation_status,
                    'MD File': md_file_url,
                    '更新日期': self._get_taipei_time()
                }
                
                detailed_rows.append(detailed_row)
            
            # 建立 DataFrame
            df = pd.DataFrame(detailed_rows, columns=self.detailed_report_columns)
            df = df.sort_values(['代號', 'MD日期'], ascending=[True, False])
            
            # 記錄過濾統計
            if filter_invalid and filtered_count > 0:
                print(f"📊 詳細報告過濾了 {filtered_count} 筆驗證失敗的資料")
            
            print(f"📊 詳細報告包含 {len(detailed_rows)} 筆有效資料")
            
            return df
            
        except Exception as e:
            print(f"❌ 生成詳細報告失敗: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(columns=self.detailed_report_columns)

    def _should_include_in_report_v351(self, company_data: Dict[str, Any]) -> bool:
        """🔧 v3.5.1 修正版判斷是否應該將此資料包含在報告中"""
        
        # 🔧 檢查 1: 基本資料完整性
        company_code = company_data.get('company_code')
        company_name = company_data.get('company_name')
        
        if not company_code or company_code == 'Unknown':
            print(f"📝 排除缺少公司代號的資料: {company_name}")
            return False
        
        if not company_name or company_name == 'Unknown':
            print(f"📝 排除缺少公司名稱的資料: {company_code}")
            return False
        
        # 🔧 檢查 2: 驗證結果檢查 (多層檢查)
        validation_result = company_data.get('validation_result', {})
        validation_status = validation_result.get('overall_status', 'unknown')
        validation_method = validation_result.get('validation_method', 'unknown')
        
        # 🔧 檢查 validation_result 中的錯誤狀態
        if validation_status == 'error':
            validation_errors = validation_result.get('errors', [])
            if validation_errors:
                main_error = str(validation_errors[0])
                print(f"🚨 排除驗證錯誤 (validation_result): {company_name}({company_code}) - {main_error[:60]}...")
                return False
        
        # 🔧 檢查 3: content_validation_passed 字段
        validation_passed = company_data.get('content_validation_passed', True)
        if not validation_passed:
            validation_errors = company_data.get('validation_errors', [])
            main_error = str(validation_errors[0]) if validation_errors else "驗證失敗"
            print(f"🚨 排除驗證失敗 (content_validation_passed): {company_name}({company_code}) - {main_error[:60]}...")
            return False
        
        # 🔧 檢查 4: 直接檢查 validation_errors 中的關鍵錯誤
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
                    print(f"🚨 排除關鍵驗證錯誤: {company_name}({company_code}) - {error_str[:60]}...")
                    return False
        
        # 🔧 檢查 5: 品質評分為 0 且有 ❌ 驗證失敗狀態
        quality_score = company_data.get('quality_score', 0)
        quality_status = company_data.get('quality_status', '')
        
        if quality_score == 0 and '❌ 驗證失敗' in quality_status:
            print(f"🚨 排除 0 分驗證失敗: {company_name}({company_code}) - 品質評分為 0 且狀態為驗證失敗")
            return False
        
        # 🔧 檢查 6: 額外的品質狀態檢查
        if '❌' in quality_status and quality_score <= 1.0:
            print(f"🚨 排除極低品質評分: {company_name}({company_code}) - 品質評分: {quality_score}, 狀態: {quality_status}")
            return False
        
        # 通過所有檢查
        return True

    def _get_filter_reason(self, company_data: Dict[str, Any]) -> str:
        """🔧 v3.5.1 取得過濾原因"""
        company_code = company_data.get('company_code', 'Unknown')
        company_name = company_data.get('company_name', 'Unknown')
        
        # 檢查基本資料
        if not company_code or company_code == 'Unknown':
            return "缺少公司代號"
        if not company_name or company_name == 'Unknown':
            return "缺少公司名稱"
        
        # 檢查驗證錯誤
        validation_errors = company_data.get('validation_errors', [])
        if validation_errors:
            main_error = str(validation_errors[0])
            if "不在觀察名單" in main_error:
                return "不在觀察名單"
            elif "公司名稱不符觀察名單" in main_error or "觀察名單顯示應為" in main_error:
                return "觀察名單名稱不符"
            elif "愛派司" in main_error or "愛立信" in main_error:
                return "公司名稱混亂"
            elif "格式無效" in main_error:
                return "格式無效"
            else:
                return "其他驗證錯誤"
        
        # 檢查驗證狀態
        validation_passed = company_data.get('content_validation_passed', True)
        if not validation_passed:
            return "驗證失敗"
        
        # 檢查品質評分
        quality_score = company_data.get('quality_score', 0)
        quality_status = company_data.get('quality_status', '')
        
        if quality_score == 0 and '❌' in quality_status:
            return "品質評分為 0"
        
        return "未知原因"

    def _generate_validation_status_marker_v351(self, company_data: Dict[str, Any]) -> str:
        """🔧 v3.5.1 生成驗證狀態標記"""
        validation_result = company_data.get('validation_result', {})
        validation_status = validation_result.get('overall_status', 'unknown')
        validation_method = validation_result.get('validation_method', 'unknown')
        validation_passed = company_data.get('content_validation_passed', True)
        validation_errors = company_data.get('validation_errors', [])
        validation_warnings = company_data.get('validation_warnings', [])
        validation_enabled = company_data.get('validation_enabled', False)
        
        # 🔧 多層驗證狀態判斷
        if validation_status == 'error' or not validation_passed:
            # 檢查錯誤類型
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

    def generate_validation_report(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """🔧 v3.5.1 生成專門的驗證報告"""
        try:
            validation_rows = []
            
            for company_data in processed_companies:
                validation_result = company_data.get('validation_result', {})
                
                validation_row = {
                    '代號': company_data.get('company_code', 'Unknown'),
                    '名稱': company_data.get('company_name', 'Unknown'),
                    '檔案名稱': company_data.get('filename', ''),
                    '驗證狀態': validation_result.get('overall_status', 'unknown'),
                    '驗證方法': validation_result.get('validation_method', 'unknown'),
                    '信心分數': validation_result.get('confidence_score', 0),
                    '錯誤數量': len(company_data.get('validation_errors', [])),
                    '警告數量': len(company_data.get('validation_warnings', [])),
                    '品質評分': company_data.get('quality_score', 0),
                    '包含在報告': self._should_include_in_report_v351(company_data),
                    '過濾原因': self._get_filter_reason(company_data) if not self._should_include_in_report_v351(company_data) else "無",
                    '主要問題': self._get_main_validation_issue(company_data),
                    '檢查時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                validation_rows.append(validation_row)
            
            # 建立 DataFrame
            validation_columns = [
                '代號', '名稱', '檔案名稱', '驗證狀態', '驗證方法', '信心分數', '錯誤數量', 
                '警告數量', '品質評分', '包含在報告', '過濾原因', '主要問題', '檢查時間'
            ]
            
            df = pd.DataFrame(validation_rows, columns=validation_columns)
            df = df.sort_values(['包含在報告', '驗證狀態', '信心分數'], ascending=[False, True, False])
            
            return df
            
        except Exception as e:
            print(f"❌ 生成驗證報告失敗: {e}")
            return pd.DataFrame()

    def _get_main_validation_issue(self, company_data: Dict[str, Any]) -> str:
        """取得主要驗證問題"""
        validation_errors = company_data.get('validation_errors', [])
        validation_warnings = company_data.get('validation_warnings', [])
        
        if validation_errors:
            main_error = str(validation_errors[0])[:80]
            return main_error + "..." if len(str(validation_errors[0])) > 80 else main_error
        
        elif validation_warnings:
            main_warning = str(validation_warnings[0])[:80]
            return main_warning + "..." if len(str(validation_warnings[0])) > 80 else main_warning
        
        else:
            return "無問題"

    def _clean_stock_code_for_display(self, code):
        """清理股票代號，確保顯示為純數字（無引號）"""
        if pd.isna(code) or code is None or code == '':
            return ''
        
        code_str = str(code).strip()
        
        # 移除任何現有的前導單引號
        if code_str.startswith("'"):
            code_str = code_str[1:]
        
        # 如果是純數字，直接返回（讓 Google Sheets 當作數字處理）
        if code_str.isdigit():
            return code_str
        
        return code_str

    def _format_md_file_url_with_warning(self, company_data: Dict[str, Any]) -> str:
        """格式化 MD 檔案連結"""
        filename = company_data.get('filename', '')
        
        if not filename:
            return ""
        
        # 確保檔案名稱有 .md 副檔名
        if not filename.endswith('.md'):
            filename += '.md'
        
        # URL 編碼檔案名稱
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
        """🔧 v3.5.1 儲存報告為 CSV - 可選包含驗證報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 檔案路徑
        portfolio_path = os.path.join(self.output_dir, f'portfolio_summary_v351_{timestamp}.csv')
        detailed_path = os.path.join(self.output_dir, f'detailed_report_v351_{timestamp}.csv')
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
            
            # 儲存驗證報告
            if validation_df is not None and not validation_df.empty:
                validation_path = os.path.join(self.output_dir, f'validation_report_v351_{timestamp}.csv')
                latest_validation_path = os.path.join(self.output_dir, 'validation_report_latest.csv')
                
                validation_df_clean = validation_df.replace('', pd.NA)
                validation_df_clean.to_csv(validation_path, index=False, encoding='utf-8-sig')
                validation_df_clean.to_csv(latest_validation_path, index=False, encoding='utf-8-sig')
                
                saved_files['validation_report'] = validation_path
                saved_files['validation_report_latest'] = latest_validation_path
            
            print(f"📁 v3.5.1 報告已儲存:")
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
        """🔧 v3.5.1 生成統計報告 - 包含修正的驗證統計"""
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
        
        # 🔧 v3.5.1 修正的驗證統計
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
        
        # 🔧 關鍵問題統計 (更準確)
        critical_issues = 0
        filter_reasons = {}
        
        for company in processed_companies:
            if not self._should_include_in_report_v351(company):
                critical_issues += 1
                reason = self._get_filter_reason(company)
                filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
        
        statistics = {
            'version': '3.5.1_fixed_validation',
            'report_type': 'watch_list_validation_fixed',
            'timestamp': datetime.now().isoformat(),
            
            # 基本統計
            'total_companies': total_companies,
            'companies_with_data': companies_with_data,
            'success_rate': round(success_rate, 1),
            'companies_with_content_date': companies_with_content_date,
            'content_date_success_rate': round(content_date_success_rate, 1),
            
            # 🔧 修正的驗證統計
            'validation_statistics': {
                'validation_passed': validation_passed,
                'validation_failed': validation_failed,
                'validation_disabled': validation_disabled,
                'validation_success_rate': round(validation_success_rate, 1),
                'critical_issues': critical_issues,
                'companies_included_in_report': companies_included_in_report,
                'inclusion_rate': round(inclusion_rate, 1),
                'filtered_out': total_companies - companies_included_in_report,
                'filter_reasons': filter_reasons
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
        stats_path = os.path.join(self.output_dir, f'statistics_v351_{timestamp}.json')
        latest_stats_path = os.path.join(self.output_dir, 'statistics_latest.json')
        
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2, default=str)
            
            with open(latest_stats_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📊 v3.5.1 統計報告已儲存: {stats_path}")
            
            # 顯示重要統計
            validation_stats = statistics.get('validation_statistics', {})
            print(f"📊 驗證成功率: {validation_stats.get('validation_success_rate', 0)}%")
            print(f"📊 報告包含率: {validation_stats.get('inclusion_rate', 0)}%")
            print(f"📊 驗證停用: {validation_stats.get('validation_disabled', 0)} 個")
            if validation_stats.get('critical_issues', 0) > 0:
                print(f"🚨 過濾問題: {validation_stats['critical_issues']} 個")
                filter_reasons = validation_stats.get('filter_reasons', {})
                for reason, count in filter_reasons.items():
                    print(f"   {reason}: {count} 個")
            
            return stats_path
            
        except Exception as e:
            print(f"❌ 儲存統計報告失敗: {e}")
            return ""

    def test_filtering_logic(self, test_companies: List[Dict]) -> Dict[str, Any]:
        """🔧 v3.5.1 新增：測試過濾邏輯的方法"""
        test_results = {
            'total_companies': len(test_companies),
            'included_companies': [],
            'excluded_companies': [],
            'filter_reasons': {}
        }
        
        for company in test_companies:
            include = self._should_include_in_report_v351(company)
            company_name = company.get('company_name', 'Unknown')
            company_code = company.get('company_code', 'Unknown')
            
            if include:
                test_results['included_companies'].append({
                    'name': company_name,
                    'code': company_code,
                    'quality_score': company.get('quality_score', 0)
                })
            else:
                reason = self._get_filter_reason(company)
                test_results['excluded_companies'].append({
                    'name': company_name,
                    'code': company_code,
                    'reason': reason,
                    'quality_score': company.get('quality_score', 0)
                })
                test_results['filter_reasons'][reason] = test_results['filter_reasons'].get(reason, 0) + 1
        
        return test_results


# 測試功能
if __name__ == "__main__":
    generator = ReportGenerator()
    
    print("=== 🔒 v3.5.1 修正版觀察名單驗證過濾的報告生成器測試 ===")
    
    # 測試數據 - 包含各種驗證狀態
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
            'validation_enabled': True,
            'validation_result': {
                'overall_status': 'valid',
                'validation_method': 'strict',
                'confidence_score': 10.0
            },
            'validation_errors': [],
            'validation_warnings': [],
            'content_length': 5000
        },
        
        # 不在觀察名單的錯誤資料
        {
            'company_name': '威剛',
            'company_code': '1122',
            'filename': '1122_威剛_yahoo_def456.md',
            'content_date': '2025/6/19',
            'analyst_count': 0,
            'target_price': None,
            'eps_2025_avg': None,
            'quality_score': 0.0,
            'quality_status': '❌ 驗證失敗',
            'content_validation_passed': False,
            'validation_enabled': True,
            'validation_result': {
                'overall_status': 'error',
                'validation_method': 'strict',
                'errors': ['代號1122不在觀察名單中，不允許處理']
            },
            'validation_errors': ['代號1122不在觀察名單中，不允許處理'],
            'validation_warnings': [],
            'content_length': 1000
        }
    ]
    
    print("測試 1: 過濾邏輯測試")
    test_results = generator.test_filtering_logic(test_companies)
    
    print(f"   總公司數: {test_results['total_companies']}")
    print(f"   包含公司: {len(test_results['included_companies'])}")
    print(f"   排除公司: {len(test_results['excluded_companies'])}")
    
    print("\n   包含的公司:")
    for company in test_results['included_companies']:
        print(f"     ✅ {company['name']} ({company['code']}) - 品質: {company['quality_score']}")
    
    print("\n   排除的公司:")
    for company in test_results['excluded_companies']:
        print(f"     ❌ {company['name']} ({company['code']}) - 原因: {company['reason']}")
    
    print("\n測試 2: 生成詳細報告")
    detailed_df = generator.generate_detailed_report(test_companies, filter_invalid=True)
    print(f"   原始資料: {len(test_companies)} 筆")
    print(f"   詳細報告包含: {len(detailed_df)} 筆記錄")
    
    expected_included = 1  # 只有台積電
    if len(detailed_df) == expected_included:
        print(f"\n✅ 修正結果正確:")
        print(f"   台積電: 正常通過")
        print(f"   威剛: 正確過濾 (不在觀察名單)")
    else:
        print(f"\n❌ 過濾結果異常，需要檢查邏輯")
        print(f"   預期包含: {expected_included} 家")
        print(f"   實際包含: {len(detailed_df)} 家")
    
    print(f"\n🎉 v3.5.1 修正版測試完成!")
    print(f"🔧 detailed_report_columns 屬性定義位置已修正")