"""
Configuration module for the CTI Aggregator.
Handles loading and validating configuration settings.
"""

import os
import yaml
import logging

logger = logging.getLogger(__name__)

def load_config(config_path):
    """
    Load configuration from a YAML file.
    
    Args:
        config_path (str): Path to the configuration file
    
    Returns:
        dict: Configuration settings
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the configuration is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required configuration sections
    required_sections = ['database', 'sources', 'ai', 'reporting']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    
    # Validate database configuration
    if 'path' not in config['database']:
        raise ValueError("Database path not specified in configuration")
    
    # Validate sources configuration
    if not config['sources'] or not isinstance(config['sources'], list):
        raise ValueError("No intelligence sources specified in configuration")
    
    # Validate AI configuration
    if 'api_key' not in config['ai']:
        raise ValueError("AI API key not specified in configuration")
    
    # Validate reporting configuration
    if 'output_directory' not in config['reporting']:
        raise ValueError("Reporting output directory not specified in configuration")
    if 'time_window_days' not in config['reporting']:
        config['reporting']['time_window_days'] = 30  # Default to 30 days if not specified
    
    # Create output directory if it doesn't exist
    os.makedirs(config['reporting']['output_directory'], exist_ok=True)
    
    return config

def get_default_config():
    """
    Generate a default configuration template.
    
    Returns:
        dict: Default configuration
    """
    return {
        'database': {
            'path': 'data/cti.db'
        },
        'sources': [
            {
                'name': 'Krebs on Security',
                'url': 'https://krebsonsecurity.com',
                'type': 'rss',
                'feed_url': 'https://krebsonsecurity.com/feed/'
            },
            {
                'name': 'Bleeping Computer',
                'url': 'https://www.bleepingcomputer.com',
                'type': 'rss',
                'feed_url': 'https://www.bleepingcomputer.com/feed/'
            },
            {
                'name': 'The Hacker News',
                'url': 'https://thehackernews.com',
                'type': 'rss',
                'feed_url': 'https://feeds.feedburner.com/TheHackersNews'
            }
        ],
        'ai': {
            'api_key': 'YOUR_API_KEY_HERE',
            'model': 'claude-3-opus-20240229'
        },
        'reporting': {
            'output_directory': 'reports',
            'time_window_days': 30
        }
    }

def create_default_config(output_path='config.yaml'):
    """
    Create a default configuration file.
    
    Args:
        output_path (str): Path to write the configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        config = get_default_config()
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Failed to create default configuration: {str(e)}")
        return False
