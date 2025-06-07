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
        
        # Mock table existence checks
        mock_db.table_exists.return_value = True
        
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
        # Mock the database connection validation
        completeness_checker.validate_database_connection = Mock(return_value=True)
        
        # Mock the individual check methods
        completeness_checker._check_table_completeness = Mock(return_value={'status': 'PASS'})
        completeness_checker._check_critical_fields = Mock(return_value={'status': 'PASS'})
        completeness_checker._check_person_completeness = Mock(return_value={'status': 'PASS'})
        
        results = completeness_checker.run_checks()
        
        assert isinstance(results, dict)
        assert 'table_completeness' in results
        assert 'critical_fields' in results
        assert 'person_completeness' in results
    
    def test_table_completeness_check(self, completeness_checker):
        """Test table completeness checking"""
        # Mock the database query response for null check
        mock_result = pd.DataFrame({
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
            'missing_ethnicity': [200]
        })
        
        completeness_checker.database.execute_query.return_value = mock_result
        completeness_checker.table_exists = Mock(return_value=True)
        
        result = completeness_checker._check_person_completeness()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'completeness_score' in result
        assert result['data']['total_persons'] == 1000
    
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
        completeness_checker.table_exists = Mock(return_value=True)
        
        result = completeness_checker._check_critical_fields()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'data' in result
    
    def test_completeness_check_database_connection_failure(self, completeness_checker):
        """Test completeness check when database connection fails"""
        completeness_checker.validate_database_connection = Mock(return_value=False)
        
        result = completeness_checker.run_checks()
        
        assert result['status'] == 'ERROR'
        assert 'Database connection failed' in result['error']
    
    def test_person_completeness_table_not_found(self, completeness_checker):
        """Test person completeness when table doesn't exist"""
        completeness_checker.table_exists = Mock(return_value=False)
        
        result = completeness_checker._check_person_completeness()
        
        assert result['status'] == 'ERROR'
        assert 'Person table not found' in result['message']


class TestTemporalChecker:
    """Test cases for TemporalChecker"""
    
    @pytest.fixture
    def temporal_checker(self):
        """Create TemporalChecker instance"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        return TemporalChecker(mock_db)
    
    def test_temporal_checker_initialization(self, temporal_checker):
        """Test TemporalChecker initialization"""
        assert temporal_checker.database is not None
        assert temporal_checker.results == {}
    
    def test_run_checks_structure(self, temporal_checker):
        """Test that run_checks returns expected structure"""
        # Mock the database connection validation
        temporal_checker.validate_database_connection = Mock(return_value=True)
        
        # Mock the individual check methods
        temporal_checker._check_future_dates = Mock(return_value={'status': 'PASS'})
        temporal_checker._check_birth_death_consistency = Mock(return_value={'status': 'PASS'})
        temporal_checker._check_events_after_death = Mock(return_value={'status': 'PASS'})
        
        results = temporal_checker.run_checks()
        
        assert isinstance(results, dict)
        expected_keys = [
            'future_dates', 'birth_death_consistency', 'events_after_death'
        ]
        for key in expected_keys:
            assert key in results
    
    def test_future_dates_check(self, temporal_checker):
        """Test future dates checking"""
        # Mock query result with future dates
        mock_result = pd.DataFrame({
            'future_count': [5]
        })
        
        temporal_checker.database.execute_query.return_value = mock_result
        temporal_checker.table_exists = Mock(return_value=True)
        
        result = temporal_checker._check_future_dates()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_future_dates' in result
        assert result['status'] == 'FAIL'  # Should fail when future dates found
    
    def test_future_dates_check_no_future_dates(self, temporal_checker):
        """Test future dates check when no future dates found"""
        # Mock query result with no future dates
        mock_result = pd.DataFrame({
            'future_count': [0]
        })
        
        temporal_checker.database.execute_query.return_value = mock_result
        temporal_checker.table_exists = Mock(return_value=True)
        
        result = temporal_checker._check_future_dates()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_future_dates' in result
        assert result['total_future_dates'] == 0
        assert result['status'] == 'PASS'  # Should pass when no future dates
    
    def test_birth_death_consistency(self, temporal_checker):
        """Test birth/death consistency checking"""
        # Mock query result with inconsistent dates
        mock_result = pd.DataFrame({
            'inconsistent_count': [2]
        })
        
        temporal_checker.database.execute_query.return_value = mock_result
        temporal_checker.table_exists = Mock(return_value=True)
        
        result = temporal_checker._check_birth_death_consistency()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'inconsistent_count' in result
        assert result['inconsistent_count'] == 2
        assert result['status'] == 'FAIL'
    
    def test_birth_death_consistency_table_missing(self, temporal_checker):
        """Test birth/death consistency when tables are missing"""
        def mock_table_exists(table_name):
            return table_name != 'death'  # Person exists, death doesn't
        
        temporal_checker.table_exists = Mock(side_effect=mock_table_exists)
        
        result = temporal_checker._check_birth_death_consistency()
        
        assert result['status'] == 'WARNING'
        assert 'not found' in result['message']
    
    def test_events_after_death_check(self, temporal_checker):
        """Test events after death checking"""
        # Mock query result with events after death
        mock_result = pd.DataFrame({
            'events_after_death': [2]
        })
        
        temporal_checker.database.execute_query.return_value = mock_result
        temporal_checker.table_exists = Mock(return_value=True)
        
        result = temporal_checker._check_events_after_death()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_events_after_death' in result
        assert result['status'] == 'FAIL'
    
    def test_events_after_death_no_death_table(self, temporal_checker):
        """Test events after death when death table doesn't exist"""
        def mock_table_exists(table_name):
            return table_name != 'death'
        
        temporal_checker.table_exists = Mock(side_effect=mock_table_exists)
        
        result = temporal_checker._check_events_after_death()
        
        assert result['status'] == 'WARNING'
        assert 'Death table not found' in result['message']


