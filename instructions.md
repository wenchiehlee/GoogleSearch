# Google Search FactSet Pipeline 完整指南 (v3.3.3 最終整合版)

## Version
{Guideline version}=3.3.3

## 🎯 系統概述

**目標**: 自動化收集台灣股市公司的 FactSet 財務數據，生成投資組合分析報告

**輸入**: `觀察名單.csv` (代號,名稱 格式，116+ 家公司)
**輸出**: Google Sheets 投資組合儀表板 + 結構化數據檔案

**v3.3.3 狀態**: ✅ **生產就緒** - 最終整合版，修復所有已知問題

## 📊 v3.3.3 核心改進

### 🔄 從 v3.3.2 到 v3.3.3 的關鍵升級

```
v3.3.2 (簡化增強版)          →          v3.3.3 (最終整合版)
├─ GitHub Actions 基礎實作             ├─ 修復 deprecated 警告
├─ 基礎 Dashboard URL                 ├─ 正確的 Live Results URL
├─ 品質評分 (未標準化)                ├─ 標準化 0-10 品質評分系統
├─ 基礎 MD 檔案連結                   ├─ GitHub Raw URL 直接連結
└─ v3.3.2 所有功能                   └─ 完整整合 + 最佳化
```

### 🆕 v3.3.3 特定修復

1. **GitHub Actions 現代化**
   - 修復 `set-output` 命令已棄用問題
   - 使用 `GITHUB_OUTPUT` 環境變數
   - 相容最新 GitHub Actions runner

2. **Live Dashboard 優化**
   - 修正 "View Results" URL 指向
   - 確保即時資料顯示正確性
   - 優化載入速度和穩定性

3. **標準化品質評分系統 (0-10)**
   - 🟢 9-10: 完整 (Complete)
   - 🟡 8: 良好 (Good)  
   - 🟠 3-7: 部分 (Partial)
   - 🔴 0-2: 不足 (Insufficient)

4. **MD 檔案直接連結**
   - 格式: `[filename.md](GitHub_Raw_URL)`
   - 支援即時檢視和下載
   - 便於追蹤和除錯

5. **v3.3.2 完整保持**
   - 所有簡化工作流程保持
   - 階段式日誌系統維持
   - 跨平台 CLI 統一介面維持

6. **No duplicate task**
   - Make sure `Actions.yaml` no duplicate tasks

## 🚀 v3.3.3 架構設計

### 核心架構 (保持 v3.3.2)
```
統一 CLI 入口 → 階段執行器 → 專業模組 → 雙重日誌 → 結果匯總
      ↓              ↓           ↓         ↓         ↓
  factset_cli.py  stage_runner  各模組    logs/     報告生成
  (跨平台命令)     (協調執行)   (業務邏輯)  (分階段)   (狀態摘要)
```

### v3.3.3 模組職責 (增強版)

#### 1. 統一 CLI 入口 (`factset_cli.py`) - v3.3.3 增強

