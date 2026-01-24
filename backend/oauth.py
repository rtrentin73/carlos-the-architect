"""
OAuth authentication module for Carlos the Architect.

Supports Google and GitHub OAuth providers.
"""

import os
from authlib.integrations.starlette_client import OAuth

# OAuth configuration
oauth = OAuth()

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"}
    )
    print("  Google OAuth configured")
else:
    print("  Google OAuth not configured (missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET)")


# GitHub OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"}
    )
    print("  GitHub OAuth configured")
else:
    print("  GitHub OAuth not configured (missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET)")


# Frontend URL for OAuth callback redirect
OAUTH_REDIRECT_BASE = os.getenv("OAUTH_REDIRECT_BASE", "http://localhost:5173")


def is_google_enabled() -> bool:
    """Check if Google OAuth is configured."""
    return GOOGLE_CLIENT_ID is not None and GOOGLE_CLIENT_SECRET is not None


def is_github_enabled() -> bool:
    """Check if GitHub OAuth is configured."""
    return GITHUB_CLIENT_ID is not None and GITHUB_CLIENT_SECRET is not None
