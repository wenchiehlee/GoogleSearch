# Google Search FactSet Pipeline 指南

## Version
{Guideline version}=3.3.0

# Google Search FactSet Pipeline 完整指南

## 🎯 系統概述

**目標**: 自動化收集台灣股市公司的 FactSet 財務數據，生成投資組合分析報告

**輸入**: `觀察名單.csv` (代號,名稱 格式，116+ 家公司)
**輸出**: Google Sheets 投資組合儀表板 + 結構化數據檔案

## 📊 核心架構

```
GitHub Actions → 目標公司載入 → 搜尋引擎 → 資料處理 → Google Sheets
      ↓              ↓           ↓         ↓           ↓
   定時執行     觀察名單.csv   factset搜尋   MD→CSV    投資組合報告
```

## 🏗️ 模組設計規範

### 1. 主控制器 (`factset_pipeline.py`)

版本={Guideline version}
```python
# 核心職責
class ProductionFactSetPipeline:
    def __init__(self):
        self.config = ProductionConfig()
        self.rate_protector = RateLimitProtector()
        self.state = WorkflowState()
    
    # 必要方法
    def run_complete_pipeline(self, strategy="intelligent"):
        # 1. 分析現有資料
        # 2. 決定執行策略
        # 3. 執行搜尋階段 (with 429 protection)
        # 4. 執行資料處理
        # 5. 上傳到 Google Sheets
    
    def analyze_existing_data(self):
        # 分析現有 MD 檔案品質和數量
        return file_count, quality_status
    
    def determine_strategy(self, existing_data):
        # conservative: 限制搜尋
        # process_existing: 只處理現有資料  
        # comprehensive: 完整搜尋
        return strategy
```

**關鍵特性**:
- ✅ 立即偵測 429 錯誤並停止搜尋
- ✅ 回退到現有資料處理
- ✅ 狀態管理和恢復機制
- ✅ 多種執行策略

### 2. 搜尋引擎 (`factset_search.py`)

版本={Guideline version}

```python
# 核心職責
def search_company_factset_data(company_name, stock_code, search_type="factset"):
    # 搜尋策略
    patterns = {
        'factset': ['{company} factset EPS 預估', '{company} 目標價'],
        'financial': ['{company} 財報 分析師 預估'],
        'missing': ['{company} 股價 分析']
    }
    
    # 429 保護機制
    try:
        results = google_search(query)
        if "429" in response or "rate limit" in response:
            raise RateLimitException("停止所有搜尋")
    except RateLimitException:
        return []  # 立即停止
    
    # URL 清理和驗證
    for url in results:
        clean_url = clean_and_validate_url(url)
        content = download_webpage_content(clean_url)
        save_as_markdown(content, unique_filename)

# 必要功能
def clean_and_validate_url(url):
    # 處理 Google redirect URLs
    # 驗證 URL 格式
    # 回傳清理後的 URL

def generate_unique_filename(company, stock_code, url, index):
    # 格式: {company}_{stock}_{domain}_{hash}.md
    # hash is based on file content. 避免檔案覆蓋

def immediate_stop_on_429():
    # 偵測到 429 後立即停止所有搜尋
    # 回傳現有收集的資料
```

**關鍵特性**:
- 🚨 **立即停止策略**: 偵測到 429 後立即停止
- 🔄 **URL 清理**: 處理 Google redirect 和惡意 URL
- 💾 **防覆蓋**: 唯一檔名生成
- 📊 **多搜尋策略**: factset, financial, missing

### 3. 資料處理器 (`data_processor.py`)

版本={Guideline version}

```python
# 核心職責
def process_all_data(parse_md=True):
    # 1. 整合 CSV 檔案
    consolidated_df = consolidate_csv_files()
    
    # 2. 解析 MD 檔案財務數據
    if parse_md:
        md_data = parse_markdown_files()
        consolidated_df = apply_md_data_to_csv(consolidated_df, md_data)
    
    # 3. 修復公司名稱對應
    consolidated_df = fix_company_mapping(consolidated_df)
    
    # 4. 生成投資組合摘要
    summary_df = generate_portfolio_summary(consolidated_df)
    
    # 5. 產生統計報告
    stats = generate_statistics(consolidated_df, summary_df)

# 財務數據提取模式
FACTSET_PATTERNS = {
    'eps_current': [r'EPS[：:\s]*([0-9]+\.?[0-9]*)'],
    'target_price': [r'目標價[：:\s]*([0-9]+\.?[0-9]*)'],
    'analyst_count': [r'分析師[：:\s]*([0-9]+)']
}

def extract_company_info_from_title(title, watchlist_df):
    # 從搜尋結果標題提取公司資訊
    # 使用觀察名單進行對應
    return company_name, stock_code
```

