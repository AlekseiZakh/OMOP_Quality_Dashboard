from setuptools import setup, find_packages
import os
import sys
from pathlib import Path

# Read the README file for long description
def read_readme():
    """Read README.md file for long description"""
    readme_path = Path(__file__).parent / "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "OMOP Quality Dashboard - Comprehensive data quality monitoring for OMOP CDM implementations"

# Read requirements from requirements.txt
def read_requirements(filename="requirements.txt"):
    """Read requirements from requirements file"""
    requirements_path = Path(__file__).parent / filename
    try:
        with open(requirements_path, "r", encoding="utf-8") as fh:
            requirements = []
            for line in fh:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    # Remove inline comments
                    if "#" in line:
                        line = line[:line.index("#")].strip()
                    requirements.append(line)
            return requirements
    except FileNotFoundError:
        # Fallback requirements if file not found
        return [
            "streamlit>=1.28.0",
            "pandas>=2.0.0",
            "plotly>=5.15.0",
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
            "python-dotenv>=1.0.0",
            "pyyaml>=6.0",
            "numpy>=1.24.0",
            "openpyxl>=3.1.0",
        ]

# Get version from app/__init__.py or environment
def get_version():
    """Get version from app module or environment variable"""
    # Try to get from environment first
    version = os.getenv("PACKAGE_VERSION")
    if version:
        return version
    
    # Try to read from app/__init__.py
    try:
        app_init_path = Path(__file__).parent / "app" / "__init__.py"
        with open(app_init_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("__version__"):
                    # Extract version from __version__ = "x.y.z"
                    return line.split("=")[1].strip().strip('"').strip("'")
    except (FileNotFoundError, IndexError):
        pass
    
    # Default version
    return "1.0.0"

# Check Python version
if sys.version_info < (3, 8):
    print("Error: OMOP Quality Dashboard requires Python 3.8 or higher")
    sys.exit(1)

# Package metadata
NAME = "omop-quality-dashboard"
VERSION = get_version()
DESCRIPTION = "Comprehensive data quality monitoring dashboard for OMOP Common Data Model implementations"
AUTHOR = "Healthcare Data Quality Team"
AUTHOR_EMAIL = "your-email@yourorg.com"
URL = "https://github.com/your-org/omop-quality-dashboard"

# Long description
LONG_DESCRIPTION = read_readme()

# Requirements
INSTALL_REQUIRES = read_requirements()

# Optional dependencies
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.11.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.5.0",
        "pre-commit>=3.0.0",
        "jupyter>=1.0.0",
    ],
    "mysql": [
        "mysql-connector-python>=8.1.0",
        "PyMySQL>=1.1.0",
    ],
    "oracle": [
        "cx-Oracle>=8.3.0",
        "oracledb>=1.4.0",
    ],
    "sqlserver": [
        "pymssql>=2.2.0",
        "pyodbc>=4.0.39",
    ],
    "snowflake": [
        "snowflake-sqlalchemy>=1.4.0",
        "snowflake-connector-python>=3.2.0",
    ],
    "bigquery": [
        "google-cloud-bigquery>=3.11.0",
        "sqlalchemy-bigquery>=1.6.0",
    ],
    "analytics": [
        "scikit-learn>=1.3.0",
        "scipy>=1.11.0",
        "statsmodels>=0.14.0",
        "seaborn>=0.12.0",
    ],
    "monitoring": [
        "prometheus-client>=0.17.0",
        "sentry-sdk>=1.32.0",
        "structlog>=23.1.0",
    ],
    "caching": [
        "redis>=4.6.0",
        "hiredis>=2.2.0",
    ],
    "notifications": [
        "email-validator>=2.0.0",
        "sendgrid>=6.10.0",
        "slack-sdk>=3.21.0",
    ],
    "performance": [
        "fastparquet>=2023.7.0",
        "pyarrow>=12.0.0",
        "dask>=2023.7.0",
    ],
    "security": [
        "cryptography>=41.0.0",
        "keyring>=24.2.0",
        "python-jose>=3.3.0",
    ],
}

