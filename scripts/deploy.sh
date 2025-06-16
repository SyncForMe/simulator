#!/bin/bash

# Observer AI Deployment Script
# Deploys the application with high availability and scaling

set -e

echo "🚀 Starting Observer AI Deployment..."

# Configuration
NAMESPACE="observer-ai"
DOCKER_REGISTRY="your-registry.com"  # Replace with your registry
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
    fi
    
    if ! command -v docker &> /dev/null; then
        error "docker is not installed"
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi
    
    log "✅ Prerequisites check passed"
}

# Build and push Docker images
build_images() {
    log "Building Docker images..."
    
    # Build backend image
    log "Building backend image..."
    docker build -t ${DOCKER_REGISTRY}/observer-ai/backend:${IMAGE_TAG} ./backend/
    docker push ${DOCKER_REGISTRY}/observer-ai/backend:${IMAGE_TAG}
    
    # Build frontend image
    log "Building frontend image..."
    docker build -t ${DOCKER_REGISTRY}/observer-ai/frontend:${IMAGE_TAG} ./frontend/
    docker push ${DOCKER_REGISTRY}/observer-ai/frontend:${IMAGE_TAG}
    
    log "✅ Images built and pushed successfully"
}

# Deploy to Kubernetes
deploy_k8s() {
    log "Deploying to Kubernetes..."
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Apply secrets (make sure to update with real values)
    kubectl apply -f k8s/secrets.yaml
    
    # Deploy Redis
    log "Deploying Redis..."
    kubectl apply -f k8s/redis-deployment.yaml
    
    # Deploy MongoDB
    log "Deploying MongoDB..."
    kubectl apply -f k8s/mongodb-deployment.yaml
    
    # Wait for databases to be ready
    log "Waiting for databases to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/mongodb -n ${NAMESPACE}
    
    # Deploy backend
    log "Deploying backend..."
    kubectl apply -f k8s/backend-deployment.yaml
    
    # Wait for backend to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/backend -n ${NAMESPACE}
    
    # Deploy frontend
    log "Deploying frontend..."
    kubectl apply -f k8s/frontend-deployment.yaml
    
    # Deploy ingress
    log "Deploying ingress..."
    kubectl apply -f k8s/ingress.yaml
    
    log "✅ Kubernetes deployment completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Install Prometheus and Grafana using Helm
    if command -v helm &> /dev/null; then
        # Add Prometheus community Helm repository
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update
        
        # Install Prometheus
        helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --create-namespace \
            --set grafana.adminPassword=admin123 \
            --set prometheus.prometheusSpec.retention=30d
        
        log "✅ Monitoring stack deployed"
    else
        warn "Helm not found, skipping monitoring setup"
    fi
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check all pods are running
    log "Checking pod status..."
    kubectl get pods -n ${NAMESPACE}
    
    # Check services
    log "Checking services..."
    kubectl get services -n ${NAMESPACE}
    
    # Check ingress
    log "Checking ingress..."
    kubectl get ingress -n ${NAMESPACE}
    
    # Test health endpoints
    log "Testing health endpoints..."
    
    # Port forward to test locally
    kubectl port-forward -n ${NAMESPACE} service/backend-service 8001:8001 &
    PORT_FORWARD_PID=$!
    
    sleep 5
    
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        log "✅ Backend health check passed"
    else
        warn "Backend health check failed"
    fi
    
    # Kill port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    log "✅ Deployment verification completed"
}

# Scale deployment for high load
scale_for_load() {
    local target_users=${1:-1000}
    
    log "Scaling deployment for ${target_users} concurrent users..."
    
    # Calculate required replicas based on expected load
    # Assuming each backend pod can handle ~100 concurrent users
    backend_replicas=$((target_users / 100))
    backend_replicas=$((backend_replicas > 50 ? 50 : backend_replicas))  # Cap at 50
    backend_replicas=$((backend_replicas < 3 ? 3 : backend_replicas))    # Minimum 3
    
    # Scale backend
    kubectl scale deployment backend --replicas=${backend_replicas} -n ${NAMESPACE}
    
    # Scale frontend (less CPU intensive)
    frontend_replicas=$((backend_replicas / 2))
    frontend_replicas=$((frontend_replicas < 2 ? 2 : frontend_replicas))
    kubectl scale deployment frontend --replicas=${frontend_replicas} -n ${NAMESPACE}
    
    log "✅ Scaled to ${backend_replicas} backend replicas and ${frontend_replicas} frontend replicas"
}

# Run load test
run_load_test() {
    local num_users=${1:-100}
    local concurrent=${2:-50}
    
    log "Running load test with ${num_users} users, ${concurrent} concurrent..."
    
    # Get the service URL
    SERVICE_URL=$(kubectl get ingress observer-ai-ingress -n ${NAMESPACE} -o jsonpath='{.spec.rules[0].host}')
    if [ -z "$SERVICE_URL" ]; then
        SERVICE_URL="http://localhost:8001"
        # Port forward for local testing
        kubectl port-forward -n ${NAMESPACE} service/backend-service 8001:8001 &
        PORT_FORWARD_PID=$!
        sleep 5
    else
        SERVICE_URL="https://${SERVICE_URL}"
    fi
    
    # Run load test
    python3 scripts/load_test.py --users ${num_users} --concurrent ${concurrent} --url ${SERVICE_URL}
    
    # Clean up port forward if used
    if [ ! -z "$PORT_FORWARD_PID" ]; then
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            # build_images  # Uncomment when you have a Docker registry
            deploy_k8s
            setup_monitoring
            verify_deployment
            ;;
        "scale")
            scale_for_load ${2:-1000}
            ;;
        "test")
            run_load_test ${2:-100} ${3:-50}
            ;;
        "monitor")
            log "Opening monitoring dashboards..."
            kubectl port-forward -n monitoring service/prometheus-grafana 3000:80 &
            log "Grafana available at: http://localhost:3000 (admin/admin123)"
            wait
            ;;
        *)
            echo "Usage: $0 {deploy|scale|test|monitor}"
            echo "  deploy        - Full deployment"
            echo "  scale [users] - Scale for number of users (default: 1000)"
            echo "  test [users] [concurrent] - Run load test (default: 100 users, 50 concurrent)"
            echo "  monitor       - Open monitoring dashboard"
            exit 1
            ;;
    esac
}

main "$@"