**關鍵特性**:
- 📄 **MD 檔案解析**: 提取 EPS、目標價、分析師數量
- 🏢 **公司名稱修復**: 使用觀察名單進行對應
- 📊 **資料品質驗證**: 檢查完整性和準確性
- 📈 **統計生成**: 成功率、覆蓋率分析

### 4. 配置管理 (`config.py`)

```python
# 觀察名單載入
def download_target_companies():
    """從 GitHub 載入觀察名單.csv"""
    url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/觀察名單.csv"
    response = requests.get(url)
    
    # 解析 CSV: 代號,名稱
    companies = []
    for row in csv.reader(io.StringIO(response.text)):
        code, name = row[0].strip(), row[1].strip()
        if code.isdigit() and len(code) == 4:
            companies.append({"code": code, "name": name})
    
    return companies

# 配置結構
DEFAULT_CONFIG = {
    "target_companies": download_target_companies(),
    "search": {
        "max_results": 10,
        "rate_limit_delay": 45,
        "circuit_breaker_threshold": 1  # 立即停止
    },
    "output": {
        "csv_dir": "data/csv",
        "md_dir": "data/md", 
        "processed_dir": "data/processed"
    }
}
```

### 5. Google Sheets 整合 (`sheets_uploader.py`)

```python
def upload_all_sheets(config):
    # 1. 載入處理後的資料
    data = {
        'summary': pd.read_csv('data/processed/portfolio_summary.csv'),
        'consolidated': pd.read_csv('data/processed/consolidated_factset.csv'),
        'statistics': json.load('data/processed/statistics.json')
    }
    
    # 2. 更新三個工作表
    update_portfolio_summary_sheet(client, data)      # 投資組合摘要
    update_detailed_data_sheet(client, data)          # 詳細資料
    update_statistics_sheet(client, data)             # 統計報告

# 驗證資料品質
def validate_data_quality(data):
    issues = []
    if len(data['summary']) == 0:
        issues.append("無投資組合資料")
    companies_with_eps = len(data['summary'][data['summary']['當前EPS預估'].notna()])
    if companies_with_eps == 0:
        issues.append("無 EPS 資料")
    return len(issues) == 0
```

## 🚨 速率限制保護機制

### 立即停止策略

```python
class RateLimitProtector:
    def __init__(self):
        self.should_stop_searching = False
        self.circuit_breaker_threshold = 1  # 第一次 429 就停止
    
    def record_429_error(self):
        self.should_stop_searching = True
        logger.error("🛑 偵測到速率限制 - 立即停止搜尋")
        logger.info("📄 將處理現有資料")
        return True
    
    def should_stop_immediately(self):
        return self.should_stop_searching
```

### 回退策略

```python
def fallback_to_existing_data():
    """當搜尋被限制時，處理現有資料"""
    existing_files = count_existing_md_files()
    if existing_files > 0:
        logger.info(f"📄 使用現有資料: {existing_files} 個檔案")
        return process_existing_data()
    else:
        logger.warning("⚠️ 無現有資料可處理")
        return False
```

## ⚙️ GitHub Actions 工作流程

### Actions.yml 結構

