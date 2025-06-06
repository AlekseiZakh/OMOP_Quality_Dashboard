import pytest
import pandas as pd
import tempfile
import sqlite3
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))


@pytest.fixture
def sample_omop_data():
    """Provide sample OMOP data for testing"""
    return {
        'person': pd.DataFrame({
            'person_id': [1, 2, 3, 4, 5],
            'gender_concept_id': [8507, 8532, 8507, 8532, 8507],
            'year_of_birth': [1980, 1975, 1990, 1985, 1992],
            'month_of_birth': [5, 8, None, 12, 3],
            'day_of_birth': [15, 22, None, 5, 10],
            'race_concept_id': [8527, 8515, 8527, 8515, 8527],
            'ethnicity_concept_id': [38003564, 38003564, None, 38003564, 38003564]
        }),
        'condition_occurrence': pd.DataFrame({
            'condition_occurrence_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 1, 2],
            'condition_concept_id': [320128, 4329847, 0, 201820, 132797],
            'condition_start_date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-15'],
            'condition_end_date': ['2023-01-20', None, None, '2023-01-25', '2023-02-20'],
            'condition_source_value': ['E11.9', 'I10', 'UNMAPPED', 'Z51.11', 'M79.3'],
            'visit_occurrence_id': [1, 2, 3, 1, 2]
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
            'visit_occurrence_id': [1, 2, 3, 1, 2]
        }),
        'visit_occurrence': pd.DataFrame({
            'visit_occurrence_id': [1, 2, 3, 4, 5],
            'person_id': [1, 2, 3, 4, 5],
            'visit_concept_id': [9202, 9201, 9202, 9201, 9202],
            'visit_start_date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-10', '2023-02-05'],
            'visit_end_date': ['2023-01-15', '2023-02-10', None, '2023-01-10', '2023-02-05'],
            'visit_source_value': ['OP', 'IP', 'OP', 'IP', 'OP']
        }),
        'concept': pd.DataFrame({
            'concept_id': [8507, 8532, 320128, 4329847, 1503297, 1308216, 9202, 9201],
            'concept_name': ['MALE', 'FEMALE', 'Essential hypertension', 'Myocardial infarction', 
                           'Metformin', 'Lisinopril', 'Outpatient Visit', 'Inpatient Visit'],
            'domain_id': ['Gender', 'Gender', 'Condition', 'Condition', 'Drug', 'Drug', 'Visit', 'Visit'],
            'vocabulary_id': ['Gender', 'Gender', 'SNOMED', 'SNOMED', 'RxNorm', 'RxNorm', 'Visit', 'Visit'],
            'concept_class_id': ['Gender', 'Gender', 'Clinical Finding', 'Clinical Finding', 
                                'Ingredient', 'Ingredient', 'Visit', 'Visit'],
            'standard_concept': ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],
            'concept_code': ['M', 'F', '59621000', '22298006', '6809', '29046', 'OP', 'IP'],
            'valid_start_date': ['1970-01-01'] * 8,
            'valid_end_date': ['2099-12-31'] * 8,
            'invalid_reason': [None] * 8
        })
    }


@pytest.fixture
def temp_sqlite_database(sample_omop_data):
    """Create a temporary SQLite database with sample OMOP data"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    conn = sqlite3.connect(temp_file.name)
    
    # Create tables and insert data
    for table_name, df in sample_omop_data.items():
        df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    conn.close()
    
    yield temp_file.name
    
    # Cleanup
    Path(temp_file.name).unlink()


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions for testing"""
    with patch('streamlit.write') as mock_write, \
         patch('streamlit.dataframe') as mock_dataframe, \
         patch('streamlit.metric') as mock_metric, \
         patch('streamlit.plotly_chart') as mock_plotly_chart, \
         patch('streamlit.columns') as mock_columns, \
         patch('streamlit.subheader') as mock_subheader, \
         patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.expander') as mock_expander, \
         patch('streamlit.selectbox') as mock_selectbox, \
         patch('streamlit.multiselect') as mock_multiselect:
        
        # Configure mock returns
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_selectbox.return_value = 1
        mock_multiselect.return_value = []
        
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
            'multiselect': mock_multiselect
        }


