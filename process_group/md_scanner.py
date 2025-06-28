"""
FactSet Pipeline v3.5.0 - MD Scanner
專門掃描和管理 data/md/ 檔案夾中的 MD 檔案
這是處理群組與檔案系統的唯一介面

檔案名稱: process_group/md_scanner.py
功能:
- 掃描所有 MD 檔案
- 找出最近的檔案
- 依公司代號尋找檔案
- 提取檔案資訊
- 完全獨立，不依賴搜尋群組
"""

import os
import glob
import re
from datetime import datetime, timedelta
from pathlib import Path

class MDScanner:
    """
    MD 檔案掃描器 - 處理群組的檔案系統介面
    負責掃描 data/md/ 目錄中的所有 MD 檔案
    """
    
    def __init__(self, md_dir="data/md"):
        self.md_dir = md_dir
        self._ensure_md_directory()
    
    def scan_all_md_files(self):
        """
        掃描所有 MD 檔案
        返回: 按時間排序的檔案路徑清單 (最新的在前)
        """
        pattern = os.path.join(self.md_dir, "*.md")
        md_files = glob.glob(pattern)
        
        # 按修改時間排序 (最新的在前)
        md_files.sort(key=self._get_file_mtime, reverse=True)
        
        return md_files
    
    def scan_recent_files(self, hours=24):
        """
        掃描最近 N 小時的 MD 檔案
        參數: hours - 小時數 (預設 24 小時)
        返回: 最近檔案清單
        """
        all_files = self.scan_all_md_files()
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_files = []
        for file_path in all_files:
            file_time = self._get_file_datetime(file_path)
            if file_time and file_time > cutoff_time:
                recent_files.append(file_path)
        
        return recent_files
    
    def find_company_files(self, company_code):
        """
        尋找特定公司的所有 MD 檔案
        參數: company_code - 公司代號 (如 "2330")
        返回: 該公司的檔案清單 (按時間排序，最新在前)
        """
        # 檔案名稱格式: {company_code}_{company_name}_{source}_{hash}_{timestamp}.md
        pattern = os.path.join(self.md_dir, f"{company_code}_*.md")
        company_files = glob.glob(pattern)
        
        # 驗證檔案名稱格式正確
        validated_files = []
        for file_path in company_files:
            filename = os.path.basename(file_path)
            if self._is_valid_md_filename(filename, company_code):
                validated_files.append(file_path)
        
        # 按時間排序
        validated_files.sort(key=self._get_file_mtime, reverse=True)
        
        return validated_files
    
    def get_latest_file_per_company(self):
        """
        取得每家公司的最新 MD 檔案
        返回: {company_code: latest_file_path} 字典
        """
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
    
    def get_file_info(self, file_path):
        """
        取得 MD 檔案的詳細資訊
        參數: file_path - 檔案路徑
        返回: 檔案資訊字典
        """
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
            'timestamp_str': name_parts[4] if len(name_parts) >= 5 else 'Unknown'
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
    
    def count_files_by_company(self):
        """
        統計每家公司的檔案數量
        返回: {company_code: file_count} 字典
        """
        all_files = self.scan_all_md_files()
        company_counts = {}
        
        for file_path in all_files:
            company_code = self._extract_company_code(file_path)
            if company_code:
                company_counts[company_code] = company_counts.get(company_code, 0) + 1
        
        return company_counts
    
    def get_stats(self):
        """
        取得 MD 檔案統計資訊
        返回: 統計資訊字典
        """
        all_files = self.scan_all_md_files()
        recent_files = self.scan_recent_files(24)
        company_counts = self.count_files_by_company()
        
        total_size = sum(os.path.getsize(f) for f in all_files if os.path.exists(f))
        
        stats = {
            'total_files': len(all_files),
            'recent_files_24h': len(recent_files),
            'unique_companies': len(company_counts),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'companies_with_files': company_counts,
            'oldest_file': min(all_files, key=self._get_file_mtime) if all_files else None,
            'newest_file': max(all_files, key=self._get_file_mtime) if all_files else None
        }
        
        return stats
    
    # 私有方法
    
    def _ensure_md_directory(self):
        """確保 MD 目錄存在"""
        Path(self.md_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_file_mtime(self, file_path):
        """取得檔案修改時間 (timestamp)"""
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0
    
    def _get_file_datetime(self, file_path):
        """取得檔案修改時間 (datetime 物件)"""
        try:
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp)
        except OSError:
            return None
    
    def _extract_company_code(self, file_path):
        """從檔案路徑提取公司代號"""
        filename = os.path.basename(file_path)
        
        # 檔案名稱格式: {company_code}_{company_name}_{source}_{hash}_{timestamp}.md
        parts = filename.replace('.md', '').split('_')
        
        if len(parts) >= 1:
            company_code = parts[0]
            # 簡單驗證: 公司代號應該是數字
            if company_code.isdigit() and len(company_code) == 4:
                return company_code
        
        return None
    
    def _is_valid_md_filename(self, filename, expected_company_code=None):
        """
        驗證 MD 檔案名稱格式是否正確
        預期格式: {company_code}_{company_name}_{source}_{hash}_{timestamp}.md
        """
        if not filename.endswith('.md'):
            return False
        
        parts = filename.replace('.md', '').split('_')
        
        # 至少要有 4 個部分: 代號_名稱_來源_hash
        if len(parts) < 4:
            return False
        
        company_code = parts[0]
        
        # 驗證公司代號格式 (4位數字)
        if not (company_code.isdigit() and len(company_code) == 4):
            return False
        
        # 如果指定了特定公司代號，要完全匹配
        if expected_company_code and company_code != expected_company_code:
            return False
        
        return True


# 測試和使用範例
if __name__ == "__main__":
    # 建立 MD 掃描器
    scanner = MDScanner()
    
    print("=== MD 檔案掃描器測試 ===")
    
    # 掃描所有檔案
    all_files = scanner.scan_all_md_files()
    print(f"\n找到 {len(all_files)} 個 MD 檔案:")
    for file_path in all_files[:5]:  # 只顯示前 5 個
        info = scanner.get_file_info(file_path)
        print(f"  {info['company_code']} - {info['company_name']} ({info['filename']})")
    
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
    
    # 統計資訊
    stats = scanner.get_stats()
    print(f"\n=== 統計資訊 ===")
    print(f"總檔案數: {stats['total_files']}")
    print(f"最近 24h: {stats['recent_files_24h']}")
    print(f"公司數量: {stats['unique_companies']}")
    print(f"總大小: {stats['total_size_mb']} MB")
    
    # 按公司檔案數量排序
    if stats['companies_with_files']:
        sorted_companies = sorted(stats['companies_with_files'].items(), 
                                key=lambda x: x[1], reverse=True)
        print(f"\n檔案最多的前 5 家公司:")
        for company, count in sorted_companies[:5]:
            print(f"  {company}: {count} 個檔案")