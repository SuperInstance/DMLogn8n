import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, IconButton, Tooltip, Badge, Chip } from '@mui/material';
import { PlayArrow, Pause, Edit, Settings, Code, Person } from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';
import { Terminal } from './Terminal';
import { StatusBar } from './StatusBar';
import { AutomationPanel } from './AutomationPanel';
import { CoderChannel } from './CoderChannel';
import { ControlModeToggle } from './ControlModeToggle';

interface EnhancedCharacterPortalProps {
  characterId: string;
  characterName: string;
  onTakeControl?: () => void;
  onReleaseControl?: () => void;
}

export const EnhancedCharacterPortal: React.FC<EnhancedCharacterPortalProps> = ({
  characterId,
  characterName,
  onTakeControl,
  onReleaseControl,
}) => {
  const [controlMode, setControlMode] = useState<'agent' | 'human' | 'hybrid'>('agent');
  const [characterState, setCharacterState] = useState({
    hp: 50,
    maxHp: 60,
    mp: 8,
    maxMp: 12,
    location: 'Forest',
    status: [],
    gold: 250,
    experience: 1250,
    level: 3,
  });
  const [terminalOutput, setTerminalOutput] = useState<TerminalLine[]>([]);
  const [aiThinking, setAiThinking] = useState<string>('');
  const [showCoderChannel, setShowCoderChannel] = useState(false);
  const [showAutomations, setShowAutomations] = useState(true);
  const [theme, setTheme] = useState('classic_green');
  const terminalRef = useRef<HTMLDivElement>(null);

  // WebSocket for real-time character updates
  const { lastMessage, sendMessage } = useWebSocket(
    `ws://localhost:8000/ws/character/${characterId}`
  );

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);

      switch (data.type) {
        case 'terminal_output':
          addTerminalLine(data);
          break;
        case 'state_update':
          setCharacterState(prev => ({ ...prev, ...data.state }));
          break;
        case 'ai_thinking':
          setAiThinking(data.thought);
          setTimeout(() => setAiThinking(''), 3000);
          break;
        case 'automation_request':
          setShowCoderChannel(true);
          break;
      }
    }
  }, [lastMessage]);

  const addTerminalLine = (data: any) => {
    const line: TerminalLine = {
      id: Date.now(),
      timestamp: new Date(),
      type: data.type || 'info',
      source: data.source || 'system',
      content: data.content,
    };

    setTerminalOutput(prev => [...prev.slice(-100), line]);

    // Auto-scroll to bottom
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  };

  const handleControlModeChange = async (newMode: 'agent' | 'human' | 'hybrid') => {
    setControlMode(newMode);

    if (newMode === 'human') {
      onTakeControl?.();
      addTerminalLine({
        type: 'system',
        content: `[HUMAN CONTROL] You are now directly controlling ${characterName}`,
        source: 'system'
      });
    } else if (newMode === 'agent') {
      onReleaseControl?.();
      addTerminalLine({
        type: 'system',
        content: `[AI CONTROL] ${characterName} is now playing autonomously`,
        source: 'system'
      });
    }
  };

  const handleCommand = (command: string) => {
    if (command.startsWith('/')) {
      // Handle special commands
      handleSlashCommand(command);
    } else {
      // Send to game
      sendMessage(JSON.stringify({
        type: 'command',
        command,
        source: controlMode === 'human' ? 'human' : 'agent'
      }));

      addTerminalLine({
        type: 'command',
        content: `> ${command}`,
        source: 'player'
      });
    }
  };

  const handleSlashCommand = (command: string) => {
    const [cmd, ...args] = command.substring(1).split(' ');

    switch (cmd) {
      case 'help':
        addTerminalLine({
          type: 'help',
          content: `Available commands:
  /help - Show this help
  /status - Show detailed character status
  /inventory - View inventory
  /abilities - List abilities and spells
  /automations - Toggle automation panel
  /coder - Open coder channel
  /theme <name> - Change terminal theme`,
          source: 'system'
        });
        break;

      case 'automations':
        setShowAutomations(!showAutomations);
        break;

      case 'coder':
        setShowCoderChannel(!showCoderChannel);
        break;

      case 'theme':
        if (args[0]) {
          setTheme(args[0]);
          addTerminalLine({
            type: 'system',
            content: `Theme changed to ${args[0]}`,
            source: 'system'
          });
        }
        break;
    }
  };

  const themeColors = {
    classic_green: {
      bg: '#000000',
      text: '#00FF00',
      border: '#003300',
    },
    matrix: {
      bg: '#000000',
      text: '#00FF41',
      border: '#003300',
    },
    amber: {
      bg: '#000000',
      text: '#FFB000',
      border: '#332200',
    },
    cyber_blue: {
      bg: '#000000',
      text: '#00FFFF',
      border: '#003333',
    }
  };

  const colors = themeColors[theme as keyof typeof themeColors] || themeColors.classic_green;

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: colors.bg,
        color: colors.text,
        fontFamily: 'Monaco, Consolas, monospace',
        fontSize: '14px',
        overflow: 'hidden',
      }}
    >
      {/* Header with Status Bar */}
      <StatusBar
        characterName={characterName}
        characterState={characterState}
        controlMode={controlMode}
        onControlModeChange={handleControlModeChange}
        theme={colors}
      />

      {/* AI Thinking Display */}
      {aiThinking && (
        <Box
          sx={{
            px: 2,
            py: 1,
            bgcolor: 'rgba(255, 255, 0, 0.1)',
            borderBottom: `1px solid ${colors.border}`,
          }}
        >
          <Typography variant="body2" sx={{ color: '#FFFF00' }}>
            [AI] {aiThinking}
          </Typography>
        </Box>
      )}

      {/* Main Content Area */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Terminal */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            borderRight: `1px solid ${colors.border}`,
          }}
        >
          <Terminal
            ref={terminalRef}
            output={terminalOutput}
            onCommand={handleCommand}
            disabled={controlMode !== 'human'}
            theme={colors}
          />
        </Box>

        {/* Right Panel */}
        {(showAutomations || showCoderChannel) && (
          <Box
            sx={{
              width: 350,
              display: 'flex',
              flexDirection: 'column',
              borderLeft: `1px solid ${colors.border}`,
              bgcolor: 'rgba(0, 0, 0, 0.5)',
            }}
          >
            {/* Tab Navigation */}
            <Box
              sx={{
                display: 'flex',
                borderBottom: `1px solid ${colors.border}`,
                p: 1,
              }}
            >
              <Chip
                icon={<Code />}
                label="Automations"
                onClick={() => setShowCoderChannel(false)}
                color={showCoderChannel ? 'default' : 'primary'}
                size="small"
                sx={{ mr: 1 }}
              />
              <Chip
                icon={<Person />}
                label="Coder"
                onClick={() => setShowCoderChannel(true)}
                color={showCoderChannel ? 'primary' : 'default'}
                size="small"
              />
            </Box>

            {/* Panel Content */}
            <Box sx={{ flex: 1, overflow: 'auto' }}>
              {showCoderChannel ? (
                <CoderChannel
                  characterId={characterId}
                  onAddAutomation={(code) => {
                    sendMessage(JSON.stringify({
                      type: 'deploy_automation',
                      code,
                    }));
                  }}
                  theme={colors}
                />
              ) : (
                <AutomationPanel
                  characterId={characterId}
                  onToggle={(automationId, active) => {
                    sendMessage(JSON.stringify({
                      type: 'toggle_automation',
                      automationId,
                      active,
                    }));
                  }}
                  theme={colors}
                />
              )}
            </Box>
          </Box>
        )}

        {/* Collapsed Right Panel Controls */}
        {!showAutomations && !showCoderChannel && (
          <Box
            sx={{
              width: 50,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              py: 2,
              gap: 2,
            }}
          >
            <Tooltip title="Show Automations">
              <IconButton
                onClick={() => {
                  setShowAutomations(true);
                  setShowCoderChannel(false);
                }}
                sx={{ color: colors.text }}
              >
                <Code />
              </IconButton>
            </Tooltip>

            <Tooltip title="Open Coder Channel">
              <IconButton
                onClick={() => {
                  setShowCoderChannel(true);
                  setShowAutomations(false);
                }}
                sx={{ color: colors.text }}
              >
                <Person />
              </IconButton>
            </Tooltip>

            <Tooltip title="Settings">
              <IconButton sx={{ color: colors.text }}>
                <Settings />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Box>

      {/* Control Mode Indicator */}
      <Box
        sx={{
          position: 'fixed',
          top: 20,
          right: 20,
          zIndex: 1000,
        }}
      >
        <ControlModeToggle
          mode={controlMode}
          onChange={handleControlModeChange}
        />
      </Box>
    </Box>
  );
};

// Types
interface TerminalLine {
  id: number;
  timestamp: Date;
  type: 'info' | 'combat' | 'dialogue' | 'system' | 'command' | 'help' | 'error';
  source: 'player' | 'ai' | 'dm' | 'system' | 'coder';
  content: string;
}

interface CharacterState {
  hp: number;
  maxHp: number;
  mp: number;
  maxMp: number;
  location: string;
  status: string[];
  gold: number;
  experience: number;
  level: number;
}