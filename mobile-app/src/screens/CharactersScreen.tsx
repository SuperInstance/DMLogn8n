import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { fetchCharacters } from '../../store/slices/characterSlice';
import { RootState } from '../../store';
import { useTheme } from '../../hooks/useTheme';
import { CharacterCard } from '../../components/CharacterCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

const CharactersScreen: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();

  const { characters, isLoading } = useSelector((state: RootState) => state.characters);

  const handleCharacterPress = (characterId: string) => {
    // Navigate to character details
    console.log('Character pressed:', characterId);
  };

  const handleCreateCharacter = () => {
    // Navigate to character creation
    console.log('Create character');
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Characters
        </Text>
        <TouchableOpacity
          style={[styles.createButton, { backgroundColor: theme.colors.primary }]}
          onPress={handleCreateCharacter}
        >
          <Icon name="add" size={24} color="white" />
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          {characters.length > 0 ? (
            characters.map((character) => (
              <View key={character.id} style={styles.characterCard}>
                <CharacterCard
                  character={character}
                  onPress={() => handleCharacterPress(character.id)}
                  size="large"
                />
              </View>
            ))
          ) : (
            <View style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}>
              <Icon name="people-outline" size={64} color={theme.colors.textSecondary} />
              <Text style={[styles.emptyStateText, { color: theme.colors.textSecondary }]}>
                No characters yet
              </Text>
              <TouchableOpacity
                style={[styles.createCharacterButton, { backgroundColor: theme.colors.primary }]}
                onPress={handleCreateCharacter}
              >
                <Text style={styles.createCharacterButtonText}>
                  Create Your First Character
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  createButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: 16,
  },
  characterCard: {
    marginBottom: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    borderRadius: 12,
    marginTop: 50,
  },
  emptyStateText: {
    fontSize: 18,
    marginTop: 16,
    marginBottom: 24,
    textAlign: 'center',
  },
  createCharacterButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  createCharacterButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CharactersScreen;