import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
fernet=Fernet(os.getenv('encryptionkey').encode())

def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    return fernet.decrypt(encrypted_value.encode()).decode()