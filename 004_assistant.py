Пользователь хочет максимально детальную разработку всех компонентов Information Operating System (IOS). Он просит все пункты, все варианты максимально подробно, детально, грамотно и по порядку.

Это масштабная задача. Мне нужно создать полноценную техническую документацию системы, включающую:

1. Automatic Classifier для SGB документов
2. Knowledge Graph Engine для связывания законов
3. Context Manager для переключения между проектами
4. Search Engine с семантическим поиском
5. Все остальные компоненты из предыдущего ответа

Учитывая объём материала, это будет очень большой документ. Я должен структурировать его максимально логично и подробно, с кодом, схемами, примерами.

Максу нужна полноценная спецификация системы, которую он сможет использовать для реализации. Учитывая его опыт в разработке (Android приложения, веб-платформы, Knowledge OS), он оценит детальный технический подход.

Создам комплексный документ, разбитый на логические разделы.# INFORMATION OPERATING SYSTEM (IOS) - Полная техническая спецификация

---

# ЧАСТЬ 1: АРХИТЕКТУРА СИСТЕМЫ

## 1.1 Общая архитектура (4-уровневая пирамида)

```
                     ┌──────────────────┐
                     │  LEVEL 1: ROOT   │  ← Единая точка входа
                     │   (Вершина)      │
                     └────────┬─────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │    LEVEL 2: DOMAINS & PROJECTS    │  ← Тематические кластеры
            │         (Средний уровень)         │
            └─────────────────┬─────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │  LEVEL 3: METADATA & NAVIGATION LAYER    │  ← Метаданные, индексы
        │         (Организационный слой)            │
        └─────────────────────┬───────────────────┘
                              │
    ┌─────────────────────────┴──────────────────────────┐
    │   LEVEL 4: RAW DATA STORAGE (Фундамент)           │  ← Документы, файлы
    │        (Хранилище информации)                      │
    └────────────────────────────────────────────────────┘
```

### 1.1.1 Детальное описание уровней

#### LEVEL 1 - ROOT (Корень системы)
**Назначение:** Единая точка доступа ко всей информационной системе

**Компоненты:**
- **Global Index** - Главный индекс всех документов
- **Master Ontology** - Общая онтология знаний
- **System Registry** - Реестр всех подсистем
- **Access Control Hub** - Центр управления доступом

**Файловая структура:**
```
/IOS-ROOT/
├── global-index.db              # Главный индекс (SQLite)
├── master-ontology.json         # Глобальная онтология
├── system-registry.yaml         # Реестр подсистем
├── config/
│   ├── domains.config           # Конфигурация доменов
│   ├── plugins.config           # Конфигурация плагинов
│   └── security.config          # Настройки безопасности
└── logs/
    ├── system.log               # Системный лог
    ├── access.log               # Лог доступа
    └── errors.log               # Лог ошибок
```

**Интерфейс ROOT:**
```python
class IOSRoot:
    """Главный интерфейс системы - точка входа"""
    
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.global_index = GlobalIndex(f"{root_path}/global-index.db")
        self.ontology = MasterOntology(f"{root_path}/master-ontology.json")
        self.registry = SystemRegistry(f"{root_path}/system-registry.yaml")
        self.access_control = AccessControlHub(f"{root_path}/config/security.config")
        
    def search(self, query: str, context: dict = None) -> List[Document]:
        """Глобальный поиск по всей системе"""
        return self.global_index.search(query, context)
    
    def get_domain(self, domain_name: str) -> Domain:
        """Получить домен знаний"""
        return self.registry.get_domain(domain_name)
    
    def list_domains(self) -> List[str]:
        """Список всех доменов"""
        return self.registry.list_domains()
    
    def create_domain(self, name: str, config: dict) -> Domain:
        """Создать новый домен"""
        domain = Domain(name, config)
        self.registry.register_domain(domain)
        return domain
```

---

#### LEVEL 2 - DOMAINS & PROJECTS (Домены и проекты)
**Назначение:** Организация знаний по тематическим областям и активным проектам

**Типы доменов:**
1. **Knowledge Domain** - постоянная область знаний (SGB-IX, медицина, техника)
2. **Project Domain** - временная рабочая область (дело в суде, бюджет 2025)
3. **Context Domain** - контекстная область (личное, работа, исследования)

