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