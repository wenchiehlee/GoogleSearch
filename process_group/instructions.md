# FactSet Pipeline v3.6.0 - Process Group 完整實作指南

## Version
{Process Group Instructions}=3.6.0

## 🎯 Process Group 概述

**目標**: 專門處理 MD 檔案的獨立群組，完全透過檔案系統與 Search Group 通訊

**輸入**: `data/md/*.md` 檔案 (由 Search Group 生成)
**輸出**: Google Sheets 報告 + CSV 檔案 + 關鍵字統計報告

**v3.6.0 新功能**: 
- ✅ 新增關鍵字統計報告 (`keyword-summary.csv`)
- ✅ MD 檔案 metadata 解析 (search_query 提取)
- ✅ 關鍵字品質評分統計分析
- ✅ 關鍵字效果評估和優化建議

**v3.6.0 架構特點**: 
- ✅ 完全獨立於 Search Group
- ✅ 透過檔案夾介面通訊 (`data/md/`)
- ✅ 模組化小檔案 (150-500 行)
- ✅ 單一職責設計
- ✅ 向下相容整合
- ✅ 關鍵字效果追蹤

## 📁 Process Group 檔案結構

```
process_group/                           # 📊 處理群組目錄
├── md_scanner.py                       # 150 行 - 檔案系統介面
├── process_cli.py                      # 500 行 - 命令列介面 (新增關鍵字命令)
├── md_parser.py                        # 600 行 - MD 內容解析 (新增 metadata 解析)
├── quality_analyzer.py                 # 500 行 - 品質分析
├── report_generator.py                 # 700 行 - 報告生成 (新增關鍵字報告)
├── keyword_analyzer.py                 # 400 行 - 關鍵字分析 (新增)
├── sheets_uploader.py                  # 500 行 - Google Sheets 上傳 (新增關鍵字工作表)
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
md_parser.py       → 只管解析 MD 內容和 metadata  
quality_analyzer.py → 只管品質評分
keyword_analyzer.py → 只管關鍵字分析 (新增)
report_generator.py → 只管生成報告
sheets_uploader.py → 只管上傳 Sheets
```

### 3. 獨立性原則
```python
# 每個模組都可以獨立測試
python md_scanner.py        # 測試檔案掃描
python md_parser.py         # 測試內容解析
python keyword_analyzer.py  # 測試關鍵字分析 (新增)
python quality_analyzer.py  # 測試品質評分
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

### 2. Process CLI (`process_cli.py`) - 500 行

#### 職責
- 提供命令列介面
- 協調各模組的執行
- 處理錯誤和日誌
- 支援向下相容性
- **新增關鍵字分析命令**

#### 核心類別
```python
class ProcessCLI:
    def __init__(self):
        self.md_scanner = MDScanner()
        # 可選模組 (graceful degradation)
        self.md_parser = None
        self.quality_analyzer = None  
        self.keyword_analyzer = None    # 新增
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
    
    def analyze_keywords_only(self, **kwargs):
        """只進行關鍵字分析 (新增)"""
    
    def generate_keyword_summary(self, upload_sheets=True, **kwargs):
        """生成關鍵字統計報告 (新增)"""
    
    def show_md_stats(self, **kwargs):
        """顯示統計資訊"""
    
    def validate_setup(self, **kwargs):
        """驗證環境設定"""
```

#### 命令列介面
```python
def main():
    parser = argparse.ArgumentParser(description='FactSet 處理系統 v3.6.0')
    parser.add_argument('command', choices=[
        'process',           # 處理所有 MD 檔案
        'process-recent',    # 處理最近的 MD 檔案
        'process-single',    # 處理單一公司
        'analyze-quality',   # 品質分析
        'analyze-keywords',  # 關鍵字分析 (新增)
        'keyword-summary',   # 關鍵字統計報告 (新增)
        'stats',            # 顯示統計資訊
        'validate'          # 驗證環境設定
    ])
    parser.add_argument('--company', help='公司代號')
    parser.add_argument('--hours', type=int, default=24, help='小時數')
    parser.add_argument('--no-upload', action='store_true', help='不上傳到 Sheets')
    parser.add_argument('--min-usage', type=int, default=1, help='關鍵字最小使用次數')
