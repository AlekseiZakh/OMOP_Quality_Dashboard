from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, date
import streamlit as st


class BaseQualityChecker(ABC):
    """Base class for all quality checkers"""
    
    def __init__(self, database):
        self.database = database
        self.results = {}
    
    @abstractmethod
    def run_checks(self) -> Dict[str, Any]:
        """Run quality checks and return results"""
        pass
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of quality check results"""
        return {
            'total_checks': len(self.results),
            'passed_checks': sum(1 for r in self.results.values() if r.get('status') == 'PASS'),
            'failed_checks': sum(1 for r in self.results.values() if r.get('status') == 'FAIL'),
            'warning_checks': sum(1 for r in self.results.values() if r.get('status') == 'WARNING')
        }


# app/quality_checks/completeness.py
"""Data completeness quality checks"""

class CompletenessChecker(BaseQualityChecker):
    """Check data completeness across OMOP tables"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all completeness checks"""
        self.results = {}
        
        # Check 1: Overall table completeness
        self.results['table_completeness'] = self._check_table_completeness()
        
        # Check 2: Critical field completeness
        self.results['critical_fields'] = self._check_critical_fields()
        
        # Check 3: Person table completeness
        self.results['person_completeness'] = self._check_person_completeness()
        
        return self.results
    
    def _check_table_completeness(self) -> Dict[str, Any]:
        """Check completeness of main OMOP tables"""
        tables = self.database.get_table_list()
        
        completeness_data = []
        for _, row in tables.iterrows():
            table_name = row['table_name']
            total_rows = row['row_count']
            
            if total_rows > 0:
                # Calculate null percentage for key fields
                null_check_query = self._get_null_check_query(table_name)
                if null_check_query:
                    null_results = self.database.execute_query(null_check_query)
                    if not null_results.empty:
                        completeness_data.append({
                            'table_name': table_name,
                            'total_rows': total_rows,
                            'null_percentage': null_results['null_percentage'].iloc[0],
                            'status': 'PASS' if null_results['null_percentage'].iloc[0] < 10 else 'WARNING'
                        })
        
        return {
            'status': 'PASS' if all(d['status'] == 'PASS' for d in completeness_data) else 'WARNING',
            'data': completeness_data,
            'message': f"Checked completeness for {len(completeness_data)} tables"
        }
    
    def _get_null_check_query(self, table_name: str) -> Optional[str]:
        """Get appropriate null check query for each table"""
        key_fields = {
            'person': ['person_id', 'gender_concept_id', 'year_of_birth'],
            'condition_occurrence': ['person_id', 'condition_concept_id', 'condition_start_date'],
            'drug_exposure': ['person_id', 'drug_concept_id', 'drug_exposure_start_date'],
            'procedure_occurrence': ['person_id', 'procedure_concept_id', 'procedure_date'],
            'measurement': ['person_id', 'measurement_concept_id', 'measurement_date'],
            'visit_occurrence': ['person_id', 'visit_concept_id', 'visit_start_date']
        }
        
        if table_name not in key_fields:
            return None
        
        fields = key_fields[table_name]
        null_conditions = [f"{field} IS NULL" for field in fields]
        
        return f"""
        SELECT 
            ROUND(
                (SUM(CASE WHEN {' OR '.join(null_conditions)} THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
                2
            ) as null_percentage
        FROM {table_name}
        """
    
    def _check_critical_fields(self) -> Dict[str, Any]:
        """Check completeness of critical fields that should never be null"""
        critical_checks = [
            {
                'name': 'Person IDs in condition_occurrence',
                'query': 'SELECT COUNT(*) as null_count FROM condition_occurrence WHERE person_id IS NULL',
                'threshold': 0
            },
            {
                'name': 'Concept IDs in condition_occurrence',
                'query': 'SELECT COUNT(*) as null_count FROM condition_occurrence WHERE condition_concept_id IS NULL',
                'threshold': 0
            },
            {
                'name': 'Start dates in drug_exposure',
                'query': 'SELECT COUNT(*) as null_count FROM drug_exposure WHERE drug_exposure_start_date IS NULL',
                'threshold': 0
            }
        ]
        
        check_results = []
        for check in critical_checks:
            try:
                result = self.database.execute_query(check['query'])
                if not result.empty:
                    null_count = result['null_count'].iloc[0]
                    status = 'PASS' if null_count <= check['threshold'] else 'FAIL'
                    check_results.append({
                        'check_name': check['name'],
                        'null_count': null_count,
                        'status': status
                    })
            except Exception as e:
                check_results.append({
                    'check_name': check['name'],
                    'null_count': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        return {
            'status': 'PASS' if all(r['status'] == 'PASS' for r in check_results) else 'FAIL',
            'data': check_results,
            'message': f"Checked {len(check_results)} critical fields"
        }
    
    def _check_person_completeness(self) -> Dict[str, Any]:
        """Check completeness of person table specifically"""
        query = """
        SELECT 
            COUNT(*) as total_persons,
            SUM(CASE WHEN gender_concept_id IS NULL THEN 1 ELSE 0 END) as missing_gender,
            SUM(CASE WHEN year_of_birth IS NULL THEN 1 ELSE 0 END) as missing_birth_year,
            SUM(CASE WHEN race_concept_id IS NULL THEN 1 ELSE 0 END) as missing_race,
            SUM(CASE WHEN ethnicity_concept_id IS NULL THEN 1 ELSE 0 END) as missing_ethnicity
        FROM person
        """
        
        try:
            result = self.database.execute_query(query)
            if not result.empty:
                data = result.iloc[0].to_dict()
                total = data['total_persons']
                
                completeness_score = 100 - (
                    (data['missing_gender'] + data['missing_birth_year']) * 100 / total / 2
                ) if total > 0 else 0
                
                return {
                    'status': 'PASS' if completeness_score >= 90 else 'WARNING',
                    'completeness_score': round(completeness_score, 2),
                    'data': data,
                    'message': f"Person table completeness: {completeness_score:.1f}%"
                }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check person table completeness'
            }


# app/quality_checks/temporal.py
"""Temporal consistency quality checks"""

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
        
        return self.results
    
    def _check_future_dates(self) -> Dict[str, Any]:
        """Check for dates in the future"""
        current_date = date.today().strftime('%Y-%m-%d')
        
        future_date_checks = [
            {
                'table': 'condition_occurrence',
                'date_field': 'condition_start_date',
                'query': f"SELECT COUNT(*) as future_count FROM condition_occurrence WHERE condition_start_date > '{current_date}'"
            },
            {
                'table': 'drug_exposure',
                'date_field': 'drug_exposure_start_date',
                'query': f"SELECT COUNT(*) as future_count FROM drug_exposure WHERE drug_exposure_start_date > '{current_date}'"
            },
            {
                'table': 'procedure_occurrence',
                'date_field': 'procedure_date',
                'query': f"SELECT COUNT(*) as future_count FROM procedure_occurrence WHERE procedure_date > '{current_date}'"
            }
        ]
        
        check_results = []
        total_future_dates = 0
        
        for check in future_date_checks:
            try:
                result = self.database.execute_query(check['query'])
                if not result.empty:
                    future_count = result['future_count'].iloc[0]
                    total_future_dates += future_count
                    check_results.append({
                        'table': check['table'],
                        'date_field': check['date_field'],
                        'future_count': future_count,
                        'status': 'PASS' if future_count == 0 else 'FAIL'
                    })
            except Exception as e:
                check_results.append({
                    'table': check['table'],
                    'date_field': check['date_field'],
                    'future_count': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        return {
            'status': 'PASS' if total_future_dates == 0 else 'FAIL',
            'total_future_dates': total_future_dates,
            'data': check_results,
            'message': f"Found {total_future_dates} future dates across all tables"
        }
    
    def _check_birth_death_consistency(self) -> Dict[str, Any]:
        """Check that death dates are after birth dates"""
        query = """
        SELECT COUNT(*) as inconsistent_count
        FROM person p
        JOIN death d ON p.person_id = d.person_id
        WHERE d.death_date < 
              CASE 
                  WHEN p.day_of_birth IS NOT NULL AND p.month_of_birth IS NOT NULL 
                  THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, p.day_of_birth)
                  ELSE MAKE_DATE(p.year_of_birth, 1, 1)
              END
        """
        
        try:
            result = self.database.execute_query(query)
            if not result.empty:
                inconsistent_count = result['inconsistent_count'].iloc[0]
                return {
                    'status': 'PASS' if inconsistent_count == 0 else 'FAIL',
                    'inconsistent_count': inconsistent_count,
                    'message': f"Found {inconsistent_count} deaths before birth"
                }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check birth/death consistency'
            }
    
    def _check_events_after_death(self) -> Dict[str, Any]:
        """Check for clinical events after death"""
        events_after_death_queries = [
            {
                'event_type': 'Conditions',
                'query': """
                SELECT COUNT(*) as events_after_death
                FROM condition_occurrence co
                JOIN death d ON co.person_id = d.person_id
                WHERE co.condition_start_date > d.death_date
                """
            },
            {
                'event_type': 'Drug exposures',
                'query': """
                SELECT COUNT(*) as events_after_death
                FROM drug_exposure de
                JOIN death d ON de.person_id = d.person_id
                WHERE de.drug_exposure_start_date > d.death_date
                """
            }
        ]
        
        check_results = []
        total_events_after_death = 0
        
        for check in events_after_death_queries:
            try:
                result = self.database.execute_query(check['query'])
                if not result.empty:
                    events_count = result['events_after_death'].iloc[0]
                    total_events_after_death += events_count
                    check_results.append({
                        'event_type': check['event_type'],
                        'events_after_death': events_count,
                        'status': 'PASS' if events_count == 0 else 'FAIL'
                    })
            except Exception as e:
                check_results.append({
                    'event_type': check['event_type'],
                    'events_after_death': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        return {
            'status': 'PASS' if total_events_after_death == 0 else 'FAIL',
            'total_events_after_death': total_events_after_death,
            'data': check_results,
            'message': f"Found {total_events_after_death} events after death"
        }
