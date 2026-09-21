# DM World Builder Portal

A comprehensive real-time world editing and campaign management system for Dungeon Masters.

## Features

### Real-Time Game Monitoring
- Live view of all character actions and locations
- Combat tracking with initiative and status
- Party dynamics and relationships
- Event timeline with rewind capability
- Performance metrics and analytics

### World Editing Tools
- Location/room creation and editing
- NPC creation with AI personality generation
- Item and treasure management
- Encounter designer with difficulty balancing
- Quest and story arc creation

### Dynamic Content Injection
- Real-time event injection during play
- Environmental effects and weather
- Random encounter triggers
- Plot twist deployment
- Custom creature spawning

### Campaign Management
- Session planning and notes
- Player progress tracking
- Homebrew content library
- House rules configuration
- Campaign state persistence

### AI Assistant Integration
- AI-powered encounter balancing
- Story suggestion engine
- Character backstory generator
- Dialogue creation assistance
- Campaign optimization recommendations

## Installation

```bash
npm run install-all
```

## Development

```bash
npm run dev
```

This will start both the backend server and frontend client concurrently.

## Architecture

- **Backend**: Node.js with Express, Socket.IO for real-time communication
- **Frontend**: React with modern UI components
- **Database**: MongoDB for data persistence
- **Real-time**: WebSocket connections via Socket.IO
- **AI Integration**: OpenAI API for content generation and assistance

## Project Structure

```
dm-world-builder/
├── server/          # Backend API and WebSocket server
├── client/          # React frontend application
├── shared/          # Shared types and utilities
└── docs/           # Documentation
```