Пользователь хочет, чтобы я продолжил с остальными компонентами. Я должен продолжить с той же детальностью и структурой, охватывая:

1. Knowledge Graph Engine - для связывания законов и создания графа знаний
2. Context Manager - для переключения между проектами
3. Search Engine - с семантическим поиском

Продолжу в том же подробном стиле с кодом, примерами и детальными объяснениями.# ЧАСТЬ 3: КОМПОНЕНТ 2 - KNOWLEDGE GRAPH ENGINE

## 3.1 Архитектура Knowledge Graph

```
┌─────────────────────────────────────────────────────────────┐
│                 KNOWLEDGE GRAPH ENGINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Entity     │  │  Relation    │  │    Graph     │      │
│  │  Extractor   │→│  Extractor   │→│   Builder    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ↓                  ↓                  ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Entity     │  │  Relation    │  │    Graph     │      │
│  │   Storage    │  │   Storage    │  │   Storage    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                           │                                  │
│                           ↓                                  │
│                  ┌──────────────┐                           │
│                  │    Query     │                           │
│                  │    Engine    │                           │
│                  └──────────────┘                           │
│                           │                                  │
│                           ↓                                  │
│        ┌──────────────────┴──────────────────┐              │
│        │                                      │              │
│  ┌──────────────┐                   ┌──────────────┐       │
│  │   Graph      │                   │ Visualization│       │
│  │  Analytics   │                   │    Engine    │       │
│  └──────────────┘                   └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 3.2 Entity Extractor (Извлечение сущностей)

```python
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
from datetime import datetime

