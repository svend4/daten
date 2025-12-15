# 1. Создать тестовые документы
python manage.py seed_data --documents=1000

# 2. Построить поисковые индексы
python manage.py rebuild_search_index

# 3. Прогреть кэш
python manage.py warm_cache --popular-queries=100

# 4. Проверить
python manage.py shell
>>> from search.models import Document
>>> Document.objects.count()
1000