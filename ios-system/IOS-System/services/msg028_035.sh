# Setup database migrations
alembic init migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Configure FastAPI with SQLAlchemy
# api/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession)

# api/dependencies.py
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session