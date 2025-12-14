#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный пример использования Information Operating System (IOS)
Демонстрирует работу всех компонентов системы
"""

import os
from datetime import datetime
from typing import List, Dict

# ============================================================================
# ПРИМЕР 1: ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ
# ============================================================================

def example_1_initialize_ios():
    """Инициализация IOS с нуля"""
    
    print("=" * 80)
    print("ПРИМЕР 1: Инициализация Information Operating System")
    print("=" * 80)
    
    # Создать корневую директорию
    ios_root_path = "/home/max/IOS-System"
    
    # Инициализировать IOS Root
    ios_root = IOSRoot(ios_root_path)
    
    print(f"✓ IOS Root создан: {ios_root_path}")
    print(f"✓ Глобальный индекс: {ios_root.global_index}")
    print(f"✓ Мастер-онтология: {ios_root.ontology}")
    
    # Создать домены
    print("\n--- Создание доменов ---")
    
    # Домен для немецкого социального права
    sgb_domain = ios_root.create_domain(
        name="SGB-IX",
        config={
            'language': 'de',
            'entity_types': ['Gesetz', 'Paragraph', 'Behörde', 'Leistung'],
            'description': 'Deutsches Sozialrecht - SGB IX, XI, XII'
        }
    )
    print(f"✓ Создан домен: {sgb_domain.name}")
    
    # Домен для медицинской информации
    medical_domain = ios_root.create_domain(
        name="Medical",
        config={
            'language': 'de',
            'entity_types': ['Diagnose', 'Behandlung', 'Medikament'],
            'description': 'Медицинская информация'
        }
    )
    print(f"✓ Создан домен: {medical_domain.name}")
    
    # Создать контексты
    print("\n--- Создание контекстов ---")
    
    context_manager = ContextManager(ios_root)
    
    # Рабочий контекст
    work_context = context_manager.create_context(
        name="Arbeit - Sozialrecht",
        context_type=ContextType.WORK,
        description="Работа с документами социального права",
        active_domains=['SGB-IX']
    )
    print(f"✓ Создан контекст: {work_context.name}")
    
    # Контекст судебного дела
    court_context = context_manager.create_context(
        name="Gerichtsverfahren S 12/2024",
        context_type=ContextType.LEGAL_CASE,
        description="Судебное дело по персональному бюджету",
        active_domains=['SGB-IX'],
        properties={
            'case_number': 'S 12/2024',
            'court': 'Sozialgericht München'
        }
    )
    print(f"✓ Создан контекст: {court_context.name}")
    
    return ios_root, sgb_domain, medical_domain, context_manager


# ============================================================================
# ПРИМЕР 2: ЗАГРУЗКА И КЛАССИФИКАЦИЯ ДОКУМЕНТОВ
# ============================================================================

def example_2_document_classification(sgb_domain):
    """Автоматическая классификация документов"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 2: Автоматическая классификация документов")
    print("=" * 80)
    
    # Симуляция документов
    documents = [
        {
            'title': 'Widerspruch gegen Bescheid vom 15.11.2024',
            'content': '''
            Sehr geehrte Damen und Herren,
            
            hiermit widerspreche ich dem Bescheid vom 15.11.2024 über die Ablehnung
            des Persönlichen Budgets gemäß § 29 SGB IX.
            
            Die Ablehnung ist rechtswidrig, da die Voraussetzungen nach § 29 SGB IX
            eindeutig erfüllt sind. Ich habe Anspruch auf Leistungen zur Teilhabe
            und kann diese in Form des Persönlichen Budgets in Anspruch nehmen.
            
            Ich beantrage die vollständige Aufhebung des Bescheids und die Bewilligung
            des Persönlichen Budgets in Höhe von 2.500 € monatlich.
            
            Mit freundlichen Grüßen
            Max Mustermann
            ''',
            'file_path': '/documents/widerspruch_2024_11_20.pdf'
        },
        {
            'title': 'Antrag auf Persönliches Budget',
            'content': '''
            Antrag auf Leistungen zur Teilhabe in Form des Persönlichen Budgets
            
            Hiermit beantrage ich gemäß § 29 SGB IX die Gewährung eines Persönlichen
            Budgets für folgende Leistungen:
            
            1. Assistenzleistungen: 1.800 € monatlich
            2. Teilhabe am Arbeitsleben: 500 € monatlich
            3. Soziale Teilhabe: 200 € monatlich
            
            Gesamtsumme: 2.500 € monatlich
            
            Zuständigkeit: Bezirk Oberbayern gemäß § 98 SGB IX
            ''',
            'file_path': '/documents/antrag_pb_2024_10_01.pdf'
        },
        {
            'title': 'Bescheid über Bewilligung Eingliederungshilfe',
            'content': '''
            Bescheid
            
            Das Sozialamt München bewilligt Ihnen ab 01.01.2025 Leistungen der
            Eingliederungshilfe nach § 99 SGB IX in Höhe von 1.200 € monatlich.
            
            Die Leistung wird für folgende Maßnahmen gewährt:
            - Assistenz im Haushalt
            - Unterstützung bei der Teilhabe am gesellschaftlichen Leben
            
            Dieser Bescheid ergeht gemäß § 120 SGB IX.
            
            Rechtsbehelfsbelehrung:
            Gegen diesen Bescheid kann innerhalb eines Monats Widerspruch eingelegt werden.
            ''',
            'file_path': '/documents/bescheid_bewilligung_2024_12_01.pdf'
        }
    ]
    
    # Классификация каждого документа
    classifier = ClassificationEngine(sgb_domain)
    
    for doc_data in documents:
        print(f"\n--- Классификация: {doc_data['title']} ---")
        
        # Создать объект документа
        document = Document(
            id=f"doc_{hash(doc_data['title'])}",
            title=doc_data['title'],
            content=doc_data['content'],
            file_path=doc_data['file_path'],
            creation_date=datetime.now()
        )
        
        # Классифицировать
        classification = classifier.classify(document)
        
        print(f"Тип документа: {classification.document_type}")
        print(f"Категория: {classification.category}")
        print(f"Подкатегория: {classification.subcategory or 'N/A'}")
        print(f"Теги: {', '.join(classification.tags)}")
        print(f"Уверенность: {classification.confidence:.2%}")
        
        # Добавить документ в домен
        sgb_domain.add_document(document)
        print(f"✓ Документ добавлен в домен")


