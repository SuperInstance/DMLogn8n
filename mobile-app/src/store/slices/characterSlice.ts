import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Character, CharacterMemory, APIResponse, PaginatedResponse } from '../../types';
import { characterService } from '../../services/characterService';
import { storageService } from '../../services/storageService';

interface CharacterState {
  characters: Character[];
  activeCharacter: Character | null;
  isLoading: boolean;
  error: string | null;
  memories: CharacterMemory[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  filters: {
    campaignId?: string;
    userId?: string;
    class?: string;
    level?: number;
    search?: string;
  };
}

const initialState: CharacterState = {
  characters: [],
  activeCharacter: null,
  isLoading: false,
  error: null,
  memories: [],
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
  },
  filters: {},
};

// Async thunks
export const fetchCharacters = createAsyncThunk(
  'character/fetchCharacters',
  async (
    params: { page?: number; limit?: number; filters?: CharacterState['filters'] },
    { rejectWithValue }
  ) => {
    try {
      const response = await characterService.getCharacters({
        page: params.page || 1,
        limit: params.limit || 20,
        ...params.filters,
      });

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch characters');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch characters');
    }
  }
);

export const fetchCharacter = createAsyncThunk(
  'character/fetchCharacter',
  async (characterId: string, { rejectWithValue }) => {
    try {
      const response = await characterService.getCharacter(characterId);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch character');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch character');
    }
  }
);

export const createCharacter = createAsyncThunk(
  'character/createCharacter',
  async (characterData: Partial<Character>, { rejectWithValue }) => {
    try {
      const response = await characterService.createCharacter(characterData);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to create character');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to create character');
    }
  }
);

export const updateCharacter = createAsyncThunk(
  'character/updateCharacter',
  async (
    { characterId, data }: { characterId: string; data: Partial<Character> },
    { rejectWithValue }
  ) => {
    try {
      const response = await characterService.updateCharacter(characterId, data);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to update character');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to update character');
    }
  }
);

export const deleteCharacter = createAsyncThunk(
  'character/deleteCharacter',
  async (characterId: string, { rejectWithValue }) => {
    try {
      const response = await characterService.deleteCharacter(characterId);

      if (response.success) {
        return characterId;
      } else {
        throw new Error(response.error || 'Failed to delete character');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to delete character');
    }
  }
);

export const levelUpCharacter = createAsyncThunk(
  'character/levelUpCharacter',
  async (
    { characterId, classData }: { characterId: string; classData: any },
    { rejectWithValue }
  ) => {
    try {
      const response = await characterService.levelUpCharacter(characterId, classData);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to level up character');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to level up character');
    }
  }
);

export const addCharacterMemory = createAsyncThunk(
  'character/addMemory',
  async (
    { characterId, memory }: { characterId: string; memory: Partial<CharacterMemory> },
    { rejectWithValue }
  ) => {
    try {
      const response = await characterService.addMemory(characterId, memory);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to add memory');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to add memory');
    }
  }
);

export const updateCharacterHealth = createAsyncThunk(
  'character/updateHealth',
  async (
    { characterId, health }: { characterId: string; health: Partial<Character['health']> },
    { rejectWithValue }
  ) => {
    try {
      const response = await characterService.updateHealth(characterId, health);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to update health');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to update health');
    }
  }
);

export const updateCharacterResources = createAsyncThunk(
  'character/updateResources',
  async (
    { characterId, resources }: { characterId: string; resources: Character['resources'] },
    { rejectWithValue }
  ) => {
    try {
      const response = await characterService.updateResources(characterId, resources);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to update resources');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to update resources');
    }
  }
);

export const uploadCharacterPortrait = createAsyncThunk(
  'character/uploadPortrait',
  async (
    { characterId, imageUri }: { characterId: string; imageUri: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await characterService.uploadPortrait(characterId, imageUri);

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to upload portrait');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to upload portrait');
    }
  }
);

