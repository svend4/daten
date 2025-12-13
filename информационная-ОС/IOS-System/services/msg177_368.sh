# 1. Bandit (security scan)
bandit -r search/ -ll

# 2. Safety (dependency check)
safety check

# 3. Django security check
python manage.py check --deploy

# Цель: 0 critical issues