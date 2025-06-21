import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://travel_user:securepassword@localhost:5432/travel_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False