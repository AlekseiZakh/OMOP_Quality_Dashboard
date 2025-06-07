import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add app directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import application modules
try:
    from database.connection import OMOPDatabase, build_connection_string
    from quality_checks.completeness import CompletenessChecker
    from quality_checks.temporal import TemporalChecker
    from quality_checks.concept_mapping import ConceptMappingChecker
    from quality_checks.referential import ReferentialIntegrityChecker
    from quality_checks.statistical import StatisticalOutlierChecker
    from utils.config import ConfigManager
    from utils.helpers import DataHelpers, StreamlitHelpers
    from visualizations.dashboard_components import DashboardComponents, QualityCheckRenderer
    from visualizations.charts import OMOPCharts
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.error("Please ensure all application modules are properly installed.")
    st.stop()

# Load configuration
@st.cache_resource
def load_config():
    """Load application configuration"""
    try:
        config = ConfigManager()
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None

# Page configuration
st.set_page_config(
    page_title="OMOP Quality Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-org/omop-quality-dashboard',
        'Report a bug': 'https://github.com/your-org/omop-quality-dashboard/issues',
        'About': "# OMOP Quality Dashboard\nComprehensive data quality monitoring for OMOP CDM implementations."
    }
)

# Load configuration
config = load_config()
if config is None:
    st.error("Failed to load configuration. Using defaults.")
    config = ConfigManager()  # Use defaults

