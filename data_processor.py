"""
data_processor.py - Data Processing Module (Enhanced with Company Mapping Fix)

Version: 3.1.0
Date: 2025-06-21
Author: Google Search FactSet Pipeline - Modular Architecture
License: MIT

ENHANCEMENTS:
- ✅ Fixed company name extraction from search results
- ✅ Resolved dtype compatibility warnings
- ✅ Improved FactSet data parsing from MD files
- ✅ Enhanced company mapping with watchlist integration
- ✅ Better data validation and quality checks
- ✅ Comprehensive error handling and logging

Description:
    Data processing module for FactSet pipeline:
    - Parses markdown files for financial data
    - Consolidates CSV data from multiple sources
    - Extracts company information from search results
    - Maps generic names to real company names
    - Generates portfolio summaries and statistics
    - Validates data quality and completeness

Dependencies:
    - pandas
    - numpy
    - re (regex)
    - json
    - pathlib
"""

import os
import re
import json
import warnings
import traceback
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Suppress specific pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Import local modules
try:
    import utils
    import config as config_module
except ImportError as e:
    print(f"⚠️ Could not import local modules: {e}")

# Version Information
__version__ = "3.1.0"
__date__ = "2025-06-21"
__author__ = "Google Search FactSet Pipeline - Enhanced"

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

