from os import getenv
from dotenv import load_dotenv


load_dotenv()


ALGORITHM = getenv('ALGORITHM')
SECRET_KEY = getenv('SECRET_KEY')

DB_USER = getenv('DB_USER')
DB_PASSWORD = getenv('DB_PASSWORD')
DB_HOST = getenv('DB_HOST')
DB_PORT = getenv('DB_PORT')
DB_NAME = getenv('DB_NAME')

DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

print(ALGORITHM)

def get_auth_data():
    return {'secret_key': SECRET_KEY, 'algorithm': ALGORITHM}

