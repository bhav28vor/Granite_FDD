# Franchisee Enrichment Pipeline - GCP Enterprise Architecture

## Overview
This document outlines the Google Cloud Platform architecture for deploying the Franchisee Enrichment Pipeline at enterprise scale, supporting both Production and Agentic workflow approaches.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INGESTION LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  📄 FDD Documents  →  📤 Cloud Storage  →  🔔 Pub/Sub Topic                    │
│     (Manual Upload)      (Raw Bucket)        (document-ingestion)              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EXTRACTION LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ⚡ Cloud Function  →  📊 Document AI  →  📤 Cloud Storage                     │
│     (PDF Parser)        (Table Extract)     (Parsed Data)                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ENRICHMENT LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                    🔔 Pub/Sub Topic (enrichment-queue)                         │
│                                     │                                           │
│               ┌─────────────────────┼─────────────────────┐                    │
│               ▼                     ▼                     ▼                    │
│  🏭 Cloud Run          🤖 Cloud Run          📊 Cloud Run                      │
│  (Production Pipeline) (Agentic Pipeline)    (Quality Control)                 │
│  • 88.6% Confidence   • 79% Agent Confidence • Data Validation                │
│  • 4 Data Sources     • LangGraph Workflows  • Confidence Scoring             │
│  • Fast Processing    • Intelligent Routing  • Exception Handling             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  📊 BigQuery                🗄️ Cloud Storage           💾 Firestore            │
│  • Enriched Records        • Processed Files           • Pipeline State        │
│  • Analytics Tables        • Audit Logs               • Configuration          │
│  • Performance Metrics     • Result Archives          • Error Tracking         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MONITORING LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  📈 Cloud Monitoring     🚨 Cloud Alerting     📊 Data Studio Dashboard        │
│  • Pipeline Metrics     • SLA Violations      • Business Analytics            │
│  • Error Rates         • Cost Alerts          • Quality Trends                │
│  • Performance KPIs    • Capacity Planning    • Executive Reports             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Ingestion Layer
**Cloud Storage (Raw Documents)**
- **Purpose**: Secure storage for incoming FDD documents
- **Configuration**: Regional bucket with versioning and lifecycle policies
- **Security**: IAM-controlled access with audit logging
- **Scaling**: Auto-scales to petabyte capacity

**Pub/Sub (Document Ingestion)**
- **Purpose**: Event-driven processing trigger
- **Configuration**: Dead letter queues for failed processing
- **Retention**: 7-day message retention
- **Scaling**: Auto-scales to millions of messages/second

### 2. Extraction Layer
**Cloud Function (PDF Parser)**
- **Runtime**: Python 3.11
- **Memory**: 1GB (adjustable based on document size)
- **Timeout**: 540 seconds
- **Triggers**: Cloud Storage object creation
- **Scaling**: 0 to 3000 concurrent executions

**Document AI (Table Extraction)**
- **Purpose**: Extract franchisee tables from FDD documents
- **Type**: Form Parser processor
- **Integration**: RESTful API calls from Cloud Functions
- **Output**: Structured JSON data

### 3. Enrichment Layer
**Cloud Run (Production Pipeline)**
- **Image**: Container with production enrichment code
- **CPU**: 2 vCPU, 4GB RAM per instance
- **Concurrency**: 80 requests per instance
- **Auto-scaling**: 0 to 100 instances
- **Features**: 88.6% confidence, 4 data sources, enterprise monitoring

**Cloud Run (Agentic Pipeline)**
- **Image**: Container with LangGraph agentic workflows
- **CPU**: 4 vCPU, 8GB RAM per instance (AI workload)
- **Concurrency**: 40 requests per instance
- **Auto-scaling**: 0 to 50 instances
- **Features**: 79% agent confidence, intelligent routing, reasoning logs

**Cloud Run (Quality Control)**
- **Purpose**: Data validation and quality assurance
- **CPU**: 1 vCPU, 2GB RAM
- **Integration**: Validates outputs from both pipelines
- **Rules**: Confidence thresholds, format validation, business rules

### 4. Data Layer
**BigQuery (Analytics Warehouse)**
- **Tables**:
  - `enriched_franchisees`: Final enriched data
  - `pipeline_metrics`: Performance and quality metrics
  - `audit_logs`: Complete processing audit trail
