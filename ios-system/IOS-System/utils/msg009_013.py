import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set

class GraphAnalytics:
    """Аналитика графа знаний"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        
    def get_most_connected_entities(self, top_n: int = 10, entity_type: Optional[str] = None) -> List[Tuple[Entity, int]]:
        """Получить наиболее связанные сущности (по степени узла)"""
        
        degree_dict = {}
        
        for entity_id, entity in self.kg.entity_index.items():
            if entity_type and entity.type != entity_type:
                continue
            
            # Степень узла (входящие + исходящие связи)
            degree = self.kg.graph.in_degree(entity_id) + self.kg.graph.out_degree(entity_id)
            degree_dict[entity] = degree
        
        # Сортировка по степени
        sorted_entities = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_entities[:top_n]
    
    def get_central_entities(self, centrality_type: str = 'betweenness', top_n: int = 10) -> List[Tuple[Entity, float]]:
        """Получить центральные сущности
        
        Args:
            centrality_type: 'betweenness', 'closeness', 'pagerank', 'eigenvector'
        """
        
        if centrality_type == 'betweenness':
            centrality = nx.betweenness_centrality(self.kg.graph)
        elif centrality_type == 'closeness':
            centrality = nx.closeness_centrality(self.kg.graph)
        elif centrality_type == 'pagerank':
            centrality = nx.pagerank(self.kg.graph)
        elif centrality_type == 'eigenvector':
            try:
                centrality = nx.eigenvector_centrality(self.kg.graph, max_iter=1000)
            except:
                centrality = nx.pagerank(self.kg.graph)  # Fallback
        else:
            raise ValueError(f"Unknown centrality type: {centrality_type}")
        
        # Преобразовать ID в Entity
        entity_centrality = []
        for entity_id, score in centrality.items():
            entity = self.kg.get_entity(entity_id)
            if entity:
                entity_centrality.append((entity, score))
        
        # Сортировка по значению центральности
        sorted_entities = sorted(entity_centrality, key=lambda x: x[1], reverse=True)
        
        return sorted_entities[:top_n]
    
    def detect_communities(self, algorithm: str = 'louvain') -> Dict[str, List[Entity]]:
        """Обнаружить сообщества (кластеры) в графе
        
        Args:
            algorithm: 'louvain', 'label_propagation', 'greedy_modularity'
        """
        
        # Преобразовать в ненаправленный граф для алгоритмов сообществ
        undirected = self.kg.graph.to_undirected()
        
        if algorithm == 'louvain':
            import community as community_louvain
            partition = community_louvain.best_partition(undirected)
        elif algorithm == 'label_propagation':
            communities = nx.algorithms.community.label_propagation_communities(undirected)
            partition = {}
            for idx, community in enumerate(communities):
                for node in community:
                    partition[node] = idx
        elif algorithm == 'greedy_modularity':
            communities = nx.algorithms.community.greedy_modularity_communities(undirected)
            partition = {}
            for idx, community in enumerate(communities):
                for node in community:
                    partition[node] = idx
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Группировка по сообществам
        communities_dict = defaultdict(list)
        for entity_id, community_id in partition.items():
            entity = self.kg.get_entity(entity_id)
            if entity:
                communities_dict[f"Community_{community_id}"].append(entity)
        
        return dict(communities_dict)
    
    def find_bridges(self) -> List[Tuple[Entity, Entity]]:
        """Найти мосты - ребра, удаление которых разъединит граф"""
        
        undirected = self.kg.graph.to_undirected()
        bridges = list(nx.bridges(undirected))
        
        bridge_entities = []
        for source_id, target_id in bridges:
            source_entity = self.kg.get_entity(source_id)
            target_entity = self.kg.get_entity(target_id)
            if source_entity and target_entity:
                bridge_entities.append((source_entity, target_entity))
        
        return bridge_entities
    
    def find_cut_vertices(self) -> List[Entity]:
        """Найти точки сочленения - узлы, удаление которых разъединит граф"""
        
        undirected = self.kg.graph.to_undirected()
        cut_vertices = list(nx.articulation_points(undirected))
        
        return [self.kg.get_entity(vid) for vid in cut_vertices if self.kg.get_entity(vid)]
    
    def analyze_relation_types(self) -> Dict[str, Dict]:
        """Анализ типов отношений"""
        
        relation_stats = defaultdict(lambda: {
            'count': 0,
            'source_types': Counter(),
            'target_types': Counter(),
            'avg_confidence': []
        })
        
        for relation in self.kg.relation_index.values():
            stats = relation_stats[relation.type]
            stats['count'] += 1
            stats['avg_confidence'].append(relation.confidence)
            
            # Типы источников и целей
            source_entity = self.kg.get_entity(relation.source_id)
            target_entity = self.kg.get_entity(relation.target_id)
            
            if source_entity:
                stats['source_types'][source_entity.type] += 1
            if target_entity:
                stats['target_types'][target_entity.type] += 1
        
        # Вычислить средние значения
        result = {}
        for rel_type, stats in relation_stats.items():
            result[rel_type] = {
                'count': stats['count'],
                'source_types': dict(stats['source_types']),
                'target_types': dict(stats['target_types']),
                'avg_confidence': np.mean(stats['avg_confidence']) if stats['avg_confidence'] else 0.0
            }
        
        return result
    
    def find_dense_subgraphs(self, min_density: float = 0.5, min_size: int = 3) -> List[Set[Entity]]:
        """Найти плотные подграфы (клики и квази-клики)"""
        
        undirected = self.kg.graph.to_undirected()
        
        dense_subgraphs = []
        
        # Найти все клики
        cliques = list(nx.find_cliques(undirected))
        
        for clique in cliques:
            if len(clique) >= min_size:
                # Проверить плотность
                subgraph = undirected.subgraph(clique)
                density = nx.density(subgraph)
                
                if density >= min_density:
                    entities = {self.kg.get_entity(nid) for nid in clique}
                    entities = {e for e in entities if e}  # Убрать None
                    if entities:
                        dense_subgraphs.append(entities)
        
        return dense_subgraphs
    
    def get_entity_importance_score(self, entity_id: str) -> float:
        """Вычислить общую важность сущности (композитная метрика)"""
        
        if entity_id not in self.kg.graph:
            return 0.0
        
        entity = self.kg.get_entity(entity_id)
        if not entity:
            return 0.0
        
        # Компоненты важности:
        scores = []
        
        # 1. Степень узла (нормализованная)
        degree = self.kg.graph.in_degree(entity_id) + self.kg.graph.out_degree(entity_id)
        max_degree = max(
            self.kg.graph.in_degree(n) + self.kg.graph.out_degree(n) 
            for n in self.kg.graph.nodes()
        ) or 1
        degree_score = degree / max_degree
        scores.append(('degree', degree_score, 0.3))
        
        # 2. PageRank
        pagerank = nx.pagerank(self.kg.graph)
        pagerank_score = pagerank.get(entity_id, 0.0)
        scores.append(('pagerank', pagerank_score, 0.3))
        
        # 3. Уверенность в извлечении
        confidence_score = entity.confidence
        scores.append(('confidence', confidence_score, 0.2))
        
        # 4. Количество упоминаний в документах
        mention_count = entity.properties.get('mention_count', 1)
        max_mentions = max(
            e.properties.get('mention_count', 1) 
            for e in self.kg.entity_index.values()
        )
        mention_score = mention_count / max_mentions
        scores.append(('mentions', mention_score, 0.2))
        
        # Взвешенная сумма
        total_score = sum(score * weight for name, score, weight in scores)
        
        return total_score
    
    def rank_entities_by_importance(self, entity_type: Optional[str] = None, top_n: int = 10) -> List[Tuple[Entity, float]]:
        """Ранжировать сущности по важности"""
        
        rankings = []
        
        for entity_id, entity in self.kg.entity_index.items():
            if entity_type and entity.type != entity_type:
                continue
            
            importance = self.get_entity_importance_score(entity_id)
            rankings.append((entity, importance))
        
        # Сортировка по важности
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings[:top_n]
    
    def find_missing_relations(self, relation_type: str, source_type: str, target_type: str) -> List[Tuple[Entity, Entity]]:
        """Найти потенциально отсутствующие отношения (предсказание связей)"""
        
        # Собрать все существующие пары для данного типа отношения
        existing_pairs = set()
        for relation in self.kg.relation_index.values():
            if relation.type == relation_type:
                existing_pairs.add((relation.source_id, relation.target_id))
        
        # Найти все сущности нужных типов
        source_entities = [e for e in self.kg.entity_index.values() if e.type == source_type]
        target_entities = [e for e in self.kg.entity_index.values() if e.type == target_type]
        
        # Предсказать отсутствующие связи
        missing_relations = []
        
        for source_entity in source_entities:
            for target_entity in target_entities:
                if (source_entity.id, target_entity.id) not in existing_pairs:
                    # Проверить, есть ли косвенная связь
                    path = self.kg.find_path(source_entity.id, target_entity.id, max_length=3)
                    
                    if path:  # Есть косвенная связь - возможно, должна быть прямая
                        missing_relations.append((source_entity, target_entity))
        
        return missing_relations
    
    def temporal_analysis(self) -> Dict[str, any]:
        """Временной анализ графа (как он рос со временем)"""
        
        # Собрать временные метки
        entity_dates = [e.created_at for e in self.kg.entity_index.values()]
        relation_dates = [r.created_at for r in self.kg.relation_index.values()]
        
        if not entity_dates:
            return {}
        
        # Сортировка по дате
        entity_dates.sort()
        relation_dates.sort()
        
        # Рост графа по месяцам
        growth_by_month = defaultdict(lambda: {'entities': 0, 'relations': 0})
        
        for date in entity_dates:
            month_key = date.strftime('%Y-%m')
            growth_by_month[month_key]['entities'] += 1
        
        for date in relation_dates:
            month_key = date.strftime('%Y-%m')
            growth_by_month[month_key]['relations'] += 1
        
        return {
            'first_entity': entity_dates[0],
            'last_entity': entity_dates[-1],
            'growth_by_month': dict(growth_by_month),
            'total_entities': len(entity_dates),
            'total_relations': len(relation_dates)
        }
    
    def knowledge_coverage_analysis(self) -> Dict[str, any]:
        """Анализ покрытия знаний"""
        
        # Анализ по типам сущностей
        entity_type_coverage = Counter(e.type for e in self.kg.entity_index.values())
        
        # Документы как источники
        source_document_coverage = Counter(e.source_document for e in self.kg.entity_index.values())
        
        # Сущности без связей (изолированные)
        isolated_entities = []
        for entity_id, entity in self.kg.entity_index.items():
            if self.kg.graph.degree(entity_id) == 0:
                isolated_entities.append(entity)
        
        # Сущности с низкой уверенностью
        low_confidence_entities = [e for e in self.kg.entity_index.values() if e.confidence < 0.6]
        
        return {
            'entity_type_distribution': dict(entity_type_coverage),
            'source_document_distribution': dict(source_document_coverage),
            'isolated_entities_count': len(isolated_entities),
            'isolated_entities': [e.to_dict() for e in isolated_entities[:10]],  # Первые 10
            'low_confidence_count': len(low_confidence_entities),
            'low_confidence_entities': [e.to_dict() for e in low_confidence_entities[:10]]
        }
    
    def generate_recommendations(self) -> Dict[str, List[str]]:
        """Генерация рекомендаций по улучшению графа"""
        
        recommendations = {
            'extract_more_entities': [],
            'add_missing_relations': [],
            'verify_low_confidence': [],
            'merge_duplicates': [],
            'expand_coverage': []
        }
        
        # 1. Рекомендации по извлечению сущностей
        entity_type_counts = Counter(e.type for e in self.kg.entity_index.values())
        avg_count = np.mean(list(entity_type_counts.values())) if entity_type_counts else 0
        
        for entity_type, count in entity_type_counts.items():
            if count < avg_count * 0.5:
                recommendations['extract_more_entities'].append(
                    f"Мало сущностей типа '{entity_type}': {count} (среднее: {avg_count:.1f})"
                )
        
        # 2. Отсутствующие связи
        missing = self.find_missing_relations('verweist_auf', 'Paragraph', 'Paragraph')
        if len(missing) > 0:
            recommendations['add_missing_relations'].append(
                f"Обнаружено {len(missing)} потенциальных связей между параграфами"
            )
        
        # 3. Низкая уверенность
        low_conf = [e for e in self.kg.entity_index.values() if e.confidence < 0.6]
        if len(low_conf) > 0:
            recommendations['verify_low_confidence'].append(
                f"Найдено {len(low_conf)} сущностей с низкой уверенностью (< 0.6)"
            )
        
        # 4. Возможные дубликаты
        name_groups = defaultdict(list)
        for entity in self.kg.entity_index.values():
            normalized = entity.name.lower().strip()
            name_groups[normalized].append(entity)
        
        duplicates = {name: entities for name, entities in name_groups.items() if len(entities) > 1}
        if duplicates:
            recommendations['merge_duplicates'].append(
                f"Обнаружено {len(duplicates)} групп возможных дубликатов"
            )
        
        # 5. Расширение покрытия
        doc_coverage = Counter(e.source_document for e in self.kg.entity_index.values())
        if len(doc_coverage) < 10:
            recommendations['expand_coverage'].append(
                f"Граф покрывает только {len(doc_coverage)} документов. Рекомендуется добавить больше источников."
            )
        
        return recommendations


class GraphStatistics:
    """Статистика графа знаний"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        self.analytics = GraphAnalytics(knowledge_graph)
    
    def generate_full_report(self) -> Dict[str, any]:
        """Генерация полного отчета о графе"""
        
        report = {
            'basic_statistics': self._basic_statistics(),
            'connectivity': self._connectivity_statistics(),
            'centrality': self._centrality_statistics(),
            'communities': self._community_statistics(),
            'temporal': self.analytics.temporal_analysis(),
            'coverage': self.analytics.knowledge_coverage_analysis(),
            'recommendations': self.analytics.generate_recommendations()
        }
        
        return report
    
    def _basic_statistics(self) -> Dict:
        """Базовая статистика"""
        
        return {
            'total_entities': len(self.kg.entity_index),
            'total_relations': len(self.kg.relation_index),
            'entity_types': Counter(e.type for e in self.kg.entity_index.values()),
            'relation_types': Counter(r.type for r in self.kg.relation_index.values()),
            'average_degree': np.mean([
                self.kg.graph.in_degree(n) + self.kg.graph.out_degree(n)
                for n in self.kg.graph.nodes()
            ]) if self.kg.graph.nodes() else 0,
            'density': nx.density(self.kg.graph)
        }
    
    def _connectivity_statistics(self) -> Dict:
        """Статистика связности"""
        
        undirected = self.kg.graph.to_undirected()
        
        return {
            'is_connected': nx.is_connected(undirected),
            'num_connected_components': nx.number_connected_components(undirected),
            'largest_component_size': len(max(nx.connected_components(undirected), key=len)) if undirected.nodes() else 0,
            'num_weakly_connected': nx.number_weakly_connected_components(self.kg.graph),
            'num_strongly_connected': nx.number_strongly_connected_components(self.kg.graph),
            'diameter': self._safe_diameter(undirected)
        }
    
    def _safe_diameter(self, graph) -> Optional[int]:
        """Безопасное вычисление диаметра (только для связного графа)"""
        try:
            if nx.is_connected(graph):
                return nx.diameter(graph)
        except:
            pass
        return None
    
    def _centrality_statistics(self) -> Dict:
        """Статистика центральности"""
        
        top_betweenness = self.analytics.get_central_entities('betweenness', top_n=5)
        top_pagerank = self.analytics.get_central_entities('pagerank', top_n=5)
        
        return {
            'top_betweenness': [(e.name, score) for e, score in top_betweenness],
            'top_pagerank': [(e.name, score) for e, score in top_pagerank]
        }
    
    def _community_statistics(self) -> Dict:
        """Статистика сообществ"""
        
        try:
            communities = self.analytics.detect_communities('louvain')
            
            return {
                'num_communities': len(communities),
                'community_sizes': {name: len(entities) for name, entities in communities.items()},
                'largest_community': max(communities.items(), key=lambda x: len(x[1]))[0] if communities else None
            }
        except:
            return {}
    
    def export_report_to_file(self, filepath: str) -> None:
        """Экспорт отчета в файл"""
        
        import json
        
        report = self.generate_full_report()
        
        # Сериализация (преобразование Counter в dict)
        def serialize(obj):
            if isinstance(obj, Counter):
                return dict(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, set):
                return list(obj)
            return obj
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=serialize)