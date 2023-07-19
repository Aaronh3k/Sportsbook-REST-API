import os

# Service id
SERVICE_ID = os.getenv("id", "dev-sports-book-rest-api")

# Environment identifier
APP_ENVIRONMENT  = os.getenv("APP_ENVIRONMENT", "dev")

# Database
RDS_HOSTNAME  = os.getenv("RDS_HOSTNAME") or "localhost"
RDS_PORT      = os.getenv("RDS_PORT")     or "5432"
RDS_DB_NAME   = os.getenv("RDS_DB_NAME")  or "sports_book"
RDS_USERNAME  = os.getenv("RDS_USERNAME") or "postgres"
RDS_PASSWORD  = os.getenv("RDS_PASSWORD") or "newpassword"

DB_URI = "postgresql://{}:{}@{}:{}/{}".format(RDS_USERNAME, RDS_PASSWORD, RDS_HOSTNAME, RDS_PORT, RDS_DB_NAME)

SQLALCHEMY_POOL_RECYCLE = int(os.getenv("SQLALCHEMY_POOL_RECYCLE", 3600))
SQLALCHEMY_DATABASE_URI = DB_URI

EX_API_KEY = os.getenv("External_API_KEY") or ""
EX_API = os.getenv("EX_API") or ""

# API URI Prefix
BASE_PATH = "/v1"
API_URI   = os.getenv("API_URI", "http://0.0.0.0:5000")