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