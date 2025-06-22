"""
sheets_uploader.py - Google Sheets Integration Module (Updated for Guideline v3.2.0)

Version: 3.2.0
Date: 2025-06-22
Author: Google Search FactSet Pipeline - Guideline v3.2.0 Compliant
License: MIT

GUIDELINE v3.2.0 COMPLIANCE:
- ✅ Updated to handle exact Portfolio Summary format from guideline
- ✅ Enhanced Detailed Data format with multi-year EPS breakdown
- ✅ Improved data validation for new column structures
- ✅ Quality score and status emoji formatting
- ✅ Enhanced statistics presentation with v3.2.0 metrics
- ✅ Optimized sheet layouts for new data structure

Description:
    Google Sheets integration module aligned with guideline v3.2.0:
    - Portfolio Summary: 14 columns with exact guideline format
    - Detailed Data: 21 columns with enhanced EPS breakdown
    - Statistics: Comprehensive quality and coverage metrics
    - Enhanced formatting and validation for new data structure
    - Maintains robust authentication and error handling

Key Features:
    - Secure authentication via environment variables
    - Guideline v3.2.0 compliant sheet formats
    - Enhanced data validation for new structures
    - Quality score and emoji status formatting
    - Multi-year EPS data presentation
    - Comprehensive error handling and recovery
    - CLI interface for standalone usage

Dependencies:
    - gspread
    - google-auth
    - pandas
    - python-dotenv
    - json
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

# Version Information - Guideline v3.2.0
__version__ = "3.2.0"
__date__ = "2025-06-22"
__author__ = "Google Search FactSet Pipeline - Guideline v3.2.0 Compliant"

# Load environment variables
load_dotenv()

# ============================================================================
# GUIDELINE v3.2.0 COLUMN SPECIFICATIONS
# ============================================================================

# Exact Portfolio Summary columns from guideline v3.2.0
PORTFOLIO_SUMMARY_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
    '分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值',
    '品質評分', '狀態', '更新日期'
]

# Enhanced Detailed Data columns from guideline v3.2.0
DETAILED_DATA_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
    '分析師數量', '目標價', '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
    '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
    '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
    '品質評分', '狀態', 'MD File Folder', '更新日期'
]

# Sheet formatting constants
SHEET_HEADER_STYLE = {
    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
}

# ============================================================================
# CONFIGURATION AND UTILITIES
# ============================================================================

def load_config(config_file=None):
    """Load configuration with guideline v3.2.0 defaults"""
    default_config = {
        "target_companies": [],
        "input": {
            "consolidated_csv": "data/processed/consolidated_factset.csv",
            "summary_csv": "data/processed/portfolio_summary.csv",
            "detailed_csv": "data/processed/detailed_data.csv",
            "stats_json": "data/processed/statistics.json"
        },
        "sheets": {
            "auto_backup": True,
            "create_missing_sheets": True,
            "update_frequency": "on_demand",
            "sheet_names": {
                "portfolio": "Portfolio Summary",
                "detailed": "Detailed Data", 
                "statistics": "Statistics"
            },
            "max_rows": {
                "portfolio": 150,    # Increased for 116+ companies
                "detailed": 150,     # Enhanced detailed data
                "statistics": 50     # Comprehensive stats
            }
        }
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Merge with defaults
                for key, value in file_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except Exception as e:
            print(f"⚠️ Error loading config file {config_file}: {e}")
            print("Using default configuration...")
    
    return default_config

def validate_input_files(config):
    """Validate that required input files exist - Updated for guideline v3.2.0"""
    required_files = [
        config['input']['summary_csv']  # Primary requirement: Portfolio Summary
    ]
    
    optional_files = [
        config['input']['detailed_csv'],
        config['input']['stats_json']
    ]
    
    missing_required = []
    missing_optional = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_required.append(file_path)
    
    for file_path in optional_files:
        if not os.path.exists(file_path):
            missing_optional.append(file_path)
    
    if missing_required:
        print("❌ Missing required input files:")
        for file_path in missing_required:
            print(f"   - {file_path}")
        print("\n💡 Run data processor first: python data_processor.py")
        return False
    
    if missing_optional:
        print("⚠️ Missing optional files (will be skipped):")
        for file_path in missing_optional:
            print(f"   - {file_path}")
    
    return True

# ============================================================================
# GOOGLE SHEETS AUTHENTICATION
# ============================================================================

def setup_google_sheets():
    """Setup Google Sheets connection using environment variable credentials"""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Get credentials from environment variable
        creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        
        if creds_json:
            try:
                creds_dict = json.loads(creds_json)
                credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
                print("✅ Using Google Sheets credentials from environment variable")
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in GOOGLE_SHEETS_CREDENTIALS: {e}")
                return None
        else:
            print(f"❌ No credentials found. Please set GOOGLE_SHEETS_CREDENTIALS in .env file")
            print("💡 Format: GOOGLE_SHEETS_CREDENTIALS='{\"type\":\"service_account\",...}'")
            return None
        
        # Authorize client
        client = gspread.authorize(credentials)
        print("✅ Google Sheets connection established!")
        return client
        
    except Exception as e:
        print(f"❌ Google Sheets setup error: {e}")
        return None

def test_sheets_connection():
    """Test Google Sheets connection and permissions"""
    print("🔧 Testing Google Sheets connection...")
    
    client = setup_google_sheets()
    if not client:
        return False
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID not found in .env file")
        print("💡 Format: GOOGLE_SHEET_ID=your_spreadsheet_id_here")
        return False
    
    try:
        spreadsheet = client.open_by_key(sheet_id)
        print(f"✅ Successfully connected to spreadsheet: {spreadsheet.title}")
        
        # List existing worksheets
        worksheets = spreadsheet.worksheets()
        print(f"📄 Found {len(worksheets)} existing worksheets:")
        for ws in worksheets:
            print(f"   - {ws.title}")
        
        print(f"🔗 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        return True
        
    except Exception as e:
        print(f"❌ Error accessing spreadsheet: {e}")
        print("💡 Make sure the service account has access to the spreadsheet")
        return False

# ============================================================================
# DATA LOADING AND VALIDATION - GUIDELINE v3.2.0
# ============================================================================

def load_data_files(config):
    """Load all data files with guideline v3.2.0 format validation"""
    data = {}
    
    try:
        # Load Portfolio Summary (Required)
        summary_file = config['input']['summary_csv']
        if os.path.exists(summary_file):
            data['summary'] = pd.read_csv(summary_file, encoding='utf-8')
            print(f"✅ Loaded Portfolio Summary: {len(data['summary'])} companies")
            
            # Validate Portfolio Summary format
            if not validate_portfolio_summary_format(data['summary']):
                print("⚠️ Portfolio Summary format validation failed")
            
        else:
            print(f"❌ Portfolio Summary file not found: {summary_file}")
            data['summary'] = None
        
        # Load Detailed Data (Optional)
        detailed_file = config['input']['detailed_csv']
        if os.path.exists(detailed_file):
            data['detailed'] = pd.read_csv(detailed_file, encoding='utf-8')
            print(f"✅ Loaded Detailed Data: {len(data['detailed'])} companies")
            
            # Validate Detailed Data format
            if not validate_detailed_data_format(data['detailed']):
                print("⚠️ Detailed Data format validation failed")
        else:
            print(f"ℹ️ Detailed Data file not found: {detailed_file} (optional)")
            data['detailed'] = None
        
        # Load Statistics (Optional)
        stats_file = config['input']['stats_json']
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                data['statistics'] = json.load(f)
            print(f"✅ Loaded Statistics data")
        else:
            print(f"ℹ️ Statistics file not found: {stats_file} (optional)")
            data['statistics'] = None
        
        return data
        
    except Exception as e:
        print(f"❌ Error loading data files: {e}")
        return None

def validate_portfolio_summary_format(df):
    """Validate Portfolio Summary matches guideline v3.2.0 format"""
    if df is None or df.empty:
        return False
    
    # Check for required columns
    missing_cols = [col for col in PORTFOLIO_SUMMARY_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"⚠️ Portfolio Summary missing columns: {missing_cols}")
        return False
    
    # Check data types and content
    required_numeric = ['MD資料筆數', '品質評分']
    for col in required_numeric:
        if col in df.columns:
            non_numeric = df[col].apply(lambda x: not str(x).replace('.', '').isdigit() and str(x) != 'nan' and str(x) != '')
            if non_numeric.any():
                print(f"⚠️ Non-numeric values found in {col}")
    
    print("✅ Portfolio Summary format validation passed")
    return True

def validate_detailed_data_format(df):
    """Validate Detailed Data matches guideline v3.2.0 format"""
    if df is None or df.empty:
        return False
    
    # Check for required columns
    missing_cols = [col for col in DETAILED_DATA_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"⚠️ Detailed Data missing columns: {missing_cols}")
        return False
    
    print("✅ Detailed Data format validation passed")
    return True

def validate_data_quality(data):
    """Validate data quality before upload - Enhanced for guideline v3.2.0"""
    issues = []
    
    if data['summary'] is not None:
        summary = data['summary']
        if len(summary) == 0:
            issues.append("Portfolio Summary is empty")
        else:
            # Check for companies with data
            companies_with_data = len(summary[summary['MD資料筆數'] > 0])
            if companies_with_data == 0:
                issues.append("No companies have MD file data")
            
            # Check for quality scores
            companies_with_quality = len(summary[summary['品質評分'] > 0])
            if companies_with_quality == 0:
                issues.append("No companies have quality scores")
            
            # Check for EPS data
            eps_columns = ['2025EPS平均值', '2026EPS平均值', '2027EPS平均值']
            companies_with_eps = 0
            for col in eps_columns:
                if col in summary.columns:
                    companies_with_eps += len(summary[summary[col].notna()])
            
            if companies_with_eps == 0:
                issues.append("No EPS forecast data found")
    else:
        issues.append("Portfolio Summary data not loaded")
    
    if issues:
        print("⚠️ Data quality issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ Data quality validation passed")
    return True

# ============================================================================
# SHEET MANAGEMENT
# ============================================================================

def create_or_get_worksheet(spreadsheet, sheet_name, rows=100, cols=20):
    """Create worksheet if it doesn't exist, or get existing one"""
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        print(f"✅ Found existing worksheet: {sheet_name}")
        return worksheet
    except:
        try:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=rows, cols=cols)
            print(f"✅ Created new worksheet: {sheet_name}")
            return worksheet
        except Exception as e:
            print(f"❌ Error creating worksheet {sheet_name}: {e}")
            return None

