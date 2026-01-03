# config.py
import os

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,     
        "pool_recycle": 300,      
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {"sslmode": "require"}
    }

    SECRET_KEY = os.getenv('SECRET_KEY') or 'fallback-secret-key-for-development-only-do-not-use-in-production'


