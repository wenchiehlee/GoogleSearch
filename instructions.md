# Google Search FactSet Pipeline 完整指南 (v3.3.2 簡化與可觀測性增強版)

## Version
{Guideline version}=3.3.2

## 🎯 系統概述

**目標**: 自動化收集台灣股市公司的 FactSet 財務數據，生成投資組合分析報告

**輸入**: `觀察名單.csv` (代號,名稱 格式，116+ 家公司)
**輸出**: Google Sheets 投資組合儀表板 + 結構化數據檔案

**v3.3.2 狀態**: ✅ **生產就緒** - 簡化工作流程 + 增強可觀測性

## 📊 v3.3.2 核心改進

### 🔄 從 v3.3.1 到 v3.3.2 的關鍵升級

```
v3.3.1 (綜合修復版)          →          v3.3.2 (簡化增強版)
├─ 複雜的 Actions.yml                  ├─ 簡潔的 Actions.yml  
├─ 內嵌 Python 邏輯                   ├─ 模組化 Python 呼叫
├─ 基礎日誌記錄                       ├─ 階段式雙重日誌系統
├─ 平台特定命令                       ├─ 統一跨平台 CLI
└─ 手動錯誤追蹤                       └─ 自動化問題診斷
```

### 🏗️ v3.3.2 設計原則

1. **簡化優先** (Simplicity First)
   - Actions.yml 只負責協調，不包含業務邏輯
   - 所有複雜邏輯移至 Python 模組
   - 清晰的階段劃分和命令結構

2. **統一 CLI 介面** (Unified CLI)
   - Windows 開發環境與 GitHub Actions 使用相同命令
   - 跨平台兼容的路徑和編碼處理
   - 一致的參數和行為

3. **增強可觀測性** (Enhanced Observability)
   - 每階段獨立日誌檔案
   - 雙重輸出：控制台 + 檔案
   - 自動問題診斷和建議

4. **保持 v3.3.1 修復** (Maintain v3.3.1 Fixes)
   - 所有 #1-9 修復保持不變
   - 效能和可靠性提升延續
   - 向後兼容現有配置

## 🚀 v3.3.2 架構設計

### 核心架構
```
統一 CLI 入口 → 階段執行器 → 專業模組 → 雙重日誌 → 結果匯總
      ↓              ↓           ↓         ↓         ↓
  factset_cli.py  stage_runner  各模組    logs/     報告生成
  (跨平台命令)     (協調執行)   (業務邏輯)  (分階段)   (狀態摘要)
```

### 模組職責重新定義

#### 1. 統一 CLI 入口 (`factset_cli.py`) - 🆕 v3.3.2

```python
# v3.3.2 核心職責 - 統一命令介面
class FactSetCLI:
    def __init__(self):
        self.logger = self._setup_enhanced_logging()
        self.stage_runner = StageRunner()
        self.config = EnhancedConfig()
    
    # v3.3.2 統一命令 - 跨平台兼容
    def execute(self, command, **kwargs):
        """統一執行入口 - Windows 和 Linux 相同行為"""
        with self._create_execution_context(command) as ctx:
            return self.stage_runner.run_stage(command, ctx, **kwargs)
    
    # v3.3.2 階段式命令
    def run_validation(self):      # 驗證階段
    def run_search(self):          # 搜尋階段  
    def run_processing(self):      # 處理階段
    def run_upload(self):          # 上傳階段
    def run_full_pipeline(self):   # 完整流程
    def run_recovery(self):        # 恢復流程
```

#### 2. 階段執行器 (`stage_runner.py`) - 🆕 v3.3.2

```python
# v3.3.2 核心職責 - 階段協調與日誌管理
class StageRunner:
    def __init__(self):
        self.memory_manager = MemoryManager()      # v3.3.1 保持
        self.rate_protector = UnifiedRateLimitProtector()  # v3.3.1 保持
        self.logger_manager = EnhancedLoggerManager()      # v3.3.2 新增
    
    def run_stage(self, stage_name, context, **kwargs):
        """v3.3.2 階段執行 - 增強日誌和錯誤處理"""
        stage_logger = self.logger_manager.get_stage_logger(stage_name)
        
        with self._stage_context(stage_name, stage_logger) as stage_ctx:
            try:
                # v3.3.2 階段前檢查
                self._pre_stage_validation(stage_name, stage_ctx)
                
                # 執行實際階段邏輯
                result = self._execute_stage_logic(stage_name, stage_ctx, **kwargs)
                
                # v3.3.2 階段後檢查
                self._post_stage_validation(stage_name, stage_ctx, result)
                
                return result
                
            except Exception as e:
                stage_logger.error(f"Stage {stage_name} failed: {e}")
                self._stage_recovery(stage_name, stage_ctx, e)
                raise
```

