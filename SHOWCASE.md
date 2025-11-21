# GameRank - Showcase Guide

## Quick Showcase Steps

### Option 1: Using Batch Files (Windows)
1. **First time setup**: Run `setup_and_run.bat`
   - This will install dependencies and run migrations
   
2. **Run server**: Run `RUN_SERVER.bat`
   - Opens server at http://127.0.0.1:8000/

### Option 2: Manual Commands

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Run Migrations
```bash
python manage.py migrate
```

#### Start Server
```bash
python manage.py runserver
```

## Showcase Pages to Visit

### 1. Statistics Page (New!)
**URL**: http://127.0.0.1:8000/statistics/
- Shows site-wide statistics
- Top rated games
- Most active users
- Games by platform/genre

### 2. Activity Feed (New!)
**URL**: http://127.0.0.1:8000/activity/
- Recent comments and follows
- Filter by user or game
- Real-time activity timeline

### 3. Home Page
**URL**: http://127.0.0.1:8000/
- All games sorted by rating
- Follow/unfollow functionality

### 4. Game Detail
**URL**: http://127.0.0.1:8000/game/{game_id}/
- Game information
- Ratings and comments
- User interactions

## Demo Data

If the database is empty, you can:
1. Access admin panel: http://127.0.0.1:8000/admin/
2. Create a superuser: `python manage.py createsuperuser`
3. Add games through admin or import from API

## Features to Showcase

✅ **Statistics Page**
- Total games, users, ratings, comments
- Top rated games with ratings
- Most followed games
- Most active users
- Platform and genre breakdowns

✅ **Activity Feed**
- Recent comments
- Recent follows
- Filtering capabilities
- Timestamps for all activities

✅ **Responsive Design**
- Works on desktop and mobile
- Clean, modern UI
- Easy navigation

## Screenshots Locations

After running the server, you can take screenshots of:
1. Statistics page showing all metrics
2. Activity feed with recent activities
3. Home page with games list
4. Game detail pages

## Troubleshooting

**Issue**: "No module named 'django'"
- Solution: Run `pip install -r requirements.txt`

**Issue**: "No such table" errors
- Solution: Run `python manage.py migrate`

**Issue**: Empty pages
- Solution: Add some test data through admin panel or create test users/games

