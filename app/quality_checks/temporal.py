from .base_checker import BaseQualityChecker
from ..database.queries import OMOPQueries
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any


class TemporalChecker(BaseQualityChecker):
    """Check temporal consistency and logic"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all temporal consistency checks"""
        self.results = {}
        
        # Check 1: Future dates
        self.results['future_dates'] = self._check_future_dates()
        
        # Check 2: Birth/death consistency
        self.results['birth_death_consistency'] = self._check_birth_death_consistency()
        
        # Check 3: Events after death
        self.results['events_after_death'] = self._check_events_after_death()
        
        # Check 4: Visit date consistency
        self.results['visit_date_consistency'] = self._check_visit_date_consistency()
        
        # Check 5: Age-related temporal issues
        self.results['age_temporal_issues'] = self._check_age_temporal_issues()
        
        return self.results
    
    def _check_future_dates(self) -> Dict[str, Any]:
        """Check for dates in the future"""
        try:
            query = OMOPQueries.get_future_dates_check()
            result = self.database.execute_query(query)
            
            if result.empty:
                return {
                    'status': 'PASS',
                    'total_future_dates': 0,
                    'data': [],
                    'message': 'No future dates found'
                }
            
            # Filter out records with 0 future dates
            future_data = result[result['future_count'] > 0]
            
            if future_data.empty:
                return {
                    'status': 'PASS',
                    'total_future_dates': 0,
                    'data': [],
                    'message': 'No future dates found'
                }
            
            total_future_dates = future_data['future_count'].sum()
            
            check_results = []
            for _, row in future_data.iterrows():
                future_count = row['future_count']
                check_results.append({
                    'table': row['table_name'],
                    'date_field': row['date_field'],
                    'future_count': future_count,
                    'status': 'FAIL' if future_count > 0 else 'PASS'
                })
            
            return {
                'status': 'FAIL' if total_future_dates > 0 else 'PASS',
                'total_future_dates': int(total_future_dates),
                'data': check_results,
                'message': f"Found {total_future_dates} future dates across all tables"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check future dates'
            }
    
    def _check_birth_death_consistency(self) -> Dict[str, Any]:
        """Check that death dates are after birth dates"""
        try:
            query = """
            SELECT 
                p.person_id,
                p.year_of_birth,
                p.month_of_birth,
                p.day_of_birth,
                d.death_date,
                CASE 
                    WHEN p.day_of_birth IS NOT NULL AND p.month_of_birth IS NOT NULL 
                    THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, p.day_of_birth)
                    WHEN p.month_of_birth IS NOT NULL
                    THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, 1)
                    ELSE MAKE_DATE(p.year_of_birth, 1, 1)
                END as calculated_birth_date
            FROM person p
            JOIN death d ON p.person_id = d.person_id
            WHERE p.year_of_birth IS NOT NULL 
            AND d.death_date IS NOT NULL
            AND d.death_date < 
                CASE 
                    WHEN p.day_of_birth IS NOT NULL AND p.month_of_birth IS NOT NULL 
                    THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, p.day_of_birth)
                    WHEN p.month_of_birth IS NOT NULL
                    THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, 1)
                    ELSE MAKE_DATE(p.year_of_birth, 1, 1)
                END
            """
            
            result = self.database.execute_query(query)
            inconsistent_count = len(result) if not result.empty else 0
            
            # Also check for extremely old people at death
            old_age_query = """
            SELECT 
                COUNT(*) as very_old_deaths
            FROM person p
            JOIN death d ON p.person_id = d.person_id
            WHERE p.year_of_birth IS NOT NULL 
            AND d.death_date IS NOT NULL
            AND (EXTRACT(YEAR FROM d.death_date) - p.year_of_birth) > 120
            """
            
            old_age_result = self.database.execute_query(old_age_query)
            very_old_deaths = old_age_result['very_old_deaths'].iloc[0] if not old_age_result.empty else 0
            
            total_issues = inconsistent_count + very_old_deaths
            
            return {
                'status': 'PASS' if total_issues == 0 else 'FAIL',
                'inconsistent_count': inconsistent_count,
                'very_old_deaths': int(very_old_deaths),
                'total_issues': total_issues,
                'data': result.to_dict('records') if not result.empty else [],
                'message': f"Found {inconsistent_count} deaths before birth and {very_old_deaths} very old deaths"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check birth/death consistency'
            }
    
    def _check_events_after_death(self) -> Dict[str, Any]:
        """Check for clinical events after death"""
        try:
            query = OMOPQueries.get_events_after_death()
            result = self.database.execute_query(query)
            
            if result.empty:
                return {
                    'status': 'PASS',
                    'total_events_after_death': 0,
                    'data': [],
                    'message': 'No events found after death'
                }
            
            # Filter out event types with 0 events after death
            events_data = result[result['events_after_death'] > 0]
            
            if events_data.empty:
                return {
                    'status': 'PASS',
                    'total_events_after_death': 0,
                    'data': [],
                    'message': 'No events found after death'
                }
            
            total_events_after_death = events_data['events_after_death'].sum()
            
            check_results = []
            for _, row in events_data.iterrows():
                events_count = row['events_after_death']
                check_results.append({
                    'event_type': row['event_type'],
                    'events_after_death': int(events_count),
                    'status': 'FAIL' if events_count > 0 else 'PASS'
                })
            
            return {
                'status': 'FAIL' if total_events_after_death > 0 else 'PASS',
                'total_events_after_death': int(total_events_after_death),
                'data': check_results,
                'message': f"Found {total_events_after_death} events after death"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check events after death'
            }
    
    def _check_visit_date_consistency(self) -> Dict[str, Any]:
        """Check visit start/end date consistency"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_visits,
                SUM(CASE WHEN visit_end_date < visit_start_date THEN 1 ELSE 0 END) as end_before_start,
                SUM(CASE WHEN visit_end_date - visit_start_date > 365 THEN 1 ELSE 0 END) as very_long_visits,
                SUM(CASE WHEN visit_end_date - visit_start_date < 0 THEN 1 ELSE 0 END) as negative_duration,
                AVG(CASE WHEN visit_end_date IS NOT NULL THEN visit_end_date - visit_start_date ELSE NULL END) as avg_duration
            FROM visit_occurrence
            WHERE visit_start_date IS NOT NULL
            """
            
            result = self.database.execute_query(query)
            
            if result.empty:
                return {
                    'status': 'ERROR',
                    'message': 'No visit data found'
                }
            
            data = result.iloc[0].to_dict()
            
            # Count total issues
            total_issues = (
                data['end_before_start'] + 
                data['negative_duration']
            )
            
            # Warnings for very long visits (might be valid)
            warnings = data['very_long_visits']
            
            # Determine status
            if total_issues == 0 and warnings == 0:
                status = 'PASS'
            elif total_issues == 0 and warnings > 0:
                status = 'WARNING'
            else:
                status = 'FAIL'
            
            return {
                'status': status,
                'total_issues': int(total_issues),
                'warnings': int(warnings),
                'data': {
                    'total_visits': int(data['total_visits']),
                    'end_before_start': int(data['end_before_start']),
                    'very_long_visits': int(data['very_long_visits']),
                    'negative_duration': int(data['negative_duration']),
                    'avg_duration': float(data['avg_duration']) if data['avg_duration'] else 0
                },
                'message': f"Found {total_issues} visit date issues and {warnings} very long visits"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check visit date consistency'
            }
    
    def _check_age_temporal_issues(self) -> Dict[str, Any]:
        """Check for age-related temporal inconsistencies"""
        try:
            # Check for events before birth
            events_before_birth_query = """
            WITH birth_dates AS (
                SELECT 
                    person_id,
                    CASE 
                        WHEN day_of_birth IS NOT NULL AND month_of_birth IS NOT NULL 
                        THEN MAKE_DATE(year_of_birth, month_of_birth, day_of_birth)
                        WHEN month_of_birth IS NOT NULL
                        THEN MAKE_DATE(year_of_birth, month_of_birth, 1)
                        ELSE MAKE_DATE(year_of_birth, 1, 1)
                    END as birth_date
                FROM person
                WHERE year_of_birth IS NOT NULL
            )
            SELECT 
                'Conditions before birth' as issue_type,
                COUNT(*) as issue_count
            FROM condition_occurrence co
            JOIN birth_dates bd ON co.person_id = bd.person_id
            WHERE co.condition_start_date < bd.birth_date
            
            UNION ALL
            
            SELECT 
                'Drugs before birth' as issue_type,
                COUNT(*) as issue_count
            FROM drug_exposure de
            JOIN birth_dates bd ON de.person_id = bd.person_id
            WHERE de.drug_exposure_start_date < bd.birth_date
            
            UNION ALL
            
            SELECT 
                'Visits before birth' as issue_type,
                COUNT(*) as issue_count
            FROM visit_occurrence vo
            JOIN birth_dates bd ON vo.person_id = bd.person_id
            WHERE vo.visit_start_date < bd.birth_date
            """
            
            result = self.database.execute_query(events_before_birth_query)
            
            if result.empty:
                return {
                    'status': 'PASS',
                    'total_issues': 0,
                    'data': [],
                    'message': 'No age-related temporal issues found'
                }
            
            # Filter out issues with 0 count
            issues_data = result[result['issue_count'] > 0]
            
            if issues_data.empty:
                return {
                    'status': 'PASS',
                    'total_issues': 0,
                    'data': [],
                    'message': 'No age-related temporal issues found'
                }
            
            total_issues = issues_data['issue_count'].sum()
            
            check_results = []
            for _, row in issues_data.iterrows():
                issue_count = row['issue_count']
                check_results.append({
                    'issue_type': row['issue_type'],
                    'issue_count': int(issue_count),
                    'status': 'FAIL' if issue_count > 0 else 'PASS'
                })
            
            return {
                'status': 'FAIL' if total_issues > 0 else 'PASS',
                'total_issues': int(total_issues),
                'data': check_results,
                'message': f"Found {total_issues} age-related temporal issues"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check age-related temporal issues'
            }
