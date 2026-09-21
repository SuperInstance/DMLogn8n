export const theme = {
  colors: {
    // Primary Colors
    primary: '#6200EE',
    primaryVariant: '#3700B3',
    secondary: '#03DAC6',
    secondaryVariant: '#018786',

    // Surface and Background
    background: '#121212',
    surface: '#1E1E1E',
    surfaceVariant: '#2C2C2C',

    // Text Colors
    text: '#FFFFFF',
    textPrimary: '#FFFFFF',
    textSecondary: '#B3B3B3',
    textDisabled: '#666666',

    // Status Colors
    success: '#4CAF50',
    warning: '#FF9800',
    error: '#F44336',
    info: '#2196F3',

    // Game Specific Colors
    health: '#F44336',
    mana: '#2196F3',
    experience: '#FFC107',
    gold: '#FFD700',

    // Rarity Colors
    common: '#9E9E9E',
    uncommon: '#4CAF50',
    rare: '#2196F3',
    epic: '#9C27B0',
    legendary: '#FF9800',

    // UI Colors
    border: '#333333',
    divider: '#2C2C2C',
    overlay: 'rgba(0, 0, 0, 0.5)',
    shadow: 'rgba(0, 0, 0, 0.2)',

    // Input Colors
    inputBackground: '#2C2C2C',
    inputBorder: '#444444',
    inputPlaceholder: '#666666',

    // Navigation Colors
    tabBar: '#1E1E1E',
    tabBarActive: '#6200EE',
    tabBarInactive: '#666666',

    // Chat Colors
    messageOwn: '#6200EE',
    messageOther: '#2C2C2C',
    systemMessage: '#FF9800',
  },

  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
    xxxl: 64,
  },

  typography: {
    // Font Families
    fontFamily: {
      regular: 'System',
      medium: 'System',
      bold: 'System',
      light: 'System',
    },

    // Font Sizes
    fontSize: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
      huge: 48,
    },

    // Font Weights
    fontWeight: {
      light: '300',
      regular: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
    },

    // Line Heights
    lineHeight: {
      xs: 16,
      sm: 20,
      base: 24,
      lg: 28,
      xl: 32,
    },
  },

  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    round: 9999,
  },

  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 2,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 4,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 8,
    },
    xl: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.35,
      shadowRadius: 16,
      elevation: 12,
    },
  },

  animations: {
    duration: {
      fast: 200,
      normal: 300,
      slow: 500,
    },
    easing: {
      easeIn: 'ease-in',
      easeOut: 'ease-out',
      easeInOut: 'ease-in-out',
    },
  },

  breakpoints: {
    small: 320,
    medium: 768,
    large: 1024,
  },

  components: {
    Button: {
      titleStyle: {
        fontFamily: 'System',
        fontWeight: '600',
        fontSize: 16,
      },
      buttonStyle: {
        borderRadius: 8,
        paddingHorizontal: 24,
        paddingVertical: 12,
      },
      raised: true,
    },

    Card: {
      containerStyle: {
        borderRadius: 12,
        backgroundColor: '#1E1E1E',
        marginBottom: 16,
      },
      wrapperStyle: {
        padding: 16,
      },
    },

    Input: {
      inputStyle: {
        color: '#FFFFFF',
        fontSize: 16,
      },
      inputContainerStyle: {
        backgroundColor: '#2C2C2C',
        borderBottomWidth: 0,
        borderRadius: 8,
        paddingHorizontal: 16,
        paddingVertical: 12,
      },
      placeholderTextColor: '#666666',
    },

    Avatar: {
      size: 'medium',
      rounded: true,
      titleStyle: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: '600',
      },
    },

    ListItem: {
      containerStyle: {
        backgroundColor: 'transparent',
        borderBottomWidth: 0,
        paddingVertical: 8,
      },
      titleStyle: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '500',
      },
      subtitleStyle: {
        color: '#B3B3B3',
        fontSize: 14,
      },
    },

    Icon: {
      size: 24,
      color: '#FFFFFF',
    },

    Text: {
      style: {
        color: '#FFFFFF',
        fontSize: 16,
      },
    },

    Header: {
      backgroundColor: '#1E1E1E',
      barStyle: 'light-content',
      containerStyle: {
        borderBottomWidth: 1,
        borderBottomColor: '#333333',
      },
      titleStyle: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: '600',
      },
    },
  },
};

export const lightTheme = {
  ...theme,
  colors: {
    ...theme.colors,
    background: '#FFFFFF',
    surface: '#F5F5F5',
    surfaceVariant: '#EEEEEE',
    text: '#000000',
    textPrimary: '#000000',
    textSecondary: '#666666',
    textDisabled: '#999999',
    border: '#E0E0E0',
    divider: '#F0F0F0',
    overlay: 'rgba(0, 0, 0, 0.3)',
    shadow: 'rgba(0, 0, 0, 0.1)',
    inputBackground: '#FFFFFF',
    inputBorder: '#E0E0E0',
    inputPlaceholder: '#999999',
    tabBar: '#FFFFFF',
    messageOwn: '#6200EE',
    messageOther: '#F5F5F5',
  },
};

export default theme;