```yaml
name: FactSet Pipeline - Rate Limiting Aware

on:
  schedule:
    - cron: "10 2 * * *"  # 每日 2:10 AM (速率限制最可能重置時)
  workflow_dispatch:
    inputs:
      execution_mode:
        type: choice
        options: ['conservative', 'process_only', 'test_only', 'force_search']
      priority_focus:
        type: choice  
        options: ['high_only', 'top_30', 'balanced']

jobs:
  # 預檢階段
  preflight:
    runs-on: ubuntu-latest
    outputs:
      rate_limited: ${{ steps.check.outputs.rate_limited }}
      has_existing_data: ${{ steps.check.outputs.has_existing_data }}
    steps:
      - name: 測試搜尋 API
        run: |
          # 簡單測試查詢以檢查 429 狀態
          python test_search_api.py
  
  # 主要管線
  pipeline:
    needs: preflight
    steps:
      - name: 載入目標公司
        run: python config.py --download-csv
      
      - name: 處理現有資料 (如果速率限制)
        if: needs.preflight.outputs.rate_limited == 'true'
        run: python data_processor.py --force --parse-md
      
      - name: 保守搜尋 (如果安全)
        if: needs.preflight.outputs.rate_limited != 'true'
        run: |
          python factset_search.py --priority-focus high_only
          # 立即停止如果遇到 429
      
      - name: 最終資料處理
        run: python data_processor.py --force --parse-md
      
      - name: 驗證並提交結果
        run: |
          # 驗證資料品質
          valid_files=$(check_data_quality.py)
          if [ "$valid_files" -gt "5" ]; then
            git add data/
            git commit -m "📊 Pipeline: $valid_files files"
            git push
          fi
      
      - name: 上傳到 Google Sheets
        env:
          GOOGLE_SHEETS_CREDENTIALS: ${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
        run: python sheets_uploader.py
```

### 環境變數需求

```bash
# GitHub Secrets
GOOGLE_SEARCH_API_KEY=your_api_key
GOOGLE_SEARCH_CSE_ID=your_cse_id  
GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account",...}'
GOOGLE_SHEET_ID=your_spreadsheet_id
```

## 📁 檔案結構規範

```
FactSet-Pipeline/
├── factset_pipeline.py        # 主控制器
├── factset_search.py          # 搜尋引擎  
├── data_processor.py          # 資料處理器
├── sheets_uploader.py         # Google Sheets 整合
├── config.py                  # 配置管理
├── utils.py                   # 工具函數
├── setup_validator.py         # 安裝驗證
├── 觀察名單.csv                # 目標公司 (代號,名稱)
├── .github/workflows/Actions.yml  # GitHub Actions
├── requirements.txt           # Python 依賴
├── .env.example              # 環境變數範本
├── data/                     # 生成的資料
│   ├── csv/                  # 搜尋結果
│   ├── md/                   # 下載的內容  
│   ├── pdf/                  # PDF 檔案
│   └── processed/            # 處理後資料
│       ├── consolidated_factset.csv
│       ├── portfolio_summary.csv
│       └── statistics.json
└── logs/                     # 日誌檔案
```

## 🔄 資料流程

### 1. 輸入階段
```
觀察名單.csv → 載入 116+ 公司 → 選擇優先級策略
```

### 2. 搜尋階段  
```
目標公司 → Google 搜尋 → 429 檢查 → MD 檔案儲存
         ↓ (如果 429)
         立即停止 → 回退到現有資料
```

### 3. 處理階段
```
MD 檔案 → 財務數據提取 → 公司名稱對應 → CSV 整合
```

### 4. 輸出階段
```
處理後資料 → 投資組合摘要 → Google Sheets → 儀表板
```

## 📊 輸出規格

### Portfolio Summary (投資組合摘要)

```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
1587,吉茂,1587-TW,2025/1/22,2025/6/22,6,23,102.3,20,20,20,4,🟢 完整,2025-06-22 10:45:00
```

* Since there is several MD files with the same "代號" and "名稱"(like 吉茂_1587_xxxxxx.md) so that 
(1) "MD資料筆數" is the numbers of MD files and 
(2) "MD最舊日期" are the oldest date of the MD file
(3) "MD最新日期"  are the latest date of the MD file
(4) In "MD資料筆數", the md files are parsed and make sure whether it is the same data that from different news source. If the same data, then "分析師數量","目標價", "2025EPS最高值","2025EPS最低值","2025EPS平均值","2026EPS最高值","2026EPS最低值","2026EPS平均值","2027EPS最高值","2027EPS最低值","2027EPS平均值" will have the same value

