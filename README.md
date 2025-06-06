# 🏥 OMOP Quality Dashboard

![Dashboard](https://img.shields.io/badge/OMOP-Quality%20Dashboard-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

A comprehensive data quality monitoring dashboard for OMOP Common Data Model implementations. Automatically detects, visualizes, and reports data quality issues to help healthcare organizations maintain high-quality research databases.

## 🎯 Features

### **Data Quality Checks**
- **📊 Completeness Analysis**: Missing data detection across all OMOP tables
- **⏰ Temporal Consistency**: Date validation, chronological logic, events after death
- **🔗 Referential Integrity**: Foreign key violations, orphaned records
- **🏷️ Concept Mapping**: Unmapped concepts, vocabulary coverage analysis
- **📈 Statistical Outliers**: Age, measurement values, drug quantities

### **Interactive Dashboard**
- **Real-time Monitoring**: Live quality metrics and alerts
- **Visual Analytics**: Interactive charts and graphs
- **Custom Queries**: SQL interface for detailed investigation
- **Export Capabilities**: CSV, Excel, PDF report generation
- **Multi-database Support**: PostgreSQL, SQL Server, SQLite

### **Professional Reports**
- **Executive Summary**: High-level quality scores for leadership
- **Technical Details**: Comprehensive findings for data engineers
- **Trend Analysis**: Quality improvement tracking over time

## 🚀 Quick Start

### **Option 1: Local Installation**

```bash
# Clone the repository
git clone https://github.com/yourusername/omop-quality-dashboard.git
cd omop-quality-dashboard

# Create virtual environment
python -m venv omop_dashboard_env
source omop_dashboard_env/bin/activate  # On Windows: omop_dashboard_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database connection
cp .env.example .env
# Edit .env with your database credentials

# Run the dashboard
python run_dashboard.py
```

### **Option 2: Docker**

```bash
# Clone and start with Docker Compose
git clone https://github.com/yourusername/omop-quality-dashboard.git
cd omop-quality-dashboard

# Start dashboard with included PostgreSQL
docker-compose up -d

# Access dashboard at http://localhost:8501
```

### **Option 3: Pip Install**

```bash
# Install from PyPI (when published)
pip install omop-quality-dashboard

# Run dashboard
omop-dashboard
```

## 📋 Prerequisites

- **Python 3.8+**
- **OMOP CDM Database** (PostgreSQL, SQL Server, or SQLite)
- **Database Access** (read permissions required)

### **Supported OMOP Versions**
- OMOP CD