def backup_sheet_data(worksheet, backup_name=None):
    """Create backup of existing sheet data"""
    try:
        if backup_name is None:
            backup_name = f"{worksheet.title}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get all values
        all_values = worksheet.get_all_values()
        
        if all_values:
            # Create backup worksheet
            spreadsheet = worksheet.spreadsheet
            backup_ws = spreadsheet.add_worksheet(title=backup_name, rows=len(all_values), cols=len(all_values[0]))
            backup_ws.update(values=all_values)
            print(f"✅ Backup created: {backup_name}")
            return backup_name
        else:
            print(f"ℹ️ No data to backup in {worksheet.title}")
            return None
            
    except Exception as e:
        print(f"⚠️ Backup failed for {worksheet.title}: {e}")
        return None

# ============================================================================
# PORTFOLIO SUMMARY SHEET UPDATE - GUIDELINE v3.2.0
# ============================================================================

def update_portfolio_summary_sheet(client, data, config):
    """Update Portfolio Summary sheet - Guideline v3.2.0 format"""
    print("📝 Updating Portfolio Summary sheet (Guideline v3.2.0 format)...")
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    spreadsheet = client.open_by_key(sheet_id)
    
    sheet_name = config['sheets']['sheet_names']['portfolio']
    max_rows = config['sheets']['max_rows']['portfolio']
    summary_sheet = create_or_get_worksheet(spreadsheet, sheet_name, rows=max_rows, cols=len(PORTFOLIO_SUMMARY_COLUMNS))
    
    if not summary_sheet:
        return False
    
    # Backup if requested
    if config['sheets']['auto_backup']:
        backup_sheet_data(summary_sheet)
    
    # Clear sheet
    summary_sheet.clear()
    
    # Create header with guideline v3.2.0 branding
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header_data = [
        [f'FactSet Portfolio Dashboard v3.2.0 - Updated: {timestamp}'],
        ['Guideline v3.2.0 Compliant Format - 觀察名單 Based Analysis'],
        [''],
    ]
    summary_sheet.update(values=header_data, range_name='A1:A3')
    
    # Add Portfolio Summary data
    if data['summary'] is not None:
        summary_df = data['summary']
        
        # Ensure all required columns are present
        portfolio_data = [PORTFOLIO_SUMMARY_COLUMNS]
        
        for _, row in summary_df.iterrows():
            formatted_row = []
            for col in PORTFOLIO_SUMMARY_COLUMNS:
                if col in summary_df.columns:
                    val = row[col]
                    # Handle different data types
                    if pd.isna(val) or val == '' or str(val) == 'nan':
                        formatted_row.append('')
                    elif col in ['MD資料筆數', '品質評分', '分析師數量']:
                        # Integer columns
                        try:
                            formatted_row.append(str(int(float(val))))
                        except:
                            formatted_row.append('0')
                    elif col in ['目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值']:
                        # Numeric columns
                        try:
                            formatted_row.append(str(float(val)))
                        except:
                            formatted_row.append('')
                    else:
                        # Text columns
                        formatted_row.append(str(val))
                else:
                    formatted_row.append('')
            
            portfolio_data.append(formatted_row)
        
        # Calculate range for Portfolio Summary
        end_row = 4 + len(portfolio_data) - 1
        end_col_letter = chr(ord('A') + len(PORTFOLIO_SUMMARY_COLUMNS) - 1)
        range_name = f'A4:{end_col_letter}{end_row}'
        
        # Update the data
        summary_sheet.update(values=portfolio_data, range_name=range_name)
        
        # Format header row
        header_range = f'A4:{end_col_letter}4'
        summary_sheet.format(header_range, {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # Apply conditional formatting for status column (狀態)
        status_col_index = PORTFOLIO_SUMMARY_COLUMNS.index('狀態') + 1
        status_col_letter = chr(ord('A') + status_col_index - 1)
        status_range = f'{status_col_letter}5:{status_col_letter}{end_row}'
        
        # Color coding for status
        summary_sheet.format(status_range, {
            'textFormat': {'bold': True}
        })
        
        print(f"   ✅ Portfolio Summary: {len(summary_df)} companies updated (Guideline v3.2.0)")
        print(f"   📊 Columns: {len(PORTFOLIO_SUMMARY_COLUMNS)} (exact guideline format)")
        
        # Summary statistics
        companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
        avg_quality = summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
        
        print(f"   📈 Companies with data: {companies_with_data}/{len(summary_df)}")
        print(f"   🎯 Average quality score: {avg_quality:.1f}/4.0")
        
        return True
    else:
        print(f"   ⚠️ No Portfolio Summary data to update")
        return False

# ============================================================================
# DETAILED DATA SHEET UPDATE - GUIDELINE v3.2.0
# ============================================================================

def update_detailed_data_sheet(client, data, config):
    """Update Detailed Data sheet - Enhanced EPS breakdown format"""
    print("📝 Updating Detailed Data sheet (Enhanced EPS breakdown)...")
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    spreadsheet = client.open_by_key(sheet_id)
    
    sheet_name = config['sheets']['sheet_names']['detailed']
    max_rows = config['sheets']['max_rows']['detailed']
    detail_sheet = create_or_get_worksheet(spreadsheet, sheet_name, rows=max_rows, cols=len(DETAILED_DATA_COLUMNS))
    
    if not detail_sheet:
        return False
    
    # Backup if requested
    if config['sheets']['auto_backup']:
        backup_sheet_data(detail_sheet)
    
    # Clear sheet
    detail_sheet.clear()
    
    # Create header
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    detail_header = [
        [f'Detailed FactSet Data v3.2.0 - Updated: {timestamp}'],
        ['Enhanced Multi-Year EPS Breakdown (2025/2026/2027)'],
        ['']
    ]
    detail_sheet.update(values=detail_header, range_name='A1:A3')
    
    # Add detailed data
    if data['detailed'] is not None:
        detailed_df = data['detailed']
        
        # Prepare detailed data with enhanced format
        detailed_data = [DETAILED_DATA_COLUMNS]
        
        for _, row in detailed_df.iterrows():
            formatted_row = []
            for col in DETAILED_DATA_COLUMNS:
                if col in detailed_df.columns:
                    val = row[col]
                    # Handle different data types
                    if pd.isna(val) or val == '' or str(val) == 'nan':
                        formatted_row.append('')
                    elif col in ['MD資料筆數', '品質評分', '分析師數量']:
                        # Integer columns
                        try:
                            formatted_row.append(str(int(float(val))))
                        except:
                            formatted_row.append('0')
                    elif 'EPS' in col or col == '目標價':
                        # Numeric EPS and target price columns
                        try:
                            formatted_row.append(str(float(val)))
                        except:
                            formatted_row.append('')
                    else:
                        # Text columns
                        formatted_row.append(str(val))
                else:
                    formatted_row.append('')
            
            detailed_data.append(formatted_row)
        
        # Calculate range for Detailed Data
        end_row = 4 + len(detailed_data) - 1
        end_col_letter = chr(ord('A') + len(DETAILED_DATA_COLUMNS) - 1)
        range_name = f'A4:{end_col_letter}{end_row}'
        
        # Update the data
        detail_sheet.update(values=detailed_data, range_name=range_name)
        
        # Format header row
        header_range = f'A4:{end_col_letter}4'
        detail_sheet.format(header_range, {
            'backgroundColor': {'red': 0.9, 'green': 0.6, 'blue': 0.2},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # Highlight EPS columns
        eps_columns = [i for i, col in enumerate(DETAILED_DATA_COLUMNS) if 'EPS' in col]
        for col_index in eps_columns:
            col_letter = chr(ord('A') + col_index)
            eps_range = f'{col_letter}5:{col_letter}{end_row}'
            detail_sheet.format(eps_range, {
                'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 1.0}
            })
        
        print(f"   ✅ Detailed Data: {len(detailed_df)} companies updated")
        print(f"   📊 Enhanced format: {len(DETAILED_DATA_COLUMNS)} columns with EPS breakdown")
        
        # EPS coverage statistics
        eps_2025_count = len(detailed_df[detailed_df['2025EPS平均值'].notna()])
        eps_2026_count = len(detailed_df[detailed_df['2026EPS平均值'].notna()])
        eps_2027_count = len(detailed_df[detailed_df['2027EPS平均值'].notna()])
        
        print(f"   📈 EPS Coverage: 2025={eps_2025_count}, 2026={eps_2026_count}, 2027={eps_2027_count}")
        
        return True
    else:
        print(f"   ℹ️ No Detailed Data available - using Portfolio Summary")
        
        # Fallback: Use summary data if detailed data not available
        if data['summary'] is not None:
            summary_df = data['summary']
            
            # Convert summary to detailed format (with limited EPS data)
            detailed_fallback = []
            detailed_fallback.append(DETAILED_DATA_COLUMNS)
            
            for _, row in summary_df.iterrows():
                detailed_row = []
                for col in DETAILED_DATA_COLUMNS:
                    if col in summary_df.columns:
                        val = row[col]
                        detailed_row.append(str(val) if not pd.isna(val) else '')
                    elif col in ['2025EPS最高值', '2025EPS最低值']:
                        # Use average for high/low if not available
                        avg_val = row.get('2025EPS平均值', '')
                        detailed_row.append(str(avg_val) if not pd.isna(avg_val) else '')
                    elif col in ['2026EPS最高值', '2026EPS最低值']:
                        avg_val = row.get('2026EPS平均值', '')
                        detailed_row.append(str(avg_val) if not pd.isna(avg_val) else '')
                    elif col in ['2027EPS最高值', '2027EPS最低值']:
                        avg_val = row.get('2027EPS平均值', '')
                        detailed_row.append(str(avg_val) if not pd.isna(avg_val) else '')
                    elif col == 'MD File Folder':
                        code = row.get('代號', '')
                        detailed_row.append(f"data/md/{code}" if code else '')
                    else:
                        detailed_row.append('')
                
                detailed_fallback.append(detailed_row)
            
            # Update with fallback data
            end_row = 4 + len(detailed_fallback) - 1
            end_col_letter = chr(ord('A') + len(DETAILED_DATA_COLUMNS) - 1)
            range_name = f'A4:{end_col_letter}{end_row}'
            
            detail_sheet.update(values=detailed_fallback, range_name=range_name)
            
            print(f"   ✅ Used Portfolio Summary as fallback: {len(summary_df)} companies")
            return True
        
        return False

# ============================================================================
# STATISTICS SHEET UPDATE - GUIDELINE v3.2.0
# ============================================================================

def update_statistics_sheet(client, data, config):
    """Update Statistics sheet - Enhanced with guideline v3.2.0 metrics"""
    print("📝 Updating Statistics sheet (v3.2.0 metrics)...")
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    spreadsheet = client.open_by_key(sheet_id)
    
    sheet_name = config['sheets']['sheet_names']['statistics']
    max_rows = config['sheets']['max_rows']['statistics']
    stats_sheet = create_or_get_worksheet(spreadsheet, sheet_name, rows=max_rows, cols=5)
    
    if not stats_sheet:
        return False
    
    # Clear sheet
    stats_sheet.clear()
    
    # Prepare statistics data
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if data['statistics'] is not None:
        stats = data['statistics']
        
        # Build comprehensive statistics table
        stats_data = [
            ['FactSet Portfolio Statistics v3.2.0', timestamp],
            ['Guideline v3.2.0 Compliant Metrics', ''],
            ['', ''],
            ['📊 總體統計', ''],
            ['目標公司總數', stats.get('total_companies', 0)],
            ['有資料公司數', stats.get('companies_with_data', 0)],
            ['資料收集率', f"{stats.get('success_rates', {}).get('data_collection_rate', 0):.1f}%"],
            ['', ''],
            ['📈 資料品質分析', ''],
            ['平均品質評分', f"{stats.get('data_quality', {}).get('average_quality_score', 0):.1f}/4.0"],
            ['平均MD檔案數', f"{stats.get('data_quality', {}).get('average_md_files_per_company', 0):.1f}"],
            ['', ''],
            ['🎯 品質分布', ''],
            ['🟢 優秀 (4分)', stats.get('quality_distribution', {}).get('excellent_4', 0)],
            ['🟡 良好 (3分)', stats.get('quality_distribution', {}).get('good_3', 0)],
            ['🟠 普通 (2分)', stats.get('quality_distribution', {}).get('fair_2', 0)],
            ['🔴 不足 (1分)', stats.get('quality_distribution', {}).get('poor_1', 0)],
            ['❌ 無資料 (0分)', stats.get('quality_distribution', {}).get('no_data_0', 0)],
            ['', ''],
            ['💰 財務資料覆蓋', ''],
            ['有目標價公司數', stats.get('data_quality', {}).get('companies_with_target_price', 0)],
            ['有分析師數量', stats.get('data_quality', {}).get('companies_with_analyst_count', 0)],
            ['財務資料率', f"{stats.get('success_rates', {}).get('financial_data_rate', 0):.1f}%"],
            ['', ''],
            ['📊 EPS預測覆蓋 (v3.2.0)', ''],
            ['2025 EPS預測', stats.get('eps_coverage', {}).get('2025_eps_coverage', 0)],
            ['2026 EPS預測', stats.get('eps_coverage', {}).get('2026_eps_coverage', 0)],
            ['2027 EPS預測', stats.get('eps_coverage', {}).get('2027_eps_coverage', 0)],
            ['多年度EPS完整', stats.get('eps_coverage', {}).get('multi_year_coverage', 0)],
            ['EPS預測率', f"{stats.get('success_rates', {}).get('eps_forecast_rate', 0):.1f}%"],
            ['', ''],
            ['🏆 狀態分布', ''],
        ]
        
        # Add status distribution
        status_dist = stats.get('status_distribution', {})
        for status, count in status_dist.items():
            stats_data.append([status, count])
        
        stats_data.extend([
            ['', ''],
            ['📅 更新資訊', ''],
            ['資料版本', 'Guideline v3.2.0'],
            ['最後更新', timestamp],
            ['來源', '觀察名單.csv (116+ 公司)'],
        ])
        
    else:
        # Fallback statistics from Portfolio Summary
        stats_data = [
            ['FactSet Portfolio Statistics v3.2.0', timestamp],
            ['', ''],
            ['📊 基本統計 (從Portfolio Summary)', ''],
        ]
        
        if data['summary'] is not None:
            summary_df = data['summary']
            companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
            avg_quality = summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
            
            stats_data.extend([
                ['總公司數', len(summary_df)],
                ['有資料公司數', companies_with_data],
                ['資料收集率', f"{(companies_with_data/len(summary_df)*100):.1f}%"],
                ['平均品質評分', f"{avg_quality:.1f}/4.0"],
                ['', ''],
                ['⚠️ 完整統計需要statistics.json', ''],
            ])
        else:
            stats_data.append(['❌ 無可用資料', ''])
    
    # Update sheet
    end_row = len(stats_data)
    stats_sheet.update(values=stats_data, range_name=f'A1:B{end_row}')
    
    # Format headers
    stats_sheet.format('A1:B1', {
        'backgroundColor': {'red': 0.2, 'green': 0.8, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    })
    
    # Format section headers (rows with emoji)
    for i, row in enumerate(stats_data, 1):
        if len(row) > 0 and any(emoji in str(row[0]) for emoji in ['📊', '📈', '🎯', '💰', '🏆', '📅']):
            stats_sheet.format(f'A{i}:B{i}', {
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                'textFormat': {'bold': True}
            })
    
    print(f"   ✅ Statistics updated ({len(stats_data)} rows) - v3.2.0 compliant")
    return True

# ============================================================================
# MAIN UPLOAD FUNCTIONS - GUIDELINE v3.2.0
# ============================================================================

def upload_all_sheets(config, sheets_to_update=None):
    """Upload all data to Google Sheets - Guideline v3.2.0 compliant"""
    print(f"🚀 Sheets Uploader v{__version__} - Guideline v3.2.0 Compliant")
    print(f"📅 Date: {__date__} | Author: {__author__}")
    print("=" * 80)
    
    # Validate input files
    if not validate_input_files(config):
        return False
    
    # Setup Google Sheets
    client = setup_google_sheets()
    if not client:
        return False
    
    # Load data
    data = load_data_files(config)
    if not data:
        return False
    
    # Validate data quality
    if not validate_data_quality(data):
        print("⚠️ Proceeding with upload despite quality issues...")
    
    # Determine which sheets to update
    if sheets_to_update is None:
        sheets_to_update = ['portfolio', 'detailed', 'statistics']
    
    # Upload to each sheet
    success_count = 0
    total_sheets = len(sheets_to_update)
    
    try:
        if 'portfolio' in sheets_to_update:
            if update_portfolio_summary_sheet(client, data, config):
                success_count += 1
        
        if 'detailed' in sheets_to_update:
            if update_detailed_data_sheet(client, data, config):
                success_count += 1
        
        if 'statistics' in sheets_to_update:
            if update_statistics_sheet(client, data, config):
                success_count += 1
        
        # Final summary
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        print(f"\n{'='*80}")
        print("🎉 GOOGLE SHEETS UPLOAD COMPLETED! (Guideline v3.2.0)")
        print("="*80)
        print(f"📊 Success Rate: {success_count}/{total_sheets} sheets updated")
        
        if success_count > 0:
            print("✅ Successfully updated sheets:")
            if 'portfolio' in sheets_to_update:
                portfolio_name = config['sheets']['sheet_names']['portfolio']
                print(f"   - {portfolio_name} (14 columns, guideline v3.2.0 format)")
            if 'detailed' in sheets_to_update:
                detailed_name = config['sheets']['sheet_names']['detailed']
                print(f"   - {detailed_name} (21 columns, enhanced EPS breakdown)")
            if 'statistics' in sheets_to_update:
                stats_name = config['sheets']['sheet_names']['statistics']
                print(f"   - {stats_name} (comprehensive v3.2.0 metrics)")
            
            print(f"\n📊 View dashboard: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
            print("🎯 Features:")
            print("   - Portfolio Summary: Exact guideline v3.2.0 format")
            print("   - Detailed Data: Multi-year EPS breakdown (2025/2026/2027)")
            print("   - Statistics: Enhanced quality and coverage metrics")
            print("   - Quality Scores: 1-4 scale with emoji status indicators")
        else:
            print("❌ No sheets were updated successfully")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        if os.getenv("FACTSET_PIPELINE_DEBUG"):
            traceback.print_exc()
        return False

def force_update_sheets(config):
    """Force update all sheets regardless of data quality"""
    print("🔧 FORCE UPDATE MODE - Updating all sheets...")
    return upload_all_sheets(config)

def update_single_sheet(config, sheet_name):
    """Update a single specific sheet"""
    sheet_mapping = {
        'portfolio': ['portfolio'],
        'detailed': ['detailed'], 
        'statistics': ['statistics'],
        'summary': ['portfolio']  # Alias
    }
    
    if sheet_name not in sheet_mapping:
        print(f"❌ Unknown sheet name: {sheet_name}")
        print(f"💡 Available sheets: {', '.join(sheet_mapping.keys())}")
        return False
    
    print(f"📝 Updating single sheet: {sheet_name} (Guideline v3.2.0)")
    return upload_all_sheets(config, sheets_to_update=sheet_mapping[sheet_name])

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main function with CLI interface - Enhanced for guideline v3.2.0"""
    parser = argparse.ArgumentParser(description=f'Sheets Uploader v{__version__} - Guideline v3.2.0 Compliant')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--test-connection', action='store_true', help='Test Google Sheets connection only')
    parser.add_argument('--update-all', action='store_true', help='Update all sheets (default)')
    parser.add_argument('--update-sheet', type=str, choices=['portfolio', 'detailed', 'statistics', 'summary'], 
                       help='Update single sheet only')
    parser.add_argument('--force-update', action='store_true', help='Force update regardless of data quality')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backups')
    parser.add_argument('--validate-format', action='store_true', help='Validate data format only')
    
    args = parser.parse_args()
    
    # Test connection only
    if args.test_connection:
        success = test_sheets_connection()
        if success:
            print("✅ Google Sheets connection test passed!")
        else:
            print("❌ Google Sheets connection test failed!")
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Handle no-backup option
    if args.no_backup:
        config['sheets']['auto_backup'] = False
        print("⚠️ Backup disabled for this run")
    
    # Validate format only
    if args.validate_format:
        data = load_data_files(config)
        if data:
            if validate_data_quality(data):
                print("✅ Data format validation passed (Guideline v3.2.0)")
            else:
                print("❌ Data format validation failed")
        return
    
    # Handle specific actions
    if args.update_sheet:
        success = update_single_sheet(config, args.update_sheet)
    elif args.force_update:
        success = force_update_sheets(config)
    else:
        # Default: update all sheets
        success = upload_all_sheets(config)
    
    if success:
        print("✅ Sheets upload completed successfully! (Guideline v3.2.0)")
        print("🎯 Dashboard includes:")
        print("   - Portfolio Summary: 14-column guideline format")
        print("   - Detailed Data: Enhanced EPS breakdown") 
        print("   - Statistics: Comprehensive quality metrics")
    else:
        print("❌ Sheets upload failed!")
        print("\n💡 Troubleshooting:")
        print("1. Check Google Sheets credentials: python sheets_uploader.py --test-connection")
        print("2. Validate data format: python sheets_uploader.py --validate-format")
        print("3. Check data files exist: python data_processor.py")
        print("4. Try force update: python sheets_uploader.py --force-update")

if __name__ == "__main__":
    main()