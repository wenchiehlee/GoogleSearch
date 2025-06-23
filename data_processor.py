"""
data_processor.py - Enhanced Data Processing Module (v3.3.0)

Version: 3.3.0
Date: 2025-06-22
Author: Google Search FactSet Pipeline - v3.3.0 Guideline Compliant

v3.3.0 ENHANCEMENTS:
- ✅ Portfolio Summary: Proper aggregation of multiple MD files per company
- ✅ Detailed Data: One row per MD file with individual quality scoring
- ✅ Enhanced MD file parsing with better financial data extraction
- ✅ Data deduplication for same data from different sources
- ✅ Improved date extraction from MD files
- ✅ Better company name matching using 觀察名單.csv
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

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Import local modules
try:
    import utils
    import config as config_module
except ImportError as e:
    print(f"⚠️ Could not import local modules: {e}")

# Version Information - v3.3.0
__version__ = "3.3.0"
__date__ = "2025-06-22"
__author__ = "Google Search FactSet Pipeline - v3.3.0 Guideline Compliant"

# ============================================================================
# ENHANCED FINANCIAL DATA EXTRACTION PATTERNS - v3.3.0
# ============================================================================

ENHANCED_FACTSET_PATTERNS = {
    # Multi-year EPS patterns with improved coverage
    'eps_2025_patterns': [
        r'2025.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'2025年.*?每股盈餘.*?([0-9]+\.?[0-9]*)',
        r'FY25.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'25年.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'2025.*?預估.*?([0-9]+\.?[0-9]*)',
        r'E2025.*?([0-9]+\.?[0-9]*)',
        r'2025.*?earnings.*?([0-9]+\.?[0-9]*)',
        r'25年.*?每股.*?([0-9]+\.?[0-9]*)',
    ],
    
    'eps_2026_patterns': [
        r'2026.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'2026年.*?每股盈餘.*?([0-9]+\.?[0-9]*)',
        r'FY26.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'26年.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'E2026.*?([0-9]+\.?[0-9]*)',
        r'2026.*?earnings.*?([0-9]+\.?[0-9]*)',
        r'26年.*?每股.*?([0-9]+\.?[0-9]*)',
    ],
    
    'eps_2027_patterns': [
        r'2027.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'2027年.*?每股盈餘.*?([0-9]+\.?[0-9]*)',
        r'FY27.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'27年.*?EPS.*?([0-9]+\.?[0-9]*)',
        r'E2027.*?([0-9]+\.?[0-9]*)',
        r'2027.*?earnings.*?([0-9]+\.?[0-9]*)',
        r'27年.*?每股.*?([0-9]+\.?[0-9]*)',
    ],
    
    # Enhanced target price patterns
    'target_price_patterns': [
        r'目標價[：:\s]*([0-9]+\.?[0-9]*)',
        r'Target.*?Price[：:\s]*([0-9]+\.?[0-9]*)',
        r'price.*?target[：:\s]*([0-9]+\.?[0-9]*)',
        r'合理價值[：:\s]*([0-9]+\.?[0-9]*)',
        r'Fair.*?Value[：:\s]*([0-9]+\.?[0-9]*)',
        r'PT[：:\s]*([0-9]+\.?[0-9]*)',
        r'目標[：:\s]*([0-9]+\.?[0-9]*)',
        r'TP[：:\s]*([0-9]+\.?[0-9]*)',
    ],
    
    # Enhanced analyst patterns
    'analyst_patterns': [
        r'分析師[：:\s]*([0-9]+)',
        r'Analyst[s]?[：:\s]*([0-9]+)',
        r'([0-9]+).*?分析師',
        r'([0-9]+).*?analyst',
        r'覆蓋.*?([0-9]+).*?分析師',
        r'([0-9]+)家.*?券商',
        r'([0-9]+)位.*?分析師',
        r'分析師.*?([0-9]+)位',
    ],
}

# Portfolio Summary columns (v3.3.0)
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

# ============================================================================
# WATCHLIST INTEGRATION - v3.3.0
# ============================================================================

def load_watchlist(watchlist_path: str = '觀察名單.csv') -> Optional[pd.DataFrame]:
    """Load the 觀察名單.csv file with enhanced error handling"""
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

def get_company_mapping_from_watchlist(watchlist_df: Optional[pd.DataFrame]) -> Dict[str, Dict]:
    """Create comprehensive company mapping from watchlist"""
    if watchlist_df is None:
        return {}
    
    mapping = {}
    for _, row in watchlist_df.iterrows():
        try:
            code = str(row['代號']).strip()
            name = str(row['名稱']).strip()
            
            if code and name and code != 'nan':
                mapping[code] = {
                    'code': code,
                    'name': name,
                    'stock_code': f"{code}-TW"
                }
        except Exception as e:
            continue
    
    return mapping

# ============================================================================
# ENHANCED MD FILE PROCESSING - v3.3.0
# ============================================================================

def extract_company_code_from_filename(filename: str) -> Optional[str]:
    """Extract company code from MD filename with enhanced patterns"""
    patterns = [
        r'(\d{4})_',        # 2330_
        r'_(\d{4})_',       # _2330_
        r'(\d{4})\.md',     # 2330.md
        r'\((\d{4})\)',     # (2330)
        r'(\d{4})-',        # 2330-
        r'-(\d{4})',        # -2330
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            code = match.group(1)
            if len(code) == 4 and code.isdigit():
                return code
    
    return None

def extract_date_from_md_file(md_file_path: Path) -> Optional[datetime]:
    """Extract date from MD file content with multiple fallback strategies"""
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try content-based date extraction
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2025-06-22
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # 22-06-2025
            r'(\d{4}年\d{1,2}月\d{1,2}日)',     # 2025年6月22日
            r'發布.*?(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'更新.*?(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for date_str in matches:
                    try:
                        # Try different formats
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                # Validate reasonable date range
                                if datetime(2020, 1, 1) <= parsed_date <= datetime.now():
                                    return parsed_date
                            except ValueError:
                                continue
                        
                        # Try Chinese format
                        if '年' in date_str:
                            year_match = re.search(r'(\d{4})年', date_str)
                            month_match = re.search(r'(\d{1,2})月', date_str)
                            day_match = re.search(r'(\d{1,2})日', date_str)
                            
                            if year_match and month_match and day_match:
                                parsed_date = datetime(
                                    int(year_match.group(1)),
                                    int(month_match.group(1)),
                                    int(day_match.group(1))
                                )
                                if datetime(2020, 1, 1) <= parsed_date <= datetime.now():
                                    return parsed_date
                    except Exception:
                        continue
        
        # Fallback: file modification time
        mod_time = datetime.fromtimestamp(md_file_path.stat().st_mtime)
        return mod_time
        
    except Exception as e:
        print(f"⚠️ Error extracting date from {md_file_path}: {e}")
        return datetime.now()

def extract_financial_data_from_md_file(md_file_path: Path) -> Dict[str, Any]:
    """Extract comprehensive financial data from single MD file - v3.3.0"""
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean and normalize content
        content = re.sub(r'\s+', ' ', content)
        content = content.replace('，', ',').replace('：', ':')
        
        extracted_data = {
            'file_path': str(md_file_path),
            'file_date': extract_date_from_md_file(md_file_path),
            'eps_2025_values': [],
            'eps_2026_values': [],
            'eps_2027_values': [],
            'target_price_values': [],
            'analyst_count_values': [],
        }
        
        # Extract EPS data for each year
        for year in ['2025', '2026', '2027']:
            pattern_key = f'eps_{year}_patterns'
            values_key = f'eps_{year}_values'
            
            if pattern_key in ENHANCED_FACTSET_PATTERNS:
                for pattern in ENHANCED_FACTSET_PATTERNS[pattern_key]:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        try:
                            value = float(match)
                            if 0.1 <= value <= 1000:  # Reasonable EPS range
                                extracted_data[values_key].append(value)
                        except (ValueError, TypeError):
                            continue
        
        # Extract target price
        for pattern in ENHANCED_FACTSET_PATTERNS['target_price_patterns']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match)
                    if 1 <= value <= 10000:  # Reasonable price range
                        extracted_data['target_price_values'].append(value)
                except (ValueError, TypeError):
                    continue
        
        # Extract analyst count
        for pattern in ENHANCED_FACTSET_PATTERNS['analyst_patterns']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value = int(match)
                    if 1 <= value <= 50:  # Reasonable analyst count
                        extracted_data['analyst_count_values'].append(value)
                except (ValueError, TypeError):
                    continue
        
        # Process to final values
        extracted_data.update(_calculate_final_values(extracted_data))
        
        return extracted_data
        
    except Exception as e:
        print(f"⚠️ Error extracting data from {md_file_path}: {e}")
        return {'file_path': str(md_file_path), 'file_date': datetime.now()}

def _calculate_final_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate final statistical values from extracted data"""
    final_values = {}
    
    # Process EPS data for each year
    for year in ['2025', '2026', '2027']:
        values_key = f'eps_{year}_values'
        values = data.get(values_key, [])
        
        if values:
            final_values[f'eps_{year}_high'] = round(max(values), 2)
            final_values[f'eps_{year}_low'] = round(min(values), 2)
            final_values[f'eps_{year}_avg'] = round(sum(values) / len(values), 2)
        else:
            final_values[f'eps_{year}_high'] = None
            final_values[f'eps_{year}_low'] = None
            final_values[f'eps_{year}_avg'] = None
    
    # Process target price
    target_prices = data.get('target_price_values', [])
    final_values['target_price'] = round(sum(target_prices) / len(target_prices), 2) if target_prices else None
    
    # Process analyst count (take max as most recent)
    analyst_counts = data.get('analyst_count_values', [])
    final_values['analyst_count'] = max(analyst_counts) if analyst_counts else None
    
    return final_values

