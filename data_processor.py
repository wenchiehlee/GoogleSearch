"""
data_processor.py - Data Processing Module (Updated for Guideline v3.2.4)

Version: 3.2.4
Date: 2025-06-22
Author: Google Search FactSet Pipeline - Guideline v3.2.4 Compliant
License: MIT

GUIDELINE v3.2.4 COMPLIANCE:
- ✅ Updated output format to match exact guideline specifications
- ✅ Portfolio Summary: 代號,名稱,股票代號,MD最舊日期,MD最新日期,MD資料筆數,分析師數量,目標價,2025EPS平均值,2026EPS平均值,2027EPS平均值,品質評分,狀態,更新日期
- ✅ Detailed Data: Enhanced with EPS high/low/avg for 2025/2026/2027
- ✅ Quality scoring system (1-4 scale)
- ✅ Status emoji indicators (🟢 完整, 🟡 良好, 🟠 部分, 🔴 不足)
- ✅ MD file date tracking and company grouping
- ✅ Enhanced company mapping with 觀察名單.csv integration

Description:
    Data processing module for FactSet pipeline aligned with guideline v3.2.4:
    - Parses markdown files for financial data
    - Groups data by company from 觀察名單.csv
    - Generates guideline-compliant portfolio summaries
    - Extracts multi-year EPS data (2025/2026/2027)
    - Calculates quality scores and status indicators
    - Validates data quality and completeness

Dependencies:
    - pandas
    - numpy
    - re (regex)
    - json
    - pathlib
    - datetime
"""

import os
import re
import json
import warnings
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib

# Suppress specific pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Import local modules
try:
    import utils
    import config as config_module
except ImportError as e:
    print(f"⚠️ Could not import local modules: {e}")

# Version Information - Guideline v3.2.4
__version__ = "3.2.4"
__date__ = "2025-06-22"
__author__ = "Google Search FactSet Pipeline - Guideline v3.2.4 Compliant"

# ============================================================================
# CONFIGURATION AND CONSTANTS - GUIDELINE v3.2.4
# ============================================================================

