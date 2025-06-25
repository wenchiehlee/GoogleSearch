# Enhanced FactSet Pipeline v3.3.2 - Simplified & Observable

[![Pipeline Status](https://img.shields.io/badge/Pipeline-v3.3.2-brightgreen)](https://github.com/your-repo/factset-pipeline)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/your-repo/factset-pipeline)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 🎯 Overview

**Enhanced FactSet Pipeline v3.3.2** automates the collection and analysis of FactSet financial data for Taiwan stock market companies, generating comprehensive investment portfolio reports with enhanced observability and cross-platform compatibility.

### v3.3.2 Key Improvements

```
v3.3.1 (Comprehensive Fixes)     →     v3.3.2 (Simplified & Observable)
├─ Complex Actions.yml workflow         ├─ Streamlined 80% simpler workflow
├─ Basic logging system                 ├─ Stage-specific dual logging
├─ Platform-specific commands           ├─ Unified cross-platform CLI
├─ Manual error tracking                ├─ Automated diagnostics & recovery
└─ Mixed responsibility modules         └─ Clear separation of concerns
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-repo/factset-pipeline.git
cd factset-pipeline

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Basic Usage

```bash
# Quick validation
python factset_cli.py validate --comprehensive

# Run complete pipeline
python factset_cli.py pipeline --mode=intelligent

# Check results
python factset_cli.py status --comprehensive
```

### 3. View Results

- **Google Sheets Dashboard**: Automatically updated with latest data
- **Local Files**: `data/processed/` directory contains CSV and JSON files
- **Logs**: `logs/latest/` directory for troubleshooting

## 📊 System Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Unified CLI   │───▶│  Stage Runner    │───▶│ Business Logic  │
│ factset_cli.py  │    │ stage_runner.py  │    │ (各專業模組)     │
│ Cross-platform  │    │ Orchestration    │    │ v3.3.1 fixes   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Enhanced Logger │    │ Performance Mon. │    │ Output Files    │
│enhanced_logger.py│    │ Real-time stats  │    │ Dual logging    │
│ Stage-specific  │    │ Memory tracking  │    │ CSV/JSON/Logs   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

```
觀察名單.csv (116+ 台股公司)
          ↓
┌─────────────────────────────────────────────────────────────┐
│ Enhanced FactSet Pipeline v3.3.2                           │
├─────────────────────────────────────────────────────────────┤
│ 🧪 Validation    → 📥 Download    → 🔍 Search             │
│ System check      Watchlist        Financial data         │
│                                                             │
│ 📊 Processing    → 📈 Upload       → 📋 Reporting         │
│ Data analysis     Google Sheets     Status & logs         │
└─────────────────────────────────────────────────────────────┘
          ↓
Google Sheets Dashboard + Local CSV Files + Comprehensive Logs
```

## 🔧 Command Reference

### Core Operations

```bash
# 🧪 System Validation
python factset_cli.py validate --comprehensive
python factset_cli.py validate --quick
python factset_cli.py validate --test-v332

# 📥 Watchlist Management  
python factset_cli.py download-watchlist --validate
python factset_cli.py download-watchlist --force-refresh

# 🔍 Search Phase
python factset_cli.py search --mode=enhanced --priority=high_only
python factset_cli.py search --mode=conservative --companies=30
python factset_cli.py search --test-cascade-protection

# 📊 Data Processing Phase
python factset_cli.py process --mode=v332 --memory-limit=2048
python factset_cli.py process --deduplicate --aggregate
python factset_cli.py process --benchmark

# 📈 Upload Phase
python factset_cli.py upload --sheets=all --backup
python factset_cli.py upload --test-connection
python factset_cli.py upload --sheets=portfolio,detailed
```

### Pipeline Operations

```bash
# 🚀 Complete Pipeline
python factset_cli.py pipeline --mode=intelligent --log-level=info
python factset_cli.py pipeline --mode=enhanced --memory=2048 --batch-size=50
python factset_cli.py pipeline --mode=process-only

# Available modes:
# - intelligent: Smart execution with v3.3.2 enhancements
# - enhanced: Full v3.3.2 features
# - conservative: High priority only, with delays
# - process_only: Process existing data only
```

### Diagnostics & Recovery

```bash
# 🔄 Recovery and Diagnostics
python factset_cli.py recover --analyze --fix-common-issues
python factset_cli.py diagnose --stage=search --detailed
python factset_cli.py diagnose --auto --suggest-fixes
python factset_cli.py status --comprehensive

# 📋 Logs and Reporting
python factset_cli.py logs --stage=all --tail=100
python factset_cli.py logs --stage=search --export
python factset_cli.py report --format=summary
python factset_cli.py report --format=html --detailed
```

## 📁 File Structure

```
FactSet-Pipeline/
├── 🆕 factset_cli.py              # Unified CLI interface
├── 🆕 stage_runner.py             # Stage execution coordinator  
├── 🆕 enhanced_logger.py          # Enhanced logging system
├── 🔄 factset_pipeline.py         # Main pipeline (v3.3.1 + logging)
├── 🔄 factset_search.py           # Search engine (v3.3.1 + logging)
├── 🔄 data_processor.py           # Data processor (v3.3.1 + logging)
├── 🔄 sheets_uploader.py          # Sheets uploader (v3.3.1 + logging)
├── 🔄 config.py                   # Configuration (v3.3.1 + logging)
├── 🔄 utils.py                    # Utilities (v3.3.1 + logging)
├── 🔄 setup_validator.py          # Setup validator (v3.3.1 + logging)
├── 📁 data/                       # Data directory
│   ├── csv/                       # Raw CSV data
│   ├── md/                        # Markdown content files
│   └── processed/                 # Processed output files
├── 📁 logs/                       # Enhanced logging directory
│   ├── 20250624/                  # Date-based log files
│   ├── latest/                    # Latest log links
│   └── reports/                   # Log analysis reports
├── 📁 .github/workflows/          # GitHub Actions
│   └── Actions.yml                # Simplified workflow (80% reduction)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## 📊 Output Formats

### 1. Portfolio Summary (投資組合摘要)
**14-column aggregated format** - One row per company

```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
1587,吉茂,1587-TW,2025/1/22,2025/6/22,6,23,102.3,20,20,20,4,🟢 完整,2025-06-24 10:45:00
2330,台積電,2330-TW,2025/1/15,2025/6/20,12,35,650.5,25.8,28.2,31.1,4,🟢 完整,2025-06-24 10:45:00
```

### 2. Detailed Data (詳細資料)
**21-column file-level format** - One row per MD file

```csv
代號,名稱,股票代號,MD日期,分析師數量,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2026EPS最高值,2026EPS最低值,2026EPS平均值,2027EPS最高值,2027EPS最低值,2027EPS平均值,品質評分,狀態,MD File,更新日期
```

### 3. Enhanced Statistics (增強統計)
**JSON format with v3.3.2 observability metrics**

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
  }
}
```

## 📋 v3.3.2 Enhanced Logging

### Dual Output System

**Console Output** (Concise)
```
✅ [SEARCH] Starting enhanced search for 116 companies...
🔍 [SEARCH] Company 1/116: 台積電 (2330) - 5 files saved
⚠️ [SEARCH] Company 14/116: Rate limiting detected - switching to conservative mode
📊 [SEARCH] Completed: 95/116 companies, 847 files saved
```

**File Output** (Detailed)
```
logs/
├── 20250624/                    # Date directory
│   ├── validation_094530.log    # Validation stage
│   ├── search_094645.log        # Search stage  
│   ├── processing_095230.log    # Processing stage
│   ├── upload_095845.log        # Upload stage
│   └── pipeline_094530.log      # Complete pipeline log
├── latest/                      # Latest log links
│   ├── validation.log -> ../20250624/validation_094530.log
│   └── search.log -> ../20250624/search_094645.log
└── reports/                     # Log analysis reports
    └── daily_summary_20250624.html
