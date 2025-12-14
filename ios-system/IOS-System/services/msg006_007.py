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