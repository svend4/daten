Пользователь просит продолжить с Search Engine. Это последний крупный компонент из списка, который я должен детально разработать. После этого нужно будет завершить полную техническую спецификацию Information Operating System.

Search Engine должен включать:
1. Архитектуру поискового движка
2. Индексирование документов
3. Различные типы поиска (полнотекстовый, семантический, фасетный)
4. Ранжирование результатов
5. Фильтрация и сортировка
6. Кэширование поисковых запросов
7. Автодополнение и подсказки
8. Поиск по метаданным
9. Интеграцию с Knowledge Graph

Давайте создадим детальную и профессиональную реализацию.# ЧАСТЬ 6: КОМПОНЕНТ 4 - SEARCH ENGINE

## 6.1 Архитектура Search Engine

```
┌─────────────────────────────────────────────────────────────┐
│                    SEARCH ENGINE                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Query     │  │   Indexer    │  │   Ranker     │      │
│  │   Parser     │→│              │→│              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ↓                  ↓                  ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Full-Text   │  │  Semantic    │  │   Faceted    │      │
│  │   Search     │  │   Search     │  │   Search     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                           │                                  │
│                           ↓                                  │
│                  ┌──────────────┐                           │
│                  │    Cache     │                           │
│                  │   Manager    │                           │
│                  └──────────────┘                           │
│                           │                                  │
│                           ↓                                  │
│        ┌──────────────────┴──────────────────┐              │
│        │                                      │              │
│  ┌──────────────┐                   ┌──────────────┐       │
│  │ Autocomplete │                   │   Filters    │       │
│  │   Engine     │                   │              │       │
│  └──────────────┘                   └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 6.2 Query Parser (Парсер запросов)

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import re
from enum import Enum

class QueryOperator(Enum):
    """Операторы запросов"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    PHRASE = "PHRASE"
    WILDCARD = "WILDCARD"
    FUZZY = "FUZZY"
    PROXIMITY = "PROXIMITY"


@dataclass
class QueryTerm:
    """Термин в поисковом запросе"""
    text: str
    field: Optional[str] = None  # Поле для поиска (title, content, etc.)
    operator: QueryOperator = QueryOperator.AND
    boost: float = 1.0  # Вес термина
    fuzzy_distance: int = 0  # Расстояние для нечеткого поиска
    
    def __repr__(self):
        return f"QueryTerm('{self.text}', field={self.field}, op={self.operator.value})"


@dataclass
class ParsedQuery:
    """Распарсенный поисковый запрос"""
    original_query: str
    terms: List[QueryTerm]
    filters: Dict[str, any] = None
    sort_by: Optional[str] = None
    limit: int = 10
    offset: int = 0
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


class QueryParser:
    """Парсер поисковых запросов"""
    
    def __init__(self):
        # Поддерживаемые операторы
        self.operators = {
            'AND': QueryOperator.AND,
            'OR': QueryOperator.OR,
            'NOT': QueryOperator.NOT,
            '&&': QueryOperator.AND,
            '||': QueryOperator.OR,
            '!': QueryOperator.NOT
        }
        
        # Поддерживаемые поля
        self.supported_fields = [
            'title', 'content', 'author', 'type', 'category',
            'date', 'tags', 'entities', 'all'
        ]
    
    def parse(self, query: str, **kwargs) -> ParsedQuery:
        """Парсинг поискового запроса
        
        Поддерживаемый синтаксис:
        - Простой поиск: "SGB-IX"
        - Поиск по полю: "title:Widerspruch"
        - Булевы операторы: "SGB-IX AND Paragraph"
        - Фразовый поиск: '"Persönliches Budget"'
        - Нечеткий поиск: "Widerspru~2" (расстояние Левенштейна)
        - Подстановочные знаки: "Widersp*"
        - Исключение: "SGB-IX NOT SGB-XII"
        - Диапазоны: "date:[2024-01-01 TO 2024-12-31]"
        - Группировка: "(SGB-IX OR SGB-XII) AND Paragraph"
        """
        
        original_query = query
        
        # Извлечь фильтры
        query, filters = self._extract_filters(query)
        
        # Извлечь сортировку
        query, sort_by = self._extract_sort(query)
        
        # Токенизация
        tokens = self._tokenize(query)
        
        # Парсинг в термины
        terms = self._parse_tokens(tokens)
        
        # Оптимизация запроса
        terms = self._optimize_terms(terms)
        
        return ParsedQuery(
            original_query=original_query,
            terms=terms,
            filters=filters,
            sort_by=sort_by,
            limit=kwargs.get('limit', 10),
            offset=kwargs.get('offset', 0)
        )
    
    def _extract_filters(self, query: str) -> Tuple[str, Dict]:
        """Извлечь фильтры из запроса"""
        
        filters = {}
        
        # Паттерны для фильтров
        patterns = {
            'type': r'type:(\w+)',
            'category': r'category:(\w+)',
            'date_from': r'date_from:(\d{4}-\d{2}-\d{2})',
            'date_to': r'date_to:(\d{4}-\d{2}-\d{2})',
            'author': r'author:"([^"]+)"',
            'tag': r'tag:(\w+)'
        }
        
        for filter_name, pattern in patterns.items():
            match = re.search(pattern, query)
            if match:
                filters[filter_name] = match.group(1)
                query = query.replace(match.group(0), '').strip()
        
        # Диапазон дат
        date_range_match = re.search(r'date:\[(\d{4}-\d{2}-\d{2})\s+TO\s+(\d{4}-\d{2}-\d{2})\]', query)
        if date_range_match:
            filters['date_from'] = date_range_match.group(1)
            filters['date_to'] = date_range_match.group(2)
            query = query.replace(date_range_match.group(0), '').strip()
        
        return query, filters
    
    def _extract_sort(self, query: str) -> Tuple[str, Optional[str]]:
        """Извлечь параметры сортировки"""
        
        sort_match = re.search(r'sort:(\w+)(?::(asc|desc))?', query)
        
        if sort_match:
            field = sort_match.group(1)
            order = sort_match.group(2) or 'desc'
            sort_by = f"{field}_{order}"
            query = query.replace(sort_match.group(0), '').strip()
            return query, sort_by
        
        return query, None
    
    def _tokenize(self, query: str) -> List[str]:
        """Токенизация запроса"""
        
        tokens = []
        
        # Обработка фраз в кавычках
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)
        
        for phrase in phrases:
            tokens.append(f'"{phrase}"')
            query = query.replace(f'"{phrase}"', '', 1)
        
        # Остальные токены
        remaining_tokens = query.split()
        tokens.extend(remaining_tokens)
        
        return [t for t in tokens if t.strip()]
    
    def _parse_tokens(self, tokens: List[str]) -> List[QueryTerm]:
        """Парсинг токенов в термины"""
        
        terms = []
        current_operator = QueryOperator.AND
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Проверка на оператор
            if token.upper() in self.operators:
                current_operator = self.operators[token.upper()]
                i += 1
                continue
            
            # Проверка на поиск по полю (field:value)
            field = None
            if ':' in token and not token.startswith('"'):
                parts = token.split(':', 1)
                if parts[0] in self.supported_fields:
                    field = parts[0]
                    token = parts[1]
            
            # Фразовый поиск
            if token.startswith('"') and token.endswith('"'):
                text = token[1:-1]
                terms.append(QueryTerm(
                    text=text,
                    field=field,
                    operator=QueryOperator.PHRASE
                ))
            
            # Нечеткий поиск (fuzzy)
            elif '~' in token:
                parts = token.split('~')
                text = parts[0]
                distance = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 2
                terms.append(QueryTerm(
                    text=text,
                    field=field,
                    operator=QueryOperator.FUZZY,
                    fuzzy_distance=distance
                ))
            
            # Подстановочные знаки (wildcard)
            elif '*' in token or '?' in token:
                terms.append(QueryTerm(
                    text=token,
                    field=field,
                    operator=QueryOperator.WILDCARD
                ))
            
            # Обычный термин
            else:
                terms.append(QueryTerm(
                    text=token,
                    field=field,
                    operator=current_operator
                ))
            
            i += 1
        
        return terms
    
    def _optimize_terms(self, terms: List[QueryTerm]) -> List[QueryTerm]:
        """Оптимизация терминов запроса"""
        
        # Удаление стоп-слов
        stopwords = {'der', 'die', 'das', 'und', 'oder', 'the', 'a', 'an', 'and', 'or'}
        
        optimized = []
        for term in terms:
            if term.text.lower() not in stopwords:
                optimized.append(term)
        
        # Если все термины были удалены, вернуть оригинальные
        if not optimized:
            return terms
        
        return optimized


## 6.3 Indexer (Индексатор)

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC, KEYWORD
from whoosh.analysis import StemmingAnalyzer, LanguageAnalyzer
from whoosh.qparser import MultifieldParser, QueryParser as WhooshQueryParser
import whoosh.qparser as qparser

class DocumentIndexer:
    """Индексатор документов"""
    
    def __init__(self, index_path: str, language: str = 'de'):
        self.index_path = index_path
        self.language = language
        
        # Создать схему индекса
        self.schema = self._create_schema()
        
        # Создать или открыть индекс
        if not os.path.exists(index_path):
            os.makedirs(index_path)
            self.ix = index.create_in(index_path, self.schema)
        else:
            self.ix = index.open_dir(index_path)
    
    def _create_schema(self) -> Schema:
        """Создать схему индекса"""
        
        # Анализатор для немецкого языка
        german_analyzer = LanguageAnalyzer('de')
        
        return Schema(
            # Идентификаторы
            doc_id=ID(stored=True, unique=True),
            
            # Текстовые поля
            title=TEXT(stored=True, analyzer=german_analyzer, field_boost=2.0),
            content=TEXT(stored=True, analyzer=german_analyzer),
            summary=TEXT(stored=True, analyzer=german_analyzer),
            
            # Метаданные
            document_type=ID(stored=True),
            category=ID(stored=True),
            subcategory=ID(stored=True),
            author=TEXT(stored=True),
            
            # Сущности (как ключевые слова)
            entities=KEYWORD(stored=True, commas=True, scorable=True),
            tags=KEYWORD(stored=True, commas=True, scorable=True),
            
            # Даты
            created_at=DATETIME(stored=True),
            modified_at=DATETIME(stored=True),
            
            # Числовые поля
            confidence=NUMERIC(stored=True, numtype=float),
            importance_score=NUMERIC(stored=True, numtype=float),
            
            # Путь к файлу
            file_path=ID(stored=True)
        )
    
    def index_document(self, document: 'Document', metadata: dict) -> None:
        """Индексировать документ"""
        
        writer = self.ix.writer()
        
        try:
            # Извлечь сущности для индексации
            entities_str = ','.join([
                e.name for e in metadata.get('entities', [])
            ]) if 'entities' in metadata else ''
            
            # Извлечь теги
            tags_str = ','.join(metadata.get('tags', [])) if 'tags' in metadata else ''
            
            # Добавить документ в индекс
            writer.update_document(
                doc_id=document.id,
                title=document.title or '',
                content=document.get_text(),
                summary=metadata.get('summary', ''),
                document_type=metadata.get('document_type', 'Unknown'),
                category=metadata.get('category', 'Uncategorized'),
                subcategory=metadata.get('subcategory', ''),
                author=document.author if hasattr(document, 'author') else '',
                entities=entities_str,
                tags=tags_str,
                created_at=document.creation_date,
                modified_at=document.modification_date,
                confidence=metadata.get('confidence', 0.0),
                importance_score=metadata.get('importance_score', 0.0),
                file_path=document.file_path
            )
            
            writer.commit()
            
        except Exception as e:
            writer.cancel()
            raise e
    
    def update_document(self, doc_id: str, **fields) -> None:
        """Обновить документ в индексе"""
        
        writer = self.ix.writer()
        
        try:
            writer.update_document(doc_id=doc_id, **fields)
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise e
    
    def delete_document(self, doc_id: str) -> None:
        """Удалить документ из индекса"""
        
        writer = self.ix.writer()
        
        try:
            writer.delete_by_term('doc_id', doc_id)
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise e
    
    def optimize_index(self) -> None:
        """Оптимизировать индекс"""
        
        writer = self.ix.writer()
        writer.commit(optimize=True)


## 6.4 Full-Text Search (Полнотекстовый поиск)

```python
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

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticSearch:
    """Семантический поиск (поиск по смыслу)"""
    
    def __init__(self, domain: 'Domain'):
        self.domain = domain
        self.vectorizer = None
        self.document_vectors = None
        self.document_ids = []
        
        # Обучить модель
        self._train()
    
    def _train(self) -> None:
        """Обучить модель на документах домена"""
        
        # Собрать все документы
        documents = self.domain.get_all_documents()
        
        if not documents:
            return
        
        # Извлечь тексты
        texts = []
        self.document_ids = []
        
        for doc in documents:
            texts.append(doc.get_text())
            self.document_ids.append(doc.id)
        
        # Векторизация (TF-IDF)
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8
        )
        
        self.document_vectors = self.vectorizer.fit_transform(texts)
    
    def search(self, query: str, top_n: int = 10) -> List[Dict]:
        """Семантический поиск"""
        
        if not self.vectorizer or not self.document_vectors:
            return []
        
        # Векторизация запроса
        query_vector = self.vectorizer.transform([query])
        
        # Вычислить косинусное сходство
        similarities = cosine_similarity(query_vector, self.document_vectors)[0]
        
        # Получить топ-N
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Только релевантные
                results.append({
                    'doc_id': self.document_ids[idx],
                    'similarity_score': float(similarities[idx]),
                    'rank': len(results) + 1
                })
        
        return results
    
    def find_similar_documents(self, doc_id: str, top_n: int = 5) -> List[Dict]:
        """Найти похожие документы"""
        
        if doc_id not in self.document_ids:
            return []
        
        # Индекс документа
        doc_idx = self.document_ids.index(doc_id)
        
        # Вектор документа
        doc_vector = self.document_vectors[doc_idx]
        
        # Вычислить сходство со всеми документами
        similarities = cosine_similarity(doc_vector, self.document_vectors)[0]
        
        # Исключить сам документ
        similarities[doc_idx] = -1
        
        # Получить топ-N
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append({
                    'doc_id': self.document_ids[idx],
                    'similarity_score': float(similarities[idx])
                })
        
        return results


