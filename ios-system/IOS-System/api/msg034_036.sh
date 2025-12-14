# Access Grafana
open http://localhost:3000
# Login: admin / (check GRAFANA_PASSWORD in .env)

# Import dashboards
# Settings -> Data Sources -> Add Prometheus
# Dashboards -> Import -> Upload ios-overview.json

# Check alerts
open http://localhost:9090/alerts

# Test alert
# Stop API container
docker-compose stop ios-api
# Wait 1 minute
# Check alert fires in Prometheus

# Restart
docker-compose start ios-api

# Verify alert resolves

git commit -m "Week 7-8 complete: Production deployment + monitoring"
git tag v0.1.0-week8