@dataclass
class Entity:
    """Сущность в графе знаний"""
    id: str                      # Уникальный ID
    type: str                    # Тип (Gesetz, Paragraph, Behörde, etc.)
    name: str                    # Название
    properties: Dict             # Дополнительные свойства
    source_document: str         # Документ-источник
    confidence: float            # Уверенность в извлечении
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'properties': self.properties,
            'source_document': self.source_document,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class EntityExtractor:
    """Извлечение сущностей из документов"""
    
    def __init__(self, entity_types_config: dict):
        self.entity_types = entity_types_config
        self.extractors = self._build_extractors()
        
    def _build_extractors(self) -> Dict[str, 'SpecificExtractor']:
        """Создать специализированные экстракторы для каждого типа сущности"""
        
        return {
            'Gesetz': GesetzExtractor(),
            'Paragraph': ParagraphExtractor(),
            'Behörde': BehördeExtractor(),
            'Person': PersonExtractor(),
            'Datum': DatumExtractor(),
            'Geldbetrag': GeldbetragExtractor(),
            'Leistung': LeistungExtractor(),
            'Verfahren': VerfahrenExtractor(),
            'Aktenzeichen': AktenzeichenExtractor()
        }
    
    def extract(self, document: 'Document') -> List[Entity]:
        """Извлечь все сущности из документа"""
        
        text = document.get_text()
        all_entities = []
        
        for entity_type, extractor in self.extractors.items():
            entities = extractor.extract(text, document.id)
            all_entities.extend(entities)
        
        # Удалить дубликаты
        unique_entities = self._deduplicate_entities(all_entities)
        
        # Связать упоминания одной сущности
        merged_entities = self._merge_entity_mentions(unique_entities)
        
        return merged_entities
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Удалить дубликаты сущностей"""
        
        seen = {}
        unique = []
        
        for entity in entities:
            key = (entity.type, entity.name.lower())
            
            if key not in seen:
                seen[key] = entity
                unique.append(entity)
            else:
                # Обновить уверенность (максимальная)
                if entity.confidence > seen[key].confidence:
                    seen[key].confidence = entity.confidence
        
        return unique
    
    def _merge_entity_mentions(self, entities: List[Entity]) -> List[Entity]:
        """Объединить упоминания одной сущности"""
        
        # Группировка по (тип, нормализованное имя)
        groups = {}
        
        for entity in entities:
            normalized_name = self._normalize_entity_name(entity.name, entity.type)
            key = (entity.type, normalized_name)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(entity)
        
        # Объединение
        merged = []
        for (entity_type, normalized_name), group in groups.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Создать объединенную сущность
                merged_entity = self._merge_group(group)
                merged.append(merged_entity)
        
        return merged
    
    def _normalize_entity_name(self, name: str, entity_type: str) -> str:
        """Нормализация имени сущности"""
        
        name = name.strip().lower()
        
        if entity_type == 'Gesetz':
            # SGB-IX, SGB IX, SGBIX -> sgb-ix
            name = re.sub(r'sgb\s*-?\s*([ivx]+)', r'sgb-\1', name)
        
        elif entity_type == 'Paragraph':
            # §29, § 29, Par. 29 -> §29
            name = re.sub(r'§\s*', '§', name)
            name = re.sub(r'par\.?\s*', '§', name)
        
        return name
    
    def _merge_group(self, entities: List[Entity]) -> Entity:
        """Объединить группу сущностей в одну"""
        
        # Взять сущность с наибольшей уверенностью как базу
        base = max(entities, key=lambda e: e.confidence)
        
        # Объединить свойства
        merged_properties = {}
        for entity in entities:
            merged_properties.update(entity.properties)
        
        # Список документов-источников
        source_documents = list(set(e.source_document for e in entities))
        
        return Entity(
            id=base.id,
            type=base.type,
            name=base.name,
            properties={
                **merged_properties,
                'source_documents': source_documents,
                'mention_count': len(entities)
            },
            source_document=base.source_document,
            confidence=max(e.confidence for e in entities),
            created_at=min(e.created_at for e in entities),
            updated_at=datetime.now()
        )


class GesetzExtractor:
    """Извлечение законов (SGB-IX, BGB, etc.)"""
    
    PATTERNS = [
        r'SGB[- ]?([IVX]+)',                    # SGB-IX, SGB IX
        r'Sozialgesetzbuch[- ]([IVX]+)',        # Sozialgesetzbuch IX
        r'(BGB)',                                # BGB
        r'(GG)',                                 # Grundgesetz
        r'(ZPO)',                                # Zivilprozessordnung
        r'(SGG)',                                # Sozialgerichtsgesetz
    ]
    
    def extract(self, text: str, document_id: str) -> List[Entity]:
        """Извлечь законы из текста"""
        
        entities = []
        
        for pattern in self.PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                law_name = match.group(0)
                law_code = match.group(1) if match.lastindex else match.group(0)
                
                entity = Entity(
                    id=f"gesetz_{self._normalize_law_name(law_name)}",
                    type='Gesetz',
                    name=law_name,
                    properties={
                        'code': law_code,
                        'full_name': self._get_full_name(law_code),
                        'url': self._get_law_url(law_code)
                    },
                    source_document=document_id,
                    confidence=0.95,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                entities.append(entity)
        
        return entities
    
    def _normalize_law_name(self, name: str) -> str:
        """Нормализация названия закона"""
        return re.sub(r'\s+', '-', name.upper())
    
    def _get_full_name(self, code: str) -> str:
        """Полное название закона"""
        names = {
            'IX': 'Sozialgesetzbuch Neuntes Buch - Rehabilitation und Teilhabe',
            'XI': 'Sozialgesetzbuch Elftes Buch - Soziale Pflegeversicherung',
            'XII': 'Sozialgesetzbuch Zwölftes Buch - Sozialhilfe',
            'BGB': 'Bürgerliches Gesetzbuch',
            'GG': 'Grundgesetz',
            'ZPO': 'Zivilprozessordnung',
            'SGG': 'Sozialgerichtsgesetz'
        }
        return names.get(code.upper(), code)
    
    def _get_law_url(self, code: str) -> str:
        """URL закона"""
        return f"https://www.gesetze-im-internet.de/sgb_{code.lower()}/index.html"


class ParagraphExtractor:
    """Извлечение параграфов"""
    
    PATTERNS = [
        r'§\s*(\d+[a-z]?)',                     # §29, §29a
        r'Paragraph\s+(\d+[a-z]?)',             # Paragraph 29
        r'Par\.\s*(\d+[a-z]?)',                 # Par. 29
    ]
    
    def extract(self, text: str, document_id: str) -> List[Entity]:
        """Извлечь параграфы из текста"""
        
        entities = []
        
        for pattern in self.PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                paragraph_number = match.group(1)
                
                # Попытаться определить к какому закону относится
                law = self._find_related_law(text, match.start())
                
                entity = Entity(
                    id=f"paragraph_{law}_{paragraph_number}",
                    type='Paragraph',
                    name=f"§{paragraph_number}",
                    properties={
                        'number': paragraph_number,
                        'law': law,
                        'title': self._extract_paragraph_title(text, match.end()),
                        'context': self._extract_context(text, match.start(), match.end())
                    },
                    source_document=document_id,
                    confidence=0.9,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                entities.append(entity)
        
        return entities
    
    def _find_related_law(self, text: str, position: int) -> str:
        """Найти закон, к которому относится параграф"""
        
        # Поиск в окрестности упоминания параграфа
        window_start = max(0, position - 200)
        window_end = min(len(text), position + 50)
        window = text[window_start:window_end]
        
        # Поиск упоминания закона
        law_match = re.search(r'SGB[- ]?([IVX]+)', window, re.IGNORECASE)
        
        if law_match:
            return f"SGB-{law_match.group(1)}"
        
        return "Unknown"
    
    def _extract_paragraph_title(self, text: str, position: int) -> Optional[str]:
        """Извлечь название параграфа"""
        
        # Ищем заголовок после номера параграфа
        window_end = min(len(text), position + 200)
        window = text[position:window_end]
        
        # Заголовок обычно идет до первой точки или новой строки
        title_match = re.search(r'([^\n\.]+)', window)
        
        if title_match:
            return title_match.group(1).strip()
        
        return None
    
    def _extract_context(self, text: str, start: int, end: int) -> str:
        """Извлечь контекст вокруг параграфа"""
        
        window_start = max(0, start - 100)
        window_end = min(len(text), end + 100)
        
        return text[window_start:window_end].strip()


class BehördeExtractor:
    """Извлечение органов власти"""
    
    KNOWN_AUTHORITIES = [
        'Sozialamt',
        'Landkreis',
        'Bezirk',
        'Sozialgericht',
        'Landessozialgericht',
        'Bundessozialgericht',
        'Integrationsamt',
        'Versorgungsamt',
        'Bundesagentur für Arbeit',
        'Jobcenter',
        'Krankenkasse',
        'Pflegekasse',
        'Rentenversicherung'
    ]
    
    PATTERNS = [
        r'(Sozialamt)\s+([A-ZÄÖÜ][a-zäöü]+)',          # Sozialamt München
        r'(Landkreis)\s+([A-ZÄÖÜ][a-zäöü]+)',          # Landkreis München
        r'(Bezirk)\s+([A-ZÄÖÜ][a-zäöü]+)',             # Bezirk Oberbayern
    ]
    
    def extract(self, text: str, document_id: str) -> List[Entity]:
        """Извлечь органы власти из текста"""
        
        entities = []
        
        # 1. Поиск известных органов
        for authority in self.KNOWN_AUTHORITIES:
            if authority.lower() in text.lower():
                entity = Entity(
                    id=f"behörde_{self._normalize_name(authority)}",
                    type='Behörde',
                    name=authority,
                    properties={
                        'type': self._classify_authority_type(authority)
                    },
                    source_document=document_id,
                    confidence=0.85,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entities.append(entity)
        
        # 2. Поиск по паттернам (с указанием места)
        for pattern in self.PATTERNS:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                authority_type = match.group(1)
                location = match.group(2)
                full_name = f"{authority_type} {location}"
                
                entity = Entity(
                    id=f"behörde_{self._normalize_name(full_name)}",
                    type='Behörde',
                    name=full_name,
                    properties={
                        'type': authority_type,
                        'location': location
                    },
                    source_document=document_id,
                    confidence=0.9,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entities.append(entity)
        
        return entities
    
    def _normalize_name(self, name: str) -> str:
        """Нормализация названия органа"""
        return name.lower().replace(' ', '_').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    
    def _classify_authority_type(self, authority: str) -> str:
        """Классификация типа органа"""
        
        if 'gericht' in authority.lower():
            return 'Gericht'
        elif 'amt' in authority.lower():
            return 'Amt'
        elif 'kasse' in authority.lower():
            return 'Kasse'
        elif 'agentur' in authority.lower():
            return 'Agentur'
        else:
            return 'Sonstige'


class LeistungExtractor:
    """Извлечение социальных услуг"""
    
    KNOWN_SERVICES = [
        'Persönliches Budget',
        'Eingliederungshilfe',
        'Grundsicherung',
        'Hilfe zur Pflege',
        'Assistenzleistungen',
        'Teilhabeleistungen',
        'Medizinische Rehabilitation',
        'Teilhabe am Arbeitsleben',
        'Teilhabe an Bildung',
        'Soziale Teilhabe',
        'Blindenhilfe',
        'Pflegegeld',
        'Verhinderungspflege'
    ]
    
    def extract(self, text: str, document_id: str) -> List[Entity]:
        """Извлечь услуги из текста"""
        
        entities = []
        
        for service in self.KNOWN_SERVICES:
            if service.lower() in text.lower():
                entity = Entity(
                    id=f"leistung_{self._normalize_name(service)}",
                    type='Leistung',
                    name=service,
                    properties={
                        'category': self._classify_service(service)
                    },
                    source_document=document_id,
                    confidence=0.85,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entities.append(entity)
        
        return entities
    
    def _normalize_name(self, name: str) -> str:
        """Нормализация названия услуги"""
        return name.lower().replace(' ', '_').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    
    def _classify_service(self, service: str) -> str:
        """Классификация типа услуги"""
        
        if 'rehabilitation' in service.lower():
            return 'Rehabilitation'
        elif 'teilhabe' in service.lower():
            return 'Teilhabe'
        elif 'pflege' in service.lower():
            return 'Pflege'
        elif 'budget' in service.lower():
            return 'Budget'
        else:
            return 'Sonstige'


class DatumExtractor:
    """Извлечение дат"""
    
    PATTERNS = [
        r'(\d{1,2}\.\d{1,2}\.\d{4})',           # 01.01.2025
        r'(\d{1,2}\.\s*\w+\s+\d{4})',           # 1. Januar 2025
        r'((?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4})'  # Januar 2025
    ]
    
    def extract(self, text: str, document_id: str) -> List[Entity]:
        """Извлечь даты из текста"""
        
        entities = []
        
        for pattern in self.PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                date_str = match.group(1)
                
                # Попытаться распарсить дату
                parsed_date = self._parse_date(date_str)
                
                # Определить тип события
                event_type = self._classify_date_event(text, match.start())
                
                entity = Entity(
                    id=f"datum_{date_str.replace('.', '_').replace(' ', '_')}_{document_id}",
                    type='Datum',
                    name=date_str,
                    properties={
                        'parsed_date': parsed_date.isoformat() if parsed_date else None,
                        'event_type': event_type,
                        'context': self._extract_date_context(text, match.start())
                    },
                    source_document=document_id,
                    confidence=0.8,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entities.append(entity)
        
        return entities
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Распарсить дату"""
        
        from dateutil import parser
        
        try:
            return parser.parse(date_str, dayfirst=True)
        except:
            return None
    
    def _classify_date_event(self, text: str, position: int) -> str:
        """Классифицировать событие по дате"""
        
        window_start = max(0, position - 50)
        window_end = min(len(text), position + 50)
        window = text[window_start:window_end].lower()
        
        if 'frist' in window or 'bis zum' in window:
            return 'Frist'
        elif 'bescheid' in window:
            return 'Bescheiddatum'
        elif 'antrag' in window:
            return 'Antragsdatum'
        elif 'widerspruch' in window:
            return 'Widerspruchsdatum'
        else:
            return 'Sonstiges Datum'
    
    def _extract_date_context(self, text: str, position: int) -> str:
        """Извлечь контекст даты"""
        
        window_start = max(0, position - 100)
        window_end = min(len(text), position + 100)
        
        return text[window_start:window_end].strip()