**Файловая структура домена:**
```
/IOS-ROOT/domains/SGB-IX/
├── domain.config                # Конфигурация домена
├── metadata/                    # Метаданные домена
│   ├── taxonomy.json            # Таксономия (иерархия понятий)
│   ├── entity-types.json        # Типы сущностей (законы, параграфы)
│   ├── relation-types.json      # Типы отношений (ссылается, отменяет)
│   └── templates/               # Шаблоны документов
│       ├── widerspruch.template
│       ├── antrag.template
│       └── beschwerde.template
├── knowledge-graph/             # Граф знаний домена
│   ├── entities.db              # База сущностей
│   ├── relations.db             # База отношений
│   └── graph.json               # Граф в JSON
├── indexes/                     # Индексы для быстрого поиска
│   ├── full-text.index          # Полнотекстовый индекс
│   ├── entity.index             # Индекс сущностей
│   └── date.index               # Индекс по датам
├── cache/                       # Кэш часто используемых данных
│   └── hot-documents.cache
└── data/                        # Сырые данные (переход к Level 4)
```

**Класс Domain:**
```python
class Domain:
    """Представляет тематический домен знаний"""
    
    def __init__(self, name: str, path: str, config: dict):
        self.name = name
        self.path = path
        self.config = config
        
        # Загрузка компонентов
        self.taxonomy = Taxonomy(f"{path}/metadata/taxonomy.json")
        self.entity_types = EntityTypes(f"{path}/metadata/entity-types.json")
        self.knowledge_graph = KnowledgeGraph(f"{path}/knowledge-graph")
        self.search_engine = DomainSearchEngine(f"{path}/indexes")
        self.cache = DomainCache(f"{path}/cache")
        
    def add_document(self, document: Document) -> None:
        """Добавить документ в домен"""
        # 1. Классифицировать документ
        classification = self.classify(document)
        
        # 2. Извлечь сущности и отношения
        entities = self.extract_entities(document)
        relations = self.extract_relations(document, entities)
        
        # 3. Обновить граф знаний
        self.knowledge_graph.add_entities(entities)
        self.knowledge_graph.add_relations(relations)
        
        # 4. Проиндексировать
        self.search_engine.index_document(document, classification)
        
        # 5. Сохранить документ
        storage_path = self.get_storage_path(classification)
        document.save(storage_path)
        
    def classify(self, document: Document) -> Classification:
        """Классифицировать документ"""
        classifier = DomainClassifier(self)
        return classifier.classify(document)
    
    def extract_entities(self, document: Document) -> List[Entity]:
        """Извлечь сущности из документа"""
        extractor = EntityExtractor(self.entity_types)
        return extractor.extract(document)
    
    def extract_relations(self, document: Document, entities: List[Entity]) -> List[Relation]:
        """Извлечь отношения между сущностями"""
        extractor = RelationExtractor(self.relation_types)
        return extractor.extract(document, entities)
```

---

#### LEVEL 3 - METADATA & NAVIGATION (Метаданные и навигация)
**Назначение:** Организация, описание и навигация по информации

**Ключевые компоненты:**

**1. Taxonomy (Таксономия)**
```json
{
  "name": "SGB-IX Taxonomy",
  "version": "1.0",
  "hierarchy": {
    "SGB-IX": {
      "type": "domain",
      "children": {
        "Teilhabe": {
          "type": "category",
          "description": "Teilhabe und Rehabilitation",
          "children": {
            "Persönliches Budget": {
              "type": "subcategory",
              "paragraphs": ["§29", "§30"],
              "related_laws": ["SGB-XII", "SGB-XI"]
            },
            "Assistenz": {
              "type": "subcategory",
              "paragraphs": ["§78", "§79"]
            }
          }
        },
        "Leistungen": {
          "type": "category",
          "children": {
            "Medizinische Rehabilitation": {},
            "Teilhabe am Arbeitsleben": {},
            "Teilhabe an Bildung": {}
          }
        }
      }
    }
  }
}
```

**2. Entity Types (Типы сущностей)**
```json
{
  "entity_types": [
    {
      "name": "Gesetz",
      "pattern": "SGB-[IVX]+",
      "properties": ["name", "full_name", "url"],
      "example": "SGB-IX"
    },
    {
      "name": "Paragraph",
      "pattern": "§\\s*\\d+[a-z]?",
      "properties": ["number", "title", "law", "text"],
      "example": "§29"
    },
    {
      "name": "Behörde",
      "pattern": null,
      "properties": ["name", "type", "address", "zuständigkeit"],
      "examples": ["Sozialamt", "Landkreis", "Bezirk"]
    },
    {
      "name": "Person",
      "pattern": null,
      "properties": ["role", "organization"],
      "examples": ["Sachbearbeiter", "Richter", "Gutachter"]
    },
    {
      "name": "Datum",
      "pattern": "\\d{2}\\.\\d{2}\\.\\d{4}",
      "properties": ["date", "event"],
      "example": "01.01.2025"
    }
  ]
}
```

