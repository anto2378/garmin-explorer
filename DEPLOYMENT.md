# Deployment Instructions: Daily Auto-Sync Feature

## Summary of Changes

This deployment adds:
- Daily automatic sync at 3 AM via systemd timer
- Last sync timestamps displayed in Dashboard and Stream pages
- Jan 1, 2026 cutoff - only activities from 2026 onwards are fetched
- Data cleanup to remove pre-2026 activities
- Manual sync still available via Stream page

## Files Modified

- `lib/database.py` - Added migration for last_synced_at column
- `lib/cache.py` - Changed sync logic to 2026-01-01 cutoff
- `lib/garmin.py` - Updated get_activities signature
- `pages/dashboard.py` - Display last sync times
- `pages/stream.py` - Display last sync times in status line

## Files Created

- `scripts/cleanup_pre2026.py` - One-time cleanup script
- `scripts/daily_sync.py` - Daily sync daemon
- `server/garmin-sync.service` - Systemd service unit
- `server/garmin-sync.timer` - Systemd timer unit

---

## Deployment Steps

### Step 1: Deploy Code

The database migration will run automatically when the app starts:

```bash
./deploy.sh
```

### Step 2: Run Cleanup Script

Remove all pre-2026 activities from the database:

```bash
ssh web-nebluda "cd /opt/garmin-explorer && /usr/local/bin/uv run python scripts/cleanup_pre2026.py"
```

### Step 3: Install Systemd Timer

Install and enable the daily sync timer:

```bash
# Copy service files
ssh web-nebluda "sudo cp /opt/garmin-explorer/server/garmin-sync.service /etc/systemd/system/"
ssh web-nebluda "sudo cp /opt/garmin-explorer/server/garmin-sync.timer /etc/systemd/system/"

# Reload systemd and enable timer
ssh web-nebluda "sudo systemctl daemon-reload"
ssh web-nebluda "sudo systemctl enable garmin-sync.timer"
ssh web-nebluda "sudo systemctl start garmin-sync.timer"
```

### Step 4: Verify Timer is Active

```bash
ssh web-nebluda "systemctl list-timers garmin-sync.timer"
```

Expected output should show:
- Timer is active and waiting
- Next trigger time at 03:00:00

---

## Testing & Verification

### Test Manual Trigger

Test the sync service manually:

```bash
ssh web-nebluda "sudo systemctl start garmin-sync.service"
ssh web-nebluda "journalctl -u garmin-sync --since '1 minute ago'"
```

### Check Database Migration

Verify the last_synced_at column was added:

```bash
ssh web-nebluda "cd /opt/garmin-explorer && sqlite3 data/garmin.db 'PRAGMA table_info(users)' | grep last_synced_at"
```

### Verify Cleanup

Confirm no pre-2026 activities remain:

```bash
ssh web-nebluda "cd /opt/garmin-explorer && sqlite3 data/garmin.db 'SELECT COUNT(*) FROM cached_activities WHERE start_time < \"2026-01-01\"'"
```

Should return: 0

### Check UI Changes

1. Visit https://fake-sporter.nebluda.com/
2. Dashboard should show "Last Sync" section in left sidebar with timestamps
3. Stream page should show sync times in the status line (e.g., "Anto (2h ago)")

---

## Monitoring

### View Sync Logs

```bash
# Follow live logs
ssh web-nebluda "journalctl -u garmin-sync -f"

# View recent logs
ssh web-nebluda "journalctl -u garmin-sync --since today"
```

### Check Next Scheduled Run

```bash
ssh web-nebluda "systemctl status garmin-sync.timer"
```

### After 3 AM - Verify Automatic Run

```bash
ssh web-nebluda "journalctl -u garmin-sync --since '02:55' --until '03:15'"
```

---

## Rollback

If needed, disable the timer and revert code:

```bash
# Stop and disable timer
ssh web-nebluda "sudo systemctl stop garmin-sync.timer"
ssh web-nebluda "sudo systemctl disable garmin-sync.timer"

# Revert code changes
git revert HEAD
./deploy.sh
```

Note: The database migration is backward compatible (just adds a nullable column), so no database rollback is needed.

---

## Troubleshooting

### Timer not triggering

Check timer status:
```bash
ssh web-nebluda "systemctl status garmin-sync.timer"
```

### Service fails

Check logs:
```bash
ssh web-nebluda "journalctl -u garmin-sync -n 50"
```

### No sync timestamps in UI

1. Verify database migration ran: `PRAGMA table_info(users)`
2. Trigger manual sync via Stream page
3. Check that last_synced_at is populated: `SELECT name, last_synced_at FROM users`