# Add 'all' extra that includes everything
EXTRAS_REQUIRE["all"] = []
for extra_deps in EXTRAS_REQUIRE.values():
    EXTRAS_REQUIRE["all"].extend(extra_deps)

# Remove duplicates from 'all'
EXTRAS_REQUIRE["all"] = list(set(EXTRAS_REQUIRE["all"]))

# Package data
PACKAGE_DATA = {
    "app": [
        "config/*.yaml",
        "config/*.yml", 
        "config/*.json",
        "sql/*.sql",
        "templates/*.html",
        "templates/*.jinja2",
        "static/*.css",
        "static/*.js",
        "static/images/*",
        "static/fonts/*",
    ],
}

# Data files
DATA_FILES = [
    ("config", ["config.yaml"]),
    (".", ["README.md", "LICENSE"]),
]

# Entry points
ENTRY_POINTS = {
    "console_scripts": [
        "omop-dashboard=run_dashboard:main",
        "omop-test=run_tests:main",
        "omop-quality-check=app.cli:main",  # Future CLI interface
    ],
}

# Classifiers
CLASSIFIERS = [
    # Development Status
    "Development Status :: 4 - Beta",
    
    # Intended Audience
    "Intended Audience :: Healthcare Industry",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Information Technology",
    "Intended Audience :: System Administrators",
    "Intended Audience :: Developers",
    
    # Topic
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
    "Topic :: Database :: Database Engines/Servers",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: System :: Monitoring",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    
    # License
    "License :: OSI Approved :: MIT License",
    
    # Programming Language
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3 :: Only",
    
    # Operating System
    "Operating System :: OS Independent",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS",
    
    # Environment
    "Environment :: Web Environment",
    "Environment :: Console",
    
    # Natural Language
    "Natural Language :: English",
    
    # Framework
    "Framework :: Streamlit",
    
    # Status
    "Typing :: Typed",
]

# Keywords
KEYWORDS = [
    "omop", "cdm", "common-data-model", "healthcare", "data-quality", 
    "dashboard", "monitoring", "analytics", "streamlit", "ohdsi",
    "medical-informatics", "healthcare-data", "clinical-research",
    "data-validation", "quality-assurance", "etl-validation", "sql",
    "postgresql", "sql-server", "data-profiling", "observational-health"
]

# Setup configuration
setup(
    # Basic metadata
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=URL,
    download_url=f"{URL}/archive/v{VERSION}.tar.gz",
    
    # Project URLs
    project_urls={
        "Homepage": URL,
        "Documentation": f"https://your-org.github.io/omop-quality-dashboard/",
        "Repository": URL,
        "Bug Reports": f"{URL}/issues",
        "Feature Requests": f"{URL}/issues",
        "Discussions": f"{URL}/discussions",
        "Changelog": f"{URL}/blob/main/CHANGELOG.md",
        "Healthcare Data Community": "https://www.ohdsi.org/",
        "OMOP CDM": "https://ohdsi.github.io/CommonDataModel/",
    },
    
    # Package discovery and inclusion
    packages=find_packages(
        include=["app", "app.*"],
        exclude=["tests", "tests.*", "docs", "docs.*"]
    ),
    include_package_data=True,
    package_data=PACKAGE_DATA,
    data_files=DATA_FILES,
    
    # Python and dependency requirements
    python_requires=">=3.8",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    
    # Entry points
    entry_points=ENTRY_POINTS,
    
    # Metadata for PyPI
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    license="MIT",
    platforms=["any"],
    
    # Build configuration
    zip_safe=False,
    setup_requires=[
        "setuptools>=45",
        "wheel>=0.37.0",
    ],
    
    # Test configuration
    test_suite="tests",
    tests_require=EXTRAS_REQUIRE["dev"],
    
    # Additional metadata
    cmdclass={},
    ext_modules=[],
    
    # Options
    options={
        "build_scripts": {
            "executable": "/usr/bin/env python",
        },
    },
)
