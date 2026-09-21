import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Campaign } from '../../types';
import { campaignService } from '../../services/campaignService';

interface CampaignState {
  campaigns: Campaign[];
  activeCampaign: Campaign | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: CampaignState = {
  campaigns: [],
  activeCampaign: null,
  isLoading: false,
  error: null,
};

export const fetchCampaigns = createAsyncThunk(
  'campaigns/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const campaigns = await campaignService.getAllCampaigns();
      return campaigns;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch campaigns');
    }
  },
);

export const fetchCampaign = createAsyncThunk(
  'campaigns/fetchOne',
  async (campaignId: string, { rejectWithValue }) => {
    try {
      const campaign = await campaignService.getCampaign(campaignId);
      return campaign;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch campaign');
    }
  },
);

export const joinCampaign = createAsyncThunk(
  'campaigns/join',
  async (campaignId: string, { rejectWithValue }) => {
    try {
      const campaign = await campaignService.joinCampaign(campaignId);
      return campaign;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to join campaign');
    }
  },
);

export const leaveCampaign = createAsyncThunk(
  'campaigns/leave',
  async (campaignId: string, { rejectWithValue }) => {
    try {
      await campaignService.leaveCampaign(campaignId);
      return campaignId;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to leave campaign');
    }
  },
);

const campaignSlice = createSlice({
  name: 'campaigns',
  initialState,
  reducers: {
    setActiveCampaign: (state, action: PayloadAction<Campaign | null>) => {
      state.activeCampaign = action.payload;
    },
    updateCampaignStatus: (state, action: PayloadAction<{ campaignId: string; isActive: boolean }>) => {
      const campaign = state.campaigns.find(c => c.id === action.payload.campaignId);
      if (campaign) {
        campaign.isActive = action.payload.isActive;
      }
      if (state.activeCampaign?.id === action.payload.campaignId) {
        state.activeCampaign.isActive = action.payload.isActive;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Campaigns
      .addCase(fetchCampaigns.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCampaigns.fulfilled, (state, action) => {
        state.isLoading = false;
        state.campaigns = action.payload;
        state.error = null;
      })
      .addCase(fetchCampaigns.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch Single Campaign
      .addCase(fetchCampaign.fulfilled, (state, action) => {
        const index = state.campaigns.findIndex(c => c.id === action.payload.id);
        if (index !== -1) {
          state.campaigns[index] = action.payload;
        } else {
          state.campaigns.push(action.payload);
        }
      })
      // Join Campaign
      .addCase(joinCampaign.fulfilled, (state, action) => {
        const index = state.campaigns.findIndex(c => c.id === action.payload.id);
        if (index === -1) {
          state.campaigns.push(action.payload);
        } else {
          state.campaigns[index] = action.payload;
        }
      })
      // Leave Campaign
      .addCase(leaveCampaign.fulfilled, (state, action) => {
        state.campaigns = state.campaigns.filter(c => c.id !== action.payload);
        if (state.activeCampaign?.id === action.payload) {
          state.activeCampaign = null;
        }
      });
  },
});

export const { setActiveCampaign, updateCampaignStatus, clearError } = campaignSlice.actions;
export default campaignSlice.reducer;