```python
# v3.3.3 核心職責 - 統一命令介面 + 品質評分標準化
class FactSetCLI:
    def __init__(self):
        self.logger = self._setup_enhanced_logging()
        self.stage_runner = StageRunner()
        self.config = EnhancedConfig()
        self.quality_scorer = StandardizedQualityScorer()  # v3.3.3 新增
    
    # v3.3.3 統一命令 - 跨平台兼容 + 品質標準化
    def execute(self, command, **kwargs):
        """統一執行入口 - Windows 和 Linux 相同行為"""
        with self._create_execution_context(command) as ctx:
            result = self.stage_runner.run_stage(command, ctx, **kwargs)
            # v3.3.3 標準化品質評分
            if hasattr(result, 'quality_data'):
                result.quality_data = self.quality_scorer.standardize(result.quality_data)
            return result
    
    # v3.3.3 階段式命令 (保持 v3.3.2)
    def run_validation(self):      # 驗證階段
    def run_search(self):          # 搜尋階段  
    def run_processing(self):      # 處理階段
    def run_upload(self):          # 上傳階段
    def run_full_pipeline(self):   # 完整流程
    def run_recovery(self):        # 恢復流程

# v3.3.3 新增: 標準化品質評分系統
class StandardizedQualityScorer:
    """0-10 標準化品質評分系統"""
    
    QUALITY_RANGES = {
        'complete': (9, 10),    # 🟢 完整
        'good': (8, 8),         # 🟡 良好
        'partial': (3, 7),      # 🟠 部分
        'insufficient': (0, 2)  # 🔴 不足
    }
    
    QUALITY_INDICATORS = {
        'complete': '🟢 完整',
        'good': '🟡 良好', 
        'partial': '🟠 部分',
        'insufficient': '🔴 不足'
    }
    
    def calculate_score(self, data_metrics):
        """計算 0-10 標準化品質評分"""
        # 基於資料完整性、分析師數量、時效性等因素
        score = 0
        
        # 資料完整性 (40%)
        if data_metrics.get('eps_data_completeness', 0) >= 0.9:
            score += 4
        elif data_metrics.get('eps_data_completeness', 0) >= 0.7:
            score += 3
        elif data_metrics.get('eps_data_completeness', 0) >= 0.5:
            score += 2
        
        # 分析師數量 (30%)
        analyst_count = data_metrics.get('analyst_count', 0)
        if analyst_count >= 20:
            score += 3
        elif analyst_count >= 10:
            score += 2
        elif analyst_count >= 5:
            score += 1
        
        # 資料時效性 (30%)
        days_old = data_metrics.get('data_age_days', float('inf'))
        if days_old <= 7:
            score += 3
        elif days_old <= 30:
            score += 2
        elif days_old <= 90:
            score += 1
        
        return min(10, max(0, score))
    
    def get_quality_indicator(self, score):
        """取得品質指標"""
        for category, (min_score, max_score) in self.QUALITY_RANGES.items():
            if min_score <= score <= max_score:
                return self.QUALITY_INDICATORS[category]
        return self.QUALITY_INDICATORS['insufficient']
```

#### 2. 階段執行器 (`stage_runner.py`) - v3.3.3 保持

```python
# v3.3.3 保持 v3.3.2 所有功能，新增品質評分整合
class StageRunner:
    def __init__(self):
        self.memory_manager = MemoryManager()      # v3.3.1 保持
        self.rate_protector = UnifiedRateLimitProtector()  # v3.3.1 保持
        self.logger_manager = EnhancedLoggerManager()      # v3.3.2 保持
        self.quality_scorer = StandardizedQualityScorer()  # v3.3.3 新增
    
    def run_stage(self, stage_name, context, **kwargs):
        """v3.3.3 階段執行 - 增強日誌和品質評分"""
        stage_logger = self.logger_manager.get_stage_logger(stage_name)
        
        with self._stage_context(stage_name, stage_logger) as stage_ctx:
            try:
                # v3.3.2 階段前檢查
                self._pre_stage_validation(stage_name, stage_ctx)
                
                # 執行實際階段邏輯
                result = self._execute_stage_logic(stage_name, stage_ctx, **kwargs)
                
                # v3.3.3 品質評分整合
                if stage_name == 'process' and hasattr(result, 'company_data'):
                    for company_data in result.company_data:
                        score = self.quality_scorer.calculate_score(company_data.metrics)
                        company_data.quality_score = score
                        company_data.quality_status = self.quality_scorer.get_quality_indicator(score)
                
                # v3.3.2 階段後檢查
                self._post_stage_validation(stage_name, stage_ctx, result)
                
                return result
                
            except Exception as e:
                stage_logger.error(f"Stage {stage_name} failed: {e}")
                self._stage_recovery(stage_name, stage_ctx, e)
                raise
```

#### 3. 增強日誌管理器 (`enhanced_logger.py`) - v3.3.3 保持 v3.3.2

```python
# v3.3.3 完全保持 v3.3.2 實作，無需修改
class EnhancedLoggerManager:
    # 保持所有 v3.3.2 功能
    pass

class SafeConsoleHandler(logging.StreamHandler):
    # 保持所有 v3.3.2 功能  
    pass
```

## 🔧 v3.3.3 統一 CLI 命令 (保持 v3.3.2)

