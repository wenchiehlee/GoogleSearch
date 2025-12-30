# FactSet Pipeline v3.6.1 - Process Group 完整實作指南 (修正版)

## Version
{Process Group Instructions}=3.6.1

## 🎯 Process Group 概述

**目標**: 專門處理 MD 檔案的獨立群組，完全透過檔案系統與 Search Group 通訊

**輸入**: `data/md/*.md` 檔案 (由 Search Group 使用 REFINED_SEARCH_PATTERNS 生成)
**輸出**: Google Sheets 報告 + CSV 檔案 + 標準化查詢模式統計報告 + 觀察名單統計報告

**v3.6.1 新功能** (相對於 v3.6.0): 
- ✅ 新增觀察名單處理統計報告 (`watchlist-summary.csv`)
- ✅ StockID_TWSE_TPEX.csv 為基礎的統計分析 (MD檔案數量、平均品質評分)
- ✅ 標準化查詢模式分析 (`{name} {symbol}` 格式，對應 REFINED_SEARCH_PATTERNS)
- ✅ 查詢模式效果評估與觀察名單公司的關聯分析
- ✅ 觀察名單覆蓋率和處理狀態統計
- ✅ 缺失公司報告與搜尋建議

## 🔍 REFINED_SEARCH_PATTERNS 整合

**Process Group 與 Search Group 協作模式**: Process Group 分析由 Search Group 基於以下標準化搜尋模式產生的 MD 檔案：

```python
REFINED_SEARCH_PATTERNS = {
    'factset_direct': [
        # Simple FactSet patterns (highest success rate)
        'factset {symbol}',
        'factset {name}', 
        '{symbol} factset',
        '{name} factset',
        'factset {symbol} EPS',
        'factset {name} 預估',
        '"{symbol}" factset 分析師',
        '"{name}" factset 目標價'
    ],
    'cnyes_factset': [
        # cnyes.com is the #1 source for FactSet data in Taiwan
        'site:cnyes.com factset {symbol}',
        'site:cnyes.com {symbol} factset',
        'site:cnyes.com {symbol} EPS 預估',
        'site:cnyes.com {name} factset',
        'site:cnyes.com {symbol} 分析師',
        'site:cnyes.com factset {name}',
        'site:cnyes.com {symbol} 台股預估'
    ],
    'eps_forecast': [
        # Direct EPS forecast searches
        '{symbol} EPS 預估',
        '{name} EPS 預估',
        '{symbol} EPS 2025',
        '{name} EPS 2025',
        '{symbol} 每股盈餘 預估',
        '{name} 每股盈餘 預估',
        '{symbol} EPS forecast',
        '{name} earnings estimates'
    ],
    'analyst_consensus': [
        # Analyst and consensus patterns
        '{symbol} 分析師 預估',
        '{name} 分析師 預估',
        '{symbol} 分析師 目標價',
        '{name} 分析師 目標價',
        '{symbol} consensus estimate',
        '{name} analyst forecast',
        '{symbol} 共識預估',
        '{name} 投資評等'
    ],
    'taiwan_financial_simple': [
        # Simple Taiwan financial site searches
        'site:cnyes.com {symbol}',
        'site:statementdog.com {symbol}',
        'site:wantgoo.com {symbol}',
        'site:goodinfo.tw {symbol}',
        'site:uanalyze.com.tw {symbol}',
        'site:findbillion.com {symbol}',
        'site:moneydj.com {symbol}',
        'site:yahoo.com {symbol} 股票'
    ]
}
```

**Process Group 查詢模式分析職責**:
- 🔧 解析 MD 檔案中的 `search_query` metadata
- 🔧 標準化查詢模式為 `{name} {symbol}` 格式
- 🔧 對應到 REFINED_SEARCH_PATTERNS 分類
- 🔧 計算各模式的品質評分和使用頻率
- 🔧 生成查詢模式效果統計報告

**v3.6.0 既有功能**:
- ✅ 關鍵字統計報告 (`keyword-summary.csv`)
- ✅ MD 檔案 metadata 解析 (search_query 提取)
- ✅ 關鍵字品質評分統計分析
- ✅ 關鍵字效果評估和優化建議