# Enhanced financial data extraction patterns for multi-year EPS
FACTSET_PATTERNS = {
    # Current EPS patterns
    'eps_current': [
        r'EPS[：:\s]*([0-9]+\.?[0-9]*)',
        r'每股盈餘[：:\s]*([0-9]+\.?[0-9]*)',
        r'預估.*?EPS[：:\s]*([0-9]+\.?[0-9]*)',
        r'Current.*?EPS[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    
    # Target price patterns
    'target_price': [
        r'目標價[：:\s]*([0-9]+\.?[0-9]*)',
        r'Target.*?Price[：:\s]*([0-9]+\.?[0-9]*)',
        r'price.*?target[：:\s]*([0-9]+\.?[0-9]*)',
        r'目標[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    
    # Analyst count patterns
    'analyst_count': [
        r'分析師[：:\s]*([0-9]+)',
        r'Analyst[s]?[：:\s]*([0-9]+)',
        r'([0-9]+).*?分析師',
        r'([0-9]+).*?analyst',
    ],
    
    # Enhanced multi-year EPS patterns - Guideline v3.2.4
    'eps_2025_high': [
        r'2025.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?High[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?EPS.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025年.*?EPS.*?高[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2025_low': [
        r'2025.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?Low[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?EPS.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025年.*?EPS.*?低[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2025_avg': [
        r'2025.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?Average[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025.*?EPS.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
        r'2025年.*?EPS.*?均[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    
    # 2026 EPS patterns
    'eps_2026_high': [
        r'2026.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
        r'2026.*?High[：:\s]*([0-9]+\.?[0-9]*)',
        r'2026.*?EPS.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2026_low': [
        r'2026.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
        r'2026.*?Low[：:\s]*([0-9]+\.?[0-9]*)',
        r'2026.*?EPS.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2026_avg': [
        r'2026.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
        r'2026.*?Average[：:\s]*([0-9]+\.?[0-9]*)',
        r'2026.*?EPS.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    
    # 2027 EPS patterns
    'eps_2027_high': [
        r'2027.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
        r'2027.*?High[：:\s]*([0-9]+\.?[0-9]*)',
        r'2027.*?EPS.*?最高[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2027_low': [
        r'2027.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
        r'2027.*?Low[：:\s]*([0-9]+\.?[0-9]*)',
        r'2027.*?EPS.*?最低[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    'eps_2027_avg': [
        r'2027.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
        r'2027.*?Average[：:\s]*([0-9]+\.?[0-9]*)',
        r'2027.*?EPS.*?平均[：:\s]*([0-9]+\.?[0-9]*)',
    ],
}

# Guideline v3.2.4 - Exact column specifications
PORTFOLIO_SUMMARY_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
    '分析師數量', '目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值',
    '品質評分', '狀態', '更新日期'
]

DETAILED_DATA_COLUMNS = [
    '代號', '名稱', '股票代號', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
    '分析師數量', '目標價', '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
    '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
    '2027EPS最高值', '2027EPS最低值', '2027EPS平均值',
    '品質評分', '狀態', 'MD File Folder', '更新日期'
]

# ============================================================================
# COMPANY MAPPING AND 觀察名單 INTEGRATION - GUIDELINE v3.2.4
# ============================================================================

def load_watchlist(watchlist_path: str = '觀察名單.csv') -> Optional[pd.DataFrame]:
    """Load the 觀察名單.csv file - Guideline v3.2.4"""
    try:
        if os.path.exists(watchlist_path):
            df = pd.read_csv(watchlist_path, encoding='utf-8')
            print(f"✅ Loaded watchlist: {len(df)} companies from 觀察名單.csv")
            return df
        else:
            print(f"⚠️ Watchlist file not found: {watchlist_path}")
            print("💡 Run: python config.py --download-csv")
            return None
    except Exception as e:
        print(f"❌ Error loading watchlist: {e}")
        return None

def get_company_from_watchlist(code: str, watchlist_df: Optional[pd.DataFrame] = None) -> Optional[Dict]:
    """Get company info from watchlist by code"""
    if watchlist_df is None:
        return None
    
    try:
        # Convert code to string for matching
        code_str = str(code).strip()
        match = watchlist_df[watchlist_df['代號'].astype(str) == code_str]
        
        if not match.empty:
            row = match.iloc[0]
            return {
                'code': str(row['代號']),
                'name': str(row['名稱']),
                'stock_code': f"{row['代號']}-TW"
            }
    except Exception as e:
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            print(f"   ⚠️ Error matching company {code}: {e}")
    
    return None

def extract_company_info_from_filename(filename: str, watchlist_df: Optional[pd.DataFrame] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract company info from MD filename - Enhanced for Guideline v3.2.4"""
    if not filename:
        return None, None, None
    
    # Extract stock code from filename patterns
    stock_patterns = [
        r'(\d{4})_',        # 2330_ (start of filename)
        r'_(\d{4})_',       # _2330_ (middle)
        r'(\d{4})\.md',     # 2330.md (end)
        r'\((\d{4})\)',     # (2330)
    ]
    
    stock_code = None
    for pattern in stock_patterns:
        match = re.search(pattern, filename)
        if match:
            stock_code = match.group(1)
            break
    
    # Get company info from watchlist if we have stock code
    if stock_code and watchlist_df is not None:
        company_info = get_company_from_watchlist(stock_code, watchlist_df)
        if company_info:
            return company_info['name'], company_info['code'], company_info['stock_code']
    
    # Fallback: extract company name from filename
    company_patterns = [
        r'^([^_]+)_\d{4}',  # CompanyName_2330
        r'(\w+)_\d{4}_',    # CompanyName_2330_
    ]
    
    company_name = None
    for pattern in company_patterns:
        match = re.search(pattern, filename)
        if match:
            company_name = match.group(1)
            break
    
    return company_name, stock_code, f"{stock_code}-TW" if stock_code else None

# ============================================================================
# MD FILE ANALYSIS AND DATE EXTRACTION - GUIDELINE v3.2.4
# ============================================================================

def extract_md_file_date(md_file_path: Path) -> Optional[datetime]:
    """Extract date from MD file content or metadata"""
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to extract date from content
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2025-06-22 or 2025/06/22
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # 22-06-2025 or 22/06/2025
            r'(\d{4}年\d{1,2}月\d{1,2}日)',     # 2025年6月22日
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for date_str in matches:
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                        
                        # Try Chinese format
                        if '年' in date_str:
                            # Parse 2025年6月22日
                            year_match = re.search(r'(\d{4})年', date_str)
                            month_match = re.search(r'(\d{1,2})月', date_str)
                            day_match = re.search(r'(\d{1,2})日', date_str)
                            
                            if year_match and month_match and day_match:
                                return datetime(
                                    int(year_match.group(1)),
                                    int(month_match.group(1)),
                                    int(day_match.group(1))
                                )
                    except:
                        continue
        
        # Fallback: use file modification time
        return datetime.fromtimestamp(md_file_path.stat().st_mtime)
        
    except Exception as e:
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            print(f"   ⚠️ Error extracting date from {md_file_path}: {e}")
        # Ultimate fallback: use current time
        return datetime.now()

def get_company_md_files(company_code: str, md_dir: Path) -> List[Path]:
    """Get all MD files for a specific company - Guideline v3.2.4"""
    company_files = []
    
    if not md_dir.exists():
        return company_files
    
    try:
        for md_file in md_dir.glob("*.md"):
            # Check if filename contains company code
            if (company_code in md_file.name or 
                f"_{company_code}_" in md_file.name or
                md_file.name.startswith(f"{company_code}_")):
                company_files.append(md_file)
        
        # Sort by modification time
        company_files.sort(key=lambda x: x.stat().st_mtime)
        
    except Exception as e:
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            print(f"   ⚠️ Error getting MD files for {company_code}: {e}")
    
    return company_files

def calculate_quality_score(md_files: List[Path]) -> int:
    """Calculate quality score 1-4 based on data completeness - Guideline v3.2.4"""
    if not md_files:
        return 0
    
    total_score = 0
    file_count = len(md_files)
    
    for md_file in md_files:
        file_score = 0
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            # Score based on content quality
            if any(keyword in content for keyword in ['eps', '每股盈餘', '預估']):
                file_score += 1
            
            if any(keyword in content for keyword in ['目標價', 'target price']):
                file_score += 1
            
            if any(keyword in content for keyword in ['分析師', 'analyst']):
                file_score += 1
            
            if any(keyword in content for keyword in ['factset', '財報', '營收']):
                file_score += 1
            
            total_score += min(4, file_score)
            
        except Exception:
            continue
    
    # Average score across all files, rounded to integer 1-4
    if file_count > 0:
        avg_score = total_score / file_count
        return max(1, min(4, round(avg_score)))
    
    return 1

def determine_status_emoji(quality_score: int, file_count: int) -> str:
    """Determine status emoji based on quality and file count - Guideline v3.2.4"""
    if quality_score >= 4 and file_count >= 3:
        return "🟢 完整"
    elif quality_score >= 3 and file_count >= 2:
        return "🟡 良好"
    elif quality_score >= 2 and file_count >= 1:
        return "🟠 部分"
    else:
        return "🔴 不足"

# ============================================================================
# ENHANCED FINANCIAL DATA EXTRACTION - GUIDELINE v3.2.4
# ============================================================================

def extract_financial_data_from_md_files(md_files: List[Path]) -> Dict[str, Any]:
    """Extract comprehensive financial data from MD files - Guideline v3.2.4"""
    if not md_files:
        return {}
    
    extracted_data = {
        'analyst_count': None,
        'target_price': None,
        'eps_2025_high': None,
        'eps_2025_low': None,
        'eps_2025_avg': None,
        'eps_2026_high': None,
        'eps_2026_low': None,
        'eps_2026_avg': None,
        'eps_2027_high': None,
        'eps_2027_low': None,
        'eps_2027_avg': None,
    }
    
    all_values = {key: [] for key in extracted_data.keys()}
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean content for better matching
            content = re.sub(r'\s+', ' ', content)
            content = content.replace('，', ',').replace('：', ':')
            
            # Extract data using patterns
            for data_type, patterns in FACTSET_PATTERNS.items():
                if data_type in ['eps_current', 'target_price', 'analyst_count'] or data_type.startswith('eps_20'):
                    for pattern in patterns:
                        try:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                for value in matches:
                                    try:
                                        numeric_value = float(value)
                                        # Store the mapping
                                        if data_type == 'target_price':
                                            all_values['target_price'].append(numeric_value)
                                        elif data_type == 'analyst_count':
                                            all_values['analyst_count'].append(int(numeric_value))
                                        elif data_type in all_values:
                                            all_values[data_type].append(numeric_value)
                                        break
                                    except ValueError:
                                        continue
                                if all_values.get(data_type):
                                    break  # Stop after first successful match
                        except Exception:
                            continue
                            
        except Exception as e:
            if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
                print(f"   ⚠️ Error extracting data from {md_file}: {e}")
            continue
    
    # Aggregate the collected values
    for key, values in all_values.items():
        if values:
            if key == 'analyst_count':
                # Take the most recent (last) value for analyst count
                extracted_data[key] = values[-1]
            elif key == 'target_price':
                # Take average target price
                extracted_data[key] = round(sum(values) / len(values), 2)
            elif 'high' in key:
                # Take maximum for high values
                extracted_data[key] = round(max(values), 2)
            elif 'low' in key:
                # Take minimum for low values
                extracted_data[key] = round(min(values), 2)
            elif 'avg' in key:
                # Take average for average values
                extracted_data[key] = round(sum(values) / len(values), 2)
    
    return extracted_data

# ============================================================================
# PORTFOLIO SUMMARY GENERATION - GUIDELINE v3.2.4
# ============================================================================

def generate_portfolio_summary(config: Dict, watchlist_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Generate portfolio summary matching Guideline v3.2.4 exact format"""
    print("📋 Generating Portfolio Summary (Guideline v3.2.4 format)...")
    
    md_dir = Path(config['output']['md_dir'])
    if not md_dir.exists():
        print(f"❌ MD directory not found: {md_dir}")
        return pd.DataFrame(columns=PORTFOLIO_SUMMARY_COLUMNS)
    
    # Load watchlist for company mapping
    if watchlist_df is None:
        watchlist_df = load_watchlist()
    
    if watchlist_df is None:
        print("⚠️ No watchlist available - using filename-based company detection")
    
    summary_data = []
    processed_companies = set()
    
    # Get all companies from watchlist or MD files
    if watchlist_df is not None:
        target_companies = [
            {'code': str(row['代號']), 'name': str(row['名稱'])}
            for _, row in watchlist_df.iterrows()
        ]
    else:
        # Fallback: extract companies from MD filenames
        target_companies = []
        for md_file in md_dir.glob("*.md"):
            company_name, stock_code, _ = extract_company_info_from_filename(md_file.name)
            if stock_code and stock_code not in processed_companies:
                target_companies.append({'code': stock_code, 'name': company_name or f"Company_{stock_code}"})
                processed_companies.add(stock_code)
    
    print(f"📊 Processing {len(target_companies)} companies from 觀察名單...")
    
    for company in target_companies:
        company_code = company['code']
        company_name = company['name']
        
        # Skip if already processed
        if company_code in processed_companies:
            continue
        processed_companies.add(company_code)
        
        # Get MD files for this company
        company_md_files = get_company_md_files(company_code, md_dir)
        
        if not company_md_files:
            # Add empty row for companies without data
            summary_row = {col: '' for col in PORTFOLIO_SUMMARY_COLUMNS}
            summary_row.update({
                '代號': company_code,
                '名稱': company_name,
                '股票代號': f"{company_code}-TW",
                'MD資料筆數': 0,
                '品質評分': 0,
                '狀態': "🔴 無資料",
                '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            summary_data.append(summary_row)
            continue
        
        # Extract dates from MD files
        file_dates = []
        for md_file in company_md_files:
            file_date = extract_md_file_date(md_file)
            if file_date:
                file_dates.append(file_date)
        
        oldest_date = min(file_dates).strftime('%Y/%m/%d') if file_dates else ''
        newest_date = max(file_dates).strftime('%Y/%m/%d') if file_dates else ''
        
        # Extract financial data
        financial_data = extract_financial_data_from_md_files(company_md_files)
        
        # Calculate quality metrics
        quality_score = calculate_quality_score(company_md_files)
        status = determine_status_emoji(quality_score, len(company_md_files))
        
        # Build summary row matching exact guideline format
        summary_row = {
            '代號': company_code,
            '名稱': company_name,
            '股票代號': f"{company_code}-TW",
            'MD最舊日期': oldest_date,
            'MD最新日期': newest_date,
            'MD資料筆數': len(company_md_files),
            '分析師數量': financial_data.get('analyst_count', ''),
            '目標價': financial_data.get('target_price', ''),
            '2025EPS平均值': financial_data.get('eps_2025_avg', ''),
            '2026EPS平均值': financial_data.get('eps_2026_avg', ''),
            '2027EPS平均值': financial_data.get('eps_2027_avg', ''),
            '品質評分': quality_score,
            '狀態': status,
            '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        summary_data.append(summary_row)
        
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            print(f"   ✅ {company_name} ({company_code}): {len(company_md_files)} files, quality={quality_score}")
    
    # Create DataFrame
    summary_df = pd.DataFrame(summary_data, columns=PORTFOLIO_SUMMARY_COLUMNS)
    
    # Clean and format data
    for col in summary_df.columns:
        if col in ['分析師數量', 'MD資料筆數', '品質評分']:
            summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').fillna(0).astype(int)
        elif col in ['目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值']:
            summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce')
        else:
            summary_df[col] = summary_df[col].astype(str).replace('nan', '')
    
    # Save portfolio summary
    output_file = config['output']['summary_csv']
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        summary_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Portfolio Summary saved: {output_file}")
        print(f"📊 Format: {len(summary_df)} companies in Guideline v3.2.4 format")
        
        # Quality statistics
        companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
        avg_quality = summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
        
        print(f"   📈 Companies with data: {companies_with_data}/{len(summary_df)}")
        print(f"   🎯 Average quality score: {avg_quality:.1f}/4.0")
        
    except Exception as e:
        print(f"❌ Error saving portfolio summary: {e}")
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            traceback.print_exc()
    
    return summary_df

# ============================================================================
# DETAILED DATA GENERATION - GUIDELINE v3.2.4
# ============================================================================

def generate_detailed_data(config: Dict, watchlist_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Generate detailed data matching Guideline v3.2.4 format"""
    print("📋 Generating Detailed Data (Guideline v3.2.4 format)...")
    
    md_dir = Path(config['output']['md_dir'])
    if not md_dir.exists():
        return pd.DataFrame(columns=DETAILED_DATA_COLUMNS)
    
    if watchlist_df is None:
        watchlist_df = load_watchlist()
    
    detailed_data = []
    processed_companies = set()
    
    # Process companies from watchlist
    if watchlist_df is not None:
        for _, row in watchlist_df.iterrows():
            company_code = str(row['代號'])
            company_name = str(row['名稱'])
            
            if company_code in processed_companies:
                continue
            processed_companies.add(company_code)
            
            company_md_files = get_company_md_files(company_code, md_dir)
            
            if not company_md_files:
                continue
            
            # Extract comprehensive financial data
            financial_data = extract_financial_data_from_md_files(company_md_files)
            
            # Extract dates
            file_dates = [extract_md_file_date(f) for f in company_md_files]
            file_dates = [d for d in file_dates if d]
            
            oldest_date = min(file_dates).strftime('%Y/%m/%d') if file_dates else ''
            newest_date = max(file_dates).strftime('%Y/%m/%d') if file_dates else ''
            
            # Calculate quality metrics
            quality_score = calculate_quality_score(company_md_files)
            status = determine_status_emoji(quality_score, len(company_md_files))
            
            # Build detailed row with enhanced EPS breakdown
            detailed_row = {
                '代號': company_code,
                '名稱': company_name,
                '股票代號': f"{company_code}-TW",
                'MD最舊日期': oldest_date,
                'MD最新日期': newest_date,
                'MD資料筆數': len(company_md_files),
                '分析師數量': financial_data.get('analyst_count', ''),
                '目標價': financial_data.get('target_price', ''),
                '2025EPS最高值': financial_data.get('eps_2025_high', ''),
                '2025EPS最低值': financial_data.get('eps_2025_low', ''),
                '2025EPS平均值': financial_data.get('eps_2025_avg', ''),
                '2026EPS最高值': financial_data.get('eps_2026_high', ''),
                '2026EPS最低值': financial_data.get('eps_2026_low', ''),
                '2026EPS平均值': financial_data.get('eps_2026_avg', ''),
                '2027EPS最高值': financial_data.get('eps_2027_high', ''),
                '2027EPS最低值': financial_data.get('eps_2027_low', ''),
                '2027EPS平均值': financial_data.get('eps_2027_avg', ''),
                '品質評分': quality_score,
                '狀態': status,
                'MD File Folder': f"data/md/{company_code}",
                '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            detailed_data.append(detailed_row)
    
    # Create DataFrame
    detailed_df = pd.DataFrame(detailed_data, columns=DETAILED_DATA_COLUMNS)
    
    # Clean and format data
    numeric_columns = [
        '分析師數量', 'MD資料筆數', '品質評分',
        '目標價', '2025EPS最高值', '2025EPS最低值', '2025EPS平均值',
        '2026EPS最高值', '2026EPS最低值', '2026EPS平均值',
        '2027EPS最高值', '2027EPS最低值', '2027EPS平均值'
    ]
    
    for col in detailed_df.columns:
        if col in ['分析師數量', 'MD資料筆數', '品質評分']:
            detailed_df[col] = pd.to_numeric(detailed_df[col], errors='coerce').fillna(0).astype(int)
        elif col in numeric_columns:
            detailed_df[col] = pd.to_numeric(detailed_df[col], errors='coerce')
        else:
            detailed_df[col] = detailed_df[col].astype(str).replace('nan', '')
    
    # Save detailed data
    output_file = os.path.join(config['output']['processed_dir'], 'detailed_data.csv')
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        detailed_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Detailed Data saved: {output_file}")
        print(f"📊 Enhanced format: {len(detailed_df)} companies with EPS breakdown")
        
    except Exception as e:
        print(f"❌ Error saving detailed data: {e}")
    
    return detailed_df

# ============================================================================
# STATISTICS AND VALIDATION - GUIDELINE v3.2.4
# ============================================================================

def generate_statistics(summary_df: pd.DataFrame, detailed_df: pd.DataFrame, config: Dict) -> Dict:
    """Generate comprehensive statistics - Guideline v3.2.4"""
    stats = {
        'generated_at': datetime.now().isoformat(),
        'guideline_version': '3.2.4',
        'total_companies': len(summary_df),
        'companies_with_data': len(summary_df[summary_df['MD資料筆數'] > 0]),
        'data_quality': {},
        'financial_coverage': {},
        'quality_distribution': {},
        'eps_coverage': {}
    }
    
    # Data quality statistics
    if not summary_df.empty:
        stats['data_quality'] = {
            'companies_with_md_files': len(summary_df[summary_df['MD資料筆數'] > 0]),
            'companies_with_target_price': len(summary_df[summary_df['目標價'].notna() & (summary_df['目標價'] != '')]),
            'companies_with_analyst_count': len(summary_df[summary_df['分析師數量'].notna() & (summary_df['分析師數量'] > 0)]),
            'average_md_files_per_company': summary_df[summary_df['MD資料筆數'] > 0]['MD資料筆數'].mean(),
            'average_quality_score': summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
        }
    
    # EPS coverage analysis
    if not summary_df.empty:
        eps_2025 = len(summary_df[summary_df['2025EPS平均值'].notna()])
        eps_2026 = len(summary_df[summary_df['2026EPS平均值'].notna()])
        eps_2027 = len(summary_df[summary_df['2027EPS平均值'].notna()])
        
        stats['eps_coverage'] = {
            '2025_eps_coverage': eps_2025,
            '2026_eps_coverage': eps_2026,
            '2027_eps_coverage': eps_2027,
            'multi_year_coverage': len(summary_df[
                (summary_df['2025EPS平均值'].notna()) & 
                (summary_df['2026EPS平均值'].notna()) & 
                (summary_df['2027EPS平均值'].notna())
            ])
        }
    
    # Quality distribution
    if not summary_df.empty:
        quality_counts = summary_df['品質評分'].value_counts().to_dict()
        stats['quality_distribution'] = {
            'excellent_4': quality_counts.get(4, 0),
            'good_3': quality_counts.get(3, 0),
            'fair_2': quality_counts.get(2, 0),
            'poor_1': quality_counts.get(1, 0),
            'no_data_0': quality_counts.get(0, 0)
        }
    
    # Status distribution
    if not summary_df.empty:
        status_counts = summary_df['狀態'].value_counts().to_dict()
        stats['status_distribution'] = status_counts
    
    # Success rates
    if stats['total_companies'] > 0:
        stats['success_rates'] = {
            'data_collection_rate': (stats['companies_with_data'] / stats['total_companies']) * 100,
            'financial_data_rate': (stats['data_quality'].get('companies_with_target_price', 0) / stats['total_companies']) * 100,
            'eps_forecast_rate': (stats['eps_coverage'].get('2025_eps_coverage', 0) / stats['total_companies']) * 100
        }
    
    # Save statistics
    output_file = config['output']['stats_json']
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Statistics saved: {output_file}")
        print(f"📊 Guideline v3.2.4 compliant statistics generated")
        
    except Exception as e:
        print(f"❌ Error saving statistics: {e}")
    
    return stats

# ============================================================================
# MAIN PROCESSING PIPELINE - GUIDELINE v3.2.4
# ============================================================================

def process_all_data(config_file: Optional[str] = None, force: bool = False, 
                    parse_md: bool = True) -> bool:
    """Process all data through the complete pipeline - Guideline v3.2.4"""
    print(f"🔧 Starting data processing (Guideline v{__version__})...")
    
    # Load configuration
    if config_file:
        config = config_module.load_config(config_file)
    else:
        config = config_module.load_config()
    
    if not config:
        print("❌ Could not load configuration")
        return False
    
    # Load watchlist
    watchlist_df = load_watchlist()
    if watchlist_df is None:
        print("⚠️ Proceeding without watchlist - using filename-based detection")
    
    success_count = 0
    total_steps = 3
    
    try:
        # Step 1: Generate Portfolio Summary (Guideline v3.2.4 format)
        print("\n📋 Generating Portfolio Summary...")
        summary_df = generate_portfolio_summary(config, watchlist_df)
        
        if summary_df.empty:
            print("❌ Failed to generate portfolio summary")
            return False
        
        success_count += 1
        print("✅ Portfolio Summary completed (Guideline v3.2.4 format)")
        
        # Step 2: Generate Detailed Data (Enhanced EPS breakdown)
        print("\n📊 Generating Detailed Data...")
        detailed_df = generate_detailed_data(config, watchlist_df)
        
        if detailed_df.empty:
            print("⚠️ No detailed data generated")
        else:
            success_count += 1
            print("✅ Detailed Data completed (Enhanced EPS breakdown)")
        
        # Step 3: Generate Statistics
        print("\n📈 Generating Statistics...")
        stats = generate_statistics(summary_df, detailed_df, config)
        
        success_count += 1
        print("✅ Statistics generation completed")
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 DATA PROCESSING SUMMARY (Guideline v3.2.4)")
        print("="*60)
        print(f"✅ Processing complete: {success_count}/{total_steps} steps successful")
        print(f"🎯 Companies processed: {len(summary_df)}")
        print(f"📄 Companies with data: {stats.get('companies_with_data', 0)}")
        
        if stats.get('success_rates'):
            rates = stats['success_rates']
            print(f"📈 Data collection rate: {rates.get('data_collection_rate', 0):.1f}%")
            print(f"💰 Financial data rate: {rates.get('financial_data_rate', 0):.1f}%")
            print(f"📊 EPS forecast rate: {rates.get('eps_forecast_rate', 0):.1f}%")
        
        if stats.get('quality_distribution'):
            quality = stats['quality_distribution']
            print(f"🏆 Quality distribution: 4={quality.get('excellent_4', 0)}, 3={quality.get('good_3', 0)}, 2={quality.get('fair_2', 0)}, 1={quality.get('poor_1', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            traceback.print_exc()
        return False

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for Guideline v3.2.4 compliance testing"""
    print(f"📊 Data Processor v{__version__} (Guideline v3.2.4 Compliant)")
    
    success = process_all_data(force=True, parse_md=True)
    
    if success:
        print("✅ Data processing completed successfully (Guideline v3.2.4)")
        print("📋 Generated files:")
        print("   - portfolio_summary.csv (Exact guideline format)")
        print("   - detailed_data.csv (Enhanced EPS breakdown)")
        print("   - statistics.json (Comprehensive metrics)")
    else:
        print("❌ Data processing failed")
    
    return success

if __name__ == "__main__":
    main()