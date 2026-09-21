import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useTheme } from '@react-navigation/native';
import GameLobbyScreen from '../screens/game/GameLobbyScreen';
import GameBoardScreen from '../screens/game/GameBoardScreen';
import CharacterSheetScreen from '../screens/game/CharacterSheetScreen';
import DiceRollerScreen from '../screens/game/DiceRollerScreen';
import GameNotesScreen from '../screens/game/GameNotesScreen';
import VoiceChatScreen from '../screens/game/VoiceChatScreen';
import ARCameraScreen from '../screens/game/ARCameraScreen';
import MapScreen from '../screens/game/MapScreen';

export type GameStackParamList = {
  GameLobby: { sessionId: string };
  GameBoard: { sessionId: string };
  CharacterSheet: { characterId: string; sessionId: string };
  DiceRoller: { sessionId: string };
  GameNotes: { sessionId: string };
  VoiceChat: { sessionId: string };
  ARCamera: { sessionId: string };
  MapView: { sessionId: string };
};

const Stack = createStackNavigator<GameStackParamList>();

const GameNavigator: React.FC = () => {
  const theme = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.background,
          borderBottomWidth: 1,
          borderBottomColor: theme.colors.border,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: theme.colors.text,
        headerTitleStyle: {
          fontFamily: 'System',
          fontSize: 18,
          fontWeight: '600',
        },
        headerBackTitleVisible: false,
        gestureEnabled: true,
        cardStyle: {
          backgroundColor: theme.colors.background,
        },
        presentation: 'card',
      }}
    >
      <Stack.Screen
        name="GameLobby"
        component={GameLobbyScreen}
        initialParams={{ sessionId: '' }}
        options={{
          title: 'Game Lobby',
          headerShown: true,
          headerLeft: undefined, // Remove back button in lobby
        }}
      />
      <Stack.Screen
        name="GameBoard"
        component={GameBoardScreen}
        initialParams={{ sessionId: '' }}
        options={{
          title: 'Game Board',
          headerShown: false, // Full screen game experience
          gestureEnabled: false, // Prevent accidental back navigation during game
        }}
      />
      <Stack.Screen
        name="CharacterSheet"
        component={CharacterSheetScreen}
        initialParams={{ characterId: '', sessionId: '' }}
        options={{
          title: 'Character Sheet',
          headerShown: true,
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="DiceRoller"
        component={DiceRollerScreen}
        initialParams={{ sessionId: '' }}
        options={{
          title: 'Dice Roller',
          headerShown: true,
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="GameNotes"
        component={GameNotesScreen}
        initialParams={{ sessionId: '' }}
        options={{
          title: 'Game Notes',
          headerShown: true,
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="VoiceChat"
        component={VoiceChatScreen}
        initialParams={{ sessionId: '' }}
        options={{
          title: 'Voice Chat',
          headerShown: false,
          presentation: 'fullScreenModal',
        }}
      />
      <Stack.Screen
        name="ARCamera"
        component={ARCameraScreen}
        initialParams={{ sessionId: '' }}
        options={{
          title: 'AR Camera',
          headerShown: false,
          presentation: 'fullScreenModal',
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="MapView"
        component={MapScreen}
        initialParams={{ sessionId: '' }}
        options={{
          title: 'Game Map',
          headerShown: true,
          presentation: 'modal',
        }}
      />
    </Stack.Navigator>
  );
};

export default GameNavigator;