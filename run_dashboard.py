#!/usr/bin/env python3
"""
OMOP Quality Dashboard Runner

This script provides a robust way to launch the OMOP Quality Dashboard with
comprehensive configuration validation, dependency checking, and error handling.
"""

import os
import sys
import subprocess
import argparse
import signal
import time
import socket
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import importlib.util

# Version information
__version__ = "1.0.0"
__author__ = "Healthcare Data Quality Team"

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


class DashboardRunner:
    """Main class for running the OMOP Quality Dashboard"""
    
    def __init__(self):
        self.logger: Optional[logging.Logger] = None
        self.process: Optional[subprocess.Popen] = None
        
    def setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging configuration"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_file = os.getenv('LOG_FILE', 'logs/omop_dashboard.log')
        log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific logger levels for third-party packages
        logging.getLogger('streamlit').setLevel(logging.WARNING)
        logging.getLogger('plotly').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
        
        return logger
    
    def check_python_version(self) -> bool:
        """Check if Python version meets requirements"""
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version < min_version:
            print(f"❌ Python {'.'.join(map(str, min_version))}+ required, got {'.'.join(map(str, current_version))}")
            return False
        
        print(f"✅ Python version: {'.'.join(map(str, current_version))}")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed with version info"""
        required_packages = {
            'streamlit': '1.28.0',
            'pandas': '2.0.0',
            'plotly': '5.15.0',
            'sqlalchemy': '2.0.0',
            'pyyaml': '6.0',
            'python-dotenv': '1.0.0'
        }
        
        missing_packages = []
        version_issues = []
        
        for package, min_version in required_packages.items():
            try:
                module = __import__(package.replace('-', '_'))
                
                # Try to get version information
                version = getattr(module, '__version__', 'unknown')
                if version != 'unknown':
                    print(f"  📦 {package}: {version}")
                else:
                    print(f"  📦 {package}: installed")
                    
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing required packages: {', '.join(missing_packages)}")
            print("   Please install them with: pip install -r requirements.txt")
            return False
        
        print("✅ All required packages are installed")
        return True
    
    def check_app_structure(self) -> bool:
        """Check if application structure is correct"""
        required_files = [
            APP_DIR / "main.py",
            APP_DIR / "__init__.py",
            APP_DIR / "database" / "__init__.py",
            APP_DIR / "quality_checks" / "__init__.py",
            APP_DIR / "visualizations" / "__init__.py",
            APP_DIR / "utils" / "__init__.py"
        ]
        
        optional_files = [
            SCRIPT_DIR / "config.yaml",
            SCRIPT_DIR / "requirements.txt"
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
        
        # Check optional files
        for file_path in optional_files:
            if file_path.exists():
                print(f"  📄 Found: {file_path.name}")
            else:
                print(f"  ⚠️  Optional file missing: {file_path.name}")
        
        print("✅ Application structure is valid")
        return True
    
    def validate_database_config(self) -> bool:
        """Validate database configuration with enhanced checks"""
        db_type = os.getenv('OMOP_DB_TYPE', 'postgresql').lower()
        db_host = os.getenv('OMOP_DB_HOST', 'localhost')
        db_port = os.getenv('OMOP_DB_PORT', '5432')
        db_name = os.getenv('OMOP_DB_NAME', 'omop_cdm')
        db_user = os.getenv('OMOP_DB_USER', '')
        
        # Validate database type
        supported_types = ['postgresql', 'postgres', 'sqlserver', 'mssql', 'sqlite', 'mysql']
        if db_type not in supported_types:
            print(f"❌ Unsupported database type: {db_type}")
            print(f"   Supported types: {', '.join(supported_types)}")
            return False
        
        # Validate required fields for non-SQLite databases
        if db_type != 'sqlite':
            if not db_name:
                print("❌ Database name (OMOP_DB_NAME) is required")
                return False
            
            if not db_user:
                print("⚠️  Database user (OMOP_DB_USER) not specified")
            
            # Validate port
            try:
                port_num = int(db_port)
                if port_num < 1 or port_num > 65535:
                    print(f"❌ Invalid port number: {db_port}")
                    return False
            except ValueError:
                print(f"❌ Invalid port number: {db_port}")
                return False
        
        print(f"📊 Database configuration:")
        print(f"   Type: {db_type}")
        if db_type != 'sqlite':
            print(f"   Host: {db_host}")
            print(f"   Port: {db_port}")
            print(f"   Database: {db_name}")
            print(f"   User: {db_user or 'Not specified'}")
        else:
            print(f"   Database file: {db_name}")
        
        return True
    
    def check_port_availability(self, host: str, port: int) -> bool:
        """Check if the specified port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    print(f"⚠️  Port {port} is already in use on {host}")
                    return False
        except socket.error:
            pass
        
        return True
    
    def test_database_connection(self) -> bool:
        """Test database connectivity (optional check)"""
        if os.getenv('SKIP_DB_TEST', 'false').lower() == 'true':
            print("⚠️  Database connection test skipped")
            return True
        
        try:
            # Import here to avoid circular imports
            sys.path.insert(0, str(APP_DIR))
            from database.connection import build_connection_string, OMOPDatabase
            
            db_type = os.getenv('OMOP_DB_TYPE', 'postgresql')
            db_host = os.getenv('OMOP_DB_HOST', 'localhost')
            db_port = int(os.getenv('OMOP_DB_PORT', '5432'))
            db_name = os.getenv('OMOP_DB_NAME', 'omop_cdm')
            db_user = os.getenv('OMOP_DB_USER', '')
            db_password = os.getenv('OMOP_DB_PASSWORD', '')
            
            if db_type.lower() == 'sqlite':
                connection_string = f"sqlite:///{db_name}"
            else:
                connection_string = build_connection_string(
                    db_type, db_host, db_port, db_name, db_user, db_password
                )
            
            # Quick connection test
            db = OMOPDatabase(connection_string)
            if db.test_connection():
                print("✅ Database connection test successful")
                return True
            else:
                print("⚠️  Database connection test failed (dashboard will still start)")
                return True  # Don't fail startup for this
                
        except Exception as e:
            print(f"⚠️  Database connection test failed: {e}")
            print("   Dashboard will still start (connection will be tested in UI)")
            return True  # Don't fail startup for this
    
    def build_streamlit_command(self, args: argparse.Namespace) -> List[str]:
        """Build the Streamlit command with comprehensive arguments"""
        
        # Base command
        cmd = [
            sys.executable,
            "-m", "streamlit",
            "run",
            str(MAIN_FILE)
        ]
        
        # Server configuration
        host = args.host or os.getenv('DASHBOARD_HOST', 'localhost')
        port = str(args.port or int(os.getenv('DASHBOARD_PORT', '8501')))
        
        cmd.extend([
            "--server.address", host,
            "--server.port", port
        ])
        
        # Theme configuration from environment or defaults
        theme_base = os.getenv('DASHBOARD_THEME', 'light')
        primary_color = os.getenv('DASHBOARD_PRIMARY_COLOR', '#1f77b4')
        bg_color = os.getenv('DASHBOARD_BG_COLOR', '#ffffff')
        secondary_bg = os.getenv('DASHBOARD_SECONDARY_BG', '#f0f2f6')
        text_color = os.getenv('DASHBOARD_TEXT_COLOR', '#262730')
        
        cmd.extend([
            "--theme.base", theme_base,
            "--theme.primaryColor", primary_color,
            "--theme.backgroundColor", bg_color,
            "--theme.secondaryBackgroundColor", secondary_bg,
            "--theme.textColor", text_color
        ])
        
        # Development settings
        if os.getenv('DEV_MODE', 'false').lower() == 'true' or args.debug:
            cmd.extend([
                "--server.runOnSave", "true",
                "--server.allowRunOnSave", "true"
            ])
        
        # Browser settings
        if args.no_browser or os.getenv('DASHBOARD_HEADLESS', 'false').lower() == 'true':
            cmd.extend(["--server.headless", "true"])
        
        # Debug mode
        if args.debug or os.getenv('DASHBOARD_DEBUG', 'false').lower() == 'true':
            cmd.extend(["--logger.level", "debug"])
        
        # CORS settings
        if os.getenv('DASHBOARD_ENABLE_CORS', 'false').lower() == 'true':
            cmd.extend(["--server.enableCORS", "true"])
        
        # Additional Streamlit configuration
        if os.getenv('DASHBOARD_ENABLE_XSRF', 'true').lower() == 'false':
            cmd.extend(["--server.enableXsrfProtection", "false"])
        
        return cmd
    
    def print_startup_info(self, args: argparse.Namespace) -> None:
        """Print comprehensive startup information"""
        host = args.host or os.getenv('DASHBOARD_HOST', 'localhost')
        port = args.port or int(os.getenv('DASHBOARD_PORT', '8501'))
        title = os.getenv('DASHBOARD_TITLE', 'OMOP Quality Dashboard')
        environment = os.getenv('ENVIRONMENT', 'development')
        version = os.getenv('VERSION', __version__)
        
        print("=" * 70)
        print(f"🏥 {title} v{version}")
        print("=" * 70)
        print(f"📡 Server: http://{host}:{port}")
        print(f"🗃️  Database: {os.getenv('OMOP_DB_TYPE', 'postgresql')} - {os.getenv('OMOP_DB_NAME', 'omop_cdm')}")
        print(f"🔧 Environment: {environment}")
        print(f"📝 Logs: {os.getenv('LOG_FILE', 'logs/omop_dashboard.log')}")
        print(f"🐍 Python: {'.'.join(map(str, sys.version_info[:3]))}")
        
        if args.debug:
            print(f"🐛 Debug mode: ENABLED")
        
        if os.getenv('DEV_MODE', 'false').lower() == 'true':
            print(f"⚡ Development mode: ENABLED")
        
        print("=" * 70)
        print("🚀 Starting dashboard...")
        print("   Press Ctrl+C to stop")
        print("=" * 70)
    
    def create_directories(self) -> None:
        """Create necessary directories with proper permissions"""
        directories = [
            Path("logs"),
            Path("exports"), 
            Path("data"),
            Path("backups"),
            Path("cache")
        ]
        
        for directory in directories:
            try:
                directory.mkdir(exist_ok=True, mode=0o755)
                # Verify directory is writable
                test_file = directory / ".test_write"
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                print(f"⚠️  Cannot create/write to directory: {directory}")
            except Exception as e:
                print(f"⚠️  Issue with directory {directory}: {e}")
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
            if self.logger:
                self.logger.info(f"Received signal {signum}, shutting down")
            
            if self.process:
                try:
                    self.process.terminate()
                    # Wait a bit for graceful shutdown
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print("⚠️  Force killing dashboard process...")
                    self.process.kill()
                except Exception as e:
                    print(f"⚠️  Error during shutdown: {e}")
            
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run_dashboard(self, args: argparse.Namespace) -> int:
        """Run the dashboard with enhanced error handling"""
        try:
            cmd = self.build_streamlit_command(args)
            
            if self.logger:
                self.logger.info(f"Executing command: {' '.join(cmd)}")
            
            # Change to script directory
            original_cwd = os.getcwd()
            os.chdir(SCRIPT_DIR)
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                cwd=SCRIPT_DIR,
                stdout=subprocess.PIPE if not args.debug else None,
                stderr=subprocess.PIPE if not args.debug else None,
                text=True
            )
            
            # Wait for process to complete
            returncode = self.process.wait()
            
            # Restore original directory
            os.chdir(original_cwd)
            
            return returncode
            
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped by user")
            if self.logger:
                self.logger.info("Dashboard stopped by user (Ctrl+C)")
            return 0
            
        except FileNotFoundError:
            print("❌ Streamlit not found. Please install with: pip install streamlit")
            if self.logger:
                self.logger.error("Streamlit not found")
            return 1
            
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
            if self.logger:
                self.logger.error(f"Error starting dashboard: {e}", exc_info=True)
            return 1
    
    def perform_health_checks(self) -> bool:
        """Perform comprehensive health checks"""
        checks = [
            ("Python version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("Application structure", self.check_app_structure),
            ("Database configuration", self.validate_database_config),
        ]
        
        print("🔍 Performing system health checks...")
        
        for check_name, check_func in checks:
            print(f"\n📋 {check_name}:")
            if not check_func():
                print(f"❌ {check_name} check failed")
                return False
        
        # Optional checks that don't fail startup
        print(f"\n📋 Database connectivity:")
        self.test_database_connection()
        
        print(f"\n📋 Port availability:")
        host = os.getenv('DASHBOARD_HOST', 'localhost')
        port = int(os.getenv('DASHBOARD_PORT', '8501'))
        if not self.check_port_availability(host, port):
            print(f"⚠️  Port {port} may be in use, but continuing anyway...")
        else:
            print(f"✅ Port {port} is available")
        
        print("\n✅ All critical health checks passed!")
        return True


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Run OMOP Quality Dashboard with comprehensive configuration options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_dashboard.py                           # Run with default settings
  python run_dashboard.py --debug                   # Run in debug mode
  python run_dashboard.py --no-browser              # Run without opening browser
  python run_dashboard.py --port 8502               # Run on custom port
  python run_dashboard.py --host 0.0.0.0            # Allow external connections
  python run_dashboard.py --check-only              # Only validate configuration
  python run_dashboard.py --health-check            # Perform comprehensive health check

Environment Variables:
  DASHBOARD_HOST          Host to bind to (default: localhost)
  DASHBOARD_PORT          Port to bind to (default: 8501)
  DASHBOARD_DEBUG         Enable debug mode (default: false)
  OMOP_DB_TYPE           Database type (postgresql, sqlserver, sqlite)
  OMOP_DB_HOST           Database host
  OMOP_DB_NAME           Database name
  LOG_LEVEL              Logging level (DEBUG, INFO, WARNING, ERROR)
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
        '--health-check',
        action='store_true',
        help='Perform comprehensive health check and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'OMOP Quality Dashboard v{__version__}'
    )
    
    parser.add_argument(
        '--config-file',
        type=str,
        help='Path to configuration file (default: config.yaml)'
    )
    
    return parser


def main() -> int:
    """Main function to run the dashboard"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create dashboard runner instance
    runner = DashboardRunner()
    
    # Override environment variables with command line arguments
    if args.host:
        os.environ['DASHBOARD_HOST'] = args.host
    
    if args.port:
        os.environ['DASHBOARD_PORT'] = str(args.port)
    
    if args.debug:
        os.environ['DASHBOARD_DEBUG'] = 'true'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Setup logging
    runner.logger = runner.setup_logging()
    runner.logger.info(f"OMOP Quality Dashboard v{__version__} starting...")
    
    # Setup signal handlers for graceful shutdown
    runner.setup_signal_handlers()
    
    # Create necessary directories
    runner.create_directories()
    
    # Perform health checks
    if not runner.perform_health_checks():
        print("\n❌ Health checks failed. Please fix the issues above.")
        return 1
    
    # If only checking, exit here
    if args.check_only or args.health_check:
        print("\n✅ All checks passed! Dashboard is ready to run.")
        return 0
    
    # Print startup information
    runner.print_startup_info(args)
    
    # Run the dashboard
    return runner.run_dashboard(args)


if __name__ == "__main__":
    sys.exit(main())