**v3.6.1 架構特點**: 
- ✅ 完全獨立於 Search Group
- ✅ 透過檔案夾介面通訊 (`data/md/`)
- ✅ 模組化小檔案 (150-600 行)
- ✅ 單一職責設計
- ✅ 向下相容整合
- ✅ 關鍵字效果追蹤
- ✅ 觀察名單公司處理狀態追蹤

## 📁 Process Group 檔案結構

```
process_group/                           # 📊 處理群組目錄
├── md_scanner.py                       # ~150 行 - 檔案系統介面
├── process_cli.py                      # ~600 行 - 命令列介面 (新增觀察名單命令)
├── md_parser.py                        # ~650 行 - MD 內容解析 (含 metadata 解析)
├── quality_analyzer.py                 # ~550 行 - 品質分析
├── report_generator.py                 # ~900 行 - 報告生成 (新增觀察名單報告)
├── keyword_analyzer.py                 # ~650 行 - 查詢模式分析 (v3.6.1 升級)
├── watchlist_analyzer.py               # ~500 行 - 觀察名單分析 (v3.6.1 新增)
├── sheets_uploader.py                  # ~600 行 - Google Sheets 上傳 (新增觀察名單工作表)
└── process_logger.py                   # ~120 行 - 日誌系統 (可選)
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
md_scanner.py         → 只管掃描 MD 檔案
md_parser.py          → 只管解析 MD 內容和 metadata  
quality_analyzer.py   → 只管品質評分
keyword_analyzer.py   → 只管查詢模式分析 (v3.6.1)
watchlist_analyzer.py → 只管觀察名單統計分析 (v3.6.1 新增)
report_generator.py   → 只管生成報告
sheets_uploader.py    → 只管上傳 Sheets
```

### 3. 獨立性原則
```python
# 每個模組都可以獨立測試
python md_scanner.py         # 測試檔案掃描
python md_parser.py          # 測試內容解析
python keyword_analyzer.py   # 測試查詢模式分析 (v3.6.1)
python watchlist_analyzer.py # 測試觀察名單分析 (v3.6.1)
python quality_analyzer.py   # 測試品質評分
```

## 📋 檔案實作規格

### 1. MD Scanner (`md_scanner.py`) - ~150 行

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

### 2. MD Parser (`md_parser.py`) - ~650 行

#### 職責 (v3.6.0 既有功能)
- 解析 MD 檔案內容
- 提取 metadata (search_query 等)
- 提取 EPS 預測資料 (2025-2027)
- 提取目標價格和分析師數量
- 計算資料豐富度
- 驗證觀察名單合規性

#### 核心功能
```python
class MDParser:
    def __init__(self):
        # 載入觀察名單進行驗證
        self.watch_list_mapping = self._load_watch_list_mapping_strict()
        self.validation_enabled = len(self.watch_list_mapping) > 0
        
        # metadata 模式 (v3.6.0 功能)
        self.metadata_patterns = {
            'search_query': r'search_query:\s*(.+?)(?:\n|$)',
            'company_code': r'company_code:\s*(.+?)(?:\n|$)',
            'data_source': r'data_source:\s*(.+?)(?:\n|$)',
            'timestamp': r'timestamp:\s*(.+?)(?:\n|$)'
        }
    
    def parse_md_file(self, file_path: str) -> Dict[str, Any]:
        """主要解析方法"""
        # 返回包含 search_keywords 的完整資料
```

### 3. Keyword Analyzer (`keyword_analyzer.py`) - ~650 行 (v3.6.1 升級為查詢模式分析器)

#### 職責 (v3.6.1 重點升級)
- 🆕 **主要功能**: 分析標準化查詢模式 (`{name} {symbol}` 格式)
- 🆕 對應 REFINED_SEARCH_PATTERNS 結構進行模式分類
- 🆕 計算查詢模式與品質評分的關聯性
- 🆕 提供查詢模式效果評估和優化建議