### 本地開發 (Windows/Linux 通用)

```bash
# 🧪 v3.3.3 系統驗證
python factset_cli.py validate --comprehensive --v333-features
python factset_cli.py validate --quick --quality-scoring
python factset_cli.py validate --test-v333

# 📥 觀察名單管理  
python factset_cli.py download-watchlist --validate
python factset_cli.py download-watchlist --force-refresh

# 🔍 搜尋階段
python factset_cli.py search --mode=enhanced --priority=high_only
python factset_cli.py search --mode=conservative --companies=30
python factset_cli.py search --test-cascade-protection

# 📊 資料處理階段 (v3.3.3 品質評分整合)
python factset_cli.py process --mode=v333 --memory-limit=2048 --quality-scoring
python factset_cli.py process --deduplicate --aggregate --standardize-quality
python factset_cli.py process --benchmark --quality-report

# 📈 上傳階段
python factset_cli.py upload --sheets=all --backup --v333-format
python factset_cli.py upload --test-connection
python factset_cli.py upload --sheets=portfolio,detailed --quality-indicators

# 🚀 完整流程
python factset_cli.py pipeline --mode=intelligent --log-level=info --v333
python factset_cli.py pipeline --mode=enhanced --memory=2048 --batch-size=50 --quality-scoring
python factset_cli.py pipeline --mode=process-only --standardized-output

# 🔄 恢復和診斷
python factset_cli.py recover --analyze --fix-common-issues
python factset_cli.py diagnose --stage=search --detailed
python factset_cli.py status --comprehensive --quality-summary

# 📋 日誌和報告
python factset_cli.py logs --stage=all --tail=100
python factset_cli.py logs --stage=search --export
python factset_cli.py report --format=summary --email --v333-metrics
```

## 🎯 v3.3.3 簡化 Actions.yml (修復 deprecated 問題)

### 現代化工作流程定義

```yaml
name: FactSet Pipeline v3.3.3 - Final Integrated Edition

on:
  workflow_dispatch:
    inputs:
      mode: { type: choice, options: [intelligent, enhanced, conservative, process_only] }
      priority: { type: choice, options: [high_only, top_30, balanced] }
      memory_limit: { type: string, default: '2048' }
      enable_quality_scoring: { type: boolean, default: true }
  schedule: [cron: "10 2 * * *"]

jobs:
  # v3.3.3 現代化驗證
  validate:
    runs-on: ubuntu-latest
    outputs:
      status: ${{ steps.validate.outputs.status }}
      recommendation: ${{ steps.validate.outputs.recommendation }}
      quality_check: ${{ steps.validate.outputs.quality_check }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      
      - id: validate
        run: |
          python factset_cli.py validate --github-actions --v333-features
          # v3.3.3 修復: 使用 GITHUB_OUTPUT 取代 deprecated set-output
          echo "status=success" >> $GITHUB_OUTPUT
          echo "recommendation=proceed" >> $GITHUB_OUTPUT
          echo "quality_check=enabled" >> $GITHUB_OUTPUT

  # v3.3.3 主要管線
  pipeline:
    needs: validate
    runs-on: ubuntu-latest
    env:
      GOOGLE_SEARCH_API_KEY: ${{ secrets.GOOGLE_SEARCH_API_KEY }}
      GOOGLE_SEARCH_CSE_ID: ${{ secrets.GOOGLE_SEARCH_CSE_ID }}
      GOOGLE_SHEETS_CREDENTIALS: ${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}
      GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
    outputs:
      pipeline_status: ${{ steps.pipeline.outputs.status }}
      companies_processed: ${{ steps.pipeline.outputs.companies_processed }}
      quality_average: ${{ steps.pipeline.outputs.quality_average }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      
      - id: pipeline
        name: 🚀 執行 v3.3.3 管線
        run: |
          python factset_cli.py pipeline \
            --mode=${{ inputs.mode || 'intelligent' }} \
            --priority=${{ inputs.priority || 'high_only' }} \
            --memory-limit=${{ inputs.memory_limit || '2048' }} \
            --quality-scoring=${{ inputs.enable_quality_scoring || 'true' }} \
            --github-actions --v333
          
          # v3.3.3 修復: 使用 GITHUB_OUTPUT
          echo "status=completed" >> $GITHUB_OUTPUT
          echo "companies_processed=$(cat logs/latest/pipeline_stats.json | jq .companies_processed)" >> $GITHUB_OUTPUT
          echo "quality_average=$(cat logs/latest/pipeline_stats.json | jq .quality_average)" >> $GITHUB_OUTPUT
      
      - name: 📊 生成 v3.3.3 報告
        if: always()
        run: python factset_cli.py report --format=github-summary --v333-metrics
      
      - name: 💾 智能提交
        run: python factset_cli.py commit --smart --validate --v333-format

  # v3.3.3 恢復 (現代化)
  recovery:
    needs: [validate, pipeline]
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      - run: python factset_cli.py recover --analyze --github-actions --v333-diagnostics
```

