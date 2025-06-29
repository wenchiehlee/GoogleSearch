## 2. download_cli.py

```python
#!/usr/bin/env python3
"""
download_cli.py - DownloadWatchlist CLI (v3.5.0)

Version: 3.5.0
Date: 2025-06-29
Author: DownloadWatchlist Group v3.5.0

Simple CLI for downloading watchlist CSV and committing to git.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Version Information
__version__ = "3.5.0"
__date__ = "2025-06-29"
__author__ = "DownloadWatchlist Group v3.5.0"

class DownloadWatchlistCLI:
    """Simple CLI for watchlist download v3.5.0"""
    
    def __init__(self):
        self.version = "3.5.0"
        # Import downloader here to avoid circular imports
        try:
            from downloader import SimpleDownloader
            self.downloader = SimpleDownloader()
        except ImportError:
            print("❌ Error: downloader.py not found")
            sys.exit(1)
    
    def handle_download(self, args):
        """處理下載命令"""
        print(f"🎯 DownloadWatchlist v{self.version} - Starting download...")
        
        force = getattr(args, 'force', False)
        if force:
            print("🔄 Force download enabled")
        
        # Execute download
        success = self.downloader.download_csv(force=force)
        
        if success:
            print("✅ Download completed successfully")
            
            # Show file info
            csv_file = '觀察名單.csv'
            if os.path.exists(csv_file):
                size = os.path.getsize(csv_file)
                print(f"📄 File: {csv_file} ({size} bytes)")
        else:
            print("❌ Download failed")
        
        return success
    
    def handle_status(self, args):
        """檢查狀態"""
        print(f"📊 DownloadWatchlist v{self.version} Status")
        print("=" * 50)
        
        csv_file = '觀察名單.csv'
        
        if os.path.exists(csv_file):
            stat = os.stat(csv_file)
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            print(f"✅ File exists: {csv_file}")
            print(f"   Size: {stat.st_size} bytes")
            print(f"   Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check if file is recent (less than 24 hours old)
            age_hours = (datetime.now() - modified_time).total_seconds() / 3600
            if age_hours < 24:
                print(f"   Age: {age_hours:.1f} hours (recent)")
            else:
                print(f"   Age: {age_hours/24:.1f} days (consider updating)")
        else:
            print(f"❌ File not found: {csv_file}")
            print("   Run: python download_cli.py download")
        
        # Check downloader status
        print(f"\n🔗 Downloader Status:")
        print(f"   URL: {self.downloader.url}")
        print(f"   Version: v{self.version}")
        
        return True

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description=f'DownloadWatchlist v{__version__} - Simple CSV Download',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
DownloadWatchlist v{__version__} - Simple watchlist CSV download

Examples:
  python download_cli.py download          # Download watchlist
  python download_cli.py download --force  # Force re-download
  python download_cli.py status            # Check status

GitHub Actions Integration:
  python download_cli.py download          # Used in Actions workflow
        """
    )
    
    parser.add_argument('--version', action='version', version=f'DownloadWatchlist v{__version__}')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download watchlist CSV')
    download_parser.add_argument('--force', action='store_true', 
                                help='Force re-download even if file exists')
    
    # Status command  
    status_parser = subparsers.add_parser('status', help='Check download status')
    
    return parser

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI
    try:
        cli = DownloadWatchlistCLI()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return 1
    
    # Execute command
    try:
        if args.command == 'download':
            success = cli.handle_download(args)
        elif args.command == 'status':
            success = cli.handle_status(args)
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
            success = False
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())