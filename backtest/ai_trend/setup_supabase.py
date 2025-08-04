#!/usr/bin/env python3
"""
Setup script for Supabase integration
Helps configure environment variables and test the connection
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with template"""
    env_content = """# Supabase Configuration
# Get these values from your Supabase project dashboard
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Optional: Service Role Key for admin operations
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# FMP API Configuration
# Get this from your Financial Modeling Prep dashboard
FMP_API_KEY=your_fmp_api_key_here
"""
    
    env_file = Path('.env')
    if env_file.exists():
        print("❌ .env file already exists!")
        response = input("Do you want to overwrite it? (y/n): ")
        if response.lower() != 'y':
            return False
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file template")
    print("📝 Please edit .env and add your Supabase credentials")
    return True

def test_connection():
    """Test Supabase connection"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from supabase_integration import SupabaseTradeDataManager
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        fmp_api_key = os.getenv('FMP_API_KEY')
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in .env file")
            return False
        
        if not fmp_api_key:
            print("❌ FMP API key not found in .env file")
            return False
        
        if not service_role_key:
            print("⚠️  SUPABASE_SERVICE_ROLE_KEY not found in .env file")
            print("💡 For backend operations, service role key is recommended")
            print("🔄 Trying with anon key...")
        
        if 'your_supabase_url_here' in supabase_url or 'your_supabase_anon_key_here' in supabase_key:
            print("❌ Please update your .env file with actual Supabase credentials")
            return False
        
        if 'your_fmp_api_key_here' in fmp_api_key:
            print("❌ Please update your .env file with actual FMP API key")
            return False
        
        # Test connection
        db_manager = SupabaseTradeDataManager(supabase_url, supabase_key, use_service_role=True)
        
        # Try to query one of the tables
        result = db_manager.get_latest_performance_summary()
        
        print("✅ Supabase connection successful!")
        print(f"📊 Found {len(result)} existing performance records")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def install_dependencies():
    """Install required packages"""
    try:
        import subprocess
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 AI Trend Navigator - Supabase Setup")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found!")
        return
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Install dependencies")
    print("2. Create .env file template")
    print("3. Test Supabase connection")
    print("4. Run complete setup")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == '1':
        install_dependencies()
    elif choice == '2':
        create_env_file()
    elif choice == '3':
        test_connection()
    elif choice == '4':
        print("\n📦 Step 1: Installing dependencies...")
        if install_dependencies():
            print("\n📄 Step 2: Creating .env file...")
            if create_env_file():
                print("\n⚠️  Please edit .env file with your Supabase credentials")
                print("💡 After editing, run this script again and choose option 3 to test connection")
            else:
                print("\n⚠️  .env file already exists. Please ensure it has correct credentials")
                print("💡 Choose option 3 to test connection")
    elif choice == '5':
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice!")
        return
    
    print("\n" + "=" * 50)
    print("Setup completed!")
    
    # Additional instructions
    print("\n📋 Next Steps:")
    print("1. Create tables in Supabase using create_supabase_tables.sql")
    print("2. Update .env file with your credentials")
    print("3. Run: python daily_supabase_update.py")
    print("4. Set up a daily cron job to run the update script")

if __name__ == "__main__":
    main() 