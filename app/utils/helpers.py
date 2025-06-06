import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, date, timedelta
import logging
import json
import re
from pathlib import Path
import hashlib


class DataHelpers:
    """Helper functions for data processing and validation"""
    
    @staticmethod
    def safe_divide(numerator: Union[int, float], denominator: Union[int, float], 
                   default: float = 0.0) -> float:
        """Safely divide two numbers, returning default if denominator is zero"""
        try:
            if denominator == 0:
                return default
            return float(numerator) / float(denominator)
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def calculate_percentage(part: Union[int, float], total: Union[int, float], 
                           precision: int = 2) -> float:
        """Calculate percentage with specified precision"""
        if total == 0:
            return 0.0
        return round((part / total) * 100, precision)
    
    @staticmethod
    def format_large_number(number: Union[int, float]) -> str:
        """Format large numbers with appropriate suffixes (K, M, B)"""
        try:
            num = float(number)
            if abs(num) >= 1e9:
                return f"{num/1e9:.1f}B"
            elif abs(num) >= 1e6:
                return f"{num/1e6:.1f}M"
            elif abs(num) >= 1e3:
                return f"{num/1e3:.1f}K"
            else:
                return f"{num:,.0f}"
        except (TypeError, ValueError):
            return str(number)
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean dataframe by handling common data quality issues"""
        if df.empty:
            return df
        
        # Create a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Convert object columns with numeric-like strings to numeric
        for col in cleaned_df.select_dtypes(include=['object']).columns:
            # Try to convert to numeric if it looks like numbers
            if cleaned_df[col].dtype == 'object':
                # Check if column contains mostly numeric-like strings
                sample_values = cleaned_df[col].dropna().head(100)
                if len(sample_values) > 0:
                    numeric_pattern = re.compile(r'^-?\d+\.?\d*$')
                    numeric_count = sum(1 for val in sample_values.astype(str) 
                                      if numeric_pattern.match(val.strip()))
                    
                    if numeric_count / len(sample_values) > 0.8:  # 80% numeric-like
                        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        # Handle infinite values
        numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
        cleaned_df[numeric_cols] = cleaned_df[numeric_cols].replace([np.inf, -np.inf], np.nan)
        
        return cleaned_df
    
    @staticmethod
    def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
        """Detect outliers using Interquartile Range (IQR) method"""
        if series.empty or not pd.api.types.is_numeric_dtype(series):
            return pd.Series([], dtype=bool, index=series.index)
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        return (series < lower_bound) | (series > upper_bound)
    
    @staticmethod
    def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive data summary statistics"""
        if df.empty:
            return {'error': 'Empty dataframe'}
        
        summary = {
            'shape': df.shape,
            'total_cells': df.shape[0] * df.shape[1],
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'dtypes': df.dtypes.value_counts().to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
            'datetime_columns': df.select_dtypes(include=['datetime']).columns.tolist()
        }
        
        # Add numeric summaries
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            summary['numeric_summary'] = numeric_df.describe().to_dict()
        
        return summary


class DateHelpers:
    """Helper functions for date and time operations"""
    
    @staticmethod
    def parse_date_flexible(date_value: Any) -> Optional[datetime]:
        """Parse date from various formats"""
        if pd.isna(date_value) or date_value is None:
            return None
        
        # If already datetime
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, date):
            return datetime.combine(date_value, datetime.min.time())
        
        # Try to parse string dates
        if isinstance(date_value, str):
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y%m%d',
                '%d-%m-%Y',
                '%d.%m.%Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(str(date_value).strip(), fmt)
                except ValueError:
                    continue
        
        # Try pandas to_datetime as last resort
        try:
            return pd.to_datetime(date_value)
        except:
            return None
    
    @staticmethod
    def calculate_age(birth_date: Union[datetime, date, str], 
                     reference_date: Optional[Union[datetime, date]] = None) -> Optional[int]:
        """Calculate age from birth date"""
        if reference_date is None:
            reference_date = date.today()
        
        birth_dt = DateHelpers.parse_date_flexible(birth_date)
        if birth_dt is None:
            return None
        
        if isinstance(reference_date, datetime):
            reference_date = reference_date.date()
        
        birth_date_only = birth_dt.date()
        
        try:
            age = reference_date.year - birth_date_only.year
            if (reference_date.month, reference_date.day) < (birth_date_only.month, birth_date_only.day):
                age -= 1
            return age
        except:
            return None
    
    @staticmethod
    def is_future_date(date_value: Any, reference_date: Optional[date] = None) -> bool:
        """Check if date is in the future"""
        if reference_date is None:
            reference_date = date.today()
        
        parsed_date = DateHelpers.parse_date_flexible(date_value)
        if parsed_date is None:
            return False
        
        return parsed_date.date() > reference_date
    
    @staticmethod
    def get_date_range_description(start_date: datetime, end_date: datetime) -> str:
        """Get human-readable description of date range"""
        try:
            delta = end_date - start_date
            years = delta.days // 365
            months = (delta.days % 365) // 30
            days = delta.days % 30
            
            parts = []
            if years > 0:
                parts.append(f"{years} year{'s' if years != 1 else ''}")
            if months > 0:
                parts.append(f"{months} month{'s' if months != 1 else ''}")
            if days > 0 or not parts:
                parts.append(f"{days} day{'s' if days != 1 else ''}")
            
            return ", ".join(parts)
        except:
            return "Unknown duration"


