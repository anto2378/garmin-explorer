# 🏃 Garmin Explorer

A modern FastAPI-based dashboard for Garmin Connect fitness data with real-time activity tracking, user management, and WhatsApp digest integration.

![Dashboard Screenshot](assets/dashboard-mockup.png)

## ✨ Features

- **🏃 Real-time Activity Dashboard**: Beautiful, responsive dashboard showing fitness statistics
- **📊 Year-to-Date Analytics**: Track progress with comprehensive YTD metrics
- **👥 Multi-User Support**: Manage multiple Garmin accounts with user authentication
- **📱 WhatsApp Integration**: Automated weekly digest messages for groups
- **🔄 Background Sync**: Celery-powered background tasks for data synchronization
- **🗄️ Flexible Database**: SQLite for local development, PostgreSQL for production
- **🐳 Docker Ready**: Complete containerization support with docker-compose

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ 
- [uv](https://github.com/astral-sh/uv) package manager

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/garmin-explorer/garmin-explorer.git
   cd garmin-explorer
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Garmin Connect credentials and settings
   ```

4. **Initialize the database**
   ```bash
   uv run python setup_system.py
   ```

5. **Generate realistic test data**
   ```bash
   uv run python scripts/generate_realistic_data.py
   ```

6. **Start the development server**
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **View the dashboard**
   Open [http://localhost:8000/static/dashboard.html](http://localhost:8000/static/dashboard.html)

### Docker Development Setup

1. **Start with docker-compose**
   ```bash
   docker-compose up -d
   ```

2. **Initialize database (first time only)**
   ```bash
   docker-compose exec web python setup_system.py
   docker-compose exec web python scripts/generate_realistic_data.py
   ```

## 🏗️ Project Structure

```
garmin-explorer/
├── app/                     # FastAPI application
│   ├── api/v1/endpoints/    # API endpoints
│   ├── core/                # Core configuration and database
│   ├── models/              # SQLAlchemy models
│   ├── services/            # Business logic services
│   └── tasks.py             # Celery background tasks
├── scripts/                 # Utility scripts
│   ├── generate_realistic_data.py  # Generate test data
│   ├── seed_test_data.py           # Seed database
│   └── tests/                      # Test files
├── static/                  # Static web files
│   └── dashboard.html       # Main dashboard interface
├── docs/                    # Documentation
├── assets/                  # Images and mockups
├── main.py                  # FastAPI application entry point
├── setup_system.py          # Database initialization
├── pyproject.toml          # uv/pip package configuration
└── docker-compose.yml      # Docker services
```

## 🎯 Core Components

### Dashboard API (`/api/v1/dashboard/`)
- **`GET /weekly`**: Weekly activity data with YTD comparisons
- **`GET /digest/latest`**: Latest weekly digest for WhatsApp sharing

### User Management (`/api/v1/users/`)
- User CRUD operations
- Garmin credential management
- Activity history tracking

### Background Services
- **Celery Workers**: Async Garmin data synchronization
- **Redis**: Task queue and caching
- **Database**: SQLite (dev) / PostgreSQL (prod)

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
DATABASE_URL=sqlite:///./garmin_local.db

# Garmin Connect Credentials
ANTO_GARMIN_EMAIL=your-email@example.com
ANTO_GARMIN_PASSWORD=your-password
JEFF_GARMIN_EMAIL=friend-email@example.com  
JEFF_GARMIN_PASSWORD=friend-password

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (for background tasks)
REDIS_URL=redis://localhost:6379

# WhatsApp Integration (optional)
WHATSAPP_API_KEY=your-whatsapp-api-key
```

### Production Environment

For production deployment:

1. **Update environment**
   ```bash
   cp .env.example .env.production
   # Configure production values
   ```

2. **Use PostgreSQL**
   ```bash
   DATABASE_URL=postgresql://user:pass@localhost/garmin_explorer
   ```

3. **Deploy with Docker**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

## 📊 Dashboard Features

### Main Dashboard Sections

1. **User Statistics**: Year-to-date metrics per user
   - Total steps, running distance, calories burned
   - Activity breakdowns and trends

2. **Monthly Comparison**: Performance vs. monthly averages
   - Week-over-week comparisons
   - Trending indicators (↑ ↓)

3. **Weekly Activity Digest**: Current week summary
   - Group totals and most popular activities
   - Export-ready WhatsApp digest format

4. **Member Comparison**: YTD leaderboard
   - Ranking by various metrics
   - Visual ranking badges

### Real-time Updates
- Data refreshes every 30 seconds
- Background sync with Garmin Connect
- Responsive design for mobile/desktop

## 🛠️ Development

### Adding New Features

1. **Create database models** in `app/models/`
2. **Add API endpoints** in `app/api/v1/endpoints/`
3. **Implement services** in `app/services/`
4. **Update dashboard** in `static/dashboard.html`

### Running Tests

```bash
uv run pytest scripts/tests/
```

### Database Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "Add new feature"

# Apply migration
uv run alembic upgrade head
```

### Background Tasks

Add new Celery tasks in `app/tasks.py`:

```python
@celery_app.task
def sync_user_activities(user_id: str):
    # Your background task logic
    pass
```

## 🔌 API Documentation

Once the server is running, view the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Documentation

- [CLAUDE.md](CLAUDE.md) - Technical architecture and development guide
- [API Documentation](http://localhost:8000/docs) - Interactive API explorer
- [Project Status](PROJECT_STATUS.md) - Current development status

## 🐛 Troubleshooting

### Common Issues

**Database connection errors**
```bash
# Reset database
rm garmin_local.db
uv run python setup_system.py
```

**Missing dependencies**
```bash
# Reinstall with uv
uv sync --reinstall
```

**Garmin authentication fails**
- Verify credentials in `.env` file
- Check if 2FA is enabled on Garmin account
- Ensure network connectivity

**Dashboard not loading data**
- Check if API server is running on port 8000
- Verify database has test data
- Check browser console for JavaScript errors

## 📞 Support

For support and questions:
- Open an [Issue](https://github.com/garmin-explorer/garmin-explorer/issues)
- Check the [Documentation](docs/)
- Review [CLAUDE.md](CLAUDE.md) for technical details

---

**Built with ❤️ using FastAPI, SQLAlchemy, and modern web technologies**