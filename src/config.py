# src/config.py
import yaml
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ProcessingConfig:
    """Processing configuration settings"""
    max_concurrent_requests: int = 3
    batch_size: int = 5
    rate_limit_delay_seconds: float = 2.0
    sample_size: int = None
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: int = 30

@dataclass
class DataQualityConfig:
    """Data quality configuration settings"""
    minimum_confidence_threshold: float = 0.5
    high_confidence_threshold: float = 0.8
    required_fields: list = None
    phone_regex: str = r"^[\+]?[1-9][\d]{0,15}$"
    email_regex: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    zip_regex: str = r"^\d{5}(-\d{4})?$"
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = ["franchisee_owner", "corporate_address"]

@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_output: bool = True
    file_output: bool = True
    log_file: str = "logs/enrichment_pipeline.log"
    track_performance: bool = True
    performance_log: str = "logs/performance_metrics.json"

@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    track_api_calls: bool = True
    track_processing_time: bool = True
    track_success_rates: bool = True
    track_data_quality: bool = True
    low_success_rate_threshold: float = 0.8
    high_processing_time_threshold: int = 300
    low_confidence_rate_threshold: float = 0.7

@dataclass
class FilePathsConfig:
    """File paths configuration"""
    input_file: str = "data/Golden Chick_DE_Takehome.xlsx"
    output_json: str = "data/enriched_franchisees.json"
    output_excel: str = "data/enriched_franchisees_enhanced.xlsx"

class PipelineConfig:
    """Main configuration class for the enrichment pipeline"""
    
    def __init__(self, config_path: str = "config/config.yaml", environment: str = None):
        self.config_path = config_path
        self.environment = environment or os.getenv('PIPELINE_ENV', 'development')
        self._config_data = self._load_config()
        
        # Initialize configuration sections
        self.processing = self._load_processing_config()
        self.data_quality = self._load_data_quality_config()
        self.logging = self._load_logging_config()
        self.monitoring = self._load_monitoring_config()
        self.file_paths = self._load_file_paths_config()
        
        # Pipeline metadata
        self.name = self._config_data.get('pipeline', {}).get('name', 'franchisee-enrichment-pipeline')
        self.version = self._config_data.get('pipeline', {}).get('version', '1.0.0')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and merge configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Apply environment-specific overrides
            if 'environments' in config_data and self.environment in config_data['environments']:
                env_config = config_data['environments'][self.environment]
                config_data = self._deep_merge(config_data, env_config)
            
            return config_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def _deep_merge(self, base_dict: Dict, override_dict: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base_dict.copy()
        
        for key, value in override_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _load_processing_config(self) -> ProcessingConfig:
        """Load processing configuration"""
        processing_data = self._config_data.get('processing', {})
        return ProcessingConfig(
            max_concurrent_requests=processing_data.get('max_concurrent_requests', 3),
            batch_size=processing_data.get('batch_size', 5),
            rate_limit_delay_seconds=processing_data.get('rate_limit_delay_seconds', 2.0),
            sample_size=processing_data.get('sample_size'),
            max_retries=processing_data.get('max_retries', 3),
            retry_delay_seconds=processing_data.get('retry_delay_seconds', 1.0),
            timeout_seconds=processing_data.get('timeout_seconds', 30)
        )
    
    def _load_data_quality_config(self) -> DataQualityConfig:
        """Load data quality configuration"""
        dq_data = self._config_data.get('data_quality', {})
        validation_data = dq_data.get('validation', {})
        
        return DataQualityConfig(
            minimum_confidence_threshold=dq_data.get('minimum_confidence_threshold', 0.5),
            high_confidence_threshold=dq_data.get('high_confidence_threshold', 0.8),
            required_fields=dq_data.get('required_fields'),
            phone_regex=validation_data.get('phone_regex', r"^[\+]?[1-9][\d]{0,15}$"),
            email_regex=validation_data.get('email_regex', r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            zip_regex=validation_data.get('zip_regex', r"^\d{5}(-\d{4})?$")
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration"""
        logging_data = self._config_data.get('logging', {})
        
        return LoggingConfig(
            level=logging_data.get('level', 'INFO'),
            format=logging_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            console_output=logging_data.get('console_output', True),
            file_output=logging_data.get('file_output', True),
            log_file=logging_data.get('log_file', 'logs/enrichment_pipeline.log'),
            track_performance=logging_data.get('track_performance', True),
            performance_log=logging_data.get('performance_log', 'logs/performance_metrics.json')
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration"""
        monitoring_data = self._config_data.get('monitoring', {})
        alerts_data = monitoring_data.get('alerts', {})
        
        return MonitoringConfig(
            track_api_calls=monitoring_data.get('track_api_calls', True),
            track_processing_time=monitoring_data.get('track_processing_time', True),
            track_success_rates=monitoring_data.get('track_success_rates', True),
            track_data_quality=monitoring_data.get('track_data_quality', True),
            low_success_rate_threshold=alerts_data.get('low_success_rate_threshold', 0.8),
            high_processing_time_threshold=alerts_data.get('high_processing_time_threshold', 300),
            low_confidence_rate_threshold=alerts_data.get('low_confidence_rate_threshold', 0.7)
        )
    
    def _load_file_paths_config(self) -> FilePathsConfig:
        """Load file paths configuration"""
        paths_data = self._config_data.get('file_paths', {})
        
        return FilePathsConfig(
            input_file=paths_data.get('input_file', 'data/Golden Chick_DE_Takehome.xlsx'),
            output_json=paths_data.get('output_json', 'data/enriched_franchisees.json'),
            output_excel=paths_data.get('output_excel', 'data/enriched_franchisees_enhanced.xlsx')
        )
    
    def get_enrichment_source_config(self, source_name: str) -> Dict[str, Any]:
        """Get configuration for a specific enrichment source"""
        sources_config = self._config_data.get('enrichment_sources', {})
        return sources_config.get(source_name, {})
    
    def is_source_enabled(self, source_name: str) -> bool:
        """Check if an enrichment source is enabled"""
        source_config = self.get_enrichment_source_config(source_name)
        return source_config.get('enabled', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/debugging"""
        return {
            'pipeline': {
                'name': self.name,
                'version': self.version,
                'environment': self.environment
            },
            'processing': self.processing.__dict__,
            'data_quality': self.data_quality.__dict__,
            'logging': self.logging.__dict__,
            'monitoring': self.monitoring.__dict__,
            'file_paths': self.file_paths.__dict__
        }

def load_config(config_path: str = "config/config.yaml", environment: str = None) -> PipelineConfig:
    """Convenience function to load pipeline configuration"""
    return PipelineConfig(config_path, environment)

# Configuration validation
def validate_config(config: PipelineConfig) -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []
    
    # Validate processing settings
    if config.processing.max_concurrent_requests <= 0:
        issues.append("max_concurrent_requests must be positive")
    
    if config.processing.batch_size <= 0:
        issues.append("batch_size must be positive")
    
    # Validate confidence thresholds
    if not 0 <= config.data_quality.minimum_confidence_threshold <= 1:
        issues.append("minimum_confidence_threshold must be between 0 and 1")
    
    if not 0 <= config.data_quality.high_confidence_threshold <= 1:
        issues.append("high_confidence_threshold must be between 0 and 1")
    
    if config.data_quality.minimum_confidence_threshold > config.data_quality.high_confidence_threshold:
        issues.append("minimum_confidence_threshold cannot be greater than high_confidence_threshold")
    
    # Validate file paths
    input_path = Path(config.file_paths.input_file)
    if not input_path.exists():
        issues.append(f"Input file does not exist: {config.file_paths.input_file}")
    
    return issues