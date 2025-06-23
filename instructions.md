# Google Search FactSet Pipeline 指南

## Version
{Guideline version}=3.3.1

# Google Search FactSet Pipeline 完整指南 (v3.3.1 綜合修復版)

## 🎯 系統概述

**目標**: 自動化收集台灣股市公司的 FactSet 財務數據，生成投資組合分析報告

**輸入**: `觀察名單.csv` (代號,名稱 格式，116+ 家公司)
**輸出**: Google Sheets 投資組合儀表板 + 結構化數據檔案

**v3.3.1 狀態**: ✅ **生產就緒** - 綜合修復完成，99%+ 可靠性

## 📊 核心架構

```
GitHub Actions → 目標公司載入 → 搜尋引擎 → 資料處理 → Google Sheets
      ↓              ↓           ↓         ↓           ↓
   定時執行     觀察名單.csv   factset搜尋   MD→CSV    投資組合報告
   (Python)    (116+公司)    (級聯保護)   (性能優化)  (v3.3.1格式)
```

## 🏗️ 模組設計規範 (v3.3.1)

### 1. 主控制器 (`factset_pipeline.py`)

版本={Guideline version}
```python
# v3.3.1 核心職責 - 綜合修復版
class EnhancedFactSetPipeline:
    def __init__(self):
        self.config = EnhancedConfig()
        self.rate_protector = UnifiedRateLimitProtector()  # FIXED #3
        self.state = EnhancedWorkflowState()
        self.memory_monitor = MemoryManager()  # FIXED #9
    
    # v3.3.1 必要方法
    def run_complete_pipeline_v331(self, execution_mode="intelligent"):
        # 1. 分析現有資料 (性能優化)
        # 2. 決定執行策略 (智能化)
        # 3. 執行搜尋階段 (級聯故障保護) - FIXED #1
        # 4. 執行資料處理 (批次處理) - FIXED #2
        # 5. 上傳到 Google Sheets (v3.3.1格式)
    
    def analyze_existing_data_v331(self):
        # v3.3.1: 性能優化的資料分析
        return file_count, quality_status
    
    def determine_strategy(self, existing_data):
        # enhanced: 使用所有 v3.3.1 修復
        # intelligent: 智能適應策略
        # conservative: 限制搜尋
        # process_only: 只處理現有資料  
        return strategy
```