**3. Relation Types (Типы отношений)**
```json
{
  "relation_types": [
    {
      "name": "verweist_auf",
      "source": ["Paragraph", "Gesetz"],
      "target": ["Paragraph", "Gesetz"],
      "description": "Ссылается на другой закон или параграф"
    },
    {
      "name": "ersetzt",
      "source": ["Paragraph", "Gesetz"],
      "target": ["Paragraph", "Gesetz"],
      "description": "Заменяет/отменяет предыдущую версию"
    },
    {
      "name": "konkretisiert",
      "source": ["Paragraph"],
      "target": ["Paragraph"],
      "description": "Конкретизирует общую норму"
    },
    {
      "name": "zuständig_für",
      "source": ["Behörde"],
      "target": ["Leistung"],
      "description": "Отвечает за предоставление услуги"
    }
  ]
}
```

**Класс Metadata Manager:**
```python
class MetadataManager:
    """Управление всеми метаданными домена"""
    
    def __init__(self, domain_path: str):
        self.taxonomy = self.load_taxonomy(f"{domain_path}/metadata/taxonomy.json")
        self.entity_types = self.load_entity_types(f"{domain_path}/metadata/entity-types.json")
        self.relation_types = self.load_relation_types(f"{domain_path}/metadata/relation-types.json")
        
    def get_category_path(self, document: Document) -> str:
        """Определить путь в таксономии для документа"""
        # Анализ содержимого документа
        keywords = self.extract_keywords(document)
        entities = self.extract_entities(document)
        
        # Поиск наилучшего соответствия в таксономии
        best_match = self.taxonomy.find_best_match(keywords, entities)
        
        return best_match.path  # Например: "SGB-IX/Teilhabe/Persönliches Budget"
    
    def generate_metadata(self, document: Document) -> dict:
        """Генерация метаданных для документа"""
        return {
            "title": self.extract_title(document),
            "category": self.get_category_path(document),
            "entities": self.extract_entities(document),
            "keywords": self.extract_keywords(document),
            "summary": self.generate_summary(document),
            "date_created": document.creation_date,
            "date_modified": document.modification_date,
            "language": self.detect_language(document),
            "document_type": self.classify_document_type(document),
            "related_documents": self.find_related(document)
        }
```

---

#### LEVEL 4 - RAW DATA STORAGE (Хранилище данных)
**Назначение:** Физическое хранение документов и файлов

**Организация хранилища:**
```
/IOS-ROOT/domains/SGB-IX/data/
├── documents/                   # Документы
│   ├── gesetze/                 # Законы
│   │   ├── SGB-IX/
│   │   │   ├── volltext/        # Полные тексты
│   │   │   │   └── sgb-ix-2024.pdf
│   │   │   └── paragraphen/     # Отдельные параграфы
│   │   │       ├── paragraph-29.md
│   │   │       └── paragraph-30.md
│   │   ├── SGB-XI/
│   │   └── SGB-XII/
│   ├── anträge/                 # Заявления
│   │   ├── 2024/
│   │   └── 2025/
│   ├── bescheide/               # Решения
│   │   ├── bewilligungen/       # Одобрения
│   │   ├── ablehnungen/         # Отказы
│   │   └── teilbewilligungen/   # Частичные одобрения
│   ├── widersprüche/            # Возражения
│   └── gerichtsverfahren/       # Судебные дела
│       ├── klagen/
│       └── urteile/
├── templates/                   # Шаблоны
│   ├── antrag-persönliches-budget.docx
│   ├── widerspruch-standard.docx
│   └── beschwerde-template.docx
├── notes/                       # Заметки
│   ├── meetings/
│   ├── research/
│   └── ideas/
└── media/                       # Медиа файлы
    ├── images/
    ├── audio/
    └── video/
```

**Класс Data Storage:**
```python
class DataStorage:
    """Управление физическим хранилищем данных"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.file_index = FileIndex(f"{storage_path}/.index.db")
        
    def store_document(self, document: Document, metadata: dict) -> str:
        """Сохранить документ и вернуть путь"""
        # Определить путь на основе метаданных
        storage_path = self.calculate_path(metadata)
        
        # Создать директории если нужно
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Сохранить документ
        document.save(storage_path)
        
        # Обновить индекс
        self.file_index.add_entry(storage_path, metadata)
        
        # Создать резервную копию
        self.create_backup(storage_path)
        
        return storage_path
    
    def calculate_path(self, metadata: dict) -> str:
        """Вычислить путь для хранения на основе метаданных"""
        category = metadata.get('category', 'uncategorized')
        doc_type = metadata.get('document_type', 'document')
        date = metadata.get('date_created', datetime.now())
        
        # Пример: /data/documents/anträge/2025/antrag-pb-2025-01-15.pdf
        return os.path.join(
            self.storage_path,
            'documents',
            category,
            str(date.year),
            f"{doc_type}-{date.strftime('%Y-%m-%d')}.{metadata.get('format', 'pdf')}"
        )
```

---

## 1.2 Системная шина данных (Data Bus)

**Аналог:** Системная шина в компьютере (связывает CPU, RAM, диски)

