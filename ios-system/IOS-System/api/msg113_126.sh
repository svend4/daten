# Backup script runs daily via CronJob
# Location: kubernetes/cronjobs/backup.yaml

apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: ios-production
spec:
  schedule: "0 2 * * *"  # 2 AM UTC daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:14
            command:
            - /bin/bash
            - -c
            - |
              BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
              BACKUP_FILE="ios_production_${BACKUP_DATE}.sql"
              
              pg_dump -h postgresql -U postgres ios_production > /tmp/${BACKUP_FILE}
              
              gzip /tmp/${BACKUP_FILE}
              
              aws s3 cp /tmp/${BACKUP_FILE}.gz s3://ios-system-backups/production/${BACKUP_FILE}.gz
              
              # Keep only 30 days of backups
              aws s3 ls s3://ios-system-backups/production/ | \
                awk '{print $4}' | \
                sort -r | \
                tail -n +31 | \
                xargs -I {} aws s3 rm s3://ios-system-backups/production/{}
          restartPolicy: OnFailure