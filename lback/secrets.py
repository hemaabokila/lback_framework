import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet


load_dotenv()

KEY = os.getenv('ENCRYPTION_KEY')
if not KEY:
    raise ValueError("ENCRYPTION_KEY must be set in the environment variables.")

fernet = Fernet(KEY.encode())

def decrypt(encrypted_data):
    return fernet.decrypt(encrypted_data.encode()).decode()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'default_secret_key'
    
  
    DATABASE_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'default_user'),
        'password': decrypt(os.getenv('DB_PASSWORD_ENCRYPTED')),  
        'database': os.getenv('DB_NAME', 'default_database')
    }

    
    API_KEYS = {
        'service_1': decrypt(os.getenv('API_KEY_SERVICE_1_ENCRYPTED')),
        'service_2': decrypt(os.getenv('API_KEY_SERVICE_2_ENCRYPTED')),
    }

    
    EMAIL_CONFIG = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.example.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'username': os.getenv('EMAIL_USERNAME', 'default_email@example.com'),
        'password': decrypt(os.getenv('EMAIL_PASSWORD_ENCRYPTED')),
    }

