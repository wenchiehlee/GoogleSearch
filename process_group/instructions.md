# FactSet Pipeline v3.5.0 - Process Group 完整實作指南

## Version
{Process Group Instructions}=3.5.0

## 🎯 Process Group 概述

**目標**: 專門處理 MD 檔案的獨立群組，完全透過檔案系統與 Search Group 通訊

**輸入**: `data/md/*.md` 檔案 (由 Search Group 生成)
**輸出**: Google Sheets 報告 + CSV 檔案

**v3.5.0 架構特點**: 
- ✅ 完全獨立於 Search Group
- ✅ 透過檔案夾介面通訊 (`data/md/`)
- ✅ 模組化小檔案 (150-500 行)
- ✅ 單一職責設計
- ✅ 向下相容整合

## 📁 Process Group 檔案結構

```
process_group/                           # 📊 處理群組目錄
├── md_scanner.py                       # 150 行 - 檔案系統介面
├── process_cli.py                      # 450 行 - 命令列介面
├── md_parser.py                        # 500 行 - MD 內容解析
├── quality_analyzer.py                 # 500 行 - 品質分析
├── report_generator.py                 # 500 行 - 報告生成
├── sheets_uploader.py                  # 400 行 - Google Sheets 上傳
└── process_logger.py                   # 100 行 - 日誌系統 (可選)
```

## 🔧 核心設計原則

### 1. 檔案夾通訊原則
```python
# Process Group 只需要知道這個目錄
MD_FILES_DIR = "data/md"  # 或 "../data/md" (取決於執行位置)

# 不需要知道 Search Group 如何建立這些檔案
# 不需要 JSON 中介格式
# 不需要複雜的 API 通訊
```

### 2. 單一職責原則
```python
# 每個檔案專注一個功能
md_scanner.py      → 只管掃描 MD 檔案
md_parser.py       → 只管解析 MD 內容  
quality_analyzer.py → 只管品質評分
report_generator.py → 只管生成報告
sheets_uploader.py → 只管上傳 Sheets
```

### 3. 獨立性原則
```python
# 每個模組都可以獨立測試
python md_scanner.py     # 測試檔案掃描
python md_parser.py      # 測試內容解析
python quality_analyzer.py # 測試品質評分
```

## 📋 檔案實作規格

### 1. MD Scanner (`md_scanner.py`) - 150 行

#### 職責
- 掃描 `data/md/` 目錄中的所有 MD 檔案
- 提供檔案清單、檔案資訊、統計資料
- 作為 Process Group 與檔案系統的唯一介面

#### 核心類別
```python
class MDScanner:
    def __init__(self, md_dir="../data/md"):
        self.md_dir = md_dir
        self._ensure_md_directory()
    
    # 核心方法
    def scan_all_md_files(self) -> List[str]:
        """掃描所有 MD 檔案，按時間排序"""
    
    def scan_recent_files(self, hours=24) -> List[str]:
        """掃描最近 N 小時的檔案"""
    
    def find_company_files(self, company_code: str) -> List[str]:
        """尋找特定公司的檔案"""
    
    def get_latest_file_per_company(self) -> Dict[str, str]:
        """取得每家公司的最新檔案"""
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """取得檔案詳細資訊"""
    
    def get_stats(self) -> Dict[str, Any]:
        """取得統計資訊"""
```

#### 檔案名稱解析
```python
# 預期的檔案名稱格式
# {company_code}_{company_name}_{source}_{hash}_{timestamp}.md
# 例如: 2330_台積電_factset_abc123_0626_1030.md

def _extract_company_code(self, file_path: str) -> str:
    """從檔案名稱提取公司代號"""
    filename = os.path.basename(file_path)
    parts = filename.replace('.md', '').split('_')
    return parts[0] if parts and parts[0].isdigit() and len(parts[0]) == 4 else None
```

#### 統計功能
```python
def get_stats(self) -> Dict[str, Any]:
    """提供完整的檔案統計"""
    return {
        'total_files': int,
        'recent_files_24h': int,
        'unique_companies': int,
        'total_size_mb': float,
        'companies_with_files': Dict[str, int],
        'oldest_file': str,
        'newest_file': str
    }
```