#### 3. 增強日誌管理器 (`enhanced_logger.py`) - 🆕 v3.3.2

```python
# v3.3.2 核心職責 - 階段式雙重日誌系統
class EnhancedLoggerManager:
    def __init__(self):
        self.log_dir = Path("logs") / datetime.now().strftime("%Y%m%d")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.stage_loggers = {}
    
    def get_stage_logger(self, stage_name):
        """v3.3.2 取得階段專屬日誌器"""
        if stage_name not in self.stage_loggers:
            self.stage_loggers[stage_name] = self._create_dual_logger(stage_name)
        return self.stage_loggers[stage_name]
    
    def _create_dual_logger(self, stage_name):
        """v3.3.2 建立雙重輸出日誌器"""
        logger = logging.getLogger(f'factset_v332.{stage_name}')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # 檔案輸出 - 階段專屬
        file_handler = logging.FileHandler(
            self.log_dir / f"{stage_name}_{datetime.now().strftime('%H%M%S')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(self._get_detailed_formatter())
        
        # 控制台輸出 - 簡潔格式
        console_handler = SafeConsoleHandler()
        console_handler.setFormatter(self._get_console_formatter())
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

# v3.3.2 跨平台安全控制台處理器
class SafeConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # v3.3.2 跨平台編碼處理
            if sys.platform == "win32":
                msg = msg.encode('utf-8', errors='replace').decode('utf-8')
            self.stream.write(msg + '\n')
            self.flush()
        except Exception:
            self.handleError(record)
```

### 4. 保持 v3.3.1 修復的核心模組

```python
# 以下模組保持 v3.3.1 的所有修復，僅增加 v3.3.2 日誌整合

# factset_pipeline.py - 保持 v3.3.1 + 新增階段式日誌
class EnhancedFactSetPipeline:
    # 保持所有 v3.3.1 修復
    # 新增: 與 StageRunner 整合的日誌系統

# factset_search.py - 保持 v3.3.1 + 新增搜尋階段日誌  
# data_processor.py - 保持 v3.3.1 + 新增處理階段日誌
# sheets_uploader.py - 保持 v3.3.1 + 新增上傳階段日誌
# config.py - 保持 v3.3.1 + 新增配置階段日誌
```

## 🔧 v3.3.2 統一 CLI 命令

### 本地開發 (Windows/Linux 通用)

```bash
# 🧪 v3.3.2 系統驗證
python factset_cli.py validate --comprehensive
python factset_cli.py validate --quick
python factset_cli.py validate --test-v332

# 📥 觀察名單管理  
python factset_cli.py download-watchlist --validate
python factset_cli.py download-watchlist --force-refresh

# 🔍 搜尋階段
python factset_cli.py search --mode=enhanced --priority=high_only
python factset_cli.py search --mode=conservative --companies=30
python factset_cli.py search --test-cascade-protection

# 📊 資料處理階段
python factset_cli.py process --mode=v332 --memory-limit=2048
python factset_cli.py process --deduplicate --aggregate
python factset_cli.py process --benchmark

# 📈 上傳階段
python factset_cli.py upload --sheets=all --backup
python factset_cli.py upload --test-connection
python factset_cli.py upload --sheets=portfolio,detailed

# 🚀 完整流程
python factset_cli.py pipeline --mode=intelligent --log-level=info
python factset_cli.py pipeline --mode=enhanced --memory=2048 --batch-size=50
python factset_cli.py pipeline --mode=process-only

# 🔄 恢復和診斷
python factset_cli.py recover --analyze --fix-common-issues
python factset_cli.py diagnose --stage=search --detailed
python factset_cli.py status --comprehensive

# 📋 日誌和報告
python factset_cli.py logs --stage=all --tail=100
python factset_cli.py logs --stage=search --export
python factset_cli.py report --format=summary --email
```

### GitHub Actions 對應命令 (相同語法)