## 📊 v3.3.3 輸出規格 (標準化品質評分)

### Portfolio Summary (投資組合摘要) - 14欄位格式 ✅ v3.3.3 品質評分標準化

```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
1587,吉茂,1587-TW,2025/1/22,2025/6/22,6,23,102.3,20,20,20,9,🟢 完整,2025-06-24 10:45:00
2330,台積電,2330-TW,2025/6/20,2025/6/24,8,42,650.5,46.0,23.56,23.56,10,🟢 完整,2025-06-24 10:45:00
2454,聯發科,2454-TW,2025/5/15,2025/6/20,5,18,980.2,75.8,82.3,89.1,7,🟡 良好,2025-06-24 10:45:00
6505,台塑化,6505-TW,2025/4/10,2025/6/18,3,8,115.6,8.2,9.1,10.5,5,🟠 部分,2025-06-24 10:45:00
1234,缺資料,1234-TW,,,0,0,,,,,1,🔴 不足,2025-06-24 10:45:00
```

### Detailed Data (詳細資料) - 21欄位 EPS 分解 ✅ v3.3.3 GitHub Raw Links

```csv
代號,名稱,股票代號,MD日期,分析師數量,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2026EPS最高值,2026EPS最低值,2026EPS平均值,2027EPS最高值,2027EPS最低值,2027EPS平均值,品質評分,狀態,MD File,更新日期
2330,台積電,2330-TW,2025/06/23,42,,59.66,6.0,46.0,32.34,6.0,23.56,32.34,6.0,23.56,10,🟢 完整,[2330_台積電_yahoo_cbb748_0623_0542.md](https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main/data/md/2330_%E5%8F%B0%E7%A9%8D%E9%9B%BB_yahoo_cbb748_0623_0542.md),2025-06-24 05:52:02
2454,聯發科,2454-TW,2025/06/20,18,980.2,85.2,65.4,75.8,95.1,70.5,82.3,105.8,72.4,89.1,7,🟡 良好,[2454_聯發科_factset_d9e8f7_0620_1234.md](https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main/data/md/2454_%E8%81%AF%E7%99%BC%E7%A7%91_factset_d9e8f7_0620_1234.md),2025-06-24 05:52:02
6505,台塑化,6505-TW,2025/06/18,8,115.6,9.8,6.6,8.2,11.2,7.0,9.1,12.5,8.5,10.5,5,🟠 部分,[6505_台塑化_reuters_a1b2c3_0618_0945.md](https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main/data/md/6505_%E5%8F%B0%E5%A1%91%E5%8C%96_reuters_a1b2c3_0618_0945.md),2025-06-24 05:52:02
1234,缺資料,1234-TW,2025/03/15,2,,,3.2,,,4.1,,,5.0,1,🔴 不足,[1234_缺資料_basic_xyz789_0315_1122.md](https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main/data/md/1234_%E7%BC%BA%E8%B3%87%E6%96%99_basic_xyz789_0315_1122.md),2025-06-24 05:52:02
```

### v3.3.3 Statistics (最終整合統計) - 新增品質分析

