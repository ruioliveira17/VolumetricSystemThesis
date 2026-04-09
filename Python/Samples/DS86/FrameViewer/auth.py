import os

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = os.environ.get("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))

pwd_context = CryptContext(schemes=["bcrypt"])

def get_password_hash(password: str) -> str:
    """
    Hashes the given password using bcrypt algorithm.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies the given plain password against the hashed password and returns True or False wether they match.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """
    Creates a JWT access token with the given data and an expiration time of 30 minutes.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {**data, "type": "access", "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token

def create_refresh_token(data: dict) -> str:
    """
    Creates a JWT refresh token with the given data and an expiration time of 7 days.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_data = {**data, "type": "refresh", "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token:str) -> dict:
    """
    Verifies the given JWT token and returns the decoded data if the token is valid, otherwise raises an exception.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    return payload