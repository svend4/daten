# Test database setup
python -c "
from ios_core.models import Base
from sqlalchemy import create_engine
engine = create_engine('postgresql://ios_user:ios_password@localhost:5432/ios_db')
Base.metadata.create_all(engine)
print('✓ Database schema created')
"