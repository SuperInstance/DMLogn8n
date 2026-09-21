#!/bin/bash

# DMLog Scaling Infrastructure Test Script
# This script tests various scaling scenarios

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="dmlog"
MONITORING_NAMESPACE="monitoring"
TEST_DURATION="${TEST_DURATION:-600}" # 10 minutes default
LOAD_GENERATOR_IMAGE="weaveworks/k6:latest"

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

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking test prerequisites..."

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        exit 1
    fi

    if ! kubectl get namespace ${NAMESPACE} &> /dev/null; then
        log_error "Namespace ${NAMESPACE} does not exist"
        exit 1
    fi

    if ! kubectl get namespace ${MONITORING_NAMESPACE} &> /dev/null; then
        log_error "Namespace ${MONITORING_NAMESPACE} does not exist"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Function to get current pod counts
get_pod_counts() {
    local service=$1
    kubectl get pods -n ${NAMESPACE} -l app=dmlog,component=${service} --no-headers | wc -l
}

# Function to get HPA metrics
get_hpa_metrics() {
    local hpa=$1
    kubectl get hpa ${hpa} -n ${NAMESPACE} -o jsonpath='{.status.currentReplicas}/{.status.desiredReplicas}'
}

# Function to get resource usage
get_resource_usage() {
    local pod_pattern=$1
    local metric=$2

    kubectl top pods -n ${NAMESPACE} -l ${pod_pattern} --no-headers | \
    awk -v metric="${metric}" '{
        if (metric == "cpu") {
            gsub(/m/, "", $2);
            sum += $2;
            count++;
        } else if (metric == "memory") {
            gsub(/Mi/, "", $3);
            sum += $3;
            count++;
        }
    } END {
        if (count > 0) print sum/count; else print 0;
    }'
}

# Function to generate load
generate_load() {
    log_test "Generating synthetic load for ${TEST_DURATION} seconds..."

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: load-generator
  namespace: ${NAMESPACE}
  labels:
    app: load-generator
spec:
  containers:
  - name: k6
    image: ${LOAD_GENERATOR_IMAGE}
    command: ["k6", "run", "--duration", "${TEST_DURATION}s", "--vus", "50", "-"]
    stdin: true
    resources:
      requests:
        cpu: 200m
        memory: 256Mi
      limits:
        cpu: 500m
        memory: 512Mi
EOF

    cat <<'EOF' | kubectl exec -i load-generator -n ${NAMESPACE} -- k6 run --duration 600s --vus 50 -
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function () {
  // Test API endpoints
  let responses = [
    http.get('http://backend-service:8080/health'),
    http.get('http://backend-service:8080/api/v1/logs'),
    http.post('http://backend-service:8080/api/v1/logs', JSON.stringify({
      level: 'info',
      message: 'Test log message',
      timestamp: new Date().toISOString()
    }), {
      headers: { 'Content-Type': 'application/json' }
    }),
  ];

  responses.forEach((response) => {
    check(response, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
    });
  });

  sleep(1);
}
EOF

    # Wait for load test to complete
    kubectl wait --for=condition=completed pod/load-generator -n ${NAMESPACE} --timeout=700s

    # Clean up
    kubectl delete pod load-generator -n ${NAMESPACE} --ignore-not-found=true

    log_info "Load generation completed"
}

# Function to test HPA scaling
test_hpa_scaling() {
    log_test "Testing Horizontal Pod Autoscaler scaling..."

    local backend_pods_before=$(get_pod_counts "backend")
    local frontend_pods_before=$(get_pod_counts "frontend")

    log_info "Initial pod counts - Backend: ${backend_pods_before}, Frontend: ${frontend_pods_before}"

    # Generate load to trigger scaling
    generate_load

    # Wait for scaling to occur
    log_info "Waiting for HPA to scale up pods..."
    sleep 60

    local backend_pods_after=$(get_pod_counts "backend")
    local frontend_pods_after=$(get_pod_counts "frontend")

    log_info "Pod counts after load - Backend: ${backend_pods_after}, Frontend: ${frontend_pods_after}"

    # Check if scaling occurred
    if [ "${backend_pods_after}" -gt "${backend_pods_before}" ]; then
        log_info "✅ Backend scaling test PASSED"
    else
        log_warn "⚠️ Backend scaling test FAILED - No scaling detected"
    fi

    if [ "${frontend_pods_after}" -gt "${frontend_pods_before}" ]; then
        log_info "✅ Frontend scaling test PASSED"
    else
        log_warn "⚠️ Frontend scaling test FAILED - No scaling detected"
    fi
}

# Function to test resource limits
test_resource_limits() {
    log_test "Testing resource limits and quotas..."

    # Check if pods are within resource limits
    local backend_cpu=$(get_resource_usage "app=dmlog,component=backend" "cpu")
    local backend_memory=$(get_resource_usage "app=dmlog,component=backend" "memory")

    log_info "Backend resource usage - CPU: ${backend_cpu}m, Memory: ${backend_memory}Mi"

    if [ "$(echo "${backend_cpu} < 800" | bc -l)" -eq 1 ]; then
        log_info "✅ Backend CPU usage within limits"
    else
        log_warn "⚠️ Backend CPU usage high: ${backend_cpu}m"
    fi

    if [ "${backend_memory}" -lt 1024 ]; then
        log_info "✅ Backend memory usage within limits"
    else
        log_warn "⚠️ Backend memory usage high: ${backend_memory}Mi"
    fi
}

