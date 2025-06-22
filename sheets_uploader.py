"""
sheets_uploader.py - Google Sheets Integration Module

Version: 3.0.0
Date: 2025-06-21
Author: Google Search FactSet Pipeline - Modular Architecture
License: MIT

Description:
    Google Sheets integration module focused ONLY on:
    - Google Sheets authentication
    - Sheet creation and updating
    - Data formatting for sheets
    - Error handling for uploads
    - NO data processing or search execution

Key Features:
    - Secure authentication via environment variables
    - Multiple sheet management (Portfolio Summary, Detailed Data, Statistics)
    - Data validation before upload
    - Comprehensive error handling
    - CLI interface for standalone usage
    - Backup and recovery options

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

# Version Information
__version__ = "3.0.0"
__date__ = "2025-06-21"
__author__ = "Google Search FactSet Pipeline - Modular Architecture"

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION AND UTILITIES
# ============================================================================

def load_config(config_file=None):
    """Load configuration from file or use defaults"""
    default_config = {
        "target_companies": [
            {"code": "2382", "name": "廣達"},
            {"code": "2412", "name": "中華電"},
            {"code": "2480", "name": "敦陽科"},
            {"code": "8299", "name": "群聯"},
            {"code": "2454", "name": "聯發科"}
        ],
        "input": {
            "consolidated_csv": "data/processed/consolidated_factset.csv",
            "summary_csv": "data/processed/portfolio_summary.csv",
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
    """Validate that required input files exist"""
    required_files = [
        config['input']['consolidated_csv'],
        config['input']['summary_csv']
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required input files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\n💡 Run data processor first: python data_processor.py")
        return False
    
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
# DATA LOADING AND VALIDATION
# ============================================================================

def load_data_files(config):
    """Load all required data files"""
    data = {}
    
    try:
        # Load consolidated data
        if os.path.exists(config['input']['consolidated_csv']):
            data['consolidated'] = pd.read_csv(config['input']['consolidated_csv'], encoding='utf-8')
            print(f"✅ Loaded consolidated data: {len(data['consolidated'])} records")
        else:
            print(f"⚠️ Consolidated data file not found: {config['input']['consolidated_csv']}")
            data['consolidated'] = None
        
        # Load summary data
        if os.path.exists(config['input']['summary_csv']):
            data['summary'] = pd.read_csv(config['input']['summary_csv'], encoding='utf-8')
            print(f"✅ Loaded summary data: {len(data['summary'])} companies")
        else:
            print(f"⚠️ Summary data file not found: {config['input']['summary_csv']}")
            data['summary'] = None
        
        # Load statistics
        if os.path.exists(config['input']['stats_json']):
            with open(config['input']['stats_json'], 'r', encoding='utf-8') as f:
                data['statistics'] = json.load(f)
            print(f"✅ Loaded statistics data")
        else:
            print(f"⚠️ Statistics file not found: {config['input']['stats_json']}")
            data['statistics'] = None
        
        return data
        
    except Exception as e:
        print(f"❌ Error loading data files: {e}")
        return None

def validate_data_quality(data):
    """Validate data quality before upload"""
    issues = []
    
    if data['consolidated'] is not None:
        consolidated = data['consolidated']
        if len(consolidated) == 0:
            issues.append("Consolidated data is empty")
        elif '公司名稱' not in consolidated.columns:
            issues.append("Consolidated data missing '公司名稱' column")
        else:
            companies_with_data = consolidated[consolidated['公司名稱'].notna() & (consolidated['公司名稱'] != '')].shape[0]
            if companies_with_data == 0:
                issues.append("No companies found in consolidated data")
    else:
        issues.append("Consolidated data not loaded")
    
    if data['summary'] is not None:
        summary = data['summary']
        if len(summary) == 0:
            issues.append("Summary data is empty")
        elif '公司名稱' not in summary.columns:
            issues.append("Summary data missing '公司名稱' column")
    else:
        issues.append("Summary data not loaded")
    
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
# SHEET UPDATES
# ============================================================================

def update_portfolio_summary_sheet(client, data, config):
    """Update Portfolio Summary sheet"""
    print("📝 Updating Portfolio Summary sheet...")
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    spreadsheet = client.open_by_key(sheet_id)
    
    sheet_name = config['sheets']['sheet_names']['portfolio']
    summary_sheet = create_or_get_worksheet(spreadsheet, sheet_name, rows=50, cols=15)
    
    if not summary_sheet:
        return False
    
    # Backup if requested
    if config['sheets']['auto_backup']:
        backup_sheet_data(summary_sheet)
    
    # Clear sheet
    summary_sheet.clear()
    
    # Create header
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header_data = [
        [f'FactSet Portfolio Dashboard - Updated: {timestamp}'],
        [''],
    ]
    summary_sheet.update(values=header_data, range_name='A1:A2')
    
    # Add summary data
    if data['summary'] is not None:
        summary_df = data['summary']
        
        # Convert to proper format, handling any data type issues
        summary_data = [summary_df.columns.tolist()]
        
        for _, row in summary_df.iterrows():
            row_data = []
            for col in summary_df.columns:
                val = row[col]
                if pd.isna(val):
                    row_data.append('')
                else:
                    row_data.append(str(val))
            summary_data.append(row_data)
        
        # Calculate range
        end_row = 3 + len(summary_data) - 1
        end_col = chr(ord('A') + len(summary_df.columns) - 1)
        range_name = f'A3:{end_col}{end_row}'
        
        summary_sheet.update(values=summary_data, range_name=range_name)
        print(f"   ✅ Portfolio Summary: {len(summary_df)} companies updated")
        return True
    else:
        print(f"   ⚠️ No summary data to update")
        return False

def update_detailed_data_sheet(client, data, config):
    """Update Detailed Data sheet"""
    print("📝 Updating Detailed Data sheet...")
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    spreadsheet = client.open_by_key(sheet_id)
    
    sheet_name = config['sheets']['sheet_names']['detailed']
    detail_sheet = create_or_get_worksheet(spreadsheet, sheet_name, rows=200, cols=25)
    
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
        [f'Detailed FactSet Data - Updated: {timestamp}'],
        ['']
    ]
    detail_sheet.update(values=detail_header, range_name='A1:A2')
    
    # Add detailed data
    if data['consolidated'] is not None:
        consolidated_df = data['consolidated']
        
        # Select important columns only
        key_columns = [
            '公司名稱', '股票代號', '日期', '當前EPS預估', '目標價', '分析師數量',
            '2025EPS平均值', '2026EPS平均值', '2027EPS平均值', 'Source_File', 'Processed_Time'
        ]
        
        # Filter to available columns
        available_cols = [col for col in key_columns if col in consolidated_df.columns]
        detail_df = consolidated_df[available_cols]
        
        # Convert to string format for Google Sheets
        detail_data = [detail_df.columns.tolist()]
        
        for _, row in detail_df.iterrows():
            row_data = []
            for col in detail_df.columns:
                val = row[col]
                if pd.isna(val):
                    row_data.append('')
                else:
                    row_data.append(str(val))
            detail_data.append(row_data)
        
        # Calculate range
        end_row = 3 + len(detail_data) - 1
        end_col = chr(ord('A') + len(available_cols) - 1)
        range_name = f'A3:{end_col}{end_row}'
        
        detail_sheet.update(values=detail_data, range_name=range_name)
        print(f"   ✅ Detailed Data: {len(consolidated_df)} records updated")
        return True
    else:
        print(f"   ⚠️ No consolidated data to update")
        return False

def update_statistics_sheet(client, data, config):
    """Update Statistics sheet"""
    print("📝 Updating Statistics sheet...")
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    spreadsheet = client.open_by_key(sheet_id)
    
    sheet_name = config['sheets']['sheet_names']['statistics']
    stats_sheet = create_or_get_worksheet(spreadsheet, sheet_name, rows=30, cols=5)
    
    if not stats_sheet:
        return False
    
    # Clear sheet
    stats_sheet.clear()
    
    # Prepare statistics data
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if data['statistics'] is not None:
        stats = data['statistics']
        
        # Extract key metrics
        proc = stats.get('processing_summary', {})
        quality = stats.get('data_quality', {})
        target = stats.get('target_analysis', {})
        
        # Build statistics table
        stats_data = [
            ['FactSet Portfolio Statistics', timestamp],
            ['', ''],
            ['檔案處理統計', ''],
            ['處理的CSV檔案數', proc.get('files_with_data', 0)],
            ['總記錄數', proc.get('total_records', 0)],
            ['唯一公司數', proc.get('unique_companies', 0)],
            ['', ''],
            ['資料品質分析', ''],
            ['完整資料公司數', quality.get('companies_with_complete_data', 0)],
            ['部分資料公司數', quality.get('companies_with_partial_data', 0)],
            ['資料不足公司數', quality.get('companies_with_minimal_data', 0)],
            ['平均品質評分', f"{quality.get('average_quality_score', 0):.1f}"],
            ['', ''],
            ['目標公司追蹤', ''],
            ['成功率', f"{target.get('coverage_rate', 0):.1f}%"],
            ['已找到公司數', f"{target.get('found_count', 0)}/{target.get('target_count', 0)}"],
            ['', '']
        ]
        
        # Add target company status
        if 'found_companies' in target:
            stats_data.append(['已找到的公司:', ''])
            for company in target['found_companies']:
                stats_data.append([company, '✅ 有資料'])
        
        if 'missing_companies' in target and target['missing_companies']:
            stats_data.append(['', ''])
            stats_data.append(['缺少的公司:', ''])
            for company in target['missing_companies']:
                stats_data.append([company, '❌ 缺少'])
    else:
        # Fallback statistics
        stats_data = [
            ['FactSet Portfolio Statistics', timestamp],
            ['', ''],
            ['狀態', '無統計資料'],
            ['', ''],
            ['💡 請先執行資料處理器', '']
        ]
    
    # Update sheet
    end_row = len(stats_data)
    stats_sheet.update(values=stats_data, range_name=f'A1:B{end_row}')
    
    print(f"   ✅ Statistics updated ({len(stats_data)} rows)")
    return True

# ============================================================================
# MAIN UPLOAD FUNCTIONS
# ============================================================================

def upload_all_sheets(config, sheets_to_update=None):
    """Upload all data to Google Sheets"""
    print(f"🚀 Sheets Uploader v{__version__} - Google Sheets Integration")
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
        
        print(f"\n{'='*60}")
        print("🎉 GOOGLE SHEETS UPLOAD COMPLETED!")
        print("="*60)
        print(f"📊 Success Rate: {success_count}/{total_sheets} sheets updated")
        
        if success_count > 0:
            print("✅ Successfully updated sheets:")
            if 'portfolio' in sheets_to_update:
                print(f"   - {config['sheets']['sheet_names']['portfolio']}")
            if 'detailed' in sheets_to_update:
                print(f"   - {config['sheets']['sheet_names']['detailed']}")
            if 'statistics' in sheets_to_update:
                print(f"   - {config['sheets']['sheet_names']['statistics']}")
            
            print(f"\n📊 View dashboard: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        else:
            print("❌ No sheets were updated successfully")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
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
    
    print(f"📝 Updating single sheet: {sheet_name}")
    return upload_all_sheets(config, sheets_to_update=sheet_mapping[sheet_name])

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description='Sheets Uploader v3.0.0 - Google Sheets Integration')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--test-connection', action='store_true', help='Test Google Sheets connection only')
    parser.add_argument('--update-all', action='store_true', help='Update all sheets (default)')
    parser.add_argument('--update-sheet', type=str, choices=['portfolio', 'detailed', 'statistics', 'summary'], 
                       help='Update single sheet only')
    parser.add_argument('--force-update', action='store_true', help='Force update regardless of data quality')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backups')
    
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
    
    # Handle specific actions
    if args.update_sheet:
        success = update_single_sheet(config, args.update_sheet)
    elif args.force_update:
        success = force_update_sheets(config)
    else:
        # Default: update all sheets
        success = upload_all_sheets(config)
    
    if success:
        print("✅ Sheets upload completed successfully!")
    else:
        print("❌ Sheets upload failed!")
        print("\n💡 Troubleshooting:")
        print("1. Check Google Sheets credentials: python sheets_uploader.py --test-connection")
        print("2. Verify data files exist: python data_processor.py --check-data")
        print("3. Try force update: python sheets_uploader.py --force-update")

if __name__ == "__main__":
    main()