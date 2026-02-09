#!/usr/bin/env python3
"""
Daily sync daemon for Garmin Explorer.
Syncs all users with OAuth tokens.
"""
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.cache import sync_user, compute_weekly_stats
from lib.garmin import TOKENS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def get_connected_users() -> list[str]:
    """Get list of users with valid OAuth tokens."""
    if not TOKENS_DIR.exists():
        return []
    return [
        d.name
        for d in sorted(TOKENS_DIR.iterdir())
        if d.is_dir() and any(d.iterdir())
    ]

def sync_all():
    """Sync all connected users."""
    users = get_connected_users()

    if not users:
        logger.warning("No connected users found")
        return

    logger.info(f"Starting daily sync for {len(users)} user(s): {', '.join(users)}")

    success_count = 0
    error_count = 0

    for user_name in users:
        try:
            logger.info(f"Syncing {user_name}...")
            result = sync_user(user_name)
            logger.info(
                f"✓ {user_name}: fetched={result['fetched']}, "
                f"new={result['new']}, total={result['cached']}"
            )

            # Recompute weekly stats
            compute_weekly_stats(user_name)
            logger.info(f"✓ {user_name}: weekly stats updated")

            success_count += 1

        except Exception as e:
            logger.error(f"✗ {user_name}: {e}", exc_info=True)
            error_count += 1

    logger.info(f"Daily sync complete: {success_count} succeeded, {error_count} failed")

    # Exit with error if all syncs failed
    if error_count > 0 and success_count == 0:
        exit(1)

if __name__ == "__main__":
    sync_all()
