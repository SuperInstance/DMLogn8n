# DMLogn8n Backup and Restore System

A comprehensive, production-ready backup and restore solution for the DMLogn8n multi-agent platform. This system provides automated backup scheduling, point-in-time recovery, cross-environment backup management, and disaster recovery capabilities.

## 🚀 Features

### Core Capabilities
- **Automated Backup Scheduling** - Configurable cron-based scheduling for all data stores
- **Point-in-Time Recovery** - Restore to any point in time with transaction log support
- **Cross-Environment Backup** - Support for dev, staging, and production environments
- **Incremental and Full Backups** - Optimized backup strategies with compression
- **Backup Validation** - Integrity checking and corruption detection
- **Disaster Recovery** - Automated failover and recovery procedures

### Supported Data Stores
- **PostgreSQL** - Database backups with WAL support
- **Redis** - Cache and session data backups
- **Qdrant** - Vector database and embedding backups
- **Configuration Files** - Environment settings and application config
- **File Systems** - User uploads, logs, and application files
- **AI Models** - Model checkpoints and training data

### Storage Backends
- **Local Storage** - File system storage with deduplication
- **AWS S3** - Cloud storage with cross-region replication
- **Google Cloud Storage** - Cloud storage with lifecycle management
- **Hybrid Storage** - Multi-cloud storage strategies

### Security & Compliance
- **Encryption at Rest** - AES-256 encryption for all backups
- **Encryption in Transit** - TLS/SSL for data transfer
- **Access Control** - Role-based access management
- **Audit Logging** - Comprehensive operation logging
- **Compliance Reporting** - Regulatory compliance support

## 📁 Architecture

```
backup/
├── backup_service.py          # Main backup orchestration service
├── restorer.py                # Restore functionality with validation
├── disaster_recovery.py       # Disaster recovery automation
├── schedulers/                # Backup scheduling components
│   ├── database_scheduler.py  # Database backup scheduler
│   ├── file_scheduler.py      # File system backup scheduler
│   └── config_scheduler.py    # Configuration backup scheduler
├── storage/                   # Storage backend implementations
│   ├── local_storage.py       # Local file system storage
│   ├── s3_storage.py          # AWS S3 storage
│   └── gcs_storage.py         # Google Cloud Storage
├── validators/                # Backup validation components
│   ├── integrity_validator.py # Checksum validation
│   └── restore_validator.py   # Restore validation
├── config/                    # Configuration files
├── logs/                      # System logs
├── scripts/                   # Utility scripts
└── runbooks/                  # Disaster recovery runbooks
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Docker (optional)
- AWS CLI (for S3 storage)
- Google Cloud CLI (for GCS storage)

### Setup

1. **Clone the repository**
```bash
cd /home/activeloguser/DMLogn8n/multi-portal-gateway/backup
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Set up databases**
```bash
# The system will automatically initialize the backup metadata database
```

5. **Configure storage backends**
```bash
# Edit config/backup_config.yaml for your storage preferences
# Set up AWS credentials for S3: aws configure
# Set up GCP credentials for GCS: gcloud auth application-default login
```

## 🔧 Configuration

### Main Configuration (`config/backup_config.yaml`)

```yaml
storage:
  local:
    backup_path: "/path/to/local/backup"
    compression_level: 6
    deduplication: true
    encryption: true

  s3:
    bucket: "your-backup-bucket"
    region: "us-east-1"
    access_key_id: "${AWS_ACCESS_KEY_ID}"
    secret_access_key: "${AWS_SECRET_ACCESS_KEY}"

schedules:
  database_full: "0 2 * * 0"      # Weekly full backup
  database_incremental: "0 3 * * *"  # Daily incremental
  files_full: "0 1 * * 0"          # Weekly files backup
  config: "0 4 * * *"              # Daily config backup

retention:
  daily_retention_days: 7
  weekly_retention_weeks: 4
  monthly_retention_months: 12
```

### Database Configuration (`config/databases.yaml`)

```yaml
databases:
  postgresql_main:
    type: postgresql
    host: localhost
    port: 5432
    database: dmlogn8n
    username: postgres
    password: "${POSTGRES_PASSWORD}"
    backup_method: logical_dump
    compression_level: 6

  redis_cache:
    type: redis
    host: localhost
    port: 6379
    database: 0
    backup_method: snapshot
```

## 📋 Usage

### Starting the Backup Service

```bash
# Start the main backup service
python backup_service.py

# Start with specific configuration
python backup_service.py --config config/backup_config.yaml
```

### Manual Backup Operations

```python
from backup_service import BackupService

# Initialize service
backup_service = BackupService()

# Start immediate backup
backup_id = await backup_service.start_backup_now('database_full', 'full')

# Check backup status
status = backup_service.get_backup_status(backup_id)
```

### Restore Operations

```python
from restorer import RestoreService

# Initialize restore service
restore_service = RestoreService()

# Create restore request
restore_request = {
    'restore_id': 'restore_001',
    'backup_id': 'backup_123',
    'restore_type': 'full',
    'scope': 'all',
    'validate_before_restore': True,
    'create_rollback_point': True
}

# Initiate restore
restore_id = await restore_service.initiate_restore(restore_request)
```

### Disaster Recovery