---

### 2. Process CLI (`process_cli.py`) - 450 行

#### 職責
- 提供命令列介面
- 協調各模組的執行
- 處理錯誤和日誌
- 支援向下相容性

#### 核心類別
```python
class ProcessCLI:
    def __init__(self):
        self.md_scanner = MDScanner()
        # 可選模組 (graceful degradation)
        self.md_parser = None
        self.quality_analyzer = None  
        self.report_generator = None
        self.sheets_uploader = None
        self._init_optional_components()
    
    # 主要命令
    def process_all_md_files(self, upload_sheets=True, **kwargs):
        """處理所有 MD 檔案"""
    
    def process_recent_md_files(self, hours=24, upload_sheets=True, **kwargs):
        """處理最近的檔案"""
    
    def process_single_company(self, company_code: str, upload_sheets=True, **kwargs):
        """處理單一公司"""
    
    def analyze_quality_only(self, **kwargs):
        """只進行品質分析"""
    
    def show_md_stats(self, **kwargs):
        """顯示統計資訊"""
    
    def validate_setup(self, **kwargs):
        """驗證環境設定"""
```

#### 命令列介面
```python
def main():
    parser = argparse.ArgumentParser(description='FactSet 處理系統 v3.5.0')
    parser.add_argument('command', choices=[
        'process',           # 處理所有 MD 檔案
        'process-recent',    # 處理最近的 MD 檔案
        'process-single',    # 處理單一公司
        'analyze-quality',   # 品質分析
        'stats',            # 顯示統計資訊
        'validate'          # 驗證環境設定
    ])
    parser.add_argument('--company', help='公司代號')
    parser.add_argument('--hours', type=int, default=24, help='小時數')
    parser.add_argument('--no-upload', action='store_true', help='不上傳到 Sheets')
```

#### 錯誤處理
```python
def _init_optional_components(self):
    """初始化可選組件，支援 graceful degradation"""
    try:
        self.md_parser = MDParser()
    except ImportError:
        pass
    
    # 基本功能 (只用 MDScanner) 總是可用
    # 進階功能 (品質分析、報告生成) 可選
```

---

### 3. MD Parser (`md_parser.py`) - 500 行

#### 職責
- 解析 MD 檔案內容
- 提取 EPS 預測資料 (2025-2027)
- 提取目標價格和分析師數量
- 計算資料豐富度

#### 核心類別
```python
class MDParser:
    def __init__(self):
        # EPS 正則表達式模式
        self.eps_patterns = [
            r'(\d{4})\s*eps\s*[預估預測估算]*\s*[:：]\s*([0-9]+\.?[0-9]*)',
            r'eps\s*(\d{4})\s*[:：]\s*([0-9]+\.?[0-9]*)',
            # ... 更多模式
        ]
        
        # 目標價格模式
        self.target_price_patterns = [
            r'目標價\s*[:：]\s*([0-9]+\.?[0-9]*)',
            r'target\s*price\s*[:：]\s*([0-9]+\.?[0-9]*)',
            # ... 更多模式
        ]
    
    def parse_md_file(self, file_path: str) -> Dict[str, Any]:
        """主要解析方法"""
```

#### 解析結果格式
```python
# parse_md_file 返回格式
{
    # 基本資訊 (從檔案路徑)
    'filename': str,
    'company_code': str,
    'company_name': str,
    'data_source': str,
    'file_mtime': datetime,
    
    # EPS 資料
    'eps_2025_high': float,
    'eps_2025_low': float,
    'eps_2025_avg': float,
    'eps_2026_high': float,
    'eps_2026_low': float,
    'eps_2026_avg': float,
    'eps_2027_high': float,
    'eps_2027_low': float,
    'eps_2027_avg': float,
    
    # 其他財務資料
    'target_price': float,
    'analyst_count': int,
    
    # 資料狀態
    'has_eps_data': bool,
    'has_target_price': bool,
    'has_analyst_info': bool,
    'data_richness_score': float,
    
    # 原始內容
    'content': str,
    'content_length': int,
    'parsed_at': datetime
}
```

