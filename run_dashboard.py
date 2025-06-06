import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the OMOP Quality Dashboard"""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    app_dir = script_dir / "app"
    main_file = app_dir / "main.py"
    
    # Check if main.py exists
    if not main_file.exists():
        print(f"Error: {main_file} not found!")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Set environment variables if .env file exists
    env_file = script_dir / ".env"
    if env_file.exists():
        print("Loading environment variables from .env file...")
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Build the streamlit command
    cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        str(main_file),
        "--server.port", os.getenv("DASHBOARD_PORT", "8501"),
        "--server.address", os.getenv("DASHBOARD_HOST", "localhost"),
        "--theme.base", "light",
        "--theme.primaryColor", "#1f77b4",
        "--theme.backgroundColor", "#ffffff",
        "--theme.secondaryBackgroundColor", "#f0f2f6"
    ]
    
    print("Starting OMOP Quality Dashboard...")
    print(f"Command: {' '.join(cmd)}")
    print("Dashboard will be available at: http://localhost:8501")
    print("Press Ctrl+C to stop the dashboard")
    
    try:
        subprocess.run(cmd, cwd=script_dir)
    except KeyboardInterrupt:
        print("\nDashboard stopped by user.")
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