```yaml
# v3.3.2 簡化 Actions.yml - 直接呼叫 CLI
- name: 🧪 系統驗證
  run: python factset_cli.py validate --comprehensive

- name: 🚀 執行管線
  run: python factset_cli.py pipeline --mode=${{ inputs.mode }} --log-level=info

- name: 📊 生成報告
  run: python factset_cli.py report --format=github-summary
```

## 📋 v3.3.2 日誌系統架構

### 階段式日誌檔案結構

```
logs/
├── 20250624/                    # 日期目錄
│   ├── validation_094530.log    # 驗證階段
│   ├── search_094645.log        # 搜尋階段
│   ├── processing_095230.log    # 處理階段
│   ├── upload_095845.log        # 上傳階段
│   ├── pipeline_094530.log      # 完整流程總日誌
│   └── error_summary.log        # 錯誤摘要
├── latest/                      # 最新日誌連結
│   ├── validation.log -> ../20250624/validation_094530.log
│   ├── search.log -> ../20250624/search_094645.log
│   └── pipeline.log -> ../20250624/pipeline_094530.log
└── reports/                     # 日誌報告
    ├── daily_summary_20250624.html
    └── error_analysis_20250624.json
```

### 雙重輸出範例

```python
# v3.3.2 階段式日誌輸出範例

# 控制台輸出 (簡潔)
🔍 [SEARCH] Starting enhanced search for 116 companies...
✅ [SEARCH] Company 1/116: 台積電 (2330) - 5 files saved
⚠️ [SEARCH] Company 14/116: Rate limiting detected - switching to conservative mode
📊 [SEARCH] Completed: 95/116 companies, 847 files saved

# 檔案輸出 (詳細) - search_094645.log
2025-06-24 09:46:45,123 [INFO] factset_v332.search - Starting enhanced search suite v3.3.2
2025-06-24 09:46:45,124 [INFO] factset_v332.search - Configuration: mode=enhanced, companies=116
2025-06-24 09:46:45,125 [DEBUG] factset_v332.search - Rate protector initialized: threshold=1
2025-06-24 09:46:47,234 [INFO] factset_v332.search - Processing company: 台積電 (2330)
2025-06-24 09:46:47,235 [DEBUG] factset_v332.search - Search query: 台積電 factset EPS 預估
2025-06-24 09:46:48,456 [INFO] factset_v332.search - Found 10 URLs for 台積電
2025-06-24 09:46:49,678 [INFO] factset_v332.search - Saved: 2330_台積電_factset_a1b2c3d4_0624094649.md
[詳細的 URL 處理、錯誤處理、效能統計...]
2025-06-24 09:52:30,789 [WARNING] factset_v332.search - Rate limiting detected: 429 Too Many Requests
2025-06-24 09:52:30,790 [INFO] factset_v332.search - Switching to conservative mode
[恢復策略、繼續處理...]
2025-06-24 10:15:45,123 [INFO] factset_v332.search - Search completed: 95/116 companies successful
```

## 🎯 v3.3.2 簡化 Actions.yml

### 簡潔的工作流程定義

```yaml
name: FactSet Pipeline v3.3.2 - Simplified & Observable

on:
  workflow_dispatch:
    inputs:
      mode: { type: choice, options: [intelligent, enhanced, conservative, process_only] }
      priority: { type: choice, options: [high_only, top_30, balanced] }
      memory_limit: { type: string, default: '2048' }
  schedule: [cron: "10 2 * * *"]

jobs:
  # v3.3.2 簡化驗證
  validate:
    runs-on: ubuntu-latest
    outputs:
      status: ${{ steps.validate.outputs.status }}
      recommendation: ${{ steps.validate.outputs.recommendation }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      - id: validate
        run: python factset_cli.py validate --github-actions

  # v3.3.2 主要管線
  pipeline:
    needs: validate
    runs-on: ubuntu-latest
    env:
      GOOGLE_SEARCH_API_KEY: ${{ secrets.GOOGLE_SEARCH_API_KEY }}
      GOOGLE_SEARCH_CSE_ID: ${{ secrets.GOOGLE_SEARCH_CSE_ID }}
      GOOGLE_SHEETS_CREDENTIALS: ${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}
      GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      
      - name: 🚀 執行 v3.3.2 管線
        run: |
          python factset_cli.py pipeline \
            --mode=${{ inputs.mode || 'intelligent' }} \
            --priority=${{ inputs.priority || 'high_only' }} \
            --memory-limit=${{ inputs.memory_limit || '2048' }} \
            --github-actions
      
      - name: 📊 生成報告
        if: always()
        run: python factset_cli.py report --format=github-summary
      
      - name: 💾 智能提交
        run: python factset_cli.py commit --smart --validate

  # v3.3.2 恢復
  recovery:
    needs: [validate, pipeline]
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      - run: python factset_cli.py recover --analyze --github-actions
```

