#!/usr/bin/env python3
"""
Quarantine MD Files Script
Moves problematic MD files to quarantine directory

Quarantine Criteria (Optional Filters):
  - Old files (--days X: older than X days)
  - Low quality files (--max-quality N: quality_score <= N)

Always Checked:
  - Inflated quality scores (high score but no actual data)
  - Inconsistent quality metadata (quality_score ≠ 品質評分)

Performance:
  - Optimized single-pass file reading
  - Real-time progress indicators
  - ETA and processing speed display

Usage:
    python quarantine_files.py                        # Check inflated/inconsistent only
    python quarantine_files.py --quarantine           # Actually move files
    python quarantine_files.py --days 90              # Add age filter (>90 days)
    python quarantine_files.py --max-quality 5        # Add quality filter (≤5)
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

    def __init__(self, days_threshold: int = None, max_quality: float = None):
        self.data_dir = Path("data/md")
        self.quarantine_base_dir = Path("data/quarantine")
        self.quarantine_base_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different quarantine reasons
        self.quarantine_dirs = {
            'old': self.quarantine_base_dir / 'old',
            'inflated_quality': self.quarantine_base_dir / 'inflated_quality',
            'inconsistent': self.quarantine_base_dir / 'inconsistent',
            'low_quality': self.quarantine_base_dir / 'low_quality'
        }

        # Create all subdirectories
        for qdir in self.quarantine_dirs.values():
            qdir.mkdir(parents=True, exist_ok=True)

        self.days_threshold = days_threshold
        self.max_quality = max_quality

        # Only calculate cutoff_date if days_threshold is specified
        if self.days_threshold is not None:
            self.cutoff_date = datetime.now() - timedelta(days=days_threshold)
            print(f"[INFO] Age threshold: {days_threshold} days")
            print(f"[INFO] Cutoff date: {self.cutoff_date.strftime('%Y-%m-%d')}")
        else:
            self.cutoff_date = None

        if self.max_quality is not None:
            print(f"[INFO] Quality threshold: {self.max_quality}")

        # Build filter description
        filters = []
        if self.cutoff_date is not None:
            filters.append(f"older than {days_threshold} days")
        if self.max_quality is not None:
            filters.append(f"quality <= {self.max_quality}")

        if filters:
            print(f"[INFO] Quarantine criteria: {' OR '.join(filters)}")
        else:
            print(f"[INFO] No age/quality filters - will check for inflated/inconsistent quality scores only")

        # Always check for inflated/inconsistent scores
        print(f"[INFO] Always checking: inflated quality scores, inconsistent metadata\n")

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

    def extract_quality_score(self, filepath: Path) -> tuple[float, bool]:
        """
        Extract quality_score or 品質評分 from MD file
        Returns: (quality_score, is_consistent)
        - is_consistent=False if both fields exist but have different values
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(2000)

            # Extract both field names if they exist
            en_match = re.search(r'quality_score:\s*([0-9]+(?:\.[0-9]+)?)', content)
            zh_match = re.search(r'品質評分:\s*([0-9]+(?:\.[0-9]+)?)', content)

            en_score = float(en_match.group(1)) if en_match else None
            zh_score = float(zh_match.group(1)) if zh_match else None

            # Check for inconsistency
            if en_score is not None and zh_score is not None:
                if abs(en_score - zh_score) > 0.01:  # Allow tiny float differences
                    print(f"[WARNING] Inconsistent quality scores in {filepath.name}: "
                          f"quality_score={en_score}, 品質評分={zh_score}")
                    return (en_score, False)  # Return English version but mark as inconsistent

            # Return whichever score exists
            if en_score is not None:
                return (en_score, True)
            if zh_score is not None:
                return (zh_score, True)

        except Exception as e:
            print(f"[ERROR] Failed to extract quality score from {filepath.name}: {e}")
        return (-1.0, True)

    def extract_stock_info(self, filename: str) -> Tuple[str, str]:
        """Extract stock code and company name from filename"""
        match = re.match(r'(\d{4})_([^_]+)_', filename)
        if match:
            return match.group(1), match.group(2)
        return "Unknown", "Unknown"

    def has_actual_data(self, filepath: Path) -> bool:
        """
        Check if file has actual FactSet data (EPS, analysts, target price)
        Returns True if data found, False if missing
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for EPS data patterns
            eps_patterns = [
                r'EPS.*?(\d{4}).*?(\d+\.?\d*)',  # EPS with year and value
                r'每股盈餘.*?(\d+\.?\d*)',
                r'earnings.*?per.*?share',
            ]

            # Check for analyst count
            analyst_patterns = [
                r'(\d+).*?位?分析師',
                r'(\d+).*?analysts?',
                r'分析師.*?(\d+)',
            ]

            # Check for target price
            target_patterns = [
                r'目標價.*?(\d+\.?\d*)',
                r'target.*?price.*?(\d+\.?\d*)',
                r'NT\$?\s*(\d+\.?\d*)',
            ]

            has_eps = any(re.search(pattern, content, re.IGNORECASE) for pattern in eps_patterns)
            has_analysts = any(re.search(pattern, content, re.IGNORECASE) for pattern in analyst_patterns)
            has_target = any(re.search(pattern, content, re.IGNORECASE) for pattern in target_patterns)

            # Also check for FactSet specific content
            has_factset = 'factset' in content.lower() or 'FactSet' in content

            return has_eps or has_analysts or has_target or has_factset

        except Exception as e:
            print(f"[ERROR] Failed to check data in {filepath.name}: {e}")
            return True  # Assume has data if we can't check

    def extract_all_info(self, filepath: Path) -> Dict:
        """
        Optimized: Extract all information from MD file in ONE read
        Returns: dict with date_obj, date_str, quality_score, is_consistent, has_data
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()  # Read file ONCE

            # Extract date (from first 2000 chars)
            header = content[:2000]

            # Look for md_date in YAML frontmatter
            md_date_match = re.search(r'md_date:\s*(\d{4})/(\d{1,2})/(\d{1,2})', header)
            if md_date_match:
                year, month, day = md_date_match.groups()
                date_str = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
                date_obj = datetime(int(year), int(month), int(day))
            else:
                # Fallback: Look for extracted_date
                extracted_match = re.search(r'extracted_date:\s*(\d{4})-(\d{2})-(\d{2})', header)
                if extracted_match:
                    year, month, day = extracted_match.groups()
                    date_str = f"{year}/{month}/{day}"
                    date_obj = datetime(int(year), int(month), int(day))
                else:
                    # Fallback: Use file modification time
                    mtime = filepath.stat().st_mtime
                    date_obj = datetime.fromtimestamp(mtime)
                    date_str = date_obj.strftime('%Y/%m/%d') + " (file mtime)"

            # Extract quality scores
            en_match = re.search(r'quality_score:\s*([0-9]+(?:\.[0-9]+)?)', header)
            zh_match = re.search(r'品質評分:\s*([0-9]+(?:\.[0-9]+)?)', header)

            en_score = float(en_match.group(1)) if en_match else None
            zh_score = float(zh_match.group(1)) if zh_match else None

            # Check for inconsistency
            is_consistent = True
            if en_score is not None and zh_score is not None:
                if abs(en_score - zh_score) > 0.01:
                    is_consistent = False

            # Get final quality score
            quality_score = en_score if en_score is not None else (zh_score if zh_score is not None else -1.0)

            # Check for actual data (use full content)
            eps_patterns = [
                r'EPS.*?(\d{4}).*?(\d+\.?\d*)',
                r'每股盈餘.*?(\d+\.?\d*)',
                r'earnings.*?per.*?share',
            ]
            analyst_patterns = [
                r'(\d+).*?位?分析師',
                r'(\d+).*?analysts?',
                r'分析師.*?(\d+)',
            ]
            target_patterns = [
                r'目標價.*?(\d+\.?\d*)',
                r'target.*?price.*?(\d+\.?\d*)',
                r'NT\$?\s*(\d+\.?\d*)',
            ]

            has_eps = any(re.search(pattern, content, re.IGNORECASE) for pattern in eps_patterns)
            has_analysts = any(re.search(pattern, content, re.IGNORECASE) for pattern in analyst_patterns)
            has_target = any(re.search(pattern, content, re.IGNORECASE) for pattern in target_patterns)
            has_factset = 'factset' in content.lower() or 'FactSet' in content

            has_data = has_eps or has_analysts or has_target or has_factset

            return {
                'date_obj': date_obj,
                'date_str': date_str,
                'quality_score': quality_score,
                'is_consistent': is_consistent,
                'has_data': has_data
            }

        except Exception as e:
            print(f"[ERROR] Failed to extract info from {filepath.name}: {e}")
            return {
                'date_obj': datetime(2020, 1, 1),
                'date_str': "2020/01/01 (error)",
                'quality_score': -1.0,
                'is_consistent': True,
                'has_data': True
            }

    def _get_quarantine_reasons(self, date_obj: datetime, quality_score: float, is_consistent: bool, has_data: bool = True) -> List[str]:
        reasons = []
        # Check for data inconsistency first
        if not is_consistent:
            reasons.append("inconsistent_quality")
        # Check for inflated quality score (high score but no actual data)
        if quality_score >= 7.0 and not has_data:
            reasons.append("inflated_quality")
        # Only check age if days_threshold was specified
        if self.cutoff_date is not None and date_obj < self.cutoff_date:
            reasons.append("old")
        # Only check quality if max_quality was specified
        if self.max_quality is not None and quality_score >= 0 and quality_score <= self.max_quality:
            reasons.append("low_quality")
        return reasons

    def scan_old_files(self) -> List[Dict]:
        """Scan for MD files older than threshold"""
        results = []

        md_files = list(self.data_dir.glob("*.md"))
        total_files = len(md_files)
        print(f"[INFO] Scanning {total_files} MD files...\n")

        # Progress tracking
        progress_interval = max(10, total_files // 10)  # Show progress every 10% or every 10 files
        start_time = datetime.now()

        for idx, filepath in enumerate(md_files, 1):
            # Show progress indicators
            if idx % progress_interval == 0 or idx == total_files:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total_files - idx) / rate if rate > 0 else 0
                print(f"[PROGRESS] {idx}/{total_files} files ({idx*100//total_files}%) | "
                      f"{rate:.1f} files/sec | ETA: {eta:.0f}s")

            # Extract all info in ONE read (optimized!)
            info = self.extract_all_info(filepath)
            date_obj = info['date_obj']
            date_str = info['date_str']
            quality_score = info['quality_score']
            is_consistent = info['is_consistent']
            has_data = info['has_data']

            # Check quarantine reasons
            reasons = self._get_quarantine_reasons(date_obj, quality_score, is_consistent, has_data)

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
                    'has_data': has_data,
                    'reasons': reasons
                })

        # Final summary
        total_time = (datetime.now() - start_time).total_seconds()
        print(f"\n[INFO] Scan completed in {total_time:.1f}s ({total_files/total_time:.1f} files/sec)")
        print(f"[INFO] Found {len(results)} files matching quarantine criteria\n")

        return results

    def generate_report(self, results: List[Dict]) -> str:
        """Generate detailed report of old files"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("QUARANTINE REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if self.cutoff_date is not None:
            report_lines.append(f"Age threshold: {self.days_threshold} days (cutoff: {self.cutoff_date.strftime('%Y-%m-%d')})")
        if self.max_quality is not None:
            report_lines.append(f"Quality threshold: <= {self.max_quality}")
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
        inflated_count = sum(1 for r in results if "inflated_quality" in r['reasons'])
        if inflated_count > 0:
            report_lines.append(f"Inflated quality scores (high score, no data): {inflated_count}")
        inconsistent_count = sum(1 for r in results if "inconsistent_quality" in r['reasons'])
        if inconsistent_count > 0:
            report_lines.append(f"Inconsistent quality scores: {inconsistent_count}")
        oldest = max(results, key=lambda x: x['age_days'])
        report_lines.append(f"Oldest file: {oldest['filename']} ({oldest['age_days']} days)")

        return '\n'.join(report_lines)

    def quarantine_files(self, results: List[Dict]) -> int:
        """Move files to quarantine, organized by reason"""
        moved_count = 0

        # Track counts by reason
        reason_counts = {reason: 0 for reason in self.quarantine_dirs.keys()}

        for result in results:
            filepath = result['filepath']
            date_obj = result['date_obj']
            reasons = result['reasons']

            # Determine primary quarantine reason (priority order)
            # Priority: inconsistent > inflated_quality > low_quality > old
            primary_reason = None
            if 'inconsistent_quality' in reasons:
                primary_reason = 'inconsistent'
            elif 'inflated_quality' in reasons:
                primary_reason = 'inflated_quality'
            elif 'low_quality' in reasons:
                primary_reason = 'low_quality'
            elif 'old' in reasons:
                primary_reason = 'old'

            if primary_reason:
                # Get the appropriate quarantine directory
                base_dir = self.quarantine_dirs[primary_reason]

                # Create subdirectory by year-month within the reason directory
                month_dir = base_dir / date_obj.strftime('%Y-%m')
                month_dir.mkdir(exist_ok=True)

                dest_path = month_dir / filepath.name

                try:
                    shutil.move(str(filepath), str(dest_path))
                    reason_counts[primary_reason] += 1
                    print(f"[OK] Moved: {filepath.name} -> {primary_reason}/{month_dir.name}/")
                    moved_count += 1
                except Exception as e:
                    print(f"[ERROR] Failed to move {filepath.name}: {e}")

        # Print summary
        print(f"\n[SUMMARY] Files moved by reason:")
        for reason, count in reason_counts.items():
            if count > 0:
                print(f"  {reason}: {count} files")

        return moved_count


def main():
    parser = argparse.ArgumentParser(
        description='Quarantine problematic MD files (inflated/inconsistent quality, optional age/quality filters)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quarantine_files.py                 # Check inflated/inconsistent only
  python quarantine_files.py --days 60       # Add age filter (>60 days)
  python quarantine_files.py --max-quality 5 # Add quality filter (≤5)
  python quarantine_files.py --quarantine    # Actually move files
  python quarantine_files.py --days 180 --quarantine  # Age filter + move
        """
    )

    parser.add_argument('--quarantine', action='store_true',
                       help='Actually move files to quarantine (default: report only)')
    parser.add_argument('--days', type=int, default=None,
                       help='Age threshold in days (omit to ignore age)')
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
            print(f"\n[OK] Quarantined {moved} files to: {quarantiner.quarantine_base_dir}/")
            print(f"[INFO] Files organized by reason: old/, inflated_quality/, inconsistent/, low_quality/")
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
