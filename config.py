"""
config.py - Configuration Management Module (FIXED FOR WATCHLIST)

Version: 3.0.0
Date: 2025-06-21
Author: Modular FactSet Pipeline Architecture

WATCHLIST FIXES:
1. ✅ Fixed CSV parsing to handle "代號,名稱" format correctly
2. ✅ Removed hardcoded COMPANY_NAME_MAPPING (CSV is single source of truth)
3. ✅ Added missing configuration keys (csv_dir, pdf_dir, md_dir)
4. ✅ Saves 觀察名單.csv locally automatically
"""

import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import csv
import io

# Version Information
__version__ = "3.0.0"
__date__ = "2025-06-21"
__author__ = "Google Search FactSet Pipeline - Modular Architecture"

# Load environment variables
load_dotenv()

# ============================================================================
# TARGET COMPANIES FROM CSV (WATCHLIST APPROACH)
# ============================================================================

WATCH_LIST_URL = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"

def download_target_companies(save_local_csv=True):
    """Download target companies from 觀察名單.csv (WATCHLIST FIXED VERSION)"""
    try:
        print("📥 Downloading target companies from 觀察名單...")
        response = requests.get(WATCH_LIST_URL, timeout=10)
        
        if response.status_code == 200:
            # Save the CSV locally
            if save_local_csv:
                try:
                    with open("觀察名單.csv", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    print("💾 Saved watch list as: 觀察名單.csv")
                except Exception as e:
                    print(f"⚠️ Could not save local CSV: {e}")
            
            # Parse CSV directly - NO hardcoded mapping!
            companies = []
            csv_content = io.StringIO(response.text)
            csv_reader = csv.reader(csv_content)
            
            # Get header
            try:
                header = next(csv_reader)
                print(f"📋 CSV Header: {header}")
            except StopIteration:
                print("❌ Empty CSV file")
                return get_fallback_companies()
            
            # Parse all companies directly from CSV
            for row_num, row in enumerate(csv_reader, 1):
                if len(row) >= 2:
                    code = row[0].strip().strip('"')
                    name = row[1].strip().strip('"')
                    
                    if code and code.isdigit() and len(code) == 4:
                        companies.append({
                            "code": code,
                            "name": name,
                            "full": f"{code}{name}"
                        })
                        
                        # Show first few
                        if row_num <= 5:
                            print(f"   ✅ {code} -> {name}")
            
            print(f"✅ Downloaded {len(companies)} target companies from CSV")
            if len(companies) > 5:
                print(f"📊 Companies: {companies[0]['name']}, {companies[1]['name']}, ... +{len(companies)-2} more")
            
            return companies if len(companies) > 0 else get_fallback_companies()
            
        else:
            print(f"⚠️ Failed to download CSV: HTTP {response.status_code}")
            return get_fallback_companies()
            
    except Exception as e:
        print(f"⚠️ Error downloading CSV: {e}")
        return get_fallback_companies()

def get_fallback_companies():
    """Fallback companies if CSV download fails"""
    print("🔄 Using fallback companies...")
    return [
        {"code": "2382", "name": "廣達", "full": "2382廣達"},
        {"code": "2330", "name": "台積電", "full": "2330台積電"},
        {"code": "2317", "name": "鴻海", "full": "2317鴻海"},
        {"code": "2454", "name": "聯發科", "full": "2454聯發科"},
        {"code": "2412", "name": "中華電", "full": "2412中華電"}
    ]

# ============================================================================
# FIXED CONFIGURATION STRUCTURE
# ============================================================================

DEFAULT_CONFIG = {
    "pipeline": {
        "name": "Google Search FactSet Data Pipeline",
        "version": "3.0.0",
        "timeout": 3600,
        "max_retries": 3
    },
    "target_companies": None,  # Will be loaded dynamically
    "search": {
        "max_results": 500,
        "timeout": 30,
        "parallel_searches": 1,
        "default_days": 360,
        "default_language": "lang_zh-TW",
        "default_country": None,
        "enable_watch_list": True
    },
    "input": {
        "csv_dir": "data/csv",
        "md_dir": "data/md",
        "pdf_dir": "data/pdf"
    },
    "output": {
        "csv_dir": "data/csv",        # FIXED: Added missing key
        "pdf_dir": "data/pdf",        # FIXED: Added missing key
        "md_dir": "data/md",          # FIXED: Added missing key
        "processed_dir": "data/processed",
        "consolidated_csv": "data/processed/consolidated_factset.csv",
        "summary_csv": "data/processed/portfolio_summary.csv",
        "stats_json": "data/processed/statistics.json",
        "logs_dir": "logs"
    },
    "quality": {
        "min_fields_for_complete": 4,
        "required_fields": ["公司名稱", "股票代號", "當前EPS預估", "目標價"],
        "quality_thresholds": {
            "excellent": 4, "good": 3, "fair": 2, "poor": 1, "missing": 0
        }
    },
    "sheets": {
        "auto_backup": True,
        "create_missing_sheets": True,
        "update_frequency": "on_demand",
        "max_backup_count": 5,
        "sheet_names": {
            "portfolio": "Portfolio Summary",
            "detailed": "Detailed Data", 
            "statistics": "Statistics"
        },
        "sheet_dimensions": {
            "portfolio": {"rows": 50, "cols": 15},
            "detailed": {"rows": 200, "cols": 25},
            "statistics": {"rows": 30, "cols": 5}
        }
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file_logging": True,
        "console_logging": True
    }
}

# Configuration templates
QUICK_CONFIG = {
    "pipeline": {"name": "FactSet Pipeline - Quick Mode"},
    "search": {"max_results": 100, "timeout": 15, "default_days": 90},
    "target_companies": "load_from_csv"
}

COMPREHENSIVE_CONFIG = {
    "pipeline": {"name": "FactSet Pipeline - Comprehensive Mode"},
    "search": {"max_results": 1000, "timeout": 60, "parallel_searches": 3, "default_days": 720},
    "target_companies": "load_from_csv"
}

CONFIG_TEMPLATES = {
    "default": DEFAULT_CONFIG,
    "quick": QUICK_CONFIG,
    "comprehensive": COMPREHENSIVE_CONFIG
}

# ============================================================================
# CONFIGURATION FUNCTIONS
# ============================================================================

def load_config(config_file=None, template=None):
    """Load configuration with dynamic CSV loading"""
    config = DEFAULT_CONFIG.copy()
    
    # Load target companies
    if config.get("target_companies") is None:
        config["target_companies"] = download_target_companies()
    
    # Apply template
    if template and template in CONFIG_TEMPLATES:
        template_config = CONFIG_TEMPLATES[template].copy()
        if template_config.get("target_companies") == "load_from_csv":
            template_config["target_companies"] = download_target_companies()
        config = merge_configs(config, template_config)
        print(f"📄 Applied template: {template}")
    
    # Load from file
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                if file_config.get("target_companies") == "load_from_csv":
                    file_config["target_companies"] = download_target_companies()
                config = merge_configs(config, file_config)
                print(f"📄 Loaded config file: {config_file}")
        except Exception as e:
            print(f"⚠️ Error loading config file {config_file}: {e}")
    
    # Final check
    if not config.get("target_companies"):
        config["target_companies"] = download_target_companies()
    
    # Apply environment overrides
    config = apply_env_overrides(config)
    
    # Validate
    validate_config(config)
    
    return config

def merge_configs(base_config, override_config):
    """Merge configuration dictionaries"""
    merged = base_config.copy()
    for key, value in override_config.items():
        if (key in merged and isinstance(merged[key], dict) and isinstance(value, dict)):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def apply_env_overrides(config):
    """Apply environment variable overrides"""
    env_mappings = {
        "GOOGLE_SEARCH_API_KEY": ("search", "api_key"),
        "GOOGLE_SEARCH_CSE_ID": ("search", "cse_id"),
        "GOOGLE_SHEET_ID": ("sheets", "sheet_id"),
        "GOOGLE_SHEETS_CREDENTIALS": ("sheets", "credentials"),
        "FACTSET_PIPELINE_DEBUG": ("logging", "debug"),
        "FACTSET_PIPELINE_TIMEOUT": ("pipeline", "timeout"),
        "FACTSET_MAX_RESULTS": ("search", "max_results")
    }
    
    applied_overrides = []
    for env_var, (section, key) in env_mappings.items():
        value = os.getenv(env_var)
        if value:
            if section not in config:
                config[section] = {}
            if key in ["timeout", "max_results", "parallel_searches"]:
                try:
                    value = int(value)
                except ValueError:
                    continue
            elif key == "debug":
                value = value.lower() in ['true', '1', 'yes', 'on']
            config[section][key] = value
            applied_overrides.append(f"{env_var} -> {section}.{key}")
    
    if applied_overrides:
        print(f"🔧 Applied {len(applied_overrides)} environment overrides")
    
    return config

def validate_config(config):
    """Validate configuration"""
    errors = []
    warnings = []
    
    required_sections = ["target_companies", "search", "input", "output", "sheets"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    if "target_companies" in config:
        if not config["target_companies"]:
            errors.append("target_companies cannot be empty")
        else:
            for i, company in enumerate(config["target_companies"]):
                if not isinstance(company, dict):
                    errors.append(f"target_companies[{i}] must be a dictionary")
                elif not all(key in company for key in ["code", "name"]):
                    errors.append(f"target_companies[{i}] missing required keys (code, name)")
    
    api_key = config.get("search", {}).get("api_key") or os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = config.get("search", {}).get("cse_id") or os.getenv("GOOGLE_SEARCH_CSE_ID")
    
    if not api_key:
        warnings.append("Google Search API key not configured")
    if not cse_id:
        warnings.append("Google Custom Search Engine ID not configured")
    
    if errors:
        print("❌ Configuration validation errors:")
        for error in errors:
            print(f"   - {error}")
        raise ValueError("Configuration validation failed")
    
    if warnings:
        print("⚠️ Configuration warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    print("✅ Configuration validation passed")

def save_config(config, output_file):
    """Save configuration to file"""
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"💾 Configuration saved: {output_file}")
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")

def create_template_configs():
    """Create template configuration files"""
    template_dir = "configs"
    os.makedirs(template_dir, exist_ok=True)
    for name, template_config in CONFIG_TEMPLATES.items():
        if name != "default":
            output_file = os.path.join(template_dir, f"{name}.json")
            save_config(template_config, output_file)
    print(f"📁 Template configurations created in: {template_dir}/")

def print_config_summary(config):
    """Print configuration summary"""
    print(f"\n📋 Configuration Summary")
    print("=" * 40)
    pipeline = config.get("pipeline", {})
    print(f"Pipeline: {pipeline.get('name', 'FactSet Pipeline')} v{pipeline.get('version', '3.0.0')}")
    companies = config.get("target_companies", [])
    print(f"Target Companies: {len(companies)} (from 觀察名單.csv)")
    for company in companies[:3]:
        print(f"   - {company.get('full', company.get('name', 'Unknown'))}")
    if len(companies) > 3:
        print(f"   ... and {len(companies) - 3} more")

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI for configuration management"""
    import argparse
    parser = argparse.ArgumentParser(description='Configuration Manager v3.0.0 (Watchlist Fixed)')
    parser.add_argument('--template', choices=CONFIG_TEMPLATES.keys(), help='Load configuration template')
    parser.add_argument('--create-templates', action='store_true', help='Create template configuration files')
    parser.add_argument('--download-csv', action='store_true', help='Download 觀察名單.csv')
    parser.add_argument('--show', action='store_true', help='Show configuration summary')
    parser.add_argument('--save', type=str, help='Save current config to file')
    
    args = parser.parse_args()
    
    if args.download_csv:
        companies = download_target_companies(save_local_csv=True)
        print(f"✅ Downloaded {len(companies)} companies and saved as 觀察名單.csv")
        return
    
    if args.create_templates:
        create_template_configs()
        return
    
    config = load_config(template=args.template)
    
    if args.show:
        print_config_summary(config)
    
    if args.save:
        save_config(config, args.save)

if __name__ == "__main__":
    main()
