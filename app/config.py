from os import getenv
from dotenv import load_dotenv


load_dotenv()


ALGORITHM = getenv('ALGORITHM')
SECRET_KEY = getenv('SECRET_KEY')


def get_auth_data():
    return {'secret_key': SECRET_KEY, 'algorithm': ALGORITHM}

