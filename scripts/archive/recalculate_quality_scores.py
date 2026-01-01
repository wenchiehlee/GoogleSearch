#!/usr/bin/env python3
"""
Recalculate Quality Scores for All MD Files
Uses the new simplified formula (v3.7.0) with 0% date weight
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from process_group.quality_analyzer_simplified import QualityAnalyzerSimplified
from process_group.md_parser import MDParser


def extract_yaml_frontmatter(content):
    """Extract YAML frontmatter from MD content"""
    if not content.startswith('---'):
        return None, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content

    return parts[1].strip(), parts[2].strip()


def parse_yaml_simple(yaml_text):
    """Simple YAML parser for frontmatter"""
    metadata = {}
    for line in yaml_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            metadata[key] = value

    return metadata


def update_yaml_quality_score(yaml_text, new_score):
    """Update quality_score in YAML text"""
    lines = yaml_text.split('\n')
    updated_lines = []
    score_updated = False

    for line in lines:
        if line.strip().startswith('quality_score:'):
            updated_lines.append(f'quality_score: {new_score}')
            score_updated = True
        else:
            updated_lines.append(line)

    # If quality_score wasn't found, add it
    if not score_updated:
        updated_lines.insert(0, f'quality_score: {new_score}')

    return '\n'.join(updated_lines)


def recalculate_md_file(md_path, analyzer, parser):
    """Recalculate quality score for a single MD file"""
    try:
        # Read MD file
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse with MDParser to get the 12 fields
        parsed_data = parser.parse_md_file(str(md_path))

        if not parsed_data:
            return None, "Failed to parse MD file"

        # Get the data needed for quality scoring
        data_for_scoring = {
            'company_code': parsed_data.get('company_code', ''),
            'company_name': parsed_data.get('company_name', ''),
            'content_date': parsed_data.get('content_date') or parsed_data.get('md_date'),
            'analyst_count': parsed_data.get('analyst_count'),
            'target_price': parsed_data.get('target_price'),
            'eps_2025_high': parsed_data.get('eps_2025_high'),
            'eps_2025_low': parsed_data.get('eps_2025_low'),
            'eps_2025_avg': parsed_data.get('eps_2025_avg'),
            'eps_2026_high': parsed_data.get('eps_2026_high'),
            'eps_2026_low': parsed_data.get('eps_2026_low'),
            'eps_2026_avg': parsed_data.get('eps_2026_avg'),
            'eps_2027_high': parsed_data.get('eps_2027_high'),
            'eps_2027_low': parsed_data.get('eps_2027_low'),
            'eps_2027_avg': parsed_data.get('eps_2027_avg'),
        }

        # Recalculate quality score with new formula
        result = analyzer.analyze(data_for_scoring)
        new_score = result['quality_score']
        old_score = parsed_data.get('quality_score', 0.0)

        # Extract and update YAML frontmatter
        yaml_text, body = extract_yaml_frontmatter(content)

        if yaml_text:
            updated_yaml = update_yaml_quality_score(yaml_text, new_score)
            updated_content = f"---\n{updated_yaml}\n---\n{body}"

            # Write back to file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            return {
                'file': md_path.name,
                'old_score': old_score,
                'new_score': new_score,
                'difference': new_score - old_score,
                'company': f"{parsed_data.get('company_code', '')} {parsed_data.get('company_name', '')}"
            }, None
        else:
            return None, "No YAML frontmatter found"

    except Exception as e:
        return None, str(e)


def main():
    """Main recalculation function"""
    print("=" * 80)
    print("Recalculating Quality Scores with New Formula (v3.7.0)")
    print("=" * 80)
    print()
    print("New Formula: 50% EPS + 40% Analyst + 10% Target + 0% Date")
    print("Old Formula: 40% EPS + 30% Analyst + 10% Target + 20% Date")
    print()

    # Initialize analyzer and parser
    analyzer = QualityAnalyzerSimplified()
    parser = MDParser()

    # Find all MD files
    md_dir = Path('data/md')
    md_files = sorted(md_dir.glob('*.md'))

    print(f"Found {len(md_files)} MD files to recalculate")
    print()

    # Track statistics
    stats = {
        'total': len(md_files),
        'success': 0,
        'failed': 0,
        'improved': 0,
        'unchanged': 0,
        'decreased': 0
    }

    improvements = []

    # Process each file
    for i, md_path in enumerate(md_files, 1):
        print(f"Processing ({i}/{len(md_files)}): {md_path.name}...", end=' ')

        result, error = recalculate_md_file(md_path, analyzer, parser)

        if result:
            stats['success'] += 1
            diff = result['difference']

            if diff > 0.1:
                stats['improved'] += 1
                improvements.append(result)
                print(f"✅ {result['old_score']:.1f} → {result['new_score']:.1f} (+{diff:.1f})")
            elif diff < -0.1:
                stats['decreased'] += 1
                print(f"⚠️ {result['old_score']:.1f} → {result['new_score']:.1f} ({diff:.1f})")
            else:
                stats['unchanged'] += 1
                print(f"→ {result['new_score']:.1f} (unchanged)")
        else:
            stats['failed'] += 1
            print(f"❌ Error: {error}")

    print()
    print("=" * 80)
    print("Recalculation Summary")
    print("=" * 80)
    print(f"Total files:      {stats['total']}")
    print(f"Success:          {stats['success']}")
    print(f"Failed:           {stats['failed']}")
    print()
    print(f"Improved:         {stats['improved']} files")
    print(f"Unchanged:        {stats['unchanged']} files")
    print(f"Decreased:        {stats['decreased']} files")
    print()

    if improvements:
        print("=" * 80)
        print("Top 10 Improvements (Old Data Now Scores Higher)")
        print("=" * 80)
        improvements.sort(key=lambda x: x['difference'], reverse=True)

        for i, item in enumerate(improvements[:10], 1):
            print(f"{i:2}. {item['company']:30} "
                  f"{item['old_score']:4.1f} → {item['new_score']:4.1f} "
                  f"(+{item['difference']:.1f})")
        print()

    print("✅ Recalculation complete!")
    print()
    print("Next step: Re-generate reports with new scores:")
    print("  cd process_group")
    print("  python process_cli.py process")
    print()


if __name__ == "__main__":
    main()
