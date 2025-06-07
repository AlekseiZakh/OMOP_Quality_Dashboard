import sys
import os
from typing import Dict, List, Any, Optional
from datetime import date

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from .base_checker import BaseQualityChecker
except ImportError:
    from base_checker import BaseQualityChecker


class TemporalChecker(BaseQualityChecker):
    """Check temporal consistency and logic"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all temporal consistency checks"""
        self.results = {}
        
        # Validate database connection first
        if not self.validate_database_connection():
            return {
                'error': 'Database connection failed',
                'status': 'ERROR'
            }
        
        # Check 1: Future dates
        self.log_check_start("future_dates")
        self.results['future_dates'] = self._check_future_dates()
        self.log_check_complete("future_dates", self.results['future_dates'].get('status', 'UNKNOWN'))
        
        # Check 2: Birth/death consistency
        self.log_check_start("birth_death_consistency")
        self.results['birth_death_consistency'] = self._check_birth_death_consistency()
        self.log_check_complete("birth_death_consistency", self.results['birth_death_consistency'].get('status', 'UNKNOWN'))
        
        # Check 3: Events after death
        self.log_check_start("events_after_death")
        self.results['events_after_death'] = self._check_events_after_death()
        self.log_check_complete("events_after_death", self.results['events_after_death'].get('status', 'UNKNOWN'))
        
        return self.results
    
    def _check_future_dates(self) -> Dict[str, Any]:
        """Check for dates in the future"""
        try:
            future_date_checks = [
                {
                    'table': 'condition_occurrence',
                    'date_field': 'condition_start_date',
                    'query': "SELECT COUNT(*) as future_count FROM condition_occurrence WHERE condition_start_date > CURRENT_DATE"
                },
                {
                    'table': 'drug_exposure',
                    'date_field': 'drug_exposure_start_date',
                    'query': "SELECT COUNT(*) as future_count FROM drug_exposure WHERE drug_exposure_start_date > CURRENT_DATE"
                },
                {
                    'table': 'procedure_occurrence',
                    'date_field': 'procedure_date',
                    'query': "SELECT COUNT(*) as future_count FROM procedure_occurrence WHERE procedure_date > CURRENT_DATE"
                },
                {
                    'table': 'measurement',
                    'date_field': 'measurement_date',
                    'query': "SELECT COUNT(*) as future_count FROM measurement WHERE measurement_date > CURRENT_DATE"
                },
                {
                    'table': 'visit_occurrence',
                    'date_field': 'visit_start_date',
                    'query': "SELECT COUNT(*) as future_count FROM visit_occurrence WHERE visit_start_date > CURRENT_DATE"
                }
            ]
            
            check_results = []
            total_future_dates = 0
            
            for check in future_date_checks:
                # Skip check if table doesn't exist
                if not self.table_exists(check['table']):
                    continue
                    
                try:
                    result = self.database.execute_query(check['query'])
                    if not result.empty:
                        future_count = result['future_count'].iloc[0]
                        total_future_dates += future_count
                        status = 'PASS' if future_count == 0 else 'FAIL'
                        
                        check_results.append({
                            'table': check['table'],
                            'date_field': check['date_field'],
                            'future_count': future_count,
                            'status': status
                        })
                except Exception as e:
                    self.logger.error(f"Error checking future dates in {check['table']}: {str(e)}")
                    check_results.append({
                        'table': check['table'],
                        'date_field': check['date_field'],
                        'future_count': 'ERROR',
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            overall_status = 'PASS' if total_future_dates == 0 else 'FAIL'
            if any(r['status'] == 'ERROR' for r in check_results):
                overall_status = 'ERROR'
            
            return {
                'status': overall_status,
                'total_future_dates': total_future_dates,
                'data': check_results,
                'message': f"Found {total_future_dates} future dates across all tables"
            }
            
        except Exception as e:
            return self.handle_error("future_dates", e)
    
    def _check_birth_death_consistency(self) -> Dict[str, Any]:
        """Check that death dates are after birth dates"""
        # Check if both tables exist
        if not (self.table_exists('person') and self.table_exists('death')):
            return {
                'status': 'WARNING',
                'inconsistent_count': 0,
                'message': 'Person or death table not found - skipping check'
            }
        
        query = """
        SELECT COUNT(*) as inconsistent_count
        FROM person p
        JOIN death d ON p.person_id = d.person_id
        WHERE d.death_date < 
              CASE 
                  WHEN p.day_of_birth IS NOT NULL AND p.month_of_birth IS NOT NULL 
                  THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, p.day_of_birth)
                  WHEN p.month_of_birth IS NOT NULL 
                  THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, 1)
                  ELSE MAKE_DATE(p.year_of_birth, 1, 1)
              END
        """
        
        try:
            result = self.database.execute_query(query)
            if not result.empty:
                inconsistent_count = result['inconsistent_count'].iloc[0]
                status = 'PASS' if inconsistent_count == 0 else 'FAIL'
                
                return {
                    'status': status,
                    'inconsistent_count': inconsistent_count,
                    'message': f"Found {inconsistent_count} deaths before birth"
                }
            else:
                return {
                    'status': 'ERROR',
                    'message': 'No data returned from birth/death consistency check'
                }
                
        except Exception as e:
            return self.handle_error("birth_death_consistency", e)
    
    def _check_events_after_death(self) -> Dict[str, Any]:
        """Check for clinical events after death"""
        # Check if death table exists
        if not self.table_exists('death'):
            return {
                'status': 'WARNING',
                'total_events_after_death': 0,
                'data': [],
                'message': 'Death table not found - skipping check'
            }
        
        events_after_death_queries = [
            {
                'event_type': 'condition_occurrence',
                'query': """
                SELECT COUNT(*) as events_after_death
                FROM condition_occurrence co
                JOIN death d ON co.person_id = d.person_id
                WHERE co.condition_start_date > d.death_date
                """,
                'table': 'condition_occurrence'
            },
            {
                'event_type': 'drug_exposure',
                'query': """
                SELECT COUNT(*) as events_after_death
                FROM drug_exposure de
                JOIN death d ON de.person_id = d.person_id
                WHERE de.drug_exposure_start_date > d.death_date
                """,
                'table': 'drug_exposure'
            },
            {
                'event_type': 'procedure_occurrence',
                'query': """
                SELECT COUNT(*) as events_after_death
                FROM procedure_occurrence po
                JOIN death d ON po.person_id = d.person_id
                WHERE po.procedure_date > d.death_date
                """,
                'table': 'procedure_occurrence'
            },
            {
                'event_type': 'measurement',
                'query': """
                SELECT COUNT(*) as events_after_death
                FROM measurement m
                JOIN death d ON m.person_id = d.person_id
                WHERE m.measurement_date > d.death_date
                """,
                'table': 'measurement'
            }
        ]
        
        try:
            check_results = []
            total_events_after_death = 0
            
            for check in events_after_death_queries:
                # Skip check if table doesn't exist
                if not self.table_exists(check['table']):
                    continue
                    
                try:
                    result = self.database.execute_query(check['query'])
                    if not result.empty:
                        events_count = result['events_after_death'].iloc[0]
                        total_events_after_death += events_count
                        status = 'PASS' if events_count == 0 else 'FAIL'
                        
                        check_results.append({
                            'event_type': check['event_type'],
                            'events_after_death': events_count,
                            'status': status
                        })
                except Exception as e:
                    self.logger.error(f"Error checking events after death for {check['event_type']}: {str(e)}")
                    check_results.append({
                        'event_type': check['event_type'],
                        'events_after_death': 'ERROR',
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            overall_status = 'PASS' if total_events_after_death == 0 else 'FAIL'
            if any(r['status'] == 'ERROR' for r in check_results):
                overall_status = 'ERROR'
            
            return {
                'status': overall_status,
                'total_events_after_death': total_events_after_death,
                'data': check_results,
                'message': f"Found {total_events_after_death} events after death"
            }
            
        except Exception as e:
            return self.handle_error("events_after_death", e)
