import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Message } from '../../types';
import { messageService } from '../../services/messageService';

interface MessageState {
  messages: Message[];
  campaignMessages: { [campaignId: string]: Message[] };
  isLoading: boolean;
  error: string | null;
  isSending: boolean;
}

const initialState: MessageState = {
  messages: [],
  campaignMessages: {},
  isLoading: false,
  error: null,
  isSending: false,
};

export const fetchCampaignMessages = createAsyncThunk(
  'messages/fetchCampaign',
  async (campaignId: string, { rejectWithValue }) => {
    try {
      const messages = await messageService.getCampaignMessages(campaignId);
      return { campaignId, messages };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch messages');
    }
  },
);

export const sendMessage = createAsyncThunk(
  'messages/send',
  async (messageData: Omit<Message, 'id' | 'timestamp'>, { rejectWithValue }) => {
    try {
      const message = await messageService.sendMessage(messageData);
      return message;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to send message');
    }
  },
);

export const sendDiceRoll = createAsyncThunk(
  'messages/sendDiceRoll',
  async (diceData: {
    campaignId: string;
    dice: string;
    result: number;
    rolls: number[];
    modifier: number;
    total: number;
    reason: string;
    characterName?: string;
  }, { rejectWithValue }) => {
    try {
      const message = await messageService.sendDiceRoll(diceData);
      return message;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to send dice roll');
    }
  },
);

const messageSlice = createSlice({
  name: 'messages',
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<Message>) => {
      const message = action.payload;
      state.messages.push(message);

      if (message.campaignId) {
        if (!state.campaignMessages[message.campaignId]) {
          state.campaignMessages[message.campaignId] = [];
        }
        state.campaignMessages[message.campaignId].push(message);
      }
    },
    clearError: (state) => {
      state.error = null;
    },
    clearCampaignMessages: (state, action: PayloadAction<string>) => {
      const campaignId = action.payload;
      delete state.campaignMessages[campaignId];
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Campaign Messages
      .addCase(fetchCampaignMessages.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCampaignMessages.fulfilled, (state, action) => {
        state.isLoading = false;
        const { campaignId, messages } = action.payload;
        state.campaignMessages[campaignId] = messages;
        state.error = null;
      })
      .addCase(fetchCampaignMessages.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Send Message
      .addCase(sendMessage.pending, (state) => {
        state.isSending = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isSending = false;
        const message = action.payload;
        state.messages.push(message);

        if (message.campaignId) {
          if (!state.campaignMessages[message.campaignId]) {
            state.campaignMessages[message.campaignId] = [];
          }
          state.campaignMessages[message.campaignId].push(message);
        }
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isSending = false;
        state.error = action.payload as string;
      })
      // Send Dice Roll
      .addCase(sendDiceRoll.pending, (state) => {
        state.isSending = true;
        state.error = null;
      })
      .addCase(sendDiceRoll.fulfilled, (state, action) => {
        state.isSending = false;
        const message = action.payload;
        state.messages.push(message);

        if (message.campaignId) {
          if (!state.campaignMessages[message.campaignId]) {
            state.campaignMessages[message.campaignId] = [];
          }
          state.campaignMessages[message.campaignId].push(message);
        }
      })
      .addCase(sendDiceRoll.rejected, (state, action) => {
        state.isSending = false;
        state.error = action.payload as string;
      });
  },
});

export const { addMessage, clearError, clearCampaignMessages } = messageSlice.actions;
export default messageSlice.reducer;