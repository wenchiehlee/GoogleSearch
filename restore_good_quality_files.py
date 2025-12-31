#!/usr/bin/env python3
"""
Restore Good Quality Files from Quarantine
Moves back files with quality_score > 6.5 from quarantine to data/md
Keeps only low-quality files (quality_score <= 6.5) in quarantine
"""

import os
import sys
import re
import shutil
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def extract_quality_score(filepath: Path) -> tuple:
    """
    Extract quality_score or 品質評分 from MD file
    Returns: (quality_score, is_consistent)
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
            if abs(en_score - zh_score) > 0.01:
                print(f"[WARNING] Inconsistent quality scores in {filepath.name}: "
                      f"quality_score={en_score}, 品質評分={zh_score}")
                return (en_score, False)

        # Return whichever score exists
        if en_score is not None:
            return (en_score, True)
        if zh_score is not None:
            return (zh_score, True)

    except Exception as e:
        print(f"[ERROR] Failed to extract quality score from {filepath.name}: {e}")
    return (-1.0, True)


def main():
    quarantine_base = Path("data/quarantine/old_files")
    target_dir = Path("data/md")

    if not quarantine_base.exists():
        print("[INFO] No quarantine directory found")
        return

    # Find all MD files in quarantine (including subdirectories)
    md_files = list(quarantine_base.glob("**/*.md"))

    print(f"[INFO] Found {len(md_files)} files in quarantine")
    print(f"[INFO] Quality threshold: > 6.5 will be restored\n")

    restored_count = 0
    kept_count = 0
    inconsistent_count = 0

    for filepath in md_files:
        quality_score, is_consistent = extract_quality_score(filepath)

        if not is_consistent:
            # Inconsistent quality scores - keep in quarantine
            print(f"[KEPT-INCONSISTENT] {filepath.name} (quality: {quality_score}, inconsistent)")
            kept_count += 1
            inconsistent_count += 1
        elif quality_score > 6.5:
            # Good quality - restore to data/md
            dest_path = target_dir / filepath.name
            try:
                shutil.move(str(filepath), str(dest_path))
                print(f"[RESTORED] {filepath.name} (quality: {quality_score})")
                restored_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to restore {filepath.name}: {e}")
        else:
            # Low quality or error - keep in quarantine
            print(f"[KEPT-LOW-QUALITY] {filepath.name} (quality: {quality_score})")
            kept_count += 1

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total files scanned: {len(md_files)}")
    print(f"Restored (quality > 6.5 and consistent): {restored_count}")
    print(f"Kept in quarantine (quality <= 6.5 or inconsistent): {kept_count}")
    if inconsistent_count > 0:
        print(f"  - Inconsistent quality scores: {inconsistent_count}")
        print(f"  - Low quality: {kept_count - inconsistent_count}")
    print(f"\n[OK] Done!")


if __name__ == "__main__":
    main()