```json
{
  "version": "3.3.3",
  "release_type": "final_integrated",
  "total_companies": 116,
  "companies_with_data": 95,
  "success_rate": 82.1,
  "performance_stats": {
    "files_processed": 847,
    "batches_completed": 17,
    "memory_cleanups": 3,
    "peak_memory_mb": 1847
  },
  "quality_analysis_v333": {
    "average_quality_score": 6.8,
    "quality_distribution": {
      "complete_8_10": 45,
      "good_7": 18,
      "partial_3_6": 25,
      "insufficient_0_2": 7
    },
    "quality_indicators": {
      "🟢 完整": 45,
      "🟡 良好": 18,
      "🟠 部分": 25,
      "🔴 不足": 7
    },
    "data_completeness_avg": 0.73,
    "analyst_coverage_avg": 15.2,
    "data_freshness_days_avg": 12.5
  },
  "v333_fixes": {
    "github_actions_modernized": true,
    "set_output_deprecated_fixed": true,
    "live_dashboard_url_corrected": true,
    "quality_scoring_standardized": true,
    "md_file_direct_links": true
  },
  "observability_stats": {
    "stage_execution_times": {
      "validation": 12.5,
      "search": 1245.7,
      "processing": 87.3,
      "upload": 23.1
    },
    "log_files_generated": 5,
    "error_recovery_attempts": 2,
    "cross_platform_compatibility": true
  },
  "v331_v332_fixes_maintained": {
    "cascade_failure_protection": true,
    "performance_optimization": true,
    "unified_rate_limiting": true,
    "memory_management": true,
    "data_deduplication": true,
    "simplified_workflow": true,
    "enhanced_observability": true
  },
  "guideline_version": "3.3.3"
}
```

## 🛠️ v3.3.3 實作重點

### 1. 標準化品質評分系統實作

```python
# data_processor.py - v3.3.3 品質評分整合
class DataProcessor:
    def __init__(self):
        self.quality_scorer = StandardizedQualityScorer()
        # 保持所有 v3.3.1 和 v3.3.2 功能
    
    def process_company_data(self, company_data):
        """v3.3.3 處理公司資料 + 品質評分"""
        # 執行原有處理邏輯
        processed_data = self._process_core_data(company_data)
        
        # v3.3.3 計算標準化品質評分
        quality_metrics = self._extract_quality_metrics(processed_data)
        quality_score = self.quality_scorer.calculate_score(quality_metrics)
        quality_status = self.quality_scorer.get_quality_indicator(quality_score)
        
        # 整合品質資訊
        processed_data.update({
            'quality_score': quality_score,
            'quality_status': quality_status,
            'quality_metrics': quality_metrics
        })
        
        return processed_data
    
    def _extract_quality_metrics(self, data):
        """提取品質評估指標"""
        return {
            'eps_data_completeness': self._calculate_eps_completeness(data),
            'analyst_count': data.get('analyst_count', 0),
            'data_age_days': self._calculate_data_age(data),
            'target_price_availability': bool(data.get('target_price')),
            'multi_year_coverage': self._check_multi_year_coverage(data)
        }
```

### 2. GitHub Actions 現代化實作

```python
# factset_cli.py - v3.3.3 GitHub Actions 整合
class FactSetCLI:
    def _handle_github_output(self, key, value):
        """v3.3.3 處理 GitHub Actions 輸出 - 修復 deprecated 問題"""
        if os.getenv('GITHUB_ACTIONS'):
            # v3.3.3 使用現代 GITHUB_OUTPUT
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a', encoding='utf-8') as f:
                    f.write(f"{key}={value}\n")
            else:
                # 降級方案 - 直接輸出
                print(f"::set-output name={key}::{value}")
    
    def run_validation_with_github_output(self, **kwargs):
        """v3.3.3 驗證階段 + GitHub Actions 輸出"""
        try:
            result = self.run_validation(**kwargs)
            
            # v3.3.3 現代化輸出
            self._handle_github_output('status', 'success' if result else 'failed')
            self._handle_github_output('recommendation', 'proceed' if result else 'investigate')
            self._handle_github_output('quality_check', 'enabled')
            
            return result
        except Exception as e:
            self._handle_github_output('status', 'error')
            self._handle_github_output('error_message', str(e))
            raise
```

