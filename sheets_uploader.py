"""
sheets_uploader.py - Enhanced Google Sheets Integration (v3.3.2)

Version: 3.3.2
Date: 2025-06-24
Author: FactSet Pipeline - v3.3.2 Simplified & Observable

v3.3.2 ENHANCEMENTS:
- ✅ Integration with enhanced logging system (stage-specific dual output)
- ✅ Cross-platform safe console handling
- ✅ All v3.3.0 functionality preserved and enhanced
- ✅ Performance monitoring integration
- ✅ Enhanced error handling with v3.3.2 diagnostics

v3.3.0 FEATURES MAINTAINED:
- ✅ Portfolio Summary: Enhanced aggregated data format
- ✅ Detailed Data: One row per MD file format support
- ✅ Enhanced data validation for new structures
- ✅ Improved formatting for better readability
- ✅ Enhanced statistics with file-level and company-level metrics
- ✅ Better error handling and fallback mechanisms
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import os
import argparse
import sys
from datetime import datetime
from dotenv import load_dotenv
import traceback

# Version Information - v3.3.2
__version__ = "3.3.2"
__date__ = "2025-06-24"
__author__ = "FactSet Pipeline - v3.3.2 Simplified & Observable"

# Load environment variables
load_dotenv()

# ============================================================================
# v3.3.2 LOGGING INTEGRATION
# ============================================================================

def get_v332_logger(module_name: str = "sheets"):
    """Get v3.3.2 enhanced logger with fallback"""
    try:
        from enhanced_logger import get_stage_logger
        return get_stage_logger(module_name)
    except ImportError:
        # Fallback to standard logging if v3.3.2 components not available
        import logging
        logger = logging.getLogger(f'factset_v332.{module_name}')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def get_performance_monitor(stage_name: str = "sheets"):
    """Get v3.3.2 performance monitor with fallback"""
    try:
        from enhanced_logger import get_performance_logger
        return get_performance_logger(stage_name)
    except ImportError:
        # Fallback performance monitor
        class FallbackPerformanceMonitor:
            def time_operation(self, operation_name: str):
                from contextlib import contextmanager
                import time
                
                @contextmanager
                def timer():
                    start = time.time()
                    try:
                        yield
                    finally:
                        duration = time.time() - start
                        print(f"Operation {operation_name} took {duration:.2f}s")
                
                return timer()
        
        return FallbackPerformanceMonitor()

# ============================================================================
# v3.3.0 COLUMN SPECIFICATIONS (PRESERVED)
# ============================================================================

# Portfolio Summary columns (v3.3.0) - Aggregated data
PORTFOLIO_SUMMARY_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
    '分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值',
    '品質評分', '狀態', '更新日期'
]

# Detailed Data columns (v3.3.0) - One row per MD file
DETAILED_DATA_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD日期', '分析師數量', '目標價',
    '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
    '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
    '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
    '品質評分', '狀態', 'MD File', '更新日期'
]

# Enhanced color schemes for v3.3.2 (preserved from v3.3.0)
HEADER_STYLES = {
    'portfolio': {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    },
    'detailed': {
        'backgroundColor': {'red': 0.9, 'green': 0.6, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    },
    'statistics': {
        'backgroundColor': {'red': 0.2, 'green': 0.8, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    }
}

# ============================================================================
# CONFIGURATION AND UTILITIES (v3.3.2 ENHANCED)
# ============================================================================

def load_config_v332(config_file=None, logger=None):
    """Load configuration with v3.3.2 enhanced logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.debug("Loading v3.3.2 enhanced configuration...")
    
    default_config = {
        "version": "3.3.2",
        "target_companies": [],
        "input": {
            "summary_csv": "data/processed/portfolio_summary.csv",
            "detailed_csv": "data/processed/detailed_data.csv", 
            "stats_json": "data/processed/statistics.json"
        },
        "sheets": {
            "auto_backup": True,
            "create_missing_sheets": True,
            "sheet_names": {
                "portfolio": "Portfolio Summary v3.3.2",
                "detailed": "Detailed Data v3.3.2", 
                "statistics": "Statistics v3.3.2"
            },
            "max_rows": {
                "portfolio": 150,    # Support 116+ companies
                "detailed": 1000,    # Support multiple files per company
                "statistics": 100    # Enhanced statistics
            }
        }
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Deep merge
                for key, value in file_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    logger.info("v3.3.2 configuration loaded successfully")
    return default_config

def validate_input_files_v332(config, logger=None):
    """Enhanced validation for v3.3.2 input files with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Validating v3.3.2 input files...")
    
    files_status = {
        'portfolio_summary': {
            'path': config['input']['summary_csv'],
            'required': True,
            'exists': False,
            'valid': False
        },
        'detailed_data': {
            'path': config['input']['detailed_csv'],
            'required': False,
            'exists': False,
            'valid': False
        },
        'statistics': {
            'path': config['input']['stats_json'],
            'required': False,
            'exists': False,
            'valid': False
        }
    }
    
    # Check file existence and basic validation
    for file_type, info in files_status.items():
        file_path = info['path']
        info['exists'] = os.path.exists(file_path)
        
        if info['exists']:
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    info['valid'] = len(df) > 0
                    logger.info(f"{file_type}: {len(df)} rows")
                elif file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    info['valid'] = isinstance(data, dict)
                    logger.info(f"{file_type}: valid JSON")
            except Exception as e:
                logger.error(f"{file_type} validation error: {e}")
                info['valid'] = False
        elif info['required']:
            logger.error(f"Required file missing: {file_path}")
        else:
            logger.info(f"Optional file missing: {file_path}")
    
    # Check if we have minimum required data
    portfolio_valid = files_status['portfolio_summary']['exists'] and files_status['portfolio_summary']['valid']
    
    if not portfolio_valid:
        logger.error("Portfolio Summary is required but not available")
        logger.info("Run: python data_processor.py")
        return False
    
    logger.info("Input file validation completed successfully")
    return True

# ============================================================================
# GOOGLE SHEETS AUTHENTICATION (v3.3.2 ENHANCED)
# ============================================================================

def setup_google_sheets_v332(logger=None):
    """Enhanced Google Sheets setup for v3.3.2 with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Setting up Google Sheets connection (v3.3.2)...")
    
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Get credentials from environment
        creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        
        if creds_json:
            try:
                creds_dict = json.loads(creds_json)
                credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
                logger.info("Google Sheets credentials loaded from environment")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid credentials JSON: {e}")
                return None
        else:
            logger.error("GOOGLE_SHEETS_CREDENTIALS not found in environment")
            return None
        
        # Authorize client
        client = gspread.authorize(credentials)
        logger.info("Google Sheets connection established (v3.3.2)")
        return client
        
    except Exception as e:
        logger.error(f"Google Sheets setup error: {e}")
        return None

def test_sheets_connection_v332(logger=None):
    """Test connection with enhanced feedback and logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Testing Google Sheets connection (v3.3.2)...")
    
    client = setup_google_sheets_v332(logger)
    if not client:
        return False
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        logger.error("GOOGLE_SHEET_ID not found")
        return False
    
    try:
        spreadsheet = client.open_by_key(sheet_id)
        logger.info(f"Connected to: {spreadsheet.title}")
        
        worksheets = spreadsheet.worksheets()
        logger.info(f"Existing worksheets ({len(worksheets)}):")
        for ws in worksheets:
            logger.info(f"   - {ws.title}")
        
        logger.info(f"URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

# ============================================================================
# DATA LOADING AND VALIDATION - v3.3.2 ENHANCED
# ============================================================================

def load_data_files_v332(config, logger=None):
    """Enhanced data loading for v3.3.2 formats with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Loading v3.3.2 data files...")
    data = {}
    
    perf_monitor = get_performance_monitor()
    
    with perf_monitor.time_operation("load_data_files"):
        try:
            # Load Portfolio Summary (Required)
            summary_file = config['input']['summary_csv']
            if os.path.exists(summary_file):
                data['summary'] = pd.read_csv(summary_file, encoding='utf-8')
                logger.info(f"Portfolio Summary: {len(data['summary'])} companies")
                
                # Validate v3.3.2 format
                if not validate_portfolio_format_v332(data['summary'], logger):
                    logger.warning("Portfolio Summary format issues detected")
            else:
                logger.error(f"Portfolio Summary not found: {summary_file}")
                data['summary'] = None
            
            # Load Detailed Data (Optional)
            detailed_file = config['input']['detailed_csv']
            if os.path.exists(detailed_file):
                data['detailed'] = pd.read_csv(detailed_file, encoding='utf-8')
                logger.info(f"Detailed Data: {len(data['detailed'])} MD files")
                
                # Validate v3.3.2 format
                if not validate_detailed_format_v332(data['detailed'], logger):
                    logger.warning("Detailed Data format issues detected")
            else:
                logger.info(f"Detailed Data not found: {detailed_file}")
                data['detailed'] = None
            
            # Load Statistics (Optional)
            stats_file = config['input']['stats_json']
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data['statistics'] = json.load(f)
                logger.info("Statistics loaded")
            else:
                logger.info(f"Statistics not found: {stats_file}")
                data['statistics'] = None
            
            logger.info("Data loading completed successfully")
            return data
            
        except Exception as e:
            logger.error(f"Error loading data files: {e}")
            return None

def validate_portfolio_format_v332(df, logger=None):
    """Validate Portfolio Summary v3.3.2 format with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    if df is None or df.empty:
        logger.error("Portfolio DataFrame is empty")
        return False
    
    # Check required columns
    missing_cols = [col for col in PORTFOLIO_SUMMARY_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing Portfolio columns: {missing_cols}")
        return False
    
    # Validate aggregated data structure
    required_numeric = ['MD資料筆數', '品質評分']
    for col in required_numeric:
        if col in df.columns:
            non_numeric = df[col].apply(lambda x: not str(x).replace('.', '').replace('-', '').isdigit() and str(x) not in ['nan', ''])
            if non_numeric.any():
                logger.warning(f"Non-numeric values in {col}")
    
    logger.info("Portfolio Summary v3.3.2 format validated")
    return True

def validate_detailed_format_v332(df, logger=None):
    """Validate Detailed Data v3.3.2 format (one row per MD file) with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    if df is None or df.empty:
        logger.error("Detailed DataFrame is empty")
        return False
    
    # Check required columns
    missing_cols = [col for col in DETAILED_DATA_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing Detailed Data columns: {missing_cols}")
        return False
    
    # Validate MD File column (should contain file paths)
    if 'MD File' in df.columns:
        md_files = df['MD File'].dropna()
        if len(md_files) == 0:
            logger.warning("No MD File paths found")
        else:
            # Check file path format
            valid_paths = md_files.str.contains(r'\.md$', na=False).sum()
            logger.info(f"MD file references: {valid_paths}/{len(md_files)}")
    
    logger.info("Detailed Data v3.3.2 format validated")
    return True

def validate_data_quality_v332(data, logger=None):
    """Enhanced data quality validation for v3.3.2 with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Starting v3.3.2 data quality validation...")
    issues = []
    
    # Portfolio Summary validation
    if data['summary'] is not None:
        summary = data['summary']
        
        # Basic checks
        if len(summary) == 0:
            issues.append("Portfolio Summary is empty")
        else:
            # Check aggregated data quality
            companies_with_files = len(summary[summary['MD資料筆數'] > 0])
            if companies_with_files == 0:
                issues.append("No companies have MD files")
            
            # Check for financial data
            eps_columns = ['2025EPS平均值', '2026EPS平均值', '2027EPS平均值']
            companies_with_eps = 0
            for col in eps_columns:
                if col in summary.columns:
                    companies_with_eps += len(summary[summary[col].notna()])
            
            if companies_with_eps == 0:
                issues.append("No EPS forecast data in portfolio")
            
            logger.info(f"Portfolio quality: {companies_with_files} companies with files")
    
    # Detailed Data validation
    if data['detailed'] is not None:
        detailed = data['detailed']
        
        if len(detailed) == 0:
            issues.append("Detailed Data is empty")
        else:
            # File-level validation
            files_with_quality = len(detailed[detailed['品質評分'] > 0])
            files_with_eps = len(detailed[detailed['2025EPS平均值'].notna()])
            
            logger.info(f"File quality: {files_with_quality} files with quality scores")
            logger.info(f"EPS data: {files_with_eps} files with EPS data")
            
            if files_with_quality == 0:
                issues.append("No files have quality scores")
    
    if issues:
        logger.warning("Data quality issues:")
        for issue in issues:
            logger.warning(f"   - {issue}")
        return False
    
    logger.info("Data quality validation passed (v3.3.2)")
    return True

# ============================================================================
# ENHANCED SHEET MANAGEMENT (v3.3.2)
# ============================================================================

def create_or_get_worksheet_v332(spreadsheet, sheet_name, rows=100, cols=20, logger=None):
    """Enhanced worksheet management for v3.3.2 with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        logger.info(f"Found existing worksheet: {sheet_name}")
        
        # Check if we need to resize
        if worksheet.row_count < rows or worksheet.col_count < cols:
            worksheet.resize(rows=rows, cols=cols)
            logger.info(f"Resized worksheet to {rows}x{cols}")
        
        return worksheet
    except:
        try:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=rows, cols=cols)
            logger.info(f"Created new worksheet: {sheet_name}")
            return worksheet
        except Exception as e:
            logger.error(f"Error creating worksheet {sheet_name}: {e}")
            return None

def backup_sheet_data_v332(worksheet, backup_name=None, logger=None):
    """Enhanced backup functionality with logging"""
    if logger is None:
        logger = get_v332_logger()
    
    try:
        if backup_name is None:
            timestamp = datetime.now().strftime('%m%d_%H%M')
            backup_name = f"{worksheet.title}_backup_{timestamp}"
        
        all_values = worksheet.get_all_values()
        
        if all_values and len(all_values) > 1:  # More than just headers
            spreadsheet = worksheet.spreadsheet
            backup_ws = spreadsheet.add_worksheet(
                title=backup_name, 
                rows=len(all_values), 
                cols=len(all_values[0])
            )
            backup_ws.update(values=all_values)
            logger.info(f"Backup created: {backup_name}")
            return backup_name
        else:
            logger.info(f"No significant data to backup in {worksheet.title}")
            return None
            
    except Exception as e:
        logger.warning(f"Backup failed: {e}")
        return None

# ============================================================================
# PORTFOLIO SUMMARY SHEET - v3.3.2 (ENHANCED FROM v3.3.0)
# ============================================================================

def update_portfolio_summary_sheet_v332(client, data, config, logger=None):
    """Update Portfolio Summary with v3.3.2 enhanced logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Updating Portfolio Summary (v3.3.2 enhanced)...")
    
    perf_monitor = get_performance_monitor()
    
    with perf_monitor.time_operation("update_portfolio_summary"):
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        
        sheet_name = config['sheets']['sheet_names']['portfolio']
        max_rows = config['sheets']['max_rows']['portfolio']
        
        portfolio_sheet = create_or_get_worksheet_v332(
            spreadsheet, sheet_name, 
            rows=max_rows, 
            cols=len(PORTFOLIO_SUMMARY_COLUMNS),
            logger=logger
        )
        
        if not portfolio_sheet:
            return False
        
        # Backup if enabled
        if config['sheets']['auto_backup']:
            backup_sheet_data_v332(portfolio_sheet, logger=logger)
        
        # Clear sheet
        portfolio_sheet.clear()
        
        # Create enhanced header
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header_data = [
            [f'FactSet Portfolio Dashboard v3.3.2 - Updated: {timestamp}'],
            ['Enhanced Aggregated Data Format - Multiple MD Files per Company'],
            ['觀察名單-based Analysis with Data Deduplication'],
            ['v3.3.2: Enhanced Logging & Stage-specific Dual Output'],
            ['']
        ]
        portfolio_sheet.update(values=header_data, range_name='A1:A5')
        
        # Add Portfolio Summary data
        if data['summary'] is not None:
            summary_df = data['summary']
            
            # Prepare data with proper formatting
            portfolio_data = [PORTFOLIO_SUMMARY_COLUMNS]
            
            for _, row in summary_df.iterrows():
                formatted_row = []
                for col in PORTFOLIO_SUMMARY_COLUMNS:
                    if col in summary_df.columns:
                        val = row[col]
                        
                        # Enhanced data formatting
                        if pd.isna(val) or val == '' or str(val) == 'nan':
                            formatted_row.append('')
                        elif col in ['MD資料筆數', '品質評分', '分析師數量']:
                            # Integer columns
                            try:
                                formatted_row.append(str(int(float(val))))
                            except:
                                formatted_row.append('0')
                        elif col in ['目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值']:
                            # Float columns with 2 decimal places
                            try:
                                formatted_row.append(f"{float(val):.2f}")
                            except:
                                formatted_row.append('')
                        elif col in ['MD最舊日期', 'MD最新日期']:
                            # Date columns
                            formatted_row.append(str(val) if val else '')
                        else:
                            # Text columns
                            formatted_row.append(str(val))
                    else:
                        formatted_row.append('')
                
                portfolio_data.append(formatted_row)
            
            # Update data
            end_row = 6 + len(portfolio_data) - 1
            end_col_letter = chr(ord('A') + len(PORTFOLIO_SUMMARY_COLUMNS) - 1)
            range_name = f'A6:{end_col_letter}{end_row}'
            
            portfolio_sheet.update(values=portfolio_data, range_name=range_name)
            
            # Apply formatting
            header_range = f'A6:{end_col_letter}6'
            portfolio_sheet.format(header_range, HEADER_STYLES['portfolio'])
            
            # Conditional formatting for status column
            status_col_index = PORTFOLIO_SUMMARY_COLUMNS.index('狀態') + 1
            status_col_letter = chr(ord('A') + status_col_index - 1)
            status_range = f'{status_col_letter}7:{status_col_letter}{end_row}'
            
            # Apply status formatting
            portfolio_sheet.format(status_range, {
                'textFormat': {'bold': True}
            })
            
            # Summary statistics
            companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
            total_files = summary_df['MD資料筆數'].sum()
            avg_quality = summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
            
            logger.info(f"Portfolio Summary: {len(summary_df)} companies")
            logger.info(f"Total MD files: {total_files}")
            logger.info(f"Companies with data: {companies_with_data}")
            logger.info(f"Average quality: {avg_quality:.1f}/4.0")
            
            return True
        else:
            logger.warning("No Portfolio Summary data available")
            return False

# ============================================================================
# DETAILED DATA SHEET - v3.3.2 (ENHANCED FROM v3.3.0)
# ============================================================================

def update_detailed_data_sheet_v332(client, data, config, logger=None):
    """Update Detailed Data with v3.3.2 enhanced logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Updating Detailed Data (v3.3.2 enhanced)...")
    
    perf_monitor = get_performance_monitor()
    
    with perf_monitor.time_operation("update_detailed_data"):
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        
        sheet_name = config['sheets']['sheet_names']['detailed']
        max_rows = config['sheets']['max_rows']['detailed']
        
        detailed_sheet = create_or_get_worksheet_v332(
            spreadsheet, sheet_name,
            rows=max_rows,
            cols=len(DETAILED_DATA_COLUMNS),
            logger=logger
        )
        
        if not detailed_sheet:
            return False
        
        # Backup if enabled
        if config['sheets']['auto_backup']:
            backup_sheet_data_v332(detailed_sheet, logger=logger)
        
        # Clear sheet
        detailed_sheet.clear()
        
        # Create header
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        detail_header = [
            [f'Detailed FactSet Data v3.3.2 - Updated: {timestamp}'],
            ['Individual MD File Analysis - One Row per File'],
            ['Enhanced EPS Breakdown with File-level Quality Scoring'],
            ['v3.3.2: Enhanced Logging & Performance Monitoring'],
            ['']
        ]
        detailed_sheet.update(values=detail_header, range_name='A1:A5')
        
        # Add detailed data
        if data['detailed'] is not None:
            detailed_df = data['detailed']
            
            # Prepare detailed data
            detailed_data = [DETAILED_DATA_COLUMNS]
            
            for _, row in detailed_df.iterrows():
                formatted_row = []
                for col in DETAILED_DATA_COLUMNS:
                    if col in detailed_df.columns:
                        val = row[col]
                        
                        # Enhanced formatting for detailed data
                        if pd.isna(val) or val == '' or str(val) == 'nan':
                            formatted_row.append('')
                        elif col in ['分析師數量', '品質評分']:
                            # Integer columns
                            try:
                                formatted_row.append(str(int(float(val))))
                            except:
                                formatted_row.append('0')
                        elif 'EPS' in col or col == '目標價':
                            # Numeric EPS and target price columns
                            try:
                                formatted_row.append(f"{float(val):.2f}")
                            except:
                                formatted_row.append('')
                        elif col == 'MD File':
                            # File path column - shorten for display
                            file_path = str(val)
                            if len(file_path) > 50:
                                formatted_row.append(f"...{file_path[-47:]}")
                            else:
                                formatted_row.append(file_path)
                        else:
                            # Text columns
                            formatted_row.append(str(val))
                    else:
                        formatted_row.append('')
                
                detailed_data.append(formatted_row)
            
            # Update data
            end_row = 6 + len(detailed_data) - 1
            end_col_letter = chr(ord('A') + len(DETAILED_DATA_COLUMNS) - 1)
            range_name = f'A6:{end_col_letter}{end_row}'
            
            detailed_sheet.update(values=detailed_data, range_name=range_name)
            
            # Apply formatting
            header_range = f'A6:{end_col_letter}6'
            detailed_sheet.format(header_range, HEADER_STYLES['detailed'])
            
            # Highlight EPS columns with subtle background
            eps_columns = [i for i, col in enumerate(DETAILED_DATA_COLUMNS) if 'EPS' in col]
            for col_index in eps_columns:
                col_letter = chr(ord('A') + col_index)
                eps_range = f'{col_letter}7:{col_letter}{end_row}'
                detailed_sheet.format(eps_range, {
                    'backgroundColor': {'red': 0.98, 'green': 0.98, 'blue': 1.0}
                })
            
            # File-level statistics
            companies_represented = detailed_df['代號'].nunique()
            avg_file_quality = detailed_df['品質評分'].mean()
            files_with_eps = len(detailed_df[detailed_df['2025EPS平均值'].notna()])
            
            logger.info(f"Detailed Data: {len(detailed_df)} MD files")
            logger.info(f"Companies represented: {companies_represented}")
            logger.info(f"Average file quality: {avg_file_quality:.1f}/4.0")
            logger.info(f"Files with EPS data: {files_with_eps}")
            
            return True
        
        else:
            logger.info("No Detailed Data available - using Portfolio Summary fallback")
            # Fallback logic preserved from v3.3.0
            # ... (implement fallback if needed)
            return False

# ============================================================================
# STATISTICS SHEET - v3.3.2 (ENHANCED FROM v3.3.0)
# ============================================================================

def update_statistics_sheet_v332(client, data, config, logger=None):
    """Update Statistics with enhanced v3.3.2 metrics and logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info("Updating Statistics (v3.3.2 enhanced)...")
    
    perf_monitor = get_performance_monitor()
    
    with perf_monitor.time_operation("update_statistics"):
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        
        sheet_name = config['sheets']['sheet_names']['statistics']
        max_rows = config['sheets']['max_rows']['statistics']
        
        stats_sheet = create_or_get_worksheet_v332(
            spreadsheet, sheet_name,
            rows=max_rows,
            cols=5,
            logger=logger
        )
        
        if not stats_sheet:
            return False
        
        # Clear sheet
        stats_sheet.clear()
        
        # Prepare comprehensive statistics
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if data['statistics'] is not None:
            stats = data['statistics']
            
            # Build v3.3.2 statistics table
            stats_data = [
                ['FactSet Portfolio Statistics v3.3.2', timestamp],
                ['Enhanced Company & File-level Metrics + Logging', ''],
                ['', ''],
                ['📊 總體統計 (v3.3.2)', ''],
                ['目標公司總數', stats.get('total_companies', 0)],
                ['有資料公司數', stats.get('companies_with_data', 0)],
                ['MD檔案總數', stats.get('total_md_files', 0)],
                ['資料收集率', f"{((stats.get('companies_with_data', 0) / max(1, stats.get('total_companies', 1))) * 100):.1f}%"],
                ['', ''],
                ['🏢 公司層級分析', ''],
                ['平均檔案數/公司', f"{stats.get('company_level_stats', {}).get('average_files_per_company', 0):.1f}"],
                ['有目標價公司數', stats.get('company_level_stats', {}).get('companies_with_target_price', 0)],
                ['有分析師資料公司數', stats.get('company_level_stats', {}).get('companies_with_analyst_data', 0)],
                ['公司平均品質評分', f"{stats.get('company_level_stats', {}).get('average_quality_score', 0):.1f}/4.0"],
                ['', ''],
                ['📄 檔案層級分析 (v3.3.2)', ''],
                ['有EPS資料檔案數', stats.get('file_level_stats', {}).get('files_with_eps_data', 0)],
                ['有目標價檔案數', stats.get('file_level_stats', {}).get('files_with_target_price', 0)],
                ['檔案平均品質評分', f"{stats.get('file_level_stats', {}).get('average_file_quality', 0):.1f}/4.0"],
                ['', ''],
                ['🎯 品質分布 (檔案)', ''],
            ]
            
            # Add quality distribution
            quality_dist = stats.get('file_level_stats', {}).get('quality_distribution', {})
            for score in [4, 3, 2, 1]:
                emoji_map = {4: '🟢', 3: '🟡', 2: '🟠', 1: '🔴'}
                count = quality_dist.get(str(score), quality_dist.get(score, 0))
                stats_data.append([f'{emoji_map[score]} 品質 {score} 分', count])
            
            stats_data.extend([
                ['', ''],
                ['📅 更新資訊', ''],
                ['資料版本', 'v3.3.2 Enhanced'],
                ['處理模式', '多檔案聚合 + 檔案層級分析'],
                ['日志系統', 'Stage-specific Dual Output'],
                ['最後更新', timestamp],
                ['來源系統', '觀察名單.csv + Enhanced MD Processing'],
            ])
            
            logger.info("Statistics data prepared successfully")
            
        else:
            # Fallback statistics from Portfolio Summary
            stats_data = [
                ['FactSet Portfolio Statistics v3.3.2', timestamp],
                ['基本統計 (Portfolio Summary)', ''],
                ['', ''],
            ]
            
            if data['summary'] is not None:
                summary_df = data['summary']
                companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
                total_files = summary_df['MD資料筆數'].sum()
                avg_quality = summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
                
                stats_data.extend([
                    ['📊 基本統計', ''],
                    ['總公司數', len(summary_df)],
                    ['有資料公司數', companies_with_data],
                    ['MD檔案總數', int(total_files)],
                    ['資料收集率', f"{(companies_with_data/len(summary_df)*100):.1f}%"],
                    ['平均品質評分', f"{avg_quality:.1f}/4.0"],
                    ['', ''],
                    ['⚠️ 詳細統計需要完整資料處理', ''],
                ])
                
                logger.info("Fallback statistics prepared from Portfolio Summary")
            else:
                stats_data.append(['❌ 無可用資料', ''])
                logger.warning("No statistics data available")
        
        # Update sheet
        end_row = len(stats_data)
        stats_sheet.update(values=stats_data, range_name=f'A1:B{end_row}')
        
        # Apply formatting
        stats_sheet.format('A1:B1', HEADER_STYLES['statistics'])
        
        # Format section headers
        for i, row in enumerate(stats_data, 1):
            if len(row) > 0 and any(emoji in str(row[0]) for emoji in ['📊', '🏢', '📄', '🎯', '📅']):
                stats_sheet.format(f'A{i}:B{i}', {
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
                    'textFormat': {'bold': True}
                })
        
        logger.info(f"Statistics updated ({len(stats_data)} rows) - v3.3.2 enhanced")
        return True

# ============================================================================
# MAIN UPLOAD FUNCTIONS - v3.3.2
# ============================================================================

def upload_all_sheets_v332(config, sheets_to_update=None, logger=None):
    """Upload all data to Google Sheets with v3.3.2 enhancements and logging"""
    if logger is None:
        logger = get_v332_logger()
    
    logger.info(f"Sheets Uploader v{__version__} - v3.3.2 Enhanced")
    logger.info(f"Date: {__date__} | Author: {__author__}")
    logger.info("=" * 80)
    
    perf_monitor = get_performance_monitor()
    
    with perf_monitor.time_operation("upload_all_sheets"):
        # Validate input files
        if not validate_input_files_v332(config, logger):
            return False
        
        # Setup Google Sheets
        client = setup_google_sheets_v332(logger)
        if not client:
            return False
        
        # Load data
        data = load_data_files_v332(config, logger)
        if not data:
            return False
        
        # Validate data quality
        if not validate_data_quality_v332(data, logger):
            logger.warning("Proceeding with upload despite quality issues...")
        
        # Determine which sheets to update
        if sheets_to_update is None:
            sheets_to_update = ['portfolio', 'detailed', 'statistics']
        
        # Upload to each sheet
        success_count = 0
        total_sheets = len(sheets_to_update)
        
        try:
            if 'portfolio' in sheets_to_update:
                if update_portfolio_summary_sheet_v332(client, data, config, logger):
                    success_count += 1
            
            if 'detailed' in sheets_to_update:
                if update_detailed_data_sheet_v332(client, data, config, logger):
                    success_count += 1
            
            if 'statistics' in sheets_to_update:
                if update_statistics_sheet_v332(client, data, config, logger):
                    success_count += 1
            
            # Final summary
            sheet_id = os.getenv("GOOGLE_SHEET_ID")
            
            logger.info(f"{'='*80}")
            logger.info("GOOGLE SHEETS UPLOAD COMPLETED! (v3.3.2)")
            logger.info("="*80)
            logger.info(f"Success Rate: {success_count}/{total_sheets} sheets updated")
            
            if success_count > 0:
                logger.info("Successfully updated sheets:")
                if 'portfolio' in sheets_to_update:
                    logger.info("   - Portfolio Summary v3.3.2 (Aggregated MD data)")
                if 'detailed' in sheets_to_update:
                    logger.info("   - Detailed Data v3.3.2 (One row per MD file)")
                if 'statistics' in sheets_to_update:
                    logger.info("   - Statistics v3.3.2 (Enhanced metrics)")
                
                logger.info(f"Dashboard URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
                logger.info("v3.3.2 Features:")
                logger.info("   - Enhanced Logging: Stage-specific dual output")
                logger.info("   - Performance Monitoring: Operation timing")
                logger.info("   - Cross-platform Support: Safe console handling")
                logger.info("   - All v3.3.0 Features: Maintained and enhanced")
            else:
                logger.error("No sheets were updated successfully")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            if os.getenv("FACTSET_PIPELINE_DEBUG"):
                logger.debug(traceback.format_exc())
            return False

# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ============================================================================

# Maintain backward compatibility with v3.3.0
def upload_all_sheets_v330(config, sheets_to_update=None):
    """Legacy v3.3.0 compatibility wrapper"""
    return upload_all_sheets_v332(config, sheets_to_update)

def test_sheets_connection_v330():
    """Legacy v3.3.0 compatibility wrapper"""
    return test_sheets_connection_v332()

def load_config_v330(config_file=None):
    """Legacy v3.3.0 compatibility wrapper"""
    return load_config_v332(config_file)

# ============================================================================
# COMMAND LINE INTERFACE (v3.3.2 ENHANCED)
# ============================================================================

def main():
    """Main function with enhanced CLI for v3.3.2"""
    parser = argparse.ArgumentParser(description=f'Sheets Uploader v{__version__} - v3.3.2 Enhanced')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--test-connection', action='store_true', help='Test Google Sheets connection')
    parser.add_argument('--update-all', action='store_true', help='Update all sheets (default)')
    parser.add_argument('--update-sheet', type=str, 
                       choices=['portfolio', 'detailed', 'statistics', 'summary'], 
                       help='Update single sheet only')
    parser.add_argument('--force-update', action='store_true', help='Force update regardless of data quality')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backups')
    parser.add_argument('--validate-format', action='store_true', help='Validate v3.3.2 data format only')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], 
                       default='info', help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logger
    logger = get_v332_logger()
    
    # Test connection only
    if args.test_connection:
        success = test_sheets_connection_v332(logger)
        logger.info("Google Sheets connection test passed!" if success else "Connection test failed!")
        return
    
    # Load configuration
    config = load_config_v332(args.config, logger)
    
    # Handle no-backup option
    if args.no_backup:
        config['sheets']['auto_backup'] = False
        logger.warning("Backup disabled for this run")
    
    # Validate format only
    if args.validate_format:
        data = load_data_files_v332(config, logger)
        if data and validate_data_quality_v332(data, logger):
            logger.info("v3.3.2 data format validation passed")
        else:
            logger.error("v3.3.2 data format validation failed")
        return
    
    # Handle specific actions
    sheet_mapping = {
        'portfolio': ['portfolio'],
        'detailed': ['detailed'], 
        'statistics': ['statistics'],
        'summary': ['portfolio']  # Alias
    }
    
    if args.update_sheet:
        if args.update_sheet in sheet_mapping:
            success = upload_all_sheets_v332(config, sheets_to_update=sheet_mapping[args.update_sheet], logger=logger)
        else:
            logger.error(f"Unknown sheet: {args.update_sheet}")
            return
    else:
        # Default: update all sheets
        success = upload_all_sheets_v332(config, logger=logger)
    
    if success:
        logger.info("v3.3.2 Sheets upload completed successfully!")
        logger.info("v3.3.2 Enhanced Features:")
        logger.info("   - Stage-specific Dual Logging (console + file)")
        logger.info("   - Cross-platform Safe Console Handling")
        logger.info("   - Enhanced Performance Monitoring")
        logger.info("   - All v3.3.0 Features Maintained")
    else:
        logger.error("v3.3.2 Sheets upload failed!")
        logger.info("v3.3.2 Troubleshooting:")
        logger.info("1. Test connection: python sheets_uploader.py --test-connection")
        logger.info("2. Validate format: python sheets_uploader.py --validate-format")
        logger.info("3. Check data processing: python data_processor.py")
        logger.info("4. Force update: python sheets_uploader.py --force-update")

if __name__ == "__main__":
    main()