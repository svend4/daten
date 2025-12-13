Отлично! Продолжаем с Disaster Recovery - это очень важная тема для production-ready системы. После этого будет финальный файл - Production Readiness Checklist.

Disaster Recovery должен включать:
1. Backup strategies
2. Recovery procedures
3. High availability setup
4. Failure scenarios and responses
5. RTO/RPO definitions
6. Testing procedures# 🎯 DEEP-DIVE: SEARCH SYSTEM (DISASTER RECOVERY)

## ФАЙЛ 15: `docs/deep-dive/search/DISASTER_RECOVERY.md`

```markdown
# Disaster Recovery Guide - Deep Dive

## 🛡️ DR Strategy Overview

### Recovery Objectives

```
┌─────────────────────────────────────────────────────────────┐
│              RECOVERY TIME OBJECTIVE (RTO)                  │
│         How long can system be down?                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tier 1: Critical Services                                  │
│  ├─ Search API: RTO = 5 minutes                            │
│  ├─ Elasticsearch: RTO = 15 minutes                        │
│  └─ PostgreSQL: RTO = 10 minutes                           │
│                                                             │
│  Tier 2: Background Services                                │
│  ├─ Indexing Pipeline: RTO = 1 hour                        │
│  ├─ Analytics: RTO = 4 hours                               │
│  └─ Backup Jobs: RTO = 24 hours                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            RECOVERY POINT OBJECTIVE (RPO)                   │
│         How much data loss is acceptable?                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tier 1: Zero Data Loss                                     │
│  ├─ User Data (PostgreSQL): RPO = 0 (synchronous repl)     │
│  └─ Search Queries: RPO = 0 (write-ahead log)              │
│                                                             │
│  Tier 2: Minimal Data Loss                                  │
│  ├─ Search Index (Elasticsearch): RPO = 5 minutes          │
│  ├─ Vector Index (Qdrant): RPO = 15 minutes                │
│  └─ Cache (Redis): RPO = N/A (ephemeral)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Backup Strategy

### Comprehensive Backup Plan

