#!/usr/bin/env python3
"""
Sample Data Generator для IOS System
Генерирует реалистичные тестовые данные
"""
import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
from faker import Faker

# Добавляем path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database.schema import (
    User, UserRole, Document, DocumentStatus, DocumentCategory,
    Tag, APIKey, Session as UserSession, AuditLog,
    KnowledgeGraphEntity, KnowledgeGraphRelation, SearchQuery
)
from security.encryption_service import EncryptionService


class SampleDataGenerator:
    """Генератор sample данных"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.fake = Faker()
        self.engine = None
        self.session_maker = None
        
        # Кэш созданных объектов
        self.users = []
        self.documents = []
        self.tags = []
        
    async def initialize(self):
        """Инициализация"""
        self.engine = create_async_engine(self.database_url, echo=False)
        self.session_maker = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
    async def cleanup(self):
        """Очистка"""
        if self.engine:
            await self.engine.dispose()
            
    async def generate_users(self, count: int = 50) -> List[User]:
        """Генерировать пользователей"""
        print(f"Generating {count} users...")
        
        encryption = EncryptionService()
        password_hash, salt = encryption.hash_password("password123")
        
        users = []
        async with self.session_maker() as session:
            for i in range(count):
                user = User(
                    username=self.fake.user_name() + str(random.randint(1, 9999)),
                    email=self.fake.email(),
                    password_hash=password_hash,
                    salt=salt,
                    full_name=self.fake.name(),
                    role=random.choice([UserRole.USER, UserRole.USER, UserRole.USER, UserRole.VIEWER]),
                    is_active=random.choice([True, True, True, False]),
                    is_verified=random.choice([True, True, False]),
                    created_at=self.fake.date_time_between(start_date='-2y', end_date='now'),
                    settings={'theme': random.choice(['light', 'dark']), 'language': 'en'},
                    preferences={'notifications': random.choice([True, False])}
                )
                users.append(user)
                
            session.add_all(users)
            await session.commit()
            
            for user in users:
                await session.refresh(user)
                
        self.users = users
        print(f"✓ Created {len(users)} users")
        return users
        
    async def generate_tags(self, count: int = 30) -> List[Tag]:
        """Генерировать теги"""
        print(f"Generating {count} tags...")
        
        tag_names = [
            'important', 'urgent', 'review', 'draft', 'final',
            'meeting', 'report', 'analysis', 'proposal', 'contract',
            'finance', 'hr', 'marketing', 'sales', 'engineering',
            'research', 'development', 'design', 'testing', 'deployment',
            'customer', 'internal', 'external', 'confidential', 'public',
            'Q1', 'Q2', 'Q3', 'Q4', '2024', '2025'
        ]
        
        colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#F5FF33', 
                  '#33FFF5', '#F533FF', '#57FF33', '#5733FF', '#FF5733']
        
        tags = []
        async with self.session_maker() as session:
            for name in tag_names[:count]:
                tag = Tag(
                    name=name,
                    description=self.fake.sentence(),
                    color=random.choice(colors),
                    usage_count=random.randint(0, 100)
                )
                tags.append(tag)
                
            session.add_all(tags)
            await session.commit()
            
            for tag in tags:
                await session.refresh(tag)
                
        self.tags = tags
        print(f"✓ Created {len(tags)} tags")
        return tags
        
    async def generate_documents(self, count: int = 200) -> List[Document]:
        """Генерировать документы"""
        print(f"Generating {count} documents...")
        
        if not self.users:
            raise ValueError("Users must be generated first")
            
        documents = []
        async with self.session_maker() as session:
            for i in range(count):
                # Случайный owner
                owner = random.choice(self.users)
                
                # Генерируем контент
                title = self.fake.sentence(nb_words=random.randint(3, 8)).rstrip('.')
                content = '\n\n'.join([self.fake.paragraph(nb_sentences=random.randint(5, 15)) 
                                      for _ in range(random.randint(3, 10))])
                
                doc = Document(
                    title=title,
                    content=content,
                    content_hash=self.fake.sha256(),
                    category=random.choice(list(DocumentCategory)),
                    status=random.choice([
                        DocumentStatus.PUBLISHED, DocumentStatus.PUBLISHED,
                        DocumentStatus.DRAFT, DocumentStatus.ARCHIVED
                    ]),
                    owner_id=owner.id,
                    file_size=len(content),
                    file_type=random.choice(['text/plain', 'text/markdown', 'application/pdf']),
                    language='en',
                    version=1,
                    created_at=self.fake.date_time_between(start_date='-1y', end_date='now'),
                    summary=self.fake.paragraph(nb_sentences=2),
                    keywords=[self.fake.word() for _ in range(random.randint(3, 7))],
                    view_count=random.randint(0, 500),
                    download_count=random.randint(0, 100),
                    metadata={'source': 'generated', 'quality': random.choice(['high', 'medium', 'low'])}
                )
                
                # Добавляем теги
                if self.tags:
                    doc.tags = random.sample(self.tags, k=random.randint(1, 5))
                    
                documents.append(doc)
                
            session.add_all(documents)
            await session.commit()
            
            for doc in documents:
                await session.refresh(doc)
                
        self.documents = documents
        print(f"✓ Created {len(documents)} documents")
        return documents
        
    async def generate_api_keys(self, count: int = 20) -> List[APIKey]:
        """Генерировать API ключи"""
        print(f"Generating {count} API keys...")
        
        if not self.users:
            raise ValueError("Users must be generated first")
            
        encryption = EncryptionService()
        
        api_keys = []
        async with self.session_maker() as session:
            for i in range(count):
                user = random.choice(self.users)
                
                # Генерируем ключ
                key = self.fake.sha256()
                key_hash = encryption.encrypt(key)
                
                api_key = APIKey(
                    user_id=user.id,
                    key_hash=key_hash,
                    key_prefix=key[:10],
                    name=f"API Key {i+1}",
                    permissions=['read', 'write'] if random.random() > 0.5 else ['read'],
                    rate_limit=random.choice([100, 500, 1000, 5000]),
                    is_active=random.choice([True, True, True, False]),
                    expires_at=datetime.utcnow() + timedelta(days=random.randint(30, 365))
                )
                api_keys.append(api_key)
                
            session.add_all(api_keys)
            await session.commit()
            
        print(f"✓ Created {len(api_keys)} API keys")
        return api_keys
        
    async def generate_audit_logs(self, count: int = 500) -> List[AuditLog]:
        """Генерировать audit логи"""
        print(f"Generating {count} audit logs...")
        
        if not self.users:
            raise ValueError("Users must be generated first")
            
        action_types = [
            'login', 'logout', 'document_created', 'document_viewed',
            'document_updated', 'document_deleted', 'search_performed',
            'permission_granted', 'permission_denied', 'security_alert'
        ]
        
        severities = ['info', 'warning', 'error', 'critical']
        
        logs = []
        async with self.session_maker() as session:
            for i in range(count):
                user = random.choice(self.users) if random.random() > 0.1 else None
                
                log = AuditLog(
                    timestamp=self.fake.date_time_between(start_date='-30d', end_date='now'),
                    action_type=random.choice(action_types),
                    severity=random.choice(severities),
                    user_id=user.id if user else None,
                    user_email=user.email if user else self.fake.email(),
                    ip_address=self.fake.ipv4(),
                    user_agent=self.fake.user_agent(),
                    resource_type=random.choice(['document', 'user', 'system', None]),
                    resource_id=str(random.randint(1, 1000)),
                    action_result=random.choice(['success', 'success', 'failed']),
                    details={'info': self.fake.sentence()},
                    request_id=self.fake.uuid4()
                )
                logs.append(log)
                
            session.add_all(logs)
            await session.commit()
            
        print(f"✓ Created {len(logs)} audit logs")
        return logs
        
    async def generate_knowledge_graph(self, entity_count: int = 100, relation_count: int = 200):
        """Генерировать граф знаний"""
        print(f"Generating knowledge graph ({entity_count} entities, {relation_count} relations)...")
        
        entity_types = ['person', 'organization', 'location', 'concept', 'event', 'product']
        relation_types = ['works_at', 'located_in', 'related_to', 'owns', 'manages', 'participates_in']
        
        entities = []
        async with self.session_maker() as session:
            # Создаем сущности
            for i in range(entity_count):
                entity = KnowledgeGraphEntity(
                    entity_type=random.choice(entity_types),
                    name=self.fake.company() if random.random() > 0.5 else self.fake.name(),
                    description=self.fake.paragraph(nb_sentences=2),
                    properties={'category': self.fake.word(), 'importance': random.randint(1, 10)},
                    confidence_score=random.uniform(0.7, 1.0),
                    source_document_id=random.choice(self.documents).id if self.documents and random.random() > 0.3 else None
                )
                entities.append(entity)
                
            session.add_all(entities)
            await session.commit()
            
            for entity in entities:
                await session.refresh(entity)
                
            # Создаем связи
            relations = []
            for i in range(relation_count):
                from_entity = random.choice(entities)
                to_entity = random.choice([e for e in entities if e.id != from_entity.id])
                
                relation = KnowledgeGraphRelation(
                    from_entity_id=from_entity.id,
                    to_entity_id=to_entity.id,
                    relation_type=random.choice(relation_types),
                    properties={'strength': random.uniform(0.5, 1.0)},
                    confidence_score=random.uniform(0.7, 1.0)
                )
                relations.append(relation)
                
            session.add_all(relations)
            await session.commit()
            
        print(f"✓ Created {len(entities)} entities and {len(relations)} relations")
        
    async def generate_search_history(self, count: int = 300) -> List[SearchQuery]:
        """Генерировать историю поиска"""
        print(f"Generating {count} search queries...")
        
        if not self.users:
            raise ValueError("Users must be generated first")
            
        search_terms = [
            'annual report', 'meeting notes', 'project proposal',
            'financial analysis', 'customer feedback', 'marketing plan',
            'technical documentation', 'user guide', 'contract',
            'budget', 'timeline', 'roadmap', 'strategy'
        ]
        
        queries = []
        async with self.session_maker() as session:
            for i in range(count):
                user = random.choice(self.users) if random.random() > 0.2 else None
                
                query = SearchQuery(
                    query_text=random.choice(search_terms) + ' ' + self.fake.word(),
                    query_type=random.choice(['semantic', 'keyword', 'advanced']),
                    user_id=user.id if user else None,
                    ip_address=self.fake.ipv4(),
                    results_count=random.randint(0, 50),
                    response_time_ms=random.uniform(10, 500),
                    filters={'category': random.choice(list(DocumentCategory)).value},
                    created_at=self.fake.date_time_between(start_date='-30d', end_date='now')
                )
                queries.append(query)
                
            session.add_all(queries)
            await session.commit()
            
        print(f"✓ Created {len(queries)} search queries")
        return queries


async def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IOS System Sample Data Generator')
    parser.add_argument('--database-url',
                       default='postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db',
                       help='Database URL')
    parser.add_argument('--users', type=int, default=50, help='Number of users')
    parser.add_argument('--documents', type=int, default=200, help='Number of documents')
    parser.add_argument('--tags', type=int, default=30, help='Number of tags')
    parser.add_argument('--api-keys', type=int, default=20, help='Number of API keys')
    parser.add_argument('--audit-logs', type=int, default=500, help='Number of audit logs')
    parser.add_argument('--kg-entities', type=int, default=100, help='Knowledge graph entities')
    parser.add_argument('--kg-relations', type=int, default=200, help='Knowledge graph relations')
    parser.add_argument('--search-queries', type=int, default=300, help='Search queries')
    parser.add_argument('--all', action='store_true', help='Generate all data types')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("IOS SYSTEM - SAMPLE DATA GENERATOR")
    print("=" * 60)
    print(f"Database: {args.database_url.split('@')[1] if '@' in args.database_url else args.database_url}")
    print("=" * 60)
    
    generator = SampleDataGenerator(args.database_url)
    
    try:
        await generator.initialize()
        
        # Генерируем данные в правильном порядке
        await generator.generate_users(args.users)
        await generator.generate_tags(args.tags)
        await generator.generate_documents(args.documents)
        await generator.generate_api_keys(args.api_keys)
        await generator.generate_audit_logs(args.audit_logs)
        await generator.generate_knowledge_graph(args.kg_entities, args.kg_relations)
        await generator.generate_search_history(args.search_queries)
        
        await generator.cleanup()
        
        print("\n" + "=" * 60)
        print("✓ SAMPLE DATA GENERATION COMPLETED")
        print("=" * 60)
        print(f"Users: {args.users}")
        print(f"Documents: {args.documents}")
        print(f"Tags: {args.tags}")
        print(f"API Keys: {args.api_keys}")
        print(f"Audit Logs: {args.audit_logs}")
        print(f"KG Entities: {args.kg_entities}")
        print(f"KG Relations: {args.kg_relations}")
        print(f"Search Queries: {args.search_queries}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
