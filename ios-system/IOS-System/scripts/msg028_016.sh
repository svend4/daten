# Deploy to staging
ssh staging-server
cd /opt/ios-system
git pull
docker-compose down
docker-compose up -d --build

# Run smoke tests
curl http://staging-server/health
python scripts/smoke_tests.py

# Monitor
docker-compose logs -f