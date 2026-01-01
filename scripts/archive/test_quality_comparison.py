#!/usr/bin/env python3
"""
Compare Old vs New (Simplified) Quality Score Formulas
Shows impact of ZERO freshness weight - date has no impact on quality
"""

import sys
from pathlib import Path

# Add process_group to path
sys.path.insert(0, str(Path(__file__).parent / 'process_group'))

from quality_analyzer_simplified import QualityAnalyzerSimplified

def test_quality_scores():
    """Test and compare quality scores with different data scenarios"""

    analyzer = QualityAnalyzerSimplified()

    print("=" * 80)
    print("Quality Score Formula Comparison: Old (20% freshness) vs New (0% freshness)")
    print("=" * 80)
    print()

    # Test scenarios with varying data freshness
    scenarios = [
        {
            'name': 'Perfect Fresh Data (6 days old)',
            'data': {
                'company_code': '2330',
                'company_name': '台積電',
                'content_date': '2025/12/25',  # 6 days old
                'analyst_count': 28,
                'target_price': 850.0,
                'eps_2025_high': 38.5, 'eps_2025_low': 32.1, 'eps_2025_avg': 35.2,
                'eps_2026_high': 46.2, 'eps_2026_low': 39.5, 'eps_2026_avg': 42.8,
                'eps_2027_high': 55.8, 'eps_2027_low': 47.2, 'eps_2027_avg': 51.3
            },
            'old_expected': 9.7
        },
        {
            'name': 'Good Data - 30 days old',
            'data': {
                'company_code': '2454',
                'company_name': '聯發科',
                'content_date': '2025/12/01',  # 30 days old
                'analyst_count': 25,
                'target_price': 1200.0,
                'eps_2025_high': 90.0, 'eps_2025_low': 75.0, 'eps_2025_avg': 82.5,
                'eps_2026_high': 110.0, 'eps_2026_low': 90.0, 'eps_2026_avg': 100.0,
                'eps_2027_high': 130.0, 'eps_2027_low': 105.0, 'eps_2027_avg': 117.5
            },
            'old_expected': 9.5
        },
        {
            'name': 'Good Data - 68 days old',
            'data': {
                'company_code': '2301',
                'company_name': '光寶科',
                'content_date': '2025/10/24',  # 68 days old
                'analyst_count': 13,
                'target_price': 168.0,
                'eps_2025_high': 6.97, 'eps_2025_low': 5.97, 'eps_2025_avg': 6.51,
                'eps_2026_high': 8.96, 'eps_2026_low': 7.05, 'eps_2026_avg': 8.07,
                'eps_2027_high': 12.32, 'eps_2027_low': 8.95, 'eps_2027_avg': 10.30
            },
            'old_expected': 8.0
        },
        {
            'name': 'Good Data - 138 days old',
            'data': {
                'company_code': '2308',
                'company_name': '台達電',
                'content_date': '2025/08/15',  # 138 days old
                'analyst_count': 21,
                'target_price': 1100.0,
                'eps_2025_high': 25.0, 'eps_2025_low': 20.0, 'eps_2025_avg': 22.5,
                'eps_2026_high': 32.0, 'eps_2026_low': 26.0, 'eps_2026_avg': 29.0,
                'eps_2027_high': 40.0, 'eps_2027_low': 32.0, 'eps_2027_avg': 36.0
            },
            'old_expected': 8.4
        },
        {
            'name': 'Good Data - Very Old (200 days)',
            'data': {
                'company_code': '2317',
                'company_name': '鴻海',
                'content_date': '2025/06/15',  # 200 days old
                'analyst_count': 23,
                'target_price': 300.0,
                'eps_2025_high': 15.5, 'eps_2025_low': 13.0, 'eps_2025_avg': 14.3,
                'eps_2026_high': 19.5, 'eps_2026_low': 15.5, 'eps_2026_avg': 17.5,
                'eps_2027_high': 23.0, 'eps_2027_low': 17.5, 'eps_2027_avg': 20.3
            },
            'old_expected': 8.0
        },
        {
            'name': 'Complete Data - 1 Year Old (365 days)',
            'data': {
                'company_code': '2412',
                'company_name': '中華電',
                'content_date': '2024/12/31',  # 365 days old
                'analyst_count': 18,
                'target_price': 125.0,
                'eps_2025_high': 5.8, 'eps_2025_low': 5.2, 'eps_2025_avg': 5.5,
                'eps_2026_high': 6.2, 'eps_2026_low': 5.5, 'eps_2026_avg': 5.9,
                'eps_2027_high': 6.8, 'eps_2027_low': 6.0, 'eps_2027_avg': 6.4
            },
            'old_expected': 7.5
        },
        {
            'name': 'Complete Data - 2 Years Old (730 days)',
            'data': {
                'company_code': '1301',
                'company_name': '台塑',
                'content_date': '2024/01/01',  # 730 days old
                'analyst_count': 15,
                'target_price': 95.0,
                'eps_2025_high': 4.5, 'eps_2025_low': 3.8, 'eps_2025_avg': 4.1,
                'eps_2026_high': 5.2, 'eps_2026_low': 4.2, 'eps_2026_avg': 4.7,
                'eps_2027_high': 6.0, 'eps_2027_low': 4.8, 'eps_2027_avg': 5.4
            },
            'old_expected': 7.2
        },
        {
            'name': 'Complete Data - 5 Years Old (1825 days)',
            'data': {
                'company_code': '2002',
                'company_name': '中鋼',
                'content_date': '2020/12/31',  # 5 years old
                'analyst_count': 12,
                'target_price': 28.0,
                'eps_2025_high': 1.2, 'eps_2025_low': 0.8, 'eps_2025_avg': 1.0,
                'eps_2026_high': 1.5, 'eps_2026_low': 1.0, 'eps_2026_avg': 1.25,
                'eps_2027_high': 1.8, 'eps_2027_low': 1.2, 'eps_2027_avg': 1.5
            },
            'old_expected': 6.8
        }
    ]

    print(f"{'Scenario':<35} {'Old Score':<12} {'New Score':<12} {'Difference':<12}")
    print("-" * 80)

    for scenario in scenarios:
        result = analyzer.analyze(scenario['data'])
        new_score = result['quality_score']
        old_score = scenario['old_expected']
        difference = new_score - old_score

        # Color coding
        if difference >= 0.5:
            diff_str = f"+{difference:.1f} ✅"
        elif difference > 0:
            diff_str = f"+{difference:.1f}"
        else:
            diff_str = f"{difference:.1f}"

        print(f"{scenario['name']:<35} {old_score:<12.1f} {new_score:<12.1f} {diff_str:<12}")

        # Show component breakdown for first and last scenario
        if scenario == scenarios[0] or scenario == scenarios[-1]:
            print(f"  Components: EPS={result['component_scores']['eps_quality']:.1f}, "
                  f"Analyst={result['component_scores']['analyst_coverage']:.1f}, "
                  f"Fresh={result['component_scores']['data_freshness']:.1f}, "
                  f"Target={result['component_scores']['target_consistency']:.1f}")
            print(f"  Weighted:   EPS={result['weighted_contributions']['eps_quality']:.2f}, "
                  f"Analyst={result['weighted_contributions']['analyst_coverage']:.2f}, "
                  f"Fresh={result['weighted_contributions']['data_freshness']:.2f}, "
                  f"Target={result['weighted_contributions']['target_consistency']:.2f}")
            print()

    print()
    print("=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Freshness Weight: OLD=20% → NEW=0% (COMPLETELY REMOVED)")
    print(f"EPS Weight:       OLD=40% → NEW=50% (primary driver)")
    print(f"Analyst Weight:   OLD=30% → NEW=40% (secondary driver)")
    print(f"Target Weight:    OLD=10% → NEW=10% (unchanged)")
    print()
    print("Key Benefits:")
    print("  ✅ Date age has ZERO impact on quality score")
    print("  ✅ 1-year, 5-year, 10-year old data: ALL SCORE THE SAME")
    print("  ✅ Quality depends ONLY on: EPS completeness + Analyst coverage + Target price")
    print("  ✅ Perfect for long-term data archives")
    print("  ✅ Clean 50-40-10 weight distribution")
    print()


if __name__ == "__main__":
    test_quality_scores()
