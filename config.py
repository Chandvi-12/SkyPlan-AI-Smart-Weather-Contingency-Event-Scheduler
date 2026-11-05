import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'skyplan-ai-secret-key-fallback-2026')
    BASE_DIR = BASE_DIR
    
    # MongoDB settings
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/skyplan_ai')
    DB_NAME = os.getenv('DB_NAME', 'skyplan_ai')
    DATA_DIR = BASE_DIR / 'data'
    
    # Weather settings
    WEATHER_PROVIDER = os.getenv('WEATHER_PROVIDER', 'open-meteo')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
    
    # ML Models directory
    MODELS_DIR = BASE_DIR / 'trained_models'
    
    # Background Scheduler
    ENABLE_BACKGROUND_SCHEDULER = os.getenv('ENABLE_BACKGROUND_SCHEDULER', 'True').lower() in ('true', '1', 'yes')
    RISK_CHECK_INTERVAL_MINUTES = int(os.getenv('RISK_CHECK_INTERVAL_MINUTES', '30'))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

