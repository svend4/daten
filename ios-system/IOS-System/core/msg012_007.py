class DomainSearchEngine:
    """Главный поисковый движок домена"""
    
    def __init__(self, domain: 'Domain', knowledge_graph: Optional[KnowledgeGraph] = None):
        self.domain = domain
        self.kg = knowledge_graph
        
        # Компоненты
        index_path = f"{domain.path}/indexes"
        self.indexer = DocumentIndexer(index_path)
        self.full_text_search = FullTextSearch(self.indexer)
        self.semantic_search = SemanticSearch(domain)
        self.faceted_search = FacetedSearch(self.indexer)
        self.ranker = SearchRanker(knowledge_graph)
        self.cache_manager = SearchCacheManager(f"{domain.path}/cache")
        self.autocomplete = AutocompleteEngine(self.indexer)
        
        # Парсер запросов
        self.query_parser = QueryParser()
    
    def search(self, query: str, search_type: str = 'full_text', **kwargs) -> Dict:
        """Унифицированный поиск
        
        Args:
            query: Поисковый запрос
            search_type: 'full_text', 'semantic', 'faceted', 'hybrid'
            **kwargs: Дополнительные параметры (limit, offset, filters, etc.)
        """
        
        # Парсинг запроса
        parsed_query = self.query_parser.parse(query, **kwargs)
        
        # Проверить кэш
        cache_key = self.cache_manager.get_cache_key(query, parsed_query.filters)
        cached_results = self.cache_manager.get(cache_key)
        
        if cached_results:
            return {
                'results': cached_results,
                'total_count': len(cached_results),
                'cached': True
            }
        
        # Выполнить поиск
        if search_type == 'full_text':
            results = self.full_text_search.search(parsed_query)
        
        elif search_type == 'semantic':
            results = self.semantic_search.search(query, top_n=parsed_query.limit)
        
        elif search_type == 'faceted':
            faceted_results = self.faceted_search.search_with_facets(parsed_query)
            results = faceted_results['documents']
            
            # Сохранить фасеты для возврата
            kwargs['facets'] = faceted_results['facets']
            kwargs['total_count'] = faceted_results['total_count']
        
        elif search_type == 'hybrid':
            # Комбинация полнотекстового и семантического поиска
            ft_results = self.full_text_search.search(parsed_query)
            sem_results = self.semantic_search.search(query, top_n=parsed_query.limit)
            
            # Объединить результаты
            results = self._merge_results(ft_results, sem_results)
        
        else:
            results = self.full_text_search.search(parsed_query)
        
        # Ранжирование
        ranking_strategy = kwargs.get('ranking', 'hybrid')
        results = self.ranker.rank_results(results, query, ranking_strategy)
        
        # Сохранить в кэш
        self.cache_manager.set(cache_key, results)
        
        return {
            'results': results,
            'total_count': kwargs.get('total_count', len(results)),
            'facets': kwargs.get('facets'),
            'cached': False,
            'query': parsed_query.original_query
        }
    
    def _merge_results(self, ft_results: List[Dict], sem_results: List[Dict]) -> List[Dict]:
        """Объединить результаты полнотекстового и семантического поиска"""
        
        # Создать словарь по doc_id
        merged = {}
        
        for result in ft_results:
            doc_id = result['doc_id']
            merged[doc_id] = result
            merged[doc_id]['ft_score'] = result.get('score', 0)
        
        for result in sem_results:
            doc_id = result['doc_id']
            if doc_id in merged:
                # Объединить оценки
                merged[doc_id]['sem_score'] = result.get('similarity_score', 0)
                merged[doc_id]['score'] = (
                    0.6 * merged[doc_id]['ft_score'] +
                    0.4 * result.get('similarity_score', 0)
                )
            else:
                merged[doc_id] = result
                merged[doc_id]['sem_score'] = result.get('similarity_score', 0)
                merged[doc_id]['ft_score'] = 0
                merged[doc_id]['score'] = 0.4 * result.get('similarity_score', 0)
        
        # Сортировка по комбинированной оценке
        results = sorted(merged.values(), key=lambda x: x.get('score', 0), reverse=True)
        
        return results
    
    def suggest(self, prefix: str, max_suggestions: int = 10) -> List[Dict]:
        """Получить автодополнение"""
        return self.autocomplete.get_suggestions(prefix, max_suggestions)
    
    def suggest_queries(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """Получить подсказки для запросов"""
        return self.autocomplete.get_query_suggestions(partial_query, max_suggestions)
    
    def find_similar(self, doc_id: str, top_n: int = 5) -> List[Dict]:
        """Найти похожие документы"""
        return self.semantic_search.find_similar_documents(doc_id, top_n)