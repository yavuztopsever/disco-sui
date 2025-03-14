from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.parent  # Get to the project root
DATA_DIR = BASE_DIR / "data"
CONTENT_DIR = DATA_DIR / "content"

# Ensure directories exist
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# Content service configuration
CONTENT_CONFIG = {
    # Directory settings
    'CONTENT_DIR': str(CONTENT_DIR),
    
    # Logging settings
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
}