**Назначение:** Обеспечение обмена данными между всеми компонентами системы

```python
class DataBus:
    """Системная шина для передачи данных между компонентами"""
    
    def __init__(self):
        self.subscribers = {}  # Подписчики на события
        self.message_queue = queue.Queue()  # Очередь сообщений
        self.running = False
        
    def publish(self, event_type: str, data: dict):
        """Публикация события в шину"""
        event = {
            'type': event_type,
            'timestamp': datetime.now(),
            'data': data
        }
        self.message_queue.put(event)
        
    def subscribe(self, event_type: str, callback: Callable):
        """Подписка на события определенного типа"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def start(self):
        """Запустить обработку событий"""
        self.running = True
        while self.running:
            try:
                event = self.message_queue.get(timeout=1)
                self._dispatch_event(event)
            except queue.Empty:
                continue
                
    def _dispatch_event(self, event: dict):
        """Отправить событие всем подписчикам"""
        event_type = event['type']
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logging.error(f"Error in event handler: {e}")

# Примеры событий
EVENTS = {
    'DOCUMENT_ADDED': 'document.added',
    'DOCUMENT_UPDATED': 'document.updated',
    'DOCUMENT_DELETED': 'document.deleted',
    'ENTITY_EXTRACTED': 'entity.extracted',
    'RELATION_CREATED': 'relation.created',
    'SEARCH_PERFORMED': 'search.performed',
    'INDEX_UPDATED': 'index.updated'
}
```

---

# ЧАСТЬ 2: КОМПОНЕНТ 1 - AUTOMATIC CLASSIFIER

## 2.1 Архитектура классификатора

```
┌─────────────────────────────────────────────────────────┐
│              AUTOMATIC CLASSIFIER                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Feature    │  │ Classification│  │   Training   │  │
│  │  Extractor   │→│    Engine     │←│    Module    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  ↑          │
│         ↓                  ↓                  │          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Text       │  │  Rule-Based  │  │   Training   │  │
│  │  Processing  │  │  Classifier  │  │    Data      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                             │
│         ↓                  ↓                             │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │   ML-Based   │  │  Confidence  │                    │
│  │  Classifier  │  │   Scorer     │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## 2.2 Feature Extractor (Извлечение признаков)

```python
class FeatureExtractor:
    """Извлечение признаков из документов для классификации"""
    
    def __init__(self, domain_config: dict):
        self.domain_config = domain_config
        self.stopwords = self.load_stopwords()
        self.entity_patterns = self.load_entity_patterns()
        
    def extract_features(self, document: Document) -> dict:
        """Извлечь все признаки документа"""
        
        text = document.get_text()
        
        features = {
            # Текстовые признаки
            'text_features': self.extract_text_features(text),
            
            # Структурные признаки
            'structure_features': self.extract_structure_features(document),
            
            # Сущности
            'entity_features': self.extract_entity_features(text),
            
            # Метаданные
            'metadata_features': self.extract_metadata_features(document),
            
            # Статистические признаки
            'statistical_features': self.extract_statistical_features(text)
        }
        
        return features
    
    def extract_text_features(self, text: str) -> dict:
        """Извлечь текстовые признаки"""
        
        # Токенизация
        tokens = self.tokenize(text)
        
        # Удаление стоп-слов
        filtered_tokens = [t for t in tokens if t.lower() not in self.stopwords]
        
        # N-граммы
        bigrams = self.get_ngrams(filtered_tokens, 2)
        trigrams = self.get_ngrams(filtered_tokens, 3)
        
        # TF-IDF
        tf_idf = self.calculate_tfidf(filtered_tokens)
        
        return {
            'tokens': filtered_tokens,
            'unique_tokens': list(set(filtered_tokens)),
            'bigrams': bigrams,
            'trigrams': trigrams,
            'tf_idf_top_10': sorted(tf_idf.items(), key=lambda x: x[1], reverse=True)[:10],
            'keywords': self.extract_keywords(text)
        }
    
    def extract_structure_features(self, document: Document) -> dict:
        """Извлечь структурные признаки"""
        
        return {
            'has_header': self.detect_header(document),
            'has_footer': self.detect_footer(document),
            'num_sections': self.count_sections(document),
            'num_paragraphs': self.count_paragraphs(document),
            'num_pages': document.page_count,
            'has_signature': self.detect_signature(document),
            'has_date': self.detect_date(document),
            'has_reference_number': self.detect_reference_number(document),
            'document_layout': self.analyze_layout(document)
        }
    
    def extract_entity_features(self, text: str) -> dict:
        """Извлечь признаки на основе сущностей"""
        
        entities = {
            'gesetze': [],      # Законы (SGB-IX, SGB-XII)
            'paragraphen': [],  # Параграфы (§29, §30)
            'behörden': [],     # Органы власти
            'personen': [],     # Персоны
            'datum': [],        # Даты
            'geld': []          # Суммы денег
        }
        
        # Поиск законов
        gesetz_pattern = r'SGB[- ]?([IVX]+)'
        entities['gesetze'] = re.findall(gesetz_pattern, text)
        
        # Поиск параграфов
        paragraph_pattern = r'§\s*(\d+[a-z]?)'
        entities['paragraphen'] = re.findall(paragraph_pattern, text)
        
        # Поиск дат
        date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}'
        entities['datum'] = re.findall(date_pattern, text)
        
        # Поиск сумм
        money_pattern = r'(\d+(?:[.,]\d+)?)\s*(?:€|EUR|Euro)'
        entities['geld'] = re.findall(money_pattern, text)
        
        # Поиск органов власти
        behörden_keywords = ['Sozialamt', 'Landkreis', 'Bezirk', 'Sozialgericht', 'Landessozialgericht']
        for keyword in behörden_keywords:
            if keyword.lower() in text.lower():
                entities['behörden'].append(keyword)
        
        return entities
    
    def extract_metadata_features(self, document: Document) -> dict:
        """Извлечь признаки из метаданных"""
        
        return {
            'file_format': document.format,
            'file_size': document.size,
            'creation_date': document.creation_date,
            'modification_date': document.modification_date,
            'author': document.author if hasattr(document, 'author') else None,
            'title': document.title if hasattr(document, 'title') else None
        }
    
    def extract_statistical_features(self, text: str) -> dict:
        """Извлечь статистические признаки"""
        
        words = text.split()
        sentences = self.split_sentences(text)
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_word_ratio': len(set(words)) / len(words) if words else 0,
            'punctuation_count': sum(1 for c in text if c in '.,;:!?'),
            'capital_letter_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0
        }
