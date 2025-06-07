import pytest
import pandas as pd
import tempfile
import sqlite3
import os
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
from datetime import datetime, timedelta
import numpy as np

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Suppress warnings during testing
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_omop_data():
    """Provide comprehensive sample OMOP data for testing"""
    # Generate more realistic dates
    base_date = datetime(2023, 1, 1)
    
    return {
        'person': pd.DataFrame({
            'person_id': [1, 2, 3, 4, 5],
            'gender_concept_id': [8507, 8532, 8507, 8532, 8507],
            'year_of_birth': [1980, 1975, 1990, 1985, 1992],
            'month_of_birth': [5, 8, None, 12, 3],
            'day_of_birth': [15, 22, None, 5, 10],
            'race_concept_id': [8527, 8515, 8527, 8515, 8527],
            'ethnicity_concept_id': [38003564, 38003564, None, 38003564, 38003564],
            'birth_datetime': [
                '1980-05-15 00:00:00', '1975-08-22 00:00:00', '1990-01-01 00:00:00',
                '1985-12-05 00:00:00', '1992-03-10 00:00:00'
            ]
        }),
        
        'condition_occurrence': pd.DataFrame({
            'condition_occurrence_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 1, 2],
            'condition_concept_id': [320128, 4329847, 0, 201820, 132797],
            'condition_start_date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-15'],
            'condition_end_date': ['2023-01-20', None, None, '2023-01-25', '2023-02-20'],
            'condition_source_value': ['E11.9', 'I10', 'UNMAPPED', 'Z51.11', 'M79.3'],
            'visit_occurrence_id': [1, 2, 3, 1, 2],
            'condition_type_concept_id': [32020, 32020, 32020, 32020, 32020]
        }),
        
        'drug_exposure': pd.DataFrame({
            'drug_exposure_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 1, 2],
            'drug_concept_id': [1503297, 1308216, 0, 1503297, 1308216],
            'drug_exposure_start_date': ['2023-01-16', '2023-02-11', '2023-03-06', '2023-01-21', '2023-02-16'],
            'drug_exposure_end_date': ['2023-01-30', '2023-02-25', None, '2023-02-04', '2023-03-02'],
            'quantity': [30, 90, None, 14, 60],
            'days_supply': [14, 14, None, 14, 14],
            'drug_source_value': ['metformin', 'lisinopril', 'UNKNOWN', 'metformin', 'lisinopril'],
            'visit_occurrence_id': [1, 2, 3, 1, 2],
            'drug_type_concept_id': [38000177, 38000177, 38000177, 38000177, 38000177]
        }),
        
        'visit_occurrence': pd.DataFrame({
            'visit_occurrence_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 4, 5],
            'visit_concept_id': [9202, 9201, 9202, 9201, 9202],
            'visit_start_date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-10', '2023-02-05'],
            'visit_end_date': ['2023-01-15', '2023-02-10', None, '2023-01-10', '2023-02-05'],
            'visit_source_value': ['OP', 'IP', 'OP', 'IP', 'OP'],
            'visit_type_concept_id': [44818517, 44818517, 44818517, 44818517, 44818517]
        }),
        
        'measurement': pd.DataFrame({
            'measurement_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 1, 2],
            'measurement_concept_id': [3013682, 3004249, 3019962, 3013682, 3004249],
            'measurement_date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-15'],
            'value_as_number': [13.5, 120, 70.2, 14.1, 115],
            'unit_concept_id': [8713, 8876, 9529, 8713, 8876],
            'visit_occurrence_id': [1, 2, 3, 1, 2]
        }),
        
        'procedure_occurrence': pd.DataFrame({
            'procedure_occurrence_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 1, 2],
            'procedure_concept_id': [4030758, 4079673, 0, 4030758, 4079673],
            'procedure_date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-15'],
            'visit_occurrence_id': [1, 2, 3, 1, 2],
            'procedure_source_value': ['99213', '93010', 'UNMAPPED', '99213', '93010']
        }),
        
        'observation': pd.DataFrame({
            'observation_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 1, 2],
            'observation_concept_id': [4275495, 4058243, 0, 4275495, 4058243],
            'observation_date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-15'],
            'visit_occurrence_id': [1, 2, 3, 1, 2],
            'observation_source_value': ['Z71.3', 'tobacco', 'UNMAPPED', 'Z71.3', 'tobacco']
        }),
        
        'concept': pd.DataFrame({
            'concept_id': [8507, 8532, 320128, 4329847, 1503297, 1308216, 9202, 9201, 0],
            'concept_name': [
                'MALE', 'FEMALE', 'Essential hypertension', 'Myocardial infarction', 
                'Metformin', 'Lisinopril', 'Outpatient Visit', 'Inpatient Visit', 'No matching concept'
            ],
            'domain_id': [
                'Gender', 'Gender', 'Condition', 'Condition', 'Drug', 'Drug', 'Visit', 'Visit', 'Metadata'
            ],
            'vocabulary_id': [
                'Gender', 'Gender', 'SNOMED', 'SNOMED', 'RxNorm', 'RxNorm', 'Visit', 'Visit', 'None'
            ],
            'concept_class_id': [
                'Gender', 'Gender', 'Clinical Finding', 'Clinical Finding', 
                'Ingredient', 'Ingredient', 'Visit', 'Visit', 'Undefined'
            ],
            'standard_concept': ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', None],
            'concept_code': ['M', 'F', '59621000', '22298006', '6809', '29046', 'OP', 'IP', 'No matching concept'],
            'valid_start_date': ['1970-01-01'] * 9,
            'valid_end_date': ['2099-12-31'] * 9,
            'invalid_reason': [None] * 9
        }),
        
        'death': pd.DataFrame({
            'person_id': [4],
            'death_date': ['2023-12-31'],
            'death_type_concept_id': [38003566],
            'cause_concept_id': [4329847],
            'cause_source_value': ['I21.9']
        }),
        
        'vocabulary': pd.DataFrame({
            'vocabulary_id': ['SNOMED', 'ICD10CM', 'RxNorm', 'LOINC', 'CPT4'],
            'vocabulary_name': ['SNOMED CT', 'ICD-10-CM', 'RxNorm', 'LOINC', 'CPT-4'],
            'vocabulary_reference': ['http://snomed.info/sct', 'https://www.cdc.gov/nchs/icd/icd10cm.htm', 
                                   'https://www.nlm.nih.gov/research/umls/rxnorm/', 
                                   'https://loinc.org/', 'https://www.ama-assn.org/practice-management/cpt']
        }),
        
        'concept_relationship': pd.DataFrame({
            'concept_id_1': [320128, 4329847, 1503297],
            'concept_id_2': [320129, 4329848, 1503298],
            'relationship_id': ['Maps to', 'Maps to', 'Maps to'],
            'valid_start_date': ['1970-01-01', '1970-01-01', '1970-01-01'],
            'valid_end_date': ['2099-12-31', '2099-12-31', '2099-12-31'],
            'invalid_reason': [None, None, None]
        })
    }


