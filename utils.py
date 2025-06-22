"""
utils.py - Shared Utilities Module

Version: 3.0.1
Date: 2025-06-21
Author: Google Search FactSet Pipeline - Modular Architecture
License: MIT

Description:
    Shared utility functions used across the FactSet pipeline modules:
    - File operations and path management
    - Date and time formatting
    - Text processing and validation
    - Logging utilities
    - Error handling helpers
    - System information gathering

Key Features:
    - Cross-platform file operations
    - Robust date parsing and formatting
    - Text cleaning and validation
    - Centralized logging setup
    - Error context management
    - System diagnostics

Dependencies:
    - os, pathlib
    - datetime
    - re
    - logging
    - platform
"""

import os
import re
import logging
from pathlib import Path

def is_debug_mode() -> bool:
    """Check if running in debug mode via environment variable."""
    return os.getenv("DEBUG", "0") == "1"

def is_file_parsed(md_path: str) -> bool:
    """Check if a Markdown file has been parsed by looking for a corresponding .parsed file."""
    parsed_flag = Path(md_path).with_suffix(".parsed")
    return parsed_flag.exists()

def mark_parsed_file(md_path: str):
    """Mark a Markdown file as parsed by creating a .parsed flag file."""
    parsed_flag = Path(md_path).with_suffix(".parsed")
    parsed_flag.touch()

def read_md_file(md_path: str) -> str:
    """Read content from a Markdown file, return as string."""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Failed to read {md_path}: {e}")
        return ""

def parse_md_file(md_content: str) -> dict:
    """Parse EPS and Revenue data from MD content using regex patterns."""
    data = {}
    try:
        eps_section = re.search(r"市場預估EPS.*?\| 中位數 \|\s*(.*?)\|\s*(.*?)\|\s*(.*?) \|", md_content, re.DOTALL)
        if eps_section:
            data["2025EPS中位數"] = eps_section.group(1).strip()
            data["2026EPS中位數"] = eps_section.group(2).strip()
            data["2027EPS中位數"] = eps_section.group(3).strip()

        revenue_section = re.search(r"市場預估營收.*?\| 中位數 \|\s*(.*?)\|\s*(.*?)\|\s*(.*?) \|", md_content, re.DOTALL)
        if revenue_section:
            data["2025營收中位數"] = revenue_section.group(1).strip()
            data["2026營收中位數"] = revenue_section.group(2).strip()
            data["2027營收中位數"] = revenue_section.group(3).strip()
    except Exception as e:
        logging.warning(f"Parse error: {e}")

    return data