```

## 2.3 Classification Engine (Движок классификации)

```python
class ClassificationEngine:
    """Главный движок классификации документов"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.rule_based_classifier = RuleBasedClassifier(domain)
        self.ml_classifier = MLClassifier(domain)
        self.feature_extractor = FeatureExtractor(domain.config)
        self.confidence_scorer = ConfidenceScorer()
        
    def classify(self, document: Document) -> Classification:
        """Классифицировать документ"""
        
        # 1. Извлечь признаки
        features = self.feature_extractor.extract_features(document)
        
        # 2. Классификация на основе правил
        rule_result = self.rule_based_classifier.classify(features)
        
        # 3. Классификация на основе ML
        ml_result = self.ml_classifier.classify(features)
        
        # 4. Объединить результаты
        combined_result = self.combine_results(rule_result, ml_result)
        
        # 5. Оценить уверенность
        confidence = self.confidence_scorer.score(combined_result, features)
        
        # 6. Создать финальную классификацию
        classification = Classification(
            document_type=combined_result['document_type'],
            category=combined_result['category'],
            subcategory=combined_result.get('subcategory'),
            tags=combined_result.get('tags', []),
            confidence=confidence,
            metadata=combined_result.get('metadata', {})
        )
        
        return classification
    
    def combine_results(self, rule_result: dict, ml_result: dict) -> dict:
        """Объединить результаты классификации"""
        
        # Если оба метода согласны - отлично
        if rule_result['document_type'] == ml_result['document_type']:
            return {
                **rule_result,
                'agreement': True,
                'confidence_boost': 0.2
            }
        
        # Если не согласны - приоритет правилам при высокой уверенности
        if rule_result['confidence'] > 0.8:
            return {
                **rule_result,
                'agreement': False,
                'ml_alternative': ml_result
            }
        
        # Иначе - ML
        return {
            **ml_result,
            'agreement': False,
            'rule_alternative': rule_result
        }
```

## 2.4 Rule-Based Classifier (Классификатор на правилах)

```python
class RuleBasedClassifier:
    """Классификация на основе экспертных правил"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.rules = self.load_rules()
        
    def load_rules(self) -> List[ClassificationRule]:
        """Загрузить правила классификации"""
        
        rules = []
        
        # Правило 1: Возражение (Widerspruch)
        rules.append(ClassificationRule(
            name="Widerspruch Detection",
            conditions=[
                KeywordCondition(['widerspruch', 'widerspreche'], min_count=1),
                KeywordCondition(['bescheid'], min_count=1),
                EntityCondition('behörden', min_count=1),
                EntityCondition('datum', min_count=1)
            ],
            result={
                'document_type': 'Widerspruch',
                'category': 'Rechtsmittel',
                'confidence': 0.9
            }
        ))
        
        # Правило 2: Заявление (Antrag)
        rules.append(ClassificationRule(
            name="Antrag Detection",
            conditions=[
                KeywordCondition(['antrag', 'beantrage', 'hiermit beantrage'], min_count=1),
                KeywordCondition(['persönliches budget', 'leistung', 'hilfe'], min_count=1),
                NOT(KeywordCondition(['widerspruch']))
            ],
            result={
                'document_type': 'Antrag',
                'category': 'Anträge',
                'confidence': 0.85
            }
        ))
        
        # Правило 3: Решение ведомства (Bescheid)
        rules.append(ClassificationRule(
            name="Bescheid Detection",
            conditions=[
                KeywordCondition(['bescheid', 'bewilligungsbescheid', 'ablehnungsbescheid'], min_count=1),
                StructureCondition('has_signature', True),
                StructureCondition('has_reference_number', True),
                EntityCondition('behörden', min_count=1)
            ],
            result={
                'document_type': 'Bescheid',
                'category': 'Bescheide',
                'confidence': 0.95
            }
        ))
        
        # Правило 4: Судебное решение (Urteil)
        rules.append(ClassificationRule(
            name="Urteil Detection",
            conditions=[
                KeywordCondition(['urteil', 'im namen des volkes', 'beschluss'], min_count=1),
                KeywordCondition(['sozialgericht', 'landessozialgericht'], min_count=1),
                EntityCondition('paragraphen', min_count=3)
            ],
            result={
                'document_type': 'Urteil',
                'category': 'Gerichtsverfahren',
                'subcategory': 'Urteile',
                'confidence': 0.98
            }
        ))
        
        # Правило 5: Закон (Gesetz)
        rules.append(ClassificationRule(
            name="Gesetz Detection",
            conditions=[
                EntityCondition('gesetze', min_count=1),
                EntityCondition('paragraphen', min_count=10),
                KeywordCondition(['sozialgesetzbuch', 'sgb'], min_count=1),
                StructureCondition('num_sections', min_value=5)
            ],
            result={
                'document_type': 'Gesetz',
                'category': 'Gesetze',
                'confidence': 0.95
            }
        ))
        
        return rules
    
    def classify(self, features: dict) -> dict:
        """Применить правила для классификации"""
        
        matches = []
        
        for rule in self.rules:
            if rule.evaluate(features):
                matches.append({
                    'rule_name': rule.name,
                    **rule.result
                })
        
        if not matches:
            return {
                'document_type': 'Unknown',
                'category': 'Uncategorized',
                'confidence': 0.0
            }
        
        # Вернуть наиболее уверенное совпадение
        best_match = max(matches, key=lambda x: x['confidence'])
        return best_match


