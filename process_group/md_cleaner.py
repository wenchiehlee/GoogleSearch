#!/usr/bin/env python3
"""
MD Cleaner - FactSet Pipeline v3.6.1
MD檔案年齡管理工具，基於提取的財務數據發布日期進行清理
完全整合Process Group架構，重用md_parser的日期提取邏輯
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import statistics

# 導入現有的MD解析器以確保日期提取邏輯一致
try:
    from md_parser import MDParser
except ImportError:
    # 如果在不同目錄運行，嘗試相對導入
    import sys
    sys.path.append(os.path.dirname(__file__))
    from md_parser import MDParser

@dataclass
class MDFileInfo:
    """MD檔案資訊數據結構"""
    filepath: str
    filename: str
    file_size: int
    file_mtime: datetime
    md_date: Optional[datetime]  # 財務數據發布日期
    extracted_date: Optional[datetime]  # 系統提取時間戳
    quality_score: Optional[float]
    company_code: str
    company_name: str
    age_days: int
    deletion_candidate: bool
    preservation_reason: Optional[str]
    date_extraction_method: str

@dataclass
class CleanupPlan:
    """清理計劃數據結構"""
    total_files: int
    deletion_candidates: List[MDFileInfo]
    preserved_files: List[MDFileInfo]
    no_date_files: List[MDFileInfo]
    estimated_space_saved: int
    safety_checks_passed: bool
    warnings: List[str]
    errors: List[str]

@dataclass
class CleanupResult:
    """清理結果數據結構"""
    files_deleted: int
    files_preserved: int
    files_backed_up: int
    space_freed: int
    errors: List[str]
    backup_location: Optional[str]
    execution_time: float
    dry_run: bool

class MDFileCleanupManager:
    """MD檔案清理管理器 v3.6.1"""
    
    def __init__(self, md_dir="data/md"):
        """初始化清理管理器"""
        self.md_dir = os.path.abspath(md_dir)
        self.version = "3.6.1"
        
        # 初始化MD解析器（重用現有邏輯）
        try:
            self.md_parser = MDParser()
            self.parser_available = True
            print(f"✅ MD解析器初始化成功 (v{self.md_parser.version})")
        except Exception as e:
            print(f"⚠️ MD解析器初始化失敗: {e}")
            print("🔧 將使用簡化的日期提取邏輯")
            self.md_parser = None
            self.parser_available = False
        
        # 清理配置
        self.config = {
            'default_retention_days': 90,
            'quality_threshold': 8,
            'extended_retention_days': 30,
            'safety_thresholds': {
                'max_deletion_percentage': 0.7,  # 最多刪除70%的檔案
                'minimum_files_remaining': 10    # 至少保留10個檔案
            },
            'backup': {
                'enabled': True,
                'archive_path': '../data/archive',
                'compression': False  # 簡化實現，不壓縮
            },
            'aggressive_deletion': True  # 無法提取日期的檔案直接刪除
        }
        
        # 確保目錄存在
        self._ensure_directories()
        
        print(f"🔧 MD檔案清理管理器 v{self.version} 初始化完成")
        print(f"📁 監控目錄: {self.md_dir}")
        print(f"⚙️ 預設保留期: {self.config['default_retention_days']}天")
        print(f"⭐ 質量閾值: {self.config['quality_threshold']}")

    def _ensure_directories(self):
        """確保必要的目錄存在"""
        os.makedirs(self.md_dir, exist_ok=True)
        if self.config['backup']['enabled']:
            archive_path = os.path.abspath(self.config['backup']['archive_path'])
            os.makedirs(archive_path, exist_ok=True)

    def scan_md_files(self) -> List[MDFileInfo]:
        """掃描所有MD檔案並提取資訊"""
        print(f"🔍 掃描MD檔案目錄: {self.md_dir}")
        
        if not os.path.exists(self.md_dir):
            print(f"❌ 目錄不存在: {self.md_dir}")
            return []
        
        md_files = []
        total_files = 0
        successful_extractions = 0
        failed_extractions = 0
        
        for filename in os.listdir(self.md_dir):
            if not filename.endswith('.md'):
                continue
                
            total_files += 1
            filepath = os.path.join(self.md_dir, filename)
            
            try:
                file_info = self._extract_file_info(filepath)
                md_files.append(file_info)
                
                if file_info.md_date:
                    successful_extractions += 1
                else:
                    failed_extractions += 1
                    
            except Exception as e:
                failed_extractions += 1
                print(f"⚠️ 處理檔案失敗 {filename}: {e}")
        
        print(f"📊 掃描結果:")
        print(f"   總檔案數: {total_files}")
        print(f"   成功解析: {successful_extractions}")
        print(f"   解析失敗: {failed_extractions}")
        print(f"   成功率: {successful_extractions/total_files*100:.1f}%" if total_files > 0 else "   成功率: 0%")
        
        return md_files

    def _extract_file_info(self, filepath: str) -> MDFileInfo:
        """提取單個MD檔案的資訊"""
        filename = os.path.basename(filepath)
        file_stat = os.stat(filepath)
        file_size = file_stat.st_size
        file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
        
        # 從檔案名提取基本資訊
        company_code, company_name = self._parse_filename(filename)
        
        # 提取MD日期（財務數據發布日期）
        md_date = None
        extracted_date = None
        quality_score = None
        date_extraction_method = "failed"
        
        try:
            if self.parser_available:
                # 使用現有的MD解析器（確保一致性）
                md_date, extracted_date, quality_score, date_extraction_method = self._extract_dates_with_parser(filepath)
            else:
                # 降級到簡化日期提取
                md_date, extracted_date, date_extraction_method = self._extract_dates_fallback(filepath)
            
        except Exception as e:
            print(f"⚠️ 日期提取失敗 {filename}: {e}")
        
        # 計算檔案年齡
        age_days = 0
        if md_date:
            age_days = (datetime.now() - md_date).days
        elif extracted_date:
            age_days = (datetime.now() - extracted_date).days
        
        return MDFileInfo(
            filepath=filepath,
            filename=filename,
            file_size=file_size,
            file_mtime=file_mtime,
            md_date=md_date,
            extracted_date=extracted_date,
            quality_score=quality_score,
            company_code=company_code,
            company_name=company_name,
            age_days=age_days,
            deletion_candidate=False,  # 稍後確定
            preservation_reason=None,
            date_extraction_method=date_extraction_method
        )

    def _extract_dates_with_parser(self, filepath: str) -> Tuple[Optional[datetime], Optional[datetime], Optional[float], str]:
        """使用現有MD解析器提取日期（確保一致性）"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用現有的bulletproof日期提取邏輯
            content_date_str = self.md_parser._extract_content_date_bulletproof(content)
            md_date = None
            if content_date_str:
                try:
                    # 解析日期字符串 (格式: YYYY/M/D)
                    md_date = datetime.strptime(content_date_str, '%Y/%m/%d')
                except ValueError as e:
                    print(f"⚠️ 日期格式解析失敗 {content_date_str}: {e}")
            
            # 提取YAML中的extracted_date
            yaml_data = self.md_parser._extract_yaml_frontmatter_enhanced(content)
            extracted_date = None
            if yaml_data.get('extracted_date'):
                try:
                    extracted_date_str = yaml_data['extracted_date']
                    # 處理ISO格式時間戳
                    if 'T' in extracted_date_str:
                        extracted_date = datetime.fromisoformat(extracted_date_str.replace('T', ' ').split('.')[0])
                    else:
                        extracted_date = datetime.fromisoformat(extracted_date_str)
                except (ValueError, TypeError):
                    pass
            
            # 提取質量評分
            quality_score = yaml_data.get('quality_score')
            if quality_score is not None:
                try:
                    quality_score = float(quality_score)
                except (ValueError, TypeError):
                    quality_score = None
            
            # 確定日期提取方法
            if md_date:
                method = "content_bulletproof"
            elif extracted_date:
                method = "yaml_fallback"
            else:
                method = "no_date_found"
            
            return md_date, extracted_date, quality_score, method
            
        except Exception as e:
            print(f"⚠️ 解析器提取失敗: {e}")
            return None, None, None, "parser_error"

    def _extract_dates_fallback(self, filepath: str) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """簡化的日期提取邏輯（降級方案）"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 簡化的內容日期匹配
            import re
            date_patterns = [
                r'鉅亨網新聞中心\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
                r'(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
                r'(\d{4})/(\d{1,2})/(\d{1,2})'
            ]
            
            md_date = None
            for pattern in date_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    try:
                        year, month, day = matches[0]
                        md_date = datetime(int(year), int(month), int(day))
                        break
                    except ValueError:
                        continue
            
            # 提取YAML中的extracted_date
            extracted_date = None
            if content.startswith('---'):
                end_pos = content.find('---', 3)
                if end_pos != -1:
                    yaml_content = content[3:end_pos]
                    extracted_match = re.search(r'extracted_date:\s*([^\n]+)', yaml_content)
                    if extracted_match:
                        try:
                            extracted_date_str = extracted_match.group(1).strip()
                            if 'T' in extracted_date_str:
                                extracted_date = datetime.fromisoformat(extracted_date_str.replace('T', ' ').split('.')[0])
                        except ValueError:
                            pass
            
            if md_date:
                method = "content_simple"
            elif extracted_date:
                method = "yaml_simple"
            else:
                method = "no_date_fallback"
            
            return md_date, extracted_date, method
            
        except Exception:
            return None, None, "fallback_error"

    def _parse_filename(self, filename: str) -> Tuple[str, str]:
        """從檔案名解析公司代碼和名稱"""
        name_without_ext = filename.replace('.md', '')
        parts = name_without_ext.split('_')
        
        company_code = ""
        company_name = ""
        
        if len(parts) >= 2:
            if parts[0].isdigit() and len(parts[0]) == 4:
                company_code = parts[0]
                company_name = parts[1]
        
        return company_code, company_name

    def analyze_files_for_cleanup(self, md_files: List[MDFileInfo], 
                                 retention_days: int = 90, 
                                 quality_threshold: float = 8) -> CleanupPlan:
        """分析檔案並生成清理計劃"""
        print(f"📋 分析檔案清理計劃...")
        print(f"   保留期限: {retention_days} 天")
        print(f"   質量閾值: {quality_threshold}")
        
        deletion_candidates = []
        preserved_files = []
        no_date_files = []
        warnings = []
        errors = []
        
        for file_info in md_files:
            should_delete, reason = self._should_delete_file(
                file_info, retention_days, quality_threshold
            )
            
            if file_info.md_date is None and file_info.extracted_date is None:
                no_date_files.append(file_info)
                if self.config['aggressive_deletion']:
                    file_info.deletion_candidate = True
                    file_info.preservation_reason = "無日期資訊，標記刪除"
                    deletion_candidates.append(file_info)
                else:
                    file_info.deletion_candidate = False
                    file_info.preservation_reason = "無日期資訊，保守保留"
                    preserved_files.append(file_info)
            elif should_delete:
                file_info.deletion_candidate = True
                file_info.preservation_reason = reason
                deletion_candidates.append(file_info)
            else:
                file_info.deletion_candidate = False
                file_info.preservation_reason = reason
                preserved_files.append(file_info)
        
        # 安全檢查
        total_files = len(md_files)
        deletion_percentage = len(deletion_candidates) / total_files if total_files > 0 else 0
        files_remaining = total_files - len(deletion_candidates)
        
        safety_checks_passed = True
        
        if deletion_percentage > self.config['safety_thresholds']['max_deletion_percentage']:
            safety_checks_passed = False
            warnings.append(f"刪除比例過高: {deletion_percentage:.1%} > {self.config['safety_thresholds']['max_deletion_percentage']:.1%}")
        
        if files_remaining < self.config['safety_thresholds']['minimum_files_remaining']:
            safety_checks_passed = False
            warnings.append(f"剩餘檔案過少: {files_remaining} < {self.config['safety_thresholds']['minimum_files_remaining']}")
        
        if len(no_date_files) > total_files * 0.5:
            warnings.append(f"無日期檔案比例過高: {len(no_date_files)}/{total_files}")
        
        # 計算預估節省空間
        estimated_space_saved = sum(f.file_size for f in deletion_candidates)
        
        plan = CleanupPlan(
            total_files=total_files,
            deletion_candidates=deletion_candidates,
            preserved_files=preserved_files,
            no_date_files=no_date_files,
            estimated_space_saved=estimated_space_saved,
            safety_checks_passed=safety_checks_passed,
            warnings=warnings,
            errors=errors
        )
        
        self._print_cleanup_analysis(plan, retention_days, quality_threshold)
        return plan

    def _should_delete_file(self, file_info: MDFileInfo, 
                          retention_days: int, 
                          quality_threshold: float) -> Tuple[bool, str]:
        """判斷是否應該刪除檔案"""
        
        # 如果沒有任何日期資訊
        if not file_info.md_date and not file_info.extracted_date:
            if self.config['aggressive_deletion']:
                return True, f"無法提取日期資訊，標記刪除"
            else:
                return False, f"無日期資訊但保守保留"
        
        # 優先使用MD日期（財務數據發布日期）
        reference_date = file_info.md_date or file_info.extracted_date
        age_days = (datetime.now() - reference_date).days
        
        # 基本保留期檢查
        if age_days <= retention_days:
            return False, f"檔案較新 ({age_days}天 ≤ {retention_days}天)"
        
        # 高質量檔案延長保留期
        if (file_info.quality_score is not None and 
            file_info.quality_score >= quality_threshold and 
            age_days <= retention_days + self.config['extended_retention_days']):
            return False, f"高質量檔案延長保留 (質量:{file_info.quality_score}, {age_days}天)"
        
        # 標記刪除
        date_source = "MD日期" if file_info.md_date else "提取日期"
        return True, f"超過保留期 ({date_source}: {age_days}天 > {retention_days}天)"

    def _print_cleanup_analysis(self, plan: CleanupPlan, retention_days: int, quality_threshold: float):
        """打印清理分析結果"""
        print(f"\n📊 清理分析結果:")
        print(f"   總檔案數: {plan.total_files}")
        print(f"   刪除候選: {len(plan.deletion_candidates)}")
        print(f"   保留檔案: {len(plan.preserved_files)}")
        print(f"   無日期檔案: {len(plan.no_date_files)}")
        print(f"   預估節省空間: {self._format_size(plan.estimated_space_saved)}")
        
        if plan.warnings:
            print(f"\n⚠️  警告:")
            for warning in plan.warnings:
                print(f"   - {warning}")
        
        if plan.errors:
            print(f"\n❌ 錯誤:")
            for error in plan.errors:
                print(f"   - {error}")
        
        print(f"\n✅ 安全檢查: {'通過' if plan.safety_checks_passed else '未通過'}")
        
        # 顯示刪除候選檔案示例
        if plan.deletion_candidates:
            print(f"\n🗑️  刪除候選示例 (前5個):")
            for i, file_info in enumerate(plan.deletion_candidates[:5]):
                date_str = file_info.md_date.strftime('%Y-%m-%d') if file_info.md_date else '無日期'
                print(f"   {i+1}. {file_info.filename} - {date_str} ({file_info.age_days}天)")

    def execute_cleanup(self, plan: CleanupPlan, dry_run: bool = True, 
                       create_backup: bool = True) -> CleanupResult:
        """執行清理計劃"""
        start_time = datetime.now()
        
        if dry_run:
            print(f"🔍 執行清理計劃 (預覽模式)")
        else:
            print(f"🗑️  執行清理計劃 (實際刪除)")
        
        if not plan.safety_checks_passed and not dry_run:
            print(f"❌ 安全檢查未通過，拒絕執行實際刪除")
            print(f"💡 使用 --force 參數強制執行，或調整保留策略")
            return CleanupResult(
                files_deleted=0,
                files_preserved=plan.total_files,
                files_backed_up=0,
                space_freed=0,
                errors=["安全檢查未通過"],
                backup_location=None,
                execution_time=0,
                dry_run=dry_run
            )
        
        backup_location = None
        files_deleted = 0
        files_backed_up = 0
        space_freed = 0
        errors = []
        
        # 創建備份
        if create_backup and not dry_run and plan.deletion_candidates:
            try:
                backup_location = self._create_backup(plan.deletion_candidates)
                files_backed_up = len(plan.deletion_candidates)
                print(f"💾 備份已創建: {backup_location}")
            except Exception as e:
                error_msg = f"備份創建失敗: {e}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                if not dry_run:
                    print(f"⚠️  無備份狀態下不執行刪除")
                    return CleanupResult(
                        files_deleted=0,
                        files_preserved=plan.total_files,
                        files_backed_up=0,
                        space_freed=0,
                        errors=errors,
                        backup_location=None,
                        execution_time=(datetime.now() - start_time).total_seconds(),
                        dry_run=dry_run
                    )
        
        # 執行刪除
        for file_info in plan.deletion_candidates:
            try:
                if dry_run:
                    print(f"🔍 [預覽] 將刪除: {file_info.filename} ({self._format_size(file_info.file_size)})")
                else:
                    os.remove(file_info.filepath)
                    print(f"🗑️  已刪除: {file_info.filename} ({self._format_size(file_info.file_size)})")
                
                files_deleted += 1
                space_freed += file_info.file_size
                
            except Exception as e:
                error_msg = f"刪除失敗 {file_info.filename}: {e}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = CleanupResult(
            files_deleted=files_deleted,
            files_preserved=len(plan.preserved_files),
            files_backed_up=files_backed_up,
            space_freed=space_freed,
            errors=errors,
            backup_location=backup_location,
            execution_time=execution_time,
            dry_run=dry_run
        )
        
        self._print_cleanup_result(result)
        return result

    def _create_backup(self, deletion_candidates: List[MDFileInfo]) -> str:
        """創建刪除檔案的備份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(
            os.path.abspath(self.config['backup']['archive_path']),
            f"cleanup_backup_{timestamp}"
        )
        
        os.makedirs(backup_dir, exist_ok=True)
        
        # 複製檔案到備份目錄
        for file_info in deletion_candidates:
            backup_path = os.path.join(backup_dir, file_info.filename)
            shutil.copy2(file_info.filepath, backup_path)
        
        # 創建備份清單
        manifest = {
            'backup_timestamp': timestamp,
            'total_files': len(deletion_candidates),
            'files': [
                {
                    'filename': f.filename,
                    'original_path': f.filepath,
                    'company_code': f.company_code,
                    'company_name': f.company_name,
                    'md_date': f.md_date.isoformat() if f.md_date else None,
                    'file_size': f.file_size,
                    'age_days': f.age_days,
                    'preservation_reason': f.preservation_reason
                }
                for f in deletion_candidates
            ],
            'total_size': sum(f.file_size for f in deletion_candidates),
            'cleaner_version': self.version
        }
        
        manifest_path = os.path.join(backup_dir, 'backup_manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        return backup_dir

    def _print_cleanup_result(self, result: CleanupResult):
        """打印清理結果"""
        mode = "預覽模式" if result.dry_run else "實際執行"
        print(f"\n📋 清理結果 ({mode}):")
        print(f"   刪除檔案: {result.files_deleted}")
        print(f"   保留檔案: {result.files_preserved}")
        print(f"   備份檔案: {result.files_backed_up}")
        print(f"   釋放空間: {self._format_size(result.space_freed)}")
        print(f"   執行時間: {result.execution_time:.2f}秒")
        
        if result.backup_location:
            print(f"   備份位置: {result.backup_location}")
        
        if result.errors:
            print(f"\n❌ 錯誤 ({len(result.errors)}):")
            for error in result.errors:
                print(f"   - {error}")
        
        if not result.dry_run and result.files_deleted > 0:
            print(f"\n✅ 清理完成！刪除了 {result.files_deleted} 個檔案")

    def generate_cleanup_report(self, md_files: List[MDFileInfo], 
                               plan: CleanupPlan, 
                               result: Optional[CleanupResult] = None) -> Dict[str, Any]:
        """生成清理報告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'cleaner_version': self.version,
            'configuration': {
                'md_directory': self.md_dir,
                'retention_days': self.config['default_retention_days'],
                'quality_threshold': self.config['quality_threshold'],
                'aggressive_deletion': self.config['aggressive_deletion']
            },
            'analysis': {
                'total_files': plan.total_files,
                'deletion_candidates': len(plan.deletion_candidates),
                'preserved_files': len(plan.preserved_files),
                'no_date_files': len(plan.no_date_files),
                'estimated_space_saved': plan.estimated_space_saved,
                'safety_checks_passed': plan.safety_checks_passed,
                'warnings': plan.warnings,
                'errors': plan.errors
            }
        }
        
        if result:
            report['execution'] = {
                'dry_run': result.dry_run,
                'files_deleted': result.files_deleted,
                'files_backed_up': result.files_backed_up,
                'space_freed': result.space_freed,
                'execution_time': result.execution_time,
                'backup_location': result.backup_location,
                'errors': result.errors
            }
        
        # 添加檔案詳情
        report['file_details'] = {
            'by_age_group': self._group_files_by_age(md_files),
            'by_quality_score': self._group_files_by_quality(md_files),
            'by_company': self._group_files_by_company(md_files)
        }
        
        return report

    def _group_files_by_age(self, md_files: List[MDFileInfo]) -> Dict[str, int]:
        """按年齡分組檔案"""
        groups = {
            '0-30天': 0,
            '31-60天': 0,
            '61-90天': 0,
            '91-180天': 0,
            '181-365天': 0,
            '365天以上': 0,
            '無日期': 0
        }
        
        for file_info in md_files:
            if file_info.age_days == 0 and not file_info.md_date:
                groups['無日期'] += 1
            elif file_info.age_days <= 30:
                groups['0-30天'] += 1
            elif file_info.age_days <= 60:
                groups['31-60天'] += 1
            elif file_info.age_days <= 90:
                groups['61-90天'] += 1
            elif file_info.age_days <= 180:
                groups['91-180天'] += 1
            elif file_info.age_days <= 365:
                groups['181-365天'] += 1
            else:
                groups['365天以上'] += 1
        
        return groups

    def _group_files_by_quality(self, md_files: List[MDFileInfo]) -> Dict[str, int]:
        """按質量評分分組檔案"""
        groups = {
            '優秀(9-10)': 0,
            '良好(7-8)': 0,
            '普通(4-6)': 0,
            '較差(1-3)': 0,
            '無評分': 0
        }
        
        for file_info in md_files:
            if file_info.quality_score is None:
                groups['無評分'] += 1
            elif file_info.quality_score >= 9:
                groups['優秀(9-10)'] += 1
            elif file_info.quality_score >= 7:
                groups['良好(7-8)'] += 1
            elif file_info.quality_score >= 4:
                groups['普通(4-6)'] += 1
            else:
                groups['較差(1-3)'] += 1
        
        return groups

    def _group_files_by_company(self, md_files: List[MDFileInfo]) -> Dict[str, int]:
        """按公司分組檔案計數"""
        company_counts = {}
        
        for file_info in md_files:
            key = f"{file_info.company_code}_{file_info.company_name}" if file_info.company_code else "Unknown"
            company_counts[key] = company_counts.get(key, 0) + 1
        
        # 返回前10個檔案數最多的公司
        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_companies[:10])

    def _format_size(self, size_bytes: int) -> str:
        """格式化檔案大小"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"

    def get_statistics(self) -> Dict[str, Any]:
        """獲取MD檔案目錄統計資訊"""
        md_files = self.scan_md_files()
        
        if not md_files:
            return {
                'total_files': 0,
                'total_size': 0,
                'date_extraction_success_rate': 0,
                'message': 'No MD files found'
            }
        
        total_size = sum(f.file_size for f in md_files)
        files_with_dates = len([f for f in md_files if f.md_date])
        success_rate = files_with_dates / len(md_files) * 100
        
        # 年齡統計
        ages = [f.age_days for f in md_files if f.md_date]
        age_stats = {}
        if ages:
            age_stats = {
                'average_age_days': statistics.mean(ages),
                'median_age_days': statistics.median(ages),
                'oldest_file_days': max(ages),
                'newest_file_days': min(ages)
            }
        
        # 質量統計
        quality_scores = [f.quality_score for f in md_files if f.quality_score is not None]
        quality_stats = {}
        if quality_scores:
            quality_stats = {
                'average_quality': statistics.mean(quality_scores),
                'median_quality': statistics.median(quality_scores),
                'highest_quality': max(quality_scores),
                'lowest_quality': min(quality_scores)
            }
        
        return {
            'total_files': len(md_files),
            'total_size': total_size,
            'total_size_formatted': self._format_size(total_size),
            'files_with_md_dates': files_with_dates,
            'date_extraction_success_rate': success_rate,
            'age_statistics': age_stats,
            'quality_statistics': quality_stats,
            'age_distribution': self._group_files_by_age(md_files),
            'quality_distribution': self._group_files_by_quality(md_files),
            'top_companies': self._group_files_by_company(md_files),
            'cleaner_version': self.version,
            'parser_available': self.parser_available
        }


# 測試功能
if __name__ == "__main__":
    print("=== MD檔案清理管理器 v3.6.1 測試 ===")
    
    # 初始化清理管理器
    cleaner = MDFileCleanupManager("data/md")
    
    # 獲取統計資訊
    print("\n📊 目錄統計:")
    stats = cleaner.get_statistics()
    print(f"   總檔案數: {stats['total_files']}")
    print(f"   總大小: {stats.get('total_size_formatted', '0 B')}")
    print(f"   日期提取成功率: {stats.get('date_extraction_success_rate', 0):.1f}%")
    
    if stats['total_files'] > 0:
        # 掃描和分析檔案
        print("\n🔍 掃描MD檔案...")
        md_files = cleaner.scan_md_files()
        
        if md_files:
            print("\n📋 生成清理計劃...")
            plan = cleaner.analyze_files_for_cleanup(md_files, retention_days=90, quality_threshold=8)
            
            print("\n🔍 執行預覽模式...")
            result = cleaner.execute_cleanup(plan, dry_run=True, create_backup=False)
            
            print("\n📄 生成清理報告...")
            report = cleaner.generate_cleanup_report(md_files, plan, result)
            
            print(f"\n✅ 測試完成！")
            print(f"   檢測到 {len(plan.deletion_candidates)} 個刪除候選檔案")
            print(f"   預估節省空間: {cleaner._format_size(plan.estimated_space_saved)}")
            print(f"   安全檢查: {'通過' if plan.safety_checks_passed else '未通過'}")
            
        else:
            print("⚠️  未找到MD檔案")
    else:
        print("⚠️  MD目錄為空或不存在")
    
    print(f"\n🎉 MD檔案清理管理器 v{cleaner.version} 就緒！")
    print(f"💡 集成到 process_cli.py 後可使用完整功能")