class TestConceptMappingChecker:
    """Test cases for ConceptMappingChecker"""
    
    @pytest.fixture
    def concept_checker(self):
        """Create ConceptMappingChecker instance"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        return ConceptMappingChecker(mock_db)
    
    def test_concept_checker_initialization(self, concept_checker):
        """Test ConceptMappingChecker initialization"""
        assert concept_checker.database is not None
        assert concept_checker.results == {}
    
    def test_run_checks_structure(self, concept_checker):
        """Test that run_checks returns expected structure"""
        # Mock the database connection validation
        concept_checker.validate_database_connection = Mock(return_value=True)
        
        # Mock the individual check methods
        concept_checker._check_unmapped_concepts = Mock(return_value={'status': 'PASS'})
        concept_checker._check_standard_concept_usage = Mock(return_value={'status': 'PASS'})
        concept_checker._check_vocabulary_coverage = Mock(return_value={'status': 'PASS'})
        
        results = concept_checker.run_checks()
        
        assert isinstance(results, dict)
        expected_keys = ['unmapped_concepts', 'standard_concept_usage', 'vocabulary_coverage']
        for key in expected_keys:
            assert key in results
    
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
    
    def test_unmapped_concepts_empty_result(self, concept_checker):
        """Test unmapped concepts check with empty result"""
        concept_checker.database.execute_query.return_value = pd.DataFrame()
        
        result = concept_checker._check_unmapped_concepts()
        
        assert result['status'] == 'WARNING'
        assert 'No data' in result['message']


class TestReferentialIntegrityChecker:
    """Test cases for ReferentialIntegrityChecker"""
    
    @pytest.fixture
    def referential_checker(self):
        """Create ReferentialIntegrityChecker instance"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        return ReferentialIntegrityChecker(mock_db)
    
    def test_referential_checker_initialization(self, referential_checker):
        """Test ReferentialIntegrityChecker initialization"""
        assert referential_checker.database is not None
        assert referential_checker.results == {}
    
    def test_run_checks_structure(self, referential_checker):
        """Test that run_checks returns expected structure"""
        # Mock the database connection validation
        referential_checker.validate_database_connection = Mock(return_value=True)
        
        # Mock the individual check methods
        referential_checker._check_foreign_key_violations = Mock(return_value={'status': 'PASS'})
        referential_checker._check_person_id_consistency = Mock(return_value={'status': 'PASS'})
        referential_checker._check_concept_id_references = Mock(return_value={'status': 'PASS'})
        
        results = referential_checker.run_checks()
        
        assert isinstance(results, dict)
        expected_keys = ['foreign_key_violations', 'person_id_consistency', 'concept_id_references']
        for key in expected_keys:
            assert key in results
    
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
        assert result['status'] == 'FAIL'
    
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
        assert result['status'] == 'FAIL'
    
    def test_concept_id_references(self, referential_checker):
        """Test concept ID references checking"""
        # Mock query result with concept reference analysis
        mock_result = pd.DataFrame({
            'table_name': ['condition_occurrence', 'drug_exposure'],
            'invalid_concept_references': [10, 5],
            'total_records': [1000, 500]
        })
        
        referential_checker.database.execute_query.return_value = mock_result
        
        result = referential_checker._check_concept_id_references()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_invalid_references' in result
        assert result['total_invalid_references'] == 15


