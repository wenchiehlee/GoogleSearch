#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan all MD files for potential false positives (company code mismatches)"""

import re
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_company_from_title(title_text):
    """Extract company codes from title in format (XXXX-TW)"""
    pattern = r'\((\d{4})[-\s]*tw\)'
    matches = re.findall(pattern, title_text.lower())
    return matches

def scan_file(md_file):
    """Scan a single MD file for company code mismatch"""
    # Extract expected company code from filename
    # Format: XXXX_CompanyName_factset_hash.md
    filename = md_file.name
    match = re.match(r'(\d{4})_([^_]+)_factset_', filename)
    if not match:
        return None

    expected_code = match.group(1)
    expected_name = match.group(2)

    # Read file (first 30000 chars to get title)
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read(30000)
    except Exception as e:
        return {'file': filename, 'error': str(e)}

    # Extract title
    title_text = ""
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if title_match:
        title_text = title_match.group(1)

    # Also check meta og:title
    meta_title_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if meta_title_match:
        title_text = meta_title_match.group(1)

    if not title_text:
        return None

    # Extract company codes from title
    title_codes = extract_company_from_title(title_text)

    # Check for mismatch
    if title_codes and expected_code not in title_codes:
        return {
            'file': filename,
            'expected_code': expected_code,
            'expected_name': expected_name,
            'title_codes': title_codes,
            'title': title_text[:150]
        }

    return None

# Scan all MD files
md_dir = Path("data/md")
md_files = list(md_dir.glob("*.md"))

print("="*80)
print(f"Scanning {len(md_files)} MD files for company code mismatches...")
print("="*80)
print()

mismatches = []
errors = []

for md_file in md_files:
    result = scan_file(md_file)
    if result:
        if 'error' in result:
            errors.append(result)
        else:
            mismatches.append(result)

# Report results
print(f"📊 SCAN RESULTS:")
print(f"   Total files scanned: {len(md_files)}")
print(f"   Files with errors: {len(errors)}")
print(f"   Files with mismatches: {len(mismatches)}")
print()

if mismatches:
    print("="*80)
    print("⚠️  FILES WITH COMPANY CODE MISMATCHES (False Positives)")
    print("="*80)
    for i, m in enumerate(mismatches, 1):
        print(f"\n{i}. {m['file']}")
        print(f"   Expected: {m['expected_code']} ({m['expected_name']})")
        print(f"   Title has: {', '.join(m['title_codes'])}")
        print(f"   Title: {m['title']}")

    print()
    print("="*80)
    print(f"🎯 RECOMMENDATION: These {len(mismatches)} files should be:")
    print(f"   - Moved to quarantine, OR")
    print(f"   - Re-validated with new Multi-Layer Validation logic")
    print("="*80)
else:
    print("✅ No company code mismatches found!")

if errors:
    print()
    print(f"⚠️  {len(errors)} files had read errors:")
    for e in errors:
        print(f"   - {e['file']}: {e['error']}")