#### 核心解析方法
```python
def _extract_eps_data(self, content: str) -> Dict[str, List[float]]:
    """提取 EPS 資料"""
    # 返回 {'2025': [46.0, 45.5], '2026': [52.3], ...}

def _extract_target_price(self, content: str) -> Optional[float]:
    """提取目標價格"""
    
def _extract_analyst_count(self, content: str) -> int:
    """提取分析師數量"""

def _calculate_eps_statistics(self, eps_data: Dict) -> Dict[str, Any]:
    """計算 EPS 統計 (高、低、平均)"""
```

---

### 4. Quality Analyzer (`quality_analyzer.py`) - 500 行

#### 職責
- 實作標準化 0-10 品質評分系統
- 多維度品質分析
- 生成品質狀態指標

#### 核心類別
```python
class QualityAnalyzer:
    # 品質範圍定義
    QUALITY_RANGES = {
        'complete': (9, 10),      # 🟢 完整
        'good': (8, 8),           # 🟡 良好
        'partial': (3, 7),        # 🟠 部分
        'insufficient': (0, 2)    # 🔴 不足
    }
    
    # 評分權重
    QUALITY_WEIGHTS = {
        'data_completeness': 0.35,    # 資料完整性 35%
        'analyst_coverage': 0.25,     # 分析師覆蓋 25%
        'data_freshness': 0.20,       # 資料新鮮度 20%
        'content_quality': 0.15,      # 內容品質 15%
        'data_consistency': 0.05      # 資料一致性 5%
    }
    
    def analyze(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """主要分析方法"""
```

#### 分析結果格式
```python
# analyze 方法返回格式
{
    'quality_score': float,      # 0-10 評分
    'quality_status': str,       # 🟢🟡🟠🔴 指標
    'quality_category': str,     # complete/good/partial/insufficient
    'analysis_timestamp': str,
    
    'detailed_analysis': {
        'data_completeness': {
            'score': float,
            'details': List[str],
            'metrics': Dict
        },
        'analyst_coverage': {...},
        'data_freshness': {...},
        'content_quality': {...},
        'data_consistency': {...}
    },
    
    'summary_metrics': {
        'eps_data_available': bool,
        'target_price_available': bool,
        'analyst_count': int,
        'content_length': int,
        'financial_keywords_found': int
    }
}
```

#### 各維度分析方法
```python
def _analyze_data_completeness(self, data: Dict) -> Dict:
    """分析資料完整性 (35% 權重)"""
    # EPS 資料完整性、目標價格、分析師數量、基本資訊

def _analyze_analyst_coverage(self, data: Dict) -> Dict:
    """分析分析師覆蓋度 (25% 權重)"""
    # 分析師數量、資料來源多樣性

def _analyze_data_freshness(self, data: Dict) -> Dict:
    """分析資料新鮮度 (20% 權重)"""
    # 檔案時間、內容時效性

def _analyze_content_quality(self, data: Dict) -> Dict:
    """分析內容品質 (15% 權重)"""
    # 內容長度、關鍵字覆蓋、來源品質

def _analyze_data_consistency(self, data: Dict) -> Dict:
    """分析資料一致性 (5% 權重)"""
    # EPS 趨勢、公司資訊、目標價格合理性
```

---

### 5. Report Generator (`report_generator.py`) - 500 行

#### 職責
- 生成標準化投資組合報告
- 支援 14 欄位摘要 + 21 欄位詳細格式
- 整合 GitHub Raw URL 連結
- 生成統計報告

#### 核心類別
```python
class ReportGenerator:
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/..."):
        self.github_repo_base = github_repo_base
        self.output_dir = "data/reports"
        
        # 欄位定義
        self.portfolio_summary_columns = [
            '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
            '分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值',
            '品質評分', '狀態', '更新日期'
        ]
        
        self.detailed_report_columns = [
            '代號', '名稱', '股票代號', 'MD日期', '分析師數量', '目標價',
            '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
            '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
            '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
            '品質評分', '狀態', 'MD File', '更新日期'
        ]
    
    def generate_portfolio_summary(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """生成投資組合摘要 (14 欄位)"""
    
    def generate_detailed_report(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """生成詳細報告 (21 欄位)"""
    
    def save_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> Dict[str, str]:
        """儲存報告為 CSV"""
```

