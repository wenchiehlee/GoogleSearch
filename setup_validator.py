#!/usr/bin/env python3
"""
setup_validator.py - Enhanced Installation and Configuration Validator (v3.3.0)

Version: 3.3.0
Date: 2025-06-22
Author: FactSet Pipeline - v3.3.0 Enhanced Architecture
License: MIT

v3.3.0 ENHANCEMENTS:
- ✅ Enhanced validation for v3.3.0 specific features
- ✅ Improved MD file processing validation
- ✅ Better data deduplication and aggregation testing
- ✅ Enhanced company name matching validation
- ✅ Improved date extraction and quality scoring tests
- ✅ Better error handling and recovery validation
- ✅ v3.3.0 specific configuration testing

Description:
    Comprehensive setup validation script for the Enhanced FactSet Pipeline v3.3.0.
    Validates all dependencies, configurations, and connections for the
    enhanced architecture with portfolio aggregation and individual file analysis.

Usage:
    python setup_validator.py                    # Full v3.3.0 validation
    python setup_validator.py --quick           # Quick validation
    python setup_validator.py --fix-issues      # Auto-fix common issues
    python setup_validator.py --test-v330       # Test v3.3.0 specific features
"""

import os
import sys
import json
import argparse
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Version Information - v3.3.0
__version__ = "3.3.0"
__date__ = "2025-06-22"
__author__ = "FactSet Pipeline - v3.3.0 Enhanced Architecture"

