import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

# Add app directory to path for imports
import sys
from pathlib import Path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from quality_checks.base_checker import BaseQualityChecker
from quality_checks.completeness import CompletenessChecker
from quality_checks.temporal import TemporalChecker
from quality_checks.concept_mapping import ConceptMappingChecker
from quality_checks.referential import ReferentialIntegrityChecker
from quality_checks.statistical import StatisticalOutlierChecker
from quality_checks import get_quality_checker, QUALITY_CHECKERS


class TestBaseQualityChecker:
    """Test cases for BaseQualityChecker"""
    
    def test_base_checker_abstract_methods(self):
        """Test that BaseQualityChecker is abstract"""
        mock_database = Mock()
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            BaseQualityChecker(mock_database)
    
    def test_quality_checker_summary(self):
        """Test summary generation functionality"""
        # Create a concrete implementation for testing
        class TestChecker(BaseQualityChecker):
            def run_checks(self):
                return {
                    'test1': {'status': 'PASS'},
                    'test2': {'status': 'FAIL'},
                    'test3': {'status': 'WARNING'}
                }
        
        mock_database = Mock()
        checker = TestChecker(mock_database)
        checker.results = checker.run_checks()
        
        summary = checker.get_summary()
        
        assert summary['total_checks'] == 3
        assert summary['passed_checks'] == 1
        assert summary['failed_checks'] == 1
        assert summary['warning_checks'] == 1


