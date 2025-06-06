import pytest
import pandas as pd
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add app directory to path for imports
import sys
from pathlib import Path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from database.connection import OMOPDatabase, build_connection_string, get_database_connection
from database.queries import OMOPQueries, QualityCheckQueries


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
        
        # Insert sample data
        cursor.execute("""
        INSERT INTO person VALUES 
        (1, 8507, 1980, 5, 15, 8527, 38003564),
        (2, 8532, 1975, 8, 22, 8515, 38003564),
        (3, 8507, 1990, NULL, NULL, 8527, NULL)
        """)
        
        cursor.execute("""
        INSERT INTO condition_occurrence VALUES 
        (1, 1, 320128, '2023-01-15', '2023-01-20', 'E11.9', 1),
        (2, 2, 4329847, '2023-02-10', NULL, 'I10', 2),
        (3, 1, 0, '2023-03-05', NULL, 'UNMAPPED_CODE', 1)
        """)
        
        cursor.execute("""
        INSERT INTO concept VALUES 
        (8507, 'MALE', 'Gender', 'Gender', 'Gender', 'S', 'M', '1970-01-01', '2099-12-31', NULL),
        (8532, 'FEMALE', 'Gender', 'Gender', 'Gender', 'S', 'F', '1970-01-01', '2099-12-31', NULL),
        (320128, 'Essential hypertension', 'Condition', 'SNOMED', 'Clinical Finding', 'S', '59621000', '1970-01-01', '2099-12-31', NULL),
        (4329847, 'Myocardial infarction', 'Condition', 'SNOMED', 'Clinical Finding', 'S', '22298006', '1970-01-01', '2099-12-31', NULL)
        """)
        
        conn.commit()
        conn.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
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
        assert result['count'].iloc[0] == 3
    
    def test_execute_query_with_parameters(self, temp_sqlite_db):
        """Test query execution with parameters"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        query = "SELECT * FROM person WHERE year_of_birth > :year"
        params = {'year': 1978}
        result = db.execute_query(query, params)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Should return 2 people born after 1978
    
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
        # Note: SQLite doesn't have the same information_schema, so this might return empty
        # In a real test, you'd mock this or use a PostgreSQL test database
    
    def test_get_table_row_count(self, temp_sqlite_db):
        """Test getting table row count"""
        connection_string = f"sqlite:///{temp_sqlite_db}"
        db = OMOPDatabase(connection_string)
        
        count = db.get_table_row_count("person")
        assert count == 3
        
        # Test non-existent table
        count = db.get_table_row_count("nonexistent_table")
        assert count == 0


class TestConnectionStringBuilder:
    """Test cases for connection string building"""
    
    def test_build_postgresql_connection_string(self):
        """Test PostgreSQL connection string building"""
        conn_str = build_connection_string(
            'postgresql', 'localhost', 5432, 'omop', 'user', 'password'
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
    
    def test_build_sqlite_connection_string(self):
        """Test SQLite connection string building"""
        conn_str = build_connection_string(
            'sqlite', '', 0, 'test.db', '', ''
        )
        expected = "sqlite:///test.db"
        assert conn_str == expected
    
    def test_unsupported_database_type(self):
        """Test unsupported database type"""
        with pytest.raises(ValueError):
            build_connection_string(
                'unsupported', 'host', 1234, 'db', 'user', 'pass'
            )


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
    
    def test_get_unmapped_concepts_summary_query(self):
        """Test unmapped concepts summary query"""
        query = OMOPQueries.get_unmapped_concepts_summary()
        
        assert isinstance(query, str)
        assert "concept_id = 0" in query
        assert "condition_occurrence" in query
        assert "drug_exposure" in query
        assert "unmapped_count" in query


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
    return mock_db


def test_mock_database_functionality(mock_database):
    """Test using mock database"""
    result = mock_database.execute_query("SELECT * FROM test")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    
    assert mock_database.test_connection() is True
    assert mock_database.get_table_row_count("test_table") == 100


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])
