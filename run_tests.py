import pytest
import sys
import os
from pathlib import Path


def main():
    """Run tests with appropriate configuration"""
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Add project to Python path
    sys.path.insert(0, str(project_root))
    
    # Default test arguments
    test_args = [
        "tests/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=70"
    ]
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            test_args.extend(["-m", "unit"])
            print("Running unit tests only...")
        elif sys.argv[1] == "integration":
            test_args.extend(["-m", "integration"])
            print("Running integration tests only...")
        elif sys.argv[1] == "fast":
            test_args.extend(["-m", "not slow"])
            print("Running fast tests only...")
        elif sys.argv[1] == "database":
            test_args.extend(["-m", "database"])
            print("Running database tests only...")
        elif sys.argv[1] == "ui":
            test_args.extend(["-m", "ui"])
            print("Running UI tests only...")
        elif sys.argv[1] == "coverage":
            test_args.extend(["--cov-report=html", "--cov-report=xml"])
            print("Running tests with detailed coverage reporting...")
        elif sys.argv[1] == "specific":
            if len(sys.argv) > 2:
                test_args = ["tests/" + sys.argv[2], "-v"]
                print(f"Running specific test file: {sys.argv[2]}")
            else:
                print("Please specify a test file after 'specific'")
                return 1
        else:
            print(f"Unknown test category: {sys.argv[1]}")
            print("Available options: unit, integration, fast, database, ui, coverage, specific <test_file>")
            return 1
    
    print(f"Test command: pytest {' '.join(test_args)}")
    
    # Run tests
    exit_code = pytest.main(test_args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        if "--cov" in test_args:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