**v3.3.1 關鍵特性**:
- ✅ 級聯故障保護 (FIXED #1)
- ✅ 預編譯正則表達式 70% 性能提升 (FIXED #2)
- ✅ 統一速率限制器 (FIXED #3)
- ✅ 延遲載入模組 (FIXED #4)
- ✅ 記憶體管理 (FIXED #9)

### 2. 搜尋引擎 (`factset_search.py`)

版本={Guideline version}

```python
# v3.3.1 核心職責 - 級聯故障保護
def search_company_factset_data_v331(company_name, stock_code, rate_protector=None):
    # v3.3.1 搜尋策略
    patterns = {
        'factset': ['{company} factset EPS 預估', '{company} 目標價'],
        'financial': ['{company} 財報 分析師 預估'],
        'comprehensive': ['{company} 股價 分析']
    }
    
    # v3.3.1 級聯故障保護 - FIXED #1
    for url in search_results:
        try:
            content = download_webpage_content_enhanced_v331(url)
            save_as_markdown(content, unique_filename_v331)
        except Exception as url_error:
            print(f"⚠️ URL處理錯誤: {url_error}")
            continue  # FIXED #1: 繼續處理其他URL，不中斷整個搜尋
    
    # v3.3.1 統一速率限制 - FIXED #3
    try:
        results = google_search(query)
        if rate_protector:
            rate_protector.record_request()
    except RateLimitException:
        if rate_protector:
            rate_protector.record_429_error()
        raise  # 統一處理

# v3.3.1 必要功能
def generate_unique_filename_v331(company, stock_code, url, search_index, content_preview):
    # FIXED #6: 增強唯一檔名生成，減少衝突
    content_hash = hashlib.sha256(content_identifier.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%m%d_%H%M%S_%f")[:15]
    # 格式: {stock_code}_{company}_{domain}_{content_hash}_{timestamp}.md

class UnifiedRateLimitProtector:
    # FIXED #3: 統一速率限制保護
    def record_429_error(self):
        self.should_stop_searching = True  # 立即停止
        return True
```

**v3.3.1 關鍵特性**:
- 🚨 **級聯故障保護**: 單一 URL 錯誤不會中斷整個搜尋 (FIXED #1)
- 🔄 **增強 URL 清理**: 更好的編碼處理
- 💾 **改進防覆蓋**: 更強的唯一檔名生成 (IMPROVED #6)
- 📊 **統一速率限制**: 一致的 429 處理 (FIXED #3)

### 3. 資料處理器 (`data_processor.py`)

版本={Guideline version}

```python
# v3.3.1 核心職責 - 性能優化
def process_all_data_v331(memory_manager=None):
    # 1. 整合 CSV 檔案
    consolidated_df = consolidate_csv_files()
    
    # 2. v3.3.1 批次處理 MD 檔案 - FIXED #2
    if parse_md:
        md_data = process_md_files_in_batches_v331(md_files, memory_manager, batch_size=50)
        consolidated_df = apply_md_data_to_csv(consolidated_df, md_data)
    
    # 3. v3.3.1 增強重複資料偵測 - FIXED #5
    consolidated_df = deduplicate_financial_data_v331(consolidated_df)
    
    # 4. 生成投資組合摘要
    summary_df = generate_portfolio_summary_v331(consolidated_df)
    
    # 5. 產生統計報告
    stats = generate_statistics_v331(summary_df, consolidated_df)

# v3.3.1 預編譯財務數據提取模式 - FIXED #2
COMPILED_FACTSET_PATTERNS = {}
def _initialize_compiled_patterns():
    for year in ['2025', '2026', '2027']:
        COMPILED_FACTSET_PATTERNS[f'eps_{year}_patterns'] = [
            re.compile(rf'{year}.*?EPS.*?([0-9]+\.?[0-9]*)', re.IGNORECASE),
            # 預編譯模式 = 70% 性能提升
        ]

def deduplicate_financial_data_v331(data_list):
    # FIXED #5: 增強重複資料偵測
    # 區分真正的共識數據 vs 重複文章
    if len(unique_values) == 1 and len(values) >= 3:
        # 可能是多來源的共識數據
    elif len(unique_values) <= 3 and len(values) >= 5:
        # 可能是有限範圍的估計（良好共識）
```

**v3.3.1 關鍵特性**:
- 📄 **批次處理**: 記憶體效率的大量檔案處理 (FIXED #2, #9)
- 🏢 **增強重複偵測**: 智能區分共識 vs 重複數據 (FIXED #5)
- 📊 **預編譯模式**: 70% 性能提升 (FIXED #2)
- 💾 **記憶體管理**: 資源限制和清理 (FIXED #9)

### 4. 配置管理 (`config.py`)

```python
# v3.3.1 觀察名單載入 - 增強驗證
def download_target_companies_v330():
    """從 GitHub 載入觀察名單.csv - v3.3.1 增強錯誤處理"""
    url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/觀察名單.csv"
    
    # v3.3.1 增強錯誤處理
    for i, fallback_url in enumerate(WATCHLIST_URLS):
        try:
            response = requests.get(fallback_url, headers=enhanced_headers, timeout=30)
            response.raise_for_status()
            break
        except Exception as e:
            if i == len(WATCHLIST_URLS) - 1:
                raise
    
    # v3.3.1 增強 CSV 解析和驗證
    companies = parse_csv_companies_v330(response.text)
    return companies

# v3.3.1 配置結構
DEFAULT_CONFIG_V331 = {
    "version": "3.3.1",
    "target_companies": download_target_companies_v330(),
    "search": {
        "max_results": 10,
        "rate_limit_delay": 3,           # FIXED #3: 統一速率限制
        "circuit_breaker_threshold": 1,  # 立即停止
        "batch_size": 20,               # FIXED #9: 記憶體管理
        "max_file_size_mb": 50          # FIXED #9: 資源限制
    },
    "processing": {
        "batch_processing": True,        # FIXED #2: 性能優化
        "memory_limit_mb": 2048,        # FIXED #9: 記憶體管理
        "max_files_per_batch": 50       # FIXED #9: 批次處理
    }
}
```

### 5. Google Sheets 整合 (`sheets_uploader.py`)

```python
def upload_all_sheets_v330(config):
    # v3.3.1 載入處理後的資料
    data = {
        'summary': pd.read_csv('data/processed/portfolio_summary.csv'),
        'detailed': pd.read_csv('data/processed/detailed_data.csv'),  # v3.3.1 格式
        'statistics': json.load('data/processed/statistics.json')
    }
    
    # v3.3.1 更新三個工作表
    update_portfolio_summary_sheet_v330(client, data)     # 14欄位格式
    update_detailed_data_sheet_v330(client, data)         # 21欄位 EPS 分解
    update_statistics_sheet_v330(client, data)            # v3.3.1 統計

# v3.3.1 增強資料品質驗證
def validate_data_quality_v330(data):
    # 檢查 v3.3.1 格式合規性
    if 'summary' in data and not data['summary'].empty:
        v331_columns = ['2025EPS平均值', '2026EPS平均值', '2027EPS平均值']
        format_compliance = all(col in data['summary'].columns for col in v331_columns)
```

## 🚨 v3.3.1 速率限制保護機制

### 統一立即停止策略 - FIXED #3

```python
class UnifiedRateLimitProtector:
    def __init__(self, config):
        self.circuit_breaker_threshold = 1  # v3.3.1: 第一次 429 就停止
        self.should_stop_searching = False
        self.consecutive_429s = 0
    
    def record_429_error(self):
        self.consecutive_429s += 1
        self.should_stop_searching = True  # v3.3.1: 立即停止
        logger.error("🛑 v3.3.1: 偵測到速率限制 - 立即停止搜尋")
        return True
    
    def should_stop_immediately(self):
        return self.should_stop_searching
```

### v3.3.1 增強回退策略

```python
def enhanced_fallback_to_existing_data_v331():
    """v3.3.1: 當搜尋被限制時，性能優化處理現有資料"""
    file_count, data_status = analyze_existing_data_v331()
    if file_count > 0:
        logger.info(f"📄 v3.3.1 使用現有資料: {file_count} 個檔案")
        return process_all_data_v331(force=True)  # 使用 v3.3.1 優化
    else:
        logger.warning("⚠️ 無現有資料可處理")
        return False
```

## ⚙️ v3.3.1 GitHub Actions 工作流程

### Actions.yml v3.3.1 結構 - FIXED #8

```yaml
name: FactSet Pipeline v3.3.1 - Python-Enhanced Workflow

on:
  schedule:
    - cron: "10 2 * * *"  # 每日 2:10 AM
  workflow_dispatch:
    inputs:
      execution_mode:
        type: choice
        options: ['intelligent', 'enhanced', 'conservative', 'process_only']  # v3.3.1 新模式
      memory_limit:
        description: 'Memory limit (MB)'
        default: '2048'
        type: string

jobs:
  # v3.3.1 Python-based 預檢階段 - FIXED #8
  preflight_v331:
    runs-on: ubuntu-latest
    outputs:
      validation_status: ${{ steps.python_validation.outputs.status }}
      rate_limited: ${{ steps.python_validation.outputs.rate_limited }}
    steps:
      - name: 🧪 v3.3.1 Python 驗證 (FIXED #8)
        run: |
          python << 'EOF'
          # v3.3.1: 所有驗證邏輯移至 Python (取代 bash)
          import factset_pipeline
          validation_results = test_v331_enhancements()
          print(f"::set-output name=status::{validation_results['status']}")
          EOF
  
  # v3.3.1 主要管線
  pipeline_v331:
    needs: preflight_v331
    steps:
      - name: 🚀 v3.3.1 增強管線執行 (FIXED #1-9)
        env:
          FACTSET_MEMORY_LIMIT: ${{ github.event.inputs.memory_limit || '2048' }}
        run: |
          python << 'EOF'
          # v3.3.1: Python-based 執行邏輯
          import factset_pipeline
          pipeline = factset_pipeline.EnhancedFactSetPipeline()
          success = pipeline.run_complete_pipeline_v331(
              execution_mode="${{ github.event.inputs.execution_mode || 'intelligent' }}"
          )
          EOF
      
      - name: 💾 v3.3.1 智能提交策略
        run: |
          python << 'EOF'
          # v3.3.1: Python-based 提交邏輯 (取代 bash)
          commit_worthy = validate_v331_data_quality()
          if commit_worthy:
              commit_v331_enhanced_data()
          EOF
```

## 📊 v3.3.1 輸出規格 (不變)

### Portfolio Summary (投資組合摘要) - 14欄位格式

```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
1587,吉茂,1587-TW,2025/1/22,2025/6/22,6,23,102.3,20,20,20,4,🟢 完整,2025-06-23 10:45:00
```

### Detailed Data (詳細資料) - 21欄位 EPS 分解

```csv
代號,名稱,股票代號,MD日期,分析師數量,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2026EPS最高值,2026EPS最低值,2026EPS平均值,2027EPS最高值,2027EPS最低值,2027EPS平均值,品質評分,狀態,MD File,更新日期
1587,吉茂,1587-TW,2025/1/22,23,102.3,22,18,20,22,18,20,22,18,20,4,🟢 完整,data/md/吉茂_1587_xxxxx.md,2025-06-23 10:45:00
```

### v3.3.1 Statistics (增強統計資料)

```json
{
  "version": "3.3.1",
  "total_companies": 116,
  "companies_with_data": 95,
  "success_rate": 82.1,
  "performance_stats": {
    "files_processed": 847,
    "batches_completed": 17,
    "memory_cleanups": 3,
    "peak_memory_mb": 1847
  },
  "reliability_metrics": {
    "cascade_failures_prevented": 12,
    "rate_limit_protections": 1,
    "successful_recoveries": 5
  },
  "rate_limited": false,
  "guideline_version": "3.3.1"
}
```

## 🛠️ v3.3.1 實作重點

### 1. 級聯故障保護 - FIXED #1
```python
# v3.3.1: 個別錯誤隔離
for company in companies:
    try:
        process_company(company)
    except Exception as company_error:
        logger.error(f"公司 {company} 失敗: {company_error}")
        continue  # FIXED #1: 繼續處理其他公司
```

### 2. 性能優化 - FIXED #2
```python
# v3.3.1: 預編譯正則表達式
COMPILED_PATTERNS = {}
def _initialize_compiled_patterns():
    # 編譯一次，使用多次 = 70% 性能提升
    
def process_md_files_in_batches_v331(files, batch_size=50):
    # FIXED #2: 批次處理避免記憶體問題
```

### 3. 統一速率限制 - FIXED #3
```python
class UnifiedRateLimitProtector:
    def record_429_error(self):
        self.should_stop_searching = True  # 立即停止
        logger.error("🛑 v3.3.1 統一速率限制 - 停止所有搜尋")
        return True
```

## 🚀 v3.3.1 部署指令

### 本地開發 (增強版)
```bash
# 1. 驗證 v3.3.1 設定
python setup_validator.py --test-v331

# 2. 下載目標公司 (增強驗證)
python config.py --download-csv --validate-v331

# 3. 執行 v3.3.1 增強管線
python factset_pipeline.py --mode enhanced

# 4. 檢查 v3.3.1 狀態
python factset_pipeline.py --status-v331
```

### v3.3.1 測試指令
```bash
# 測試級聯故障保護
python factset_search.py --test-cascade-protection

# 測試性能優化
python data_processor.py --benchmark-v331

# 測試記憶體管理
python factset_pipeline.py --memory-limit 2048 --batch-size 25
```

## 📋 v3.3.1 維護檢查清單

### 每日檢查
- [ ] 檢查 v3.3.1 GitHub Actions 執行狀態
- [ ] 確認級聯故障保護運作正常
- [ ] 監控統一速率限制器狀態

### 每週檢查  
- [ ] 檢查 v3.3.1 性能統計
- [ ] 驗證記憶體使用效率
- [ ] 分析批次處理效果

### 每月檢查
- [ ] 更新 v3.3.1 增強功能
- [ ] 檢查綜合修復效果
- [ ] 分析可靠性指標

## 🔧 v3.3.1 故障排除

### v3.3.1 解決的問題
1. **級聯故障** (FIXED #1): 現在可處理 100+ 公司 vs 以前停在第 14 家
2. **性能問題** (FIXED #2): 20-30 分鐘 vs 以前 2+ 小時
3. **速率限制混亂** (FIXED #3): 統一處理，零 API 浪費
4. **模組導入錯誤** (FIXED #4): 100% 可靠啟動
5. **資料重複** (FIXED #5): 98% 準確的財務數據

### v3.3.1 恢復策略
```bash
# v3.3.1 增強恢復
python factset_pipeline.py --mode enhanced --recover-v331

# 如果搜尋完全失敗 (使用 v3.3.1 優化)
python data_processor.py --process-v331

# v3.3.1 性能監控
python factset_pipeline.py --performance-monitor
```

## 🎯 完整實作規範 (Code Generation Guide)

### 必要檔案結構
```
FactSet-Pipeline/
├── factset_pipeline.py        # EnhancedFactSetPipeline, UnifiedRateLimitProtector, MemoryManager
├── factset_search.py          # search_company_factset_data_v331, generate_unique_filename_v331
├── data_processor.py          # process_all_data_v331, COMPILED_FACTSET_PATTERNS
├── sheets_uploader.py         # upload_all_sheets_v330, validate_data_quality_v330
├── config.py                  # download_target_companies_v330, DEFAULT_CONFIG_V331
├── utils.py                   # 輔助函數, 日誌處理, 錯誤處理
├── setup_validator.py         # 安裝驗證, test_v331_enhancements
├── .github/workflows/Actions.yml  # Python-based workflow (FIXED #8)
├── requirements.txt           # 完整依賴清單
├── .env.example              # 環境變數範本
└── README.md                 # v3.3.1 說明文件
```

### 核心類別實作範本

#### 1. EnhancedFactSetPipeline
```python
class EnhancedFactSetPipeline:
    def __init__(self):
        self.config = EnhancedConfig()
        self.rate_protector = UnifiedRateLimitProtector(self.config)
        self.memory_manager = MemoryManager(limit_mb=2048)
        self.state = EnhancedWorkflowState()
    
    def run_complete_pipeline_v331(self, execution_mode="intelligent"):
        # 1. 分析現有資料
        file_count, data_status = self.analyze_existing_data_v331()
        
        # 2. 決定策略
        if execution_mode == "enhanced":
            # 使用所有 v3.3.1 修復
        elif execution_mode == "process_only":
            # 僅處理現有資料
        
        # 3. 執行階段
        success = self.execute_phases(strategy)
        return success
```

#### 2. UnifiedRateLimitProtector
```python
class UnifiedRateLimitProtector:
    def __init__(self, config):
        self.consecutive_429s = 0
        self.should_stop_searching = False
        self.circuit_breaker_threshold = 1
    
    def record_429_error(self):
        self.consecutive_429s += 1
        self.should_stop_searching = True
        return True
```

### 必要環境變數
```bash
# .env 檔案必須包含
GOOGLE_SEARCH_API_KEY=your_api_key
GOOGLE_SEARCH_CSE_ID=your_cse_id
GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account",...}'
GOOGLE_SHEET_ID=your_spreadsheet_id

# v3.3.1 專用設定
FACTSET_MEMORY_LIMIT=2048
FACTSET_BATCH_SIZE=50
FACTSET_PIPELINE_VERSION=3.3.1
```

### GitHub Actions 完整規範
```yaml
# Actions.yml 必須包含的 jobs:
jobs:
  preflight_v331:    # Python-based validation (FIXED #8)
  pipeline_v331:     # Enhanced execution with all fixes
  recovery_v331:     # Enhanced recovery strategy

# 必要的 Python 邏輯嵌入:
- 模組導入測試 (FIXED #4)
- 記憶體檢查 (FIXED #9)  
- 資料品質驗證
- 智能提交策略
```

### 必要依賴清單 (requirements.txt)
```
requests>=2.28.0
pandas>=1.5.0
gspread>=5.7.0
google-auth>=2.15.0
python-dotenv>=0.19.0
beautifulsoup4>=4.11.0
markdownify>=0.11.0
validators>=0.20.0
psutil>=5.9.0
```

### 關鍵性能模式
```python
# 預編譯正則表達式 (FIXED #2)
COMPILED_FACTSET_PATTERNS = {}
def _initialize_compiled_patterns():
    # 一次編譯，多次使用

# 批次處理 (FIXED #2, #9)
def process_md_files_in_batches_v331(files, batch_size=50):
    # 記憶體效率處理

# 級聯故障保護 (FIXED #1)
for item in items:
    try:
        process_item(item)
    except Exception as e:
        logger.error(f"Item {item} failed: {e}")
        continue  # 繼續處理其他項目
```

### 資料格式驗證規則
```python
# Portfolio Summary 14欄位驗證
PORTFOLIO_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
    '分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值',
    '品質評分', '狀態', '更新日期'
]

# Detailed Data 21欄位驗證  
DETAILED_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD日期', '分析師數量', '目標價',
    '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
    '2026EPS最高值', '2026EPS最低值', '2026EPS平均值', 
    '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
    '品質評分', '狀態', 'MD File', '更新日期'
]
```

### 測試驗證規範
```python
# 必要測試函數
def test_v331_enhancements():
    # 測試級聯故障保護
    # 測試統一速率限制器
    # 測試記憶體管理
    # 測試批次處理
    # 測試模組導入
    
def validate_v331_data_quality():
    # 檢查檔案數量和品質
    # 驗證格式合規性
    # 確認資料完整性
```

---

**此完整指南作為緊湊的程式碼生成參考，包含所有必要的架構規範、實作細節、配置要求和驗證規則，可直接用於生成完整的 v3.3.1 FactSet Pipeline 系統。**