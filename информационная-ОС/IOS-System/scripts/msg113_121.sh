# Check if database migration was applied
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "SELECT version FROM alembic_version;"

# Check if new data written that depends on new schema
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_name = 'documents'
    AND column_name NOT IN (
      SELECT column_name FROM information_schema.columns
      WHERE table_schema = 'public_v1_0_0'
    );
  "