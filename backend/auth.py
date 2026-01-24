from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "carlos-architect-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: bool = False
    is_admin: bool = False


class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# In-memory user storage (replace with database in production)
users_db: dict[str, dict] = {}


def seed_admin_user():
    """Seed the default admin user on startup."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "carlos-admin-2024")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@carlos.ai")

    if admin_username not in users_db:
        hashed_password = get_password_hash(admin_password)
        users_db[admin_username] = {
            "username": admin_username,
            "email": admin_email,
            "hashed_password": hashed_password,
            "disabled": False,
            "is_admin": True,
        }
        print(f"  Seeded admin user: {admin_username}")
    return admin_username


def get_all_users() -> list[User]:
    """Get all users (admin only)."""
    return [
        User(
            username=u["username"],
            email=u.get("email"),
            disabled=u.get("disabled", False),
            is_admin=u.get("is_admin", False),
        )
        for u in users_db.values()
    ]


def set_user_admin(username: str, is_admin: bool) -> Optional[User]:
    """Promote or demote a user's admin status."""
    if username not in users_db:
        return None
    users_db[username]["is_admin"] = is_admin
    user_dict = users_db[username]
    return User(
        username=user_dict["username"],
        email=user_dict.get("email"),
        disabled=user_dict.get("disabled", False),
        is_admin=user_dict.get("is_admin", False),
    )


def set_user_disabled(username: str, disabled: bool) -> Optional[User]:
    """Enable or disable a user account."""
    if username not in users_db:
        return None
    users_db[username]["disabled"] = disabled
    user_dict = users_db[username]
    return User(
        username=user_dict["username"],
        email=user_dict.get("email"),
        disabled=user_dict.get("disabled", False),
        is_admin=user_dict.get("is_admin", False),
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    if username in users_db:
        user_dict = users_db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_user(user_create: UserCreate) -> User:
    if user_create.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user_create.password)
    user_dict = {
        "username": user_create.username,
        "email": user_create.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "is_admin": False,
    }
    users_db[user_create.username] = user_dict
    return User(username=user_create.username, email=user_create.email, is_admin=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require admin role for an endpoint."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
