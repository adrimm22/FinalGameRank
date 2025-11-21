# GameRank - Quick Start Guide

## Prerequisites
- Python 3.8+ installed
- pip installed

## Setup Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations (if needed)
```bash
python manage.py migrate
```

### 3. Create Superuser (optional, for admin access)
```bash
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

The server will start at: **http://127.0.0.1:8000/**

## Available Pages

- **Home**: `http://127.0.0.1:8000/` - Main page with all games
- **Statistics**: `http://127.0.0.1:8000/statistics/` - Site statistics
- **Activity Feed**: `http://127.0.0.1:8000/activity/` - Recent activity
- **User Page**: `http://127.0.0.1:8000/user/` - User profile (requires login)
- **Admin**: `http://127.0.0.1:8000/admin/` - Django admin panel

## Quick Test

1. Start the server: `python manage.py runserver`
2. Open browser: `http://127.0.0.1:8000/statistics/`
3. Check activity: `http://127.0.0.1:8000/activity/`

## Note
If you see "No games" or empty data, you may need to:
- Add games through the admin panel
- Or import games from the API endpoint: `http://127.0.0.1:8000/games/api/`