#### 核心類別 (v3.6.1 增強版)
```python
class KeywordAnalyzer:
    def __init__(self):
        # 🆕 REFINED_SEARCH_PATTERNS 對應的模式分類
        self.refined_search_patterns = {
            'factset_direct': [
                'factset {symbol}', 'factset {name}', '{symbol} factset', '{name} factset',
                'factset {symbol} eps', 'factset {name} 預估', '{name} {symbol} factset 分析師'
            ],
            'cnyes_factset': [
                'site:cnyes.com factset {symbol}', 'site:cnyes.com {symbol} factset',
                'site:cnyes.com {symbol} eps 預估', 'site:cnyes.com {name} factset'
            ],
            'eps_forecast': [
                '{symbol} eps 預估', '{name} eps 預估', '{symbol} eps 2025',
                '{name} {symbol} eps', '{name} {symbol} eps 預估'
            ],
            'analyst_consensus': [
                '{symbol} 分析師 預估', '{name} 分析師 預估', '{symbol} 分析師 目標價',
                '{name} {symbol} 分析師', '{name} {symbol} 分析師 預估'
            ],
            'taiwan_financial_simple': [
                'site:cnyes.com {symbol}', 'site:statementdog.com {symbol}',
                '{name} {symbol} 股票', '{name} {symbol} 股價'
            ]
        }
    
    def analyze_query_patterns(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """🆕 主要方法：分析標準化查詢模式"""
    
    def analyze_all_keywords(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """🔧 自動轉換為查詢模式分析（向下相容）"""
    
    def _normalize_query_pattern(self, pattern: str, company_name: str, company_code: str) -> str:
        """🆕 標準化查詢模式為 {name} {symbol} 格式"""
    
    def _identify_pattern_type(self, pattern: str) -> str:
        """🆕 識別查詢模式類型（對應 REFINED_SEARCH_PATTERNS）"""
    
    def _calculate_pattern_effectiveness_score(self, usage_count: int, quality_scores: List[float]) -> float:
        """🆕 計算查詢模式效果評分"""
```

### 4. Watchlist Analyzer (`watchlist_analyzer.py`) - ~500 行 (v3.6.1 新增)

#### 職責
- 載入和解析StockID_TWSE_TPEX.csv
- 統計每家觀察名單公司的MD檔案處理狀態
- 分析觀察名單公司的搜尋關鍵字模式
- 計算觀察名單覆蓋率和處理效果
- 提供觀察名單與關鍵字效果的關聯分析

#### 核心類別
```python
class WatchlistAnalyzer:
    def __init__(self):
        self.watchlist_mapping = self._load_watchlist()
        self.validation_enabled = len(self.watchlist_mapping) > 0
        
        # 觀察名單狀態分類
        self.status_categories = {
            'processed': '已處理',
            'not_found': '未找到MD檔案',
            'validation_failed': '驗證失敗',
            'low_quality': '品質過低',
            'multiple_files': '多個檔案'
        }
    
    def analyze_watchlist_coverage(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """分析觀察名單覆蓋情況"""
    
    def analyze_company_processing_status(self, processed_companies: List[Dict]) -> Dict[str, Dict]:
        """分析每家公司的處理狀態"""
    
    def analyze_search_patterns(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """分析搜尋關鍵字模式"""
    
    def generate_missing_companies_report(self, processed_companies: List[Dict]) -> List[Dict]:
        """生成缺失公司報告"""
    
    def calculate_keyword_effectiveness_by_company(self, processed_companies: List[Dict]) -> Dict[str, Dict]:
        """計算每家公司的關鍵字效果"""
```

#### 分析結果格式
```python
# analyze_watchlist_coverage 返回格式
{
    'total_watchlist_companies': int,
    'companies_with_md_files': int,
    'companies_processed_successfully': int,
    'coverage_rate': float,
    'success_rate': float,
    
    'company_status_summary': {
        'processed': int,        # ✅ 已處理
        'not_found': int,        # ❌ 未找到
        'validation_failed': int, # 🚫 驗證失敗
        'low_quality': int,      # 🔴 品質過低
        'multiple_files': int    # 📄 多個檔案
    },
    
    'quality_statistics': {
        'average_quality_score': float,
        'median_quality_score': float,
        'companies_above_8': int,
        'companies_below_3': int,
        'zero_score_companies': int
    },
    
    'search_pattern_analysis': {
        'most_common_keywords': List[Tuple[str, int]],
        'keyword_quality_correlation': Dict[str, float],
        'companies_by_keyword_count': Dict[str, List[str]],
        'effective_search_patterns': List[str]
    }
}
```