class TestStatisticalOutlierChecker:
    """Test cases for StatisticalOutlierChecker"""
    
    @pytest.fixture
    def statistical_checker(self):
        """Create StatisticalOutlierChecker instance"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        return StatisticalOutlierChecker(mock_db)
    
    def test_statistical_checker_initialization(self, statistical_checker):
        """Test StatisticalOutlierChecker initialization"""
        assert statistical_checker.database is not None
        assert statistical_checker.results == {}
    
    def test_run_checks_structure(self, statistical_checker):
        """Test that run_checks returns expected structure"""
        # Mock the database connection validation
        statistical_checker.validate_database_connection = Mock(return_value=True)
        
        # Mock the individual check methods
        statistical_checker._check_age_outliers = Mock(return_value={'status': 'PASS'})
        statistical_checker._check_measurement_outliers = Mock(return_value={'status': 'PASS'})
        statistical_checker._check_demographic_inconsistencies = Mock(return_value={'status': 'PASS'})
        
        results = statistical_checker.run_checks()
        
        assert isinstance(results, dict)
        expected_keys = ['age_outliers', 'measurement_outliers', 'demographic_inconsistencies']
        for key in expected_keys:
            assert key in results
    
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
        assert 'outlier_count' in result
        assert result['outlier_count'] == 3
        assert result['status'] == 'FAIL'
    
    def test_measurement_outliers_check(self, statistical_checker):
        """Test measurement outliers checking"""
        # Mock query result with measurement outliers
        mock_result = pd.DataFrame({
            'measurement_concept_id': [3013682, 3004249, 3019962],
            'concept_name': ['Hemoglobin', 'Blood pressure', 'Weight'],
            'outlier_count': [5, 12, 3],
            'total_measurements': [1000, 800, 600],
            'outlier_percentage': [0.5, 1.5, 0.5]
        })
        
        statistical_checker.database.execute_query.return_value = mock_result
        
        result = statistical_checker._check_measurement_outliers()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_outliers' in result
        assert result['total_outliers'] == 20
    
    def test_demographic_inconsistencies_check(self, statistical_checker):
        """Test demographic inconsistencies checking"""
        # Mock query result with demographic issues
        mock_result = pd.DataFrame({
            'inconsistency_type': ['Gender changes', 'Birth year changes', 'Race changes'],
            'affected_persons': [2, 1, 3],
            'issue_description': ['Person has different genders across visits', 
                                'Birth year inconsistent', 
                                'Race concept changes']
        })
        
        statistical_checker.database.execute_query.return_value = mock_result
        
        result = statistical_checker._check_demographic_inconsistencies()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'total_inconsistent_persons' in result
        assert result['total_inconsistent_persons'] == 6
    
    def test_age_outliers_no_outliers(self, statistical_checker):
        """Test age outliers check when no outliers found"""
        # Mock query result with no outliers
        statistical_checker.database.execute_query.return_value = pd.DataFrame()
        
        result = statistical_checker._check_age_outliers()
        
        assert result['status'] == 'PASS'
        assert result['outlier_count'] == 0


class TestQualityCheckerFactory:
    """Test cases for quality checker factory functions"""
    
    def test_get_quality_checker_completeness(self):
        """Test getting completeness checker"""
        mock_db = Mock()
        checker = get_quality_checker('completeness', mock_db)
        
        assert isinstance(checker, CompletenessChecker)
        assert checker.database == mock_db
    
    def test_get_quality_checker_temporal(self):
        """Test getting temporal checker"""
        mock_db = Mock()
        checker = get_quality_checker('temporal', mock_db)
        
        assert isinstance(checker, TemporalChecker)
        assert checker.database == mock_db
    
    def test_get_quality_checker_concept_mapping(self):
        """Test getting concept mapping checker"""
        mock_db = Mock()
        checker = get_quality_checker('concept_mapping', mock_db)
        
        assert isinstance(checker, ConceptMappingChecker)
        assert checker.database == mock_db
    
    def test_get_quality_checker_referential(self):
        """Test getting referential integrity checker"""
        mock_db = Mock()
        checker = get_quality_checker('referential', mock_db)
        
        assert isinstance(checker, ReferentialIntegrityChecker)
        assert checker.database == mock_db
    
    def test_get_quality_checker_statistical(self):
        """Test getting statistical outlier checker"""
        mock_db = Mock()
        checker = get_quality_checker('statistical', mock_db)
        
        assert isinstance(checker, StatisticalOutlierChecker)
        assert checker.database == mock_db
    
    def test_get_quality_checker_invalid_type(self):
        """Test getting invalid checker type"""
        mock_db = Mock()
        
        with pytest.raises(ValueError):
            get_quality_checker('invalid_type', mock_db)
    
    def test_quality_checkers_registry(self):
        """Test QUALITY_CHECKERS registry"""
        assert isinstance(QUALITY_CHECKERS, dict)
        assert 'completeness' in QUALITY_CHECKERS
        assert 'temporal' in QUALITY_CHECKERS
        assert 'concept_mapping' in QUALITY_CHECKERS
        assert 'referential' in QUALITY_CHECKERS
        assert 'statistical' in QUALITY_CHECKERS
        
        # Check that all values are checker classes
        for checker_name, checker_class in QUALITY_CHECKERS.items():
            assert issubclass(checker_class, BaseQualityChecker)


class TestQualityCheckerErrorHandling:
    """Test error handling in quality checkers"""
    
    def test_completeness_checker_query_error(self):
        """Test completeness checker handling query errors"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("Database error")
        mock_db.table_exists.return_value = True
        
        checker = CompletenessChecker(mock_db)
        checker.validate_database_connection = Mock(return_value=True)
        
        result = checker._check_person_completeness()
        
        assert result['status'] == 'ERROR'
        assert 'error' in result
    
    def test_temporal_checker_query_error(self):
        """Test temporal checker handling query errors"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("Database error")
        mock_db.table_exists.return_value = True
        
        checker = TemporalChecker(mock_db)
        
        result = checker._check_future_dates()
        
        assert result['status'] == 'ERROR'
        assert 'error' in result
    
    def test_concept_mapping_checker_query_error(self):
        """Test concept mapping checker handling query errors"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("Database error")
        mock_db.table_exists.return_value = True
        
        checker = ConceptMappingChecker(mock_db)
        
        result = checker._check_unmapped_concepts()
        
        assert result['status'] == 'ERROR'
        assert 'error' in result


