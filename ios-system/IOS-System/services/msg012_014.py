class FacetedSearch:
    """Фасетный поиск (поиск с фасетами/гранями)"""
    
    def __init__(self, indexer: DocumentIndexer):
        self.indexer = indexer
        self.ix = indexer.ix
    
    def search_with_facets(self, parsed_query: ParsedQuery, 
                          facet_fields: List[str] = None) -> Dict:
        """Поиск с фасетами
        
        Возвращает результаты + агрегированные данные по фасетам
        """
        
        if facet_fields is None:
            facet_fields = ['document_type', 'category', 'author']
        
        with self.ix.searcher() as searcher:
            # Построить основной запрос
            full_text_search = FullTextSearch(self.indexer)
            whoosh_query = full_text_search._build_whoosh_query(parsed_query)
            
            # Выполнить поиск
            results = searcher.search(whoosh_query, limit=None)
            
            # Собрать фасеты
            facets = {}
            for field in facet_fields:
                facets[field] = self._compute_facet(results, field)
            
            # Получить документы для текущей страницы
            documents = []
            start = parsed_query.offset
            end = start + parsed_query.limit
            
            for hit in list(results)[start:end]:
                documents.append(full_text_search._hit_to_dict(hit))
            
            return {
                'documents': documents,
                'facets': facets,
                'total_count': len(results)
            }
    
    def _compute_facet(self, results, field: str) -> Dict[str, int]:
        """Вычислить фасет (агрегация по полю)"""
        
        from collections import Counter
        
        values = []
        for hit in results:
            value = hit.get(field)
            if value:
                values.append(value)
        
        return dict(Counter(values))
    
    def apply_facet_filter(self, parsed_query: ParsedQuery, 
                          facet_field: str, facet_value: str) -> ParsedQuery:
        """Применить фасетный фильтр к запросу"""
        
        # Добавить фильтр
        parsed_query.filters[facet_field] = facet_value
        
        return parsed_query


## 6.7 Search Ranker (Ранжирование результатов)