```

#### 錯誤處理
```python
def _init_optional_components(self):
    """初始化可選組件，支援 graceful degradation"""
    try:
        self.md_parser = MDParser()
    except ImportError:
        pass
    
    try:
        self.keyword_analyzer = KeywordAnalyzer()  # 新增
    except ImportError:
        pass
    
    # 基本功能 (只用 MDScanner) 總是可用
    # 進階功能 (品質分析、關鍵字分析、報告生成) 可選
```

---

### 3. MD Parser (`md_parser.py`) - 600 行

#### 職責
- 解析 MD 檔案內容
- **新增 metadata 解析 (search_query 提取)**
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
        
        # Metadata 模式 (新增)
        self.metadata_patterns = {
            'search_query': r'search_query:\s*(.+?)(?:\n|$)',
            'company_code': r'company_code:\s*(.+?)(?:\n|$)',
            'data_source': r'data_source:\s*(.+?)(?:\n|$)',
            'timestamp': r'timestamp:\s*(.+?)(?:\n|$)'
        }
    
    def parse_md_file(self, file_path: str) -> Dict[str, Any]:
        """主要解析方法"""
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """提取 MD 檔案 metadata (新增)"""
```

#### 解析結果格式
```python
# parse_md_file 返回格式 (v3.6.0 新增欄位)
{
    # 基本資訊 (從檔案路徑)
    'filename': str,
    'company_code': str,
    'company_name': str,
    'data_source': str,
    'file_mtime': datetime,
    
    # Metadata 資訊 (新增)
    'search_query': str,           # 例如: "神盾 factset EPS 預估"
    'search_keywords': List[str],  # 例如: ["神盾", "factset", "EPS", "預估"]
    'metadata_complete': bool,     # metadata 是否完整
    
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
def _extract_metadata(self, content: str) -> Dict[str, Any]:
    """提取 MD 檔案 metadata (新增)"""
    metadata = {}
    
    # 尋找 metadata 區塊 (通常在檔案開頭)
    lines = content.split('\n')[:20]  # 檢查前20行
    
    for line in lines:
        for key, pattern in self.metadata_patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()
    
    # 處理 search_query
    if 'search_query' in metadata:
        search_query = metadata['search_query']
        # 分解成關鍵字
        keywords = self._extract_keywords_from_query(search_query)
        metadata['search_keywords'] = keywords
    
    return metadata

def _extract_keywords_from_query(self, search_query: str) -> List[str]:
    """從 search_query 提取關鍵字 (新增)"""
    # 移除常見的連接詞和停用詞
    stop_words = {'的', '和', '與', '或', '及', 'and', 'or', 'the', 'a', 'an'}
    
    # 分割並清理關鍵字
    keywords = []
    for word in search_query.split():
        word = word.strip().lower()
        if word and word not in stop_words and len(word) > 1:
            keywords.append(word)
    
    return keywords

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

### 4. Keyword Analyzer (`keyword_analyzer.py`) - 400 行 (新增)

#### 職責
- 分析所有 MD 檔案中的關鍵字使用情況
- 計算關鍵字與品質評分的關聯性
- 提供關鍵字效果評估
- 支援關鍵字過濾和統計

#### 核心類別
```python
class KeywordAnalyzer:
    def __init__(self):
        self.stop_words = {
            '的', '和', '與', '或', '及', '在', '為', '是', '有', '此', '將', '會',
            'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for'
        }
        
        # 關鍵字分類
        self.keyword_categories = {
            'company': ['公司', '企業', '集團', 'corp', 'company', 'group'],
            'financial': ['eps', '營收', '獲利', '股價', '目標價', 'revenue', 'profit'],
            'analysis': ['分析', '預估', '評估', '展望', 'analysis', 'forecast', 'estimate'],
            'source': ['factset', 'bloomberg', '券商', '投顧', 'analyst']
        }
    
    def analyze_all_keywords(self, processed_companies: List[Dict]) -> Dict[str, Any]:
        """分析所有關鍵字統計"""
    
    def get_keyword_quality_mapping(self, processed_companies: List[Dict]) -> Dict[str, Dict]:
        """取得關鍵字與品質評分的對應關係"""
    
    def filter_keywords_by_usage(self, keyword_stats: Dict, min_usage: int = 2) -> Dict:
        """過濾低使用率關鍵字"""
    
    def categorize_keywords(self, keywords: List[str]) -> Dict[str, List[str]]:
        """將關鍵字分類"""
    
    def get_top_keywords(self, keyword_stats: Dict, top_n: int = 20) -> List[Tuple[str, Dict]]:
        """取得效果最好的關鍵字"""
