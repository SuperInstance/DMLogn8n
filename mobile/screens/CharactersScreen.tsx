import React, { useEffect, useCallback, useState } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  Alert,
  Animated,
} from 'react-native';
import {
  Text,
  Card,
  Button,
  Avatar,
  Icon,
  SearchBar,
  Chip,
  FAB,
} from 'react-native-elements';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useTheme } from '@react-navigation/native';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { fetchUserCharacters, deleteCharacter } from '../store/slices/userSlice';
import { Character } from '../types';
import CharacterCard from '../components/CharacterCard';
import LoadingScreen from './LoadingScreen';

type CharactersScreenNavigationProp = NativeStackNavigationProp<any>;

const CharactersScreen: React.FC = () => {
  const navigation = useNavigation<CharactersScreenNavigationProp>();
  const theme = useTheme();
  const dispatch = useDispatch();

  const { characters, isLoading, error } = useSelector((state: RootState) => state.user);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCharacters, setSelectedCharacters] = useState<string[]>([]);
  const [isSelectionMode, setIsSelectionMode] = useState(false);

  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = useCallback(async () => {
    try {
      await dispatch(fetchUserCharacters());
    } catch (error) {
      console.error('Failed to load characters:', error);
      Alert.alert('Error', 'Failed to load characters');
    }
  }, [dispatch]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await loadCharacters();
    } finally {
      setRefreshing(false);
    }
  }, [loadCharacters]);

  const handleCharacterPress = (character: Character) => {
    if (isSelectionMode) {
      toggleCharacterSelection(character.id);
    } else {
      navigation.navigate('CharacterDetail', { characterId: character.id });
    }
  };

  const handleCharacterLongPress = (character: Character) => {
    if (!isSelectionMode) {
      setIsSelectionMode(true);
      setSelectedCharacters([character.id]);
    }
  };

  const toggleCharacterSelection = (characterId: string) => {
    setSelectedCharacters(prev =>
      prev.includes(characterId)
        ? prev.filter(id => id !== characterId)
        : [...prev, characterId]
    );
  };

  const handleDeleteCharacter = async (character: Character) => {
    Alert.alert(
      'Delete Character',
      `Are you sure you want to delete ${character.name}? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await dispatch(deleteCharacter(character.id));
              await loadCharacters();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete character');
            }
          },
        },
      ]
    );
  };

  const handleBatchDelete = async () => {
    if (selectedCharacters.length === 0) return;

    Alert.alert(
      'Delete Characters',
      `Are you sure you want to delete ${selectedCharacters.length} character(s)? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await Promise.all(
                selectedCharacters.map(id => dispatch(deleteCharacter(id)))
              );
              setSelectedCharacters([]);
              setIsSelectionMode(false);
              await loadCharacters();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete characters');
            }
          },
        },
      ]
    );
  };

  const exitSelectionMode = () => {
    setIsSelectionMode(false);
    setSelectedCharacters([]);
  };

  const filteredCharacters = characters?.filter(character => {
    const matchesSearch = character.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         character.class.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filter === 'all' ||
                         (filter === 'active' && character.health > 0) ||
                         (filter === 'inactive' && character.health <= 0);
    return matchesSearch && matchesFilter;
  }) || [];

  const renderCharacter = ({ item, index }: { item: Character; index: number }) => (
    <Animated.View
      style={{
        transform: [
          {
            translateY: new Animated.Value(0).setValue(
              isSelectionMode && selectedCharacters.includes(item.id) ? -2 : 0
            ),
          },
        ],
      }}
    >
      <CharacterCard
        character={item}
        onPress={() => handleCharacterPress(item)}
        onLongPress={() => handleCharacterLongPress(item)}
        onEdit={() => navigation.navigate('CharacterDetail', { characterId: item.id })}
        onDelete={() => handleDeleteCharacter(item)}
        showActions={!isSelectionMode}
        isSelected={isSelectionMode && selectedCharacters.includes(item.id)}
        showSelectionIndicator={isSelectionMode}
      />
    </Animated.View>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Icon
        name="people-outline"
        type="ionicon"
        size={64}
        color={theme.colors.textSecondary}
      />
      <Text h4 style={[styles.emptyTitle, { color: theme.colors.text }]}>
        No Characters Yet
      </Text>
      <Text style={[styles.emptySubtitle, { color: theme.colors.textSecondary }]}>
        Create your first character to begin your adventure
      </Text>
      <Button
        title="Create Character"
        onPress={() => navigation.navigate('CreateCharacter')}
        buttonStyle={{
          backgroundColor: theme.colors.primary,
          borderRadius: 12,
          paddingHorizontal: 24,
          paddingVertical: 12,
          marginTop: 24,
        }}
        titleStyle={{
          fontSize: 16,
          fontWeight: '600',
        }}
      />
    </View>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <SearchBar
        placeholder="Search characters..."
        onChangeText={setSearchQuery}
        value={searchQuery}
        containerStyle={styles.searchContainer}
        inputContainerStyle={[styles.searchInput, { backgroundColor: theme.colors.inputBackground }]}
        inputStyle={{ color: theme.colors.text }}
        placeholderTextColor={theme.colors.textSecondary}
        searchIcon={{ color: theme.colors.textSecondary }}
        clearIcon={{ color: theme.colors.textSecondary }}
      />

      <View style={styles.filters}>
        <Chip
          title="All"
          type={filter === 'all' ? 'solid' : 'outline'}
          onPress={() => setFilter('all')}
          buttonStyle={[
            styles.chip,
            filter === 'all' && { backgroundColor: theme.colors.primary },
          ]}
          titleStyle={[
            styles.chipText,
            filter === 'all' && { color: '#FFFFFF' },
          ]}
        />
        <Chip
          title="Active"
          type={filter === 'active' ? 'solid' : 'outline'}
          onPress={() => setFilter('active')}
          buttonStyle={[
            styles.chip,
            filter === 'active' && { backgroundColor: theme.colors.success },
          ]}
          titleStyle={[
            styles.chipText,
            filter === 'active' && { color: '#FFFFFF' },
          ]}
        />
        <Chip
          title="Inactive"
          type={filter === 'inactive' ? 'solid' : 'outline'}
          onPress={() => setFilter('inactive')}
          buttonStyle={[
            styles.chip,
            filter === 'inactive' && { backgroundColor: theme.colors.textSecondary },
          ]}
          titleStyle={[
            styles.chipText,
            filter === 'inactive' && { color: '#FFFFFF' },
          ]}
        />
      </View>
    </View>
  );

  if (isLoading && !characters) {
    return <LoadingScreen />;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {isSelectionMode && (
        <View style={[styles.selectionHeader, { backgroundColor: theme.colors.surface }]}>
          <View style={styles.selectionInfo}>
            <Text style={[styles.selectionText, { color: theme.colors.text }]}>
              {selectedCharacters.length} selected
            </Text>
          </View>
          <View style={styles.selectionActions}>
            <Button
              type="clear"
              title="Cancel"
              onPress={exitSelectionMode}
              titleStyle={{ color: theme.colors.textSecondary }}
            />
            {selectedCharacters.length > 0 && (
              <Button
                type="clear"
                title="Delete"
                onPress={handleBatchDelete}
                titleStyle={{ color: theme.colors.error }}
              />
            )}
          </View>
        </View>
      )}

      <FlatList
        data={filteredCharacters}
        renderItem={renderCharacter}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmptyState}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={[theme.colors.primary]}
            tintColor={theme.colors.primary}
          />
        }
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
      />

      <FAB
        icon={<Icon name="add" type="ionicon" color="#FFFFFF" />}
        placement="right"
        color={theme.colors.primary}
        onPress={() => navigation.navigate('CreateCharacter')}
        disabled={isSelectionMode}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  selectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  selectionInfo: {
    flex: 1,
  },
  selectionText: {
    fontSize: 16,
    fontWeight: '600',
  },
  selectionActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  header: {
    padding: 16,
  },
  searchContainer: {
    backgroundColor: 'transparent',
    borderBottomWidth: 0,
    borderTopWidth: 0,
    paddingHorizontal: 0,
    paddingVertical: 0,
    marginBottom: 16,
  },
  searchInput: {
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 48,
  },
  filters: {
    flexDirection: 'row',
    gap: 8,
  },
  chip: {
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  chipText: {
    fontSize: 14,
    fontWeight: '500',
  },
  listContainer: {
    paddingHorizontal: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
  },
});

export default CharactersScreen;