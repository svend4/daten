#!/usr/bin/env python3
"""
Database Migration Script для IOS System
Создание и миграция production database
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Добавляем path к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.schema import (
    Base, create_all_tables, drop_all_tables, get_table_names,
    User, UserRole
)
from security.encryption_service import EncryptionService


class DatabaseMigration:
    """Управление миграциями БД"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_engine = None
        
    def create_sync_engine(self):
        """Создать sync engine"""
        # Конвертируем async URL в sync
        sync_url = self.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        self.engine = create_engine(sync_url, echo=True)
        return self.engine
        
    def create_async_engine(self):
        """Создать async engine"""
        self.async_engine = create_async_engine(self.database_url, echo=True)
        return self.async_engine
        
    def create_database(self):
        """Создать базу данных если не существует"""
        # Подключаемся к postgres database
        base_url = self.database_url.rsplit('/', 1)[0]
        db_name = self.database_url.rsplit('/', 1)[1].split('?')[0]
        
        sync_base_url = base_url.replace('postgresql+asyncpg://', 'postgresql://')
        engine = create_engine(f"{sync_base_url}/postgres", isolation_level='AUTOCOMMIT')
        
        with engine.connect() as conn:
            # Проверяем существование БД
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"Creating database: {db_name}")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✓ Database {db_name} created")
            else:
                print(f"✓ Database {db_name} already exists")
                
        engine.dispose()
        
    def create_tables(self):
        """Создать все таблицы"""
        print("\nCreating tables...")
        engine = self.create_sync_engine()
        
        create_all_tables(engine)
        
        print("\n✓ Tables created:")
        for table_name in get_table_names():
            print(f"  - {table_name}")
            
        engine.dispose()
        
    def drop_tables(self):
        """Удалить все таблицы"""
        print("\n⚠️  Dropping all tables...")
        engine = self.create_sync_engine()
        
        drop_all_tables(engine)
        
        print("✓ All tables dropped")
        engine.dispose()
        
    async def create_admin_user(self, username: str = "admin", password: str = "admin123", email: str = "admin@ios.system"):
        """Создать admin пользователя"""
        print("\nCreating admin user...")
        
        engine = self.create_async_engine()
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Проверяем существование
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✓ Admin user '{username}' already exists")
                return existing_user
                
            # Создаем пользователя
            encryption = EncryptionService()
            password_hash, salt = encryption.hash_password(password)
            
            admin = User(
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow()
            )
            
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            
            print(f"✓ Admin user created:")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"  Role: {admin.role.value}")
            
        await engine.dispose()
        return admin
        
    async def create_test_users(self, count: int = 10):
        """Создать тестовых пользователей"""
        print(f"\nCreating {count} test users...")
        
        engine = self.create_async_engine()
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        encryption = EncryptionService()
        password_hash, salt = encryption.hash_password("testpass123")
        
        async with async_session() as session:
            users = []
            for i in range(1, count + 1):
                user = User(
                    username=f"user{i}",
                    email=f"user{i}@test.com",
                    password_hash=password_hash,
                    salt=salt,
                    full_name=f"Test User {i}",
                    role=UserRole.USER,
                    is_active=True,
                    is_verified=True
                )
                users.append(user)
                
            session.add_all(users)
            await session.commit()
            
            print(f"✓ Created {count} test users (user1...user{count})")
            print(f"  Password: testpass123")
            
        await engine.dispose()
        
    def create_indexes(self):
        """Создать дополнительные индексы"""
        print("\nCreating additional indexes...")
        engine = self.create_sync_engine()
        
        with engine.connect() as conn:
            # GIN индекс для полнотекстового поиска (PostgreSQL)
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_documents_fulltext_gin 
                    ON documents USING gin(to_tsvector('english', title || ' ' || content))
                """))
                print("✓ Full-text search index created")
            except Exception as e:
                print(f"⚠️  Could not create full-text index: {e}")
                
            conn.commit()
            
        engine.dispose()
        
    def verify_migration(self):
        """Проверить успешность миграции"""
        print("\nVerifying migration...")
        engine = self.create_sync_engine()
        
        with engine.connect() as conn:
            # Проверяем таблицы
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            expected_tables = get_table_names()
            missing_tables = set(expected_tables) - set(tables)
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            else:
                print(f"✓ All {len(tables)} tables present")
                
            # Проверяем пользователей
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"✓ Users in database: {user_count}")
            
        engine.dispose()
        return True


async def main():
    """Основная функция миграции"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IOS System Database Migration')
    parser.add_argument('--database-url', 
                       default='postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db',
                       help='Database URL')
    parser.add_argument('--action', 
                       choices=['create', 'drop', 'recreate', 'verify'],
                       default='create',
                       help='Migration action')
    parser.add_argument('--create-admin', action='store_true', help='Create admin user')
    parser.add_argument('--create-test-users', type=int, help='Create N test users')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("IOS SYSTEM - DATABASE MIGRATION")
    print("=" * 60)
    print(f"Database: {args.database_url.split('@')[1] if '@' in args.database_url else args.database_url}")
    print(f"Action: {args.action}")
    print("=" * 60)
    
    migration = DatabaseMigration(args.database_url)
    
    try:
        if args.action == 'drop':
            confirm = input("\n⚠️  This will DROP ALL TABLES. Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                migration.drop_tables()
            else:
                print("Aborted")
                return
                
        elif args.action == 'recreate':
            confirm = input("\n⚠️  This will DROP and RECREATE ALL TABLES. Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                migration.drop_tables()
                migration.create_database()
                migration.create_tables()
                migration.create_indexes()
            else:
                print("Aborted")
                return
                
        elif args.action == 'create':
            migration.create_database()
            migration.create_tables()
            migration.create_indexes()
            
        elif args.action == 'verify':
            success = migration.verify_migration()
            if not success:
                sys.exit(1)
                
        # Дополнительные действия
        if args.create_admin:
            await migration.create_admin_user()
            
        if args.create_test_users:
            await migration.create_test_users(args.create_test_users)
            
        # Финальная проверка
        if args.action in ['create', 'recreate']:
            migration.verify_migration()
            
        print("\n" + "=" * 60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
