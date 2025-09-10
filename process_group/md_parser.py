#!/usr/bin/env python3
"""
MD Parser - FactSet Pipeline v3.6.1 (Refined)
增強版 MD 檔案解析器，支援查詢模式提取和觀察名單驗證
完全整合 v3.6.1 功能要求
"""

import os
import re
import yaml
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import statistics
import json

class MDParser:
    def __init__(self):
        """初始化 MD 解析器 - v3.6.1 增強版"""
        
        self.version = "3.6.1"
        
        # 🆕 增強的 metadata 模式 - 支援查詢模式提取
        self.metadata_patterns = {
            'search_query': r'search_query:\s*(.+?)(?:\n|$)',
            'keywords': r'keywords:\s*(.+?)(?:\n|$)',
            'search_terms': r'search_terms:\s*(.+?)(?:\n|$)',
            'query_pattern': r'query_pattern:\s*(.+?)(?:\n|$)',
            'original_query': r'original_query:\s*(.+?)(?:\n|$)',
            'company_code': r'company_code:\s*(.+?)(?:\n|$)',
            'company_name': r'company_name:\s*(.+?)(?:\n|$)',
            'data_source': r'data_source:\s*(.+?)(?:\n|$)',
            'timestamp': r'timestamp:\s*(.+?)(?:\n|$)',
            'extracted_date': r'extracted_date:\s*(.+?)(?:\n|$)'
        }
        
        # 原有的日期和數據提取模式
        self.date_patterns = [
            r'\*\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'\*\s*更新[：:]\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'更新[：:]\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'鉅亨網新聞中心\s*\n\s*\n\s*(\d{4})年(\d{1,2})月(\d{1,2})日[週周]?[一二三四五六日天]?\s*[上下]午\s*\d{1,2}:\d{1,2}',
            r'鉅亨網新聞中心\s*\n\s*\n\s*(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'鉅亨網新聞中心[\s\n]+(\d{4})年(\d{1,2})月(\d{1,2})日[週周]?[一二三四五六日天]?',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日[週周]?[一二三四五六日天]?\s*[上下]午\s*\d{1,2}:\d{1,2}',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日[週周]?[一二三四五六日天]?',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}:\d{1,2}',
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
        ]
        
        self.eps_patterns = [
            r'(\d{4})年[^|]*\|\s*([0-9]+\.?[0-9]*)',
            r'(\d{4})\s*年\s*[:：]?\s*([0-9]+\.?[0-9]*)',
            r'(\d{4})\s*eps\s*[預估預測估算]*\s*[:：]\s*([0-9]+\.?[0-9]*)',
            r'eps\s*(\d{4})\s*[:：]\s*([0-9]+\.?[0-9]*)',
            r'平均值[^|]*(\d{4})[^|]*\|\s*([0-9]+\.?[0-9]*)',
            r'中位數[^|]*(\d{4})[^|]*\|\s*([0-9]+\.?[0-9]*)',
        ]
        
        self.target_price_patterns = [
            r'目標價\s*[:：為]\s*([0-9]+\.?[0-9]*)\s*元',
            r'預估目標價\s*[:：為]\s*([0-9]+\.?[0-9]*)\s*元',
            r'target\s*price\s*[:：]\s*([0-9]+\.?[0-9]*)',
        ]
        
        self.analyst_patterns = [
            r'共\s*(\d+)\s*位分析師',
            r'(\d+)\s*位分析師',
            r'(\d+)\s*analysts?',
        ]

        # 🔧 載入觀察名單並進行嚴格驗證
        self.watch_list_mapping = self._load_watch_list_mapping_enhanced()
        self.validation_enabled = len(self.watch_list_mapping) > 0
        
        print(f"🔧 MDParser v{self.version} 初始化完成")
        print(f"📋 觀察名單驗證: {'啟用' if self.validation_enabled else '停用'} ({len(self.watch_list_mapping)} 家公司)")

    def _load_watch_list_mapping_enhanced(self) -> Dict[str, str]:
        """🆕 v3.6.1 增強的觀察名單載入"""
        mapping = {}
        
        possible_paths = [
            'StockID_TWSE_TPEX.csv',
            '../StockID_TWSE_TPEX.csv',
            '../../StockID_TWSE_TPEX.csv',
            'data/StockID_TWSE_TPEX.csv',
            '../data/StockID_TWSE_TPEX.csv',
            'watchlist.csv',
            '../watchlist.csv'
        ]
        
        for csv_path in possible_paths:
            if os.path.exists(csv_path):
                try:
                    print(f"🔍 嘗試載入觀察名單: {csv_path}")
                    
                    # 🔧 使用多種編碼嘗試讀取
                    encodings = ['utf-8', 'utf-8-sig', 'big5', 'gbk', 'cp950']
                    df = None
                    
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(csv_path, header=None, names=['code', 'name'], encoding=encoding)
                            print(f"✅ 成功使用 {encoding} 編碼讀取")
                            break
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            print(f"⚠️ 使用 {encoding} 編碼讀取失敗: {e}")
                            continue
                    
                    if df is None:
                        print(f"❌ 無法使用任何編碼讀取 {csv_path}")
                        continue
                    
                    # 🔧 嚴格驗證和清理數據
                    valid_count = 0
                    invalid_count = 0
                    duplicate_count = 0
                    
                    for idx, row in df.iterrows():
                        try:
                            # 提取並清理代號和名稱
                            code = str(row['code']).strip()
                            name = str(row['name']).strip()
                            
                            # 🔧 嚴格驗證公司代號格式
                            if not self._is_valid_company_code(code):
                                print(f"⚠️ 無效公司代號格式: '{code}' (第{idx+1}行)")
                                invalid_count += 1
                                continue
                            
                            # 🔧 驗證公司名稱
                            if not self._is_valid_company_name(name):
                                print(f"⚠️ 無效公司名稱: '{name}' (代號: {code}, 第{idx+1}行)")
                                invalid_count += 1
                                continue
                            
                            # 🔧 檢查重複代號
                            if code in mapping:
                                print(f"⚠️ 重複公司代號: {code} - 原有: {mapping[code]}, 新的: {name}")
                                duplicate_count += 1
                                continue
                            
                            # 添加到映射
                            mapping[code] = name
                            valid_count += 1
                            
                        except Exception as e:
                            print(f"❌ 處理第{idx+1}行時發生錯誤: {e}")
                            invalid_count += 1
                            continue
                    
                    # 🔧 驗證載入結果
                    total_rows = len(df)
                    if valid_count == 0:
                        print(f"❌ 觀察名單無有效數據: {csv_path}")
                        continue
                    
                    print(f"📊 觀察名單載入統計:")
                    print(f"   檔案: {csv_path}")
                    print(f"   總行數: {total_rows}")
                    print(f"   有效數據: {valid_count}")
                    print(f"   無效數據: {invalid_count}")
                    print(f"   重複數據: {duplicate_count}")
                    print(f"   成功率: {valid_count/total_rows*100:.1f}%")
                    
                    # 🔧 額外驗證：檢查是否有已知的測試公司
                    self._validate_watch_list_content_enhanced(mapping)
                    
                    return mapping
                    
                except Exception as e:
                    print(f"❌ 讀取觀察名單失敗 {csv_path}: {e}")
                    continue
        
        # 🔧 如果觀察名單載入失敗，返回空字典但不停止系統
        print("❌ 所有觀察名單載入嘗試均失敗")
        print("⚠️ 系統將在無驗證模式下運行")
        return {}

    def parse_md_file(self, file_path: str) -> Dict[str, Any]:
        """🆕 v3.6.1 增強版 MD 檔案解析"""
        try:
            # 讀取檔案內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本檔案資訊
            file_info = self._extract_file_info(file_path)
            company_code = file_info.get('company_code', '')
            company_name = file_info.get('company_name', '')
            
            # 🆕 增強的 YAML front matter 解析
            yaml_data = self._extract_yaml_frontmatter_enhanced(content)
            
            # 🆕 查詢模式提取 (v3.6.1 核心功能)
            search_keywords = self._extract_search_keywords_enhanced(content, yaml_data)
            
            # 🔧 核心驗證：對照觀察名單 (增強版)
            validation_result = self._validate_against_watch_list_enhanced(company_code, company_name)
            
            # 原有功能：日期提取
            content_date = self._extract_content_date_bulletproof(content)
            extraction_status = "content_extraction" if content_date else "no_date_found"
            
            # 原有功能：EPS 等資料提取
            eps_data = self._extract_eps_data(content)
            eps_stats = self._calculate_eps_statistics(eps_data)
            target_price = self._extract_target_price(content)
            analyst_count = self._extract_analyst_count(content)
            data_richness = self._calculate_data_richness(eps_stats, target_price, analyst_count)
            
            # 🆕 內容品質評估 (v3.6.1)
            content_quality_metrics = self._assess_content_quality(content)
            
            # 組合結果
            result = {
                # 基本資訊
                'filename': os.path.basename(file_path),
                'company_code': company_code,
                'company_name': company_name,
                'data_source': file_info.get('data_source', ''),
                'file_mtime': datetime.fromtimestamp(os.path.getmtime(file_path)),
                
                # 日期資訊
                'content_date': content_date,
                'extracted_date': yaml_data.get('extracted_date'),
                'filename_date': file_info.get('parsed_timestamp'),
                
                # EPS 資料
                **eps_stats,
                
                # 其他財務資料
                'target_price': target_price,
                'analyst_count': analyst_count,
                
                # 資料狀態
                'has_eps_data': len(eps_data) > 0,
                'has_target_price': target_price is not None,
                'has_analyst_info': analyst_count > 0,
                'data_richness_score': data_richness,
                
                # 🆕 v3.6.1 增強功能
                'search_keywords': search_keywords,  # 關鍵！查詢模式分析需要
                'content_quality_metrics': content_quality_metrics,
                
                # YAML 資料
                'yaml_data': yaml_data,
                
                # 🔧 增強版驗證結果
                'validation_result': validation_result,
                'content_validation_passed': validation_result['overall_status'] == 'valid',
                'validation_warnings': validation_result.get('warnings', []),
                'validation_errors': validation_result.get('errors', []),
                'validation_enabled': self.validation_enabled,
                
                # 原始內容
                'content': content,
                'content_length': len(content),
                'parsed_at': datetime.now(),
                
                # 調試資訊
                'parser_version': self.version,
                'date_extraction_method': extraction_status,
                'debug_info': self._get_debug_info_enhanced(content, content_date, search_keywords)
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 解析檔案失敗 {file_path}: {e}")
            return self._create_empty_result_enhanced(file_path, str(e))

    def _extract_search_keywords_enhanced(self, content: str, yaml_data: Dict) -> List[str]:
        """🆕 v3.6.1 增強的搜尋關鍵字提取"""
        keywords = []
        
        try:
            # 1. 從 YAML metadata 中提取
            for field_name in ['search_query', 'keywords', 'search_terms', 'query_pattern', 'original_query']:
                field_value = yaml_data.get(field_name, '')
                if field_value and isinstance(field_value, str):
                    # 清理和分割關鍵字
                    cleaned_keywords = self._clean_and_split_keywords(field_value)
                    keywords.extend(cleaned_keywords)
            
            # 2. 從內容的 metadata 中提取
            if content.startswith('---'):
                try:
                    end_pos = content.find('---', 3)
                    if end_pos != -1:
                        yaml_content = content[3:end_pos].strip()
                        
                        # 使用正則表達式提取查詢相關欄位
                        for field_name, pattern in self.metadata_patterns.items():
                            matches = re.findall(pattern, yaml_content, re.MULTILINE | re.IGNORECASE)
                            for match in matches:
                                if match.strip():
                                    cleaned_keywords = self._clean_and_split_keywords(match.strip())
                                    keywords.extend(cleaned_keywords)
                except Exception as e:
                    print(f"⚠️ YAML metadata 解析失敗: {e}")
            
            # 3. 去重並過濾
            unique_keywords = []
            seen_keywords = set()
            
            for keyword in keywords:
                keyword_lower = keyword.lower().strip()
                if (keyword_lower not in seen_keywords and 
                    self._is_valid_keyword(keyword_lower) and
                    len(keyword_lower) >= 2):
                    unique_keywords.append(keyword.strip())
                    seen_keywords.add(keyword_lower)
            
            # 4. 按重要性排序
            sorted_keywords = self._sort_keywords_by_importance(unique_keywords)
            
            return sorted_keywords[:20]  # 限制最多20個關鍵字
            
        except Exception as e:
            print(f"⚠️ 搜尋關鍵字提取失敗: {e}")
            return []

    def _clean_and_split_keywords(self, text: str) -> List[str]:
        """清理和分割關鍵字"""
        if not text or not isinstance(text, str):
            return []
        
        # 移除常見的搜尋運算符
        cleaned = re.sub(r'[+\-"():]', ' ', text)
        
        # 分割關鍵字 (支援多種分隔符)
        keywords = re.split(r'[,，;；\s]+', cleaned)
        
        # 清理每個關鍵字
        cleaned_keywords = []
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword and len(keyword) >= 2:
                cleaned_keywords.append(keyword)
        
        return cleaned_keywords

    def _is_valid_keyword(self, keyword: str) -> bool:
        """檢查是否為有效關鍵字"""
        if not keyword or len(keyword) < 2:
            return False
        
        # 停用詞列表
        stop_words = {
            '的', '和', '與', '或', '及', '在', '為', '是', '有', '此', '將', '會', '了', '就', '都',
            'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with'
        }
        
        if keyword.lower() in stop_words:
            return False
        
        # 檢查是否為純數字或符號
        if keyword.isdigit() or not re.search(r'[a-zA-Z\u4e00-\u9fff]', keyword):
            return False
        
        return True

    def _sort_keywords_by_importance(self, keywords: List[str]) -> List[str]:
        """按重要性排序關鍵字"""
        def get_importance_score(keyword: str) -> int:
            score = 0
            keyword_lower = keyword.lower()
            
            # 高重要性關鍵字
            high_importance = ['factset', 'eps', '目標價', '分析師', '預估', 'bloomberg', 'reuters']
            if any(imp in keyword_lower for imp in high_importance):
                score += 10
            
            # 中重要性關鍵字
            medium_importance = ['財報', '營收', '獲利', '股價', '評等', 'analyst', 'forecast', 'estimate']
            if any(imp in keyword_lower for imp in medium_importance):
                score += 5
            
            # 公司名稱和代號
            if re.search(r'\d{4}', keyword) or len(keyword) <= 4:
                score += 8
            
            # 中文關鍵字稍微提高優先級
            if re.search(r'[\u4e00-\u9fff]', keyword):
                score += 2
            
            return score
        
        return sorted(keywords, key=get_importance_score, reverse=True)

    def _assess_content_quality(self, content: str) -> Dict[str, Any]:
        """🆕 v3.6.1 評估內容品質"""
        metrics = {
            'content_length': len(content),
            'paragraph_count': len(content.split('\n\n')),
            'line_count': len(content.split('\n')),
            'chinese_char_ratio': 0,
            'financial_keyword_count': 0,
            'table_count': 0,
            'number_count': 0,
            'has_metadata': content.startswith('---'),
            'structure_score': 0
        }
        
        try:
            # 中文字符比例
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
            if metrics['content_length'] > 0:
                metrics['chinese_char_ratio'] = round(chinese_chars / metrics['content_length'], 3)
            
            # 財務關鍵字計數
            financial_keywords = [
                'eps', '每股盈餘', '營收', '獲利', '淨利', '毛利', '目標價', '分析師', 
                '預估', '評等', 'factset', 'bloomberg', '股價', '市值'
            ]
            for keyword in financial_keywords:
                metrics['financial_keyword_count'] += len(re.findall(keyword, content, re.IGNORECASE))
            
            # 表格計數
            metrics['table_count'] = content.count('|')
            
            # 數字計數
            metrics['number_count'] = len(re.findall(r'\d+\.?\d*', content))
            
            # 結構評分 (0-10)
            structure_score = 0
            if metrics['has_metadata']:
                structure_score += 3
            if metrics['paragraph_count'] >= 3:
                structure_score += 2
            if metrics['table_count'] > 0:
                structure_score += 2
            if metrics['financial_keyword_count'] >= 5:
                structure_score += 2
            if metrics['content_length'] >= 1000:
                structure_score += 1
            
            metrics['structure_score'] = min(structure_score, 10)
            
        except Exception as e:
            print(f"⚠️ 內容品質評估失敗: {e}")
        
        return metrics

    def _extract_yaml_frontmatter_enhanced(self, content: str) -> Dict[str, Any]:
        """🆕 v3.6.1 增強的 YAML front matter 提取"""
        try:
            if content.startswith('---'):
                end_pos = content.find('---', 3)
                if end_pos != -1:
                    yaml_content = content[3:end_pos].strip()
                    
                    # 嘗試使用 yaml 解析器
                    try:
                        yaml_data = yaml.safe_load(yaml_content) or {}
                        
                        # 額外清理和驗證
                        cleaned_data = {}
                        for key, value in yaml_data.items():
                            if isinstance(value, str):
                                cleaned_data[key] = value.strip()
                            else:
                                cleaned_data[key] = value
                        
                        return cleaned_data
                        
                    except yaml.YAMLError as e:
                        print(f"⚠️ YAML 解析失敗，嘗試手動解析: {e}")
                        
                        # 手動解析關鍵欄位
                        manual_data = {}
                        for field_name, pattern in self.metadata_patterns.items():
                            matches = re.findall(pattern, yaml_content, re.MULTILINE | re.IGNORECASE)
                            if matches:
                                manual_data[field_name] = matches[0].strip()
                        
                        return manual_data
                        
        except Exception as e:
            print(f"⚠️ YAML frontmatter 提取失敗: {e}")
        
        return {}

    def _validate_against_watch_list_enhanced(self, company_code: str, company_name: str) -> Dict[str, Any]:
        """🆕 v3.6.1 增強的觀察名單驗證"""
        
        validation_result = {
            'overall_status': 'valid',
            'warnings': [],
            'errors': [],
            'confidence_score': 10.0,
            'validation_method': 'enhanced_v3.6.1',
            'detailed_checks': []
        }
        
        # 🔧 如果觀察名單未載入，記錄但不阻止處理
        if not self.validation_enabled:
            validation_result['warnings'].append("觀察名單未載入，跳過驗證")
            validation_result['confidence_score'] = 5.0
            validation_result['validation_method'] = 'disabled'
            validation_result['detailed_checks'].append("驗證功能已停用")
            print(f"⚠️ 觀察名單驗證已停用: {company_code} - {company_name}")
            return validation_result
        
        # 🔧 嚴格檢查輸入參數
        if not company_code or not company_name:
            validation_result['overall_status'] = 'error'
            validation_result['confidence_score'] = 0.0
            error_msg = f"公司代號或名稱為空: 代號='{company_code}', 名稱='{company_name}'"
            validation_result['errors'].append(error_msg)
            validation_result['detailed_checks'].append("輸入參數檢查失敗")
            print(f"❌ 參數錯誤: {error_msg}")
            return validation_result
        
        # 🔧 清理輸入數據
        clean_code = str(company_code).strip().strip('\'"')
        clean_name = str(company_name).strip()
        
        # 🔧 檢查 1: 公司代號格式驗證
        validation_result['detailed_checks'].append("檢查公司代號格式")
        if not self._is_valid_company_code(clean_code):
            validation_result['overall_status'] = 'error'
            validation_result['confidence_score'] = 0.0
            error_msg = f"公司代號格式無效: '{clean_code}'"
            validation_result['errors'].append(error_msg)
            validation_result['detailed_checks'].append("公司代號格式檢查失敗")
            print(f"❌ 代號格式無效: {clean_code}")
            return validation_result
        
        # 🔧 檢查 2: 公司代號是否在觀察名單中
        validation_result['detailed_checks'].append("檢查觀察名單包含狀態")
        if clean_code not in self.watch_list_mapping:
            validation_result['overall_status'] = 'error'
            validation_result['confidence_score'] = 0.0
            error_msg = f"代號{clean_code}不在觀察名單中，不允許處理"
            validation_result['errors'].append(error_msg)
            validation_result['detailed_checks'].append("觀察名單包含檢查失敗")
            print(f"❌ 不在觀察名單: {clean_code}")
            
            # 🔧 額外信息：提供相似的代號建議
            similar_codes = self._find_similar_codes(clean_code)
            if similar_codes:
                suggestion_msg = f"相似代號建議: {', '.join(similar_codes[:3])}"
                validation_result['warnings'].append(suggestion_msg)
                validation_result['detailed_checks'].append(f"找到相似代號: {len(similar_codes)}個")
            
            return validation_result
        
        # 🔧 檢查 3: 公司名稱是否與觀察名單一致 (增強比較)
        validation_result['detailed_checks'].append("檢查公司名稱一致性")
        correct_name = self.watch_list_mapping[clean_code]
        
        # 🔧 多層次名稱比較
        name_match = self._compare_company_names_enhanced(clean_name, correct_name)
        
        if not name_match['is_match']:
            validation_result['overall_status'] = 'error'
            validation_result['confidence_score'] = 0.0
            error_msg = f"公司名稱不符觀察名單：檔案為{clean_name}({clean_code})，觀察名單顯示應為{correct_name}({clean_code})"
            validation_result['errors'].append(error_msg)
            validation_result['detailed_checks'].append("公司名稱一致性檢查失敗")
            
            # 🔧 額外信息：詳細的不匹配分析
            if name_match['details']:
                validation_result['errors'].append(f"詳細比較: {name_match['details']}")
                validation_result['detailed_checks'].append(f"名稱比較詳情: {name_match['match_type']}")
            
            print(f"❌ 名稱不符: {clean_code}")
            print(f"   檔案名稱: '{clean_name}'")
            print(f"   觀察名單: '{correct_name}'")
            print(f"   比較詳情: {name_match['details']}")
            
            return validation_result
        
        # 🔧 檢查通過
        validation_result['confidence_score'] = name_match['confidence_score']
        validation_result['detailed_checks'].append(f"所有檢查通過，名稱匹配類型: {name_match['match_type']}")
        
        if name_match['confidence_score'] < 10.0:
            validation_result['warnings'].append(f"名稱匹配度: {name_match['confidence_score']}/10")
        
        print(f"✅ 驗證通過: {clean_code} - {clean_name} (信心度: {name_match['confidence_score']})")
        return validation_result

    def _compare_company_names_enhanced(self, name1: str, name2: str) -> Dict[str, Any]:
        """🆕 v3.6.1 增強的公司名稱比較"""
        comparison_result = {
            'is_match': False,
            'confidence_score': 0.0,
            'details': '',
            'match_type': 'no_match'
        }
        
        # 層次 1: 完全匹配
        if name1 == name2:
            comparison_result.update({
                'is_match': True,
                'confidence_score': 10.0,
                'details': '完全匹配',
                'match_type': 'exact_match'
            })
            return comparison_result
        
        # 層次 2: 移除空白後匹配
        clean_name1 = re.sub(r'\s+', '', name1)
        clean_name2 = re.sub(r'\s+', '', name2)
        
        if clean_name1 == clean_name2:
            comparison_result.update({
                'is_match': True,
                'confidence_score': 9.5,
                'details': '移除空白後匹配',
                'match_type': 'whitespace_normalized'
            })
            return comparison_result
        
        # 層次 3: 移除常見後綴詞後匹配
        suffixes = ['股份有限公司', '有限公司', '公司', '集團', '控股', 'Corporation', 'Corp', 'Inc', 'Ltd', 'Group']
        
        def remove_suffixes(name):
            for suffix in suffixes:
                if name.endswith(suffix):
                    name = name[:-len(suffix)].strip()
            return name
        
        core_name1 = remove_suffixes(clean_name1)
        core_name2 = remove_suffixes(clean_name2)
        
        if core_name1 == core_name2:
            comparison_result.update({
                'is_match': True,
                'confidence_score': 9.0,
                'details': '移除後綴詞後匹配',
                'match_type': 'suffix_removed'
            })
            return comparison_result
        
        # 層次 4: 部分包含匹配
        if core_name1 in core_name2 or core_name2 in core_name1:
            comparison_result.update({
                'is_match': True,
                'confidence_score': 7.0,
                'details': f'部分包含匹配: "{core_name1}" vs "{core_name2}"',
                'match_type': 'partial_contain'
            })
            return comparison_result
        
        # 層次 5: 編輯距離匹配 (新增)
        similarity = self._calculate_string_similarity(core_name1, core_name2)
        if similarity >= 0.8:  # 80% 相似度
            comparison_result.update({
                'is_match': True,
                'confidence_score': round(similarity * 6, 1),  # 最高6分
                'details': f'高相似度匹配: {similarity:.2f}',
                'match_type': 'high_similarity'
            })
            return comparison_result
        
        # 不匹配
        comparison_result.update({
            'details': f'完全不匹配: "{name1}" vs "{name2}" (相似度: {similarity:.2f})',
            'match_type': 'no_match'
        })
        return comparison_result

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """計算字符串相似度 (簡化版編輯距離)"""
        try:
            if not str1 or not str2:
                return 0.0
            
            if str1 == str2:
                return 1.0
            
            # 簡化的相似度計算
            longer = str1 if len(str1) > len(str2) else str2
            shorter = str2 if len(str1) > len(str2) else str1
            
            # 計算共同字符
            common_chars = sum(1 for char in shorter if char in longer)
            similarity = common_chars / len(longer)
            
            return similarity
            
        except Exception:
            return 0.0

    def _get_debug_info_enhanced(self, content: str, extracted_date: Optional[str], 
                                search_keywords: List[str]) -> Dict[str, Any]:
        """🆕 v3.6.1 增強的調試資訊"""
        return {
            'content_preview': content[:200] + "..." if len(content) > 200 else content,
            'extracted_date': extracted_date,
            'yaml_detected': content.startswith('---'),
            'content_length': len(content),
            'search_keywords_count': len(search_keywords),
            'search_keywords_preview': search_keywords[:5],
            'watch_list_loaded': self.validation_enabled,
            'watch_list_size': len(self.watch_list_mapping),
            'parser_version': self.version,
            'content_structure': {
                'has_metadata': content.startswith('---'),
                'paragraph_count': len(content.split('\n\n')),
                'line_count': len(content.split('\n')),
                'chinese_detected': bool(re.search(r'[\u4e00-\u9fff]', content))
            }
        }

    def _create_empty_result_enhanced(self, file_path: str, error_msg: str) -> Dict[str, Any]:
        """🆕 v3.6.1 增強的空結果建立"""
        file_info = self._extract_file_info(file_path)
        
        return {
            'filename': os.path.basename(file_path),
            'company_code': file_info.get('company_code'),
            'company_name': file_info.get('company_name'),
            'data_source': file_info.get('data_source'),
            'file_mtime': datetime.fromtimestamp(os.path.getmtime(file_path)) if os.path.exists(file_path) else None,
            'content_date': None,
            'eps_2025_high': None, 'eps_2025_low': None, 'eps_2025_avg': None,
            'eps_2026_high': None, 'eps_2026_low': None, 'eps_2026_avg': None,
            'eps_2027_high': None, 'eps_2027_low': None, 'eps_2027_avg': None,
            'target_price': None,
            'analyst_count': 0,
            'has_eps_data': False,
            'has_target_price': False,
            'has_analyst_info': False,
            'data_richness_score': 0.0,
            'search_keywords': [],  # 重要！
            'content_quality_metrics': {},
            'yaml_data': {},
            'content': '',
            'content_length': 0,
            'parsed_at': datetime.now(),
            'parser_version': self.version,
            'error': error_msg,
            'date_extraction_method': 'error',
            'validation_result': {
                'overall_status': 'error', 
                'errors': [error_msg],
                'validation_method': 'error_state'
            },
            'content_validation_passed': False,
            'validation_warnings': [],
            'validation_errors': [error_msg],
            'validation_enabled': self.validation_enabled
        }

    # 保留原有的私有方法 (略微調整以支援增強功能)
    def _is_valid_company_code(self, code: str) -> bool:
        """驗證公司代號格式"""
        if not code or code in ['nan', 'NaN', 'null', 'None', '', 'NULL']:
            return False
        
        clean_code = code.strip().strip('\'"')
        
        if not clean_code.isdigit():
            return False
            
        if len(clean_code) != 4:
            return False
        
        try:
            code_num = int(clean_code)
            if not (1000 <= code_num <= 9999):
                return False
        except ValueError:
            return False
        
        return True

    def _is_valid_company_name(self, name: str) -> bool:
        """驗證公司名稱"""
        if not name or name in ['nan', 'NaN', 'null', 'None', '', 'NULL']:
            return False
        
        clean_name = name.strip()
        
        if len(clean_name) < 1 or len(clean_name) > 30:
            return False
        
        invalid_chars = ['|', '\t', '\n', '\r', '\x00']
        if any(char in clean_name for char in invalid_chars):
            return False
        
        return True

    def _find_similar_codes(self, target_code: str) -> List[str]:
        """尋找相似的公司代號"""
        if not self.watch_list_mapping:
            return []
        
        similar_codes = []
        target_num = None
        
        try:
            target_num = int(target_code)
        except ValueError:
            return similar_codes
        
        for code in self.watch_list_mapping.keys():
            try:
                code_num = int(code)
                if abs(code_num - target_num) <= 10:
                    similar_codes.append(code)
            except ValueError:
                continue
        
        return sorted(similar_codes)

    def _validate_watch_list_content_enhanced(self, mapping: Dict[str, str]):
        """🆕 v3.6.1 增強的觀察名單內容驗證"""
        if not mapping:
            return
        
        # 檢查是否有常見的測試公司
        test_companies = {
            '2330': '台積電',
            '2317': '鴻海', 
            '2454': '聯發科',
            '2882': '國泰金',
            '2412': '中華電'
        }
        
        found_test_companies = 0
        for code, expected_name in test_companies.items():
            if code in mapping:
                actual_name = mapping[code]
                name_match = self._compare_company_names_enhanced(actual_name, expected_name)
                if name_match['is_match']:
                    found_test_companies += 1
                    print(f"✅ 找到測試公司: {code} - {actual_name} (匹配類型: {name_match['match_type']})")
                else:
                    print(f"⚠️ 測試公司名稱不符: {code} - 期望:{expected_name}, 實際:{actual_name}")
        
        # 統計分析
        code_ranges = self._analyze_code_ranges(mapping)
        print(f"📊 觀察名單代號分布: {code_ranges}")
        
        if found_test_companies == 0:
            print("⚠️ 未找到任何已知測試公司，請檢查觀察名單內容")
        else:
            print(f"✅ 找到 {found_test_companies}/{len(test_companies)} 個測試公司")

    def _analyze_code_ranges(self, mapping: Dict[str, str]) -> Dict[str, int]:
        """分析公司代號範圍分布"""
        ranges = {
            '1000-1999': 0,
            '2000-2999': 0, 
            '3000-3999': 0,
            '4000-4999': 0,
            '5000-5999': 0,
            '6000-6999': 0,
            '7000-7999': 0,
            '8000-8999': 0,
            '9000-9999': 0
        }
        
        for code in mapping.keys():
            try:
                code_num = int(code)
                range_key = f"{(code_num // 1000) * 1000}-{(code_num // 1000) * 1000 + 999}"
                if range_key in ranges:
                    ranges[range_key] += 1
            except ValueError:
                continue
        
        return ranges

    # 保留原有方法 (略作調整以支援新功能)
    # [原有的所有其他方法保持不變，只是確保與新功能相容]
    
    def _extract_content_date_bulletproof(self, content: str) -> Optional[str]:
        """絕對防彈的日期提取 - 排除 YAML frontmatter"""
        actual_content = self._get_content_without_yaml(content)
        found_dates = []
        
        for i, pattern in enumerate(self.date_patterns):
            matches = re.findall(pattern, actual_content, re.MULTILINE | re.DOTALL)
            
            if matches:
                for match in matches:
                    try:
                        if len(match) >= 3:
                            year, month, day = match[0], match[1], match[2]
                            
                            if self._validate_date(year, month, day):
                                date_str = f"{year}/{int(month)}/{int(day)}"
                                confidence = self._calculate_date_confidence(pattern, match, actual_content, i)
                                
                                found_dates.append({
                                    'date': date_str,
                                    'pattern_index': i,
                                    'pattern': pattern,
                                    'confidence': confidence,
                                    'match': match
                                })
                                
                    except (ValueError, IndexError) as e:
                        continue
        
        if found_dates:
            found_dates.sort(key=lambda x: x['confidence'], reverse=True)
            best_date = found_dates[0]
            return best_date['date']
        
        return None

    def _get_content_without_yaml(self, content: str) -> str:
        """移除 YAML frontmatter，只返回實際內容"""
        try:
            if content.startswith('---'):
                end_pos = content.find('---', 3)
                if end_pos != -1:
                    actual_content = content[end_pos + 3:].strip()
                    return actual_content
        except Exception as e:
            pass
        return content

    # [其他原有方法保持不變...]
    def _validate_date(self, year: str, month: str, day: str) -> bool:
        """驗證日期的合理性"""
        try:
            y, m, d = int(year), int(month), int(day)
            if not (2020 <= y <= 2030):
                return False
            if not (1 <= m <= 12):
                return False
            if not (1 <= d <= 31):
                return False
            datetime(y, m, d)
            return True
        except (ValueError, TypeError):
            return False

    def _calculate_date_confidence(self, pattern: str, match: tuple, content: str, pattern_index: int) -> float:
        """計算日期匹配的可信度"""
        confidence = 5.0
        
        if pattern_index == 0:
            confidence += 6.0
        elif pattern_index == 1:
            confidence += 5.5
        elif pattern_index == 2:
            confidence += 5.0
        elif pattern_index <= 6:
            confidence += 4.0
        elif 'cmoney' in content.lower() or 'CMoney' in content:
            confidence += 2.5
        elif '鉅亨網' in pattern:
            confidence += 2.0
        elif '年' in pattern and '月' in pattern:
            confidence += 1.5
        elif '-' in pattern:
            confidence += 1.0
        
        match_text = ''.join(match)
        position = content.find(match_text)
        if position != -1:
            if position < len(content) * 0.1:
                confidence += 2.0
            elif position < len(content) * 0.3:
                confidence += 1.0
        
        try:
            year = int(match[0])
            current_year = datetime.now().year
            if year == current_year:
                confidence += 1.5
            elif year == current_year - 1:
                confidence += 1.0
        except:
            pass
        
        return confidence

    def _extract_file_info(self, file_path: str) -> Dict[str, Any]:
        """從檔案路徑提取基本資訊"""
        filename = os.path.basename(file_path)
        name_without_ext = filename.replace('.md', '')
        parts = name_without_ext.split('_')
        
        result = {
            'company_code': None,
            'company_name': None,
            'data_source': None,
            'timestamp': None,
            'parsed_timestamp': None
        }
        
        if len(parts) >= 2:
            if parts[0].isdigit() and len(parts[0]) == 4:
                result['company_code'] = parts[0]
            
            if len(parts) > 1:
                result['company_name'] = parts[1]
            
            if len(parts) > 2:
                result['data_source'] = parts[2]
        
        return result

    def _extract_eps_data(self, content: str) -> Dict[str, List[float]]:
        """提取 EPS 資料"""
        eps_data = {'2025': [], '2026': [], '2027': []}
        
        eps_data.update(self._extract_eps_from_table(content))
        
        for pattern in self.eps_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    year = match[0]
                    value = float(match[1])
                    
                    if year in eps_data and 0 < value < 1000:
                        eps_data[year].append(value)
                except (ValueError, IndexError):
                    continue
        
        for year in eps_data:
            eps_data[year] = list(set(eps_data[year]))
        
        return eps_data

    def _extract_eps_from_table(self, content: str) -> Dict[str, List[float]]:
        """從表格中提取 EPS 資料"""
        eps_data = {'2025': [], '2026': [], '2027': []}
        
        table_patterns = [
            r'\|\s*(最高值|最低值|平均值|中位數)[^|]*\|\s*([0-9]+\.?[0-9]*)[^|]*\|\s*([0-9]+\.?[0-9]*)\s*\|\s*([0-9]+\.?[0-9]*)',
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    years = ['2025', '2026', '2027']
                    for i, year in enumerate(years):
                        if i + 1 < len(match):
                            value_str = match[i + 1].strip()
                            value_str = re.sub(r'\([^)]*\)', '', value_str)
                            value = float(value_str)
                            if 0 < value < 1000:
                                eps_data[year].append(value)
                except (ValueError, IndexError):
                    continue
        
        return eps_data

    def _extract_target_price(self, content: str) -> Optional[float]:
        """提取目標價格"""
        for pattern in self.target_price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    price = float(matches[0])
                    if 0 < price < 10000:
                        return price
                except ValueError:
                    continue
        return None

    def _extract_analyst_count(self, content: str) -> int:
        """提取分析師數量"""
        for pattern in self.analyst_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    count = int(matches[0])
                    if 0 < count < 1000:
                        return count
                except ValueError:
                    continue
        return 0

    def _calculate_eps_statistics(self, eps_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """計算 EPS 統計資料"""
        result = {}
        
        for year in ['2025', '2026', '2027']:
            values = eps_data.get(year, [])
            
            if values:
                result[f'eps_{year}_high'] = max(values)
                result[f'eps_{year}_low'] = min(values)
                result[f'eps_{year}_avg'] = round(statistics.mean(values), 2)
            else:
                result[f'eps_{year}_high'] = None
                result[f'eps_{year}_low'] = None
                result[f'eps_{year}_avg'] = None
        
        return result

    def _calculate_data_richness(self, eps_stats: Dict, target_price: Optional[float], analyst_count: int) -> float:
        """計算資料豐富度分數 (0-10)"""
        score = 0
        
        eps_years = ['2025', '2026', '2027']
        eps_available = sum(1 for year in eps_years if eps_stats.get(f'eps_{year}_avg') is not None)
        score += (eps_available / len(eps_years)) * 6
        
        if target_price is not None:
            score += 2
        
        if analyst_count > 0:
            if analyst_count >= 20:
                score += 2
            elif analyst_count >= 10:
                score += 1.5
            elif analyst_count >= 5:
                score += 1
            else:
                score += 0.5
        
        return round(min(score, 10), 2)


# 測試功能
if __name__ == "__main__":
    parser = MDParser()
    
    print(f"=== MD Parser v{parser.version} 測試 (增強版觀察名單驗證和查詢模式提取) ===")
    print(f"📋 觀察名單載入: {len(parser.watch_list_mapping)} 家公司")
    print(f"🔧 驗證功能: {'啟用' if parser.validation_enabled else '停用'}")
    
    if parser.validation_enabled:
        # 測試增強版驗證邏輯
        test_cases = [
            ('6462', 'ase'),      # 錯誤名稱
            ('6811', 'fubon'),    # 錯誤名稱  
            ('9999', '不存在'),    # 不存在的代號
            ('abc', 'test'),      # 無效格式
            ('2330', '台積電')     # 正常公司 (如果在觀察名單中)
        ]
        
        print(f"\n🧪 增強版驗證測試:")
        for code, name in test_cases:
            result = parser._validate_against_watch_list_enhanced(code, name)
            status = result['overall_status']
            errors = len(result.get('errors', []))
            confidence = result.get('confidence_score', 0)
            method = result.get('validation_method', 'unknown')
            checks = len(result.get('detailed_checks', []))
            
            print(f"  {code} ({name}): {status} - 信心度:{confidence} - 方法:{method} - 檢查:{checks} - 錯誤:{errors}")
            
            if errors > 0:
                for error in result.get('errors', [])[:1]:  # 只顯示第一個錯誤
                    print(f"    ❌ {error}")
    else:
        print("⚠️ 觀察名單驗證已停用")
    
    # 測試查詢模式提取
    print(f"\n🧪 查詢模式提取測試:")
    test_content = '''---
search_query: 台積電 2330 factset eps 預估
keywords: 半導體, 晶圓代工, 台積電, factset
original_query: "台積電" factset 分析師 目標價
---

台積電第三季財報分析...
'''
    
    test_yaml = {
        'search_query': '神盾 6462 factset 生物辨識',
        'keywords': '神盾, factset, 指紋辨識'
    }
    
    keywords = parser._extract_search_keywords_enhanced(test_content, test_yaml)
    print(f"   提取的關鍵字: {keywords}")
    print(f"   關鍵字數量: {len(keywords)}")
    
    print(f"\n✅ v{parser.version} 增強版 MD Parser 已啟動！")
    print(f"🆕 新功能: 增強觀察名單驗證、查詢模式提取、內容品質評估")
    print(f"🔧 主要修正: 多層次名稱比較、相似度計算、詳細驗證日誌")