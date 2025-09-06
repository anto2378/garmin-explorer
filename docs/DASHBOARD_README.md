# Fake Sporters - Weekly Activity Dashboard

A public dashboard displaying weekly activity data for all users, with focus on steps, running distance, and active calories.

## Features

### 🏃‍♂️ Public Dashboard
- **URL**: `nebluda.com/fake-sporters`
- **Display**: Weekly activity data for all active users
- **Metrics**: Steps, running distance, active calories, total activities
- **Comparisons**: Previous week, monthly average, year-to-date
- **Week Navigation**: Current week, last week, 2-4 weeks ago

### 📱 WhatsApp Digest
- **Endpoint**: `/api/v1/whatsapp/weekly`
- **Previous Week**: `/api/v1/whatsapp/previous-week`
- **Format**: WhatsApp-ready formatted message
- **Content**: Group totals, top performers, individual summaries

## API Endpoints

### Dashboard API
```
GET /api/v1/dashboard/weekly?week_offset=0
```
- `week_offset`: Number of weeks back (0 = current week)
- Returns: Complete dashboard data with comparisons

### WhatsApp Digest API  
```
GET /api/v1/whatsapp/weekly?week_offset=0
GET /api/v1/whatsapp/previous-week
```
- Returns: WhatsApp-formatted message ready for sharing

## Dashboard Features

### Weekly Overview
- **Total Steps**: Sum of all user steps for the week
- **Running Distance**: Total kilometers from running activities  
- **Active Calories**: Total calories burned from all activities
- **Total Activities**: Count of all recorded activities
- **Active Users**: Number of users with at least one activity

### Individual Performance
- User ranking by total activities
- Individual metrics: steps, running distance, calories, activities
- Activity breakdown by type for each user

### Comparisons
- **Previous Week**: Change in metrics vs last week (with percentages)
- **Monthly Average**: Comparison with 4-week rolling average
- **Year-to-Date**: Comparison with weekly average since January 1st

### WhatsApp Integration
- Formatted digest messages ready for group sharing
- Leaderboards for different metrics
- Individual performance summaries
- Motivational content with emojis

## Data Sources

The dashboard pulls data from the Activity model which includes:
- **Steps**: From `processed_metrics.steps` or `raw_data.steps/totalSteps`
- **Running Distance**: From activities with type 'running', 'run', or 'jogging'
- **Active Calories**: From `calories` field or `processed_metrics.active_calories` or `raw_data.calories/activeCalories`
- **Activities**: All recorded Garmin activities

## Usage Examples

### View Current Week Dashboard
Visit: `http://your-domain.com/fake-sporters`

### Get WhatsApp Digest for Previous Week (Monday sharing)
```bash
curl http://your-api-domain.com/api/v1/whatsapp/previous-week
```

### Get Dashboard Data for 2 Weeks Ago
```bash
curl http://your-api-domain.com/api/v1/dashboard/weekly?week_offset=2
```

## Configuration

### Environment Setup
The dashboard works with your existing FastAPI application. Make sure:
1. Database is configured with User and Activity models
2. Static files are served from `/static` directory
3. CORS is configured for your domain

### Domain Configuration
To serve at `nebluda.com/fake-sporters`:
1. Configure your reverse proxy (nginx/Apache) to route the subdomain
2. Update CORS settings in `app.core.config.py`
3. The `/fake-sporters` endpoint serves the dashboard HTML

## Mobile Responsive
The dashboard is fully responsive and works well on:
- Desktop browsers
- Tablets  
- Mobile devices
- WhatsApp in-app browser

## Week Definition
- Week starts on Monday 00:00:00
- Week ends on Sunday 23:59:59
- Week numbers follow ISO calendar standard
- All times are handled in UTC/server timezone