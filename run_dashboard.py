import os
import sys
import subprocess
import argparse
from pathlib import Path
import logging
from dotenv import load_dotenv

# Get the directory containing this script
SCRIPT_DIR = Path(__file__).parent.absolute()
APP_DIR = SCRIPT_DIR / "app"
MAIN_FILE = APP_DIR / "main.py"

# Load environment variables
ENV_FILE = SCRIPT_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
    print(f"✅ Loaded environment variables from {ENV_FILE}")
else:
    print(f"⚠️  No .env file found at {ENV_FILE}")
    print("   Dashboard will use default configuration")

def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'logs/omop_dashboard.log')
    
    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'sqlalchemy',
        'pyyaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("   Please install them with: pip install -r requirements.txt")
        return False
    
    return True

def check_app_structure():
    """Check if application structure is correct"""
    required_files = [
        APP_DIR / "main.py",
        APP_DIR / "__init__.py",
        APP_DIR / "database" / "__init__.py",
        APP_DIR / "quality_checks" / "__init__.py",
        APP_DIR / "visualizations" / "__init__.py",
        APP_DIR / "utils" / "__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if missing_files:
        print(f"❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    return True

def validate_database_config():
    """Validate database configuration"""
    db_type = os.getenv('OMOP_DB_TYPE', 'postgresql')
    db_host = os.getenv('OMOP_DB_HOST', 'localhost')
    db_name = os.getenv('OMOP_DB_NAME', 'omop_cdm')
    
    if not db_name:
        print("❌ Database name (OMOP_DB_NAME) is required")
        return False
    
    if db_type.lower() not in ['postgresql', 'sqlserver', 'sqlite']:
        print(f"❌ Unsupported database type: {db_type}")
        print("   Supported types: postgresql, sqlserver, sqlite")
        return False
    
    print(f"📊 Database configuration:")
    print(f"   Type: {db_type}")
    print(f"   Host: {db_host}")
    print(f"   Database: {db_name}")
    
    return True

def build_streamlit_command(args):
    """Build the Streamlit command with appropriate arguments"""
    
    # Base command
    cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        str(MAIN_FILE)
    ]
    
    # Server configuration
    host = os.getenv('DASHBOARD_HOST', 'localhost')
    port = os.getenv('DASHBOARD_PORT', '8501')
    
    cmd.extend([
        "--server.address", host,
        "--server.port", port
    ])
    
    # Theme configuration
    cmd.extend([
        "--theme.base", "light",
        "--theme.primaryColor", "#1f77b4",
        "--theme.backgroundColor", "#ffffff",
        "--theme.secondaryBackgroundColor", "#f0f2f6",
        "--theme.textColor", "#262730"
    ])
    
    # Development settings
    if os.getenv('DEV_MODE', 'false').lower() == 'true':
        cmd.extend([
            "--server.runOnSave", "true",
            "--server.allowRunOnSave", "true"
        ])
    
    # Browser settings
    if args.no_browser:
        cmd.extend(["--server.headless", "true"])
    
    # Debug mode
    if args.debug or os.getenv('DASHBOARD_DEBUG', 'false').lower() == 'true':
        cmd.extend(["--logger.level", "debug"])
    
    return cmd

def print_startup_info():
    """Print startup information"""
    host = os.getenv('DASHBOARD_HOST', 'localhost')
    port = os.getenv('DASHBOARD_PORT', '8501')
    title = os.getenv('DASHBOARD_TITLE', 'OMOP Quality Dashboard')
    
    print("=" * 60)
    print(f"🏥 {title}")
    print("=" * 60)
    print(f"📡 Server: http://{host}:{port}")
    print(f"🗃️  Database: {os.getenv('OMOP_DB_TYPE', 'postgresql')} - {os.getenv('OMOP_DB_NAME', 'omop_cdm')}")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"📝 Logs: {os.getenv('LOG_FILE', 'logs/omop_dashboard.log')}")
    print("=" * 60)
    print("🚀 Starting dashboard...")
    print("   Press Ctrl+C to stop")
    print("=" * 60)

def create_directories():
    """Create necessary directories"""
    directories = [
        Path("logs"),
        Path("exports"),
        Path("data"),
        Path("backups")
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)

def main():
    """Main function to run the dashboard"""
    parser = argparse.ArgumentParser(
        description="Run OMOP Quality Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_dashboard.py                    # Run with default settings
  python run_dashboard.py --debug            # Run in debug mode
  python run_dashboard.py --no-browser       # Run without opening browser
  python run_dashboard.py --port 8502        # Run on custom port
  python run_dashboard.py --host 0.0.0.0     # Allow external connections
        """
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode with verbose logging'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not automatically open browser'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        help='Host address to bind to (overrides DASHBOARD_HOST)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        help='Port to bind to (overrides DASHBOARD_PORT)'
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check configuration and dependencies, do not start dashboard'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='OMOP Quality Dashboard v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Override environment variables with command line arguments
    if args.host:
        os.environ['DASHBOARD_HOST'] = args.host
    
    if args.port:
        os.environ['DASHBOARD_PORT'] = str(args.port)
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting OMOP Quality Dashboard...")
    
    # Create necessary directories
    create_directories()
    
    # Perform checks
    print("🔍 Checking system requirements...")
    
    if not check_dependencies():
        sys.exit(1)
    print("✅ Dependencies check passed")
    
    if not check_app_structure():
        sys.exit(1)
    print("✅ Application structure check passed")
    
    if not validate_database_config():
        sys.exit(1)
    print("✅ Database configuration check passed")
    
    if args.check_only:
        print("✅ All checks passed! Dashboard is ready to run.")
        return 0
    
    # Print startup information
    print_startup_info()
    
    # Build and execute Streamlit command
    try:
        cmd = build_streamlit_command(args)
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Change to script directory
        os.chdir(SCRIPT_DIR)
        
        # Run Streamlit
        process = subprocess.run(cmd, cwd=SCRIPT_DIR)
        return process.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        logger.info("Dashboard stopped by user (Ctrl+C)")
        return 0
        
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install with: pip install streamlit")
        logger.error("Streamlit not found")
        return 1
        
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        logger.error(f"Error starting dashboard: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
