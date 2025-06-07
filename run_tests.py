#!/usr/bin/env python3
"""
OMOP Quality Dashboard Test Runner

This script provides a comprehensive test runner for the OMOP Quality Dashboard
with support for different test categories, coverage reporting, and CI/CD integration.
"""

import pytest
import sys
import os
import argparse
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Version information
__version__ = "1.0.0"
__author__ = "Healthcare Data Quality Team"

# Test configuration
DEFAULT_COVERAGE_THRESHOLD = 80
TEST_TIMEOUT = 300  # 5 minutes default timeout


class TestRunner:
    """Enhanced test runner for OMOP Quality Dashboard"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.app_dir = self.project_root / "app"
        self.start_time: Optional[float] = None
        
    def setup_environment(self) -> None:
        """Setup test environment"""
        # Ensure we're in the project root
        os.chdir(self.project_root)
        
        # Add project to Python path
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
        
        # Set test environment variables
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['LOG_LEVEL'] = 'ERROR'  # Reduce log noise during tests
        os.environ['DASHBOARD_DEBUG'] = 'false'
        
        # Create necessary test directories
        test_dirs = ['logs', 'htmlcov', 'reports']
        for test_dir in test_dirs:
            (self.project_root / test_dir).mkdir(exist_ok=True)
    
    def validate_test_environment(self) -> bool:
        """Validate that test environment is properly set up"""
        # Check if test directory exists
        if not self.test_dir.exists():
            print(f"❌ Test directory not found: {self.test_dir}")
            return False
        
        # Check if app directory exists
        if not self.app_dir.exists():
            print(f"❌ App directory not found: {self.app_dir}")
            return False
        
        # Check for pytest
        try:
            import pytest
        except ImportError:
            print("❌ pytest not found. Install with: pip install pytest")
            return False
        
        # Check for required test dependencies
        required_test_deps = ['pytest-cov', 'pytest-mock']
        missing_deps = []
        
        for dep in required_test_deps:
            try:
                __import__(dep.replace('-', '_'))
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"⚠️  Missing optional test dependencies: {', '.join(missing_deps)}")
            print("   Install with: pip install pytest-cov pytest-mock")
        
        return True
    
    def get_test_categories(self) -> Dict[str, Dict[str, str]]:
        """Get available test categories and their configurations"""
        return {
            'unit': {
                'markers': 'unit',
                'description': 'Fast, isolated unit tests',
                'timeout': '30'
            },
            'integration': {
                'markers': 'integration',
                'description': 'Integration tests with component interactions',
                'timeout': '120'
            },
            'e2e': {
                'markers': 'e2e',
                'description': 'End-to-end workflow tests',
                'timeout': '300'
            },
            'database': {
                'markers': 'database',
                'description': 'Tests requiring database connections',
                'timeout': '60'
            },
            'ui': {
                'markers': 'ui',
                'description': 'User interface and Streamlit component tests',
                'timeout': '60'
            },
            'slow': {
                'markers': 'slow',
                'description': 'Long-running performance tests',
                'timeout': '600'
            },
            'fast': {
                'markers': 'not slow',
                'description': 'Quick tests (excludes slow tests)',
                'timeout': '60'
            },
            'smoke': {
                'markers': 'smoke',
                'description': 'Basic functionality verification tests',
                'timeout': '30'
            },
            'performance': {
                'markers': 'performance',
                'description': 'Performance benchmark tests',
                'timeout': '300'
            },
            'security': {
                'markers': 'security',
                'description': 'Security-related tests',
                'timeout': '60'
            },
            'quality': {
                'markers': 'completeness or temporal or concept_mapping or referential or statistical',
                'description': 'All quality check tests',
                'timeout': '120'
            }
        }
    
    def build_pytest_args(self, test_type: str, args: argparse.Namespace) -> List[str]:
        """Build pytest arguments based on test type and options"""
        pytest_args = []
        
        # Base test directory
        if args.test_file:
            pytest_args.append(f"tests/{args.test_file}")
        else:
            pytest_args.append("tests/")
        
        # Verbosity
        if args.verbose:
            pytest_args.extend(["-v", "-s"])
        elif args.quiet:
            pytest_args.append("-q")
        else:
            pytest_args.append("-v")
        
        # Test selection
        categories = self.get_test_categories()
        if test_type in categories:
            pytest_args.extend(["-m", categories[test_type]['markers']])
            
            # Set timeout based on test type
            if not args.no_timeout:
                timeout = args.timeout or categories[test_type]['timeout']
                pytest_args.extend(["--timeout", timeout])
        
        # Coverage options
        if args.coverage or test_type == 'coverage':
            pytest_args.extend([
                "--cov=app",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml",
                "--cov-report=term-missing"
            ])
            
            if args.coverage_fail_under:
                pytest_args.extend([f"--cov-fail-under={args.coverage_fail_under}"])
            else:
                pytest_args.extend([f"--cov-fail-under={DEFAULT_COVERAGE_THRESHOLD}"])
            
            # Branch coverage for better analysis
            if args.branch_coverage:
                pytest_args.append("--cov-branch")
        
        # Parallel execution
        if args.parallel and args.parallel > 1:
            pytest_args.extend(["-n", str(args.parallel)])
        
        # Fail fast
        if args.fail_fast:
            pytest_args.extend(["--maxfail", "1"])
        elif args.max_failures:
            pytest_args.extend(["--maxfail", str(args.max_failures)])
        
        # Output options
        if args.tb_style:
            pytest_args.extend(["--tb", args.tb_style])
        else:
            pytest_args.extend(["--tb", "short"])
        
        # JUnit XML output for CI
        if args.junit_xml:
            pytest_args.extend(["--junit-xml", args.junit_xml])
        
        # HTML report
        if args.html_report:
            pytest_args.extend(["--html", args.html_report, "--self-contained-html"])
        
        # Benchmark options
        if test_type == 'performance' or args.benchmark:
            pytest_args.append("--benchmark-enable")
            if args.benchmark_save:
                pytest_args.extend(["--benchmark-save", args.benchmark_save])
        
        # Additional pytest options
        if args.strict_markers:
            pytest_args.append("--strict-markers")
        
        if args.disable_warnings:
            pytest_args.append("--disable-warnings")
        
        # Custom pytest options
        if args.pytest_args:
            pytest_args.extend(args.pytest_args.split())
        
        return pytest_args
    
    def run_tests(self, pytest_args: List[str], test_type: str) -> int:
        """Run tests with enhanced reporting"""
        self.start_time = time.time()
        
        print(f"🧪 Running {test_type} tests...")
        print(f"📁 Test directory: {self.test_dir}")
        print(f"🐍 Python: {'.'.join(map(str, sys.version_info[:3]))}")
        print(f"⚙️  pytest command: pytest {' '.join(pytest_args)}")
        print("=" * 70)
        
        # Run pytest
        try:
            exit_code = pytest.main(pytest_args)
        except KeyboardInterrupt:
            print("\n🛑 Tests interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Error running tests: {e}")
            return 1
        
        # Calculate duration
        duration = time.time() - self.start_time if self.start_time else 0
        
        # Print results
        print("=" * 70)
        self.print_test_results(exit_code, test_type, duration, pytest_args)
        
        return exit_code
    
    def print_test_results(self, exit_code: int, test_type: str, duration: float, pytest_args: List[str]) -> None:
        """Print comprehensive test results"""
        minutes, seconds = divmod(duration, 60)
        
        if exit_code == 0:
            print(f"✅ All {test_type} tests passed!")
            print(f"⏱️  Duration: {int(minutes)}m {seconds:.1f}s")
        else:
            print(f"❌ {test_type.title()} tests failed (exit code: {exit_code})")
            print(f"⏱️  Duration: {int(minutes)}m {seconds:.1f}s")
        
        # Coverage report info
        if "--cov" in pytest_args:
            print("📊 Coverage reports generated:")
            print("   - HTML: htmlcov/index.html")
            if "--cov-report=xml" in ' '.join(pytest_args):
                print("   - XML: coverage.xml")
        
        # HTML report info
        if "--html" in pytest_args:
            html_index = pytest_args.index("--html")
            if html_index + 1 < len(pytest_args):
                html_file = pytest_args[html_index + 1]
                print(f"📄 HTML report: {html_file}")
        
        # JUnit XML info
        if "--junit-xml" in pytest_args:
            junit_index = pytest_args.index("--junit-xml")
            if junit_index + 1 < len(pytest_args):
                junit_file = pytest_args[junit_index + 1]
                print(f"📋 JUnit XML: {junit_file}")
    
    def list_tests(self, test_type: str = None) -> None:
        """List available tests"""
        print("📋 Available tests:")
        
        args = ["--collect-only", "-q", "tests/"]
        if test_type:
            categories = self.get_test_categories()
            if test_type in categories:
                args.extend(["-m", categories[test_type]['markers']])
        
        try:
            pytest.main(args)
        except Exception as e:
            print(f"Error listing tests: {e}")
    
    def show_coverage_report(self) -> None:
        """Show coverage report if available"""
        coverage_file = self.project_root / "htmlcov" / "index.html"
        if coverage_file.exists():
            print(f"📊 Opening coverage report: {coverage_file}")
            try:
                import webbrowser
                webbrowser.open(f"file://{coverage_file.absolute()}")
            except Exception:
                print(f"Please open manually: {coverage_file}")
        else:
            print("❌ No coverage report found. Run tests with --coverage first.")
    
    def clean_test_artifacts(self) -> None:
        """Clean test artifacts and reports"""
        artifacts = [
            "htmlcov",
            "coverage.xml",
            ".coverage",
            ".pytest_cache",
            "reports",
            "test-results.xml"
        ]
        
        cleaned = []
        for artifact in artifacts:
            artifact_path = self.project_root / artifact
            if artifact_path.exists():
                if artifact_path.is_dir():
                    import shutil
                    shutil.rmtree(artifact_path)
                else:
                    artifact_path.unlink()
                cleaned.append(artifact)
        
        if cleaned:
            print(f"🧹 Cleaned test artifacts: {', '.join(cleaned)}")
        else:
            print("✨ No test artifacts to clean")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser"""
    parser = argparse.ArgumentParser(
        description="OMOP Quality Dashboard Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                              # Run all tests
  python run_tests.py unit                         # Run unit tests only
  python run_tests.py integration --coverage       # Integration tests with coverage
  python run_tests.py --test-file test_database.py # Run specific test file
  python run_tests.py performance --benchmark      # Run performance tests
  python run_tests.py --parallel 4                 # Run tests in parallel
  python run_tests.py --list-tests                 # List all available tests
  python run_tests.py --clean                      # Clean test artifacts

Test Categories:
  unit           Fast, isolated unit tests
  integration    Integration tests with component interactions
  e2e            End-to-end workflow tests
  database       Tests requiring database connections
  ui             User interface and Streamlit component tests
  slow           Long-running performance tests
  fast           Quick tests (excludes slow tests)
  smoke          Basic functionality verification tests
  performance    Performance benchmark tests
  security       Security-related tests
  quality        All quality check tests (completeness, temporal, etc.)
        """
    )
    
    # Positional argument for test type
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    # Test selection options
    parser.add_argument(
        '--test-file',
        type=str,
        help='Run specific test file (relative to tests/ directory)'
    )
    
    parser.add_argument(
        '--list-tests',
        action='store_true',
        help='List available tests and exit'
    )
    
    # Coverage options
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--coverage-fail-under',
        type=int,
        help=f'Fail if coverage is below threshold (default: {DEFAULT_COVERAGE_THRESHOLD})'
    )
    
    parser.add_argument(
        '--branch-coverage',
        action='store_true',
        help='Include branch coverage analysis'
    )
    
    parser.add_argument(
        '--show-coverage',
        action='store_true',
        help='Open coverage report in browser'
    )
    
    # Execution options
    parser.add_argument(
        '--parallel',
        type=int,
        help='Run tests in parallel (requires pytest-xdist)'
    )
    
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '--max-failures',
        type=int,
        help='Maximum number of failures before stopping'
    )
    
    parser.add_argument(
        '--timeout',
        type=str,
        help='Test timeout in seconds'
    )
    
    parser.add_argument(
        '--no-timeout',
        action='store_true',
        help='Disable test timeouts'
    )
    
    # Output options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Quiet output'
    )
    
    parser.add_argument(
        '--tb-style',
        choices=['auto', 'long', 'short', 'line', 'native', 'no'],
        help='Traceback style for failures'
    )
    
    # Report generation
    parser.add_argument(
        '--html-report',
        type=str,
        help='Generate HTML test report'
    )
    
    parser.add_argument(
        '--junit-xml',
        type=str,
        help='Generate JUnit XML report for CI'
    )
    
    # Performance testing
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Enable benchmark tests (requires pytest-benchmark)'
    )
    
    parser.add_argument(
        '--benchmark-save',
        type=str,
        help='Save benchmark results with given name'
    )
    
    # pytest options
    parser.add_argument(
        '--strict-markers',
        action='store_true',
        help='Treat unknown markers as errors'
    )
    
    parser.add_argument(
        '--disable-warnings',
        action='store_true',
        help='Disable warning summary'
    )
    
    parser.add_argument(
        '--pytest-args',
        type=str,
        help='Additional arguments to pass to pytest'
    )
    
    # Utility options
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean test artifacts and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'OMOP Quality Dashboard Test Runner v{__version__}'
    )
    
    return parser


def main() -> int:
    """Main function"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    # Handle utility commands
    if args.clean:
        runner.clean_test_artifacts()
        return 0
    
    if args.show_coverage:
        runner.show_coverage_report()
        return 0
    
    if args.list_tests:
        runner.list_tests(args.test_type if args.test_type != 'all' else None)
        return 0
    
    # Setup test environment
    runner.setup_environment()
    
    # Validate test environment
    if not runner.validate_test_environment():
        return 1
    
    # Get test categories
    categories = runner.get_test_categories()
    
    # Validate test type
    test_type = args.test_type
    if test_type != 'all' and test_type not in categories:
        print(f"❌ Unknown test category: {test_type}")
        print("Available categories:")
        for cat, info in categories.items():
            print(f"  {cat:12} - {info['description']}")
        return 1
    
    # Build pytest arguments
    pytest_args = runner.build_pytest_args(test_type, args)
    
    # Run tests
    return runner.run_tests(pytest_args, test_type)


if __name__ == "__main__":
    sys.exit(main())