## 📊 v3.3.2 輸出規格 (保持 v3.3.1)

### Portfolio Summary (投資組合摘要) - 14欄位格式 ✅ 不變

```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
1587,吉茂,1587-TW,2025/1/22,2025/6/22,6,23,102.3,20,20,20,4,🟢 完整,2025-06-24 10:45:00
```

### Detailed Data (詳細資料) - 21欄位 EPS 分解 ✅ 不變

### v3.3.2 Statistics (增強統計資料) - 新增可觀測性指標

```json
{
  "version": "3.3.2",
  "total_companies": 116,
  "companies_with_data": 95,
  "success_rate": 82.1,
  "performance_stats": {
    "files_processed": 847,
    "batches_completed": 17,
    "memory_cleanups": 3,
    "peak_memory_mb": 1847
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
  "v331_fixes_maintained": {
    "cascade_failure_protection": true,
    "performance_optimization": true,
    "unified_rate_limiting": true,
    "memory_management": true,
    "data_deduplication": true
  },
  "guideline_version": "3.3.2"
}
```

## 🛠️ v3.3.2 實作重點

### 1. 統一 CLI 介面實作

```python
# factset_cli.py - v3.3.2 統一入口
def main():
    cli = FactSetCLI()
    
    # 跨平台參數解析
    parser = create_unified_parser()
    args = parser.parse_args()
    
    # 執行命令 (Windows/Linux 相同行為)
    try:
        result = cli.execute(args.command, **vars(args))
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        cli.logger.warning("執行被使用者中斷")
        sys.exit(130)
    except Exception as e:
        cli.logger.error(f"執行失敗: {e}")
        sys.exit(1)
```

### 2. 階段式執行器實作

```python
# stage_runner.py - v3.3.2 階段協調
class StageRunner:
    def _execute_stage_logic(self, stage_name, context, **kwargs):
        """根據階段名稱執行對應邏輯"""
        stage_map = {
            'validate': self._run_validation_stage,
            'search': self._run_search_stage,
            'process': self._run_processing_stage,
            'upload': self._run_upload_stage,
            'pipeline': self._run_pipeline_stage
        }
        
        if stage_name not in stage_map:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        return stage_map[stage_name](context, **kwargs)
```

### 3. 保持 v3.3.1 所有修復

```python
# 以下類別和功能完全保持 v3.3.1 版本，確保所有修復維持有效：

# ✅ FIXED #1: 級聯故障保護
class CascadeFailureProtection:  # 保持不變

# ✅ FIXED #2: 性能優化 (預編譯正則表達式)
COMPILED_FACTSET_PATTERNS = {}  # 保持不變

# ✅ FIXED #3: 統一速率限制器
class UnifiedRateLimitProtector:  # 保持不變

# ✅ FIXED #4: 模組導入修復 (延遲載入)
class LazyImporter:  # 保持不變

# ✅ FIXED #5: 資料聚合修復 (智能去重)
def deduplicate_financial_data_v331():  # 保持不變

# ✅ FIXED #9: 記憶體管理
class MemoryManager:  # 保持不變

# v3.3.2 新增: 只是在現有功能基礎上增加更好的日誌整合
```

## 🚀 v3.3.2 部署指令

### 本地開發 (跨平台)

```bash
# Windows PowerShell 或 Linux Bash - 相同命令

# 1. 快速開始
python factset_cli.py pipeline --mode=intelligent

# 2. 完整驗證
python factset_cli.py validate --comprehensive --fix-issues

# 3. 階段式執行
python factset_cli.py search --mode=conservative --log-level=debug
python factset_cli.py process --memory-limit=2048 --batch-size=25
python factset_cli.py upload --test-connection

# 4. 診斷和日誌
python factset_cli.py logs --stage=search --tail=50
python factset_cli.py diagnose --issue="rate limiting" --suggest-fix
python factset_cli.py status --detailed --export=json
```

### GitHub Actions (相同命令)

```yaml
# 完全相同的命令語法
run: python factset_cli.py pipeline --mode=enhanced --github-actions
```

## 📋 v3.3.2 維護和監控

### 日誌檢查命令