### 5. Process CLI (`process_cli.py`) - ~600 行

#### 職責
- 提供命令列介面
- 協調各模組的執行
- 處理錯誤和日誌
- 支援向下相容性
- **新增觀察名單分析命令**

#### 核心類別
```python
class ProcessCLI:
    def __init__(self):
        self.md_scanner = MDScanner()
        # 可選模組 (graceful degradation)
        self.md_parser = None
        self.quality_analyzer = None  
        self.keyword_analyzer = None       # v3.6.1 升級
        self.watchlist_analyzer = None     # v3.6.1 新增
        self.report_generator = None
        self.sheets_uploader = None
        self._init_optional_components()
    
    # 主要命令
    def process_all_md_files(self, upload_sheets=True, **kwargs):
        """處理所有 MD 檔案 - v3.6.1 包含觀察名單分析"""
    
    def analyze_keywords_only(self, **kwargs):
        """只進行查詢模式分析 (v3.6.1 升級)"""
    
    def analyze_watchlist_only(self, **kwargs):
        """只進行觀察名單分析 (v3.6.1 新增)"""
    
    def generate_keyword_summary(self, upload_sheets=True, **kwargs):
        """生成查詢模式統計報告 (v3.6.1 升級)"""
    
    def generate_watchlist_summary(self, upload_sheets=True, **kwargs):
        """生成觀察名單統計報告 (v3.6.1 新增)"""
```

#### 命令列介面 (v3.6.1 完整版)
```python
def main():
    parser = argparse.ArgumentParser(description='FactSet 處理系統 v3.6.1')
    parser.add_argument('command', choices=[
        'process',            # 處理所有 MD 檔案
        'process-recent',     # 處理最近的 MD 檔案
        'process-single',     # 處理單一公司
        'analyze-quality',    # 品質分析
        'analyze-keywords',   # 查詢模式分析 (v3.6.1 升級)
        'analyze-watchlist',  # 觀察名單分析 (v3.6.1 新增)
        'keyword-summary',    # 查詢模式統計報告 (v3.6.1 升級)
        'watchlist-summary',  # 觀察名單統計報告 (v3.6.1 新增)
        'stats',             # 顯示統計資訊
        'validate'           # 驗證環境設定
    ])
    parser.add_argument('--company', help='公司代號')
    parser.add_argument('--hours', type=int, default=24, help='小時數')
    parser.add_argument('--no-upload', action='store_true', help='不上傳到 Sheets')
    parser.add_argument('--force-upload', action='store_true', help='強制上傳，忽略驗證錯誤')
    parser.add_argument('--min-usage', type=int, default=1, help='查詢模式最小使用次數')
    parser.add_argument('--include-missing', action='store_true', help='包含缺失公司資訊')
    parser.add_argument('--dry-run', action='store_true', help='預覽模式，不實際執行')
```

### 6. Report Generator (`report_generator.py`) - ~900 行

#### 職責
- 生成標準化投資組合報告
- 支援 14 欄位摘要 + 22 欄位詳細格式
- 🆕 生成標準化查詢模式統計報告 (`query-pattern-summary.csv`) - v3.6.1
- 🆕 新增觀察名單統計報告 (`watchlist-summary.csv`) - v3.6.1
- 整合 GitHub Raw URL 連結
- 生成統計報告

