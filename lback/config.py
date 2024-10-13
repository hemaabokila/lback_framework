import os

class Config:

    DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///mydatabase.db")  
    SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")  
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")  
    API_VERSION = os.getenv("API_VERSION", "v1")
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

    @staticmethod
    def validate():
        if not Config.SECRET_KEY or Config.SECRET_KEY == "your_default_secret_key":
            raise ValueError("SECRET_KEY must be set and cannot be the default value.")
        
        if not Config.DATABASE_URI:
            raise ValueError("DATABASE_URI must be set.")
        
        if not Config.API_VERSION:
            raise ValueError("API_VERSION must be set.")
        
        if Config.LOGGING_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError("LOGGING_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL.")

if __name__ == "__main__":
    try:
        Config.validate()
        print("Application configuration is valid.")
    except ValueError as e:
        print(f"Configuration error: {e}")

