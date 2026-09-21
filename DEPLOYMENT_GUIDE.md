# DMLog Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying DMLog to production using the complete infrastructure setup created in Phase 6.

## Architecture Overview

The DMLog production infrastructure consists of:

1. **Kubernetes Cluster** (Amazon EKS)
   - Multi-node cluster with auto-scaling
   - High availability across multiple AZs
   - Proper resource limits and requests

2. **Application Components**
   - Backend API services (FastAPI)
   - Frontend web application (React)
   - PostgreSQL database (RDS)
   - Redis cache (ElastiCache)

3. **Monitoring & Logging**
   - Prometheus for metrics collection
   - Grafana for visualization
   - ELK stack (Elasticsearch, Logstash, Kibana) for log aggregation
   - Loki for log aggregation (alternative to ELK)
   - Fluent Bit for log shipping

4. **Security & Compliance**
   - Pod Security Policies
   - Network Policies
   - Certificate management (cert-manager)
   - Security scanning (Trivy, Falco)
   - WAF configuration

5. **Performance Optimization**
   - CloudFront CDN
   - Redis caching strategy
   - Load balancing with Nginx
   - Auto-scaling configurations

## Prerequisites

### Required Tools
- Terraform >= 1.5.0
- kubectl >= 1.28
- Helm >= 3.10
- AWS CLI >= 2.0
- Docker >= 20.10

### AWS Services Required
- AWS Account with appropriate permissions
- Route 53 domain (dmlog.com)
- ACM certificate for SSL
- S3 buckets for static assets and logs
- IAM roles and policies

### Environment Setup
```bash
# Set up AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"

# Configure kubectl
aws eks update-kubeconfig --name dmlog-prod-cluster --region us-west-2

# Verify cluster access
kubectl get nodes
```

## Deployment Steps

### 1. Infrastructure Deployment (Terraform)

#### 1.1 Initialize Terraform
```bash
cd deploy/terraform/environments/production

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the changes
terraform apply
```

#### 1.2 Verify Infrastructure
```bash
# Check EKS cluster
aws eks describe-cluster --name dmlog-prod-cluster

# Check VPC and subnets
aws ec2 describe-vpcs --filters Name=tag:Name,Values=dmlog-production-vpc

# Check RDS instance
aws rds describe-db-instances --db-instance-identifier dmlog-production-db

# Check ElastiCache cluster
aws elasticache describe-replication-groups --replication-group-id dmlog-production-replica-group
```

### 2. Kubernetes Cluster Setup

#### 2.1 Install Essential Add-ons
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Install metrics-server for HPA
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

#### 2.2 Configure Security
```bash
# Apply Pod Security Policies
kubectl apply -f deploy/security/pod-security-policy.yaml

# Apply Network Policies
kubectl apply -f deploy/security/network-policy.yaml

# Configure certificate management
kubectl apply -f deploy/security/certificate-management.yaml
```

#### 2.3 Deploy Monitoring Stack
```bash
# Deploy Prometheus
kubectl apply -f deploy/monitoring/prometheus.yaml

# Deploy Grafana
kubectl apply -f deploy/monitoring/grafana.yaml

# Deploy Elasticsearch
kubectl apply -f deploy/monitoring/elasticsearch.yaml

# Deploy Kibana
kubectl apply -f deploy/monitoring/kibana.yaml

# Deploy Loki (optional)
kubectl apply -f deploy/monitoring/loki.yaml

# Deploy Fluent Bit for log shipping
kubectl apply -f deploy/monitoring/fluent-bit.yaml
```

### 3. Application Deployment

#### 3.1 Create Secrets
```bash
# Create application secrets
kubectl create secret generic dmlog-secrets \
  --from-literal=DATABASE_URL="postgresql://user:password@host:5432/dbname" \
  --from-literal=REDIS_PASSWORD="your-redis-password" \
  --from-literal=SECRET_KEY="your-secret-key" \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --from-literal=ANTHROPIC_API_KEY="your-anthropic-key" \
  --namespace dmlog

# Create registry credentials
kubectl create secret docker-registry registry-credentials \
  --docker-server=ghcr.io \
  --docker-username=your-github-username \
  --docker-password=your-github-token \
  --namespace dmlog
```

#### 3.2 Deploy Using Helm
```bash
# Deploy the application
helm upgrade --install dmlog ./deploy/helm/dmlog \
  --namespace dmlog \
  --create-namespace \
  --values ./deploy/helm/dmlog/values-production.yaml \
  --wait \
  --timeout=15m
```

#### 3.3 Deploy Using Manifests (Alternative)
```bash
# Create namespace
kubectl apply -f deploy/kubernetes/namespace.yaml

# Apply configurations
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secrets.yaml

# Deploy databases
kubectl apply -f deploy/kubernetes/database-deployment.yaml
kubectl apply -f deploy/kubernetes/redis-deployment.yaml

# Deploy applications
kubectl apply -f deploy/kubernetes/backend-deployment.yaml
kubectl apply -f deploy/kubernetes/frontend-deployment.yaml

# Configure ingress and autoscaling
kubectl apply -f deploy/kubernetes/ingress.yaml
kubectl apply -f deploy/kubernetes/hpa.yaml

# Configure service accounts and RBAC
kubectl apply -f deploy/kubernetes/service-account.yaml
```

### 4. Performance Optimization Setup

#### 4.1 Configure CDN
```bash
# Apply CloudFront configuration
kubectl apply -f deploy/performance/cloudfront.yaml

# Update DNS records to point to CloudFront
# This needs to be done manually in Route 53 or via Terraform
```