class GeldbetragExtractor:
    """Извлечение денежных сумм"""
    
    PATTERNS = [
        r'(\d+(?:[.,]\d+)?)\s*(?:€|EUR|Euro)',         # 1234.56 €
        r'€\s*(\d+(?:[.,]\d+)?)',                       # € 1234.56
    ]
    
    def extract(self, text: str, document_id: str) -> List[Entity]:
        """Извлечь денежные суммы из текста"""
        
        entities = []
        
        for pattern in self.PATTERNS:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                amount_str = match.group(1)
                
                # Нормализация (запятая -> точка)
                amount_normalized = amount_str.replace(',', '.')
                
                try:
                    amount = float(amount_normalized)
                except:
                    continue
                
                # Определить назначение суммы
                purpose = self._classify_amount_purpose(text, match.start())
                
                entity = Entity(
                    id=f"geld_{amount}_{document_id}_{match.start()}",
                    type='Geldbetrag',
                    name=f"{amount_str} €",
                    properties={
                        'amount': amount,
                        'currency': 'EUR',
                        'purpose': purpose,
                        'context': self._extract_amount_context(text, match.start())
                    },
                    source_document=document_id,
                    confidence=0.85,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entities.append(entity)
        
        return entities
    
    def _classify_amount_purpose(self, text: str, position: int) -> str:
        """Классифицировать назначение суммы"""
        
        window_start = max(0, position - 100)
        window_end = min(len(text), position + 100)
        window = text[window_start:window_end].lower()
        
        if 'budget' in window:
            return 'Persönliches Budget'
        elif 'kosten' in window:
            return 'Kosten'
        elif 'erstattung' in window:
            return 'Erstattung'
        elif 'monat' in window:
            return 'Monatlicher Betrag'
        else:
            return 'Sonstiger Betrag'
    
    def _extract_amount_context(self, text: str, position: int) -> str:
        """Извлечь контекст суммы"""
        
        window_start = max(0, position - 100)
        window_end = min(len(text), position + 100)
        
        return text[window_start:window_end].strip()


class AktenzeichenExtractor:
    """Извлечение номеров дел"""
    
    PATTERNS = [
        r'([A-Z]{1,2}\s*\d+/\d+)',                      # S 12/2024
        r'Az\.?\s*:?\s*([A-Z]{1,2}\s*\d+/\d+)',        # Az.: S 12/2024
        r'Aktenzeichen\s*:?\s*([A-Z]{1,2}\s*\d+/\d+)', # Aktenzeichen: S 12/2024
    ]
    
    def extract(self, text: str, document_id: str) -> List[Entity]:
        """Извлечь номера дел из текста"""
        
        entities = []
        
        for pattern in self.PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                aktenzeichen = match.group(1)
                
                # Определить тип суда
                court_type = self._classify_court_type(aktenzeichen)
                
                entity = Entity(
                    id=f"aktenzeichen_{aktenzeichen.replace('/', '_').replace(' ', '')}",
                    type='Aktenzeichen',
                    name=aktenzeichen,
                    properties={
                        'court_type': court_type,
                        'normalized': self._normalize_aktenzeichen(aktenzeichen)
                    },
                    source_document=document_id,
                    confidence=0.9,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entities.append(entity)
        
        return entities
    
    def _classify_court_type(self, aktenzeichen: str) -> str:
        """Определить тип суда по номеру дела"""
        
        prefix = aktenzeichen.split()[0]
        
        court_types = {
            'S': 'Sozialgericht',
            'L': 'Landessozialgericht',
            'B': 'Bundessozialgericht',
            'VG': 'Verwaltungsgericht',
            'OVG': 'Oberverwaltungsgericht'
        }
        
        return court_types.get(prefix, 'Unbekannt')
    
    def _normalize_aktenzeichen(self, aktenzeichen: str) -> str:
        """Нормализация номера дела"""
        return re.sub(r'\s+', ' ', aktenzeichen.strip())
```

## 3.3 Relation Extractor (Извлечение отношений)

```python
@dataclass
class Relation:
    """Отношение между сущностями в графе"""
    id: str                      # Уникальный ID
    type: str                    # Тип отношения
    source_id: str               # ID исходной сущности
    target_id: str               # ID целевой сущности
    properties: Dict             # Дополнительные свойства
    source_document: str         # Документ-источник
    confidence: float            # Уверенность
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'properties': self.properties,
            'source_document': self.source_document,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class RelationExtractor:
    """Извлечение отношений между сущностями"""
    
    def __init__(self, relation_types_config: dict):
        self.relation_types = relation_types_config
        self.extractors = self._build_extractors()
        
    def _build_extractors(self) -> List['RelationPattern']:
        """Создать паттерны для извлечения отношений"""
        
        return [
            # Отношение: Параграф -> Закон (принадлежит)
            RelationPattern(
                name='paragraph_belongs_to_law',
                relation_type='belongs_to',
                source_type='Paragraph',
                target_type='Gesetz',
                patterns=[
                    r'§\s*\d+[a-z]?\s+(?:des\s+)?SGB[- ]?([IVX]+)',
                    r'§\s*\d+[a-z]?\s+(?:des\s+)?Sozialgesetzbuchs?\s+([IVX]+)'
                ],
                confidence=0.95
            ),
            
            # Отношение: Параграф -> Параграф (ссылается)
            RelationPattern(
                name='paragraph_references_paragraph',
                relation_type='verweist_auf',
                source_type='Paragraph',
                target_type='Paragraph',
                patterns=[
                    r'gemäß\s+§\s*\d+[a-z]?',
                    r'nach\s+§\s*\d+[a-z]?',
                    r'im\s+Sinne\s+(?:des\s+)?§\s*\d+[a-z]?',
                    r'entsprechend\s+§\s*\d+[a-z]?'
                ],
                confidence=0.9
            ),
            
            # Отношение: Behörde -> Leistung (zuständig für)
            RelationPattern(
                name='authority_responsible_for_service',
                relation_type='zuständig_für',
                source_type='Behörde',
                target_type='Leistung',
                patterns=[
                    r'(Sozialamt|Landkreis|Bezirk)\s+ist\s+zuständig\s+für',
                    r'Zuständigkeit\s+(?:des\s+)?(Sozialamt|Landkreis|Bezirk)'
                ],
                confidence=0.85
            ),
            
            # Отношение: Bescheid -> Leistung (betrifft)
            RelationPattern(
                name='decision_concerns_service',
                relation_type='betrifft',
                source_type='Bescheid',
                target_type='Leistung',
                patterns=[
                    r'Bescheid\s+über\s+(.+)',
                    r'bewilligt\s+(.+)',
                    r'abgelehnt\s+(.+)'
                ],
                confidence=0.8
            ),
            
            # Отношение: Datum -> Event (Frist)
            RelationPattern(
                name='date_is_deadline',
                relation_type='frist_für',
                source_type='Datum',
                target_type='Verfahren',
                patterns=[
                    r'Frist\s+bis\s+zum\s+\d{1,2}\.\d{1,2}\.\d{4}',
                    r'binnen\s+\d+\s+(?:Tagen|Wochen|Monaten)'
                ],
                confidence=0.85
            )
        ]
    
    def extract(self, document: 'Document', entities: List[Entity]) -> List[Relation]:
        """Извлечь отношения между сущностями"""
        
        text = document.get_text()
        all_relations = []
        
        # 1. Отношения на основе паттернов
        for pattern in self.extractors:
            relations = pattern.extract(text, entities, document.id)
            all_relations.extend(relations)
        
        # 2. Отношения на основе близости (co-occurrence)
        proximity_relations = self._extract_proximity_relations(text, entities, document.id)
        all_relations.extend(proximity_relations)
        
        # 3. Отношения на основе структуры документа
        structural_relations = self._extract_structural_relations(document, entities)
        all_relations.extend(structural_relations)
        
        # Удалить дубликаты
        unique_relations = self._deduplicate_relations(all_relations)
        
        return unique_relations
    
    def _extract_proximity_relations(self, text: str, entities: List[Entity], document_id: str) -> List[Relation]:
        """Извлечь отношения на основе близости упоминаний"""
        
        relations = []
        window_size = 200  # Размер окна для поиска связей
        
        # Найти все позиции упоминаний сущностей
        entity_positions = []
        for entity in entities:
            # Найти все упоминания сущности в тексте
            positions = [m.start() for m in re.finditer(re.escape(entity.name), text, re.IGNORECASE)]
            for pos in positions:
                entity_positions.append((pos, entity))
        
        # Сортировать по позиции
        entity_positions.sort(key=lambda x: x[0])
        
        # Найти сущности в пределах окна
        for i, (pos1, entity1) in enumerate(entity_positions):
            for pos2, entity2 in entity_positions[i+1:]:
                if pos2 - pos1 > window_size:
                    break  # За пределами окна
                
                if entity1.id != entity2.id:
                    # Создать отношение "mentioned_with"
                    relation = Relation(
                        id=f"rel_proximity_{entity1.id}_{entity2.id}",
                        type='mentioned_with',
                        source_id=entity1.id,
                        target_id=entity2.id,
                        properties={
                            'distance': pos2 - pos1,
                            'context': text[pos1:pos2]
                        },
                        source_document=document_id,
                        confidence=0.6,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    relations.append(relation)
        
        return relations
    
    def _extract_structural_relations(self, document: 'Document', entities: List[Entity]) -> List[Relation]:
        """Извлечь отношения на основе структуры документа"""
        
        relations = []
        
        # Если документ - это возражение (Widerspruch)
        if document.document_type == 'Widerspruch':
            # Найти решение (Bescheid), на которое подается возражение
            bescheid_entities = [e for e in entities if e.type == 'Bescheid']
            widerspruch_entity = Entity(
                id=f"widerspruch_{document.id}",
                type='Widerspruch',
                name=document.title or 'Widerspruch',
                properties={},
                source_document=document.id,
                confidence=1.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            for bescheid in bescheid_entities:
                relation = Relation(
                    id=f"rel_widerspruch_gegen_{bescheid.id}",
                    type='richtet_sich_gegen',
                    source_id=widerspruch_entity.id,
                    target_id=bescheid.id,
                    properties={},
                    source_document=document.id,
                    confidence=0.9,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                relations.append(relation)
        
        return relations
    
    def _deduplicate_relations(self, relations: List[Relation]) -> List[Relation]:
        """Удалить дубликаты отношений"""
        
        seen = {}
        unique = []
        
        for relation in relations:
            # Ключ: (тип, источник, цель) - без учета направления
            key = (relation.type, min(relation.source_id, relation.target_id), max(relation.source_id, relation.target_id))
            
            if key not in seen:
                seen[key] = relation
                unique.append(relation)
            else:
                # Обновить уверенность (максимальная)
                if relation.confidence > seen[key].confidence:
                    seen[key].confidence = relation.confidence
        
        return unique


class RelationPattern:
    """Паттерн для извлечения отношения"""
    
    def __init__(self, name: str, relation_type: str, source_type: str, target_type: str, 
                 patterns: List[str], confidence: float):
        self.name = name
        self.relation_type = relation_type
        self.source_type = source_type
        self.target_type = target_type
        self.patterns = patterns
        self.confidence = confidence
    
    def extract(self, text: str, entities: List[Entity], document_id: str) -> List[Relation]:
        """Извлечь отношения по паттернам"""
        
        relations = []
        
        # Фильтровать сущности по типам
        source_entities = [e for e in entities if e.type == self.source_type]
        target_entities = [e for e in entities if e.type == self.target_type]
        
        for pattern in self.patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Найти ближайшие сущности нужных типов
                source_entity = self._find_nearest_entity(text, match.start(), source_entities, direction='before')
                target_entity = self._find_nearest_entity(text, match.start(), target_entities, direction='after')
                
                if source_entity and target_entity:
                    relation = Relation(
                        id=f"rel_{self.relation_type}_{source_entity.id}_{target_entity.id}",
                        type=self.relation_type,
                        source_id=source_entity.id,
                        target_id=target_entity.id,
                        properties={
                            'pattern': pattern,
                            'match_text': match.group(0)
                        },
                        source_document=document_id,
                        confidence=self.confidence,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    relations.append(relation)
        
        return relations
    
    def _find_nearest_entity(self, text: str, position: int, entities: List[Entity], direction: str = 'before') -> Optional[Entity]:
        """Найти ближайшую сущность в заданном направлении"""
        
        nearest = None
        min_distance = float('inf')
        
        for entity in entities:
            # Найти все упоминания сущности
            entity_positions = [m.start() for m in re.finditer(re.escape(entity.name), text, re.IGNORECASE)]
            
            for ent_pos in entity_positions:
                if direction == 'before' and ent_pos < position:
                    distance = position - ent_pos
                elif direction == 'after' and ent_pos > position:
                    distance = ent_pos - position
                else:
                    continue
                
                if distance < min_distance:
                    min_distance = distance
                    nearest = entity
        
        return nearest
```

## 3.4 Graph Builder (Построение графа)

```python
import networkx as nx
from typing import Set

class KnowledgeGraph:
    """Граф знаний домена"""
    
    def __init__(self, domain_path: str):
        self.domain_path = domain_path
        self.graph = nx.MultiDiGraph()  # Направленный мультиграф
        self.entity_index = {}  # ID -> Entity
        self.relation_index = {}  # ID -> Relation
        
        # Загрузить существующий граф
        self.load()
    
    def add_entity(self, entity: Entity) -> None:
        """Добавить сущность в граф"""
        
        # Добавить узел
        self.graph.add_node(
            entity.id,
            **entity.to_dict()
        )
        
        # Сохранить в индекс
        self.entity_index[entity.id] = entity
    
    def add_entities(self, entities: List[Entity]) -> None:
        """Добавить несколько сущностей"""
        for entity in entities:
            self.add_entity(entity)
    
    def add_relation(self, relation: Relation) -> None:
        """Добавить отношение в граф"""
        
        # Добавить ребро
        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            key=relation.id,
            **relation.to_dict()
        )
        
        # Сохранить в индекс
        self.relation_index[relation.id] = relation
    
    def add_relations(self, relations: List[Relation]) -> None:
        """Добавить несколько отношений"""
        for relation in relations:
            self.add_relation(relation)
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Получить сущность по ID"""
        return self.entity_index.get(entity_id)
    
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """Получить отношение по ID"""
        return self.relation_index.get(relation_id)
    
    def get_related_entities(self, entity_id: str, relation_type: Optional[str] = None, 
                            direction: str = 'both') -> List[Entity]:
        """Получить связанные сущности"""
        
        related_ids = set()
        
        if direction in ['out', 'both']:
            # Исходящие связи
            for target_id in self.graph.successors(entity_id):
                if relation_type is None:
                    related_ids.add(target_id)
                else:
                    # Проверить тип отношения
                    edges = self.graph.get_edge_data(entity_id, target_id)
                    for edge_key, edge_data in edges.items():
                        if edge_data.get('type') == relation_type:
                            related_ids.add(target_id)
        
        if direction in ['in', 'both']:
            # Входящие связи
            for source_id in self.graph.predecessors(entity_id):
                if relation_type is None:
                    related_ids.add(source_id)
                else:
                    edges = self.graph.get_edge_data(source_id, entity_id)
                    for edge_key, edge_data in edges.items():
                        if edge_data.get('type') == relation_type:
                            related_ids.add(source_id)
        
        return [self.entity_index[eid] for eid in related_ids if eid in self.entity_index]
    
    def find_path(self, source_id: str, target_id: str, max_length: int = 5) -> Optional[List[str]]:
        """Найти путь между двумя сущностями"""
        
        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            if len(path) <= max_length:
                return path
        except nx.NetworkXNoPath:
            pass
        
        return None
    
    def get_subgraph(self, entity_ids: List[str], depth: int = 1) -> 'KnowledgeGraph':
        """Получить подграф вокруг заданных сущностей"""
        
        # Собрать все узлы в пределах depth шагов
        nodes_to_include = set(entity_ids)
        
        for _ in range(depth):
            new_nodes = set()
            for node in nodes_to_include:
                # Добавить соседей
                new_nodes.update(self.graph.successors(node))
                new_nodes.update(self.graph.predecessors(node))
            nodes_to_include.update(new_nodes)
        
        # Создать подграф
        subgraph = self.graph.subgraph(nodes_to_include).copy()
        
        # Создать новый KnowledgeGraph
        kg = KnowledgeGraph(self.domain_path)
        kg.graph = subgraph
        
        # Заполнить индексы
        for node in subgraph.nodes():
            if node in self.entity_index:
                kg.entity_index[node] = self.entity_index[node]
        
        for u, v, key in subgraph.edges(keys=True):
            edge_data = subgraph.get_edge_data(u, v, key)
            relation_id = edge_data.get('id')
            if relation_id and relation_id in self.relation_index:
                kg.relation_index[relation_id] = self.relation_index[relation_id]
        
        return kg
    
    def save(self) -> None:
        """Сохранить граф на диск"""
        
        import json
        
        graph_path = f"{self.domain_path}/knowledge-graph"
        os.makedirs(graph_path, exist_ok=True)
        
        # Сохранить граф
        nx.write_gpickle(self.graph, f"{graph_path}/graph.gpickle")
        
        # Сохранить индексы
        with open(f"{graph_path}/entities.json", 'w', encoding='utf-8') as f:
            entities_data = {eid: entity.to_dict() for eid, entity in self.entity_index.items()}
            json.dump(entities_data, f, ensure_ascii=False, indent=2)
        
        with open(f"{graph_path}/relations.json", 'w', encoding='utf-8') as f:
            relations_data = {rid: relation.to_dict() for rid, relation in self.relation_index.items()}
            json.dump(relations_data, f, ensure_ascii=False, indent=2)
    
    def load(self) -> None:
        """Загрузить граф с диска"""
        
        import json
        
        graph_path = f"{self.domain_path}/knowledge-graph"
        
        if not os.path.exists(graph_path):
            return
        
        # Загрузить граф
        graph_file = f"{graph_path}/graph.gpickle"
        if os.path.exists(graph_file):
            self.graph = nx.read_gpickle(graph_file)
        
        # Загрузить индексы
        entities_file = f"{graph_path}/entities.json"
        if os.path.exists(entities_file):
            with open(entities_file, 'r', encoding='utf-8') as f:
                entities_data = json.load(f)
                for eid, data in entities_data.items():
                    # Восстановить Entity
                    entity = Entity(
                        id=data['id'],
                        type=data['type'],
                        name=data['name'],
                        properties=data['properties'],
                        source_document=data['source_document'],
                        confidence=data['confidence'],
                        created_at=datetime.fromisoformat(data['created_at']),
                        updated_at=datetime.fromisoformat(data['updated_at'])
                    )
                    self.entity_index[eid] = entity
        
        relations_file = f"{graph_path}/relations.json"
        if os.path.exists(relations_file):
            with open(relations_file, 'r', encoding='utf-8') as f:
                relations_data = json.load(f)
                for rid, data in relations_data.items():
                    # Восстановить Relation
                    relation = Relation(
                        id=data['id'],
                        type=data['type'],
                        source_id=data['source_id'],
                        target_id=data['target_id'],
                        properties=data['properties'],
                        source_document=data['source_document'],
                        confidence=data['confidence'],
                        created_at=datetime.fromisoformat(data['created_at']),
                        updated_at=datetime.fromisoformat(data['updated_at'])
                    )
                    self.relation_index[rid] = relation
    
    def get_statistics(self) -> dict:
        """Получить статистику графа"""
        
        # Статистика по типам сущностей
        entity_type_counts = {}
        for entity in self.entity_index.values():
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1
        
        # Статистика по типам отношений
        relation_type_counts = {}
        for relation in self.relation_index.values():
            relation_type_counts[relation.type] = relation_type_counts.get(relation.type, 0) + 1
        
        return {
            'total_entities': len(self.entity_index),
            'total_relations': len(self.relation_index),
            'entity_types': entity_type_counts,
            'relation_types': relation_type_counts,
            'density': nx.density(self.graph),
            'connected_components': nx.number_weakly_connected_components(self.graph)
        }
```

## 3.5 Query Engine (Запросы к графу)

```python
class GraphQueryEngine:
    """Движок для запросов к графу знаний"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
    
    def find_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Найти все сущности заданного типа"""
        return [e for e in self.kg.entity_index.values() if e.type == entity_type]
    
    def find_entities_by_name(self, name_pattern: str) -> List[Entity]:
        """Найти сущности по имени (поддерживает регулярные выражения)"""
        
        pattern = re.compile(name_pattern, re.IGNORECASE)
        return [e for e in self.kg.entity_index.values() if pattern.search(e.name)]
    
    def find_entities_by_property(self, property_name: str, property_value: any) -> List[Entity]:
        """Найти сущности по значению свойства"""
        
        results = []
        for entity in self.kg.entity_index.values():
            if property_name in entity.properties:
                if entity.properties[property_name] == property_value:
                    results.append(entity)
        
        return results
    
    def get_entity_neighbors(self, entity_id: str, relation_type: Optional[str] = None, 
                            max_distance: int = 1) -> List[Tuple[Entity, int]]:
        """Получить соседей сущности с расстоянием"""
        
        if entity_id not in self.kg.graph:
            return []
        
        neighbors = []
        
        # BFS для поиска соседей
        visited = {entity_id}
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, distance = queue.pop(0)
            
            if distance >= max_distance:
                continue
            
            # Получить соседей
            for neighbor_id in self.kg.graph.successors(current_id):
                if neighbor_id not in visited:
                    # Проверить тип отношения если указан
                    if relation_type is not None:
                        edges = self.kg.graph.get_edge_data(current_id, neighbor_id)
                        has_matching_edge = any(
                            edge_data.get('type') == relation_type 
                            for edge_data in edges.values()
                        )
                        if not has_matching_edge:
                            continue
                    
                    visited.add(neighbor_id)
                    entity = self.kg.get_entity(neighbor_id)
                    if entity:
                        neighbors.append((entity, distance + 1))
                        queue.append((neighbor_id, distance + 1))
        
        return neighbors
    
    def find_paths_between(self, source_id: str, target_id: str, max_length: int = 5) -> List[List[Entity]]:
        """Найти все пути между двумя сущностями"""
        
        if source_id not in self.kg.graph or target_id not in self.kg.graph:
            return []
        
        paths = []
        
        try:
            # Найти все простые пути
            for path in nx.all_simple_paths(self.kg.graph, source_id, target_id, cutoff=max_length):
                entities = [self.kg.get_entity(eid) for eid in path]
                if all(entities):
                    paths.append(entities)
        except nx.NetworkXNoPath:
            pass
        
        return paths
    
    def find_related_laws(self, paragraph: str) -> List[Entity]:
        """Найти все законы, в которых упоминается параграф"""
        
        # Найти сущность параграфа
        paragraph_entities = self.find_entities_by_name(f"§{paragraph}")
        
        if not paragraph_entities:
            return []
        
        laws = []
        for para_entity in paragraph_entities:
            # Найти связанные законы
            related = self.kg.get_related_entities(para_entity.id, relation_type='belongs_to')
            laws.extend([e for e in related if e.type == 'Gesetz'])
        
        return list(set(laws))  # Убрать дубликаты
    
    def find_authorities_responsible_for_service(self, service_name: str) -> List[Entity]:
        """Найти органы, ответственные за услугу"""
        
        # Найти сущность услуги
        service_entities = self.find_entities_by_name(service_name)
        
        if not service_entities:
            return []
        
        authorities = []
        for service_entity in service_entities:
            # Найти связанные органы (входящие связи типа zuständig_für)
            related = self.kg.get_related_entities(service_entity.id, relation_type='zuständig_für', direction='in')
            authorities.extend([e for e in related if e.type == 'Behörde'])
        
        return list(set(authorities))
    
    def get_entity_context(self, entity_id: str, depth: int = 2) -> Dict:
        """Получить полный контекст сущности"""
        
        entity = self.kg.get_entity(entity_id)
        if not entity:
            return {}
        
        # Получить подграф
        subgraph = self.kg.get_subgraph([entity_id], depth=depth)
        
        # Собрать информацию
        context = {
            'entity': entity.to_dict(),
            'related_entities': {},
            'relations': []
        }
        
        # Сгруппировать связанные сущности по типу отношения
        for relation in subgraph.relation_index.values():
            if relation.source_id == entity_id:
                if relation.type not in context['related_entities']:
                    context['related_entities'][relation.type] = []
                
                target_entity = subgraph.get_entity(relation.target_id)
                if target_entity:
                    context['related_entities'][relation.type].append(target_entity.to_dict())
                
                context['relations'].append(relation.to_dict())
        
        return context
    
    def cypher_like_query(self, query: str) -> List[Dict]:
        """Простой Cypher-подобный язык запросов
        
        Примеры:
        - "MATCH (p:Paragraph)-[:belongs_to]->(g:Gesetz) RETURN p, g"
        - "MATCH (b:Behörde)-[:zuständig_für]->(l:Leistung {name: 'Persönliches Budget'}) RETURN b"
        """
        
        # Упрощенный парсинг (для демонстрации)
        # В реальной системе нужен полноценный парсер
        
        if 'MATCH' in query and 'RETURN' in query:
            match_part = query.split('RETURN')[0].replace('MATCH', '').strip()
            return_part = query.split('RETURN')[1].strip()
            
            # Парсинг паттерна
            # (source:SourceType)-[:relation_type]->(target:TargetType)
            pattern = r'\((\w+):(\w+)\)-\[:(\w+)\]->\((\w+):(\w+)\)'
            match = re.search(pattern, match_part)
            
            if match:
                source_var, source_type, rel_type, target_var, target_type = match.groups()
                
                results = []
                
                # Найти все сущности исходного типа
                source_entities = self.find_entities_by_type(source_type)
                
                for source_entity in source_entities:
                    # Найти связанные сущности целевого типа
                    related = self.kg.get_related_entities(source_entity.id, relation_type=rel_type)
                    
                    for target_entity in related:
                        if target_entity.type == target_type:
                            results.append({
                                source_var: source_entity.to_dict(),
                                target_var: target_entity.to_dict()
                            })
                
                return results
        
        return []
```

Продолжить с Graph Analytics и Visualization Engine?