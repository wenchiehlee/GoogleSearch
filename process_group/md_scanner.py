#!/usr/bin/env python3
"""
MD Scanner - FactSet Pipeline v3.6.1 (Refined)
專門掃描和管理 data/md/ 檔案夾中的 MD 檔案
完全獨立，支援觀察名單統計分析

檔案名稱: process_group/md_scanner.py
功能:
- 掃描所有 MD 檔案
- 找出最近的檔案  
- 依公司代號尋找檔案
- 提取檔案資訊
- 支援觀察名單覆蓋統計
- 增強錯誤處理和日誌
"""

import os
import glob
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

class MDScanner:
    """
    MD 檔案掃描器 v3.6.1 (Refined) - 處理群組的檔案系統介面
    負責掃描 data/md/ 目錄中的所有 MD 檔案，支援觀察名單統計
    """

    def __init__(self, md_dir="data/md"):
        self.md_dir = md_dir
        self.version = "3.6.1"
        self._ensure_md_directory()
        
        # 檔案名稱驗證模式
        self.filename_pattern = re.compile(r'^(\d{4})_([^_]+)_([^_]+)_([^_]+)_?.*\.md$')
        
        # 統計資料快取
        self._stats_cache = {}
        self._cache_timestamp = None
        self._cache_duration = 300  # 5分鐘快取
    
    def scan_all_md_files(self) -> List[str]:
        """
        掃描所有 MD 檔案
        返回: 按時間排序的檔案路徑清單 (最新的在前)
        """
        try:
            pattern = os.path.join(self.md_dir, "*.md")
            md_files = glob.glob(pattern)
            
            # 過濾有效的 MD 檔案
            valid_files = []
            for file_path in md_files:
                if self._is_valid_md_file(file_path):
                    valid_files.append(file_path)
                else:
                    print(f"⚠️ 跳過無效檔案: {os.path.basename(file_path)}")
            
            # 按修改時間排序 (最新的在前)
            valid_files.sort(key=self._get_file_mtime, reverse=True)
            
            return valid_files
            
        except Exception as e:
            print(f"❌ 掃描 MD 檔案失敗: {e}")
            return []
    
    def scan_recent_files(self, hours=24) -> List[str]:
        """
        掃描最近 N 小時的 MD 檔案
        參數: hours - 小時數 (預設 24 小時)
        返回: 最近檔案清單
        """
        try:
            all_files = self.scan_all_md_files()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_files = []
            for file_path in all_files:
                file_time = self._get_file_datetime(file_path)
                if file_time and file_time > cutoff_time:
                    recent_files.append(file_path)
            
            return recent_files
            
        except Exception as e:
            print(f"❌ 掃描最近檔案失敗: {e}")
            return []
    
    def find_company_files(self, company_code: str) -> List[str]:
        """
        尋找特定公司的所有 MD 檔案
        參數: company_code - 公司代號 (如 "2330")
        返回: 該公司的檔案清單 (按時間排序，最新在前)
        """
        try:
            # 清理公司代號
            clean_code = str(company_code).strip()
            if not self._is_valid_company_code(clean_code):
                print(f"⚠️ 無效的公司代號格式: {company_code}")
                return []
            
            # 檔案名稱格式: {company_code}_{company_name}_{source}_{hash}_{timestamp}.md
            pattern = os.path.join(self.md_dir, f"{clean_code}_*.md")
            company_files = glob.glob(pattern)
            
            # 驗證檔案名稱格式正確
            validated_files = []
            for file_path in company_files:
                if self._is_valid_md_filename(file_path, clean_code):
                    validated_files.append(file_path)
                else:
                    print(f"⚠️ 檔案格式不符: {os.path.basename(file_path)}")
            
            # 按時間排序
            validated_files.sort(key=self._get_file_mtime, reverse=True)
            
            return validated_files
            
        except Exception as e:
            print(f"❌ 尋找公司檔案失敗 ({company_code}): {e}")
            return []
    
    def get_latest_file_per_company(self) -> Dict[str, str]:
        """
        取得每家公司的最新 MD 檔案
        返回: {company_code: latest_file_path} 字典
        """
        try:
            all_files = self.scan_all_md_files()
            company_latest = {}
            
            for file_path in all_files:
                company_code = self._extract_company_code(file_path)
                if company_code:
                    # 如果是該公司第一個檔案，或者比現有檔案更新
                    if (company_code not in company_latest or 
                        self._get_file_mtime(file_path) > self._get_file_mtime(company_latest[company_code])):
                        company_latest[company_code] = file_path
            
            return company_latest
            
        except Exception as e:
            print(f"❌ 取得最新檔案失敗: {e}")
            return {}
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        取得 MD 檔案的詳細資訊
        參數: file_path - 檔案路徑
        返回: 檔案資訊字典
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            filename = os.path.basename(file_path)
            
            # 解析檔案名稱: 代號_名稱_來源_hash_時間.md
            # 例如: 2330_台積電_factset_abc123_0626_1030.md
            name_parts = filename.replace('.md', '').split('_')
            
            info = {
                'file_path': file_path,
                'filename': filename,
                'file_size': os.path.getsize(file_path),
                'file_mtime': self._get_file_datetime(file_path),
                'company_code': name_parts[0] if len(name_parts) >= 1 else 'Unknown',
                'company_name': name_parts[1] if len(name_parts) >= 2 else 'Unknown',
                'data_source': name_parts[2] if len(name_parts) >= 3 else 'Unknown',
                'file_hash': name_parts[3] if len(name_parts) >= 4 else 'Unknown',
                'timestamp_str': name_parts[4] if len(name_parts) >= 5 else 'Unknown',
                'valid_format': self._is_valid_md_filename(file_path),
                'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
            }
            
            # 嘗試解析時間戳記
            if len(name_parts) >= 5:
                try:
                    # 時間格式: MMDD_HHMM (如 0626_1030)
                    month_day = name_parts[4]
                    hour_min = name_parts[5] if len(name_parts) >= 6 else '0000'
                    
                    if len(month_day) == 4 and len(hour_min) == 4:
                        month = int(month_day[:2])
                        day = int(month_day[2:])
                        hour = int(hour_min[:2])
                        minute = int(hour_min[2:])
                        
                        # 假設是當年
                        current_year = datetime.now().year
                        parsed_time = datetime(current_year, month, day, hour, minute)
                        info['parsed_timestamp'] = parsed_time
                except (ValueError, IndexError):
                    info['parsed_timestamp'] = None
            
            return info
            
        except Exception as e:
            print(f"❌ 取得檔案資訊失敗 ({file_path}): {e}")
            return None
    
    def count_files_by_company(self) -> Dict[str, int]:
        """
        統計每家公司的檔案數量
        返回: {company_code: file_count} 字典
        """
        try:
            all_files = self.scan_all_md_files()
            company_counts = {}
            
            for file_path in all_files:
                company_code = self._extract_company_code(file_path)
                if company_code:
                    company_counts[company_code] = company_counts.get(company_code, 0) + 1
            
            return company_counts
            
        except Exception as e:
            print(f"❌ 統計公司檔案數量失敗: {e}")
            return {}
    
    def get_watchlist_coverage_stats(self, watchlist_codes: List[str]) -> Dict[str, Any]:
        """
        🆕 v3.6.1 計算觀察名單覆蓋統計
        參數: watchlist_codes - 觀察名單公司代號清單
        返回: 覆蓋統計資訊
        """
        try:
            all_files = self.scan_all_md_files()
            processed_codes = set()
            
            # 收集已處理的公司代號
            for file_path in all_files:
                company_code = self._extract_company_code(file_path)
                if company_code:
                    processed_codes.add(company_code)
            
            # 計算覆蓋統計
            total_watchlist = len(watchlist_codes)
            covered_companies = len([code for code in watchlist_codes if code in processed_codes])
            missing_companies = [code for code in watchlist_codes if code not in processed_codes]
            
            coverage_rate = (covered_companies / total_watchlist) * 100 if total_watchlist > 0 else 0
            
            # 按公司代號範圍分析覆蓋情況
            coverage_by_range = self._analyze_coverage_by_range(watchlist_codes, processed_codes)
            
            return {
                'total_watchlist_companies': total_watchlist,
                'companies_with_files': covered_companies,
                'missing_companies': missing_companies,
                'missing_count': len(missing_companies),
                'coverage_rate': round(coverage_rate, 1),
                'coverage_by_range': coverage_by_range,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 觀察名單覆蓋統計失敗: {e}")
            return {
                'total_watchlist_companies': 0,
                'companies_with_files': 0,
                'coverage_rate': 0.0,
                'error': str(e)
            }
    
    def get_stats(self, force_refresh=False) -> Dict[str, Any]:
        """
        取得 MD 檔案統計資訊 (帶快取)
        返回: 統計資訊字典
        """
        try:
            # 檢查快取
            if not force_refresh and self._is_cache_valid():
                return self._stats_cache
            
            all_files = self.scan_all_md_files()
            recent_files = self.scan_recent_files(24)
            company_counts = self.count_files_by_company()
            
            # 計算檔案大小
            total_size = 0
            file_sizes = []
            for f in all_files:
                if os.path.exists(f):
                    size = os.path.getsize(f)
                    total_size += size
                    file_sizes.append(size)
            
            # 計算時間範圍
            oldest_file = min(all_files, key=self._get_file_mtime) if all_files else None
            newest_file = max(all_files, key=self._get_file_mtime) if all_files else None
            
            # 檔案大小統計
            size_stats = {}
            if file_sizes:
                size_stats = {
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'average_size_kb': round(sum(file_sizes) / len(file_sizes) / 1024, 2),
                    'largest_file_mb': round(max(file_sizes) / (1024 * 1024), 2),
                    'smallest_file_kb': round(min(file_sizes) / 1024, 2)
                }
            
            # 數據品質統計
            quality_stats = self._analyze_file_quality(all_files)
            
            stats = {
                'version': self.version,
                'scan_timestamp': datetime.now().isoformat(),
                'total_files': len(all_files),
                'recent_files_24h': len(recent_files),
                'unique_companies': len(company_counts),
                'companies_with_files': company_counts,
                'oldest_file': oldest_file,
                'newest_file': newest_file,
                'file_size_stats': size_stats,
                'quality_stats': quality_stats,
                'top_companies_by_files': self._get_top_companies(company_counts, 10)
            }
            
            # 更新快取
            self._stats_cache = stats
            self._cache_timestamp = datetime.now()
            
            return stats
            
        except Exception as e:
            print(f"❌ 取得統計資訊失敗: {e}")
            return {
                'version': self.version,
                'error': str(e),
                'total_files': 0,
                'unique_companies': 0
            }
    
    # 私有方法
    
    def _ensure_md_directory(self):
        """確保 MD 目錄存在"""
        try:
            Path(self.md_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"❌ 建立 MD 目錄失敗: {e}")
    
    def _get_file_mtime(self, file_path: str) -> float:
        """取得檔案修改時間 (timestamp)"""
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0
    
    def _get_file_datetime(self, file_path: str) -> Optional[datetime]:
        """取得檔案修改時間 (datetime 物件)"""
        try:
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp)
        except OSError:
            return None
    
    def _extract_company_code(self, file_path: str) -> Optional[str]:
        """從檔案路徑提取公司代號"""
        try:
            filename = os.path.basename(file_path)
            
            # 使用正則表達式匹配
            match = self.filename_pattern.match(filename)
            if match:
                company_code = match.group(1)
                if self._is_valid_company_code(company_code):
                    return company_code
            
            # 回退到分割方法
            parts = filename.replace('.md', '').split('_')
            if len(parts) >= 1:
                company_code = parts[0]
                if self._is_valid_company_code(company_code):
                    return company_code
            
            return None
            
        except Exception as e:
            print(f"⚠️ 提取公司代號失敗 ({file_path}): {e}")
            return None
    
    def _is_valid_company_code(self, code: str) -> bool:
        """驗證公司代號格式"""
        try:
            if not code or not isinstance(code, str):
                return False
            
            clean_code = code.strip()
            
            # 必須是4位數字
            if not (clean_code.isdigit() and len(clean_code) == 4):
                return False
            
            # 檢查數字範圍 (台股代號範圍)
            code_num = int(clean_code)
            return 1000 <= code_num <= 9999
            
        except (ValueError, TypeError):
            return False
    
    def _is_valid_md_file(self, file_path: str) -> bool:
        """檢查是否為有效的 MD 檔案"""
        try:
            if not file_path.endswith('.md'):
                return False
            
            if not os.path.exists(file_path):
                return False
            
            # 檢查檔案大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False
            
            # 檢查檔案名稱格式
            return self._is_valid_md_filename(file_path)
            
        except Exception:
            return False
    
    def _is_valid_md_filename(self, file_path: str, expected_company_code: str = None) -> bool:
        """
        驗證 MD 檔案名稱格式是否正確
        預期格式: {company_code}_{company_name}_{source}_{hash}_{timestamp}.md
        """
        try:
            filename = os.path.basename(file_path)
            
            if not filename.endswith('.md'):
                return False
            
            # 使用正則表達式驗證
            match = self.filename_pattern.match(filename)
            if not match:
                return False
            
            company_code = match.group(1)
            
            # 驗證公司代號格式
            if not self._is_valid_company_code(company_code):
                return False
            
            # 如果指定了特定公司代號，要完全匹配
            if expected_company_code and company_code != expected_company_code:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _analyze_coverage_by_range(self, watchlist_codes: List[str], processed_codes: set) -> Dict[str, Dict]:
        """分析不同代號範圍的覆蓋情況"""
        ranges = {
            '1000-2999': {'total': 0, 'covered': 0},
            '3000-5999': {'total': 0, 'covered': 0},
            '6000-8999': {'total': 0, 'covered': 0},
            '9000+': {'total': 0, 'covered': 0}
        }
        
        for code in watchlist_codes:
            try:
                code_num = int(code)
                range_key = None
                
                if 1000 <= code_num <= 2999:
                    range_key = '1000-2999'
                elif 3000 <= code_num <= 5999:
                    range_key = '3000-5999'
                elif 6000 <= code_num <= 8999:
                    range_key = '6000-8999'
                else:
                    range_key = '9000+'
                
                if range_key:
                    ranges[range_key]['total'] += 1
                    if code in processed_codes:
                        ranges[range_key]['covered'] += 1
                        
            except ValueError:
                continue
        
        # 計算覆蓋率
        for range_key, stats in ranges.items():
            if stats['total'] > 0:
                stats['coverage_rate'] = round((stats['covered'] / stats['total']) * 100, 1)
            else:
                stats['coverage_rate'] = 0.0
        
        return ranges
    
    def _analyze_file_quality(self, file_paths: List[str]) -> Dict[str, Any]:
        """分析檔案品質統計"""
        try:
            quality_stats = {
                'valid_format_files': 0,
                'invalid_format_files': 0,
                'empty_files': 0,
                'large_files': 0,  # > 50KB
                'very_large_files': 0,  # > 500KB
                'recent_files': 0,  # 最近7天
                'old_files': 0  # 超過30天
            }
            
            cutoff_recent = datetime.now() - timedelta(days=7)
            cutoff_old = datetime.now() - timedelta(days=30)
            
            for file_path in file_paths:
                try:
                    # 格式檢查
                    if self._is_valid_md_filename(file_path):
                        quality_stats['valid_format_files'] += 1
                    else:
                        quality_stats['invalid_format_files'] += 1
                    
                    # 大小檢查
                    file_size = os.path.getsize(file_path)
                    if file_size == 0:
                        quality_stats['empty_files'] += 1
                    elif file_size > 500 * 1024:  # 500KB
                        quality_stats['very_large_files'] += 1
                    elif file_size > 50 * 1024:  # 50KB
                        quality_stats['large_files'] += 1
                    
                    # 時間檢查
                    file_time = self._get_file_datetime(file_path)
                    if file_time:
                        if file_time > cutoff_recent:
                            quality_stats['recent_files'] += 1
                        elif file_time < cutoff_old:
                            quality_stats['old_files'] += 1
                            
                except Exception as e:
                    print(f"⚠️ 分析檔案品質失敗 ({file_path}): {e}")
                    continue
            
            return quality_stats
            
        except Exception as e:
            print(f"❌ 檔案品質分析失敗: {e}")
            return {}
    
    def _get_top_companies(self, company_counts: Dict[str, int], top_n: int) -> List[Tuple[str, int]]:
        """取得檔案數量最多的前 N 家公司"""
        try:
            sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
            return sorted_companies[:top_n]
        except Exception:
            return []
    
    def _is_cache_valid(self) -> bool:
        """檢查快取是否有效"""
        if not self._cache_timestamp or not self._stats_cache:
            return False
        
        cache_age = (datetime.now() - self._cache_timestamp).total_seconds()
        return cache_age < self._cache_duration


