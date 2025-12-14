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