def calculate_quality_score_for_file(data: Dict[str, Any]) -> int:
    """Calculate quality score for individual MD file - v3.3.0"""
    score = 1  # Base score
    
    # Check EPS data availability (main indicator)
    eps_years_with_data = 0
    for year in ['2025', '2026', '2027']:
        if data.get(f'eps_{year}_avg') is not None:
            eps_years_with_data += 1
    
    if eps_years_with_data >= 3:
        score = 4  # Excellent - all 3 years
    elif eps_years_with_data >= 2:
        score = 3  # Good - 2 years
    elif eps_years_with_data >= 1:
        score = 2  # Fair - 1 year
    
    # Bonus for additional data
    if data.get('target_price') is not None:
        score = min(4, score + 1)
    
    if data.get('analyst_count') is not None:
        score = min(4, score + 1)
    
    return max(1, min(4, score))

def determine_status_emoji(quality_score: int) -> str:
    """Determine status emoji based on quality score"""
    if quality_score >= 4:
        return "🟢 完整"
    elif quality_score >= 3:
        return "🟡 良好"
    elif quality_score >= 2:
        return "🟠 部分"
    else:
        return "🔴 不足"

# ============================================================================
# DATA DEDUPLICATION - v3.3.0
# ============================================================================

def deduplicate_financial_data(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deduplicate same financial data from different sources
    
    Logic: If multiple files have the same EPS/target price values, 
    they're likely the same data from different news sources
    """
    if not data_list:
        return {}
    
    # Collect all values for statistical analysis
    all_eps_2025 = []
    all_eps_2026 = []
    all_eps_2027 = []
    all_target_prices = []
    all_analyst_counts = []
    
    for data in data_list:
        if data.get('eps_2025_avg') is not None:
            all_eps_2025.append(data['eps_2025_avg'])
        if data.get('eps_2026_avg') is not None:
            all_eps_2026.append(data['eps_2026_avg'])
        if data.get('eps_2027_avg') is not None:
            all_eps_2027.append(data['eps_2027_avg'])
        if data.get('target_price') is not None:
            all_target_prices.append(data['target_price'])
        if data.get('analyst_count') is not None:
            all_analyst_counts.append(data['analyst_count'])
    
    # Calculate deduplicated values
    deduplicated = {}
    
    # For EPS: if all values are the same, use that; otherwise use average
    for year, values in [('2025', all_eps_2025), ('2026', all_eps_2026), ('2027', all_eps_2027)]:
        if values:
            unique_values = list(set(values))
            if len(unique_values) == 1:
                # All same - likely duplicate data
                deduplicated[f'eps_{year}_avg'] = unique_values[0]
                deduplicated[f'eps_{year}_high'] = unique_values[0]
                deduplicated[f'eps_{year}_low'] = unique_values[0]
            else:
                # Different values - calculate statistics
                deduplicated[f'eps_{year}_avg'] = round(sum(values) / len(values), 2)
                deduplicated[f'eps_{year}_high'] = round(max(values), 2)
                deduplicated[f'eps_{year}_low'] = round(min(values), 2)
    
    # For target price: average if different, same if identical
    if all_target_prices:
        unique_prices = list(set(all_target_prices))
        if len(unique_prices) == 1:
            deduplicated['target_price'] = unique_prices[0]
        else:
            deduplicated['target_price'] = round(sum(all_target_prices) / len(all_target_prices), 2)
    
    # For analyst count: take the maximum (most recent/comprehensive)
    if all_analyst_counts:
        deduplicated['analyst_count'] = max(all_analyst_counts)
    
    return deduplicated

# ============================================================================
# PORTFOLIO SUMMARY GENERATION - v3.3.0
# ============================================================================

def generate_portfolio_summary_v330(config: Dict, watchlist_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Generate Portfolio Summary with proper MD file aggregation - v3.3.0"""
    print("📋 Generating Portfolio Summary (v3.3.0 format with MD aggregation)...")
    
    md_dir = Path(config['output']['md_dir'])
    if not md_dir.exists():
        print(f"❌ MD directory not found: {md_dir}")
        return pd.DataFrame(columns=PORTFOLIO_SUMMARY_COLUMNS)
    
    # Load watchlist for company mapping
    if watchlist_df is None:
        watchlist_df = load_watchlist()
    
    company_mapping = get_company_mapping_from_watchlist(watchlist_df)
    
    # Group MD files by company code
    company_files = {}
    for md_file in md_dir.glob("*.md"):
        company_code = extract_company_code_from_filename(md_file.name)
        if company_code and company_code in company_mapping:
            if company_code not in company_files:
                company_files[company_code] = []
            company_files[company_code].append(md_file)
    
    print(f"📊 Found MD files for {len(company_files)} companies")
    
    summary_data = []
    
    # Process each company in watchlist
    for company_code, company_info in company_mapping.items():
        md_files = company_files.get(company_code, [])
        
        if not md_files:
            # Company with no data
            summary_row = {
                '代號': company_code,
                '名稱': company_info['name'],
                '股票代號': company_info['stock_code'],
                'MD最舊日期': '',
                'MD最新日期': '',
                'MD資料筆數': 0,
                '分析師數量': 0,
                '目標價': '',
                '2025EPS平均值': '',
                '2026EPS平均值': '',
                '2027EPS平均值': '',
                '品質評分': 0,
                '狀態': "🔴 無資料",
                '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            summary_data.append(summary_row)
            continue
        
        # Process all MD files for this company
        file_data_list = []
        file_dates = []
        
        for md_file in md_files:
            file_data = extract_financial_data_from_md_file(md_file)
            if file_data:
                file_data_list.append(file_data)
                if file_data.get('file_date'):
                    file_dates.append(file_data['file_date'])
        
        # Calculate aggregated data
        if file_data_list:
            # Deduplicate and aggregate financial data
            aggregated_data = deduplicate_financial_data(file_data_list)
            
            # Calculate date range
            oldest_date = min(file_dates).strftime('%Y/%m/%d') if file_dates else ''
            newest_date = max(file_dates).strftime('%Y/%m/%d') if file_dates else ''
            
            # Calculate overall quality score for company
            file_scores = [calculate_quality_score_for_file(data) for data in file_data_list]
            overall_quality = max(file_scores) if file_scores else 1
            
            summary_row = {
                '代號': company_code,
                '名稱': company_info['name'],
                '股票代號': company_info['stock_code'],
                'MD最舊日期': oldest_date,
                'MD最新日期': newest_date,
                'MD資料筆數': len(md_files),
                '分析師數量': aggregated_data.get('analyst_count', 0) or 0,
                '目標價': aggregated_data.get('target_price', ''),
                '2025EPS平均值': aggregated_data.get('eps_2025_avg', ''),
                '2026EPS平均值': aggregated_data.get('eps_2026_avg', ''),
                '2027EPS平均值': aggregated_data.get('eps_2027_avg', ''),
                '品質評分': overall_quality,
                '狀態': determine_status_emoji(overall_quality),
                '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            summary_data.append(summary_row)
        
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            print(f"   ✅ {company_info['name']} ({company_code}): {len(md_files)} files")
    
    # Create DataFrame
    summary_df = pd.DataFrame(summary_data, columns=PORTFOLIO_SUMMARY_COLUMNS)
    
    # Clean numeric columns
    numeric_columns = ['MD資料筆數', '分析師數量', '品質評分']
    for col in numeric_columns:
        summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').fillna(0).astype(int)
    
    # Clean float columns
    float_columns = ['目標價', '2025EPS平均值', '2026EPS平均值', '2027EPS平均值']
    for col in float_columns:
        summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce')
    
    # Save portfolio summary
    output_file = config['output']['summary_csv']
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        summary_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Portfolio Summary saved: {output_file}")
        print(f"📊 Format: {len(summary_df)} companies in v3.3.0 format")
        
        # Quality statistics
        companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
        avg_quality = summary_df[summary_df['品質評分'] > 0]['品質評分'].mean()
        
        print(f"   📈 Companies with data: {companies_with_data}/{len(summary_df)}")
        if avg_quality > 0:
            print(f"   🎯 Average quality score: {avg_quality:.1f}/4.0")
        
    except Exception as e:
        print(f"❌ Error saving portfolio summary: {e}")
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            traceback.print_exc()
    
    return summary_df

# ============================================================================
# DETAILED DATA GENERATION - v3.3.0 (One row per MD file)
# ============================================================================

def generate_detailed_data_v330(config: Dict, watchlist_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Generate Detailed Data with one row per MD file - v3.3.0"""
    print("📋 Generating Detailed Data (v3.3.0 format - one row per MD file)...")
    
    md_dir = Path(config['output']['md_dir'])
    if not md_dir.exists():
        return pd.DataFrame(columns=DETAILED_DATA_COLUMNS)
    
    if watchlist_df is None:
        watchlist_df = load_watchlist()
    
    company_mapping = get_company_mapping_from_watchlist(watchlist_df)
    
    detailed_data = []
    
    # Process each MD file individually
    for md_file in md_dir.glob("*.md"):
        company_code = extract_company_code_from_filename(md_file.name)
        
        if not company_code or company_code not in company_mapping:
            continue
        
        company_info = company_mapping[company_code]
        
        # Extract data from this specific file
        file_data = extract_financial_data_from_md_file(md_file)
        
        if file_data:
            quality_score = calculate_quality_score_for_file(file_data)
            file_date = file_data.get('file_date')
            
            detailed_row = {
                '代號': company_code,
                '名稱': company_info['name'],
                '股票代號': company_info['stock_code'],
                'MD日期': file_date.strftime('%Y/%m/%d') if file_date else '',
                '分析師數量': file_data.get('analyst_count', 0) or 0,
                '目標價': file_data.get('target_price', ''),
                '2025EPS最高值': file_data.get('eps_2025_high', ''),
                '2025EPS最低值': file_data.get('eps_2025_low', ''),
                '2025EPS平均值': file_data.get('eps_2025_avg', ''),
                '2026EPS最高值': file_data.get('eps_2026_high', ''),
                '2026EPS最低值': file_data.get('eps_2026_low', ''),
                '2026EPS平均值': file_data.get('eps_2026_avg', ''),
                '2027EPS最高值': file_data.get('eps_2027_high', ''),
                '2027EPS最低值': file_data.get('eps_2027_low', ''),
                '2027EPS平均值': file_data.get('eps_2027_avg', ''),
                '品質評分': quality_score,
                '狀態': determine_status_emoji(quality_score),
                'MD File': f"data/md/{md_file.name}",
                '更新日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            detailed_data.append(detailed_row)
    
    # Create DataFrame
    detailed_df = pd.DataFrame(detailed_data, columns=DETAILED_DATA_COLUMNS)
    
    # Clean numeric columns
    numeric_columns = ['分析師數量', '品質評分']
    for col in numeric_columns:
        detailed_df[col] = pd.to_numeric(detailed_df[col], errors='coerce').fillna(0).astype(int)
    
    # Clean float columns
    float_columns = [col for col in DETAILED_DATA_COLUMNS if 'EPS' in col or col == '目標價']
    for col in float_columns:
        if col in detailed_df.columns:
            detailed_df[col] = pd.to_numeric(detailed_df[col], errors='coerce')
    
    # Save detailed data
    output_file = os.path.join(config['output']['processed_dir'], 'detailed_data.csv')
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        detailed_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Detailed Data saved: {output_file}")
        print(f"📊 Format: {len(detailed_df)} MD files in v3.3.0 format")
        
        if len(detailed_df) > 0:
            # File-level statistics
            companies_represented = detailed_df['代號'].nunique()
            avg_quality = detailed_df['品質評分'].mean()
            
            print(f"   📈 MD files processed: {len(detailed_df)}")
            print(f"   🏢 Companies represented: {companies_represented}")
            print(f"   🎯 Average file quality: {avg_quality:.1f}/4.0")
        
    except Exception as e:
        print(f"❌ Error saving detailed data: {e}")
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            traceback.print_exc()
    
    return detailed_df

# ============================================================================
# MAIN PROCESSING PIPELINE - v3.3.0
# ============================================================================

def process_all_data_v330(config_file: Optional[str] = None, force: bool = False, 
                          parse_md: bool = True) -> bool:
    """Process all data through the complete v3.3.0 pipeline"""
    print(f"🔧 Starting v3.3.0 data processing pipeline...")
    
    # Load configuration
    if config_file:
        config = config_module.load_config_v330(config_file)
    else:
        config = config_module.load_config_v330()
    
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
        # Step 1: Generate Portfolio Summary (v3.3.0 with aggregation)
        print("\n📋 Generating Portfolio Summary (v3.3.0 with MD aggregation)...")
        summary_df = generate_portfolio_summary_v330(config, watchlist_df)
        
        if summary_df.empty:
            print("❌ Failed to generate portfolio summary")
            return False
        
        success_count += 1
        print("✅ Portfolio Summary completed (v3.3.0 format)")
        
        # Step 2: Generate Detailed Data (v3.3.0 - one row per MD file)
        print("\n📊 Generating Detailed Data (v3.3.0 - one row per MD file)...")
        detailed_df = generate_detailed_data_v330(config, watchlist_df)
        
        if detailed_df.empty:
            print("⚠️ No detailed data generated")
        else:
            success_count += 1
            print("✅ Detailed Data completed (v3.3.0 format)")
        
        # Step 3: Generate Enhanced Statistics
        print("\n📈 Generating Enhanced Statistics...")
        stats = generate_statistics_v330(summary_df, detailed_df, config)
        
        success_count += 1
        print("✅ Statistics generation completed")
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 V3.3.0 DATA PROCESSING SUMMARY")
        print("="*60)
        print(f"✅ Processing complete: {success_count}/{total_steps} steps successful")
        print(f"🎯 Companies in portfolio: {len(summary_df)}")
        print(f"📄 Individual MD files: {len(detailed_df)}")
        
        # Enhanced statistics
        companies_with_data = len(summary_df[summary_df['MD資料筆數'] > 0])
        if companies_with_data > 0:
            print(f"📈 Companies with data: {companies_with_data}")
            avg_files_per_company = summary_df[summary_df['MD資料筆數'] > 0]['MD資料筆數'].mean()
            print(f"📊 Average files per company: {avg_files_per_company:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ v3.3.0 data processing failed: {e}")
        if hasattr(utils, 'is_debug_mode') and utils.is_debug_mode():
            traceback.print_exc()
        return False

def generate_statistics_v330(summary_df: pd.DataFrame, detailed_df: pd.DataFrame, config: Dict) -> Dict:
    """Generate comprehensive statistics for v3.3.0"""
    stats = {
        'generated_at': datetime.now().isoformat(),
        'guideline_version': '3.3.0',
        'total_companies': len(summary_df),
        'companies_with_data': len(summary_df[summary_df['MD資料筆數'] > 0]),
        'total_md_files': len(detailed_df),
        'data_quality': {},
        'file_level_stats': {},
        'company_level_stats': {}
    }
    
    # Company-level statistics
    if not summary_df.empty:
        stats['company_level_stats'] = {
            'companies_with_target_price': len(summary_df[summary_df['目標價'].notna()]),
            'companies_with_analyst_data': len(summary_df[summary_df['分析師數量'] > 0]),
            'average_quality_score': summary_df[summary_df['品質評分'] > 0]['品質評分'].mean(),
            'average_files_per_company': summary_df[summary_df['MD資料筆數'] > 0]['MD資料筆數'].mean()
        }
    
    # File-level statistics  
    if not detailed_df.empty:
        stats['file_level_stats'] = {
            'files_with_eps_data': len(detailed_df[detailed_df['2025EPS平均值'].notna()]),
            'files_with_target_price': len(detailed_df[detailed_df['目標價'].notna()]),
            'average_file_quality': detailed_df['品質評分'].mean(),
            'quality_distribution': detailed_df['品質評分'].value_counts().to_dict()
        }
    
    # Save statistics
    output_file = config['output']['stats_json']
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Statistics saved: {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving statistics: {e}")
    
    return stats

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for v3.3.0 processing"""
    print(f"📊 Data Processor v{__version__} (v3.3.0 Guideline Compliant)")
    
    success = process_all_data_v330(force=True, parse_md=True)
    
    if success:
        print("✅ v3.3.0 data processing completed successfully!")
        print("📋 Generated files:")
        print("   - portfolio_summary.csv (v3.3.0 aggregated format)")
        print("   - detailed_data.csv (v3.3.0 one-row-per-file format)")
        print("   - statistics.json (Enhanced v3.3.0 metrics)")
    else:
        print("❌ v3.3.0 data processing failed")
    
    return success

if __name__ == "__main__":
    main()