# Function to test health checks
test_health_checks() {
    log_test "Testing application health checks..."

    # Test backend health
    local backend_health=$(kubectl exec -n ${NAMESPACE} deployment/backend-deployment -- curl -s http://localhost:8080/health || echo "failed")

    if [[ "${backend_health}" == *"healthy"* ]]; then
        log_info "✅ Backend health check PASSED"
    else
        log_error "❌ Backend health check FAILED"
    fi

    # Test frontend health
    local frontend_health=$(kubectl exec -n ${NAMESPACE} deployment/frontend-deployment -- curl -s http://localhost/health || echo "failed")

    if [[ "${frontend_health}" == *"healthy"* ]]; then
        log_info "✅ Frontend health check PASSED"
    else
        log_error "❌ Frontend health check FAILED"
    fi
}

# Function to test monitoring
test_monitoring() {
    log_test "Testing monitoring components..."

    # Check Prometheus targets
    local prometheus_targets=$(kubectl exec -n ${MONITORING_NAMESPACE} deployment/prometheus-enhanced -- curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets | length' || echo "0")

    if [ "${prometheus_targets}" -gt 0 ]; then
        log_info "✅ Prometheus targets active: ${prometheus_targets}"
    else
        log_error "❌ No active Prometheus targets"
    fi

    # Check Alertmanager
    local alertmanager_health=$(kubectl exec -n ${MONITORING_NAMESPACE} deployment/alertmanager-enhanced -- curl -s http://localhost:9093/-/healthy || echo "failed")

    if [[ "${alertmanager_health}" == *"OK"* ]]; then
        log_info "✅ Alertmanager health check PASSED"
    else
        log_error "❌ Alertmanager health check FAILED"
    fi
}

# Function to test CDN configuration
test_cdn() {
    log_test "Testing CDN configuration..."

    # This would test CloudFront distribution if deployed
    # For now, we'll just check if the Terraform outputs exist
    if terraform -C terraform output -json &> /dev/null; then
        local cloudfront_domain=$(terraform -C terraform output -json cloudfront_domain_name 2>/dev/null | jq -r . || echo "unknown")

        if [ "${cloudfront_domain}" != "unknown" ] && [ "${cloudfront_domain}" != "null" ]; then
            log_info "✅ CDN domain configured: ${cloudfront_domain}"

            # Test CDN health
            if curl -s --connect-timeout 5 "https://${cloudfront_domain}/health" | grep -q "healthy"; then
                log_info "✅ CDN health check PASSED"
            else
                log_warn "⚠️ CDN health check FAILED or not accessible"
            fi
        else
            log_warn "⚠️ CDN not configured or not deployed"
        fi
    else
        log_warn "⚠️ Terraform outputs not available"
    fi
}

# Function to test failover scenarios
test_failover() {
    log_test "Testing failover scenarios..."

    # Simulate pod failure
    log_info "Simulating backend pod failure..."

    local backend_pods_before=$(get_pod_counts "backend")
    kubectl delete pod -n ${NAMESPACE} -l app=dmlog,component=backend --all

    # Wait for replica set to recreate pods
    sleep 30

    local backend_pods_after=$(get_pod_counts "backend")

    if [ "${backend_pods_after}" -ge "${backend_pods_before}" ]; then
        log_info "✅ Pod failover test PASSED"
    else
        log_error "❌ Pod failover test FAILED - Expected ${backend_pods_before} pods, got ${backend_pods_after}"
    fi
}

# Function to generate test report
generate_report() {
    log_info "Generating test report..."

    local report_file="scaling-test-report-$(date +%Y%m%d-%H%M%S).txt"

    cat > "${report_file}" << EOF
DMLog Scaling Infrastructure Test Report
========================================
Date: $(date)
Environment: $(kubectl config current-context)
Namespace: ${NAMESPACE}

Test Results:
------------
EOF

    # Add HPA status
    cat >> "${report_file}" << EOF
HPA Status:
-----------
$(kubectl get hpa -n ${NAMESPACE})

Pod Status:
-----------
$(kubectl get pods -n ${NAMESPACE})

Resource Usage:
--------------
$(kubectl top pods -n ${NAMESPACE})

Test Summary:
-------------
EOF

    # Add test results based on earlier tests
    # This would be populated based on test results

    log_info "Test report generated: ${report_file}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test DMLog scaling infrastructure

Options:
    -h, --help              Show this help message
    -d, --duration          Test duration in seconds (default: 600)
    -c, --component         Test specific component (hpa, resources, health, monitoring, cdn, failover)
    --report-only           Generate report without running tests

Examples:
    $0                                      # Run all tests
    $0 -d 300                               # Run tests for 5 minutes
    $0 -c hpa                               # Test only HPA scaling
    $0 --report-only                        # Generate report only

EOF
}

# Main function
main() {
    local test_component="all"
    local report_only=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--duration)
                TEST_DURATION="$2"
                shift 2
                ;;
            -c|--component)
                test_component="$2"
                shift 2
                ;;
            --report-only)
                report_only=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    log_info "Starting DMLog scaling infrastructure tests"
    log_info "Test duration: ${TEST_DURATION} seconds"
    log_info "Component: ${test_component}"

    # Check prerequisites
    check_prerequisites

    if [ "$report_only" = true ]; then
        generate_report
        exit 0
    fi

    # Run tests based on component selection
    case $test_component in
        "all")
            test_health_checks
            test_hpa_scaling
            test_resource_limits
            test_monitoring
            test_cdn
            test_failover
            ;;
        "hpa")
            test_hpa_scaling
            ;;
        "resources")
            test_resource_limits
            ;;
        "health")
            test_health_checks
            ;;
        "monitoring")
            test_monitoring
            ;;
        "cdn")
            test_cdn
            ;;
        "failover")
            test_failover
            ;;
        *)
            log_error "Unknown component: ${test_component}"
            show_usage
            exit 1
            ;;
    esac

    # Generate report
    generate_report

    log_info "DMLog scaling infrastructure tests completed!"
    log_info "Check the test report for detailed results."
}

# Run main function
main "$@"