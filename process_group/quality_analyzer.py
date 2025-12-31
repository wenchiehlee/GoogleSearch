#!/usr/bin/env python3
"""
Quality Analyzer - FactSet Pipeline v3.5.1
Forces quality score = 0 for all validation failures
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

class QualityAnalyzer:
    """品質分析器 - 強制驗證失敗評分為 0"""
    
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
    
    # 評分權重
    QUALITY_WEIGHTS = {
        'data_completeness': 0.30,    # 資料完整性 30%
        'analyst_coverage': 0.20,     # 分析師覆蓋 20%
        'data_freshness': 0.15,       # 資料新鮮度 15%
        'content_quality': 0.15,      # 內容品質 15%
        'data_consistency': 0.05,     # 資料一致性 5%
        'content_validation': 0.15    # 內容驗證 15%
    }
    
    def __init__(self):
        """初始化品質分析器"""
        self.financial_keywords = [
            'eps', '每股盈餘', '營收', '營業收入', '淨利', '獲利',
            '目標價', '評等', '分析師', '預估', '預測', 'factset',
            'revenue', 'earnings', 'profit', 'target', 'analyst'
        ]

    def analyze(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """主要分析方法 - 檢查驗證失敗並強制 0 分"""
        try:
            company_code = parsed_data.get('company_code', '')
            company_name = parsed_data.get('company_name', '')
            
            # 檢查驗證結果
            validation_result = parsed_data.get('validation_result', {})
            validation_status = validation_result.get('overall_status', 'valid')
            validation_passed = parsed_data.get('content_validation_passed', True)
            
            # 如果驗證失敗，直接返回 0 分
            if not validation_passed or validation_status == 'error':
                validation_errors = parsed_data.get('validation_errors', [])
                main_error = str(validation_errors[0]) if validation_errors else "驗證失敗"
                
                print(f"❌ 驗證失敗強制 0 分: {company_code} ({company_name}) - {main_error[:50]}...")
                return self._create_zero_score_analysis(company_code, company_name, main_error)
            
            # 正常的品質分析邏輯
            completeness_analysis = self._analyze_data_completeness(parsed_data)
            coverage_analysis = self._analyze_analyst_coverage(parsed_data)
            freshness_analysis = self._analyze_data_freshness(parsed_data)
            content_analysis = self._analyze_content_quality(parsed_data)
            consistency_analysis = self._analyze_data_consistency(parsed_data)
            validation_analysis = self._analyze_content_validation(parsed_data)
            
            # CRITICAL: 直接使用 MD 檔案的 quality_score，不重新計算
            # 品質評分應該只從 MD 檔案讀取，保持與 Search Group 一致
            md_quality_score = parsed_data.get('quality_score', 0)
            if md_quality_score > 0:
                final_quality_score = round(md_quality_score, 1)
            else:
                # Fallback: 如果 MD 檔案缺少 quality_score，使用預設值 0
                final_quality_score = 0.0
            
            # 確定品質類別和狀態
            quality_category = self._determine_quality_category_fixed(final_quality_score)
            quality_status = self.QUALITY_INDICATORS[quality_category]
            
            # 生成摘要指標
            summary_metrics = self._generate_summary_metrics(parsed_data)
            
            return {
                'quality_score': final_quality_score,
                'quality_status': quality_status,
                'quality_category': quality_category,
                'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                
                'detailed_analysis': {
                    'data_completeness': completeness_analysis,
                    'analyst_coverage': coverage_analysis,
                    'data_freshness': freshness_analysis,
                    'content_quality': content_analysis,
                    'data_consistency': consistency_analysis,
                    'content_validation': validation_analysis
                },
                
                'summary_metrics': summary_metrics,
                
                'validation_summary': {
                    'validation_passed': validation_passed,
                    'validation_warnings': parsed_data.get('validation_warnings', []),
                    'validation_errors': parsed_data.get('validation_errors', []),
                    'has_validation_issues': len(parsed_data.get('validation_errors', [])) > 0
                },
                
                'score_adjustment': {
                    'base_score': round(final_quality_score, 1),  # 使用 MD 檔案的品質評分
                    'final_score': final_quality_score,
                    'adjustment_reason': "正常評分，無調整"
                }
            }
            
        except Exception as e:
            print(f"❌ 品質分析失敗: {e}")
            return self._create_empty_analysis(str(e))

    def _create_zero_score_analysis(self, company_code: str, company_name: str, error_msg: str) -> Dict[str, Any]:
        """建立強制 0 分的品質分析結果"""
        return {
            'quality_score': 0.0,
            'quality_status': '❌ 驗證失敗',
            'quality_category': 'insufficient',
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            'detailed_analysis': {
                'validation_failure': {
                    'score': 0.0,
                    'details': [f"❌ 驗證失敗: {error_msg}"],
                    'metrics': {
                        'validation_failure': True,
                        'company_code': company_code,
                        'company_name': company_name
                    }
                }
            },
            
            'summary_metrics': {
                'content_validation_passed': False,
                'validation_error_count': 1,
                'validation_failure': True,
                'eps_data_available': False,
                'target_price_available': False,
                'analyst_count': 0,
                'content_length': 0,
                'financial_keywords_found': 0
            },
            
            'validation_summary': {
                'validation_passed': False,
                'validation_errors': [error_msg],
                'validation_warnings': [],
                'has_validation_issues': True
            },
            
            'score_adjustment': {
                'base_score': 0.0,
                'final_score': 0.0,
                'adjustment_reason': f"驗證失敗強制 0 分: {error_msg[:50]}..."
            }
        }

    def _analyze_content_validation(self, data: Dict) -> Dict:
        """分析內容驗證結果 (15% 權重)"""
        score = 8.0  # 預設高分，有問題才扣分
        details = []
        metrics = {}
        
        validation_result = data.get('validation_result', {})
        validation_status = validation_result.get('overall_status', 'unknown')
        validation_confidence = validation_result.get('confidence_score', 10.0)
        validation_errors = data.get('validation_errors', [])
        validation_warnings = data.get('validation_warnings', [])
        
        # 根據驗證狀態評分
        if validation_status == 'valid':
            score = 10.0
            details.append("✅ 內容驗證通過")
        elif validation_status == 'warning':
            score = 6.0
            details.append(f"🟡 內容驗證有警告 ({len(validation_warnings)} 項)")
        elif validation_status == 'error':
            score = 0.0  # 驗證錯誤直接 0 分
            details.append(f"❌ 內容驗證失敗 ({len(validation_errors)} 項錯誤)")
        else:
            score = 5.0
            details.append("⚠️ 內容驗證狀態未知")
        
        # 檢查具體的驗證問題
        for error in validation_errors:
            if any(keyword in str(error) for keyword in ['公司名稱不符', '不在觀察名單']):
                score = 0.0  # 關鍵問題直接 0 分
                details.append("❌ 發現關鍵驗證問題")
                break
        
        # 記錄驗證指標
        metrics.update({
            'validation_status': validation_status,
            'validation_confidence': validation_confidence,
            'error_count': len(validation_errors),
            'warning_count': len(validation_warnings),
            'has_validation_failure': score == 0.0
        })
        
        return {
            'score': round(max(0, min(score, 10)), 2),
            'details': details,
            'metrics': metrics
        }

    def _determine_quality_category_fixed(self, score: float) -> str:
        """確定品質類別"""
        for category, (min_score, max_score) in self.QUALITY_RANGES.items():
            if min_score <= score <= max_score:
                return category
        
        if score >= 9.0:
            return 'complete'
        elif score >= 8.0:
            return 'good'
        elif score >= 3.0:
            return 'partial'
        else:
            return 'insufficient'

    def _analyze_data_completeness(self, data: Dict) -> Dict:
        """分析資料完整性 (30% 權重)"""
        score = 0
        details = []
        metrics = {}
        
        # EPS 資料完整性 (40% of this dimension)
        eps_years = ['2025', '2026', '2027']
        eps_available = 0
        
        for year in eps_years:
            if data.get(f'eps_{year}_avg') is not None:
                eps_available += 1
        
        eps_completeness = eps_available / len(eps_years)
        score += eps_completeness * 4.0
        
        if eps_available == 3:
            details.append("✅ EPS 預測完整 (2025-2027)")
        elif eps_available == 2:
            details.append("🟡 EPS 預測部分完整")
        elif eps_available == 1:
            details.append("🟠 EPS 預測資料有限")
        else:
            details.append("❌ 缺少 EPS 預測資料")
        
        metrics['eps_years_available'] = eps_available
        
        # 目標價格 (30% of this dimension)
        if data.get('target_price') is not None:
            score += 3.0
            details.append("✅ 目標價格資訊完整")
            metrics['has_target_price'] = True
        else:
            details.append("❌ 缺少目標價格")
            metrics['has_target_price'] = False
        
        # 分析師數量 (20% of this dimension)
        analyst_count = data.get('analyst_count', 0)
        if analyst_count >= 10:
            score += 2.0
            details.append(f"✅ 分析師覆蓋充足 ({analyst_count}位)")
        elif analyst_count >= 5:
            score += 1.5
            details.append(f"🟡 分析師覆蓋一般 ({analyst_count}位)")
        elif analyst_count > 0:
            score += 1.0
            details.append(f"🟠 分析師覆蓋有限 ({analyst_count}位)")
        else:
            details.append("❌ 缺少分析師資訊")
        
        metrics['analyst_count'] = analyst_count
        
        # 基本資訊 (10% of this dimension)
        basic_info_score = 0
        if data.get('company_code'):
            basic_info_score += 0.5
        if data.get('company_name'):
            basic_info_score += 0.5
        
        score += basic_info_score * 1.0
        
        if basic_info_score == 1.0:
            details.append("✅ 基本公司資訊完整")
        else:
            details.append("🟠 基本公司資訊不完整")
        
        metrics['basic_info_complete'] = basic_info_score == 1.0
        
        return {
            'score': round(min(score, 10), 2),
            'details': details,
            'metrics': metrics
        }

    def _analyze_analyst_coverage(self, data: Dict) -> Dict:
        """分析分析師覆蓋度 (20% 權重)"""
        score = 0
        details = []
        metrics = {}
        
        analyst_count = data.get('analyst_count', 0)
        
        # 分析師數量評分 (70% of this dimension)
        if analyst_count >= 30:
            score += 7.0
            details.append(f"🌟 優秀的分析師覆蓋 ({analyst_count}位)")
        elif analyst_count >= 20:
            score += 6.0
            details.append(f"✅ 良好的分析師覆蓋 ({analyst_count}位)")
        elif analyst_count >= 15:
            score += 5.0
            details.append(f"🟡 適中的分析師覆蓋 ({analyst_count}位)")
        elif analyst_count >= 10:
            score += 4.0
            details.append(f"🟠 基本的分析師覆蓋 ({analyst_count}位)")
        elif analyst_count >= 5:
            score += 2.5
            details.append(f"🔴 有限的分析師覆蓋 ({analyst_count}位)")
        elif analyst_count > 0:
            score += 1.0
            details.append(f"⚠️ 極少的分析師覆蓋 ({analyst_count}位)")
        else:
            details.append("❌ 無分析師覆蓋資訊")
        
        metrics['analyst_count'] = analyst_count
        
        # 資料來源品質 (30% of this dimension)
        data_source = data.get('data_source', '').lower()
        if 'factset' in data_source:
            score += 3.0
            details.append("✅ 高品質資料來源 (FactSet)")
            metrics['data_source_quality'] = 'high'
        elif any(source in data_source for source in ['bloomberg', 'refinitiv', 'reuters']):
            score += 2.5
            details.append("🟡 中等品質資料來源")
            metrics['data_source_quality'] = 'medium'
        elif data_source:
            score += 1.5
            details.append("🟠 一般資料來源")
            metrics['data_source_quality'] = 'basic'
        else:
            details.append("❌ 未知資料來源")
            metrics['data_source_quality'] = 'unknown'
        
        return {
            'score': round(min(score, 10), 2),
            'details': details,
            'metrics': metrics
        }

    def _analyze_data_freshness(self, data: Dict) -> Dict:
        """分析資料新鮮度 (15% 權重)"""
        score = 0
        details = []
        metrics = {}
        
        # 取得內容日期或檔案修改時間
        content_date = data.get('content_date')
        file_mtime = data.get('file_mtime')
        
        reference_date = content_date or file_mtime
        
        if reference_date:
            if isinstance(reference_date, str):
                try:
                    # 處理不同的日期格式
                    if '/' in reference_date:
                        # 2025/6/6 格式
                        date_parts = reference_date.split('/')
                        if len(date_parts) == 3:
                            year, month, day = date_parts
                            reference_date = datetime(int(year), int(month), int(day))
                    else:
                        reference_date = datetime.fromisoformat(reference_date.replace('Z', '+00:00'))
                except:
                    reference_date = None
            
            if reference_date:
                now = datetime.now()
                if reference_date.tzinfo is None:
                    reference_date = reference_date.replace(tzinfo=None)
                    now = now.replace(tzinfo=None)
                
                age_days = (now - reference_date).days
                
                # 資料新鮮度評分
                if age_days <= 7:
                    score += 8
                    details.append(f"✅ 資料非常新鮮 ({age_days} 天)")
                elif age_days <= 30:
                    score += 7
                    details.append(f"✅ 資料新鮮 ({age_days} 天)")
                elif age_days <= 90:
                    score += 5
                    details.append(f"🟡 資料較新 ({age_days} 天)")
                elif age_days <= 180:
                    score += 3
                    details.append(f"🟠 資料較舊 ({age_days} 天)")
                else:
                    score += 1
                    details.append(f"🔴 資料過舊 ({age_days} 天)")
                
                metrics['age_days'] = age_days
        else:
            score += 2
            details.append("⚠️ 無法確定資料時間")
        
        return {
            'score': round(min(score, 10), 2),
            'details': details,
            'metrics': metrics
        }

    def _analyze_content_quality(self, data: Dict) -> Dict:
        """分析內容品質 (15% 權重)"""
        score = 0
        details = []
        metrics = {}
        
        content = str(data.get('content', ''))
        content_length = len(content)
        
        # 內容長度評分
        if content_length >= 5000:
            score += 4
            details.append(f"✅ 內容豐富 ({content_length} 字元)")
        elif content_length >= 2000:
            score += 3
            details.append(f"🟡 內容適中 ({content_length} 字元)")
        elif content_length >= 500:
            score += 2
            details.append(f"🟠 內容較少 ({content_length} 字元)")
        else:
            score += 1
            details.append(f"🔴 內容過少 ({content_length} 字元)")
        
        # 財務關鍵字檢查
        keyword_count = sum(1 for keyword in self.financial_keywords if keyword in content.lower())
        
        if keyword_count >= 8:
            score += 4
            details.append(f"✅ 財務關鍵字豐富 ({keyword_count})")
        elif keyword_count >= 5:
            score += 3
            details.append(f"🟡 財務關鍵字一般 ({keyword_count})")
        elif keyword_count >= 2:
            score += 2
            details.append(f"🟠 財務關鍵字較少 ({keyword_count})")
        else:
            score += 1
            details.append(f"🔴 財務關鍵字稀少 ({keyword_count})")
        
        metrics['content_length'] = content_length
        metrics['keyword_count'] = keyword_count
        
        return {
            'score': round(min(score, 10), 2),
            'details': details,
            'metrics': metrics
        }

    def _analyze_data_consistency(self, data: Dict) -> Dict:
        """分析資料一致性 (5% 權重)"""
        score = 8  # 預設高分，有問題才扣分
        details = []
        issues = []
        
        # 檢查 EPS 趨勢一致性
        eps_2025 = data.get('eps_2025_avg')
        eps_2026 = data.get('eps_2026_avg')
        eps_2027 = data.get('eps_2027_avg')
        
        if eps_2025 and eps_2026 and eps_2027:
            # 檢查異常的 EPS 變化
            if abs(eps_2026 - eps_2025) > eps_2025 * 2:
                score -= 2
                issues.append("EPS 2025-2026 變化異常")
            
            if abs(eps_2027 - eps_2026) > eps_2026 * 2:
                score -= 2
                issues.append("EPS 2026-2027 變化異常")
        
        # 檢查公司資訊一致性
        company_code = data.get('company_code', '')
        if company_code and not (company_code.isdigit() and len(company_code) == 4):
            score -= 1
            issues.append("公司代號格式異常")
        
        # 檢查目標價格合理性
        target_price = data.get('target_price')
        if target_price and (target_price <= 0 or target_price > 10000):
            score -= 1
            issues.append("目標價格數值異常")
        
        if issues:
            details.append(f"❌ 發現 {len(issues)} 個一致性問題")
            details.extend([f"  - {issue}" for issue in issues])
        else:
            details.append("✅ 資料一致性良好")
        
        return {
            'score': max(0, min(10, score)),
            'details': details,
            'metrics': {'consistency_issues': issues}
        }

    def _generate_summary_metrics(self, data: Dict) -> Dict:
        """生成摘要指標"""
        return {
            'eps_data_available': any(data.get(f'eps_{year}_avg') is not None for year in ['2025', '2026', '2027']),
            'target_price_available': data.get('target_price') is not None,
            'analyst_count': data.get('analyst_count', 0),
            'content_length': len(str(data.get('content', ''))),
            'financial_keywords_found': sum(1 for keyword in self.financial_keywords if keyword in str(data.get('content', '')).lower()),
            'content_validation_passed': data.get('content_validation_passed', True),
            'validation_error_count': len(data.get('validation_errors', [])),
            'validation_warning_count': len(data.get('validation_warnings', []))
        }

    def _create_empty_analysis(self, error_msg: str) -> Dict:
        """建立空的分析結果"""
        return {
            'quality_score': 0,
            'quality_status': '🔴 不足',
            'quality_category': 'insufficient',
            'error': error_msg,
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'validation_summary': {
                'validation_passed': False,
                'validation_errors': [error_msg],
                'has_validation_issues': True
            }
        }


# 測試功能
if __name__ == "__main__":
    analyzer = QualityAnalyzer()
    
    print("=== 品質分析器測試 (觀察名單驗證) ===")
    
    # 測試已知問題公司
    test_cases = [
        # 驗證失敗
        {
            'company_code': '6462',
            'company_name': 'ase',
            'validation_errors': ['公司名稱不符觀察名單'],
            'content_validation_passed': False
        },
        # 不在觀察名單
        {
            'company_code': '1122',
            'company_name': '威剛',
            'validation_errors': ['不在觀察名單中'],
            'content_validation_passed': False
        },
        # 正常公司
        {
            'company_code': '2330',
            'company_name': '台積電',
            'validation_errors': [],
            'content_validation_passed': True,
            'analyst_count': 42,
            'target_price': 650.5,
            'eps_2025_avg': 46.0
        }
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test_data['company_code']} ({test_data['company_name']})")
        result = analyzer.analyze(test_data)
        score = result['quality_score']
        status = result['quality_status']
        print(f"   品質評分: {score} {status}")
        
        if test_data['company_code'] in ['6462', '1122']:
            expected = "0.0 ❌ 驗證失敗"
            actual = f"{score} {status}"
            print(f"   預期: {expected}")
            print(f"   實際: {actual}")
            print(f"   結果: {'✅ 正確' if score == 0.0 else '❌ 錯誤'}")
    
    print(f"\n✅ 品質分析器已啟動！")
    print(f"❌ 所有驗證失敗的公司將被強制設定為 0 分")