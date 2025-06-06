OMOP Quality Dashboard Documentation
Welcome to the comprehensive documentation for the OMOP Quality Dashboard.
📚 Documentation Structure

installation.md - Installation and setup guide
user_guide.md - Complete user guide
api_reference.md - API documentation
configuration.md - Configuration options
quality_checks.md - Quality check documentation
deployment.md - Deployment strategies
troubleshooting.md - Common issues and solutions
contributing.md - Development contribution guide
changelog.md - Version history and changes

🎯 Quick Links

🚀 Quick Start Guide
📊 Quality Check Overview
⚙️ Configuration Reference
🐛 Troubleshooting

📖 About This Documentation
This documentation is designed for:

Healthcare Data Engineers implementing OMOP CDM
Research Informaticists managing healthcare databases
Clinical Researchers validating data for studies
Quality Assurance Teams in healthcare organizations
OHDSI Community members working with OMOP data


docs/installation.md
Installation Guide
🎯 Quick Start
Prerequisites

Python 3.8 or higher
Access to an OMOP CDM database (PostgreSQL, SQL Server, or SQLite)
4GB+ RAM recommended

1. Clone Repository
bashgit clone https://github.com/your-org/omop-quality-dashboard.git
cd omop-quality-dashboard
2. Create Virtual Environment
bashpython -m venv omop_dashboard_env
source omop_dashboard_env/bin/activate  # On Windows: omop_dashboard_env\Scripts\activate
3. Install Dependencies
bashpip install -r requirements.txt
4. Configure Database
bashcp .env.example .env
nano .env  # Edit with your database credentials
5. Run Dashboard
bashpython run_dashboard.py
Dashboard will be available at: http://localhost:8501
🐳 Docker Installation
Quick Docker Setup
bash# Clone repository
git clone https://github.com/your-org/omop-quality-dashboard.git
cd omop-quality-dashboard

# Copy environment file
cp .env.example .env
# Edit .env with your database settings

# Start with Docker Compose
docker-compose up -d
Production Docker Deployment
bash# Production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With monitoring
docker-compose --profile with-monitoring up -d

# With reverse proxy
docker-compose --profile with-proxy up -d
🔧 Detailed Installation
System Requirements
Minimum Requirements:

CPU: 2 cores
RAM: 2GB
Storage: 5GB free space
Python: 3.8+

Recommended Requirements:

CPU: 4+ cores
RAM: 8GB+
Storage: 20GB+ free space
Python: 3.10+

Database Setup
PostgreSQL
bash# Install PostgreSQL client
sudo apt-get install postgresql-client  # Ubuntu/Debian
brew install postgresql                  # macOS

# Connection string format
OMOP_DB_CONNECTION_STRING=postgresql://username:password@host:5432/database
SQL Server
bash# Install SQL Server drivers
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo apt-get install msodbcsql17

# Connection string format  
OMOP_DB_CONNECTION_STRING=mssql+pymssql://username:password@host:1433/database
SQLite (Testing)
bash# No additional setup required
OMOP_DB_CONNECTION_STRING=sqlite:///path/to/omop.db
Advanced Configuration
Performance Tuning
bash# .env configuration
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
MAX_MEMORY_MB=4096
DASHBOARD_CACHE_TTL=600
Security Configuration
bash# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Update .env
SECRET_KEY=your_generated_key_here
ENABLE_AUTHENTICATION=true
Verification
Test Installation
bash# Check configuration
python run_dashboard.py --check-only

# Run tests
python -m pytest tests/ -v

# Test database connection
python -c "
from app.database.connection import OMOPDatabase
import os
db = OMOPDatabase(os.getenv('OMOP_DB_CONNECTION_STRING'))
print('✅ Database connection successful!')
"
🚀 Development Setup
Development Environment
bash# Install development dependencies
pip install -r requirements-test.txt

# Setup pre-commit hooks
pre-commit install

# Run in development mode
DASHBOARD_DEBUG=true DEV_MODE=true python run_dashboard.py
IDE Configuration
VS Code
json// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./omop_dashboard_env/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
PyCharm

Open project in PyCharm
Set interpreter to ./omop_dashboard_env/bin/python
Enable code formatting with Black
Configure run configuration for run_dashboard.py