class StreamlitHelpers:
    """Helper functions for Streamlit UI components"""
    
    @staticmethod
    def create_download_link(data: Union[pd.DataFrame, str, bytes], 
                           filename: str, 
                           link_text: str = "Download") -> str:
        """Create a download link for data"""
        if isinstance(data, pd.DataFrame):
            csv = data.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            mime_type = "text/csv"
        elif isinstance(data, str):
            b64 = base64.b64encode(data.encode()).decode()
            mime_type = "text/plain"
        elif isinstance(data, bytes):
            b64 = base64.b64encode(data).decode()
            mime_type = "application/octet-stream"
        else:
            return ""
        
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{link_text}</a>'
        return href
    
    @staticmethod
    def display_dataframe_with_pagination(df: pd.DataFrame, 
                                        page_size: int = 100,
                                        key: str = "paginated_df") -> pd.DataFrame:
        """Display dataframe with pagination"""
        if df.empty:
            st.info("No data to display")
            return df
        
        total_rows = len(df)
        total_pages = (total_rows - 1) // page_size + 1
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.selectbox(
                    f"Page (showing {page_size} rows per page)",
                    range(1, total_pages + 1),
                    key=f"{key}_page_selector"
                )
            
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            
            st.info(f"Showing rows {start_idx + 1}-{end_idx} of {total_rows}")
            displayed_df = df.iloc[start_idx:end_idx]
        else:
            displayed_df = df
        
        st.dataframe(displayed_df, use_container_width=True, key=f"{key}_dataframe")
        return displayed_df
    
    @staticmethod
    def create_metric_delta_color(current_value: float, 
                                previous_value: Optional[float] = None,
                                higher_is_better: bool = True) -> Tuple[Optional[float], str]:
        """Calculate metric delta and determine color"""
        if previous_value is None:
            return None, "normal"
        
        delta = current_value - previous_value
        
        if delta == 0:
            return 0, "off"
        elif (delta > 0 and higher_is_better) or (delta < 0 and not higher_is_better):
            return delta, "normal"
        else:
            return delta, "inverse"
    
    @staticmethod
    def format_metric_value(value: Union[int, float], 
                          metric_type: str = "count") -> str:
        """Format metric values based on type"""
        if pd.isna(value):
            return "N/A"
        
        if metric_type == "percentage":
            return f"{value:.1f}%"
        elif metric_type == "currency":
            return f"${value:,.2f}"
        elif metric_type == "count":
            return DataHelpers.format_large_number(value)
        elif metric_type == "ratio":
            return f"{value:.3f}"
        else:
            return str(value)


class ValidationHelpers:
    """Helper functions for data validation"""
    
    @staticmethod
    def validate_omop_person_id(person_id: Any) -> bool:
        """Validate OMOP person_id format"""
        try:
            pid = int(person_id)
            return pid > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_omop_concept_id(concept_id: Any) -> bool:
        """Validate OMOP concept_id format"""
        try:
            cid = int(concept_id)
            return cid >= 0  # 0 is valid for unmapped concepts
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date_range(start_date: Any, end_date: Any) -> Dict[str, Any]:
        """Validate date range consistency"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        start_dt = DateHelpers.parse_date_flexible(start_date)
        end_dt = DateHelpers.parse_date_flexible(end_date)
        
        if start_dt is None:
            result['valid'] = False
            result['errors'].append("Invalid start date format")
        
        if end_dt is None:
            result['valid'] = False
            result['errors'].append("Invalid end date format")
        
        if start_dt and end_dt:
            if start_dt > end_dt:
                result['valid'] = False
                result['errors'].append("Start date is after end date")
            
            # Check for suspiciously long periods
            if (end_dt - start_dt).days > 365 * 10:  # More than 10 years
                result['warnings'].append("Date range spans more than 10 years")
        
        return result
    
    @staticmethod
    def validate_numeric_range(value: Any, min_value: Optional[float] = None, 
                             max_value: Optional[float] = None) -> Dict[str, Any]:
        """Validate numeric value is within expected range"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                result['valid'] = False
                result['errors'].append(f"Value {num_value} is below minimum {min_value}")
            
            if max_value is not None and num_value > max_value:
                result['valid'] = False
                result['errors'].append(f"Value {num_value} is above maximum {max_value}")
            
        except (ValueError, TypeError):
            result['valid'] = False
            result['errors'].append("Value is not numeric")
        
        return result