class ClassificationRule:
    """Правило классификации"""
    
    def __init__(self, name: str, conditions: List, result: dict):
        self.name = name
        self.conditions = conditions
        self.result = result
        
    def evaluate(self, features: dict) -> bool:
        """Проверить, выполняются ли все условия"""
        return all(condition.check(features) for condition in self.conditions)


class KeywordCondition:
    """Условие на наличие ключевых слов"""
    
    def __init__(self, keywords: List[str], min_count: int = 1):
        self.keywords = [k.lower() for k in keywords]
        self.min_count = min_count
        
    def check(self, features: dict) -> bool:
        text_features = features.get('text_features', {})
        tokens = [t.lower() for t in text_features.get('tokens', [])]
        
        count = sum(1 for keyword in self.keywords if keyword in ' '.join(tokens))
        return count >= self.min_count


class EntityCondition:
    """Условие на наличие сущностей"""
    
    def __init__(self, entity_type: str, min_count: int = 1):
        self.entity_type = entity_type
        self.min_count = min_count
        
    def check(self, features: dict) -> bool:
        entity_features = features.get('entity_features', {})
        entities = entity_features.get(self.entity_type, [])
        return len(entities) >= self.min_count


class StructureCondition:
    """Условие на структурные признаки"""
    
    def __init__(self, feature_name: str, expected_value=None, min_value=None):
        self.feature_name = feature_name
        self.expected_value = expected_value
        self.min_value = min_value
        
    def check(self, features: dict) -> bool:
        structure_features = features.get('structure_features', {})
        value = structure_features.get(self.feature_name)
        
        if self.expected_value is not None:
            return value == self.expected_value
        
        if self.min_value is not None:
            return value >= self.min_value
        
        return False


class NOT:
    """Отрицание условия"""
    
    def __init__(self, condition):
        self.condition = condition
        
    def check(self, features: dict) -> bool:
        return not self.condition.check(features)
