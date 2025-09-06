# Garmin Companion System - Deployment Guide

## 🚀 Final System Overview

The Garmin Companion System is now finalized with simple multi-user authentication and complete weekly digest functionality.

### ✅ What's Included

- **Multi-User Support**: 2-3 users configured via .env file
- **Simple Authentication**: No JWT complexity - just email/password stored in .env
- **Automatic Setup**: One command sets up users, groups, and database
- **Weekly Digests**: Complete analysis, leaderboards, achievements
- **WhatsApp Integration**: Ready for WhatsApp Business API
- **Background Tasks**: Automated syncing and digest generation

## 📋 Quick Start

### 1. Configuration

Copy and configure the environment file:

```bash
cp .env.production .env
```

Edit `.env` with your users' information:

```env
# User 1 - Admin
USER1_EMAIL=admin@yourcompany.com
USER1_PASSWORD=your-admin-password
USER1_NAME=Admin User
USER1_GARMIN_EMAIL=admin-garmin@gmail.com
USER1_GARMIN_PASSWORD=admin-garmin-password
USER1_ROLE=admin

# User 2
USER2_EMAIL=user2@yourcompany.com
USER2_PASSWORD=user2-password
USER2_NAME=Team Member 2
USER2_GARMIN_EMAIL=user2-garmin@gmail.com
USER2_GARMIN_PASSWORD=user2-garmin-password
USER2_ROLE=member

# User 3
USER3_EMAIL=user3@yourcompany.com
USER3_PASSWORD=user3-password
USER3_NAME=Team Member 3
USER3_GARMIN_EMAIL=user3-garmin@gmail.com
USER3_GARMIN_PASSWORD=user3-garmin-password
USER3_ROLE=member
```

### 2. Deploy System

Start the system:

```bash
docker-compose up -d
```

Initialize users and groups:

```bash
docker-compose exec web python setup_system.py
```

### 3. Access System

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔐 Authentication

### Simple Login

```bash
curl -X POST "http://localhost:8000/api/v1/simple-auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com", 
    "password": "your-admin-password"
  }'
```

### Check Auth Status

```bash
curl -X GET "http://localhost:8000/api/v1/simple-auth/status" \
  --cookie-jar cookies.txt --cookie cookies.txt
```

## 📊 Weekly Digest Usage

### Generate Digest Preview

```bash
# Get your group ID first
curl -X GET "http://localhost:8000/api/v1/groups/" \
  --cookie cookies.txt

# Preview digest
curl -X GET "http://localhost:8000/api/v1/digest/{group_id}/preview" \
  --cookie cookies.txt
```

### Send Weekly Digest

```bash
curl -X POST "http://localhost:8000/api/v1/digest/{group_id}/send" \
  --cookie cookies.txt
```

## 🔄 Activity Sync

### Manual Sync

```bash
curl -X POST "http://localhost:8000/api/v1/activities/sync/immediate" \
  --cookie cookies.txt
```

### Check Activity Stats

```bash
curl -X GET "http://localhost:8000/api/v1/activities/stats?days_back=30" \
  --cookie cookies.txt
```

## 🌐 WhatsApp Integration

Configure WhatsApp Business API in `.env`:

```env
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_API_TOKEN=your-whatsapp-business-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
DEFAULT_WHATSAPP_GROUP_ID=your-group-id@g.us
```

## 📅 Automated Scheduling

The system automatically:

- **Daily**: Syncs activities at 6 AM (configurable)
- **Weekly**: Generates and sends digests on Mondays at 8 AM
- **Monthly**: Cleans up old data

Configure schedules in `.env`:

```env
SYNC_SCHEDULE=0 6 * * *          # Daily at 6 AM
DIGEST_SCHEDULE=0 8 * * 1        # Mondays at 8 AM
```

## 🗂️ File Structure

```
garmin-explorer/
├── docker-compose.yml           # Docker services
├── .env                        # Configuration
├── setup_system.py             # One-time setup
├── app/
│   ├── models/                 # Database models
│   ├── services/               # Business logic
│   ├── api/                    # REST endpoints
│   └── core/                   # Core functionality
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

## 🚀 Production Deployment

### Docker Swarm / Kubernetes

1. Update `docker-compose.yml` for production:
   - Use external database (AWS RDS, etc.)
   - Configure proper secrets management
   - Add load balancing if needed

2. Set up monitoring:
   - Health checks: `/health`
   - Metrics endpoint (if needed)
   - Log aggregation

### Environment Variables

Essential production variables:

```env
DATABASE_URL=postgresql://user:pass@prod-db/garmin_companion
REDIS_URL=redis://prod-redis:6379
SECRET_KEY=your-strong-production-secret
DEBUG=false
WHATSAPP_API_TOKEN=your-production-token
```

## 🔧 Maintenance

### Backup Database

```bash
docker-compose exec db pg_dump -U garmin_user garmin_companion > backup.sql
```

### View Logs

```bash
docker-compose logs web
docker-compose logs worker
docker-compose logs db
```

### Update System

```bash
git pull
docker-compose build
docker-compose up -d
```

## 📞 Support

### Common Issues

1. **Garmin Auth Failed**: Check credentials in .env
2. **WhatsApp Not Sending**: Verify WhatsApp Business API setup
3. **No Activities**: Ensure Garmin sync is working
4. **Database Errors**: Check PostgreSQL connection

### Debug Commands

```bash
# Check system status
docker-compose exec web python -c "
from app.services.simple_auth_service import auth_service
print('Configured users:', len(auth_service.get_all_users()))
"

# Test Garmin connection
docker-compose exec web python -c "
from garminconnect import Garmin
client = Garmin('your-email', 'your-password')
client.login()
print('Garmin connection: OK')
"
```

---

## 🎉 System Complete!

Your Garmin Companion System is now ready for production with:

✅ **Simple Multi-User Authentication**  
✅ **Automated Activity Syncing**  
✅ **Weekly Digest Generation**  
✅ **WhatsApp Integration**  
✅ **Background Task Processing**  
✅ **Production-Ready Deployment**

**All user credentials are managed via .env file - no complex authentication needed!**