class FileHelpers:
    """Helper functions for file operations"""
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Create a safe filename by removing/replacing problematic characters"""
        # Remove or replace problematic characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove multiple consecutive underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Trim underscores from start and end
        safe_name = safe_name.strip('_')
        
        # Ensure it's not empty
        if not safe_name:
            safe_name = "untitled"
        
        return safe_name
    
    @staticmethod
    def get_file_hash(filepath: Union[str, Path]) -> Optional[str]:
        """Get MD5 hash of a file"""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating file hash: {e}")
            return None
    
    @staticmethod
    def ensure_directory_exists(directory: Union[str, Path]):
        """Ensure directory exists, create if it doesn't"""
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating directory {directory}: {e}")
    
    @staticmethod
    def get_file_size_mb(filepath: Union[str, Path]) -> float:
        """Get file size in MB"""
        try:
            return Path(filepath).stat().st_size / (1024 * 1024)
        except Exception:
            return 0.0


class CacheHelpers:
    """Helper functions for caching and performance optimization"""
    
    @staticmethod
    def generate_cache_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        # Create a string representation of all arguments
        key_parts = []
        
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, (list, tuple)):
                key_parts.append(str(hash(tuple(arg))))
            elif isinstance(arg, dict):
                key_parts.append(str(hash(tuple(sorted(arg.items())))))
            else:
                key_parts.append(str(hash(str(arg))))
        
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}={value}")
        
        cache_key = "_".join(key_parts)
        return hashlib.md5(cache_key.encode()).hexdigest()
    
    @staticmethod
    def cache_dataframe(df: pd.DataFrame, cache_key: str, ttl_minutes: int = 60):
        """Cache dataframe in Streamlit session state with TTL"""
        if 'dataframe_cache' not in st.session_state:
            st.session_state.dataframe_cache = {}
        
        cache_entry = {
            'data': df,
            'timestamp': datetime.now(),
            'ttl_minutes': ttl_minutes
        }
        
        st.session_state.dataframe_cache[cache_key] = cache_entry
    
    @staticmethod
    def get_cached_dataframe(cache_key: str) -> Optional[pd.DataFrame]:
        """Retrieve cached dataframe if still valid"""
        if 'dataframe_cache' not in st.session_state:
            return None
        
        cache_entry = st.session_state.dataframe_cache.get(cache_key)
        if cache_entry is None:
            return None
        
        # Check if cache is still valid
        elapsed_minutes = (datetime.now() - cache_entry['timestamp']).total_seconds() / 60
        if elapsed_minutes > cache_entry['ttl_minutes']:
            # Cache expired, remove it
            del st.session_state.dataframe_cache[cache_key]
            return None
        
        return cache_entry['data']
    
    @staticmethod
    def clear_expired_cache():
        """Clear expired cache entries"""
        if 'dataframe_cache' not in st.session_state:
            return
        
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in st.session_state.dataframe_cache.items():
            elapsed_minutes = (current_time - entry['timestamp']).total_seconds() / 60
            if elapsed_minutes > entry['ttl_minutes']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del st.session_state.dataframe_cache[key]