class TestCompletenessChecker:
    """Test cases for CompletenessChecker"""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database with sample data"""
        mock_db = Mock()
        
        # Mock table list
        mock_db.get_table_list.return_value = pd.DataFrame({
            'table_name': ['person', 'condition_occurrence', 'drug_exposure'],
            'row_count': [1000, 5000, 3000]
        })
        
        return mock_db
    
    @pytest.fixture
    def completeness_checker(self, mock_database):
        """Create CompletenessChecker instance"""
        return CompletenessChecker(mock_database)
    
    def test_completeness_checker_initialization(self, mock_database):
        """Test CompletenessChecker initialization"""
        checker = CompletenessChecker(mock_database)
        assert checker.database == mock_database
        assert checker.results == {}
    
    def test_run_checks_structure(self, completeness_checker):
        """Test that run_checks returns expected structure"""
        # Mock the individual check methods
        completeness_checker._check_table_completeness = Mock(return_value={'status': 'PASS'})
        completeness_checker._check_critical_fields = Mock(return_value={'status': 'PASS'})
        completeness_checker._check_person_completeness = Mock(return_value={'status': 'PASS'})
        completeness_checker._check_domain_completeness = Mock(return_value={'status': 'PASS'})
        
        results = completeness_checker.run_checks()
        
        assert isinstance(results, dict)
        assert 'table_completeness' in results
        assert 'critical_fields' in results
        assert 'person_completeness' in results
        assert 'domain_completeness' in results
    
    def test_table_completeness_check(self, completeness_checker):
        """Test table completeness checking"""
        # Mock the database query response
        mock_result = pd.DataFrame({
            'table_name': ['person'],
            'total_rows': [1000],
            'null_records': [50],
            'null_percentage': [5.0]
        })
        
        completeness_checker.database.execute_query.return_value = mock_result
        
        result = completeness_checker._check_table_completeness()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'data' in result
        assert 'message' in result
    
    def test_person_completeness_check(self, completeness_checker):
        """Test person table completeness checking"""
        # Mock person demographics query result
        mock_result = pd.DataFrame({
            'total_persons': [1000],
            'missing_gender': [10],
            'missing_birth_year': [5],
            'missing_race': [100],
            'missing_ethnicity': [200],
            'completeness_score': [92.5]
        })
        
        completeness_checker.database.execute_query.return_value = mock_result
        
        result = completeness_checker._check_person_completeness()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'completeness_score' in result
        assert result['completeness_score'] == 92.5
    
    def test_critical_fields_check(self, completeness_checker):
        """Test critical fields checking"""
        # Mock responses for critical field queries
        def mock_execute_query(query):
            if "person_id IS NULL" in query:
                return pd.DataFrame({'null_count': [0]})
            elif "condition_concept_id IS NULL" in query:
                return pd.DataFrame({'null_count': [5]})
            else:
                return pd.DataFrame({'null_count': [0]})
        
        completeness_checker.database.execute_query.side_effect = mock_execute_query
        
        result = completeness_checker._check_critical_fields()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_failures' in result
        assert 'data' in result


class TestTemporalChecker:
    """Test cases for TemporalChecker"""
    
    @pytest.fixture
    def temporal_checker(self):
        """Create TemporalChecker instance"""
        mock_db = Mock()
        return TemporalChecker(mock_db)
    
    def test_temporal_checker_initialization(self, temporal_checker):
        """Test TemporalChecker initialization"""
        assert temporal_checker.database is not None
        assert temporal_checker.results == {}
    
    def test_run_checks_structure(self, temporal_checker):
        """Test that run_checks returns expected structure"""
        # Mock the individual check methods
        temporal_checker._check_future_dates = Mock(return_value={'status': 'PASS'})
        temporal_checker._check_birth_death_consistency = Mock(return_value={'status': 'PASS'})
        temporal_checker._check_events_after_death = Mock(return_value={'status': 'PASS'})
        temporal_checker._check_visit_date_consistency = Mock(return_value={'status': 'PASS'})
        temporal_checker._check_age_temporal_issues = Mock(return_value={'status': 'PASS'})
        
        results = temporal_checker.run_checks()
        
        assert isinstance(results, dict)
        expected_keys = [
            'future_dates', 'birth_death_consistency', 'events_after_death',
            'visit_date_consistency', 'age_temporal_issues'
        ]
        for key in expected_keys:
            assert key in results
    
    def test_future_dates_check(self, temporal_checker):
        """Test future dates checking"""
        # Mock query result with future dates
        mock_result = pd.DataFrame({
            'table_name': ['condition_occurrence', 'drug_exposure'],
            'date_field': ['condition_start_date', 'drug_exposure_start_date'],
            'future_count': [5, 3]
        })
        
        temporal_checker.database.execute_query.return_value = mock_result
        
        result = temporal_checker._check_future_dates()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_future_dates' in result
        assert result['total_future_dates'] == 8
        assert result['status'] == 'FAIL'  # Should fail when future dates found
    
    def test_birth_death_consistency(self, temporal_checker):
        """Test birth/death consistency checking"""
        # Mock query result with inconsistent dates
        mock_result = pd.DataFrame({
            'person_id': [1, 2],
            'year_of_birth': [1990, 1985],
            'death_date': ['1985-01-01', '1980-01-01']
        })
        
        temporal_checker.database.execute_query.return_value = mock_result
        
        result = temporal_checker._check_birth_death_consistency()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'inconsistent_count' in result
    
    def test_events_after_death_check(self, temporal_checker):
        """Test events after death checking"""
        # Mock query result with events after death
        mock_result = pd.DataFrame({
            'event_type': ['condition_occurrence', 'drug_exposure'],
            'events_after_death': [2, 1]
        })
        
        temporal_checker.database.execute_query.return_value = mock_result
        
        result = temporal_checker._check_events_after_death()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_events_after_death' in result
        assert result['total_events_after_death'] == 3


class TestConceptMappingChecker:
    """Test cases for ConceptMappingChecker"""
    
    @pytest.fixture
    def concept_checker(self):
        """Create ConceptMappingChecker instance"""
        mock_db = Mock()
        return ConceptMappingChecker(mock_db)
    
    def test_concept_checker_initialization(self, concept_checker):
        """Test ConceptMappingChecker initialization"""
        assert concept_checker.database is not None
        assert concept_checker.results == {}
    
    def test_unmapped_concepts_check(self, concept_checker):
        """Test unmapped concepts checking"""
        # Mock query result with unmapped concepts
        mock_result = pd.DataFrame({
            'domain': ['Condition', 'Drug', 'Procedure'],
            'total_records': [10000, 5000, 3000],
            'unmapped_count': [500, 100, 50],
            'unmapped_percentage': [5.0, 2.0, 1.7]
        })
        
        concept_checker.database.execute_query.return_value = mock_result
        
        result = concept_checker._check_unmapped_concepts()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_unmapped' in result
        assert 'max_unmapped_percentage' in result
        assert result['total_unmapped'] == 650
        assert result['max_unmapped_percentage'] == 5.0
    
    def test_standard_concept_usage(self, concept_checker):
        """Test standard concept usage checking"""
        # Mock query result with standard concept usage
        mock_result = pd.DataFrame({
            'standard_concept': ['S', 'C', None],
            'total_usage': [8000, 1500, 500],
            'percentage': [80.0, 15.0, 5.0]
        })
        
        concept_checker.database.execute_query.return_value = mock_result
        
        result = concept_checker._check_standard_concept_usage()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'standard_percentage' in result
        assert result['standard_percentage'] == 80.0
        assert result['status'] == 'PASS'  # 80% meets threshold
    
    def test_vocabulary_coverage(self, concept_checker):
        """Test vocabulary coverage checking"""
        # Mock query result with vocabulary usage
        mock_result = pd.DataFrame({
            'vocabulary_id': ['SNOMED', 'ICD10CM', 'LOINC'],
            'vocabulary_name': ['SNOMED CT', 'ICD-10-CM', 'LOINC'],
            'unique_concepts': [5000, 2000, 1500],
            'condition_usage': [8000, 2000, 0],
            'drug_usage': [0, 0, 0],
            'procedure_usage': [1000, 500, 3000]
        })
        
        concept_checker.database.execute_query.return_value = mock_result
        
        result = concept_checker._check_vocabulary_coverage()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_vocabularies' in result
        assert result['total_vocabularies'] == 3


class TestReferentialIntegrityChecker:
    """Test cases for ReferentialIntegrityChecker"""
    
    @pytest.fixture
    def referential_checker(self):
        """Create ReferentialIntegrityChecker instance"""
        mock_db = Mock()
        return ReferentialIntegrityChecker(mock_db)
    
    def test_foreign_key_violations(self, referential_checker):
        """Test foreign key violations checking"""
        # Mock query result with violations
        mock_result = pd.DataFrame({
            'relationship': ['condition_occurrence -> person', 'drug_exposure -> person'],
            'violation_count': [5, 2]
        })
        
        referential_checker.database.execute_query.return_value = mock_result
        
        result = referential_checker._check_foreign_key_violations()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_violations' in result
        assert result['total_violations'] == 7
    
    def test_person_id_consistency(self, referential_checker):
        """Test person ID consistency checking"""
        # Mock query result with person ID analysis
        mock_result = pd.DataFrame({
            'persons_in_person_table': [1000],
            'persons_in_clinical_tables': [1005],
            'clinical_persons_missing_from_person_table': [5],
            'total_missing_references': [15]
        })
        
        referential_checker.database.execute_query.return_value = mock_result
        
        result = referential_checker._check_person_id_consistency()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'missing_persons' in result
        assert result['missing_persons'] == 5


class TestStatisticalOutlierChecker:
    """Test cases for StatisticalOutlierChecker"""
    
    @pytest.fixture
    def statistical_checker(self):
        """Create StatisticalOutlierChecker instance"""
        mock_db = Mock()
        return StatisticalOutlierChecker(mock_db)
    
    def test_age_outliers_check(self, statistical_checker):
        """Test age outliers checking"""
        # Mock query result with age outliers
        mock_result = pd.DataFrame({
            'person_id': [1, 2, 3],
            'year_of_birth': [1800, 2025, 1900],
            'current_age': [224, -1, 124],
            'issue_type': ['Birth year too early', 'Future birth year', 'Age over 120']
        })
        
        statistical_checker.database.execute_query.return_value = mock_result
        
        result = statistical_checker._check_age_outliers()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'outl