#### 核心類別
```python
class ReportGenerator:
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/..."):
        self.github_repo_base = github_repo_base
        self.output_dir = "data/reports"
        
        # 投資組合摘要欄位
        self.portfolio_summary_columns = [
            '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
            '分析師數量', '目標價',
            '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
            '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
            '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
            '品質評分', '狀態', 'MD日期', 'MD File', '處理日期'
        ]

        # 詳細報告欄位 (22 欄位 - 包含驗證狀態)
        self.detailed_report_columns = [
            '代號', '名稱', '股票代號', 'MD日期', '分析師數量', '目標價',
            '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
            '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
            '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
            '品質評分', '狀態', '驗證狀態', 'MD File', '搜尋日期', '處理日期'
        ]

        # 🆕 查詢模式報告欄位 (10 欄位) - v3.6.1 主要功能
        self.query_pattern_summary_columns = [
            'Query pattern', '使用次數', '平均品質評分', '最高品質評分', '最低品質評分',
            '相關公司數量', '品質狀態', '分類', '效果評級', '處理日期'
        ]
        
        # 🆕 觀察名單報告欄位 (12 欄位) - v3.6.1 新增
        self.watchlist_summary_columns = [
            '公司代號', '公司名稱', 'MD檔案數量', '處理狀態', '平均品質評分', '最高品質評分',
            '搜尋關鍵字數量', '主要關鍵字', '關鍵字平均品質', '最新檔案日期', '驗證狀態', '處理日期'
        ]
    
    def generate_portfolio_summary(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """生成投資組合摘要 (14 欄位)"""
    
    def generate_detailed_report(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """生成詳細報告 (22 欄位)"""
    
    def generate_keyword_summary(self, keyword_analysis: Dict[str, Any]) -> pd.DataFrame:
        """🆕 生成標準化查詢模式統計報告"""
    
    def _generate_query_pattern_summary(self, pattern_analysis: Dict[str, Any]) -> pd.DataFrame:
        """🆕 生成標準化查詢模式統計報告"""
    
    def generate_watchlist_summary(self, watchlist_analysis: Dict[str, Any]) -> pd.DataFrame:
        """🆕 生成觀察名單統計報告 (v3.6.1 新增)"""
    
    def save_all_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                        keyword_df: pd.DataFrame = None, watchlist_df: pd.DataFrame = None) -> Dict[str, str]:
        """🔧 儲存所有報告為 CSV - 包含查詢模式和觀察名單報告"""
```

#### 🆕 查詢模式報告格式 (v3.6.1)
```csv
Query pattern,使用次數,平均品質評分,最高品質評分,最低品質評分,相關公司數量,品質狀態,分類,效果評級,處理日期
{name} {symbol} factset 分析師,30,7.89,8.7,4.3,15,🟡 良好,FactSet直接,良好 ⭐⭐,2025-06-30 13:32:00
{name} {symbol} factset eps,25,8.5,9.2,7.1,12,🟡 良好,FactSet直接,良好 ⭐⭐,2025-06-30 13:32:00
site:cnyes.com {symbol} factset,18,7.2,8.1,6.3,10,🟡 良好,鉅亨網FactSet,良好 ⭐⭐,2025-06-30 13:32:00
```

### 7. Sheets Uploader (`sheets_uploader.py`) - ~600 行

#### 職責
- 上傳報告到 Google Sheets
- 設定工作表格式和樣式
- 上傳查詢模式工作表 (v3.6.1)
- **新增觀察名單工作表上傳 (v3.6.1)**
- 處理 Google Sheets API 連線
- 支援連線測試

#### 核心類別
```python
class SheetsUploader:
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/..."):
        # 工作表名稱 (v3.6.1 完整版)
        self.worksheet_names = {
            'portfolio': 'Portfolio Summary',
            'detailed': 'Detailed Report',
            'keywords': 'Query Pattern Summary',    # v3.6.1 升級
            'watchlist': 'Watchlist Summary'       # v3.6.1 新增
        }
    
    def upload_all_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                          keyword_df: pd.DataFrame = None, watchlist_df: pd.DataFrame = None) -> bool:
        """上傳所有報告 (v3.6.1 包含觀察名單報告)"""
    
    def _upload_keyword_summary(self, keyword_df: pd.DataFrame) -> bool:
        """上傳查詢模式統計報告 (v3.6.1 升級)"""
    
    def _upload_watchlist_summary(self, watchlist_df: pd.DataFrame) -> bool:
        """上傳觀察名單統計報告 (v3.6.1 新增)"""
```

