#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Multi-Layer Validation on problematic file"""

import re
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Test the problematic file
test_file = Path("data/md/2454_聯發科_factset_c30625ab.md")

# Read file (just first 50000 chars to get title and some content)
with open(test_file, 'r', encoding='utf-8') as f:
    content = f.read(50000)

# Expected values (what was searched for)
symbol = "2454"
name = "聯發科"

print("="*60)
print("Testing Multi-Layer Validation")
print("="*60)
print(f"File: {test_file.name}")
print(f"Expected: {symbol} ({name})")
print()

# Layer 1: Title validation
print("LAYER 1: Title Validation")
print("-"*60)
title_text = ""
title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
if title_match:
    title_text = title_match.group(1)
    print(f"Title found: {title_text[:200]}...")

meta_title_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
if meta_title_match:
    title_text = meta_title_match.group(1)
    print(f"Meta og:title: {title_text}")

# Check for wrong company code in title
other_company_pattern = r'\((\d{4})[-\s]*tw\)'
title_company_matches = re.findall(other_company_pattern, title_text.lower())
print(f"Company codes in title: {title_company_matches}")

if title_company_matches:
    found_symbols = [m for m in title_company_matches]
    if symbol not in found_symbols and len(found_symbols) > 0:
        wrong_symbol = found_symbols[0]
        print(f"❌ REJECTED: Title mentions different company ({wrong_symbol}-TW) instead of {symbol}")
        print(f"   This file would be REJECTED at Layer 1")
        sys.exit(0)

print()

# Layer 2: Combined pattern check
print("LAYER 2: Combined Pattern Check")
print("-"*60)
content_lower = content.lower()
symbol_lower = symbol.lower()
name_lower = name.lower()

combined_patterns = [
    rf'{name_lower}[^\)]*\({symbol}[-\s]*tw\)',
    rf'\({symbol}[-\s]*tw\)[^\)]*{name_lower}',
    rf'{symbol}[-\s]*tw[^\)]*{name_lower}',
    rf'{name_lower}[^\d]{{0,20}}{symbol}[-\s]*tw',
    rf'代號[:：\s]*{symbol}[^\)]*{name_lower}',
]

has_combined_match = False
for i, pattern in enumerate(combined_patterns):
    match = re.search(pattern, content_lower)
    if match:
        has_combined_match = True
        print(f"✓ Pattern {i+1} matched: {match.group(0)[:100]}")
        break

if has_combined_match:
    print("✅ ACCEPTED at Layer 2")
    sys.exit(0)
else:
    print("No combined pattern found")

print()

# Layer 3: Proximity check
print("LAYER 3: Proximity Check")
print("-"*60)
symbol_positions = [m.start() for m in re.finditer(symbol, content_lower)]
name_positions = [m.start() for m in re.finditer(name_lower, content_lower)]

print(f"Symbol '{symbol}' found at positions: {symbol_positions[:5]}...")
print(f"Name '{name}' found at positions: {name_positions[:5]}...")

proximity_threshold = 200
has_proximity_match = False
min_distance = float('inf')

for sym_pos in symbol_positions:
    for name_pos in name_positions:
        distance = abs(sym_pos - name_pos)
        if distance <= proximity_threshold:
            has_proximity_match = True
            min_distance = min(min_distance, distance)

if has_proximity_match:
    print(f"✅ ACCEPTED at Layer 3 (min distance: {min_distance} chars)")
    sys.exit(0)
else:
    print(f"No proximity match (closest: {min_distance} chars > {proximity_threshold} threshold)")

print()
print("="*60)
print("FINAL RESULT: Would be REJECTED or pass to Layer 4 fallback")
print("="*60)
