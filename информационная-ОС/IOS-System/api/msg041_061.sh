# Обновить requirements.txt
cat >> requirements.txt << 'EOF'

# Observability
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-jaeger==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-redis==0.42b0
opentelemetry-instrumentation-requests==0.42b0
python-json-logger==2.0.7
prometheus-client==0.19.0
sentry-sdk[fastapi]==1.39.1
EOF

# Установить зависимости
pip install -r requirements.txt