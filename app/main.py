import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Add app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import OMOPDatabase, build_connection_string, load_db_config_from_env
from quality_checks.completeness import CompletenessChecker
from quality_checks.temporal import TemporalChecker

# Page configuration
st.set_page_config(
    page_title="OMOP Quality Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-pass { color: #28a745; }
    .status-fail { color: #dc3545; }
    .status-warning { color: #ffc107; }
    .status-error { color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">🏥 OMOP Quality Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for database connection
st.sidebar.header("🔗 Database Connection")

# Database connection form
with st.sidebar.form("db_connection"):
    st.subheader("Connection Settings")
    
    db_type = st.selectbox(
        "Database Type",
        ["PostgreSQL", "SQL Server", "SQLite"],
        index=0
    )
    
    if db_type != "SQLite":
        host = st.text_input("Host", value="localhost")
        port = st.number_input("Port", value=5432 if db_type == "PostgreSQL" else 1433)
        database = st.text_input("Database Name", value="omop_cdm")
        username = st.text_input("Username", value="omop_user")
        password = st.text_input("Password", type="password")
    else:
        database = st.text_input("Database File Path", value="omop.db")
        host = port = username = password = None
    
    connect_button = st.form_submit_button("Connect to Database")

# Initialize session state
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'database' not in st.session_state:
    st.session_state.database = None

# Handle database connection
if connect_button:
    try:
        with st.spinner("Connecting to database..."):
            if db_type == "SQLite":
                connection_string = f"sqlite:///{database}"
            else:
                connection_string = build_connection_string(
                    db_type.lower(), host, port, database, username, password
                )
            
            st.session_state.database = OMOPDatabase(connection_string)
            
            if st.session_state.database.test_connection():
                st.session_state.db_connected = True
                st.sidebar.success("✅ Connected successfully!")
            else:
                st.sidebar.error("❌ Connection failed!")
                st.session_state.db_connected = False
    except Exception as e:
        st.sidebar.error(f"❌ Connection error: {str(e)}")
        st.session_state.db_connected = False

# Show connection status
if st.session_state.db_connected:
    st.sidebar.success("🟢 Database Connected")
else:
    st.sidebar.warning("🔴 Database Not Connected")

# Main dashboard content
if st.session_state.db_connected and st.session_state.database:
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Completeness", "⏰ Temporal", "🔍 Detailed Analysis"])
    
    with tab1:
        st.header("📊 Quality Overview")
        
        # Database overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                tables = st.session_state.database.get_table_list()
                total_tables = len(tables) if not tables.empty else 0
                st.metric("OMOP Tables", total_tables)
            except:
                st.metric("OMOP Tables", "Error")
        
        with col2:
            try:
                person_count = st.session_state.database.get_table_row_count("person")
                st.metric("Total Patients", f"{person_count:,}")
            except:
                st.metric("Total Patients", "Error")
        
        with col3:
            try:
                condition_count = st.session_state.database.get_table_row_count("condition_occurrence")
                st.metric("Conditions", f"{condition_count:,}")
            except:
                st.metric("Conditions", "Error")
        
        with col4:
            try:
                drug_count = st.session_state.database.get_table_row_count("drug_exposure")
                st.metric("Drug Exposures", f"{drug_count:,}")
            except:
                st.metric("Drug Exposures", "Error")
        
        # Table overview chart
        st.subheader("📋 Table Row Counts")
        try:
            tables_df = st.session_state.database.get_table_list()
            if not tables_df.empty:
                fig = px.bar(
                    tables_df.head(10), 
                    x='table_name', 
                    y='row_count',
                    title="Top 10 OMOP Tables by Row Count",
                    labels={'table_name': 'Table Name', 'row_count': 'Row Count'}
                )
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No table data available")
        except Exception as e:
            st.error(f"Error loading table data: {str(e)}")
    
    with tab2:
        st.header("📋 Data Completeness Analysis")
        
        if st.button("🔍 Run Completeness Checks", type="primary"):
            with st.spinner("Running completeness checks..."):
                try:
                    completeness_checker = CompletenessChecker(st.session_state.database)
                    results = completeness_checker.run_checks()
                    
                    # Summary metrics
                    summary = completeness_checker.get_summary()
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Checks", summary['total_checks'])
                    
                    with col2:
                        st.metric("Passed", summary['passed_checks'], 
                                delta=summary['passed_checks'], delta_color="normal")
                    
                    with col3:
                        st.metric("Warnings", summary['warning_checks'],
                                delta=summary['warning_checks'], delta_color="inverse")
                    
                    with col4:
                        st.metric("Failed", summary['failed_checks'],
                                delta=summary['failed_checks'], delta_color="inverse")
                    
                    # Display detailed results
                    st.subheader("🏥 Table Completeness Results")
                    if 'table_completeness' in results:
                        table_data = results['table_completeness'].get('data', [])
                        if table_data:
                            df = pd.DataFrame(table_data)
                            
                            # Create completeness visualization
                            fig = px.bar(
                                df, 
                                x='table_name', 
                                y='null_percentage',
                                color='status',
                                title="Null Percentage by Table",
                                labels={'null_percentage': 'Null Percentage (%)', 'table_name': 'Table Name'},
                                color_discrete_map={'PASS': '#28a745', 'WARNING': '#ffc107', 'FAIL': '#dc3545'}
                            )
                            fig.update_xaxis(tickangle=45)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Data table
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.warning("No table completeness data available")
                    
                    # Critical fields results
                    st.subheader("🔍 Critical Fields Analysis")
                    if 'critical_fields' in results:
                        critical_data = results['critical_fields'].get('data', [])
                        if critical_data:
                            critical_df = pd.DataFrame(critical_data)
                            
                            # Display critical fields status
                            for _, row in critical_df.iterrows():
                                status_class = f"status-{row['status'].lower()}"
                                st.markdown(
                                    f"<p class='{status_class}'><strong>{row['check_name']}</strong>: "
                                    f"{row['null_count']} null values ({row['status']})</p>", 
                                    unsafe_allow_html=True
                                )
                        else:
                            st.warning("No critical fields data available")
                    
                    # Person table completeness
                    st.subheader("👤 Person Table Analysis")
                    if 'person_completeness' in results:
                        person_result = results['person_completeness']
                        if 'completeness_score' in person_result:
                            score = person_result['completeness_score']
                            
                            # Completeness gauge
                            fig = go.Figure(go.Indicator(
                                mode = "gauge+number+delta",
                                value = score,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': "Person Table Completeness Score"},
                                delta = {'reference': 90},
                                gauge = {
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "darkblue"},
                                    'steps': [
                                        {'range': [0, 50], 'color': "lightgray"},
                                        {'range': [50, 80], 'color': "yellow"},
                                        {'range': [80, 100], 'color': "lightgreen"}
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': 90
                                    }
                                }
                            ))
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Detailed person data
                            if 'data' in person_result:
                                person_data = person_result['data']
                                st.write("**Person Table Details:**")
                                person_metrics = st.columns(5)
                                with person_metrics[0]:
                                    st.metric("Total Persons", f"{person_data.get('total_persons', 0):,}")
                                with person_metrics[1]:
                                    st.metric("Missing Gender", person_data.get('missing_gender', 0))
                                with person_metrics[2]:
                                    st.metric("Missing Birth Year", person_data.get('missing_birth_year', 0))
                                with person_metrics[3]:
                                    st.metric("Missing Race", person_data.get('missing_race', 0))
                                with person_metrics[4]:
                                    st.metric("Missing Ethnicity", person_data.get('missing_ethnicity', 0))
                        else:
                            st.error("Error analyzing person table completeness")
                    
                except Exception as e:
                    st.error(f"Error running completeness checks: {str(e)}")
    
    with tab3:
        st.header("⏰ Temporal Consistency Analysis")
        
        if st.button("🔍 Run Temporal Checks", type="primary"):
            with st.spinner("Running temporal consistency checks..."):
                try:
                    temporal_checker = TemporalChecker(st.session_state.database)
                    results = temporal_checker.run_checks()
                    
                    # Summary metrics
                    summary = temporal_checker.get_summary()
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Checks", summary['total_checks'])
                    with col2:
                        st.metric("Passed", summary['passed_checks'])
                    with col3:
                        st.metric("Warnings", summary['warning_checks'])
                    with col4:
                        st.metric("Failed", summary['failed_checks'])
                    
                    # Future dates check
                    st.subheader("📅 Future Dates Analysis")
                    if 'future_dates' in results:
                        future_result = results['future_dates']
                        total_future = future_result.get('total_future_dates', 0)
                        
                        if total_future > 0:
                            st.error(f"❌ Found {total_future} records with future dates!")
                            
                            future_data = future_result.get('data', [])
                            if future_data:
                                future_df = pd.DataFrame(future_data)
                                
                                # Future dates by table chart
                                fig = px.bar(
                                    future_df, 
                                    x='table', 
                                    y='future_count',
                                    title="Future Dates by Table",
                                    labels={'future_count': 'Number of Future Dates', 'table': 'Table Name'}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                st.dataframe(future_df, use_container_width=True)
                        else:
                            st.success("✅ No future dates found!")
                    
                    # Birth/death consistency
                    st.subheader("👶➡️💀 Birth/Death Consistency")
                    if 'birth_death_consistency' in results:
                        bd_result = results['birth_death_consistency']
                        inconsistent_count = bd_result.get('inconsistent_count', 0)
                        
                        if inconsistent_count > 0:
                            st.error(f"❌ Found {inconsistent_count} deaths before birth!")
                        else:
                            st.success("✅ All birth/death dates are consistent!")
                    
                    # Events after death
                    st.subheader("💀➡️🏥 Events After Death")
                    if 'events_after_death' in results:
                        ead_result = results['events_after_death']
                        total_events = ead_result.get('total_events_after_death', 0)
                        
                        if total_events > 0:
                            st.error(f"❌ Found {total_events} clinical events after death!")
                            
                            ead_data = ead_result.get('data', [])
                            if ead_data:
                                ead_df = pd.DataFrame(ead_data)
                                
                                # Events after death chart
                                fig = px.bar(
                                    ead_df, 
                                    x='event_type', 
                                    y='events_after_death',
                                    title="Events After Death by Type",
                                    labels={'events_after_death': 'Number of Events', 'event_type': 'Event Type'}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                st.dataframe(ead_df, use_container_width=True)
                        else:
                            st.success("✅ No events found after death!")
                    
                except Exception as e:
                    st.error(f"Error running temporal checks: {str(e)}")
    
    with tab4:
        st.header("🔍 Detailed Analysis")
        
        # Custom query interface
        st.subheader("📝 Custom Query")
        st.write("Execute custom SQL queries to investigate specific data quality issues.")
        
        query_text = st.text_area(
            "Enter your SQL query:",
            height=150,
            placeholder="SELECT * FROM person LIMIT 10;"
        )
        
        if st.button("Execute Query"):
            if query_text.strip():
                try:
                    with st.spinner("Executing query..."):
                        result = st.session_state.database.execute_query(query_text)
                        
                        if not result.empty:
                            st.success(f"Query returned {len(result)} rows")
                            st.dataframe(result, use_container_width=True)
                            
                            # Download button
                            csv = result.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Results as CSV",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime='text/csv'
                            )
                        else:
                            st.warning("Query returned no results")
                            
                except Exception as e:
                    st.error(f"Query execution error: {str(e)}")
            else:
                st.warning("Please enter a query to execute")
        
        # Predefined analysis options
        st.subheader("📊 Predefined Analyses")
        
        analysis_type = st.selectbox(
            "Select analysis type:",
            [
                "Top 10 Conditions by Frequency",
                "Age Distribution at First Visit",
                "Gender Distribution",
                "Most Common Drug Classes",
                "Visit Type Distribution",
                "Data Volume by Year"
            ]
        )
        
        if st.button("Run Analysis"):
            try:
                with st.spinner("Running analysis..."):
                    if analysis_type == "Top 10 Conditions by Frequency":
                        query = """
                        SELECT 
                            c.concept_name,
                            COUNT(*) as frequency
                        FROM condition_occurrence co
                        JOIN concept c ON co.condition_concept_id = c.concept_id
                        WHERE c.concept_id != 0
                        GROUP BY c.concept_name
                        ORDER BY frequency DESC
                        LIMIT 10
                        """
                        result = st.session_state.database.execute_query(query)
                        
                        if not result.empty:
                            fig = px.bar(
                                result, 
                                x='frequency', 
                                y='concept_name',
                                orientation='h',
                                title="Top 10 Conditions by Frequency"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            st.dataframe(result, use_container_width=True)
                    
                    elif analysis_type == "Age Distribution at First Visit":
                        query = """
                        SELECT 
                            FLOOR((EXTRACT(YEAR FROM vo.visit_start_date) - p.year_of_birth) / 10) * 10 as age_group,
                            COUNT(*) as count
                        FROM person p
                        JOIN visit_occurrence vo ON p.person_id = vo.person_id
                        WHERE p.year_of_birth IS NOT NULL
                        GROUP BY age_group
                        ORDER BY age_group
                        """
                        result = st.session_state.database.execute_query(query)
                        
                        if not result.empty:
                            result['age_range'] = result['age_group'].astype(str) + '-' + (result['age_group'] + 9).astype(str)
                            fig = px.bar(
                                result, 
                                x='age_range', 
                                y='count',
                                title="Age Distribution at First Visit"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            st.dataframe(result, use_container_width=True)
                    
                    elif analysis_type == "Gender Distribution":
                        query = """
                        SELECT 
                            c.concept_name as gender,
                            COUNT(*) as count
                        FROM person p
                        JOIN concept c ON p.gender_concept_id = c.concept_id
                        GROUP BY c.concept_name
                        ORDER BY count DESC
                        """
                        result = st.session_state.database.execute_query(query)
                        
                        if not result.empty:
                            fig = px.pie(
                                result, 
                                values='count', 
                                names='gender',
                                title="Gender Distribution"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            st.dataframe(result, use_container_width=True)
                    
                    # Add more predefined analyses here...
                    else:
                        st.info("Analysis not yet implemented. Please use custom query instead.")
                        
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")

else:
    # Welcome screen when not connected
    st.markdown("""
    ## Welcome to the OMOP Quality Dashboard! 🎉
    
    This dashboard helps you monitor and analyze the quality of your OMOP Common Data Model implementation.
    
    ### 🚀 Getting Started:
    1. **Connect to Database**: Use the sidebar to connect to your OMOP database
    2. **Overview**: Get a high-level view of your data
    3. **Completeness**: Analyze data completeness across tables
    4. **Temporal**: Check temporal consistency and logic
    5. **Detailed Analysis**: Run custom queries and predefined analyses
    
    ### 📊 Quality Checks Include:
    - **Data Completeness**: Missing values, null percentages
    - **Temporal Consistency**: Future dates, events after death
    - **Referential Integrity**: Foreign key violations
    - **Concept Mapping**: Unmapped concepts, vocabulary coverage
    - **Statistical Outliers**: Unusual patterns and distributions
    
    ### 🔧 Supported Databases:
    - PostgreSQL
    - SQL Server  
    - SQLite
    
    **Ready to start?** Connect your database using the sidebar! 👈
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    🏥 OMOP Quality Dashboard | Built with ❤️ for the healthcare data community
</div>
""", unsafe_allow_html=True)
