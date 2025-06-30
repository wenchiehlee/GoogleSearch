#!/usr/bin/env python3
"""
Process Logger - FactSet Pipeline v3.6.1
日誌系統 (可選) - ~120 行
"""

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class ProcessLogger:
    """處理群組日誌系統 - v3.6.1 可選組件"""
    
    def __init__(self, log_dir="logs/process", enable_file_logging=True, enable_console_logging=True):
        """初始化日誌系統"""
        self.log_dir = log_dir
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        
        # 確保日誌目錄存在
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # 設定日誌格式
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.date_format = '%Y-%m-%d %H:%M:%S'
        
        # 初始化 logger
        self.logger = self._setup_logger()
        
        # 操作統計
        self.operation_stats = {
            'start_time': datetime.now().isoformat(),
            'operations_logged': 0,
            'errors_logged': 0,
            'warnings_logged': 0
        }
        
        self.info("ProcessLogger v3.6.1 已初始化")

    def _setup_logger(self) -> logging.Logger:
        """設定 logger"""
        logger = logging.getLogger('FactSetProcess')
        logger.setLevel(logging.DEBUG)
        
        # 清除現有的 handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 檔案日誌 handler
        if self.enable_file_logging:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(self.log_dir, f'process_log_{timestamp}.log')
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(self.log_format, self.date_format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # 控制台日誌 handler
        if self.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger

    def info(self, message: str, extra_data: Optional[Dict] = None):
        """記錄信息"""
        self._log_with_stats(logging.INFO, message, extra_data)

    def warning(self, message: str, extra_data: Optional[Dict] = None):
        """記錄警告"""
        self.operation_stats['warnings_logged'] += 1
        self._log_with_stats(logging.WARNING, message, extra_data)

    def error(self, message: str, extra_data: Optional[Dict] = None):
        """記錄錯誤"""
        self.operation_stats['errors_logged'] += 1
        self._log_with_stats(logging.ERROR, message, extra_data)

    def debug(self, message: str, extra_data: Optional[Dict] = None):
        """記錄調試信息"""
        self._log_with_stats(logging.DEBUG, message, extra_data)

    def _log_with_stats(self, level: int, message: str, extra_data: Optional[Dict] = None):
        """記錄日誌並更新統計"""
        self.operation_stats['operations_logged'] += 1
        
        # 如果有額外數據，格式化訊息
        if extra_data:
            formatted_message = f"{message} | Data: {json.dumps(extra_data, default=str, ensure_ascii=False)}"
        else:
            formatted_message = message
        
        self.logger.log(level, formatted_message)

    def log_company_processing(self, company_code: str, company_name: str, 
                             status: str, quality_score: float, **kwargs):
        """記錄公司處理狀態"""
        extra_data = {
            'company_code': company_code,
            'company_name': company_name,
            'status': status,
            'quality_score': quality_score,
            **kwargs
        }
        
        if status == 'success':
            self.info(f"✅ 公司處理成功: {company_name} ({company_code}) - 品質: {quality_score}", extra_data)
        elif status == 'warning':
            self.warning(f"⚠️ 公司處理有警告: {company_name} ({company_code})", extra_data)
        else:
            self.error(f"❌ 公司處理失敗: {company_name} ({company_code})", extra_data)

    def log_validation_result(self, company_code: str, validation_result: Dict):
        """記錄驗證結果"""
        validation_status = validation_result.get('overall_status', 'unknown')
        validation_errors = validation_result.get('errors', [])
        
        extra_data = {
            'company_code': company_code,
            'validation_result': validation_result
        }
        
        if validation_status == 'valid':
            self.info(f"✅ 驗證通過: {company_code}", extra_data)
        elif validation_status == 'error':
            error_preview = str(validation_errors[0])[:50] if validation_errors else "未知錯誤"
            self.error(f"❌ 驗證失敗: {company_code} - {error_preview}...", extra_data)
        else:
            self.warning(f"⚠️ 驗證狀態未知: {company_code}", extra_data)

    def log_keyword_analysis(self, total_keywords: int, unique_keywords: int, 
                           top_keywords: list, **kwargs):
        """記錄關鍵字分析結果"""
        extra_data = {
            'total_keywords': total_keywords,
            'unique_keywords': unique_keywords,
            'top_keywords': top_keywords[:5],  # 只記錄前5個
            **kwargs
        }
        
        self.info(f"🔍 關鍵字分析完成: 總數 {total_keywords}, 唯一 {unique_keywords}", extra_data)

    def log_watchlist_analysis(self, total_companies: int, coverage_rate: float, 
                             success_rate: float, **kwargs):
        """記錄觀察名單分析結果"""
        extra_data = {
            'total_companies': total_companies,
            'coverage_rate': coverage_rate,
            'success_rate': success_rate,
            **kwargs
        }
        
        self.info(f"📋 觀察名單分析完成: {total_companies} 家公司, 覆蓋率 {coverage_rate}%, 成功率 {success_rate}%", extra_data)

    def log_report_generation(self, report_type: str, record_count: int, 
                            file_path: str, **kwargs):
        """記錄報告生成"""
        extra_data = {
            'report_type': report_type,
            'record_count': record_count,
            'file_path': file_path,
            **kwargs
        }
        
        self.info(f"📄 報告生成完成: {report_type} ({record_count} 筆記錄) -> {file_path}", extra_data)

    def log_sheets_upload(self, report_type: str, success: bool, **kwargs):
        """記錄 Google Sheets 上傳"""
        extra_data = {
            'report_type': report_type,
            'success': success,
            **kwargs
        }
        
        if success:
            self.info(f"☁️ Google Sheets 上傳成功: {report_type}", extra_data)
        else:
            self.error(f"❌ Google Sheets 上傳失敗: {report_type}", extra_data)

    def get_stats(self) -> Dict[str, Any]:
        """取得日誌統計"""
        current_time = datetime.now()
        start_time = datetime.fromisoformat(self.operation_stats['start_time'])
        duration = current_time - start_time
        
        return {
            **self.operation_stats,
            'current_time': current_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'log_directory': self.log_dir,
            'file_logging_enabled': self.enable_file_logging,
            'console_logging_enabled': self.enable_console_logging
        }

    def save_stats(self):
        """儲存統計資訊"""
        stats = self.get_stats()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_file = os.path.join(self.log_dir, f'process_stats_{timestamp}.json')
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
        
        self.info(f"📊 統計資訊已儲存: {stats_file}")
        return stats_file

    def close(self):
        """關閉日誌系統"""
        # 記錄最終統計
        final_stats = self.get_stats()
        self.info(f"📊 ProcessLogger 關閉 - 總操作: {final_stats['operations_logged']}, 錯誤: {final_stats['errors_logged']}, 警告: {final_stats['warnings_logged']}")
        
        # 儲存統計
        self.save_stats()
        
        # 關閉所有 handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


# 全域 logger 實例 (可選使用)
_global_logger: Optional[ProcessLogger] = None

def get_logger() -> ProcessLogger:
    """取得全域 logger 實例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = ProcessLogger()
    return _global_logger

def init_logger(**kwargs) -> ProcessLogger:
    """初始化全域 logger"""
    global _global_logger
    _global_logger = ProcessLogger(**kwargs)
    return _global_logger

def close_logger():
    """關閉全域 logger"""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None


# 測試功能
if __name__ == "__main__":
    print("=== Process Logger 測試 v3.6.1 ===")
    
    # 建立 logger
    logger = ProcessLogger()
    
    # 測試各種日誌記錄
    logger.info("測試信息記錄")
    logger.warning("測試警告記錄")
    logger.error("測試錯誤記錄")
    logger.debug("測試調試記錄")
    
    # 測試業務日誌
    logger.log_company_processing("2330", "台積電", "success", 9.5, 
                                validation_passed=True, files_processed=3)
    
    logger.log_validation_result("6462", {
        'overall_status': 'valid',
        'confidence_score': 8.5,
        'warnings': []
    })
    
    logger.log_keyword_analysis(150, 45, ['factset', 'eps', '台積電', '預估', '目標價'])
    
    logger.log_watchlist_analysis(100, 85.5, 78.2, 
                                health_grade='B+', missing_companies=12)
    
    logger.log_report_generation("portfolio_summary", 50, "data/reports/portfolio_latest.csv")
    
    logger.log_sheets_upload("watchlist_summary", True, worksheet_name="Watchlist Summary")
    
    # 顯示統計
    stats = logger.get_stats()
    print(f"\n📊 日誌統計:")
    print(f"   總操作數: {stats['operations_logged']}")
    print(f"   錯誤數: {stats['errors_logged']}")
    print(f"   警告數: {stats['warnings_logged']}")
    print(f"   運行時間: {stats['duration_seconds']:.1f} 秒")
    
    # 關閉 logger
    logger.close()
    
    print("\n✅ Process Logger 測試完成!")