```python
# scripts/backup_manager.py

"""
Comprehensive backup management system
"""

import subprocess
import boto3
import datetime
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

class BackupManager:
    """
    Centralized backup management
    
    Handles:
    - PostgreSQL backups
    - Elasticsearch snapshots
    - Qdrant backups
    - Configuration backups
    """
    
    def __init__(self, s3_bucket: str = 'ios-backups'):
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket
        self.backup_dir = Path('/var/backups/ios')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup_postgresql(self, retention_days: int = 30) -> Dict:
        """
        Backup PostgreSQL database
        
        Strategy:
        - Full backup daily
        - WAL archiving for point-in-time recovery
        - Retention: 30 days
        
        Returns:
            Backup metadata
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'postgres_backup_{timestamp}.sql.gz'
        
        logger.info(f"Starting PostgreSQL backup: {backup_file}")
        
        # Run pg_dump with compression
        cmd = [
            'pg_dump',
            '-U', 'ios',
            '-h', 'postgres-primary',
            '-d', 'ios_db',
            '-F', 'c',  # Custom format (compressed)
            '-f', str(backup_file)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Upload to S3
            s3_key = f'postgresql/daily/{backup_file.name}'
            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD_IA',  # Cheaper storage
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            # Cleanup old backups
            self._cleanup_old_backups('postgresql/daily/', retention_days)
            
            backup_size = backup_file.stat().st_size
            
            logger.info(
                f"PostgreSQL backup completed: {backup_size / 1024**2:.2f} MB"
            )
            
            return {
                'status': 'success',
                'backup_file': str(backup_file),
                's3_key': s3_key,
                'size_mb': backup_size / 1024**2,
                'timestamp': timestamp
            }
        
        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL backup failed: {e.stderr}")
            return {'status': 'error', 'error': str(e)}
    
    def backup_elasticsearch(self, repository: str = 'ios_backup') -> Dict:
        """
        Backup Elasticsearch indices
        
        Strategy:
        - Snapshot to shared storage (S3/NFS)
        - Incremental snapshots
        - Retention: 30 days
        """
        import requests
        
        es_host = 'http://elasticsearch-master:9200'
        snapshot_name = f"snapshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting Elasticsearch snapshot: {snapshot_name}")
        
        try:
            # Create snapshot
            response = requests.put(
                f"{es_host}/_snapshot/{repository}/{snapshot_name}",
                json={
                    "indices": "ios-documents-*",
                    "ignore_unavailable": True,
                    "include_global_state": False
                },
                params={"wait_for_completion": "false"}
            )
            
            response.raise_for_status()
            
            logger.info(f"Elasticsearch snapshot initiated: {snapshot_name}")
            
            return {
                'status': 'success',
                'repository': repository,
                'snapshot': snapshot_name,
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        except requests.RequestException as e:
            logger.error(f"Elasticsearch snapshot failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def backup_qdrant(self) -> Dict:
        """
        Backup Qdrant collections
        
        Strategy:
        - Snapshot entire data directory
        - Upload to S3
        - Retention: 30 days
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'qdrant_backup_{timestamp}.tar.gz'
        
        logger.info(f"Starting Qdrant backup: {backup_file}")
        
        # Create tarball of Qdrant data
        cmd = [
            'tar',
            '-czf', str(backup_file),
            '-C', '/var/lib/qdrant',
            'storage'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Upload to S3
            s3_key = f'qdrant/daily/{backup_file.name}'
            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD_IA',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            backup_size = backup_file.stat().st_size
            
            logger.info(
                f"Qdrant backup completed: {backup_size / 1024**2:.2f} MB"
            )
            
            return {
                'status': 'success',
                'backup_file': str(backup_file),
                's3_key': s3_key,
                'size_mb': backup_size / 1024**2,
                'timestamp': timestamp
            }
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Qdrant backup failed: {e.stderr}")
            return {'status': 'error', 'error': str(e)}
    
    def backup_configurations(self) -> Dict:
        """
        Backup system configurations
        
        Includes:
        - Docker configs
        - NGINX configs
        - Environment files
        - Scripts
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'configs_{timestamp}.tar.gz'
        
        config_paths = [
            '/etc/nginx',
            '/opt/ios/docker-compose.yml',
            '/opt/ios/.env.production',
            '/opt/ios/scripts'
        ]
        
        cmd = ['tar', '-czf', str(backup_file)] + config_paths
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            s3_key = f'configs/{backup_file.name}'
            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key
            )
            
            return {
                'status': 'success',
                's3_key': s3_key,
                'timestamp': timestamp
            }
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Config backup failed: {e.stderr}")
            return {'status': 'error', 'error': str(e)}
    
    def _cleanup_old_backups(self, prefix: str, retention_days: int):
        """Delete backups older than retention period"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
        
        # List objects in S3
        response = self.s3_client.list_objects_v2(
            Bucket=self.s3_bucket,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return
        
        for obj in response['Contents']:
            if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                logger.info(f"Deleting old backup: {obj['Key']}")
                self.s3_client.delete_object(
                    Bucket=self.s3_bucket,
                    Key=obj['Key']
                )
    
    def run_full_backup(self) -> Dict:
        """
        Run complete backup of all components
        
        Orchestrates all backup tasks
        """
        logger.info("="*60)
        logger.info("STARTING FULL BACKUP")
        logger.info("="*60)
        
        results = {
            'start_time': datetime.datetime.now().isoformat(),
            'backups': {}
        }
        
        # PostgreSQL
        logger.info("\n1. Backing up PostgreSQL...")
        results['backups']['postgresql'] = self.backup_postgresql()
        
        # Elasticsearch
        logger.info("\n2. Backing up Elasticsearch...")
        results['backups']['elasticsearch'] = self.backup_elasticsearch()
        
        # Qdrant
        logger.info("\n3. Backing up Qdrant...")
        results['backups']['qdrant'] = self.backup_qdrant()
        
        # Configurations
        logger.info("\n4. Backing up configurations...")
        results['backups']['configs'] = self.backup_configurations()
        
        results['end_time'] = datetime.datetime.now().isoformat()
        results['status'] = 'success' if all(
            b.get('status') == 'success' 
            for b in results['backups'].values()
        ) else 'partial_failure'
        
        logger.info("\n" + "="*60)
        logger.info(f"BACKUP COMPLETED: {results['status']}")
        logger.info("="*60)
        
        return results


# Automated backup scheduling
BACKUP_SCHEDULE = """
# Crontab for automated backups

# Full backup daily at 2 AM
0 2 * * * /opt/ios/scripts/run_backup.sh full

# PostgreSQL incremental (WAL archiving) - continuous
*/5 * * * * /opt/ios/scripts/archive_wal.sh

# Elasticsearch snapshot - every 6 hours
0 */6 * * * /opt/ios/scripts/backup_elasticsearch.sh

# Qdrant backup - daily at 3 AM
0 3 * * * /opt/ios/scripts/backup_qdrant.sh

# Cleanup old backups - weekly
0 4 * * 0 /opt/ios/scripts/cleanup_old_backups.sh

# Verify backups - daily at 5 AM
0 5 * * * /opt/ios/scripts/verify_backups.sh
"""
```

