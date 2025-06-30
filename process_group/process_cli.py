#!/usr/bin/env python3
"""
FactSet Pipeline v3.6.1 - Process CLI (Complete Implementation)
處理群組的命令列介面 - 完整的觀察名單統計和分析功能
"""

import sys
import os
import re
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

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
    
    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"✅ 載入環境變數: {env_path}")
            env_loaded = True
            break
    
    if not env_loaded:
        print("⚠️ 未找到 .env 檔案，使用系統環境變數")

except ImportError:
    print("⚠️ python-dotenv 未安裝，使用系統環境變數")

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入組件
try:
    from md_scanner import MDScanner
    print("✅ MDScanner 已載入")
except ImportError as e:
    print(f"❌ MDScanner 載入失敗: {e}")
    MDScanner = None

try:
    from md_parser import MDParser
    print("✅ MDParser 已載入")
except ImportError as e:
    print(f"❌ MDParser 載入失敗: {e}")
    MDParser = None

try:
    from quality_analyzer import QualityAnalyzer
    print("✅ QualityAnalyzer 已載入")
except ImportError as e:
    print(f"❌ QualityAnalyzer 載入失敗: {e}")
    QualityAnalyzer = None

try:
    from keyword_analyzer import KeywordAnalyzer
    print("✅ KeywordAnalyzer 已載入")
except ImportError as e:
    print(f"❌ KeywordAnalyzer 載入失敗: {e}")
    KeywordAnalyzer = None

try:
    from watchlist_analyzer import WatchlistAnalyzer
    print("✅ WatchlistAnalyzer v3.6.1 已載入")
except ImportError as e:
    print(f"❌ WatchlistAnalyzer 載入失敗: {e}")
    WatchlistAnalyzer = None

try:
    from report_generator import ReportGenerator
    print("✅ ReportGenerator 已載入")
except ImportError as e:
    print(f"❌ ReportGenerator 載入失敗: {e}")
    ReportGenerator = None

try:
    from sheets_uploader import SheetsUploader
    print("✅ SheetsUploader 已載入")
except ImportError as e:
    print(f"⚠️ SheetsUploader 載入失敗: {e}")
    SheetsUploader = None