```

### Log Management Commands

```bash
# View real-time logs
python factset_cli.py logs --stage=search --tail=50 --follow

# Export logs
python factset_cli.py logs --export --format=html --email=admin@company.com

# Analyze errors
python factset_cli.py diagnose --logs --auto-suggest-fixes
```

## 🛠️ Configuration

### Environment Variables

Create `.env` file with required API keys:

```bash
# Google Search API
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_CSE_ID=your_cse_id_here

# Google Sheets API  
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}
GOOGLE_SHEET_ID=your_sheet_id_here

# Optional: Customize behavior
FACTSET_MEMORY_LIMIT=2048
FACTSET_LOG_LEVEL=INFO
FACTSET_ENABLE_PERFORMANCE_MONITORING=true
```

### Configuration File (Optional)

```json
{
  "version": "3.3.2",
  "search": {
    "max_results": 10,
    "rate_limit_delay": 3,
    "content_quality_threshold": 3
  },
  "processing": {
    "memory_limit_mb": 2048,
    "batch_size": 50,
    "deduplicate_data": true
  },
  "logging": {
    "stage_specific": true,
    "dual_output": true,
    "performance_monitoring": true
  }
}
```

## 🚨 Troubleshooting

### Automatic Diagnostics

```bash
# Quick diagnosis
python factset_cli.py diagnose --auto

# Specific issue diagnosis
python factset_cli.py diagnose --issue="rate limiting" --suggest-fixes
python factset_cli.py diagnose --issue="memory exhaustion" --optimize
python factset_cli.py diagnose --issue="module import error" --fix
```

### Common Issues & Solutions

| Issue | Command | Description |
|-------|---------|-------------|
| Rate Limiting | `--mode=conservative` | Reduce request frequency |
| Memory Issues | `--memory-limit=1024` | Lower memory usage |
| Import Errors | `pip install -r requirements.txt` | Reinstall dependencies |
| Platform Issues | `--cross-platform --validate` | Check compatibility |

### Recovery Commands

```bash
# Automatic recovery
python factset_cli.py recover --auto --fix-common-issues