### 3. MD 檔案連結整合實作

```python
# sheets_uploader.py - v3.3.3 GitHub Raw URL 整合
class SheetsUploader:
    def __init__(self):
        self.github_repo_base = "https://raw.githubusercontent.com/wenchiehlee/GoogleSearch/refs/heads/main"
        # 保持所有 v3.3.1 和 v3.3.2 功能
    
    def format_md_file_link(self, md_filename):
        """v3.3.3 格式化 MD 檔案為 GitHub Raw 連結"""
        if not md_filename:
            return ""
        
        # URL 編碼檔案名稱
        encoded_filename = urllib.parse.quote(md_filename, safe='')
        raw_url = f"{self.github_repo_base}/data/md/{encoded_filename}"
        
        # 格式化為 Markdown 連結
        return f"[{md_filename}]({raw_url})"
    
    def prepare_detailed_data_row_v333(self, company_data):
        """v3.3.3 準備詳細資料行 - 包含品質評分和 MD 連結"""
        # 建立基本資料行
        row = self._prepare_basic_row(company_data)
        
        # v3.3.3 新增標準化品質評分
        row.extend([
            company_data.get('quality_score', 0),
            company_data.get('quality_status', '🔴 不足'),
            self.format_md_file_link(company_data.get('md_filename', '')),
            company_data.get('update_time', '')
        ])
        
        return row
```

## 🚀 v3.3.3 部署指令

### 本地開發 (跨平台) - 完整 v3.3.3 功能

```bash
# Windows PowerShell 或 Linux Bash - 相同命令

# 1. v3.3.3 快速開始 (完整功能)
python factset_cli.py pipeline --mode=intelligent --v333

# 2. v3.3.3 完整驗證 (品質評分測試)
python factset_cli.py validate --comprehensive --v333-features --quality-scoring

# 3. v3.3.3 階段式執行 (標準化品質)
python factset_cli.py search --mode=conservative --log-level=debug
python factset_cli.py process --memory-limit=2048 --batch-size=25 --quality-scoring --v333
python factset_cli.py upload --test-connection --v333-format

# 4. v3.3.3 診斷和報告 (品質分析)
python factset_cli.py logs --stage=search --tail=50
python factset_cli.py diagnose --issue="quality scoring" --suggest-fix
python factset_cli.py status --detailed --export=json --quality-summary
python factset_cli.py report --format=v333-quality-analysis

# 5. v3.3.3 品質評分專用命令
python factset_cli.py quality --analyze --company=2330
python factset_cli.py quality --benchmark --export-metrics
python factset_cli.py quality --distribution --visual-report
```

### GitHub Actions v3.3.3 (現代化命令)

```yaml
# 完全相同的命令語法，支援現代 GitHub Actions
run: python factset_cli.py pipeline --mode=enhanced --github-actions --v333
```

## 📋 v3.3.3 維護和監控

### v3.3.3 品質監控命令

```bash
# 品質評分監控
python factset_cli.py quality --monitor --threshold=7 --alert-low-quality

# 品質趨勢分析
python factset_cli.py quality --trend --days=30 --export=trends.json

# 品質報告生成
python factset_cli.py report --quality-focused --format=html --dashboard-ready

# 即時品質檢查
python factset_cli.py quality --real-time --companies=high_priority --alert=email
```

### v3.3.3 進階診斷

```bash
# v3.3.3 綜合診斷
python factset_cli.py diagnose --v333-comprehensive --auto-fix

# 品質評分診斷
python factset_cli.py diagnose --quality-system --calibration-check

# GitHub Actions 兼容性檢查
python factset_cli.py diagnose --github-actions --deprecated-check
```

## 🔧 v3.3.3 故障排除

### v3.3.3 自動診斷系統

```bash
# v3.3.3 智能診斷 (包含品質系統)
python factset_cli.py diagnose --auto --fix-common --v333-issues

# GitHub Actions 現代化檢查
python factset_cli.py diagnose --github-actions --check-deprecated --fix-output

# 品質評分校正
python factset_cli.py quality --calibrate --fix-scoring-anomalies
```