```

#### 分析結果格式
```python
# analyze_all_keywords 返回格式
{
    'total_keywords': int,
    'unique_keywords': int,
    'total_usage': int,
    'avg_quality_score': float,
    
    'keyword_stats': {
        'keyword_name': {
            'usage_count': int,
            'avg_quality_score': float,
            'max_quality_score': float,
            'min_quality_score': float,
            'company_count': int,
            'companies': List[str],
            'quality_scores': List[float],
            'category': str
        }
    },
    
    'category_stats': {
        'company': {'count': int, 'avg_quality': float},
        'financial': {'count': int, 'avg_quality': float},
        'analysis': {'count': int, 'avg_quality': float},
        'source': {'count': int, 'avg_quality': float},
        'other': {'count': int, 'avg_quality': float}
    },
    
    'quality_distribution': {
        'excellent': List[str],    # 9-10 分關鍵字
        'good': List[str],         # 7-8 分關鍵字
        'average': List[str],      # 5-6 分關鍵字
        'poor': List[str]          # 0-4 分關鍵字
    }
}
```

#### 核心分析方法
```python
def _calculate_keyword_statistics(self, processed_companies: List[Dict]) -> Dict[str, Dict]:
    """計算每個關鍵字的統計資料"""
    keyword_stats = {}
    
    for company_data in processed_companies:
        keywords = company_data.get('search_keywords', [])
        quality_score = company_data.get('quality_score', 0)
        company_code = company_data.get('company_code', '')
        
        for keyword in keywords:
            if keyword not in keyword_stats:
                keyword_stats[keyword] = {
                    'usage_count': 0,
                    'quality_scores': [],
                    'companies': set(),
                    'category': self._get_keyword_category(keyword)
                }
            
            keyword_stats[keyword]['usage_count'] += 1
            keyword_stats[keyword]['quality_scores'].append(quality_score)
            keyword_stats[keyword]['companies'].add(company_code)
    
    # 計算統計值
    for keyword, stats in keyword_stats.items():
        scores = stats['quality_scores']
        stats.update({
            'avg_quality_score': sum(scores) / len(scores),
            'max_quality_score': max(scores),
            'min_quality_score': min(scores),
            'company_count': len(stats['companies']),
            'companies': list(stats['companies'])
        })
    
    return keyword_stats

def _get_keyword_category(self, keyword: str) -> str:
    """判斷關鍵字類別"""
    keyword_lower = keyword.lower()
    
    for category, category_keywords in self.keyword_categories.items():
        if any(ck in keyword_lower for ck in category_keywords):
            return category
    
    return 'other'

def _calculate_quality_distribution(self, keyword_stats: Dict) -> Dict[str, List[str]]:
    """計算品質分布"""
    distribution = {
        'excellent': [],  # 9-10 分
        'good': [],       # 7-8 分  
        'average': [],    # 5-6 分
        'poor': []        # 0-4 分
    }
    
    for keyword, stats in keyword_stats.items():
        avg_score = stats['avg_quality_score']
        if avg_score >= 9:
            distribution['excellent'].append(keyword)
        elif avg_score >= 7:
            distribution['good'].append(keyword)
        elif avg_score >= 5:
            distribution['average'].append(keyword)
        else:
            distribution['poor'].append(keyword)
    
    return distribution
```

---

### 5. Quality Analyzer (`quality_analyzer.py`) - 500 行

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

### 6. Report Generator (`report_generator.py`) - 700 行

#### 職責
- 生成標準化投資組合報告
- 支援 14 欄位摘要 + 21 欄位詳細格式
- **新增關鍵字統計報告 (keyword-summary.csv)**
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
        
        # 關鍵字報告欄位 (新增)
        self.keyword_summary_columns = [
            '關鍵字', '使用次數', '平均品質評分', '最高品質評分', '最低品質評分',
            '相關公司數量', '品質狀態', '分類', '效果評級', '更新日期'
        ]
    
    def generate_portfolio_summary(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """生成投資組合摘要 (14 欄位)"""
    
    def generate_detailed_report(self, processed_companies: List[Dict]) -> pd.DataFrame:
        """生成詳細報告 (21 欄位)"""
    
    def generate_keyword_summary(self, keyword_analysis: Dict[str, Any]) -> pd.DataFrame:
        """生成關鍵字統計報告 (新增)"""
    
    def save_all_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                        keyword_df: pd.DataFrame = None) -> Dict[str, str]:
        """儲存所有報告為 CSV (新增關鍵字報告)"""
```