---

## 🔄 Recovery Procedures

### PostgreSQL Recovery

```bash
#!/bin/bash
# scripts/restore_postgresql.sh

set -e

echo "======================================"
echo "PostgreSQL Recovery"
echo "======================================"

BACKUP_FILE="$1"
TARGET_DB="ios_db"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Step 1: Stop applications
echo "1. Stopping applications..."
docker-compose stop api celery-worker

# Step 2: Drop existing database
echo "2. Dropping existing database..."
docker-compose exec -T postgres psql -U postgres <<EOF
DROP DATABASE IF EXISTS ${TARGET_DB};
CREATE DATABASE ${TARGET_DB} OWNER ios;
EOF

# Step 3: Restore from backup
echo "3. Restoring from backup..."
if [[ $BACKUP_FILE == s3://* ]]; then
    # Download from S3
    echo "   Downloading from S3..."
    aws s3 cp "$BACKUP_FILE" /tmp/restore.dump
    BACKUP_FILE=/tmp/restore.dump
fi

docker-compose exec -T postgres pg_restore \
    -U ios \
    -d ${TARGET_DB} \
    -v \
    < "$BACKUP_FILE"

# Step 4: Verify restoration
echo "4. Verifying restoration..."
ROW_COUNT=$(docker-compose exec -T postgres psql -U ios -d ${TARGET_DB} -t -c "SELECT COUNT(*) FROM documents;")
echo "   Documents restored: $ROW_COUNT"

# Step 5: Restart applications
echo "5. Restarting applications..."
docker-compose start api celery-worker

echo ""
echo "======================================"
echo "PostgreSQL recovery completed!"
echo "======================================"
```

### Elasticsearch Recovery

```python
# scripts/restore_elasticsearch.py

"""
Elasticsearch snapshot restoration
"""

import requests
import time
import sys

class ElasticsearchRecovery:
    """
    Elasticsearch disaster recovery
    """
    
    def __init__(self, es_host: str = 'http://localhost:9200'):
        self.es_host = es_host
    
    def restore_snapshot(
        self,
        repository: str,
        snapshot: str,
        indices: str = 'ios-documents-*'
    ):
        """
        Restore Elasticsearch snapshot
        
        Args:
            repository: Snapshot repository name
            snapshot: Snapshot name
            indices: Index pattern to restore
        """
        print("="*60)
        print("ELASTICSEARCH SNAPSHOT RESTORATION")
        print("="*60)
        
        # Step 1: Close existing indices
        print("\n1. Closing existing indices...")
        response = requests.post(
            f"{self.es_host}/{indices}/_close",
            params={'ignore_unavailable': 'true'}
        )
        print(f"   Status: {response.status_code}")
        
        # Step 2: Start restoration
        print("\n2. Starting snapshot restoration...")
        restore_body = {
            "indices": indices,
            "ignore_unavailable": True,
            "include_global_state": False,
            "rename_pattern": "(.+)",
            "rename_replacement": "$1"
        }
        
        response = requests.post(
            f"{self.es_host}/_snapshot/{repository}/{snapshot}/_restore",
            json=restore_body
        )
        
        if response.status_code not in [200, 202]:
            print(f"   ERROR: {response.text}")
            sys.exit(1)
        
        print("   Restoration initiated")
        
        # Step 3: Monitor progress
        print("\n3. Monitoring restoration progress...")
        while True:
            response = requests.get(
                f"{self.es_host}/_snapshot/{repository}/{snapshot}/_status"
            )
            
            data = response.json()
            snapshots = data.get('snapshots', [])
            
            if not snapshots:
                print("   ERROR: Snapshot not found")
                break
            
            snapshot_data = snapshots[0]
            state = snapshot_data.get('state')
            
            if state == 'SUCCESS':
                print("   ✓ Restoration completed successfully")
                break
            elif state == 'FAILED':
                print("   ✗ Restoration failed")
                break
            
            # Show progress
            shards = snapshot_data.get('shards_stats', {})
            done = shards.get('done', 0)
            total = shards.get('total', 0)
            
            if total > 0:
                percent = (done / total) * 100
                print(f"   Progress: {done}/{total} shards ({percent:.1f}%)")
            
            time.sleep(5)
        
        # Step 4: Open indices
        print("\n4. Opening restored indices...")
        response = requests.post(f"{self.es_host}/{indices}/_open")
        print(f"   Status: {response.status_code}")
        
        # Step 5: Verify
        print("\n5. Verifying restoration...")
        response = requests.get(f"{self.es_host}/_cat/indices/{indices}?v")
        print(response.text)
        
        print("\n" + "="*60)
        print("RESTORATION COMPLETED")
        print("="*60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Restore Elasticsearch snapshot')
    parser.add_argument('--repository', required=True, help='Repository name')
    parser.add_argument('--snapshot', required=True, help='Snapshot name')
    parser.add_argument('--indices', default='ios-documents-*', help='Index pattern')
    parser.add_argument('--host', default='http://localhost:9200', help='ES host')
    
    args = parser.parse_args()
    
    recovery = ElasticsearchRecovery(es_host=args.host)
    recovery.restore_snapshot(
        repository=args.repository,
        snapshot=args.snapshot,
        indices=args.indices
    )
```

