from functools import lru_cache
import hashlib
import pickle

class SearchCacheManager:
    """Управление кэшем поисковых запросов"""
    
    def __init__(self, cache_path: str, max_size: int = 1000):
        self.cache_path = cache_path
        self.max_size = max_size
        self.cache = {}
        
        os.makedirs(cache_path, exist_ok=True)
        
        # Загрузить кэш
        self.load_cache()
    
    def get_cache_key(self, query: str, filters: Dict) -> str:
        """Создать ключ кэша"""
        
        # Нормализация запроса
        normalized_query = query.lower().strip()
        
        # Создать хэш
        cache_data = {
            'query': normalized_query,
            'filters': sorted(filters.items()) if filters else []
        }
        
        cache_str = str(cache_data)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[List[Dict]]:
        """Получить результаты из кэша"""
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Проверить срок действия (24 часа)
            if (datetime.now() - entry['timestamp']).total_seconds() < 86400:
                entry['hits'] += 1
                return entry['results']
            else:
                # Устаревший кэш
                del self.cache[cache_key]
        
        return None
    
    def set(self, cache_key: str, results: List[Dict]) -> None:
        """Сохранить результаты в кэш"""
        
        # Если кэш полон, удалить наименее используемые
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[cache_key] = {
            'results': results,
            'timestamp': datetime.now(),
            'hits': 0
        }
        
        # Сохранить кэш на диск
        self.save_cache()
    
    def _evict_lru(self) -> None:
        """Удалить наименее используемые записи (LRU)"""
        
        if not self.cache:
            return
        
        # Найти запись с наименьшим количеством обращений
        lru_key = min(self.cache.items(), key=lambda x: x[1]['hits'])[0]
        del self.cache[lru_key]
    
    def save_cache(self) -> None:
        """Сохранить кэш на диск"""
        
        cache_file = f"{self.cache_path}/search_cache.pkl"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def load_cache(self) -> None:
        """Загрузить кэш с диска"""
        
        cache_file = f"{self.cache_path}/search_cache.pkl"
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
            except:
                self.cache = {}
    
    def clear(self) -> None:
        """Очистить кэш"""
        
        self.cache = {}
        self.save_cache()


## 6.9 Autocomplete Engine (Автодополнение)