# Financial data extraction patterns
FACTSET_PATTERNS = {
    'eps_current': [
        r'EPS[：:\s]*([0-9]+\.?[0-9]*)',
        r'每股盈餘[：:\s]*([0-9]+\.?[0-9]*)',
        r'預估.*?EPS[：:\s]*([0-9]+\.?[0-9]*)',
        r'Current.*?EPS[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_previous': [
        r'先前.*?EPS[：:\s]*([0-9]+\.?[0-9]*)',
        r'Previous.*?EPS[：:\s]*([0-9]+\.?[0-9]*)',
        r'上次.*?預估[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'target_price': [
        r'目標價[：:\s]*([0-9]+\.?[0-9]*)',
        r'Target.*?Price[：:\s]*([0-9]+\.?[0-9]*)',
        r'price.*?target[：:\s]*([0-9]+\.?[0-9]*)',
        r'目標[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'analyst_count': [
        r'分析師[：:\s]*([0-9]+)',
        r'Analyst[s]?[：:\s]*([0-9]+)',
        r'([0-9]+).*?分析師',
        r'([0-9]+).*?analyst',
    ],
    'eps_2025_high': [
        r'2025.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?High[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?EPS.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2025_low': [
        r'2025.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?Low[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?EPS.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2025_avg': [
        r'2025.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?Average[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?EPS.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2025_median': [
        r'2025.*?中位數[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?Median[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?EPS.*?中位數[：:\s]*([0-9]+\.?[0-9]*)',
    ],
}

# Numeric columns that should be converted to float
NUMERIC_COLUMNS = [
    '當前EPS預估', '先前EPS預估', '目標價', '分析師數量',
    '2025EPS最高值', '2025EPS最低值', '2025EPS平均值', '2025EPS中位數',
    '2026EPS最高值', '2026EPS最低值', '2026EPS平均值', '2026EPS中位數',
    '2027EPS最高值', '2027EPS最低值', '2027EPS平均值', '2027EPS中位數',
    '2025營收最高值', '2025營收最低值', '2025營收平均值', '2025營收中位數',
    '2026營收最高值', '2026營收最低值', '2026營收平均值', '2026營收中位數',
    '2027營收最高值', '2027營收最低值', '2027營收平均值', '2027營收中位數',
]

# ============================================================================
# COMPANY NAME EXTRACTION AND MAPPING
# ============================================================================

def load_watchlist(watchlist_path: str = '觀察名單.csv') -> Optional[pd.DataFrame]:
    """
    Load the watchlist CSV file
    """
    try:
        if os.path.exists(watchlist_path):
            df = pd.read_csv(watchlist_path, encoding='utf-8')
            print(f"✅ Loaded watchlist: {len(df)} companies")
            return df
        else:
            print(f"⚠️ Watchlist file not found: {watchlist_path}")
            return None
    except Exception as e:
        print(f"❌ Error loading watchlist: {e}")
        return None

def extract_company_info_from_title(title: str, watchlist_df: Optional[pd.DataFrame] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract company name and stock code from search result title
    """
    if not title:
        return None, None
    
    company_name = None
    stock_code = None
    
    # Extract stock code patterns
    stock_patterns = [
        r'\((\d{4})\)',      # (2454)
        r'(\d{4})\.TW',      # 2454.TW
        r'(\d{4})-TW',       # 2454-TW
        r'(\d{4})\.TPE',     # 2454.TPE
    ]
    
    for pattern in stock_patterns:
        match = re.search(pattern, title)
        if match:
            stock_code = match.group(1)
            break
    
    # Extract known company names (extended list)
    company_patterns = [
        r'(台積電|台灣積體電路)',
        r'(聯發科|MediaTek)',
        r'(富邦金|富邦金控|Fubon)',
        r'(鴻海|Hon Hai|Foxconn)',
        r'(台達電|Delta)',
        r'(光寶科|Lite-On)',
        r'(聯電|UMC)',
        r'(廣達|Quanta)',
        r'(華碩|ASUS)',
        r'(宏碁|Acer)',
        r'(緯創|Wistron)',
        r'(仁寶|Compal)',
        r'(和碩|Pegatron)',
        r'(日月光|ASE)',
        r'(矽品|SPIL)',
        r'(欣興|Unimicron)',
        r'(南亞科|Nanya)',
        r'(群聯|Phison)',
        r'(瑞昱|Realtek)',
        r'(吉茂)',
        r'(中華電|中華電信)',
        r'(台塑|Formosa)',
        r'(國泰金|國泰金控)',
        r'(玉山金|玉山金控)',
        r'(統一|統一企業)',
        r'(長榮|Evergreen)',
        r'(陽明|Yang Ming)',
        r'(中鋼|China Steel)',
        r'(台化|台灣化纖)',
        r'(南亞|Nan Ya)',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            # Take the first (usually Chinese) name
            company_name = match.group(1).split('|')[0]
            break
    
    # If we have stock code, try to match with watchlist
    if stock_code and watchlist_df is not None:
        try:
            # Convert stock code to string for matching
            watchlist_match = watchlist_df[watchlist_df['代號'].astype(str) == str(stock_code)]
            if not watchlist_match.empty:
                company_name = watchlist_match.iloc[0]['名稱']
        except Exception as e:
            pass  # Continue with existing company_name
    
    # If we have company name but no stock code, try reverse lookup
    if company_name and not stock_code and watchlist_df is not None:
        try:
            watchlist_match = watchlist_df[watchlist_df['名稱'] == company_name]
            if not watchlist_match.empty:
                stock_code = str(watchlist_match.iloc[0]['代號'])
        except Exception as e:
            pass  # Continue with existing stock_code
    
    # Fallback: manual mapping for common companies
    if stock_code and not company_name:
        stock_to_company = {
            '2330': '台積電',
            '2454': '聯發科',
            '2881': '富邦金',
            '2317': '鴻海',
            '2308': '台達電',
            '2301': '光寶科',
            '2303': '聯電',
            '2382': '廣達',
            '2357': '華碩',
            '2353': '宏碁',
            '3231': '緯創',
            '2324': '仁寶',
            '4938': '和碩',
            '2311': '日月光',
            '2325': '矽品',
            '3037': '欣興',
            '2408': '南亞科',
            '8299': '群聯',
            '2379': '瑞昱',
            '1587': '吉茂',
            '2412': '中華電',
            '6505': '台塑化',
            '2882': '國泰金',
            '2884': '玉山金',
            '1216': '統一',
            '2603': '長榮',
            '2609': '陽明',
            '2002': '中鋼',
        }
        company_name = stock_to_company.get(stock_code, company_name)
    
    return company_name, stock_code

def fix_company_mapping(df: pd.DataFrame, watchlist_path: str = '觀察名單.csv') -> pd.DataFrame:
    """
    Fix the missing company names and stock codes in consolidated data
    """
    print("🔧 Fixing company name mapping...")
    
    # Load watchlist
    watchlist_df = load_watchlist(watchlist_path)
    
    # Track improvements
    fixed_names = 0
    fixed_codes = 0
    
    # Process each row
    for idx, row in df.iterrows():
        needs_fix = (pd.isna(row.get('公司名稱')) or 
                    row.get('公司名稱') == '' or 
                    row.get('公司名稱') == 'null' or
                    str(row.get('公司名稱')).startswith('Company_'))
        
        if needs_fix:
            title = row.get('Title', '')
            if title:
                # Extract company info from title
                company_name, stock_code = extract_company_info_from_title(title, watchlist_df)
                
                if company_name and company_name != row.get('公司名稱'):
                    df.at[idx, '公司名稱'] = company_name
                    fixed_names += 1
                
                if stock_code and stock_code != row.get('股票代號'):
                    df.at[idx, '股票代號'] = stock_code
                    fixed_codes += 1
    
    print(f"✅ Company mapping fixed:")
    print(f"   📝 Company names: {fixed_names} fixed")
    print(f"   🔢 Stock codes: {fixed_codes} fixed")
    
    return df

# ============================================================================
# MARKDOWN FILE PARSING
# ============================================================================

def extract_factset_data_from_content(content: str) -> Dict[str, Any]:
    """
    Extract FactSet financial data from markdown content
    """
    if not content:
        return {}
    
    extracted_data = {}
    
    # Clean content for better matching
    content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
    content = content.replace('，', ',').replace('：', ':')  # Normalize punctuation
    
    # Extract data using patterns
    for data_type, patterns in FACTSET_PATTERNS.items():
        for pattern in patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Take the first valid match
                    value = matches[0]
                    try:
                        # Convert to float if possible
                        numeric_value = float(value)
                        extracted_data[data_type] = numeric_value
                        break  # Stop after first successful match
                    except ValueError:
                        continue  # Try next pattern
            except Exception as e:
                continue  # Skip problematic patterns
    
    # Map extracted data to column names
    column_mapping = {
        'eps_current': '當前EPS預估',
        'eps_previous': '先前EPS預估',
        'target_price': '目標價',
        'analyst_count': '分析師數量',
        'eps_2025_high': '2025EPS最高值',
        'eps_2025_low': '2025EPS最低值',
        'eps_2025_avg': '2025EPS平均值',
        'eps_2025_median': '2025EPS中位數',
    }
    
    # Convert to final format
    final_data = {}
    for key, value in extracted_data.items():
        if key in column_mapping:
            final_data[column_mapping[key]] = value
    
    return final_data

def parse_markdown_files(csv_file: str, config: Dict) -> List[Dict]:
    """
    Parse markdown files associated with a CSV file
    """
    md_dir = config['output']['md_dir']
    csv_filename = os.path.splitext(os.path.basename(csv_file))[0]
    
    # Find corresponding MD files
    md_files = []
    if os.path.exists(md_dir):
        for md_file in os.listdir(md_dir):
            if md_file.endswith('.md'):
                # Check if this MD file might belong to this batch
                # Look for batch number or similar naming patterns
                if csv_filename.replace('FactSet_Batch_', '') in md_file or 'webpage' in md_file:
                    md_files.append(os.path.join(md_dir, md_file))
    
    if not md_files:
        print(f"📄 No MD files to process for {os.path.basename(csv_file)}")
        return []
    
    print(f"📝 Processing {len(md_files)} MD files for {os.path.basename(csv_file)}")
    
    parsed_data = []
    errors = 0
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract financial data
            financial_data = extract_factset_data_from_content(content)
            
            if financial_data:
                # Add metadata
                financial_data.update({
                    'MD_File': os.path.basename(md_file),
                    'Source_File': os.path.basename(csv_file),
                    'Processed_Time': datetime.now().isoformat()
                })
                parsed_data.append(financial_data)
        
        except Exception as e:
            errors += 1
            if utils.is_debug_mode():
                print(f"   ❌ Error parsing {md_file}: {e}")
    
    print(f"📊 Parsing complete: {len(parsed_data)} records parsed, {errors} errors")
    return parsed_data

def apply_md_data_to_csv(df: pd.DataFrame, parsed_md_data: List[Dict]) -> pd.DataFrame:
    """
    Apply parsed markdown data to CSV dataframe
    """
    if not parsed_md_data:
        return df
    
    updates_applied = 0
    
    for md_data in parsed_md_data:
        md_filename = md_data.get('MD_File', '')
        
        # Find corresponding rows in CSV by MD file name
        matching_rows = df[df['MD File'] == md_filename]
        
        if matching_rows.empty:
            # Try to match by partial filename or other criteria
            base_name = md_filename.replace('.md', '')
            matching_rows = df[df['MD File'].str.contains(base_name, na=False)]
        
        # Apply data to matching rows
        for idx in matching_rows.index:
            for column, value in md_data.items():
                if column in df.columns and column not in ['MD_File', 'Source_File', 'Processed_Time']:
                    if pd.isna(df.at[idx, column]) or df.at[idx, column] == '':
                        # Safe assignment with proper dtype handling
                        try:
                            if column in NUMERIC_COLUMNS:
                                df.at[idx, column] = pd.to_numeric(value, errors='coerce')
                            else:
                                df.at[idx, column] = str(value)
                            updates_applied += 1
                        except Exception as e:
                            if utils.is_debug_mode():
                                print(f"   ⚠️ Error updating {column}: {e}")
    
    if updates_applied > 0:
        print(f"   ✅ Applied {updates_applied} updates from MD files")
    
    return df

# ============================================================================
# CSV PROCESSING AND CONSOLIDATION
# ============================================================================

def safe_numeric_conversion(value: Any, column_name: str) -> Any:
    """
    Safely convert values to appropriate types with proper error handling
    """
    if pd.isna(value) or value == '' or value == 'null':
        return np.nan
    
    if column_name in NUMERIC_COLUMNS:
        try:
            # Clean numeric string
            if isinstance(value, str):
                # Remove common non-numeric characters
                cleaned = re.sub(r'[^\d\.-]', '', value)
                if cleaned:
                    return float(cleaned)
                else:
                    return np.nan
            else:
                return float(value)
        except (ValueError, TypeError):
            return np.nan
    else:
        return str(value) if value is not None else ''

def process_single_csv(csv_file: str, config: Dict, parse_md: bool = True) -> pd.DataFrame:
    """
    Process a single CSV file with optional MD parsing
    """
    try:
        # Read CSV with proper encoding handling
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_file, encoding='cp1252')
        
        if df.empty:
            return df
        
        # Parse markdown files if requested
        parsed_md_data = []
        if parse_md:
            parsed_md_data = parse_markdown_files(csv_file, config)
        
        # Apply MD data to CSV
        if parsed_md_data:
            df = apply_md_data_to_csv(df, parsed_md_data)
        
        # Fix company mapping
        df = fix_company_mapping(df)
        
        # Safe data type conversion
        for column in df.columns:
            if column in NUMERIC_COLUMNS:
                df[column] = df[column].apply(lambda x: safe_numeric_conversion(x, column))
            else:
                df[column] = df[column].astype(str).replace('nan', '')
        
        # Add processing metadata
        df['Source_File'] = os.path.basename(csv_file)
        df['Processed_Time'] = datetime.now().isoformat()
        
        return df
    
    except Exception as e:
        print(f"❌ Error processing {csv_file}: {e}")
        if utils.is_debug_mode():
            traceback.print_exc()
        return pd.DataFrame()

def consolidate_csv_files(config: Dict, parse_md: bool = True) -> pd.DataFrame:
    """
    Consolidate all CSV files into a single dataframe
    """
    print("📊 Consolidating CSV files...")
    
    csv_dir = config['output']['csv_dir']
    if not os.path.exists(csv_dir):
        print(f"❌ CSV directory not found: {csv_dir}")
        return pd.DataFrame()
    
    # Find all CSV files
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}")
        return pd.DataFrame()
    
    print(f"📄 Found {len(csv_files)} CSV files to process")
    
    # Process each CSV file
    all_dataframes = []
    for csv_file in sorted(csv_files):
        csv_path = os.path.join(csv_dir, csv_file)
        df = process_single_csv(csv_path, config, parse_md)
        
        if not df.empty:
            print(f"✅ {csv_file}: {len(df)} records")
            all_dataframes.append(df)
        else:
            print(f"⚠️ {csv_file}: No data")
    
    if not all_dataframes:
        print("❌ No data found in any CSV files")
        return pd.DataFrame()
    
    # Combine all dataframes
    consolidated_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    
    # Save consolidated data
    output_file = config['output']['consolidated_csv']
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        consolidated_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Consolidated data saved: {output_file}")
        print(f"📊 Total records: {len(consolidated_df)}")
    except Exception as e:
        print(f"❌ Error saving consolidated data: {e}")
    
    return consolidated_df

# ============================================================================
# PORTFOLIO SUMMARY GENERATION
# ============================================================================

def generate_portfolio_summary(consolidated_df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Generate portfolio summary from consolidated data
    """
    print("📋 Generating portfolio summary...")
    
    if consolidated_df.empty:
        print("❌ No consolidated data available for summary")
        return pd.DataFrame()
    
    # Group by company and aggregate data
    summary_columns = [
        '公司名稱', '股票代號', '當前EPS預估', '目標價', '分析師數量', 
        '資料來源', '更新時間'
    ]
    
    # Prepare summary data
    summary_data = []
    
    # Get unique companies
    companies = consolidated_df['公司名稱'].dropna().unique()
    companies = [c for c in companies if c != '' and c != 'null' and not str(c).startswith('Company_')]
    
    if not companies:
        print("⚠️ No valid company names found, using all records")
        # Fallback: use all records even if company names are missing
        for idx, row in consolidated_df.iterrows():
            summary_row = {}
            for col in summary_columns:
                if col in row:
                    summary_row[col] = row[col]
                else:
                    summary_row[col] = ''
            
            # Use source file as data source if missing
            if not summary_row.get('資料來源'):
                summary_row['資料來源'] = row.get('Source_File', '')
            
            summary_data.append(summary_row)
    else:
        print(f"📊 Processing {len(companies)} unique companies")
        
        for company in companies:
            company_data = consolidated_df[consolidated_df['公司名稱'] == company]
            
            if company_data.empty:
                continue
            
            # Aggregate company data
            summary_row = {
                '公司名稱': company,
                '股票代號': '',
                '當前EPS預估': np.nan,
                '目標價': '',
                '分析師數量': '',
                '資料來源': '',
                '更新時間': datetime.now().isoformat()
            }
            
            # Get stock code (take first non-empty value)
            stock_codes = company_data['股票代號'].dropna()
            stock_codes = stock_codes[stock_codes != '']
            if not stock_codes.empty:
                summary_row['股票代號'] = stock_codes.iloc[0]
            
            # Get current EPS (take most recent or highest confidence value)
            eps_values = company_data['當前EPS預估'].dropna()
            if not eps_values.empty:
                # Take the most recent non-zero value
                non_zero_eps = eps_values[eps_values != 0]
                if not non_zero_eps.empty:
                    summary_row['當前EPS預估'] = non_zero_eps.iloc[-1]
                else:
                    summary_row['當前EPS預估'] = eps_values.iloc[-1]
            
            # Get target price
            target_prices = company_data['目標價'].dropna()
            target_prices = target_prices[target_prices != '']
            if not target_prices.empty:
                summary_row['目標價'] = target_prices.iloc[-1]
            
            # Get analyst count
            analyst_counts = company_data['分析師數量'].dropna()
            analyst_counts = analyst_counts[analyst_counts != '']
            if not analyst_counts.empty:
                summary_row['分析師數量'] = analyst_counts.iloc[-1]
            
            # Get data source
            sources = company_data['Source_File'].dropna()
            if not sources.empty:
                summary_row['資料來源'] = sources.iloc[-1]
            
            summary_data.append(summary_row)
    
    # Create summary dataframe
    summary_df = pd.DataFrame(summary_data)
    
    # Clean and validate summary data
    for column in summary_df.columns:
        if column in NUMERIC_COLUMNS:
            summary_df[column] = summary_df[column].apply(
                lambda x: safe_numeric_conversion(x, column)
            )
        else:
            summary_df[column] = summary_df[column].astype(str).replace('nan', '')
    
    # Save portfolio summary
    output_file = config['output']['summary_csv']
    try:
        summary_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Portfolio summary saved: {output_file}")
        print(f"📊 Companies in summary: {len(summary_df)}")
        
        # Show data quality stats
        companies_with_names = len(summary_df[summary_df['公司名稱'] != ''])
        companies_with_codes = len(summary_df[summary_df['股票代號'] != ''])
        companies_with_eps = len(summary_df[summary_df['當前EPS預估'].notna()])
        
        print(f"   📝 Companies with names: {companies_with_names}/{len(summary_df)}")
        print(f"   🔢 Companies with codes: {companies_with_codes}/{len(summary_df)}")
        print(f"   💰 Companies with EPS: {companies_with_eps}/{len(summary_df)}")
        
    except Exception as e:
        print(f"❌ Error saving portfolio summary: {e}")
        if utils.is_debug_mode():
            traceback.print_exc()
    
    return summary_df

# ============================================================================
# STATISTICS AND VALIDATION
# ============================================================================

def generate_statistics(consolidated_df: pd.DataFrame, summary_df: pd.DataFrame, 
                       config: Dict) -> Dict:
    """
    Generate comprehensive statistics about the data quality
    """
    stats = {
        'generated_at': datetime.now().isoformat(),
        'total_records': len(consolidated_df),
        'total_companies': len(summary_df),
        'data_quality': {},
        'search_results': {},
        'financial_data': {},
        'source_breakdown': {}
    }
    
    # Data quality statistics
    if not consolidated_df.empty:
        stats['data_quality'] = {
            'records_with_titles': len(consolidated_df[consolidated_df['Title'].notna()]),
            'records_with_links': len(consolidated_df[consolidated_df['Link'].notna()]),
            'records_with_company_names': len(consolidated_df[
                (consolidated_df['公司名稱'].notna()) & 
                (consolidated_df['公司名稱'] != '') &
                (~consolidated_df['公司名稱'].str.startswith('Company_', na=False))
            ]),
            'records_with_stock_codes': len(consolidated_df[
                (consolidated_df['股票代號'].notna()) & 
                (consolidated_df['股票代號'] != '')
            ]),
        }
    
    # Financial data statistics
    if not summary_df.empty:
        stats['financial_data'] = {
            'companies_with_eps': len(summary_df[summary_df['當前EPS預估'].notna()]),
            'companies_with_target_price': len(summary_df[
                (summary_df['目標價'].notna()) & (summary_df['目標價'] != '')
            ]),
            'companies_with_analyst_count': len(summary_df[
                (summary_df['分析師數量'].notna()) & (summary_df['分析師數量'] != '')
            ]),
        }
    
    # Source breakdown
    if not consolidated_df.empty and 'Source_File' in consolidated_df.columns:
        source_counts = consolidated_df['Source_File'].value_counts().to_dict()
        stats['source_breakdown'] = source_counts
    
    # Calculate success rates
    if stats['total_records'] > 0:
        stats['success_rates'] = {
            'company_mapping_rate': (stats['data_quality'].get('records_with_company_names', 0) / 
                                   stats['total_records']) * 100,
            'financial_data_rate': (stats['financial_data'].get('companies_with_eps', 0) / 
                                  max(stats['total_companies'], 1)) * 100,
        }
    
    # Save statistics
    output_file = config['output']['stats_json']
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"✅ Statistics saved: {output_file}")
    except Exception as e:
        print(f"❌ Error saving statistics: {e}")
    
    return stats

def validate_data_quality(consolidated_df: pd.DataFrame, summary_df: pd.DataFrame) -> Dict:
    """
    Validate data quality and identify issues
    """
    issues = []
    warnings = []
    
    # Check for empty dataframes
    if consolidated_df.empty:
        issues.append("No consolidated data found")
    
    if summary_df.empty:
        issues.append("No portfolio summary data found")
        return {'issues': issues, 'warnings': warnings}
    
    # Check company name mapping
    companies_with_real_names = len(summary_df[
        (summary_df['公司名稱'].notna()) & 
        (summary_df['公司名稱'] != '') &
        (~summary_df['公司名稱'].str.startswith('Company_', na=False))
    ])
    
    if companies_with_real_names == 0:
        issues.append("No companies found with real names (all showing as Company_X or null)")
    elif companies_with_real_names < len(summary_df) * 0.5:
        warnings.append(f"Only {companies_with_real_names}/{len(summary_df)} companies have real names")
    
    # Check financial data availability
    companies_with_eps = len(summary_df[summary_df['當前EPS預估'].notna()])
    if companies_with_eps == 0:
        issues.append("No companies found with EPS data")
    elif companies_with_eps < len(summary_df) * 0.2:
        warnings.append(f"Only {companies_with_eps}/{len(summary_df)} companies have EPS data")
    
    # Check stock codes
    companies_with_codes = len(summary_df[
        (summary_df['股票代號'].notna()) & (summary_df['股票代號'] != '')
    ])
    if companies_with_codes < len(summary_df) * 0.3:
        warnings.append(f"Only {companies_with_codes}/{len(summary_df)} companies have stock codes")
    
    return {'issues': issues, 'warnings': warnings}

# ============================================================================
# MAIN PROCESSING PIPELINE
# ============================================================================

def process_all_data(config_file: Optional[str] = None, force: bool = False, 
                    parse_md: bool = True) -> bool:
    """
    Process all data through the complete pipeline
    """
    print(f"🔧 Starting data processing...")
    
    # Load configuration
    if config_file:
        config = config_module.load_config(config_file)
    else:
        config = config_module.load_config()
    
    if not config:
        print("❌ Could not load configuration")
        return False
    
    success_count = 0
    total_steps = 3
    
    try:
        # Step 1: Parse markdown files and consolidate CSV data
        print("\n🧩 Parsing markdown files...")
        consolidated_df = consolidate_csv_files(config, parse_md)
        
        if consolidated_df.empty:
            print("❌ No data found to process")
            return False
        
        success_count += 1
        print("✅ MD file parsing completed")
        
        # Step 2: Generate portfolio summary
        print("\n📋 Generating portfolio summary...")
        summary_df = generate_portfolio_summary(consolidated_df, config)
        
        if summary_df.empty:
            print("❌ Failed to generate portfolio summary")
            return False
        
        success_count += 1
        print("✅ Portfolio summary completed")
        
        # Step 3: Generate statistics and validate
        print("\n📊 Generating statistics...")
        stats = generate_statistics(consolidated_df, summary_df, config)
        
        # Validate data quality
        validation_result = validate_data_quality(consolidated_df, summary_df)
        
        if validation_result['issues']:
            print("⚠️ Data quality issues found:")
            for issue in validation_result['issues']:
                print(f"   - {issue}")
        
        if validation_result['warnings']:
            print("⚠️ Data quality warnings:")
            for warning in validation_result['warnings']:
                print(f"   - {warning}")
        
        success_count += 1
        print("✅ Statistics generation completed")
        
        # Final summary
        print(f"\n{'='*50}")
        print("📊 DATA PROCESSING SUMMARY")
        print("="*50)
        print(f"✅ Data processing complete: {success_count}/{total_steps} steps successful")
        print(f"📄 Total records processed: {len(consolidated_df)}")
        print(f"🏢 Companies in portfolio: {len(summary_df)}")
        
        if stats.get('success_rates'):
            rates = stats['success_rates']
            print(f"📈 Company mapping rate: {rates.get('company_mapping_rate', 0):.1f}%")
            print(f"💰 Financial data rate: {rates.get('financial_data_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        if utils.is_debug_mode():
            traceback.print_exc()
        return False

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """
    Main entry point for testing
    """
    print(f"📊 Data Processor v{__version__}")
    
    success = process_all_data(force=True, parse_md=True)
    
    if success:
        print("✅ Data processing completed successfully")
    else:
        print("❌ Data processing failed")
    
    return success

if __name__ == "__main__":
    main()