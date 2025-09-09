#!/usr/bin/env python3
"""
Process CLI - FactSet Pipeline v3.6.1
命令列介面用於處理MD檔案、分析和清理功能
完整版包含所有v3.6.1功能
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# 導入Process Group模組
try:
    from md_scanner import MDScanner
    MD_SCANNER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MD掃描功能不可用: {e}")
    MD_SCANNER_AVAILABLE = False

try:
    from md_parser import MDParser
    MD_PARSER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MD解析功能不可用: {e}")
    MD_PARSER_AVAILABLE = False

try:
    from quality_analyzer import QualityAnalyzer
    QUALITY_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 品質分析功能不可用: {e}")
    QUALITY_ANALYZER_AVAILABLE = False

try:
    from keyword_analyzer import KeywordAnalyzer
    KEYWORD_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 關鍵字分析功能不可用: {e}")
    KEYWORD_ANALYZER_AVAILABLE = False

try:
    from watchlist_analyzer import WatchlistAnalyzer
    WATCHLIST_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 觀察名單分析功能不可用: {e}")
    WATCHLIST_ANALYZER_AVAILABLE = False

try:
    from report_generator import ReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 報告生成功能不可用: {e}")
    REPORT_GENERATOR_AVAILABLE = False

try:
    from sheets_uploader import SheetsUploader
    SHEETS_UPLOADER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Google Sheets上傳功能不可用: {e}")
    SHEETS_UPLOADER_AVAILABLE = False

try:
    from md_cleaner import MDFileCleanupManager
    MD_CLEANER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MD清理功能不可用: {e}")
    MD_CLEANER_AVAILABLE = False


class ProcessCLI:
    """
    Process CLI v3.6.1 - FactSet Pipeline 命令列介面
    支援MD檔案處理、分析、清理等完整功能
    """
    
    def __init__(self):
        self.version = "3.6.1"
        
        # 初始化MD掃描器 (必需)
        if MD_SCANNER_AVAILABLE:
            try:
                self.md_scanner = MDScanner()
                print(f"✅ MD掃描器初始化成功 (v{self.md_scanner.version})")
            except Exception as e:
                print(f"❌ MD掃描器初始化失敗: {e}")
                self.md_scanner = None
        else:
            self.md_scanner = None
        
        # 初始化可選模組 (graceful degradation)
        self.md_parser = None
        self.quality_analyzer = None
        self.keyword_analyzer = None
        self.watchlist_analyzer = None
        self.report_generator = None
        self.sheets_uploader = None
        self.md_cleaner = None
        
        self._init_optional_components()
        
        print(f"🔧 Process CLI v{self.version} 初始化完成")
    
    def _init_optional_components(self):
        """初始化可選組件"""
        
        # MD解析器
        if MD_PARSER_AVAILABLE:
            try:
                self.md_parser = MDParser()
                print(f"✅ MD解析器初始化成功 (v{self.md_parser.version})")
            except Exception as e:
                print(f"⚠️ MD解析器初始化失敗: {e}")
        
        # 品質分析器
        if QUALITY_ANALYZER_AVAILABLE:
            try:
                self.quality_analyzer = QualityAnalyzer()
                print(f"✅ 品質分析器初始化成功")
            except Exception as e:
                print(f"⚠️ 品質分析器初始化失敗: {e}")
        
        # 關鍵字分析器 (v3.6.1升級)
        if KEYWORD_ANALYZER_AVAILABLE:
            try:
                self.keyword_analyzer = KeywordAnalyzer()
                print(f"✅ 關鍵字分析器初始化成功")
            except Exception as e:
                print(f"⚠️ 關鍵字分析器初始化失敗: {e}")
        
        # 觀察名單分析器 (v3.6.1新增)
        if WATCHLIST_ANALYZER_AVAILABLE:
            try:
                self.watchlist_analyzer = WatchlistAnalyzer()
                print(f"✅ 觀察名單分析器初始化成功")
            except Exception as e:
                print(f"⚠️ 觀察名單分析器初始化失敗: {e}")
        
        # 報告生成器
        if REPORT_GENERATOR_AVAILABLE:
            try:
                self.report_generator = ReportGenerator()
                print(f"✅ 報告生成器初始化成功")
            except Exception as e:
                print(f"⚠️ 報告生成器初始化失敗: {e}")
        
        # Google Sheets上傳器
        if SHEETS_UPLOADER_AVAILABLE:
            try:
                self.sheets_uploader = SheetsUploader()
                print(f"✅ Google Sheets上傳器初始化成功")
            except Exception as e:
                print(f"⚠️ Google Sheets上傳器初始化失敗: {e}")
        
        # MD清理管理器 (v3.6.1新增)
        if MD_CLEANER_AVAILABLE:
            try:
                self.md_cleaner = MDFileCleanupManager()
                print(f"✅ MD清理功能已啟用 (v{self.md_cleaner.version})")
            except Exception as e:
                print(f"⚠️ MD清理管理器初始化失敗: {e}")
    
    def process_all_md_files(self, upload_sheets=True):
        """處理所有MD檔案 - v3.6.1完整版"""
        if not self.md_scanner:
            print("❌ MD掃描器不可用")
            return False
        
        try:
            print(f"🔄 開始處理所有MD檔案...")
            
            # 1. 掃描檔案
            md_files = self.md_scanner.scan_all_md_files()
            if not md_files:
                print("📁 未找到MD檔案")
                return True
            
            print(f"📄 找到 {len(md_files)} 個MD檔案")
            
            # 2. 解析每個檔案
            processed_companies = []
            parse_errors = 0
            
            for i, md_file in enumerate(md_files, 1):
                try:
                    print(f"📖 處理 {i}/{len(md_files)}: {os.path.basename(md_file)}")
                    
                    if self.md_parser:
                        parsed_data = self.md_parser.parse_md_file(md_file)
                    else:
                        # 簡化解析
                        parsed_data = self._simple_parse_md_file(md_file)
                    
                    # 品質分析
                    if self.quality_analyzer:
                        quality_data = self.quality_analyzer.analyze(parsed_data)
                        parsed_data.update(quality_data)
                    
                    processed_companies.append(parsed_data)
                    
                except Exception as e:
                    print(f"⚠️ 處理檔案失敗 {os.path.basename(md_file)}: {e}")
                    parse_errors += 1
            
            print(f"✅ 處理完成: {len(processed_companies)} 成功, {parse_errors} 失敗")
            
            # 3. 關鍵字分析 (v3.6.1升級)
            pattern_analysis = None
            if self.keyword_analyzer:
                print(f"🔍 執行查詢模式分析...")
                pattern_analysis = self.keyword_analyzer.analyze_query_patterns(processed_companies)
            
            # 4. 觀察名單分析 (v3.6.1新增)
            watchlist_analysis = None
            if self.watchlist_analyzer:
                print(f"📋 執行觀察名單分析...")
                watchlist_analysis = self.watchlist_analyzer.analyze_watchlist_coverage(processed_companies)
            
            # 5. 生成報告
            if self.report_generator:
                print(f"📊 生成報告...")
                portfolio_summary = self.report_generator.generate_portfolio_summary(processed_companies)
                detailed_report = self.report_generator.generate_detailed_report(processed_companies)
                
                pattern_summary = None
                if pattern_analysis:
                    pattern_summary = self.report_generator.generate_keyword_summary(pattern_analysis)
                
                watchlist_summary = None
                if watchlist_analysis:
                    watchlist_summary = self.report_generator.generate_watchlist_summary(watchlist_analysis)
                
                # 儲存報告
                saved_reports = self.report_generator.save_all_reports(
                    portfolio_summary, detailed_report, pattern_summary, watchlist_summary
                )
                
                for report_name, file_path in saved_reports.items():
                    print(f"💾 {report_name} 已儲存: {file_path}")
                
                # 6. 上傳 (可選)
                if upload_sheets and self.sheets_uploader:
                    print(f"☁️ 上傳到Google Sheets...")
                    upload_success = self.sheets_uploader.upload_all_reports(
                        portfolio_summary, detailed_report, pattern_summary, watchlist_summary
                    )
                    if upload_success:
                        print(f"✅ Google Sheets上傳成功")
                    else:
                        print(f"⚠️ Google Sheets上傳失敗")
            
            return True
            
        except Exception as e:
            print(f"❌ 處理MD檔案失敗: {e}")
            return False
    
    def process_recent_md_files(self, hours=24, upload_sheets=True):
        """處理最近的MD檔案"""
        if not self.md_scanner:
            print("❌ MD掃描器不可用")
            return False
        
        try:
            print(f"🔄 處理最近 {hours} 小時的MD檔案...")
            
            recent_files = self.md_scanner.scan_recent_files(hours)
            if not recent_files:
                print(f"📁 最近 {hours} 小時內未找到新檔案")
                return True
            
            print(f"📄 找到 {len(recent_files)} 個最近檔案")
            
            # 使用相同的處理邏輯，但只處理最近檔案
            # 這裡可以重用 process_all_md_files 的邏輯
            return self._process_file_list(recent_files, upload_sheets)
            
        except Exception as e:
            print(f"❌ 處理最近檔案失敗: {e}")
            return False
    
    def process_single_company(self, company_code, upload_sheets=True):
        """處理單一公司"""
        if not self.md_scanner:
            print("❌ MD掃描器不可用")
            return False
        
        try:
            print(f"🔄 處理公司 {company_code}...")
            
            company_files = self.md_scanner.find_company_files(company_code)
            if not company_files:
                print(f"📁 未找到公司 {company_code} 的檔案")
                return False
            
            print(f"📄 找到 {len(company_files)} 個檔案")
            
            return self._process_file_list(company_files, upload_sheets)
            
        except Exception as e:
            print(f"❌ 處理單一公司失敗: {e}")
            return False
    
    def analyze_quality(self):
        """品質分析"""
        if not self.md_scanner:
            print("❌ MD掃描器不可用")
            return False
        
        try:
            print(f"📊 執行品質分析...")
            
            md_files = self.md_scanner.scan_all_md_files()
            if not md_files:
                print("📁 未找到MD檔案")
                return True
            
            processed_companies = []
            for md_file in md_files:
                try:
                    if self.md_parser:
                        parsed_data = self.md_parser.parse_md_file(md_file)
                    else:
                        parsed_data = self._simple_parse_md_file(md_file)
                    
                    if self.quality_analyzer:
                        quality_data = self.quality_analyzer.analyze(parsed_data)
                        parsed_data.update(quality_data)
                    
                    processed_companies.append(parsed_data)
                    
                except Exception as e:
                    print(f"⚠️ 分析檔案失敗: {os.path.basename(md_file)}: {e}")
            
            # 顯示品質統計
            if processed_companies:
                quality_scores = [c.get('quality_score', 0) for c in processed_companies if c.get('quality_score')]
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    print(f"📈 平均品質評分: {avg_quality:.2f}")
                    print(f"📊 高品質檔案 (>8): {len([s for s in quality_scores if s > 8])}")
                    print(f"📊 中等品質檔案 (5-8): {len([s for s in quality_scores if 5 <= s <= 8])}")
                    print(f"📊 低品質檔案 (<5): {len([s for s in quality_scores if s < 5])}")
            
            return True
            
        except Exception as e:
            print(f"❌ 品質分析失敗: {e}")
            return False
    
    def analyze_keywords(self):
        """查詢模式分析 (v3.6.1升級)"""
        if not self.keyword_analyzer:
            print("❌ 關鍵字分析器不可用")
            return False
        
        try:
            print(f"🔍 執行查詢模式分析...")
            
            # 先獲取處理過的公司資料
            processed_companies = self._get_processed_companies()
            if not processed_companies:
                print("📁 無處理過的公司資料")
                return False
            
            # 執行查詢模式分析
            pattern_analysis = self.keyword_analyzer.analyze_query_patterns(processed_companies)
            
            # 顯示分析結果
            if pattern_analysis:
                print(f"📊 查詢模式統計:")
                patterns = pattern_analysis.get('pattern_statistics', {})
                print(f"   總模式數: {patterns.get('total_patterns', 0)}")
                print(f"   有效模式數: {patterns.get('valid_patterns', 0)}")
                print(f"   平均使用次數: {patterns.get('average_usage', 0):.1f}")
                
                # 顯示熱門模式
                top_patterns = pattern_analysis.get('top_patterns', [])
                print(f"📈 熱門查詢模式:")
                for i, (pattern, count) in enumerate(top_patterns[:5], 1):
                    print(f"   {i}. {pattern}: {count} 次")
            
            return True
            
        except Exception as e:
            print(f"❌ 查詢模式分析失敗: {e}")
            return False
    
    def analyze_watchlist(self):
        """觀察名單分析 (v3.6.1新增)"""
        if not self.watchlist_analyzer:
            print("❌ 觀察名單分析器不可用")
            return False
        
        try:
            print(f"📋 執行觀察名單分析...")
            
            # 先獲取處理過的公司資料
            processed_companies = self._get_processed_companies()
            if not processed_companies:
                print("📁 無處理過的公司資料")
                return False
            
            # 執行觀察名單分析
            watchlist_analysis = self.watchlist_analyzer.analyze_watchlist_coverage(processed_companies)
            
            # 顯示分析結果
            if watchlist_analysis:
                print(f"📊 觀察名單覆蓋統計:")
                print(f"   總觀察名單公司: {watchlist_analysis.get('total_watchlist_companies', 0)}")
                print(f"   有MD檔案公司: {watchlist_analysis.get('companies_with_md_files', 0)}")
                print(f"   成功處理公司: {watchlist_analysis.get('companies_processed_successfully', 0)}")
                print(f"   覆蓋率: {watchlist_analysis.get('coverage_rate', 0):.1f}%")
                print(f"   成功率: {watchlist_analysis.get('success_rate', 0):.1f}%")
                
                # 顯示狀態統計
                status_summary = watchlist_analysis.get('company_status_summary', {})
                print(f"📈 處理狀態分布:")
                for status, count in status_summary.items():
                    print(f"   {status}: {count} 家公司")
            
            return True
            
        except Exception as e:
            print(f"❌ 觀察名單分析失敗: {e}")
            return False
    
    def generate_keyword_summary(self, upload_sheets=True, min_usage=1):
        """生成查詢模式統計報告 (v3.6.1升級)"""
        if not self.keyword_analyzer or not self.report_generator:
            print("❌ 關鍵字分析或報告生成功能不可用")
            return False
        
        try:
            print(f"📊 生成查詢模式統計報告...")
            
            processed_companies = self._get_processed_companies()
            if not processed_companies:
                return False
            
            # 執行分析
            pattern_analysis = self.keyword_analyzer.analyze_query_patterns(processed_companies)
            
            # 生成報告
            pattern_summary = self.report_generator.generate_keyword_summary(pattern_analysis)
            
            # 儲存報告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"query-pattern-summary_{timestamp}.csv"
            filepath = os.path.join("data/reports", filename)
            
            os.makedirs("data/reports", exist_ok=True)
            pattern_summary.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"💾 查詢模式報告已儲存: {filename}")
            
            # 上傳到Sheets
            if upload_sheets and self.sheets_uploader:
                upload_success = self.sheets_uploader._upload_keyword_summary(pattern_summary)
                if upload_success:
                    print(f"☁️ 已上傳到Google Sheets")
            
            return True
            
        except Exception as e:
            print(f"❌ 生成查詢模式報告失敗: {e}")
            return False
    
    def generate_watchlist_summary(self, upload_sheets=True, include_missing=False):
        """生成觀察名單統計報告 (v3.6.1新增)"""
        if not self.watchlist_analyzer or not self.report_generator:
            print("❌ 觀察名單分析或報告生成功能不可用")
            return False
        
        try:
            print(f"📋 生成觀察名單統計報告...")
            
            processed_companies = self._get_processed_companies()
            if not processed_companies:
                return False
            
            # 執行分析
            watchlist_analysis = self.watchlist_analyzer.analyze_watchlist_coverage(processed_companies)
            
            # 生成報告
            watchlist_summary = self.report_generator.generate_watchlist_summary(watchlist_analysis)
            
            # 儲存報告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"watchlist-summary_{timestamp}.csv"
            filepath = os.path.join("data/reports", filename)
            
            os.makedirs("data/reports", exist_ok=True)
            watchlist_summary.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"💾 觀察名單報告已儲存: {filename}")
            
            # 上傳到Sheets
            if upload_sheets and self.sheets_uploader:
                upload_success = self.sheets_uploader._upload_watchlist_summary(watchlist_summary)
                if upload_success:
                    print(f"☁️ 已上傳到Google Sheets")
            
            return True
            
        except Exception as e:
            print(f"❌ 生成觀察名單報告失敗: {e}")
            return False
    
    # MD檔案清理功能 (v3.6.1新增)
    
    def cleanup_md_files(self, days=90, quality_threshold=8, dry_run=True, 
                        create_backup=True, force=False, generate_report=True):
        """MD檔案清理命令 - 基於財務數據發布日期"""
        if not self.md_cleaner:
            print("❌ MD清理功能不可用")
            return False
        
        try:
            print(f"🧹 開始MD檔案清理...")
            print(f"   保留期限: {days} 天")
            print(f"   質量閾值: {quality_threshold}")
            print(f"   模式: {'預覽' if dry_run else '實際執行'}")
            
            # 掃描MD檔案
            md_files = self.md_cleaner.scan_md_files()
            if not md_files:
                print("📁 未找到MD檔案")
                return True
            
            # 生成清理計劃
            plan = self.md_cleaner.analyze_files_for_cleanup(
                md_files, 
                retention_days=days, 
                quality_threshold=quality_threshold
            )
            
            # 安全檢查
            if not plan.safety_checks_passed and not force and not dry_run:
                print(f"\n⚠️ 安全檢查未通過，清理計劃存在風險:")
                for warning in plan.warnings:
                    print(f"   - {warning}")
                print(f"\n💡 選項:")
                print(f"   1. 使用 --dry-run 預覽詳細資訊")
                print(f"   2. 使用 --force 強制執行")
                print(f"   3. 調整 --days 或 --quality-threshold 參數")
                return False
            
            # 執行清理
            result = self.md_cleaner.execute_cleanup(
                plan, 
                dry_run=dry_run, 
                create_backup=create_backup
            )
            
            # 生成報告
            if generate_report:
                report = self.md_cleaner.generate_cleanup_report(md_files, plan, result)
                self._save_cleanup_report(report, dry_run)
            
            return result.files_deleted > 0 or dry_run
            
        except Exception as e:
            print(f"❌ MD檔案清理失敗: {e}")
            return False
    
    def show_md_cleanup_preview(self, days=90, quality_threshold=8, show_details=False):
        """顯示MD檔案清理預覽"""
        if not self.md_cleaner:
            print("❌ MD清理功能不可用")
            return False
        
        try:
            print(f"🔍 MD檔案清理預覽 (保留期: {days}天, 質量閾值: {quality_threshold})")
            
            # 掃描和分析檔案
            md_files = self.md_cleaner.scan_md_files()
            if not md_files:
                print("📁 未找到MD檔案")
                return True
            
            plan = self.md_cleaner.analyze_files_for_cleanup(
                md_files, retention_days=days, quality_threshold=quality_threshold
            )
            
            # 顯示詳細預覽
            print(f"\n📋 清理計劃詳情:")
            print(f"   📄 總檔案數: {plan.total_files}")
            print(f"   🗑️  刪除候選: {len(plan.deletion_candidates)}")
            print(f"   💾 保留檔案: {len(plan.preserved_files)}")
            print(f"   ❓ 無日期檔案: {len(plan.no_date_files)}")
            print(f"   💽 預估節省: {self.md_cleaner._format_size(plan.estimated_space_saved)}")
            
            # 顯示刪除候選詳情
            if plan.deletion_candidates and show_details:
                print(f"\n🗑️  刪除候選檔案清單:")
                for i, file_info in enumerate(plan.deletion_candidates):
                    date_str = file_info.md_date.strftime('%Y-%m-%d') if file_info.md_date else '無日期'
                    quality_str = f"(Q:{file_info.quality_score:.1f})" if file_info.quality_score else "(無評分)"
                    size_str = self.md_cleaner._format_size(file_info.file_size)
                    print(f"   {i+1:3d}. {file_info.filename}")
                    print(f"        日期: {date_str} | 年齡: {file_info.age_days}天 | 大小: {size_str} {quality_str}")
                    print(f"        原因: {file_info.preservation_reason}")
            
            # 安全檢查結果
            if plan.safety_checks_passed:
                print(f"\n✅ 安全檢查通過，可以執行清理")
            else:
                print(f"\n⚠️  安全檢查警告:")
                for warning in plan.warnings:
                    print(f"   - {warning}")
                print(f"\n💡 建議使用 --force 參數強制執行或調整參數")
            
            return True
            
        except Exception as e:
            print(f"❌ 預覽生成失敗: {e}")
            return False
    
    def analyze_md_files(self):
        """分析MD檔案狀態"""
        if not self.md_cleaner:
            print("❌ MD清理功能不可用")
            return False
        
        try:
            print(f"📊 分析MD檔案狀態...")
            
            # 獲取統計資訊
            stats = self.md_cleaner.get_statistics()
            
            print(f"\n📋 MD檔案目錄統計:")
            print(f"   📁 目錄: {self.md_cleaner.md_dir}")
            print(f"   📄 總檔案數: {stats['total_files']}")
            print(f"   💾 總大小: {stats.get('total_size_formatted', '0 B')}")
            print(f"   📅 日期提取成功率: {stats.get('date_extraction_success_rate', 0):.1f}%")
            print(f"   🔧 解析器可用: {'是' if stats.get('parser_available', False) else '否'}")
            
            if stats.get('age_statistics'):
                age_stats = stats['age_statistics']
                print(f"\n📈 年齡統計:")
                print(f"   平均年齡: {age_stats.get('average_age_days', 0):.1f} 天")
                print(f"   中位數年齡: {age_stats.get('median_age_days', 0):.1f} 天")
                print(f"   最舊檔案: {age_stats.get('oldest_file_days', 0)} 天")
                print(f"   最新檔案: {age_stats.get('newest_file_days', 0)} 天")
            
            if stats.get('quality_statistics'):
                quality_stats = stats['quality_statistics']
                print(f"\n⭐ 質量統計:")
                print(f"   平均質量: {quality_stats.get('average_quality', 0):.1f}")
                print(f"   最高質量: {quality_stats.get('highest_quality', 0):.1f}")
                print(f"   最低質量: {quality_stats.get('lowest_quality', 0):.1f}")
            
            # 年齡分布
            if stats.get('age_distribution'):
                print(f"\n📊 年齡分布:")
                for age_group, count in stats['age_distribution'].items():
                    print(f"   {age_group}: {count} 檔案")
            
            # 質量分布
            if stats.get('quality_distribution'):
                print(f"\n🏆 質量分布:")
                for quality_group, count in stats['quality_distribution'].items():
                    print(f"   {quality_group}: {count} 檔案")
            
            # 熱門公司
            if stats.get('top_companies'):
                print(f"\n🏢 檔案數最多的公司 (Top 5):")
                for i, (company, count) in enumerate(list(stats['top_companies'].items())[:5]):
                    print(f"   {i+1}. {company}: {count} 檔案")
            
            return True
            
        except Exception as e:
            print(f"❌ MD檔案分析失敗: {e}")
            return False
    
    def show_statistics(self):
        """顯示統計資訊"""
        if not self.md_scanner:
            print("❌ MD掃描器不可用")
            return False
        
        try:
            print(f"📊 Process CLI v{self.version} 統計資訊")
            
            # MD掃描器統計
            stats = self.md_scanner.get_stats()
            print(f"\n📄 MD檔案統計:")
            print(f"   總檔案數: {stats['total_files']}")
            print(f"   最近24h: {stats['recent_files_24h']}")
            print(f"   公司數量: {stats['unique_companies']}")
            
            if 'file_size_stats' in stats:
                size_stats = stats['file_size_stats']
                print(f"   總大小: {size_stats.get('total_size_mb', 0)} MB")
                print(f"   平均大小: {size_stats.get('average_size_kb', 0)} KB")
            
            # 組件狀態
            print(f"\n🔧 組件狀態:")
            print(f"   MD掃描器: {'✅' if self.md_scanner else '❌'}")
            print(f"   MD解析器: {'✅' if self.md_parser else '❌'}")
            print(f"   品質分析器: {'✅' if self.quality_analyzer else '❌'}")
            print(f"   關鍵字分析器: {'✅' if self.keyword_analyzer else '❌'}")
            print(f"   觀察名單分析器: {'✅' if self.watchlist_analyzer else '❌'}")
            print(f"   報告生成器: {'✅' if self.report_generator else '❌'}")
            print(f"   Google Sheets上傳: {'✅' if self.sheets_uploader else '❌'}")
            print(f"   MD清理功能: {'✅' if self.md_cleaner else '❌'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 統計資訊獲取失敗: {e}")
            return False
    
    def validate_setup(self):
        """驗證環境設定"""
        try:
            print(f"🔍 驗證 Process CLI v{self.version} 環境設定...")
            
            validation_results = {}
            
            # 驗證MD掃描器
            if self.md_scanner:
                md_files = self.md_scanner.scan_all_md_files()
                validation_results['md_scanner'] = f"✅ 找到 {len(md_files)} 個檔案"
            else:
                validation_results['md_scanner'] = "❌ MD掃描器不可用"
            
            # 驗證其他組件
            validation_results['md_parser'] = "✅ MD解析器已載入" if self.md_parser else "❌ MD解析器不可用"
            validation_results['quality_analyzer'] = "✅ 品質分析器已載入" if self.quality_analyzer else "❌ 品質分析器不可用"
            validation_results['keyword_analyzer'] = "✅ 關鍵字分析器已載入" if self.keyword_analyzer else "❌ 關鍵字分析器不可用"
            validation_results['watchlist_analyzer'] = "✅ 觀察名單分析器已載入" if self.watchlist_analyzer else "❌ 觀察名單分析器不可用"
            validation_results['report_generator'] = "✅ 報告生成器已載入" if self.report_generator else "❌ 報告生成器不可用"
            validation_results['sheets_uploader'] = "✅ Google Sheets上傳器已載入" if self.sheets_uploader else "❌ Google Sheets上傳器不可用"
            validation_results['md_cleaner'] = "✅ MD清理功能已載入" if self.md_cleaner else "❌ MD清理功能不可用"
            
            # 顯示驗證結果
            print(f"\n📋 驗證結果:")
            for component, status in validation_results.items():
                print(f"   {component}: {status}")
            
            # 檢查觀察名單
            if self.watchlist_analyzer:
                watchlist_size = len(self.watchlist_analyzer.watchlist_mapping)
                print(f"\n📋 觀察名單: 載入 {watchlist_size} 家公司")
            
            # 檢查目錄結構
            directories = ['data', 'data/md', 'data/reports']
            print(f"\n📁 目錄結構:")
            for directory in directories:
                exists = os.path.exists(directory)
                print(f"   {directory}: {'✅' if exists else '❌'}")
                if not exists:
                    os.makedirs(directory, exist_ok=True)
                    print(f"      已創建目錄: {directory}")
            
            return True
            
        except Exception as e:
            print(f"❌ 環境驗證失敗: {e}")
            return False
    
    # 輔助方法
    
    def _process_file_list(self, file_list, upload_sheets=True):
        """處理指定的檔案清單"""
        processed_companies = []
        
        for md_file in file_list:
            try:
                if self.md_parser:
                    parsed_data = self.md_parser.parse_md_file(md_file)
                else:
                    parsed_data = self._simple_parse_md_file(md_file)
                
                if self.quality_analyzer:
                    quality_data = self.quality_analyzer.analyze(parsed_data)
                    parsed_data.update(quality_data)
                
                processed_companies.append(parsed_data)
                
            except Exception as e:
                print(f"⚠️ 處理檔案失敗: {os.path.basename(md_file)}: {e}")
        
        # 生成和上傳報告
        if processed_companies and self.report_generator:
            portfolio_summary = self.report_generator.generate_portfolio_summary(processed_companies)
            detailed_report = self.report_generator.generate_detailed_report(processed_companies)
            
            if upload_sheets and self.sheets_uploader:
                self.sheets_uploader.upload_all_reports(portfolio_summary, detailed_report)
        
        return len(processed_companies) > 0
    
    def _simple_parse_md_file(self, file_path):
        """簡化的MD檔案解析 (當MD解析器不可用時)"""
        filename = os.path.basename(file_path)
        parts = filename.replace('.md', '').split('_')
        
        return {
            'filename': filename,
            'company_code': parts[0] if len(parts) >= 1 else 'Unknown',
            'company_name': parts[1] if len(parts) >= 2 else 'Unknown',
            'data_source': parts[2] if len(parts) >= 3 else 'Unknown',
            'file_mtime': datetime.fromtimestamp(os.path.getmtime(file_path)),
            'search_keywords': [],
            'quality_score': 5.0,  # 預設分數
            'has_eps_data': False,
            'has_target_price': False,
            'has_analyst_info': False
        }
    
    def _get_processed_companies(self):
        """獲取處理過的公司資料"""
        if not self.md_scanner:
            return []
        
        md_files = self.md_scanner.scan_all_md_files()
        processed_companies = []
        
        for md_file in md_files:
            try:
                if self.md_parser:
                    parsed_data = self.md_parser.parse_md_file(md_file)
                else:
                    parsed_data = self._simple_parse_md_file(md_file)
                
                if self.quality_analyzer:
                    quality_data = self.quality_analyzer.analyze(parsed_data)
                    parsed_data.update(quality_data)
                
                processed_companies.append(parsed_data)
                
            except Exception as e:
                continue
        
        return processed_companies
    
    def _save_cleanup_report(self, report: Dict[str, Any], dry_run: bool):
        """儲存清理報告"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            mode = "preview" if dry_run else "execution"
            
            # 確保報告目錄存在
            reports_dir = "data/reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # 儲存JSON報告
            report_filename = f"md_cleanup_{mode}_{timestamp}.json"
            report_path = os.path.join(reports_dir, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # 儲存最新版本
            latest_path = os.path.join(reports_dir, f"md_cleanup_{mode}_latest.json")
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 清理報告已儲存: {report_filename}")
            
        except Exception as e:
            print(f"⚠️ 報告儲存失敗: {e}")


def main():
    """主程式入口點"""
    parser = argparse.ArgumentParser(description='FactSet 處理系統 v3.6.1 (含MD檔案清理)')
    parser.add_argument('command', choices=[
        'process',            # 處理所有 MD 檔案
        'process-recent',     # 處理最近的 MD 檔案
        'process-single',     # 處理單一公司
        'analyze-quality',    # 品質分析
        'analyze-keywords',   # 查詢模式分析
        'analyze-watchlist',  # 觀察名單分析
        'keyword-summary',    # 查詢模式統計報告
        'watchlist-summary',  # 觀察名單統計報告
        'cleanup',           # MD檔案清理
        'cleanup-preview',   # MD檔案清理預覽
        'analyze-md',        # MD檔案狀態分析
        'stats',             # 顯示統計資訊
        'validate'           # 驗證環境設定
    ])
    
    # 現有參數
    parser.add_argument('--company', help='公司代號')
    parser.add_argument('--hours', type=int, default=24, help='小時數')
    parser.add_argument('--no-upload', action='store_true', help='不上傳到 Sheets')
    parser.add_argument('--force-upload', action='store_true', help='強制上傳，忽略驗證錯誤')
    parser.add_argument('--min-usage', type=int, default=1, help='查詢模式最小使用次數')
    parser.add_argument('--include-missing', action='store_true', help='包含缺失公司資訊')
    parser.add_argument('--dry-run', action='store_true', help='預覽模式，不實際執行')
    
    # 新增清理相關參數
    parser.add_argument('--days', type=int, default=90, help='MD檔案保留天數 (預設: 90)')
    parser.add_argument('--quality-threshold', type=float, default=8, help='高質量檔案延長保留閾值 (預設: 8)')
    parser.add_argument('--no-backup', action='store_true', help='清理時不創建備份')
    parser.add_argument('--force', action='store_true', help='強制執行清理，忽略安全檢查')
    parser.add_argument('--show-details', action='store_true', help='顯示詳細的檔案清單')
    parser.add_argument('--no-report', action='store_true', help='不生成清理報告')
    
    args = parser.parse_args()
    
    # 創建CLI實例
    cli = ProcessCLI()
    success = False
    
    try:
        # 命令處理
        if args.command == 'process':
            success = cli.process_all_md_files(upload_sheets=not args.no_upload)
        elif args.command == 'process-recent':
            success = cli.process_recent_md_files(hours=args.hours, upload_sheets=not args.no_upload)
        elif args.command == 'process-single':
            if not args.company:
                print("❌ 處理單一公司需要指定 --company 參數")
                success = False
            else:
                success = cli.process_single_company(args.company, upload_sheets=not args.no_upload)
        elif args.command == 'analyze-quality':
            success = cli.analyze_quality()
        elif args.command == 'analyze-keywords':
            success = cli.analyze_keywords()
        elif args.command == 'analyze-watchlist':
            success = cli.analyze_watchlist()
        elif args.command == 'keyword-summary':
            success = cli.generate_keyword_summary(upload_sheets=not args.no_upload, min_usage=args.min_usage)
        elif args.command == 'watchlist-summary':
            success = cli.generate_watchlist_summary(upload_sheets=not args.no_upload, include_missing=args.include_missing)
        elif args.command == 'cleanup':
            success = cli.cleanup_md_files(
                days=args.days,
                quality_threshold=args.quality_threshold,
                dry_run=args.dry_run,
                create_backup=not args.no_backup,
                force=args.force,
                generate_report=not args.no_report
            )
        elif args.command == 'cleanup-preview':
            success = cli.show_md_cleanup_preview(
                days=args.days,
                quality_threshold=args.quality_threshold,
                show_details=args.show_details
            )
        elif args.command == 'analyze-md':
            success = cli.analyze_md_files()
        elif args.command == 'stats':
            success = cli.show_statistics()
        elif args.command == 'validate':
            success = cli.validate_setup()
        else:
            print(f"❌ 未知命令: {args.command}")
            success = False
    
    except KeyboardInterrupt:
        print(f"\n⚠️ 用戶中斷操作")
        success = False
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        success = False
    
    # 退出程式碼
    exit_code = 0 if success else 1
    print(f"\n🏁 執行完成 (退出碼: {exit_code})")
    exit(exit_code)


if __name__ == "__main__":
    main()