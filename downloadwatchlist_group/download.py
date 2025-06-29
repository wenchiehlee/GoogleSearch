#!/usr/bin/env python3
"""
downloader.py - Simple Watchlist Downloader (v3.5.0)

Version: 3.5.0
Date: 2025-06-29
Author: DownloadWatchlist Group v3.5.0

Simple downloader for watchlist CSV from GitHub.
"""

import requests
import os
import sys
from pathlib import Path

# Version Information
__version__ = "3.5.0"
__date__ = "2025-06-29"
__author__ = "DownloadWatchlist Group v3.5.0"

class SimpleDownloader:
    """Simple CSV downloader for watchlist v3.5.0"""
    
    def __init__(self):
        # Default GitHub Raw URL for watchlist
        self.url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"
        self.output_file = "觀察名單.csv"
        self.timeout = 30
        
        # Setup HTTP headers
        self.headers = {
            'User-Agent': f'DownloadWatchlist-v{__version__}/1.0',
            'Accept': 'text/csv,text/plain,*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache'
        }
    
    def download_csv(self, force=False, url=None):
        """
        Download CSV file from URL
        
        Args:
            force (bool): Force download even if file exists
            url (str): Custom URL to download from
            
        Returns:
            bool: True if successful, False otherwise
        """
        download_url = url or self.url
        
        print(f"🎯 Downloading watchlist from:")
        print(f"   {download_url}")
        
        # Check if file exists and force flag
        if not force and os.path.exists(self.output_file):
            print(f"ℹ️ File already exists: {self.output_file}")
            print("   Use --force to re-download")
            return True
        
        try:
            # Make HTTP request
            print("📡 Making HTTP request...")
            response = requests.get(
                download_url, 
                headers=self.headers,
                timeout=self.timeout
            )
            
            # Check response status
            response.raise_for_status()
            
            # Check content
            if not response.text.strip():
                print("❌ Downloaded content is empty")
                return False
            
            # Basic CSV validation
            if not self._validate_csv_content(response.text):
                print("⚠️ Content may not be valid CSV format")
                # Continue anyway for flexibility
            
            # Save to file
            print(f"💾 Saving to: {self.output_file}")
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Verify saved file
            if os.path.exists(self.output_file):
                file_size = os.path.getsize(self.output_file)
                print(f"✅ Download completed: {file_size} bytes")
                
                # Show first few lines for verification
                self._show_file_preview()
                
                return True
            else:
                print("❌ File was not saved properly")
                return False
                
        except requests.exceptions.Timeout:
            print(f"❌ Download timeout after {self.timeout} seconds")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - check network connectivity")
            return False
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP error: {e}")
            if hasattr(e.response, 'status_code'):
                print(f"   Status code: {e.response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def _validate_csv_content(self, content):
        """
        Basic CSV content validation
        
        Args:
            content (str): CSV content to validate
            
        Returns:
            bool: True if content looks like valid CSV
        """
        lines = content.strip().split('\n')
        
        # Check minimum lines
        if len(lines) < 2:
            return False
        
        # Check header
        header = lines[0]
        if '代號' not in header or '名稱' not in header:
            return False
        
        # Check data lines
        data_lines = [line for line in lines[1:] if line.strip()]
        if len(data_lines) < 1:
            return False
        
        # Basic format check on first data line
        if data_lines:
            first_line = data_lines[0]
            parts = first_line.split(',')
            if len(parts) < 2:
                return False
        
        return True
    
    def _show_file_preview(self):
        """Show preview of downloaded file"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print("📋 File preview:")
            for i, line in enumerate(lines[:5]):  # Show first 5 lines
                print(f"   {i+1}: {line.strip()}")
            
            if len(lines) > 5:
                print(f"   ... and {len(lines)-5} more lines")
            
            print(f"📊 Total lines: {len(lines)}")
            
        except Exception as e:
            print(f"⚠️ Could not preview file: {e}")
    
    def get_file_info(self):
        """Get information about the downloaded file"""
        if not os.path.exists(self.output_file):
            return None
        
        stat = os.stat(self.output_file)
        return {
            'file': self.output_file,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'exists': True
        }

# For standalone testing
if __name__ == "__main__":
    print(f"SimpleDownloader v{__version__} - Standalone Test")
    
    downloader = SimpleDownloader()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("🧪 Running test download...")
        success = downloader.download_csv(force=True)
        
        if success:
            info = downloader.get_file_info()
            print(f"📊 File info: {info}")
        
        print(f"Test result: {'✅ PASS' if success else '❌ FAIL'}")
    else:
        print("Usage: python downloader.py --test")
        print("       python download_cli.py download")