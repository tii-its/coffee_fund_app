# Coffee Fund Web App

A team coffee fund management application with consumption tracking and cash movement management.

## Features

- Track product consumption for team members
- Manage cash deposits and payouts with two-person confirmation
- Multi-user concurrent support (kiosk, desktop, mobile)
- Internationalization support (German/English)
- Role-based access (User/Treasurer)
- Audit logging for all actions

## Quick Start

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Start development environment:
   ```bash
   make dev
   ```

3. Run migrations:
   ```bash
   make migrate
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Commands

- `make dev` - Start development environment
- `make test` - Run all tests
- `make lint` - Run linting
- `make migrate` - Run database migrations
- `make clean` - Clean up containers and volumes

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.x, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, i18next
- **Testing**: Pytest, Vitest, Playwright
- **Development**: Docker Compose, Makefile