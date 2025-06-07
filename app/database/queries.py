from typing import Dict, List, Optional
from datetime import date
import logging


class OMOPQueries:
    """Collection of pre-defined OMOP quality check queries"""
    
    @staticmethod
    def get_table_row_counts() -> str:
        """Get row counts for all OMOP tables"""
        return """
        SELECT 
            'person' as table_name, COUNT(*) as row_count FROM person
        UNION ALL
        SELECT 
            'condition_occurrence' as table_name, COUNT(*) as row_count FROM condition_occurrence
        UNION ALL
        SELECT 
            'drug_exposure' as table_name, COUNT(*) as row_count FROM drug_exposure
        UNION ALL
        SELECT 
            'procedure_occurrence' as table_name, COUNT(*) as row_count FROM procedure_occurrence
        UNION ALL
        SELECT 
            'measurement' as table_name, COUNT(*) as row_count FROM measurement
        UNION ALL
        SELECT 
            'observation' as table_name, COUNT(*) as row_count FROM observation
        UNION ALL
        SELECT 
            'visit_occurrence' as table_name, COUNT(*) as row_count FROM visit_occurrence
        UNION ALL
        SELECT 
            'death' as table_name, COUNT(*) as row_count FROM death
        ORDER BY row_count DESC
        """
    
    @staticmethod
    def get_completeness_check(table_name: str, fields: List[str]) -> str:
        """Generate completeness check query for specified fields"""
        if not fields:
            raise ValueError("Fields list cannot be empty")
        
        null_conditions = [f"{field} IS NULL" for field in fields]
        
        return f"""
        SELECT 
            '{table_name}' as table_name,
            COUNT(*) as total_records,
            SUM(CASE WHEN {' OR '.join(null_conditions)} THEN 1 ELSE 0 END) as null_records,
            CASE 
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND(
                    (SUM(CASE WHEN {' OR '.join(null_conditions)} THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
                    2
                )
            END as null_percentage
        FROM {table_name}
        """
    
    @staticmethod
    def get_person_demographics_quality() -> str:
        """Check person table demographic data quality"""
        return """
        SELECT 
            COUNT(*) as total_persons,
            SUM(CASE WHEN gender_concept_id IS NULL THEN 1 ELSE 0 END) as missing_gender,
            SUM(CASE WHEN year_of_birth IS NULL THEN 1 ELSE 0 END) as missing_birth_year,
            SUM(CASE WHEN race_concept_id IS NULL THEN 1 ELSE 0 END) as missing_race,
            SUM(CASE WHEN ethnicity_concept_id IS NULL THEN 1 ELSE 0 END) as missing_ethnicity,
            SUM(CASE WHEN year_of_birth < 1900 THEN 1 ELSE 0 END) as invalid_birth_year_low,
            SUM(CASE WHEN year_of_birth > EXTRACT(YEAR FROM CURRENT_DATE) THEN 1 ELSE 0 END) as invalid_birth_year_high,
            SUM(CASE WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) > 120 THEN 1 ELSE 0 END) as unrealistic_age,
            CASE 
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND(
                    (COUNT(*) - SUM(CASE WHEN gender_concept_id IS NULL OR year_of_birth IS NULL THEN 1 ELSE 0 END)) * 100.0 / COUNT(*),
                    2
                )
            END as completeness_score
        FROM person
        """
    
    @staticmethod
    def get_future_dates_check() -> str:
        """Check for future dates across clinical tables"""
        return """
        SELECT 
            'condition_occurrence' as table_name,
            'condition_start_date' as date_field,
            COUNT(*) as future_count
        FROM condition_occurrence 
        WHERE condition_start_date > CURRENT_DATE
        
        UNION ALL
        
        SELECT 
            'drug_exposure' as table_name,
            'drug_exposure_start_date' as date_field,
            COUNT(*) as future_count
        FROM drug_exposure 
        WHERE drug_exposure_start_date > CURRENT_DATE
        
        UNION ALL
        
        SELECT 
            'procedure_occurrence' as table_name,
            'procedure_date' as date_field,
            COUNT(*) as future_count
        FROM procedure_occurrence 
        WHERE procedure_date > CURRENT_DATE
        
        UNION ALL
        
        SELECT 
            'measurement' as table_name,
            'measurement_date' as date_field,
            COUNT(*) as future_count
        FROM measurement 
        WHERE measurement_date > CURRENT_DATE
        
        UNION ALL
        
        SELECT 
            'visit_occurrence' as table_name,
            'visit_start_date' as date_field,
            COUNT(*) as future_count
        FROM visit_occurrence 
        WHERE visit_start_date > CURRENT_DATE
        
        ORDER BY future_count DESC
        """
    
    @staticmethod
    def get_events_after_death() -> str:
        """Check for clinical events occurring after death"""
        return """
        SELECT 
            'condition_occurrence' as event_type,
            COUNT(*) as events_after_death
        FROM condition_occurrence co
        JOIN death d ON co.person_id = d.person_id
        WHERE co.condition_start_date > d.death_date
        
        UNION ALL
        
        SELECT 
            'drug_exposure' as event_type,
            COUNT(*) as events_after_death
        FROM drug_exposure de
        JOIN death d ON de.person_id = d.person_id
        WHERE de.drug_exposure_start_date > d.death_date
        
        UNION ALL
        
        SELECT 
            'procedure_occurrence' as event_type,
            COUNT(*) as events_after_death
        FROM procedure_occurrence po
        JOIN death d ON po.person_id = d.person_id
        WHERE po.procedure_date > d.death_date
        
        UNION ALL
        
        SELECT 
            'measurement' as event_type,
            COUNT(*) as events_after_death
        FROM measurement m
        JOIN death d ON m.person_id = d.person_id
        WHERE m.measurement_date > d.death_date
        
        ORDER BY events_after_death DESC
        """
    
    @staticmethod
    def get_birth_death_consistency() -> str:
        """Check for deaths before birth (temporal logic violation)"""
        return """
        SELECT COUNT(*) as inconsistent_count
        FROM person p
        JOIN death d ON p.person_id = d.person_id
        WHERE d.death_date < 
            CASE 
                WHEN p.month_of_birth IS NOT NULL AND p.day_of_birth IS NOT NULL 
                THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, p.day_of_birth)
                WHEN p.month_of_birth IS NOT NULL 
                THEN MAKE_DATE(p.year_of_birth, p.month_of_birth, 1)
                ELSE MAKE_DATE(p.year_of_birth, 1, 1)
            END
        """
    
    @staticmethod
    def get_unmapped_concepts_summary() -> str:
        """Get summary of unmapped concepts across domains"""
        return """
        SELECT 
            'Condition' as domain,
            COUNT(*) as total_records,
            SUM(CASE WHEN condition_concept_id = 0 THEN 1 ELSE 0 END) as unmapped_count,
            CASE 
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND(
                    (SUM(CASE WHEN condition_concept_id = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                    2
                )
            END as unmapped_percentage
        FROM condition_occurrence
        
        UNION ALL
        
        SELECT 
            'Drug' as domain,
            COUNT(*) as total_records,
            SUM(CASE WHEN drug_concept_id = 0 THEN 1 ELSE 0 END) as unmapped_count,
            CASE 
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND(
                    (SUM(CASE WHEN drug_concept_id = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                    2
                )
            END as unmapped_percentage
        FROM drug_exposure
        
        UNION ALL
        
        SELECT 
            'Procedure' as domain,
            COUNT(*) as total_records,
            SUM(CASE WHEN procedure_concept_id = 0 THEN 1 ELSE 0 END) as unmapped_count,
            CASE 
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND(
                    (SUM(CASE WHEN procedure_concept_id = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                    2
                )
            END as unmapped_percentage
        FROM procedure_occurrence
        
        UNION ALL
        
        SELECT 
            'Measurement' as domain,
            COUNT(*) as total_records,
            SUM(CASE WHEN measurement_concept_id = 0 THEN 1 ELSE 0 END) as unmapped_count,
            CASE 
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND(
                    (SUM(CASE WHEN measurement_concept_id = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                    2
                )
            END as unmapped_percentage
        FROM measurement
        
        ORDER BY unmapped_percentage DESC
        """
    
    @staticmethod
    def get_standard_concept_usage() -> str:
        """Analyze standard vs non-standard concept usage"""
        return """
        WITH concept_usage AS (
            SELECT 
                COALESCE(c.standard_concept, 'NULL') as standard_concept,
                COUNT(*) as usage_count
            FROM condition_occurrence co
            JOIN concept c ON co.condition_concept_id = c.concept_id
            WHERE c.concept_id != 0
            GROUP BY c.standard_concept
            
            UNION ALL
            
            SELECT 
                COALESCE(c.standard_concept, 'NULL') as standard_concept,
                COUNT(*) as usage_count
            FROM drug_exposure de
            JOIN concept c ON de.drug_concept_id = c.concept_id
            WHERE c.concept_id != 0
            GROUP BY c.standard_concept
            
            UNION ALL
            
            SELECT 
                COALESCE(c.standard_concept, 'NULL') as standard_concept,
                COUNT(*) as usage_count
            FROM procedure_occurrence po
            JOIN concept c ON po.procedure_concept_id = c.concept_id
            WHERE c.concept_id != 0
            GROUP BY c.standard_concept
        )
        SELECT 
            standard_concept,
            SUM(usage_count) as total_usage,
            CASE 
                WHEN SUM(SUM(usage_count)) OVER() = 0 THEN 0.0
                ELSE ROUND(
                    (SUM(usage_count) * 100.0) / SUM(SUM(usage_count)) OVER(),
                    2
                )
            END as percentage
        FROM concept_usage
        GROUP BY standard_concept
        ORDER BY total_usage DESC
        """
    
    @staticmethod
    def get_foreign_key_violations() -> str:
        """Check for foreign key violations across tables"""
        return """
        -- Conditions without valid person_id
        SELECT 
            'condition_occurrence -> person' as relationship,
            COUNT(*) as violation_count
        FROM condition_occurrence co
        LEFT JOIN person p ON co.person_id = p.person_id
        WHERE co.person_id IS NOT NULL AND p.person_id IS NULL
        
        UNION ALL
        
        -- Drug exposures without valid person_id
        SELECT 
            'drug_exposure -> person' as relationship,
            COUNT(*) as violation_count
        FROM drug_exposure de
        LEFT JOIN person p ON de.person_id = p.person_id
        WHERE de.person_id IS NOT NULL AND p.person_id IS NULL
        
        UNION ALL
        
        -- Conditions without valid visit_occurrence_id (when specified)
        SELECT 
            'condition_occurrence -> visit_occurrence' as relationship,
            COUNT(*) as violation_count
        FROM condition_occurrence co
        LEFT JOIN visit_occurrence vo ON co.visit_occurrence_id = vo.visit_occurrence_id
        WHERE co.visit_occurrence_id IS NOT NULL AND vo.visit_occurrence_id IS NULL
        
        UNION ALL
        
        -- Drug exposures without valid visit_occurrence_id (when specified)
        SELECT 
            'drug_exposure -> visit_occurrence' as relationship,
            COUNT(*) as violation_count
        FROM drug_exposure de
        LEFT JOIN visit_occurrence vo ON de.visit_occurrence_id = vo.visit_occurrence_id
        WHERE de.visit_occurrence_id IS NOT NULL AND vo.visit_occurrence_id IS NULL
        
        ORDER BY violation_count DESC
        """
    
    @staticmethod
    def get_vocabulary_coverage() -> str:
        """Analyze vocabulary coverage and usage"""
        return """
        SELECT 
            v.vocabulary_id,
            v.vocabulary_name,
            COUNT(DISTINCT c.concept_id) as unique_concepts,
            COALESCE(cond_usage.usage_count, 0) as condition_usage,
            COALESCE(drug_usage.usage_count, 0) as drug_usage,
            COALESCE(proc_usage.usage_count, 0) as procedure_usage,
            (COALESCE(cond_usage.usage_count, 0) + 
             COALESCE(drug_usage.usage_count, 0) + 
             COALESCE(proc_usage.usage_count, 0)) as total_usage
        FROM vocabulary v
        LEFT JOIN concept c ON v.vocabulary_id = c.vocabulary_id
        LEFT JOIN (
            SELECT condition_concept_id, COUNT(*) as usage_count
            FROM condition_occurrence 
            WHERE condition_concept_id != 0
            GROUP BY condition_concept_id
        ) cond_usage ON c.concept_id = cond_usage.condition_concept_id
        LEFT JOIN (
            SELECT drug_concept_id, COUNT(*) as usage_count
            FROM drug_exposure 
            WHERE drug_concept_id != 0
            GROUP BY drug_concept_id
        ) drug_usage ON c.concept_id = drug_usage.drug_concept_id
        LEFT JOIN (
            SELECT procedure_concept_id, COUNT(*) as usage_count
            FROM procedure_occurrence 
            WHERE procedure_concept_id != 0
            GROUP BY procedure_concept_id
        ) proc_usage ON c.concept_id = proc_usage.procedure_concept_id
        WHERE c.concept_id IS NOT NULL AND c.concept_id != 0
        GROUP BY v.vocabulary_id, v.vocabulary_name, cond_usage.usage_count, drug_usage.usage_count, proc_usage.usage_count
        HAVING COUNT(DISTINCT c.concept_id) > 0
        ORDER BY total_usage DESC
        LIMIT 20
        """
    
    @staticmethod
    def get_measurement_outliers() -> str:
        """Identify measurement value outliers for common vital signs"""
        return """
        WITH measurement_stats AS (
            SELECT 
                m.measurement_concept_id,
                c.concept_name,
                COUNT(*) as measurement_count,
                AVG(m.value_as_number) as avg_value,
                STDDEV(m.value_as_number) as std_value,
                MIN(m.value_as_number) as min_value,
                MAX(m.value_as_number) as max_value,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY m.value_as_number) as q1,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY m.value_as_number) as q3
            FROM measurement m
            JOIN concept c ON m.measurement_concept_id = c.concept_id
            WHERE m.value_as_number IS NOT NULL
            AND m.measurement_concept_id IN (
                3027018,  -- Heart rate
                3012888,  -- Body temperature
                3004249,  -- Body weight
                3013762,  -- Body height
                3018586,  -- BMI
                3004327,  -- Systolic blood pressure
                3012888   -- Diastolic blood pressure
            )
            GROUP BY m.measurement_concept_id, c.concept_name
            HAVING COUNT(*) > 10
        )
        SELECT 
            measurement_concept_id,
            concept_name,
            measurement_count,
            ROUND(COALESCE(avg_value, 0), 2) as avg_value,
            ROUND(COALESCE(std_value, 0), 2) as std_value,
            COALESCE(min_value, 0) as min_value,
            COALESCE(max_value, 0) as max_value,
            ROUND(COALESCE(q1, 0), 2) as q1,
            ROUND(COALESCE(q3, 0), 2) as q3,
            CASE 
                WHEN concept_name ILIKE '%heart rate%' AND (min_value < 30 OR max_value > 200) THEN 'OUTLIER'
                WHEN concept_name ILIKE '%temperature%' AND (min_value < 32 OR max_value > 45) THEN 'OUTLIER'
                WHEN concept_name ILIKE '%weight%' AND (min_value < 0.5 OR max_value > 500) THEN 'OUTLIER'
                WHEN concept_name ILIKE '%height%' AND (min_value < 30 OR max_value > 250) THEN 'OUTLIER'
                WHEN concept_name ILIKE '%bmi%' AND (min_value < 10 OR max_value > 80) THEN 'OUTLIER'
                WHEN concept_name ILIKE '%blood pressure%' AND (min_value < 40 OR max_value > 300) THEN 'OUTLIER'
                ELSE 'NORMAL'
            END as outlier_status
        FROM measurement_stats
        ORDER BY measurement_count DESC
        """
    
    @staticmethod
    def get_visit_duration_analysis() -> str:
        """Analyze visit durations for outliers"""
        return """
        SELECT 
            visit_concept_id,
            COALESCE(c.concept_name, 'Unknown') as visit_type,
            COUNT(*) as visit_count,
            ROUND(
                AVG(CASE 
                    WHEN visit_end_date IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (visit_end_date - visit_start_date)) / 86400.0
                    ELSE NULL 
                END), 2
            ) as avg_duration_days,
            MIN(CASE 
                WHEN visit_end_date IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (visit_end_date - visit_start_date)) / 86400.0
                ELSE NULL 
            END) as min_duration_days,
            MAX(CASE 
                WHEN visit_end_date IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (visit_end_date - visit_start_date)) / 86400.0
                ELSE NULL 
            END) as max_duration_days,
            SUM(CASE 
                WHEN visit_end_date IS NOT NULL AND visit_end_date < visit_start_date 
                THEN 1 ELSE 0 
            END) as negative_durations,
            SUM(CASE 
                WHEN visit_end_date IS NOT NULL AND 
                     EXTRACT(EPOCH FROM (visit_end_date - visit_start_date)) / 86400.0 > 365 
                THEN 1 ELSE 0 
            END) as very_long_visits
        FROM visit_occurrence vo
        LEFT JOIN concept c ON vo.visit_concept_id = c.concept_id
        WHERE visit_start_date IS NOT NULL
        GROUP BY visit_concept_id, c.concept_name
        ORDER BY visit_count DESC
        """
    
    @staticmethod
    def get_data_density_by_year() -> str:
        """Analyze data density and trends by year"""
        return """
        SELECT 
            EXTRACT(YEAR FROM condition_start_date) as year,
            COUNT(DISTINCT person_id) as unique_patients,
            COUNT(*) as total_conditions,
            CASE 
                WHEN COUNT(DISTINCT person_id) = 0 THEN 0.0
                ELSE ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT person_id), 2)
            END as conditions_per_patient
        FROM condition_occurrence
        WHERE condition_start_date IS NOT NULL
        AND EXTRACT(YEAR FROM condition_start_date) >= 2010
        AND EXTRACT(YEAR FROM condition_start_date) <= EXTRACT(YEAR FROM CURRENT_DATE)
        GROUP BY EXTRACT(YEAR FROM condition_start_date)
        ORDER BY year
        """


