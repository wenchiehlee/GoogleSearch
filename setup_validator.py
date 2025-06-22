#!/usr/bin/env python3
"""
setup_validator.py - Installation and Configuration Validator (Updated for Enhanced Architecture)

Version: 3.2.0
Date: 2025-06-22
Author: FactSet Pipeline - Enhanced Architecture
License: MIT

UPDATES FOR ENHANCED ARCHITECTURE:
- ✅ Updated required files list to reflect factset_search.py
- ✅ Enhanced validation for priority-based search capabilities
- ✅ Improved module import testing for enhanced architecture
- ✅ Added validation for watchlist integration components
- ✅ Updated recommendations for enhanced pipeline usage

Description:
    Comprehensive setup validation script for the Enhanced FactSet Pipeline.
    Validates all dependencies, configurations, and connections for the
    streamlined architecture with priority-based search capabilities.

Usage:
    python setup_validator.py                    # Full validation
    python setup_validator.py --quick           # Quick validation
    python setup_validator.py --fix-issues      # Auto-fix common issues
"""

import os
import sys
import json
import argparse
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Version Information
__version__ = "3.2.0"
__date__ = "2025-06-22"
__author__ = "FactSet Pipeline - Enhanced Architecture"

class EnhancedSetupValidator:
    """Enhanced setup validation for FactSet Pipeline v3.2.0"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes_applied = []
        self.current_dir = Path(__file__).parent
        
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
        """Check Python version compatibility"""
        print("\n🐍 Checking Python Version...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            self.log_success(f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.log_error(f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
            return False
    
    def check_required_files(self) -> bool:
        """Check for required enhanced pipeline files"""
        print("\n📁 Checking Required Files...")
        
        # Updated required files for enhanced architecture
        required_files = [
            "factset_pipeline.py",
            "factset_search.py",      # Updated: was googlesearch.py
            "data_processor.py",
            "sheets_uploader.py",
            "config.py",
            "utils.py",
            "requirements.txt"
        ]
        
        all_present = True
        
        for file in required_files:
            file_path = self.current_dir / file
            if file_path.exists():
                self.log_success(f"{file}")
            else:
                self.log_error(f"Missing required file: {file}")
                all_present = False
        
        # Check for legacy files and suggest migration
        legacy_files = ["googlesearch.py", "GoogleSearch.py"]
        for legacy_file in legacy_files:
            if (self.current_dir / legacy_file).exists():
                self.log_warning(f"Legacy file detected: {legacy_file}")
                self.log_info(f"Consider archiving {legacy_file} - functionality moved to factset_search.py")
        
        return all_present
    
    def check_dependencies(self) -> bool:
        """Check Python dependencies for enhanced features"""
        print("\n📦 Checking Python Dependencies...")
        
        required_packages = [
            ("requests", "HTTP library for search and downloads"),
            ("pandas", "Data processing and analysis"),
            ("gspread", "Google Sheets API integration"),
            ("google.auth", "Google authentication"),
            ("dotenv", "Environment variables"),
            ("beautifulsoup4", "HTML parsing for content extraction"),
            ("markdownify", "HTML to Markdown conversion")
        ]
        
        # Optional but recommended packages
        optional_packages = [
            ("googlesearch-python", "Google Custom Search functionality"),
            ("selenium", "Advanced web scraping capabilities")
        ]
        
        all_installed = True
        
        # Check required packages
        for package, description in required_packages:
            try:
                importlib.import_module(package.replace("-", "_").replace("beautifulsoup4", "bs4"))
                self.log_success(f"{package} - {description}")
            except ImportError:
                self.log_error(f"Missing package: {package} ({description})")
                all_installed = False
        
        # Check optional packages
        for package, description in optional_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                self.log_success(f"{package} - {description} (optional)")
            except ImportError:
                self.log_warning(f"Optional package not found: {package} ({description})")
        
        return all_installed
    
    def check_external_tools(self) -> bool:
        """Check external tool availability"""
        print("\n🔧 Checking External Tools...")
        
        tools = [
            ("markitdown", "PDF to Markdown conversion", True),
            ("wkhtmltopdf", "Web page to PDF conversion", False)
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
                    self.log_warning(f"{tool} not found - {description}")
        
        return any_available
    
    def check_environment_variables(self) -> bool:
        """Check environment variable configuration for enhanced features"""
        print("\n🔐 Checking Environment Variables...")
        
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
        
        optional_vars = [
            ("FACTSET_PIPELINE_DEBUG", "Debug mode flag", False),
            ("FACTSET_MAX_RESULTS", "Maximum search results", False)
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
    
    def check_directory_structure(self, fix_issues: bool = False) -> bool:
        """Check and optionally create directory structure for enhanced pipeline"""
        print("\n📂 Checking Directory Structure...")
        
        required_dirs = [
            "data",
            "data/csv",
            "data/md", 
            "data/pdf",
            "data/processed",
            "logs",
            "configs",
            "legacy"  # Added: for archived files
        ]
        
        all_present = True
        
        for dir_name in required_dirs:
            dir_path = self.current_dir / dir_name
            if dir_path.exists():
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
    
    def check_configuration_files(self, fix_issues: bool = False) -> bool:
        """Check and optionally create configuration files"""
        print("\n⚙️ Checking Configuration Files...")
        
        # Check .env file
        env_file = self.current_dir / ".env"
        env_example = self.current_dir / ".env.example"
        
        if env_file.exists():
            self.log_success(".env file exists")
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
        
        # Check watchlist file
        watchlist_file = self.current_dir / "觀察名單.csv"
        if watchlist_file.exists():
            self.log_success("觀察名單.csv (watchlist) exists")
            # Validate watchlist format
            try:
                import pandas as pd
                df = pd.read_csv(watchlist_file, encoding='utf-8')
                if '代號' in df.columns and '名稱' in df.columns:
                    self.log_success(f"Watchlist format valid: {len(df)} companies")
                else:
                    self.log_warning("Watchlist missing required columns (代號, 名稱)")
            except Exception as e:
                self.log_warning(f"Watchlist validation error: {e}")
        else:
            self.log_warning("觀察名單.csv missing - run: python config.py --download-csv")
        
        # Check configuration templates
        configs_dir = self.current_dir / "configs"
        if configs_dir.exists():
            config_files = list(configs_dir.glob("*.json"))
            if config_files:
                self.log_success(f"Configuration templates: {len(config_files)} files")
            else:
                if fix_issues:
                    self.apply_fix("Will create configuration templates")
                    return self.create_config_templates()
                else:
                    self.log_warning("No configuration templates found")
        else:
            if fix_issues and (self.current_dir / "config.py").exists():
                try:
                    sys.path.insert(0, str(self.current_dir))
                    import config
                    config.create_template_configs()
                    self.apply_fix("Created configuration templates")
                except Exception as e:
                    self.log_error(f"Cannot create config templates: {e}")
                    return False
            else:
                self.log_warning("configs/ directory missing")
                return False
        
        return True
    
    def create_config_templates(self) -> bool:
        """Create configuration templates using config.py"""
        try:
            sys.path.insert(0, str(self.current_dir))
            import config
            config.create_template_configs()
            self.log_success("Configuration templates created")
            return True
        except Exception as e:
            self.log_error(f"Error creating config templates: {e}")
            return False
    
    def test_module_imports(self) -> bool:
        """Test importing enhanced pipeline modules"""
        print("\n📋 Testing Module Imports...")
        
        modules = [
            ("factset_pipeline", "Enhanced main orchestrator"),
            ("factset_search", "Enhanced search engine"),  # Updated: was googlesearch
            ("data_processor", "Enhanced data processor"),
            ("sheets_uploader", "Enhanced sheets uploader"),
            ("config", "Configuration manager"),
            ("utils", "Utilities")
        ]
        
        sys.path.insert(0, str(self.current_dir))
        all_imported = True
        
        for module_name, description in modules:
            try:
                importlib.import_module(module_name)
                self.log_success(f"{module_name}.py - {description}")
            except ImportError as e:
                self.log_error(f"Cannot import {module_name}.py: {e}")
                all_imported = False
            except Exception as e:
                self.log_warning(f"Import warning for {module_name}.py: {e}")
        
        return all_imported
    
    def test_enhanced_features(self) -> bool:
        """Test enhanced pipeline features"""
        print("\n🔍 Testing Enhanced Features...")
        
        try:
            sys.path.insert(0, str(self.current_dir))
            
            # Test watchlist loading
            try:
                import config
                test_config = config.load_config()
                companies = test_config.get('target_companies', [])
                if companies and len(companies) > 10:
                    self.log_success(f"Watchlist integration: {len(companies)} companies loaded")
                else:
                    self.log_warning(f"Watchlist integration: Only {len(companies)} companies loaded")
            except Exception as e:
                self.log_warning(f"Watchlist test error: {e}")
            
            # Test enhanced search module availability
            try:
                import factset_search
                if hasattr(factset_search, 'run_enhanced_search_suite'):
                    self.log_success("Enhanced search capabilities available")
                else:
                    self.log_warning("Enhanced search module missing key functions")
            except Exception as e:
                self.log_warning(f"Enhanced search test error: {e}")
            
            # Test priority management
            try:
                if hasattr(factset_search, 'SearchPrioritizer'):
                    self.log_success("Priority-based search management available")
                else:
                    self.log_warning("Priority management features not found")
            except:
                self.log_warning("Priority management test failed")
            
            return True
            
        except Exception as e:
            self.log_error(f"Enhanced features test failed: {e}")
            return False
    
    def test_api_connections(self) -> bool:
        """Test API connections for enhanced pipeline"""
        print("\n🌐 Testing API Connections...")
        
        sys.path.insert(0, str(self.current_dir))
        
        # Test Google Search API
        try:
            import factset_search
            self.log_info("Enhanced search module available for testing")
            self.log_info("Google Search test skipped (requires API quota)")
        except Exception as e:
            self.log_warning(f"Cannot test enhanced search: {e}")
        
        # Test Google Sheets API
        try:
            import sheets_uploader
            self.log_info("Enhanced sheets uploader available")
            self.log_info("Google Sheets test skipped (use: python sheets_uploader.py --test-connection)")
        except Exception as e:
            self.log_warning(f"Cannot test enhanced sheets: {e}")
        
        return True
    
    def run_validation(self, quick: bool = False, fix_issues: bool = False) -> bool:
        """Run complete enhanced validation"""
        print(f"🚀 Enhanced FactSet Pipeline Setup Validator v{__version__}")
        print("=" * 80)
        
        if fix_issues:
            print("🔧 Auto-fix mode enabled")
        if quick:
            print("⚡ Quick validation mode")
        
        print()
        
        # Core checks
        checks = [
            ("Python Version", self.check_python_version),
            ("Required Files", self.check_required_files),
            ("Python Dependencies", self.check_dependencies),
            ("External Tools", self.check_external_tools),
            ("Environment Variables", self.check_environment_variables),
        ]
        
        # Additional checks for full validation
        if not quick:
            checks.extend([
                ("Directory Structure", lambda: self.check_directory_structure(fix_issues)),
                ("Configuration Files", lambda: self.check_configuration_files(fix_issues)),
                ("Module Imports", self.test_module_imports),
                ("Enhanced Features", self.test_enhanced_features),
                ("API Connections", self.test_api_connections),
            ])
        
        # Run all checks
        results = {}
        for check_name, check_func in checks:
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.log_error(f"Check '{check_name}' failed with exception: {e}")
                results[check_name] = False
        
        # Summary
        self.print_enhanced_summary(results)
        
        # Return overall success
        return all(results.values()) and len(self.errors) == 0
    
    def print_enhanced_summary(self, results: Dict[str, bool]):
        """Print enhanced validation summary"""
        print("\n" + "=" * 80)
        print("📊 ENHANCED VALIDATION SUMMARY")
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
        
        # Enhanced next steps
        print(f"\n🔄 Next Steps:")
        
        if len(self.errors) == 0:
            print("   🎉 Enhanced setup looks good! Try running:")
            print("      python factset_pipeline.py --status")
            print("      python factset_pipeline.py --analyze-data")
            print("      python factset_pipeline.py --strategy high_priority_focus")
        else:
            print("   🔧 Fix the errors above, then re-run validation")
            print("   💡 Try: python setup_validator.py --fix-issues")
            
            if len(self.warnings) > 0:
                print("   ⚠️ Also address warnings for optimal performance")
        
        print()
        print("🔧 Enhanced Pipeline Commands:")
        print("   python setup_validator.py --fix-issues         # Auto-fix issues")
        print("   python factset_search.py --validate-setup      # Test enhanced search")
        print("   python factset_search.py --priority-focus high_only  # Priority search")
        print("   python sheets_uploader.py --test-connection     # Test sheets")
        print("   python config.py --download-csv                # Download watchlist")
        print("   python factset_pipeline.py --analyze-data      # Analyze existing data")

def main():
    """Main CLI function for enhanced validator"""
    parser = argparse.ArgumentParser(
        description="Enhanced FactSet Pipeline Setup Validator v3.2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick validation (core checks only)")
    parser.add_argument("--fix-issues", action="store_true",
                       help="Automatically fix common issues")
    parser.add_argument("--version", action="version", 
                       version=f"Enhanced Setup Validator v{__version__}")
    
    args = parser.parse_args()
    
    # Run enhanced validation
    validator = EnhancedSetupValidator()
    success = validator.run_validation(quick=args.quick, fix_issues=args.fix_issues)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()