# ============================================================================
# ПРИМЕР 3: ПОСТРОЕНИЕ ГРАФА ЗНАНИЙ
# ============================================================================

def example_3_knowledge_graph_construction(sgb_domain):
    """Построение графа знаний из документов"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 3: Построение графа знаний")
    print("=" * 80)
    
    # Получить граф знаний домена
    kg = sgb_domain.knowledge_graph
    
    # Пример документа для извлечения сущностей и отношений
    document = Document(
        id="doc_example_kg",
        title="SGB IX - Rehabilitation und Teilhabe",
        content='''
        Das Sozialgesetzbuch Neuntes Buch (SGB IX) regelt die Rehabilitation und
        Teilhabe von Menschen mit Behinderungen.
        
        § 29 SGB IX regelt das Persönliche Budget. Menschen mit Behinderungen können
        anstelle von Dienst- oder Sachleistungen ein Persönliches Budget erhalten.
        
        Die Zuständigkeit liegt beim Bezirk gemäß § 98 SGB IX. Das Sozialamt ist
        für die Eingliederungshilfe nach § 99 SGB IX zuständig.
        
        § 29 verweist auf § 8 SGB IX bezüglich der Wunsch- und Wahlrechte.
        ''',
        file_path="/documents/sgb_ix_excerpt.pdf",
        creation_date=datetime.now()
    )
    
    print("\n--- Извлечение сущностей ---")
    
    # Извлечение сущностей
    entity_extractor = EntityExtractor(sgb_domain.entity_types)
    entities = entity_extractor.extract(document)
    
    for entity in entities:
        print(f"• {entity.type}: {entity.name} (уверенность: {entity.confidence:.2%})")
        kg.add_entity(entity)
    
    print(f"\n✓ Извлечено {len(entities)} сущностей")
    
    print("\n--- Извлечение отношений ---")
    
    # Извлечение отношений
    relation_extractor = RelationExtractor(sgb_domain.relation_types)
    relations = relation_extractor.extract(document, entities)
    
    for relation in relations:
        source = kg.get_entity(relation.source_id)
        target = kg.get_entity(relation.target_id)
        if source and target:
            print(f"• {source.name} --[{relation.type}]--> {target.name}")
            kg.add_relation(relation)
    
    print(f"\n✓ Извлечено {len(relations)} отношений")
    
    # Сохранить граф
    kg.save()
    print("\n✓ Граф знаний сохранен")
    
    # Статистика графа
    print("\n--- Статистика графа ---")
    stats = kg.get_statistics()
    print(f"Всего сущностей: {stats['total_entities']}")
    print(f"Всего отношений: {stats['total_relations']}")
    print(f"Типы сущностей: {stats['entity_types']}")
    print(f"Типы отношений: {stats['relation_types']}")
    
    return kg


# ============================================================================
# ПРИМЕР 4: ЗАПРОСЫ К ГРАФУ ЗНАНИЙ
# ============================================================================

def example_4_graph_queries(kg):
    """Запросы к графу знаний"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 4: Запросы к графу знаний")
    print("=" * 80)
    
    query_engine = GraphQueryEngine(kg)
    
    # Запрос 1: Найти все параграфы
    print("\n--- Запрос 1: Все параграфы ---")
    paragraphs = query_engine.find_entities_by_type('Paragraph')
    for para in paragraphs[:5]:
        print(f"• {para.name}: {para.properties.get('title', 'Без названия')}")
    
    # Запрос 2: Найти законы, связанные с персональным бюджетом
    print("\n--- Запрос 2: Законы, связанные с 'Persönliches Budget' ---")
    pb_entities = query_engine.find_entities_by_name("Persönliches Budget")
    if pb_entities:
        pb_entity = pb_entities[0]
        related = kg.get_related_entities(pb_entity.id, relation_type='verweist_auf')
        for entity in related:
            print(f"• {entity.type}: {entity.name}")
    
    # Запрос 3: Найти органы, ответственные за услуги
    print("\n--- Запрос 3: Органы власти ---")
    authorities = query_engine.find_entities_by_type('Behörde')
    for auth in authorities:
        responsible_for = kg.get_related_entities(auth.id, relation_type='zuständig_für')
        if responsible_for:
            print(f"• {auth.name} отвечает за:")
            for service in responsible_for:
                print(f"  - {service.name}")
    
    # Запрос 4: Cypher-подобный запрос
    print("\n--- Запрос 4: Cypher-like Query ---")
    print("MATCH (p:Paragraph)-[:belongs_to]->(g:Gesetz) RETURN p, g")
    
    results = query_engine.cypher_like_query(
        "MATCH (p:Paragraph)-[:belongs_to]->(g:Gesetz) RETURN p, g"
    )
    
    for result in results[:5]:
        print(f"• Параграф: {result['p']['name']} → Закон: {result['g']['name']}")
    
    # Запрос 5: Найти путь между сущностями
    print("\n--- Запрос 5: Путь между сущностями ---")
    
    # Найти §29 и Bezirk
    para_29 = query_engine.find_entities_by_name("§29")
    bezirk = query_engine.find_entities_by_name("Bezirk")
    
    if para_29 and bezirk:
        path = kg.find_path(para_29[0].id, bezirk[0].id, max_length=5)
        if path:
            print(f"Найден путь между {para_29[0].name} и {bezirk[0].name}:")
            for entity_id in path:
                entity = kg.get_entity(entity_id)
                print(f"  → {entity.name}")


