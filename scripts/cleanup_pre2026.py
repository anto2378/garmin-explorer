#!/usr/bin/env python3
"""
One-time cleanup: Delete all activities before Jan 1, 2026.
Run once during deployment.
"""
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_pre2026_activities():
    """Delete all activities with start_time before 2026-01-01."""
    with get_db() as db:
        # Delete old activities
        result = db.execute(
            "DELETE FROM cached_activities WHERE start_time < '2026-01-01'"
        )
        deleted = result.rowcount
        logger.info(f"Deleted {deleted} pre-2026 activities")

        # Delete old weekly stats
        result = db.execute(
            "DELETE FROM weekly_stats WHERE week_start < '2026-01-01'"
        )
        deleted_weeks = result.rowcount
        logger.info(f"Deleted {deleted_weeks} pre-2026 weekly stats")

    return deleted

if __name__ == "__main__":
    count = cleanup_pre2026_activities()
    logger.info(f"Cleanup complete: {count} activities removed")
