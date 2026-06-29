#PASSWORD HASGING AND JWT tokens
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from config import settings
from jose import jwt, JWTError


password_hash = PasswordHash((
    Argon2Hasher(),
    BcryptHasher(),
))


def hash_password(password: str) -> str:
    return password_hash.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)



def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp" : expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(), 
        algorithm=settings.algorithm
    )


    return encoded_jwt


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm]
        )

        return payload
    except JWTError:
        return None




