# DMLog Quick Start Guide

Get DMLog up and running in minutes! This guide covers the fastest way to deploy DMLog for development, testing, or production use.

## 🚀 One-Command Deployment

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for cloning the repository
- **4GB+ RAM** and **20GB+ storage** recommended

### Quick Start (Development)

```bash
# Clone and deploy in one command
git clone https://github.com/dmlog/dmlog.git && cd dmlog && ./deploy.sh development
```

That's it! DMLog will automatically:
- ✅ Download and configure all services
- ✅ Set up PostgreSQL, Redis, and monitoring
- ✅ Run database migrations
- ✅ Start the web dashboard and API
- ✅ Open your browser to the application

### Access Points

Once deployment completes, access DMLog at:

- **🎮 Main Dashboard**: http://localhost:3000
- **📚 API Documentation**: http://localhost:8000/docs
- **📊 Monitoring Dashboard**: http://localhost:3001 (admin/admin)
- **🔍 Health Check**: http://localhost:8000/api/v1/health

## 📋 What You Get

The deployment includes these services:

| Service | Description | URL | Port |
|---------|-------------|-----|------|
| **Web Dashboard** | Main user interface | http://localhost:3000 | 3000 |
| **API Server** | REST API and WebSocket | http://localhost:8000 | 8000 |
| **PostgreSQL** | Primary database | - | 5432 |
| **Redis** | Cache and session store | - | 6379 |
| **Grafana** | Monitoring dashboards | http://localhost:3001 | 3001 |
| **Prometheus** | Metrics collection | - | 9090 |

## 🎯 First Steps

### 1. Create Your Account

1. Open http://localhost:3000 in your browser
2. Click "Sign Up"
3. Enter your email and password
4. Complete your profile with gaming preferences

### 2. Create Your First Campaign

1. Navigate to "Campaigns" in the sidebar
2. Click "Create Campaign"
3. Fill in campaign details:
   - Campaign name
   - Description
   - D&D edition (5e recommended)
   - Expected number of players

### 3. Create a Character

1. Go to "Characters" in the sidebar
2. Click "Create Character"
3. Choose character options:
   - Name and race
   - Class and level
   - Background story
   - Ability scores

### 4. Start a Session

1. Navigate to your campaign
2. Click "Start Session"
3. Invite players using the session code
4. Use real-time features for live gameplay

## 🛠️ Common Tasks

### Check System Status

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f

# Check API health
curl http://localhost:8000/api/v1/health
```

### Stop DMLog

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ Deletes data)
docker-compose down -v
```

### Update DMLog

```bash
# Pull latest changes
git pull origin main

# Redeploy with latest code
./deploy.sh development
```

## 🎮 Test the Features

### Create Test Data

```bash
# Load sample characters and campaigns
docker-compose exec api python scripts/load_sample_data.py
```

### Test API Endpoints

```bash
# List characters
curl http://localhost:8000/api/v1/characters/

# Create a character
curl -X POST http://localhost:8000/api/v1/characters/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Character","race":"Human","class":"Fighter","level":1}'
```

### Test WebSocket Connection

Open browser console and connect:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/connect?user_id=test');

// Listen for messages
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

// Send a test message
ws.send(JSON.stringify({
  type: 'test',
  data: { message: 'Hello DMLog!' }
}));
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
netstat -tlnp | grep :3000

# Stop conflicting services
sudo systemctl stop nginx  # or other conflicting service
```

**Permission Denied**
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

**Out of Memory**
```bash
# Check system resources
free -h
docker system prune -a
```

**Database Connection Issues**
```bash
# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

### Get Help

- **📖 Documentation**: [Full Documentation Suite](docs/README.md)
- **🐛 Issues**: [GitHub Issues](https://github.com/dmlog/dmlog/issues)
- **💬 Discord**: [DMLog Discord](https://discord.gg/dmlog)
- **📧 Email**: support@dmlog.com

## 🎯 Next Steps

Now that DMLog is running, explore these features:

### For Players
- Create detailed character sheets
- Join campaigns with invite codes
- Track character progression
- Use real-time session features

### For Dungeon Masters
- Create and manage multiple campaigns
- Track sessions and player progress
- Use dice rolling and combat tracking
- Generate session summaries

### For Developers
- Explore the [API documentation](http://localhost:8000/docs)
- Check out the [source code](https://github.com/dmlog/dmlog)
- Read the [contributing guide](docs/developer/contributing-guide.md)
- Build custom integrations

## 🔄 Production Deployment

When you're ready to deploy to production:

```bash
# Deploy to production environment
./deploy.sh production

# Deploy to AWS EC2
./deploy.sh aws-ec2 latest ec2-user@your-instance.com

# Deploy to NVIDIA Jetson
./deploy.sh jetson
```

**Important**: Read the [Production Deployment Guide](docs/technical/deployment-guide.md#production-environment) before deploying to production.

## 📊 Monitor Your Instance

### Grafana Dashboards

Access Grafana at http://localhost:3001 (admin/admin):

- **System Overview**: CPU, memory, disk usage
- **Application Metrics**: API requests, response times
- **Database Performance**: Query performance, connections
- **Cache Analytics**: Redis hit rates, memory usage

### Key Metrics to Watch

- **API Response Time**: Should be < 100ms
- **Database Connections**: Monitor for connection pool exhaustion
- **Memory Usage**: Watch for memory leaks
- **Disk Space**: Ensure adequate storage for logs and data

---

**🎉 Congratulations!** You now have a fully functional DMLog instance running. Start exploring the features and create your first campaign!

**Need help?** Check our [comprehensive documentation](docs/README.md) or [contact support](mailto:support@dmlog.com).