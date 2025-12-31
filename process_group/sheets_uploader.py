#!/usr/bin/env python3
"""
Sheets Uploader - FactSet Pipeline v3.6.1 (修復版)
修復 columnWidth API 錯誤，增加 CSV-only 模式
"""

import os
import gspread
import pandas as pd
import math
import time
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
    """Google Sheets 上傳器 v3.6.1 - 修復版本 + CSV-only 模式"""
    
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main"):
        self.github_repo_base = github_repo_base
        self.client = None
        self.spreadsheet = None
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        # 🔧 v3.6.1 更新的驗證設定
        self.validation_settings = {
            'check_before_upload': True,
            'allow_warning_data': True,
            'allow_error_data': False,
            'max_validation_errors': 5,
            'skip_not_block': True,
            'enhanced_validation': True,
            'generate_validation_csv': True,
            'upload_validation_to_sheets': True,  # 🔧 默認關閉 Sheets 上傳
            'csv_output_dir': 'data/reports',
            'csv_only_mode': False  # 🆕 新增 CSV-only 模式
        }
        
        # 🆕 v3.6.1 工作表名稱
        self.worksheet_names = {
            'portfolio': '投資組合摘要',
            'detailed': '詳細報告',
            'validation': '驗證摘要',  
            'keywords': '查詢模式摘要',
            'watchlist': '觀察名單摘要'  # 新增
        }
        
        # 確保輸出目錄存在
        os.makedirs(self.validation_settings['csv_output_dir'], exist_ok=True)
        
        # 🆕 API 限制設定
        self.api_settings = {
            'max_retries': 3,
            'retry_delay': 2,  # 秒
            'batch_size': 100,  # 每次批量操作的行數
            'rate_limit_delay': 0.5  # API 調用間隔
        }

    def upload_all_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                          keyword_df: pd.DataFrame = None, watchlist_df: pd.DataFrame = None, 
                          csv_only=False) -> bool:
        """🔧 v3.6.1 主要上傳方法 - 支援 CSV-only 模式"""
        
        # 🆕 如果啟用 CSV-only 模式，只生成 CSV
        if csv_only or self.validation_settings.get('csv_only_mode', False):
            return self._csv_only_mode(portfolio_df, detailed_df, keyword_df, watchlist_df)
        
        try:
            # 上傳前驗證
            if self.validation_settings['check_before_upload']:
                validation_result = self._validate_before_upload_v361(portfolio_df, detailed_df, watchlist_df)
                
                if not validation_result['safe_to_upload']:
                    print(f"🚨 上傳驗證失敗: {validation_result['reason']}")
                    print(f"📊 問題摘要: {validation_result['summary']}")
                    
                    if validation_result['severity'] == 'critical':
                        print("❌ 發現關鍵問題，改用 CSV-only 模式")
                        return self._csv_only_mode(portfolio_df, detailed_df, keyword_df, watchlist_df)
                    elif validation_result['severity'] == 'warning':
                        print("⚠️ 發現警告，建議使用 CSV-only 模式")
                        return self._csv_only_mode(portfolio_df, detailed_df, keyword_df, watchlist_df)
                else:
                    if validation_result.get('reason'):
                        print(f"📊 驗證統計: {validation_result['reason']}")
                        print(f"📊 問題摘要: {validation_result['summary']}")
                    else:
                        print("✅ 上傳前驗證通過")
            
            # 🔧 增加 API 限制檢查
            if not self._check_api_availability():
                print("⚠️ Google Sheets API 可能接近限制，改用 CSV-only 模式")
                return self._csv_only_mode(portfolio_df, detailed_df, keyword_df, watchlist_df)
            
            # 設定連線
            if not self._setup_connection():
                print("❌ Google Sheets 連線失敗，改用 CSV-only 模式")
                return self._csv_only_mode(portfolio_df, detailed_df, keyword_df, watchlist_df)
            
            # 標記問題資料
            portfolio_df_marked = self._mark_problematic_data_v361(portfolio_df)
            detailed_df_marked = self._mark_problematic_data_v361(detailed_df)
            
            success_count = 0
            total_uploads = 4  # 基本上傳數量
            
            # 上傳投資組合摘要
            if self._upload_portfolio_summary_safe(portfolio_df_marked):
                success_count += 1
                print("📊 投資組合摘要上傳成功")
            else:
                print("❌ 投資組合摘要上傳失敗")
            
            # 上傳詳細報告
            if self._upload_detailed_report_safe(detailed_df_marked):
                success_count += 1
                print("📊 詳細報告上傳成功")
            else:
                print("❌ 詳細報告上傳失敗")
            
            # 上傳關鍵字報告
            if keyword_df is not None and not keyword_df.empty:
                if self._upload_keyword_summary_safe(keyword_df):
                    success_count += 1
                    print("📊 關鍵字報告上傳成功")
                else:
                    print("⚠️ 關鍵字報告上傳失敗")
            
            # 上傳觀察名單報告
            if watchlist_df is not None and not watchlist_df.empty:
                if self._upload_watchlist_summary_safe(watchlist_df):
                    success_count += 1
                    print("📊 觀察名單報告上傳成功")
                else:
                    print("⚠️ 觀察名單報告上傳失敗")
            
            # 🔧 同時生成 CSV 備份
            self._generate_csv_backup(portfolio_df, detailed_df, keyword_df, watchlist_df)
            
            # 處理驗證摘要
            self._handle_validation_summary_v361_safe(portfolio_df, detailed_df, watchlist_df)
            
            # 評估上傳成功率
            success_rate = success_count / max(total_uploads, 1)
            if success_rate >= 0.5:
                print(f"✅ 上傳完成 (成功率: {success_rate:.1%})")
                return True
            else:
                print(f"⚠️ 部分上傳失敗 (成功率: {success_rate:.1%})")
                print("💡 建議使用生成的 CSV 檔案")
                return False
            
        except Exception as e:
            print(f"❌ 上傳過程中發生錯誤: {e}")
            print("🔄 改用 CSV-only 模式...")
            return self._csv_only_mode(portfolio_df, detailed_df, keyword_df, watchlist_df)

    def _csv_only_mode(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                      keyword_df: pd.DataFrame = None, watchlist_df: pd.DataFrame = None) -> bool:
        """🆕 CSV-only 模式 - 完全避免 Google Sheets API"""
        try:
            print("📁 啟動 CSV-only 模式...")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_files = {}
            
            # 1. 投資組合摘要 CSV
            portfolio_path = os.path.join(self.validation_settings['csv_output_dir'], f'portfolio_summary_{timestamp}.csv')
            portfolio_latest = os.path.join(self.validation_settings['csv_output_dir'], 'factset_portfolio_summary_latest.csv')
            
            portfolio_df_clean = portfolio_df.fillna('')
            portfolio_df_clean.to_csv(portfolio_path, index=False, encoding='utf-8-sig')
            portfolio_df_clean.to_csv(portfolio_latest, index=False, encoding='utf-8-sig')
            
            saved_files['portfolio'] = portfolio_path
            print(f"✅ 投資組合摘要 CSV: {os.path.basename(portfolio_path)}")
            
            # 2. 詳細報告 CSV
            detailed_path = os.path.join(self.validation_settings['csv_output_dir'], f'detailed_report_{timestamp}.csv')
            detailed_latest = os.path.join(self.validation_settings['csv_output_dir'], 'factset_detailed_report_latest.csv')
            
            detailed_df_clean = detailed_df.fillna('')
            detailed_df_clean.to_csv(detailed_path, index=False, encoding='utf-8-sig')
            detailed_df_clean.to_csv(detailed_latest, index=False, encoding='utf-8-sig')
            
            saved_files['detailed'] = detailed_path
            print(f"✅ 詳細報告 CSV: {os.path.basename(detailed_path)}")
            
            # 3. 關鍵字/查詢模式報告 CSV
            if keyword_df is not None and not keyword_df.empty:
                # 檢查是否為查詢模式報告
                if len(keyword_df.columns) > 0 and keyword_df.columns[0] == 'Query pattern':
                    keyword_path = os.path.join(self.validation_settings['csv_output_dir'], 'factset_query_pattern_summary_latest.csv')
                    report_type = "查詢模式統計"
                else:
                    keyword_path = os.path.join(self.validation_settings['csv_output_dir'], 'keyword_summary_latest.csv')
                    report_type = "關鍵字統計"

                keyword_df_clean = keyword_df.fillna('')
                keyword_df_clean.to_csv(keyword_path, index=False, encoding='utf-8-sig')

                saved_files['keyword'] = keyword_path
                print(f"✅ {report_type} CSV: {os.path.basename(keyword_path)}")
            
            # 4. 觀察名單報告 CSV
            if watchlist_df is not None and not watchlist_df.empty:
                watchlist_path = os.path.join(self.validation_settings['csv_output_dir'], 'watchlist_summary_latest.csv')

                watchlist_df_clean = watchlist_df.fillna('')
                watchlist_df_clean.to_csv(watchlist_path, index=False, encoding='utf-8-sig')

                saved_files['watchlist'] = watchlist_path
                print(f"✅ 觀察名單統計 CSV: {os.path.basename(watchlist_path)}")

            # 5. 生成驗證摘要 CSV
            validation_data = self._generate_validation_summary_data_v361(portfolio_df, detailed_df, watchlist_df)
            validation_path = os.path.join(self.validation_settings['csv_output_dir'], 'validation_summary_latest.csv')

            validation_data.to_csv(validation_path, index=False, encoding='utf-8-sig')

            saved_files['validation'] = validation_path
            print(f"✅ 驗證摘要 CSV: {os.path.basename(validation_path)}")
            
            # 6. 生成使用指南
            self._generate_usage_guide(saved_files, timestamp)
            
            print(f"\n🎉 CSV-only 模式完成！")
            print(f"📁 所有檔案位於: {os.path.abspath(self.validation_settings['csv_output_dir'])}")
            print(f"📋 使用指南: generation_guide_latest.md")
            print(f"\n💡 手動上傳建議:")
            print(f"   1. 開啟 Google Sheets")
            print(f"   2. 匯入各個 *_latest.csv 檔案")
            print(f"   3. 每個 CSV 建立為一個工作表")
            
            return True
            
        except Exception as e:
            print(f"❌ CSV-only 模式失敗: {e}")
            return False

    def _upload_watchlist_summary_safe(self, watchlist_df: pd.DataFrame) -> bool:
        """🔧 安全版本的觀察名單上傳 - 修復 columnWidth 問題"""
        try:
            # 建立或取得觀察名單工作表
            try:
                worksheet = self.spreadsheet.worksheet(self.worksheet_names['watchlist'])
            except gspread.WorksheetNotFound:
                print("📊 建立觀察名單工作表...")
                worksheet = self.spreadsheet.add_worksheet(
                    title=self.worksheet_names['watchlist'], 
                    rows=1000, 
                    cols=15
                )
            
            # 清空現有資料
            worksheet.clear()
            time.sleep(self.api_settings['rate_limit_delay'])
            
            # 清理資料
            watchlist_df_clean = watchlist_df.copy()
            watchlist_df_clean = watchlist_df_clean.fillna('')
            
            # 確保公司代號格式正確
            if '公司代號' in watchlist_df_clean.columns:
                watchlist_df_clean['公司代號'] = watchlist_df_clean['公司代號'].apply(self._clean_stock_code)
            
            # 格式化數值欄位
            numeric_columns = ['MD檔案數量', '平均品質評分', '最高品質評分', '搜尋關鍵字數量', '關鍵字平均品質']
            for col in numeric_columns:
                if col in watchlist_df_clean.columns:
                    watchlist_df_clean[col] = watchlist_df_clean[col].apply(self._format_numeric_value)
            
            # 準備上傳資料
            headers = watchlist_df_clean.columns.tolist()
            data = watchlist_df_clean.values.tolist()
            
            # 確保所有資料都是 JSON 相容的
            data = [[self._ensure_json_compatible(cell) for cell in row] for row in data]
            
            # 上傳標題
            worksheet.update('A1', [headers])
            time.sleep(self.api_settings['rate_limit_delay'])
            
            # 分批上傳資料
            if data:
                batch_size = self.api_settings['batch_size']
                for i in range(0, len(data), batch_size):
                    batch_data = data[i:i + batch_size]
                    start_row = i + 2  # +2 因為標題佔第1行，資料從第2行開始
                    range_name = f'A{start_row}'
                    
                    worksheet.update(range_name, batch_data)
                    time.sleep(self.api_settings['rate_limit_delay'])
                    
                    if i + batch_size < len(data):
                        print(f"   已上傳 {i + batch_size}/{len(data)} 行...")
            
            # 🔧 修復後的格式設定 - 不使用 columnWidth
            self._format_watchlist_worksheet_fixed(worksheet, len(watchlist_df_clean))
            
            print("📊 觀察名單報告上傳完成")
            return True
            
        except Exception as e:
            print(f"❌ 觀察名單報告上傳失敗: {e}")
            return False

    def _format_watchlist_worksheet_fixed(self, worksheet, data_rows: int):
        """🔧 修復版本：格式化觀察名單工作表 - 不使用 columnWidth"""
        try:
            # 設定標題列格式
            worksheet.format('A1:L1', {
                'backgroundColor': {'red': 0.2, 'green': 0.7, 'blue': 0.9},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            time.sleep(self.api_settings['rate_limit_delay'])
            
            if data_rows > 0:
                try:
                    # 設定數值欄位格式 - 分批處理
                    ranges_to_format = [
                        ('E:F', {'numberFormat': {'type': 'NUMBER', 'pattern': '0.00'}}),  # 品質評分欄位
                        ('I:I', {'numberFormat': {'type': 'NUMBER', 'pattern': '0.00'}})   # 關鍵字平均品質
                    ]
                    
                    for range_name, format_dict in ranges_to_format:
                        try:
                            worksheet.format(range_name, format_dict)
                            time.sleep(self.api_settings['rate_limit_delay'])
                        except Exception as format_error:
                            print(f"⚠️ 設定 {range_name} 格式失敗: {format_error}")
                
                except Exception as number_format_error:
                    print(f"⚠️ 設定數值格式失敗: {number_format_error}")
                
                # 🔧 移除 columnWidth 設定，改用簡單的文字格式
                try:
                    # 設定文字對齊
                    worksheet.format('A:A', {'horizontalAlignment': 'CENTER'})   # 公司代號置中
                    time.sleep(self.api_settings['rate_limit_delay'])
                    
                    worksheet.format('B:B', {'horizontalAlignment': 'LEFT'})     # 公司名稱左對齊
                    time.sleep(self.api_settings['rate_limit_delay'])
                    
                except Exception as align_error:
                    print(f"⚠️ 設定對齊格式失敗: {align_error}")
                    
        except Exception as e:
            print(f"⚠️ 觀察名單工作表格式設定失敗: {e}")

    def _upload_portfolio_summary_safe(self, portfolio_df: pd.DataFrame) -> bool:
        """安全版本的投資組合摘要上傳"""
        return self._upload_with_retry("投資組合摘要", portfolio_df, self._upload_portfolio_summary)

    def _upload_detailed_report_safe(self, detailed_df: pd.DataFrame) -> bool:
        """安全版本的詳細報告上傳"""
        return self._upload_with_retry("詳細報告", detailed_df, self._upload_detailed_report)

    def _upload_keyword_summary_safe(self, keyword_df: pd.DataFrame) -> bool:
        """安全版本的關鍵字報告上傳"""
        return self._upload_with_retry("關鍵字報告", keyword_df, self._upload_keyword_summary)

    def _upload_with_retry(self, report_name: str, df: pd.DataFrame, upload_func) -> bool:
        """通用的重試上傳方法"""
        for attempt in range(self.api_settings['max_retries']):
            try:
                result = upload_func(df)
                if result:
                    return True
                else:
                    print(f"⚠️ {report_name} 上傳嘗試 {attempt + 1} 失敗")
                    
            except Exception as e:
                print(f"⚠️ {report_name} 上傳嘗試 {attempt + 1} 錯誤: {e}")
                
                # 檢查是否為 API 限制錯誤
                if "quota exceeded" in str(e).lower() or "429" in str(e):
                    print(f"🚫 API 限制，停止重試 {report_name}")
                    return False
                
                if attempt < self.api_settings['max_retries'] - 1:
                    wait_time = self.api_settings['retry_delay'] * (attempt + 1)
                    print(f"⏳ 等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
        
        print(f"❌ {report_name} 所有重試失敗")
        return False

    def _check_api_availability(self) -> bool:
        """檢查 API 可用性"""
        try:
            if not self.sheet_id:
                return False
            
            # 簡單的連線測試
            if self.client is None:
                return self._setup_connection()
            
            return True
            
        except Exception as e:
            if "quota exceeded" in str(e).lower() or "429" in str(e):
                return False
            return True

    def _generate_csv_backup(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                           keyword_df: pd.DataFrame = None, watchlist_df: pd.DataFrame = None):
        """生成 CSV 備份檔案"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.validation_settings['csv_output_dir'], 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # 備份主要報告
            portfolio_df.to_csv(os.path.join(backup_dir, f'portfolio_backup_{timestamp}.csv'), 
                               index=False, encoding='utf-8-sig')
            detailed_df.to_csv(os.path.join(backup_dir, f'detailed_backup_{timestamp}.csv'), 
                              index=False, encoding='utf-8-sig')
            
            if keyword_df is not None and not keyword_df.empty:
                keyword_df.to_csv(os.path.join(backup_dir, f'keyword_backup_{timestamp}.csv'), 
                                 index=False, encoding='utf-8-sig')
            
            if watchlist_df is not None and not watchlist_df.empty:
                watchlist_df.to_csv(os.path.join(backup_dir, f'watchlist_backup_{timestamp}.csv'), 
                                   index=False, encoding='utf-8-sig')
            
            print(f"💾 CSV 備份已生成: {backup_dir}")
            
        except Exception as e:
            print(f"⚠️ CSV 備份生成失敗: {e}")

    def _generate_usage_guide(self, saved_files: Dict[str, str], timestamp: str):
        """生成使用指南"""
        guide_content = f"""
# FactSet Pipeline v3.6.1 - CSV 報告使用指南
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
時間戳: {timestamp}

## 📁 生成的檔案清單

### 主要報告檔案
"""
        
        for report_type, file_path in saved_files.items():
            filename = os.path.basename(file_path)
            guide_content += f"- {report_type}: `{filename}`\n"
        
        guide_content += f"""

### 最新版本檔案 (無時間戳)
- `factset_portfolio_summary_latest.csv` - 投資組合摘要
- `factset_detailed_report_latest.csv` - 詳細報告
- `factset_query_pattern_summary_latest.csv` - 查詢模式統計 (如有)
- `watchlist_summary_latest.csv` - 觀察名單統計 (如有)
- `validation_summary_latest.csv` - 驗證摘要

## 🔧 Google Sheets 手動上傳步驟

### 方法 1: 檔案匯入
1. 開啟 Google Sheets
2. 建立新的試算表或開啟現有試算表
3. 點選「檔案」→「匯入」
4. 上傳 CSV 檔案
5. 選擇「建立新工作表」
6. 重複步驟 3-5 for 每個 CSV 檔案

### 方法 2: 複製貼上
1. 用 Excel 或文字編輯器開啟 CSV 檔案
2. 全選並複製內容
3. 在 Google Sheets 中建立新工作表
4. 貼上內容
5. 如果格式有問題，使用「資料」→「分欄」功能

## 📊 各報告檔案說明

### 投資組合摘要 (portfolio_summary_*.csv)
- **用途**: 每家公司的關鍵指標摘要
- **欄位**: 14 個欄位，包含代號、名稱、EPS 預測、品質評分等
- **適用**: 高階主管報告、快速概覽

### 詳細報告 (detailed_report_*.csv)
- **用途**: 所有記錄的完整詳細資訊
- **欄位**: 22 個欄位，包含所有 EPS 數據、驗證狀態、MD 檔案連結
- **適用**: 分析師深度分析、資料驗證

### 查詢模式統計 (query_pattern_summary_*.csv)
- **用途**: 搜尋查詢模式效果分析
- **欄位**: 10 個欄位，包含模式使用次數、品質評分、分類
- **適用**: 系統優化、搜尋策略改進

### 觀察名單統計 (watchlist_summary_*.csv)
- **用途**: 觀察名單公司處理狀態分析
- **欄位**: 12 個欄位，包含處理狀態、品質評分、關鍵字分析
- **適用**: 覆蓋率監控、優先處理規劃

### 驗證摘要 (validation_summary_*.csv)
- **用途**: 整體處理狀態和統計摘要
- **欄位**: 5 個欄位，包含統計項目、數值、說明
- **適用**: 系統健康度監控、處理品質評估

## 💡 使用建議

### Excel 分析
1. 使用 Excel 的樞紐分析表功能進行深度分析
2. 建立圖表視覺化呈現資料
3. 設定條件格式突出關鍵資訊

### 自動化處理
1. 可以寫程式定期處理 `*_latest.csv` 檔案
2. 建立監控儀表板讀取這些 CSV
3. 設定警報系統監控品質評分變化

### 資料整合
1. 使用 SQL 資料庫匯入這些 CSV 進行複雜查詢
2. 結合其他資料源進行交叉分析
3. 建立歷史資料趨勢分析

## ⚠️ 注意事項

### 檔案編碼
- 所有 CSV 檔案使用 UTF-8-BOM 編碼
- Excel 開啟時中文應正常顯示
- 如有亂碼，請確認編碼設定

### 資料格式
- 數值欄位已經格式化，可直接用於計算
- 日期格式為 YYYY-MM-DD
- 股票代號為純數字格式

### 更新頻率
- 時間戳版本檔案保留歷史記錄
- `*_latest.csv` 檔案總是最新版本
- 建議定期備份重要的時間戳版本

---
FactSet Pipeline v3.6.1 - CSV Only Mode
避免 Google Sheets API 限制，提供穩定可靠的輸出方案
"""

        # 儲存使用指南 (只生成 latest 版本)
        guide_path = os.path.join(self.validation_settings['csv_output_dir'], 'generation_guide_latest.md')

        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)

    def _handle_validation_summary_v361_safe(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                                            watchlist_df: pd.DataFrame = None):
        """🔧 安全版本的驗證摘要處理"""
        try:
            # 1. 生成驗證摘要數據
            validation_data = self._generate_validation_summary_data_v361(portfolio_df, detailed_df, watchlist_df)
            
            # 2. 生成 CSV 檔案（總是執行）
            csv_file = self._save_validation_summary_csv(validation_data)
            if csv_file:
                print(f"📊 驗證摘要 CSV 已生成: {os.path.basename(csv_file)}")
            
            # 3. 嘗試上傳到 Google Sheets（可選，有 API 限制保護）
            if self.validation_settings.get('upload_validation_to_sheets', False):
                try:
                    if self._check_api_availability():
                        self._upload_validation_summary_simple(validation_data)
                        print("📊 驗證摘要已上傳到 Google Sheets")
                    else:
                        print("⚠️ API 限制，跳過 Google Sheets 驗證摘要上傳")
                except Exception as e:
                    print(f"⚠️ Google Sheets 驗證摘要上傳失敗: {e}")
                    print("💡 但 CSV 檔案已生成，可手動上傳")
            
        except Exception as e:
            print(f"⚠️ 驗證摘要處理失敗: {e}")

    # 保持其他原有方法不變...
    def _validate_before_upload_v361(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                                    watchlist_df: pd.DataFrame = None) -> Dict[str, Any]:
        """上傳前驗證檢查"""
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
        
        # 觀察名單相關統計
        watchlist_summary = {
            'watchlist_provided': watchlist_df is not None and not watchlist_df.empty,
            'watchlist_companies': 0,
            'coverage_rate': 0.0
        }
        
        if watchlist_df is not None and not watchlist_df.empty:
            watchlist_companies = len(watchlist_df)
            processed_companies = len([idx for idx, row in watchlist_df.iterrows() 
                                     if row.get('處理狀態', '') == '✅ 已處理'])
            
            watchlist_summary.update({
                'watchlist_companies': watchlist_companies,
                'processed_companies': processed_companies,
                'coverage_rate': (processed_companies / watchlist_companies) * 100 if watchlist_companies > 0 else 0
            })
        
        validation_result['summary'] = {
            'total_companies': total_companies,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'validation_disabled': validation_disabled_count,
            'validation_issues': len(validation_issues),
            'watchlist_summary': watchlist_summary
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
                status_parts = []
                if validation_disabled_count > 0:
                    status_parts.append(f'{validation_disabled_count} 個驗證停用')
                if warning_issues > 0:
                    status_parts.append(f'{warning_issues} 個警告')
                if watchlist_summary['watchlist_provided']:
                    status_parts.append(f"觀察名單覆蓋率 {watchlist_summary['coverage_rate']:.1f}%")
                
                if status_parts:
                    validation_result['reason'] = f'發現 {", ".join(status_parts)}，將繼續上傳'
                    validation_result['severity'] = 'info'
        
        return validation_result

    def _mark_problematic_data_v361(self, df: pd.DataFrame) -> pd.DataFrame:
        """標記問題資料"""
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
        
        return df_marked

    def _generate_validation_summary_data_v361(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                                             watchlist_df: pd.DataFrame = None) -> pd.DataFrame:
        """生成驗證摘要數據"""
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
        
        # 觀察名單統計
        if watchlist_df is not None and not watchlist_df.empty:
            total_watchlist = len(watchlist_df)
            processed_count = len([idx for idx, row in watchlist_df.iterrows() 
                                 if row.get('處理狀態', '') == '✅ 已處理'])
            not_found_count = len([idx for idx, row in watchlist_df.iterrows() 
                                 if row.get('處理狀態', '') == '❌ 未找到'])
            coverage_rate = (processed_count / total_watchlist) * 100 if total_watchlist > 0 else 0
            
            summary_rows.extend([
                {
                    '項目': '觀察名單總數',
                    '數值': total_watchlist,
                    '說明': '觀察名單中的公司總數',
                    '詳細資訊': f'這是處理的基準清單',
                    '更新時間': current_time
                },
                {
                    '項目': '觀察名單已處理',
                    '數值': processed_count,
                    '說明': '觀察名單中已成功處理的公司數',
                    '詳細資訊': f'覆蓋率: {coverage_rate:.1f}%',
                    '更新時間': current_time
                },
                {
                    '項目': '觀察名單未找到',
                    '數值': not_found_count,
                    '說明': '觀察名單中未找到MD檔案的公司數',
                    '詳細資訊': f'需要加強搜尋的公司',
                    '更新時間': current_time
                }
            ])
        
        return pd.DataFrame(summary_rows)

    def _save_validation_summary_csv(self, validation_df: pd.DataFrame) -> str:
        """儲存驗證摘要為 CSV 檔案 (只生成 latest 版本)"""
        try:
            csv_path = os.path.join(self.validation_settings['csv_output_dir'], 'validation_summary_latest.csv')

            # 儲存 CSV
            validation_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

            return csv_path
            
        except Exception as e:
            print(f"❌ 儲存驗證摘要 CSV 失敗: {e}")
            return ""

    def _upload_validation_summary_simple(self, validation_df: pd.DataFrame):
        """簡化版驗證摘要上傳"""
        try:
            # 嘗試找到或建立驗證摘要工作表
            try:
                validation_worksheet = self.spreadsheet.worksheet(self.worksheet_names['validation'])
            except gspread.WorksheetNotFound:
                print("📊 建立驗證摘要工作表...")
                validation_worksheet = self.spreadsheet.add_worksheet(title=self.worksheet_names['validation'], rows=200, cols=10)
            
            # 清空現有內容
            validation_worksheet.clear()
            time.sleep(self.api_settings['rate_limit_delay'])
            
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
            time.sleep(self.api_settings['rate_limit_delay'])
            
            # 上傳數據
            if clean_data:
                validation_worksheet.update('A2', clean_data)
                time.sleep(self.api_settings['rate_limit_delay'])
            
            # 只設定最基本的標題格式
            try:
                validation_worksheet.format('A1:E1', {
                    'textFormat': {'bold': True}
                })
            except:
                pass
            
        except Exception as e:
            raise Exception(f"簡化上傳失敗: {e}")

    # 其他輔助方法
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
                portfolio_worksheet = self.spreadsheet.worksheet(self.worksheet_names['portfolio'])
            except gspread.WorksheetNotFound:
                print("📊 建立投資組合摘要工作表...")
                portfolio_worksheet = self.spreadsheet.add_worksheet(title=self.worksheet_names['portfolio'], rows=1000, cols=20)
            
            portfolio_worksheet.clear()
            time.sleep(self.api_settings['rate_limit_delay'])
            
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
            time.sleep(self.api_settings['rate_limit_delay'])
            
            if data:
                portfolio_worksheet.update('A2', data)
                time.sleep(self.api_settings['rate_limit_delay'])
            
            return True
            
        except Exception as e:
            print(f"❌ 投資組合摘要上傳失敗: {e}")
            return False

    def _upload_detailed_report(self, detailed_df: pd.DataFrame) -> bool:
        """上傳詳細報告"""
        try:
            try:
                detailed_worksheet = self.spreadsheet.worksheet(self.worksheet_names['detailed'])
            except gspread.WorksheetNotFound:
                print("📊 建立詳細報告工作表...")
                detailed_worksheet = self.spreadsheet.add_worksheet(title=self.worksheet_names['detailed'], rows=2000, cols=25)
            
            detailed_worksheet.clear()
            time.sleep(self.api_settings['rate_limit_delay'])
            
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
            time.sleep(self.api_settings['rate_limit_delay'])
            
            if data:
                # 分批上傳大量資料
                batch_size = self.api_settings['batch_size']
                for i in range(0, len(data), batch_size):
                    batch_data = data[i:i + batch_size]
                    start_row = i + 2
                    range_name = f'A{start_row}'
                    
                    detailed_worksheet.update(range_name, batch_data)
                    time.sleep(self.api_settings['rate_limit_delay'])
                    
                    if i + batch_size < len(data):
                        print(f"   已上傳 {i + batch_size}/{len(data)} 行...")
            
            return True
            
        except Exception as e:
            print(f"❌ 詳細報告上傳失敗: {e}")
            return False

    def _upload_keyword_summary(self, keyword_df: pd.DataFrame) -> bool:
        """上傳關鍵字統計報告"""
        try:
            try:
                worksheet = self.spreadsheet.worksheet(self.worksheet_names['keywords'])
            except gspread.WorksheetNotFound:
                print("📊 建立關鍵字工作表...")
                worksheet = self.spreadsheet.add_worksheet(
                    title=self.worksheet_names['keywords'], 
                    rows=1000, 
                    cols=12
                )
            
            worksheet.clear()
            time.sleep(self.api_settings['rate_limit_delay'])
            
            keyword_df_clean = keyword_df.copy()
            keyword_df_clean = keyword_df_clean.fillna('')
            
            numeric_columns = ['使用次數', '平均品質評分', '最高品質評分', '最低品質評分', '相關公司數量']
            for col in numeric_columns:
                if col in keyword_df_clean.columns:
                    keyword_df_clean[col] = keyword_df_clean[col].apply(self._format_numeric_value)
            
            headers = keyword_df_clean.columns.tolist()
            data = keyword_df_clean.values.tolist()
            
            data = [[self._ensure_json_compatible(cell) for cell in row] for row in data]
            
            worksheet.update('A1', [headers])
            time.sleep(self.api_settings['rate_limit_delay'])
            
            if data:
                worksheet.update('A2', data)
                time.sleep(self.api_settings['rate_limit_delay'])
            
            # 設定基本格式
            try:
                worksheet.format('A1:J1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                })
                time.sleep(self.api_settings['rate_limit_delay'])
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ 關鍵字報告上傳失敗: {e}")
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

    # 🆕 公用方法：只生成 CSV，不上傳
    def generate_csv_only(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                         keyword_df: pd.DataFrame = None, watchlist_df: pd.DataFrame = None) -> bool:
        """🆕 公用方法：只生成 CSV 檔案，不上傳到 Google Sheets"""
        return self._csv_only_mode(portfolio_df, detailed_df, keyword_df, watchlist_df)


# 測試功能
if __name__ == "__main__":
    uploader = SheetsUploader()
    
    print("=== 🔧 修復版 Sheets Uploader v3.6.1 測試 ===")
    
    # 測試資料
    import pandas as pd
    
    test_portfolio = pd.DataFrame([
        {'代號': '2330', '名稱': '台積電', '品質評分': 10.0, '狀態': '🟢 完整'},
        {'代號': '6462', '名稱': '神盾', '品質評分': 7.0, '狀態': '🟡 良好'}
    ])
    
    test_detailed = pd.DataFrame([
        {'代號': '2330', '名稱': '台積電', '品質評分': 10.0, '驗證狀態': '✅ 通過'},
        {'代號': '6462', '名稱': '神盾', '品質評分': 7.0, '驗證狀態': '⚠️ 驗證停用'}
    ])
    
    test_watchlist = pd.DataFrame([
        {
            '公司代號': '2330',
            '公司名稱': '台積電',
            'MD檔案數量': 2,
            '處理狀態': '✅ 已處理',
            '平均品質評分': 9.2,
            '最高品質評分': 10.0,
            '搜尋關鍵字數量': 4,
            '主要關鍵字': '台積電, factset, eps',
            '關鍵字平均品質': 8.5,
            '最新檔案日期': '2025-06-24',
            '驗證狀態': '✅ 驗證通過'
        }
    ])
    
    print("測試 1: CSV-only 模式")
    success = uploader.generate_csv_only(test_portfolio, test_detailed, None, test_watchlist)
    if success:
        print("   ✅ CSV-only 模式測試成功")
    else:
        print("   ❌ CSV-only 模式測試失敗")
    
    print("\n測試 2: 上傳前驗證")
    validation_result = uploader._validate_before_upload_v361(test_portfolio, test_detailed, test_watchlist)
    print(f"   驗證結果: {validation_result['safe_to_upload']}")
    print(f"   驗證摘要: {validation_result['summary']}")
    
    print("\n測試 3: API 可用性檢查")
    api_available = uploader._check_api_availability()
    print(f"   API 可用: {api_available}")
    
    print(f"\n🎉 修復版 Sheets Uploader v3.6.1 測試完成!")
    print(f"✅ 修復 columnWidth API 錯誤")
    print(f"✅ 增加 API 限制保護機制")
    print(f"✅ 支援 CSV-only 模式")
    print(f"✅ 增強錯誤處理和重試機制")
    print(f"✅ 自動 fallback 到 CSV 模式")
    
    print(f"\n💡 使用建議:")
    print(f"   對於大量資料或 API 限制情況，使用 csv_only=True")
    print(f"   系統會自動檢測 API 問題並切換到 CSV 模式")
    print(f"   所有 CSV 檔案都有完整的使用指南")
