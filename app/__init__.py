
__version__ = "1.0.0"
__author__ = "Aleksei Zakharov"
__email__ = "aleksey.zajarov@gmail.com"
__description__ = "Comprehensive data quality monitoring dashboard for OMOP Common Data Model"

# Import main components for easy access
try:
    from .database.connection import OMOPDatabase, build_connection_string
    from .database.queries import OMOPQueries
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from database.connection import OMOPDatabase, build_connection_string
    from database.queries import OMOPQueries

__all__ = [
    'OMOPDatabase',
    'build_connection_string',
    'OMOPQueries'
]