```bash
# 查看今日所有階段日誌
python factset_cli.py logs --today --all-stages

# 查看特定階段錯誤
python factset_cli.py logs --stage=search --level=error --last=24h

# 生成日誌摘要報告
python factset_cli.py report --logs --format=html --email=admin@company.com

# 診斷特定問題
python factset_cli.py diagnose --symptom="no data generated" --verbose
```

### 效能監控

```bash
# 檢查 v3.3.2 效能統計
python factset_cli.py performance --compare-with=v331 --detailed

# 記憶體使用分析
python factset_cli.py analyze --memory --stage=processing --optimization-tips

# 跨平台兼容性檢查
python factset_cli.py validate --cross-platform --windows --linux
```

## 🔧 v3.3.2 故障排除

### 自動診斷系統

```bash
# v3.3.2 智能診斷
python factset_cli.py diagnose --auto --fix-common

# 常見問題自動修復
python factset_cli.py recover --issue="module import error" --auto-fix
python factset_cli.py recover --issue="rate limiting" --wait-and-retry
python factset_cli.py recover --issue="memory exhaustion" --optimize

# 跨平台問題診斷
python factset_cli.py diagnose --platform-specific --encoding --paths
```

### 階段式恢復

```bash
# 從特定階段恢復
python factset_cli.py recover --from-stage=search --continue-pipeline
python factset_cli.py recover --from-stage=processing --reprocess-data

# 使用現有資料恢復
python factset_cli.py recover --use-existing --skip-search --process-only
```

## 📈 v3.3.2 與 v3.3.1 比較摘要

| 特性 | v3.3.1 | v3.3.2 | 改進 |
|------|--------|--------|------|
| **工作流程複雜度** | 複雜 Actions.yml | 簡潔 Actions.yml | ✅ 80% 簡化 |
| **跨平台命令** | 部分兼容 | 完全統一 | ✅ 100% 兼容 |
| **日誌系統** | 基礎日誌 | 階段式雙重日誌 | ✅ 可觀測性大幅提升 |
| **錯誤診斷** | 手動檢查 | 自動診斷修復 | ✅ 智能化故障排除 |
| **開發體驗** | 良好 | 優秀 | ✅ CLI 統一化 |
| **維護性** | 複雜 | 簡單 | ✅ 模組化清晰 |
| **所有 v3.3.1 修復** | ✅ | ✅ | ✅ 完全保持 |

## 🎯 v3.3.2 完整實作檢查清單

### 必要檔案 (新增/修改)

```
FactSet-Pipeline/
├── factset_cli.py              # 🆕 統一 CLI 入口
├── stage_runner.py             # 🆕 階段執行器
├── enhanced_logger.py          # 🆕 增強日誌管理器
├── factset_pipeline.py         # 🔄 保持 v3.3.1 + 日誌整合
├── factset_search.py           # 🔄 保持 v3.3.1 + 日誌整合
├── data_processor.py           # 🔄 保持 v3.3.1 + 日誌整合
├── sheets_uploader.py          # 🔄 保持 v3.3.1 + 日誌整合
├── config.py                   # 🔄 保持 v3.3.1 + 日誌整合
├── utils.py                    # 🔄 保持 v3.3.1 + 日誌整合
├── setup_validator.py          # 🔄 保持 v3.3.1 + 日誌整合
├── .github/workflows/Actions.yml # 🔄 大幅簡化 (移除內嵌 Python)
├── requirements.txt            # 🔄 新增日誌相關依賴
├── .env.example               # ✅ 保持不變
└── README.md                  # 🔄 更新為 v3.3.2 說明
```

### 核心實作要點

1. **factset_cli.py** - 實作所有統一命令
2. **stage_runner.py** - 協調執行並管理階段
3. **enhanced_logger.py** - 雙重輸出日誌系統
4. **Actions.yml** - 移除所有內嵌 Python，只呼叫 CLI
5. **跨平台測試** - Windows 和 Linux 命令一致性

### v3.3.1 修復維護要求

- ✅ 所有 FIXED #1-9 功能必須完全保持
- ✅ 效能優化不能退化
- ✅ 現有配置檔案向後兼容
- ✅ 輸出格式完全相同

---

**v3.3.2 總結**: 在保持 v3.3.1 所有修復和效能的基礎上，大幅簡化了工作流程、統一了跨平台 CLI、增強了可觀測性，提供了更好的開發和維護體驗。