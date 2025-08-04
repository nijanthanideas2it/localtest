# Projexiq - Project Management System Backend API

A modern, scalable backend API for the Projexiq Project Management System built with FastAPI, SQLAlchemy, and PostgreSQL.

## 🚀 Features

### Core Functionality
- **User Management**: Authentication, authorization, and user profiles
- **Project Management**: Create, update, and manage projects with team collaboration
- **Task Management**: Comprehensive task tracking with assignments and dependencies
- **Time Tracking**: Log and track time spent on tasks and projects
- **File Management**: Upload, version, and manage project files with permissions
- **Comments & Collaboration**: Real-time commenting and team communication
- **Analytics & Reporting**: Comprehensive project and team analytics
- **Notifications**: Real-time notifications and email alerts
- **Audit Trail**: Complete audit logging for compliance and tracking

### Technical Features
- **RESTful API**: Complete REST API with OpenAPI documentation
- **WebSocket Support**: Real-time communication for live updates
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Granular permissions and access control
- **Database Migrations**: Alembic for schema versioning
- **Comprehensive Testing**: Unit and integration tests
- **API Documentation**: Auto-generated Swagger and ReDoc documentation

## 🛠 Technology Stack

- **Framework**: FastAPI 0.116.1
- **Language**: Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy 2.0.42 ORM
- **Authentication**: JWT with python-jose
- **Password Hashing**: bcrypt with passlib
- **Validation**: Pydantic 2.11.7
- **Migrations**: Alembic 1.16.4
- **Dependency Management**: Poetry
- **Testing**: pytest 8.4.1 + httpx
- **Code Quality**: Black, isort, flake8, mypy

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- Poetry (for dependency management)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
```env
# Application
DEBUG=true
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_HOSTS=["http://localhost:3000","http://localhost:8080"]

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/project_management
DATABASE_ECHO=false

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password
PASSWORD_MIN_LENGTH=8
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb project_management

# Run database migrations
poetry run alembic upgrade head

# Seed initial data (optional)
poetry run python scripts/seed_data.py
```

### 4. Start Development Server

```bash
# Start the development server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
backend/
├── app/                          # Main application package
│   ├── api/                      # API route handlers
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── users.py             # User management endpoints
│   │   ├── projects.py          # Project management endpoints
│   │   ├── tasks.py             # Task management endpoints
│   │   ├── time_entries.py      # Time tracking endpoints
│   │   ├── files.py             # File management endpoints
│   │   ├── comments.py          # Comment system endpoints
│   │   ├── notifications.py     # Notification endpoints
│   │   ├── reports.py           # Reporting endpoints
│   │   ├── analytics.py         # Analytics endpoints
│   │   ├── audit.py             # Audit endpoints
│   │   └── websocket.py         # WebSocket endpoints
│   ├── core/                     # Core application configuration
│   │   ├── config.py            # Application settings
│   │   ├── security.py          # Security utilities
│   │   ├── dependencies.py      # Dependency injection
│   │   └── auth.py              # Authentication logic
│   ├── models/                   # Database models
│   │   ├── user.py              # User model
│   │   ├── project.py           # Project model
│   │   ├── task.py              # Task model
│   │   ├── time_entry.py        # Time entry model
│   │   ├── file.py              # File model
│   │   ├── comment.py           # Comment model
│   │   └── audit_log.py         # Audit log model
│   ├── schemas/                  # Pydantic schemas
│   │   ├── auth.py              # Authentication schemas
│   │   ├── user.py              # User schemas
│   │   ├── project.py           # Project schemas
│   │   ├── task.py              # Task schemas
│   │   └── common.py            # Common schemas
│   ├── services/                 # Business logic services
│   │   ├── user_service.py      # User business logic
│   │   ├── project_service.py   # Project business logic
│   │   ├── task_service.py      # Task business logic
│   │   ├── file_service.py      # File business logic
│   │   └── notification_service.py # Notification logic
│   ├── db/                       # Database configuration
│   │   ├── database.py          # Database connection
│   │   └── utils.py             # Database utilities
│   ├── middleware/               # Custom middleware
│   │   └── security.py          # Security middleware
│   ├── utils/                    # Utility functions
│   ├── websocket/                # WebSocket management
│   │   └── manager.py           # WebSocket connection manager
│   └── main.py                   # FastAPI application entry point
├── tests/                        # Test suite
│   ├── test_auth.py             # Authentication tests
│   ├── test_projects.py         # Project tests
│   ├── test_tasks.py            # Task tests
│   ├── test_files.py            # File tests
│   └── test_integration.py      # Integration tests
├── migrations/                   # Database migrations
├── scripts/                      # Utility scripts
│   ├── seed_data.py             # Database seeding
│   └── check_and_seed.py        # Data validation
├── uploads/                      # File upload directory
├── pyproject.toml               # Poetry configuration
├── alembic.ini                  # Alembic configuration
├── env.example                  # Environment template
└── README.md                    # This file
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_auth.py

# Run tests with verbose output
poetry run pytest -v
```

