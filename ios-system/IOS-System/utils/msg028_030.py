# ⚠️ ПРОБЛЕМА: Загрузка всех результатов в память
results = query.all()  # Может быть миллионы записей

# ✅ РЕШЕНИЕ: Streaming
def stream_results(query):
    for batch in query.yield_per(1000):
        yield batch