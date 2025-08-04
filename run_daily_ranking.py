#!/usr/bin/env python3
"""
Daily Asset Ranking Runner
Simplified script to run the complete global asset ranking system
Handles Go PATH setup automatically for Windows users
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_go_path():
    """Add Go to PATH if it's not already available (Windows)"""
    if sys.platform.startswith('win'):
        # Common Go installation paths on Windows
        go_paths = [
            r"C:\Program Files\Go\bin",
            r"C:\Go\bin",
            os.path.expanduser(r"~\go\bin"),
        ]
        
        current_path = os.environ.get('PATH', '')
        
        for go_path in go_paths:
            if Path(go_path).exists() and go_path not in current_path:
                os.environ['PATH'] = current_path + os.pathsep + go_path
                print(f"✅ Added Go to PATH: {go_path}")
                return True
        
        # Check if go is already available
        try:
            subprocess.run(['go', 'version'], capture_output=True, check=True)
            print("✅ Go is already available in PATH")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Go not found. Please install Go or add it to your PATH manually.")
            return False
    else:
        # Unix-like systems (Linux, macOS)
        try:
            subprocess.run(['go', 'version'], capture_output=True, check=True)
            print("✅ Go is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Go not found. Please install Go or add it to your PATH.")
            return False

def main():
    """Main runner function"""
    print("🌟 DAILY GLOBAL ASSET RANKING SYSTEM")
    print("=" * 50)
    
    # Setup Go PATH
    if not setup_go_path():
        print("\n💡 To install Go:")
        print("   Windows: Download from https://golang.org/dl/")
        print("   Linux: sudo apt install golang-go")
        print("   macOS: brew install go")
        return
    
    # Check if we're in the right directory
    if not Path('combine_all_assets.py').exists():
        print("❌ combine_all_assets.py not found!")
        print("💡 Make sure you're running this from the algotradar directory")
        return
    
    # Check for .env file
    if not Path('.env').exists():
        print("⚠️  .env file not found!")
        print("💡 Copy env_example.txt to .env and add your API keys")
        if Path('env_example.txt').exists():
            print("   Example file available: env_example.txt")
        return
    
    print("\n🚀 Starting global asset ranking...")
    print("This will:")
    print("  1. ✅ Fetch global stocks & commodities (Go + FMP API)")
    print("  2. ✅ Fetch cryptocurrencies (Python + CCXT)")
    print("  3. ✅ Combine & rank all assets")
    print("  4. ✅ Upload to Supabase database")
    print()
    
    try:
        # Run the complete analysis
        result = subprocess.run([
            sys.executable, 'combine_all_assets.py'
        ], check=True)
        
        print("\n🎉 Daily ranking completed successfully!")
        print("📊 Check your Supabase database for updated rankings")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Process failed with exit code {e.returncode}")
        print("💡 Check the error messages above for troubleshooting")
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 