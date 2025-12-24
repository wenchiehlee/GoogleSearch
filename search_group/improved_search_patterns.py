#!/usr/bin/env python3
"""
Improved Search Patterns for Taiwan Stocks
Enhanced patterns that reduce false positives and improve content quality

Usage:
    Use these patterns in search_cli.py for better search results
    Specifically optimized for major Taiwan stocks like TSMC (2330)
"""

# ENHANCED SEARCH PATTERNS - v3.5.2
# These patterns are designed to:
# 1. Find FactSet analyst consensus data
# 2. Avoid false positives (prices that match stock codes)
# 3. Focus on recent, high-quality financial analysis

IMPROVED_SEARCH_PATTERNS = {
    # TIER 1: Highest quality - Direct FactSet reports
    'factset_direct_enhanced': [
        # TSMC and major stocks - very specific
        'site:cnyes.com "FactSet" "{symbol}-TW" "EPS" "預估"',
        'site:cnyes.com "鉅亨速報" "Factset" "{name}" "{symbol}" "EPS"',
        '"{symbol}-TW" "FactSet" "分析師" "目標價" "預估"',

        # With year specification for recency
        'site:cnyes.com "{name}" "FactSet" "2025" "EPS"',
        'site:cnyes.com "{name}" "FactSet" "2026" "EPS"',
    ],

    # TIER 2: Analyst consensus from major sources
    'analyst_consensus_enhanced': [
        # Financial news sites with FactSet data
        'site:cnyes.com "{name}" "分析師" "共識" "預估"',
        'site:moneydj.com "{symbol}" "FactSet" "目標價"',

        # Avoid ambiguous numbers by requiring company name
        '"{name}" "分析師" "{symbol}-TW" "EPS" "預估"',
    ],

    # TIER 3: EPS forecast tables (likely to have structured data)
    'eps_forecast_tables': [
        # Tables with multiple years
        '"{name}" "EPS預估" "2025" "2026" "2027"',
        'site:cnyes.com "{name}" "市場預估" "EPS"',

        # With analyst count
        '"{name}" "{symbol}" "分析師" "EPS" "平均值"',
        '"{name}" "共識" "中位數" "EPS"',
    ],

    # TIER 4: Company-specific financial analysis
    'company_analysis_enhanced': [
        # Avoid generic mentions, require substantial context
        '"{name}" "{symbol}-TW" "財報" "預估" after:2024',
        '"{name}" "目標價" "投資評等" "分析師" -論壇',  # Exclude forums

        # Institutional reports
        'site:statementdog.com "{name}" "預估EPS"',
        'site:wantgoo.com "{name}" "EPS" "預測"',
    ],
}


# STOCK-SPECIFIC OPTIMIZED PATTERNS
# For stocks with common numbers in prices/other contexts
STOCK_SPECIFIC_PATTERNS = {
    '2330': {  # TSMC - avoid confusion with price "2330元"
        'primary': [
            'site:cnyes.com "台積電" "2330-TW" "FactSet" "EPS"',
            '"TSMC" "2330-TW" "analyst" "consensus" "EPS"',
            'site:cnyes.com "鉅亨速報" "台積電" "FactSet" "預估"',
            '"台積電" "分析師" "目標價" "2025" "EPS" -"2330元"',  # Exclude price mentions
        ],
        'secondary': [
            'site:cnyes.com "台積電" "市場預估" "EPS" "2025"',
            '"台積電" "共識" "EPS" "分析師" "中位數"',
        ]
    },

    '2317': {  # Hon Hai (Foxconn)
        'primary': [
            'site:cnyes.com "鴻海" "2317-TW" "FactSet"',
            '"鴻海" "2317-TW" "分析師" "EPS預估"',
            'site:cnyes.com "鉅亨速報" "鴻海" "FactSet"',
        ],
        'secondary': [
            '"Hon Hai" "2317" "analyst" "target price"',
            'site:cnyes.com "鴻海" "市場預估" "EPS"',
        ]
    },

    '2454': {  # MediaTek
        'primary': [
            'site:cnyes.com "聯發科" "2454-TW" "FactSet"',
            '"MediaTek" "2454-TW" "analyst" "consensus"',
            'site:cnyes.com "聯發科" "分析師" "EPS預估"',
        ],
        'secondary': [
            '"聯發科" "市場預估" "目標價" "2025"',
            'site:cnyes.com "聯發科" "FactSet" "調查"',
        ]
    },

    '2308': {  # Delta Electronics
        'primary': [
            'site:cnyes.com "台達電" "2308-TW" "FactSet"',
            '"台達電" "2308-TW" "分析師" "共識"',
        ],
        'secondary': [
            '"Delta Electronics" "2308" "analyst" "estimate"',
            'site:cnyes.com "台達電" "EPS預估" "2025"',
        ]
    },
}


