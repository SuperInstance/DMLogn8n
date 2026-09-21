import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Combat, CombatParticipant } from '../../types';
import { combatService } from '../../services/combatService';

interface CombatState {
  combats: Combat[];
  activeCombat: Combat | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: CombatState = {
  combats: [],
  activeCombat: null,
  isLoading: false,
  error: null,
};

export const fetchActiveCombat = createAsyncThunk(
  'combat/fetchActive',
  async (campaignId: string, { rejectWithValue }) => {
    try {
      const combat = await combatService.getActiveCombat(campaignId);
      return combat;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch active combat');
    }
  },
);

export const startCombat = createAsyncThunk(
  'combat/start',
  async ({ campaignId, participants }: { campaignId: string; participants: CombatParticipant[] }, { rejectWithValue }) => {
    try {
      const combat = await combatService.startCombat(campaignId, participants);
      return combat;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to start combat');
    }
  },
);

export const endCombat = createAsyncThunk(
  'combat/end',
  async (combatId: string, { rejectWithValue }) => {
    try {
      await combatService.endCombat(combatId);
      return combatId;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to end combat');
    }
  },
);

export const nextTurn = createAsyncThunk(
  'combat/nextTurn',
  async (combatId: string, { rejectWithValue }) => {
    try {
      const combat = await combatService.nextTurn(combatId);
      return combat;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to advance turn');
    }
  },
);

export const updateParticipant = createAsyncThunk(
  'combat/updateParticipant',
  async ({ combatId, participantId, data }: { combatId: string; participantId: string; data: Partial<CombatParticipant> }, { rejectWithValue }) => {
    try {
      const combat = await combatService.updateParticipant(combatId, participantId, data);
      return combat;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update participant');
    }
  },
);

const combatSlice = createSlice({
  name: 'combat',
  initialState,
  reducers: {
    setActiveCombat: (state, action: PayloadAction<Combat | null>) => {
      state.activeCombat = action.payload;
    },
    updateParticipantHealth: (state, action: PayloadAction<{ participantId: string; hp: number }>) => {
      if (state.activeCombat) {
        const participant = state.activeCombat.participants.find(p => p.id === action.payload.participantId);
        if (participant) {
          participant.hp = Math.max(0, Math.min(action.payload.hp, participant.maxHp));
        }
      }
    },
    addCondition: (state, action: PayloadAction<{ participantId: string; condition: string }>) => {
      if (state.activeCombat) {
        const participant = state.activeCombat.participants.find(p => p.id === action.payload.participantId);
        if (participant && !participant.conditions.includes(action.payload.condition)) {
          participant.conditions.push(action.payload.condition);
        }
      }
    },
    removeCondition: (state, action: PayloadAction<{ participantId: string; condition: string }>) => {
      if (state.activeCombat) {
        const participant = state.activeCombat.participants.find(p => p.id === action.payload.participantId);
        if (participant) {
          participant.conditions = participant.conditions.filter(c => c !== action.payload.condition);
        }
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Active Combat
      .addCase(fetchActiveCombat.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchActiveCombat.fulfilled, (state, action) => {
        state.isLoading = false;
        state.activeCombat = action.payload;
        state.error = null;
      })
      .addCase(fetchActiveCombat.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Start Combat
      .addCase(startCombat.fulfilled, (state, action) => {
        state.activeCombat = action.payload;
        const index = state.combats.findIndex(c => c.id === action.payload.id);
        if (index === -1) {
          state.combats.push(action.payload);
        } else {
          state.combats[index] = action.payload;
        }
      })
      // End Combat
      .addCase(endCombat.fulfilled, (state, action) => {
        state.combats = state.combats.filter(c => c.id !== action.payload);
        if (state.activeCombat?.id === action.payload) {
          state.activeCombat = null;
        }
      })
      // Next Turn
      .addCase(nextTurn.fulfilled, (state, action) => {
        if (state.activeCombat?.id === action.payload.id) {
          state.activeCombat = action.payload;
        }
        const index = state.combats.findIndex(c => c.id === action.payload.id);
        if (index !== -1) {
          state.combats[index] = action.payload;
        }
      })
      // Update Participant
      .addCase(updateParticipant.fulfilled, (state, action) => {
        if (state.activeCombat?.id === action.payload.id) {
          state.activeCombat = action.payload;
        }
        const index = state.combats.findIndex(c => c.id === action.payload.id);
        if (index !== -1) {
          state.combats[index] = action.payload;
        }
      });
  },
});

export const {
  setActiveCombat,
  updateParticipantHealth,
  addCondition,
  removeCondition,
  clearError,
} = combatSlice.actions;

export default combatSlice.reducer;