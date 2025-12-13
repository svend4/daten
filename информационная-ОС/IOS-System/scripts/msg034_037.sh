# Add to docker-compose.production.yml

  celery-worker:
    image: ios-system:${VERSION:-latest}
    container_name: ios-celery-worker
    command: celery -A ios_core.tasks.celery_app worker --loglevel=info --concurrency=4
    
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    
    volumes:
      - ios-data:/data/ios-root
    
    depends_on:
      - redis
      - postgres
    
    networks:
      - ios-network

  celery-beat:
    image: ios-system:${VERSION:-latest}
    container_name: ios-celery-beat
    command: celery -A ios_core.tasks.celery_app beat --loglevel=info
    
    environment:
      - REDIS_URL=redis://redis:6379/0
    
    depends_on:
      - redis
    
    networks:
      - ios-network