## 🔗 模組整合模式

### 1. Process CLI 整合模式 (v3.6.1 更新)
```python
class ProcessCLI:
    def process_all_md_files(self, **kwargs):
        # 1. 掃描檔案
        md_files = self.md_scanner.scan_all_md_files()
        
        # 2. 解析每個檔案 (包含 metadata)
        processed_companies = []
        for md_file in md_files:
            parsed_data = self.md_parser.parse_md_file(md_file)
            quality_data = self.quality_analyzer.analyze(parsed_data)
            company_data = {**parsed_data, **quality_data}
            processed_companies.append(company_data)
        
        # 3. 查詢模式分析 (v3.6.1 升級)
        pattern_analysis = None
        if self.keyword_analyzer:
            pattern_analysis = self.keyword_analyzer.analyze_query_patterns(processed_companies)
        
        # 4. 觀察名單分析 (v3.6.1 新增)
        watchlist_analysis = None
        if self.watchlist_analyzer:
            watchlist_analysis = self.watchlist_analyzer.analyze_watchlist_coverage(processed_companies)
        
        # 5. 生成報告 (包含所有報告)
        portfolio_summary = self.report_generator.generate_portfolio_summary(processed_companies)
        detailed_report = self.report_generator.generate_detailed_report(processed_companies)
        
        pattern_summary = None
        if pattern_analysis:
            pattern_summary = self.report_generator.generate_keyword_summary(pattern_analysis)
        
        watchlist_summary = None
        if watchlist_analysis:
            watchlist_summary = self.report_generator.generate_watchlist_summary(watchlist_analysis)
        
        # 6. 上傳 (可選)
        if upload_sheets:
            self.sheets_uploader.upload_all_reports(
                portfolio_summary, detailed_report, pattern_summary, watchlist_summary
            )
```

### 2. 資料流動模式 (v3.6.1 更新)
```
MD Files → MDScanner → ProcessCLI → MDParser → QualityAnalyzer → KeywordAnalyzer (v3.6.1) → WatchlistAnalyzer (v3.6.1) → ReportGenerator → SheetsUploader
   ↓           ↓           ↓           ↓            ↓               ↓                      ↓                    ↓                ↓
檔案清單    檔案資訊    解析資料    品質評分     查詢模式分析          觀察名單分析          結構化資料           CSV報告         Google Sheets
                      (含metadata)                (v3.6.1)           (v3.6.1)             (4個報告)
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
    
    # 測試查詢模式分析 (v3.6.1)
    if self.keyword_analyzer:
        results['keyword_analyzer'] = "查詢模式分析模組已載入"
    
    # 測試觀察名單分析 (v3.6.1)
    if self.watchlist_analyzer:
        watchlist_size = len(self.watchlist_analyzer.watchlist_mapping)
        results['watchlist_analyzer'] = f"觀察名單載入 {watchlist_size} 家公司"
    
    # 測試其他組件...
    return results
```

### 3. 使用者測試模式
```bash
# 基本功能測試
python process_cli.py validate
python process_cli.py stats

# 查詢模式功能測試 (v3.6.1)
python process_cli.py analyze-keywords
python process_cli.py keyword-summary --no-upload

# 觀察名單功能測試 (v3.6.1 新增)
python process_cli.py analyze-watchlist
python process_cli.py watchlist-summary --no-upload
python process_cli.py watchlist-summary --include-missing

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
statistics  # Python 標準庫

# Google Sheets 依賴 (可選)
gspread>=5.0.0
google-auth>=2.0.0

# 可選依賴
pytz>=2021.1  # 時區處理
```

### 2. 安裝指令
```bash
# 基本安裝
pip install pandas python-dotenv pytz

# 完整安裝 (包含 Google Sheets)
pip install pandas python-dotenv pytz gspread google-auth
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

# 3. 處理檔案 (包含所有分析)
python process_cli.py process --no-upload

# 4. 品質分析
python process_cli.py analyze-quality
```

