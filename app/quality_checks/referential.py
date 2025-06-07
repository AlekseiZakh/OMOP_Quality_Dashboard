import sys
import os
from typing import Dict, List, Any
import pandas as pd

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from .base_checker import BaseQualityChecker
    from ..database.queries import OMOPQueries
except ImportError:
    try:
        from base_checker import BaseQualityChecker
        from database.queries import OMOPQueries
    except ImportError:
        # Fallback for development/testing
        class BaseQualityChecker:
            def __init__(self, database):
                self.database = database
                self.results = {}
                
        class OMOPQueries:
            @staticmethod
            def get_foreign_key_violations():
                return "SELECT 'placeholder' as relationship, 0 as violation_count"


class ReferentialIntegrityChecker(BaseQualityChecker):
    """Check referential integrity across OMOP tables"""
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all referential integrity checks"""
        self.results = {}
        
        # Validate database connection first
        if not self.validate_database_connection():
            return {
                'error': 'Database connection failed',
                'status': 'ERROR'
            }
        
        # Check 1: Foreign key violations
        self.log_check_start("foreign_key_violations")
        self.results['foreign_key_violations'] = self._check_foreign_key_violations()
        self.log_check_complete("foreign_key_violations", self.results['foreign_key_violations'].get('status', 'UNKNOWN'))
        
        # Check 2: Orphaned records
        self.log_check_start("orphaned_records")
        self.results['orphaned_records'] = self._check_orphaned_records()
        self.log_check_complete("orphaned_records", self.results['orphaned_records'].get('status', 'UNKNOWN'))
        
        # Check 3: Person ID consistency
        self.log_check_start("person_id_consistency")
        self.results['person_id_consistency'] = self._check_person_id_consistency()
        self.log_check_complete("person_id_consistency", self.results['person_id_consistency'].get('status', 'UNKNOWN'))
        
        # Check 4: Visit occurrence relationships
        self.log_check_start("visit_relationships")
        self.results['visit_relationships'] = self._check_visit_relationships()
        self.log_check_complete("visit_relationships", self.results['visit_relationships'].get('status', 'UNKNOWN'))
        
        # Check 5: Concept ID integrity
        self.log_check_start("concept_integrity")
        self.results['concept_integrity'] = self._check_concept_integrity()
        self.log_check_complete("concept_integrity", self.results['concept_integrity'].get('status', 'UNKNOWN'))
        
        return self.results
    
    def _check_foreign_key_violations(self) -> Dict[str, Any]:
        """Check for foreign key violations in critical relationships"""
        try:
            query = OMOPQueries.get_foreign_key_violations()
            result = self.database.execute_query(query)
            
            if result.empty:
                return {
                    'status': 'PASS',
                    'total_violations': 0,
                    'data': [],
                    'message': 'No foreign key violations found'
                }
            
            # Filter out relationships with 0 violations
            violations_data = result[result['violation_count'] > 0]
            
            if violations_data.empty:
                return {
                    'status': 'PASS',
                    'total_violations': 0,
                    'data': [],
                    'message': 'No foreign key violations found'
                }
            
            total_violations = violations_data['violation_count'].sum()
            
            violation_results = []
            for _, row in violations_data.iterrows():
                violation_count = row['violation_count']
                violation_results.append({
                    'relationship': row['relationship'],
                    'violations': int(violation_count),
                    'status': 'FAIL' if violation_count > 0 else 'PASS'
                })
            
            return {
                'status': 'FAIL' if total_violations > 0 else 'PASS',
                'total_violations': int(total_violations),
                'data': violation_results,
                'message': f"Found {total_violations} foreign key violations"
            }
            
        except Exception as e:
            return self.handle_error("foreign_key_violations", e)
    
    def _check_orphaned_records(self) -> Dict[str, Any]:
        """Check for orphaned records without proper parent references"""
        orphan_checks = [
            {
                'name': 'Conditions without visits',
                'table': 'condition_occurrence',
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
                'table': 'drug_exposure',
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
                'name': 'Procedures without visits',
                'table': 'procedure_occurrence',
                'query': """
                SELECT COUNT(*) as orphan_count
                FROM procedure_occurrence po
                WHERE po.visit_occurrence_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM visit_occurrence vo 
                    WHERE vo.visit_occurrence_id = po.visit_occurrence_id
                )
                """
            },
            {
                'name': 'Measurements without person',
                'table': 'measurement',
                'query': """
                SELECT COUNT(*) as orphan_count
                FROM measurement m
                WHERE NOT EXISTS (
                    SELECT 1 FROM person p 
                    WHERE p.person_id = m.person_id
                )
                """
            },
            {
                'name': 'Observations without person',
                'table': 'observation',
                'query': """
                SELECT COUNT(*) as orphan_count
                FROM observation o
                WHERE NOT EXISTS (
                    SELECT 1 FROM person p 
                    WHERE p.person_id = o.person_id
                )
                """
            }
        ]
        
        orphan_results = []
        total_orphans = 0
        
        for check in orphan_checks:
            # Skip check if required table doesn't exist
            if not self.table_exists(check['table']):
                continue
                
            try:
                result = self.database.execute_query(check['query'])
                if not result.empty:
                    orphan_count = result['orphan_count'].iloc[0]
                    total_orphans += orphan_count
                    
                    # Determine status based on orphan count
                    if orphan_count == 0:
                        status = 'PASS'
                    elif orphan_count < 100:
                        status = 'WARNING'
                    else:
                        status = 'FAIL'
                    
                    orphan_results.append({
                        'check_name': check['name'],
                        'orphan_count': int(orphan_count),
                        'status': status
                    })
                    
            except Exception as e:
                self.logger.error(f"Error in orphan check {check['name']}: {str(e)}")
                orphan_results.append({
                    'check_name': check['name'],
                    'orphan_count': 'ERROR',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Overall status
        if total_orphans == 0:
            overall_status = 'PASS'
        elif total_orphans < 100:
            overall_status = 'WARNING'
        else:
            overall_status = 'FAIL'
        
        # Check for any errors
        if any(r['status'] == 'ERROR' for r in orphan_results):
            overall_status = 'ERROR'
        
        return {
            'status': overall_status,
            'total_orphans': total_orphans,
            'data': orphan_results,
            'message': f"Found {total_orphans} orphaned records"
        }
    
    def _check_person_id_consistency(self) -> Dict[str, Any]:
        """Check person_id consistency across all clinical event tables"""
        # Check if person table exists
        if not self.table_exists('person'):
            return {
                'status': 'ERROR',
                'message': 'Person table not found'
            }
        
        try:
            # Get unique person IDs from each clinical table
            person_consistency_query = """
            WITH person_ids AS (
                SELECT DISTINCT person_id FROM person
            ),
            clinical_person_ids AS (
                SELECT DISTINCT person_id, 'condition_occurrence' as table_name FROM condition_occurrence
                UNION
                SELECT DISTINCT person_id, 'drug_exposure' as table_name FROM drug_exposure  
                UNION
                SELECT DISTINCT person_id, 'procedure_occurrence' as table_name FROM procedure_occurrence
                UNION
                SELECT DISTINCT person_id, 'measurement' as table_name FROM measurement
                UNION
                SELECT DISTINCT person_id, 'observation' as table_name FROM observation
                UNION
                SELECT DISTINCT person_id, 'visit_occurrence' as table_name FROM visit_occurrence
            ),
            missing_persons AS (
                SELECT DISTINCT cpi.person_id, cpi.table_name
                FROM clinical_person_ids cpi
                LEFT JOIN person_ids pi ON cpi.person_id = pi.person_id
                WHERE pi.person_id IS NULL
            )
            SELECT 
                (SELECT COUNT(DISTINCT person_id) FROM person_ids) as persons_in_person_table,
                (SELECT COUNT(DISTINCT person_id) FROM clinical_person_ids) as persons_in_clinical_tables,
                (SELECT COUNT(DISTINCT person_id) FROM missing_persons) as clinical_persons_missing_from_person_table,
                (SELECT COUNT(*) FROM missing_persons) as total_missing_references
            """
            
            # Build dynamic query based on existing tables
            clinical_tables = ['condition_occurrence', 'drug_exposure', 'procedure_occurrence', 
                             'measurement', 'observation', 'visit_occurrence']
            
            existing_tables = [table for table in clinical_tables if self.table_exists(table)]
            
            if not existing_tables:
                return {
                    'status': 'WARNING',
                    'message': 'No clinical tables found to check person ID consistency',
                    'missing_persons': 0
                }
            
            # Build dynamic query for existing tables only
            union_parts = []
            for table in existing_tables:
                union_parts.append(f"SELECT DISTINCT person_id, '{table}' as table_name FROM {table}")
            
            dynamic_query = f"""
            WITH person_ids AS (
                SELECT DISTINCT person_id FROM person
            ),
            clinical_person_ids AS (
                {' UNION '.join(union_parts)}
            ),
            missing_persons AS (
                SELECT DISTINCT cpi.person_id, cpi.table_name
                FROM clinical_person_ids cpi
                LEFT JOIN person_ids pi ON cpi.person_id = pi.person_id
                WHERE pi.person_id IS NULL
            )
            SELECT 
                (SELECT COUNT(DISTINCT person_id) FROM person_ids) as persons_in_person_table,
                (SELECT COUNT(DISTINCT person_id) FROM clinical_person_ids) as persons_in_clinical_tables,
                (SELECT COUNT(DISTINCT person_id) FROM missing_persons) as clinical_persons_missing_from_person_table,
                (SELECT COUNT(*) FROM missing_persons) as total_missing_references
            """
            
            result = self.database.execute_query(dynamic_query)
            
            if result.empty:
                return {
                    'status': 'ERROR',
                    'message': 'Failed to analyze person ID consistency'
                }
            
            data = result.iloc[0].to_dict()
            missing_persons = data['clinical_persons_missing_from_person_table']
            missing_references = data['total_missing_references']
            
            # Get detailed breakdown of missing person references
            if missing_persons > 0:
                detail_union_parts = []
                for table in existing_tables:
                    detail_union_parts.append(f"SELECT DISTINCT person_id, '{table}' as table_name FROM {table}")
                
                missing_detail_query = f"""
                WITH clinical_person_ids AS (
                    {' UNION '.join(detail_union_parts)}
                )
                SELECT 
                    cpi.table_name,
                    COUNT(*) as missing_person_references
                FROM clinical_person_ids cpi
                LEFT JOIN person p ON cpi.person_id = p.person_id
                WHERE p.person_id IS NULL
                GROUP BY cpi.table_name
                ORDER BY missing_person_references DESC
                """
                
                try:
                    detail_result = self.database.execute_query(missing_detail_query)
                    missing_details = detail_result.to_dict('records') if not detail_result.empty else []
                except Exception as e:
                    self.logger.warning(f"Failed to get missing person details: {str(e)}")
                    missing_details = []
            else:
                missing_details = []
            
            return {
                'status': 'PASS' if missing_persons == 0 else 'FAIL',
                'data': {k: int(v) for k, v in data.items()},
                'missing_persons': int(missing_persons),
                'missing_references': int(missing_references),
                'missing_details': missing_details,
                'tables_checked': existing_tables,
                'message': f"Found {missing_persons} person IDs in clinical tables missing from person table"
            }
            
        except Exception as e:
            return self.handle_error("person_id_consistency", e)
    
    def _check_visit_relationships(self) -> Dict[str, Any]:
        """Check visit occurrence relationships and hierarchies"""
        # Check if visit_occurrence table exists
        if not self.table_exists('visit_occurrence'):
            return {
                'status': 'WARNING',
                'message': 'Visit_occurrence table not found'
            }
        
        try:
            visit_checks_query = """
            SELECT 
                COUNT(*) as total_visits,
                SUM(CASE WHEN visit_occurrence_id IS NULL THEN 1 ELSE 0 END) as visits_without_ids,
                SUM(CASE WHEN person_id IS NULL THEN 1 ELSE 0 END) as visits_without_person,
                SUM(CASE WHEN visit_start_date IS NULL THEN 1 ELSE 0 END) as visits_without_start_date,
                SUM(CASE WHEN visit_end_date < visit_start_date THEN 1 ELSE 0 END) as visits_end_before_start,
                SUM(CASE WHEN visit_concept_id IS NULL THEN 1 ELSE 0 END) as visits_without_concept,
                COUNT(DISTINCT person_id) as unique_persons_with_visits
            FROM visit_occurrence
            """
            
            result = self.database.execute_query(visit_checks_query)
            
            if result.empty:
                return {
                    'status': 'ERROR',
                    'message': 'No visit data found'
                }
            
            data = result.iloc[0].to_dict()
            
            # Calculate total issues
            total_issues = (
                data['visits_without_ids'] + 
                data['visits_without_person'] + 
                data['visits_without_start_date'] + 
                data['visits_end_before_start'] +
                data['visits_without_concept']
            )
            
            # Check for visit detail relationships if visit_detail table exists
            visit_detail_issues = 0
            if self.table_exists('visit_detail'):
                try:
                    visit_detail_query = """
                    SELECT COUNT(*) as orphaned_visit_details
                    FROM visit_detail vd
                    WHERE NOT EXISTS (
                        SELECT 1 FROM visit_occurrence vo 
                        WHERE vo.visit_occurrence_id = vd.visit_occurrence_id
                    )
                    """
                    visit_detail_result = self.database.execute_query(visit_detail_query)
                    if not visit_detail_result.empty:
                        visit_detail_issues = visit_detail_result['orphaned_visit_details'].iloc[0]
                        data['orphaned_visit_details'] = int(visit_detail_issues)
                        total_issues += visit_detail_issues
                except Exception as e:
                    self.logger.warning(f"Failed to check visit_detail orphans: {str(e)}")
                    data['orphaned_visit_details'] = 'ERROR'
            else:
                data['orphaned_visit_details'] = 0
            
            return {
                'status': 'PASS' if total_issues == 0 else 'WARNING' if total_issues < 10 else 'FAIL',
                'total_issues': int(total_issues),
                'data': {k: int(v) if isinstance(v, (int, float)) else v for k, v in data.items()},
                'message': f"Found {total_issues} visit relationship issues"
            }
            
        except Exception as e:
            return self.handle_error("visit_relationships", e)
    
    def _check_concept_integrity(self) -> Dict[str, Any]:
        """Check concept ID integrity across domain tables"""
        # Check if concept table exists
        if not self.table_exists('concept'):
            return {
                'status': 'WARNING',
                'message': 'Concept table not found - skipping concept integrity check'
            }
        
        try:
            concept_checks = [
                {
                    'domain': 'Condition',
                    'table': 'condition_occurrence',
                    'concept_field': 'condition_concept_id',
                    'expected_domain': 'Condition'
                },
                {
                    'domain': 'Drug',
                    'table': 'drug_exposure',
                    'concept_field': 'drug_concept_id',
                    'expected_domain': 'Drug'
                },
                {
                    'domain': 'Procedure',
                    'table': 'procedure_occurrence',
                    'concept_field': 'procedure_concept_id',
                    'expected_domain': 'Procedure'
                },
                {
                    'domain': 'Measurement',
                    'table': 'measurement',
                    'concept_field': 'measurement_concept_id',
                    'expected_domain': 'Measurement'
                }
            ]
            
            concept_results = []
            total_violations = 0
            
            for check in concept_checks:
                # Skip if table doesn't exist
                if not self.table_exists(check['table']):
                    continue
                    
                try:
                    # Check for concepts that don't exist in concept table
                    missing_concepts_query = f"""
                    SELECT COUNT(*) as missing_concepts
                    FROM {check['table']} t
                    WHERE t.{check['concept_field']} != 0
                    AND NOT EXISTS (
                        SELECT 1 FROM concept c 
                        WHERE c.concept_id = t.{check['concept_field']}
                    )
                    """
                    
                    # Check for concepts in wrong domain
                    wrong_domain_query = f"""
                    SELECT COUNT(*) as wrong_domain_concepts
                    FROM {check['table']} t
                    JOIN concept c ON t.{check['concept_field']} = c.concept_id
                    WHERE c.domain_id != '{check['expected_domain']}'
                    AND c.concept_id != 0
                    """
                    
                    missing_result = self.database.execute_query(missing_concepts_query)
                    domain_result = self.database.execute_query(wrong_domain_query)
                    
                    missing_count = missing_result['missing_concepts'].iloc[0] if not missing_result.empty else 0
                    wrong_domain_count = domain_result['wrong_domain_concepts'].iloc[0] if not domain_result.empty else 0
                    
                    total_domain_violations = missing_count + wrong_domain_count
                    total_violations += total_domain_violations
                    
                    concept_results.append({
                        'domain': check['domain'],
                        'table': check['table'],
                        'missing_concepts': int(missing_count),
                        'wrong_domain_concepts': int(wrong_domain_count),
                        'total_violations': int(total_domain_violations),
                        'status': 'PASS' if total_domain_violations == 0 else 'FAIL'
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error checking concept integrity for {check['domain']}: {str(e)}")
                    concept_results.append({
                        'domain': check['domain'],
                        'table': check['table'],
                        'missing_concepts': 'ERROR',
                        'wrong_domain_concepts': 'ERROR',
                        'total_violations': 'ERROR',
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            overall_status = 'PASS'
            if total_violations > 0:
                overall_status = 'FAIL'
            elif any(r['status'] == 'ERROR' for r in concept_results):
                overall_status = 'ERROR'
            
            return {
                'status': overall_status,
                'total_violations': total_violations,
                'data': concept_results,
                'message': f"Found {total_violations} concept integrity violations"
            }
            
        except Exception as e:
            return self.handle_error("concept_integrity", e)