@pytest.fixture
def sample_omop_data_with_issues():
    """Provide sample OMOP data that contains various quality issues for testing"""
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return {
        'person': pd.DataFrame({
            'person_id': [1, 2, 3, 4, 5],
            'gender_concept_id': [8507, 8532, None, 8532, 8507],  # Missing gender
            'year_of_birth': [1800, 1975, 2030, None, 1992],      # Unrealistic years, missing
            'month_of_birth': [5, 8, None, 12, 3],
            'day_of_birth': [15, 22, None, 5, 10],
            'race_concept_id': [8527, 8515, 8527, 8515, None],
            'ethnicity_concept_id': [38003564, None, None, 38003564, 38003564]
        }),
        
        'condition_occurrence': pd.DataFrame({
            'condition_occurrence_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 999, 1, 2],  # Invalid person_id
            'condition_concept_id': [320128, 0, 0, 201820, 132797],  # Unmapped concepts
            'condition_start_date': ['2023-01-15', future_date, '2023-03-05', '2023-01-20', '2024-01-01'],
            'condition_end_date': ['2023-01-10', None, None, '2023-01-15', '2023-02-20'],  # End before start
            'visit_occurrence_id': [1, 2, 999, 1, 2]  # Invalid visit_id
        }),
        
        'drug_exposure': pd.DataFrame({
            'drug_exposure_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 999, 2],  # Invalid person_id
            'drug_concept_id': [1503297, 0, 0, 1503297, 1308216],  # Unmapped concepts
            'drug_exposure_start_date': ['2023-01-16', '2023-02-11', future_date, '2023-01-21', '2023-02-16'],
            'quantity': [30, -5, None, 14, 1000000],  # Negative quantity, extreme value
            'days_supply': [14, -1, None, 14, 14]  # Negative days supply
        })
    }


