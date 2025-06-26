# Enhanced FactSet Pipeline v3.3.3 - Final Integrated Edition

[![Pipeline Status](https://img.shields.io/badge/Pipeline-v3.3.3-brightgreen)](https://github.com/your-repo/factset-pipeline)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/your-repo/factset-pipeline)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Quality Scoring](https://img.shields.io/badge/Quality%20Scoring-0--10%20Scale-orange)](https://github.com/your-repo/factset-pipeline)

## 🎯 Overview

**Enhanced FactSet Pipeline v3.3.3** automates the collection and analysis of FactSet financial data for Taiwan stock market companies, generating comprehensive investment portfolio reports with **standardized quality scoring**, **GitHub Actions modernization**, and **direct MD file access**.

### 🆕 v3.3.3 Final Integrated Edition

```
v3.3.2 (Simplified & Observable)     →     v3.3.3 (Final Integrated Edition)
├─ Basic quality scoring                   ├─ Standardized Quality Scoring (0-10)
├─ GitHub Actions basic support            ├─ GitHub Actions Modernization (GITHUB_OUTPUT)
├─ Basic MD file links                     ├─ GitHub Raw URL Direct Links
├─ Standard dashboard URL                  ├─ Live Dashboard Optimization
└─ All v3.3.2 features                    └─ All features maintained + enhanced
```

### 🌟 v3.3.3 Key Features

- **🎯 Standardized Quality Scoring**: 0-10 scale with visual indicators (🟢🟡🟠🔴)
- **🔗 GitHub Raw URLs**: Direct clickable links to MD files
- **⚡ GitHub Actions Modernization**: Fixed deprecated warnings, GITHUB_OUTPUT support
- **📊 Live Dashboard Optimization**: Corrected URL pointing for real-time data
- **🔄 Legacy Compatibility**: All v3.3.2 + v3.3.1 features maintained
- **🌐 Cross-platform**: Windows/Linux/macOS unified commands

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

### 2. v3.3.3 Enhanced Usage

```bash
# Quick validation with v3.3.3 features
python factset_cli.py validate --comprehensive --test-v333

# Run complete pipeline with quality scoring
python factset_cli.py pipeline --mode=intelligent --v333

# Check quality-enhanced results
python factset_cli.py status --comprehensive --quality-summary
```

### 3. View v3.3.3 Results

- **📊 Google Sheets Dashboard**: Enhanced with quality indicators and GitHub Raw links
- **📁 Local Files**: `data/processed/` with standardized quality scoring
- **🔗 Direct MD Access**: Clickable GitHub Raw URLs for immediate file viewing
- **📋 Quality Reports**: Comprehensive 0-10 quality analysis

## 📊 v3.3.3 System Architecture

### Enhanced Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Unified CLI   │───▶│  Stage Runner    │───▶│ Business Logic  │
│ factset_cli.py  │    │ stage_runner.py  │    │ + Quality Score │
│ v3.3.3 Enhanced │    │ Quality Integrated│    │ (各專業模組)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│Quality Scorer   │    │ Enhanced Logger  │    │ GitHub Raw URLs │
│0-10 Standardized│    │enhanced_logger.py│    │ Direct MD Links │
│🟢🟡🟠🔴 Indicators│    │ Stage-specific   │    │ v3.3.3 Format  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### v3.3.3 Data Flow

```
觀察名單.csv (116+ 台股公司)
          ↓
┌─────────────────────────────────────────────────────────────┐
│ Enhanced FactSet Pipeline v3.3.3 Final Integrated Edition  │
├─────────────────────────────────────────────────────────────┤
│ 🧪 Validation    → 📥 Download    → 🔍 Search             │
│ v3.3.3 Features   Quality Check    Enhanced patterns      │
│                                                             │
│ 📊 Processing    → 📈 Upload       → 📋 Reporting         │
│ Quality Scoring   GitHub Raw URLs   Quality Analysis      │
│ 0-10 Scale        🟢🟡🟠🔴 Status    Comprehensive Stats   │
└─────────────────────────────────────────────────────────────┘
          ↓
Google Sheets (Quality Enhanced) + GitHub Raw Links + Quality Reports
```

## 🎯 v3.3.3 Quality Scoring System

### Standardized 0-10 Scale

| Score Range | Indicator | Description | Criteria |
|-------------|-----------|-------------|----------|
| **9-10** | 🟢 完整 | Complete | EPS data 90%+, 20+ analysts, data ≤7 days |
| **8** | 🟡 良好 | Good | EPS data 70%+, 10+ analysts, data ≤30 days |
| **3-7** | 🟠 部分 | Partial | EPS data 30%+, 5+ analysts, data ≤90 days |
| **0-2** | 🔴 不足 | Insufficient | Limited or missing data |

### Quality Commands

```bash
# Quality analysis
python factset_cli.py quality --analyze
python factset_cli.py quality --distribution
python factset_cli.py quality --benchmark

# Quality monitoring
python factset_cli.py quality --monitor --threshold=7
python factset_cli.py quality --calibrate --fix-scoring-anomalies

# Quality reports
python factset_cli.py report --quality-focused --v333-metrics
```

## 🔧 v3.3.3 Command Reference

### Core Operations

```bash
# 🧪 System Validation (v3.3.3)
python factset_cli.py validate --comprehensive --test-v333
python factset_cli.py validate --quality-scoring --test-cli
python factset_cli.py validate --github-actions --modern-output

# 📥 Watchlist Management  
python factset_cli.py download-watchlist --validate --force-refresh

# 🔍 Search Phase (Enhanced)
python factset_cli.py search --mode=enhanced --priority=high_only
python factset_cli.py search --mode=conservative --quality-threshold=7

# 📊 Data Processing Phase (v3.3.3)
python factset_cli.py process --mode=v333 --quality-scoring
python factset_cli.py process --standardize-quality --memory-limit=2048
python factset_cli.py process --deduplicate --aggregate --v333-format

# 📈 Upload Phase (GitHub Raw URLs)
python factset_cli.py upload --v333-format --quality-indicators
python factset_cli.py upload --github-raw-urls --backup
python factset_cli.py upload --test-connection --modern-format
```

### v3.3.3 Pipeline Operations

```bash
# 🚀 Complete Pipeline (v3.3.3)
python factset_cli.py pipeline --mode=intelligent --v333
python factset_cli.py pipeline --quality-scoring --standardize-quality
python factset_cli.py pipeline --mode=enhanced --github-actions --modern

# Available v3.3.3 modes:
# - intelligent: Smart execution with quality scoring
# - enhanced: Full v3.3.3 features
# - v333: Latest integrated features
# - conservative: High priority with quality focus
# - process_only: Process with quality standardization
```

### v3.3.3 Quality & Diagnostics

```bash
# 🎯 Quality Scoring
python factset_cli.py quality --analyze --company=2330
python factset_cli.py quality --distribution --export=html
python factset_cli.py quality --monitor --alert-low-quality

# 🔄 Recovery and Diagnostics (v3.3.3)
python factset_cli.py recover --v333-diagnostics --auto-fix
python factset_cli.py diagnose --quality-system --comprehensive
python factset_cli.py diagnose --github-actions --check-deprecated

# 📋 Enhanced Logs and Reporting
python factset_cli.py logs --stage=all --quality-filter=high
python factset_cli.py report --format=v333-quality-analysis
python factset_cli.py report --github-summary --modern-output
```

## 📁 v3.3.3 File Structure

```
FactSet-Pipeline/
├── 🆕 factset_cli.py              # v3.3.3 Unified CLI + Quality Scoring
├── 🆕 stage_runner.py             # v3.3.3 Stage Coordinator + Quality Integration
├── ✅ enhanced_logger.py          # v3.3.2 Enhanced logging (maintained)
├── 🔄 factset_pipeline.py         # v3.3.3 Main pipeline + Quality Scoring
├── 🔄 factset_search.py           # v3.3.3 Search engine + Quality Assessment
├── 🔄 data_processor.py           # v3.3.3 Data processor + Standardized Quality
├── 🔄 sheets_uploader.py          # v3.3.3 Sheets uploader + GitHub Raw URLs
├── 🔄 config.py                   # v3.3.3 Configuration + Quality Settings
├── 🔄 utils.py                    # v3.3.3 Utilities + Quality Tools
├── 🔄 setup_validator.py          # v3.3.3 Setup validator + Quality Tests
├── 📁 data/                       # Data directory
│   ├── csv/                       # Raw CSV data
│   ├── md/                        # Markdown content files
│   └── processed/                 # v3.3.3 Processed files with quality scores
├── 📁 logs/                       # Enhanced logging directory
│   ├── 20250624/                  # Date-based log files
│   ├── latest/                    # Latest log links
│   └── reports/                   # v3.3.3 Quality analysis reports
├── 📁 .github/workflows/          # GitHub Actions
│   └── Actions.yml                # v3.3.3 Modernized workflow (GITHUB_OUTPUT)
├── requirements.txt               # Python dependencies + quality analysis libs
├── .env.example                   # Environment variables template
└── README.md                      # This file (v3.3.3)
```

## 📊 v3.3.3 Enhanced Output Formats

### 1. Portfolio Summary (投資組合摘要) - v3.3.3 Quality Enhanced
**14-column format with standardized quality scoring**

```csv
代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
1587,吉茂,1587-TW,2025/1/22,2025/6/22,6,23,102.3,20,20,20,9,🟢 完整,2025-06-24 10:45:00
2330,台積電,2330-TW,2025/1/15,2025/6/20,12,35,650.5,25.8,28.2,31.1,10,🟢 完整,2025-06-24 10:45:00
2454,聯發科,2454-TW,2025/5/15,2025/6/20,8,18,980.2,75.8,82.3,89.1,7,🟠 部分,2025-06-24 10:45:00
```

### 2. Detailed Data (詳細資料) - v3.3.3 GitHub Raw URLs
**21-column format with direct MD file links**

```csv
代號,名稱,股票代號,MD日期,分析師數量,目標價,2025EPS最高值,2025EPS最低值,2025EPS平均值,2026EPS最高值,2026EPS最低值,2026EPS平均值,2027EPS最高值,2027EPS最低值,2027EPS平均值,品質評分,狀態,MD File,更新日期
2330,台積電,2330-TW,2025/06/23,42,650.5,59.66,6.0,46.0,32.34,6.0,23.56,32.34,6.0,23.56,10,🟢 完整,[2330_台積電_yahoo.md](https://raw.githubusercontent.com/.../2330_台積電_yahoo.md),2025-06-24 05:52:02
```

### 3. v3.3.3 Enhanced Statistics
**JSON format with quality analysis and modernization tracking**

```json
{
  "version": "3.3.3",
  "release_type": "final_integrated",
  "total_companies": 116,
  "companies_with_data": 95,
  "success_rate": 82.1,
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
  "performance_stats": {
    "files_processed": 847,
    "peak_memory_mb": 1847,
    "quality_calculations": 847,
    "github_raw_urls_generated": 847
  }
}
```

## 📋 v3.3.3 Enhanced Logging

### Stage-Specific Quality Logging

**Console Output** (Enhanced with Quality)
```
✅ [SEARCH] Starting v3.3.3 enhanced search with quality scoring...
🔍 [SEARCH] Company 1/116: 台積電 (2330) - Quality: 10/10 🟢 完整
🎯 [PROCESS] v3.3.3 quality scoring: Average 6.8/10 (🟢45 🟡18 🟠25 🔴7)
📊 [UPLOAD] GitHub Raw URLs generated: 847 direct links
🎉 [PIPELINE] v3.3.3 Final completed: 95/116 companies, Quality optimized
```

**File Output** (Comprehensive with Quality Metrics)
```
logs/
├── 20250624/                    
│   ├── validation_094530.log    # v3.3.3 validation with quality tests
│   ├── search_094645.log        # Search with quality assessment  
│   ├── processing_095230.log    # Processing with quality calculation
│   ├── upload_095845.log        # Upload with GitHub Raw URL generation
│   └── pipeline_094530.log      # Complete pipeline with quality summary
├── latest/                      
│   └── quality_analysis.json    # v3.3.3 Real-time quality metrics
└── reports/                     
    ├── quality_distribution.html # v3.3.3 Quality analysis dashboard
    └── github_modernization.log  # GitHub Actions upgrade status
```

## 🛠️ v3.3.3 Configuration

### Enhanced Environment Variables

```bash
# Google APIs (unchanged)
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_CSE_ID=your_cse_id_here
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}
GOOGLE_SHEET_ID=your_sheet_id_here

# v3.3.3 Quality Scoring
FACTSET_ENABLE_QUALITY_SCORING=true
FACTSET_QUALITY_SCALE=0-10
FACTSET_QUALITY_INDICATORS=true

# v3.3.3 GitHub Features
FACTSET_GITHUB_RAW_URLS=true
GITHUB_OUTPUT=/path/to/output  # For GitHub Actions modernization

# v3.3.3 Enhanced Performance
FACTSET_MEMORY_LIMIT=2048
FACTSET_LOG_LEVEL=INFO
FACTSET_ENABLE_PERFORMANCE_MONITORING=true
```

### v3.3.3 Configuration File

```json
{
  "version": "3.3.3",
  "quality": {
    "enable_scoring": true,
    "scoring_scale": "0-10",
    "quality_indicators": true,
    "legacy_conversion": true,
    "quality_thresholds": {
      "complete": 9,
      "good": 8,
      "partial": 3,
      "insufficient": 0
    }
  },
  "v333_features": {
    "github_raw_urls": true,
    "standardized_quality_scoring": true,
    "github_actions_modernization": true,
    "live_dashboard_optimization": true
  },
  "search": {
    "max_results": 10,
    "rate_limit_delay": 3,
    "content_quality_threshold": 7
  },
  "processing": {
    "memory_limit_mb": 2048,
    "batch_size": 50,
    "quality_scoring": true,
    "standardize_quality": true
  }
}
```

## 🚨 v3.3.3 Troubleshooting

### Enhanced Automatic Diagnostics

```bash
# v3.3.3 comprehensive diagnosis
python factset_cli.py diagnose --v333-comprehensive --auto-fix

# Quality system diagnosis
python factset_cli.py diagnose --quality-system --calibration-check

# GitHub Actions modernization check
python factset_cli.py diagnose --github-actions --deprecated-check --fix

# MD file link verification
python factset_cli.py diagnose --md-links --github-raw-test
```

### v3.3.3 Specific Issues & Solutions

| Issue | Command | Description |
|-------|---------|-------------|
| Quality Scoring | `--quality-scoring --calibrate` | Fix quality calculation issues |
| GitHub Raw URLs | `--github-raw-urls --test-links` | Verify MD file accessibility |
| GitHub Actions | `--modernize-actions --fix-deprecated` | Update GitHub workflow |
| Legacy Scores | `--standardize-quality --convert-legacy` | Convert 1-4 to 0-10 scale |

### v3.3.3 Recovery Commands

```bash
# Quality-focused recovery
python factset_cli.py recover --quality-repair --standardize-scores

# GitHub Actions recovery
python factset_cli.py recover --github-actions --modernize-output

# Comprehensive v3.3.3 recovery
python factset_cli.py recover --v333-complete --fix-all-issues
```

## 🔄 v3.3.3 GitHub Actions Integration

### Modernized Workflow (Fixed Deprecated Warnings)

```yaml
# .github/workflows/Actions.yml (v3.3.3)
- name: 🚀 Execute v3.3.3 Final Pipeline  
  id: pipeline
  run: |
    python factset_cli.py pipeline \
      --mode=${{ inputs.execution_mode || 'intelligent' }} \
      --v333 --quality-scoring --github-actions
    
    # v3.3.3 Fixed: Use GITHUB_OUTPUT instead of deprecated set-output
    echo "quality_average=$(cat quality_metrics.json | jq .average_score)" >> $GITHUB_OUTPUT
    echo "github_raw_urls=$(cat link_stats.json | jq .urls_generated)" >> $GITHUB_OUTPUT
```

### v3.3.3 Workflow Features

- ✅ **GITHUB_OUTPUT Support**: Modern output handling (no deprecated warnings)
- ✅ **Quality Metrics**: Automatic quality score reporting  
- ✅ **GitHub Raw URLs**: Direct MD file link generation
- ✅ **Enhanced Artifacts**: Quality reports and link verification
- ✅ **Backward Compatibility**: All v3.3.2 features maintained

## 📈 v3.3.3 Performance & Monitoring

### Quality-Enhanced Performance

```bash
# v3.3.3 performance with quality metrics
python factset_cli.py performance --quality-analysis --detailed

# Memory monitoring with quality processing
python factset_cli.py analyze --memory --quality-overhead --optimization

# Cross-platform testing with v3.3.3 features
python factset_cli.py validate --cross-platform --v333-full-test
```

### v3.3.3 Monitoring Capabilities

- **🎯 Quality Scoring Performance**: Real-time quality calculation metrics
- **🔗 GitHub Raw URL Generation**: Link creation and validation timing
- **📊 Enhanced Statistics**: Quality distribution analysis
- **⚡ GitHub Actions Modernization**: Performance improvement tracking
- **🌐 Cross-platform Quality**: Consistent scoring across platforms

## 🔄 Migration from v3.3.2

### What's New in v3.3.3

| Aspect | v3.3.2 | v3.3.3 | Migration |
|--------|--------|--------|-----------|
| **Quality Scoring** | Basic scoring | 0-10 standardized | Auto-converts legacy scores |
| **GitHub Actions** | Basic support | Modernized (GITHUB_OUTPUT) | No action needed |
| **MD File Links** | Basic links | GitHub Raw URLs | Automatic enhancement |
| **Dashboard** | Standard | Live optimized | Improved performance |
| **Compatibility** | v3.3.2 features | All maintained + enhanced | Zero breaking changes |

### v3.3.2 → v3.3.3 Migration

```bash
# 1. Update repository
git pull origin main

# 2. No new dependencies required
pip install -r requirements.txt

# 3. Test v3.3.3 features
python factset_cli.py validate --test-v333 --quality-scoring

# 4. Run with v3.3.3 enhancements
python factset_cli.py pipeline --v333 --quality-scoring

# 5. Verify quality scoring
python factset_cli.py quality --analyze --distribution
```

**Migration Notes**: 
- ✅ All v3.3.2 commands work unchanged
- ✅ Quality scores auto-convert from legacy scale  
- ✅ GitHub Actions modernize automatically
- ✅ No configuration changes required

## 🤝 Contributing

### v3.3.3 Development Setup

```bash
# Clone and setup
git clone https://github.com/your-repo/factset-pipeline.git
cd factset-pipeline
pip install -r requirements-dev.txt

# Test v3.3.3 features
python factset_cli.py validate --test-v333 --quality-scoring --comprehensive

# Test quality scoring system
python factset_cli.py quality --benchmark --calibration-test

# Test GitHub Actions modernization
python factset_cli.py diagnose --github-actions --modern-test
```

### v3.3.3 Code Standards

- **🎯 Quality Integration**: All new features must support quality scoring
- **🔗 GitHub Raw URLs**: Use standardized link format for MD files  
- **⚡ GitHub Actions Compatibility**: Support GITHUB_OUTPUT format
- **📊 Enhanced Logging**: Integrate with quality metrics system
- **🌐 Cross-platform**: Maintain Windows/Linux/macOS compatibility

## 📊 Version Comparison

| Feature | v3.3.0 | v3.3.1 | v3.3.2 | v3.3.3 |
|---------|--------|--------|--------|--------|
| **Core Pipeline** | ✅ | ✅ | ✅ | ✅ |
| **Quality Scoring** | None | Basic | Enhanced | **Standardized 0-10** |
| **GitHub Actions** | Basic | Complex | Simplified | **Modernized** |
| **MD File Links** | Basic | Enhanced | Good | **GitHub Raw URLs** |
| **Cross-platform** | Partial | Good | Excellent | **Excellent** |
| **Logging** | Basic | Enhanced | Dual Output | **Quality Enhanced** |
| **Observability** | Limited | Good | Comprehensive | **Quality Focused** |
| **CLI Interface** | Mixed | Improved | Unified | **Quality Integrated** |
| **Dashboard** | Standard | Improved | Enhanced | **Live Optimized** |

## 🌟 v3.3.3 Final Features Summary

### ✨ What Makes v3.3.3 Special

- **🎯 Zero-to-Production Quality Scoring**: Complete 0-10 standardized system
- **🔗 One-Click MD File Access**: Direct GitHub Raw URL links  
- **⚡ Future-Proof GitHub Actions**: Modern GITHUB_OUTPUT support
- **📊 Live Dashboard Excellence**: Optimized real-time data display
- **🔄 100% Backward Compatibility**: All v3.3.2 + v3.3.1 features maintained
- **🌐 Cross-Platform Excellence**: Identical behavior across all platforms

### 🚀 Ready for Production

v3.3.3 represents the **Final Integrated Edition** - a production-ready system that combines all the best features from previous versions with cutting-edge enhancements for quality analysis, direct file access, and modern CI/CD integration.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Links

- **📊 Live Dashboard**: [Google Sheets Dashboard](https://docs.google.com/spreadsheets/d/your_sheet_id/edit) (v3.3.3 Optimized)
- **📖 Complete Guide**: [v3.3.3 Instructions](instructions.md)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-repo/factset-pipeline/issues)
- **🔗 GitHub Raw Files**: Direct MD file access via GitHub Raw URLs
- **🎯 Quality Reports**: Comprehensive 0-10 quality analysis

---

**Enhanced FactSet Pipeline v3.3.3 - Final Integrated Edition**

*Bringing together the best of financial data automation with standardized quality scoring, modern GitHub integration, and direct file access - all while maintaining complete backward compatibility.*

For questions or support, please [open an issue](https://github.com/your-repo/factset-pipeline/issues) or contact the development team.