# ============================================================================
# ПРИМЕР 5: АНАЛИТИКА ГРАФА
# ============================================================================

def example_5_graph_analytics(kg):
    """Аналитика графа знаний"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 5: Аналитика графа знаний")
    print("=" * 80)
    
    analytics = GraphAnalytics(kg)
    
    # Наиболее связанные сущности
    print("\n--- Топ-10 наиболее связанных сущностей ---")
    most_connected = analytics.get_most_connected_entities(top_n=10)
    for entity, degree in most_connected:
        print(f"• {entity.name} ({entity.type}): {degree} связей")
    
    # Центральные сущности (PageRank)
    print("\n--- Топ-5 центральных сущностей (PageRank) ---")
    central = analytics.get_central_entities('pagerank', top_n=5)
    for entity, score in central:
        print(f"• {entity.name}: {score:.4f}")
    
    # Обнаружение сообществ
    print("\n--- Обнаружение сообществ ---")
    communities = analytics.detect_communities('louvain')
    print(f"Обнаружено {len(communities)} сообществ:")
    for comm_name, entities in list(communities.items())[:3]:
        print(f"\n{comm_name} ({len(entities)} сущностей):")
        for entity in entities[:5]:
            print(f"  • {entity.name} ({entity.type})")
    
    # Рекомендации по улучшению
    print("\n--- Рекомендации по улучшению графа ---")
    recommendations = analytics.generate_recommendations()
    for category, recs in recommendations.items():
        if recs:
            print(f"\n{category}:")
            for rec in recs:
                print(f"  • {rec}")


# ============================================================================
# ПРИМЕР 6: ПОИСК ДОКУМЕНТОВ
# ============================================================================

def example_6_document_search(sgb_domain):
    """Поиск документов"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 6: Поиск документов")
    print("=" * 80)
    
    search_engine = sgb_domain.search_engine
    
    # Пример 1: Простой полнотекстовый поиск
    print("\n--- Поиск 1: Простой поиск ---")
    print("Запрос: 'Persönliches Budget'")
    
    results = search_engine.search(
        query="Persönliches Budget",
        search_type='full_text',
        limit=5
    )
    
    print(f"Найдено документов: {results['total_count']}")
    for i, doc in enumerate(results['results'], 1):
        print(f"\n{i}. {doc['title']}")
        print(f"   Тип: {doc['document_type']}")
        print(f"   Релевантность: {doc['score']:.4f}")
        if doc.get('highlights'):
            print(f"   Выдержка: {doc['highlights'][:200]}...")
    
    # Пример 2: Поиск с операторами
    print("\n\n--- Поиск 2: С булевыми операторами ---")
    print("Запрос: 'SGB-IX AND Paragraph NOT Widerspruch'")
    
    results = search_engine.search(
        query="SGB-IX AND Paragraph NOT Widerspruch",
        search_type='full_text',
        limit=5
    )
    
    for i, doc in enumerate(results['results'], 1):
        print(f"{i}. {doc['title']} (score: {doc['score']:.4f})")
    
    # Пример 3: Поиск по полю
    print("\n\n--- Поиск 3: Поиск по полю ---")
    print("Запрос: 'title:Widerspruch'")
    
    results = search_engine.search(
        query="title:Widerspruch",
        search_type='full_text',
        limit=5
    )
    
    for i, doc in enumerate(results['results'], 1):
        print(f"{i}. {doc['title']}")
    
    # Пример 4: Фасетный поиск
    print("\n\n--- Поиск 4: Фасетный поиск ---")
    print("Запрос: 'SGB-IX' с фасетами")
    
    results = search_engine.search(
        query="SGB-IX",
        search_type='faceted',
        limit=10
    )
    
    print(f"\nНайдено: {results['total_count']} документов")
    
    if results['facets']:
        print("\nФасеты:")
        for facet_name, facet_values in results['facets'].items():
            print(f"\n{facet_name}:")
            for value, count in facet_values.items():
                print(f"  • {value}: {count}")
    
    # Пример 5: Семантический поиск
    print("\n\n--- Поиск 5: Семантический поиск ---")
    print("Запрос: 'Как получить помощь для инвалидов?'")
    
    results = search_engine.search(
        query="Wie bekomme ich Hilfe für Menschen mit Behinderungen?",
        search_type='semantic',
        limit=5
    )
    
    for i, doc in enumerate(results['results'], 1):
        print(f"{i}. {doc.get('title', 'N/A')} (similarity: {doc.get('similarity_score', 0):.4f})")
    
    # Пример 6: Гибридный поиск
    print("\n\n--- Поиск 6: Гибридный поиск ---")
    print("Запрос: 'Teilhabe Leistungen'")
    
    results = search_engine.search(
        query="Teilhabe Leistungen",
        search_type='hybrid',
        ranking='hybrid',
        limit=5
    )
    
    for i, doc in enumerate(results['results'], 1):
        print(f"{i}. {doc.get('title', 'N/A')}")
        print(f"   FT Score: {doc.get('ft_score', 0):.4f}")
        print(f"   Sem Score: {doc.get('sem_score', 0):.4f}")
        print(f"   Combined: {doc.get('score', 0):.4f}")
    
    # Пример 7: Автодополнение
    print("\n\n--- Автодополнение ---")
    print("Префикс: 'Pers'")
    
    suggestions = search_engine.suggest("Pers", max_suggestions=5)
    for suggestion in suggestions:
        print(f"• {suggestion['term']} (частота: {suggestion['frequency']})")


