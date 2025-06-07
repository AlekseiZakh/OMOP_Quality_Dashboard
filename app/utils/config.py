import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import streamlit as st


class ConfigManager:
    """Manages configuration settings for the OMOP Quality Dashboard"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
                logging.info(f"Configuration loaded from {self.config_file}")
            else:
                logging.warning(f"Configuration file {self.config_file} not found, using defaults")
                self.config = self._get_default_config()
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'database': {
                'default_type': 'postgresql',
                'default_host': 'localhost',
                'default_port': 5432,
                'default_database': 'omop_cdm',
                'pool_size': 5,
                'max_overflow': 10,
                'pool_recycle': 3600
            },
            'quality_checks': {
                'completeness': {
                    'critical_field_threshold': 0,
                    'table_completeness_warning': 10,
                    'table_completeness_fail': 25,
                    'person_completeness_pass': 90
                },
                'temporal': {
                    'max_age': 120,
                    'min_birth_year': 1900,
                    'future_date_tolerance': 0
                },
                'concept_mapping': {
                    'unmapped_warning': 5,
                    'unmapped_fail': 15,
                    'standard_concept_threshold': 80
                },
                'referential': {
                    'orphan_warning': 100,
                    'orphan_fail': 1000
                },
                'statistical': {
                    'outlier_warning': 10,
                    'outlier_fail': 50
                }
            },
            'dashboard': {
                'title': 'OMOP Quality Dashboard',
                'subtitle': 'Comprehensive Data Quality Monitoring',
                'refresh_interval': 300,
                'max_query_results': 1000,
                'chart_height': 400,
                'chart_colors': {
                    'pass': '#28a745',
                    'warning': '#ffc107',
                    'fail': '#dc3545',
                    'error': '#6c757d'
                }
            },
            'reporting': {
                'export_formats': ['csv', 'excel', 'pdf'],
                'report_templates': [
                    'executive_summary',
                    'technical_detail',
                    'trend_analysis'
                ]
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'omop_dashboard.log',
                'max_file_size': 10485760,
                'backup_count': 5
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('database.default_host')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        Example: config.set('database.default_host', 'new_host')
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set the value
        config_ref[keys[-1]] = value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get('database', {})
    
    def get_quality_check_config(self, check_type: str) -> Dict[str, Any]:
        """Get quality check configuration for specific check type"""
        return self.get(f'quality_checks.{check_type}', {})
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration"""
        return self.get('dashboard', {})
    
    def get_chart_colors(self) -> Dict[str, str]:
        """Get chart color configuration"""
        return self.get('dashboard.chart_colors', {
            'pass': '#28a745',
            'warning': '#ffc107',
            'fail': '#dc3545',
            'error': '#6c757d'
        })
    
    def save_config(self, config_file: Optional[str] = None):
        """Save current configuration to file"""
        file_path = config_file or self.config_file
        
        try:
            with open(file_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False, indent=2)
            logging.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    
    def update_from_env(self):
        """Update configuration from environment variables"""
        env_mappings = {
            'OMOP_DB_TYPE': 'database.default_type',
            'OMOP_DB_HOST': 'database.default_host',
            'OMOP_DB_PORT': 'database.default_port',
            'OMOP_DB_NAME': 'database.default_database',
            'OMOP_DB_USER': 'database.default_user',
            'OMOP_DB_PASSWORD': 'database.default_password',
            'DASHBOARD_TITLE': 'dashboard.title',
            'DASHBOARD_REFRESH_INTERVAL': 'dashboard.refresh_interval',
            'LOG_LEVEL': 'logging.level'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert numeric values
                if config_key.endswith(('port', 'refresh_interval', 'pool_size', 'max_overflow')):
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        continue
                
                self.set(config_key, env_value)
                logging.debug(f"Updated {config_key} from environment variable {env_var}")
    
    def validate_config(self) -> bool:
        """Validate configuration for required fields"""
        required_sections = ['database', 'quality_checks', 'dashboard']
        
        for section in required_sections:
            if section not in self.config:
                logging.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate database config
        db_config = self.get_database_config()
        required_db_fields = ['default_type', 'default_host', 'default_port', 'default_database']
        
        for field in required_db_fields:
            if field not in db_config:
                logging.warning(f"Missing database configuration field: {field}")
        
        return True


class StreamlitConfig:
    """Streamlit-specific configuration helpers"""
    
    @staticmethod
    def setup_page_config(config_manager: ConfigManager):
        """Setup Streamlit page configuration"""
        dashboard_config = config_manager.get_dashboard_config()
        
        try:
            st.set_page_config(
                page_title=dashboard_config.get('title', 'OMOP Quality Dashboard'),
                page_icon="🏥",
                layout="wide",
                initial_sidebar_state="expanded"
            )
        except st.errors.StreamlitAPIException:
            # Page config already set, skip
            pass
    
    @staticmethod
    def apply_custom_css(config_manager: ConfigManager):
        """Apply custom CSS styling"""
        colors = config_manager.get_chart_colors()
        
        custom_css = f"""
        <style>
            .main-header {{
                font-size: 2.5rem;
                font-weight: bold;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
            }}
            
            .metric-card {{
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
                border-left: 4px solid #1f77b4;
            }}
            
            .status-pass {{ 
                color: {colors['pass']};
                font-weight: bold;
            }}
            
            .status-warning {{ 
                color: {colors['warning']};
                font-weight: bold;
            }}
            
            .status-fail {{ 
                color: {colors['fail']};
                font-weight: bold;
            }}
            
            .status-error {{ 
                color: {colors['error']};
                font-weight: bold;
            }}
            
            .sidebar .sidebar-content {{
                background-color: #f8f9fa;
            }}
            
            .stAlert {{
                border-radius: 0.5rem;
            }}
            
            .quality-score-high {{
                background: linear-gradient(90deg, {colors['pass']}, #20c997);
                color: white;
                padding: 0.5rem;
                border-radius: 0.25rem;
                text-align: center;
                font-weight: bold;
            }}
            
            .quality-score-medium {{
                background: linear-gradient(90deg, {colors['warning']}, #fd7e14);
                color: white;
                padding: 0.5rem;
                border-radius: 0.25rem;
                text-align: center;
                font-weight: bold;
            }}
            
            .quality-score-low {{
                background: linear-gradient(90deg, {colors['fail']}, #e74c3c);
                color: white;
                padding: 0.5rem;
                border-radius: 0.25rem;
                text-align: center;
                font-weight: bold;
            }}
            
            /* Additional utility classes */
            .highlight-box {{
                background-color: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 0.25rem;
            }}
            
            .data-table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1rem 0;
            }}
            
            .data-table th,
            .data-table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            .data-table th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
        </style>
        """
        
        st.markdown(custom_css, unsafe_allow_html=True)
    
    @staticmethod
    def get_theme_colors(config_manager: ConfigManager) -> Dict[str, str]:
        """Get theme colors for Plotly charts"""
        colors = config_manager.get_chart_colors()
        
        return {
            'primary': '#1f77b4',
            'success': colors['pass'],
            'warning': colors['warning'],
            'danger': colors['fail'],
            'secondary': colors['error'],
            'background': '#ffffff',
            'surface': '#f8f9fa'
        }


# Global configuration instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
        _config_instance.update_from_env()
    return _config_instance

def init_logging(config_manager: Optional[ConfigManager] = None):
    """Initialize logging based on configuration"""
    if config_manager is None:
        config_manager = get_config()
    
    log_config = config_manager.get('logging', {})
    
    # Avoid reinitializing logging if already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_config.get('file', 'omop_dashboard.log')),
                logging.StreamHandler()
            ]
        )
    
    # Set up log rotation if needed
    log_file = log_config.get('file', 'omop_dashboard.log')
    max_size = log_config.get('max_file_size', 10485760)  # 10MB
    backup_count = log_config.get('backup_count', 5)
    
    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > max_size:
            # Simple log rotation
            for i in range(backup_count - 1, 0, -1):
                old_log = f"{log_file}.{i}"
                new_log = f"{log_file}.{i + 1}"
                if os.path.exists(old_log):
                    os.rename(old_log, new_log)
            
            if os.path.exists(log_file):
                os.rename(log_file, f"{log_file}.1")
    except OSError as e:
        # Handle case where log rotation fails (e.g., in cloud environments)
        logging.warning(f"Log rotation failed: {e}")


# Utility functions for easy access
def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    return get_config().get_database_config()

def get_quality_thresholds(check_type: str) -> Dict[str, Any]:
    """Get quality check thresholds"""
    return get_config().get_quality_check_config(check_type)

def get_chart_colors() -> Dict[str, str]:
    """Get chart colors"""
    return get_config().get_chart_colors()


# Export main classes and functions
__all__ = [
    'ConfigManager',
    'StreamlitConfig',
    'get_config',
    'init_logging',
    'get_database_config',
    'get_quality_thresholds',
    'get_chart_colors'
]
