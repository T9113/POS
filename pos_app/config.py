import os
import sys

# Detect frozen PyInstaller executable
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # Directory where .exe is located
    APP_DIR = os.path.dirname(sys.executable)
    # Temporary directory where PyInstaller extracts bundled files
    RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    # Running from Python source (d:\Cli\POS)
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database path - sits right next to the .exe for 100% portability
DB_PATH = os.path.join(APP_DIR, "pos_data.db")

# User data directories
DATA_DIR = os.path.join(APP_DIR, "data")
BACKUPS_DIR = os.path.join(APP_DIR, "backups")
EXPORTS_DIR = os.path.join(APP_DIR, "exports")
PRODUCT_IMAGES_DIR = os.path.join(DATA_DIR, "product_images")
ASSETS_DIR = os.path.join(RESOURCE_DIR, "assets")

# Ensure required local directories exist
for path in [DATA_DIR, BACKUPS_DIR, EXPORTS_DIR, PRODUCT_IMAGES_DIR]:
    os.makedirs(path, exist_ok=True)

# Application metadata
APP_NAME = "SwiftPOS"
APP_VERSION = "1.0.0"
DEFAULT_CURRENCY = "Rs"
DEFAULT_TAX_RATE = 0.0
DEFAULT_TAX_NAME = "VAT"
