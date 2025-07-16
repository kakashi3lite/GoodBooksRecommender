# ML Pipeline Enhancements - Step 2 Implementation Guide

## Overview

This document describes the comprehensive ML pipeline enhancements implemented for the GoodBooks Recommender system. The enhancements include automated model retraining, A/B testing framework, vector store scaling, and production-grade model management.

## 🚀 Key Features Implemented

### 1. Automated Model Retraining Workflows

#### Airflow Integration
- **Scheduled Retraining**: Weekly automated retraining using Apache Airflow
- **Data Validation**: Comprehensive data quality checks before training
- **Performance Monitoring**: Automatic detection of model degradation
- **Rollback Capability**: Safe rollback to previous versions on failure

#### MLflow Model Versioning
- **Experiment Tracking**: Complete experiment history with metrics and parameters
- **Model Registry**: Centralized model storage with version control
- **Artifact Management**: Automated storage of models and metadata
- **S3 Integration**: Optional S3 backend for scalable artifact storage

#### Dynamic Model Loading
- **Hot-Swapping**: Zero-downtime model updates
- **Model Watching**: Automatic detection of new model versions
- **Fallback Support**: Graceful handling of model loading failures
- **Cache Management**: Intelligent caching of multiple model versions

### 2. Advanced A/B Testing Framework

#### Request Routing
- **Multiple Strategies**: Random, weighted, and staged rollout strategies
- **Traffic Control**: Configurable traffic splitting between variants
- **User Assignment**: Consistent user assignment across requests
- **Context-Aware**: Routing based on user characteristics

#### Real-time Metrics
- **Live Tracking**: Real-time metric collection during experiments
- **Multiple Metrics**: Support for precision, recall, CTR, satisfaction scores
- **Statistical Analysis**: Automated t-tests and confidence intervals
- **Auto-stopping**: Automatic experiment termination based on significance

#### Persistent Storage
- **Redis Integration**: Scalable storage for experiment data
- **Data Retention**: Configurable retention policies
- **Backup/Recovery**: Reliable data persistence across restarts

### 3. Scalable Vector Store Architecture

#### Multi-Backend Support
- **FAISS Optimization**: Hierarchical indices, GPU acceleration, compression
- **Milvus Integration**: Distributed vector database for large-scale deployments
- **Pinecone Support**: Cloud-native vector search with minimal setup

#### Sharding and Distribution
- **Automatic Sharding**: Intelligent data partitioning for large datasets
- **Parallel Processing**: Concurrent search across multiple shards
- **Load Balancing**: Even distribution of query load
- **Memory Optimization**: Efficient memory usage with configurable limits

#### Performance Enhancements
- **Async Operations**: Non-blocking I/O for better concurrency
- **Batch Processing**: Efficient batch embedding generation
- **Connection Pooling**: Optimized database connections
- **Caching**: Intelligent caching of embeddings and results

## 📁 File Structure

```
GoodBooksRecommender/
├── airflow/
│   └── dags/
│       └── goodbooks_retraining_dag.py    # Airflow DAG for retraining
├── config/
│   ├── airflow.cfg                        # Airflow configuration
│   ├── mlflow.env                         # MLflow environment variables
│   └── vector_store.ini                   # Vector store configuration
├── src/
│   ├── core/
│   │   ├── mlflow_integration.py          # MLflow model registry
│   │   └── distributed_vector_store.py   # Enhanced vector store
│   ├── models/
│   │   ├── model_manager.py               # Enhanced with hot-swapping
│   │   └── ab_tester.py                   # Enhanced A/B testing
│   ├── api/
│   │   └── main.py                        # Enhanced with A/B endpoints
│   └── config.py                          # Updated configuration
└── requirements.txt                       # Updated dependencies
```

## 🔧 Setup and Configuration

### 1. Environment Variables

Create a `.env` file with the following configurations:

```bash
# MLflow Configuration
MLFLOW_TRACKING_URI=file:./mlruns
MLFLOW_EXPERIMENT_NAME=goodbooks_recommender
MLFLOW_S3_BUCKET=your-mlflow-bucket  # Optional

# Airflow Configuration
AIRFLOW_HOME=./airflow
AIRFLOW_DAGS_FOLDER=./airflow/dags

# A/B Testing Configuration
AB_TESTING_ENABLED=true
AB_TEST_REDIS_DB=2
AB_TEST_DEFAULT_TRAFFIC_SPLIT=0.1

# Vector Store Configuration
VECTOR_STORE_TYPE=faiss  # faiss, milvus, pinecone
VECTOR_STORE_SHARDING_ENABLED=true
VECTOR_STORE_SHARD_SIZE=50000
VECTOR_STORE_USE_GPU=false

# Model Management
MODEL_WATCHING_ENABLED=true
MODEL_WATCH_INTERVAL=300
MODEL_HOT_SWAP_ENABLED=true

# Distributed Vector DB (Optional)
MILVUS_HOST=localhost
MILVUS_PORT=19530
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-east-1-aws

# AWS S3 (Optional)
S3_BUCKET=your-model-bucket
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 2. Installation

```bash
# Install enhanced dependencies
pip install -r requirements.txt

# Initialize Airflow (first time only)
airflow db init
airflow users create --username admin --password admin \
    --firstname Admin --lastname User --role Admin \
    --email admin@example.com

# Start Airflow services
airflow scheduler &
airflow webserver &

# Start MLflow server (optional)
mlflow server --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlartifacts \
    --host 127.0.0.1 --port 5000 &
```

### 3. API Usage

#### Start A/B Test
```bash
curl -X POST "http://localhost:8000/admin/experiments" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "experiment_id": "new_model_test",
    "description": "Testing new collaborative filter",
    "traffic_split": 0.1,
    "metrics": ["precision", "recall", "click_through_rate"]
  }'
```

#### Get Recommendations with A/B Testing
```bash
curl -X POST "http://localhost:8000/recommendations" \
  -H "X-Experiment-ID: new_model_test" \
  -d '{
    "user_id": 123,
    "n_recommendations": 5
  }'
```

#### Deploy New Model
```bash
curl -X POST "http://localhost:8000/admin/models/deploy" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "model_uri": "models:/goodbooks_hybrid_recommender/1",
    "version": "v1.0.1",
    "metadata": {"deployment_type": "manual"}
  }'
```

## 📊 Monitoring and Metrics

### Airflow Monitoring
- **DAG Status**: Monitor retraining pipeline success/failure
- **Task Logs**: Detailed logs for each pipeline step
- **Alerts**: Email notifications on failures
- **Retry Logic**: Automatic retry on transient failures

### MLflow Tracking
- **Experiment Comparison**: Compare model versions and metrics
- **Artifact Storage**: Access to model files and metadata
- **Model Registry**: Track production deployments
- **Lineage**: Full model training lineage

### A/B Testing Dashboard
- **Real-time Results**: Live experiment metrics
- **Statistical Significance**: Confidence intervals and p-values
- **Traffic Distribution**: Monitor actual vs. expected traffic split
- **Auto-stop Notifications**: Alerts when experiments conclude

### Vector Store Metrics
- **Query Performance**: Search latency and throughput
- **Index Statistics**: Size, memory usage, hit rates
- **Shard Distribution**: Load balancing across shards
- **Backend Health**: Status of Milvus/Pinecone connections

## 🔄 Operational Workflows

### Daily Operations
1. **Monitor Airflow**: Check DAG runs and task statuses
2. **Review A/B Tests**: Check active experiments and results
3. **Model Health**: Verify model performance and availability
4. **System Metrics**: Monitor API performance and errors

### Weekly Operations
1. **Model Retraining**: Review automated retraining results
2. **A/B Test Analysis**: Analyze completed experiments
3. **Performance Review**: Check system-wide performance trends
4. **Capacity Planning**: Monitor resource usage and scaling needs

### Model Deployment Process
1. **Training**: New model trained via Airflow DAG
2. **Validation**: Automated model validation checks
3. **A/B Testing**: Deploy to subset of traffic
4. **Analysis**: Monitor metrics and statistical significance
5. **Full Deployment**: Promote successful models to production
6. **Monitoring**: Continuous performance monitoring

## 🚨 Troubleshooting

### Common Issues

#### Airflow DAG Not Running
```bash
# Check Airflow scheduler status
airflow scheduler --daemon