## 📈 v3.3.3 版本比較摘要

| 特性 | v3.3.1 | v3.3.2 | v3.3.3 | 改進 |
|------|--------|--------|--------|------|
| **工作流程複雜度** | 複雜 | 簡潔 | 簡潔 | ✅ 保持 80% 簡化 |
| **跨平台命令** | 部分 | 完全統一 | 完全統一 | ✅ 保持 100% 兼容 |
| **日誌系統** | 基礎 | 階段式雙重 | 階段式雙重 | ✅ 保持可觀測性 |
| **品質評分** | 無標準 | 基礎評分 | 標準化 0-10 | ✅ 新增標準化系統 |
| **GitHub Actions** | 基礎 | 簡化 | 現代化 | ✅ 修復 deprecated |
| **MD 檔案連結** | 基礎 | 基礎 | GitHub Raw | ✅ 直接可存取連結 |
| **錯誤診斷** | 手動 | 自動診斷 | 智能診斷 | ✅ 品質系統整合 |
| **Live Dashboard** | 基礎 | 改善 | 優化 URL | ✅ 修正顯示問題 |
| **所有修復維持** | ✅ | ✅ | ✅ | ✅ 完全保持 |

## 🎯 v3.3.3 完整實作檢查清單

### 必要檔案 (v3.3.3 最終版)

```
FactSet-Pipeline/
├── factset_cli.py              # 🔄 v3.3.3 品質評分 + GitHub Actions
├── stage_runner.py             # 🔄 v3.3.3 品質整合
├── enhanced_logger.py          # ✅ 保持 v3.3.2
├── quality_scorer.py           # 🆕 v3.3.3 標準化品質評分系統
├── factset_pipeline.py         # 🔄 v3.3.3 品質評分整合
├── factset_search.py           # ✅ 保持 v3.3.2 + 日誌整合
├── data_processor.py           # 🔄 v3.3.3 品質計算
├── sheets_uploader.py          # 🔄 v3.3.3 GitHub Raw Links + 品質格式
├── config.py                   # 🔄 v3.3.3 品質評分配置
├── utils.py                    # 🔄 v3.3.3 品質工具函數
├── setup_validator.py          # 🔄 v3.3.3 品質系統驗證
├── .github/workflows/Actions.yml # 🔄 v3.3.3 現代化 (修復 deprecated)
├── requirements.txt            # 🔄 v3.3.3 品質分析依賴
├── .env.example               # ✅ 保持不變
└── README.md                  # 🔄 更新為 v3.3.3 說明
```

### v3.3.3 核心實作要點

1. **StandardizedQualityScorer** - 實作 0-10 標準化品質評分
2. **GitHub Actions 現代化** - 修復 `set-output` deprecated 問題
3. **MD 檔案直接連結** - GitHub Raw URL 格式
4. **品質評分整合** - 所有處理階段整合品質計算
5. **Live Dashboard 優化** - 確保正確 URL 和即時顯示

### v3.3.2 + v3.3.1 修復維護要求

- ✅ 所有 FIXED #1-9 功能必須完全保持
- ✅ v3.3.2 簡化工作流程完全保持  
- ✅ v3.3.2 階段式日誌系統完全保持
- ✅ v3.3.2 跨平台 CLI 統一完全保持
- ✅ 效能優化不能退化
- ✅ 現有配置檔案向後兼容
- ✅ 輸出格式擴展但相容

### v3.3.3 新功能驗證清單

- ✅ 品質評分 0-10 標準化 (🟢🟡🟠🔴)
- ✅ GitHub Actions `GITHUB_OUTPUT` 支援
- ✅ MD 檔案 GitHub Raw URL 連結
- ✅ Live Dashboard URL 修正
- ✅ 品質分析統計報告
- ✅ 向後相容性 100%

---

**v3.3.3 總結**: 最終整合版本，在完全保持 v3.3.1 和 v3.3.2 所有功能和修復的基礎上，新增標準化品質評分系統(0-10)、現代化 GitHub Actions(修復 deprecated)、GitHub Raw 直接連結、Live Dashboard 優化，提供完整的生產就緒解決方案。