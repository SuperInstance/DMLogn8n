#!/bin/bash

# DMLog Production Deployment Script
# This script automates the complete production deployment process

set -euo pipefail

# Configuration
ENVIRONMENT="production"
AWS_REGION="us-west-2"
CLUSTER_NAME="dmlog-prod-cluster"
NAMESPACE="dmlog"
HELM_CHART_PATH="./deploy/helm/dmlog"
TERRAFORM_PATH="./deploy/terraform/environments/production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check required tools
    local tools=("terraform" "kubectl" "helm" "aws" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "Required tool $tool is not installed"
            exit 1
        fi
    done

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured properly"
        exit 1
    fi

    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        warning "Kubernetes cluster not accessible. Will update kubeconfig after EKS creation."
    fi

    success "Prerequisites check completed"
}

# Deploy infrastructure
deploy_infrastructure() {
    log "Starting infrastructure deployment..."

    cd "$TERRAFORM_PATH"

    # Initialize Terraform
    log "Initializing Terraform..."
    terraform init

    # Plan the deployment
    log "Creating Terraform plan..."
    terraform plan -out=tfplan

    # Confirm deployment
    read -p "Do you want to apply the infrastructure changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Applying Terraform changes..."
        terraform apply tfplan
        success "Infrastructure deployment completed"
    else
        error "Infrastructure deployment cancelled"
        exit 1
    fi

    # Update kubeconfig
    log "Updating kubeconfig..."
    aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"

    cd - > /dev/null
}

# Verify infrastructure
verify_infrastructure() {
    log "Verifying infrastructure..."

    # Check EKS cluster
    log "Checking EKS cluster..."
    if ! aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" &> /dev/null; then
        error "EKS cluster not found"
        exit 1
    fi

    # Check cluster nodes
    log "Checking cluster nodes..."
    local node_count
    node_count=$(kubectl get nodes --no-headers | wc -l)
    if [ "$node_count" -eq 0 ]; then
        error "No nodes found in cluster"
        exit 1
    fi
    success "Found $node_count nodes in cluster"

    # Check VPC and networking
    log "Checking VPC configuration..."
    local vpc_id
    vpc_id=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query 'cluster.resourcesVpcConfig.vpcId' --output text)
    if [ -z "$vpc_id" ]; then
        error "VPC configuration not found"
        exit 1
    fi
    success "VPC configuration verified: $vpc_id"

    # Check RDS instance
    log "Checking RDS instance..."
    local db_status
    db_status=$(aws rds describe-db-instances --db-instance-identifier "dmlog-${ENVIRONMENT}-db" --region "$AWS_REGION" --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "not-found")
    if [ "$db_status" != "available" ]; then
        error "RDS instance not available (status: $db_status)"
        exit 1
    fi
    success "RDS instance is available"

    # Check ElastiCache
    log "Checking ElastiCache cluster..."
    local cache_status
    cache_status=$(aws elasticache describe-replication-groups --replication-group-id "dmlog-${ENVIRONMENT}" --region "$AWS_REGION" --query 'ReplicationGroups[0].Status' --output text 2>/dev/null || echo "not-found")
    if [ "$cache_status" != "available" ]; then
        error "ElastiCache cluster not available (status: $cache_status)"
        exit 1
    fi
    success "ElastiCache cluster is available"

    success "Infrastructure verification completed"
}