## 6.6 Faceted Search (Фасетный поиск)

```python
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

```python
class SearchRanker:
    """Ранжирование результатов поиска"""
    
    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None):
        self.kg = knowledge_graph
    
    def rank_results(self, results: List[Dict], query: str, 
                    ranking_strategy: str = 'hybrid') -> List[Dict]:
        """Ранжировать результаты
        
        Стратегии:
        - 'relevance': По текстовой релевантности (BM25)
        - 'importance': По важности сущностей
        - 'recency': По свежести
        - 'hybrid': Комбинация всех факторов
        """
        
        if ranking_strategy == 'relevance':
            # Уже отсортировано по релевантности (BM25)
            return results
        
        elif ranking_strategy == 'importance':
            return self._rank_by_importance(results)
        
        elif ranking_strategy == 'recency':
            return self._rank_by_recency(results)
        
        elif ranking_strategy == 'hybrid':
            return self._rank_hybrid(results, query)
        
        else:
            return results
    
    def _rank_by_importance(self, results: List[Dict]) -> List[Dict]:
        """Ранжирование по важности (на основе графа знаний)"""
        
        if not self.kg:
            return results
        
        from .graph_analytics import GraphAnalytics
        analytics = GraphAnalytics(self.kg)
        
        # Добавить оценку важности
        for result in results:
            doc_id = result['doc_id']
            
            # Найти сущности из документа
            doc_entities = self._get_document_entities(doc_id)
            
            # Вычислить среднюю важность сущностей
            importance_scores = []
            for entity in doc_entities:
                score = analytics.get_entity_importance_score(entity.id)
                importance_scores.append(score)
            
            avg_importance = np.mean(importance_scores) if importance_scores else 0.0
            result['importance_score'] = avg_importance
        
        # Сортировка по важности
        return sorted(results, key=lambda x: x.get('importance_score', 0), reverse=True)
    
    def _rank_by_recency(self, results: List[Dict]) -> List[Dict]:
        """Ранжирование по свежести"""
        
        for result in results:
            created_at = result.get('created_at')
            if created_at:
                # Вычислить свежесть (дни назад)
                created_date = datetime.fromisoformat(created_at)
                days_ago = (datetime.now() - created_date).days
                
                # Оценка свежести (экспоненциальный спад)
                recency_score = np.exp(-days_ago / 365.0)
                result['recency_score'] = recency_score
            else:
                result['recency_score'] = 0.0
        
        # Сортировка по свежести
        return sorted(results, key=lambda x: x.get('recency_score', 0), reverse=True)
    
    def _rank_hybrid(self, results: List[Dict], query: str) -> List[Dict]:
        """Гибридное ранжирование"""
        
        # Нормализация оценок
        max_score = max(r.get('score', 0) for r in results) if results else 1.0
        
        for result in results:
            # Релевантность (BM25)
            relevance_score = result.get('score', 0) / max_score if max_score > 0 else 0
            
            # Важность
            importance_score = result.get('importance_score', 0)
            
            # Свежесть
            recency_score = result.get('recency_score', 0)
            
            # Комбинированная оценка (взвешенная сумма)
            combined_score = (
                0.5 * relevance_score +
                0.3 * importance_score +
                0.2 * recency_score
            )
            
            result['combined_score'] = combined_score
        
        # Сортировка по комбинированной оценке
        return sorted(results, key=lambda x: x.get('combined_score', 0), reverse=True)
    
    def _get_document_entities(self, doc_id: str) -> List['Entity']:
        """Получить сущности из документа"""
        
        if not self.kg:
            return []
        
        # Найти все сущности, связанные с документом
        entities = []
        for entity in self.kg.entity_index.values():
            if entity.source_document == doc_id:
                entities.append(entity)
        
        return entities


