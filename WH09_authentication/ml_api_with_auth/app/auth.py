"""Модуль для аутентификации и авторизации."""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.models import TokenData

# Настройки безопасности
SECRET_KEY = "your-secret-key-change-in-production"  # В продакшене использовать переменную окружения
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# "База данных" пользователей в памяти
# Используем предвычисленные хеши для избежания проблем при импорте
users_db = {
    "admin": {
        "username": "admin",
        # bcrypt hash для "admin123"
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWkZ5rHy2E7D7zKK",
        "role": "admin"
    },
    "user": {
        "username": "user",
        # bcrypt hash для "user123"
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "role": "user"
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хешу."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Хеширует пароль."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Аутентифицирует пользователя."""
    user = users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Получает текущего пользователя из токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role is None:
            raise credentials_exception

        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

    user = users_db.get(token_data.username)
    if user is None:
        raise credentials_exception

    return user


def require_role(required_role: str):
    """Декоратор для проверки роли пользователя."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    return role_checker


def register_user(username: str, password: str, role: str = "user") -> dict:
    """Регистрирует нового пользователя."""
    if username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    if role not in ["user", "admin"]:
        role = "user"

    hashed_password = get_password_hash(password)
    user = {
        "username": username,
        "hashed_password": hashed_password,
        "role": role
    }
    users_db[username] = user

    return {"username": username, "role": role}