@pytest.fixture
def large_sample_data():
    """Generate larger dataset for performance testing"""
    np.random.seed(42)  # For reproducible results
    
    n_persons = 10000
    n_conditions = 50000
    
    return {
        'person': pd.DataFrame({
            'person_id': range(1, n_persons + 1),
            'gender_concept_id': np.random.choice([8507, 8532], n_persons),
            'year_of_birth': np.random.randint(1930, 2010, n_persons),
            'race_concept_id': np.random.choice([8527, 8515, 8516], n_persons),
            'ethnicity_concept_id': np.random.choice([38003564, 38003563], n_persons)
        }),
        
        'condition_occurrence': pd.DataFrame({
            'condition_occurrence_id': range(1, n_conditions + 1),
            'person_id': np.random.randint(1, n_persons + 1, n_conditions),
            'condition_concept_id': np.random.choice([320128, 4329847, 201820, 132797], n_conditions),
            'condition_start_date': pd.date_range('2020-01-01', '2023-12-31', n_conditions).strftime('%Y-%m-%d')
        })
    }


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture
def temp_sqlite_database(sample_omop_data):
    """Create a temporary SQLite database with sample OMOP data"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    conn = sqlite3.connect(temp_file.name)
    
    try:
        # Create tables and insert data
        for table_name, df in sample_omop_data.items():
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Create some indexes for better performance
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX idx_person_id ON person(person_id)")
        cursor.execute("CREATE INDEX idx_condition_person_id ON condition_occurrence(person_id)")
        cursor.execute("CREATE INDEX idx_drug_person_id ON drug_exposure(person_id)")
        cursor.execute("CREATE INDEX idx_visit_person_id ON visit_occurrence(person_id)")
        conn.commit()
        
    finally:
        conn.close()
    
    yield temp_file.name
    
    # Cleanup
    try:
        Path(temp_file.name).unlink()
    except OSError:
        pass  # File might already be deleted


@pytest.fixture
def temp_sqlite_database_with_issues(sample_omop_data_with_issues):
    """Create a temporary SQLite database with problematic data for testing quality checks"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    conn = sqlite3.connect(temp_file.name)
    
    try:
        for table_name, df in sample_omop_data_with_issues.items():
            df.to_sql(table_name, conn, if_exists='replace', index=False)
    finally:
        conn.close()
    
    yield temp_file.name
    
    # Cleanup
    try:
        Path(temp_file.name).unlink()
    except OSError:
        pass


@pytest.fixture
def mock_database():
    """Create a comprehensive mock database for testing"""
    mock_db = Mock()
    
    # Configure common return values
    mock_db.test_connection.return_value = True
    mock_db.get_table_row_count.return_value = 1000
    mock_db.table_exists.return_value = True
    
    mock_db.get_table_list.return_value = pd.DataFrame({
        'table_name': ['person', 'condition_occurrence', 'drug_exposure', 'visit_occurrence'],
        'row_count': [1000, 5000, 3000, 2000]
    })
    
    mock_db.execute_query.return_value = pd.DataFrame({
        'count': [100],
        'percentage': [95.5]
    })
    
    mock_db.get_database_info.return_value = {
        'connection_status': True,
        'tables_found': 4,
        'database_type': 'sqlite',
        'version': '3.39.0'
    }
    
    return mock_db


