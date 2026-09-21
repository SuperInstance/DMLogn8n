/**
 * Development server for D&D AR/VR WebXR Application
 * Provides local development with hot reload and WebSocket support
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const fs = require('fs');
const { open } = require('open');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Configuration
const PORT = process.env.PORT || 8080;
const HOST = process.env.HOST || 'localhost';
const NODE_ENV = process.env.NODE_ENV || 'development';

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use(express.static(path.join(__dirname, 'dist')));
app.use(express.static(path.join(__dirname, 'public')));

// Enable CORS for development
if (NODE_ENV === 'development') {
    app.use((req, res, next) => {
        res.header('Access-Control-Allow-Origin', '*');
        res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
        res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
        if (req.method === 'OPTIONS') {
            res.sendStatus(200);
        } else {
            next();
        }
    });
}

// API Routes
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: require('./package.json').version,
        environment: NODE_ENV
    });
});

app.get('/api/capabilities', (req, res) => {
    res.json({
        webxr: true,
        vr: true,
        ar: true,
        handTracking: true,
        spatialAudio: true,
        performance: {
            targetFPS: 90,
            adaptiveQuality: true,
            comfortSettings: true
        }
    });
});

// WebSocket for real-time communication
const clients = new Set();

wss.on('connection', (ws) => {
    console.log('🔗 New WebSocket connection established');
    clients.add(ws);

    // Send welcome message
    ws.send(JSON.stringify({
        type: 'welcome',
        message: 'Connected to D&D AR/VR Server',
        timestamp: new Date().toISOString()
    }));

    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            console.log('📨 Received message:', data.type);

            // Handle different message types
            switch (data.type) {
                case 'heartbeat':
                    ws.send(JSON.stringify({
                        type: 'heartbeat-response',
                        timestamp: new Date().toISOString()
                    }));
                    break;

                case 'dice-roll':
                    // Broadcast dice roll to other clients
                    broadcastToOthers(ws, {
                        type: 'dice-roll',
                        playerId: data.playerId,
                        diceType: data.diceType,
                        result: data.result,
                        timestamp: new Date().toISOString()
                    });
                    break;

                case 'spell-cast':
                    // Broadcast spell cast to other clients
                    broadcastToOthers(ws, {
                        type: 'spell-cast',
                        playerId: data.playerId,
                        spellId: data.spellId,
                        target: data.target,
                        timestamp: new Date().toISOString()
                    });
                    break;

                case 'chat-message':
                    // Broadcast chat message
                    broadcastToAll({
                        type: 'chat-message',
                        playerId: data.playerId,
                        playerName: data.playerName,
                        message: data.message,
                        timestamp: new Date().toISOString()
                    });
                    break;

                default:
                    console.log('🔷 Unknown message type:', data.type);
            }
        } catch (error) {
            console.error('❌ Error parsing message:', error);
        }
    });

    ws.on('close', () => {
        console.log('🔌 WebSocket connection closed');
        clients.delete(ws);
    });

    ws.on('error', (error) => {
        console.error('❌ WebSocket error:', error);
        clients.delete(ws);
    });
});

function broadcastToAll(message) {
    const messageStr = JSON.stringify(message);
    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(messageStr);
        }
    });
}

function broadcastToOthers(sender, message) {
    const messageStr = JSON.stringify(message);
    clients.forEach(client => {
        if (client !== sender && client.readyState === WebSocket.OPEN) {
            client.send(messageStr);
        }
    });
}

// Serve main application
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/ar-view', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'ar-view.html'));
});

// Development middleware
if (NODE_ENV === 'development') {
    // Hot reload for static files
    const chokidar = require('chokidar');

    const watcher = chokidar.watch(path.join(__dirname, 'public'));
    watcher.on('change', (filepath) => {
        console.log(`📁 File changed: ${filepath}`);

        // Notify clients about reload
        broadcastToAll({
            type: 'reload',
            message: 'Static files updated',
            timestamp: new Date().toISOString()
        });
    });

    // Logging middleware
    app.use((req, res, next) => {
        const timestamp = new Date().toISOString();
        console.log(`📡 ${timestamp} ${req.method} ${req.url}`);
        next();
    });

    // Error handling middleware
    app.use((error, req, res, next) => {
        console.error('❌ Server error:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: NODE_ENV === 'development' ? error.message : 'Something went wrong',
            timestamp: new Date().toISOString()
        });
    });
}

// Performance monitoring
const performanceMetrics = {
    requests: 0,
    webSocketConnections: 0,
    startTime: Date.now()
};

app.use((req, res, next) => {
    performanceMetrics.requests++;
    next();
});

// Metrics endpoint
app.get('/api/metrics', (req, res) => {
    const uptime = Date.now() - performanceMetrics.startTime;
    res.json({
        uptime: uptime,
        requests: performanceMetrics.requests,
        webSocketConnections: clients.size,
        memory: process.memoryUsage(),
        timestamp: new Date().toISOString()
    });
});

// Fallback for SPA routing
app.get('*', (req, res) => {
    if (req.path.startsWith('/api/')) {
        res.status(404).json({
            error: 'API endpoint not found',
            path: req.path,
            timestamp: new Date().toISOString()
        });
    } else {
        // Serve index.html for SPA routing
        res.sendFile(path.join(__dirname, 'public', 'index.html'));
    }
});

// Start server
server.listen(PORT, HOST, () => {
    const url = `http://${HOST}:${PORT}`;
    console.log(`🚀 D&D AR/VR Development Server running at ${url}`);
    console.log(`📊 Metrics available at ${url}/api/metrics`);
    console.log(`🔌 WebSocket server running on ws://${HOST}:${PORT}`);
    console.log(`🌍 Environment: ${NODE_ENV}`);

    // Open browser in development
    if (NODE_ENV === 'development') {
        setTimeout(() => {
            open(url).catch(() => {
                console.log('📂 Could not open browser automatically. Please open manually.');
            });
        }, 1000);
    }
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 SIGTERM received, shutting down gracefully...');

    // Close WebSocket connections
    wss.close(() => {
        console.log('🔌 WebSocket server closed');
    });

    // Close HTTP server
    server.close(() => {
        console.log('🌐 HTTP server closed');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('🛑 SIGINT received, shutting down gracefully...');

    // Close WebSocket connections
    wss.close(() => {
        console.log('🔌 WebSocket server closed');
    });

    // Close HTTP server
    server.close(() => {
        console.log('🌐 HTTP server closed');
        process.exit(0);
    });
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('💥 Uncaught Exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

module.exports = { app, server, wss };