### Detailed Data (詳細資料)
```csv
代號,名稱,股票代號,MD日期,分析師數量,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2026EPS最高值,2026EPS最低值,2026EPS平均值,2027EPS最高值,2027EPS最低值,2027EPS平均值,品質評分,狀態,MD File,更新日期
1587,吉茂,1587-TW,2025/1/22,2025/6/22,6,23,102.3,20,18,23,20,18,23,20,18,23,4,🟢 完整,data/md/吉茂_1587_xxxxx.md,2025-06-22 10:45:00
```
* Every row is only from one MD file (Filename can be found from "MD File"=data/md/吉茂_1587_xxxxx.md so 品質評分,狀態 is verified on the "MD File" only)


### Statistics (統計資料)
```json
{
  "total_companies": 116,
  "companies_with_data": 45,
  "success_rate": 38.8,
  "rate_limited": false,
  "last_updated": "2025-06-22T10:45:00"
}
```

## 🛠️ 實作重點

### 1. 速率限制處理
```python
# 在每個搜尋請求中
try:
    response = requests.get(search_url)
    if response.status_code == 429:
        raise RateLimitException("立即停止")
except RateLimitException:
    logger.error("🛑 速率限制 - 停止所有搜尋")
    return process_existing_data()
```

### 2. 資料品質驗證
```python
def validate_data_before_commit():
    md_files = count_valid_md_files()
    factset_files = count_factset_content_files()
    
    if md_files > 20 and factset_files > 5:
        return "high_quality"
    elif md_files > 10:
        return "acceptable"
    else:
        return "insufficient"
```

### 3. 錯誤處理模式
```python
def safe_operation_with_fallback():
    try:
        return primary_operation()
    except RateLimitException:
        logger.warning("速率限制 - 使用備用方案")
        return fallback_operation()
    except Exception as e:
        logger.error(f"一般錯誤: {e}")
        return default_result()
```

## 🧪 測試和驗證

### 單元測試
```python
def test_company_mapping():
    title = "台積電(2330) Q4財報預估"
    company, code = extract_company_info(title)
    assert company == "台積電"
    assert code == "2330"

def test_rate_limit_protection():
    protector = RateLimitProtector()
    protector.record_429_error()
    assert protector.should_stop_immediately() == True
```

### 整合測試
```bash
# 測試完整流程 (無搜尋)
python factset_pipeline.py --mode process_only

# 測試個別模組
python config.py --show
python data_processor.py --check-data
python sheets_uploader.py --test-connection
```

## 🚀 部署指令

### 本地開發
```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 配置環境變數
cp .env.example .env
# 編輯 .env 檔案

# 3. 下載目標公司
python config.py --download-csv

# 4. 驗證設定
python setup_validator.py

# 5. 執行管線
python factset_pipeline.py --mode conservative
```

### GitHub Actions 部署
```bash
# 1. 設定 GitHub Secrets
# 2. 推送程式碼到 main 分支
# 3. 手動觸發或等待定時執行
```

## 📋 維護檢查清單

### 每日檢查
- [ ] 檢查 GitHub Actions 執行狀態
- [ ] 確認 Google Sheets 儀表板更新
- [ ] 監控速率限制警告

### 每週檢查  
- [ ] 檢查觀察名單.csv 是否更新
- [ ] 驗證資料品質統計
- [ ] 清理舊的備份檔案

### 每月檢查
- [ ] 更新 Python 依賴
- [ ] 檢查 Google API 配額使用量
- [ ] 分析投資組合覆蓋率

## 🔧 故障排除

### 常見問題
1. **429 速率限制**: 等待 4-12 小時，使用保守模式
2. **無搜尋結果**: 檢查 API 金鑰和 CSE ID
3. **Google Sheets 錯誤**: 驗證服務帳戶權限
4. **資料品質差**: 調整搜尋模式，增加延遲

### 恢復策略
```bash
# 如果搜尋完全失敗
python data_processor.py --force --parse-md
python sheets_uploader.py

# 如果部分失敗  
python factset_pipeline.py --recover

# 重置狀態
python factset_pipeline.py --reset
```

---

**這個指南提供了重建整個 FactSet Pipeline 所需的完整架構、實作細節和最佳實務。按照此指南可以生成具備速率限制保護、資料品質驗證和智能回退機制的完整系統。**