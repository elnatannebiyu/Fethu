# Project Setup Instructions

This guide will help you set up and run this Django project from scratch on any machine.

## Prerequisites

- **Python 3.9 or higher** (Python 3.10+ recommended)
- **pip** package manager
- **Git** (if cloning from repository)

### Check Your Python Version

```bash
python3 --version
```

If your Python version is below 3.9, you'll need to install a newer version.

## Setup Steps

### 1. Navigate to Project Directory

```bash
cd /path/to/Fethu/Rental/le_gize
```

Replace `/path/to/Fethu` with the actual path where the project is located.

### 2. Create Virtual Environment

**Important:** Virtual environments are OS-specific. If you're switching from Windows to Mac/Linux (or vice versa), you must create a new virtual environment.

```bash
# Create virtual environment
python3.12 -m venv .venv
```

### 3. Activate Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```cmd
.venv\Scripts\activate
```

You should see `(.venv)` appear in your terminal prompt.

### 4. Upgrade pip

```bash
pip install --upgrade pip
```

### 5. Install Dependencies

```bash
pip install -r ../requirements.txt
```

This will install:
- Django 4.2.7
- python-decouple
- django-crispy-forms
- django-filter
- django-tables2
- whitenoise
- Pillow (for image handling)

### 6. Set Up Database

**Run migrations to create database tables:**

```bash
python manage.py migrate
```

### 7. Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to enter:
- Username
- Email address (optional)
- Password (you'll need to type it twice)

### 8. Start Development Server

```bash
python manage.py runserver
```

The server will start at: **http://127.0.0.1:8000/**

## Accessing the Application

- **Main site:** http://127.0.0.1:8000/
- **Admin panel:** http://127.0.0.1:8000/admin/

Login with the superuser credentials you created in step 7.

## Common Issues & Solutions

### Issue: "No module named django"

**Solution:** Make sure your virtual environment is activated. You should see `(.venv)` in your terminal prompt.

### Issue: "Pillow is not installed"

**Solution:** Install Pillow manually:
```bash
pip install Pillow
```

### Issue: Migration errors

**Solution:** If you encounter migration conflicts, you can reset the database:
```bash
# WARNING: This deletes all data!
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Issue: Virtual environment from different OS

**Solution:** Delete the old virtual environment and create a new one:
```bash
# Delete old environment
rm -rf .venv  # On Mac/Linux
# OR
rmdir /s .venv  # On Windows

# Create new environment
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r ../requirements.txt
```

## Project Structure

```
Fethu/
├── Rental/
│   ├── requirements.txt          # Project dependencies
│   └── le_gize/                  # Main Django project
│       ├── manage.py             # Django management script
│       ├── db.sqlite3            # SQLite database (created after migration)
│       ├── .venv/                # Virtual environment (create this)
│       ├── le_gize/              # Project settings
│       │   ├── settings.py       # Django settings
│       │   ├── urls.py           # URL routing
│       │   └── wsgi.py           # WSGI config
│       ├── accounts/             # User authentication app
│       ├── core/                 # Core functionality
│       ├── orders/               # Order management
│       ├── products/             # Product catalog
│       ├── personnel/            # Personnel management
│       ├── reports/              # Reporting features
│       ├── templates/            # HTML templates
│       ├── static/               # CSS, JS, images
│       └── media/                # User uploads
```

## Development Workflow

### Making Code Changes

The development server auto-reloads when you save files. Just edit your code and refresh the browser.

### Creating New Database Tables

1. Modify models in `models.py`
2. Create migrations:
   ```bash
   python manage.py makemigrations
   ```
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```

### Collecting Static Files (for production)

```bash
python manage.py collectstatic
```

### Running Tests

```bash
python manage.py test
```

## Stopping the Server

Press `CTRL + C` in the terminal where the server is running.

## Deactivating Virtual Environment

When you're done working:

```bash
deactivate
```

## Next Steps After Setup

1. **Explore the admin panel** at http://127.0.0.1:8000/admin/
2. **Create test data** (products, categories, users)
3. **Review the application features** based on user roles
4. **Check the main README** (if available) for application-specific documentation

## Quick Reference Commands

```bash
# Activate virtual environment
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Start server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Django shell (for testing)
python manage.py shell

# Deactivate virtual environment
deactivate
```

## Getting Help

If you encounter issues not covered here:
1. Check that your virtual environment is activated
2. Verify Python version is 3.9+
3. Ensure all dependencies are installed
4. Check Django documentation: https://docs.djangoproject.com/

---

**Last Updated:** April 2026
