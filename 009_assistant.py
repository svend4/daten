Пользователь хочет, чтобы я продолжил с Graph Analytics и Visualization Engine. Продолжаю разработку детальной технической спецификации Information Operating System.

Следующие компоненты:
1. Graph Analytics - анализ графа знаний
2. Visualization Engine - визуализация графа
3. Затем перейду к Context Manager (компонент 3)
4. И Search Engine (компонент 4)

Буду максимально детальным и структурированным.## 3.6 Graph Analytics (Аналитика графа)

```python
class GraphAnalytics:
    """Аналитика и анализ графа знаний"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
    
    def find_central_entities(self, top_n: int = 10, metric: str = 'degree') -> List[Tuple[Entity, float]]:
        """Найти наиболее центральные сущности
        
        Metrics:
        - degree: Степень узла (количество связей)
        - betweenness: Посредничество (частота на кратчайших путях)
        - closeness: Близость (среднее расстояние до других узлов)
        - pagerank: PageRank (важность по алгоритму Google)
        """
        
        if metric == 'degree':
            centrality = nx