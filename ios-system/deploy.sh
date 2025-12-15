#!/bin/bash
# Deployment Script для IOS System
# Автоматизация deployment процесса

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   IOS SYSTEM - DEPLOYMENT SCRIPT${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please copy .env.production.example to .env and configure it."
    exit 1
fi

echo -e "${GREEN}✓ .env file found${NC}"

# Load environment variables
set -a
source .env
set +a

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Docker
if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Deployment menu
show_menu() {
    echo ""
    echo -e "${YELLOW}Select deployment action:${NC}"
    echo ""
    echo "1) Initial Setup (first time deployment)"
    echo "2) Deploy/Update (build and restart all services)"
    echo "3) Stop all services"
    echo "4) View logs"
    echo "5) Run database migrations"
    echo "6) Backup database"
    echo "7) Restore database"
    echo "8) SSL Certificate setup"
    echo "9) Health check"
    echo "10) Clean up (remove all data - DANGEROUS)"
    echo "11) Exit"
    echo ""
}

# Initial setup
initial_setup() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   INITIAL SETUP${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    # Create necessary directories
    echo "Creating directories..."
    mkdir -p logs certbot/conf certbot/www prometheus grafana/provisioning
    
    # Pull images
    echo "Pulling Docker images..."
    docker-compose pull
    
    # Build custom images
    echo "Building custom images..."
    docker-compose build
    
    # Start services
    echo "Starting services..."
    docker-compose up -d
    
    # Wait for database
    echo "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    echo "Running database migrations..."
    docker-compose exec -T backend python database/migrate.py --action create --create-admin
    
    echo -e "${GREEN}✓ Initial setup complete!${NC}"
    echo ""
    echo "Access points:"
    echo "  Frontend: http://localhost (or your domain)"
    echo "  Backend API: http://localhost/api"
    echo "  Grafana: http://localhost:3001"
    echo "  Prometheus: http://localhost:9090"
}

# Deploy/Update
deploy() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   DEPLOYING/UPDATING${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    # Pull latest images
    echo "Pulling latest images..."
    docker-compose pull
    
    # Build images
    echo "Building images..."
    docker-compose build --no-cache
    
    # Stop services
    echo "Stopping services..."
    docker-compose down
    
    # Start services
    echo "Starting services..."
    docker-compose up -d
    
    # Wait for services
    echo "Waiting for services to start..."
    sleep 15
    
    # Health check
    health_check
    
    echo -e "${GREEN}✓ Deployment complete!${NC}"
}

# Stop services
stop_services() {
    echo "Stopping all services..."
    docker-compose down
    echo -e "${GREEN}✓ All services stopped${NC}"
}

# View logs
view_logs() {
    echo "Select service to view logs:"
    echo "1) All services"
    echo "2) Backend"
    echo "3) Frontend"
    echo "4) Nginx"
    echo "5) PostgreSQL"
    echo "6) Redis"
    read -p "Choice: " log_choice
    
    case $log_choice in
        1) docker-compose logs -f ;;
        2) docker-compose logs -f backend ;;
        3) docker-compose logs -f frontend ;;
        4) docker-compose logs -f nginx ;;
        5) docker-compose logs -f postgres ;;
        6) docker-compose logs -f redis ;;
        *) echo "Invalid choice" ;;
    esac
}

# Database migrations
run_migrations() {
    echo "Running database migrations..."
    docker-compose exec backend python database/migrate.py --action create
    echo -e "${GREEN}✓ Migrations complete${NC}"
}

# Backup database
backup_database() {
    echo "Creating database backup..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "backups/${BACKUP_FILE}"
    echo -e "${GREEN}✓ Backup created: backups/${BACKUP_FILE}${NC}"
}

# Restore database
restore_database() {
    echo "Available backups:"
    ls -lh backups/
    read -p "Enter backup filename to restore: " BACKUP_FILE
    
    if [ -f "backups/${BACKUP_FILE}" ]; then
        echo "Restoring database..."
        docker-compose exec -T postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB} < "backups/${BACKUP_FILE}"
        echo -e "${GREEN}✓ Database restored${NC}"
    else
        echo -e "${RED}❌ Backup file not found${NC}"
    fi
}

# SSL setup
ssl_setup() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   SSL CERTIFICATE SETUP${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    if [ -z "$DOMAIN" ] || [ -z "$SSL_EMAIL" ]; then
        echo -e "${RED}❌ DOMAIN and SSL_EMAIL must be set in .env${NC}"
        exit 1
    fi
    
    echo "Setting up SSL certificate for: ${DOMAIN}"
    
    # Get certificate
    docker-compose run --rm certbot certonly --webroot \
        -w /var/www/certbot \
        -d ${DOMAIN} \
        --email ${SSL_EMAIL} \
        --agree-tos \
        --no-eff-email
    
    echo -e "${GREEN}✓ SSL certificate obtained${NC}"
    echo "Restarting nginx..."
    docker-compose restart nginx
}

# Health check
health_check() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   HEALTH CHECK${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    # Check backend
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend: Healthy${NC}"
    else
        echo -e "${RED}✗ Backend: Unhealthy${NC}"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend: Healthy${NC}"
    else
        echo -e "${RED}✗ Frontend: Unhealthy${NC}"
    fi
    
    # Check database
    if docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER} >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL: Healthy${NC}"
    else
        echo -e "${RED}✗ PostgreSQL: Unhealthy${NC}"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis: Healthy${NC}"
    else
        echo -e "${RED}✗ Redis: Unhealthy${NC}"
    fi
}

# Clean up
cleanup() {
    echo -e "${RED}⚠️  WARNING: This will delete ALL data!${NC}"
    read -p "Type 'yes' to confirm: " confirm
    
    if [ "$confirm" == "yes" ]; then
        echo "Stopping and removing all containers..."
        docker-compose down -v
        echo "Removing images..."
        docker-compose down --rmi all
        echo -e "${GREEN}✓ Cleanup complete${NC}"
    else
        echo "Cleanup cancelled"
    fi
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice [1-11]: " choice
    
    case $choice in
        1) initial_setup ;;
        2) deploy ;;
        3) stop_services ;;
        4) view_logs ;;
        5) run_migrations ;;
        6) backup_database ;;
        7) restore_database ;;
        8) ssl_setup ;;
        9) health_check ;;
        10) cleanup ;;
        11) echo "Exiting..."; exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