#### 關鍵字報告生成 (新增)
```python
def generate_keyword_summary(self, keyword_analysis: Dict[str, Any]) -> pd.DataFrame:
    """生成關鍵字統計報告"""
    keyword_data = []
    keyword_stats = keyword_analysis.get('keyword_stats', {})
    
    for keyword, stats in keyword_stats.items():
        # 計算效果評級
        avg_score = stats['avg_quality_score']
        if avg_score >= 9:
            effect_rating = "優秀 ⭐⭐⭐"
        elif avg_score >= 7:
            effect_rating = "良好 ⭐⭐"
        elif avg_score >= 5:
            effect_rating = "普通 ⭐"
        else:
            effect_rating = "需改善"
        
        # 品質狀態
        quality_status = self._get_quality_status(avg_score)
        
        keyword_data.append({
            '關鍵字': keyword,
            '使用次數': stats['usage_count'],
            '平均品質評分': round(avg_score, 2),
            '最高品質評分': stats['max_quality_score'],
            '最低品質評分': stats['min_quality_score'],
            '相關公司數量': stats['company_count'],
            '品質狀態': quality_status,
            '分類': stats['category'],
            '效果評級': effect_rating,
            '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # 按平均品質評分排序
    keyword_data.sort(key=lambda x: x['平均品質評分'], reverse=True)
    
    return pd.DataFrame(keyword_data, columns=self.keyword_summary_columns)

def _get_quality_status(self, score: float) -> str:
    """取得品質狀態指標"""
    if score >= 9:
        return "🟢 優秀"
    elif score >= 7:
        return "🟡 良好"
    elif score >= 5:
        return "🟠 普通"
    else:
        return "🔴 需改善"
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

# Keyword Summary (10 欄位) - 新增
關鍵字,使用次數,平均品質評分,最高品質評分,最低品質評分,相關公司數量,品質狀態,分類,效果評級,更新日期
神盾,15,8.7,10,7.2,8,🟡 良好,company,良好 ⭐⭐,2025-06-24 10:45:00
factset,45,8.2,10,5.1,25,🟡 良好,source,良好 ⭐⭐,2025-06-24 10:45:00
eps,38,7.9,9.8,4.3,22,🟡 良好,financial,良好 ⭐⭐,2025-06-24 10:45:00
預估,33,7.1,9.5,3.2,19,🟡 良好,analysis,良好 ⭐⭐,2025-06-24 10:45:00
```

---

### 7. Sheets Uploader (`sheets_uploader.py`) - 500 行

#### 職責
- 上傳報告到 Google Sheets
- 設定工作表格式和樣式
- **新增關鍵字工作表上傳**
- 處理 Google Sheets API 連線
- 支援連線測試

#### 核心類別
```python
class SheetsUploader:
    def __init__(self, github_repo_base="https://raw.githubusercontent.com/..."):
        self.github_repo_base = github_repo_base
        self.client = None
        self.spreadsheet = None
        
        # 工作表名稱
        self.worksheet_names = {
            'portfolio': 'Portfolio Summary',
            'detailed': 'Detailed Report',
            'keywords': 'Keyword Summary'  # 新增
        }
    
    def upload_all_reports(self, portfolio_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                          keyword_df: pd.DataFrame = None) -> bool:
        """上傳所有報告 (新增關鍵字報告)"""
    
    def test_connection(self) -> bool:
        """測試 Google Sheets 連線"""
    
    def _setup_connection(self) -> bool:
        """設定 Google Sheets 連線"""
    
    def _upload_portfolio_summary(self, portfolio_df: pd.DataFrame) -> bool:
        """上傳投資組合摘要"""
    
    def _upload_detailed_report(self, detailed_df: pd.DataFrame) -> bool:
        """上傳詳細報告"""
    
    def _upload_keyword_summary(self, keyword_df: pd.DataFrame) -> bool:
        """上傳關鍵字統計報告 (新增)"""
```

