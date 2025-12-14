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