@pytest.fixture
def mock_database_connection_failure():
    """Mock database that fails to connect"""
    mock_db = Mock()
    mock_db.test_connection.return_value = False
    mock_db.get_table_list.side_effect = Exception("Connection failed")
    mock_db.execute_query.side_effect = Exception("Connection failed")
    
    return mock_db


# =============================================================================
# STREAMLIT MOCKING FIXTURES
# =============================================================================

@pytest.fixture
def mock_streamlit():
    """Comprehensive mock for Streamlit functions"""
    with patch('streamlit.write') as mock_write, \
         patch('streamlit.dataframe') as mock_dataframe, \
         patch('streamlit.metric') as mock_metric, \
         patch('streamlit.plotly_chart') as mock_plotly_chart, \
         patch('streamlit.columns') as mock_columns, \
         patch('streamlit.subheader') as mock_subheader, \
         patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.expander') as mock_expander, \
         patch('streamlit.selectbox') as mock_selectbox, \
         patch('streamlit.multiselect') as mock_multiselect, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.checkbox') as mock_checkbox, \
         patch('streamlit.slider') as mock_slider, \
         patch('streamlit.text_input') as mock_text_input, \
         patch('streamlit.number_input') as mock_number_input, \
         patch('streamlit.text_area') as mock_text_area, \
         patch('streamlit.sidebar') as mock_sidebar, \
         patch('streamlit.tabs') as mock_tabs, \
         patch('streamlit.container') as mock_container, \
         patch('streamlit.empty') as mock_empty, \
         patch('streamlit.spinner') as mock_spinner, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.info') as mock_info:
        
        # Configure mock returns
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_selectbox.return_value = 1
        mock_multiselect.return_value = []
        mock_button.return_value = False
        mock_checkbox.return_value = False
        mock_slider.return_value = 50
        mock_text_input.return_value = ""
        mock_number_input.return_value = 0
        mock_text_area.return_value = ""
        
        # Configure sidebar mock
        mock_sidebar.form = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
        mock_sidebar.header = Mock()
        mock_sidebar.subheader = Mock()
        mock_sidebar.button = Mock(return_value=False)
        mock_sidebar.selectbox = Mock(return_value="postgresql")
        mock_sidebar.text_input = Mock(return_value="localhost")
        mock_sidebar.number_input = Mock(return_value=5432)
        
        # Configure spinner as context manager
        mock_spinner_context = Mock()
        mock_spinner_context.__enter__ = Mock(return_value=mock_spinner_context)
        mock_spinner_context.__exit__ = Mock(return_value=None)
        mock_spinner.return_value = mock_spinner_context
        
        yield {
            'write': mock_write,
            'dataframe': mock_dataframe,
            'metric': mock_metric,
            'plotly_chart': mock_plotly_chart,
            'columns': mock_columns,
            'subheader': mock_subheader,
            'markdown': mock_markdown,
            'expander': mock_expander,
            'selectbox': mock_selectbox,
            'multiselect': mock_multiselect,
            'button': mock_button,
            'checkbox': mock_checkbox,
            'slider': mock_slider,
            'text_input': mock_text_input,
            'number_input': mock_number_input,
            'text_area': mock_text_area,
            'sidebar': mock_sidebar,
            'tabs': mock_tabs,
            'container': mock_container,
            'empty': mock_empty,
            'spinner': mock_spinner,
            'success': mock_success,
            'error': mock_error,
            'warning': mock_warning,
            'info': mock_info
        }


# =============================================================================
# SAMPLE RESULTS FIXTURES
# =============================================================================