## 6.8 Cache Manager (Управление кэшем)

```python
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

```python
from collections import Counter

class AutocompleteEngine:
    """Движок автодополнения"""
    
    def __init__(self, indexer: DocumentIndexer):
        self.indexer = indexer
        self.ix = indexer.ix
        self.suggestions_cache = {}
        
        # Построить словарь терминов
        self._build_term_dictionary()
    
    def _build_term_dictionary(self) -> None:
        """Построить словарь всех терминов"""
        
        with self.ix.searcher() as searcher:
            # Собрать все термины из индекса
            self.term_freq = Counter()
            
            for fieldname in ['title', 'content', 'entities', 'tags']:
                reader = searcher.reader()
                
                for term in reader.lexicon(fieldname):
                    # Декодировать термин
                    term_text = term.decode('utf-8') if isinstance(term, bytes) else term
                    
                    # Частота термина
                    freq = reader.doc_frequency(fieldname, term)
                    self.term_freq[term_text] += freq
    
    def get_suggestions(self, prefix: str, max_suggestions: int = 10) -> List[Dict]:
        """Получить подсказки для префикса"""
        
        prefix = prefix.lower().strip()
        
        if not prefix:
            return []
        
        # Проверить кэш
        cache_key = f"{prefix}_{max_suggestions}"
        if cache_key in self.suggestions_cache:
            return self.suggestions_cache[cache_key]
        
        # Найти совпадения
        matches = []
        
        for term, freq in self.term_freq.items():
            if term.lower().startswith(prefix):
                matches.append({
                    'term': term,
                    'frequency': freq,
                    'score': self._calculate_suggestion_score(term, prefix, freq)
                })
        
        # Сортировка по оценке
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        suggestions = matches[:max_suggestions]
        
        # Сохранить в кэш
        self.suggestions_cache[cache_key] = suggestions
        
        return suggestions
    
    def _calculate_suggestion_score(self, term: str, prefix: str, frequency: int) -> float:
        """Вычислить оценку подсказки"""
        
        # Факторы:
        # 1. Частота термина
        # 2. Длина совпадения с префиксом
        # 3. Позиция в слове
        
        freq_score = np.log1p(frequency)  # Логарифм частоты
        
        # Чем больше совпадение, тем выше оценка
        match_length = len(prefix)
        length_score = match_length / len(term)
        
        # Совпадение с начала слова - лучше
        position_score = 1.0 if term.lower().startswith(prefix) else 0.5
        
        return freq_score * length_score * position_score
    
    def get_query_suggestions(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """Получить подсказки для всего запроса"""
        
        # Парсинг частичного запроса
        tokens = partial_query.split()
        
        if not tokens:
            return []
        
        # Подсказки для последнего токена
        last_token = tokens[-1]
        suggestions = self.get_suggestions(last_token, max_suggestions)
        
        # Составить полные запросы
        query_suggestions = []
        for suggestion in suggestions:
            full_query = ' '.join(tokens[:-1] + [suggestion['term']])
            query_suggestions.append(full_query.strip())
        
        return query_suggestions


## 6.10 Main Search Engine (Главный поисковый движок)

```python
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
```

---

Это завершает разработку всех четырех основных компонентов Information Operating System:
1. ✅ Automatic Classifier
2. ✅ Knowledge Graph Engine  
3. ✅ Context Manager
4. ✅ Search Engine

Хотите, чтобы я теперь создал:
1. **Полный пример использования** всей системы IOS?
2. **API интерфейсы** для взаимодействия с системой?
3. **Deployment guide** для развертывания?
4. **Примеры интеграции** с вашими существующими проектами (Android приложения, Knowledge OS)?