#### 關鍵字工作表上傳 (新增)
```python
def _upload_keyword_summary(self, keyword_df: pd.DataFrame) -> bool:
    """上傳關鍵字統計報告"""
    try:
        # 建立或取得關鍵字工作表
        try:
            worksheet = self.spreadsheet.worksheet(self.worksheet_names['keywords'])
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=self.worksheet_names['keywords'], 
                rows=1000, 
                cols=20
            )
        
        # 清空現有資料
        worksheet.clear()
        
        # 上傳資料
        worksheet.update([keyword_df.columns.values.tolist()] + keyword_df.values.tolist())
        
        # 設定格式
        self._format_keyword_worksheet(worksheet, len(keyword_df))
        
        return True
    except Exception as e:
        print(f"❌ 關鍵字報告上傳失敗: {e}")
        return False

def _format_keyword_worksheet(self, worksheet, data_rows: int):
    """格式化關鍵字工作表 (新增)"""
    # 設定標題列格式
    worksheet.format('A1:J1', {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    })
    
    # 設定品質評分欄位顏色編碼
    if data_rows > 0:
        # 優秀 (9-10): 綠色
        worksheet.format(f'C2:C{data_rows+1}', {
            'backgroundColor': {'red': 0.8, 'green': 1, 'blue': 0.8}
        })
        
        # 設定關鍵字欄位自動寬度
        worksheet.format('A:A', {'columnWidth': 120})
        worksheet.format('B:J', {'columnWidth': 100})
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

### 1. Process CLI 整合模式 (v3.6.0 更新)
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
        
        # 3. 關鍵字分析 (新增)
        keyword_analysis = self.keyword_analyzer.analyze_all_keywords(processed_companies)
        
        # 4. 生成報告 (包含關鍵字報告)
        portfolio_summary = self.report_generator.generate_portfolio_summary(processed_companies)
        detailed_report = self.report_generator.generate_detailed_report(processed_companies)
        keyword_summary = self.report_generator.generate_keyword_summary(keyword_analysis)
        
        # 5. 上傳 (可選)
        if upload_sheets:
            self.sheets_uploader.upload_all_reports(portfolio_summary, detailed_report, keyword_summary)
    
    def generate_keyword_summary(self, upload_sheets=True, **kwargs):
        """專門生成關鍵字統計報告 (新增)"""
        # 1. 掃描檔案
        md_files = self.md_scanner.scan_all_md_files()
        
        # 2. 解析 metadata
        processed_companies = []
        for md_file in md_files:
            parsed_data = self.md_parser.parse_md_file(md_file)
            quality_data = self.quality_analyzer.analyze(parsed_data)
            company_data = {**parsed_data, **quality_data}
            processed_companies.append(company_data)
        
        # 3. 關鍵字分析
        keyword_analysis = self.keyword_analyzer.analyze_all_keywords(processed_companies)
        
        # 4. 生成關鍵字報告
        keyword_summary = self.report_generator.generate_keyword_summary(keyword_analysis)
        
        # 5. 儲存 CSV
        csv_path = self.report_generator.save_keyword_summary(keyword_summary)
        
        # 6. 上傳 (可選)
        if upload_sheets and self.sheets_uploader:
            self.sheets_uploader._upload_keyword_summary(keyword_summary)
        
        return keyword_analysis, csv_path
```

### 2. 錯誤處理模式
```python
def _init_optional_components(self):
    """Graceful degradation 模式"""
    components = [
        ('md_parser', MDParser),
        ('quality_analyzer', QualityAnalyzer),
        ('keyword_analyzer', KeywordAnalyzer),  # 新增
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

### 3. 資料流動模式 (v3.6.0 更新)
```
MD Files → MDScanner → ProcessCLI → MDParser → QualityAnalyzer → KeywordAnalyzer → ReportGenerator → SheetsUploader
   ↓           ↓           ↓           ↓            ↓               ↓               ↓              ↓
