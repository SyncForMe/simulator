#!/bin/bash

echo "🚀 Deploying Observer AI Production Infrastructure"
echo "=================================================="

# Set environment variables
export MONGO_PASSWORD="secure_mongo_password_123"
export JWT_SECRET="production_jwt_secret_key_456"
export GRAFANA_PASSWORD="admin_grafana_pass_789"
export BACKEND_URL="https://your-domain.com"

echo "📦 Starting production deployment with Docker Compose..."

# Create .env file for production
cat > .env.production << EOF
MONGO_PASSWORD=${MONGO_PASSWORD}
JWT_SECRET=${JWT_SECRET}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
BACKEND_URL=${BACKEND_URL}
EOF

# Deploy with production configuration
docker-compose -f docker-compose.production.yml --env-file .env.production up -d

echo "✅ Production deployment started!"
echo ""
echo "🔍 Services Status:"
docker-compose -f docker-compose.production.yml ps

echo ""
echo "📊 This deployment provides:"
echo "   • 3 Backend instances with 4 workers each (12 total workers)"
echo "   • Load-balanced Nginx frontend"
echo "   • Redis caching"
echo "   • Optimized MongoDB"
echo "   • Prometheus monitoring"
echo "   • Grafana dashboards"
echo ""
echo "🎯 Estimated capacity: ~1,200 concurrent users"
echo "💰 Cost: Much lower than cloud Kubernetes"

echo ""
echo "🌐 Access your services:"
echo "   • Application: http://localhost"
echo "   • Monitoring: http://localhost:3001 (admin/admin_grafana_pass_789)"
echo "   • Metrics: http://localhost:9090"