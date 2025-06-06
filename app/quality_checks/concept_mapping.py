from .base_checker import BaseQualityChecker
import pandas as pd
from typing import Dict, Any


class ConceptMappingChecker(BaseQualityChecker):
    """Check concept mapping quality and vocabulary coverage"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all concept mapping quality checks"""
        self.results = {}
        
        # Check 1: Unmapped concepts (concept_id = 0)
        self.results['unmapped_concepts'] = self._check_unmapped_concepts()
        
        # Check 2: Standard vs non-standard concept usage
        self.results['standard_concepts'] = self._check_standard_concept_usage()
        
        # Check 3: Vocabulary coverage
        self.results['vocabulary_coverage'] = self._check_vocabulary_coverage()
        
        # Check 4: Invalid concept domains
        self.results['domain_integrity'] = self._check_domain_integrity()
        
        return self.results
    
    def _check_unmapped_concepts(self) -> Dict[str, Any]:
        """Check for unmapped concepts (concept_id = 0) across domain tables"""
        unmapped_queries = [
            {
                'domain': 'Condition',
                'table': 'condition_occurrence',
                'concept_field': 'condition_concept_id',
                'source_field': 'condition_source_value'
            },
            {
                'domain': 'Drug',
                'table': 'drug_exposure',
                'concept_field': 'drug_concept_id',
                'source_field': 'drug_source_value'
            },
            {
                'domain': 'Procedure',
                'table': 'procedure_occurrence',
                'concept_field': 'procedure_concept_id',
                'source_field': 'procedure_source_value'
            },
            {
                'domain': 'Measurement',
                'table': 'measurement',
                'concept_field': 'measurement_concept_id',
                'source_field': 'measurement_source_value'
            }
        ]
        
        unmapped_results = []
        total_unmapped = 0
        
        for query_info in unmapped_queries:
            try:
                query = f"""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN {query_info['concept_field']} = 0 THEN 1 ELSE 0 END) as unmapped_count,
                    ROUND(
                        (SUM(CASE WHEN {query_info['concept_field']} = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
                        2
                    ) as unmapped_percentage
                FROM {query_info['table']}
                WHERE {query_info['concept_field']} IS NOT NULL
                """
                
                result = self.database.execute_query(query)
                if not result.empty:
                    row = result.iloc[0]
                    unmapped_count = row['unmapped_count']
                    total_unmapped += unmapped_count
                    
                    unmapped_results.append({
                        'domain': query_info['domain'],
                        'table': query_info['table'],
                        'total_records': row['total_records'],
                        'unmapped_count': unmapped_count,
                        'unmapped_percentage': row['unmapped_percentage'],
                        'status': 'PASS' if row['unmapped_percentage'] < 5 else 'WARNING' if row['unmapped_percentage'] < 15 else 'FAIL'
                    })
                    
            except Exception as e:
                unmapped_results.append({
                    'domain': query_info['domain'],
                    'table': query_info['table'],
                    'total_records': 0,
                    'unmapped_count': 'ERROR',
                    'unmapped_percentage': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        overall_status = 'PASS'
        if any(r['status'] == 'FAIL' for r in unmapped_results):
            overall_status = 'FAIL'
        elif any(r['status'] == 'WARNING' for r in unmapped_results):
            overall_status = 'WARNING'
        
        return {
            'status': overall_status,
            'total_unmapped': total_unmapped,
            'data': unmapped_results,
            'message': f"Found {total_unmapped} unmapped concepts across all domains"
        }
    
    def _check_standard_concept_usage(self) -> Dict[str, Any]:
        """Check usage of standard vs non-standard concepts"""
        try:
            query = """
            SELECT 
                c.standard_concept,
                COUNT(*) as usage_count,
                ROUND((COUNT(*) * 100.0) / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            WHERE c.concept_id != 0
            GROUP BY c.standard_concept
            ORDER BY usage_count DESC
            """
            
            result = self.database.execute_query(query)
            if not result.empty:
                standard_usage = result[result['standard_concept'] == 'S']['percentage'].iloc[0] if not result[result['standard_concept'] == 'S'].empty else 0
                
                return {
                    'status': 'PASS' if standard_usage >= 80 else 'WARNING' if standard_usage >= 60 else 'FAIL',
                    'standard_percentage': standard_usage,
                    'data': result.to_dict('records'),
                    'message': f"{standard_usage:.1f}% of concepts are standard concepts"
                }
            else:
                return {
                    'status': 'ERROR',
                    'message': 'No concept usage data found'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check standard concept usage'
            }
    
    def _check_vocabulary_coverage(self) -> Dict[str, Any]:
        """Analyze vocabulary coverage across domains"""
        try:
            query = """
            SELECT 
                v.vocabulary_id,
                v.vocabulary_name,
                COUNT(DISTINCT c.concept_id) as concept_count,
                COUNT(DISTINCT co.condition_occurrence_id) as usage_count
            FROM vocabulary v
            LEFT JOIN concept c ON v.vocabulary_id = c.vocabulary_id
            LEFT JOIN condition_occurrence co ON c.concept_id = co.condition_concept_id
            WHERE c.concept_id != 0
            GROUP BY v.vocabulary_id, v.vocabulary_name
            HAVING COUNT(DISTINCT c.concept_id) > 0
            ORDER BY usage_count DESC
            LIMIT 20
            """
            
            result = self.database.execute_query(query)
            if not result.empty:
                total_vocabularies = len(result)
                
                return {
                    'status': 'PASS' if total_vocabularies >= 5 else 'WARNING',
                    'total_vocabularies': total_vocabularies,
                    'data': result.to_dict('records'),
                    'message': f"Found {total_vocabularies} vocabularies in use"
                }
            else:
                return {
                    'status': 'WARNING',
                    'message': 'No vocabulary usage data found'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check vocabulary coverage'
            }
    
    def _check_domain_integrity(self) -> Dict[str, Any]:
        """Check if concepts are used in appropriate domain tables"""
        domain_checks = [
            {
                'expected_domain': 'Condition',
                'table': 'condition_occurrence',
                'concept_field': 'condition_concept_id'
            },
            {
                'expected_domain': 'Drug',
                'table': 'drug_exposure',
                'concept_field': 'drug_concept_id'
            },
            {
                'expected_domain': 'Procedure',
                'table': 'procedure_occurrence',
                'concept_field': 'procedure_concept_id'
            }
        ]
        
        domain_results = []
        total_violations = 0
        
        for check in domain_checks:
            try:
                query = f"""
                SELECT COUNT(*) as violation_count
                FROM {check['table']} t
                JOIN concept c ON t.{check['concept_field']} = c.concept_id
                WHERE c.domain_id != '{check['expected_domain']}'
                AND c.concept_id != 0
                """
                
                result = self.database.execute_query(query)
                if not result.empty:
                    violation_count = result['violation_count'].iloc[0]
                    total_violations += violation_count
                    
                    domain_results.append({
                        'domain': check['expected_domain'],
                        'table': check['table'],
                        'violations': violation_count,
                        'status': 'PASS' if violation_count == 0 else 'FAIL'
                    })
                    
            except Exception as e:
                domain_results.append({
                    'domain': check['expected_domain'],
                    'table': check['table'],
                    'violations': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        return {
            'status': 'PASS' if total_violations == 0 else 'FAIL',
            'total_violations': total_violations,
            'data': domain_results,
            'message': f"Found {total_violations} domain integrity violations"
        }


# app/quality_checks/referential.py
"""Referential integrity quality checks"""

from .base_checker import BaseQualityChecker
import pandas as pd
from typing import Dict, Any, List


class ReferentialIntegrityChecker(BaseQualityChecker):
    """Check referential integrity across OMOP tables"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all referential integrity checks"""
        self.results = {}
        
        # Check 1: Foreign key violations
        self.results['foreign_key_violations'] = self._check_foreign_key_violations()
        
        # Check 2: Orphaned records
        self.results['orphaned_records'] = self._check_orphaned_records()
        
        # Check 3: Person ID consistency
        self.results['person_id_consistency'] = self._check_person_id_consistency()
        
        # Check 4: Visit occurrence relationships
        self.results['visit_relationships'] = self._check_visit_relationships()
        
        return self.results
    
    def _check_foreign_key_violations(self) -> Dict[str, Any]:
        """Check for foreign key violations in critical relationships"""
        fk_checks = [
            {
                'name': 'Condition to Person',
                'child_table': 'condition_occurrence',
                'child_key': 'person_id',
                'parent_table': 'person',
                'parent_key': 'person_id'
            },
            {
                'name': 'Drug to Person',
                'child_table': 'drug_exposure',
                'child_key': 'person_id',
                'parent_table': 'person',
                'parent_key': 'person_id'
            },
            {
                'name': 'Visit to Person',
                'child_table': 'visit_occurrence',
                'child_key': 'person_id',
                'parent_table': 'person',
                'parent_key': 'person_id'
            },
            {
                'name': 'Condition to Visit',
                'child_table': 'condition_occurrence',
                'child_key': 'visit_occurrence_id',
                'parent_table': 'visit_occurrence',
                'parent_key': 'visit_occurrence_id'
            }
        ]
        
        violation_results = []
        total_violations = 0
        
        for check in fk_checks:
            try:
                query = f"""
                SELECT COUNT(*) as violation_count
                FROM {check['child_table']} c
                LEFT JOIN {check['parent_table']} p ON c.{check['child_key']} = p.{check['parent_key']}
                WHERE c.{check['child_key']} IS NOT NULL 
                AND p.{check['parent_key']} IS NULL
                """
                
                result = self.database.execute_query(query)
                if not result.empty:
                    violation_count = result['violation_count'].iloc[0]
                    total_violations += violation_count
                    
                    violation_results.append({
                        'relationship': check['name'],
                        'child_table': check['child_table'],
                        'parent_table': check['parent_table'],
                        'violations': violation_count,
                        'status': 'PASS' if violation_count == 0 else 'FAIL'
                    })
                    
            except Exception as e:
                violation_results.append({
                    'relationship': check['name'],
                    'child_table': check['child_table'],
                    'parent_table': check['parent_table'],
                    'violations': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        return {
            'status': 'PASS' if total_violations == 0 else 'FAIL',
            'total_violations': total_violations,
            'data': violation_results,
            'message': f"Found {total_violations} foreign key violations"
        }
    
    def _check_orphaned_records(self) -> Dict[str, Any]:
        """Check for orphaned records without proper parent references"""
        orphan_checks = [
            {
                'name': 'Conditions without visits',
                'query': """
                SELECT COUNT(*) as orphan_count
                FROM condition_occurrence co
                WHERE co.visit_occurrence_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM visit_occurrence vo 
                    WHERE vo.visit_occurrence_id = co.visit_occurrence_id
                )
                """
            },
            {
                'name': 'Drugs without visits',
                'query': """
                SELECT COUNT(*) as orphan_count
                FROM drug_exposure de
                WHERE de.visit_occurrence_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM visit_occurrence vo 
                    WHERE vo.visit_occurrence_id = de.visit_occurrence_id
                )
                """
            },
            {
                'name': 'Measurements without person',
                'query': """
                SELECT COUNT(*) as orphan_count
                FROM measurement m
                WHERE NOT EXISTS (
                    SELECT 1 FROM person p 
                    WHERE p.person_id = m.person_id
                )
                """
            }
        ]
        
        orphan_results = []
        total_orphans = 0
        
        for check in orphan_checks:
            try:
                result = self.database.execute_query(check['query'])
                if not result.empty:
                    orphan_count = result['orphan_count'].iloc[0]
                    total_orphans += orphan_count
                    
                    orphan_results.append({
                        'check_name': check['name'],
                        'orphan_count': orphan_count,
                        'status': 'PASS' if orphan_count == 0 else 'WARNING' if orphan_count < 100 else 'FAIL'
                    })
                    
            except Exception as e:
                orphan_results.append({
                    'check_name': check['name'],
                    'orphan_count': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        return {
            'status': 'PASS' if total_orphans == 0 else 'WARNING' if total_orphans < 100 else 'FAIL',
            'total_orphans': total_orphans,
            'data': orphan_results,
            'message': f"Found {total_orphans} orphaned records"
        }
    
    def _check_person_id_consistency(self) -> Dict[str, Any]:
        """Check person_id consistency across all clinical event tables"""
        try:
            # Get unique person IDs from each clinical table
            person_consistency_query = """
            WITH person_ids AS (
                SELECT person_id FROM person
            ),
            all_clinical_persons AS (
                SELECT DISTINCT person_id FROM condition_occurrence
                UNION
                SELECT DISTINCT person_id FROM drug_exposure  
                UNION
                SELECT DISTINCT person_id FROM procedure_occurrence
                UNION
                SELECT DISTINCT person_id FROM measurement
                UNION
                SELECT DISTINCT person_id FROM observation
                UNION
                SELECT DISTINCT person_id FROM visit_occurrence
            )
            SELECT 
                (SELECT COUNT(DISTINCT person_id) FROM person_ids) as persons_in_person_table,
                (SELECT COUNT(DISTINCT person_id) FROM all_clinical_persons) as persons_in_clinical_tables,
                (SELECT COUNT(DISTINCT acp.person_id) 
                 FROM all_clinical_persons acp 
                 LEFT JOIN person_ids pi ON acp.person_id = pi.person_id 
                 WHERE pi.person_id IS NULL) as clinical_persons_missing_from_person_table
            """
            
            result = self.database.execute_query(person_consistency_query)
            if not result.empty:
                data = result.iloc[0].to_dict()
                missing_persons = data['clinical_persons_missing_from_person_table']
                
                return {
                    'status': 'PASS' if missing_persons == 0 else 'FAIL',
                    'data': data,
                    'missing_persons': missing_persons,
                    'message': f"Found {missing_persons} person IDs in clinical tables missing from person table"
                }
            else:
                return {
                    'status': 'ERROR',
                    'message': 'Failed to analyze person ID consistency'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Error checking person ID consistency'
            }
    
    def _check_visit_relationships(self) -> Dict[str, Any]:
        """Check visit occurrence relationships and hierarchies"""
        try:
            visit_checks_query = """
            SELECT 
                (SELECT COUNT(*) FROM visit_occurrence WHERE visit_occurrence_id IS NULL) as visits_without_ids,
                (SELECT COUNT(*) FROM visit_occurrence WHERE person_id IS NULL) as visits_without_person,
                (SELECT COUNT(*) FROM visit_occurrence WHERE visit_start_date IS NULL) as visits_without_start_date,
                (SELECT COUNT(*) FROM visit_occurrence WHERE visit_end_date < visit_start_date) as visits_end_before_start,
                (SELECT COUNT(DISTINCT person_id) FROM visit_occurrence) as unique_persons_with_visits,
                (SELECT COUNT(*) FROM visit_occurrence) as total_visits
            """
            
            result = self.database.execute_query(visit_checks_query)
            if not result.empty:
                data = result.iloc[0].to_dict()
                
                # Calculate issues
                total_issues = (
                    data['visits_without_ids'] + 
                    data['visits_without_person'] + 
                    data['visits_without_start_date'] + 
                    data['visits_end_before_start']
                )
                
                return {
                    'status': 'PASS' if total_issues == 0 else 'WARNING' if total_issues < 10 else 'FAIL',
                    'total_issues': total_issues,
                    'data': data,
                    'message': f"Found {total_issues} visit relationship issues"
                }
            else:
                return {
                    'status': 'ERROR',
                    'message': 'Failed to analyze visit relationships'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Error checking visit relationships'
            }


# app/quality_checks/statistical.py
"""Statistical outlier detection quality checks"""

from .base_checker import BaseQualityChecker
import pandas as pd
import numpy as np
from typing import Dict, Any, List


class StatisticalOutlierChecker(BaseQualityChecker):
    """Detect statistical outliers and anomalies in OMOP data"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all statistical outlier checks"""
        self.results = {}
        
        # Check 1: Age outliers
        self.results['age_outliers'] = self._check_age_outliers()
        
        # Check 2: Quantity outliers in drug exposures
        self.results['drug_quantity_outliers'] = self._check_drug_quantity_outliers()
        
        # Check 3: Measurement value outliers
        self.results['measurement_outliers'] = self._check_measurement_outliers()
        
        # Check 4: Visit duration outliers
        self.results['visit_duration_outliers'] = self._check_visit_duration_outliers()
        
        return self.results
    
    def _check_age_outliers(self) -> Dict[str, Any]:
        """Check for unrealistic ages"""
        try:
            age_query = """
            SELECT 
                person_id,
                year_of_birth,
                EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth as current_age
            FROM person 
            WHERE year_of_birth IS NOT NULL
            AND (
                year_of_birth < 1900 
                OR year_of_birth > EXTRACT(YEAR FROM CURRENT_DATE)
                OR (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) > 120
            )
            """
            
            result = self.database.execute_query(age_query)
            outlier_count = len(result) if not result.empty else 0
            
            return {
                'status': 'PASS' if outlier_count == 0 else 'WARNING' if outlier_count < 10 else 'FAIL',
                'outlier_count': outlier_count,
                'data': result.to_dict('records') if not result.empty else [],
                'message': f"Found {outlier_count} age outliers"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check age outliers'
            }
    
    def _check_drug_quantity_outliers(self) -> Dict[str, Any]:
        """Check for unusual drug quantities"""
        try:
            quantity_query = """
            SELECT 
                drug_exposure_id,
                person_id,
                quantity,
                days_supply
            FROM drug_exposure 
            WHERE quantity IS NOT NULL
            AND (
                quantity < 0 
                OR quantity > 10000
                OR (days_supply IS NOT NULL AND days_supply > 365)
                OR (days_supply IS NOT NULL AND days_supply < 0)
            )
            ORDER BY quantity DESC
            LIMIT 100
            """
            
            result = self.database.execute_query(quantity_query)
            outlier_count = len(result) if not result.empty else 0
            
            return {
                'status': 'PASS' if outlier_count == 0 else 'WARNING' if outlier_count < 50 else 'FAIL',
                'outlier_count': outlier_count,
                'data': result.to_dict('records') if not result.empty else [],
                'message': f"Found {outlier_count} drug quantity outliers"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check drug quantity outliers'
            }
    
    def _check_measurement_outliers(self) -> Dict[str, Any]:
        """Check for unusual measurement values"""
        try:
            # Focus on common vital signs and lab values
            measurement_query = """
            WITH measurement_stats AS (
                SELECT 
                    m.measurement_concept_id,
                    c.concept_name,
                    COUNT(*) as measurement_count,
                    AVG(m.value_as_number) as avg_value,
                    STDDEV(m.value_as_number) as std_value,
                    MIN(m.value_as_number) as min_value,
                    MAX(m.value_as_number) as max_value
                FROM measurement m
                JOIN concept c ON m.measurement_concept_id = c.concept_id
                WHERE m.value_as_number IS NOT NULL
                AND m.measurement_concept_id IN (
                    3027018,  -- Heart rate
                    3012888,  -- Body temperature
                    3004249,  -- Body weight
                    3013762   -- Body height
                )
                GROUP BY m.measurement_concept_id, c.concept_name
                HAVING COUNT(*) > 10
            )
            SELECT 
                measurement_concept_id,
                concept_name,
                measurement_count,
                ROUND(avg_value, 2) as avg_value,
                ROUND(std_value, 2) as std_value,
                min_value,
                max_value,
                CASE 
                    WHEN concept_name LIKE '%Heart rate%' AND (min_value < 30 OR max_value > 200) THEN 'OUTLIER'
                    WHEN concept_name LIKE '%temperature%' AND (min_value < 32 OR max_value > 45) THEN 'OUTLIER'
                    WHEN concept_name LIKE '%weight%' AND (min_value < 0.5 OR max_value > 500) THEN 'OUTLIER'
                    WHEN concept_name LIKE '%height%' AND (min_value < 30 OR max_value > 250) THEN 'OUTLIER'
                    ELSE 'NORMAL'
                END as outlier_status
            FROM measurement_stats
            """
            
            result = self.database.execute_query(measurement_query)
            if not result.empty:
                outlier_measurements = result[result['outlier_status'] == 'OUTLIER']
                outlier_count = len(outlier_measurements)
                
                return {
                    'status': 'PASS' if outlier_count == 0 else 'WARNING',
                    'outlier_count': outlier_count,
                    'data': result.to_dict('records'),
                    'message': f"Found {outlier_count} measurements with outlier ranges"
                }
            else:
                return {
                    'status': 'WARNING',
                    'message': 'No measurement data available for analysis'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check measurement outliers'
            }
    
    def _check_visit_duration_outliers(self) -> Dict[str, Any]:
        """Check for unusual visit durations"""
        try:
            duration_query = """
            SELECT 
                visit_occurrence_id,
                person_id,
                visit_start_date,
                visit_end_date,
                CASE 
                    WHEN visit_end_date IS NOT NULL 
                    THEN visit_end_date - visit_start_date 
                    ELSE NULL 
                END as duration_days
            FROM visit_occurrence 
            WHERE visit_start_date IS NOT NULL
            AND visit_end_date IS NOT NULL
            AND (
                visit_end_date - visit_start_date < 0  -- Negative duration
                OR visit_end_date - visit_start_date > 365  -- More than a year
            )
            ORDER BY duration_days DESC
            LIMIT 100
            """
            
            result = self.database.execute_query(duration_query)
            outlier_count = len(result) if not result.empty else 0
            
            return {
                'status': 'PASS' if outlier_count == 0 else 'WARNING' if outlier_count < 20 else 'FAIL',
                'outlier_count': outlier_count,
                'data': result.to_dict('records') if not result.empty else [],
                'message': f"Found {outlier_count} visit duration outliers"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check visit duration outliers'
            }


# app/quality_checks/__init__.py
"""Quality checks module initialization"""

from .base_checker import BaseQualityChecker
from .completeness import CompletenessChecker
from .temporal import TemporalChecker
from .concept_mapping import ConceptMappingChecker
from .referential import ReferentialIntegrityChecker
from .statistical import StatisticalOutlierChecker

__all__ = [
    'BaseQualityChecker',
    'CompletenessChecker', 
    'TemporalChecker',
    'ConceptMappingChecker',
    'ReferentialIntegrityChecker',
    'StatisticalOutlierChecker'
]


# Quality check registry for easy access
QUALITY_CHECKERS = {
    'completeness': CompletenessChecker,
    'temporal': TemporalChecker,
    'concept_mapping': ConceptMappingChecker,
    'referential': ReferentialIntegrityChecker,
    'statistical': StatisticalOutlierChecker
}


def get_quality_checker(checker_name: str, database):
    """Factory function to get quality checker by name"""
    if checker_name in QUALITY_CHECKERS:
        return QUALITY_CHECKERS[checker_name](database)
    else:
        raise ValueError(f"Unknown quality checker: {checker_name}")
