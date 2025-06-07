import os
from typing import Optional, Dict, Any
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import streamlit as st
import logging


class OMOPDatabase:
    """Handler for OMOP database connections and queries"""
    
    def __init__(self, connection_string: str):
        """Initialize database connection"""
        self.connection_string = connection_string
        self.engine = None
        self.session_maker = None
        self.logger = logging.getLogger(__name__)
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            self.session_maker = sessionmaker(bind=self.engine)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            error_msg = f"Database connection failed: {str(e)}"
            self.logger.error(error_msg)
            if 'st' in globals():  # Only show streamlit error if streamlit is available
                st.error(error_msg)
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        try:
            with self.engine.connect() as conn:
                if params:
                    result = pd.read_sql(text(query), conn, params=params)
                else:
                    result = pd.read_sql(text(query), conn)
            return result
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            self.logger.error(error_msg)
            if 'st' in globals():
                st.error(error_msg)
            return pd.DataFrame()
    
    def get_table_list(self) -> pd.DataFrame:
        """Get list of OMOP tables in the database with row counts"""
        omop_tables = [
            'person', 'observation_period', 'visit_occurrence', 'visit_detail',
            'condition_occurrence', 'drug_exposure', 'procedure_occurrence',
            'device_exposure', 'measurement', 'observation', 'death',
            'note', 'note_nlp', 'specimen', 'fact_relationship',
            'location', 'care_site', 'provider', 'payer_plan_period',
            'cost', 'drug_era', 'dose_era', 'condition_era'
        ]
        
        # Try different approaches based on database type
        try:
            # First try: Check which tables actually exist and get row counts
            table_data = []
            for table in omop_tables:
                try:
                    # Check if table exists by trying to get its row count
                    count_query = f"SELECT COUNT(*) as row_count FROM {table}"
                    result = self.execute_query(count_query)
                    
                    if not result.empty:
                        row_count = result.iloc[0]['row_count']
                        table_data.append({
                            'table_name': table,
                            'row_count': row_count
                        })
                except Exception:
                    # Table doesn't exist or can't access it, skip
                    continue
            
            return pd.DataFrame(table_data)
            
        except Exception as e:
            self.logger.error(f"Error getting table list: {str(e)}")
            # Fallback: return empty DataFrame
            return pd.DataFrame(columns=['table_name', 'row_count'])
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a specific table"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.execute_query(query)
            return int(result['count'].iloc[0]) if not result.empty else 0
        except Exception as e:
            self.logger.error(f"Error getting row count for {table_name}: {str(e)}")
            return 0
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            query = f"SELECT 1 FROM {table_name} LIMIT 1"
            result = self.execute_query(query)
            return True
        except Exception:
            return False
    
    def test_connection(self) -> bool:
        """Test if database connection is working"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get basic database information"""
        try:
            # Get database version/type info
            version_queries = {
                'postgresql': "SELECT version()",
                'mysql': "SELECT version()",
                'sqlite': "SELECT sqlite_version()",
                'mssql': "SELECT @@version"
            }
            
            db_info = {
                'connection_string': self.connection_string.split('@')[1] if '@' in self.connection_string else 'Unknown',
                'engine': str(self.engine.dialect.name) if self.engine else 'Unknown',
                'tables_found': len(self.get_table_list()),
                'connection_status': self.test_connection()
            }
            
            return db_info
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {str(e)}")
            return {'error': str(e)}


@st.cache_resource
def get_database_connection(connection_string: str) -> OMOPDatabase:
    """Cached database connection"""
    return OMOPDatabase(connection_string)


def build_connection_string(db_type: str, host: str, port: int, 
                          database: str, username: str, password: str) -> str:
    """Build database connection string"""
    # Normalize database type
    db_type = db_type.lower().replace(' ', '').replace('_', '')
    
    if db_type in ['postgresql', 'postgres']:
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    elif db_type in ['sqlserver', 'mssql']:
        return f"mssql+pymssql://{username}:{password}@{host}:{port}/{database}"
    elif db_type == 'sqlite':
        return f"sqlite:///{database}"
    elif db_type == 'mysql':
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def load_db_config_from_env() -> Dict[str, Any]:
    """Load database configuration from environment variables"""
    return {
        'db_type': os.getenv('OMOP_DB_TYPE', 'postgresql'),
        'host': os.getenv('OMOP_DB_HOST', 'localhost'),
        'port': int(os.getenv('OMOP_DB_PORT', '5432')),
        'database': os.getenv('OMOP_DB_NAME', 'omop'),
        'username': os.getenv('OMOP_DB_USER', 'omop_user'),
        'password': os.getenv('OMOP_DB_PASSWORD', '')
    }


def validate_connection_params(db_type: str, host: str, port: int, 
                             database: str, username: str, password: str) -> Dict[str, Any]:
    """Validate connection parameters"""
    errors = []
    
    if not db_type:
        errors.append("Database type is required")
    
    if db_type.lower() != 'sqlite':
        if not host:
            errors.append("Host is required")
        if not database:
            errors.append("Database name is required")
        if not username:
            errors.append("Username is required")
        if port <= 0 or port > 65535:
            errors.append("Port must be between 1 and 65535")
    else:
        if not database:
            errors.append("Database file path is required for SQLite")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