### Code Quality

```bash
# Format code with Black
poetry run black app/ tests/

# Sort imports with isort
poetry run isort app/ tests/

# Lint with flake8
poetry run flake8 app/ tests/

# Type checking with mypy
poetry run mypy app/
```

### Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history
```

### Seeding Data

```bash
# Seed with sample data
poetry run python scripts/seed_data.py

# Check and seed if needed
poetry run python scripts/check_and_seed.py

# Simple seeding
poetry run python scripts/simple_seed.py
```

## 📚 API Documentation

### Authentication

All API endpoints require JWT authentication except for login and registration.

```bash
# Login to get access token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# Use token in subsequent requests
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | User authentication |
| `/auth/register` | POST | User registration |
| `/auth/refresh` | POST | Refresh access token |
| `/users/me` | GET | Get current user profile |
| `/projects` | GET/POST | List/Create projects |
| `/projects/{id}` | GET/PUT/DELETE | Project CRUD operations |
| `/tasks` | GET/POST | List/Create tasks |
| `/tasks/{id}` | GET/PUT/DELETE | Task CRUD operations |
| `/time-entries` | GET/POST | Time tracking |
| `/files` | GET/POST | File management |
| `/comments` | GET/POST | Comment system |
| `/reports` | GET | Generate reports |
| `/analytics` | GET | Analytics data |

### WebSocket Endpoints

- `/ws/notifications` - Real-time notifications
- `/ws/project/{project_id}` - Project-specific updates
- `/ws/chat/{project_id}` - Project chat

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt for password security
- **Role-Based Access Control**: Granular permissions system
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation
- **SQL Injection Prevention**: Parameterized queries
- **Rate Limiting**: Request throttling (configurable)
- **Audit Logging**: Complete audit trail for all operations

## 🚀 Deployment

### Production Setup

1. **Environment Configuration**
   ```bash
   # Set production environment variables
   export DEBUG=false
   export DATABASE_URL=postgresql://user:pass@host:port/db
   export SECRET_KEY=your-production-secret-key
   ```

2. **Database Migration**
   ```bash
   poetry run alembic upgrade head
   ```

3. **Start Production Server**
   ```bash
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Docker Deployment (Planned)

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY . .
RUN poetry run alembic upgrade head

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Testing

The project includes comprehensive test coverage:

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Database Tests**: Database operation testing
- **Security Tests**: Authentication and authorization testing
- **Performance Tests**: Load and stress testing

### Test Data

Default test credentials:
- **Email**: admin@example.com
- **Password**: password123

## 📊 Monitoring & Logging

- **Health Check**: `/health` endpoint for monitoring
- **Application Info**: `/info` endpoint for version and status
- **Structured Logging**: JSON formatted logs
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: Response time monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- **Documentation**: Check the API docs at `/docs`
- **Issues**: Create an issue in the repository
- **Email**: Contact the development team

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Complete project management functionality
- User authentication and authorization
- File management system
- Real-time notifications
- Comprehensive API documentation

---

**Built with ❤️ by the Projexiq Development Team** 