- **Partitioning**: By processing date
- **Clustering**: By franchise brand, state
- **Access**: Row-level security for sensitive data

**Cloud Storage (Processed Data)**
- **Buckets**:
  - `processed-documents`: Successfully processed files
  - `failed-documents`: Documents requiring manual review
  - `archived-results`: Long-term storage for compliance
- **Lifecycle**: Auto-transition to cheaper storage classes

**Firestore (Operational Data)**
- **Collections**:
  - `pipeline_state`: Real-time processing status
  - `configuration`: Dynamic pipeline configuration
  - `error_tracking`: Error categorization and resolution

### 5. Monitoring Layer
**Cloud Monitoring**
- **Custom Metrics**:
  - Pipeline throughput (records/hour)
  - Confidence score distributions
  - Data source success rates
  - Cost per enriched record
- **SLI/SLO**: 99.5% availability, <5 minute processing time

**Cloud Alerting**
- **Alert Policies**:
  - Pipeline failures (immediate)
  - Quality degradation (confidence < 80%)
  - Cost anomalies (>20% budget variance)
  - Capacity limits (>80% resource utilization)

**Data Studio Dashboard**
- **Business Metrics**: Daily enrichment volumes, quality trends
- **Operational Metrics**: Pipeline performance, error rates
- **Cost Analytics**: Resource utilization, optimization opportunities

## Security Architecture

### Identity & Access Management (IAM)
```
Service Accounts:
├── enrichment-pipeline-sa          (Cloud Run services)
├── document-parser-sa               (Cloud Functions)
├── monitoring-sa                    (Cloud Monitoring)
└── analyst-sa                       (Data Studio, BigQuery read-only)

Custom Roles:
├── franchisee.dataProcessor         (Pipeline operations)
├── franchisee.qualityReviewer       (Data validation)
└── franchisee.businessAnalyst       (Dashboard access)
```

### Network Security
- **VPC**: Private Google Access for Cloud Run
- **Firewall**: Ingress rules for authenticated services only
- **Cloud Endpoints**: API gateway for external integrations
- **Private Service Connect**: Secure BigQuery access

### Data Security
- **Encryption**: Data encrypted at rest and in transit
- **DLP API**: Scan for PII in documents before processing
- **Audit Logging**: Complete audit trail for compliance
- **Backup Strategy**: Cross-region replication for disaster recovery

## Scaling Strategy

### Horizontal Scaling
**Cloud Run Auto-scaling**
```yaml
Production Pipeline:
  min_instances: 1
  max_instances: 100
  target_concurrency: 80
  cpu_threshold: 70%

Agentic Pipeline:
  min_instances: 0
  max_instances: 50
  target_concurrency: 40
  cpu_threshold: 60%
```

**BigQuery Scaling**
- **Slots**: Auto-scaling compute (500-2000 slots)
- **Storage**: Automatic partitioning and clustering
- **Query Optimization**: Materialized views for common analytics

### Vertical Scaling
**Resource Allocation by Workload**
```
Document Processing: 1 vCPU, 2GB RAM
Production Enrichment: 2 vCPU, 4GB RAM  
Agentic Enrichment: 4 vCPU, 8GB RAM
Quality Control: 1 vCPU, 2GB RAM
```

### Performance Optimization
- **Batch Processing**: Process documents in optimal batch sizes
- **Parallel Execution**: Concurrent enrichment of multiple records
- **Caching Strategy**: Redis for frequently accessed data sources
- **CDN**: Cloud CDN for static assets and API responses

## Cost Optimization

### Resource Management
**Cloud Run Cost Controls**
- **CPU Allocation**: Right-sized for workload requirements
- **Request Timeout**: Optimized timeouts to prevent resource waste
- **Concurrency**: Tuned for maximum efficiency
- **Cold Start Optimization**: Minimize container startup time

**Storage Cost Management**
- **Lifecycle Policies**: Auto-transition to cheaper storage classes
  - Nearline (30 days): Infrequently accessed data
  - Coldline (90 days): Backup and archive data
  - Archive (365 days): Long-term compliance storage
- **Data Retention**: Automated cleanup of temporary processing data

### Monitoring & Budgets
**Budget Alerts**
- **Monthly Budget**: $5,000/month for production workload
- **Alert Thresholds**: 50%, 80%, 90%, 100% of budget
- **Cost Attribution**: Detailed labeling for cost analysis