# ============================================================================
# ПРИМЕР 7: РАБОТА С КОНТЕКСТАМИ
# ============================================================================

def example_7_context_management(context_manager, sgb_domain):
    """Работа с контекстами"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 7: Работа с контекстами")
    print("=" * 80)
    
    # Создать контекст для конкретного дела
    print("\n--- Создание контекста для судебного дела ---")
    
    case_context = context_manager.create_context(
        name="Дело S 12/2024 - Персональный бюджет",
        context_type=ContextType.LEGAL_CASE,
        description="Судебное дело по отказу в персональном бюджете",
        active_domains=['SGB-IX'],
        properties={
            'case_number': 'S 12/2024',
            'court': 'Sozialgericht München',
            'plaintiff': 'Max Mustermann',
            'defendant': 'Bezirk Oberbayern',
            'date_filed': '2024-11-25'
        }
    )
    
    print(f"✓ Создан контекст: {case_context.name}")
    print(f"  ID: {case_context.id}")
    print(f"  Тип: {case_context.type.value}")
    
    # Переключиться на контекст
    print("\n--- Переключение контекста ---")
    
    state = context_manager.switch_context(case_context.id)
    
    print(f"✓ Переключено на контекст: {case_context.name}")
    print(f"  Активные домены: {state['context']['active_domains']}")
    print(f"  Активные документы: {len(state['context']['active_documents'])}")
    
    # Добавить документы в контекст
    print("\n--- Добавление документов в контекст ---")
    
    relevant_docs = [
        "doc_widerspruch_2024",
        "doc_bescheid_ablehnung",
        "doc_antrag_pb"
    ]
    
    for doc_id in relevant_docs:
        context_manager.add_to_context('document', doc_id)
        print(f"✓ Добавлен документ: {doc_id}")
    
    # Добавить поисковые запросы
    print("\n--- История поисковых запросов ---")
    
    searches = [
        "§29 SGB IX Persönliches Budget",
        "Zuständigkeit Bezirk",
        "Widerspruchsfrist"
    ]
    
    for search_query in searches:
        context_manager.add_to_context('search', search_query)
        print(f"✓ Поиск: {search_query}")
    
    # Получить рекомендации на основе контекста
    print("\n--- Рекомендации на основе контекста ---")
    
    recommendations = context_manager.get_context_recommendations()
    for rec in recommendations:
        print(f"\n{rec['type']}:")
        if rec['type'] == 'related_searches':
            for search in rec['searches']:
                print(f"  • {search}")
        else:
            print(f"  • {rec.get('suggestion', 'N/A')}")
    
    # История переключений контекста
    print("\n--- История контекстов ---")
    
    history = context_manager.get_context_history(limit=5)
    for item in history:
        ctx = item['context']
        print(f"• {ctx['name']} ({ctx['type']}) - {item['accessed_at']}")


# ============================================================================
# ПРИМЕР 8: ВИЗУАЛИЗАЦИЯ ГРАФА
# ============================================================================

def example_8_graph_visualization(kg, output_dir="/tmp/ios_visualizations"):
    """Визуализация графа знаний"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 8: Визуализация графа знаний")
    print("=" * 80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    viz = GraphVisualization(kg)
    
    # 1. Полный граф
    print("\n--- Визуализация полного графа ---")
    viz.visualize_full_graph(
        output_file=f"{output_dir}/full_graph.html",
        layout='spring'
    )
    print(f"✓ Сохранено: {output_dir}/full_graph.html")
    
    # 2. Подграф вокруг сущности
    print("\n--- Визуализация подграфа вокруг §29 ---")
    
    # Найти §29
    query_engine = GraphQueryEngine(kg)
    para_29 = query_engine.find_entities_by_name("§29")
    
    if para_29:
        viz.visualize_entity_neighborhood(
            entity_id=para_29[0].id,
            max_distance=2,
            output_file=f"{output_dir}/para_29_neighborhood.html"
        )
        print(f"✓ Сохранено: {output_dir}/para_29_neighborhood.html")
    
    # 3. Распределение типов сущностей
    print("\n--- График распределения типов сущностей ---")
    viz.create_entity_type_distribution_chart(
        output_file=f"{output_dir}/entity_distribution.html"
    )
    print(f"✓ Сохранено: {output_dir}/entity_distribution.html")
    
    # 4. Распределение типов отношений
    print("\n--- График распределения типов отношений ---")
    viz.create_relation_type_distribution_chart(
        output_file=f"{output_dir}/relation_distribution.html"
    )
    print(f"✓ Сохранено: {output_dir}/relation_distribution.html")
    
    # 5. Рост графа во времени
    print("\n--- График роста графа ---")
    viz.create_temporal_growth_chart(
        output_file=f"{output_dir}/temporal_growth.html"
    )
    print(f"✓ Сохранено: {output_dir}/temporal_growth.html")
    
    # 6. Визуализация сообществ
    print("\n--- Визуализация сообществ ---")
    viz.create_community_visualization(
        algorithm='louvain',
        output_file=f"{output_dir}/communities.html"
    )
    print(f"✓ Сохранено: {output_dir}/communities.html")
    
    # 7. Экспорт для Gephi
    print("\n--- Экспорт для Gephi ---")
    viz.export_to_gephi(
        output_file=f"{output_dir}/knowledge_graph.gexf"
    )
    print(f"✓ Сохранено: {output_dir}/knowledge_graph.gexf")


# ============================================================================
# ПРИМЕР 9: КОМПЛЕКСНЫЙ WORKFLOW
# ============================================================================

def example_9_complete_workflow():
    """Комплексный workflow: от документа до инсайтов"""
    
    print("\n" + "=" * 80)
    print("ПРИМЕР 9: Комплексный workflow")
    print("=" * 80)
    
    # Сценарий: Пользователь получил отказ и готовит возражение
    
    print("\n=== СЦЕНАРИЙ: Подготовка возражения ===\n")
    
    # Шаг 1: Инициализация
    print("Шаг 1: Инициализация системы...")
    ios_root, sgb_domain, _, context_manager = example_1_initialize_ios()
    
    # Шаг 2: Создать контекст для работы
    print("\nШаг 2: Создание контекста работы...")
    work_context = context_manager.create_context(
        name="Подготовка возражения",
        context_type=ContextType.WORK,
        description="Работа над возражением на отказ в персональном бюджете"
    )
    context_manager.switch_context(work_context.id)
    
    # Шаг 3: Загрузить документ с отказом
    print("\nШаг 3: Загрузка и анализ документа с отказом...")
    
    bescheid_doc = Document(
        id="bescheid_ablehnung_20241115",
        title="Bescheid über Ablehnung Persönliches Budget",
        content='''
        Bescheid
        
        Das Sozialamt München lehnt Ihren Antrag auf Persönliches Budget
        gemäß § 29 SGB IX vom 01.10.2024 ab.
        
        Begründung:
        Die Voraussetzungen für die Gewährung eines Persönlichen Budgets
        sind nicht erfüllt. Die beantragten Leistungen können im Rahmen
        der Sachleistungen erbracht werden.
        
        Rechtsbehelfsbelehrung:
        Gegen diesen Bescheid kann innerhalb eines Monats nach Bekanntgabe
        Widerspruch eingelegt werden.
        
        München, den 15.11.2024
        Sozialamt München
        ''',
        file_path="/documents/bescheid_ablehnung.pdf",
        creation_date=datetime(2024, 11, 15)
    )
    
    # Классификация
    classifier = ClassificationEngine(sgb_domain)
    classification = classifier.classify(bescheid_doc)
    print(f"  Тип: {classification.document_type}")
    print(f"  Категория: {classification.category}")
    
    # Добавить в домен
    sgb_domain.add_document(bescheid_doc)
    context_manager.add_to_context('document', bescheid_doc.id)
    
    # Шаг 4: Поиск релевантной информации
    print("\nШаг 4: Поиск релевантной правовой информации...")
    
    search_queries = [
        "§29 SGB IX Voraussetzungen",
        "Persönliches Budget Rechtsanspruch",
        "Widerspruch gegen Ablehnung"
    ]
    
    relevant_info = []
    search_engine = sgb_domain.search_engine
    
    for query in search_queries:
        print(f"\n  Поиск: '{query}'")
        results = search_engine.search(query, limit=3)
        
        for doc in results['results']:
            print(f"    • {doc['title']} (score: {doc['score']:.3f})")
            relevant_info.append(doc)
        
        context_manager.add_to_context('search', query)
    
    # Шаг 5: Анализ графа знаний
    print("\nШаг 5: Анализ связей в графе знаний...")
    
    kg = sgb_domain.knowledge_graph
    query_engine = GraphQueryEngine(kg)
    
    # Найти §29
    para_29 = query_engine.find_entities_by_name("§29")
    
    if para_29:
        print(f"\n  Найден: {para_29[0].name}")
        
        # Найти связанные параграфы
        related = kg.get_related_entities(para_29[0].id, relation_type='verweist_auf')
        print(f"\n  Связанные параграфы:")
        for entity in related:
            print(f"    • {entity.name}: {entity.properties.get('title', 'N/A')}")
    
    # Шаг 6: Генерация структуры возражения
    print("\nШаг 6: Генерация структуры возражения...")
    
    widerspruch_structure = {
        'Adressat': 'Sozialamt München',
        'Betreff': 'Widerspruch gegen Bescheid vom 15.11.2024',
        'Abschnitte': [
            {
                'titel': 'Einleitung',
                'inhalt': 'Hiermit widerspreche ich dem Bescheid...'
            },
            {
                'titel': 'Rechtliche Grundlagen',
                'inhalt': [
                    '§ 29 SGB IX - Rechtsanspruch auf Persönliches Budget',
                    'Voraussetzungen sind erfüllt',
                    'Verweise auf verwandte Paragrafen'
                ]
            },
            {
                'titel': 'Begründung',
                'inhalt': [
                    'Sachleistungen ungeeignet',
                    'Persönliches Budget ermöglicht bessere Teilhabe',
                    'Wunsch- und Wahlrecht nach § 8 SGB IX'
                ]
            },
            {
                'titel': 'Antrag',
                'inhalt': 'Aufhebung des Bescheids und Bewilligung des Budgets'
            }
        ]
    }
    
    print("\n  Struktur возражения:")
    for section in widerspruch_structure['Abschnitte']:
        print(f"    • {section['titel']}")
    
    # Шаг 7: Создать документ возражения
    print("\nШаг 7: Создание документа возражения...")
    
    widerspruch_doc = Document(
        id="widerspruch_20241120",
        title="Widerspruch gegen Bescheid vom 15.11.2024",
        content='''
        [Автоматически сгенерированное возражение на основе анализа]
        
        Sozialamt München
        
        Widerspruch gegen Bescheid vom 15.11.2024
        
        Sehr geehrte Damen und Herren,
        
        hiermit widerspreche ich dem Bescheid vom 15.11.2024 über die Ablehnung
        des Persönlichen Budgets gemäß § 29 SGB IX.
        
        [... полное содержание возражения ...]
        ''',
        file_path="/documents/widerspruch_generated.pdf",
        creation_date=datetime.now()
    )
    
    sgb_domain.add_document(widerspruch_doc)
    context_manager.add_to_context('document', widerspruch_doc.id)
    
    print(f"  ✓ Документ создан: {widerspruch_doc.title}")
    
    # Шаг 8: Сохранить контекст работы
    print("\nШаг 8: Сохранение контекста работы...")
    context_manager.save_current_state()
    print("  ✓ Контекст сохранен")
    
    # Шаг 9: Генерация отчета
    print("\nШаг 9: Генерация отчета о проделанной работе...")
    
    report = {
        'date': datetime.now().isoformat(),
        'context': work_context.name,
        'documents_processed': 2,
        'searches_performed': len(search_queries),
        'entities_extracted': len(kg.entity_index),
        'knowledge_connections': len(kg.relation_index),
        'output_document': widerspruch_doc.title
    }
    
    print("\n  === ОТЧЕТ ===")
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    print("\n✓ Workflow завершен успешно!")


# ============================================================================
# MAIN: Запуск всех примеров
# ============================================================================

def main():
    """Запуск всех примеров"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     INFORMATION OPERATING SYSTEM (IOS) - DEMO EXAMPLES         ║
    ║                                                                 ║
    ║  Комплексная демонстрация всех возможностей системы            ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Пример 1: Инициализация
    ios_root, sgb_domain, medical_domain, context_manager = example_1_initialize_ios()
    
    # Пример 2: Классификация документов
    example_2_document_classification(sgb_domain)
    
    # Пример 3: Построение графа знаний
    kg = example_3_knowledge_graph_construction(sgb_domain)
    
    # Пример 4: Запросы к графу
    example_4_graph_queries(kg)
    
    # Пример 5: Аналитика
    example_5_graph_analytics(kg)
    
    # Пример 6: Поиск
    example_6_document_search(sgb_domain)
    
    # Пример 7: Контексты
    example_7_context_management(context_manager, sgb_domain)
    
    # Пример 8: Визуализация
    example_8_graph_visualization(kg)
    
    # Пример 9: Комплексный workflow
    example_9_complete_workflow()
    
    print("""
    
    ╔════════════════════════════════════════════════════════════════╗
    ║                    ВСЕ ПРИМЕРЫ ЗАВЕРШЕНЫ                        ║
    ╚════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()