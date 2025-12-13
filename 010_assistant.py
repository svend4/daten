Продолжаю с Graph Analytics и Visualization Engine, затем перейду к Context Manager и Search Engine.# ЧАСТЬ 4: GRAPH ANALYTICS & VISUALIZATION

## 4.1 Graph Analytics (Аналитика графа)

```python
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
```

## 4.2 Visualization Engine (Визуализация графа)

```python
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional

class GraphVisualization:
    """Визуализация графа знаний"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        
    def visualize_full_graph(self, output_file: str = 'knowledge_graph.html', 
                            layout: str = 'spring') -> None:
        """Визуализация полного графа (интерактивная)"""
        
        # Выбор алгоритма раскладки
        if layout == 'spring':
            pos = nx.spring_layout(self.kg.graph, k=0.5, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(self.kg.graph)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(self.kg.graph)
        else:
            pos = nx.spring_layout(self.kg.graph)
        
        # Подготовка данных для Plotly
        edge_trace = self._create_edge_trace(pos)
        node_trace = self._create_node_trace(pos)
        
        # Создание фигуры
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title='Knowledge Graph',
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
        )
        
        fig.write_html(output_file)
        print(f"График сохранен в {output_file}")
    
    def _create_edge_trace(self, pos: Dict) -> go.Scatter:
        """Создать trace для ребер"""
        
        edge_x = []
        edge_y = []
        
        for edge in self.kg.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        return go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
    
    def _create_node_trace(self, pos: Dict) -> go.Scatter:
        """Создать trace для узлов"""
        
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        # Цвета для разных типов сущностей
        color_map = {
            'Gesetz': '#FF6B6B',
            'Paragraph': '#4ECDC4',
            'Behörde': '#45B7D1',
            'Person': '#FFA07A',
            'Datum': '#98D8C8',
            'Geldbetrag': '#F7DC6F',
            'Leistung': '#BB8FCE',
            'Verfahren': '#85C1E2',
            'Aktenzeichen': '#F8B739'
        }
        
        for node_id in self.kg.graph.nodes():
            x, y = pos[node_id]
            node_x.append(x)
            node_y.append(y)
            
            entity = self.kg.get_entity(node_id)
            if entity:
                node_text.append(f"{entity.name}<br>Type: {entity.type}<br>Confidence: {entity.confidence:.2f}")
                node_colors.append(color_map.get(entity.type, '#95A5A6'))
                
                # Размер узла зависит от степени
                degree = self.kg.graph.in_degree(node_id) + self.kg.graph.out_degree(node_id)
                node_sizes.append(10 + degree * 2)
            else:
                node_text.append('Unknown')
                node_colors.append('#95A5A6')
                node_sizes.append(10)
        
        return go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                showscale=False,
                color=node_colors,
                size=node_sizes,
                line=dict(width=2, color='white')
            )
        )
    
    def visualize_subgraph(self, entity_ids: List[str], depth: int = 1, 
                          output_file: str = 'subgraph.html') -> None:
        """Визуализация подграфа вокруг заданных сущностей"""
        
        subgraph_kg = self.kg.get_subgraph(entity_ids, depth=depth)
        
        # Временно заменить граф
        original_graph = self.kg.graph
        self.kg.graph = subgraph_kg.graph
        
        self.visualize_full_graph(output_file=output_file)
        
        # Восстановить оригинальный граф
        self.kg.graph = original_graph
    
    def visualize_entity_neighborhood(self, entity_id: str, max_distance: int = 2,
                                     output_file: str = 'neighborhood.html') -> None:
        """Визуализация окрестности сущности"""
        
        # Собрать все узлы в окрестности
        neighbors_with_distance = GraphQueryEngine(self.kg).get_entity_neighbors(
            entity_id, max_distance=max_distance
        )
        
        neighbor_ids = [entity_id] + [e.id for e, dist in neighbors_with_distance]
        
        self.visualize_subgraph(neighbor_ids, depth=0, output_file=output_file)
    
    def create_entity_type_distribution_chart(self, output_file: str = 'entity_distribution.html') -> None:
        """График распределения типов сущностей"""
        
        type_counts = Counter(e.type for e in self.kg.entity_index.values())
        
        fig = px.bar(
            x=list(type_counts.keys()),
            y=list(type_counts.values()),
            labels={'x': 'Entity Type', 'y': 'Count'},
            title='Entity Type Distribution'
        )
        
        fig.write_html(output_file)
    
    def create_relation_type_distribution_chart(self, output_file: str = 'relation_distribution.html') -> None:
        """График распределения типов отношений"""
        
        type_counts = Counter(r.type for r in self.kg.relation_index.values())
        
        fig = px.bar(
            x=list(type_counts.keys()),
            y=list(type_counts.values()),
            labels={'x': 'Relation Type', 'y': 'Count'},
            title='Relation Type Distribution'
        )
        
        fig.write_html(output_file)
    
    def create_temporal_growth_chart(self, output_file: str = 'temporal_growth.html') -> None:
        """График роста графа во времени"""
        
        analytics = GraphAnalytics(self.kg)
        temporal_data = analytics.temporal_analysis()
        
        if 'growth_by_month' not in temporal_data:
            print("Недостаточно данных для временного анализа")
            return
        
        months = sorted(temporal_data['growth_by_month'].keys())
        entity_counts = [temporal_data['growth_by_month'][m]['entities'] for m in months]
        relation_counts = [temporal_data['growth_by_month'][m]['relations'] for m in months]
        
        # Кумулятивные суммы
        cumulative_entities = np.cumsum(entity_counts)
        cumulative_relations = np.cumsum(relation_counts)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative_entities,
            mode='lines+markers',
            name='Entities',
            line=dict(color='#4ECDC4', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative_relations,
            mode='lines+markers',
            name='Relations',
            line=dict(color='#FF6B6B', width=2)
        ))
        
        fig.update_layout(
            title='Knowledge Graph Growth Over Time',
            xaxis_title='Month',
            yaxis_title='Cumulative Count',
            hovermode='x unified'
        )
        
        fig.write_html(output_file)
    
    def create_centrality_heatmap(self, output_file: str = 'centrality_heatmap.html') -> None:
        """Тепловая карта центральности сущностей"""
        
        analytics = GraphAnalytics(self.kg)
        
        # Вычислить разные метрики центральности
        betweenness = analytics.get_central_entities('betweenness', top_n=20)
        pagerank = analytics.get_central_entities('pagerank', top_n=20)
        
        # Объединить топ сущности
        all_entities = set()
        for e, _ in betweenness:
            all_entities.add(e)
        for e, _ in pagerank:
            all_entities.add(e)
        
        # Создать матрицу
        entity_names = [e.name for e in all_entities]
        
        betweenness_dict = {e.name: score for e, score in betweenness}
        pagerank_dict = {e.name: score for e, score in pagerank}
        
        matrix = []
        for name in entity_names:
            matrix.append([
                betweenness_dict.get(name, 0),
                pagerank_dict.get(name, 0)
            ])
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=['Betweenness', 'PageRank'],
            y=entity_names,
            colorscale='Viridis'
        ))
        
        fig.update_layout(
            title='Entity Centrality Heatmap',
            xaxis_title='Centrality Metric',
            yaxis_title='Entity'
        )
        
        fig.write_html(output_file)
    
    def create_community_visualization(self, algorithm: str = 'louvain',
                                      output_file: str = 'communities.html') -> None:
        """Визуализация сообществ"""
        
        analytics = GraphAnalytics(self.kg)
        communities = analytics.detect_communities(algorithm=algorithm)
        
        # Назначить цвета сообществам
        community_colors = {}
        color_palette = px.colors.qualitative.Plotly
        
        for idx, (community_name, entities) in enumerate(communities.items()):
            color = color_palette[idx % len(color_palette)]
            for entity in entities:
                community_colors[entity.id] = color
        
        # Раскладка
        pos = nx.spring_layout(self.kg.graph, k=0.5, iterations=50)
        
        # Создать trace для ребер
        edge_trace = self._create_edge_trace(pos)
        
        # Создать trace для узлов с цветами сообществ
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        for node_id in self.kg.graph.nodes():
            x, y = pos[node_id]
            node_x.append(x)
            node_y.append(y)
            
            entity = self.kg.get_entity(node_id)
            if entity:
                node_text.append(f"{entity.name}<br>Type: {entity.type}")
                node_colors.append(community_colors.get(node_id, '#95A5A6'))
            else:
                node_text.append('Unknown')
                node_colors.append('#95A5A6')
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                color=node_colors,
                size=15,
                line=dict(width=2, color='white')
            )
        )
        
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=f'Communities ({algorithm})',
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        
        fig.write_html(output_file)
    
    def export_to_gephi(self, output_file: str = 'knowledge_graph.gexf') -> None:
        """Экспорт графа в формат GEXF для Gephi"""
        
        nx.write_gexf(self.kg.graph, output_file)
        print(f"Граф экспортирован в {output_file} для Gephi")
    
    def export_to_cytoscape(self, output_file: str = 'knowledge_graph_cytoscape.json') -> None:
        """Экспорт графа в формат Cytoscape.js"""
        
        from networkx.readwrite import cytoscape_data
        
        cyto_data = cytoscape_data(self.kg.graph)
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cyto_data, f, ensure_ascii=False, indent=2)
        
        print(f"Граф экспортирован в {output_file} для Cytoscape")
```