#### GitHub Raw URL 格式化
```python
def _format_md_file_link(self, filename: str) -> str:
    """格式化 MD 檔案為 GitHub Raw URL"""
    # 輸出格式: [filename.md](GitHub_Raw_URL)
    encoded_filename = urllib.parse.quote(filename, safe='')
    raw_url = f"{self.github_repo_base}/data/md/{encoded_filename}"
    return f"[{filename}]({raw_url})"
```

#### 報告格式範例
```csv
# Portfolio Summary (14 欄位)
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
2330,台積電,2330-TW,2025/06/24,2025/06/24,1,42,650.5,46.00,23.56,23.56,10,🟢 完整,2025-06-24 10:45:00

# Detailed Report (21 欄位)
代號,名稱,股票代號,MD日期,分析師數量,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2026EPS最高值,2026EPS最低值,2026EPS平均值,2027EPS最高值,2027EPS最低值,2027EPS平均值,品質評分,狀態,MD File,更新日期
2330,台積電,2330-TW,2025/06/23,42,,59.66,6.00,46.00,32.34,6.00,23.56,32.34,6.00,23.56,10,🟢 完整,[2330_台積電_factset_abc123.md](https://raw.github...),2025-06-24 05:52:02
```

---

### 6. Sheets Uploader (`sheets_uploader.py`) - 400 行

#### 職責
- 上傳報告到 Google Sheets
- 設定工作表格式和樣式
- 處理 Google Sheets API 連線
- 支援連線測試

#### 核心類別
```python
class SheetsUploader:
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/..."):
        self.github_repo_base = github_repo_base
        self.client = None
        self.spreadsheet = None
    
    def upload_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame) -> bool:
        """主要上傳方法"""
    
    def test_connection(self) -> bool:
        """測試 Google Sheets 連線"""
    
    def _setup_connection(self) -> bool:
        """設定 Google Sheets 連線"""
    
    def _upload_portfolio_summary(self, portfolio_df: pd.DataFrame) -> bool:
        """上傳投資組合摘要"""
    
    def _upload_detailed_report(self, detailed_df: pd.DataFrame) -> bool:
        """上傳詳細報告"""
```

#### 環境變數需求
```python
# 需要的環境變數
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_SHEETS_CREDENTIALS={"type": "service_account", ...}
```

#### 依賴套件
```python
# requirements 需要
gspread>=5.0.0
google-auth>=2.0.0
pandas>=1.3.0
python-dotenv>=0.19.0
```

---

## 🔗 模組整合模式

### 1. Process CLI 整合模式
```python
class ProcessCLI:
    def process_all_md_files(self, **kwargs):
        # 1. 掃描檔案
        md_files = self.md_scanner.scan_all_md_files()
        
        # 2. 解析每個檔案
        processed_companies = []
        for md_file in md_files:
            parsed_data = self.md_parser.parse_md_file(md_file)
            quality_data = self.quality_analyzer.analyze(parsed_data)
            company_data = {**parsed_data, **quality_data}
            processed_companies.append(company_data)
        
        # 3. 生成報告
        portfolio_summary = self.report_generator.generate_portfolio_summary(processed_companies)
        detailed_report = self.report_generator.generate_detailed_report(processed_companies)
        
        # 4. 上傳 (可選)
        if upload_sheets:
            self.sheets_uploader.upload_reports(portfolio_summary, detailed_report)
```

### 2. 錯誤處理模式
```python
def _init_optional_components(self):
    """Graceful degradation 模式"""
    components = [
        ('md_parser', MDParser),
        ('quality_analyzer', QualityAnalyzer),
        ('report_generator', ReportGenerator),
        ('sheets_uploader', SheetsUploader)
    ]
    
    for name, cls in components:
        try:
            setattr(self, name, cls())
        except ImportError:
            setattr(self, name, None)
            print(f"⚠️ {name} 模組未載入")
```