### 2. 查詢模式分析流程 (v3.6.1)
```bash
# 生成查詢模式統計報告
python process_cli.py keyword-summary

# 生成查詢模式統計報告 (不上傳)
python process_cli.py keyword-summary --no-upload

# 過濾低使用率查詢模式
python process_cli.py keyword-summary --min-usage=3
```

### 3. 觀察名單分析流程 (v3.6.1 新增)
```bash
# 分析觀察名單覆蓋情況
python process_cli.py analyze-watchlist

# 生成觀察名單統計報告
python process_cli.py watchlist-summary

# 生成觀察名單統計報告 (不上傳)
python process_cli.py watchlist-summary --no-upload

# 包含缺失公司資訊
python process_cli.py watchlist-summary --include-missing

# 預覽模式
python process_cli.py watchlist-summary --dry-run
```

### 4. 高級使用流程
```bash
# 處理最近檔案
python process_cli.py process-recent --hours=12

# 處理單一公司
python process_cli.py process-single --company=2330

# 完整處理 (包含所有分析和上傳)
python process_cli.py process

# 強制上傳模式
python process_cli.py process --force-upload
```

## 📋 實作檢查清單

### ✅ 必須實作的功能
- [ ] `MDScanner` 檔案掃描和統計 (~150 行)
- [ ] `ProcessCLI` 命令列介面和協調 (~600 行)
- [ ] `MDParser` MD 內容解析和 metadata 提取 (~650 行)
- [ ] `QualityAnalyzer` 品質評分系統 (~550 行)
- [ ] `KeywordAnalyzer` 查詢模式分析系統 (~650 行) - v3.6.1 升級
- [ ] `WatchlistAnalyzer` 觀察名單分析系統 (~500 行) - v3.6.1 新增
- [ ] `ReportGenerator` 報告生成 (~900 行) - 包含所有報告
- [ ] `SheetsUploader` Google Sheets 上傳 (~600 行) - 包含所有工作表

### ✅ 必須支援的格式
- [ ] 14 欄位投資組合摘要格式
- [ ] 22 欄位詳細報告格式 (包含驗證狀態)
- [ ] 10 欄位查詢模式統計格式 (v3.6.1 主要)
- [ ] 12 欄位觀察名單統計格式 (v3.6.1 新增)
- [ ] GitHub Raw URL MD 檔案連結
- [ ] 0-10 標準化品質評分
- [ ] 🟢🟡🟠🔴 品質狀態指標

### ✅ 必須提供的命令
- [ ] `process` - 處理所有檔案 (包含所有分析)
- [ ] `process-recent` - 處理最近檔案
- [ ] `process-single` - 處理單一公司
- [ ] `analyze-quality` - 品質分析
- [ ] `analyze-keywords` - 查詢模式分析 (v3.6.1 升級)
- [ ] `analyze-watchlist` - 觀察名單分析 (v3.6.1 新增)
- [ ] `keyword-summary` - 查詢模式統計報告 (v3.6.1 升級)
- [ ] `watchlist-summary` - 觀察名單統計報告 (v3.6.1 新增)
- [ ] `stats` - 統計資訊
- [ ] `validate` - 環境驗證

### ✅ 查詢模式分析功能 (v3.6.1 升級)
- [ ] 從 search_query 提取查詢模式
- [ ] 標準化查詢模式為 `{name} {symbol}` 格式
- [ ] 對應到 REFINED_SEARCH_PATTERNS 分類
- [ ] 計算查詢模式使用統計
- [ ] 查詢模式與品質評分關聯分析
- [ ] 查詢模式效果評級 (優秀/良好/普通/需改善)
- [ ] 查詢模式品質分布統計
- [ ] 低使用率查詢模式過濾
- [ ] 查詢模式 CSV 報告生成
- [ ] 查詢模式 Google Sheets 上傳

### ✅ 觀察名單分析功能 (v3.6.1 新增)
- [ ] 載入StockID_TWSE_TPEX.csv檔案
- [ ] 計算觀察名單覆蓋率統計
- [ ] 分析每家公司的處理狀態
- [ ] 統計每家公司的MD檔案數量
- [ ] 計算平均品質評分
- [ ] 分析搜尋關鍵字模式
- [ ] 關鍵字效果與公司的關聯分析
- [ ] 生成缺失公司報告
- [ ] 優先級評估和搜尋建議
- [ ] 觀察名單 CSV 報告生成
- [ ] 觀察名單 Google Sheets 上傳

