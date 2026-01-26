from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os

from user_store import get_user_store

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
    auth_provider: str = "local"  # "local", "google", "github"
    oauth_id: Optional[str] = None  # Provider-specific user ID
    avatar_url: Optional[str] = None  # Profile picture from OAuth


class UserInDB(User):
    hashed_password: Optional[str] = None  # Optional for OAuth users


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


async def seed_admin_user():
    """Seed the default admin user on startup."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "carlos-admin-2024")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@carlos.ai")

    store = get_user_store()

    # Check if admin already exists
    existing = await store.get_user(admin_username)
    if existing:
        return admin_username

    # Create admin user
    hashed_password = get_password_hash(admin_password)
    user_dict = {
        "username": admin_username,
        "email": admin_email,
        "hashed_password": hashed_password,
        "disabled": False,
        "is_admin": True,
        "auth_provider": "local",
        "oauth_id": None,
        "avatar_url": None,
    }
    await store.create_user(user_dict)
    print(f"  Seeded admin user: {admin_username}")
    return admin_username


async def get_all_users() -> list[User]:
    """Get all users (admin only)."""
    store = get_user_store()
    users = await store.get_all_users()
    return [
        User(
            username=u["username"],
            email=u.get("email"),
            disabled=u.get("disabled", False),
            is_admin=u.get("is_admin", False),
            auth_provider=u.get("auth_provider", "local"),
            oauth_id=u.get("oauth_id"),
            avatar_url=u.get("avatar_url"),
        )
        for u in users
    ]


async def set_user_admin(username: str, is_admin: bool) -> Optional[User]:
    """Promote or demote a user's admin status."""
    store = get_user_store()
    updated = await store.update_user(username, {"is_admin": is_admin})
    if not updated:
        return None
    return User(
        username=updated["username"],
        email=updated.get("email"),
        disabled=updated.get("disabled", False),
        is_admin=updated.get("is_admin", False),
        auth_provider=updated.get("auth_provider", "local"),
        oauth_id=updated.get("oauth_id"),
        avatar_url=updated.get("avatar_url"),
    )


async def set_user_disabled(username: str, disabled: bool) -> Optional[User]:
    """Enable or disable a user account."""
    store = get_user_store()
    updated = await store.update_user(username, {"disabled": disabled})
    if not updated:
        return None
    return User(
        username=updated["username"],
        email=updated.get("email"),
        disabled=updated.get("disabled", False),
        is_admin=updated.get("is_admin", False),
        auth_provider=updated.get("auth_provider", "local"),
        oauth_id=updated.get("oauth_id"),
        avatar_url=updated.get("avatar_url"),
    )


async def delete_user(username: str) -> bool:
    """Delete a user account permanently. Returns True if deleted, False if not found."""
    store = get_user_store()
    return await store.delete_user(username)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user(username: str) -> Optional[UserInDB]:
    store = get_user_store()
    user_dict = await store.get_user(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = await get_user(username)
    if not user:
        return None
    # OAuth users cannot login with password
    if user.auth_provider != "local":
        return None
    if not user.hashed_password:
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


async def create_user(user_create: UserCreate) -> User:
    store = get_user_store()

    if await store.username_exists(user_create.username):
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
        "auth_provider": "local",
        "oauth_id": None,
        "avatar_url": None,
    }
    await store.create_user(user_dict)
    return User(username=user_create.username, email=user_create.email, is_admin=False)


async def get_user_by_oauth(provider: str, oauth_id: str) -> Optional[UserInDB]:
    """Find a user by OAuth provider and ID."""
    store = get_user_store()
    user_dict = await store.get_user_by_oauth(provider, oauth_id)
    if user_dict:
        return UserInDB(**user_dict)
    return None


async def create_oauth_user(
    provider: str,
    oauth_id: str,
    email: str,
    username: str,
    avatar_url: Optional[str] = None
) -> User:
    """Create a new user from OAuth login."""
    store = get_user_store()

    # Generate unique username if already taken
    base_username = username
    counter = 1
    while await store.username_exists(username):
        username = f"{base_username}{counter}"
        counter += 1

    user_dict = {
        "username": username,
        "email": email,
        "hashed_password": None,  # OAuth users don't have passwords
        "disabled": False,
        "is_admin": False,
        "auth_provider": provider,
        "oauth_id": oauth_id,
        "avatar_url": avatar_url,
    }
    await store.create_user(user_dict)
    return User(**{k: v for k, v in user_dict.items() if k != "hashed_password"})


async def get_or_create_oauth_user(
    provider: str,
    oauth_id: str,
    email: str,
    name: str,
    avatar_url: Optional[str] = None
) -> User:
    """Get existing OAuth user or create a new one."""
    # Try to find existing user by OAuth ID
    existing_user = await get_user_by_oauth(provider, oauth_id)
    if existing_user:
        return User(**existing_user.model_dump(exclude={"hashed_password"}))

    # Create new OAuth user
    # Use email prefix as username, or name if email not available
    username = email.split("@")[0] if email else name.replace(" ", "").lower()
    return await create_oauth_user(provider, oauth_id, email, username, avatar_url)


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

    user = await get_user(username=token_data.username)
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