class OMOPHelpers:
    """OMOP-specific helper functions"""
    
    @staticmethod
    def get_omop_table_relationships() -> Dict[str, List[str]]:
        """Get OMOP table relationships for referential integrity checks"""
        return {
            'person': ['condition_occurrence', 'drug_exposure', 'procedure_occurrence', 
                      'measurement', 'observation', 'visit_occurrence', 'death'],
            'visit_occurrence': ['condition_occurrence', 'drug_exposure', 'procedure_occurrence',
                               'measurement', 'observation', 'visit_detail'],
            'concept': ['condition_occurrence.condition_concept_id', 'drug_exposure.drug_concept_id',
                       'procedure_occurrence.procedure_concept_id', 'measurement.measurement_concept_id'],
            'care_site': ['visit_occurrence', 'person'],
            'provider': ['visit_occurrence', 'condition_occurrence', 'drug_exposure', 'procedure_occurrence']
        }
    
    @staticmethod
    def get_omop_domain_tables() -> Dict[str, str]:
        """Get mapping of OMOP domains to their primary tables"""
        return {
            'Condition': 'condition_occurrence',
            'Drug': 'drug_exposure',
            'Procedure': 'procedure_occurrence',
            'Measurement': 'measurement',
            'Observation': 'observation',
            'Visit': 'visit_occurrence',
            'Device': 'device_exposure',
            'Specimen': 'specimen'
        }
    
    @staticmethod
    def get_critical_omop_fields() -> Dict[str, List[str]]:
        """Get critical fields that should not be null for each OMOP table"""
        return {
            'person': ['person_id', 'gender_concept_id', 'year_of_birth'],
            'condition_occurrence': ['condition_occurrence_id', 'person_id', 'condition_concept_id', 'condition_start_date'],
            'drug_exposure': ['drug_exposure_id', 'person_id', 'drug_concept_id', 'drug_exposure_start_date'],
            'procedure_occurrence': ['procedure_occurrence_id', 'person_id', 'procedure_concept_id', 'procedure_date'],
            'measurement': ['measurement_id', 'person_id', 'measurement_concept_id', 'measurement_date'],
            'observation': ['observation_id', 'person_id', 'observation_concept_id', 'observation_date'],
            'visit_occurrence': ['visit_occurrence_id', 'person_id', 'visit_concept_id', 'visit_start_date'],
            'death': ['person_id', 'death_date']
        }
    
    @staticmethod
    def validate_omop_cdm_version(version: str) -> bool:
        """Validate OMOP CDM version format"""
        pattern = r'^v?\d+\.\d+(\.\d+)?
        return bool(re.match(pattern, version.lower()))
    
    @staticmethod
    def get_standard_vocabularies() -> List[str]:
        """Get list of standard OMOP vocabularies"""
        return [
            'SNOMED', 'ICD10CM', 'ICD9CM', 'CPT4', 'HCPCS',
            'LOINC', 'RxNorm', 'NDC', 'Gender', 'Race',
            'Ethnicity', 'Visit', 'Relationship', 'Type Concept'
        ]


class ErrorHelpers:
    """Helper functions for error handling and logging"""
    
    @staticmethod
    def log_error(error: Exception, context: str = "", extra_data: Optional[Dict] = None):
        """Log error with context and optional extra data"""
        error_msg = f"Error in {context}: {str(error)}"
        
        if extra_data:
            error_msg += f" | Extra data: {json.dumps(extra_data, default=str)}"
        
        logging.error(error_msg, exc_info=True)
    
    @staticmethod
    def safe_execute(func, *args, default_return=None, context: str = "", **kwargs):
        """Safely execute a function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHelpers.log_error(e, context)
            return default_return
    
    @staticmethod
    def create_error_summary(errors: List[str], warnings: List[str] = None) -> Dict[str, Any]:
        """Create a standardized error summary"""
        warnings = warnings or []
        
        return {
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'errors': errors,
            'warnings': warnings,
            'status': 'ERROR' if errors else 'WARNING' if warnings else 'SUCCESS'
        }


class PerformanceHelpers:
    """Helper functions for performance monitoring"""
    
    @staticmethod
    def time_function(func):
        """Decorator to time function execution"""
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logging.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logging.error(f"Function {func.__name__} failed after {execution_time:.2f} seconds: {e}")
                raise
        return wrapper
    
    @staticmethod
    def monitor_memory_usage(func):
        """Decorator to monitor memory usage"""
        def wrapper(*args, **kwargs):
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            result = func(*args, **kwargs)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_diff = memory_after - memory_before
            
            logging.info(f"Function {func.__name__} memory usage: {memory_diff:.2f} MB")
            
            if memory_diff > 100:  # More than 100MB
                logging.warning(f"High memory usage detected in {func.__name__}: {memory_diff:.2f} MB")
            
            return result
        return wrapper


# Utility functions for common operations
def format_sql_query(query: str) -> str:
    """Format SQL query for better readability"""
    # Basic SQL formatting
    formatted = re.sub(r'\s+', ' ', query.strip())
    formatted = re.sub(r'\s*,\s*', ',\n    ', formatted)
    formatted = re.sub(r'\bFROM\b', '\nFROM', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bWHERE\b', '\nWHERE', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bJOIN\b', '\nJOIN', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bGROUP BY\b', '\nGROUP BY', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bORDER BY\b', '\nORDER BY', formatted, flags=re.IGNORECASE)
    return formatted


def get_timestamp() -> str:
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# Import base64 for download functionality
import base64

# Export all helper classes and functions
__all__ = [
    'DataHelpers',
    'DateHelpers', 
    'StreamlitHelpers',
    'ValidationHelpers',
    'FileHelpers',
    'CacheHelpers',
    'OMOPHelpers',
    'ErrorHelpers',
    'PerformanceHelpers',
    'format_sql_query',
    'get_timestamp',
    'truncate_string'
]