# Install cluster add-ons
install_cluster_addons() {
    log "Installing cluster add-ons..."

    # Create namespaces
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -

    # Install cert-manager
    log "Installing cert-manager..."
    if ! helm repo add jetstack https://charts.jetstack.io --force-update 2>/dev/null; then
        helm repo add jetstack https://charts.jetstack.io
    fi
    helm repo update
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --version v1.13.0 \
        --set installCRDs=true

    # Wait for cert-manager to be ready
    log "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s

    # Install ingress-nginx
    log "Installing ingress-nginx..."
    if ! helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx --force-update 2>/dev/null; then
        helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    fi
    helm repo update
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.publishService.enabled=true

    # Install metrics-server
    log "Installing metrics-server..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

    # Wait for metrics-server to be ready
    log "Waiting for metrics-server to be ready..."
    kubectl wait --for=condition=available deployment/metrics-server -n kube-system --timeout=300s

    success "Cluster add-ons installation completed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."

    # Deploy Prometheus
    log "Deploying Prometheus..."
    kubectl apply -f deploy/monitoring/prometheus.yaml

    # Deploy Grafana
    log "Deploying Grafana..."
    kubectl apply -f deploy/monitoring/grafana.yaml

    # Deploy ELK stack
    log "Deploying Elasticsearch..."
    kubectl apply -f deploy/monitoring/elasticsearch.yaml

    log "Waiting for Elasticsearch to be ready..."
    kubectl wait --for=condition=ready pod -l app=elasticsearch -n logging --timeout=600s

    log "Deploying Kibana..."
    kubectl apply -f deploy/monitoring/kibana.yaml

    # Deploy logging
    log "Deploying Fluent Bit..."
    kubectl apply -f deploy/monitoring/fluent-bit.yaml

    # Wait for monitoring stack to be ready
    log "Waiting for monitoring stack to be ready..."
    kubectl wait --for=condition=available deployment/prometheus -n monitoring --timeout=300s
    kubectl wait --for=condition=available deployment/grafana -n monitoring --timeout=300s

    success "Monitoring stack deployment completed"
}

# Deploy security configurations
deploy_security() {
    log "Deploying security configurations..."

    # Apply Pod Security Policies
    log "Applying Pod Security Policies..."
    kubectl apply -f deploy/security/pod-security-policy.yaml

    # Apply Network Policies
    log "Applying Network Policies..."
    kubectl apply -f deploy/security/network-policy.yaml

    # Configure certificate management
    log "Configuring certificate management..."
    kubectl apply -f deploy/security/certificate-management.yaml

    # Deploy security scanners
    log "Deploying security scanners..."
    kubectl apply -f deploy/security/security-scanner.yaml

    success "Security configurations deployment completed"
}

# Create application secrets
create_secrets() {
    log "Creating application secrets..."

    # Check if secrets already exist
    if kubectl get secret dmlog-secrets -n "$NAMESPACE" &> /dev/null; then
        warning "Secrets already exist. Skipping creation."
        return
    fi

    # Prompt for secrets or use environment variables
    local database_url="${DATABASE_URL:-}"
    local redis_password="${REDIS_PASSWORD:-}"
    local secret_key="${SECRET_KEY:-}"
    local openai_api_key="${OPENAI_API_KEY:-}"
    local anthropic_api_key="${ANTHROPIC_API_KEY:-}"

    # Create secrets
    kubectl create secret generic dmlog-secrets \
        --namespace "$NAMESPACE" \
        --from-literal=DATABASE_URL="$database_url" \
        --from-literal=REDIS_PASSWORD="$redis_password" \
        --from-literal=SECRET_KEY="$secret_key" \
        --from-literal=OPENAI_API_KEY="$openai_api_key" \
        --from-literal=ANTHROPIC_API_KEY="$anthropic_api_key" \
        --dry-run=client -o yaml | kubectl apply -f -

    success "Application secrets created"
}

# Deploy application
deploy_application() {
    log "Deploying DMLog application..."

    # Check if Helm chart exists
    if [ ! -d "$HELM_CHART_PATH" ]; then
        error "Helm chart not found at $HELM_CHART_PATH"
        exit 1
    fi

    # Deploy using Helm
    log "Deploying application with Helm..."
    helm upgrade --install dmlog "$HELM_CHART_PATH" \
        --namespace "$NAMESPACE" \
        --values "$HELM_CHART_PATH/values.yaml" \
        --values "$HELM_CHART_PATH/values-production.yaml" \
        --wait \
        --timeout=15m

    success "Application deployment completed"
}

