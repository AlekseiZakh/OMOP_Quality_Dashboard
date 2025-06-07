import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add app directory to path for imports
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

try:
    from visualizations.dashboard_components import DashboardComponents, QualityCheckRenderer
    from visualizations.charts import OMOPCharts, InteractiveCharts
    from utils.config import ConfigManager, StreamlitConfig
    from utils.helpers import DataHelpers, DateHelpers, StreamlitHelpers
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestDashboardComponents:
    """Test cases for dashboard UI components"""
    
    def test_render_status_badge(self):
        """Test status badge rendering"""
        # Test different status types
        pass_badge = DashboardComponents.render_status_badge("PASS", "All checks passed")
        warning_badge = DashboardComponents.render_status_badge("WARNING", "Some issues found")
        fail_badge = DashboardComponents.render_status_badge("FAIL", "Critical issues")
        error_badge = DashboardComponents.render_status_badge("ERROR", "System error")
        
        assert isinstance(pass_badge, str)
        assert "PASS" in pass_badge
        assert "#28a745" in pass_badge  # Green color
        
        assert isinstance(warning_badge, str)
        assert "WARNING" in warning_badge
        assert "#ffc107" in warning_badge  # Yellow color
        
        assert isinstance(fail_badge, str)
        assert "FAIL" in fail_badge
        assert "#dc3545" in fail_badge  # Red color
        
        assert isinstance(error_badge, str)
        assert "ERROR" in error_badge
        assert "#6c757d" in error_badge  # Gray color
    
    def test_render_status_badge_edge_cases(self):
        """Test status badge with edge cases"""
        # Test unknown status
        unknown_badge = DashboardComponents.render_status_badge("UNKNOWN")
        assert isinstance(unknown_badge, str)
        assert "ERROR" in unknown_badge  # Should default to ERROR styling
        
        # Test empty message
        empty_badge = DashboardComponents.render_status_badge("PASS", "")
        assert isinstance(empty_badge, str)
        assert "PASS" in empty_badge
    
    @patch('streamlit.metric')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_render_metric_card(self, mock_markdown, mock_columns, mock_metric):
        """Test metric card rendering"""
        # Mock Streamlit columns
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        DashboardComponents.render_metric_card(
            title="Test Metric",
            value=100,
            delta=5,
            status="PASS",
            help_text="This is a test metric"
        )
        
        # Verify Streamlit functions were called
        mock_columns.assert_called_once()
        mock_col1.__enter__.assert_called_once()
        mock_col2.__enter__.assert_called_once()
    
    def test_render_quality_score_gauge(self):
        """Test quality score gauge creation"""
        fig = DashboardComponents.render_quality_score_gauge(85.5, "Test Quality Score")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'indicator'
        assert fig.data[0].value == 85.5
    
    def test_render_quality_score_gauge_edge_cases(self):
        """Test quality score gauge with edge cases"""
        # Test with score > 100
        fig = DashboardComponents.render_quality_score_gauge(150, "Test")
        assert isinstance(fig, go.Figure)
        assert fig.data[0].value == 100  # Should be clamped to 100
        
        # Test with negative score
        fig = DashboardComponents.render_quality_score_gauge(-10, "Test")
        assert isinstance(fig, go.Figure)
        assert fig.data[0].value == 0  # Should be clamped to 0
        
        # Test with None score
        fig = DashboardComponents.render_quality_score_gauge(None, "Test")
        assert isinstance(fig, go.Figure)
        assert fig.data[0].value == 0
    
    def test_render_status_distribution_pie(self):
        """Test status distribution pie chart"""
        status_counts = {
            'PASS': 10,
            'WARNING': 3,
            'FAIL': 2,
            'ERROR': 1
        }
        
        fig = DashboardComponents.render_status_distribution_pie(status_counts)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'pie'
        assert list(fig.data[0].values) == [10, 3, 2, 1]
    
    def test_render_status_distribution_pie_empty(self):
        """Test status distribution pie chart with empty data"""
        status_counts = {}
        
        fig = DashboardComponents.render_status_distribution_pie(status_counts)
        
        assert fig is None
    
    def test_render_quality_trend_chart(self):
        """Test quality trend chart creation"""
        trend_data = pd.DataFrame({
            'date': ['2023-01-01', '2023-02-01', '2023-03-01'],
            'quality_score': [85, 87, 92]
        })
        
        fig = DashboardComponents.render_quality_trend_chart(
            trend_data, 'date', 'quality_score', "Quality Trend"
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'scatter'
    
    def test_render_quality_trend_chart_empty_data(self):
        """Test quality trend chart with empty data"""
        empty_data = pd.DataFrame()
        
        fig = DashboardComponents.render_quality_trend_chart(
            empty_data, 'date', 'quality_score'
        )
        
        assert fig is None
    
    def test_render_table_completeness_heatmap(self):
        """Test table completeness heatmap"""
        completeness_data = [
            {'table_name': 'person', 'null_percentage': 5},
            {'table_name': 'condition_occurrence', 'null_percentage': 10},
            {'table_name': 'drug_exposure', 'null_percentage': 2}
        ]
        
        fig = DashboardComponents.render_table_completeness_heatmap(completeness_data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'heatmap'
    
    @patch('streamlit.expander')
    @patch('streamlit.dataframe')
    def test_render_expandable_details(self, mock_dataframe, mock_expander):
        """Test expandable details section"""
        mock_expander_context = Mock()
        mock_expander.return_value.__enter__ = Mock(return_value=mock_expander_context)
        mock_expander.return_value.__exit__ = Mock(return_value=None)
        
        test_data = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        
        DashboardComponents.render_expandable_details("Test Details", test_data, "test_key")
        
        mock_expander.assert_called_once()
    
    @patch('streamlit.download_button')
    def test_render_download_section(self, mock_download_button):
        """Test download section rendering"""
        test_data = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        
        DashboardComponents.render_download_section(test_data, "test_data")
        
        # Should create download buttons for different formats
        assert mock_download_button.call_count >= 2
    
    @patch('streamlit.progress')
    @patch('streamlit.caption')
    def test_render_progress_bar(self, mock_caption, mock_progress):
        """Test progress bar rendering"""
        DashboardComponents.render_progress_bar(7, 10, "Test Progress")
        
        mock_progress.assert_called_once_with(0.7)
        mock_caption.assert_called_once_with("Test Progress: 7/10 (70.0%)")
    
    @patch('streamlit.progress')
    @patch('streamlit.caption')
    def test_render_progress_bar_edge_cases(self, mock_caption, mock_progress):
        """Test progress bar with edge cases"""
        # Test with zero total
        DashboardComponents.render_progress_bar(5, 0, "Test Progress")
        mock_progress.assert_called_with(0)
        
        # Test with current > total
        DashboardComponents.render_progress_bar(15, 10, "Test Progress")
        mock_progress.assert_called_with(1.0)  # Should be clamped to 1.0


class TestQualityCheckRenderer:
    """Test cases for quality check result rendering"""
    
    def test_render_check_results_structure(self):
        """Test quality check results rendering structure"""
        mock_results = {
            'completeness_check': {
                'status': 'PASS',
                'message': 'All completeness checks passed',
                'data': [{'table': 'person', 'completeness': 95}]
            },
            'temporal_check': {
                'status': 'WARNING',
                'message': 'Some temporal issues found',
                'data': [{'issue': 'future_dates', 'count': 5}]
            }
        }
        
        # Test that the method exists and can be called
        assert hasattr(QualityCheckRenderer, 'render_check_results')
        assert callable(QualityCheckRenderer.render_check_results)
    
    def test_extract_summary(self):
        """Test summary extraction from results"""
        mock_results = {
            'check1': {'status': 'PASS'},
            'check2': {'status': 'FAIL'},
            'check3': {'status': 'WARNING'},
            'check4': {'status': 'PASS'}
        }
        
        summary = QualityCheckRenderer._extract_summary(mock_results)
        
        assert isinstance(summary, dict)
        assert 'Total Checks' in summary
        assert summary['Total Checks']['value'] == 4
        assert 'Passed' in summary
        assert summary['Passed']['value'] == 2
        assert 'Failed' in summary
        assert summary['Failed']['value'] == 1
    
    def test_extract_summary_empty_results(self):
        """Test summary extraction with empty results"""
        summary = QualityCheckRenderer._extract_summary({})
        assert isinstance(summary, dict)
        # Should handle empty results gracefully
    
    def test_extract_summary_invalid_results(self):
        """Test summary extraction with invalid results"""
        invalid_results = {
            'check1': 'not_a_dict',
            'check2': {'no_status': 'value'}
        }
        
        summary = QualityCheckRenderer._extract_summary(invalid_results)
        assert isinstance(summary, dict)
        # Should handle invalid data gracefully


class TestOMOPCharts:
    """Test cases for OMOP-specific charts"""
    
    def test_create_completeness_bar_chart(self):
        """Test completeness bar chart creation"""
        completeness_data = [
            {'table_name': 'person', 'total_rows': 1000, 'null_percentage': 5},
            {'table_name': 'condition_occurrence', 'total_rows': 5000, 'null_percentage': 10},
            {'table_name': 'drug_exposure', 'total_rows': 3000, 'null_percentage': 2}
        ]
        
        fig = OMOPCharts.create_completeness_bar_chart(completeness_data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'bar'
        assert len(fig.data[0].x) == 3
    
    def test_create_completeness_bar_chart_empty(self):
        """Test completeness bar chart with empty data"""
        fig = OMOPCharts.create_completeness_bar_chart([])
        
        assert isinstance(fig, go.Figure)
        # Should create an empty chart with message
    
    def test_create_temporal_issues_chart(self):
        """Test temporal issues chart creation"""
        temporal_data = {
            'future_dates': {
                'data': [
                    {'table': 'condition_occurrence', 'future_count': 5},
                    {'table': 'drug_exposure', 'future_count': 3}
                ]
            },
            'events_after_death': {
                'data': [
                    {'event_type': 'condition_occurrence', 'events_after_death': 2}
                ]
            }
        }
        
        fig = OMOPCharts.create_temporal_issues_chart(temporal_data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'bar'
    
    def test_create_concept_mapping_sunburst(self):
        """Test concept mapping sunburst chart"""
        mapping_data = {
            'unmapped_concepts': {
                'data': [
                    {
                        'domain': 'Condition',
                        'total_records': 10000,
                        'unmapped_count': 500
                    },
                    {
                        'domain': 'Drug',
                        'total_records': 5000,
                        'unmapped_count': 100
                    }
                ]
            }
        }
        
        fig = OMOPCharts.create_concept_mapping_sunburst(mapping_data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'sunburst'
    
    def test_create_vocabulary_treemap(self):
        """Test vocabulary treemap creation"""
        vocab_data = [
            {
                'vocabulary_name': 'SNOMED CT',
                'unique_concepts': 5000,
                'condition_usage': 8000,
                'drug_usage': 0,
                'procedure_usage': 1000
            },
            {
                'vocabulary_name': 'RxNorm',
                'unique_concepts': 3000,
                'condition_usage': 0,
                'drug_usage': 5000,
                'procedure_usage': 0
            }
        ]
        
        fig = OMOPCharts.create_vocabulary_treemap(vocab_data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'treemap'
    
    def test_create_data_density_timeline(self):
        """Test data density timeline creation"""
        density_data = [
            {'year': 2020, 'total_conditions': 10000, 'unique_patients': 1000},
            {'year': 2021, 'total_conditions': 12000, 'unique_patients': 1200},
            {'year': 2022, 'total_conditions': 15000, 'unique_patients': 1500}
        ]
        
        fig = OMOPCharts.create_data_density_timeline(density_data)
        
        assert isinstance(fig, go.Figure)
        # Should have subplots for conditions and patients
        assert len(fig.data) == 2
    
    def test_create_age_distribution_histogram(self):
        """Test age distribution histogram"""
        age_data = [
            {'age_group': 'Under 18', 'count': 100, 'percentage': 10},
            {'age_group': '18-30', 'count': 200, 'percentage': 20},
            {'age_group': '31-50', 'count': 300, 'percentage': 30},
            {'age_group': '51-70', 'count': 250, 'percentage': 25},
            {'age_group': 'Over 70', 'count': 150, 'percentage': 15}
        ]
        
        fig = OMOPCharts.create_age_distribution_histogram(age_data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'bar'
    
    def test_create_quality_summary_radar(self):
        """Test quality summary radar chart"""
        quality_scores = {
            'Completeness': 85,
            'Temporal': 92,
            'Concept Mapping': 78,
            'Referential': 95,
            'Statistical': 88
        }
        
        fig = OMOPCharts.create_quality_summary_radar(quality_scores)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'scatterpolar'


class TestInteractiveCharts:
    """Test cases for interactive chart components"""
    
    @patch('streamlit.sidebar.multiselect')
    def test_create_filterable_table_chart(self, mock_multiselect):
        """Test filterable table chart creation"""
        test_data = [
            {'category': 'A', 'value': 10, 'status': 'PASS'},
            {'category': 'B', 'value': 20, 'status': 'FAIL'},
            {'category': 'A', 'value': 15, 'status': 'WARNING'}
        ]
        
        # Mock the multiselect to return all values
        mock_multiselect.return_value = ['A', 'B']
        
        fig, filters = InteractiveCharts.create_filterable_table_chart(test_data, "Test Chart")
        
        assert isinstance(fig, go.Figure)
        assert isinstance(filters, dict)
    
    def test_create_time_series_chart(self):
        """Test time series chart creation"""
        time_data = [
            {'date': '2023-01-01', 'value': 100},
            {'date': '2023-02-01', 'value': 110},
            {'date': '2023-03-01', 'value': 120}
        ]
        
        fig = InteractiveCharts.create_time_series_chart(
            time_data, 'date', 'value', "Test Time Series"
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'scatter'
    
    def test_create_time_series_chart_invalid_data(self):
        """Test time series chart with invalid data"""
        # Test with missing columns
        invalid_data = [{'wrong_col': 'value'}]
        
        fig = InteractiveCharts.create_time_series_chart(
            invalid_data, 'date', 'value'
        )
        
        assert isinstance(fig, go.Figure)
        # Should handle invalid data gracefully


class TestConfigManager:
    """Test cases for configuration management"""
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization"""
        config = ConfigManager()
        
        assert isinstance(config.config, dict)
        assert 'database' in config.config
        assert 'quality_checks' in config.config
        assert 'dashboard' in config.config
    
    def test_config_get_method(self):
        """Test configuration value retrieval"""
        config = ConfigManager()
        
        # Test getting nested value
        db_type = config.get('database.default_type')
        assert db_type == 'postgresql'
        
        # Test getting non-existent value with default
        missing_value = config.get('nonexistent.key', 'default')
        assert missing_value == 'default'
    
    def test_config_set_method(self):
        """Test configuration value setting"""
        config = ConfigManager()
        
        config.set('test.new_value', 'test_data')
        assert config.get('test.new_value') == 'test_data'
    
    def test_get_chart_colors(self):
        """Test chart colors retrieval"""
        config = ConfigManager()
        colors = config.get_chart_colors()
        
        assert isinstance(colors, dict)
        assert 'pass' in colors
        assert 'warning' in colors
        assert 'fail' in colors
        assert 'error' in colors
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = ConfigManager()
        is_valid = config.validate_config()
        
        assert isinstance(is_valid, bool)
        assert is_valid is True  # Default config should be valid


class TestStreamlitConfig:
    """Test cases for Streamlit-specific configuration"""
    
    @patch('streamlit.set_page_config')
    def test_setup_page_config(self, mock_set_page_config):
        """Test Streamlit page configuration setup"""
        config = ConfigManager()
        StreamlitConfig.setup_page_config(config)
        
        mock_set_page_config.assert_called_once()
        args, kwargs = mock_set_page_config.call_args
        assert 'page_title' in kwargs
        assert 'page_icon' in kwargs
    
    @patch('streamlit.markdown')
    def test_apply_custom_css(self, mock_markdown):
        """Test custom CSS application"""
        config = ConfigManager()
        StreamlitConfig.apply_custom_css(config)
        
        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args
        assert 'unsafe_allow_html' in kwargs
        assert kwargs['unsafe_allow_html'] is True
    
    def test_get_theme_colors(self):
        """Test theme colors retrieval"""
        config = ConfigManager()
        theme_colors = StreamlitConfig.get_theme_colors(config)
        
        assert isinstance(theme_colors, dict)
        assert 'primary' in theme_colors
        assert 'success' in theme_colors
        assert 'warning' in theme_colors
        assert 'danger' in theme_colors


class TestUtilityHelpers:
    """Test cases for utility helper functions"""
    
    def test_data_helpers_safe_divide(self):
        """Test safe division functionality"""
        assert DataHelpers.safe_divide(10, 2) == 5.0
        assert DataHelpers.safe_divide(10, 0) == 0.0
        assert DataHelpers.safe_divide(10, 0, default=999) == 999
        assert DataHelpers.safe_divide("invalid", 2) == 0.0
    
    def test_data_helpers_calculate_percentage(self):
        """Test percentage calculation"""
        assert DataHelpers.calculate_percentage(25, 100) == 25.0
        assert DataHelpers.calculate_percentage(1, 3, precision=3) == 33.333
        assert DataHelpers.calculate_percentage(10, 0) == 0.0
    
    def test_data_helpers_format_large_number(self):
        """Test large number formatting"""
        assert DataHelpers.format_large_number(1500) == "1.5K"
        assert DataHelpers.format_large_number(1500000) == "1.5M"
        assert DataHelpers.format_large_number(1500000000) == "1.5B"
        assert DataHelpers.format_large_number(500) == "500"
    
    def test_data_helpers_clean_dataframe(self):
        """Test dataframe cleaning"""
        df = pd.DataFrame({
            'numeric_str': ['1', '2', '3.5', 'invalid'],
            'mixed': [1, 2, np.inf, 4],
            'normal': ['a', 'b', 'c', 'd']
        })
        
        cleaned_df = DataHelpers.clean_dataframe(df)
        
        assert isinstance(cleaned_df, pd.DataFrame)
        assert not np.isinf(cleaned_df['mixed']).any()
    
    def test_data_helpers_detect_outliers_iqr(self):
        """Test IQR outlier detection"""
        series = pd.Series([1, 2, 3, 4, 5, 100])  # 100 is an outlier
        outliers = DataHelpers.detect_outliers_iqr(series)
        
        assert isinstance(outliers, pd.Series)
        assert outliers.dtype == bool
        assert outliers.iloc[-1] == True  # Last value should be detected as outlier
    
    def test_data_helpers_get_data_summary(self):
        """Test data summary generation"""
        df = pd.DataFrame({
            'numeric': [1, 2, 3, 4, 5],
            'text': ['a', 'b', 'c', 'd', 'e'],
            'with_nulls': [1, 2, None, 4, 5]
        })
        
        summary = DataHelpers.get_data_summary(df)
        
        assert isinstance(summary, dict)
        assert 'shape' in summary
        assert 'missing_values' in summary
        assert 'numeric_columns' in summary
        assert summary['shape'] == (5, 3)
    
    def test_date_helpers_parse_date_flexible(self):
        """Test flexible date parsing"""
        # Test various date formats
        assert DateHelpers.parse_date_flexible('2023-01-15') is not None
        assert DateHelpers.parse_date_flexible('01/15/2023') is not None
        assert DateHelpers.parse_date_flexible('2023-01-15 10:30:00') is not None
        assert DateHelpers.parse_date_flexible('invalid_date') is None
        assert DateHelpers.parse_date_flexible(None) is None
    
    def test_date_helpers_calculate_age(self):
        """Test age calculation"""
        from datetime import date
        
        # Test with known date
        birth_date = '1990-01-01'
        reference_date = date(2023, 1, 1)
        age = DateHelpers.calculate_age(birth_date, reference_date)
        
        assert age == 33
        
        # Test with invalid date
        age_invalid = DateHelpers.calculate_age('invalid_date')
        assert age_invalid is None
    
    def test_date_helpers_is_future_date(self):
        """Test future date detection"""
        from datetime import date, timedelta
        
        future_date = date.today() + timedelta(days=30)
        past_date = date.today() - timedelta(days=30)
        
        assert DateHelpers.is_future_date(future_date) is True
        assert DateHelpers.is_future_date(past_date) is False
        assert DateHelpers.is_future_date('invalid_date') is False
    
    @patch('streamlit.selectbox')
    @patch('streamlit.dataframe')
    @patch('streamlit.info')
    @patch('streamlit.columns')
    def test_streamlit_helpers_display_dataframe_with_pagination(self, mock_columns, mock_info, mock_dataframe, mock_selectbox):
        """Test paginated dataframe display"""
        # Create test dataframe with 250 rows
        df = pd.DataFrame({'col1': range(250), 'col2': range(250, 500)})
        
        # Mock columns
        mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        # Mock selectbox to return page 2
        mock_selectbox.return_value = 2
        
        displayed_df = StreamlitHelpers.display_dataframe_with_pagination(df, page_size=100)
        
        assert isinstance(displayed_df, pd.DataFrame)
        mock_selectbox.assert_called_once()
        mock_dataframe.assert_called_once()
    
    def test_streamlit_helpers_create_metric_delta_color(self):
        """Test metric delta color calculation"""
        # Test improvement (higher is better)
        delta, color = StreamlitHelpers.create_metric_delta_color(100, 90, higher_is_better=True)
        assert delta == 10
        assert color == "normal"
        
        # Test decline (higher is better)
        delta, color = StreamlitHelpers.create_metric_delta_color(80, 90, higher_is_better=True)
        assert delta == -10
        assert color == "inverse"
        
        # Test with no previous value
        delta, color = StreamlitHelpers.create_metric_delta_color(100, None)
        assert delta is None
        assert color == "normal"
    
    def test_streamlit_helpers_format_metric_value(self):
        """Test metric value formatting"""
        assert StreamlitHelpers.format_metric_value(85.5, "percentage") == "85.5%"
        assert StreamlitHelpers.format_metric_value(1234.56, "currency") == "$1,234.56"
        assert StreamlitHelpers.format_metric_value(1500, "count") == "1.5K"
        assert StreamlitHelpers.format_metric_value(0.123, "ratio") == "0.123"


class TestDashboardIntegration:
    """Integration tests for dashboard components"""
    
    @patch('streamlit.plotly_chart')
    @patch('streamlit.subheader')
    def test_dashboard_workflow_integration(self, mock_subheader, mock_plotly_chart):
        """Test integrated dashboard workflow"""
        # Mock quality check results
        mock_results = {
            'completeness': {
                'table_completeness': {
                    'status': 'PASS',
                    'data': [
                        {'table_name': 'person', 'null_percentage': 5, 'total_rows': 1000}
                    ]
                }
            }
        }
        
        # Test chart creation and rendering
        completeness_data = mock_results['completeness']['table_completeness']['data']
        fig = OMOPCharts.create_completeness_bar_chart(completeness_data)
        
        assert isinstance(fig, go.Figure)
    
    def test_configuration_dashboard_integration(self):
        """Test configuration integration with dashboard"""
        config = ConfigManager()
        
        # Test that dashboar
