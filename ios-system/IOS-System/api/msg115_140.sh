# Vertical scaling - increase instance size
# AWS RDS
aws rds modify-db-instance \
  --db-instance-identifier ios-production-db \
  --db-instance-class db.r5.2xlarge \
  --apply-immediately

# Check modification status
aws rds describe-db-instances \
  --db-instance-identifier ios-production-db \
  --query 'DBInstances[0].DBInstanceStatus'

# Horizontal scaling - add read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier ios-production-db-replica-1 \
  --source-db-instance-identifier ios-production-db \
  --db-instance-class db.r5.xlarge \
  --publicly-accessible

# Configure app to use read replica
kubectl set env deployment/ios-api -n ios-production \
  DATABASE_READ_URL="postgresql://user:pass@replica-endpoint:5432/ios_production"

# Connection pooling - increase pool size
kubectl set env deployment/ios-api -n ios-production \
  DB_POOL_SIZE=50 \
  DB_MAX_OVERFLOW=20