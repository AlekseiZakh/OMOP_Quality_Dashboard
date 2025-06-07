try:
    from .base_checker import BaseQualityChecker
    from .completeness import CompletenessChecker
    from .temporal import TemporalChecker
    from .concept_mapping import ConceptMappingChecker
    from .referential import ReferentialIntegrityChecker
    from .statistical import StatisticalOutlierChecker
except ImportError as e:
    # Handle relative import issues
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from base_checker import BaseQualityChecker
    from completeness import CompletenessChecker
    from temporal import TemporalChecker
    from concept_mapping import ConceptMappingChecker
    from referential import ReferentialIntegrityChecker
    from statistical import StatisticalOutlierChecker

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

__all__ = [
    'BaseQualityChecker',
    'CompletenessChecker', 
    'TemporalChecker',
    'ConceptMappingChecker',
    'ReferentialIntegrityChecker',
    'StatisticalOutlierChecker',
    'QUALITY_CHECKERS',
    'get_quality_checker'
]
