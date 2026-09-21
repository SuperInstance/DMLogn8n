import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Chip,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Tooltip,
  Badge,
  Fab
} from '@mui/material';
import {
  Send,
  SmartToy,
  Psychology,
  AutoStories,
  Groups,
  Balance,
  Lightbulb,
  History,
  Settings,
  ExpandMore,
  Close,
  Add,
  Edit,
  Save,
  Refresh,
  Star,
  ThumbUp,
  ThumbDown,
  ContentCopy,
  Download,
  Upload
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { useSocket } from '../../contexts/SocketContext';
import { useCampaign } from '../../contexts/CampaignContext';
import MessageBubble from '../../components/AIAssistant/MessageBubble';
import SuggestionCard from '../../components/AIAssistant/SuggestionCard';
import CharacterBackstoryGenerator from '../../components/AIAssistant/CharacterBackstoryGenerator';
import DialogueCreator from '../../components/AIAssistant/DialogueCreator';
import EncounterBalancer from '../../components/AIAssistant/EncounterBalancer';
import StoryEngine from '../../components/AIAssistant/StoryEngine';

const AIAssistant = ({ campaignId }) => {
  const { socket, connected, isDM } = useSocket();
  const { currentCampaign, characters, locations, quests } = useCampaign();

  const [activeTab, setActiveTab] = useState(0);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [aiSettings, setAiSettings] = useState({
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 1000,
    personality: 'helpful-creative',
    autoSuggest: true,
    contextAware: true
  });

  const [suggestions, setSuggestions] = useState([]);
  const [storyPrompt, setStoryPrompt] = useState('');
  const [backstoryDialog, setBackstoryDialog] = useState(false);
  const [dialogueDialog, setDialogueDialog] = useState(false);
  const [encounterDialog, setEncounterDialog] = useState(false);
  const [selectedCharacter, setSelectedCharacter] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Generate initial suggestions when campaign loads
  useEffect(() => {
    if (currentCampaign && aiSettings.autoSuggest) {
      generateSuggestions();
    }
  }, [currentCampaign, aiSettings.autoSuggest]);

  const generateSuggestions = async () => {
    if (!currentCampaign) return;

    const suggestionPrompts = [
      {
        type: 'story',
        title: 'Story Hook',
        prompt: `Generate a compelling story hook for a D&D campaign called "${currentCampaign.name}". The tone is ${currentCampaign.worldSettings?.tone || 'balanced'}.`
      },
      {
        type: 'encounter',
        title: 'Encounter Idea',
        prompt: `Suggest a balanced combat encounter for ${characters.filter(c => c.type === 'player').length} level ${getAveragePlayerLevel()} players.`
      },
      {
        type: 'npc',
        title: 'NPC Concept',
        prompt: `Create an interesting NPC concept that fits in a ${currentCampaign.worldSettings?.tone || 'balanced'} campaign.`
      },
      {
        type: 'location',
        title: 'Location Idea',
        prompt: `Design a unique location that would fit well in this campaign world.`
      }
    ];

    try {
      const newSuggestions = await Promise.all(
        suggestionPrompts.map(async (suggestion) => {
          const response = await callAI(suggestion.prompt, 150);
          return {
            ...suggestion,
            content: response,
            timestamp: new Date()
          };
        })
      );

      setSuggestions(newSuggestions);
    } catch (error) {
      console.error('Error generating suggestions:', error);
    }
  };

  const getAveragePlayerLevel = () => {
    const playerCharacters = characters.filter(c => c.type === 'player');
    if (playerCharacters.length === 0) return 1;
    const totalLevel = playerCharacters.reduce((sum, char) => sum + (char.level || 1), 0);
    return Math.round(totalLevel / playerCharacters.length);
  };

  const callAI = async (prompt, maxTokens = aiSettings.maxTokens) => {
    // This would call your AI API
    // For now, we'll simulate responses
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    const responses = [
      "Based on your campaign's current state, I suggest introducing a mysterious artifact that grants visions of an ancient civilization. This could lead the players to discover hidden ruins beneath the current location.",
      "Consider having a trusted NPC suddenly disappear, leaving behind only a cryptic note and an unusual magical residue. This creates immediate intrigue and gives players a clear objective.",
      "The local merchants guild could be secretly involved in smuggling rare magical components. Players might stumble upon this during routine shopping, leading to a complex web of intrigue.",
      "A celestial event approaching in 3 days could create time pressure - perhaps the alignment of moons will open a portal, or an eclipse will weaken magical wards throughout the region."
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Create context for the AI
      const context = {
        campaignName: currentCampaign?.name,
        playerCount: characters.filter(c => c.type === 'player').length,
        averageLevel: getAveragePlayerLevel(),
        currentLocation: currentCampaign?.currentState?.currentLocation,
        campaignTone: currentCampaign?.worldSettings?.tone,
        activeQuests: quests.filter(q => q.status === 'active').length,
        characters: characters.map(c => ({ name: c.name, level: c.level, class: c.class, type: c.type }))
      };

      const enhancedPrompt = `
Campaign Context: ${JSON.stringify(context, null, 2)}

User Question: ${inputMessage}

Please provide a helpful and creative response tailored to this D&D campaign. Consider the current campaign state and provide actionable advice.
      `;

      const aiResponse = await callAI(enhancedPrompt);

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: aiResponse,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error getting AI response:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'I apologize, but I encountered an error while processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const generateBackstory = async (character) => {
    setSelectedCharacter(character);
    setBackstoryDialog(true);
  };

  const createDialogue = async (npc, situation) => {
    setSelectedCharacter(npc);
    setDialogueDialog(true);
  };

  const balanceEncounter = async (partyLevel, difficulty) => {
    setEncounterDialog(true);
  };

  const generateStory = async () => {
    if (!storyPrompt.trim()) return;

    setIsLoading(true);
    try {
      const prompt = `
Generate a complete D&D adventure hook based on this prompt: "${storyPrompt}"

Include:
1. A compelling title
2. Brief setup (2-3 sentences)
3. Key NPCs involved
4. Potential locations
5. 3-4 possible outcomes
6. Rewards/consequences

Campaign: ${currentCampaign?.name}
Players: ${characters.filter(c => c.type === 'player').length} level ${getAveragePlayerLevel()}
Tone: ${currentCampaign?.worldSettings?.tone}
      `;

      const story = await callAI(prompt, 2000);

      const storyMessage = {
        id: Date.now(),
        type: 'story',
        content: story,
        prompt: storyPrompt,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, storyMessage]);
      setStoryPrompt('');
    } catch (error) {
      console.error('Error generating story:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = (messageId, feedback) => {
    // Send feedback to improve AI responses
    console.log(`Feedback for message ${messageId}: ${feedback}`);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const exportConversation = () => {
    const conversationText = messages
      .map(msg => `[${msg.timestamp.toLocaleString()}] ${msg.type.toUpperCase()}: ${msg.content}`)
      .join('\n\n');

    const blob = new Blob([conversationText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-conversation-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #330867 0%, #4a1a8c 100%)'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SmartToy sx={{ color: '#ff6b35', fontSize: 32 }} />
          <Box>
            <Typography variant="h4" className="fantasy-font" sx={{ color: 'white' }}>
              AI Assistant
            </Typography>
            <Typography variant="caption" sx={{ color: '#cccccc' }}>
              Powered by advanced AI for creative storytelling
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Badge badgeContent={suggestions.length} color="primary">
            <IconButton color="inherit" onClick={generateSuggestions}>
              <Lightbulb />
            </IconButton>
          </Badge>
          <IconButton color="inherit" onClick={exportConversation}>
            <Download />
          </IconButton>
          <IconButton color="inherit" onClick={() => setAiSettings(!aiSettings)}>
            <Settings />
          </IconButton>
        </Box>
      </Paper>

      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Sidebar - Quick Actions */}
        <Box sx={{ width: 300, borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} variant="scrollable" scrollButtons="auto">
              <Tab label="Chat" icon={<Chat />} />
              <Tab label="Generate" icon={<AutoStories />} />
              <Tab label="Balance" icon={<Balance />} />
              <Tab label="History" icon={<History />} />
            </Tabs>
          </Box>

          <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            {activeTab === 0 && (
              <Box>
                <Typography variant="h6" gutterBottom>Quick Actions</Typography>
                <List dense>
                  <ListItem button onClick={() => characters.filter(c => c.type === 'player').forEach(generateBackstory)}>
                    <ListItemIcon><Groups /></ListItemIcon>
                    <ListItemText primary="Generate Backstories" secondary="For all player characters" />
                  </ListItem>
                  <ListItem button onClick={() => npcs.slice(0, 3).forEach(npc => createDialogue(npc, 'greeting'))}>
                    <ListItemIcon><Chat /></ListItemIcon>
                    <ListItemText primary="Create Dialogue" secondary="For key NPCs" />
                  </ListItem>
                  <ListItem button onClick={() => balanceEncounter(getAveragePlayerLevel(), 'medium')}>
                    <ListItemIcon><Balance /></ListItemIcon>
                    <ListItemText primary="Balance Encounter" secondary={`For level ${getAveragePlayerLevel()} party`} />
                  </ListItem>
                </List>

                <Divider sx={{ my: 2 }} />

                <Typography variant="h6" gutterBack>Character Tools</Typography>
                <List dense>
                  {characters.filter(c => c.type === 'player').map(character => (
                    <ListItem key={character.id} button onClick={() => generateBackstory(character)}>
                      <ListItemIcon><Person /></ListItemIcon>
                      <ListItemText primary={character.name} secondary={`${character.level} ${character.class}`} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {activeTab === 1 && (
              <StoryEngine
                campaign={currentCampaign}
                characters={characters}
                locations={locations}
                onStoryGenerated={(story) => {
                  const storyMessage = {
                    id: Date.now(),
                    type: 'story',
                    content: story,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, storyMessage]);
                }}
              />
            )}

            {activeTab === 2 && (
              <EncounterBalancer
                partyLevel={getAveragePlayerLevel()}
                partySize={characters.filter(c => c.type === 'player').length}
                onBalanced={(encounter) => {
                  const encounterMessage = {
                    id: Date.now(),
                    type: 'encounter',
                    content: encounter,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, encounterMessage]);
                }}
              />
            )}

            {activeTab === 3 && (
              <Box>
                <Typography variant="h6" gutterBottom>Conversation History</Typography>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={generateSuggestions}
                  sx={{ mb: 2 }}
                >
                  Refresh Suggestions
                </Button>

                <Typography variant="subtitle2" gutterBack>Recent Suggestions</Typography>
                {suggestions.map((suggestion, index) => (
                  <Accordion key={index} sx={{ mb: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="subtitle2">{suggestion.title}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        {suggestion.content}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button size="small" startIcon={<Add />}>
                          Use This
                        </Button>
                        <Button size="small" startIcon={<Edit />}>
                          Modify
                        </Button>
                        <Button size="small" startIcon={<ContentCopy />} onClick={() => copyToClipboard(suggestion.content)}>
                          Copy
                        </Button>
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Box>
            )}
          </Box>
        </Box>

        {/* Main Chat Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Messages */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            {messages.length === 0 ? (
              <Box sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center'
              }}>
                <SmartToy sx={{ fontSize: 64, color: '#666', mb: 2 }} />
                <Typography variant="h5" color="text.secondary" gutterBottom>
                  Welcome to your AI Assistant
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  I can help you with story ideas, character development, encounter balancing, and more.
                </Typography>
                <Grid container spacing={2} sx={{ maxWidth: 600, mx: 'auto' }}>
                  <Grid item xs={12} sm={6}>
                    <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
                      <CardContent sx={{ textAlign: 'center', py: 2 }}>
                        <AutoStories color="primary" sx={{ fontSize: 32, mb: 1 }} />
                        <Typography variant="subtitle2">Generate Story</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
                      <CardContent sx={{ textAlign: 'center', py: 2 }}>
                        <Psychology color="secondary" sx={{ fontSize: 32, mb: 1 }} />
                        <Typography variant="subtitle2">Balance Encounter</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Box>
            ) : (
              <Box>
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    onFeedback={handleFeedback}
                    onCopy={copyToClipboard}
                  />
                ))}
                <div ref={messagesEndRef} />
              </Box>
            )}
          </Box>

          {/* Input Area */}
          <Paper sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder="Ask me anything about your campaign..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading || !connected}
                InputProps={{
                  startAdornment: <SmartToy sx={{ color: 'action.active', mr: 1 }} />
                }}
              />
              <IconButton
                color="primary"
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading || !connected}
                sx={{
                  bgcolor: '#ff6b35',
                  color: 'white',
                  '&:hover': { bgcolor: '#cc5528' },
                  '&:disabled': { bgcolor: 'action.disabled' }
                }}
              >
                {isLoading ? <CircularProgress size={24} /> : <Send />}
              </IconButton>
            </Box>
            {!connected && (
              <Alert severity="warning" sx={{ mt: 1 }}>
                AI Assistant requires an active connection to the server.
              </Alert>
            )}
          </Paper>
        </Box>

        {/* Right Sidebar - Suggestions */}
        {suggestions.length > 0 && (
          <Box sx={{ width: 320, borderLeft: 1, borderColor: 'divider', p: 2, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              <Lightbulb sx={{ verticalAlign: 'middle', mr: 1 }} />
              AI Suggestions
            </Typography>

            {suggestions.map((suggestion, index) => (
              <SuggestionCard
                key={index}
                suggestion={suggestion}
                onAccept={() => {
                  // Apply suggestion
                }}
                onModify={() => {
                  // Open in chat for modification
                  setInputMessage(`Help me expand on this idea: ${suggestion.content}`);
                }}
                onDismiss={() => {
                  setSuggestions(prev => prev.filter((_, i) => i !== index));
                }}
              />
            ))}
          </Box>
        )}
      </Box>

      {/* Character Backstory Dialog */}
      <Dialog open={backstoryDialog} onClose={() => setBackstoryDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Generate Character Backstory</DialogTitle>
        <DialogContent>
          {selectedCharacter && (
            <CharacterBackstoryGenerator
              character={selectedCharacter}
              campaign={currentCampaign}
              onBackstoryGenerated={(backstory) => {
                const backstoryMessage = {
                  id: Date.now(),
                  type: 'backstory',
                  content: backstory,
                  characterId: selectedCharacter.id,
                  timestamp: new Date()
                };
                setMessages(prev => [...prev, backstoryMessage]);
                setBackstoryDialog(false);
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Dialogue Creator Dialog */}
      <Dialog open={dialogueDialog} onClose={() => setDialogueDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Create NPC Dialogue</DialogTitle>
        <DialogContent>
          {selectedCharacter && (
            <DialogueCreator
              npc={selectedCharacter}
              campaign={currentCampaign}
              onDialogueCreated={(dialogue) => {
                const dialogueMessage = {
                  id: Date.now(),
                  type: 'dialogue',
                  content: dialogue,
                  npcId: selectedCharacter.id,
                  timestamp: new Date()
                };
                setMessages(prev => [...prev, dialogueMessage]);
                setDialogueDialog(false);
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          bgcolor: '#ff6b35'
        }}
        onClick={generateSuggestions}
      >
        <Lightbulb />
      </Fab>
    </Box>
  );
};

export default AIAssistant;