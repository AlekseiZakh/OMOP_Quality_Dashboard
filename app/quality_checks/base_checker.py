from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, date
import logging


class BaseQualityChecker(ABC):
    """Base class for all quality checkers"""
    
    def __init__(self, database):
        self.database = database
        self.results = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def run_checks(self) -> Dict[str, Any]:
        """Run quality checks and return results"""
        pass
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of quality check results"""
        if not self.results:
            return {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warning_checks': 0
            }
        
        # Handle nested results structure
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        warning_checks = 0
        
        for result_key, result_data in self.results.items():
            if isinstance(result_data, dict):
                status = result_data.get('status', 'UNKNOWN')
                total_checks += 1
                
                if status == 'PASS':
                    passed_checks += 1
                elif status == 'FAIL' or status == 'ERROR':
                    failed_checks += 1
                elif status == 'WARNING':
                    warning_checks += 1
                
                # Handle nested data arrays
                if 'data' in result_data and isinstance(result_data['data'], list):
                    for item in result_data['data']:
                        if isinstance(item, dict) and 'status' in item:
                            item_status = item['status']
                            total_checks += 1
                            
                            if item_status == 'PASS':
                                passed_checks += 1
                            elif item_status == 'FAIL' or item_status == 'ERROR':
                                failed_checks += 1
                            elif item_status == 'WARNING':
                                warning_checks += 1
        
        return {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'warning_checks': warning_checks
        }
    
    def log_check_start(self, check_name: str):
        """Log the start of a quality check"""
        self.logger.info(f"Starting check: {check_name}")
    
    def log_check_complete(self, check_name: str, status: str):
        """Log the completion of a quality check"""
        self.logger.info(f"Completed check: {check_name} - Status: {status}")
    
    def handle_error(self, check_name: str, error: Exception) -> Dict[str, Any]:
        """Handle errors during checks"""
        error_msg = f"Error in {check_name}: {str(error)}"
        self.logger.error(error_msg)
        
        return {
            'status': 'ERROR',
            'error': str(error),
            'message': error_msg
        }
    
    def validate_database_connection(self) -> bool:
        """Validate that database connection is working"""
        try:
            return self.database.test_connection()
        except Exception as e:
            self.logger.error(f"Database connection validation failed: {str(e)}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            return self.database.table_exists(table_name)
        except Exception as e:
            self.logger.error(f"Error checking if table {table_name} exists: {str(e)}")
            return False