```

## 2.5 ML-Based Classifier (Классификатор на ML)

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier

class MLClassifier:
    """Классификация на основе машинного обучения"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=2
        )
        
        # Ансамбль классификаторов
        self.classifier = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('nb', MultinomialNB()),
                ('svm', SVC(kernel='linear', probability=True, random_state=42))
            ],
            voting='soft'
        )
        
        self.is_trained = False
        self.label_encoder = {}
        
    def train(self, training_data: List[TrainingExample]):
        """Обучить классификатор"""
        
        # Подготовка данных
        texts = [example.text for example in training_data]
        labels = [example.label for example in training_data]
        
        # Кодирование меток
        unique_labels = list(set(labels))
        self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
        encoded_labels = [self.label_encoder[label] for label in labels]
        
        # Векторизация текстов
        X = self.vectorizer.fit_transform(texts)
        y = np.array(encoded_labels)
        
        # Обучение
        self.classifier.fit(X, y)
        self.is_trained = True
        
        # Сохранение модели
        self.save_model()
        
    def classify(self, features: dict) -> dict:
        """Классифицировать на основе признаков"""
        
        if not self.is_trained:
            return {
                'document_type': 'Unknown',
                'category': 'Uncategorized',
                'confidence': 0.0,
                'error': 'Model not trained'
            }
        
        # Подготовка текста из признаков
        text = self.features_to_text(features)
        
        # Векторизация
        X = self.vectorizer.transform([text])
        
        # Предсказание
        prediction = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        
        # Декодирование метки
        reverse_encoder = {idx: label for label, idx in self.label_encoder.items()}
        predicted_label = reverse_encoder[prediction]
        confidence = probabilities[prediction]
        
        # Разбор метки (формат: "document_type|category|subcategory")
        parts = predicted_label.split('|')
        
        return {
            'document_type': parts[0] if len(parts) > 0 else 'Unknown',
            'category': parts[1] if len(parts) > 1 else 'Uncategorized',
            'subcategory': parts[2] if len(parts) > 2 else None,
            'confidence': float(confidence),
            'all_probabilities': {
                reverse_encoder[idx]: float(prob) 
                for idx, prob in enumerate(probabilities)
            }
        }
    
    def features_to_text(self, features: dict) -> str:
        """Преобразовать признаки в текст для классификации"""
        
        parts = []
        
        # Текстовые признаки
        text_features = features.get('text_features', {})
        if 'tokens' in text_features:
            parts.append(' '.join(text_features['tokens']))
        
        # Ключевые слова (с весом)
        if 'keywords' in text_features:
            keywords_repeated = ' '.join([kw] * 3 for kw in text_features['keywords'])
            parts.append(keywords_repeated)
        
        # Сущности
        entity_features = features.get('entity_features', {})
        for entity_type, entities in entity_features.items():
            if entities:
                parts.append(' '.join([f"{entity_type}_{e}" for e in entities]))
        
        return ' '.join(parts)
    
    def save_model(self):
        """Сохранить обученную модель"""
        import joblib
        
        model_path = f"{self.domain.path}/ml-models"
        os.makedirs(model_path, exist_ok=True)
        
        joblib.dump(self.classifier, f"{model_path}/classifier.pkl")
        joblib.dump(self.vectorizer, f"{model_path}/vectorizer.pkl")
        joblib.dump(self.label_encoder, f"{model_path}/label_encoder.pkl")
        
    def load_model(self):
        """Загрузить обученную модель"""
        import joblib
        
        model_path = f"{self.domain.path}/ml-models"
        
        if os.path.exists(f"{model_path}/classifier.pkl"):
            self.classifier = joblib.load(f"{model_path}/classifier.pkl")
            self.vectorizer = joblib.load(f"{model_path}/vectorizer.pkl")
            self.label_encoder = joblib.load(f"{model_path}/label_encoder.pkl")
            self.is_trained = True
```

## 2.6 Training Module (Модуль обучения)