🔍 Troubleshooting Installation
Common Issues
Package Installation Failures
bash# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install with no cache
pip install --no-cache-dir -r requirements.txt

# Platform-specific packages
pip install --only-binary=all -r requirements.txt
Database Connection Issues
bash# Test connectivity
telnet your-db-host 5432  # PostgreSQL
telnet your-db-host 1433  # SQL Server

# Check credentials
psql -h host -U username -d database  # PostgreSQL
sqlcmd -S host -U username -d database  # SQL Server
Memory Issues
bash# Reduce memory usage
export MAX_MEMORY_MB=1024
export MAX_DATAFRAME_ROWS=10000

# Monitor memory usage
htop  # Linux/macOS
taskmgr  # Windows
Port Conflicts
bash# Check port usage
netstat -an | grep 8501  # Linux/macOS
netstat -an | findstr 8501  # Windows

# Use different port
python run_dashboard.py --port 8502
Getting Help

📖 User Guide
🐛 Troubleshooting Guide
💬 GitHub Issues
📧 Contact: support@yourorg.com


docs/user_guide.md
User Guide
🏥 Overview
The OMOP Quality Dashboard provides comprehensive data quality monitoring for OMOP Common Data Model implementations. This guide covers all features and functionality.
🚀 Getting Started
First Launch

Start the dashboard: python run_dashboard.py
Open browser to: http://localhost:8501
Configure database connection in sidebar
Click "Connect to Database"

Dashboard Layout

Sidebar: Database connection and filters
Main Area: Quality check results and visualizations
Tabs: Different analysis views (Overview, Completeness, Temporal, etc.)

📊 Quality Check Overview
Overview Tab
The Overview tab provides a high-level summary of your OMOP data:

Database Metrics: Table counts, patient counts, record volumes
Quality Score: Overall data quality percentage
Table Overview: Row counts for all OMOP tables
Recent Activity: Data freshness indicators

Quality Check Types
1. Completeness Analysis
Purpose: Identify missing or incomplete data
Checks Include:

Missing values in critical fields (person_id, concept_ids)
Table-level completeness percentages
Person demographics completeness
Domain-specific completeness (conditions, drugs, procedures)

How to Use:

Go to "Completeness" tab
Click "Run Completeness Checks"
Review results by category:

Critical Fields: Must-have fields (should be 100% complete)
Table Completeness: Overall null percentages by table
Person Analysis: Demographics completeness with scoring



Interpreting Results:

🟢 PASS: < 5% missing data
🟡 WARNING: 5-15% missing data
🔴 FAIL: > 15% missing data

2. Temporal Consistency
Purpose: Detect date-related data quality issues
Checks Include:

Future dates in clinical events
Events occurring after patient death
Birth/death date consistency
Visit duration anomalies
Age-related temporal issues

How to Use:

Go to "Temporal" tab
Click "Run Temporal Checks"
Review findings:

Future Dates: Events with impossible future dates
Events After Death: Clinical activity post-death
Date Inconsistencies: Logical date relationship violations



Common Issues:

Data entry errors (typos in dates)
System clock issues during data collection
ETL process date handling problems

3. Concept Mapping Quality
Purpose: Assess vocabulary mapping and standardization
Checks Include:

Unmapped concepts (concept_id = 0)
Standard vs non-standard concept usage
Vocabulary coverage analysis
Domain integrity validation
Source value completeness

How to Use:

Go to "Concept Mapping" tab
Review mapping quality by domain
Identify vocabularies needing attention
Export unmapped concepts for remediation

Best Practices:

Aim for < 5% unmapped concepts
Prefer standard concepts (≥ 80%)
Maintain source values for traceability

4. Referential Integrity
Purpose: Ensure proper relationships between tables
Checks Include:

Foreign key violations
Orphaned records without parent references
Person ID consistency across tables
Visit occurrence relationships

How to Use:

Go to "Referential" tab
Run integrity checks
Focus on high-priority violations:

Missing person references
Broken visit associations
Concept ID mismatches



5. Statistical Outliers
Purpose: Identify unusual values and distributions
Checks Include:

Age outliers (unrealistic ages)
Drug quantity anomalies
Measurement value outliers
Visit duration extremes
Data distribution analysis

How to Use:

Go to "Statistical" tab
Review outlier categories
Investigate flagged records
Determine if outliers are:

Data entry errors
Valid extreme cases
System artifacts



🔍 Advanced Features
Custom SQL Queries
Location: Detailed Analysis tab
Purpose: Investigate specific data quality issues
How to Use:

Enter SQL query in text area
Click "Execute Query"
Results displayed in interactive table
Download results as CSV

Example Queries:
sql-- Find patients with multiple genders
SELECT person_id, COUNT(DISTINCT gender_concept_id) as gender_count
FROM person p
JOIN visit_occurrence v ON p.person_id = v.person_id  
GROUP BY person_id
HAVING COUNT(DISTINCT gender_concept_id) > 1;

-- Identify high-frequency conditions
SELECT c.concept_name, COUNT(*) as frequency
FROM condition_occurrence co
JOIN concept c ON co.condition_concept_id = c.concept_id
GROUP BY c.concept_name
ORDER BY frequency DESC
LIMIT 20;
Filtering and Drill-Down

Date Range Filters: Focus on specific time periods
Patient Population: Filter by demographics
Table-Specific: Analyze individual OMOP tables
Interactive Charts: Click to drill down into details

Export and Reporting
Available Formats:

CSV: Raw data export
Excel: Formatted reports with multiple sheets
PDF: Executive summary reports

Export Options:

Individual check results
Complete quality assessment
Custom query results
Chart visualizations

📈 Visualization Guide
Chart Types

Bar Charts: Completeness percentages, outlier counts
Pie Charts: Status distributions, vocabulary usage
Heatmaps: Table completeness overview
Time Series: Trends over time
Scatter Plots: Outlier analysis
Treemaps: Vocabulary coverage

Interactive Features

Hover Details: Additional information on mouse-over
Zoom and Pan: Explore chart details
Filter Controls: Adjust data display
Download Charts: Save as PNG or SVG

⚙️ Configuration
Database Connection
Supported Databases:

PostgreSQL (recommended)
SQL Server
SQLite (testing only)

Connection Methods:

UI Form: Enter credentials in sidebar
Environment Variables: Set in .env file
Connection String: Full connection URL

Quality Thresholds
Customize warning and failure thresholds:
bash# .env configuration
COMPLETENESS_WARNING_THRESHOLD=10
COMPLETENESS_FAIL_THRESHOLD=25
CONCEPT_UNMAPPED_WARNING=5
TEMPORAL_MAX_AGE=120
Performance Settings
bash# Optimize for large databases
DB_POOL_SIZE=10
MAX_DATAFRAME_ROWS=50000
DASHBOARD_CACHE_TTL=600
🔧 Troubleshooting
Common Issues
Slow Performance
Symptoms: Long loading times, timeouts
Solutions:

Increase database connection pool size
Add database indexes on frequently queried columns
Reduce MAX_DATAFRAME_ROWS setting
Enable result caching

Memory Issues
Symptoms: Out of memory errors, browser crashes
Solutions:

Reduce data volume with date filters
Lower MAX_MEMORY_MB setting
Process data in smaller chunks
Restart dashboard application

Connection Problems
Symptoms: Database connection failures
Solutions:

Verify database credentials
Check network connectivity
Confirm database server is running
Review firewall settings

Performance Optimization
Database Indexes
sql-- Recommended indexes for performance
CREATE INDEX idx_person_birth_year ON person(year_of_birth);
CREATE INDEX idx_condition_start_date ON condition_occurrence(condition_start_date);
CREATE INDEX idx_drug_start_date ON drug_exposure(drug_exposure_start_date);
CREATE INDEX idx_visit_start_date ON visit_occurrence(visit_start_date);
Query Optimization

Use date ranges to limit data volume
Pre-filter data in database views
Consider materialized views for complex queries
Monitor query execution plans

📚 Best Practices
Regular Monitoring

Daily: Check for new data quality issues
Weekly: Review trend analysis and quality scores
Monthly: Generate comprehensive quality reports
Quarterly: Update quality thresholds and rules

Data Quality Workflow

Detection: Run automated quality checks
Analysis: Investigate flagged issues
Resolution: Fix data or ETL processes
Validation: Verify improvements
Documentation: Record findings and actions

