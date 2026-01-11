import os
from dotenv import load_dotenv

load_dotenv()

# GLM API Key
GLM_API_KEY = os.getenv("GLM_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invoices.db")

# Upload settings
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB per file
MAX_FILES_PER_BATCH = 200

# Confidence threshold
CONFIDENCE_THRESHOLD = 0.9

# Anomaly rules
AMOUNT_ANOMALY_THRESHOLD = 5000  # Amount > 5000 needs review
DATE_ANOMALY_DAYS = 180  # Invoice older than 180 days