@pytest.fixture
def mock_database():
    """Create a mock database for testing"""
    mock_db = Mock()
    
    # Configure common return values
    mock_db.test_connection.return_value = True
    mock_db.get_table_row_count.return_value = 1000
    mock_db.get_table_list.return_value = pd.DataFrame({
        'table_name': ['person', 'condition_occurrence', 'drug_exposure'],
        'row_count': [1000, 5000, 3000]
    })
    mock_db.execute_query.return_value = pd.DataFrame({
        'count': [100],
        'percentage': [95.5]
    })
    
    return mock_db


@pytest.fixture
def sample_quality_results():
    """Provide sample quality check results"""
    return {
        'completeness': {
            'table_completeness': {
                'status': 'PASS',
                'data': [
                    {'table_name': 'person', 'null_percentage': 5, 'total_rows': 1000, 'status': 'PASS'},
                    {'table_name': 'condition_occurrence', 'null_percentage': 8, 'total_rows': 5000, 'status': 'WARNING'}
                ],
                'message': 'Checked 2 tables for completeness'
            },
            'critical_fields': {
                'status': 'PASS',
                'total_failures': 0,
                'data': [
                    {'check_name': 'Person IDs', 'null_count': 0, 'status': 'PASS'},
                    {'check_name': 'Concept IDs', 'null_count': 0, 'status': 'PASS'}
                ],
                'message': 'All critical fields are complete'
            }
        },
        'temporal': {
            'future_dates': {
                'status': 'FAIL',
                'total_future_dates': 5,
                'data': [
                    {'table': 'condition_occurrence', 'date_field': 'condition_start_date', 'future_count': 3},
                    {'table': 'drug_exposure', 'date_field': 'drug_exposure_start_date', 'future_count': 2}
                ],
                'message': 'Found 5 future dates'
            },
            'events_after_death': {
                'status': 'PASS',
                'total_events_after_death': 0,
                'data': [],
                'message': 'No events after death found'
            }
        }
    }


@pytest.fixture
def sample_chart_data():
    """Provide sample data for chart testing"""
    return {
        'completeness_data': [
            {'table_name': 'person', 'null_percentage': 5, 'total_rows': 1000},
            {'table_name': 'condition_occurrence', 'null_percentage': 10, 'total_rows': 5000},
            {'table_name': 'drug_exposure', 'null_percentage': 2, 'total_rows': 3000}
        ],
        'vocabulary_data': [
            {
                'vocabulary_name': 'SNOMED CT',
                'unique_concepts': 5000,
                'condition_usage': 8000,
                'drug_usage': 0,
                'procedure_usage': 1000
            },
            {
                'vocabulary_name': 'RxNorm',
                'unique_concepts': 3000,
                'condition_usage': 0,
                'drug_usage': 5000,
                'procedure_usage': 0
            }
        ],
        'age_distribution': [
            {'age_group': 'Under 18', 'count': 100, 'percentage': 10},
            {'age_group': '18-30', 'count': 200, 'percentage': 20},
            {'age_group': '31-50', 'count': 300, 'percentage': 30},
            {'age_group': '51-70', 'count': 250, 'percentage': 25},
            {'age_group': 'Over 70', 'count': 150, 'percentage': 15}
        ]
    }


# Test markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.database = pytest.mark.database
pytest.mark.ui = pytest.mark.ui


def pytest_configure(config):
    """Configure pytest with custom settings"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as testing UI components"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add unit marker to tests by default
        if not any(marker in item.keywords for marker in ['integration', 'slow', 'database', 'ui']):
            item.add_marker(pytest.mark.unit)
        
        # Add database marker to database-related tests
        if 'database' in item.name.lower() or 'db' in item.name.lower():
            item.add_marker(pytest.mark.database)
        
        # Add UI marker to UI-related tests
        if any(ui_term in item.name.lower() for ui_term in ['dashboard', 'chart', 'component', 'streamlit']):
            item.add_marker(pytest.mark.ui)