# 測試功能
if __name__ == "__main__":
    # 建立 MD 掃描器
    scanner = MDScanner()
    
    print(f"=== MD 檔案掃描器測試 v{scanner.version} ===")
    
    # 掃描所有檔案
    all_files = scanner.scan_all_md_files()
    print(f"\n找到 {len(all_files)} 個 MD 檔案:")
    for file_path in all_files[:5]:  # 只顯示前 5 個
        info = scanner.get_file_info(file_path)
        if info:
            print(f"  {info['company_code']} - {info['company_name']} ({info['filename']}) - {info['size_mb']}MB")
    
    # 掃描最近檔案
    recent_files = scanner.scan_recent_files(24)
    print(f"\n最近 24 小時內的檔案: {len(recent_files)} 個")
    
    # 尋找特定公司
    company_code = "2330"
    company_files = scanner.find_company_files(company_code)
    print(f"\n公司 {company_code} 的檔案: {len(company_files)} 個")
    
    # 每家公司最新檔案
    latest_per_company = scanner.get_latest_file_per_company()
    print(f"\n每家公司最新檔案: {len(latest_per_company)} 家公司")
    
    # 🆕 觀察名單覆蓋測試
    test_watchlist = ['2330', '2317', '6462', '2454', '1234']  # 包含可能不存在的公司
    coverage_stats = scanner.get_watchlist_coverage_stats(test_watchlist)
    print(f"\n🆕 觀察名單覆蓋統計:")
    print(f"   總觀察名單: {coverage_stats['total_watchlist_companies']}")
    print(f"   有檔案公司: {coverage_stats['companies_with_files']}")
    print(f"   覆蓋率: {coverage_stats['coverage_rate']}%")
    print(f"   缺失公司: {coverage_stats['missing_companies']}")
    
    # 統計資訊
    stats = scanner.get_stats()
    print(f"\n=== 統計資訊 v{stats['version']} ===")
    print(f"總檔案數: {stats['total_files']}")
    print(f"最近 24h: {stats['recent_files_24h']}")
    print(f"公司數量: {stats['unique_companies']}")
    
    if 'file_size_stats' in stats:
        size_stats = stats['file_size_stats']
        print(f"總大小: {size_stats.get('total_size_mb', 0)} MB")
        print(f"平均大小: {size_stats.get('average_size_kb', 0)} KB")
    
    if 'quality_stats' in stats:
        quality_stats = stats['quality_stats']
        print(f"有效格式檔案: {quality_stats.get('valid_format_files', 0)}")
        print(f"無效格式檔案: {quality_stats.get('invalid_format_files', 0)}")
    
    # 按公司檔案數量排序
    if 'top_companies_by_files' in stats:
        top_companies = stats['top_companies_by_files']
        print(f"\n檔案最多的前 5 家公司:")
        for company, count in top_companies[:5]:
            print(f"  {company}: {count} 個檔案")
    
    print(f"\n✅ v{scanner.version} MD 掃描器測試完成！")
    print(f"🆕 新功能: 觀察名單覆蓋統計、增強檔案品質分析、智能快取")