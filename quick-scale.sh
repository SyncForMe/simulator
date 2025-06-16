#!/bin/bash

echo "⚡ Quick Scale: Optimizing current Observer AI setup"
echo "=================================================="

# Stop current services
echo "🔄 Stopping current services..."
sudo supervisorctl stop backend frontend

# Backup current configuration
echo "💾 Backing up current configuration..."
cp /app/backend/.env /app/backend/.env.backup
cp /app/frontend/.env /app/frontend/.env.backup

# Install production requirements
echo "📦 Installing optimizations..."
cd /app/backend
pip install redis aioredis uvloop motor[srv] prometheus-client

# Update supervisor configuration for optimized backend
cat > /etc/supervisor/conf.d/backend.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/uvicorn server_optimized:app --host 0.0.0.0 --port 8001 --workers 4 --loop uvloop
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=PATH="/root/.venv/bin"
user=root
stopsignal=TERM
EOF

# Add Redis service
cat > /etc/supervisor/conf.d/redis.conf << 'EOF'
[program:redis]
command=redis-server --port 6379 --maxmemory 1gb --maxmemory-policy allkeys-lru --save 60 1000
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/redis.err.log
stdout_logfile=/var/log/supervisor/redis.out.log
user=root
EOF

# Update backend environment for optimization
cat >> /app/backend/.env << 'EOF'

# Optimization settings
REDIS_URL=redis://localhost:6379
WORKERS=4
MAX_CONNECTIONS=200
CONNECTION_POOL_SIZE=20
ENABLE_CACHING=true
ENABLE_MONITORING=true
EOF

# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start optimized services
echo "🚀 Starting optimized services..."
sudo supervisorctl start redis
sudo supervisorctl start backend
sudo supervisorctl start frontend

echo ""
echo "✅ Quick optimization complete!"
echo ""
echo "📊 Improvements:"
echo "   • 4 backend workers (was 1)"
echo "   • Redis caching enabled"
echo "   • Connection pooling"
echo "   • Performance monitoring"
echo ""
echo "🎯 New estimated capacity: ~400-500 concurrent users"
echo ""
echo "🔍 Check status:"
echo "   sudo supervisorctl status"
echo ""
echo "📈 Monitor performance:"
echo "   tail -f /var/log/supervisor/backend.out.log"