Team Collaboration

Share Reports: Export quality assessments for team review
Document Issues: Track quality problems and resolutions
Set Alerts: Configure notifications for critical issues
Regular Reviews: Schedule team quality review meetings

🆘 Getting Help
Documentation

Installation Guide
Configuration Reference
Quality Checks Details
API Documentation

Support Resources

📖 Troubleshooting Guide
💬 GitHub Issues
📧 Email: support@yourorg.com
🌐 OHDSI Forums

Training Resources

Video Tutorials: Available on project website
Webinars: Monthly quality check training sessions
Documentation: Comprehensive guides and examples
Community: Active OHDSI and user community


docs/quality_checks.md
Quality Checks Reference
📊 Overview
The OMOP Quality Dashboard performs five main categories of quality checks, each designed to identify specific types of data quality issues common in healthcare databases.
🔍 Completeness Checks
Purpose
Identify missing or incomplete data that could impact research validity.
Checks Performed
Table Completeness

Description: Analyzes null percentages in key fields across OMOP tables
Algorithm: Counts null values in critical fields and calculates percentages
Thresholds:

PASS: < 10% null values
WARNING: 10-25% null values
FAIL: > 25% null values



Critical Fields Analysis

Description: Ensures essential fields are never null
Fields Checked:

person.person_id
person.gender_concept_id
condition_occurrence.person_id
condition_occurrence.condition_concept_id
drug_exposure.person_id
drug_exposure.drug_concept_id


Threshold: 0 null values allowed

Person Demographics Quality

Description: Comprehensive analysis of person table completeness
Metrics:

Overall completeness score (weighted)
Individual field completeness percentages
Missing demographic combinations


Scoring: Based on clinical research requirements

Domain Completeness

Description: Domain-specific completeness analysis
Domains: Condition, Drug, Procedure, Measurement
Analysis: Source values, type concepts, required fields

SQL Examples
sql-- Table completeness check
SELECT 
    COUNT(*) as total_records,
    SUM(CASE WHEN person_id IS NULL OR gender_concept_id IS NULL 
        THEN 1 ELSE 0 END) as incomplete_records,
    ROUND(incomplete_records * 100.0 / total_records, 2) as incomplete_percentage
FROM person;

-- Critical field check
SELECT COUNT(*) as null_person_ids
FROM condition_occurrence 
WHERE person_id IS NULL;
⏰ Temporal Consistency Checks
Purpose
Detect chronological inconsistencies and impossible dates.
Checks Performed
Future Dates Detection

Description: Identifies clinical events with future dates
Tables Checked: All clinical event tables
Logic: Compare event dates with current date
Tolerance: Configurable (default: 0 days)

Birth/Death Consistency

Description: Validates death occurs after birth
Logic: Compare death_date with calculated birth date
Considerations: Handles partial birth dates (missing month/day)

Events After Death

Description: Finds clinical activities after patient death
Tables Checked:

condition_occurrence
drug_exposure
procedure_occurrence
measurement
observation


Logic: Join with death table and compare dates

Visit Date Consistency

Description: Validates visit start/end date relationships
Checks:

End date after start date
Reasonable visit durations
Missing required dates



Age-Related Temporal Issues

Description: Identifies age-related inconsistencies
Checks:

Events before birth
Unrealistic ages (> 120 years)
Pediatric events in adults



SQL Examples
sql-- Future dates check
SELECT COUNT(*) as future_conditions
FROM condition_occurrence
WHERE condition_start_date > CURRENT_DATE;

-- Events after death
SELECT COUNT(*) as events_after_death
FROM condition_occurrence co
JOIN death d ON co.person_id = d.person_id
WHERE co.condition_start_date > d.death_date;

-- Visit duration check
SELECT COUNT(*) as negative_duration_visits
FROM visit_occurrence
WHERE visit_end_date < visit_start_date;
🏷️ Concept Mapping Quality Checks
Purpose
Assess the quality of vocabulary mapping and concept standardization.
Checks Performed
Unmapped Concepts Analysis

Description: Identifies concepts mapped to concept_id = 0
Calculation: Percentage of unmapped concepts by domain
Thresholds:

PASS: < 5% unmapped
WARNING: 5-15% unmapped
FAIL: > 15% unmapped