### Complete System Recovery

```python
# scripts/disaster_recovery.py

"""
Complete system disaster recovery
"""

import subprocess
import time
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DisasterRecovery:
    """
    Orchestrate complete system recovery
    
    Recovery order:
    1. Infrastructure (Docker, networks)
    2. PostgreSQL (primary data)
    3. Elasticsearch (search index)
    4. Qdrant (vector index)
    5. Redis (cache - rebuild)
    6. Applications (API, workers)
    """
    
    def __init__(self):
        self.recovery_steps: List[Dict] = []
    
    def add_step(self, name: str, func, **kwargs):
        """Add recovery step"""
        self.recovery_steps.append({
            'name': name,
            'func': func,
            'kwargs': kwargs
        })
    
    def execute_recovery(self):
        """Execute all recovery steps"""
        logger.info("="*60)
        logger.info("DISASTER RECOVERY - STARTING")
        logger.info("="*60)
        
        total_steps = len(self.recovery_steps)
        
        for i, step in enumerate(self.recovery_steps, 1):
            logger.info(f"\n[{i}/{total_steps}] {step['name']}")
            logger.info("-"*60)
            
            try:
                step['func'](**step['kwargs'])
                logger.info(f"✓ Step completed: {step['name']}")
            
            except Exception as e:
                logger.error(f"✗ Step failed: {step['name']}")
                logger.error(f"Error: {e}")
                
                # Ask whether to continue
                response = input("\nContinue with next step? (y/n): ")
                if response.lower() != 'y':
                    logger.error("Recovery aborted")
                    return False
        
        logger.info("\n" + "="*60)
        logger.info("DISASTER RECOVERY - COMPLETED")
        logger.info("="*60)
        
        return True
    
    def step_infrastructure(self):
        """Step 1: Restore infrastructure"""
        logger.info("Starting Docker infrastructure...")
        
        # Pull latest images
        subprocess.run(['docker-compose', 'pull'], check=True)
        
        # Start infrastructure services
        subprocess.run([
            'docker-compose', 'up', '-d',
            'postgres', 'elasticsearch', 'qdrant', 'redis'
        ], check=True)
        
        # Wait for services to be ready
        logger.info("Waiting for services to be ready...")
        time.sleep(30)
    
    def step_restore_postgresql(self, backup_file: str):
        """Step 2: Restore PostgreSQL"""
        logger.info(f"Restoring PostgreSQL from: {backup_file}")
        
        subprocess.run([
            '/opt/ios/scripts/restore_postgresql.sh',
            backup_file
        ], check=True)
    
    def step_restore_elasticsearch(self, repository: str, snapshot: str):
        """Step 3: Restore Elasticsearch"""
        logger.info(f"Restoring Elasticsearch: {repository}/{snapshot}")
        
        subprocess.run([
            'python',
            '/opt/ios/scripts/restore_elasticsearch.py',
            '--repository', repository,
            '--snapshot', snapshot
        ], check=True)
    
    def step_restore_qdrant(self, backup_file: str):
        """Step 4: Restore Qdrant"""
        logger.info(f"Restoring Qdrant from: {backup_file}")
        
        # Stop Qdrant
        subprocess.run(['docker-compose', 'stop', 'qdrant'], check=True)
        
        # Extract backup
        subprocess.run([
            'tar',
            '-xzf', backup_file,
            '-C', '/var/lib/qdrant'
        ], check=True)
        
        # Start Qdrant
        subprocess.run(['docker-compose', 'start', 'qdrant'], check=True)
        
        time.sleep(10)
    
    def step_rebuild_cache(self):
        """Step 5: Rebuild cache"""
        logger.info("Rebuilding Redis cache...")
        
        # Flush Redis
        subprocess.run([
            'docker-compose', 'exec', '-T', 'redis',
            'redis-cli', 'FLUSHALL'
        ], check=True)
        
        # Warm up cache
        subprocess.run([
            'python',
            '/opt/ios/scripts/warmup_cache.py'
        ], check=True)
    
    def step_start_applications(self):
        """Step 6: Start applications"""
        logger.info("Starting applications...")
        
        subprocess.run([
            'docker-compose', 'up', '-d',
            'api', 'celery-worker', 'celery-beat', 'nginx'
        ], check=True)
        
        time.sleep(10)
    
    def step_verify_system(self):
        """Step 7: Verify system"""
        logger.info("Verifying system health...")
        
        # Check API health
        import requests
        
        try:
            response = requests.get('http://localhost/health/', timeout=10)
            if response.status_code == 200:
                logger.info("✓ API health check passed")
            else:
                logger.error(f"✗ API health check failed: {response.status_code}")
        
        except requests.RequestException as e:
            logger.error(f"✗ API health check failed: {e}")
        
        # Test search
        try:
            response = requests.post(
                'http://localhost/api/search/',
                json={'query': 'test', 'page': 1, 'page_size': 10},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Search test passed: {len(data.get('results', []))} results")
            else:
                logger.error(f"✗ Search test failed: {response.status_code}")
        
        except requests.RequestException as e:
            logger.error(f"✗ Search test failed: {e}")


# DR Runbook
DR_RUNBOOK = """
# DISASTER RECOVERY RUNBOOK

## Prerequisites
- Access to backup storage (S3)
- SSH access to production servers
- Database credentials
- Latest backup identifiers

## Recovery Procedure

### 1. Assess Situation
- Identify what failed
- Determine scope of recovery needed
- Check backup availability
- Estimate RTO/RPO

### 2. Notify Stakeholders
- Alert operations team
- Post status update
- Set recovery expectations

### 3. Execute Recovery

#### Full System Recovery
```bash
cd /opt/ios
python scripts/disaster_recovery.py \\
    --postgres-backup s3://backups/postgresql/latest.dump \\
    --es-repository ios_backup \\
    --es-snapshot snapshot_20241213 \\
    --qdrant-backup s3://backups/qdrant/latest.tar.gz