@pytest.fixture
def sample_quality_results():
    """Provide comprehensive sample quality check results"""
    return {
        'completeness': {
            'table_completeness': {
                'status': 'PASS',
                'data': [
                    {'table_name': 'person', 'null_percentage': 5, 'total_rows': 1000, 'status': 'PASS'},
                    {'table_name': 'condition_occurrence', 'null_percentage': 8, 'total_rows': 5000, 'status': 'WARNING'},
                    {'table_name': 'drug_exposure', 'null_percentage': 15, 'total_rows': 3000, 'status': 'WARNING'}
                ],
                'message': 'Checked 3 tables for completeness'
            },
            'critical_fields': {
                'status': 'FAIL',
                'total_failures': 2,
                'data': [
                    {'check_name': 'Person IDs in condition_occurrence', 'null_count': 0, 'status': 'PASS'},
                    {'check_name': 'Concept IDs in condition_occurrence', 'null_count': 5, 'status': 'FAIL'},
                    {'check_name': 'Person IDs in drug_exposure', 'null_count': 0, 'status': 'PASS'},
                    {'check_name': 'Start dates in drug_exposure', 'null_count': 3, 'status': 'FAIL'}
                ],
                'message': 'Found issues in 2 critical field checks'
            },
            'person_completeness': {
                'status': 'PASS',
                'completeness_score': 92.5,
                'data': {
                    'total_persons': 1000,
                    'missing_gender': 10,
                    'missing_birth_year': 5,
                    'missing_race': 100,
                    'missing_ethnicity': 200
                },
                'message': 'Person table completeness: 92.5%'
            }
        },
        'temporal': {
            'future_dates': {
                'status': 'FAIL',
                'total_future_dates': 5,
                'data': [
                    {'table': 'condition_occurrence', 'date_field': 'condition_start_date', 'future_count': 3, 'status': 'FAIL'},
                    {'table': 'drug_exposure', 'date_field': 'drug_exposure_start_date', 'future_count': 2, 'status': 'FAIL'}
                ],
                'message': 'Found 5 future dates across tables'
            },
            'birth_death_consistency': {
                'status': 'PASS',
                'inconsistent_count': 0,
                'message': 'All birth/death dates are consistent'
            },
            'events_after_death': {
                'status': 'PASS',
                'total_events_after_death': 0,
                'data': [],
                'message': 'No events after death found'
            }
        },
        'concept_mapping': {
            'unmapped_concepts': {
                'status': 'WARNING',
                'total_unmapped': 250,
                'max_unmapped_percentage': 8.5,
                'data': [
                    {'domain': 'Condition', 'total_records': 5000, 'unmapped_count': 150, 'unmapped_percentage': 3.0},
                    {'domain': 'Drug', 'total_records': 3000, 'unmapped_count': 100, 'unmapped_percentage': 3.3}
                ],
                'message': 'Found 250 unmapped concepts across domains'
            },
            'standard_concept_usage': {
                'status': 'PASS',
                'standard_percentage': 85.2,
                'data': {
                    'total_concepts': 10000,
                    'standard_concepts': 8520,
                    'non_standard_concepts': 1480
                },
                'message': 'Standard concept usage: 85.2%'
            }
        }
    }


