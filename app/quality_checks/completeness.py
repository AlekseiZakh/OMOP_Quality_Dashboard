from .base_checker import BaseQualityChecker
from ..database.queries import OMOPQueries
import pandas as pd
from typing import Dict, List, Any, Optional


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
        
        # Check 4: Domain-specific completeness
        self.results['domain_completeness'] = self._check_domain_completeness()
        
        return self.results
    
    def _check_table_completeness(self) -> Dict[str, Any]:
        """Check completeness of main OMOP tables"""
        try:
            # Get basic table information
            tables_query = OMOPQueries.get_table_row_counts()
            tables_df = self.database.execute_query(tables_query)
            
            if tables_df.empty:
                return {
                    'status': 'ERROR',
                    'message': 'No table data found',
                    'data': []
                }
            
            completeness_data = []
            
            # Define key fields for each table to check for null values
            table_key_fields = {
                'person': ['person_id', 'gender_concept_id', 'year_of_birth'],
                'condition_occurrence': ['person_id', 'condition_concept_id', 'condition_start_date'],
                'drug_exposure': ['person_id', 'drug_concept_id', 'drug_exposure_start_date'],
                'procedure_occurrence': ['person_id', 'procedure_concept_id', 'procedure_date'],
                'measurement': ['person_id', 'measurement_concept_id', 'measurement_date'],
                'visit_occurrence': ['person_id', 'visit_concept_id', 'visit_start_date'],
                'observation': ['person_id', 'observation_concept_id', 'observation_date'],
                'death': ['person_id', 'death_date']
            }
            
            for _, row in tables_df.iterrows():
                table_name = row['table_name']
                total_rows = row['row_count']
                
                if total_rows > 0 and table_name in table_key_fields:
                    # Check null percentage for key fields
                    null_query = OMOPQueries.get_completeness_check(
                        table_name, 
                        table_key_fields[table_name]
                    )
                    
                    try:
                        null_results = self.database.execute_query(null_query)
                        if not null_results.empty:
                            null_percentage = null_results['null_percentage'].iloc[0]
                            
                            # Determine status based on null percentage
                            if null_percentage == 0:
                                status = 'PASS'
                            elif null_percentage < 5:
                                status = 'WARNING'
                            else:
                                status = 'FAIL'
                            
                            completeness_data.append({
                                'table_name': table_name,
                                'total_rows': total_rows,
                                'null_percentage': null_percentage,
                                'status': status,
                                'key_fields': ', '.join(table_key_fields[table_name])
                            })
                    except Exception as e:
                        completeness_data.append({
                            'table_name': table_name,
                            'total_rows': total_rows,
                            'null_percentage': 'ERROR',
                            'status': 'ERROR',
                            'error': str(e)
                        })
            
            # Overall status
            if not completeness_data:
                overall_status = 'WARNING'
            elif all(d['status'] == 'PASS' for d in completeness_data):
                overall_status = 'PASS'
            elif any(d['status'] == 'FAIL' for d in completeness_data):
                overall_status = 'FAIL'
            else:
                overall_status = 'WARNING'
            
            return {
                'status': overall_status,
                'data': completeness_data,
                'message': f"Checked completeness for {len(completeness_data)} tables"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check table completeness'
            }
    
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
            },
            {
                'name': 'Person IDs in visit_occurrence',
                'query': 'SELECT COUNT(*) as null_count FROM visit_occurrence WHERE person_id IS NULL',
                'threshold': 0
            },
            {
                'name': 'Visit concept IDs in visit_occurrence',
                'query': 'SELECT COUNT(*) as null_count FROM visit_occurrence WHERE visit_concept_id IS NULL',
                'threshold': 0
            }
        ]
        
        check_results = []
        total_failures = 0
        
        for check in critical_checks:
            try:
                result = self.database.execute_query(check['query'])
                if not result.empty:
                    null_count = result['null_count'].iloc[0]
                    status = 'PASS' if null_count <= check['threshold'] else 'FAIL'
                    
                    if status == 'FAIL':
                        total_failures += null_count
                    
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
                    'threshold': check['threshold'],
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        overall_status = 'PASS' if total_failures == 0 else 'FAIL'
        
        return {
            'status': overall_status,
            'total_failures': total_failures,
            'data': check_results,
            'message': f"Found {total_failures} critical field violations"
        }
    
    def _check_person_completeness(self) -> Dict[str, Any]:
        """Check completeness of person table specifically"""
        try:
            query = OMOPQueries.get_person_demographics_quality()
            result = self.database.execute_query(query)
            
            if result.empty:
                return {
                    'status': 'ERROR',
                    'message': 'No person data found'
                }
            
            data = result.iloc[0].to_dict()
            total_persons = data['total_persons']
            
            if total_persons == 0:
                return {
                    'status': 'ERROR',
                    'message': 'No persons in person table'
                }
            
            # Calculate completeness scores
            completeness_score = data.get('completeness_score', 0)
            
            # Individual field completeness percentages
            gender_completeness = 100 - (data['missing_gender'] * 100 / total_persons)
            birth_year_completeness = 100 - (data['missing_birth_year'] * 100 / total_persons)
            race_completeness = 100 - (data['missing_race'] * 100 / total_persons)
            ethnicity_completeness = 100 - (data['missing_ethnicity'] * 100 / total_persons)
            
            # Quality issues
            quality_issues = []
            if data['invalid_birth_year_low'] > 0:
                quality_issues.append(f"{data['invalid_birth_year_low']} persons with birth year < 1900")
            if data['invalid_birth_year_high'] > 0:
                quality_issues.append(f"{data['invalid_birth_year_high']} persons with future birth year")
            if data['unrealistic_age'] > 0:
                quality_issues.append(f"{data['unrealistic_age']} persons with age > 120")
            
            # Determine status
            if completeness_score >= 95 and len(quality_issues) == 0:
                status = 'PASS'
            elif completeness_score >= 85:
                status = 'WARNING'
            else:
                status = 'FAIL'
            
            return {
                'status': status,
                'completeness_score': round(completeness_score, 2),
                'data': data,
                'field_completeness': {
                    'gender': round(gender_completeness, 2),
                    'birth_year': round(birth_year_completeness, 2),
                    'race': round(race_completeness, 2),
                    'ethnicity': round(ethnicity_completeness, 2)
                },
                'quality_issues': quality_issues,
                'message': f"Person table completeness: {completeness_score:.1f}%"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check person table completeness'
            }
    
    def _check_domain_completeness(self) -> Dict[str, Any]:
        """Check completeness within specific clinical domains"""
        try:
            # Check condition domain
            conditions_query = """
            SELECT 
                COUNT(*) as total_conditions,
                SUM(CASE WHEN condition_source_value IS NULL OR condition_source_value = '' THEN 1 ELSE 0 END) as missing_source_value,
                SUM(CASE WHEN condition_type_concept_id IS NULL THEN 1 ELSE 0 END) as missing_type_concept,
                SUM(CASE WHEN condition_end_date IS NULL THEN 1 ELSE 0 END) as missing_end_date
            FROM condition_occurrence
            """
            
            # Check drug domain
            drugs_query = """
            SELECT 
                COUNT(*) as total_drugs,
                SUM(CASE WHEN drug_source_value IS NULL OR drug_source_value = '' THEN 1 ELSE 0 END) as missing_source_value,
                SUM(CASE WHEN drug_type_concept_id IS NULL THEN 1 ELSE 0 END) as missing_type_concept,
                SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) as missing_quantity,
                SUM(CASE WHEN days_supply IS NULL THEN 1 ELSE 0 END) as missing_days_supply
            FROM drug_exposure
            """
            
            domain_results = []
            
            # Process conditions
            try:
                conditions_result = self.database.execute_query(conditions_query)
                if not conditions_result.empty:
                    cond_data = conditions_result.iloc[0].to_dict()
                    total = cond_data['total_conditions']
                    
                    if total > 0:
                        completeness_score = 100 - (
                            (cond_data['missing_source_value'] + cond_data['missing_type_concept']) * 100 / total / 2
                        )
                        
                        domain_results.append({
                            'domain': 'Condition',
                            'total_records': total,
                            'completeness_score': round(completeness_score, 2),
                            'details': cond_data,
                            'status': 'PASS' if completeness_score >= 80 else 'WARNING' if completeness_score >= 60 else 'FAIL'
                        })
            except Exception as e:
                domain_results.append({
                    'domain': 'Condition',
                    'status': 'ERROR',
                    'error': str(e)
                })
            
            # Process drugs
            try:
                drugs_result = self.database.execute_query(drugs_query)
                if not drugs_result.empty:
                    drug_data = drugs_result.iloc[0].to_dict()
                    total = drug_data['total_drugs']
                    
                    if total > 0:
                        completeness_score = 100 - (
                            (drug_data['missing_source_value'] + drug_data['missing_type_concept']) * 100 / total / 2
                        )
                        
                        domain_results.append({
                            'domain': 'Drug',
                            'total_records': total,
                            'completeness_score': round(completeness_score, 2),
                            'details': drug_data,
                            'status': 'PASS' if completeness_score >= 80 else 'WARNING' if completeness_score >= 60 else 'FAIL'
                        })
            except Exception as e:
                domain_results.append({
                    'domain': 'Drug',
                    'status': 'ERROR',
                    'error': str(e)
                })
            
            # Overall status
            if not domain_results:
                overall_status = 'ERROR'
            elif all(d['status'] == 'PASS' for d in domain_results if d['status'] != 'ERROR'):
                overall_status = 'PASS'
            elif any(d['status'] == 'FAIL' for d in domain_results):
                overall_status = 'FAIL'
            else:
                overall_status = 'WARNING'
            
            return {
                'status': overall_status,
                'data': domain_results,
                'message': f"Checked completeness for {len(domain_results)} clinical domains"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check domain completeness'
            }
