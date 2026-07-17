@echo off
cd /d "%~dp0"
set USE_SQLITE=true
python manage.py migrate
python manage.py seed_demo_data --force
pause