Standard Concept Usage

Description: Analyzes usage of standard vs non-standard concepts
Metrics:

Percentage using standard concepts (S)
Classification concepts (C) usage
Non-standard concept usage


Target: ≥ 80% standard concept usage

Vocabulary Coverage

Description: Analyzes diversity and usage of vocabularies
Metrics:

Number of active vocabularies
Usage distribution across vocabularies
Vocabulary concentration analysis



Domain Integrity

Description: Ensures concepts are used in appropriate domain tables
Validation:

Condition concepts in condition_occurrence
Drug concepts in drug_exposure
Procedure concepts in procedure_occurrence



Source Value Completeness

Description: Checks completeness of source_value fields
Importance: Essential for traceability and debugging

SQL Examples
sql-- Unmapped concepts by domain
SELECT 
    'Condition' as domain,
    COUNT(*) as total_records,
    SUM(CASE WHEN condition_concept_id = 0 THEN 1 ELSE 0 END) as unmapped_count,
    ROUND(unmapped_count * 100.0 / total_records, 2) as unmapped_percentage
FROM condition_occurrence;

-- Standard concept usage
SELECT 
    c.standard_concept,
    COUNT(*) as usage_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM condition_occurrence co
JOIN concept c ON co.condition_concept_id = c.concept_id
WHERE c.concept_id != 0
GROUP BY c.standard_concept;

-- Domain integrity check
SELECT COUNT(*) as wrong_domain_concepts
FROM condition_occurrence co
JOIN concept c ON co.condition_concept_id = c.concept_id
WHERE c.domain_id != 'Condition' AND c.concept_id != 0;
🔗 Referential Integrity Checks
Purpose
Ensure proper relationships and foreign key constraints between tables.
Checks Performed
Foreign Key Violations

Description: Identifies broken relationships between tables
Key Relationships:

Clinical tables → person
Clinical tables → visit_occurrence
All tables → concept (for concept_ids)
Tables → care_site, provider (where applicable)



Orphaned Records

Description: Finds records without proper parent references
Examples:

Conditions without valid visit_occurrence_id
Drugs without person_id in person table
Measurements without valid person references



Person ID Consistency

Description: Validates person_id usage across all tables
Analysis:

Person IDs in clinical tables but not in person table
Consistency of person_id values
Cross-table person_id validation



Visit Relationships

Description: Analyzes visit_occurrence table integrity
Checks:

Visit records without person_id
Missing visit concept_ids
Visit_detail relationships (if applicable)



Concept ID Integrity

Description: Validates concept_id references
Validation:

Concept IDs exist in concept table
Concepts used in appropriate domains
Valid concept hierarchies



SQL Examples
sql-- Foreign key violations (condition → person)
SELECT COUNT(*) as orphaned_conditions
FROM condition_occurrence co
LEFT JOIN person p ON co.person_id = p.person_id
WHERE co.person_id IS NOT NULL AND p.person_id IS NULL;

-- Person ID consistency across tables
SELECT 
    COUNT(DISTINCT person_id) as clinical_persons,
    (SELECT COUNT(DISTINCT person_id) FROM person) as person_table_count
FROM (
    SELECT person_id FROM condition_occurrence
    UNION
    SELECT person_id FROM drug_exposure
    UNION 
    SELECT person_id FROM visit_occurrence
) clinical_tables;

-- Concept reference integrity
SELECT COUNT(*) as invalid_concept_references
FROM condition_occurrence co
WHERE co.condition_concept_id != 0
AND NOT EXISTS (
    SELECT 1 FROM concept c 
    WHERE c.concept_id = co.condition_concept_id
);
📈 Statistical Outlier Checks
Purpose
Identify statistically unusual values that may indicate data quality issues.
Checks Performed
Age Outliers

Description: Identifies unrealistic ages and birth years
Criteria:

Birth year < 1900
Birth year > current year
Current age > 120 years
Negative ages



Drug Quantity Outliers

Description: Flags unusual drug quantities and days_supply
Outlier Criteria:

Negative quantities
Extremely high quantities (> 10,000)
Days supply > 365
Negative days supply



Measurement Value Outliers

Description: Identifies physiologically impossible measurements
Common Measurements:

Heart rate: Normal range 30-200 bpm
Body temperature: Normal range 32-45°C
Weight: Normal range 0.5-500 kg
Height: Normal range 30-250 cm
Blood pressure: Normal range 40-300 mmHg



Visit Duration Outliers

Description: Flags unusual visit durations
Criteria:

Negative durations (end before start)
Extremely long visits (> 365 days)
Missing end dates for inpatient visits



Distribution Anomalies

Description: Analyzes data distributions for unusual patterns
Analysis:

Gender distribution skew
Age distribution anomalies
Sudden data volume changes by year
Duplicate record patterns



SQL Examples
sql-- Age outliers
SELECT person_id, year_of_birth, 
       EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth as current_age
FROM person 
WHERE year_of_birth < 1900 
   OR year_of_birth > EXTRACT(YEAR FROM CURRENT_DATE)
   OR (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) > 120;

-- Drug quantity outliers  
SELECT drug_exposure_id, person_id, quantity, days_supply
FROM drug_exposure
WHERE quantity < 0 OR quantity > 10000
   OR days_supply < 0 OR days_supply > 365;

-- Measurement outliers (heart rate example)
SELECT measurement_id, person_id, value_as_number
FROM measurement m
JOIN concept c ON m.measurement_concept_id = c.concept_id
WHERE c.concept_name ILIKE '%heart rate%'
  AND (value_as_number < 30 OR value_as_number > 200);
⚙️ Configuration
Threshold Customization
Quality check thresholds can be customized via environment variables:
bash# Completeness thresholds
COMPLETENESS_WARNING_THRESHOLD=10
COMPLETENESS_FAIL_THRESHOLD=25
COMPLETENESS_PERSON_PASS_THRESHOLD=90

# Temporal settings
TEMPORAL_MAX_AGE=120
TEMPORAL_MIN_BIRTH_YEAR=1900
TEMPORAL_FUTURE_DATE_TOLERANCE=0

# Concept mapping thresholds
CONCEPT_UNMAPPED_WARNING=5
CONCEPT_UNMAPPED_FAIL=15
CONCEPT_STANDARD_THRESHOLD=80

# Statistical outlier settings
STATISTICAL_OUTLIER_WARNING=10
STATISTICAL_OUTLIER_FAIL=50
Custom Quality Rules
Future versions will support custom quality rules defined in YAML:
yaml# config/custom_rules.yaml
custom_checks:
  - name: "institution_specific_age_check"
    description: "Custom age validation for pediatric hospital"
    query: "SELECT COUNT(*) FROM person WHERE year_of_birth > 2005"
    threshold: 1000
    severity: "WARNING"
📊 Quality Scoring
Overall Quality Score
The dashboard calculates an overall quality score (0-100%) based on:

Completeness (30%): Weighted by table importance
Temporal Consistency (25%): Critical for research validity
Concept Mapping (20%): Important for interoperability
Referential Integrity (15%): Database consistency
Statistical Outliers (10%): Data plausibility

Scoring Algorithm
pythonquality_score = (
    completeness_score * 0.30 +
    temporal_score * 0.25 +
    concept_score * 0.20 +
    referential_score * 0.15 +
    statistical_score * 0.10
)
Quality Categories

Excellent (90-100%): Research-ready data
Good (80-89%): Minor issues, generally usable
Fair (70-79%): Moderate issues, some limitations
Poor (60-69%): Significant issues, major limitations
Critical (< 60%): Substantial problems, not research-ready

🔄 Automated Monitoring
Scheduled Checks
Configure automated quality checks:
bash# Run quality checks daily at 2 AM
QUALITY_CHECK_SCHEDULE="0 2 * * *"
ENABLE_SCHEDULED_CHECKS=true
EMAIL_ALERTS=true
ALERT_RECIPIENTS="data-team@yourorg.com"
Quality Trends
Track quality changes over time:

Daily quality score trends
New issue detection
Improvement tracking
Regression alerts

Integration with ETL
Integrate quality checks with ETL processes:

Pre-ETL validation
Post-ETL quality assessment
Quality gates for production
Automated rollback triggers


📊 Quality Check Overview
Overview Tab
The Overview tab provides a high-level summary of your OMOP data:

Database Metrics: Table counts, patient counts, record volumes