---

# ЧАСТЬ 5: КОМПОНЕНТ 3 - CONTEXT MANAGER

## 5.1 Архитектура Context Manager

```python
from dataclasses import dataclass, field
from enum import Enum

class ContextType(Enum):
    """Типы контекстов"""
    WORK = "work"
    PERSONAL = "personal"
    PROJECT = "project"
    RESEARCH = "research"
    LEGAL_CASE = "legal_case"
    TEMPORARY = "temporary"


@dataclass
class Context:
    """Контекст работы"""
    id: str
    name: str
    type: ContextType
    description: str
    
    # Активные объекты в контексте
    active_domains: List[str] = field(default_factory=list)
    active_projects: List[str] = field(default_factory=list)
    active_documents: List[str] = field(default_factory=list)
    recent_searches: List[str] = field(default_factory=list)
    
    # Состояние
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    # Метаданные
    tags: List[str] = field(default_factory=list)
    properties: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'active_domains': self.active_domains,
            'active_projects': self.active_projects,
            'active_documents': self.active_documents,
            'recent_searches': self.recent_searches,
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'tags': self.tags,
            'properties': self.properties
        }


class ContextManager:
    """Управление контекстами работы - аналог Process Scheduler в ОС"""
    
    def __init__(self, ios_root: 'IOSRoot'):
        self.ios_root = ios_root
        self.contexts: Dict[str, Context] = {}
        self.current_context: Optional[Context] = None
        self.context_history: List[Tuple[Context, datetime]] = []
        
        # Загрузить контексты
        self.load_contexts()
    
    def create_context(self, name: str, context_type: ContextType, 
                      description: str = "", **kwargs) -> Context:
        """Создать новый контекст"""
        
        context_id = f"ctx_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
        
        context = Context(
            id=context_id,
            name=name,
            type=context_type,
            description=description,
            **kwargs
        )
        
        self.contexts[context_id] = context
        self.save_contexts()
        
        return context
    
    def switch_context(self, context_id: str) -> Dict[str, any]:
        """Переключиться на другой контекст"""
        
        if context_id not in self.contexts:
            raise ValueError(f"Context {context_id} not found")
        
        # Сохранить текущий контекст
        if self.current_context:
            self.save_current_state()
            self.context_history.append((self.current_context, datetime.now()))
        
        # Загрузить новый контекст
        new_context = self.contexts[context_id]
        self.current_context = new_context
        
        # Обновить статистику
        new_context.last_accessed = datetime.now()
        new_context.access_count += 1
        
        # Загрузить состояние
        state = self.load_context_state(new_context)
        
        return state
    
    def save_current_state(self) -> None:
        """Сохранить состояние текущего контекста"""
        
        if not self.current_context:
            return
        
        # Сохранить активные документы, поиски и т.д.
        self.save_contexts()
    
    def load_context_state(self, context: Context) -> Dict[str, any]:
        """Загрузить состояние контекста"""
        
        state = {
            'context': context.to_dict(),
            'domains': [],
            'projects': [],
            'documents': [],
            'recent_searches': context.recent_searches[-10:]  # Последние 10
        }
        
        # Загрузить домены
        for domain_name in context.active_domains:
            try:
                domain = self.ios_root.get_domain(domain_name)
                state['domains'].append({
                    'name': domain.name,
                    'statistics': domain.get_statistics()
                })
            except:
                pass
        
        # Загрузить документы
        for doc_id in context.active_documents[-20:]:  # Последние 20
            # Поиск документа в доменах
            for domain_name in context.active_domains:
                try:
                    domain = self.ios_root.get_domain(domain_name)
                    # Здесь нужна реализация поиска документа по ID
                    # doc = domain.get_document(doc_id)
                    # if doc:
                    #     state['documents'].append(doc.to_dict())
                except:
                    pass
        
        return state
    
    def add_to_context(self, item_type: str, item_id: str) -> None:
        """Добавить объект в текущий контекст"""
        
        if not self.current_context:
            return
        
        if item_type == 'domain':
            if item_id not in self.current_context.active_domains:
                self.current_context.active_domains.append(item_id)
        
        elif item_type == 'project':
            if item_id not in self.current_context.active_projects:
                self.current_context.active_projects.append(item_id)
        
        elif item_type == 'document':
            if item_id not in self.current_context.active_documents:
                self.current_context.active_documents.append(item_id)
                # Ограничить список последними 100 документами
                if len(self.current_context.active_documents) > 100:
                    self.current_context.active_documents = self.current_context.active_documents[-100:]
        
        elif item_type == 'search':
            if item_id not in self.current_context.recent_searches:
                self.current_context.recent_searches.append(item_id)
                # Ограничить список последними 50 поисками
                if len(self.current_context.recent_searches) > 50:
                    self.current_context.recent_searches = self.current_context.recent_searches[-50:]
        
        self.save_contexts()
    
    def get_context_recommendations(self) -> List[Dict]:
        """Получить рекомендации на основе текущего контекста"""
        
        if not self.current_context:
            return []
        
        recommendations = []
        
        # 1. Рекомендации на основе активных доменов
        for domain_name in self.current_context.active_domains:
            # Найти связанные документы
            # domain = self.ios_root.get_domain(domain_name)
            # recent_docs = domain.get_recent_documents(limit=5)
            # recommendations.append({
            #     'type': 'recent_documents',
            #     'domain': domain_name,
            #     'documents': recent_docs
            # })
            pass
        
        # 2. Рекомендации на основе истории поисков
        if self.current_context.recent_searches:
            # Найти связанные поиски
            recommendations.append({
                'type': 'related_searches',
                'searches': self.current_context.recent_searches[-5:]
            })
        
        # 3. Рекомендации на основе времени суток
        current_hour = datetime.now().hour
        
        if 9 <= current_hour < 12:
            recommendations.append({
                'type': 'time_based',
                'suggestion': 'Утренние задачи: проверка новых документов и обновлений'
            })
        elif 14 <= current_hour < 18:
            recommendations.append({
                'type': 'time_based',
                'suggestion': 'Время для глубокой работы: анализ и создание документов'
            })
        
        return recommendations
    
    def get_context_history(self, limit: int = 10) -> List[Dict]:
        """Получить историю переключений контекста"""
        
        history = []
        for context, timestamp in self.context_history[-limit:]:
            history.append({
                'context': context.to_dict(),
                'accessed_at': timestamp.isoformat()
            })
        
        return history
    
    def save_contexts(self) -> None:
        """Сохранить все контексты"""
        
        import json
        
        contexts_path = f"{self.ios_root.root_path}/contexts"
        os.makedirs(contexts_path, exist_ok=True)
        
        contexts_data = {cid: ctx.to_dict() for cid, ctx in self.contexts.items()}
        
        with open(f"{contexts_path}/contexts.json", 'w', encoding='utf-8') as f:
            json.dump(contexts_data, f, ensure_ascii=False, indent=2)
    
    def load_contexts(self) -> None:
        """Загрузить контексты"""
        
        import json
        
        contexts_path = f"{self.ios_root.root_path}/contexts"
        contexts_file = f"{contexts_path}/contexts.json"
        
        if not os.path.exists(contexts_file):
            return
        
        with open(contexts_file, 'r', encoding='utf-8') as f:
            contexts_data = json.load(f)
        
        for cid, data in contexts_data.items():
            context = Context(
                id=data['id'],
                name=data['name'],
                type=ContextType(data['type']),
                description=data['description'],
                active_domains=data.get('active_domains', []),
                active_projects=data.get('active_projects', []),
                active_documents=data.get('active_documents', []),
                recent_searches=data.get('recent_searches', []),
                last_accessed=datetime.fromisoformat(data['last_accessed']),
                access_count=data.get('access_count', 0),
                tags=data.get('tags', []),
                properties=data.get('properties', {})
            )
            
            self.contexts[cid] = context
```

Продолжить с Search Engine?