from .base_checker import BaseQualityChecker
from ..database.queries import OMOPQueries
import pandas as pd
import numpy as np
from typing import Dict, List, Any


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
        
        # Check 5: Data distribution anomalies
        self.results['distribution_anomalies'] = self._check_distribution_anomalies()
        
        return self.results
    
    def _check_age_outliers(self) -> Dict[str, Any]:
        """Check for unrealistic ages"""
        try:
            age_query = """
            SELECT 
                person_id,
                year_of_birth,
                EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth as current_age,
                CASE 
                    WHEN year_of_birth < 1900 THEN 'Birth year too early'
                    WHEN year_of_birth > EXTRACT(YEAR FROM CURRENT_DATE) THEN 'Future birth year'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) > 120 THEN 'Age over 120'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) < 0 THEN 'Negative age'
                    ELSE 'Unknown issue'
                END as issue_type
            FROM person 
            WHERE year_of_birth IS NOT NULL
            AND (
                year_of_birth < 1900 
                OR year_of_birth > EXTRACT(YEAR FROM CURRENT_DATE)
                OR (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) > 120
                OR (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) < 0
            )
            ORDER BY current_age DESC
            LIMIT 100
            """
            
            result = self.database.execute_query(age_query)
            outlier_count = len(result) if not result.empty else 0
            
            # Group by issue type
            issue_summary = []
            if not result.empty:
                issue_counts = result['issue_type'].value_counts()
                for issue_type, count in issue_counts.items():
                    issue_summary.append({
                        'issue_type': issue_type,
                        'count': int(count)
                    })
            
            return {
                'status': 'PASS' if outlier_count == 0 else 'WARNING' if outlier_count < 10 else 'FAIL',
                'outlier_count': outlier_count,
                'issue_summary': issue_summary,
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
                drug_concept_id,
                quantity,
                days_supply,
                CASE 
                    WHEN quantity < 0 THEN 'Negative quantity'
                    WHEN quantity > 10000 THEN 'Extremely high quantity'
                    WHEN days_supply IS NOT NULL AND days_supply > 365 THEN 'Days supply over 1 year'
                    WHEN days_supply IS NOT NULL AND days_supply < 0 THEN 'Negative days supply'
                    ELSE 'Other issue'
                END as issue_type
            FROM drug_exposure 
            WHERE (
                quantity IS NOT NULL AND (quantity < 0 OR quantity > 10000)
            ) OR (
                days_supply IS NOT NULL AND (days_supply > 365 OR days_supply < 0)
            )
            ORDER BY quantity DESC NULLS LAST
            LIMIT 100
            """
            
            result = self.database.execute_query(quantity_query)
            outlier_count = len(result) if not result.empty else 0
            
            # Summary statistics
            summary_query = """
            SELECT 
                COUNT(*) as total_drug_exposures,
                COUNT(quantity) as records_with_quantity,
                COUNT(days_supply) as records_with_days_supply,
                AVG(quantity) as avg_quantity,
                STDDEV(quantity) as std_quantity,
                MIN(quantity) as min_quantity,
                MAX(quantity) as max_quantity,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY quantity) as p95_quantity
            FROM drug_exposure
            WHERE quantity IS NOT NULL AND quantity >= 0
            """
            
            try:
                summary_result = self.database.execute_query(summary_query)
                summary_stats = summary_result.iloc[0].to_dict() if not summary_result.empty else {}
            except:
                summary_stats = {}
            
            # Group by issue type
            issue_summary = []
            if not result.empty:
                issue_counts = result['issue_type'].value_counts()
                for issue_type, count in issue_counts.items():
                    issue_summary.append({
                        'issue_type': issue_type,
                        'count': int(count)
                    })
            
            return {
                'status': 'PASS' if outlier_count == 0 else 'WARNING' if outlier_count < 50 else 'FAIL',
                'outlier_count': outlier_count,
                'issue_summary': issue_summary,
                'summary_stats': summary_stats,
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
            query = OMOPQueries.get_measurement_outliers()
            result = self.database.execute_query(query)
            
            if result.empty:
                return {
                    'status': 'WARNING',
                    'outlier_count': 0,
                    'data': [],
                    'message': 'No measurement data available for analysis'
                }
            
            outlier_measurements = result[result['outlier_status'] == 'OUTLIER']
            outlier_count = len(outlier_measurements)
            
            # Get detailed outlier records for the most problematic measurements
            detailed_outliers = []
            if not outlier_measurements.empty:
                for _, row in outlier_measurements.head(5).iterrows():  # Top 5 problematic measurements
                    concept_id = row['measurement_concept_id']
                    concept_name = row['concept_name']
                    
                    # Get specific outlier records
                    outlier_records_query = f"""
                    SELECT 
                        person_id,
                        measurement_date,
                        value_as_number,
                        unit_concept_id
                    FROM measurement 
                    WHERE measurement_concept_id = {concept_id}
                    AND value_as_number IS NOT NULL
                    AND (
                        value_as_number < {row['min_value']} OR 
                        value_as_number > {row['max_value']}
                    )
                    ORDER BY ABS(value_as_number - {row['avg_value']}) DESC
                    LIMIT 10
                    """
                    
                    try:
                        outlier_records = self.database.execute_query(outlier_records_query)
                        detailed_outliers.append({
                            'concept_name': concept_name,
                            'concept_id': int(concept_id),
                            'outlier_records': outlier_records.to_dict('records') if not outlier_records.empty else []
                        })
                    except:
                        pass
            
            return {
                'status': 'PASS' if outlier_count == 0 else 'WARNING',
                'outlier_count': outlier_count,
                'measurements_analyzed': len(result),
                'data': result.to_dict('records'),
                'detailed_outliers': detailed_outliers,
                'message': f"Found {outlier_count} measurements with outlier ranges"
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
            query = OMOPQueries.get_visit_duration_analysis()
            result = self.database.execute_query(query)
            
            if result.empty:
                return {
                    'status': 'WARNING',
                    'message': 'No visit data available for analysis'
                }
            
            # Count total outliers
            total_negative = result['negative_durations'].sum()
            total_very_long = result['very_long_visits'].sum()
            total_outliers = total_negative + total_very_long
            
            # Get specific outlier records
            outlier_records_query = """
            SELECT 
                visit_occurrence_id,
                person_id,
                visit_start_date,
                visit_end_date,
                visit_end_date - visit_start_date as duration_days,
                CASE 
                    WHEN visit_end_date - visit_start_date < 0 THEN 'Negative duration'
                    WHEN visit_end_date - visit_start_date > 365 THEN 'Very long visit'
                    ELSE 'Other'
                END as issue_type
            FROM visit_occurrence 
            WHERE visit_start_date IS NOT NULL
            AND visit_end_date IS NOT NULL
            AND (
                visit_end_date - visit_start_date < 0
                OR visit_end_date - visit_start_date > 365
            )
            ORDER BY ABS(visit_end_date - visit_start_date) DESC
            LIMIT 50
            """
            
            try:
                outlier_records = self.database.execute_query(outlier_records_query)
                outlier_details = outlier_records.to_dict('records') if not outlier_records.empty else []
            except:
                outlier_details = []
            
            return {
                'status': 'PASS' if total_outliers == 0 else 'WARNING' if total_outliers < 20 else 'FAIL',
                'total_outliers': int(total_outliers),
                'negative_durations': int(total_negative),
                'very_long_visits': int(total_very_long),
                'data': result.to_dict('records'),
                'outlier_details': outlier_details,
                'message': f"Found {total_outliers} visit duration outliers"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check visit duration outliers'
            }
    
    def _check_distribution_anomalies(self) -> Dict[str, Any]:
        """Check for unusual data distributions"""
        try:
            # Check gender distribution
            gender_query = """
            SELECT 
                c.concept_name as gender,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM person p
            JOIN concept c ON p.gender_concept_id = c.concept_id
            GROUP BY c.concept_name
            ORDER BY count DESC
            """
            
            # Check age distribution
            age_distribution_query = """
            SELECT 
                CASE 
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) < 18 THEN 'Under 18'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) BETWEEN 18 AND 30 THEN '18-30'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) BETWEEN 31 AND 50 THEN '31-50'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) BETWEEN 51 AND 70 THEN '51-70'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) > 70 THEN 'Over 70'
                    ELSE 'Unknown'
                END as age_group,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM person
            WHERE year_of_birth IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) < 18 THEN 'Under 18'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) BETWEEN 18 AND 30 THEN '18-30'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) BETWEEN 31 AND 50 THEN '31-50'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) BETWEEN 51 AND 70 THEN '51-70'
                    WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - year_of_birth) > 70 THEN 'Over 70'
                    ELSE 'Unknown'
                END
            ORDER BY count DESC
            """
            
            # Check data density by year
            data_density_query = OMOPQueries.get_data_density_by_year()
            
            distribution_results = {}
            anomalies_found = []
            
            # Process gender distribution
            try:
                gender_result = self.database.execute_query(gender_query)
                if not gender_result.empty:
                    distribution_results['gender_distribution'] = gender_result.to_dict('records')
                    
                    # Check for anomalies in gender distribution
                    male_pct = gender_result[gender_result['gender'].str.contains('Male|MALE', case=False, na=False)]['percentage'].sum()
                    female_pct = gender_result[gender_result['gender'].str.contains('Female|FEMALE', case=False, na=False)]['percentage'].sum()
                    
                    if abs(male_pct - female_pct) > 30:  # More than 30% difference
                        anomalies_found.append(f"Gender distribution heavily skewed: {male_pct:.1f}% male, {female_pct:.1f}% female")
                    
                    if male_pct < 10 or female_pct < 10:
                        anomalies_found.append("One gender severely underrepresented (<10%)")
            except Exception as e:
                distribution_results['gender_distribution'] = []
                anomalies_found.append(f"Failed to analyze gender distribution: {str(e)}")
            
            # Process age distribution
            try:
                age_result = self.database.execute_query(age_distribution_query)
                if not age_result.empty:
                    distribution_results['age_distribution'] = age_result.to_dict('records')
                    
                    # Check for anomalies in age distribution
                    under_18_pct = age_result[age_result['age_group'] == 'Under 18']['percentage'].sum()
                    over_70_pct = age_result[age_result['age_group'] == 'Over 70']['percentage'].sum()
                    
                    if under_18_pct > 50:
                        anomalies_found.append(f"Unusually high percentage of patients under 18: {under_18_pct:.1f}%")
                    
                    if over_70_pct > 60:
                        anomalies_found.append(f"Unusually high percentage of patients over 70: {over_70_pct:.1f}%")
                    
                    # Check for missing age groups
                    age_groups = set(age_result['age_group'].tolist())
                    expected_groups = {'18-30', '31-50', '51-70'}
                    missing_groups = expected_groups - age_groups
                    if missing_groups:
                        anomalies_found.append(f"Missing age groups: {', '.join(missing_groups)}")
            except Exception as e:
                distribution_results['age_distribution'] = []
                anomalies_found.append(f"Failed to analyze age distribution: {str(e)}")
            
            # Process data density by year
            try:
                density_result = self.database.execute_query(data_density_query)
                if not density_result.empty:
                    distribution_results['data_density_by_year'] = density_result.to_dict('records')
                    
                    # Check for anomalies in yearly data
                    if len(density_result) > 1:
                        # Check for sudden drops in data volume
                        density_result['year'] = density_result['year'].astype(int)
                        density_result = density_result.sort_values('year')
                        
                        for i in range(1, len(density_result)):
                            current_conditions = density_result.iloc[i]['total_conditions']
                            previous_conditions = density_result.iloc[i-1]['total_conditions']
                            
                            if previous_conditions > 0:
                                pct_change = ((current_conditions - previous_conditions) / previous_conditions) * 100
                                
                                if pct_change < -50:  # More than 50% drop
                                    year = density_result.iloc[i]['year']
                                    anomalies_found.append(f"Significant data drop in {year}: {pct_change:.1f}% decrease")
                                elif pct_change > 200:  # More than 200% increase
                                    year = density_result.iloc[i]['year']
                                    anomalies_found.append(f"Unusual data spike in {year}: {pct_change:.1f}% increase")
            except Exception as e:
                distribution_results['data_density_by_year'] = []
                anomalies_found.append(f"Failed to analyze data density: {str(e)}")
            
            # Check for duplicates (potential data quality issue)
            try:
                duplicate_query = """
                WITH duplicate_conditions AS (
                    SELECT 
                        person_id,
                        condition_concept_id,
                        condition_start_date,
                        COUNT(*) as duplicate_count
                    FROM condition_occurrence
                    GROUP BY person_id, condition_concept_id, condition_start_date
                    HAVING COUNT(*) > 1
                )
                SELECT 
                    COUNT(*) as total_duplicate_groups,
                    SUM(duplicate_count) as total_duplicate_records
                FROM duplicate_conditions
                """
                
                duplicate_result = self.database.execute_query(duplicate_query)
                if not duplicate_result.empty:
                    dup_data = duplicate_result.iloc[0].to_dict()
                    distribution_results['duplicate_analysis'] = dup_data
                    
                    total_duplicates = dup_data.get('total_duplicate_records', 0)
                    if total_duplicates > 100:
                        anomalies_found.append(f"High number of duplicate condition records: {total_duplicates}")
            except Exception as e:
                distribution_results['duplicate_analysis'] = {}
                anomalies_found.append(f"Failed to analyze duplicates: {str(e)}")
            
            # Determine overall status
            if not anomalies_found:
                status = 'PASS'
            elif len(anomalies_found) <= 2:
                status = 'WARNING'
            else:
                status = 'FAIL'
            
            return {
                'status': status,
                'anomaly_count': len(anomalies_found),
                'anomalies_found': anomalies_found,
                'distribution_data': distribution_results,
                'message': f"Found {len(anomalies_found)} distribution anomalies"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': 'Failed to check distribution anomalies'
            }
