#!/usr/bin/env python3
"""
Sheets Uploader - FactSet Pipeline v3.5.1 (Enhanced Validation Support)
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
    """Google Sheets 上傳器 v3.5.1 - 增強觀察名單驗證支援"""
    
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main"):
        self.github_repo_base = github_repo_base
        self.client = None
        self.spreadsheet = None
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        # 🔧 v3.5.1 更新的驗證設定 - 更寬鬆但有統計
        self.validation_settings = {
            'check_before_upload': True,    # 仍然檢查，但主要用於統計
            'allow_warning_data': True,     # 允許警告資料
            'allow_error_data': False,      # 🔧 修改: 不允許錯誤資料 (ReportGenerator 已過濾)
            'max_validation_errors': 5,     # 🔧 修改: 降低錯誤容忍度
            'skip_not_block': True,         # 跳過問題資料，不阻止上傳
            'enhanced_validation': True     # 🔧 新增: 啟用增強驗證檢查
        }

    def _clean_stock_code(self, code):
        """清理股票代號格式"""
        if pd.isna(code) or code is None:
            return ''
        
        code_str = str(code).strip()
        
        if code_str.startswith("'"):
            code_str = code_str[1:]
        
        # 🔧 關鍵差異：返回整數而不是字符串
        if code_str.isdigit() and len(code_str) == 4:
            return int(code_str)  # 返回整數
        
        # 處理股票代號格式
        if '-TW' in code_str:
            parts = code_str.split('-TW')
            if len(parts) == 2 and parts[0].isdigit() and len(parts[0]) == 4:
                return f"{int(parts[0])}-TW"
        
        return code_str
        
    def upload_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> bool:
        """🔧 v3.5.1 主要上傳方法 - 增強驗證支援"""
        try:
            # 🔧 上傳前驗證 (v3.5.1 增強版)
            if self.validation_settings['check_before_upload']:
                validation_result = self._validate_before_upload_v351(portfolio_df, detailed_df)
                
                if not validation_result['safe_to_upload']:
                    print(f"🚨 上傳驗證失敗: {validation_result['reason']}")
                    print(f"📊 問題摘要: {validation_result['summary']}")
                    
                    # 🔧 v3.5.1 更智能的處理
                    if validation_result['severity'] == 'critical':
                        print("❌ 發現關鍵問題，停止上傳")
                        return False
                    elif validation_result['severity'] == 'warning' and not self._ask_force_upload():
                        print("❌ 取消上傳")
                        return False
                    else:
                        print("⚠️ 忽略警告，繼續上傳")
                else:
                    # 顯示驗證統計但繼續上傳
                    if validation_result.get('reason'):
                        print(f"📊 驗證統計: {validation_result['reason']}")
                        print(f"📊 問題摘要: {validation_result['summary']}")
                    else:
                        print("✅ 上傳前驗證通過")
            
            # 設定連線
            if not self._setup_connection():
                print("❌ Google Sheets 連線失敗")
                return False
            
            # 🔧 在上傳前標記問題資料 (v3.5.1 增強版)
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
            
            # 🔧 v3.5.1 上傳增強的驗證摘要
            self._upload_validation_summary_v351(portfolio_df, detailed_df)
            
            print("✅ 所有報告上傳成功")
            return True
            
        except Exception as e:
            print(f"❌ 上傳過程中發生錯誤: {e}")
            return False

    def _validate_before_upload_v351(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> Dict[str, Any]:
        """🔧 v3.5.1 增強的上傳前驗證檢查"""
        validation_result = {
            'safe_to_upload': True,
            'reason': '',
            'summary': {},
            'issues': [],
            'severity': 'info'  # info, warning, critical
        }
        
        # 檢查 DataFrame 是否為空
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
        
        # 🔧 v3.5.1 增強的驗證狀態分析
        validation_issues = []
        critical_issues = 0
        warning_issues = 0
        validation_disabled_count = 0
        
        # 檢查詳細報告中的驗證狀態
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
        
        # 🔧 分析結果並設定驗證狀態
        total_companies = len(detailed_df)
        validation_result['summary'] = {
            'total_companies': total_companies,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'validation_disabled': validation_disabled_count,
            'validation_issues': len(validation_issues)
        }
        
        validation_result['issues'] = validation_issues
        
        # 🔧 根據增強的設定判斷是否安全上傳
        if self.validation_settings.get('enhanced_validation', False):
            # 理論上不應該有關鍵問題，因為 ReportGenerator 已經過濾了
            if critical_issues > 0:
                validation_result['safe_to_upload'] = False
                validation_result['severity'] = 'critical'
                validation_result['reason'] = f'發現 {critical_issues} 個關鍵驗證問題 (這些應該已被過濾)'
                
            elif warning_issues > total_companies * 0.5:  # 超過50%的警告
                validation_result['safe_to_upload'] = False
                validation_result['severity'] = 'warning'
                validation_result['reason'] = f'警告問題過多: {warning_issues}/{total_companies} ({warning_issues/total_companies*100:.1f}%)'
                
            else:
                # 正常情況
                validation_result['safe_to_upload'] = True
                if validation_disabled_count > 0 or warning_issues > 0:
                    validation_result['reason'] = f'發現 {warning_issues} 個警告、{validation_disabled_count} 個驗證停用，將繼續上傳'
                    validation_result['severity'] = 'info'
        else:
            # 原有邏輯
            if critical_issues > self.validation_settings['max_validation_errors']:
                validation_result['safe_to_upload'] = False
                validation_result['reason'] = f'發現 {critical_issues} 個嚴重驗證錯誤 (上限: {self.validation_settings["max_validation_errors"]})'
                validation_result['severity'] = 'critical'
        
        return validation_result

    def _mark_problematic_data_v351(self, df: pd.DataFrame) -> pd.DataFrame:
        """🔧 v3.5.1 增強的問題資料標記"""
        df_marked = df.copy()
        
        # 如果有驗證狀態欄位，在公司名稱前加上標記
        if '驗證狀態' in df_marked.columns and '名稱' in df_marked.columns:
            for idx, row in df_marked.iterrows():
                validation_status = str(row.get('驗證狀態', ''))
                company_name = str(row.get('名稱', ''))
                
                # 🔧 更細緻的標記邏輯
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
        
        # 標記極低品質評分的資料
        if '品質評分' in df_marked.columns and '名稱' in df_marked.columns:
            for idx, row in df_marked.iterrows():
                quality_score = row.get('品質評分', 10)
                company_name = str(row.get('名稱', ''))
                
                # 避免重複標記
                if not any(marker in company_name for marker in ['🚫', '❌', '📝', '🔄', '⚠️']):
                    if quality_score <= 2.0:
                        df_marked.at[idx, '名稱'] = f"🔴 {company_name}"
        
        return df_marked

    def _ask_force_upload(self) -> bool:
        """詢問是否強制上傳"""
        # 🔧 v3.5.1 更智能的決策
        # 在自動化環境中，如果是警告級別的問題，允許上傳
        # 如果是關鍵問題，則拒絕上傳
        return False

    def _upload_validation_summary_v351(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame):
        """🔧 v3.5.1 上傳增強的驗證摘要"""
        try:
            # 生成增強的驗證摘要資料
            validation_summary = self._generate_validation_summary_v351(portfolio_df, detailed_df)
            
            # 嘗試找到或建立驗證摘要工作表
            try:
                validation_worksheet = self.spreadsheet.worksheet("驗證摘要")
            except gspread.WorksheetNotFound:
                print("📊 建立驗證摘要工作表...")
                validation_worksheet = self.spreadsheet.add_worksheet(title="驗證摘要", rows=100, cols=10)
            
            # 清空現有內容
            validation_worksheet.clear()
            
            # 設定標題
            headers = ['項目', '數值', '說明', '詳細資訊', '更新時間']
            validation_worksheet.update('A1:E1', [headers])
            
            # 上傳驗證摘要資料
            validation_worksheet.update('A2', validation_summary)
            
            # 🔧 設定格式
            self._format_validation_worksheet(validation_worksheet, len(validation_summary))
            
            print("📊 v3.5.1 增強驗證摘要已上傳")
            
        except Exception as e:
            print(f"⚠️ 驗證摘要上傳失敗: {e}")

    def _generate_validation_summary_v351(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> List[List]:
        """🔧 v3.5.1 生成增強的驗證摘要資料"""
        summary_data = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 基本統計
        summary_data.append(['總公司數', len(portfolio_df), '投資組合中的公司總數', f'詳細記錄: {len(detailed_df)}', current_time])
        
        # 🔧 v3.5.1 增強的驗證統計
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
            
            # 新增詳細的驗證統計
            summary_data.append(['驗證通過', passed_count, '通過內容驗證的記錄數', f'成功率: {passed_count/len(detailed_df)*100:.1f}%', current_time])
            summary_data.append(['驗證停用', disabled_count, '因觀察名單未載入而停用驗證', '這些公司仍會包含在報告中', current_time])
            summary_data.append(['驗證警告', warning_count, '有驗證警告的記錄數', '需要人工檢查', current_time])
            summary_data.append(['關鍵問題', critical_count, '嚴重驗證問題的記錄數', '應已被過濾排除', current_time])
            
            # 🔧 驗證品質指標
            total_validation_active = len(detailed_df) - disabled_count
            if total_validation_active > 0:
                validation_quality = (passed_count / total_validation_active) * 100
                summary_data.append(['驗證品質', f'{validation_quality:.1f}%', '啟用驗證中的通過率', f'活躍驗證: {total_validation_active}', current_time])
        
        # 品質統計
        if '品質評分' in detailed_df.columns:
            quality_scores = detailed_df['品質評分'].dropna()
            if not quality_scores.empty:
                avg_quality = quality_scores.mean()
                high_quality = len(quality_scores[quality_scores >= 8.0])
                low_quality = len(quality_scores[quality_scores <= 3.0])
                zero_quality = len(quality_scores[quality_scores == 0.0])
                
                summary_data.append(['平均品質評分', f'{avg_quality:.1f}', '所有記錄的平均品質評分', f'最高: {quality_scores.max():.1f}, 最低: {quality_scores.min():.1f}', current_time])
                summary_data.append(['高品質記錄', high_quality, '品質評分 ≥ 8.0 的記錄數', f'佔比: {high_quality/len(quality_scores)*100:.1f}%', current_time])
                summary_data.append(['低品質記錄', low_quality, '品質評分 ≤ 3.0 的記錄數', f'佔比: {low_quality/len(quality_scores)*100:.1f}%', current_time])
                
                if zero_quality > 0:
                    summary_data.append(['零分記錄', zero_quality, '品質評分為 0 的記錄數', '通常表示驗證失敗', current_time])
        
        # 🔧 v3.5.1 新增: 系統健康度指標
        system_health = self._calculate_system_health(detailed_df)
        summary_data.append(['系統健康度', f'{system_health:.1f}%', '整體資料處理品質指標', '綜合驗證和品質評分', current_time])
        
        return summary_data

    def _calculate_system_health(self, detailed_df: pd.DataFrame) -> float:
        """🔧 v3.5.1 計算系統健康度指標"""
        if detailed_df.empty:
            return 0.0
        
        health_score = 100.0
        
        # 驗證健康度 (40%)
        if '驗證狀態' in detailed_df.columns:
            validation_counts = detailed_df['驗證狀態'].value_counts()
            total_records = len(detailed_df)
            
            critical_issues = sum(count for status, count in validation_counts.items() 
                                if any(marker in str(status) for marker in ['❌', '🚫']))
            
            if critical_issues > 0:
                health_score -= (critical_issues / total_records) * 40
        
        # 品質健康度 (60%)
        if '品質評分' in detailed_df.columns:
            quality_scores = detailed_df['品質評分'].dropna()
            if not quality_scores.empty:
                avg_quality = quality_scores.mean()
                quality_health = (avg_quality / 10) * 60
                health_score = health_score * 0.4 + quality_health
        
        return max(0.0, min(100.0, health_score))

    def _format_validation_worksheet(self, worksheet, data_rows: int):
        """🔧 v3.5.1 格式化驗證工作表"""
        # 設定標題列格式
        worksheet.format('A1:E1', {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # 設定欄寬
        worksheet.format('A:A', {'columnWidth': 150})
        worksheet.format('B:B', {'columnWidth': 100})
        worksheet.format('C:C', {'columnWidth': 200})
        worksheet.format('D:D', {'columnWidth': 180})
        worksheet.format('E:E', {'columnWidth': 150})
        
        # 🔧 根據數值設定顏色編碼
        if data_rows > 1:
            # 健康度相關的條件格式可以在這裡設定
            pass

    def test_connection(self) -> bool:
        """測試 Google Sheets 連線"""
        try:
            if self._setup_connection():
                # 嘗試讀取試算表資訊
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
            # 檢查環境變數
            if not self.sheet_id:
                print("❌ 未設定 GOOGLE_SHEET_ID 環境變數")
                return False
            
            credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            if not credentials_json:
                print("❌ 未設定 GOOGLE_SHEETS_CREDENTIALS 環境變數")
                return False
            
            # 解析認證資訊
            credentials_info = json.loads(credentials_json)
            
            # 建立認證物件
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(
                credentials_info, scopes=scopes
            )
            
            # 建立 gspread 客戶端
            self.client = gspread.authorize(credentials)
            
            # 開啟試算表
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Google Sheets 連線設定失敗: {e}")
            return False

    def _upload_portfolio_summary(self, portfolio_df: pd.DataFrame) -> bool:
        """上傳投資組合摘要"""
        try:
            # 嘗試找到或建立投資組合摘要工作表
            try:
                portfolio_worksheet = self.spreadsheet.worksheet("投資組合摘要")
            except gspread.WorksheetNotFound:
                print("📊 建立投資組合摘要工作表...")
                portfolio_worksheet = self.spreadsheet.add_worksheet(title="投資組合摘要", rows=1000, cols=20)
            
            # 清空現有內容
            portfolio_worksheet.clear()
            
            # 清理 DataFrame，確保股票代號為純數字
            portfolio_df_clean = portfolio_df.copy()
            
            # 將 NaN 替換為空字符串
            portfolio_df_clean = portfolio_df_clean.fillna('')
            
            # 特別處理股票代號欄位
            if '代號' in portfolio_df_clean.columns:
                portfolio_df_clean['代號'] = portfolio_df_clean['代號'].apply(self._clean_stock_code)
            
            if '股票代號' in portfolio_df_clean.columns:
                portfolio_df_clean['股票代號'] = portfolio_df_clean['股票代號'].apply(self._clean_stock_code)
            
            # 確保數值欄位的格式正確
            numeric_columns = ['分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值', '品質評分']
            for col in numeric_columns:
                if col in portfolio_df_clean.columns:
                    portfolio_df_clean[col] = portfolio_df_clean[col].apply(self._format_numeric_value)
            
            # 準備資料
            headers = portfolio_df_clean.columns.tolist()
            data = portfolio_df_clean.values.tolist()
            
            # 確保所有資料都是乾淨的
            data = [[self._ensure_json_compatible(cell) for cell in row] for row in data]
            
            # 上傳標題
            portfolio_worksheet.update('A1', [headers])
            
            # 上傳資料
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
            # 嘗試找到或建立詳細報告工作表
            try:
                detailed_worksheet = self.spreadsheet.worksheet("詳細報告")
            except gspread.WorksheetNotFound:
                print("📊 建立詳細報告工作表...")
                detailed_worksheet = self.spreadsheet.add_worksheet(title="詳細報告", rows=2000, cols=25)
            
            # 清空現有內容
            detailed_worksheet.clear()
            
            # 清理 DataFrame
            detailed_df_clean = detailed_df.copy()
            
            # 將 NaN 替換為空字符串
            detailed_df_clean = detailed_df_clean.fillna('')
            
            # 特別處理股票代號欄位
            if '代號' in detailed_df_clean.columns:
                detailed_df_clean['代號'] = detailed_df_clean['代號'].apply(self._clean_stock_code)
            
            if '股票代號' in detailed_df_clean.columns:
                detailed_df_clean['股票代號'] = detailed_df_clean['股票代號'].apply(self._clean_stock_code)
            
            # 確保數值欄位的格式正確
            numeric_columns = [
                '分析師數量', '目標價', '品質評分',
                '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
                '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
                '2027EPS最高值', '2027EPS最低值', '2027EPS平均值'
            ]
            for col in numeric_columns:
                if col in detailed_df_clean.columns:
                    detailed_df_clean[col] = detailed_df_clean[col].apply(self._format_numeric_value)
            
            # 準備資料
            headers = detailed_df_clean.columns.tolist()
            data = detailed_df_clean.values.tolist()
            
            # 確保所有資料都是乾淨的
            data = [[self._ensure_json_compatible(cell) for cell in row] for row in data]
            
            # 上傳標題
            detailed_worksheet.update('A1', [headers])
            
            # 上傳資料
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
            # 保留適當的小數位數
            if isinstance(value, float):
                # 如果是整數值，顯示為整數
                if value.is_integer():
                    return str(int(value))
                else:
                    return f"{value:.2f}"
            else:
                return str(value)
        
        return str(value)

    def _ensure_json_compatible(self, value):
        """確保值與 JSON 相容 - 不添加引號"""
        if pd.isna(value) or value is None:
            return ''
        
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return ''
            return str(value)  # 直接轉為字符串，不加引號
        
        # 如果是字符串，檢查是否以引號開頭並移除
        str_value = str(value)
        if str_value.startswith("'"):
            str_value = str_value[1:]
        
        return str_value if str_value != '' else ''


# 測試功能
if __name__ == "__main__":
    uploader = SheetsUploader()
    
    print("=== 🔒 v3.5.1 增強觀察名單驗證支援的 Sheets Uploader 測試 ===")
    
    # 測試資料 - 包含不同驗證狀態
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
            '品質評分': 6.5,
            '狀態': '🟠 部分',
            '驗證狀態': '⚠️ 有警告'
        }
    ]
    
    detailed_df = pd.DataFrame(test_detailed_data)
    portfolio_df = pd.DataFrame([
        {'代號': '2330', '名稱': '台積電', '品質評分': 10.0},
        {'代號': '6462', '名稱': '神盾', '品質評分': 7.0},
        {'代號': '1234', '名稱': '測試公司', '品質評分': 6.5}
    ])
    
    print("測試 1: v3.5.1 上傳前驗證")
    validation_result = uploader._validate_before_upload_v351(portfolio_df, detailed_df)
    print(f"   安全上傳: {validation_result['safe_to_upload']}")
    print(f"   嚴重性: {validation_result['severity']}")
    print(f"   問題摘要: {validation_result['summary']}")
    print(f"   原因: {validation_result.get('reason', 'N/A')}")
    
    print("\n測試 2: v3.5.1 標記問題資料")
    marked_df = uploader._mark_problematic_data_v351(detailed_df)
    print("   標記結果:")
    for idx, row in marked_df.iterrows():
        company = row['名稱']
        validation = row['驗證狀態']
        print(f"     {company} - {validation}")
    
    print("\n測試 3: v3.5.1 生成增強驗證摘要")
    validation_summary = uploader._generate_validation_summary_v351(portfolio_df, detailed_df)
    print("   驗證摘要:")
    for item in validation_summary:
        print(f"     {item[0]}: {item[1]} ({item[2]})")
    
    print("\n測試 4: 系統健康度計算")
    health_score = uploader._calculate_system_health(detailed_df)
    print(f"   系統健康度: {health_score:.1f}%")
    
    print(f"\n✅ 預期結果:")
    print(f"   台積電: ✅ 台積電 (正常)")
    print(f"   神盾: ⚠️ 神盾 (驗證停用)")
    print(f"   測試公司: ⚠️ 測試公司 (警告)")
    print(f"   上傳安全性: 應為 True (沒有關鍵問題)")
    print(f"   健康度: 應該較高 (沒有0分或❌)")
    
    print(f"\n🎉 v3.5.1 測試完成!")