class TestQualityCheckerIntegration:
    """Integration tests for quality checkers"""
    
    def test_run_all_quality_checks(self):
        """Test running all quality checkers together"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        mock_db.execute_query.return_value = pd.DataFrame({'test': [1]})
        
        checkers = [
            CompletenessChecker(mock_db),
            TemporalChecker(mock_db),
            ConceptMappingChecker(mock_db),
            ReferentialIntegrityChecker(mock_db),
            StatisticalOutlierChecker(mock_db)
        ]
        
        all_results = {}
        for checker in checkers:
            checker.validate_database_connection = Mock(return_value=True)
            # Mock all check methods to return simple success
            for method_name in dir(checker):
                if method_name.startswith('_check_'):
                    setattr(checker, method_name, Mock(return_value={'status': 'PASS'}))
            
            results = checker.run_checks()
            all_results[checker.__class__.__name__] = results
        
        assert len(all_results) == 5
        assert all(isinstance(result, dict) for result in all_results.values())
    
    def test_quality_checker_logging(self):
        """Test that quality checkers log appropriately"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        mock_db.execute_query.return_value = pd.DataFrame({'test': [1]})
        
        checker = CompletenessChecker(mock_db)
        checker.validate_database_connection = Mock(return_value=True)
        checker._check_table_completeness = Mock(return_value={'status': 'PASS'})
        checker._check_critical_fields = Mock(return_value={'status': 'PASS'})
        checker._check_person_completeness = Mock(return_value={'status': 'PASS'})
        
        # Mock logger
        checker.logger = Mock()
        
        results = checker.run_checks()
        
        # Verify that logging methods were called
        assert checker.logger.info.called or checker.logger.debug.called
    
    def test_quality_checker_summary_generation(self):
        """Test summary generation across multiple checkers"""
        mock_db = Mock()
        
        # Create checker with mixed results
        checker = CompletenessChecker(mock_db)
        checker.results = {
            'check1': {'status': 'PASS'},
            'check2': {'status': 'FAIL'},
            'check3': {'status': 'WARNING'},
            'check4': {'status': 'ERROR'}
        }
        
        summary = checker.get_summary()
        
        assert summary['total_checks'] == 4
        assert summary['passed_checks'] == 1
        assert summary['failed_checks'] == 1
        assert summary['warning_checks'] == 1
        assert summary['error_checks'] == 1


class TestQualityCheckerEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_database_tables(self):
        """Test quality checkers with empty database tables"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        mock_db.execute_query.return_value = pd.DataFrame()  # Empty result
        
        checker = CompletenessChecker(mock_db)
        checker.validate_database_connection = Mock(return_value=True)
        
        result = checker._check_person_completeness()
        
        assert result['status'] in ['ERROR', 'WARNING']
    
    def test_missing_required_tables(self):
        """Test quality checkers when required tables are missing"""
        mock_db = Mock()
        mock_db.table_exists.return_value = False  # No tables exist
        
        checker = TemporalChecker(mock_db)
        checker.validate_database_connection = Mock(return_value=True)
        
        result = checker._check_birth_death_consistency()
        
        assert result['status'] == 'WARNING'
        assert 'not found' in result['message']
    
    def test_null_database_responses(self):
        """Test handling of null/None database responses"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        mock_db.execute_query.return_value = None
        
        checker = StatisticalOutlierChecker(mock_db)
        
        result = checker._check_age_outliers()
        
        assert result['status'] == 'ERROR'
    
    def test_malformed_query_results(self):
        """Test handling of malformed query results"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        
        # Return DataFrame with unexpected columns
        mock_db.execute_query.return_value = pd.DataFrame({
            'unexpected_column': [1, 2, 3],
            'another_unexpected': ['a', 'b', 'c']
        })
        
        checker = ConceptMappingChecker(mock_db)
        
        result = checker._check_unmapped_concepts()
        
        # Should handle gracefully and return error status
        assert result['status'] in ['ERROR', 'WARNING']
    
    def test_very_large_numbers(self):
        """Test handling of very large numbers in results"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        
        # Return DataFrame with very large numbers
        mock_db.execute_query.return_value = pd.DataFrame({
            'total_persons': [999999999],
            'missing_gender': [999999998],
            'missing_birth_year': [999999997],
            'missing_race': [999999996],
            'missing_ethnicity': [999999995]
        })
        
        checker = CompletenessChecker(mock_db)
        
        result = checker._check_person_completeness()
        
        assert isinstance(result, dict)
        assert 'completeness_score' in result
        # Should handle large numbers without crashing
    
    def test_special_characters_in_data(self):
        """Test handling of special characters in database responses"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        
        # Return DataFrame with special characters
        mock_db.execute_query.return_value = pd.DataFrame({
            'domain': ['Condition™', 'Drug®', 'Procedure©'],
            'total_records': [1000, 500, 300],
            'unmapped_count': [50, 25, 15],
            'unmapped_percentage': [5.0, 5.0, 5.0]
        })
        
        checker = ConceptMappingChecker(mock_db)
        
        result = checker._check_unmapped_concepts()
        
        assert isinstance(result, dict)
        assert result['status'] in ['PASS', 'WARNING', 'FAIL']


class TestQualityCheckerPerformance:
    """Test performance-related aspects of quality checkers"""
    
    def test_large_dataset_handling(self):
        """Test quality checkers with large datasets"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        
        # Simulate large dataset
        large_data = pd.DataFrame({
            'person_id': range(100000),
            'year_of_birth': [1980] * 100000,
            'current_age': [43] * 100000,
            'issue_type': ['Normal'] * 100000
        })
        
        mock_db.execute_query.return_value = large_data
        
        checker = StatisticalOutlierChecker(mock_db)
        
        # Should handle large datasets without issues
        result = checker._check_age_outliers()
        
        assert isinstance(result, dict)
        assert 'outlier_count' in result
    
    def test_concurrent_checker_execution(self):
        """Test running multiple checkers concurrently (simulation)"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        mock_db.execute_query.return_value = pd.DataFrame({'test': [1]})
        
        checkers = [
            CompletenessChecker(mock_db),
            TemporalChecker(mock_db),
            ConceptMappingChecker(mock_db)
        ]
        
        results = []
        for checker in checkers:
            checker.validate_database_connection = Mock(return_value=True)
            # Mock all check methods
            for method_name in dir(checker):
                if method_name.startswith('_check_'):
                    setattr(checker, method_name, Mock(return_value={'status': 'PASS'}))
            
            result = checker.run_checks()
            results.append(result)
        
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results)


class TestQualityCheckerConfiguration:
    """Test configuration-related functionality"""
    
    def test_checker_with_custom_thresholds(self):
        """Test quality checkers with custom thresholds"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        
        # Test completeness checker with custom threshold
        mock_db.execute_query.return_value = pd.DataFrame({
            'total_persons': [1000],
            'missing_gender': [150],  # 15% missing
            'missing_birth_year': [100],  # 10% missing
            'missing_race': [200],
            'missing_ethnicity': [300]
        })
        
        checker = CompletenessChecker(mock_db)
        
        result = checker._check_person_completeness()
        
        # Should handle different threshold scenarios
        assert isinstance(result, dict)
        assert 'completeness_score' in result
    
    def test_checker_status_thresholds(self):
        """Test quality checker status determination based on thresholds"""
        mock_db = Mock()
        mock_db.table_exists.return_value = True
        
        # Test different scenarios for temporal checker
        test_cases = [
            ({'future_count': [0]}, 'PASS'),  # No future dates
            ({'future_count': [5]}, 'FAIL'),  # Some future dates
            ({'future_count': [100]}, 'FAIL')  # Many future dates
        ]
        
        checker = TemporalChecker(mock_db)
        
        for mock_data, expected_status in test_cases:
            mock_db.execute_query.return_value = pd.DataFrame(mock_data)
            result = checker._check_future_dates()
            
            assert result['status'] == expected_status