檔案清單    檔案資訊    解析資料    品質評分     關鍵字分析      結構化資料      CSV報告      Google Sheets
                      (含metadata)                              (3個報告)
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
    
    # 測試關鍵字分析 (新增)
    if self.keyword_analyzer:
        # 簡單測試
        results['keyword_analyzer'] = "關鍵字分析模組已載入"
    
    # 測試其他組件...
    return results
```

### 3. 使用者測試模式
```bash
# 基本功能測試
python process_cli.py validate
python process_cli.py stats

# 關鍵字功能測試 (新增)
python process_cli.py analyze-keywords
python process_cli.py keyword-summary --no-upload

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

# 5. 關鍵字分析 (新增)
python process_cli.py analyze-keywords
```

### 2. 關鍵字分析流程 (新增)
```bash
# 生成關鍵字統計報告
python process_cli.py keyword-summary

# 生成關鍵字統計報告 (不上傳)
python process_cli.py keyword-summary --no-upload

# 過濾低使用率關鍵字
python process_cli.py keyword-summary --min-usage=3
```

### 3. 高級使用流程
```bash
# 處理最近檔案
python process_cli.py process-recent --hours=12

# 處理單一公司
python process_cli.py process-single --company=2330

# 完整處理 (包含關鍵字分析和上傳)
python process_cli.py process
```

### 4. 故障排除
```bash
# 檢查模組載入狀態
python process_cli.py validate

# 測試 Google Sheets 連線
python sheets_uploader.py --test-connection

# 檢查檔案狀態
python process_cli.py stats

# 檢查關鍵字分析 (新增)
python keyword_analyzer.py --test-analysis
```

## 📋 實作檢查清單

### ✅ 必須實作的功能
- [ ] `MDScanner` 檔案掃描和統計
- [ ] `ProcessCLI` 命令列介面和協調
- [ ] `MDParser` MD 內容解析和 metadata 提取 (更新)
- [ ] `QualityAnalyzer` 品質評分系統
- [ ] `KeywordAnalyzer` 關鍵字分析系統 (新增)
- [ ] `ReportGenerator` 報告生成 (包含關鍵字報告)
- [ ] `SheetsUploader` Google Sheets 上傳 (包含關鍵字工作表)

### ✅ 必須支援的格式
- [ ] 14 欄位投資組合摘要格式
- [ ] 21 欄位詳細報告格式
- [ ] 10 欄位關鍵字統計格式 (新增)
- [ ] GitHub Raw URL MD 檔案連結
- [ ] 0-10 標準化品質評分
- [ ] 🟢🟡🟠🔴 品質狀態指標

### ✅ 必須提供的命令
- [ ] `process` - 處理所有檔案
- [ ] `process-recent` - 處理最近檔案
- [ ] `process-single` - 處理單一公司
- [ ] `analyze-quality` - 品質分析
- [ ] `analyze-keywords` - 關鍵字分析 (新增)
- [ ] `keyword-summary` - 關鍵字統計報告 (新增)
- [ ] `stats` - 統計資訊
- [ ] `validate` - 環境驗證

### ✅ 必須處理的錯誤
- [ ] 模組載入失敗 (graceful degradation)
- [ ] 檔案不存在或格式錯誤
- [ ] Metadata 解析失敗 (新增)
- [ ] 關鍵字提取失敗 (新增)
- [ ] Google Sheets 連線失敗
- [ ] 解析錯誤和資料品質問題

### ✅ 關鍵字分析功能 (新增)
- [ ] 從 search_query 提取關鍵字
- [ ] 計算關鍵字使用統計
- [ ] 關鍵字與品質評分關聯分析
- [ ] 關鍵字分類 (公司、財務、分析、來源)
- [ ] 關鍵字效果評級 (優秀/良好/普通/需改善)
- [ ] 關鍵字品質分布統計
- [ ] 低使用率關鍵字過濾
- [ ] 關鍵字 CSV 報告生成
- [ ] 關鍵字 Google Sheets 上傳

---

**v3.6.0 Process Group 總結**: 在 v3.5.0 基礎上新增了完整的關鍵字分析功能，可以統計 MD 檔案中 search_query 的關鍵字使用情況，分析關鍵字與品質評分的關聯性，生成關鍵字統計報告，幫助了解哪些關鍵字效果好、哪些需要改善，為搜尋策略優化提供數據支撐。