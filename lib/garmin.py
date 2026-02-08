"""
Garmin Connect API wrapper with persistent token management.

Each user's OAuth tokens are stored in data/tokens/{user_name}/ via Garth.
Tokens are valid for ~1 year. On subsequent calls, the client re-authenticates
from the stored token without needing email/password.
"""

import logging
from datetime import date, timedelta
from pathlib import Path

from garminconnect import Garmin

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
TOKENS_DIR = DATA_DIR / "tokens"


def _token_dir(user_name: str) -> str:
    """Return the token storage path for a user, creating it if needed."""
    path = TOKENS_DIR / user_name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def login(user_name: str, email: str, password: str) -> Garmin:
    """
    Authenticate with Garmin Connect using email/password.
    Saves OAuth tokens to disk for future use.

    Returns an authenticated Garmin client.
    """
    token_dir = _token_dir(user_name)
    client = Garmin(email, password)
    client.login()
    client.garth.dump(token_dir)
    logger.info("Authenticated and saved tokens for %s", user_name)
    return client


def resume(user_name: str) -> Garmin:
    """
    Re-authenticate from stored tokens (no email/password needed).
    Raises FileNotFoundError if no tokens exist for this user.
    """
    token_dir = _token_dir(user_name)
    token_path = Path(token_dir)

    # Check that token files actually exist
    if not any(token_path.iterdir()):
        raise FileNotFoundError(
            f"No tokens found for user '{user_name}' in {token_dir}"
        )

    client = Garmin()
    client.login(token_dir)
    logger.info("Resumed session from tokens for %s", user_name)
    return client


def get_client(
    user_name: str, email: str | None = None, password: str | None = None
) -> Garmin:
    """
    Get an authenticated Garmin client.
    Tries stored tokens first; falls back to email/password if provided.
    """
    try:
        return resume(user_name)
    except (FileNotFoundError, Exception) as e:
        logger.info("Could not resume session for %s: %s", user_name, e)
        if email and password:
            return login(user_name, email, password)
        raise


def get_activities(client: Garmin, days: int = 30) -> list[dict]:
    """Fetch recent activities for the given number of days."""
    return client.get_activities_by_date(
        startdate=(date.today() - timedelta(days=days)).isoformat(),
        enddate=date.today().isoformat(),
    )


def get_display_name(client: Garmin) -> str:
    """Get user's display name from Garmin."""
    return client.get_full_name() or "Unknown"
