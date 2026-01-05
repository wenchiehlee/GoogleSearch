#!/usr/bin/env python3
"""
Simplified Quality Analyzer - FactSet Pipeline v3.8.0
UPDATED: Added Revenue scoring + Strict validation for EPS and Revenue
- EPS Validation: High >= Median AND Average >= Low (else score = 0)
- Revenue Validation: High >= Average AND Median >= Low (else score = 0)
- Date freshness has ZERO weight (0%) AND 0-5 years old = all equally valid (10.0)
"""

from datetime import datetime
from typing import Dict, Any

class QualityAnalyzerSimplified:
    """簡化品質分析器 v3.8.0 - 包含營收評分與嚴格驗證"""

    # 品質範圍定義
    QUALITY_RANGES = {
        'complete': (9.0, 10.0),      # 🟢 完整 (9.0-10.0)
        'good': (8.0, 8.99),          # 🟡 良好 (8.0-8.99)
        'partial': (3.0, 7.99),       # 🟠 部分 (3.0-7.99)
        'insufficient': (0.0, 2.99)   # 🔴 不足 (0.0-2.99)
    }

    # 品質狀態指標
    QUALITY_INDICATORS = {
        'complete': '🟢 完整',
        'good': '🟡 良好',
        'partial': '🟠 部分',
        'insufficient': '🔴 不足'
    }

    # 更新評分權重 (總和 = 100%)
    WEIGHTS = {
        'eps_quality': 0.35,        # EPS 資料品質 35% (降低)
        'revenue_quality': 0.25,    # 營收資料品質 25% (新增)
        'analyst_coverage': 0.30,   # 分析師覆蓋 30% (降低)
        'data_freshness': 0.00,     # 資料新鮮度 0% (完全移除日期影響)
        'target_consistency': 0.10  # 目標價與一致性 10% (保持)
    }

    def __init__(self):
        """初始化簡化品質分析器 v3.8.0"""
        pass

    def analyze(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析方法 v3.8.0 - 包含營收評分

        欄位:
        1. MD日期 (content_date)
        2. 分析師數量 (analyst_count)
        3. 目標價 (target_price)
        4-12. EPS欄位 (eps_2025/2026/2027_high/low/avg/median)
        13-21. 營收欄位 (revenue_2025/2026/2027_high/low/avg/median)
        """
        try:
            company_code = parsed_data.get('company_code', '')
            company_name = parsed_data.get('company_name', '')

            # 計算五個組件分數
            eps_score = self._calculate_eps_quality(parsed_data)
            revenue_score = self._calculate_revenue_quality(parsed_data)
            analyst_score = self._calculate_analyst_coverage(parsed_data)
            freshness_score = self._calculate_data_freshness(parsed_data)
            target_score = self._calculate_target_consistency(parsed_data)

            # 加權總分
            final_score = (
                eps_score * self.WEIGHTS['eps_quality'] +
                revenue_score * self.WEIGHTS['revenue_quality'] +
                analyst_score * self.WEIGHTS['analyst_coverage'] +
                freshness_score * self.WEIGHTS['data_freshness'] +
                target_score * self.WEIGHTS['target_consistency']
            )

            # 四捨五入到一位小數
            final_score = round(final_score, 1)

            # 確定品質類別
            quality_category = self._determine_quality_category(final_score)
            quality_status = self.QUALITY_INDICATORS[quality_category]

            return {
                'quality_score': final_score,
                'quality_status': quality_status,
                'quality_category': quality_category,
                'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

                'component_scores': {
                    'eps_quality': round(eps_score, 2),
                    'revenue_quality': round(revenue_score, 2),
                    'analyst_coverage': round(analyst_score, 2),
                    'data_freshness': round(freshness_score, 2),
                    'target_consistency': round(target_score, 2)
                },

                'weighted_contributions': {
                    'eps_quality': round(eps_score * self.WEIGHTS['eps_quality'], 2),
                    'revenue_quality': round(revenue_score * self.WEIGHTS['revenue_quality'], 2),
                    'analyst_coverage': round(analyst_score * self.WEIGHTS['analyst_coverage'], 2),
                    'data_freshness': round(freshness_score * self.WEIGHTS['data_freshness'], 2),
                    'target_consistency': round(target_score * self.WEIGHTS['target_consistency'], 2)
                },

                'summary_metrics': {
                    'eps_years_available': sum(1 for year in ['2026', '2027', '2028']
                                              if parsed_data.get(f'eps_{year}_avg') is not None),
                    'revenue_years_available': sum(1 for year in ['2026', '2027', '2028']
                                                  if parsed_data.get(f'revenue_{year}_avg') is not None),
                    'analyst_count': parsed_data.get('analyst_count', 0),
                    'has_target_price': parsed_data.get('target_price') is not None,
                    'content_age_days': self._get_age_days(parsed_data.get('content_date'))
                }
            }

        except Exception as e:
            print(f"❌ 簡化品質分析失敗: {e}")
            return self._create_empty_analysis(str(e))

    def _calculate_eps_quality(self, data: Dict) -> float:
        """
        計算 EPS 資料品質分數 (0-10) - v3.8.0 嚴格驗證

        嚴格驗證規則:
        - High >= Median (中位數)
        - Average >= Low
        - 任一年不符合 → 整體 EPS score = 0

        組成:
        - 覆蓋率 (50%): 有幾年的 EPS 資料
        - 品質 (50%): EPS 範圍是否有效
        """
        eps_years = ['2026', '2027', '2028']

        # 先進行嚴格驗證
        for year in eps_years:
            high = data.get(f'eps_{year}_high')
            low = data.get(f'eps_{year}_low')
            avg = data.get(f'eps_{year}_avg')
            median = data.get(f'eps_{year}_median')

            # 如果該年有任何 EPS 資料，就必須全部符合驗證規則
            if any([high is not None, low is not None, avg is not None, median is not None]):
                # 檢查是否有完整資料
                if not all([high is not None, low is not None, avg is not None, median is not None]):
                    # 資料不完整，但不算驗證失敗，繼續
                    continue

                # 嚴格驗證: High >= Median AND Average >= Low
                if not (high >= median and avg >= low):
                    print(f"❌ EPS {year} 驗證失敗: High({high}) < Median({median}) or Avg({avg}) < Low({low})")
                    return 0.0  # 驗證失敗，直接返回 0 分

        # 通過驗證後，進行正常評分
        score = 0.0

        # 1. 覆蓋率評分 (最高5分)
        eps_available = sum(1 for year in eps_years
                           if data.get(f'eps_{year}_avg') is not None)

        coverage_score = (eps_available / 3) * 5.0
        score += coverage_score

        # 2. 範圍品質評分 (最高5分)
        quality_score = 0.0

        for year in eps_years:
            high = data.get(f'eps_{year}_high')
            low = data.get(f'eps_{year}_low')
            avg = data.get(f'eps_{year}_avg')

            if all([high is not None, low is not None, avg is not None]):
                # 檢查: Low ≤ Avg ≤ High
                if low <= avg <= high:
                    quality_score += 1.0

                    # 獎勵: 範圍緊密 (High/Low < 2.0)
                    if low > 0 and (high / low) < 2.0:
                        quality_score += 0.67

        quality_score = min(quality_score, 5.0)
        score += quality_score

        return min(score, 10.0)

    def _calculate_revenue_quality(self, data: Dict) -> float:
        """
        計算營收資料品質分數 (0-10) - v3.8.0 新增

        嚴格驗證規則:
        - High >= Average
        - Median (中位數) >= Low
        - 任一年不符合 → 整體營收 score = 0

        組成:
        - 覆蓋率 (50%): 有幾年的營收資料
        - 品質 (50%): 營收範圍是否有效
        """
        revenue_years = ['2026', '2027', '2028']

        # 先進行嚴格驗證
        for year in revenue_years:
            high = data.get(f'revenue_{year}_high')
            low = data.get(f'revenue_{year}_low')
            avg = data.get(f'revenue_{year}_avg')
            median = data.get(f'revenue_{year}_median')

            # 如果該年有任何營收資料，就必須全部符合驗證規則
            if any([high is not None, low is not None, avg is not None, median is not None]):
                # 檢查是否有完整資料
                if not all([high is not None, low is not None, avg is not None, median is not None]):
                    # 資料不完整，但不算驗證失敗，繼續
                    continue

                # 嚴格驗證: High >= Average AND Median >= Low
                if not (high >= avg and median >= low):
                    print(f"❌ 營收 {year} 驗證失敗: High({high}) < Avg({avg}) or Median({median}) < Low({low})")
                    return 0.0  # 驗證失敗，直接返回 0 分

        # 通過驗證後，進行正常評分
        score = 0.0

        # 1. 覆蓋率評分 (最高5分)
        revenue_available = sum(1 for year in revenue_years
                               if data.get(f'revenue_{year}_avg') is not None)

        coverage_score = (revenue_available / 3) * 5.0
        score += coverage_score

        # 2. 範圍品質評分 (最高5分)
        quality_score = 0.0

        for year in revenue_years:
            high = data.get(f'revenue_{year}_high')
            low = data.get(f'revenue_{year}_low')
            avg = data.get(f'revenue_{year}_avg')

            if all([high is not None, low is not None, avg is not None]):
                # 檢查: Low ≤ Avg ≤ High
                if low <= avg <= high:
                    quality_score += 1.0

                    # 獎勵: 範圍緊密 (High/Low < 2.0)
                    if low > 0 and (high / low) < 2.0:
                        quality_score += 0.67

        quality_score = min(quality_score, 5.0)
        score += quality_score

        return min(score, 10.0)

    def _calculate_analyst_coverage(self, data: Dict) -> float:
        """
        計算分析師覆蓋分數 (0-10)

        僅基於分析師數量
        """
        analyst_count = data.get('analyst_count', 0)

        if analyst_count >= 30:
            return 10.0  # 優秀
        elif analyst_count >= 20:
            return 9.0   # 很好
        elif analyst_count >= 15:
            return 8.0   # 良好
        elif analyst_count >= 10:
            return 6.5   # 中等
        elif analyst_count >= 5:
            return 4.0   # 有限
        elif analyst_count >= 1:
            return 2.0   # 極少
        else:
            return 0.0   # 無

    def _calculate_data_freshness(self, data: Dict) -> float:
        """
        計算資料新鮮度分數 (0-10)

        基於 MD日期 的年齡
        權重設為 0% - 日期對品質分數完全無影響
        保留此函數僅用於報告顯示，不影響最終評分

        更新: 所有日期都視為同等有效 (10.0分) - 無年齡限制
        """
        content_date = data.get('content_date')

        if not content_date:
            return 0.0

        age_days = self._get_age_days(content_date)

        if age_days is None:
            return 0.0

        # 所有有效日期都給予滿分 - 完全無年齡歧視
        return 10.0

    def _calculate_target_consistency(self, data: Dict) -> float:
        """
        計算目標價與一致性分數 (0-10)

        組成:
        - 目標價存在 (60%): 6分
        - EPS 一致性 (40%): 4分
        """
        score = 0.0

        # 1. 目標價 (6分)
        target_price = data.get('target_price')
        if target_price is not None and target_price > 0:
            score += 6.0

        # 2. EPS 趨勢一致性 (4分)
        eps_2026 = data.get('eps_2026_avg')
        eps_2027 = data.get('eps_2027_avg')
        eps_2028 = data.get('eps_2028_avg')

        consistency_score = 4.0

        # 檢查異常變化 (>1000% YoY)
        if eps_2026 and eps_2027 and eps_2026 > 0:
            if abs(eps_2027 - eps_2026) > eps_2026 * 10:
                consistency_score -= 2.0

        if eps_2027 and eps_2028 and eps_2027 > 0:
            if abs(eps_2028 - eps_2027) > eps_2027 * 10:
                consistency_score -= 2.0

        score += max(0, consistency_score)

        return min(score, 10.0)

    def _get_age_days(self, content_date) -> int:
        """計算日期年齡（天數）"""
        if not content_date:
            return None

        try:
            # 解析日期格式
            if isinstance(content_date, str):
                if '/' in content_date:
                    # 格式: "2025/10/24"
                    parts = content_date.split('/')
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                elif '-' in content_date:
                    # 格式: "2025-10-24"
                    parts = content_date.split('-')
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    return None

                date_obj = datetime(year, month, day)
            elif isinstance(content_date, datetime):
                date_obj = content_date
            else:
                return None

            # 計算年齡
            now = datetime.now()
            age_days = (now - date_obj).days

            return age_days

        except Exception as e:
            print(f"⚠️ 日期解析失敗: {e}")
            return None

    def _determine_quality_category(self, score: float) -> str:
        """確定品質類別"""
        for category, (min_score, max_score) in self.QUALITY_RANGES.items():
            if min_score <= score <= max_score:
                return category

        # 備用分類
        if score >= 9.0:
            return 'complete'
        elif score >= 8.0:
            return 'good'
        elif score >= 3.0:
            return 'partial'
        else:
            return 'insufficient'

    def _create_empty_analysis(self, error_msg: str) -> Dict:
        """建立空的分析結果"""
        return {
            'quality_score': 0.0,
            'quality_status': '🔴 不足',
            'quality_category': 'insufficient',
            'error': error_msg,
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'component_scores': {
                'eps_quality': 0.0,
                'revenue_quality': 0.0,
                'analyst_coverage': 0.0,
                'data_freshness': 0.0,
                'target_consistency': 0.0
            }
        }


# 測試功能
if __name__ == "__main__":
    analyzer = QualityAnalyzerSimplified()

    print("=== 簡化品質分析器測試 v3.8.0 ===")
    print(f"權重配置: {analyzer.WEIGHTS}")
    print()

    # 測試案例1: 完美資料 (包含營收)
    test_case_1 = {
        'company_code': '2330',
        'company_name': '台積電',
        'content_date': '2025/12/25',
        'analyst_count': 28,
        'target_price': 850.0,
        'eps_2025_high': 38.5,
        'eps_2025_low': 32.1,
        'eps_2025_avg': 35.2,
        'eps_2025_median': 35.0,
        'eps_2026_high': 46.2,
        'eps_2026_low': 39.5,
        'eps_2026_avg': 42.8,
        'eps_2026_median': 42.5,
        'eps_2027_high': 55.8,
        'eps_2027_low': 47.2,
        'eps_2027_avg': 51.3,
        'eps_2027_median': 51.0,
        'revenue_2025_high': 3500000,
        'revenue_2025_low': 3200000,
        'revenue_2025_avg': 3350000,
        'revenue_2025_median': 3340000,
        'revenue_2026_high': 3800000,
        'revenue_2026_low': 3400000,
        'revenue_2026_avg': 3600000,
        'revenue_2026_median': 3590000,
        'revenue_2027_high': 4200000,
        'revenue_2027_low': 3700000,
        'revenue_2027_avg': 3950000,
        'revenue_2027_median': 3940000
    }

    result = analyzer.analyze(test_case_1)
    print(f"測試案例1 (完美資料 - EPS + 營收):")
    print(f"  品質分數: {result['quality_score']}")
    print(f"  品質狀態: {result['quality_status']}")
    print(f"  組件分數: {result['component_scores']}")
    print(f"  加權貢獻: {result['weighted_contributions']}")
    print()

    # 測試案例2: EPS 驗證失敗 (High < Median)
    test_case_2 = {
        'company_code': '2301',
        'company_name': '光寶科',
        'content_date': '2025/10/24',
        'analyst_count': 13,
        'target_price': 168.0,
        'eps_2025_high': 6.0,  # High < Median (6.5) → 驗證失敗
        'eps_2025_low': 5.97,
        'eps_2025_avg': 6.51,
        'eps_2025_median': 6.5,
        'revenue_2025_high': 150000,
        'revenue_2025_low': 140000,
        'revenue_2025_avg': 145000,
        'revenue_2025_median': 145000
    }

    result = analyzer.analyze(test_case_2)
    print(f"測試案例2 (EPS驗證失敗 - High < Median):")
    print(f"  品質分數: {result['quality_score']}")
    print(f"  品質狀態: {result['quality_status']}")
    print(f"  組件分數: {result['component_scores']}")
    print(f"  預期: EPS score = 0.0")
    print()

    # 測試案例3: 營收驗證失敗 (Median < Low)
    test_case_3 = {
        'company_code': '2454',
        'company_name': '聯發科',
        'content_date': '2025/11/15',
        'analyst_count': 25,
        'target_price': 1200.0,
        'eps_2025_high': 95.0,
        'eps_2025_low': 85.0,
        'eps_2025_avg': 90.0,
        'eps_2025_median': 90.0,
        'revenue_2025_high': 580000,
        'revenue_2025_low': 520000,
        'revenue_2025_avg': 550000,
        'revenue_2025_median': 500000  # Median < Low → 驗證失敗
    }

    result = analyzer.analyze(test_case_3)
    print(f"測試案例3 (營收驗證失敗 - Median < Low):")
    print(f"  品質分數: {result['quality_score']}")
    print(f"  品質狀態: {result['quality_status']}")
    print(f"  組件分數: {result['component_scores']}")
    print(f"  預期: Revenue score = 0.0")
    print()

    print("✅ 簡化品質分析器 v3.8.0 測試完成")
    print(f"🎯 新功能:")
    print(f"   ✅ 營收評分 (25% 權重)")
    print(f"   ✅ EPS 嚴格驗證: High >= Median, Avg >= Low")
    print(f"   ✅ 營收嚴格驗證: High >= Avg, Median >= Low")
