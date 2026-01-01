#!/usr/bin/env python3
"""
Migrate files from old quarantine structure to new organized structure
From: data/quarantine/old_files/{year-month}/
To:   data/quarantine/{reason}/{year-month}/
"""

import os
import sys
import re
import shutil
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def extract_file_info(filepath):
    """Extract metadata to determine quarantine reason"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        header = content[:2000]

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

        quality_score = en_score if en_score is not None else (zh_score if zh_score is not None else -1.0)

        # Check for actual data
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
            'quality_score': quality_score,
            'is_consistent': is_consistent,
            'has_data': has_data
        }

    except Exception as e:
        print(f"[WARNING] Failed to extract info from {filepath.name}: {e}")
        return None


def determine_reason(info):
    """Determine primary quarantine reason (same priority as main script)"""
    if info is None:
        return 'old'  # Default to 'old' if we can't determine

    # Priority: inconsistent > inflated_quality > low_quality > old
    if not info['is_consistent']:
        return 'inconsistent'
    elif info['quality_score'] >= 7.0 and not info['has_data']:
        return 'inflated_quality'
    elif 0 <= info['quality_score'] <= 5:  # Assume low quality threshold was 5
        return 'low_quality'
    else:
        return 'old'


def migrate_files():
    """Migrate files from old structure to new structure"""
    old_base = Path("data/quarantine/old_files")
    new_base = Path("data/quarantine")

    if not old_base.exists():
        print(f"[INFO] No old quarantine directory found at {old_base}")
        return

    # Create new subdirectories
    new_dirs = {
        'old': new_base / 'old',
        'inflated_quality': new_base / 'inflated_quality',
        'inconsistent': new_base / 'inconsistent',
        'low_quality': new_base / 'low_quality'
    }

    for qdir in new_dirs.values():
        qdir.mkdir(parents=True, exist_ok=True)

    # Find all MD files
    md_files = list(old_base.glob("**/*.md"))
    total_files = len(md_files)

    print(f"[INFO] Found {total_files} files to migrate\n")

    # Track counts
    reason_counts = {reason: 0 for reason in new_dirs.keys()}
    failed_count = 0

    for idx, old_path in enumerate(md_files, 1):
        # Get the month directory (e.g., "2025-01")
        month_dir = old_path.parent.name

        # Extract file info and determine reason
        info = extract_file_info(old_path)
        reason = determine_reason(info)

        # Create destination path
        dest_dir = new_dirs[reason] / month_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / old_path.name

        # Move file
        try:
            shutil.move(str(old_path), str(dest_path))
            reason_counts[reason] += 1
            print(f"[{idx}/{total_files}] Moved: {old_path.name} -> {reason}/{month_dir}/")
        except Exception as e:
            print(f"[ERROR] Failed to move {old_path.name}: {e}")
            failed_count += 1

    # Print summary
    print(f"\n{'='*80}")
    print("MIGRATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total files processed: {total_files}")
    print(f"\nFiles by reason:")
    for reason, count in reason_counts.items():
        if count > 0:
            print(f"  {reason}: {count} files")
    if failed_count > 0:
        print(f"\nFailed: {failed_count} files")

    # Remove empty month directories
    print(f"\n[INFO] Cleaning up empty directories...")
    for month_dir in old_base.iterdir():
        if month_dir.is_dir() and not any(month_dir.iterdir()):
            month_dir.rmdir()
            print(f"[OK] Removed empty directory: {month_dir}")

    # Remove old_files directory if empty
    if not any(old_base.iterdir()):
        old_base.rmdir()
        print(f"[OK] Removed old quarantine directory: {old_base}")
        print(f"\n[SUCCESS] Migration complete! New structure at: {new_base}/")
    else:
        print(f"\n[WARNING] Old directory not empty: {old_base}")
        print(f"[INFO] Please check and manually remove if appropriate")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate quarantine files to new organized structure')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("="*80)
    print("QUARANTINE MIGRATION TOOL")
    print("="*80)
    print()

    if args.confirm:
        migrate_files()
    else:
        response = input("Migrate files from old structure to new organized structure? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            migrate_files()
        else:
            print("[INFO] Migration cancelled.")
