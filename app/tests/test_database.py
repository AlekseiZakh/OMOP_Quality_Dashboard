import pytest
import pandas as pd
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sys
from pathlib import Path

# Add app directory to path for imports
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

try:
    from database.connection import OMOPDatabase, build_connection_string, get_database_connection
    from database.queries import OMOPQueries, QualityCheckQueries
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestOMOPDatabase:
    """Test cases for OMOPDatabase class"""
    
    @pytest.fixture
    def temp_sqlite_db(self):
        """Create a temporary SQLite database for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Create test database with sample OMOP tables
        conn = sqlite3.connect(temp_file.name)
        cursor = conn.cursor()
        
        # Create sample tables
        cursor.execute("""
        CREATE TABLE person (
            person_id INTEGER PRIMARY KEY,
            gender_concept_id INTEGER,
            year_of_birth INTEGER,
            month_of_birth INTEGER,
            day_of_birth INTEGER,
            race_concept_id INTEGER,
            ethnicity_concept_id INTEGER
        )
        """)
        
        cursor.execute("""
        CREATE TABLE condition_occurrence (
            condition_occurrence_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            condition_concept_id INTEGER,
            condition_start_date DATE,
            condition_end_date DATE,
            condition_source_value TEXT,
            visit_occurrence_id INTEGER
        )
        """)
        
        cursor.execute("""
        CREATE TABLE drug_exposure (
            drug_exposure_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            drug_concept_id INTEGER,
            drug_exposure_start_date DATE,
            drug_exposure_end_date DATE,
            drug_source_value TEXT,
            visit_occurrence_id INTEGER
        )
        """)
        
        cursor.execute("""
        CREATE TABLE visit_occurrence (
            visit_occurrence_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            visit_concept_id INTEGER,
            visit_start_date DATE,
            visit_end_date DATE,
            visit_source_value TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE concept (
            concept_id INTEGER PRIMARY KEY,
            concept_name TEXT,
            domain_id TEXT,
            vocabulary_id TEXT,
            concept_class_id TEXT,
            standard_concept TEXT,
            concept_code TEXT,
            valid_start_date DATE,
            valid_end_date DATE,
            invalid_reason TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE death (
            person_id INTEGER PRIMARY KEY,
            death_date DATE,
            death_type_concept_id INTEGER,
            cause_concept_id INTEGER,
            cause_source_value TEXT
        )
        """)
        
        # Insert sample data
        cursor.execute("""
        INSERT INTO person VALUES 
        (1, 8507, 1980, 5, 15, 8527, 38003564),
        (2, 8532, 1975, 8, 22, 8515, 38003564),
        (3, 8507, 1990, NULL, NULL, 8527, NULL),
        (4, 8532, 1985, 12, 31, 8515, 38003564)
        """)
        
        cursor.execute("""
        INSERT INTO condition_occurrence VALUES 
        (1, 1, 320128, '2023-01-15', '2023-01-20', 'E11.9', 1),
        (2, 2, 4329847, '2023-02-10', NULL, 'I10', 2),
        (3, 1, 0, '2023-03-05', NULL, 'UNMAPPED_CODE', 1),
        (4, 3, 320128, '2023-04-01', '2023-04-05', 'E11.9', 3)
        """)
        
        cursor.execute("""
        INSERT INTO drug_exposure VALUES 
        (1, 1, 1308216, '2023-01-16', '2023-01-30', 'METFORMIN', 1),
        (2, 2, 0, '2023-02-11', '2023-02-25', 'UNMAPPED_DRUG', 2),
        (3, 3, 1308216, '2023-04-02', '2023-04-16', 'METFORMIN', 3)
        """)
        
        cursor.execute("""
        INSERT INTO visit_occurrence VALUES 
        (1, 1, 9202, '2023-01-15', '2023-01-20', 'OUTPATIENT'),
        (2, 2, 9201, '2023-02-10', '2023-02-12', 'INPATIENT'),
        (3, 3, 9202, '2023-04-01', '2023-04-05', 'OUTPATIENT')
        """)
        
        cursor.execute("""
        INSERT INTO concept VALUES 
        (8507, 'MALE', 'Gender', 'Gender', 'Gender', 'S', 'M', '1970-01-01', '2099-12-31', NULL),
        (8532, 'FEMALE', 'Gender', 'Gender', 'Gender', 'S', 'F', '1970-01-01', '2099-12-31', NULL),
        (320128, 'Essential hypertension', 'Condition', 'SNOMED', 'Clinical Finding', 'S', '59621000', '1970-01-01', '2099-12-31', NULL),
        (4329847, 'Myocardial infarction', 'Condition', 'SNOMED', 'Clinical Finding', 'S', '22298006', '1970-01-01', '2099-12-31', NULL),
        (1308216, 'Metformin', 'Drug', 'RxNorm', 'Ingredient', 'S', '6809', '1970-01-01', '2099-12-31', NULL),
        (9202, 'Outpatient Visit', 'Visit', 'Visit', 'Visit', 'S', 'OP', '1970-01-01', '2099-12-31', NULL),
        (9201, 'Inpatient Visit', 'Visit', 'Visit', 'Visit', 'S', 'IP', '1970-01-01', '2099-12-31', NULL)
        """)
        
        cursor.execute("""
        INSERT INTO death VALUES 
        (4, '2023-12-31', 38003566, 4329847, 'I21.9')
        """)
        
        conn.commit()
        conn.close()
        
        yield temp_file.name
        
        # Cleanup
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass  # File might already be deleted
    
    def test_database_initialization(self, temp_sqlite_db):
        """Test database initialization"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        assert db.connection_string == connection_string
        assert db.engine is not None
        assert db.session_maker is not None
    
    def test_database_connection_success(self, temp_sqlite_db):
        """Test successful database connection"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        assert db.test_connection() is True
    
    def test_database_connection_failure(self):
        """Test database connection failure"""
        invalid_connection_string = "sqlite:///nonexistent_file.db"
        
        with pytest.raises(Exception):
            OMOPDatabase(invalid_connection_string)
    
    def test_execute_query_success(self, temp_sqlite_db):
        """Test successful query execution"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        query = "SELECT COUNT(*) as count FROM person"
        result = db.execute_query(query)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert result['count'].iloc[0] == 4  # Updated to match our test data
    
    def test_execute_query_with_parameters(self, temp_sqlite_db):
        """Test query execution with parameters"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        query = "SELECT * FROM person WHERE year_of_birth > :year"
        params = {'year': 1978}
        result = db.execute_query(query, params)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # Should return 3 people born after 1978
    
    def test_execute_query_failure(self, temp_sqlite_db):
        """Test query execution failure"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        invalid_query = "SELECT * FROM nonexistent_table"
        result = db.execute_query(invalid_query)
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    def test_get_table_list(self, temp_sqlite_db):
        """Test getting table list"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        tables = db.get_table_list()
        
        assert isinstance(tables, pd.DataFrame)
        # For SQLite, this will check actual table existence
        # The method should find our test tables
    
    def test_get_table_row_count(self, temp_sqlite_db):
        """Test getting table row count"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        count = db.get_table_row_count("person")
        assert count == 4
        
        count = db.get_table_row_count("condition_occurrence")
        assert count == 4
        
        # Test non-existent table
        count = db.get_table_row_count("nonexistent_table")
        assert count == 0
    
    def test_table_exists(self, temp_sqlite_db):
        """Test table existence checking"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        assert db.table_exists("person") is True
        assert db.table_exists("condition_occurrence") is True
        assert db.table_exists("nonexistent_table") is False
    
    def test_get_database_info(self, temp_sqlite_db):
        """Test database info retrieval"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        info = db.get_database_info()
        
        assert isinstance(info, dict)
        assert 'connection_status' in info
        assert 'tables_found' in info
        assert info['connection_status'] is True


class TestConnectionStringBuilder:
    """Test cases for connection string building"""
    
    def test_build_postgresql_connection_string(self):
        """Test PostgreSQL connection string building"""
        conn_str = build_connection_string(
            'postgresql', 'localhost', 5432, 'omop', 'user', 'password'
        )
        expected = "postgresql://user:password@localhost:5432/omop"
        assert conn_str == expected
    
    def test_build_postgresql_variant_connection_string(self):
        """Test PostgreSQL variant connection string building"""
        conn_str = build_connection_string(
            'postgres', 'localhost', 5432, 'omop', 'user', 'password'
        )
        expected = "postgresql://user:password@localhost:5432/omop"
        assert conn_str == expected
    
    def test_build_sqlserver_connection_string(self):
        """Test SQL Server connection string building"""
        conn_str = build_connection_string(
            'sqlserver', 'server', 1433, 'omop', 'user', 'password'
        )
        expected = "mssql+pymssql://user:password@server:1433/omop"
        assert conn_str == expected
    
    def test_build_mssql_connection_string(self):
        """Test MSSQL connection string building"""
        conn_str = build_connection_string(
            'mssql', 'server', 1433, 'omop', 'user', 'password'
        )
        expected = "mssql+pymssql://user:password@server:1433/omop"
        assert conn_str == expected
    
    def test_build_sqlite_connection_string(self):
        """Test SQLite connection string building"""
        conn_str = build_connection_string(
            'sqlite', '', 0, 'test.db', '', ''
        )
        expected = "sqlite:///test.db"
        assert conn_str == expected
    
    def test_build_mysql_connection_string(self):
        """Test MySQL connection string building"""
        conn_str = build_connection_string(
            'mysql', 'localhost', 3306, 'omop', 'user', 'password'
        )
        expected = "mysql+pymysql://user:password@localhost:3306/omop"
        assert conn_str == expected
    
    def test_unsupported_database_type(self):
        """Test unsupported database type"""
        with pytest.raises(ValueError):
            build_connection_string(
                'unsupported', 'host', 1234, 'db', 'user', 'pass'
            )
    
    def test_validate_connection_params(self):
        """Test connection parameter validation"""
        from database.connection import validate_connection_params
        
        # Valid PostgreSQL params
        result = validate_connection_params('postgresql', 'localhost', 5432, 'omop', 'user', 'pass')
        assert result['valid'] is True
        assert len(result['errors']) == 0
        
        # Invalid params - missing database
        result = validate_connection_params('postgresql', 'localhost', 5432, '', 'user', 'pass')
        assert result['valid'] is False
        assert 'Database name is required' in result['errors']
        
        # Invalid port
        result = validate_connection_params('postgresql', 'localhost', 70000, 'omop', 'user', 'pass')
        assert result['valid'] is False
        assert 'Port must be between 1 and 65535' in result['errors']
        
        # Valid SQLite params
        result = validate_connection_params('sqlite', '', 0, '/path/to/db.sqlite', '', '')
        assert result['valid'] is True


class TestOMOPQueries:
    """Test cases for OMOP queries"""
    
    def test_get_table_row_counts_query(self):
        """Test table row counts query generation"""
        query = OMOPQueries.get_table_row_counts()
        
        assert isinstance(query, str)
        assert "SELECT" in query.upper()
        assert "person" in query
        assert "condition_occurrence" in query
        assert "UNION ALL" in query.upper()
    
    def test_get_completeness_check_query(self):
        """Test completeness check query generation"""
        table_name = "person"
        fields = ["person_id", "gender_concept_id"]
        
        query = OMOPQueries.get_completeness_check(table_name, fields)
        
        assert isinstance(query, str)
        assert table_name in query
        assert "person_id IS NULL" in query
        assert "gender_concept_id IS NULL" in query
        assert "null_percentage" in query
    
    def test_get_completeness_check_query_empty_fields(self):
        """Test completeness check query with empty fields"""
        with pytest.raises(ValueError):
            OMOPQueries.get_completeness_check("person", [])
    
    def test_get_person_demographics_quality_query(self):
        """Test person demographics quality query"""
        query = OMOPQueries.get_person_demographics_quality()
        
        assert isinstance(query, str)
        assert "person" in query
        assert "gender_concept_id" in query
        assert "year_of_birth" in query
        assert "completeness_score" in query
    
    def test_get_future_dates_check_query(self):
        """Test future dates check query"""
        query = OMOPQueries.get_future_dates_check()
        
        assert isinstance(query, str)
        assert "condition_start_date" in query
        assert "drug_exposure_start_date" in query
        assert "CURRENT_DATE" in query.upper() or "current_date" in query
    
    def test_get_events_after_death_query(self):
        """Test events after death check query"""
        query = OMOPQueries.get_events_after_death()
        
        assert isinstance(query, str)
        assert "death" in query
        assert "condition_occurrence" in query
        assert "drug_exposure" in query
        assert "death_date" in query
    
    def test_get_birth_death_consistency_query(self):
        """Test birth/death consistency check query"""
        query = OMOPQueries.get_birth_death_consistency()
        
        assert isinstance(query, str)
        assert "person" in query
        assert "death" in query
        assert "death_date" in query
        assert "year_of_birth" in query
    
    def test_get_unmapped_concepts_summary_query(self):
        """Test unmapped concepts summary query"""
        query = OMOPQueries.get_unmapped_concepts_summary()
        
        assert isinstance(query, str)
        assert "concept_id = 0" in query
        assert "condition_occurrence" in query
        assert "drug_exposure" in query
        assert "unmapped_count" in query
    
    def test_get_foreign_key_violations_query(self):
        """Test foreign key violations query"""
        query = OMOPQueries.get_foreign_key_violations()
        
        assert isinstance(query, str)
        assert "person" in query
        assert "condition_occurrence" in query
        assert "visit_occurrence" in query
        assert "violation_count" in query
    
    def test_get_measurement_outliers_query(self):
        """Test measurement outliers query"""
        query = OMOPQueries.get_measurement_outliers()
        
        assert isinstance(query, str)
        assert "measurement" in query
        assert "value_as_number" in query
        assert "outlier_status" in query


class TestQualityCheckQueries:
    """Test cases for quality check query collections"""
    
    def test_critical_completeness_checks(self):
        """Test critical completeness checks collection"""
        queries = QualityCheckQueries.critical_completeness_checks()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)
    
    def test_temporal_integrity_checks(self):
        """Test temporal integrity checks collection"""
        queries = QualityCheckQueries.temporal_integrity_checks()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)
    
    def test_concept_quality_checks(self):
        """Test concept quality checks collection"""
        queries = QualityCheckQueries.concept_quality_checks()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)
    
    def test_referential_integrity_checks(self):
        """Test referential integrity checks collection"""
        queries = QualityCheckQueries.referential_integrity_checks()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)
    
    def test_statistical_outlier_checks(self):
        """Test statistical outlier checks collection"""
        queries = QualityCheckQueries.statistical_outlier_checks()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)
    
    def test_get_all_quality_checks(self):
        """Test getting all quality checks organized by category"""
        all_checks = QualityCheckQueries.get_all_quality_checks()
        
        assert isinstance(all_checks, dict)
        assert 'completeness' in all_checks
        assert 'temporal' in all_checks
        assert 'concept_mapping' in all_checks
        assert 'referential' in all_checks
        assert 'statistical' in all_checks