class TestQualityCheckerDocumentation:
    """Test that quality checkers have proper documentation"""
    
    def test_checker_class_docstrings(self):
        """Test that all checker classes have docstrings"""
        checker_classes = [
            CompletenessChecker,
            TemporalChecker,
            ConceptMappingChecker,
            ReferentialIntegrityChecker,
            StatisticalOutlierChecker
        ]
        
        for checker_class in checker_classes:
            assert checker_class.__doc__ is not None
            assert len(checker_class.__doc__.strip()) > 0
    
    def test_checker_method_docstrings(self):
        """Test that key checker methods have docstrings"""
        mock_db = Mock()
        checker = CompletenessChecker(mock_db)
        
        # Test that run_checks has docstring
        assert checker.run_checks.__doc__ is not None
        
        # Test that private check methods have docstrings
        private_methods = [method for method in dir(checker) 
                          if method.startswith('_check_')]
        
        for method_name in private_methods:
            method = getattr(checker, method_name)
            if callable(method):
                assert method.__doc__ is not None, f"Method {method_name} missing docstring"


class TestQualityCheckerValidation:
    """Test input validation in quality checkers"""
    
    def test_invalid_database_object(self):
        """Test quality checkers with invalid database objects"""
        # Test with None database
        with pytest.raises(Exception):
            CompletenessChecker(None)
        
        # Test with invalid database object
        with pytest.raises(Exception):
            TemporalChecker("not_a_database")
    
    def test_checker_method_parameter_validation(self):
        """Test parameter validation in checker methods"""
        mock_db = Mock()
        checker = CompletenessChecker(mock_db)
        
        # Test _get_null_check_query with invalid table name
        result = checker._get_null_check_query("nonexistent_table")
        assert result is None
        
        # Test _get_null_check_query with valid table name
        result = checker._get_null_check_query("person")
        assert isinstance(result, str)
        assert "person" in result


if __name__ == "__main__":
    # Run tests with coverage reporting
    pytest.main([__file__, "-v", "--cov=app.quality_checks", "--cov-report=html"])