### ✅ 必須處理的錯誤
- [ ] 模組載入失敗 (graceful degradation)
- [ ] StockID_TWSE_TPEX.csv 載入失敗 (降級運行)
- [ ] 檔案不存在或格式錯誤
- [ ] Metadata 解析失敗
- [ ] 查詢模式提取失敗
- [ ] Google Sheets 連線失敗
- [ ] 解析錯誤和資料品質問題

## 📊 報告格式範例

### Portfolio Summary (14 欄位)
```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2026EPS最高值,2026EPS最低值,2026EPS平均值,2027EPS最高值,2027EPS最低值,2027EPS平均值,品質評分,狀態,MD日期,MD File,處理日期
2330,台積電,2330-TW,2025/06/24,2025/06/24,1,42,650.5,46.00,23.56,23.56,10,🟢 完整,2025-06-24 10:45:00
```

### Query Pattern Summary (10 欄位) - v3.6.1 主要功能
```csv
Query pattern,使用次數,平均品質評分,最高品質評分,最低品質評分,相關公司數量,品質狀態,分類,效果評級,處理日期
{name} {symbol} factset 分析師,30,7.89,8.7,4.3,15,🟡 良好,FactSet直接,良好 ⭐⭐,2025-06-30 13:32:00
{name} {symbol} factset eps,25,8.5,9.2,7.1,12,🟡 良好,FactSet直接,良好 ⭐⭐,2025-06-30 13:32:00
site:cnyes.com {symbol} factset,18,7.2,8.1,6.3,10,🟡 良好,鉅亨網FactSet,良好 ⭐⭐,2025-06-30 13:32:00
```

### Watchlist Summary (12 欄位) - v3.6.1 新增
```csv
公司代號,公司名稱,MD檔案數量,處理狀態,平均品質評分,最高品質評分,搜尋關鍵字數量,主要關鍵字,關鍵字平均品質,最新檔案日期,驗證狀態,處理日期
2330,台積電,3,✅ 已處理,9.2,10.0,4,台積電 factset eps 預估,8.5,2025-06-24,✅ 驗證通過,2025-06-24 10:45:00
6462,神盾,1,✅ 已處理,7.5,7.5,3,神盾 factset 目標價,7.2,2025-06-23,✅ 驗證通過,2025-06-24 10:45:00
1234,測試公司,0,❌ 未找到,0.0,0.0,0,,0.0,,❌ 無資料,2025-06-24 10:45:00
```

## 🎯 故障排除

### 1. 常見問題
```bash
# 檢查模組載入狀態
python process_cli.py validate

# 檢查觀察名單載入
python watchlist_analyzer.py

# 測試 Google Sheets 連線
python sheets_uploader.py --test-connection

# 檢查檔案狀態
python process_cli.py stats
```

### 2. 錯誤訊息解讀
- `❌ 觀察名單未載入` → 檢查 `StockID_TWSE_TPEX.csv` 檔案是否存在
- `🚫 不在觀察名單` → 此公司不在觀察名單中，已自動排除
- `⚠️ 驗證停用` → 觀察名單功能停用，但系統正常運行
- `❌ Google Sheets 連線失敗` → 檢查環境變數設定

---

**v3.6.1 Process Group 總結**: 在 v3.6.0 關鍵字分析基礎上，升級為標準化查詢模式分析器，新增了完整的觀察名單處理統計功能。查詢模式分析器能識別和標準化 REFINED_SEARCH_PATTERNS 中定義的搜尋模式，將其轉換為 `{name} {symbol}` 格式並進行效果分析。觀察名單分析器基於StockID_TWSE_TPEX.csv統計每家公司的MD檔案處理狀態、品質評分、搜尋關鍵字模式等，提供觀察名單覆蓋率分析，幫助了解哪些公司已處理、哪些缺失，以及各公司的處理效果，為系統優化和公司覆蓋策略提供數據支撐。