def get_search_patterns_for_stock(symbol: str, name: str, tier: str = 'all') -> list:
    """
    Get optimized search patterns for a specific stock

    Args:
        symbol: Stock code (e.g., '2330')
        name: Company name (e.g., '台積電')
        tier: 'primary', 'secondary', or 'all'

    Returns:
        List of formatted search query strings
    """
    patterns = []

    # Check if we have stock-specific patterns
    if symbol in STOCK_SPECIFIC_PATTERNS:
        stock_patterns = STOCK_SPECIFIC_PATTERNS[symbol]

        if tier in ['primary', 'all']:
            patterns.extend(stock_patterns.get('primary', []))

        if tier in ['secondary', 'all']:
            patterns.extend(stock_patterns.get('secondary', []))

    else:
        # Use general patterns and substitute
        for category, pattern_list in IMPROVED_SEARCH_PATTERNS.items():
            # For tier='primary', only use first category
            if tier == 'primary' and category != 'factset_direct_enhanced':
                continue

            # For tier='secondary', skip first category
            if tier == 'secondary' and category == 'factset_direct_enhanced':
                continue

            for pattern in pattern_list:
                formatted = pattern.format(symbol=symbol, name=name)
                patterns.append(formatted)

    return patterns


def print_patterns_for_stock(symbol: str, name: str):
    """Print all patterns for a stock (for testing)"""
    print(f"\n{'='*80}")
    print(f"SEARCH PATTERNS FOR: {symbol} - {name}")
    print(f"{'='*80}\n")

    primary = get_search_patterns_for_stock(symbol, name, tier='primary')
    print(f"PRIMARY PATTERNS ({len(primary)}):")
    for i, pattern in enumerate(primary, 1):
        print(f"  {i}. {pattern}")

    secondary = get_search_patterns_for_stock(symbol, name, tier='secondary')
    print(f"\nSECONDARY PATTERNS ({len(secondary)}):")
    for i, pattern in enumerate(secondary, 1):
        print(f"  {i}. {pattern}")

    print(f"\nTOTAL: {len(primary) + len(secondary)} patterns")
    print(f"{'='*80}\n")


# CLI for testing patterns
if __name__ == "__main__":
    import sys

    # Set UTF-8 for Windows
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    print("IMPROVED SEARCH PATTERNS - FactSet Pipeline v3.5.2")
    print("=" * 80)

    # Test with major stocks
    test_stocks = [
        ('2330', '台積電'),
        ('2317', '鴻海'),
        ('2454', '聯發科'),
        ('2301', '光寶科'),  # No specific patterns, will use general
    ]

    for symbol, name in test_stocks:
        print_patterns_for_stock(symbol, name)

    print("\nUSAGE EXAMPLE:")
    print("-" * 80)
    print("from improved_search_patterns import get_search_patterns_for_stock")
    print("")
    print("# Get primary patterns for TSMC")
    print("patterns = get_search_patterns_for_stock('2330', '台積電', tier='primary')")
    print("")
    print("# Use in search loop")
    print("for pattern in patterns:")
    print("    results = api_manager.search(pattern)")
    print("    # process results...")
    print("-" * 80)
