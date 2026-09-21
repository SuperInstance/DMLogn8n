#!/bin/bash

# DMLog Scaling Infrastructure Deployment Script
# This script deploys all scaling components for DMLog infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="dmlog"
MONITORING_NAMESPACE="monitoring"
CLUSTER_NAME="dmlog-prod"
REGION="${AWS_REGION:-us-west-2}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi

    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "terraform is not installed"
        exit 1
    fi

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi

    # Check kubectl cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Function to create namespaces
create_namespaces() {
    log_info "Creating namespaces..."

    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace ${MONITORING_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

    log_info "Namespaces created successfully"
}

# Function to deploy HPA configurations
deploy_hpa() {
    log_info "Deploying Horizontal Pod Autoscalers..."

    # Deploy advanced HPA configurations
    kubectl apply -f kubernetes/advanced-hpa.yaml -n ${NAMESPACE}

    # Wait for HPAs to be ready
    kubectl wait --for=condition=Available horizontalpodautoscaler --all -n ${NAMESPACE} --timeout=300s

    log_info "HPA configurations deployed successfully"
}

# Function to deploy predictive scaling
deploy_predictive_scaling() {
    log_info "Deploying predictive scaling components..."

    # Deploy predictive scaling configurations
    kubectl apply -f kubernetes/predictive-scaling.yaml -n ${NAMESPACE}

    # Create secrets for predictive scaler
    if ! kubectl get secret dmlog-kubeconfig -n ${NAMESPACE} &> /dev/null; then
        log_warn "Creating placeholder kubeconfig secret - please update with actual credentials"
        kubectl create secret generic dmlog-kubeconfig \
            --from-literal=kubeconfig="placeholder" \
            -n ${NAMESPACE}
    fi

    # Wait for predictive scaler to be ready
    kubectl wait --for=condition=Available deployment/predictive-scaler -n ${NAMESPACE} --timeout=300s

    log_info "Predictive scaling deployed successfully"
}

# Function to deploy cluster autoscaler
deploy_cluster_autoscaler() {
    log_info "Deploying cluster autoscaler..."

    # Deploy cluster autoscaler configurations
    kubectl apply -f kubernetes/cluster-autoscaler.yaml -n kube-system

    # Wait for cluster autoscaler to be ready
    kubectl wait --for=condition=Available deployment/cluster-autoscaler -n kube-system --timeout=300s

    log_info "Cluster autoscaler deployed successfully"
}

# Function to deploy advanced load balancing
deploy_load_balancing() {
    log_info "Deploying advanced load balancing configurations..."

    # Install Istio for advanced traffic management (if not already installed)
    if ! helm list -n istio-system | grep -q istiod; then
        log_info "Installing Istio..."
        helm repo add istio https://istio-release.storage.googleapis.com/charts
        helm repo update
        helm install istiod istio/istiod -n istio-system --create-namespace
        kubectl wait --for=condition=Available deployment/istiod -n istio-system --timeout=300s
    fi

    # Deploy load balancing configurations
    kubectl apply -f kubernetes/advanced-loadbalancing.yaml -n ${NAMESPACE}

    log_info "Advanced load balancing deployed successfully"
}

# Function to deploy GSLB
deploy_gslb() {
    log_info "Deploying Global Server Load Balancing..."

    # Deploy GSLB configurations
    kubectl apply -f kubernetes/gslb.yaml -n ${NAMESPACE}

    # Create AWS credentials secret for GSLB controller
    if ! kubectl get secret aws-credentials -n ${NAMESPACE} &> /dev/null; then
        log_warn "Creating placeholder AWS credentials secret - please update with actual credentials"
        kubectl create secret generic aws-credentials \
            --from-literal=credentials="placeholder" \
            -n ${NAMESPACE}
    fi

    # Wait for GSLB controller to be ready
    kubectl wait --for=condition=Available deployment/gslb-controller -n ${NAMESPACE} --timeout=300s

    log_info "GSLB deployed successfully"
}

# Function to deploy monitoring
deploy_monitoring() {
    log_info "Deploying monitoring and alerting..."

    # Deploy monitoring configurations
    kubectl apply -f kubernetes/monitoring.yaml -n ${MONITORING_NAMESPACE}

    # Create PVCs for Prometheus and Alertmanager
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-storage-pvc
  namespace: ${MONITORING_NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: gp3
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: alertmanager-storage-pvc
  namespace: ${MONITORING_NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: gp3
EOF

    # Wait for monitoring components to be ready
    kubectl wait --for=condition=Available deployment/prometheus-enhanced -n ${MONITORING_NAMESPACE} --timeout=300s
    kubectl wait --for=condition=Available deployment/alertmanager-enhanced -n ${MONITORING_NAMESPACE} --timeout=300s

    log_info "Monitoring and alerting deployed successfully"
}

# Function to deploy CDN and edge computing
deploy_cdn_edge() {
    log_info "Deploying CDN and edge computing infrastructure..."

    # Change to Terraform directory
    cd terraform

    # Initialize Terraform
    terraform init

    # Plan Terraform deployment
    terraform plan -var="environment=${ENVIRONMENT}" -out=tfplan

    # Apply Terraform configuration
    terraform apply -auto-approve tfplan

    cd ..

    log_info "CDN and edge computing deployed successfully"
}

# Function to deploy resource optimization
deploy_resource_optimization() {
    log_info "Deploying resource optimization..."

    # Change to Terraform directory
    cd terraform

    # Plan and apply resource optimization
    terraform plan -var="environment=${ENVIRONMENT}" -var-file="resource-optimization.tfvars" -out=optimization-plan
    terraform apply -auto-approve optimization-plan

    cd ..

    log_info "Resource optimization deployed successfully"
}

# Function to verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check all deployments are running
    log_info "Checking deployments in ${NAMESPACE}..."
    kubectl get deployments -n ${NAMESPACE}

    log_info "Checking deployments in ${MONITORING_NAMESPACE}..."
    kubectl get deployments -n ${MONITORING_NAMESPACE}

    # Check HPAs are working
    log_info "Checking Horizontal Pod Autoscalers..."
    kubectl get hpa -n ${NAMESPACE}

    # Check cluster autoscaler
    log_info "Checking cluster autoscaler..."
    kubectl get deployment cluster-autoscaler -n kube-system

    # Check monitoring components
    log_info "Checking monitoring components..."
    kubectl get pods -n ${MONITORING_NAMESPACE} -l app=prometheus
    kubectl get pods -n ${MONITORING_NAMESPACE} -l app=alertmanager

    log_info "Deployment verification completed"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy DMLog scaling infrastructure

Options:
    -h, --help              Show this help message
    -e, --environment       Environment name (default: production)
    -r, --region            AWS region (default: us-west-2)
    --skip-cdn              Skip CDN and edge computing deployment
    --skip-optimization     Skip resource optimization deployment
    --verify-only           Only verify existing deployment

Examples:
    $0                                      # Deploy all components
    $0 -e staging                           # Deploy to staging environment
    $0 --skip-cdn                           # Deploy without CDN components
    $0 --verify-only                        # Verify existing deployment

EOF
}

# Main function
main() {
    local skip_cdn=false
    local skip_optimization=false
    local verify_only=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            --skip-cdn)
                skip_cdn=true
                shift
                ;;
            --skip-optimization)
                skip_optimization=true
                shift
                ;;
            --verify-only)
                verify_only=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    log_info "Starting DMLog scaling infrastructure deployment"
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Region: ${REGION}"

    if [ "$verify_only" = true ]; then
        verify_deployment
        exit 0
    fi

    # Check prerequisites
    check_prerequisites

    # Create namespaces
    create_namespaces

    # Deploy components in order
    deploy_hpa
    deploy_predictive_scaling
    deploy_cluster_autoscaler
    deploy_load_balancing
    deploy_gslb
    deploy_monitoring

    # Deploy optional components
    if [ "$skip_cdn" = false ]; then
        deploy_cdn_edge
    else
        log_warn "Skipping CDN and edge computing deployment"
    fi

    if [ "$skip_optimization" = false ]; then
        deploy_resource_optimization
    else
        log_warn "Skipping resource optimization deployment"
    fi

    # Verify deployment
    verify_deployment

    log_info "DMLog scaling infrastructure deployment completed successfully!"

    cat << EOF

Next steps:
1. Update placeholder secrets with actual credentials
2. Configure DNS records for GSLB and CDN
3. Set up alert routing in Alertmanager
4. Monitor the deployment and adjust scaling policies as needed

Access points:
- Grafana: kubectl port-forward -n ${MONITORING_NAMESPACE} svc/grafana 3000:3000
- Prometheus: kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus 9090:9090
- Alertmanager: kubectl port-forward -n ${MONITORING_NAMESPACE} svc/alertmanager 9093:9093

EOF
}

# Run main function
main "$@"