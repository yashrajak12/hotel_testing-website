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
        "pool_size": 10,
        "max_overflow": 5,
    }