class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def test_query_execution_with_real_data(self, temp_sqlite_db):
        """Test query execution with real OMOP-like data"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        # Test completeness query
        query = OMOPQueries.get_completeness_check("person", ["gender_concept_id", "year_of_birth"])
        result = db.execute_query(query)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'null_percentage' in result.columns
    
    def test_demographics_quality_with_real_data(self, temp_sqlite_db):
        """Test demographics quality query with real data"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        query = OMOPQueries.get_person_demographics_quality()
        result = db.execute_query(query)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'total_persons' in result.columns
        assert 'completeness_score' in result.columns
        
        # Check that we have the expected number of persons
        assert result['total_persons'].iloc[0] == 4
    
    def test_unmapped_concepts_with_real_data(self, temp_sqlite_db):
        """Test unmapped concepts query with real data"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        query = OMOPQueries.get_unmapped_concepts_summary()
        result = db.execute_query(query)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'domain' in result.columns
        assert 'unmapped_count' in result.columns


class TestDatabaseCaching:
    """Test cases for database caching functionality"""
    
    @patch('streamlit.cache_resource')
    def test_get_database_connection_caching(self, mock_cache):
        """Test database connection caching"""
        mock_cache.return_value = lambda x: x  # Mock decorator
        
        connection_string = "sqlite:///test.db"
        
        # This would normally test the caching, but we need to mock Streamlit
        # In a real environment, this would be tested differently
        assert callable(get_database_connection)


class TestDatabaseErrorHandling:
    """Test cases for database error handling"""
    
    def test_connection_error_handling(self):
        """Test connection error handling"""
        with pytest.raises(Exception):
            OMOPDatabase("invalid://connection/string")
    
    def test_query_error_handling(self, temp_sqlite_db):
        """Test query error handling"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        # Test invalid SQL
        result = db.execute_query("INVALID SQL QUERY")
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    def test_parameter_error_handling(self, temp_sqlite_db):
        """Test parameter error handling"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        # Test query with invalid parameters
        query = "SELECT * FROM person WHERE person_id = :invalid_param"
        result = db.execute_query(query, {"wrong_param": 1})
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    def test_connection_test_error_handling(self):
        """Test connection test error handling"""
        # Create database with invalid connection string but don't fail immediately
        try:
            db = OMOPDatabase("sqlite:///nonexistent_path/test.db")
        except:
            # If initialization fails, that's expected
            pass
        else:
            # If initialization succeeds, test_connection should fail gracefully
            assert db.test_connection() is False


class TestDatabasePerformance:
    """Test cases for database performance"""
    
    def test_large_query_handling(self, temp_sqlite_db):
        """Test handling of larger queries"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        # Create a query that joins multiple tables
        query = """
        SELECT p.person_id, p.year_of_birth, c.condition_concept_id, d.drug_concept_id
        FROM person p
        LEFT JOIN condition_occurrence c ON p.person_id = c.person_id
        LEFT JOIN drug_exposure d ON p.person_id = d.person_id
        """
        
        result = db.execute_query(query)
        
        assert isinstance(result, pd.DataFrame)
        # Should handle the join without issues
    
    def test_concurrent_query_handling(self, temp_sqlite_db):
        """Test handling of concurrent queries"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db1 = OMOPDatabase(connection_string)
        db2 = OMOPDatabase(connection_string)
        
        # Both connections should work independently
        result1 = db1.execute_query("SELECT COUNT(*) as count FROM person")
        result2 = db2.execute_query("SELECT COUNT(*) as count FROM condition_occurrence")
        
        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)
        assert not result1.empty
        assert not result2.empty


@pytest.fixture
def mock_database():
    """Create a mock database for testing"""
    mock_db = Mock(spec=OMOPDatabase)
    mock_db.execute_query.return_value = pd.DataFrame({
        'test_column': [1, 2, 3],
        'another_column': ['a', 'b', 'c']
    })
    mock_db.test_connection.return_value = True
    mock_db.get_table_row_count.return_value = 100
    mock_db.table_exists.return_value = True
    mock_db.get_table_list.return_value = pd.DataFrame({
        'table_name': ['person', 'condition_occurrence', 'drug_exposure'],
        'row_count': [1000, 5000, 3000]
    })
    return mock_db


class TestMockDatabase:
    """Test cases using mock database"""
    
    def test_mock_database_functionality(self, mock_database):
        """Test using mock database"""
        result = mock_database.execute_query("SELECT * FROM test")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        
        assert mock_database.test_connection() is True
        assert mock_database.get_table_row_count("test_table") == 100
        assert mock_database.table_exists("test_table") is True
    
    def test_mock_database_table_list(self, mock_database):
        """Test mock database table list functionality"""
        tables = mock_database.get_table_list()
        assert isinstance(tables, pd.DataFrame)
        assert 'table_name' in tables.columns
        assert 'row_count' in tables.columns
        assert len(tables) == 3


class TestDatabaseEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_query_result(self, temp_sqlite_db):
        """Test handling of queries that return no results"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        query = "SELECT * FROM person WHERE person_id = 999999"
        result = db.execute_query(query)
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    def test_null_parameter_handling(self, temp_sqlite_db):
        """Test handling of null parameters"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        query = "SELECT * FROM person WHERE year_of_birth = :year"
        result = db.execute_query(query, {'year': None})
        
        assert isinstance(result, pd.DataFrame)
    
    def test_special_characters_in_query(self, temp_sqlite_db):
        """Test handling of special characters in queries"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        # Query with special characters should be handled safely
        query = "SELECT * FROM person WHERE 1=1 -- comment"
        result = db.execute_query(query)
        
        assert isinstance(result, pd.DataFrame)


if __name__ == "__main__":
    # Run tests with coverage reporting
    pytest.main([__file__, "-v", "--cov=app.database", "--cov-report=html"])
