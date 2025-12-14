# 1. Активировать virtual environment
poetry shell

# 2. Создать Django проект
django-admin startproject ios_core .

# 3. Создать приложения
python manage.py startapp search
python manage.py startapp analytics

# 4. Обновить settings.py