### 3. 資料流動模式
```
MD Files → MDScanner → ProcessCLI → MDParser → QualityAnalyzer → ReportGenerator → SheetsUploader
   ↓           ↓           ↓           ↓            ↓               ↓              ↓
檔案清單    檔案資訊    解析資料    品質評分     結構化資料      CSV報告      Google Sheets
```

## 🧪 測試和驗證

### 1. 單元測試模式
```python
# 每個模組都支援獨立測試
if __name__ == "__main__":
    # 建立測試資料
    # 執行核心功能
    # 顯示測試結果
```

### 2. 整合測試模式
```python
# process_cli.py 中的驗證命令
def validate_setup(self):
    """驗證所有組件"""
    results = {}
    
    # 測試檔案掃描
    md_files = self.md_scanner.scan_all_md_files()
    results['md_scanner'] = f"找到 {len(md_files)} 個檔案"
    
    # 測試其他組件...
    return results
```

### 3. 使用者測試模式
```bash
# 基本功能測試
python process_cli.py validate
python process_cli.py stats

# 完整功能測試
python process_cli.py process --no-upload
python process_cli.py analyze-quality
```

## 📦 依賴和安裝

### 1. 必要依賴
```txt
# 核心依賴 (process_requirements.txt)
pandas>=1.3.0
python-dotenv>=0.19.0

# Google Sheets 依賴 (可選)
gspread>=5.0.0
google-auth>=2.0.0
```

### 2. 安裝指令
```bash
# 基本安裝
pip install pandas python-dotenv

# 完整安裝 (包含 Google Sheets)
pip install pandas python-dotenv gspread google-auth
```

### 3. 環境設定
```bash
# .env 檔案
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_SHEETS_CREDENTIALS={"type": "service_account", ...}
```

## 🚀 部署和使用

### 1. 基本使用流程
```bash
# 1. 檢查環境
python process_cli.py validate

# 2. 查看統計
python process_cli.py stats

# 3. 處理檔案
python process_cli.py process --no-upload

# 4. 品質分析
python process_cli.py analyze-quality
```

### 2. 高級使用流程
```bash
# 處理最近檔案
python process_cli.py process-recent --hours=12

# 處理單一公司
python process_cli.py process-single --company=2330

# 完整處理 (包含上傳)
python process_cli.py process
```

### 3. 故障排除
```bash
# 檢查模組載入狀態
python process_cli.py validate

# 測試 Google Sheets 連線
python sheets_uploader.py --test-connection

# 檢查檔案狀態
python process_cli.py stats
```

## 📋 實作檢查清單

### ✅ 必須實作的功能
- [ ] `MDScanner` 檔案掃描和統計
- [ ] `ProcessCLI` 命令列介面和協調
- [ ] `MDParser` MD 內容解析 
- [ ] `QualityAnalyzer` 品質評分系統
- [ ] `ReportGenerator` 報告生成
- [ ] `SheetsUploader` Google Sheets 上傳

### ✅ 必須支援的格式
- [ ] 14 欄位投資組合摘要格式
- [ ] 21 欄位詳細報告格式
- [ ] GitHub Raw URL MD 檔案連結
- [ ] 0-10 標準化品質評分
- [ ] 🟢🟡🟠🔴 品質狀態指標

### ✅ 必須提供的命令
- [ ] `process` - 處理所有檔案
- [ ] `process-recent` - 處理最近檔案
- [ ] `process-single` - 處理單一公司
- [ ] `analyze-quality` - 品質分析
- [ ] `stats` - 統計資訊
- [ ] `validate` - 環境驗證

### ✅ 必須處理的錯誤
- [ ] 模組載入失敗 (graceful degradation)
- [ ] 檔案不存在或格式錯誤
- [ ] Google Sheets 連線失敗
- [ ] 解析錯誤和資料品質問題

---

**v3.5.0 Process Group 總結**: 這是一個完全獨立的處理群組，透過檔案夾介面與 Search Group 通訊，每個檔案專注單一職責，支援完整的財務資料處理流程，從 MD 檔案掃描到 Google Sheets 報告生成。