class ProcessCLI:
    """處理命令列介面 - v3.6.1 完整實現"""
    
    def __init__(self):
        print("🔧 初始化 ProcessCLI v3.6.1...")
        
        # 核心組件 - MDScanner 是必須的
        if MDScanner:
            self.md_scanner = MDScanner()
            print("✅ MDScanner 已初始化")
        else:
            raise ImportError("MDScanner 是必須的組件")
        
        # 初始化其他組件
        self.md_parser = None
        self.quality_analyzer = None  
        self.keyword_analyzer = None
        self.watchlist_analyzer = None
        self.report_generator = None
        self.sheets_uploader = None
        
        self._init_components()
        self._ensure_output_directories()
    
    def _init_components(self):
        """初始化所有可用組件"""
        # MD Parser
        if MDParser:
            try:
                self.md_parser = MDParser()
                validation_status = "啟用" if self.md_parser.validation_enabled else "停用"
                watch_list_size = len(self.md_parser.watch_list_mapping)
                print(f"✅ MDParser 已初始化 - 觀察名單驗證: {validation_status} ({watch_list_size} 家公司)")
            except Exception as e:
                print(f"❌ MDParser 初始化失敗: {e}")
        
        # Quality Analyzer
        if QualityAnalyzer:
            try:
                self.quality_analyzer = QualityAnalyzer()
                print("✅ QualityAnalyzer 已初始化")
            except Exception as e:
                print(f"❌ QualityAnalyzer 初始化失敗: {e}")
        
        # Keyword Analyzer
        if KeywordAnalyzer:
            try:
                self.keyword_analyzer = KeywordAnalyzer()
                print("✅ KeywordAnalyzer 已初始化")
            except Exception as e:
                print(f"❌ KeywordAnalyzer 初始化失敗: {e}")
                self.keyword_analyzer = None
        
        # Watchlist Analyzer v3.6.1
        if WatchlistAnalyzer:
            try:
                self.watchlist_analyzer = WatchlistAnalyzer()
                watchlist_status = "啟用" if self.watchlist_analyzer.validation_enabled else "停用"
                watchlist_size = len(self.watchlist_analyzer.watchlist_mapping)
                print(f"✅ WatchlistAnalyzer v3.6.1 已初始化 - 觀察名單分析: {watchlist_status} ({watchlist_size} 家公司)")
            except Exception as e:
                print(f"❌ WatchlistAnalyzer 初始化失敗: {e}")
                self.watchlist_analyzer = None
        
        # Report Generator
        if ReportGenerator:
            try:
                self.report_generator = ReportGenerator()
                print("✅ ReportGenerator 已初始化")
            except Exception as e:
                print(f"❌ ReportGenerator 初始化失敗: {e}")
                self.report_generator = None
        
        # Sheets Uploader
        if SheetsUploader:
            try:
                self.sheets_uploader = SheetsUploader()
                print("✅ SheetsUploader 已初始化")
            except Exception as e:
                print(f"⚠️ SheetsUploader 初始化失敗: {e}")
                self.sheets_uploader = None

    def process_all_md_files(self, upload_sheets=True, **kwargs):
        """🔧 v3.6.1 處理所有 MD 檔案 - 新增觀察名單分析"""
        print("\n🚀 開始處理所有 MD 檔案 v3.6.1...")
        
        # 檢查觀察名單狀態
        if self.md_parser:
            validation_status = "啟用" if self.md_parser.validation_enabled else "停用"
            watch_list_size = len(self.md_parser.watch_list_mapping)
            print(f"📋 觀察名單驗證: {validation_status} ({watch_list_size} 家公司)")
        
        if self.watchlist_analyzer:
            watchlist_analysis_status = "啟用" if self.watchlist_analyzer.validation_enabled else "停用"
            watchlist_size = len(self.watchlist_analyzer.watchlist_mapping)
            print(f"📊 觀察名單分析: {watchlist_analysis_status} ({watchlist_size} 家公司)")
        
        # 掃描 MD 檔案
        md_files = self.md_scanner.scan_all_md_files()
        print(f"📁 發現 {len(md_files)} 個 MD 檔案")
        
        if not md_files:
            print("❌ 沒有找到任何 MD 檔案")
            print("💡 請先執行搜尋群組來生成 MD 檔案")
            return []
        
        # 處理檔案
        processed_companies = self._process_md_file_list_v361(md_files, **kwargs)
        
        # 生成報告前的最終統計
        if processed_companies:
            print(f"\n🎯 報告生成階段 v3.6.1:")
            
            # 預先檢查有多少公司會被包含在報告中
            if self.report_generator:
                companies_for_report = [c for c in processed_companies 
                                      if self.report_generator._should_include_in_report_v351(c)]
                
                excluded_count = len(processed_companies) - len(companies_for_report)
                
                print(f"📊 處理結果摘要:")
                print(f"   已處理公司: {len(processed_companies)} 家")
                print(f"   將納入報告: {len(companies_for_report)} 家")
                print(f"   因驗證失敗排除: {excluded_count} 家")
                
                if excluded_count > 0:
                    print(f"   ✅ 成功過濾了 {excluded_count} 家有問題的公司")
            
            # 生成和上傳報告 (包含觀察名單報告)
            self._generate_and_upload_reports_v361(processed_companies, upload_sheets, 
                                                   force_upload=kwargs.get('force_upload', False))
            
            print(f"✅ 處理完成")
            
            # 顯示最終驗證摘要
            self._display_processing_validation_summary_v361(processed_companies)
        else:
            print("❌ 沒有成功處理任何檔案")
        
        return processed_companies

    def process_recent_files(self, hours=24, upload_sheets=True, **kwargs):
        """🔧 v3.6.1 處理最近的 MD 檔案"""
        print(f"\n🚀 處理最近 {hours} 小時的 MD 檔案 v3.6.1...")
        
        recent_files = self.md_scanner.scan_recent_files(hours)
        print(f"📁 發現 {len(recent_files)} 個最近的 MD 檔案")
        
        if not recent_files:
            print(f"❌ 最近 {hours} 小時內沒有 MD 檔案")
            return []
        
        # 處理最近的檔案
        processed_companies = self._process_md_file_list_v361(recent_files, **kwargs)
        
        if processed_companies:
            # 生成和上傳報告
            self._generate_and_upload_reports_v361(processed_companies, upload_sheets,
                                                   force_upload=kwargs.get('force_upload', False))
            
            print(f"✅ 最近檔案處理完成")
        
        return processed_companies

    def process_single_company(self, company_code, upload_sheets=True, **kwargs):
        """🔧 v3.6.1 處理單一公司"""
        print(f"\n🚀 處理單一公司: {company_code} v3.6.1...")
        
        company_files = self.md_scanner.find_company_files(company_code)
        print(f"📁 發現公司 {company_code} 的 {len(company_files)} 個 MD 檔案")
        
        if not company_files:
            print(f"❌ 沒有找到公司 {company_code} 的 MD 檔案")
            return []
        
        # 處理公司檔案
        processed_companies = self._process_md_file_list_v361(company_files, **kwargs)
        
        if processed_companies:
            # 生成和上傳報告
            self._generate_and_upload_reports_v361(processed_companies, upload_sheets,
                                                   force_upload=kwargs.get('force_upload', False))
            
            print(f"✅ 公司 {company_code} 處理完成")
        
        return processed_companies

    def analyze_quality_only(self, **kwargs):
        """🔧 v3.6.1 只進行品質分析"""
        print("\n📊 執行品質分析 v3.6.1...")
        
        md_files = self.md_scanner.scan_all_md_files()
        
        if not md_files:
            print("❌ 沒有找到 MD 檔案")
            return {}
        
        processed_companies = []
        quality_stats = {
            'total_files': len(md_files),
            'processed_files': 0,
            'quality_distribution': {'excellent': 0, 'good': 0, 'partial': 0, 'insufficient': 0},
            'validation_stats': {'passed': 0, 'failed': 0, 'disabled': 0}
        }
        
        print(f"📊 分析 {len(md_files)} 個 MD 檔案的品質")
        
        for md_file in md_files:
            try:
                if self.md_parser and self.quality_analyzer:
                    parsed_data = self.md_parser.parse_md_file(md_file)
                    quality_data = self.quality_analyzer.analyze(parsed_data)
                    
                    company_data = {**parsed_data, **quality_data}
                    processed_companies.append(company_data)
                    
                    # 統計品質分布
                    quality_category = quality_data.get('quality_category', 'insufficient')
                    quality_stats['quality_distribution'][quality_category] += 1
                    
                    # 統計驗證狀態
                    if parsed_data.get('content_validation_passed', True):
                        quality_stats['validation_stats']['passed'] += 1
                    elif parsed_data.get('validation_result', {}).get('validation_method') == 'disabled':
                        quality_stats['validation_stats']['disabled'] += 1
                    else:
                        quality_stats['validation_stats']['failed'] += 1
                    
                    quality_stats['processed_files'] += 1
                
            except Exception as e:
                print(f"❌ 分析失敗: {os.path.basename(md_file)} - {e}")
                continue
        
        # 顯示品質分析結果
        self._display_quality_analysis_results(quality_stats)
        
        # 儲存品質分析結果
        self._save_quality_analysis(quality_stats, processed_companies)
        
        print(f"✅ 品質分析完成: {quality_stats['processed_files']}/{quality_stats['total_files']} 成功")
        return quality_stats

    def analyze_keywords_only(self, min_usage=1, **kwargs):
        """🔧 v3.6.1 只進行關鍵字分析"""
        print(f"\n📊 執行關鍵字分析 v3.6.1 (最小使用次數: {min_usage})...")
        
        if not self.keyword_analyzer:
            print("❌ KeywordAnalyzer 未載入，無法進行關鍵字分析")
            return {}
        
        md_files = self.md_scanner.scan_all_md_files()
        
        if not md_files:
            print("❌ 沒有找到 MD 檔案")
            return {}
        
        print(f"📊 分析 {len(md_files)} 個 MD 檔案的關鍵字使用情況")
        
        # 處理檔案以提取關鍵字
        processed_companies = []
        success_count = 0
        
        for md_file in md_files:
            try:
                file_info = self.md_scanner.get_file_info(md_file)
                
                if self.md_parser and self.quality_analyzer:
                    parsed_data = self.md_parser.parse_md_file(md_file)
                    quality_data = self.quality_analyzer.analyze(parsed_data)
                    
                    company_data = {
                        **parsed_data,
                        **quality_data,
                        'processed_at': datetime.now()
                    }
                else:
                    company_data = self._basic_process_md_file(md_file, file_info)
                
                processed_companies.append(company_data)
                success_count += 1
                
            except Exception as e:
                print(f"❌ 處理失敗: {os.path.basename(md_file)} - {e}")
                continue
        
        # 執行關鍵字分析
        keyword_analysis = self.keyword_analyzer.analyze_all_keywords(processed_companies)
        
        # 過濾低使用率關鍵字
        if min_usage > 1:
            keyword_analysis = self.keyword_analyzer.filter_keywords_by_usage(
                keyword_analysis, min_usage
            )
        
        # 儲存關鍵字分析結果
        self._save_keyword_analysis(keyword_analysis)
        self._display_keyword_summary(keyword_analysis, min_usage)
        
        print(f"✅ 關鍵字分析完成: {success_count}/{len(md_files)} 成功")
        return keyword_analysis

    def analyze_watchlist_only(self, **kwargs):
        """🆕 v3.6.1 只進行觀察名單分析"""
        print("\n📊 執行觀察名單分析 v3.6.1...")
        
        if not self.watchlist_analyzer:
            print("❌ WatchlistAnalyzer 未載入，無法進行觀察名單分析")
            return {}
        
        md_files = self.md_scanner.scan_all_md_files()
        
        if not md_files:
            print("❌ 沒有找到 MD 檔案")
            return {}
        
        print(f"📊 分析 {len(md_files)} 個 MD 檔案的觀察名單覆蓋情況")
        
        # 處理檔案
        processed_companies = []
        success_count = 0
        
        for md_file in md_files:
            try:
                file_info = self.md_scanner.get_file_info(md_file)
                
                if self.md_parser and self.quality_analyzer:
                    parsed_data = self.md_parser.parse_md_file(md_file)
                    quality_data = self.quality_analyzer.analyze(parsed_data)
                    
                    company_data = {
                        **parsed_data,
                        **quality_data,
                        'processed_at': datetime.now()
                    }
                else:
                    company_data = self._basic_process_md_file(md_file, file_info)
                
                processed_companies.append(company_data)
                success_count += 1
                
            except Exception as e:
                print(f"❌ 處理失敗: {os.path.basename(md_file)} - {e}")
                continue
        
        # 執行觀察名單分析
        watchlist_analysis = self.watchlist_analyzer.analyze_watchlist_coverage(processed_companies)
        
        # 儲存分析結果
        self._save_watchlist_analysis(watchlist_analysis)
        self._display_watchlist_summary(watchlist_analysis)
        
        print(f"✅ 觀察名單分析完成: {success_count}/{len(md_files)} 成功")
        return watchlist_analysis

    def generate_keyword_summary(self, upload_sheets=True, min_usage=1, **kwargs):
        """🔧 v3.6.1 生成關鍵字統計報告"""
        print(f"\n📊 生成關鍵字統計報告 v3.6.1...")
        
        if not self.keyword_analyzer:
            print("❌ KeywordAnalyzer 未載入，無法生成關鍵字報告")
            return {}, ""
        
        # 先執行關鍵字分析
        keyword_analysis = self.analyze_keywords_only(min_usage=min_usage, **kwargs)
        
        if not keyword_analysis:
            print("❌ 關鍵字分析失敗")
            return {}, ""
        
        # 生成關鍵字報告
        if self.report_generator:
            keyword_summary = self.report_generator.generate_keyword_summary(keyword_analysis)
            
            # 儲存 CSV
            csv_path = self.report_generator.save_keyword_summary(keyword_summary)
            
            # 上傳 (可選)
            if upload_sheets and self.sheets_uploader:
                try:
                    self.sheets_uploader._upload_keyword_summary(keyword_summary)
                    print("☁️ 關鍵字報告已上傳到 Google Sheets")
                except Exception as e:
                    print(f"⚠️ Google Sheets 上傳失敗: {e}")
            
            # 顯示統計摘要
            self._display_keyword_generation_summary(keyword_analysis, min_usage)
            
            return keyword_analysis, csv_path
        else:
            print("❌ ReportGenerator 未載入，無法生成報告")
            return keyword_analysis, ""

    def generate_watchlist_summary(self, upload_sheets=True, include_missing=False, **kwargs):
        """🆕 v3.6.1 生成觀察名單統計報告"""
        print(f"\n📊 生成觀察名單統計報告 v3.6.1...")
        
        if not self.watchlist_analyzer:
            print("❌ WatchlistAnalyzer 未載入，無法生成觀察名單報告")
            return {}, ""
        
        # 掃描檔案
        md_files = self.md_scanner.scan_all_md_files()
        print(f"📁 掃描到 {len(md_files)} 個 MD 檔案")
        
        # 解析檔案
        processed_companies = []
        for md_file in md_files:
            try:
                parsed_data = self.md_parser.parse_md_file(md_file) if self.md_parser else {}
                quality_data = self.quality_analyzer.analyze(parsed_data) if self.quality_analyzer else {}
                company_data = {**parsed_data, **quality_data}
                processed_companies.append(company_data)
            except Exception as e:
                print(f"⚠️ 處理檔案失敗: {os.path.basename(md_file)} - {e}")
                continue
        
        print(f"📊 成功處理 {len(processed_companies)} 個檔案")
        
        # 觀察名單分析
        watchlist_analysis = self.watchlist_analyzer.analyze_watchlist_coverage(processed_companies)
        
        # 生成觀察名單報告
        if self.report_generator:
            watchlist_summary = self.report_generator.generate_watchlist_summary(watchlist_analysis)
            
            # 可選：包含缺失公司資訊
            if include_missing:
                print("📋 包含缺失公司資訊...")
                missing_companies = self.watchlist_analyzer.generate_missing_companies_report(processed_companies)
                watchlist_summary = self._append_missing_companies(watchlist_summary, missing_companies)
            
            # 儲存 CSV
            csv_path = self.report_generator.save_watchlist_summary(watchlist_summary)
            
            # 上傳 (可選)
            if upload_sheets and self.sheets_uploader:
                try:
                    self.sheets_uploader._upload_watchlist_summary(watchlist_summary)
                    print("☁️ 觀察名單報告已上傳到 Google Sheets")
                except Exception as e:
                    print(f"⚠️ Google Sheets 上傳失敗: {e}")
            
            # 顯示統計摘要
            missing_count = len(missing_companies) if include_missing else 0
            self._display_watchlist_generation_summary(watchlist_analysis, missing_count)
            
            return watchlist_analysis, csv_path
        else:
            print("❌ ReportGenerator 未載入，無法生成報告")
            return watchlist_analysis, ""

    def show_stats(self, **kwargs):
        """🔧 v3.6.1 顯示統計資訊"""
        print("\n📊 系統統計資訊 v3.6.1")
        print("=" * 50)
        
        # MD 檔案統計
        try:
            stats = self.md_scanner.get_stats()
            print(f"📁 MD 檔案統計:")
            print(f"   總檔案數: {stats['total_files']}")
            print(f"   最近 24h: {stats['recent_files_24h']}")
            print(f"   公司數量: {stats['unique_companies']}")
            print(f"   總大小: {stats['total_size_mb']} MB")
            
            if stats['oldest_file']:
                print(f"   最舊檔案: {os.path.basename(stats['oldest_file'])}")
            if stats['newest_file']:
                print(f"   最新檔案: {os.path.basename(stats['newest_file'])}")
        except Exception as e:
            print(f"❌ MD 檔案統計失敗: {e}")
        
        # 觀察名單統計
        if self.md_parser and self.md_parser.validation_enabled:
            watch_list_size = len(self.md_parser.watch_list_mapping)
            print(f"\n📋 觀察名單統計:")
            print(f"   觀察名單公司數: {watch_list_size}")
            print(f"   驗證狀態: 啟用")
        else:
            print(f"\n📋 觀察名單統計:")
            print(f"   驗證狀態: 停用")
        
        # 觀察名單分析統計 (v3.6.1)
        if self.watchlist_analyzer and self.watchlist_analyzer.validation_enabled:
            watchlist_analysis_size = len(self.watchlist_analyzer.watchlist_mapping)
            print(f"\n📊 觀察名單分析統計 (v3.6.1):")
            print(f"   分析範圍公司數: {watchlist_analysis_size}")
            print(f"   分析狀態: 啟用")
        else:
            print(f"\n📊 觀察名單分析統計 (v3.6.1):")
            print(f"   分析狀態: 停用")
        
        # 按公司檔案數量排序
        try:
            if stats['companies_with_files']:
                sorted_companies = sorted(stats['companies_with_files'].items(), 
                                        key=lambda x: x[1], reverse=True)
                print(f"\n📊 檔案最多的前 10 家公司:")
                for company, count in sorted_companies[:10]:
                    print(f"   {company}: {count} 個檔案")
        except Exception as e:
            print(f"⚠️ 公司檔案統計顯示失敗: {e}")
        
        # 組件狀態
        print(f"\n🔧 組件狀態:")
        components = [
            ('MD Scanner', self.md_scanner is not None),
            ('MD Parser', self.md_parser is not None),
            ('Quality Analyzer', self.quality_analyzer is not None),
            ('Keyword Analyzer', self.keyword_analyzer is not None),
            ('Watchlist Analyzer', self.watchlist_analyzer is not None),
            ('Report Generator', self.report_generator is not None),
            ('Sheets Uploader', self.sheets_uploader is not None)
        ]
        
        for name, status in components:
            status_icon = "✅" if status else "❌"
            print(f"   {name}: {status_icon}")

    def validate_setup(self, **kwargs):
        """🔧 v3.6.1 驗證處理環境設定 - 包含觀察名單分析檢查"""
        print("\n🔧 驗證處理環境設定 v3.6.1")
        print("=" * 50)
        
        validation_results = {}
        
        # 檢查 MD 目錄
        try:
            md_files = self.md_scanner.scan_all_md_files()
            validation_results['md_scanner'] = {
                'status': '✅ 正常',
                'details': f'找到 {len(md_files)} 個 MD 檔案'
            }
        except Exception as e:
            validation_results['md_scanner'] = {
                'status': '❌ 錯誤',
                'details': str(e)
            }
        
        # 檢查觀察名單載入狀態
        if self.md_parser:
            validation_enabled = self.md_parser.validation_enabled
            watch_list_size = len(self.md_parser.watch_list_mapping)
            
            if validation_enabled:
                validation_results['watch_list'] = {
                    'status': '✅ 已載入',
                    'details': f'觀察名單包含 {watch_list_size} 家公司'
                }
            else:
                validation_results['watch_list'] = {
                    'status': '⚠️ 未載入',
                    'details': '觀察名單檔案無法載入或為空，驗證功能已停用'
                }
        else:
            validation_results['watch_list'] = {
                'status': '❌ 無法檢查',
                'details': 'MD Parser 未載入'
            }
        
        # 檢查觀察名單分析器
        if self.watchlist_analyzer:
            watchlist_analysis_enabled = self.watchlist_analyzer.validation_enabled
            watchlist_size = len(self.watchlist_analyzer.watchlist_mapping)
            
            if watchlist_analysis_enabled:
                validation_results['watchlist_analyzer'] = {
                    'status': '✅ 已載入',
                    'details': f'觀察名單分析器包含 {watchlist_size} 家公司'
                }
            else:
                validation_results['watchlist_analyzer'] = {
                    'status': '⚠️ 未載入',
                    'details': '觀察名單分析器無法載入觀察名單檔案'
                }
        else:
            validation_results['watchlist_analyzer'] = {
                'status': '❌ 未載入',
                'details': 'WatchlistAnalyzer 模組未載入'
            }
        
        # 檢查其他組件
        components = [
            ('md_parser', self.md_parser),
            ('quality_analyzer', self.quality_analyzer),
            ('keyword_analyzer', self.keyword_analyzer),
            ('report_generator', self.report_generator),
            ('sheets_uploader', self.sheets_uploader)
        ]
        
        for name, component in components:
            if component:
                try:
                    if hasattr(component, 'test_connection'):
                        result = component.test_connection()
                        validation_results[name] = {
                            'status': '✅ 正常' if result else '⚠️ 警告',
                            'details': '連線測試成功' if result else '連線測試失敗'
                        }
                    else:
                        validation_results[name] = {
                            'status': '✅ 已載入',
                            'details': '模組已成功載入'
                        }
                except Exception as e:
                    validation_results[name] = {
                        'status': '❌ 錯誤',
                        'details': str(e)
                    }
            else:
                validation_results[name] = {
                    'status': '⚠️ 未載入',
                    'details': '模組未安裝或載入失敗'
                }
        
        # 顯示結果
        for component, result in validation_results.items():
            print(f"{component:18}: {result['status']} - {result['details']}")
        
        return validation_results

    # 私有輔助方法
    def _process_md_file_list_v361(self, md_files, **kwargs):
        """🔧 v3.6.1 處理 MD 檔案清單 - 包含觀察名單分析統計"""
        processed_companies = []
        validation_stats = {
            'total_processed': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'validation_disabled': 0,
            'not_in_watchlist': 0,
            'name_mismatch': 0,
            'invalid_format': 0,
            'other_errors': 0
        }
        
        print(f"\n📄 開始處理 {len(md_files)} 個 MD 檔案...")
        
        for i, md_file in enumerate(md_files, 1):
            try:
                print(f"📄 處理 {i}/{len(md_files)}: {os.path.basename(md_file)}")
                
                file_info = self.md_scanner.get_file_info(md_file)
                validation_stats['total_processed'] += 1
                
                if self.md_parser:
                    parsed_data = self.md_parser.parse_md_file(md_file)
                    
                    # 詳細的驗證狀態分析
                    validation_result = parsed_data.get('validation_result', {})
                    validation_status = validation_result.get('overall_status', 'unknown')
                    validation_method = validation_result.get('validation_method', 'unknown')
                    validation_errors = parsed_data.get('validation_errors', [])
                    
                    # 統計驗證狀態
                    if validation_method == 'disabled':
                        validation_stats['validation_disabled'] += 1
                        status_icon = "⚠️"
                        status_msg = "驗證停用 (觀察名單未載入)"
                        validation_passed = True
                        
                    elif validation_status == 'valid':
                        validation_stats['validation_passed'] += 1
                        status_icon = "✅"
                        status_msg = "驗證通過"
                        validation_passed = True
                        
                    elif validation_status == 'error':
                        validation_stats['validation_failed'] += 1
                        status_icon = "❌"
                        validation_passed = False
                        
                        # 分析失敗原因
                        main_error = validation_errors[0] if validation_errors else "未知錯誤"
                        main_error_str = str(main_error)
                        
                        if "不在觀察名單中" in main_error_str:
                            validation_stats['not_in_watchlist'] += 1
                            status_msg = "不在觀察名單"
                        elif "公司名稱不符觀察名單" in main_error_str or "觀察名單顯示應為" in main_error_str:
                            validation_stats['name_mismatch'] += 1
                            status_msg = "觀察名單名稱不符"
                        elif "公司代號格式無效" in main_error_str or "參數錯誤" in main_error_str:
                            validation_stats['invalid_format'] += 1
                            status_msg = "格式無效"
                        else:
                            validation_stats['other_errors'] += 1
                            status_msg = "其他驗證錯誤"
                    
                    else:
                        validation_stats['validation_failed'] += 1
                        status_icon = "❓"
                        status_msg = "未知驗證狀態"
                        validation_passed = False
                    
                    # 更新 parsed_data 的驗證狀態
                    parsed_data['content_validation_passed'] = validation_passed
                    
                    if self.quality_analyzer:
                        quality_data = self.quality_analyzer.analyze(parsed_data)
                        
                        company_data = {
                            **parsed_data,
                            'quality_score': quality_data.get('quality_score', 0),
                            'quality_status': quality_data.get('quality_status', '🔴 不足'),
                            'quality_category': quality_data.get('quality_category', 'insufficient'),
                            'processed_at': datetime.now()
                        }
                    else:
                        company_data = {
                            **parsed_data,
                            'quality_score': parsed_data.get('data_richness_score', 0),
                            'quality_status': self._get_quality_status(parsed_data.get('data_richness_score', 0)),
                            'quality_category': 'partial',
                            'processed_at': datetime.now()
                        }
                else:
                    company_data = self._basic_process_md_file(md_file, file_info)
                    validation_stats['validation_passed'] += 1
                    status_icon = "✅"
                    status_msg = "基本處理"
                
                processed_companies.append(company_data)
                
                # 詳細的處理結果顯示
                company_name = company_data.get('company_name', 'Unknown')
                company_code = company_data.get('company_code', 'Unknown')
                quality_score = company_data.get('quality_score', 0)
                quality_status = company_data.get('quality_status', '🔴 不足')
                
                print(f"   {status_icon} {company_name} ({company_code}) - 品質: {quality_score:.1f} {quality_status} - {status_msg}")
                
                # 如果驗證失敗，顯示詳細原因
                if not validation_passed and validation_errors:
                    error_preview = str(validation_errors[0])[:80]
                    print(f"      🔍 驗證問題: {error_preview}...")
                    
                    if "不在觀察名單" in error_preview:
                        print(f"      💡 此公司將被排除在最終報告之外")
                
            except Exception as e:
                print(f"   ❌ 處理失敗: {os.path.basename(md_file)} - {e}")
                continue
        
        # 處理完成後顯示詳細統計
        self._display_processing_statistics_v361(validation_stats)
        
        return processed_companies

    def _generate_and_upload_reports_v361(self, processed_companies, upload_sheets=True, force_upload=False):
        """🆕 v3.6.1 生成報告並上傳 - 包含觀察名單報告"""
        try:
            if self.report_generator:
                print("📊 使用 ReportGenerator v3.6.1 生成報告...")
                
                # 生成標準報告
                portfolio_summary = self.report_generator.generate_portfolio_summary(processed_companies)
                detailed_report = self.report_generator.generate_detailed_report(processed_companies)
                
                # 生成關鍵字報告
                keyword_summary = None
                if self.keyword_analyzer:
                    try:
                        keyword_analysis = self.keyword_analyzer.analyze_all_keywords(processed_companies)
                        keyword_summary = self.report_generator.generate_keyword_summary(keyword_analysis)
                        print("📊 關鍵字報告已生成")
                    except Exception as e:
                        print(f"⚠️ 關鍵字報告生成失敗: {e}")
                
                # 生成觀察名單報告
                watchlist_summary = None
                if self.watchlist_analyzer:
                    try:
                        watchlist_analysis = self.watchlist_analyzer.analyze_watchlist_coverage(processed_companies)
                        watchlist_summary = self.report_generator.generate_watchlist_summary(watchlist_analysis)
                        print("📊 觀察名單報告已生成")
                    except Exception as e:
                        print(f"⚠️ 觀察名單報告生成失敗: {e}")
                
                # 儲存報告
                saved_files = self.report_generator.save_all_reports(
                    portfolio_summary, detailed_report, keyword_summary, watchlist_summary
                )
                
                if saved_files:
                    print("📁 報告已成功儲存:")
                    for report_type, file_path in saved_files.items():
                        if 'latest' in report_type:
                            print(f"   ✅ {report_type}: {file_path}")
                
                # 生成統計報告
                try:
                    statistics = self.report_generator.generate_statistics_report(processed_companies)
                    stats_file = self.report_generator.save_statistics_report(statistics)
                    if stats_file:
                        print(f"   📊 統計報告: {stats_file}")
                except Exception as e:
                    print(f"   ⚠️ 統計報告生成失敗: {e}")
                
                # 上傳到 Google Sheets
                if upload_sheets and self.sheets_uploader:
                    try:
                        print("☁️ 上傳到 Google Sheets v3.6.1...")
                        
                        if force_upload:
                            print("⚠️ 強制上傳模式：忽略驗證錯誤")
                        
                        success = self.sheets_uploader.upload_all_reports(
                            portfolio_summary, detailed_report, keyword_summary, watchlist_summary
                        )
                        
                        if success:
                            print("   ✅ Google Sheets 上傳成功 (包含觀察名單工作表)")
                        else:
                            print("   ❌ Google Sheets 上傳失敗")
                    except Exception as e:
                        print(f"   ❌ Google Sheets 上傳錯誤: {e}")
                
            else:
                print("❌ ReportGenerator 未載入，無法生成標準報告")
                self._generate_minimal_reports(processed_companies)
        
        except Exception as e:
            print(f"❌ 報告生成或上傳失敗: {e}")

    # 輔助顯示和儲存方法
    def _display_quality_analysis_results(self, quality_stats):
        """顯示品質分析結果"""
        print(f"\n📊 品質分析結果:")
        print(f"=" * 40)
        print(f"📁 處理統計: {quality_stats['processed_files']}/{quality_stats['total_files']}")
        
        print(f"\n📊 品質分布:")
        dist = quality_stats['quality_distribution']
        for category, count in dist.items():
            category_name = {
                'excellent': '🟢 優秀 (9-10分)',
                'good': '🟡 良好 (8-9分)',
                'partial': '🟠 部分 (3-8分)',
                'insufficient': '🔴 不足 (0-3分)'
            }.get(category, category)
            print(f"   {category_name}: {count}")
        
        print(f"\n📊 驗證統計:")
        validation = quality_stats['validation_stats']
        print(f"   ✅ 驗證通過: {validation['passed']}")
        print(f"   ❌ 驗證失敗: {validation['failed']}")
        print(f"   ⚠️ 驗證停用: {validation['disabled']}")

    def _save_quality_analysis(self, quality_stats, processed_companies):
        """儲存品質分析結果"""
        output_file = "data/reports/quality_analysis.json"
        
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '3.6.1',
            'analysis_type': 'quality_only',
            'statistics': quality_stats,
            'company_count': len(processed_companies)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 品質分析結果已儲存: {output_file}")

    def _display_keyword_summary(self, keyword_analysis, min_usage):
        """顯示關鍵字分析摘要"""
        if 'error' in keyword_analysis:
            print(f"❌ 關鍵字分析失敗: {keyword_analysis['error']}")
            return
        
        keyword_stats = keyword_analysis.get('keyword_stats', {})
        
        print(f"\n📊 關鍵字分析摘要 (最小使用次數: {min_usage}):")
        print(f"有效關鍵字數量: {len(keyword_stats)}")
        
        # 顯示效果最好的關鍵字
        top_keywords = sorted(keyword_stats.items(), 
                            key=lambda x: x[1]['avg_quality_score'], reverse=True)[:10]
        
        print(f"效果最好的關鍵字:")
        for keyword, stats in top_keywords:
            print(f"  {keyword}: 平均分數 {stats['avg_quality_score']:.1f} (使用 {stats['usage_count']} 次)")

    def _save_keyword_analysis(self, keyword_analysis):
        """儲存關鍵字分析結果"""
        output_file = "data/reports/keyword_analysis.json"
        
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '3.6.1',
            'analysis_type': 'keyword_analysis',
            'results': keyword_analysis
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 關鍵字分析結果已儲存: {output_file}")

    def _save_watchlist_analysis(self, watchlist_analysis):
        """儲存觀察名單分析結果"""
        output_file = "data/reports/watchlist_analysis.json"
        
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '3.6.1',
            'analysis_type': 'watchlist_coverage',
            'results': watchlist_analysis
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 觀察名單分析結果已儲存: {output_file}")

    def _display_watchlist_summary(self, watchlist_analysis):
        """顯示觀察名單分析摘要"""
        if 'error' in watchlist_analysis:
            print(f"❌ 觀察名單分析失敗: {watchlist_analysis['error']}")
            return
        
        total_companies = watchlist_analysis['total_watchlist_companies']
        companies_with_files = watchlist_analysis['companies_with_md_files']
        coverage_rate = watchlist_analysis['coverage_rate']
        success_rate = watchlist_analysis['success_rate']
        
        print("\n📊 觀察名單分析摘要:")
        print(f"觀察名單總公司數: {total_companies}")
        print(f"有MD檔案公司數: {companies_with_files}")
        print(f"覆蓋率: {coverage_rate}%")
        print(f"成功處理率: {success_rate}%")
        
        # 顯示狀態分佈
        status_summary = watchlist_analysis['company_status_summary']
        print("公司狀態分佈:")
        for status, count in status_summary.items():
            status_name = {
                'processed': '已處理',
                'not_found': '未找到MD檔案',
                'validation_failed': '驗證失敗',
                'low_quality': '品質過低',
                'multiple_files': '多個檔案'
            }.get(status, status)
            print(f"  {status_name}: {count} 家")

    def _append_missing_companies(self, watchlist_summary, missing_companies):
        """將缺失公司資訊附加到觀察名單報告"""
        import pandas as pd
        
        # 準備缺失公司資料
        missing_data = []
        for company in missing_companies:
            missing_data.append({
                '公司代號': company['company_code'],
                '公司名稱': company['company_name'],
                'MD檔案數量': 0,
                '處理狀態': '❌ 缺失MD檔案',
                '平均品質評分': 0.0,
                '最高品質評分': 0.0,
                '搜尋關鍵字數量': len(company.get('suggested_keywords', [])),
                '主要關鍵字': ', '.join(company.get('suggested_keywords', [])[:3]),
                '關鍵字平均品質': 0.0,
                '最新檔案日期': '',
                '驗證狀態': '❌ 無資料',
                '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        missing_df = pd.DataFrame(missing_data)
        
        # 合併現有報告和缺失公司資料
        if not missing_df.empty:
            # 確保欄位一致
            common_columns = list(set(watchlist_summary.columns) & set(missing_df.columns))
            combined_df = pd.concat([
                watchlist_summary[common_columns],
                missing_df[common_columns]
            ], ignore_index=True)
            
            print(f"📋 已附加 {len(missing_companies)} 家缺失公司到觀察名單報告")
            return combined_df
        
        return watchlist_summary

    def _display_keyword_generation_summary(self, keyword_analysis, min_usage):
        """顯示關鍵字報告生成摘要"""
        keyword_stats = keyword_analysis.get('keyword_stats', {})
        
        print(f"\n📊 關鍵字報告生成摘要:")
        print(f"=" * 40)
        print(f"📊 關鍵字統計 (最小使用: {min_usage} 次):")
        print(f"   有效關鍵字: {len(keyword_stats)}")
        
        if keyword_stats:
            # 統計分類
            categories = {}
            for keyword, stats in keyword_stats.items():
                category = stats.get('category', 'other')
                categories[category] = categories.get(category, 0) + 1
            
            print(f"📊 關鍵字分類:")
            for category, count in categories.items():
                print(f"   {category}: {count}")

    def _display_watchlist_generation_summary(self, watchlist_analysis, missing_count=0):
        """顯示觀察名單報告生成摘要"""
        total_companies = watchlist_analysis.get('total_watchlist_companies', 0)
        companies_with_files = watchlist_analysis.get('companies_with_md_files', 0)
        companies_processed = watchlist_analysis.get('companies_processed_successfully', 0)
        coverage_rate = watchlist_analysis.get('coverage_rate', 0)
        success_rate = watchlist_analysis.get('success_rate', 0)
        
        print(f"\n📊 觀察名單報告生成摘要:")
        print(f"=" * 40)
        print(f"📋 觀察名單總公司數: {total_companies}")
        print(f"📁 有MD檔案公司數: {companies_with_files}")
        print(f"✅ 成功處理公司數: {companies_processed}")
        print(f"📊 覆蓋率: {coverage_rate}%")
        print(f"🎯 成功率: {success_rate}%")
        
        if missing_count > 0:
            print(f"❌ 缺失公司數: {missing_count}")

    def _ensure_output_directories(self):
        """確保輸出目錄存在"""
        directories = [
            "data/reports",
            "data/quarantine",
            "data/quarantine/watch_list_issues",
            "logs/process"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _display_processing_statistics_v361(self, validation_stats: Dict):
        """顯示處理統計資訊"""
        total = validation_stats['total_processed']
        passed = validation_stats['validation_passed']
        failed = validation_stats['validation_failed']
        disabled = validation_stats['validation_disabled']
        
        print(f"\n📊 處理統計摘要 v3.6.1:")
        print(f"=" * 40)
        print(f"📁 總處理檔案: {total}")
        print(f"✅ 驗證通過: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ 驗證失敗: {failed} ({failed/total*100:.1f}%)")
        print(f"⚠️ 驗證停用: {disabled} ({disabled/total*100:.1f}%)")
        
        if failed > 0:
            print(f"\n❌ 驗證失敗詳細分類:")
            not_in_watchlist = validation_stats['not_in_watchlist']
            name_mismatch = validation_stats['name_mismatch']
            invalid_format = validation_stats['invalid_format']
            other_errors = validation_stats['other_errors']
            
            if not_in_watchlist > 0:
                print(f"   🚫 不在觀察名單: {not_in_watchlist} 個")
            if name_mismatch > 0:
                print(f"   📝 觀察名單名稱不符: {name_mismatch} 個")
            if invalid_format > 0:
                print(f"   📋 格式無效: {invalid_format} 個")
            if other_errors > 0:
                print(f"   ⚠️ 其他錯誤: {other_errors} 個")
            
            print(f"\n💡 這些驗證失敗的公司將不會出現在最終報告中")

    def _display_processing_validation_summary_v361(self, processed_companies: List):
        """顯示處理過程中的驗證摘要"""
        validation_passed = sum(1 for c in processed_companies if c.get('content_validation_passed', True))
        validation_failed = len(processed_companies) - validation_passed
        validation_disabled = sum(1 for c in processed_companies 
                                if c.get('validation_result', {}).get('validation_method') == 'disabled')
        
        if validation_failed > 0 or validation_disabled > 0:
            print(f"\n⚠️ 最終驗證摘要 v3.6.1:")
            print(f"✅ 驗證通過: {validation_passed}")
            print(f"❌ 驗證失敗: {validation_failed}")
            print(f"⚠️ 驗證停用: {validation_disabled}")

    def _basic_process_md_file(self, md_file, file_info):
        """基本的 MD 檔案處理（當其他模組不可用時）"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        basic_score = self._calculate_basic_quality_score(file_info)
        
        company_data = {
            **file_info,
            'content': content,
            'content_length': len(content),
            'quality_score': basic_score,
            'quality_status': self._get_quality_status(basic_score),
            'quality_category': 'partial',
            'processed_at': datetime.now(),
            'processing_method': 'basic',
            'content_validation_passed': True,
            'validation_errors': [],
            'validation_warnings': []
        }
        
        return company_data

    def _calculate_basic_quality_score(self, file_info):
        """基於檔案資訊計算基本品質評分"""
        score = 0
        
        file_size = file_info.get('file_size', 0)
        if file_size > 5000:
            score += 3
        elif file_size > 2000:
            score += 2
        elif file_size > 500:
            score += 1
        
        if file_info.get('company_code', 'Unknown') != 'Unknown':
            score += 2
        if file_info.get('company_name', 'Unknown') != 'Unknown':
            score += 2
        
        source = file_info.get('data_source', 'Unknown').lower()
        if 'factset' in source:
            score += 3
        elif source in ['yahoo', 'reuters', 'bloomberg']:
            score += 2
        elif source != 'unknown':
            score += 1
        
        return min(10, max(0, score))

    def _get_quality_status(self, score):
        """根據評分取得品質狀態"""
        if score >= 9:
            return "🟢 完整"
        elif score >= 8:
            return "🟡 良好"
        elif score >= 3:
            return "🟠 部分"
        else:
            return "🔴 不足"

    def _generate_minimal_reports(self, processed_companies):
        """生成最小化報告（當 ReportGenerator 不可用時）"""
        import pandas as pd
        
        print("📄 生成最小化報告...")
        
        summary_data = []
        for company in processed_companies:
            summary_data.append({
                '代號': company.get('company_code', ''),
                '名稱': company.get('company_name', ''),
                '品質評分': company.get('quality_score', 0),
                '狀態': company.get('quality_status', ''),
                '驗證通過': company.get('content_validation_passed', True),
                '處理時間': company.get('processed_at', '')
            })
        
        df = pd.DataFrame(summary_data)
        emergency_file = "data/reports/emergency_summary.csv"
        df.to_csv(emergency_file, index=False, encoding='utf-8-sig')
        print(f"📁 緊急報告已儲存: {emergency_file}")


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description='FactSet 處理系統 v3.6.1 (完整實現)')
    parser.add_argument('command', choices=[
        'process',            # 處理所有 MD 檔案
        'process-recent',     # 處理最近的 MD 檔案
        'process-single',     # 處理單一公司
        'analyze-quality',    # 品質分析
        'analyze-keywords',   # 關鍵字分析
        'analyze-watchlist',  # 觀察名單分析
        'keyword-summary',    # 關鍵字統計報告
        'watchlist-summary',  # 觀察名單統計報告
        'stats',             # 顯示統計資訊
        'validate'           # 驗證環境設定
    ])
    parser.add_argument('--company', help='單一公司代號 (用於 process-single)')
    parser.add_argument('--hours', type=int, default=24, help='最近小時數 (用於 process-recent)')
    parser.add_argument('--no-upload', action='store_true', help='不上傳到 Google Sheets')
    parser.add_argument('--force-upload', action='store_true', help='強制上傳，忽略驗證錯誤')
    parser.add_argument('--min-usage', type=int, default=1, help='關鍵字最小使用次數')
    parser.add_argument('--include-missing', action='store_true', help='包含缺失公司資訊 (用於 watchlist-summary)')
    parser.add_argument('--dry-run', action='store_true', help='預覽模式，不實際執行')
    
    args = parser.parse_args()
    
    # 建立 CLI 實例
    try:
        cli = ProcessCLI()
    except Exception as e:
        print(f"❌ ProcessCLI 初始化失敗: {e}")
        sys.exit(1)
    
    # 預覽模式
    if args.dry_run:
        print("🔍 預覽模式：顯示將要執行的操作")
        print(f"命令: {args.command}")
        print(f"參數: {vars(args)}")
        return
    
    # 執行對應命令
    try:
        if args.command == 'process':
            cli.process_all_md_files(upload_sheets=not args.no_upload, force_upload=args.force_upload)
        
        elif args.command == 'process-recent':
            cli.process_recent_files(hours=args.hours, upload_sheets=not args.no_upload, force_upload=args.force_upload)
            
        elif args.command == 'process-single':
            if not args.company:
                print("❌ 請提供 --company 參數")
                sys.exit(1)
            cli.process_single_company(args.company, upload_sheets=not args.no_upload, force_upload=args.force_upload)
        
        elif args.command == 'analyze-quality':
            cli.analyze_quality_only()
        
        elif args.command == 'analyze-keywords':
            cli.analyze_keywords_only(min_usage=args.min_usage)
        
        elif args.command == 'analyze-watchlist':
            cli.analyze_watchlist_only()
        
        elif args.command == 'keyword-summary':
            cli.generate_keyword_summary(upload_sheets=not args.no_upload, min_usage=args.min_usage)
        
        elif args.command == 'watchlist-summary':
            cli.generate_watchlist_summary(upload_sheets=not args.no_upload, include_missing=args.include_missing)
        
        elif args.command == 'stats':
            cli.show_stats()
        
        elif args.command == 'validate':
            cli.validate_setup()
    
    except KeyboardInterrupt:
        print("\n⏹️ 使用者中斷操作")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()