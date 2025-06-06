__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "Comprehensive data quality monitoring dashboard for OMOP Common Data Model"

# Import main components for easy access
from .database.connection import OMOPDatabase
from .quality_checks import QUALITY_CHECKERS

__all__ = [
    'OMOPDatabase',
    'QUALITY_CHECKERS'
]

