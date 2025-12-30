#!/usr/bin/env python3
"""
Quarantine Old MD Files Script
Moves MD files older than 3 months to quarantine directory

Usage:
    python quarantine_files.py                        # Scan and report only
    python quarantine_files.py --quarantine           # Actually move files
    python quarantine_files.py --days 90              # Custom age threshold
    python quarantine_files.py --max-quality 5        # Quarantine low-quality files
    python quarantine_files.py --days 90 --max-quality 5 --quarantine
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class OldFileQuarantiner:
    """Quarantine MD files older than specified threshold"""

    def __init__(self, days_threshold: int = 90, max_quality: float = None):
        self.data_dir = Path("data/md")
        self.quarantine_dir = Path("data/quarantine/old_files")
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.days_threshold = days_threshold
        self.max_quality = max_quality
        self.cutoff_date = datetime.now() - timedelta(days=days_threshold)

        print(f"[INFO] Quarantine threshold: {days_threshold} days")
        print(f"[INFO] Cutoff date: {self.cutoff_date.strftime('%Y-%m-%d')}")
        if self.max_quality is not None:
            print(f"[INFO] Max quality threshold: {self.max_quality}")
        print(f"[INFO] Files older than cutoff or below quality will be quarantined\n")

    def extract_md_date(self, filepath: Path) -> Tuple[datetime, str]:
        """Extract md_date from MD file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # Read first 2000 chars for metadata

            # Look for md_date in YAML frontmatter
            md_date_match = re.search(r'md_date:\s*(\d{4})/(\d{1,2})/(\d{1,2})', content)
            if md_date_match:
                year, month, day = md_date_match.groups()
                date_str = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj, date_str

            # Fallback: Look for extracted_date
            extracted_match = re.search(r'extracted_date:\s*(\d{4})-(\d{2})-(\d{2})', content)
            if extracted_match:
                year, month, day = extracted_match.groups()
                date_str = f"{year}/{month}/{day}"
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj, date_str

            # Fallback: Use file modification time
            mtime = filepath.stat().st_mtime
            date_obj = datetime.fromtimestamp(mtime)
            date_str = date_obj.strftime('%Y/%m/%d')
            return date_obj, f"{date_str} (file mtime)"

        except Exception as e:
            print(f"[ERROR] Failed to extract date from {filepath.name}: {e}")
            # Return very old date to be safe
            return datetime(2020, 1, 1), "2020/01/01 (error)"

    def extract_quality_score(self, filepath: Path) -> float:
        """Extract quality_score from MD file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(2000)
            match = re.search(r'quality_score:\s*([0-9]+(?:\.[0-9]+)?)', content)
            if match:
                return float(match.group(1))
        except Exception as e:
            print(f"[ERROR] Failed to extract quality score from {filepath.name}: {e}")
        return -1.0

    def extract_stock_info(self, filename: str) -> Tuple[str, str]:
        """Extract stock code and company name from filename"""
        match = re.match(r'(\d{4})_([^_]+)_', filename)
        if match:
            return match.group(1), match.group(2)
        return "Unknown", "Unknown"

    def _get_quarantine_reasons(self, date_obj: datetime, quality_score: float) -> List[str]:
        reasons = []
        if date_obj < self.cutoff_date:
            reasons.append("old")
        if self.max_quality is not None and quality_score >= 0 and quality_score <= self.max_quality:
            reasons.append("low_quality")
        return reasons

    def scan_old_files(self) -> List[Dict]:
        """Scan for MD files older than threshold"""
        results = []

        md_files = list(self.data_dir.glob("*.md"))
        print(f"[INFO] Scanning {len(md_files)} MD files...\n")

        for filepath in md_files:
            date_obj, date_str = self.extract_md_date(filepath)
            quality_score = self.extract_quality_score(filepath)
            reasons = self._get_quarantine_reasons(date_obj, quality_score)

            if reasons:
                stock_code, company_name = self.extract_stock_info(filepath.name)
                age_days = (datetime.now() - date_obj).days

                results.append({
                    'filepath': filepath,
                    'filename': filepath.name,
                    'stock_code': stock_code,
                    'company_name': company_name,
                    'md_date': date_str,
                    'date_obj': date_obj,
                    'age_days': age_days,
                    'quality_score': quality_score,
                    'reasons': reasons
                })

        return results

    def generate_report(self, results: List[Dict]) -> str:
        """Generate detailed report of old files"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("OLD FILES QUARANTINE REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Threshold: {self.days_threshold} days (cutoff: {self.cutoff_date.strftime('%Y-%m-%d')})")
        if self.max_quality is not None:
            report_lines.append(f"Max quality: {self.max_quality}")
        report_lines.append("=" * 80)
        report_lines.append("")

        if not results:
            report_lines.append("No old files found!")
            return '\n'.join(report_lines)

        report_lines.append(f"Total old files found: {len(results)}")
        report_lines.append("")

        # Group by stock code
        by_stock = {}
        for result in results:
            stock = result['stock_code']
            if stock not in by_stock:
                by_stock[stock] = []
            by_stock[stock].append(result)

        # Sort by stock code
        for stock, items in sorted(by_stock.items()):
            report_lines.append(f"\nStock: {stock} ({items[0]['company_name']})")
            report_lines.append(f"  Old files: {len(items)}")
            report_lines.append("")

            # Sort by age (oldest first)
            items.sort(key=lambda x: x['age_days'], reverse=True)

            for item in items[:5]:  # Show first 5 oldest
                report_lines.append(f"  File: {item['filename']}")
                report_lines.append(f"    Date: {item['md_date']}")
                report_lines.append(f"    Age: {item['age_days']} days")
                report_lines.append(f"    Quality: {item['quality_score']}")
                report_lines.append(f"    Reasons: {', '.join(item['reasons'])}")
                report_lines.append("")

            if len(items) > 5:
                report_lines.append(f"  ... and {len(items) - 5} more files")
                report_lines.append("")

        # Summary statistics
        report_lines.append("\n" + "=" * 80)
        report_lines.append("SUMMARY")
        report_lines.append("=" * 80)
        report_lines.append(f"Total stocks affected: {len(by_stock)}")
        report_lines.append(f"Total files to quarantine: {len(results)}")
        report_lines.append(f"Average age: {sum(r['age_days'] for r in results) / len(results):.1f} days")
        if self.max_quality is not None:
            low_quality_count = sum(1 for r in results if "low_quality" in r['reasons'])
            report_lines.append(f"Low quality files: {low_quality_count}")
        oldest = max(results, key=lambda x: x['age_days'])
        report_lines.append(f"Oldest file: {oldest['filename']} ({oldest['age_days']} days)")

        return '\n'.join(report_lines)

    def quarantine_files(self, results: List[Dict]) -> int:
        """Move old files to quarantine"""
        moved_count = 0

        # Group by month for organized quarantine
        for result in results:
            filepath = result['filepath']
            date_obj = result['date_obj']

            # Create subdirectory by year-month
            month_dir = self.quarantine_dir / date_obj.strftime('%Y-%m')
            month_dir.mkdir(exist_ok=True)

            dest_path = month_dir / filepath.name

            try:
                shutil.move(str(filepath), str(dest_path))
                print(f"[OK] Moved: {filepath.name} -> {month_dir.name}/")
                moved_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to move {filepath.name}: {e}")

        return moved_count


