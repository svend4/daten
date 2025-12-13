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