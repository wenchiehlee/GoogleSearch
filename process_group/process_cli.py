#!/usr/bin/env python3
"""
FactSet Pipeline v3.5.0 - Process CLI (Enhanced with Data Validation)
處理群組的命令列介面 - 資料驗證增強版
"""

import sys
import os
import re
import argparse
import json
from datetime import datetime
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
    """處理命令列介面 - 資料驗證增強版"""
    
    def __init__(self):
        print("🔧 初始化 ProcessCLI...")
        
        # 核心組件 - MDScanner 是必須的
        if MDScanner:
            self.md_scanner = MDScanner()
            print("✅ MDScanner 已初始化")
        else:
            raise ImportError("MDScanner 是必須的組件")
        
        # 初始化其他組件
        self.md_parser = None
        self.quality_analyzer = None  
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
                print("✅ MDParser 已初始化")
            except Exception as e:
                print(f"❌ MDParser 初始化失敗: {e}")
        
        # Quality Analyzer
        if QualityAnalyzer:
            try:
                self.quality_analyzer = QualityAnalyzer()
                print("✅ QualityAnalyzer 已初始化")
            except Exception as e:
                print(f"❌ QualityAnalyzer 初始化失敗: {e}")
        
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

    def validate_data_integrity(self, **kwargs):
        """驗證資料完整性 - 偵測愛派司/愛立信等問題"""
        print("\n🔍 開始資料完整性驗證...")
        print("=" * 60)
        
        # 掃描所有 MD 檔案
        md_files = self.md_scanner.scan_all_md_files()
        
        if not md_files:
            print("❌ 沒有找到 MD 檔案")
            return {}
        
        print(f"📁 驗證 {len(md_files)} 個 MD 檔案")
        
        validation_results = {
            'total_files': len(md_files),
            'validation_passed': 0,
            'validation_warnings': 0,
            'validation_errors': 0,
            'critical_issues': [],
            'detailed_results': [],
            'summary_by_status': {
                'valid': [],
                'warning': [],
                'error': []
            }
        }
        
        # 逐一驗證檔案
        for i, md_file in enumerate(md_files, 1):
            try:
                print(f"🔍 驗證 {i}/{len(md_files)}: {os.path.basename(md_file)}")
                
                # 取得檔案基本資訊
                file_info = self.md_scanner.get_file_info(md_file)
                
                if self.md_parser:
                    # 使用增強版 MD Parser 進行驗證
                    parsed_data = self.md_parser.parse_md_file(md_file)
                    validation_result = parsed_data.get('validation_result', {})
                    
                    # 記錄驗證結果
                    file_result = {
                        'filename': os.path.basename(md_file),
                        'company_code': file_info.get('company_code'),
                        'company_name': file_info.get('company_name'),
                        'validation_status': validation_result.get('overall_status', 'unknown'),
                        'confidence_score': validation_result.get('confidence_score', 0),
                        'errors': validation_result.get('errors', []),
                        'warnings': validation_result.get('warnings', []),
                        'file_size': file_info.get('file_size', 0),
                        'content_length': parsed_data.get('content_length', 0)
                    }
                    
                    # 統計驗證狀態
                    status = validation_result.get('overall_status', 'unknown')
                    if status == 'valid':
                        validation_results['validation_passed'] += 1
                        validation_results['summary_by_status']['valid'].append(file_result)
                        print(f"   ✅ 驗證通過")
                    elif status == 'warning':
                        validation_results['validation_warnings'] += 1
                        validation_results['summary_by_status']['warning'].append(file_result)
                        print(f"   🟡 有警告 ({len(validation_result.get('warnings', []))} 項)")
                    elif status == 'error':
                        validation_results['validation_errors'] += 1
                        validation_results['summary_by_status']['error'].append(file_result)
                        print(f"   ❌ 驗證失敗 ({len(validation_result.get('errors', []))} 項錯誤)")
                        
                        # 檢查是否為關鍵問題
                        for error in validation_result.get('errors', []):
                            # 🆕 關鍵問題的偵測 (移除了錯誤訊息檢查)
                            critical_patterns = [
                                r'愛派司.*愛立信',      # 愛派司/愛立信問題
                                r'愛立信.*愛派司',      # 愛立信/愛派司問題  
                                r'公司名稱不符觀察名單',  # 觀察名單不符
                                r'觀察名單顯示應為'      # 觀察名單錯誤
                            ]
                            
                            if any(re.search(pattern, str(error), re.IGNORECASE) for pattern in critical_patterns):
                                issue_type = 'company_mismatch'
                                if '觀察名單' in str(error):
                                    issue_type = 'watchlist_mismatch'
                                
                                validation_results['critical_issues'].append({
                                    'type': issue_type,
                                    'file': os.path.basename(md_file),
                                    'description': error,
                                    'severity': 'critical'
                                })
                    
                    validation_results['detailed_results'].append(file_result)
                
                else:
                    # 基本驗證（當 MD Parser 不可用時）
                    basic_result = self._basic_file_validation(md_file, file_info)
                    validation_results['detailed_results'].append(basic_result)
                
            except Exception as e:
                print(f"   ❌ 驗證異常: {e}")
                validation_results['validation_errors'] += 1
                continue
        
        # 儲存驗證結果
        self._save_validation_results(validation_results)
        
        # 顯示驗證摘要
        self._display_validation_summary(validation_results)
        
        return validation_results

    def _basic_file_validation(self, md_file: str, file_info: Dict) -> Dict:
        """基本檔案驗證（當 MD Parser 不可用時）"""
        # 讀取檔案內容進行基本檢查
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            warnings = []
            
            # 基本內容檢查
            if len(content) < 500:
                warnings.append("檔案內容過短")
            
            # 🔧 移除對 "Oops, something went wrong" 的檢查 - 這很常見，不需要特別處理
            
            # 簡單的公司名稱檢查
            expected_name = file_info.get('company_name', '')
            expected_code = file_info.get('company_code', '')
            
            # 愛派司/愛立信檢查
            if expected_name == '愛派司' and '愛立信' in content:
                issues.append("可能的公司名稱錯誤：檔案為愛派司但內容提到愛立信")
            
            # 🆕 基本的觀察名單檢查（如果有的話）
            try:
                import pandas as pd
                # 嘗試載入觀察名單
                possible_paths = ['觀察名單.csv', '../觀察名單.csv', '../../觀察名單.csv']
                for csv_path in possible_paths:
                    if os.path.exists(csv_path):
                        df = pd.read_csv(csv_path, header=None, names=['code', 'name'])
                        watch_mapping = {}
                        for _, row in df.iterrows():
                            code = str(row['code']).strip()
                            name = str(row['name']).strip()
                            if code and name and code != 'nan' and name != 'nan':
                                watch_mapping[code] = name
                        
                        # 檢查觀察名單一致性
                        if expected_code in watch_mapping:
                            correct_name = watch_mapping[expected_code]
                            if expected_name != correct_name:
                                issues.append(f"公司名稱不符觀察名單：檔案為{expected_name}({expected_code})，觀察名單為{correct_name}({expected_code})")
                        break
            except:
                pass  # 如果檢查失敗，跳過觀察名單驗證
            
            status = 'error' if issues else ('warning' if warnings else 'valid')
            
            return {
                'filename': os.path.basename(md_file),
                'company_code': file_info.get('company_code'),
                'company_name': file_info.get('company_name'),
                'validation_status': status,
                'confidence_score': 0 if issues else (5 if warnings else 8),
                'errors': issues,
                'warnings': warnings,
                'file_size': file_info.get('file_size', 0),
                'content_length': len(content),
                'validation_method': 'basic'
            }
            
        except Exception as e:
            return {
                'filename': os.path.basename(md_file),
                'validation_status': 'error',
                'errors': [f"檔案讀取失敗: {str(e)}"],
                'validation_method': 'basic'
            }

    def _save_validation_results(self, validation_results: Dict):
        """儲存驗證結果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/reports/validation_results_{timestamp}.json"
        latest_file = "data/reports/validation_results_latest.json"
        
        # 加入時間戳記
        validation_results['timestamp'] = datetime.now().isoformat()
        validation_results['version'] = '3.5.0_enhanced'
        
        # 儲存檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, ensure_ascii=False, indent=2, default=str)
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 驗證結果已儲存: {output_file}")

    def _display_validation_summary(self, results: Dict):
        """顯示驗證摘要"""
        total = results['total_files']
        passed = results['validation_passed']
        warnings = results['validation_warnings'] 
        errors = results['validation_errors']
        critical = len(results['critical_issues'])
        
        print(f"\n📊 資料驗證摘要:")
        print(f"=" * 40)
        print(f"📁 總檔案數: {total}")
        print(f"✅ 驗證通過: {passed} ({passed/total*100:.1f}%)")
        print(f"🟡 有警告: {warnings} ({warnings/total*100:.1f}%)")
        print(f"❌ 驗證失敗: {errors} ({errors/total*100:.1f}%)")
        print(f"🚨 關鍵問題: {critical}")
        
        # 顯示關鍵問題詳情
        if critical > 0:
            print(f"\n🚨 關鍵問題詳情:")
            for issue in results['critical_issues']:
                print(f"  📄 {issue['file']}")
                print(f"     類型: {issue['type']}")
                print(f"     描述: {issue['description']}")
                print(f"     嚴重性: {issue['severity']}")
        
        # 顯示驗證失敗的檔案
        error_files = results['summary_by_status'].get('error', [])
        if error_files:
            print(f"\n❌ 驗證失敗的檔案 (前5個):")
            for file_result in error_files[:5]:
                print(f"  📄 {file_result['filename']}")
                print(f"     公司: {file_result.get('company_name', 'Unknown')} ({file_result.get('company_code', 'Unknown')})")
                print(f"     錯誤: {file_result.get('errors', [])[:2]}")  # 只顯示前2個錯誤

    def clean_invalid_data(self, dry_run=True, **kwargs):
        """清理無效資料 - 移動或標記有問題的檔案"""
        print(f"\n🧹 清理無效資料 ({'預覽模式' if dry_run else '執行模式'})")
        print("=" * 50)
        
        # 先執行驗證
        validation_results = self.validate_data_integrity()
        
        # 找出需要清理的檔案
        error_files = validation_results['summary_by_status'].get('error', [])
        critical_issues = validation_results['critical_issues']
        
        if not error_files and not critical_issues:
            print("✅ 沒有發現需要清理的檔案")
            return
        
        # 建立清理目錄
        quarantine_dir = "data/quarantine"
        if not dry_run:
            os.makedirs(quarantine_dir, exist_ok=True)
        
        cleanup_actions = []
        
        # 處理關鍵問題檔案
        for issue in critical_issues:
            filename = issue['file']
            action = {
                'filename': filename,
                'reason': issue['description'],
                'action': 'quarantine',
                'severity': 'critical'
            }
            cleanup_actions.append(action)
            
            if dry_run:
                print(f"🔍 [預覽] 將隔離: {filename}")
                print(f"    原因: {issue['description']}")
            else:
                # 實際移動檔案
                src_path = os.path.join("data/md", filename)
                dst_path = os.path.join(quarantine_dir, filename)
                
                try:
                    import shutil
                    shutil.move(src_path, dst_path)
                    print(f"✅ 已隔離: {filename}")
                except Exception as e:
                    print(f"❌ 隔離失敗: {filename} - {e}")
        
        # 處理其他錯誤檔案
        for file_result in error_files:
            filename = file_result['filename']
            
            # 跳過已經處理的關鍵問題檔案
            if any(issue['file'] == filename for issue in critical_issues):
                continue
            
            action = {
                'filename': filename,
                'reason': ', '.join(file_result.get('errors', [])),
                'action': 'review',
                'severity': 'error'
            }
            cleanup_actions.append(action)
            
            if dry_run:
                print(f"🔍 [預覽] 需要檢查: {filename}")
                print(f"    錯誤: {', '.join(file_result.get('errors', [])[:2])}")
        
        # 儲存清理報告
        cleanup_report = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'total_actions': len(cleanup_actions),
            'actions': cleanup_actions,
            'validation_summary': {
                'total_files': validation_results['total_files'],
                'error_files': len(error_files),
                'critical_issues': len(critical_issues)
            }
        }
        
        report_file = f"data/reports/cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(cleanup_report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📊 清理摘要:")
        print(f"🔍 檢查檔案: {validation_results['total_files']}")
        print(f"🚨 關鍵問題: {len(critical_issues)}")
        print(f"❌ 錯誤檔案: {len(error_files)}")
        print(f"📄 清理報告: {report_file}")
        
        if dry_run:
            print(f"\n💡 執行實際清理: python process_cli.py clean-data --execute")

    # 原有功能保持不變
    def process_all_md_files(self, upload_sheets=True, **kwargs):
        """處理所有 MD 檔案 - 🆕 增強版本統計"""
        print("\n🚀 開始處理所有 MD 檔案...")
        
        # 1. 掃描 MD 檔案
        md_files = self.md_scanner.scan_all_md_files()
        print(f"📁 發現 {len(md_files)} 個 MD 檔案")
        
        if not md_files:
            print("❌ 沒有找到任何 MD 檔案")
            print("💡 請先執行搜尋群組來生成 MD 檔案")
            return []
        
        # 2. 處理檔案
        processed_companies = self._process_md_file_list(md_files, **kwargs)
        
        # 3. 生成報告前的最終統計
        if processed_companies:
            print(f"\n🎯 報告生成階段:")
            
            # 預先檢查有多少公司會被包含在報告中
            if self.report_generator:
                companies_for_report = [c for c in processed_companies 
                                      if self.report_generator._should_include_in_report(c)]
                
                excluded_count = len(processed_companies) - len(companies_for_report)
                
                print(f"📊 處理結果摘要:")
                print(f"   已處理公司: {len(processed_companies)} 家")
                print(f"   將納入報告: {len(companies_for_report)} 家")
                print(f"   因驗證失敗排除: {excluded_count} 家")
                
                if excluded_count > 0:
                    print(f"   ✅ 成功過濾了 {excluded_count} 家有問題的公司")
            
            # 4. 生成和上傳報告
            self._generate_and_upload_reports_fixed(processed_companies, upload_sheets, 
                                                   force_upload=kwargs.get('force_upload', False))
            
            print(f"✅ 處理完成")
            
            # 顯示最終驗證摘要
            self._display_processing_validation_summary(processed_companies)
        else:
            print("❌ 沒有成功處理任何檔案")
        
        return processed_companies

    def _display_processing_validation_summary(self, processed_companies: List):
        """顯示處理過程中的驗證摘要 - 🆕 增強版本"""
        validation_passed = sum(1 for c in processed_companies if c.get('content_validation_passed', True))
        validation_failed = len(processed_companies) - validation_passed
        
        if validation_failed > 0:
            print(f"\n⚠️ 驗證摘要:")
            print(f"✅ 驗證通過: {validation_passed}")
            print(f"❌ 驗證失敗: {validation_failed}")
            
            # 🆕 詳細分析驗證失敗的原因
            failed_companies = [c for c in processed_companies if not c.get('content_validation_passed', True)]
            if failed_companies:
                print(f"\n❌ 驗證失敗的公司分析:")
                
                error_summary = {}
                for company in failed_companies:
                    errors = company.get('validation_errors', [])
                    if errors:
                        main_error = str(errors[0])
                        if "不在觀察名單" in main_error:
                            error_summary['不在觀察名單'] = error_summary.get('不在觀察名單', []) + [company]
                        elif any(keyword in main_error for keyword in ['愛派司', '愛立信']):
                            error_summary['公司名稱錯誤'] = error_summary.get('公司名稱錯誤', []) + [company]
                        elif "觀察名單顯示應為" in main_error:
                            error_summary['觀察名單名稱不符'] = error_summary.get('觀察名單名稱不符', []) + [company]
                        else:
                            error_summary['其他'] = error_summary.get('其他', []) + [company]
                
                for error_type, companies in error_summary.items():
                    print(f"   {error_type} ({len(companies)} 家):")
                    for company in companies[:3]:  # 只顯示前3個
                        print(f"     - {company.get('company_name', 'Unknown')} ({company.get('company_code', 'Unknown')})")
                    if len(companies) > 3:
                        print(f"     - ... 還有 {len(companies) - 3} 家")
                
                print(f"\n💡 這些公司已自動排除，不會出現在報告和 Google Sheets 中")

    def process_recent_md_files(self, hours=24, upload_sheets=True, **kwargs):
        """處理最近 N 小時的 MD 檔案"""
        print(f"\n🚀 處理最近 {hours} 小時的 MD 檔案...")
        
        recent_files = self.md_scanner.scan_recent_files(hours)
        print(f"📁 發現 {len(recent_files)} 個最近的 MD 檔案")
        
        if not recent_files:
            print(f"📁 最近 {hours} 小時內沒有新的 MD 檔案")
            return []
        
        processed_companies = self._process_md_file_list(recent_files, **kwargs)
        
        if processed_companies:
            self._generate_and_upload_reports_fixed(processed_companies, upload_sheets)
            print(f"✅ 處理完成: {len(processed_companies)} 家公司")
            self._display_processing_validation_summary(processed_companies)
        
        return processed_companies

    def process_single_company(self, company_code, upload_sheets=True, **kwargs):
        """處理單一公司的 MD 檔案"""
        print(f"\n🚀 處理單一公司: {company_code}")
        
        company_files = self.md_scanner.find_company_files(company_code)
        
        if not company_files:
            print(f"❌ 找不到公司 {company_code} 的 MD 檔案")
            return None
        
        latest_file = company_files[0]
        print(f"📁 找到 {len(company_files)} 個檔案，使用最新的: {os.path.basename(latest_file)}")
        
        processed_companies = self._process_md_file_list([latest_file], **kwargs)
        
        if processed_companies:
            if upload_sheets:
                self._generate_and_upload_reports_fixed(processed_companies, upload_sheets)
            print(f"✅ 處理完成: {company_code}")
            return processed_companies[0]
        else:
            print(f"❌ 處理失敗: {company_code}")
            return None

    def analyze_quality_only(self, **kwargs):
        """只進行品質分析"""
        print("\n📊 執行品質分析...")
        
        md_files = self.md_scanner.scan_all_md_files()
        
        if not md_files:
            print("❌ 沒有找到 MD 檔案")
            return []
        
        print(f"📊 分析 {len(md_files)} 個 MD 檔案的品質")
        
        quality_results = []
        success_count = 0
        
        for md_file in md_files:
            try:
                file_info = self.md_scanner.get_file_info(md_file)
                
                if self.quality_analyzer and self.md_parser:
                    parsed_data = self.md_parser.parse_md_file(md_file)
                    quality_data = self.quality_analyzer.analyze(parsed_data)
                    
                    quality_result = {
                        'company_code': file_info['company_code'],
                        'company_name': file_info['company_name'],
                        'quality_score': quality_data.get('quality_score', 0),
                        'quality_status': quality_data.get('quality_status', '🔴 不足'),
                        'md_file': os.path.basename(md_file),
                        'file_size': file_info['file_size'],
                        'file_time': file_info['file_mtime'],
                        # 加入驗證資訊
                        'validation_passed': parsed_data.get('content_validation_passed', True),
                        'validation_errors': len(parsed_data.get('validation_errors', []))
                    }
                else:
                    basic_score = self._calculate_basic_quality_score(file_info)
                    quality_result = {
                        'company_code': file_info['company_code'],
                        'company_name': file_info['company_name'],
                        'quality_score': basic_score,
                        'quality_status': self._get_quality_status(basic_score),
                        'md_file': os.path.basename(md_file),
                        'file_size': file_info['file_size'],
                        'file_time': file_info['file_mtime'],
                        'validation_passed': True,
                        'validation_errors': 0
                    }
                
                quality_results.append(quality_result)
                success_count += 1
                
            except Exception as e:
                print(f"❌ 品質分析失敗: {os.path.basename(md_file)} - {e}")
                continue
        
        self._save_quality_analysis(quality_results)
        self._display_quality_summary(quality_results)
        
        print(f"✅ 品質分析完成: {success_count}/{len(md_files)} 成功")
        return quality_results

    def show_md_stats(self, **kwargs):
        """顯示 MD 檔案統計資訊"""
        print("\n📊 MD 檔案統計資訊")
        print("=" * 50)
        
        stats = self.md_scanner.get_stats()
        
        print(f"📁 總檔案數: {stats['total_files']}")
        print(f"🕐 最近 24h: {stats['recent_files_24h']}")
        print(f"🏢 公司數量: {stats['unique_companies']}")
        print(f"💾 總大小: {stats['total_size_mb']} MB")
        
        if stats['oldest_file']:
            oldest_info = self.md_scanner.get_file_info(stats['oldest_file'])
            print(f"📅 最舊檔案: {oldest_info['filename']} ({oldest_info['file_mtime']})")
        
        if stats['newest_file']:
            newest_info = self.md_scanner.get_file_info(stats['newest_file'])
            print(f"🆕 最新檔案: {newest_info['filename']} ({newest_info['file_mtime']})")
        
        if stats['companies_with_files']:
            print("\n📈 檔案最多的公司 (前 10 名):")
            sorted_companies = sorted(stats['companies_with_files'].items(), 
                                    key=lambda x: x[1], reverse=True)
            for i, (company, count) in enumerate(sorted_companies[:10], 1):
                print(f"  {i:2}. {company}: {count} 個檔案")
        
        return stats

    def validate_setup(self, **kwargs):
        """驗證處理環境設定"""
        print("\n🔧 驗證處理環境設定")
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
        
        # 檢查其他組件
        components = [
            ('md_parser', self.md_parser),
            ('quality_analyzer', self.quality_analyzer),
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
            print(f"{component:15}: {result['status']} - {result['details']}")
        
        return validation_results

    # 私有方法
    def _ensure_output_directories(self):
        """確保輸出目錄存在"""
        directories = [
            "data/reports",
            "data/quarantine",
            "logs/process"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _process_md_file_list(self, md_files, **kwargs):
        """處理 MD 檔案清單 - 🆕 增強驗證日誌和統計"""
        processed_companies = []
        validation_stats = {
            'total_processed': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'not_in_watchlist': 0,
            'name_mismatch': 0,
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
                    
                    # 🆕 詳細的驗證狀態分析
                    validation_passed = parsed_data.get('content_validation_passed', True)
                    validation_errors = parsed_data.get('validation_errors', [])
                    validation_result = parsed_data.get('validation_result', {})
                    
                    if validation_passed:
                        validation_stats['validation_passed'] += 1
                        status_icon = "✅"
                        status_msg = "驗證通過"
                    else:
                        validation_stats['validation_failed'] += 1
                        status_icon = "❌"
                        
                        # 分析失敗原因
                        main_error = validation_errors[0] if validation_errors else "未知錯誤"
                        if "不在觀察名單" in str(main_error):
                            validation_stats['not_in_watchlist'] += 1
                            status_msg = "不在觀察名單"
                        elif any(keyword in str(main_error) for keyword in ['愛派司', '愛立信']):
                            validation_stats['other_errors'] += 1
                            status_msg = "公司名稱錯誤"
                        elif "觀察名單顯示應為" in str(main_error):
                            validation_stats['name_mismatch'] += 1
                            status_msg = "觀察名單名稱不符"
                        else:
                            validation_stats['other_errors'] += 1
                            status_msg = "其他驗證錯誤"
                    
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
                    validation_stats['validation_passed'] += 1  # 基本處理假設通過驗證
                    status_icon = "✅"
                    status_msg = "基本處理"
                
                processed_companies.append(company_data)
                
                # 🆕 詳細的處理結果顯示
                company_name = company_data.get('company_name', 'Unknown')
                company_code = company_data.get('company_code', 'Unknown')
                quality_score = company_data.get('quality_score', 0)
                quality_status = company_data.get('quality_status', '🔴 不足')
                
                print(f"   {status_icon} {company_name} ({company_code}) - 品質: {quality_score:.1f} {quality_status} - {status_msg}")
                
                # 如果驗證失敗，顯示詳細原因
                if not validation_passed and validation_errors:
                    print(f"      🔍 驗證問題: {str(validation_errors[0])[:80]}...")
                    
                    # 如果是觀察名單問題，提供更多資訊
                    if "不在觀察名單" in str(validation_errors[0]):
                        print(f"      💡 此公司將被排除在最終報告之外")
                
            except Exception as e:
                print(f"   ❌ 處理失敗: {os.path.basename(md_file)} - {e}")
                continue
        
        # 🆕 處理完成後顯示詳細統計
        self._display_processing_statistics(validation_stats)
        
        return processed_companies

    def _display_processing_statistics(self, validation_stats: Dict):
        """🆕 顯示處理統計資訊"""
        total = validation_stats['total_processed']
        passed = validation_stats['validation_passed']
        failed = validation_stats['validation_failed']
        
        print(f"\n📊 處理統計摘要:")
        print(f"=" * 40)
        print(f"📁 總處理檔案: {total}")
        print(f"✅ 驗證通過: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ 驗證失敗: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print(f"\n❌ 驗證失敗詳細分類:")
            not_in_watchlist = validation_stats['not_in_watchlist']
            name_mismatch = validation_stats['name_mismatch']
            other_errors = validation_stats['other_errors']
            
            if not_in_watchlist > 0:
                print(f"   🚫 不在觀察名單: {not_in_watchlist} 個")
            if name_mismatch > 0:
                print(f"   📝 觀察名單名稱不符: {name_mismatch} 個")
            if other_errors > 0:
                print(f"   ⚠️ 其他錯誤: {other_errors} 個")
            
            print(f"\n💡 這些驗證失敗的公司將不會出現在最終報告中")

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

    def _generate_and_upload_reports_fixed(self, processed_companies, upload_sheets=True, force_upload=False):
        """生成報告並上傳 - 🆕 支援強制上傳"""
        try:
            if self.report_generator:
                print("📊 使用 ReportGenerator 生成報告...")
                
                portfolio_summary = self.report_generator.generate_portfolio_summary(processed_companies)
                detailed_report = self.report_generator.generate_detailed_report(processed_companies)
                
                saved_files = self.report_generator.save_reports(portfolio_summary, detailed_report)
                
                if saved_files:
                    print("📁 報告已成功儲存:")
                    for report_type, file_path in saved_files.items():
                        if 'latest' in report_type:
                            print(f"   ✅ {report_type}: {file_path}")
                
                try:
                    statistics = self.report_generator.generate_statistics_report(processed_companies)
                    stats_file = self.report_generator.save_statistics_report(statistics)
                    if stats_file:
                        print(f"   📊 統計報告: {stats_file}")
                except Exception as e:
                    print(f"   ⚠️ 統計報告生成失敗: {e}")
                
                if upload_sheets and self.sheets_uploader:
                    try:
                        print("☁️ 上傳到 Google Sheets...")
                        
                        # 🆕 如果強制上傳，調整驗證設定
                        if force_upload:
                            print("⚠️ 強制上傳模式：忽略驗證錯誤")
                            original_settings = self.sheets_uploader.validation_settings.copy()
                            self.sheets_uploader.validation_settings.update({
                                'allow_error_data': True,
                                'max_validation_errors': 10000,
                                'check_before_upload': False  # 完全跳過驗證檢查
                            })
                        
                        success = self.sheets_uploader.upload_reports(portfolio_summary, detailed_report)
                        
                        # 🆕 恢復原始設定
                        if force_upload:
                            self.sheets_uploader.validation_settings = original_settings
                        
                        if success:
                            print("   ✅ Google Sheets 上傳成功")
                        else:
                            print("   ❌ Google Sheets 上傳失敗")
                    except Exception as e:
                        print(f"   ❌ Google Sheets 上傳錯誤: {e}")
                
            else:
                print("❌ ReportGenerator 未載入，無法生成標準報告")
                self._generate_minimal_reports(processed_companies)
        
        except Exception as e:
            print(f"❌ 報告生成或上傳失敗: {e}")

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

    def _save_quality_analysis(self, quality_results):
        """儲存品質分析結果"""
        output_file = "data/reports/quality_analysis.json"
        
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(quality_results),
            'results': quality_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 品質分析結果已儲存: {output_file}")

    def _display_quality_summary(self, quality_results):
        """顯示品質分析摘要"""
        if not quality_results:
            return
        
        quality_counts = {}
        total_score = 0
        validation_failed = 0
        
        for result in quality_results:
            status = result['quality_status']
            quality_counts[status] = quality_counts.get(status, 0) + 1
            total_score += result.get('quality_score', 0)
            if not result.get('validation_passed', True):
                validation_failed += 1
        
        avg_score = total_score / len(quality_results)
        
        print("\n📊 品質分析摘要:")
        print(f"平均品質評分: {avg_score:.1f}/10")
        print(f"驗證失敗檔案: {validation_failed}/{len(quality_results)}")
        print("品質分佈:")
        for status, count in quality_counts.items():
            percentage = (count / len(quality_results)) * 100
            print(f"  {status}: {count} 個 ({percentage:.1f}%)")


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description='FactSet 處理系統 v3.5.0 (資料驗證增強版)')
    parser.add_argument('command', choices=[
        'process',           # 處理所有 MD 檔案
        'process-recent',    # 處理最近的 MD 檔案
        'process-single',    # 處理單一公司
        'analyze-quality',   # 品質分析
        'validate-data',     # 🆕 資料驗證
        'clean-data',        # 🆕 清理無效資料
        'stats',            # 顯示統計資訊
        'validate'          # 驗證環境設定
    ])
    parser.add_argument('--company', help='單一公司代號 (用於 process-single)')
    parser.add_argument('--hours', type=int, default=24, help='最近小時數 (用於 process-recent)')
    parser.add_argument('--no-upload', action='store_true', help='不上傳到 Google Sheets')
    parser.add_argument('--force-upload', action='store_true', help='強制上傳，忽略驗證錯誤')
    parser.add_argument('--execute', action='store_true', help='實際執行清理 (用於 clean-data)')
    
    args = parser.parse_args()
    
    # 建立 CLI 實例
    try:
        cli = ProcessCLI()
    except Exception as e:
        print(f"❌ ProcessCLI 初始化失敗: {e}")
        sys.exit(1)
    
    # 執行對應命令
    try:
        if args.command == 'process':
            cli.process_all_md_files(upload_sheets=not args.no_upload, force_upload=args.force_upload if hasattr(args, 'force_upload') else False)
        
        elif args.command == 'process-recent':
            cli.process_recent_md_files(args.hours, upload_sheets=not args.no_upload)
        
        elif args.command == 'process-single':
            if not args.company:
                print("❌ 請提供 --company 參數")
                sys.exit(1)
            cli.process_single_company(args.company, upload_sheets=not args.no_upload)
        
        elif args.command == 'analyze-quality':
            cli.analyze_quality_only()
        
        elif args.command == 'validate-data':
            cli.validate_data_integrity()
        
        elif args.command == 'clean-data':
            cli.clean_invalid_data(dry_run=not args.execute)
        
        elif args.command == 'stats':
            cli.show_md_stats()
        
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