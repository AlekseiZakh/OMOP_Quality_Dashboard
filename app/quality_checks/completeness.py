import sys
import os
from typing import Dict, List, Any, Optional

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from .base_checker import BaseQualityChecker
except ImportError:
    from base_checker import BaseQualityChecker


class CompletenessChecker(BaseQualityChecker):
    """Check data completeness across OMOP tables"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all completeness checks"""
        self.results = {}
        
        # Validate database connection first
        if not self.validate_database_connection():
            return {
                'error': 'Database connection failed',
                'status': 'ERROR'
            }
        
        # Check 1: Overall table completeness
        self.log_check_start("table_completeness")
        self.results['table_completeness'] = self._check_table_completeness()
        self.log_check_complete("table_completeness", self.results['table_completeness'].get('status', 'UNKNOWN'))
        
        # Check 2: Critical field completeness
        self.log_check_start("critical_fields")
        self.results['critical_fields'] = self._check_critical_fields()
        self.log_check_complete("critical_fields", self.results['critical_fields'].get('status', 'UNKNOWN'))
        
        # Check 3: Person table completeness
        self.log_check_start("person_completeness")
        self.results['person_completeness'] = self._check_person_completeness()
        self.log_check_complete("person_completeness", self.results['person_completeness'].get('status', 'UNKNOWN'))
        
        return self.results
    
    def _check_table_completeness(self) -> Dict[str, Any]:
        """Check completeness of main OMOP tables"""
        try:
            tables = self.database.get_table_list()
            
            if tables.empty:
                return {
                    'status': 'WARNING',
                    'data': [],
                    'message': 'No OMOP tables found'
                }
            
            completeness_data = []
            for _, row in tables.iterrows():
                table_name = row['table_name']
                total_rows = row['row_count']
                
                if total_rows > 0:
                    # Calculate null percentage for key fields
                    null_check_query = self._get_null_check_query(table_name)
                    if null_check_query:
                        try:
                            null_results = self.database.execute_query(null_check_query)
                            if not null_results.empty:
                                null_percentage = null_results['null_percentage'].iloc[0]
                                status = 'PASS' if null_percentage < 10 else ('WARNING' if null_percentage < 25 else 'FAIL')
                                
                                completeness_data.append({
                                    'table_name': table_name,
                                    'total_rows': total_rows,
                                    'null_percentage': null_percentage,
                                    'status': status
                                })
                        except Exception as e:
                            self.logger.error(f"Error checking completeness for {table_name}: {str(e)}")
                            completeness_data.append({
                                'table_name': table_name,
                                'total_rows': total_rows,
                                'null_percentage': 'ERROR',
                                'status': 'ERROR',
                                'error': str(e)
                            })
            
            overall_status = 'PASS'
            if any(d['status'] == 'FAIL' for d in completeness_data):
                overall_status = 'FAIL'
            elif any(d['status'] == 'WARNING' for d in completeness_data):
                overall_status = 'WARNING'
            
            return {
                'status': overall_status,
                'data': completeness_data,
                'message': f"Checked completeness for {len(completeness_data)} tables"
            }
            
        except Exception as e:
            return self.handle_error("table_completeness", e)
    
    def _get_null_check_query(self, table_name: str) -> Optional[str]:
        """Get appropriate null check query for each table"""
        key_fields = {
            'person': ['person_id', 'gender_concept_id', 'year_of_birth'],
            'condition_occurrence': ['person_id', 'condition_concept_id', 'condition_start_date'],
            'drug_exposure': ['person_id', 'drug_concept_id', 'drug_exposure_start_date'],
            'procedure_occurrence': ['person_id', 'procedure_concept_id', 'procedure_date'],
            'measurement': ['person_id', 'measurement_concept_id', 'measurement_date'],
            'visit_occurrence': ['person_id', 'visit_concept_id', 'visit_start_date'],
            'observation': ['person_id', 'observation_concept_id', 'observation_date'],
            'death': ['person_id', 'death_date']
        }
        
        if table_name not in key_fields:
            return None
        
        fields = key_fields[table_name]
        null_conditions = [f"{field} IS NULL" for field in fields]
        
        return f"""
        SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND(
                    (SUM(CASE WHEN {' OR '.join(null_conditions)} THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
                    2
                )
            END as null_percentage
        FROM {table_name}
        """
    
    def _check_critical_fields(self) -> Dict[str, Any]:
        """Check completeness of critical fields that should never be null"""
        critical_checks = [
            {
                'name': 'Person IDs in condition_occurrence',
                'query': 'SELECT COUNT(*) as null_count FROM condition_occurrence WHERE person_id IS NULL',
                'threshold': 0,
                'table': 'condition_occurrence'
            },
            {
                'name': 'Concept IDs in condition_occurrence',
                'query': 'SELECT COUNT(*) as null_count FROM condition_occurrence WHERE condition_concept_id IS NULL',
                'threshold': 0,
                'table': 'condition_occurrence'
            },
            {
                'name': 'Person IDs in drug_exposure',
                'query': 'SELECT COUNT(*) as null_count FROM drug_exposure WHERE person_id IS NULL',
                'threshold': 0,
                'table': 'drug_exposure'
            },
            {
                'name': 'Start dates in drug_exposure',
                'query': 'SELECT COUNT(*) as null_count FROM drug_exposure WHERE drug_exposure_start_date IS NULL',
                'threshold': 0,
                'table': 'drug_exposure'
            }
        ]
        
        check_results = []
        for check in critical_checks:
            # Skip check if table doesn't exist
            if not self.table_exists(check['table']):
                continue
                
            try:
                result = self.database.execute_query(check['query'])
                if not result.empty:
                    null_count = result['null_count'].iloc[0]
                    status = 'PASS' if null_count <= check['threshold'] else 'FAIL'
                    check_results.append({
                        'check_name': check['name'],
                        'null_count': null_count,
                        'threshold': check['threshold'],
                        'status': status
                    })
            except Exception as e:
                check_results.append({
                    'check_name': check['name'],
                    'null_count': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        overall_status = 'PASS'
        if any(r['status'] == 'FAIL' for r in check_results):
            overall_status = 'FAIL'
        elif any(r['status'] == 'ERROR' for r in check_results):
            overall_status = 'ERROR'
        
        return {
            'status': overall_status,
            'data': check_results,
            'message': f"Checked {len(check_results)} critical fields"
        }
    
    def _check_person_completeness(self) -> Dict[str, Any]:
        """Check completeness of person table specifically"""
        if not self.table_exists('person'):
            return {
                'status': 'ERROR',
                'message': 'Person table not found',
                'completeness_score': 0
            }
        
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
                
                if total == 0:
                    return {
                        'status': 'ERROR',
                        'message': 'No persons found in person table',
                        'completeness_score': 0,
                        'data': data
                    }
                
                # Calculate completeness score based on critical fields
                missing_critical = data['missing_gender'] + data['missing_birth_year']
                completeness_score = max(0, 100 - (missing_critical * 100 / total / 2))
                
                status = 'PASS' if completeness_score >= 90 else ('WARNING' if completeness_score >= 75 else 'FAIL')
                
                return {
                    'status': status,
                    'completeness_score': round(completeness_score, 2),
                    'data': data,
                    'message': f"Person table completeness: {completeness_score:.1f}%"
                }
            else:
                return {
                    'status': 'ERROR',
                    'message': 'No data returned from person table query',
                    'completeness_score': 0
                }
                
        except Exception as e:
            return self.handle_error("person_completeness", e)
