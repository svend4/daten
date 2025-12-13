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