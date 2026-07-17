import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-replace-in-prod-12345')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "resume_matcher.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configurations
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'uploads'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16 MB limit
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # Rate Limiting Configurations
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per day; 30 per hour; 2 per second')
    
    # Gemini AI Config
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    
    # Environment
    ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = ENV == 'development'