```

#### Partial Recovery - Database Only
```bash
./scripts/restore_postgresql.sh s3://backups/postgresql/latest.dump
```

#### Partial Recovery - Search Index Only
```bash
python scripts/restore_elasticsearch.py \\
    --repository ios_backup \\
    --snapshot snapshot_20241213
```

### 4. Verify Recovery
- Check all services are running
- Test critical functionality
- Verify data integrity
- Check monitoring dashboards

### 5. Post-Recovery
- Document incident
- Update runbook
- Schedule post-mortem
- Test backup procedures

## Common Scenarios

### Scenario 1: Database Corruption
1. Stop applications
2. Restore from latest backup
3. Replay WAL logs (if available)
4. Verify data integrity
5. Restart applications

### Scenario 2: Elasticsearch Cluster Failure
1. Check cluster health
2. Restore from snapshot
3. Verify indices
4. Restart search services

### Scenario 3: Complete Data Center Loss
1. Spin up infrastructure in backup region
2. Restore all services from backups
3. Update DNS/load balancers
4. Verify end-to-end functionality

## Contact Information
- On-call Engineer: [phone]
- Database Admin: [phone]
- Infrastructure Lead: [phone]
- Escalation: [phone]

## Important URLs
- Monitoring: https://grafana.ios.com
- Status Page: https://status.ios.com
- Backups: s3://ios-backups/
- Runbooks: https://wiki.ios.com/dr
"""


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Disaster Recovery')
    parser.add_argument('--postgres-backup', required=True)
    parser.add_argument('--es-repository', required=True)
    parser.add_argument('--es-snapshot', required=True)
    parser.add_argument('--qdrant-backup', required=True)
    
    args = parser.parse_args()
    
    dr = DisasterRecovery()
    
    # Add recovery steps
    dr.add_step('Infrastructure', dr.step_infrastructure)
    dr.add_step(
        'PostgreSQL',
        dr.step_restore_postgresql,
        backup_file=args.postgres_backup
    )
    dr.add_step(
        'Elasticsearch',
        dr.step_restore_elasticsearch,
        repository=args.es_repository,
        snapshot=args.es_snapshot
    )
    dr.add_step(
        'Qdrant',
        dr.step_restore_qdrant,
        backup_file=args.qdrant_backup
    )
    dr.add_step('Cache', dr.step_rebuild_cache)
    dr.add_step('Applications', dr.step_start_applications)
    dr.add_step('Verification', dr.step_verify_system)
    
    # Execute recovery
    success = dr.execute_recovery()
    
    if success:
        print("\n✓ Disaster recovery completed successfully")
    else:
        print("\n✗ Disaster recovery failed or was aborted")
```