# Deploy performance optimizations
deploy_performance() {
    log "Deploying performance optimizations..."

    # Deploy advanced caching
    log "Deploying Redis cluster with advanced caching..."
    kubectl apply -f deploy/performance/caching-strategy.yaml

    # Deploy load balancer
    log "Deploying optimized load balancer..."
    kubectl apply -f deploy/performance/load-balancer.yaml

    # Configure CloudFront (manual step)
    log "CloudFront configuration requires manual setup via AWS console or Terraform"
    log "Please ensure CloudFront distribution is configured to point to the load balancer"

    success "Performance optimizations deployment completed"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."

    # Check application pods
    log "Checking application pods..."
    kubectl get pods -n "$NAMESPACE"
    if ! kubectl wait --for=condition=ready pod -l app=dmlog -n "$NAMESPACE" --timeout=600s; then
        error "Application pods not ready"
        exit 1
    fi

    # Check services
    log "Checking services..."
    kubectl get services -n "$NAMESPACE"

    # Check ingress
    log "Checking ingress..."
    kubectl get ingress -n "$NAMESPACE"

    # Check certificate status
    log "Checking certificate status..."
    kubectl get certificates -n "$NAMESPACE"

    # Run health checks
    log "Running health checks..."
    local backend_url="https://api.dmlog.com/health"
    local frontend_url="https://app.dmlog.com"

    if curl -f -s "$backend_url" > /dev/null; then
        success "Backend health check passed"
    else
        error "Backend health check failed"
        exit 1
    fi

    if curl -f -s "$frontend_url" > /dev/null; then
        success "Frontend health check passed"
    else
        error "Frontend health check failed"
        exit 1
    fi

    success "Deployment verification completed"
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."

    local report_file="deployment-report-$(date +%Y%m%d-%H%M%S).md"

    cat > "$report_file" << EOF
# DMLog Production Deployment Report

**Date:** $(date)
**Environment:** $ENVIRONMENT
**Cluster:** $CLUSTER_NAME

## Infrastructure

- **EKS Cluster:** $(kubectl version --short | grep 'Server Version')
- **Node Count:** $(kubectl get nodes --no-headers | wc -l)
- **VPC ID:** $(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query 'cluster.resourcesVpcConfig.vpcId' --output text)

## Application Status

- **Namespace:** $NAMESPACE
- **Pods:** $(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
- **Services:** $(kubectl get services -n "$NAMESPACE" --no-headers | wc -l)
- **Deployments:** $(kubectl get deployments -n "$NAMESPACE" --no-headers | wc -l)

## Monitoring

- **Prometheus:** $(kubectl get pods -n monitoring -l app=prometheus --no-headers | wc -l) pods
- **Grafana:** $(kubectl get pods -n monitoring -l app=grafana --no-headers | wc -l) pods

## URLs

- **Frontend:** https://app.dmlog.com
- **API:** https://api.dmlog.com
- **Grafana:** https://monitoring.dmlog.com
- **Kibana:** https://logs.dmlog.com

## Next Steps

1. Configure Grafana dashboards
2. Set up alerting rules
3. Test backup and restore procedures
4. Configure performance monitoring
5. Schedule regular security scans

## Support

For issues, check the monitoring dashboards or contact the infrastructure team.
EOF

    success "Deployment report generated: $report_file"
}

# Cleanup function
cleanup() {
    log "Performing cleanup..."
    # Add any cleanup tasks here
    success "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting DMLog production deployment..."

    # Set up error handling
    trap cleanup EXIT

    # Deployment steps
    check_prerequisites
    deploy_infrastructure
    verify_infrastructure
    install_cluster_addons
    deploy_monitoring
    deploy_security
    create_secrets
    deploy_application
    deploy_performance
    verify_deployment
    generate_report

    success "DMLog production deployment completed successfully!"
    log "Application is available at https://app.dmlog.com"
    log "API is available at https://api.dmlog.com"
    log "Monitoring is available at https://monitoring.dmlog.com"
}

# Script usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -i, --infra    Deploy infrastructure only"
    echo "  -a, --app      Deploy application only (assumes infrastructure exists)"
    echo "  -m, --monitor  Deploy monitoring stack only"
    echo "  -s, --security Deploy security configurations only"
    echo ""
    echo "Environment variables:"
    echo "  DATABASE_URL      PostgreSQL connection URL"
    echo "  REDIS_PASSWORD    Redis password"
    echo "  SECRET_KEY        Application secret key"
    echo "  OPENAI_API_KEY    OpenAI API key"
    echo "  ANTHROPIC_API_KEY Anthropic API key"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    -i|--infra)
        check_prerequisites
        deploy_infrastructure
        verify_infrastructure
        ;;
    -a|--app)
        create_secrets
        deploy_application
        deploy_performance
        verify_deployment
        ;;
    -m|--monitor)
        deploy_monitoring
        ;;
    -s|--security)
        deploy_security
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        usage
        exit 1
        ;;
esac