@pytest.fixture
def sample_chart_data():
    """Provide sample data for chart testing"""
    return {
        'completeness_data': [
            {'table_name': 'person', 'null_percentage': 5, 'total_rows': 1000, 'status': 'PASS'},
            {'table_name': 'condition_occurrence', 'null_percentage': 10, 'total_rows': 5000, 'status': 'WARNING'},
            {'table_name': 'drug_exposure', 'null_percentage': 2, 'total_rows': 3000, 'status': 'PASS'},
            {'table_name': 'procedure_occurrence', 'null_percentage': 15, 'total_rows': 2000, 'status': 'WARNING'},
            {'table_name': 'measurement', 'null_percentage': 30, 'total_rows': 8000, 'status': 'FAIL'}
        ],
        'vocabulary_data': [
            {
                'vocabulary_name': 'SNOMED CT',
                'unique_concepts': 5000,
                'condition_usage': 8000,
                'drug_usage': 0,
                'procedure_usage': 1000,
                'measurement_usage': 500
            },
            {
                'vocabulary_name': 'RxNorm',
                'unique_concepts': 3000,
                'condition_usage': 0,
                'drug_usage': 5000,
                'procedure_usage': 0,
                'measurement_usage': 0
            },
            {
                'vocabulary_name': 'LOINC',
                'unique_concepts': 2000,
                'condition_usage': 0,
                'drug_usage': 0,
                'procedure_usage': 0,
                'measurement_usage': 7500
            }
        ],
        'age_distribution': [
            {'age_group': 'Under 18', 'count': 100, 'percentage': 10},
            {'age_group': '18-30', 'count': 200, 'percentage': 20},
            {'age_group': '31-50', 'count': 300, 'percentage': 30},
            {'age_group': '51-70', 'count': 250, 'percentage': 25},
            {'age_group': 'Over 70', 'count': 150, 'percentage': 15}
        ],
        'temporal_issues': {
            'future_dates': [
                {'table': 'condition_occurrence', 'future_count': 5},
                {'table': 'drug_exposure', 'future_count': 3},
                {'table': 'procedure_occurrence', 'future_count': 1}
            ],
            'events_after_death': [
                {'event_type': 'condition_occurrence', 'events_after_death': 0},
                {'event_type': 'drug_exposure', 'events_after_death': 2}
            ]
        }
    }


# =============================================================================
# CONFIGURATION FIXTURES
# =============================================================================

@pytest.fixture
def sample_config():
    """Provide sample configuration for testing"""
    return {
        'database': {
            'default_type': 'postgresql',
            'pool_size': 5,
            'query_timeout': 300
        },
        'quality_checks': {
            'completeness': {
                'table_completeness_warning': 10,
                'table_completeness_fail': 25
            },
            'temporal': {
                'max_age': 120,
                'future_date_tolerance': 0
            }
        },
        'dashboard': {
            'title': 'Test Dashboard',
            'refresh_interval': 300,
            'chart_colors': {
                'pass': '#28a745',
                'warning': '#ffc107',
                'fail': '#dc3545'
            }
        }
    }


@pytest.fixture
def mock_config_manager():
    """Mock configuration manager"""
    config_manager = Mock()
    config_manager.get.side_effect = lambda key, default=None: {
        'database.default_type': 'postgresql',
        'database.pool_size': 5,
        'dashboard.title': 'OMOP Quality Dashboard',
        'dashboard.refresh_interval': 300,
        'quality_checks.completeness.table_completeness_warning': 10,
        'quality_checks.completeness.table_completeness_fail': 25,
        'quality_checks.temporal.max_age': 120,
        'quality_checks.temporal.future_date_tolerance': 0,
        'dashboard.chart_colors.pass': '#28a745',
        'dashboard.chart_colors.warning': '#ffc107',
        'dashboard.chart_colors.fail': '#dc3545'
    }.get(key, default)
    
    config_manager.get_chart_colors.return_value = {
        'pass': '#28a745',
        'warning': '#ffc107',
        'fail': '#dc3545',
        'error': '#6c757d'
    }
    
    return config_manager


# =============================================================================
# ENVIRONMENT AND UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def suppress_logging():
    """Suppress logging during tests"""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically setup test environment for all tests"""
    # Set test environment variables
    original_env = os.environ.copy()
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['LOG_LEVEL'] = 'ERROR'  # Reduce log noise during tests
    os.environ['DASHBOARD_DEBUG'] = 'false'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# =============================================================================
# PERFORMANCE AND BENCHMARKING FIXTURES
# =============================================================================

@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer for performance testing"""
    import time
    
    class BenchmarkTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.end_time - self.start_time
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return BenchmarkTimer()


