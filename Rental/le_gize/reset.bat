@echo off
cd /d C:\Users\Administrator\Desktop\Fethu\rental\le_gize

echo Deleting database...
if exist db.sqlite3 del db.sqlite3

echo Deleting migration folders...
if exist accounts\migrations rmdir /s /q accounts\migrations
if exist products\migrations rmdir /s /q products\migrations
if exist orders\migrations rmdir /s /q orders\migrations
if exist personnel\migrations rmdir /s /q personnel\migrations
if exist reports\migrations rmdir /s /q reports\migrations
if exist core\migrations rmdir /s /q core\migrations

echo Creating migrations...
python manage.py makemigrations accounts
python manage.py makemigrations products
python manage.py makemigrations personnel
python manage.py makemigrations orders

echo Applying migrations...
python manage.py migrate

echo Creating superuser...
python manage.py createsuperuser

pause