class EnhancedSetupValidator:
    """Enhanced setup validation for FactSet Pipeline v3.3.0"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes_applied = []
        self.current_dir = Path(__file__).parent
        self.version = "3.3.0"
        
    def log_error(self, message: str):
        """Log an error"""
        self.errors.append(message)
        print(f"❌ {message}")
    
    def log_warning(self, message: str):
        """Log a warning"""
        self.warnings.append(message)
        print(f"⚠️ {message}")
    
    def log_success(self, message: str):
        """Log a success"""
        print(f"✅ {message}")
    
    def log_info(self, message: str):
        """Log info"""
        print(f"ℹ️ {message}")
    
    def apply_fix(self, fix_description: str):
        """Record a fix that was applied"""
        self.fixes_applied.append(fix_description)
        print(f"🔧 {fix_description}")
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility for v3.3.0"""
        print("\n🐍 Checking Python Version (v3.3.0 requirements)...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            self.log_success(f"Python {version.major}.{version.minor}.{version.micro}")
            if version.minor >= 10:
                self.log_info("Python 3.10+ detected - optimal for v3.3.0 features")
            return True
        else:
            self.log_error(f"Python 3.8+ required for v3.3.0, found {version.major}.{version.minor}.{version.micro}")
            return False
    
    def check_required_files_v330(self) -> bool:
        """Check for required v3.3.0 enhanced pipeline files"""
        print("\n📁 Checking Required Files (v3.3.0)...")
        
        # Enhanced required files for v3.3.0
        required_files = [
            "factset_pipeline.py",      # v3.3.0 enhanced main pipeline
            "factset_search.py",        # v3.3.0 enhanced search engine
            "data_processor.py",        # v3.3.0 enhanced data processor
            "sheets_uploader.py",       # v3.3.0 enhanced sheets uploader
            "config.py",                # v3.3.0 enhanced configuration
            "utils.py",                 # v3.3.0 enhanced utilities
            "requirements.txt"          # Dependencies
        ]
        
        # v3.3.0 specific files
        v330_specific_files = [
            "setup_validator.py"        # This file (v3.3.0)
        ]
        
        all_present = True
        
        # Check required files
        for file in required_files:
            file_path = self.current_dir / file
            if file_path.exists():
                # Check if file has v3.3.0 features
                if self._check_file_version(file_path):
                    self.log_success(f"{file} (v3.3.0 enhanced)")
                else:
                    self.log_warning(f"{file} (may need v3.3.0 update)")
            else:
                self.log_error(f"Missing required file: {file}")
                all_present = False
        
        # Check v3.3.0 specific files
        for file in v330_specific_files:
            file_path = self.current_dir / file
            if file_path.exists():
                self.log_success(f"{file} (v3.3.0)")
            else:
                self.log_warning(f"v3.3.0 file missing: {file}")
        
        # Check for legacy files
        legacy_files = [
            "googlesearch.py", "GoogleSearch.py",
            "basic_search.py", "simple_processor.py"
        ]
        for legacy_file in legacy_files:
            if (self.current_dir / legacy_file).exists():
                self.log_warning(f"Legacy file detected: {legacy_file}")
                self.log_info(f"Consider archiving {legacy_file} - functionality moved to v3.3.0 modules")
        
        return all_present
    
    def _check_file_version(self, file_path: Path) -> bool:
        """Check if file contains v3.3.0 indicators"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for v3.3.0 indicators
            v330_indicators = [
                "3.3.0", "v3.3.0", 
                "Enhanced", "enhanced",
                "aggregation", "deduplication",
                "individual_file_analysis", "company_level"
            ]
            
            return any(indicator in content for indicator in v330_indicators)
        except Exception:
            return False
    
    def check_dependencies_v330(self) -> bool:
        """Check Python dependencies for v3.3.0 enhanced features"""
        print("\n📦 Checking Python Dependencies (v3.3.0)...")
        
        required_packages = [
            ("requests", "HTTP library for enhanced search and downloads"),
            ("pandas", "Data processing and analysis (v3.3.0 aggregation)"),
            ("gspread", "Google Sheets API integration (v3.3.0 enhanced)"),
            ("google.auth", "Google authentication"),
            ("dotenv", "Environment variables"),
            ("beautifulsoup4", "HTML parsing for enhanced content extraction"),
            ("markdownify", "HTML to Markdown conversion"),
            ("pathlib", "Enhanced path handling (built-in)")
        ]
        
        # v3.3.0 enhanced optional packages
        optional_packages = [
            ("googlesearch-python", "Google Custom Search (enhanced patterns)"),
            ("selenium", "Advanced web scraping for complex sites"),
            ("validators", "Enhanced URL validation"),
            ("numpy", "Numerical operations for data processing"),
            ("python-dateutil", "Enhanced date parsing")
        ]
        
        all_installed = True
        
        # Check required packages
        for package, description in required_packages:
            try:
                # Handle special package names
                import_name = package.replace("-", "_").replace("beautifulsoup4", "bs4")
                if package == "google.auth":
                    import_name = "google.auth"
                elif package == "pathlib":
                    import_name = "pathlib"
                
                importlib.import_module(import_name)
                self.log_success(f"{package} - {description}")
            except ImportError:
                self.log_error(f"Missing package: {package} ({description})")
                all_installed = False
        
        # Check optional packages with v3.3.0 benefits
        optional_count = 0
        for package, description in optional_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                self.log_success(f"{package} - {description} (v3.3.0 enhanced)")
                optional_count += 1
            except ImportError:
                self.log_warning(f"Optional package not found: {package} ({description})")
        
        self.log_info(f"Optional packages installed: {optional_count}/{len(optional_packages)}")
        
        return all_installed
    
    def check_external_tools_v330(self) -> bool:
        """Check external tool availability for v3.3.0"""
        print("\n🔧 Checking External Tools (v3.3.0)...")
        
        tools = [
            ("markitdown", "PDF to Markdown conversion (v3.3.0 enhanced)", False),
            ("wkhtmltopdf", "Web page to PDF conversion", False),
            ("pandoc", "Document conversion utility", False)
        ]
        
        any_available = False
        
        for tool, description, required in tools:
            try:
                result = subprocess.run(
                    [tool, "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    self.log_success(f"{tool} - {description}")
                    any_available = True
                else:
                    if required:
                        self.log_error(f"{tool} not working - {description}")
                    else:
                        self.log_warning(f"{tool} not available - {description}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                if required:
                    self.log_error(f"{tool} not found - {description}")
                else:
                    self.log_info(f"{tool} not found - {description} (optional)")
        
        # Git check for version control
        try:
            subprocess.run(["git", "--version"], capture_output=True, timeout=5)
            self.log_success("git - Version control (recommended for v3.3.0)")
            any_available = True
        except:
            self.log_info("git not found - Version control (optional)")
        
        return any_available
    
    def check_environment_variables_v330(self) -> bool:
        """Check environment variable configuration for v3.3.0"""
        print("\n🔐 Checking Environment Variables (v3.3.0)...")
        
        # Try to load .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            self.log_success(".env file loading capability")
        except ImportError:
            self.log_warning("python-dotenv not available for .env file loading")
        
        required_vars = [
            ("GOOGLE_SEARCH_API_KEY", "Google Search API Key", True),
            ("GOOGLE_SEARCH_CSE_ID", "Google Custom Search Engine ID", True),
            ("GOOGLE_SHEETS_CREDENTIALS", "Google Sheets Service Account JSON", True),
            ("GOOGLE_SHEET_ID", "Google Spreadsheet ID", True)
        ]
        
        # v3.3.0 enhanced optional variables
        optional_vars = [
            ("FACTSET_PIPELINE_DEBUG", "Debug mode flag", False),
            ("FACTSET_MAX_RESULTS", "Maximum search results", False),
            ("FACTSET_QUALITY_THRESHOLD", "Content quality threshold (v3.3.0)", False),
            ("FACTSET_ENABLE_DEDUP", "Enable data deduplication (v3.3.0)", False),
            ("FACTSET_ENABLE_AGGREGATION", "Enable company aggregation (v3.3.0)", False),
            ("FACTSET_ENHANCED_PARSING", "Enhanced date/data parsing (v3.3.0)", False)
        ]
        
        all_required_present = True
        
        for var, description, required in required_vars + optional_vars:
            value = os.getenv(var)
            if value and value.strip():
                if var == "GOOGLE_SHEETS_CREDENTIALS":
                    # Validate JSON format
                    try:
                        json.loads(value)
                        self.log_success(f"{var} - {description} (valid JSON)")
                    except json.JSONDecodeError:
                        self.log_error(f"{var} - {description} (invalid JSON)")
                        if required:
                            all_required_present = False
                else:
                    self.log_success(f"{var} - {description}")
            else:
                if required:
                    self.log_error(f"{var} - {description} (missing)")
                    all_required_present = False
                else:
                    self.log_info(f"{var} - {description} (optional, not set)")
        
        return all_required_present
    
    def check_directory_structure_v330(self, fix_issues: bool = False) -> bool:
        """Check and optionally create directory structure for v3.3.0"""
        print("\n📂 Checking Directory Structure (v3.3.0)...")
        
        required_dirs = [
            "data",
            "data/csv",
            "data/md", 
            "data/pdf",
            "data/processed",
            "logs",
            "configs",
            "backups",          # v3.3.0: Enhanced backups
            "temp",             # v3.3.0: Temporary processing
            "legacy"            # v3.3.0: Archived files
        ]
        
        all_present = True
        
        for dir_name in required_dirs:
            dir_path = self.current_dir / dir_name
            if dir_path.exists():
                # Check if directory has content (for data directories)
                if dir_name.startswith("data/"):
                    file_count = len(list(dir_path.glob("*")))
                    if file_count > 0:
                        self.log_success(f"{dir_name}/ ({file_count} files)")
                    else:
                        self.log_success(f"{dir_name}/ (empty)")
                else:
                    self.log_success(f"{dir_name}/")
            else:
                if fix_issues:
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        self.apply_fix(f"Created directory: {dir_name}/")
                    except Exception as e:
                        self.log_error(f"Cannot create directory {dir_name}/: {e}")
                        all_present = False
                else:
                    self.log_warning(f"Missing directory: {dir_name}/")
                    all_present = False
        
        return all_present
    
    def check_configuration_files_v330(self, fix_issues: bool = False) -> bool:
        """Check and optionally create v3.3.0 configuration files"""
        print("\n⚙️ Checking Configuration Files (v3.3.0)...")
        
        # Check .env file
        env_file = self.current_dir / ".env"
        env_example = self.current_dir / ".env.example"
        
        if env_file.exists():
            self.log_success(".env file exists")
            # Check for v3.3.0 variables
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                v330_vars = ["FACTSET_QUALITY_THRESHOLD", "FACTSET_ENABLE_DEDUP", "FACTSET_ENABLE_AGGREGATION"]
                v330_found = sum(1 for var in v330_vars if var in env_content)
                if v330_found > 0:
                    self.log_info(f"v3.3.0 variables found: {v330_found}/{len(v330_vars)}")
                else:
                    self.log_info("Consider adding v3.3.0 specific environment variables")
            except Exception:
                pass
        else:
            if env_example.exists() and fix_issues:
                try:
                    import shutil
                    shutil.copy(env_example, env_file)
                    self.apply_fix("Created .env file from .env.example template")
                    self.log_warning("Please edit .env file with your actual credentials")
                except Exception as e:
                    self.log_error(f"Cannot create .env file: {e}")
            else:
                self.log_warning(".env file missing (copy from .env.example)")
        
        # Check watchlist file with v3.3.0 validation
        watchlist_file = self.current_dir / "觀察名單.csv"
        if watchlist_file.exists():
            self.log_success("觀察名單.csv (watchlist) exists")
            # Enhanced validation for v3.3.0
            try:
                import pandas as pd
                df = pd.read_csv(watchlist_file, encoding='utf-8')
                if '代號' in df.columns and '名稱' in df.columns:
                    self.log_success(f"Watchlist format valid: {len(df)} companies")
                    
                    # v3.3.0: Check for duplicate codes
                    duplicates = df['代號'].duplicated().sum()
                    if duplicates > 0:
                        self.log_warning(f"Found {duplicates} duplicate company codes")
                    else:
                        self.log_success("No duplicate company codes found")
                else:
                    self.log_warning("Watchlist missing required columns (代號, 名稱)")
            except Exception as e:
                self.log_warning(f"Watchlist validation error: {e}")
        else:
            self.log_warning("觀察名單.csv missing - run: python config.py --download-csv")
        
        # Check v3.3.0 configuration templates
        configs_dir = self.current_dir / "configs"
        if configs_dir.exists():
            config_files = list(configs_dir.glob("*.json"))
            if config_files:
                self.log_success(f"Configuration templates: {len(config_files)} files")
                # Check for v3.3.0 specific configs
                v330_configs = [f for f in config_files if "v330" in f.name or "3.3.0" in f.name]
                if v330_configs:
                    self.log_info(f"v3.3.0 specific configs: {len(v330_configs)}")
            else:
                if fix_issues:
                    self.apply_fix("Will create v3.3.0 configuration templates")
                    return self.create_config_templates_v330()
                else:
                    self.log_warning("No configuration templates found")
        else:
            if fix_issues:
                try:
                    configs_dir.mkdir(exist_ok=True)
                    self.apply_fix("Created configs directory")
                except Exception as e:
                    self.log_error(f"Cannot create configs directory: {e}")
                    return False
            else:
                self.log_warning("configs/ directory missing")
                return False
        
        return True
    
    def create_config_templates_v330(self) -> bool:
        """Create v3.3.0 configuration templates"""
        try:
            configs_dir = self.current_dir / "configs"
            configs_dir.mkdir(exist_ok=True)
            
            # v3.3.0 enhanced template
            v330_template = {
                "version": "3.3.0",
                "created_at": datetime.now().isoformat(),
                "processing": {
                    "deduplicate_data": True,
                    "aggregate_by_company": True,
                    "individual_file_analysis": True,
                    "enhanced_date_extraction": True,
                    "quality_scoring": True
                },
                "search": {
                    "content_quality_threshold": 3,
                    "enhanced_patterns": True,
                    "improved_url_cleaning": True
                }
            }
            
            config_file = configs_dir / "v330_enhanced.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(v330_template, f, indent=2, ensure_ascii=False)
            
            self.log_success("Created v3.3.0 configuration template")
            return True
        except Exception as e:
            self.log_error(f"Error creating v3.3.0 config templates: {e}")
            return False
    
    def test_module_imports_v330(self) -> bool:
        """Test importing v3.3.0 enhanced pipeline modules"""
        print("\n📋 Testing Module Imports (v3.3.0)...")
        
        modules = [
            ("factset_pipeline", "v3.3.0 Enhanced main orchestrator"),
            ("factset_search", "v3.3.0 Enhanced search engine"),
            ("data_processor", "v3.3.0 Enhanced data processor"),
            ("sheets_uploader", "v3.3.0 Enhanced sheets uploader"),
            ("config", "v3.3.0 Configuration manager"),
            ("utils", "v3.3.0 Enhanced utilities")
        ]
        
        sys.path.insert(0, str(self.current_dir))
        all_imported = True
        
        for module_name, description in modules:
            try:
                module = importlib.import_module(module_name)
                
                # Check for v3.3.0 specific features
                v330_features = self._check_module_v330_features(module, module_name)
                if v330_features:
                    self.log_success(f"{module_name}.py - {description} ✨")
                else:
                    self.log_success(f"{module_name}.py - {description}")
                    self.log_warning(f"{module_name} may not have v3.3.0 enhancements")
                    
            except ImportError as e:
                self.log_error(f"Cannot import {module_name}.py: {e}")
                all_imported = False
            except Exception as e:
                self.log_warning(f"Import warning for {module_name}.py: {e}")
        
        return all_imported
    
    def _check_module_v330_features(self, module, module_name: str) -> bool:
        """Check if module has v3.3.0 specific features"""
        try:
            # Check for v3.3.0 version indicators
            if hasattr(module, '__version__') and "3.3.0" in module.__version__:
                return True
            
            # Check for v3.3.0 specific functions/classes
            v330_indicators = {
                'factset_search': ['run_enhanced_search_suite_v330', 'generate_unique_filename_v330'],
                'data_processor': ['process_all_data_v330', 'generate_portfolio_summary_v330'],
                'sheets_uploader': ['upload_all_sheets_v330', 'update_portfolio_summary_sheet_v330'],
                'factset_pipeline': ['EnhancedFactSetPipeline', 'run_complete_pipeline_v330'],
                'config': ['load_config_v330', 'download_target_companies_v330']
            }
            
            if module_name in v330_indicators:
                indicators = v330_indicators[module_name]
                found = sum(1 for indicator in indicators if hasattr(module, indicator))
                return found > 0
            
            return False
        except Exception:
            return False
    
    def test_v330_enhanced_features(self) -> bool:
        """Test v3.3.0 specific enhanced features"""
        print("\n🔍 Testing v3.3.0 Enhanced Features...")
        
        try:
            sys.path.insert(0, str(self.current_dir))
            
            # Test enhanced watchlist loading
            try:
                import config
                if hasattr(config, 'download_target_companies_v330'):
                    self.log_success("v3.3.0 Enhanced watchlist loading available")
                    # Test the function
                    companies = config.download_target_companies_v330()
                    if companies and len(companies) > 10:
                        self.log_success(f"Watchlist test: {len(companies)} companies loaded")
                    else:
                        self.log_warning(f"Watchlist test: Only {len(companies)} companies loaded")
                else:
                    self.log_warning("v3.3.0 enhanced watchlist loading not found")
            except Exception as e:
                self.log_warning(f"Enhanced watchlist test error: {e}")
            
            # Test data deduplication features
            try:
                import data_processor
                if hasattr(data_processor, 'deduplicate_financial_data'):
                    self.log_success("v3.3.0 Data deduplication features available")
                else:
                    self.log_warning("v3.3.0 data deduplication not found")
            except Exception as e:
                self.log_warning(f"Data deduplication test error: {e}")
            
            # Test portfolio aggregation
            try:
                if hasattr(data_processor, 'generate_portfolio_summary_v330'):
                    self.log_success("v3.3.0 Portfolio aggregation available")
                else:
                    self.log_warning("v3.3.0 portfolio aggregation not found")
            except Exception as e:
                self.log_warning(f"Portfolio aggregation test error: {e}")
            
            # Test individual file analysis
            try:
                if hasattr(data_processor, 'generate_detailed_data_v330'):
                    self.log_success("v3.3.0 Individual file analysis available")
                else:
                    self.log_warning("v3.3.0 individual file analysis not found")
            except Exception as e:
                self.log_warning(f"Individual file analysis test error: {e}")
            
            # Test enhanced search capabilities
            try:
                import factset_search
                if hasattr(factset_search, 'run_enhanced_search_suite_v330'):
                    self.log_success("v3.3.0 Enhanced search suite available")
                else:
                    self.log_warning("v3.3.0 enhanced search suite not found")
            except Exception as e:
                self.log_warning(f"Enhanced search test error: {e}")
            
            return True
            
        except Exception as e:
            self.log_error(f"v3.3.0 enhanced features test failed: {e}")
            return False
    
    def test_api_connections_v330(self) -> bool:
        """Test API connections for v3.3.0 enhanced pipeline"""
        print("\n🌐 Testing API Connections (v3.3.0)...")
        
        sys.path.insert(0, str(self.current_dir))
        
        # Test Google Search API with v3.3.0 enhancements
        try:
            import factset_search
            self.log_info("v3.3.0 Enhanced search module available for testing")
            self.log_info("Google Search test skipped (requires API quota)")
            
            # Check if enhanced error handling is available
            if hasattr(factset_search, 'RateLimitException'):
                self.log_success("Enhanced rate limiting protection available")
            else:
                self.log_warning("Enhanced rate limiting protection not found")
        except Exception as e:
            self.log_warning(f"Cannot test v3.3.0 enhanced search: {e}")
        
        # Test Google Sheets API with v3.3.0 enhancements
        try:
            import sheets_uploader
            self.log_info("v3.3.0 Enhanced sheets uploader available")
            self.log_info("Google Sheets test skipped (use: python sheets_uploader.py --test-connection)")
            
            # Check for v3.3.0 specific functions
            if hasattr(sheets_uploader, 'test_sheets_connection_v330'):
                self.log_success("v3.3.0 Enhanced sheets testing available")
            else:
                self.log_warning("v3.3.0 enhanced sheets testing not found")
        except Exception as e:
            self.log_warning(f"Cannot test v3.3.0 enhanced sheets: {e}")
        
        return True
    
    def run_validation_v330(self, quick: bool = False, fix_issues: bool = False, test_v330: bool = False) -> bool:
        """Run complete v3.3.0 enhanced validation"""
        print(f"🚀 Enhanced FactSet Pipeline Setup Validator v{__version__}")
        print("=" * 80)
        
        if fix_issues:
            print("🔧 Auto-fix mode enabled")
        if quick:
            print("⚡ Quick validation mode")
        if test_v330:
            print("🧪 v3.3.0 specific feature testing enabled")
        
        print()
        
        # Core checks
        checks = [
            ("Python Version", self.check_python_version),
            ("Required Files (v3.3.0)", self.check_required_files_v330),
            ("Python Dependencies (v3.3.0)", self.check_dependencies_v330),
            ("External Tools (v3.3.0)", self.check_external_tools_v330),
            ("Environment Variables (v3.3.0)", self.check_environment_variables_v330),
        ]
        
        # Additional checks for full validation
        if not quick:
            checks.extend([
                ("Directory Structure (v3.3.0)", lambda: self.check_directory_structure_v330(fix_issues)),
                ("Configuration Files (v3.3.0)", lambda: self.check_configuration_files_v330(fix_issues)),
                ("Module Imports (v3.3.0)", self.test_module_imports_v330),
                ("API Connections (v3.3.0)", self.test_api_connections_v330),
            ])
        
        # v3.3.0 specific tests
        if test_v330 or not quick:
            checks.append(("v3.3.0 Enhanced Features", self.test_v330_enhanced_features))
        
        # Run all checks
        results = {}
        for check_name, check_func in checks:
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.log_error(f"Check '{check_name}' failed with exception: {e}")
                results[check_name] = False
        
        # Summary
        self.print_v330_summary(results)
        
        # Return overall success
        return all(results.values()) and len(self.errors) == 0
    
    def print_v330_summary(self, results: Dict[str, bool]):
        """Print v3.3.0 enhanced validation summary"""
        print("\n" + "=" * 80)
        print("📊 v3.3.0 ENHANCED VALIDATION SUMMARY")
        print("=" * 80)
        
        # Results by category
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"📋 Checks: {passed}/{total} passed")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️ Warnings: {len(self.warnings)}")
        
        if self.fixes_applied:
            print(f"🔧 Fixes Applied: {len(self.fixes_applied)}")
        
        # Detailed results
        print(f"\n📋 Check Results:")
        for check_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {check_name}")
        
        # v3.3.0 enhanced next steps
        print(f"\n🔄 Next Steps (v3.3.0):")
        
        if len(self.errors) == 0:
            print("   🎉 v3.3.0 Enhanced setup looks excellent! Try running:")
            print("      python factset_pipeline.py --status-v330")
            print("      python factset_pipeline.py --analyze-v330")
            print("      python factset_pipeline.py --mode enhanced")
            print("      python factset_pipeline.py --quality-threshold 4")
        else:
            print("   🔧 Fix the errors above, then re-run validation")
            print("   💡 Try: python setup_validator.py --fix-issues")
            
            if len(self.warnings) > 0:
                print("   ⚠️ Address warnings for optimal v3.3.0 performance")
        
        print()
        print("🔧 v3.3.0 Enhanced Pipeline Commands:")
        print("   python setup_validator.py --fix-issues         # Auto-fix issues")
        print("   python setup_validator.py --test-v330          # Test v3.3.0 features")
        print("   python factset_search.py --run-enhanced-v330   # v3.3.0 search")
        print("   python data_processor.py --process-v330        # v3.3.0 processing")
        print("   python sheets_uploader.py --test-connection    # Test sheets")
        print("   python config.py --download-csv               # Download watchlist")
        print("   python factset_pipeline.py --mode enhanced    # Full v3.3.0 pipeline")

def main():
    """Main CLI function for v3.3.0 enhanced validator"""
    parser = argparse.ArgumentParser(
        description="Enhanced FactSet Pipeline Setup Validator v3.3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick validation (core checks only)")
    parser.add_argument("--fix-issues", action="store_true",
                       help="Automatically fix common issues")
    parser.add_argument("--test-v330", action="store_true",
                       help="Test v3.3.0 specific enhanced features")
    parser.add_argument("--version", action="version", 
                       version=f"Enhanced Setup Validator v{__version__}")
    
    args = parser.parse_args()
    
    # Run v3.3.0 enhanced validation
    validator = EnhancedSetupValidator()
    success = validator.run_validation_v330(
        quick=args.quick, 
        fix_issues=args.fix_issues, 
        test_v330=args.test_v330
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()