#### 4.2 Configure Advanced Caching
```bash
# Deploy Redis cluster with advanced caching
kubectl apply -f deploy/performance/caching-strategy.yaml

# Configure load balancer
kubectl apply -f deploy/performance/load-balancer.yaml
```

### 5. Security Configuration

#### 5.1 Set up Security Scanning
```bash
# Deploy security scanners
kubectl apply -f deploy/security/security-scanner.yaml

# Verify security policies are in place
kubectl get podsecuritypolicies
kubectl get networkpolicies --all-namespaces
```

#### 5.2 Configure WAF
```bash
# AWS WAF should be configured via the Terraform scripts
# Verify WAF is attached to CloudFront distribution
aws wafv2 get-web-acl --name DMLogWebACL --scope CLOUDFRONT
```

## Verification Checklist

### Infrastructure Verification
- [ ] EKS cluster is running and healthy
- [ ] All nodes are ready
- [ ] RDS database is accessible
- [ ] Redis cluster is accessible
- [ ] S3 buckets are created and configured
- [ ] CloudFront distribution is deployed
- [ ] SSL certificates are valid

### Application Verification
- [ ] Backend services are running
- [ ] Frontend application is accessible
- [ ] Database connections are working
- [ ] Redis cache is working
- [ ] API endpoints are responding
- [ ] Static assets are loading

### Monitoring Verification
- [ ] Prometheus is collecting metrics
- [ ] Grafana dashboards are accessible
- [ ] Logs are being collected and searchable
- [ ] Alerts are configured and working
- [ ] Health checks are passing

### Security Verification
- [ ] Pod Security Policies are enforced
- [ ] Network Policies are working
- [ ] SSL certificates are valid
- [ ] WAF is blocking malicious requests
- [ ] Security scanners are running

### Performance Verification
- [ ] CDN is caching static assets
- [ ] Redis cache is working
- [ ] Load balancer is distributing traffic
- [ ] Auto-scaling is working
- [ ] Response times are acceptable

## Maintenance and Operations

### Daily Checks
```bash
# Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces

# Check resource usage
kubectl top nodes
kubectl top pods --all-namespaces

# Check logs
kubectl logs -n dmlog -l app=dmlog --tail=100

# Check monitoring
curl http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up
```

### Weekly Maintenance
```bash
# Update certificates (cert-manager handles this automatically)
kubectl get certificates --all-namespaces

# Check security scan results
kubectl get cronjobs -n dmlog
kubectl logs -n dmlog job/trivy-security-scanner-<timestamp>

# Review and update resource limits
kubectl describe pods -n dmlog
```

### Monthly Maintenance
```bash
# Update Kubernetes versions
aws eks update-cluster-version --name dmlog-prod-cluster --kubernetes-version <new-version>

# Update Helm charts
helm repo update
helm upgrade dmlog ./deploy/helm/dmlog --values ./deploy/helm/dmlog/values-production.yaml

# Review and update Terraform configurations
cd deploy/terraform/environments/production
terraform plan
```

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting
```bash
# Check pod status and events
kubectl describe pod <pod-name> -n dmlog

# Check resource limits
kubectl describe nodes

# Check logs
kubectl logs <pod-name> -n dmlog
```

#### 2. Database Connection Issues
```bash
# Check database connectivity
kubectl exec -it <backend-pod> -n dmlog -- nc -zv postgresql-service 5432

# Check database logs
aws rds describe-db-log-files --db-instance-identifier dmlog-production-db
```

#### 3. Cache Issues
```bash
# Check Redis connectivity
kubectl exec -it <backend-pod> -n dmlog -- redis-cli -h redis-service -p 6379 ping

# Check Redis logs
kubectl logs -l app=redis -n dmlog
```

#### 4. SSL Certificate Issues
```bash
# Check certificate status
kubectl describe certificate dmlog-wildcard -n cert-manager

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager
```

### Emergency Procedures

#### 1. Application Rollback
```bash
# Rollback using Helm
helm rollback dmlog <previous-revision> -n dmlog

# Rollback using kubectl
kubectl rollout undo deployment/backend-deployment -n dmlog
kubectl rollout undo deployment/frontend-deployment -n dmlog
```

#### 2. Database Recovery
```bash
# Create snapshot (automated, but can be manual)
aws rds create-db-snapshot --db-instance-identifier dmlog-production-db --db-snapshot-identifier emergency-snapshot-$(date +%Y%m%d-%H%M%S)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot --db-instance-identifier dmlog-production-db-restored --db-snapshot-identifier <snapshot-id>
```

#### 3. Scale Emergency
```bash
# Scale up quickly
kubectl scale deployment backend-deployment --replicas=10 -n dmlog
kubectl scale deployment frontend-deployment --replicas=5 -n dmlog

# Scale down after emergency
kubectl scale deployment backend-deployment --replicas=3 -n dmlog
kubectl scale deployment frontend-deployment --replicas=2 -n dmlog
```

## Security Best Practices

1. **Regular Updates**: Keep all components updated to latest versions
2. **Access Control**: Use principle of least privilege for all access
3. **Monitoring**: Set up alerts for security events
4. **Backup**: Regular backups and test restoration procedures
5. **Audit**: Regular security audits and penetration testing
6. **Secrets Management**: Use external secret stores for production secrets
7. **Network Security**: Implement proper network segmentation
8. **Compliance**: Ensure compliance with relevant standards (SOC2, HIPAA, etc.)

## Support

For issues and support:
1. Check monitoring dashboards for alerts
2. Review logs in Kibana/Loki
3. Check GitHub Issues for known problems
4. Contact the infrastructure team for critical issues

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Terraform Documentation](https://www.terraform.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)