#!/usr/bin/env python3
"""
Sheets Uploader - FactSet Pipeline v3.5.1 (CSV Validation Summary Solution)
完整解決方案：生成 CSV 驗證摘要檔案，避免 Google Sheets API 格式問題
增強對觀察名單驗證的支援，更好地處理驗證狀態
"""

import os
import gspread
import pandas as pd
import math
from datetime import datetime
from typing import Dict, Any, List, Optional
from google.oauth2.service_account import Credentials
import json

# 🔧 載入環境變數
try:
    from dotenv import load_dotenv
    # 載入 .env 檔案 - 嘗試多個路徑
    env_paths = [
        '.env',
        '../.env', 
        '../../.env',
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), '../.env')
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break
except ImportError:
    pass

class SheetsUploader:
    """Google Sheets 上傳器 v3.5.1 - CSV 驗證摘要解決方案"""
    
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main"):
        self.github_repo_base = github_repo_base
        self.client = None
        self.spreadsheet = None
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        # 🔧 v3.5.1 更新的驗證設定
        self.validation_settings = {
            'check_before_upload': True,
            'allow_warning_data': True,
            'allow_error_data': False,
            'max_validation_errors': 5,
            'skip_not_block': True,
            'enhanced_validation': True,
            'generate_validation_csv': True,      # 🆕 生成驗證摘要 CSV
            'upload_validation_to_sheets': True,  # 🆕 上傳驗證摘要到 Sheets（簡化版）
            'csv_output_dir': 'data/reports'      # 🆕 CSV 輸出目錄
        }
        
        # 確保輸出目錄存在
        os.makedirs(self.validation_settings['csv_output_dir'], exist_ok=True)

    def _clean_stock_code(self, code):
        """清理股票代號格式"""
        if pd.isna(code) or code is None:
            return ''
        
        code_str = str(code).strip()
        
        if code_str.startswith("'"):
            code_str = code_str[1:]
        
        if code_str.isdigit() and len(code_str) == 4:
            return int(code_str)
        
        if '-TW' in code_str:
            parts = code_str.split('-TW')
            if len(parts) == 2 and parts[0].isdigit() and len(parts[0]) == 4:
                return f"{int(parts[0])}-TW"
        
        return code_str
        
    def upload_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> bool:
        """🔧 v3.5.1 主要上傳方法 - 包含 CSV 驗證摘要"""
        try:
            # 🔧 上傳前驗證
            if self.validation_settings['check_before_upload']:
                validation_result = self._validate_before_upload_v351(portfolio_df, detailed_df)
                
                if not validation_result['safe_to_upload']:
                    print(f"🚨 上傳驗證失敗: {validation_result['reason']}")
                    print(f"📊 問題摘要: {validation_result['summary']}")
                    
                    if validation_result['severity'] == 'critical':
                        print("❌ 發現關鍵問題，停止上傳")
                        return False
                    elif validation_result['severity'] == 'warning' and not self._ask_force_upload():
                        print("❌ 取消上傳")
                        return False
                    else:
                        print("⚠️ 忽略警告，繼續上傳")
                else:
                    if validation_result.get('reason'):
                        print(f"📊 驗證統計: {validation_result['reason']}")
                        print(f"📊 問題摘要: {validation_result['summary']}")
                    else:
                        print("✅ 上傳前驗證通過")
            
            # 設定連線
            if not self._setup_connection():
                print("❌ Google Sheets 連線失敗")
                return False
            
            # 標記問題資料
            portfolio_df_marked = self._mark_problematic_data_v351(portfolio_df)
            detailed_df_marked = self._mark_problematic_data_v351(detailed_df)
            
            # 上傳投資組合摘要
            if not self._upload_portfolio_summary(portfolio_df_marked):
                print("❌ 投資組合摘要上傳失敗")
                return False
            
            # 上傳詳細報告
            if not self._upload_detailed_report(detailed_df_marked):
                print("❌ 詳細報告上傳失敗")
                return False
            
            # 🆕 處理驗證摘要 - CSV 生成和可選的 Sheets 上傳
            self._handle_validation_summary(portfolio_df, detailed_df)
            
            print("✅ 所有報告上傳成功")
            return True
            
        except Exception as e:
            print(f"❌ 上傳過程中發生錯誤: {e}")
            return False

    def _handle_validation_summary(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame):
        """🆕 處理驗證摘要 - 生成 CSV 和可選的 Sheets 上傳"""
        try:
            # 1. 生成驗證摘要數據
            validation_data = self._generate_validation_summary_data(portfolio_df, detailed_df)
            
            # 2. 生成 CSV 檔案
            if self.validation_settings.get('generate_validation_csv', True):
                csv_file = self._save_validation_summary_csv(validation_data)
                if csv_file:
                    print(f"📊 驗證摘要 CSV 已生成: {csv_file}")
            
            # 3. 嘗試上傳到 Google Sheets（簡化版，無格式設定）
            if self.validation_settings.get('upload_validation_to_sheets', True):
                try:
                    self._upload_validation_summary_simple(validation_data)
                    print("📊 驗證摘要已上傳到 Google Sheets")
                except Exception as e:
                    print(f"⚠️ Google Sheets 驗證摘要上傳失敗: {e}")
                    print("💡 但 CSV 檔案已生成，可手動上傳")
            
        except Exception as e:
            print(f"⚠️ 驗證摘要處理失敗: {e}")

    def _generate_validation_summary_data(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> pd.DataFrame:
        """🆕 生成驗證摘要數據為 DataFrame"""
        summary_rows = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 基本統計
        summary_rows.append({
            '項目': '總公司數',
            '數值': len(portfolio_df),
            '說明': '投資組合中的公司總數',
            '詳細資訊': f'詳細記錄: {len(detailed_df)}',
            '更新時間': current_time
        })
        
        # 驗證狀態統計
        if '驗證狀態' in detailed_df.columns:
            validation_counts = detailed_df['驗證狀態'].value_counts()
            
            # 分類統計
            passed_count = 0
            warning_count = 0
            disabled_count = 0
            critical_count = 0
            
            for status, count in validation_counts.items():
                status_str = str(status)
                if '✅' in status_str:
                    passed_count += count
                elif '⚠️ 驗證停用' in status_str:
                    disabled_count += count
                elif '⚠️' in status_str:
                    warning_count += count
                elif any(marker in status_str for marker in ['❌', '🚫', '📝', '🔄']):
                    critical_count += count
            
            # 詳細驗證統計
            total_records = len(detailed_df)
            summary_rows.extend([
                {
                    '項目': '驗證通過',
                    '數值': passed_count,
                    '說明': '通過內容驗證的記錄數',
                    '詳細資訊': f'成功率: {passed_count/total_records*100:.1f}%',
                    '更新時間': current_time
                },
                {
                    '項目': '驗證停用',
                    '數值': disabled_count,
                    '說明': '因觀察名單未載入而停用驗證',
                    '詳細資訊': '這些公司仍會包含在報告中',
                    '更新時間': current_time
                },
                {
                    '項目': '驗證警告',
                    '數值': warning_count,
                    '說明': '有驗證警告的記錄數',
                    '詳細資訊': '需要人工檢查',
                    '更新時間': current_time
                },
                {
                    '項目': '關鍵問題',
                    '數值': critical_count,
                    '說明': '嚴重驗證問題的記錄數',
                    '詳細資訊': '應已被過濾排除',
                    '更新時間': current_time
                }
            ])
            
            # 驗證品質指標
            total_validation_active = total_records - disabled_count
            if total_validation_active > 0:
                validation_quality = (passed_count / total_validation_active) * 100
                summary_rows.append({
                    '項目': '驗證品質',
                    '數值': f'{validation_quality:.1f}%',
                    '說明': '啟用驗證中的通過率',
                    '詳細資訊': f'活躍驗證: {total_validation_active}',
                    '更新時間': current_time
                })
        
        # 品質統計
        if '品質評分' in detailed_df.columns:
            quality_scores = detailed_df['品質評分'].dropna()
            if not quality_scores.empty:
                avg_quality = quality_scores.mean()
                high_quality = len(quality_scores[quality_scores >= 8.0])
                low_quality = len(quality_scores[quality_scores <= 3.0])
                zero_quality = len(quality_scores[quality_scores == 0.0])
                
                quality_rows = [
                    {
                        '項目': '平均品質評分',
                        '數值': f'{avg_quality:.1f}',
                        '說明': '所有記錄的平均品質評分',
                        '詳細資訊': f'最高: {quality_scores.max():.1f}, 最低: {quality_scores.min():.1f}',
                        '更新時間': current_time
                    },
                    {
                        '項目': '高品質記錄',
                        '數值': high_quality,
                        '說明': '品質評分 ≥ 8.0 的記錄數',
                        '詳細資訊': f'佔比: {high_quality/len(quality_scores)*100:.1f}%',
                        '更新時間': current_time
                    },
                    {
                        '項目': '低品質記錄',
                        '數值': low_quality,
                        '說明': '品質評分 ≤ 3.0 的記錄數',
                        '詳細資訊': f'佔比: {low_quality/len(quality_scores)*100:.1f}%',
                        '更新時間': current_time
                    }
                ]
                
                summary_rows.extend(quality_rows)
                
                if zero_quality > 0:
                    summary_rows.append({
                        '項目': '零分記錄',
                        '數值': zero_quality,
                        '說明': '品質評分為 0 的記錄數',
                        '詳細資訊': '通常表示驗證失敗',
                        '更新時間': current_time
                    })
        
        # 系統健康度指標
        system_health = self._calculate_system_health(detailed_df)
        summary_rows.append({
            '項目': '系統健康度',
            '數值': f'{system_health:.1f}%',
            '說明': '整體資料處理品質指標',
            '詳細資訊': '綜合驗證和品質評分',
            '更新時間': current_time
        })
        
        # 額外的驗證狀態詳細分解
        if '驗證狀態' in detailed_df.columns:
            status_breakdown = detailed_df['驗證狀態'].value_counts()
            for status, count in status_breakdown.items():
                if count > 0:
                    summary_rows.append({
                        '項目': f'狀態詳細: {status}',
                        '數值': count,
                        '說明': f'具有「{status}」狀態的記錄數',
                        '詳細資訊': f'佔總數 {count/len(detailed_df)*100:.1f}%',
                        '更新時間': current_time
                    })
        
        return pd.DataFrame(summary_rows)

    def _save_validation_summary_csv(self, validation_df: pd.DataFrame) -> str:
        """🆕 儲存驗證摘要為 CSV 檔案"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'validation_summary_{timestamp}.csv'
            csv_path = os.path.join(self.validation_settings['csv_output_dir'], csv_filename)
            
            # 儲存 CSV
            validation_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # 同時儲存最新版本
            latest_csv_path = os.path.join(self.validation_settings['csv_output_dir'], 'validation_summary_latest.csv')
            validation_df.to_csv(latest_csv_path, index=False, encoding='utf-8-sig')
            
            return csv_path
            
        except Exception as e:
            print(f"❌ 儲存驗證摘要 CSV 失敗: {e}")
            return ""

    def _upload_validation_summary_simple(self, validation_df: pd.DataFrame):
        """🆕 簡化版驗證摘要上傳 - 只上傳數據，不設定格式"""
        try:
            # 嘗試找到或建立驗證摘要工作表
            try:
                validation_worksheet = self.spreadsheet.worksheet("驗證摘要")
            except gspread.WorksheetNotFound:
                print("📊 建立驗證摘要工作表...")
                validation_worksheet = self.spreadsheet.add_worksheet(title="驗證摘要", rows=200, cols=10)
            
            # 清空現有內容
            validation_worksheet.clear()
            
            # 準備數據
            headers = validation_df.columns.tolist()
            data = validation_df.values.tolist()
            
            # 確保所有數據都是字符串格式，避免格式問題
            clean_data = []
            for row in data:
                clean_row = []
                for cell in row:
                    if pd.isna(cell):
                        clean_row.append('')
                    else:
                        clean_row.append(str(cell))
                clean_data.append(clean_row)
            
            # 上傳標題
            validation_worksheet.update('A1', [headers])
            
            # 上傳數據
            if clean_data:
                validation_worksheet.update('A2', clean_data)
            
            # 🔧 只設定最基本的標題格式，避免 columnWidth 問題
            try:
                validation_worksheet.format('A1:E1', {
                    'textFormat': {'bold': True}
                })
            except:
                # 如果連基本格式都失敗，就完全跳過格式設定
                pass
            
        except Exception as e:
            raise Exception(f"簡化上傳失敗: {e}")

    def _validate_before_upload_v351(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> Dict[str, Any]:
        """🔧 v3.5.1 增強的上傳前驗證檢查"""
        validation_result = {
            'safe_to_upload': True,
            'reason': '',
            'summary': {},
            'issues': [],
            'severity': 'info'
        }
        
        if portfolio_df.empty:
            validation_result['safe_to_upload'] = False
            validation_result['reason'] = '投資組合摘要為空'
            validation_result['severity'] = 'critical'
            return validation_result
        
        if detailed_df.empty:
            validation_result['safe_to_upload'] = False
            validation_result['reason'] = '詳細報告為空'
            validation_result['severity'] = 'critical'
            return validation_result
        
        # 驗證狀態分析
        validation_issues = []
        critical_issues = 0
        warning_issues = 0
        validation_disabled_count = 0
        
        if '驗證狀態' in detailed_df.columns:
            for idx, row in detailed_df.iterrows():
                validation_status = str(row.get('驗證狀態', ''))
                company_name = row.get('名稱', 'Unknown')
                company_code = row.get('代號', 'Unknown')
                
                if '🚫' in validation_status or '❌' in validation_status:
                    critical_issues += 1
                    validation_issues.append({
                        'company': f"{company_name}({company_code})",
                        'type': 'critical',
                        'status': validation_status
                    })
                elif '⚠️' in validation_status:
                    if '驗證停用' in validation_status:
                        validation_disabled_count += 1
                    else:
                        warning_issues += 1
                    validation_issues.append({
                        'company': f"{company_name}({company_code})",
                        'type': 'warning',
                        'status': validation_status
                    })
        
        total_companies = len(detailed_df)
        validation_result['summary'] = {
            'total_companies': total_companies,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'validation_disabled': validation_disabled_count,
            'validation_issues': len(validation_issues)
        }
        
        validation_result['issues'] = validation_issues
        
        if self.validation_settings.get('enhanced_validation', False):
            if critical_issues > 0:
                validation_result['safe_to_upload'] = False
                validation_result['severity'] = 'critical'
                validation_result['reason'] = f'發現 {critical_issues} 個關鍵驗證問題'
            elif warning_issues > total_companies * 0.5:
                validation_result['safe_to_upload'] = False
                validation_result['severity'] = 'warning'
                validation_result['reason'] = f'警告問題過多: {warning_issues}/{total_companies}'
            else:
                validation_result['safe_to_upload'] = True
                if validation_disabled_count > 0 or warning_issues > 0:
                    validation_result['reason'] = f'發現 {warning_issues} 個警告、{validation_disabled_count} 個驗證停用，將繼續上傳'
                    validation_result['severity'] = 'info'
        
        return validation_result

    def _mark_problematic_data_v351(self, df: pd.DataFrame) -> pd.DataFrame:
        """🔧 v3.5.1 增強的問題資料標記"""
        df_marked = df.copy()
        
        if '驗證狀態' in df_marked.columns and '名稱' in df_marked.columns:
            for idx, row in df_marked.iterrows():
                validation_status = str(row.get('驗證狀態', ''))
                company_name = str(row.get('名稱', ''))
                
                if '🚫' in validation_status:
                    df_marked.at[idx, '名稱'] = f"🚫 {company_name}"
                elif '❌' in validation_status:
                    df_marked.at[idx, '名稱'] = f"❌ {company_name}"
                elif '📝' in validation_status:
                    df_marked.at[idx, '名稱'] = f"📝 {company_name}"
                elif '🔄' in validation_status:
                    df_marked.at[idx, '名稱'] = f"🔄 {company_name}"
                elif '⚠️ 驗證停用' in validation_status:
                    df_marked.at[idx, '名稱'] = f"⚠️ {company_name}"
                elif '⚠️' in validation_status:
                    df_marked.at[idx, '名稱'] = f"⚠️ {company_name}"
        
        if '品質評分' in df_marked.columns and '名稱' in df_marked.columns:
            for idx, row in df_marked.iterrows():
                quality_score = row.get('品質評分', 10)
                company_name = str(row.get('名稱', ''))
                
                if not any(marker in company_name for marker in ['🚫', '❌', '📝', '🔄', '⚠️']):
                    if quality_score <= 2.0:
                        df_marked.at[idx, '名稱'] = f"🔴 {company_name}"
        
        return df_marked

    def _calculate_system_health(self, detailed_df: pd.DataFrame) -> float:
        """🔧 v3.5.1 計算系統健康度指標"""
        if detailed_df.empty:
            return 0.0
        
        health_score = 100.0
        
        if '驗證狀態' in detailed_df.columns:
            validation_counts = detailed_df['驗證狀態'].value_counts()
            total_records = len(detailed_df)
            
            critical_issues = sum(count for status, count in validation_counts.items() 
                                if any(marker in str(status) for marker in ['❌', '🚫']))
            
            if critical_issues > 0:
                health_score -= (critical_issues / total_records) * 40
        
        if '品質評分' in detailed_df.columns:
            quality_scores = detailed_df['品質評分'].dropna()
            if not quality_scores.empty:
                avg_quality = quality_scores.mean()
                quality_health = (avg_quality / 10) * 60
                health_score = health_score * 0.4 + quality_health
        
        return max(0.0, min(100.0, health_score))

    def _ask_force_upload(self) -> bool:
        """詢問是否強制上傳"""
        return False

    def test_connection(self) -> bool:
        """測試 Google Sheets 連線"""
        try:
            if self._setup_connection():
                spreadsheet_info = self.spreadsheet.title
                print(f"✅ Google Sheets 連線成功: {spreadsheet_info}")
                return True
            else:
                print("❌ Google Sheets 連線失敗")
                return False
        except Exception as e:
            print(f"❌ Google Sheets 連線測試失敗: {e}")
            return False

    def _setup_connection(self) -> bool:
        """設定 Google Sheets 連線"""
        try:
            if not self.sheet_id:
                print("❌ 未設定 GOOGLE_SHEET_ID 環境變數")
                return False
            
            credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            if not credentials_json:
                print("❌ 未設定 GOOGLE_SHEETS_CREDENTIALS 環境變數")
                return False
            
            credentials_info = json.loads(credentials_json)
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(
                credentials_info, scopes=scopes
            )
            
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Google Sheets 連線設定失敗: {e}")
            return False

    def _upload_portfolio_summary(self, portfolio_df: pd.DataFrame) -> bool:
        """上傳投資組合摘要"""
        try:
            try:
                portfolio_worksheet = self.spreadsheet.worksheet("投資組合摘要")
            except gspread.WorksheetNotFound:
                print("📊 建立投資組合摘要工作表...")
                portfolio_worksheet = self.spreadsheet.add_worksheet(title="投資組合摘要", rows=1000, cols=20)
            
            portfolio_worksheet.clear()
            
            portfolio_df_clean = portfolio_df.copy()
            portfolio_df_clean = portfolio_df_clean.fillna('')
            
            if '代號' in portfolio_df_clean.columns:
                portfolio_df_clean['代號'] = portfolio_df_clean['代號'].apply(self._clean_stock_code)
            
            if '股票代號' in portfolio_df_clean.columns:
                portfolio_df_clean['股票代號'] = portfolio_df_clean['股票代號'].apply(self._clean_stock_code)
            
            numeric_columns = ['分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值', '品質評分']
            for col in numeric_columns:
                if col in portfolio_df_clean.columns:
                    portfolio_df_clean[col] = portfolio_df_clean[col].apply(self._format_numeric_value)
            
            headers = portfolio_df_clean.columns.tolist()
            data = portfolio_df_clean.values.tolist()
            
            data = [[self._ensure_json_compatible(cell) for cell in row] for row in data]
            
            portfolio_worksheet.update('A1', [headers])
            
            if data:
                portfolio_worksheet.update('A2', data)
            
            print("📊 投資組合摘要上傳完成")
            return True
            
        except Exception as e:
            print(f"❌ 投資組合摘要上傳失敗: {e}")
            return False

    def _upload_detailed_report(self, detailed_df: pd.DataFrame) -> bool:
        """上傳詳細報告"""
        try:
            try:
                detailed_worksheet = self.spreadsheet.worksheet("詳細報告")
            except gspread.WorksheetNotFound:
                print("📊 建立詳細報告工作表...")
                detailed_worksheet = self.spreadsheet.add_worksheet(title="詳細報告", rows=2000, cols=25)
            
            detailed_worksheet.clear()
            
            detailed_df_clean = detailed_df.copy()
            detailed_df_clean = detailed_df_clean.fillna('')
            
            if '代號' in detailed_df_clean.columns:
                detailed_df_clean['代號'] = detailed_df_clean['代號'].apply(self._clean_stock_code)
            
            if '股票代號' in detailed_df_clean.columns:
                detailed_df_clean['股票代號'] = detailed_df_clean['股票代號'].apply(self._clean_stock_code)
            
            numeric_columns = [
                '分析師數量', '目標價', '品質評分',
                '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
                '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
                '2027EPS最高值', '2027EPS最低值', '2027EPS平均值'
            ]
            for col in numeric_columns:
                if col in detailed_df_clean.columns:
                    detailed_df_clean[col] = detailed_df_clean[col].apply(self._format_numeric_value)
            
            headers = detailed_df_clean.columns.tolist()
            data = detailed_df_clean.values.tolist()
            
            data = [[self._ensure_json_compatible(cell) for cell in row] for row in data]
            
            detailed_worksheet.update('A1', [headers])
            
            if data:
                detailed_worksheet.update('A2', data)
            
            print("📊 詳細報告上傳完成")
            return True
            
        except Exception as e:
            print(f"❌ 詳細報告上傳失敗: {e}")
            return False

    def _format_numeric_value(self, value):
        """格式化數值，處理 NaN 和特殊值"""
        if pd.isna(value) or value is None:
            return ''
        
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return ''
            if isinstance(value, float):
                if value.is_integer():
                    return str(int(value))
                else:
                    return f"{value:.2f}"
            else:
                return str(value)
        
        return str(value)

    def _ensure_json_compatible(self, value):
        """確保值與 JSON 相容"""
        if pd.isna(value) or value is None:
            return ''
        
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return ''
            return str(value)
        
        str_value = str(value)
        if str_value.startswith("'"):
            str_value = str_value[1:]
        
        return str_value if str_value != '' else ''

    # 🆕 公用方法：手動生成驗證摘要 CSV
    def generate_validation_csv_only(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> str:
        """🆕 只生成驗證摘要 CSV，不上傳到 Google Sheets"""
        try:
            validation_data = self._generate_validation_summary_data(portfolio_df, detailed_df)
            csv_file = self._save_validation_summary_csv(validation_data)
            
            if csv_file:
                print(f"📊 驗證摘要 CSV 已生成: {csv_file}")
                print(f"💡 您可以手動將此 CSV 檔案上傳到 Google Sheets")
                return csv_file
            else:
                print("❌ 驗證摘要 CSV 生成失敗")
                return ""
                
        except Exception as e:
            print(f"❌ 生成驗證摘要 CSV 失敗: {e}")
            return ""


# 測試功能
if __name__ == "__main__":
    uploader = SheetsUploader()
    
    print("=== 🔒 v3.5.1 CSV 驗證摘要解決方案測試 ===")
    
    # 測試資料
    import pandas as pd
    
    test_detailed_data = [
        {
            '代號': '2330',
            '名稱': '台積電',
            '品質評分': 10.0,
            '狀態': '🟢 完整',
            '驗證狀態': '✅ 通過'
        },
        {
            '代號': '6462',
            '名稱': '神盾',
            '品質評分': 7.0,
            '狀態': '🟠 部分',
            '驗證狀態': '⚠️ 驗證停用'
        },
        {
            '代號': '1234',
            '名稱': '測試公司',
            '品質評分': 0.0,
            '狀態': '❌ 驗證失敗',
            '驗證狀態': '🚫 不在觀察名單'
        }
    ]
    
    detailed_df = pd.DataFrame(test_detailed_data)
    portfolio_df = pd.DataFrame([
        {'代號': '2330', '名稱': '台積電', '品質評分': 10.0},
        {'代號': '6462', '名稱': '神盾', '品質評分': 7.0}
    ])
    
    print("測試 1: 生成驗證摘要數據")
    validation_data = uploader._generate_validation_summary_data(portfolio_df, detailed_df)
    print(f"   生成的驗證摘要包含 {len(validation_data)} 行數據")
    print("   前幾行數據:")
    for i, row in validation_data.head().iterrows():
        print(f"     {row['項目']}: {row['數值']} - {row['說明']}")
    
    print("\n測試 2: 儲存 CSV 檔案")
    csv_file = uploader._save_validation_summary_csv(validation_data)
    if csv_file:
        print(f"   ✅ CSV 檔案已儲存: {csv_file}")
    else:
        print("   ❌ CSV 檔案儲存失敗")
    
    print("\n測試 3: 只生成 CSV 的方法")
    csv_only_file = uploader.generate_validation_csv_only(portfolio_df, detailed_df)
    if csv_only_file:
        print(f"   ✅ 只生成 CSV 成功: {csv_only_file}")
    
    print(f"\n🎉 CSV 驗證摘要解決方案測試完成!")
    print(f"✅ 生成詳細的驗證統計 CSV")
    print(f"✅ 可選擇性上傳到 Google Sheets (簡化版)")
    print(f"✅ 完全避免 columnWidth API 問題")
    print(f"✅ 提供手動上傳的 CSV 檔案")
    
    print(f"\n💡 使用方式:")
    print(f"1. CSV 檔案會自動生成在 data/reports/ 目錄")
    print(f"2. 可以手動將 CSV 檔案上傳到 Google Sheets")
    print(f"3. 或者讓系統嘗試簡化上傳（無格式設定）")
    print(f"4. 主要報告功能完全不受影響")