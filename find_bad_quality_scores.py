#!/usr/bin/env python3
"""
Find MD files with inflated quality scores (high score but no actual data)
"""
import os
import sys
import re
from pathlib import Path

def extract_yaml_quality_score(content):
    """Extract quality_score from YAML frontmatter"""
    match = re.search(r'^quality_score:\s*(\d+\.?\d*)$', content, re.MULTILINE)
    if match:
        return float(match.group(1))
    return None

def has_actual_data(content):
    """Check if file has actual FactSet data (EPS, analysts, target price)"""
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

def analyze_md_files(md_dir, min_quality_threshold=7.0):
    """Analyze all MD files and find those with inflated quality scores"""
    md_path = Path(md_dir)
    if not md_path.exists():
        print(f"[ERROR] Directory not found: {md_dir}")
        return []

    md_files = list(md_path.glob("*.md"))
    print(f"[INFO] Found {len(md_files)} MD files\n")

    problematic_files = []

    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            quality_score = extract_yaml_quality_score(content)
            if quality_score is None:
                continue

            # Only check files with high quality scores
            if quality_score >= min_quality_threshold:
                has_data = has_actual_data(content)

                if not has_data:
                    problematic_files.append({
                        'file': md_file.name,
                        'path': str(md_file),
                        'quality_score': quality_score
                    })

                    # Extract company info from filename
                    filename = md_file.name
                    parts = filename.replace('_factset_', ' ').replace('.md', '').split('_')
                    if len(parts) >= 2:
                        stock_code = parts[0]
                        company_name = parts[1]
                        print(f"[BAD] {stock_code} {company_name}: quality_score={quality_score} but NO actual data")
                        print(f"   File: {md_file.name}")
                        print()

        except Exception as e:
            print(f"[WARN] Error processing {md_file.name}: {e}")
            continue

    return problematic_files

if __name__ == "__main__":
    md_dir = "data/md"
    min_threshold = 7.0

    if len(sys.argv) > 1:
        md_dir = sys.argv[1]
    if len(sys.argv) > 2:
        min_threshold = float(sys.argv[2])

    print(f"[SCAN] Analyzing MD files in: {md_dir}")
    print(f"[SCAN] Quality score threshold: >= {min_threshold}")
    print(f"[SCAN] Looking for: High score but no EPS/analyst/target price data\n")
    print("=" * 70)
    print()

    problematic = analyze_md_files(md_dir, min_threshold)

    print("=" * 70)
    print(f"\n[SUMMARY] Total problematic files: {len(problematic)}")

    if problematic:
        print(f"\nTo remove these files:")
        for item in problematic:
            print(f"rm \"{item['path']}\"")
