#!/usr/bin/env python3
"""
Quick Stock Verification Tool
Process and verify specific stocks only (for testing)

Usage:
    python verify_stocks.py 2330 2357              # Verify specific stocks
    python verify_stocks.py 2330 2357 --upload     # Verify and upload to sheets
"""

import os
import sys
import argparse
from pathlib import Path

# Set UTF-8 encoding for Windows console (only if not already set)
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add process_group to path
sys.path.insert(0, str(Path(__file__).parent / 'process_group'))

from md_scanner import MDScanner
from md_parser import MDParser
from quality_analyzer import QualityAnalyzer
from report_generator import ReportGenerator


def verify_stocks(stock_codes: list, upload: bool = False):
    """Quick verification for specific stocks"""

    print("=" * 80)
    print("QUICK STOCK VERIFICATION TOOL")
    print(f"Stocks to verify: {', '.join(stock_codes)}")
    print("=" * 80)
    print()

    # Initialize components
    print("[1/4] Initializing components...")
    scanner = MDScanner()
    parser = MDParser()
    analyzer = QualityAnalyzer()
    generator = ReportGenerator()
    print("[OK] Components ready\n")

    # Scan MD files for specified stocks only
    print(f"[2/4] Scanning MD files for stocks: {', '.join(stock_codes)}...")
    all_files = scanner.scan_all_md_files()

    # Filter to only specified stocks (check just the filename)
    filtered_files = [
        f for f in all_files
        if any(Path(f).name.startswith(f"{code}_") for code in stock_codes)
    ]

    print(f"[OK] Found {len(filtered_files)} files for specified stocks")
    print(f"     (Total files in directory: {len(all_files)})\n")

    if not filtered_files:
        print("[ERROR] No files found for specified stocks!")
        return

    # Parse files
    print(f"[3/4] Parsing {len(filtered_files)} files...")
    processed_companies = []

    for i, filename in enumerate(filtered_files, 1):
        print(f"     Processing ({i}/{len(filtered_files)}): {filename}")

        file_data = parser.parse_md_file(filename)
        if file_data:
            # Add quality analysis
            quality_analysis = analyzer.analyze(file_data)
            file_data.update(quality_analysis)
            processed_companies.append(file_data)

    print(f"[OK] Successfully parsed {len(processed_companies)} files\n")

    # Generate reports
    print("[4/4] Generating reports...")
    portfolio_summary = generator.generate_portfolio_summary(processed_companies)
    detailed_report = generator.generate_detailed_report(processed_companies)

    print(f"[OK] Portfolio summary: {len(portfolio_summary)} companies")
    print(f"[OK] Detailed report: {len(detailed_report)} records\n")

    # Display results
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    print()

    if len(portfolio_summary) > 0:
        print("Portfolio Summary:")
        print("-" * 80)

        # Display key columns
        display_cols = ['代號', '名稱', 'MD最舊日期', 'MD最新日期', 'MD資料筆數',
                       '分析師數量', '品質評分', '狀態']

        for _, row in portfolio_summary.iterrows():
            print(f"\nStock: {row['代號']} - {row['名稱']}")
            print(f"  MD Date Range: {row['MD最舊日期']} to {row['MD最新日期']}")
            print(f"  MD Files: {row['MD資料筆數']}")
            print(f"  Analysts: {row['分析師數量']}")
            print(f"  Quality: {row['品質評分']} - {row['狀態']}")

            # Show EPS data
            eps_cols = ['2025EPS平均值', '2026EPS平均值', '2027EPS平均值']
            eps_values = [str(row[col]) if row[col] and str(row[col]) != 'nan' else '-'
                         for col in eps_cols]
            print(f"  EPS Estimates: 2025={eps_values[0]}, 2026={eps_values[1]}, 2027={eps_values[2]}")
    else:
        print("[WARNING] No data in portfolio summary!")

    print()
    print("=" * 80)
    print("DETAILED FILES")
    print("=" * 80)

    # Group by stock
    for stock_code in stock_codes:
        stock_files = detailed_report[detailed_report['代號'] == stock_code]

        if len(stock_files) > 0:
            print(f"\nStock {stock_code}: {len(stock_files)} files")

            # Show newest and oldest
            sorted_files = stock_files.sort_values('MD日期', ascending=False)

            print(f"  Newest: {sorted_files.iloc[0]['MD日期']}")
            if len(sorted_files) > 1:
                print(f"  Oldest: {sorted_files.iloc[-1]['MD日期']}")

            # Show date distribution
            date_counts = sorted_files['MD日期'].value_counts().head(5)
            print(f"  Top MD dates ({len(date_counts)}):")
            for date, count in date_counts.items():
                print(f"    {date}: {count} files")
        else:
            print(f"\nStock {stock_code}: No files found!")

    # Save results
    print()
    print("=" * 80)
    output_dir = Path("data/reports/verification")
    output_dir.mkdir(parents=True, exist_ok=True)

    portfolio_file = output_dir / "portfolio_verification.csv"
    detailed_file = output_dir / "detailed_verification.csv"

    portfolio_summary.to_csv(portfolio_file, index=False, encoding='utf-8-sig')
    detailed_report.to_csv(detailed_file, index=False, encoding='utf-8-sig')

    print(f"[OK] Results saved to:")
    print(f"     {portfolio_file}")
    print(f"     {detailed_file}")

    print()
    print("=" * 80)
    print("[OK] Verification complete!")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Quick verification for specific stocks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python verify_stocks.py 2330                   # Verify single stock
  python verify_stocks.py 2330 2357              # Verify multiple stocks
  python verify_stocks.py 2330 2357 --upload     # Verify and upload
        """
    )

    parser.add_argument('stocks', nargs='+', help='Stock codes to verify (e.g., 2330 2357)')
    parser.add_argument('--upload', action='store_true', help='Upload to Google Sheets')

    args = parser.parse_args()

    verify_stocks(args.stocks, upload=args.upload)


if __name__ == "__main__":
    main()