# Convenience functions for commonly used queries
class QualityCheckQueries:
    """Simplified interface for common quality check queries"""
    
    @staticmethod
    def critical_completeness_checks() -> List[str]:
        """Return list of critical completeness check queries"""
        return [
            OMOPQueries.get_person_demographics_quality(),
            OMOPQueries.get_completeness_check('condition_occurrence', ['person_id', 'condition_concept_id']),
            OMOPQueries.get_completeness_check('drug_exposure', ['person_id', 'drug_concept_id']),
            OMOPQueries.get_completeness_check('visit_occurrence', ['person_id', 'visit_concept_id'])
        ]
    
    @staticmethod
    def temporal_integrity_checks() -> List[str]:
        """Return list of temporal integrity check queries"""
        return [
            OMOPQueries.get_future_dates_check(),
            OMOPQueries.get_events_after_death(),
            OMOPQueries.get_birth_death_consistency()
        ]
    
    @staticmethod
    def concept_quality_checks() -> List[str]:
        """Return list of concept mapping quality check queries"""
        return [
            OMOPQueries.get_unmapped_concepts_summary(),
            OMOPQueries.get_standard_concept_usage(),
            OMOPQueries.get_vocabulary_coverage()
        ]
    
    @staticmethod
    def referential_integrity_checks() -> List[str]:
        """Return list of referential integrity check queries"""
        return [
            OMOPQueries.get_foreign_key_violations()
        ]
    
    @staticmethod
    def statistical_outlier_checks() -> List[str]:
        """Return list of statistical outlier check queries"""
        return [
            OMOPQueries.get_measurement_outliers(),
            OMOPQueries.get_visit_duration_analysis()
        ]
    
    @staticmethod
    def get_all_quality_checks() -> Dict[str, List[str]]:
        """Return all quality checks organized by category"""
        return {
            'completeness': QualityCheckQueries.critical_completeness_checks(),
            'temporal': QualityCheckQueries.temporal_integrity_checks(),
            'concept_mapping': QualityCheckQueries.concept_quality_checks(),
            'referential': QualityCheckQueries.referential_integrity_checks(),
            'statistical': QualityCheckQueries.statistical_outlier_checks()
        }


# Export the main classes
__all__ = ['OMOPQueries', 'QualityCheckQueries']