**Resource Optimization**
- **Committed Use Discounts**: 1-year commit for stable workloads
- **Sustained Use Discounts**: Automatic discounts for consistent usage
- **Preemptible Instances**: For non-critical batch processing

## Deployment Strategy

### Environment Management
```
Development Environment:
├── Reduced resource limits
├── Sample data processing
├── Feature development and testing
└── Cost: ~$200/month

Staging Environment:
├── Production-like configuration
├── Full-scale testing
├── Performance validation
└── Cost: ~$1,000/month

Production Environment:
├── Full resource allocation
├── 99.5% availability SLA
├── Complete monitoring and alerting
└── Cost: ~$5,000/month
```

### CI/CD Pipeline
**Cloud Build Configuration**
```yaml
Pipeline Stages:
1. Code Quality: Linting, type checking, security scanning
2. Unit Testing: Automated test suite execution
3. Integration Testing: End-to-end pipeline validation
4. Container Building: Docker image creation and scanning
5. Deployment: Rolling deployment to Cloud Run
6. Monitoring: Health checks and performance validation
```

### Infrastructure as Code
**Terraform Modules**
- **Core Infrastructure**: VPC, IAM, security policies
- **Data Pipeline**: Cloud Run services, Pub/Sub, Cloud Functions
- **Data Storage**: BigQuery datasets, Cloud Storage buckets
- **Monitoring**: Dashboards, alerts, log sinks

## Business Continuity

### Disaster Recovery
**Recovery Objectives**
- **RTO (Recovery Time Objective)**: 1 hour
- **RPO (Recovery Point Objective)**: 15 minutes
- **Cross-Region Backup**: Automated replication to secondary region

**Backup Strategy**
- **Database Backups**: Daily BigQuery exports to Cloud Storage
- **Code Repository**: Multi-region Git repositories
- **Configuration**: Infrastructure as Code in version control
- **Documentation**: Regularly updated runbooks and procedures

### High Availability
**Multi-Zone Deployment**
- **Cloud Run**: Automatic multi-zone distribution
- **Load Balancing**: Global HTTP(S) Load Balancer
- **Health Checks**: Automated failover for unhealthy instances
- **Data Replication**: Cross-zone BigQuery and Storage replication

## Success Metrics

### Business KPIs
- **Processing Volume**: 10,000+ documents per day
- **Data Quality**: >95% confidence score achievement
- **Processing Speed**: <5 minutes end-to-end processing
- **Cost Efficiency**: <$0.50 per enriched franchisee record

### Technical SLIs
- **Availability**: 99.5% uptime
- **Latency**: P95 < 2 seconds for enrichment API
- **Error Rate**: <0.1% processing failures
- **Scalability**: Handle 10x traffic spikes without degradation

### Operational Metrics
- **Mean Time to Recovery (MTTR)**: <30 minutes
- **Change Failure Rate**: <2%
- **Deployment Frequency**: Daily deployments
- **Lead Time**: <24 hours from code to production

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- ✅ Set up GCP project and basic infrastructure
- ✅ Deploy production pipeline to Cloud Run
- ✅ Configure BigQuery data warehouse
- ✅ Implement basic monitoring and alerting

### Phase 2: Advanced Features (Week 3-4)
- ✅ Deploy agentic pipeline with LangGraph
- ✅ Implement quality control automation
- ✅ Set up comprehensive monitoring dashboard
- ✅ Configure security and compliance controls

### Phase 3: Optimization (Week 5-6)
- ✅ Performance tuning and cost optimization
- ✅ Advanced analytics and business intelligence
- ✅ Disaster recovery testing and validation
- ✅ Documentation and team training

### Phase 4: Scale & Enhance (Ongoing)
- 🔄 Continuous performance optimization
- 🔄 New data source integrations
- 🔄 Advanced AI/ML capabilities
- 🔄 Business intelligence enhancements

## Conclusion

This architecture provides a robust, scalable, and cost-effective solution for enterprise-scale franchisee data enrichment. The dual-pipeline approach (Production + Agentic) demonstrates both reliable business operations and innovative AI capabilities, positioning the organization for current needs and future growth.

The cloud-native design leverages GCP's managed services to minimize operational overhead while maximizing scalability and reliability. Comprehensive monitoring and security controls ensure enterprise-grade operations suitable for sensitive business data processing.