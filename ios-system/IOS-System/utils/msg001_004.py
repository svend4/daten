def build_knowledge_graph(documents):
    graph = {}
    
    for doc in documents:
        # Извлечь сущности (законы, организации, понятия)
        entities = extract_entities(doc)
        
        # Извлечь связи (ссылается на, противоречит, дополняет)
        relations = extract_relations(doc, entities)
        
        # Добавить в граф
        graph.add_nodes(entities)
        graph.add_edges(relations)
    
    return graph