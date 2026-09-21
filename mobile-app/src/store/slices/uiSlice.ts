import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  currentRoute: string;
  previousRoute?: string;
  params?: any;
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  toast: {
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    visible: boolean;
  } | null;
  modal: {
    type: string;
    visible: boolean;
    data?: any;
  } | null;
  drawer: {
    isOpen: boolean;
  };
  tabBar: {
    visible: boolean;
  };
  keyboard: {
    isVisible: boolean;
    height: number;
  };
}

const initialState: UIState = {
  currentRoute: 'Auth',
  isLoading: false,
  isRefreshing: false,
  error: null,
  toast: null,
  modal: null,
  drawer: {
    isOpen: false,
  },
  tabBar: {
    visible: true,
  },
  keyboard: {
    isVisible: false,
    height: 0,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setCurrentRoute: (state, action: PayloadAction<{ route: string; params?: any }>) => {
      state.previousRoute = state.currentRoute;
      state.currentRoute = action.payload.route;
      state.params = action.payload.params;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setRefreshing: (state, action: PayloadAction<boolean>) => {
      state.isRefreshing = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    showToast: (state, action: PayloadAction<{ message: string; type?: 'success' | 'error' | 'warning' | 'info' }>) => {
      state.toast = {
        message: action.payload.message,
        type: action.payload.type || 'info',
        visible: true,
      };
    },
    hideToast: (state) => {
      if (state.toast) {
        state.toast.visible = false;
      }
    },
    clearToast: (state) => {
      state.toast = null;
    },
    showModal: (state, action: PayloadAction<{ type: string; data?: any }>) => {
      state.modal = {
        type: action.payload.type,
        visible: true,
        data: action.payload.data,
      };
    },
    hideModal: (state) => {
      if (state.modal) {
        state.modal.visible = false;
      }
    },
    clearModal: (state) => {
      state.modal = null;
    },
    openDrawer: (state) => {
      state.drawer.isOpen = true;
    },
    closeDrawer: (state) => {
      state.drawer.isOpen = false;
    },
    setTabBarVisible: (state, action: PayloadAction<boolean>) => {
      state.tabBar.visible = action.payload;
    },
    setKeyboardVisible: (state, action: PayloadAction<{ isVisible: boolean; height: number }>) => {
      state.keyboard = {
        isVisible: action.payload.isVisible,
        height: action.payload.height,
      };
    },
  },
});

export const {
  setCurrentRoute,
  setLoading,
  setRefreshing,
  setError,
  showToast,
  hideToast,
  clearToast,
  showModal,
  hideModal,
  clearModal,
  openDrawer,
  closeDrawer,
  setTabBarVisible,
  setKeyboardVisible,
} = uiSlice.actions;

export default uiSlice.reducer;