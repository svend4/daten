# Initialize Alembic
alembic init migrations

# Edit alembic.ini
sqlalchemy.url = postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Run migration
alembic upgrade head