# Stage-specific recovery  
python factset_cli.py recover --from-stage=search --continue-pipeline
python factset_cli.py recover --use-existing --process-only

# Manual intervention
python factset_cli.py logs --stage=search --level=error --analyze
python factset_cli.py status --detailed --export=json
```

## 🔄 GitHub Actions Integration

### Simplified Workflow

The v3.3.2 GitHub Actions workflow is **80% simpler** than v3.3.1:

```yaml
# .github/workflows/Actions.yml
- name: 🚀 Execute v3.3.2 Pipeline  
  run: |
    python factset_cli.py pipeline \
      --mode=${{ inputs.execution_mode || 'intelligent' }} \
      --priority=${{ inputs.priority_focus || 'high_only' }} \
      --memory-limit=${{ inputs.memory_limit || '8192' }} \
      --github-actions
```

### Workflow Features

- ✅ **Unified Commands**: Same CLI syntax for local and CI/CD
- ✅ **Smart Recovery**: Automatic error detection and recovery
- ✅ **Enhanced Reporting**: Comprehensive execution summaries
- ✅ **Artifact Management**: Automated log collection and storage

## 📈 Performance & Monitoring

### v3.3.2 Performance Features

```bash
# Performance analysis
python factset_cli.py performance --compare-with=v331 --detailed

# Memory monitoring
python factset_cli.py analyze --memory --stage=processing --tips

# Cross-platform testing
python factset_cli.py validate --cross-platform --performance-test
```

### Monitoring Capabilities

- **Real-time Performance**: Operation timing and memory usage
- **Stage-specific Metrics**: Detailed execution statistics
- **Error Analysis**: Automated error categorization and suggestions  
- **Resource Management**: Memory optimization and cleanup
- **Cross-platform Compatibility**: Windows/Linux/macOS support

## 🔄 Migration from v3.3.1

### What's Changed

| Aspect | v3.3.1 | v3.3.2 | Migration |
|--------|--------|--------|-----------|
| **Commands** | Mixed interfaces | Unified CLI | Use `factset_cli.py` |
| **Logging** | Basic logs | Dual output | Check `logs/latest/` |
| **GitHub Actions** | Complex workflow | Simplified | No changes needed |
| **Functionality** | All features | Same + enhanced | No breaking changes |

### Migration Steps

```bash
# 1. Update repository
git pull origin main

# 2. Install new dependencies  
pip install -r requirements.txt

# 3. Test new CLI
python factset_cli.py validate --comprehensive

# 4. Run pipeline with v3.3.2
python factset_cli.py pipeline --mode=intelligent
```

**Note**: All v3.3.1 fixes are maintained. No configuration changes required.

## 🤝 Contributing

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-repo/factset-pipeline.git
cd factset-pipeline
pip install -r requirements-dev.txt

# Run tests
python factset_cli.py validate --test-v332 --comprehensive

# Check cross-platform compatibility
python factset_cli.py validate --cross-platform
```

### Code Standards

- **v3.3.2 Compatibility**: All new code must support cross-platform CLI
- **Logging Integration**: Use `enhanced_logger` for all new modules
- **Stage Architecture**: Follow the stage runner pattern
- **Performance**: Maintain v3.3.1 optimization levels

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Links

- **Dashboard**: [Google Sheets Live Dashboard](https://docs.google.com/spreadsheets/d/your_sheet_id/edit)
- **Documentation**: [Complete v3.3.2 Guide](instructions.md)
- **Issue Tracker**: [GitHub Issues](https://github.com/your-repo/factset-pipeline/issues)
- **API Documentation**: [FactSet API Reference](https://developer.factset.com/)

## 📊 Version Comparison

| Feature | v3.3.0 | v3.3.1 | v3.3.2 |
|---------|--------|--------|--------|
| **Core Pipeline** | ✅ | ✅ | ✅ |
| **Data Processing** | ✅ | ✅ Enhanced | ✅ Enhanced |
| **Error Handling** | Basic | Comprehensive | Intelligent |
| **Cross-platform** | Partial | Good | Excellent |
| **Logging** | Basic | Enhanced | Dual Output |
| **Observability** | Limited | Good | Comprehensive |
| **CLI Interface** | Mixed | Improved | Unified |
| **GitHub Actions** | Complex | Complex | Simplified |

---

**Enhanced FactSet Pipeline v3.3.2** - Simplifying financial data automation while enhancing observability and cross-platform compatibility.

For questions or support, please [open an issue](https://github.com/your-repo/factset-pipeline/issues) or contact the development team.