def main():
    parser = argparse.ArgumentParser(
        description='Quarantine old MD files (default: >90 days)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quarantine_files.py                 # Scan and report (90 days)
  python quarantine_files.py --days 60       # Use 60 days threshold
  python quarantine_files.py --quarantine    # Actually quarantine files
  python quarantine_files.py --days 180 --quarantine  # Quarantine >180 days
        """
    )

    parser.add_argument('--quarantine', action='store_true',
                       help='Actually move files to quarantine (default: report only)')
    parser.add_argument('--days', type=int, default=90,
                       help='Age threshold in days (default: 90)')
    parser.add_argument('--max-quality', type=float, default=None,
                       help='Quarantine files with quality_score <= max-quality')
    parser.add_argument('--output', type=str, default='old_files_report.txt',
                       help='Output report filename')

    args = parser.parse_args()

    print("=" * 80)
    print("OLD FILES QUARANTINE TOOL - FactSet Pipeline")
    print("=" * 80)
    print()

    # Scan for old files
    quarantiner = OldFileQuarantiner(days_threshold=args.days, max_quality=args.max_quality)
    results = quarantiner.scan_old_files()

    # Generate report
    report = quarantiner.generate_report(results)
    print(report)

    # Save report to file
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[OK] Report saved to: {args.output}")

    # Quarantine if requested
    if args.quarantine and results:
        print()
        print("=" * 80)
        response = input(f"Quarantine {len(results)} old files? (yes/no): ")

        if response.lower() in ['yes', 'y']:
            moved = quarantiner.quarantine_files(results)
            print(f"\n[OK] Quarantined {moved} files to: {quarantiner.quarantine_dir}")
        else:
            print("[INFO] Quarantine cancelled.")
    elif results and not args.quarantine:
        print()
        print("=" * 80)
        print("[INFO] Run with --quarantine flag to move these files.")

    print()
    print("[OK] Done!")


if __name__ == "__main__":
    main()
