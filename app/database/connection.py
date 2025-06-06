import os
from typing import Optional, Dict, Any
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import streamlit as st


class OMOPDatabase:
    """Handler for OMOP database connections and queries"""
    
    def __init__(self, connection_string: str):
        """Initialize database connection"""
        self.connection_string = connection_string
        self.engine = None
        self.session_maker = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self.session_maker = sessionmaker(bind=self.engine)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(query, conn, params=params)
            return result
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            return pd.DataFrame()
    
    def get_table_list(self) -> pd.DataFrame:
        """Get list of OMOP tables in the database"""
        omop_tables = [
            'person', 'observation_period', 'visit_occurrence', 'visit_detail',
            'condition_occurrence', 'drug_exposure', 'procedure_occurrence',
            'device_exposure', 'measurement', 'observation', 'death',
            'note', 'note_nlp', 'specimen', 'fact_relationship',
            'location', 'care_site', 'provider', 'payer_plan_period',
            'cost', 'drug_era', 'dose_era', 'condition_era'
        ]
        
        query = """
        SELECT table_name, 
               COUNT(*) as row_count
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ({})
        GROUP BY table_name
        ORDER BY table_name
        """.format(','.join([f"'{table}'" for table in omop_tables]))
        
        try:
            return self.execute_query(query)
        except:
            # Fallback for databases that don't support information_schema
            return pd.DataFrame({'table_name': omop_tables, 'row_count': [0] * len(omop_tables)})
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a specific table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        try:
            result = self.execute_query(query)
            return result['count'].iloc[0] if not result.empty else 0
        except:
            return 0
    
    def test_connection(self) -> bool:
        """Test if database connection is working"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except:
            return False


@st.cache_resource
def get_database_connection(connection_string: str) -> OMOPDatabase:
    """Cached database connection"""
    return OMOPDatabase(connection_string)


def build_connection_string(db_type: str, host: str, port: int, 
                          database: str, username: str, password: str) -> str:
    """Build database connection string"""
    if db_type.lower() == 'postgresql':
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    elif db_type.lower() == 'sqlserver':
        return f"mssql+pymssql://{username}:{password}@{host}:{port}/{database}"
    elif db_type.lower() == 'sqlite':
        return f"sqlite:///{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# Configuration helpers
def load_db_config_from_env():
    """Load database configuration from environment variables"""
    return {
        'db_type': os.getenv('OMOP_DB_TYPE', 'postgresql'),
        'host': os.getenv('OMOP_DB_HOST', 'localhost'),
        'port': int(os.getenv('OMOP_DB_PORT', '5432')),
        'database': os.getenv('OMOP_DB_NAME', 'omop'),
        'username': os.getenv('OMOP_DB_USER', 'omop_user'),
        'password': os.getenv('OMOP_DB_PASSWORD', '')
    }