@pytest.fixture
def memory_profiler():
    """Memory profiling fixture for testing memory usage"""
    import tracemalloc
    
    class MemoryProfiler:
        def __init__(self):
            self.start_snapshot = None
            self.end_snapshot = None
        
        def start(self):
            tracemalloc.start()
            self.start_snapshot = tracemalloc.take_snapshot()
        
        def stop(self):
            self.end_snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
            
            if self.start_snapshot:
                top_stats = self.end_snapshot.compare_to(self.start_snapshot, 'lineno')
                return top_stats[:10]  # Top 10 memory allocations
            return []
    
    return MemoryProfiler()


# =============================================================================
# PYTEST CONFIGURATION AND MARKERS
# =============================================================================

# Test markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.database = pytest.mark.database
pytest.mark.ui = pytest.mark.ui
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security


def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Register custom markers
    markers = [
        "unit: mark test as a unit test",
        "integration: mark test as an integration test", 
        "slow: mark test as slow running",
        "database: mark test as requiring database",
        "ui: mark test as testing UI components",
        "performance: mark test as performance/benchmark test",
        "security: mark test as security-related test",
        "smoke: mark test as smoke test for basic functionality",
        "regression: mark test as regression test",
        "api: mark test as API test",
        "e2e: mark test as end-to-end test"
    ]
    
    for marker in markers:
        config.addinivalue_line("markers", marker)
    
    # Configure test output
    config.option.verbose = 2 if config.option.verbose < 2 else config.option.verbose


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically and configure test execution"""
    
    for item in items:
        # Add unit marker to tests by default if no other category marker present
        category_markers = ['integration', 'slow', 'database', 'ui', 'performance', 'security', 'e2e']
        if not any(marker in item.keywords for marker in category_markers):
            item.add_marker(pytest.mark.unit)
        
        # Auto-mark database-related tests
        if any(db_term in item.name.lower() for db_term in ['database', 'db', 'sql', 'connection']):
            item.add_marker(pytest.mark.database)
        
        # Auto-mark UI-related tests
        ui_terms = ['dashboard', 'chart', 'component', 'streamlit', 'ui', 'interface']
        if any(ui_term in item.name.lower() for ui_term in ui_terms):
            item.add_marker(pytest.mark.ui)
        
        # Auto-mark performance tests
        perf_terms = ['performance', 'benchmark', 'speed', 'memory', 'large']
        if any(perf_term in item.name.lower() for perf_term in perf_terms):
            item.add_marker(pytest.mark.performance)
        
        # Auto-mark slow tests
        slow_terms = ['slow', 'large_dataset', 'integration', 'e2e']
        if any(slow_term in item.name.lower() for slow_term in slow_terms):
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark security tests
        security_terms = ['security', 'auth', 'permission', 'access', 'vulnerability']
        if any(security_term in item.name.lower() for security_term in security_terms):
            item.add_marker(pytest.mark.security)


def pytest_runtest_setup(item):
    """Setup before each test runs"""
    # Skip slow tests if not explicitly requested
    if "slow" in item.keywords and not item.config.getoption("--runslow", default=False):
        pytest.skip("need --runslow option to run slow tests")
    
    # Skip database tests if database not available (can be configured)
    if "database" in item.keywords:
        # Add any database availability checks here
        pass
    
    # Skip performance tests unless explicitly requested
    if "performance" in item.keywords and not item.config.getoption("--runperf", default=False):
        pytest.skip("need --runperf option to run performance tests")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--runslow", 
        action="store_true", 
        default=False, 
        help="run slow tests"
    )
    parser.addoption(
        "--runperf", 
        action="store_true", 
        default=False, 
        help="run performance tests"
    )
    parser.addoption(
        "--database-url",
        action="store",
        default=None,
        help="database URL for integration tests"
    )


def pytest_report_header(config):
    """Add custom header to test reports"""
    return [
        "OMOP Quality Dashboard Test Suite",
        f"Python: {sys.version}",
        f"Test Environment: {os.environ.get('ENVIRONMENT', 'test')}",
        f"Database URL: {config.getoption('--database-url', 'Not provided')}"
    ]


# =============================================================================
# FIXTURE CLEANUP AND FINALIZATION
# =============================================================================

def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    # Create necessary test directories
    test_dirs = ['logs', 'exports', 'data', 'cache']
    for dir_name in test_dirs:
        test_dir = Path(__file__).parent / dir_name
        test_dir.mkdir(exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    # Cleanup test artifacts
    test_dirs = ['cache', 'temp']
    for dir_name in test_dirs:
        test_dir = Path(__file__).parent / dir_name
        if test_dir.exists():
            import shutil
            try:
                shutil.rmtree(test_dir)
            except OSError:
                pass


# =============================================================================
# HELPER FUNCTIONS FOR TESTS
# =============================================================================

def create_mock_quality_checker(checker_type="completeness", status="PASS"):
    """Helper function to create mock quality checkers"""
    mock_checker = Mock()
    mock_checker.run_checks.return_value = {
        f'{checker_type}_check': {
            'status': status,
            'message': f'{checker_type} check completed',
            'data': []
        }
    }
    mock_checker.get_summary.return_value = {
        'total_checks': 1,
        'passed_checks': 1 if status == 'PASS' else 0,
        'failed_checks': 1 if status == 'FAIL' else 0,
        'warning_checks': 1 if status == 'WARNING' else 0,
        'error_checks': 1 if status == 'ERROR' else 0
    }
    return mock_checker


def assert_dataframe_structure(df, expected_columns, min_rows=0):
    """Helper function to assert DataFrame structure"""
    assert isinstance(df, pd.DataFrame), "Expected pandas DataFrame"
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    assert len(df) >= min_rows, f"Expected at least {min_rows} rows, got {len(df)}"


def assert_quality_check_result(result, expected_status=None, required_keys=None):
    """Helper function to assert quality check result structure"""
    assert isinstance(result, dict), "Quality check result must be a dictionary"
    
    # Check required keys
    default_keys = ['status', 'message']
    if required_keys:
        default_keys.extend(required_keys)
    
    for key in default_keys:
        assert key in result, f"Missing required key '{key}' in quality check result"
    
    # Check status if provided
    if expected_status:
        assert result['status'] == expected_status, f"Expected status '{expected_status}', got '{result['status']}'"
    
    # Validate status is one of the expected values
    valid_statuses = ['PASS', 'FAIL', 'WARNING', 'ERROR']
    assert result['status'] in valid_statuses, f"Status must be one of {valid_statuses}, got '{result['status']}'"


# =============================================================================
# PARAMETRIZED TEST DATA
# =============================================================================

# Common test parameters for database types
DATABASE_TYPES = [
    ("postgresql", 5432),
    ("sqlserver", 1433),
    ("mysql", 3306),
    ("sqlite", 0)
]

# Common test parameters for quality check statuses
QUALITY_STATUSES = ["PASS", "FAIL", "WARNING", "ERROR"]

# Common test parameters for OMOP table names
OMOP_TABLES = [
    "person", "condition_occurrence", "drug_exposure", 
    "procedure_occurrence", "measurement", "visit_occurrence", 
    "observation", "death", "concept"
]

# Export these for use in test files
__all__ = [
    'sample_omop_data',
    'sample_omop_data_with_issues', 
    'large_sample_data',
    'temp_sqlite_database',
    'temp_sqlite_database_with_issues',
    'mock_database',
    'mock_database_connection_failure',
    'mock_streamlit',
    'sample_quality_results',
    'sample_chart_data',
    'sample_config',
    'mock_config_manager',
    'temp_directory',
    'mock_logger',
    'suppress_logging',
    'benchmark_timer',
    'memory_profiler',
    'create_mock_quality_checker',
    'assert_dataframe_structure',
    'assert_quality_check_result',
    'DATABASE_TYPES',
    'QUALITY_STATUSES',
    'OMOP_TABLES'
]