```python
class TrainingModule:
    """Модуль для обучения и улучшения классификатора"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.ml_classifier = MLClassifier(domain)
        self.training_data = []
        
    def collect_training_data(self) -> List[TrainingExample]:
        """Собрать обучающие данные"""
        
        training_examples = []
        
        # 1. Из уже классифицированных документов
        classified_docs = self.domain.get_classified_documents()
        for doc in classified_docs:
            example = TrainingExample(
                text=doc.get_text(),
                label=f"{doc.document_type}|{doc.category}|{doc.subcategory or ''}",
                source='manual_classification'
            )
            training_examples.append(example)
        
        # 2. Из шаблонов
        templates = self.domain.get_templates()
        for template in templates:
            example = TrainingExample(
                text=template.get_text(),
                label=f"{template.document_type}|{template.category}|",
                source='template'
            )
            training_examples.append(example)
        
        # 3. Синтетические данные (аугментация)
        augmented = self.augment_training_data(training_examples)
        training_examples.extend(augmented)
        
        return training_examples
    
    def augment_training_data(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Аугментация обучающих данных"""
        
        augmented = []
        
        for example in examples:
            # Замена синонимов
            synonyms = self.get_synonyms(example.text)
            for synonym_text in synonyms:
                augmented.append(TrainingExample(
                    text=synonym_text,
                    label=example.label,
                    source='augmentation_synonym'
                ))
            
            # Изменение порядка предложений
            shuffled = self.shuffle_sentences(example.text)
            augmented.append(TrainingExample(
                text=shuffled,
                label=example.label,
                source='augmentation_shuffle'
            ))
        
        return augmented
    
    def train_classifier(self):
        """Обучить классификатор"""
        
        # Собрать данные
        training_data = self.collect_training_data()
        
        # Разделить на train/validation
        from sklearn.model_selection import train_test_split
        train_data, val_data = train_test_split(training_data, test_size=0.2, random_state=42)
        
        # Обучить
        self.ml_classifier.train(train_data)
        
        # Оценить качество
        metrics = self.evaluate_classifier(val_data)
        
        return metrics
    
    def evaluate_classifier(self, validation_data: List[TrainingExample]) -> dict:
        """Оценить качество классификатора"""
        
        predictions = []
        true_labels = []
        
        for example in validation_data:
            features = self.extract_features_from_text(example.text)
            result = self.ml_classifier.classify(features)
            
            predicted_label = f"{result['document_type']}|{result['category']}|{result.get('subcategory', '')}"
            predictions.append(predicted_label)
            true_labels.append(example.label)
        
        # Метрики
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
        
        accuracy = accuracy_score(true_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(true_labels, predictions, average='weighted')
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'classification_report': classification_report(true_labels, predictions)
        }
    
    def active_learning_loop(self):
        """Активное обучение - классификатор запрашивает примеры для обучения"""
        
        # Найти неклассифицированные документы
        unclassified = self.domain.get_unclassified_documents()
        
        for doc in unclassified:
            # Попытка классификации
            features = self.extract_features_from_text(doc.get_text())
            result = self.ml_classifier.classify(features)
            
            # Если уверенность низкая - запросить помощь пользователя
            if result['confidence'] < 0.7:
                user_label = self.request_user_classification(doc)
                
                if user_label:
                    # Добавить в обучающую выборку
                    example = TrainingExample(
                        text=doc.get_text(),
                        label=user_label,
                        source='active_learning'
                    )
                    self.training_data.append(example)
                    
                    # Переобучить
                    if len(self.training_data) >= 10:
                        self.train_classifier()
                        self.training_data = []
```

## 2.7 Confidence Scorer (Оценка уверенности)

```python
class ConfidenceScorer:
    """Оценка уверенности в классификации"""
    
    def score(self, classification_result: dict, features: dict) -> float:
        """Вычислить итоговую уверенность"""
        
        scores = []
        
        # 1. Базовая уверенность из классификатора
        base_confidence = classification_result.get('confidence', 0.5)
        scores.append(('base', base_confidence, 0.4))
        
        # 2. Согласованность методов
        if classification_result.get('agreement', False):
            scores.append(('agreement', 1.0, 0.2))
        else:
            scores.append(('agreement', 0.5, 0.2))
        
        # 3. Наличие ключевых признаков
        key_features_score = self.evaluate_key_features(classification_result, features)
        scores.append(('key_features', key_features_score, 0.2))
        
        # 4. Полнота документа
        completeness_score = self.evaluate_completeness(features)
        scores.append(('completeness', completeness_score, 0.1))
        
        # 5. Консистентность с другими документами
        consistency_score = self.evaluate_consistency(classification_result, features)
        scores.append(('consistency', consistency_score, 0.1))
        
        # Взвешенная сумма
        total_score = sum(score * weight for name, score, weight in scores)
        
        return min(1.0, max(0.0, total_score))
    
    def evaluate_key_features(self, classification_result: dict, features: dict) -> float:
        """Оценить наличие ключевых признаков для типа документа"""
        
        doc_type = classification_result.get('document_type')
        
        if doc_type == 'Widerspruch':
            required_features = ['widerspruch', 'bescheid', 'behörden']
        elif doc_type == 'Antrag':
            required_features = ['antrag', 'persönliches budget']
        elif doc_type == 'Bescheid':
            required_features = ['bescheid', 'signature', 'reference_number']
        else:
            return 0.5
        
        # Проверить наличие
        present_count = 0
        for feature in required_features:
            if self.feature_present(feature, features):
                present_count += 1
        
        return present_count / len(required_features)
    
    def feature_present(self, feature_name: str, features: dict) -> bool:
        """Проверить наличие признака"""
        
        # Проверка в текстовых признаках
        text_features = features.get('text_features', {})
        tokens = [t.lower() for t in text_features.get('tokens', [])]
        if feature_name.lower() in ' '.join(tokens):
            return True
        
        # Проверка в структурных признаках
        structure_features = features.get('structure_features', {})
        if feature_name in structure_features and structure_features[feature_name]:
            return True
        
        return False
```

---

Продолжить с остальными компонентами (Knowledge Graph Engine, Context Manager, Search Engine)?