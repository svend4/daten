from whoosh.searching import Hit
from typing import List, Dict

class FullTextSearch:
    """Полнотекстовый поиск"""
    
    def __init__(self, indexer: DocumentIndexer):
        self.indexer = indexer
        self.ix = indexer.ix
    
    def search(self, parsed_query: ParsedQuery) -> List[Dict]:
        """Выполнить поиск"""
        
        with self.ix.searcher() as searcher:
            # Построить запрос Whoosh
            whoosh_query = self._build_whoosh_query(parsed_query)
            
            # Применить фильтры
            filter_query = self._build_filter_query(parsed_query.filters)
            
            # Выполнить поиск
            results = searcher.search(
                whoosh_query,
                filter=filter_query,
                limit=parsed_query.limit + parsed_query.offset,
                sortedby=self._get_sort_field(parsed_query.sort_by)
            )
            
            # Преобразовать результаты
            documents = []
            for hit in results[parsed_query.offset:]:
                documents.append(self._hit_to_dict(hit))
            
            return documents
    
    def _build_whoosh_query(self, parsed_query: ParsedQuery):
        """Построить запрос Whoosh из ParsedQuery"""
        
        from whoosh.query import And, Or, Not, Term, Phrase, Wildcard, FuzzyTerm
        
        if not parsed_query.terms:
            # Пустой запрос - вернуть все
            return Term('doc_id', '*')
        
        # Группировка терминов по операторам
        and_terms = []
        or_terms = []
        not_terms = []
        
        for term in parsed_query.terms:
            field = term.field or 'content'
            
            if term.operator == QueryOperator.PHRASE:
                query_obj = Phrase(field, term.text.split())
            elif term.operator == QueryOperator.FUZZY:
                query_obj = FuzzyTerm(field, term.text, maxdist=term.fuzzy_distance)
            elif term.operator == QueryOperator.WILDCARD:
                query_obj = Wildcard(field, term.text)
            else:
                query_obj = Term(field, term.text)
            
            # Применить boost
            if term.boost != 1.0:
                query_obj = query_obj ** term.boost
            
            # Группировка
            if term.operator == QueryOperator.NOT:
                not_terms.append(query_obj)
            elif term.operator == QueryOperator.OR:
                or_terms.append(query_obj)
            else:  # AND
                and_terms.append(query_obj)
        
        # Комбинировать
        final_query = None
        
        if and_terms:
            final_query = And(and_terms)
        
        if or_terms:
            or_query = Or(or_terms)
            if final_query:
                final_query = And([final_query, or_query])
            else:
                final_query = or_query
        
        if not_terms:
            not_query = Not(*not_terms)
            if final_query:
                final_query = And([final_query, not_query])
            else:
                final_query = not_query
        
        return final_query or Term('doc_id', '*')
    
    def _build_filter_query(self, filters: Dict):
        """Построить фильтр-запрос"""
        
        from whoosh.query import And, Term, DateRange
        from datetime import datetime
        
        if not filters:
            return None
        
        filter_queries = []
        
        for field, value in filters.items():
            if field == 'type':
                filter_queries.append(Term('document_type', value))
            
            elif field == 'category':
                filter_queries.append(Term('category', value))
            
            elif field == 'date_from' and 'date_to' in filters:
                date_from = datetime.fromisoformat(value)
                date_to = datetime.fromisoformat(filters['date_to'])
                filter_queries.append(DateRange('created_at', date_from, date_to))
            
            elif field == 'tag':
                filter_queries.append(Term('tags', value))
        
        if filter_queries:
            return And(filter_queries)
        
        return None
    
    def _get_sort_field(self, sort_by: Optional[str]):
        """Получить поле для сортировки"""
        
        if not sort_by:
            return None  # Сортировка по релевантности
        
        # Парсинг sort_by (например, "date_desc")
        parts = sort_by.split('_')
        field = parts[0]
        order = parts[1] if len(parts) > 1 else 'desc'
        
        from whoosh.sorting import FieldFacet
        
        reverse = (order == 'desc')
        
        return FieldFacet(field, reverse=reverse)
    
    def _hit_to_dict(self, hit: Hit) -> Dict:
        """Преобразовать результат поиска в словарь"""
        
        return {
            'doc_id': hit['doc_id'],
            'title': hit['title'],
            'summary': hit.get('summary', ''),
            'document_type': hit['document_type'],
            'category': hit['category'],
            'score': hit.score,
            'rank': hit.rank,
            'file_path': hit['file_path'],
            'created_at': hit['created_at'].isoformat() if hit['created_at'] else None,
            'highlights': hit.highlights('content', top=3)  # Подсветка совпадений
        }


## 6.5 Semantic Search (Семантический поиск)