```python
from disaster_recovery import DisasterRecoverySystem

# Initialize DR system
dr_system = DisasterRecoverySystem()

# Detect disaster event
disaster_event = await dr_system.detect_disaster({
    'description': 'Database server failure',
    'affected_systems': ['database'],
    'severity': 'critical'
})

# Initiate recovery
recovery_operation = await dr_system.initiate_recovery(disaster_event)
```

## 📊 Monitoring

### Prometheus Metrics

The system exports Prometheus metrics on port 8090:

- `backup_operations_total` - Total backup operations by type and status
- `backup_duration_seconds` - Backup duration histogram
- `backup_size_bytes` - Backup size gauge
- `restore_operations_total` - Total restore operations
- `active_backups` - Number of active backup operations

### Health Checks

```bash
# Check service health
curl http://localhost:8090/health

# Get metrics
curl http://localhost:8090/metrics
```

### Log Monitoring

```bash
# View backup logs
tail -f logs/backup_service.log

# View restore logs
tail -f logs/restore.log
```

## 🔒 Security

### Encryption

All backups are encrypted using AES-256 encryption by default:

```yaml
encryption:
  enabled: true
  key_rotation_days: 90
  algorithm: "AES256"
```

### Access Control

Configure role-based access control in the configuration:

```yaml
access_control:
  roles:
    admin:
      permissions: ["*"]
    operator:
      permissions: ["backup:read", "backup:create", "restore:read"]
    viewer:
      permissions: ["backup:read", "restore:read"]
```

### Audit Logging

All operations are logged with comprehensive audit trails:

```bash
# View audit logs
grep "AUDIT" logs/backup_service.log
```

## 🧪 Testing

### Backup Validation

```bash
# Validate backup integrity
python -c "
from validators.integrity_validator import IntegrityValidator
validator = IntegrityValidator()
result = await validator.validate_backup('backup_123')
print(result)
"
```

### Disaster Recovery Testing

```bash
# Run DR test
python disaster_recovery.py --test --scenario system_failure

# Generate DR test report
python disaster_recovery.py --report --last-test
```

### Restore Testing

```bash
# Test restore in staging
python restorer.py --test --backup-id backup_123 --environment staging
```

## 📈 Performance Optimization

### Backup Optimization

1. **Parallel Processing** - Enable parallel backup operations
2. **Compression** - Optimize compression levels based on data type
3. **Deduplication** - Enable block-level deduplication
4. **Incremental Backups** - Use incremental backups for large datasets

### Storage Optimization

1. **Tiered Storage** - Use different storage classes for different data ages
2. **Lifecycle Policies** - Implement automated data lifecycle management
3. **Cross-Region Replication** - Replicate critical backups across regions

### Network Optimization

1. **Bandwidth Throttling** - Limit backup bandwidth during peak hours
2. **Compression** - Reduce network transfer with compression
3. **Multipart Uploads** - Use multipart uploads for large files

## 🚨 Troubleshooting

### Common Issues

1. **Backup Fails with Permission Error**
   ```bash
   # Check permissions
   ls -la /home/activeloguser/DMLogn8n/multi-portal-gateway/backup/
   # Fix permissions
   chmod 750 /home/activeloguser/DMLogn8n/multi-portal-gateway/backup/
   ```

2. **S3 Upload Fails**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   # Test S3 access
   aws s3 ls s3://your-backup-bucket
   ```

3. **Database Backup Fails**
   ```bash
   # Check PostgreSQL connection
   psql -h localhost -U postgres -d dmlogn8n
   # Check disk space
   df -h
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Analysis

```bash
# Search for errors
grep "ERROR" logs/backup_service.log

# Analyze performance
grep "backup completed" logs/backup_service.log | tail -10

# Monitor active operations
grep "active_backups" logs/backup_service.log
```

## 📚 API Reference

### Backup Service API

```python
# Get backup status
GET /api/v1/backups/{backup_id}/status

# List backups
GET /api/v1/backups?limit=50&status=completed

# Start backup
POST /api/v1/backups
{
  "job_name": "database_full",
  "backup_type": "full"
}

# Get service health
GET /api/v1/health
```

### Restore Service API

```python
# Initiate restore
POST /api/v1/restores
{
  "backup_id": "backup_123",
  "restore_type": "full",
  "scope": "all"
}

# Get restore status
GET /api/v1/restores/{restore_id}/status

# List restore operations
GET /api/v1/restores?limit=50
```

## 🔄 Maintenance

### Regular Tasks

1. **Weekly**
   - Review backup logs
   - Check storage usage
   - Validate critical backups

2. **Monthly**
   - Test restore procedures
   - Update encryption keys
   - Review retention policies

3. **Quarterly**
   - Full disaster recovery test
   - Performance optimization review
   - Security audit

### Cleanup Operations

```bash
# Clean up old logs
find logs/ -name "*.log" -mtime +30 -delete

# Clean up temporary files
find /tmp -name "backup_*" -mtime +1 -delete

# Cleanup old metadata
python scripts/cleanup_metadata.py --days 90
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [Link to comprehensive docs]
- **Issues**: [GitHub Issues]
- **Email**: support@dmlogn8n.com
- **Slack**: #dmlogn8n-backups

## 🗺️ Roadmap

- [ ] Web UI for backup management
- [ ] Multi-cloud storage orchestration
- [ ] Advanced backup analytics
- [ ] Machine learning for backup optimization
- [ ] Blockchain-based backup verification
- [ ] Edge computing support