# Verify DAG syntax
python airflow/dags/goodbooks_retraining_dag.py

# Check logs
tail -f airflow/logs/scheduler/latest/*.log
```

#### MLflow Connection Issues
```bash
# Check MLflow server
curl http://localhost:5000/health

# Restart MLflow server
pkill -f mlflow
mlflow server --backend-store-uri sqlite:///mlflow.db &
```

#### A/B Test Assignment Issues
```bash
# Check Redis connection
redis-cli ping

# Verify experiment status
curl "http://localhost:8000/admin/experiments/test_id/results"

# Clear experiment cache
redis-cli del "ab_experiment:*"
```

#### Vector Store Performance Issues
```bash
# Check vector store statistics
curl "http://localhost:8000/admin/vector-store/stats"

# Rebuild vector store
curl -X POST "http://localhost:8000/admin/vector-store/rebuild"

# Monitor memory usage
ps aux | grep -E "(python|airflow|mlflow)"
```

### Performance Tuning

#### FAISS Optimization
- Increase `nlist` for better recall at the cost of speed
- Enable GPU acceleration for large datasets
- Use compression for memory-constrained environments
- Adjust `efSearch` for HNSW indices

#### A/B Testing Optimization
- Reduce Redis memory usage by adjusting retention policies
- Use staged rollout for gradual traffic increase
- Implement early stopping to reduce experiment duration
- Cache model predictions to reduce computational load

#### Model Management Optimization
- Adjust model cache size based on available memory
- Reduce model watching interval for faster updates
- Use async model loading for better responsiveness
- Implement model compression for faster transfers

## 📈 Scaling Considerations

### Horizontal Scaling
- **Multi-Instance API**: Deploy multiple API instances behind load balancer
- **Airflow Cluster**: Use CeleryExecutor for distributed task execution
- **Redis Cluster**: Scale Redis for high-availability A/B testing
- **Vector Store Sharding**: Distribute vector indices across multiple nodes

### Vertical Scaling
- **GPU Acceleration**: Use GPU-enabled instances for FAISS
- **Memory Optimization**: Increase RAM for larger model caches
- **CPU Scaling**: Use multi-core instances for parallel processing
- **Storage Scaling**: Use SSD storage for faster model loading

### Cloud Deployment
- **Kubernetes**: Use K8s for container orchestration and auto-scaling
- **Managed Services**: Leverage cloud-managed MLflow, Airflow, and vector DBs
- **Auto-scaling**: Implement HPA for dynamic resource allocation
- **Monitoring**: Use cloud monitoring services for comprehensive observability

## 🔐 Security Considerations

### Authentication & Authorization
- **API Keys**: Secure admin endpoints with API key authentication
- **Role-Based Access**: Implement different access levels for different operations
- **Network Security**: Use VPCs and security groups in cloud deployments
- **Encryption**: Encrypt model artifacts and sensitive data at rest and in transit

### Data Privacy
- **User Data**: Ensure user data is properly anonymized in experiments
- **Model Privacy**: Protect proprietary model architectures and parameters
- **Audit Logging**: Log all administrative actions for compliance
- **Data Retention**: Implement proper data retention and deletion policies

This implementation provides a production-ready ML pipeline with comprehensive monitoring, scaling capabilities, and operational excellence features suitable for enterprise deployments.