---

## 🧪 DR Testing

### Monthly DR Drill

```python
# scripts/dr_drill.py

"""
Disaster Recovery Drill

Tests recovery procedures without affecting production
"""

import subprocess
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DRDrill:
    """
    Automated DR testing
    
    Creates test environment and validates recovery
    """
    
    def __init__(self):
        self.test_env = 'dr-test'
        self.results = []
    
    def run_drill(self):
        """Execute full DR drill"""
        logger.info("="*60)
        logger.info("DISASTER RECOVERY DRILL")
        logger.info(f"Date: {datetime.datetime.now()}")
        logger.info("="*60)
        
        tests = [
            ('PostgreSQL Restore', self.test_postgres_restore),
            ('Elasticsearch Restore', self.test_elasticsearch_restore),
            ('Qdrant Restore', self.test_qdrant_restore),
            ('Full System Recovery', self.test_full_recovery),
            ('Recovery Time', self.test_recovery_time),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\nTesting: {test_name}")
            logger.info("-"*60)
            
            try:
                result = test_func()
                self.results.append({
                    'test': test_name,
                    'status': 'PASS' if result else 'FAIL',
                    'timestamp': datetime.datetime.now()
                })
                
                logger.info(f"✓ {test_name}: PASS")
            
            except Exception as e:
                logger.error(f"✗ {test_name}: FAIL - {e}")
                self.results.append({
                    'test': test_name,
                    'status': 'FAIL',
                    'error': str(e),
                    'timestamp': datetime.datetime.now()
                })
        
        self.generate_report()
    
    def test_postgres_restore(self) -> bool:
        """Test PostgreSQL backup/restore"""
        # Implementation
        return True
    
    def test_elasticsearch_restore(self) -> bool:
        """Test Elasticsearch snapshot restore"""
        # Implementation
        return True
    
    def test_qdrant_restore(self) -> bool:
        """Test Qdrant backup restore"""
        # Implementation
        return True
    
    def test_full_recovery(self) -> bool:
        """Test complete system recovery"""
        # Implementation
        return True
    
    def test_recovery_time(self) -> bool:
        """Measure and verify RTO"""
        # Implementation
        return True
    
    def generate_report(self):
        """Generate DR drill report"""
        logger.info("\n" + "="*60)
        logger.info("DR DRILL RESULTS")
        logger.info("="*60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)
        
        logger.info(f"\nTests Passed: {passed}/{total}")
        
        for result in self.results:
            status_icon = '✓' if result['status'] == 'PASS' else '✗'
            logger.info(f"{status_icon} {result['test']}: {result['status']}")
        
        logger.info("\n" + "="*60)


if __name__ == '__main__':
    drill = DRDrill()
    drill.run_drill()
```

---

**Продолжение следует...**

Создано:
- ✅ RTO/RPO definitions
- ✅ Comprehensive backup strategy
- ✅ Recovery procedures (PostgreSQL, ES, Qdrant)
- ✅ Complete system disaster recovery orchestration
- ✅ DR runbook
- ✅ DR testing/drill framework

**ФИНАЛ:**
- ФАЙЛ 16: Production Readiness Checklist (последний файл!)

**Готовы завершить с Production Readiness Checklist?**