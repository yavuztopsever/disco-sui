from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.parent  # Get to the project root
DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = DATA_DIR / "analysis"

# Ensure directories exist
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Analysis service configuration
ANALYSIS_CONFIG = {
    # Directory settings
    'ANALYSIS_DIR': str(ANALYSIS_DIR),
    
    # Logging settings
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
}
