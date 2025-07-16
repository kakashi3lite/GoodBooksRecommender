# Redis Cluster Configuration Guide

## Overview

This guide covers setting up Redis clustering for production deployment of the GoodBooks Recommender system. We support both managed cloud services and manual cluster setup.

## Managed Redis Cluster Options

### AWS ElastiCache for Redis
- **Recommended for AWS deployments**
- Automatic failover and multi-AZ deployment
- Built-in monitoring and backup
- Supports Redis Cluster mode with sharding

### Google Cloud Memorystore
- **Recommended for GCP deployments**
- High availability with automatic failover
- Built-in monitoring and alerting
- VPC-native connectivity

### Azure Cache for Redis
- **Recommended for Azure deployments**
- Enterprise tier supports clustering
- Built-in backup and geo-replication
- Integration with Azure Monitor

## Manual Redis Cluster Setup

### Prerequisites
- 6 Redis instances minimum (3 masters, 3 replicas)
- Network connectivity between all nodes
- Consistent Redis version across all nodes

### Cluster Configuration

#### Environment Variables for Cluster Mode
```bash
# Redis Cluster Configuration
REDIS_CLUSTER_ENABLED=true
REDIS_CLUSTER_NODES=redis-1:6379,redis-2:6379,redis-3:6379,redis-4:6379,redis-5:6379,redis-6:6379
REDIS_CLUSTER_SLOTS_REFRESH_INTERVAL=10
REDIS_CLUSTER_MAX_REDIRECTIONS=3
REDIS_CLUSTER_RETRY_ON_FAIL=true
REDIS_PASSWORD=your-secure-password
```

#### Docker Compose for Redis Cluster
```yaml
version: '3.8'

services:
  redis-1:
    image: redis:7-alpine
    command: >
      redis-server 
      --cluster-enabled yes 
      --cluster-config-file nodes.conf 
      --cluster-node-timeout 5000 
      --appendonly yes
      --requirepass ${REDIS_PASSWORD}
    ports:
      - "7001:6379"
    volumes:
      - redis-1-data:/data
    networks:
      - redis-cluster

  redis-2:
    image: redis:7-alpine
    command: >
      redis-server 
      --cluster-enabled yes 
      --cluster-config-file nodes.conf 
      --cluster-node-timeout 5000 
      --appendonly yes
      --requirepass ${REDIS_PASSWORD}
    ports:
      - "7002:6379"
    volumes:
      - redis-2-data:/data
    networks:
      - redis-cluster

  # ... repeat for redis-3 through redis-6

networks:
  redis-cluster:
    driver: bridge

volumes:
  redis-1-data:
  redis-2-data:
  # ... repeat for all nodes
```

## Session Data Persistence During Outages

### Failover Strategy
1. **Automatic Failover**: Redis Sentinel or cluster mode handles automatic promotion
2. **Data Replication**: All writes are replicated to slave nodes
3. **Session Recovery**: Application implements exponential backoff for reconnection

### Graceful Degradation
- In-memory fallback when Redis is unavailable
- Session data persisted to database for critical operations
- Cache warming on Redis recovery

## Testing Cluster Setup

### Connection Test
```bash
# Test cluster connectivity
redis-cli -c -h redis-cluster-endpoint -p 6379 -a your-password ping

# Check cluster status
redis-cli -c -h redis-cluster-endpoint -p 6379 -a your-password cluster nodes
```

### Failover Test
```bash
# Simulate node failure
docker stop redis-1

# Verify automatic failover
redis-cli -c -h redis-cluster-endpoint -p 6379 -a your-password cluster nodes
```

## Performance Tuning

### Memory Optimization
```
# Redis memory settings
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Network Optimization
```
# Network timeouts
timeout 300
tcp-keepalive 300
tcp-backlog 511
```

## Monitoring Cluster Health

### Key Metrics to Monitor
- Cluster state and node availability
- Memory usage per node
- Network latency between nodes
- Failed operations and redirections
- Master-slave lag

### Alerting Thresholds
- Node down: Immediate alert
- Memory usage > 80%: Warning
- Master-slave lag > 10s: Critical
- Failed operations > 1%: Warning

## Security Considerations

### Network Security
- Use VPC/private networks for cluster communication
- Enable Redis AUTH with strong passwords
- Consider TLS encryption for sensitive data

### Access Control
- Implement Redis ACLs for fine-grained permissions
- Regular password rotation
- Network-level access restrictions

## Backup and Recovery

### Automated Backups
- Daily RDB snapshots
- AOF persistence for point-in-time recovery
- Cross-region backup replication

### Recovery Procedures
1. Identify the scope of data loss
2. Stop application writes
3. Restore from latest consistent backup
4. Verify data integrity
5. Resume application operations

## Cost Optimization

### Managed Services
- Use reserved instances for predictable workloads
- Enable compression for data transfer
- Right-size instances based on actual usage

### Self-Managed
- Use smaller instances with more nodes for better cost/performance
- Implement data sharding to distribute load
- Monitor and optimize memory usage patterns
