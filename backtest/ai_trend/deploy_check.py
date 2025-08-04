#!/usr/bin/env python3
"""
Deployment Check Script
Verifies that all components are properly set up for server deployment
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def check_files():
    """Check if all required files exist"""
    print("📁 CHECKING REQUIRED FILES...")
    
    required_files = [
        'daily_supabase_update.py',
        'supabase_integration.py', 
        'requirements.txt',
        '.env',
        'run_daily_update.sh'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_environment():
    """Check environment variables"""
    print("\n🔐 CHECKING ENVIRONMENT VARIABLES...")
    
    # Load .env file
    load_dotenv()
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'FMP_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            masked_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ❌ {var} - MISSING")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_python_dependencies():
    """Check if Python dependencies are installed"""
    print("\n📦 CHECKING PYTHON DEPENDENCIES...")
    
    try:
        # Read requirements.txt
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip().split('==')[0].split('>=')[0] for line in f if line.strip() and not line.startswith('#')]
        
        missing_deps = []
        for dep in requirements:
            try:
                __import__(dep)
                print(f"   ✅ {dep}")
            except ImportError:
                print(f"   ❌ {dep} - NOT INSTALLED")
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"\n   💡 Install missing dependencies with:")
            print(f"   pip install {' '.join(missing_deps)}")
        
        return len(missing_deps) == 0
        
    except FileNotFoundError:
        print("   ❌ requirements.txt not found")
        return False

def check_script_permissions():
    """Check if shell script has execute permissions"""
    print("\n🔑 CHECKING SCRIPT PERMISSIONS...")
    
    shell_script = 'run_daily_update.sh'
    if os.path.exists(shell_script):
        permissions = oct(os.stat(shell_script).st_mode)[-3:]
        if permissions >= '755':
            print(f"   ✅ {shell_script} has execute permissions ({permissions})")
            return True
        else:
            print(f"   ❌ {shell_script} needs execute permissions")
            print(f"   💡 Run: chmod +x {shell_script}")
            return False
    else:
        print(f"   ❌ {shell_script} not found")
        return False

def test_database_connection():
    """Test connection to Supabase"""
    print("\n🔗 TESTING DATABASE CONNECTION...")
    
    try:
        from supabase_integration import SupabaseTradeDataManager
        
        db_manager = SupabaseTradeDataManager(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
            use_service_role=True
        )
        
        # Test a simple query
        result = db_manager.supabase.schema('ai_trend_analysis').table('performance_summary').select('*').limit(1).execute()
        print("   ✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def check_python_path():
    """Check Python path for cron"""
    print("\n🐍 CHECKING PYTHON PATH...")
    
    try:
        python_path = subprocess.check_output(['which', 'python3']).decode().strip()
        print(f"   ✅ Python3 path: {python_path}")
        
        # Check if it's in the shell script
        if os.path.exists('run_daily_update.sh'):
            with open('run_daily_update.sh', 'r') as f:
                script_content = f.read()
                if python_path in script_content or '/usr/bin/python3' in script_content:
                    print("   ✅ Python path configured in shell script")
                    return True
                else:
                    print("   ⚠️  Update PYTHON_PATH in run_daily_update.sh")
                    print(f"   💡 Set PYTHON_PATH=\"{python_path}\"")
                    return False
        
        return True
        
    except subprocess.CalledProcessError:
        print("   ❌ Python3 not found")
        return False

def generate_cron_command():
    """Generate the cron command"""
    print("\n⏰ CRON JOB SETUP...")
    
    current_dir = os.getcwd()
    shell_script_path = os.path.join(current_dir, 'run_daily_update.sh')
    
    print("   Add this line to your crontab (crontab -e):")
    print(f"   0 */4 * * * {shell_script_path}")
    print()
    print("   Alternative schedules:")
    print(f"   # Every 4 hours: 0 */4 * * * {shell_script_path}")
    print(f"   # Specific times: 0 8,12,16,20 * * * {shell_script_path}")
    print(f"   # Market hours only: 0 9,13,17 * * 1-5 {shell_script_path}")

def main():
    """Main deployment check"""
    print("🚀 AI TREND NAVIGATOR - DEPLOYMENT CHECK")
    print("=" * 50)
    
    checks = [
        check_files(),
        check_environment(),
        check_python_dependencies(),
        check_script_permissions(),
        check_python_path(),
        test_database_connection()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 DEPLOYMENT CHECK RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        generate_cron_command()
    else:
        print("❌ Some checks failed - Fix issues before deployment")
        print("\n💡 Common fixes:")
        print("   - Run: pip install -r requirements.txt")
        print("   - Run: chmod +x run_daily_update.sh") 
        print("   - Check .env file has correct credentials")
        print("   - Update paths in run_daily_update.sh")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 