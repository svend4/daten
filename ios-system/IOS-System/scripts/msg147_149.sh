cd /opt/ios
python scripts/disaster_recovery.py \\
    --postgres-backup s3://backups/postgresql/latest.dump \\
    --es-repository ios_backup \\
    --es-snapshot snapshot_20241213 \\
    --qdrant-backup s3://backups/qdrant/latest.tar.gz