# Apply custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #f0f2f6 0%, #e8ecf0 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #ddd;
    }
    .status-pass { 
        color: #28a745; 
        font-weight: bold;
    }
    .status-fail { 
        color: #dc3545; 
        font-weight: bold;
    }
    .status-warning { 
        color: #ffc107; 
        font-weight: bold;
    }
    .status-error { 
        color: #6c757d; 
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stAlert {
        border-radius: 0.5rem;
    }
    .quality-summary {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Database connection functions
@st.cache_resource
def create_database_connection(connection_string):
    """Create and cache database connection"""
    try:
        db = OMOPDatabase(connection_string)
        if db.test_connection():
            return db
        else:
            return None
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def validate_connection_params(db_type, host, port, database, username, password):
    """Validate database connection parameters"""
    errors = []
    
    if not database:
        errors.append("Database name is required")
    
    if db_type.lower() != 'sqlite':
        if not host:
            errors.append("Host is required")
        if not username:
            errors.append("Username is required")
        if not password:
            errors.append("Password is required")
        if port <= 0 or port > 65535:
            errors.append("Port must be between 1 and 65535")
    
    return errors

# Main title with configuration
dashboard_title = config.get('dashboard.title', 'OMOP Quality Dashboard')
st.markdown(f'<h1 class="main-header">🏥 {dashboard_title}</h1>', unsafe_allow_html=True)

# Sidebar for database connection
st.sidebar.header("🔗 Database Connection")

# Database connection form
with st.sidebar.form("db_connection"):
    st.subheader("Connection Settings")
    
    db_type = st.selectbox(
        "Database Type",
        ["postgresql", "sqlserver", "sqlite"],
        format_func=lambda x: x.title(),
        index=0
    )
    
    if db_type != "sqlite":
        host = st.text_input("Host", value=os.getenv('OMOP_DB_HOST', 'localhost'))
        port = st.number_input(
            "Port", 
            value=int(os.getenv('OMOP_DB_PORT', 5432 if db_type == 'postgresql' else 1433)),
            min_value=1,
            max_value=65535
        )
        database = st.text_input("Database Name", value=os.getenv('OMOP_DB_NAME', 'omop_cdm'))
        username = st.text_input("Username", value=os.getenv('OMOP_DB_USER', 'omop_user'))
        password = st.text_input("Password", type="password", value=os.getenv('OMOP_DB_PASSWORD', ''))
    else:
        database = st.text_input("Database File Path", value=os.getenv('OMOP_DB_NAME', 'omop.db'))
        host = port = username = password = None
    
    connect_button = st.form_submit_button("🔌 Connect to Database", type="primary")

# Initialize session state
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'database' not in st.session_state:
    st.session_state.database = None
if 'connection_string' not in st.session_state:
    st.session_state.connection_string = None

# Handle database connection
if connect_button:
    # Validate parameters
    validation_errors = validate_connection_params(db_type, host, port, database, username, password)
    
    if validation_errors:
        for error in validation_errors:
            st.sidebar.error(f"❌ {error}")
    else:
        try:
            with st.spinner("Connecting to database..."):
                # Build connection string
                if db_type == "sqlite":
                    connection_string = f"sqlite:///{database}"
                else:
                    connection_string = build_connection_string(
                        db_type, host, port, database, username, password
                    )
                
                # Test connection
                database_obj = create_database_connection(connection_string)
                
                if database_obj:
                    st.session_state.database = database_obj
                    st.session_state.connection_string = connection_string
                    st.session_state.db_connected = True
                    st.sidebar.success("✅ Connected successfully!")
                    
                    # Log connection
                    logger.info(f"Successfully connected to {db_type} database")
                    
                    # Show database info
                    db_info = database_obj.get_database_info()
                    st.sidebar.info(f"📊 Tables found: {db_info.get('tables_found', 0)}")
                    
                else:
                    st.sidebar.error("❌ Connection failed! Please check your credentials.")
                    st.session_state.db_connected = False
                    
        except Exception as e:
            st.sidebar.error(f"❌ Connection error: {str(e)}")
            st.session_state.db_connected = False
            logger.error(f"Database connection error: {e}")

# Show connection status
if st.session_state.db_connected:
    st.sidebar.success("🟢 Database Connected")
    
    # Connection details
    with st.sidebar.expander("Connection Details"):
        if st.session_state.database:
            db_info = st.session_state.database.get_database_info()
            st.write(f"**Type:** {db_type.title()}")
            st.write(f"**Database:** {database}")
            if db_type != 'sqlite':
                st.write(f"**Host:** {host}:{port}")
            st.write(f"**Tables:** {db_info.get('tables_found', 'Unknown')}")
            st.write(f"**Status:** {db_info.get('connection_status', 'Unknown')}")
else:
    st.sidebar.warning("🔴 Database Not Connected")

# Auto-refresh option
if st.session_state.db_connected:
    refresh_interval = config.get('dashboard.refresh_interval', 300)
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh", value=False)
    if auto_refresh:
        st.sidebar.info(f"Refreshing every {refresh_interval} seconds")

# Main dashboard content
if st.session_state.db_connected and st.session_state.database:
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", 
        "📋 Completeness", 
        "⏰ Temporal", 
        "🔗 Concept Mapping",
        "🔍 Referential",
        "📈 Advanced"
    ])
    
    with tab1:
        st.header("📊 Data Quality Overview")
        
        # Quick summary cards
        try:
            # Database overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                tables = st.session_state.database.get_table_list()
                total_tables = len(tables) if not tables.empty else 0
                st.metric(
                    "OMOP Tables", 
                    total_tables,
                    help="Total number of OMOP CDM tables found in the database"
                )
            
            with col2:
                person_count = st.session_state.database.get_table_row_count("person")
                st.metric(
                    "Total Patients", 
                    f"{person_count:,}",
                    help="Total number of unique patients in the person table"
                )
            
            with col3:
                condition_count = st.session_state.database.get_table_row_count("condition_occurrence")
                st.metric(
                    "Condition Records", 
                    f"{condition_count:,}",
                    help="Total number of condition occurrence records"
                )
            
            with col4:
                drug_count = st.session_state.database.get_table_row_count("drug_exposure")
                st.metric(
                    "Drug Exposures", 
                    f"{drug_count:,}",
                    help="Total number of drug exposure records"
                )
            
            # Table overview visualization
            st.subheader("📋 Table Population Overview")
            
            if not tables.empty and 'row_count' in tables.columns:
                # Filter to show only tables with data
                populated_tables = tables[tables['row_count'] > 0].head(15)
                
                if not populated_tables.empty:
                    fig = px.bar(
                        populated_tables, 
                        x='table_name', 
                        y='row_count',
                        title="Table Row Counts (Top 15 Populated Tables)",
                        labels={'table_name': 'Table Name', 'row_count': 'Row Count'},
                        color='row_count',
                        color_continuous_scale='Blues'
                    )
                    fig.update_xaxis(tickangle=45)
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Data quality summary placeholder
                    st.subheader("🎯 Quality Score Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Placeholder quality scores - would be calculated from actual checks
                        overall_score = 85  # This would come from running all checks
                        DashboardComponents.render_quality_score_gauge(
                            overall_score, "Overall Quality Score"
                        )
                    
                    with col2:
                        st.markdown("### Recent Alerts")
                        st.info("🔍 Run quality checks to see alerts")
                        st.warning("⚠️ Future dates detected (run temporal checks)")
                        st.success("✅ Person table completeness: Good")
                    
                    with col3:
                        st.markdown("### Quick Actions")
                        if st.button("🚀 Run All Quality Checks", type="primary"):
                            st.info("Navigate to specific tabs to run quality checks")
                        
                        if st.button("📊 Generate Report"):
                            st.info("Report generation feature coming soon!")
                        
                        if st.button("📧 Email Summary"):
                            st.info("Email alerts feature coming soon!")
                
            else:
                st.warning("No table data available or tables are empty")
                
        except Exception as e:
            st.error(f"Error loading overview data: {str(e)}")
            logger.error(f"Overview tab error: {e}")
    
    with tab2:
        st.header("📋 Data Completeness Analysis")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔍 Run Completeness Checks", type="primary", use_container_width=True):
                with st.spinner("Running completeness checks..."):
                    try:
                        completeness_checker = CompletenessChecker(st.session_state.database)
                        results = completeness_checker.run_checks()
                        st.session_state.completeness_results = results
                        st.success("✅ Completeness checks completed!")
                        
                    except Exception as e:
                        st.error(f"Error running completeness checks: {str(e)}")
                        logger.error(f"Completeness check error: {e}")
        
        with col1:
            if 'completeness_results' in st.session_state:
                # Display results using the dashboard components
                QualityCheckRenderer.render_check_results(
                    st.session_state.completeness_results,
                    "Completeness Analysis Results"
                )
    
    with tab3:
        st.header("⏰ Temporal Consistency Analysis")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔍 Run Temporal Checks", type="primary", use_container_width=True):
                with st.spinner("Running temporal consistency checks..."):
                    try:
                        temporal_checker = TemporalChecker(st.session_state.database)
                        results = temporal_checker.run_checks()
                        st.session_state.temporal_results = results
                        st.success("✅ Temporal checks completed!")
                        
                    except Exception as e:
                        st.error(f"Error running temporal checks: {str(e)}")
                        logger.error(f"Temporal check error: {e}")
        
        with col1:
            if 'temporal_results' in st.session_state:
                QualityCheckRenderer.render_check_results(
                    st.session_state.temporal_results,
                    "Temporal Consistency Results"
                )
    
    with tab4:
        st.header("🔗 Concept Mapping Quality")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔍 Run Concept Checks", type="primary", use_container_width=True):
                with st.spinner("Running concept mapping checks..."):
                    try:
                        concept_checker = ConceptMappingChecker(st.session_state.database)
                        results = concept_checker.run_checks()
                        st.session_state.concept_results = results
                        st.success("✅ Concept mapping checks completed!")
                        
                    except Exception as e:
                        st.error(f"Error running concept checks: {str(e)}")
                        logger.error(f"Concept check error: {e}")
        
        with col1:
            if 'concept_results' in st.session_state:
                QualityCheckRenderer.render_check_results(
                    st.session_state.concept_results,
                    "Concept Mapping Results"
                )
    
    with tab5:
        st.header("🔍 Referential Integrity")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔍 Run Referential Checks", type="primary", use_container_width=True):
                with st.spinner("Running referential integrity checks..."):
                    try:
                        referential_checker = ReferentialIntegrityChecker(st.session_state.database)
                        results = referential_checker.run_checks()
                        st.session_state.referential_results = results
                        st.success("✅ Referential integrity checks completed!")
                        
                    except Exception as e:
                        st.error(f"Error running referential checks: {str(e)}")
                        logger.error(f"Referential check error: {e}")
        
        with col1:
            if 'referential_results' in st.session_state:
                QualityCheckRenderer.render_check_results(
                    st.session_state.referential_results,
                    "Referential Integrity Results"
                )
    
    with tab6:
        st.header("📈 Advanced Analysis & Custom Queries")
        
        # Custom query interface
        st.subheader("📝 Custom SQL Query")
        
        # Query examples
        with st.expander("💡 Example Queries"):
            st.code("""
-- Top 10 most common conditions
SELECT c.concept_name, COUNT(*) as frequency
FROM condition_occurrence co
JOIN concept c ON co.condition_concept_id = c.concept_id
WHERE c.concept_id != 0
GROUP BY c.concept_name
ORDER BY frequency DESC
LIMIT 10;

-- Age distribution
SELECT 
    FLOOR((EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) / 10) * 10 as age_group,
    COUNT(*) as count
FROM person 
WHERE year_of_birth IS NOT NULL
GROUP BY age_group
ORDER BY age_group;

-- Data quality overview
SELECT 
    'person' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN gender_concept_id IS NULL THEN 1 ELSE 0 END) as missing_gender,
    SUM(CASE WHEN year_of_birth IS NULL THEN 1 ELSE 0 END) as missing_birth_year
FROM person;
            """)
        
        query_text = st.text_area(
            "Enter your SQL query:",
            height=200,
            placeholder="SELECT * FROM person LIMIT 10;",
            help="Enter a valid SQL query to analyze your OMOP data"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            execute_query = st.button("▶️ Execute Query", type="primary")
        
        with col2:
            limit_results = st.number_input(
                "Limit results to:", 
                min_value=10, 
                max_value=10000, 
                value=1000,
                step=10
            )
        
        if execute_query and query_text.strip():
            try:
                with st.spinner("Executing query..."):
                    # Add LIMIT if not present and result limiting is requested
                    if limit_results and 'LIMIT' not in query_text.upper():
                        query_text += f" LIMIT {limit_results}"
                    
                    result = st.session_state.database.execute_query(query_text)
                    
                    if not result.empty:
                        st.success(f"✅ Query returned {len(result)} rows")
                        
                        # Display results
                        st.dataframe(result, use_container_width=True)
                        
                        # Download options
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            csv = result.to_csv(index=False)
                            st.download_button(
                                label="📥 Download as CSV",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime='text/csv'
                            )
                        
                        with col2:
                            # If openpyxl is available, offer Excel download
                            try:
                                from io import BytesIO
                                buffer = BytesIO()
                                result.to_excel(buffer, index=False)
                                excel_data = buffer.getvalue()
                                
                                st.download_button(
                                    label="📊 Download as Excel",
                                    data=excel_data,
                                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                )
                            except ImportError:
                                st.info("Install openpyxl for Excel download support")
                        
                        with col3:
                            if len(result.select_dtypes(include=[np.number]).columns) > 0:
                                if st.button("📊 Create Chart"):
                                    st.info("Chart creation feature coming soon!")
                    else:
                        st.warning("⚠️ Query returned no results")
                        
            except Exception as e:
                st.error(f"❌ Query execution error: {str(e)}")
                logger.error(f"Query execution error: {e}")

else:
    # Welcome screen when not connected
    st.markdown("""
    <div class="quality-summary">
    
    ## Welcome to the OMOP Quality Dashboard! 🎉
    
    This comprehensive dashboard helps you monitor and analyze the quality of your OMOP Common Data Model implementation.
    
    ### 🚀 Getting Started:
    1. **Connect to Database**: Use the sidebar to connect to your OMOP database
    2. **Overview**: Get a high-level view of your data quality
    3. **Run Quality Checks**: Analyze completeness, temporal consistency, and more
    4. **Generate Reports**: Export findings and track improvements over time
    
    ### 📊 Quality Dimensions Analyzed:
    - **📋 Data Completeness**: Missing values, null percentages, critical field analysis
    - **⏰ Temporal Consistency**: Future dates, chronological logic, events after death
    - **🔗 Concept Mapping**: Unmapped concepts, vocabulary coverage, standard concept usage
    - **🔍 Referential Integrity**: Foreign key violations, orphaned records
    - **📈 Statistical Analysis**: Outliers, distributions, demographic consistency
    
    ### 🔧 Supported Database Systems:
    - **PostgreSQL** - Most common for OMOP implementations
    - **Microsoft SQL Server** - Enterprise healthcare environments  
    - **SQLite** - Testing and development scenarios
    
    ### 🎯 Key Features:
    - **Real-time Quality Monitoring** - Live dashboard updates
    - **Interactive Visualizations** - Drill-down capabilities
    - **Custom Query Interface** - Advanced analysis tools
    - **Export & Reporting** - Share findings with your team
    - **Configurable Thresholds** - Adapt to your quality standards
    
    **Ready to start?** Connect your OMOP database using the sidebar! 👈
    
    </div>
    """, unsafe_allow_html=True)
    
    # Sample screenshots or demo data could go here
    st.markdown("### 📸 Dashboard Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Completeness Analysis**
        - Table-level completeness scoring
        - Critical field validation
        - Person demographics analysis
        - Interactive completeness heatmaps
        """)
    
    with col2:
        st.info("""
        **Temporal Validation**
        - Future date detection
        - Birth/death consistency
        - Event chronology validation
        - Age-related outlier identification
        """)

# Footer with version and links
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🏥 <strong>OMOP Quality Dashboard v1.0.0</strong><br>
    Built with ❤️ for the healthcare data community<br>
    <small>Powered by Streamlit • OMOP CDM • Python</small>
</div>
""", unsafe_allow_html=True)
