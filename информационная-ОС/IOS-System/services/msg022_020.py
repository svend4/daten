# requirements.txt
# Python зависимости для IOS

fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0

# Caching
redis==5.0.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# HTTP clients
httpx==0.25.2
requests==2.31.0

# WebSocket
websockets==12.0

# Search & NLP
whoosh==2.7.4
scikit-learn==1.3.2
numpy==1.26.2

# Graph processing
networkx==3.2.1
python-louvain==0.16

# Visualization
matplotlib==3.8.2
plotly==5.18.0

# Document processing
python-docx==1.1.0
PyPDF2==3.0.1
openpyxl==3.1.2
python-pptx==0.6.23

# Utilities
python-dotenv==1.0.0
aiofiles==23.2.1