const characterSlice = createSlice({
  name: 'character',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },

    setActiveCharacter: (state, action: PayloadAction<Character | null>) => {
      state.activeCharacter = action.payload;
    },

    updateLocalCharacter: (state, action: PayloadAction<{ characterId: string; data: Partial<Character> }>) => {
      const { characterId, data } = action.payload;

      // Update active character if it matches
      if (state.activeCharacter && state.activeCharacter.id === characterId) {
        state.activeCharacter = { ...state.activeCharacter, ...data };
      }

      // Update character in list
      const characterIndex = state.characters.findIndex(char => char.id === characterId);
      if (characterIndex !== -1) {
        state.characters[characterIndex] = { ...state.characters[characterIndex], ...data };
      }
    },

    setFilters: (state, action: PayloadAction<Partial<CharacterState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    clearFilters: (state) => {
      state.filters = {};
    },

    addLocalMemory: (state, action: PayloadAction<CharacterMemory>) => {
      state.memories.unshift(action.payload);
    },

    updateLocalMemory: (state, action: PayloadAction<{ memoryId: string; data: Partial<CharacterMemory> }>) => {
      const { memoryId, data } = action.payload;
      const memoryIndex = state.memories.findIndex(memory => memory.id === memoryId);
      if (memoryIndex !== -1) {
        state.memories[memoryIndex] = { ...state.memories[memoryIndex], ...data };
      }
    },

    deleteLocalMemory: (state, action: PayloadAction<string>) => {
      state.memories = state.memories.filter(memory => memory.id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch characters
      .addCase(fetchCharacters.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCharacters.fulfilled, (state, action) => {
        state.isLoading = false;
        state.characters = action.payload.items;
        state.pagination = {
          page: action.payload.page,
          limit: action.payload.limit,
          total: action.payload.total,
          totalPages: action.payload.totalPages,
        };
      })
      .addCase(fetchCharacters.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Fetch single character
      .addCase(fetchCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        state.activeCharacter = action.payload;

        // Update or add to list
        const existingIndex = state.characters.findIndex(char => char.id === action.payload.id);
        if (existingIndex !== -1) {
          state.characters[existingIndex] = action.payload;
        } else {
          state.characters.push(action.payload);
        }
      })
      .addCase(fetchCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Create character
      .addCase(createCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        state.characters.unshift(action.payload);
        state.activeCharacter = action.payload;
      })
      .addCase(createCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Update character
      .addCase(updateCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        const updatedCharacter = action.payload;

        // Update active character
        if (state.activeCharacter && state.activeCharacter.id === updatedCharacter.id) {
          state.activeCharacter = updatedCharacter;
        }

        // Update in list
        const characterIndex = state.characters.findIndex(char => char.id === updatedCharacter.id);
        if (characterIndex !== -1) {
          state.characters[characterIndex] = updatedCharacter;
        }
      })
      .addCase(updateCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Delete character
      .addCase(deleteCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        const deletedId = action.payload;

        state.characters = state.characters.filter(char => char.id !== deletedId);

        if (state.activeCharacter && state.activeCharacter.id === deletedId) {
          state.activeCharacter = null;
        }
      })
      .addCase(deleteCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Level up character
      .addCase(levelUpCharacter.fulfilled, (state, action) => {
        const leveledCharacter = action.payload;

        // Update active character
        if (state.activeCharacter && state.activeCharacter.id === leveledCharacter.id) {
          state.activeCharacter = leveledCharacter;
        }

        // Update in list
        const characterIndex = state.characters.findIndex(char => char.id === leveledCharacter.id);
        if (characterIndex !== -1) {
          state.characters[characterIndex] = leveledCharacter;
        }
      })

      // Add memory
      .addCase(addCharacterMemory.fulfilled, (state, action) => {
        state.memories.unshift(action.payload);

        // Update character's memories
        if (state.activeCharacter) {
          state.activeCharacter.memories = [action.payload, ...state.activeCharacter.memories];
        }
      })

      // Update health
      .addCase(updateCharacterHealth.fulfilled, (state, action) => {
        const { characterId, health } = action.payload;

        // Update active character
        if (state.activeCharacter && state.activeCharacter.id === characterId) {
          state.activeCharacter.health = health;
        }

        // Update in list
        const characterIndex = state.characters.findIndex(char => char.id === characterId);
        if (characterIndex !== -1) {
          state.characters[characterIndex].health = health;
        }
      })

      // Update resources
      .addCase(updateCharacterResources.fulfilled, (state, action) => {
        const { characterId, resources } = action.payload;

        // Update active character
        if (state.activeCharacter && state.activeCharacter.id === characterId) {
          state.activeCharacter.resources = resources;
        }

        // Update in list
        const characterIndex = state.characters.findIndex(char => char.id === characterId);
        if (characterIndex !== -1) {
          state.characters[characterIndex].resources = resources;
        }
      })

      // Upload portrait
      .addCase(uploadCharacterPortrait.fulfilled, (state, action) => {
        const { characterId, portrait } = action.payload;

        // Update active character
        if (state.activeCharacter && state.activeCharacter.id === characterId) {
          state.activeCharacter.portrait = portrait;
        }

        // Update in list
        const characterIndex = state.characters.findIndex(char => char.id === characterId);
        if (characterIndex !== -1) {
          state.characters[characterIndex].portrait = portrait;
        }
      });
  },
});

export const {
  clearError,
  setActiveCharacter,
  updateLocalCharacter,
  setFilters,
  clearFilters,
  addLocalMemory,
  updateLocalMemory,
  deleteLocalMemory,
} = characterSlice.actions;

export default characterSlice.reducer;