import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';
import { createTheme } from '@rneui/themed';

// DMlogn8n brand colors
export const colors = {
  primary: '#D4A574', // Gold/brass color for D&D theme
  secondary: '#8B4513', // Brown
  accent: '#FF6B35', // Orange accent
  background: '#2C1810', // Dark brown background
  surface: '#3D2817', // Slightly lighter brown
  text: '#F5E6D3', // Light cream text
  textSecondary: '#C4A57B', // Muted gold
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#F44336',
  info: '#2196F3',
  health: '#E53935', // Red for health
  mana: '#1E88E5', // Blue for mana
  stamina: '#43A047', // Green for stamina
  dice: {
    d4: '#FF6B35',
    d6: '#4CAF50',
    d8: '#2196F3',
    d10: '#9C27B0',
    d12: '#FF9800',
    d20: '#F44336',
    d100: '#607D8B',
  },
  class: {
    fighter: '#795548',
    wizard: '#9C27B0',
    rogue: '#424242',
    cleric: '#FDD835',
    druid: '#4CAF50',
    ranger: '#795548',
    barbarian: '#D32F2F',
    monk: '#FF9800',
    paladin: '#FDD835',
    bard: '#E91E63',
    sorcerer: '#9C27B0',
    warlock: '#9C27B0',
  },
};

export const paperTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: colors.primary,
    secondary: colors.secondary,
    background: colors.background,
    surface: colors.surface,
    onPrimary: colors.background,
    onSecondary: colors.text,
    onBackground: colors.text,
    onSurface: colors.text,
    text: colors.text,
    textSecondary: colors.textSecondary,
    error: colors.error,
    success: colors.success,
    warning: colors.warning,
    info: colors.info,
  },
  roundness: 12,
  fonts: {
    ...MD3DarkTheme.fonts,
    headlineLarge: {
      ...MD3DarkTheme.fonts.headlineLarge,
      fontFamily: 'Cinzel-Regular',
    },
    headlineMedium: {
      ...MD3DarkTheme.fonts.headlineMedium,
      fontFamily: 'Cinzel-Regular',
    },
  },
};

export const rneuiTheme = createTheme({
  lightColors: {
    primary: colors.primary,
    secondary: colors.secondary,
    background: colors.background,
    surface: colors.surface,
    grey0: colors.text,
    grey1: colors.textSecondary,
    grey2: '#B8956A',
    grey3: '#A68B5B',
    grey4: '#8B6F47',
    grey5: '#705638',
    error: colors.error,
    warning: colors.warning,
    success: colors.success,
    info: colors.info,
  },
  darkColors: {
    primary: colors.primary,
    secondary: colors.secondary,
    background: colors.background,
    surface: colors.surface,
    grey0: colors.text,
    grey1: colors.textSecondary,
    grey2: '#B8956A',
    grey3: '#A68B5B',
    grey4: '#8B6F47',
    grey5: '#705638',
    error: colors.error,
    warning: colors.warning,
    success: colors.success,
    info: colors.info,
  },
  mode: 'dark',
  components: {
    Button: {
      titleStyle: {
        fontFamily: 'Cinzel-Regular',
        fontWeight: '600',
      },
      buttonStyle: {
        borderRadius: 25,
        paddingHorizontal: 20,
      },
    },
    Input: {
      inputStyle: {
        fontFamily: 'Lato-Regular',
      },
      labelStyle: {
        fontFamily: 'Lato-Bold',
      },
    },
    Text: {
      style: {
        fontFamily: 'Lato-Regular',
      },
      h1Style: {
        fontFamily: 'Cinzel-Regular',
        fontWeight: '700',
      },
      h2Style: {
        fontFamily: 'Cinzel-Regular',
        fontWeight: '600',
      },
      h3Style: {
        fontFamily: 'Cinzel-Regular',
        fontWeight: '500',
      },
      h4Style: {
        fontFamily: 'Lato-Bold',
      },
    },
    Card: {
      containerStyle: {
        backgroundColor: colors.surface,
        borderRadius: 15,
        borderWidth: 1,
        borderColor: colors.primary + '30',
      },
    },
    Avatar: {
      containerStyle: {
        borderWidth: 2,
        borderColor: colors.primary,
      },
    },
    Icon: {
      color: colors.primary,
    },
  },
});

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const typography = {
  h1: {
    fontSize: 32,
    fontFamily: 'Cinzel-Regular',
    fontWeight: '700',
    lineHeight: 40,
  },
  h2: {
    fontSize: 28,
    fontFamily: 'Cinzel-Regular',
    fontWeight: '600',
    lineHeight: 36,
  },
  h3: {
    fontSize: 24,
    fontFamily: 'Cinzel-Regular',
    fontWeight: '500',
    lineHeight: 32,
  },
  h4: {
    fontSize: 20,
    fontFamily: 'Lato-Bold',
    fontWeight: '600',
    lineHeight: 28,
  },
  body1: {
    fontSize: 16,
    fontFamily: 'Lato-Regular',
    lineHeight: 24,
  },
  body2: {
    fontSize: 14,
    fontFamily: 'Lato-Regular',
    lineHeight: 20,
  },
  caption: {
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    lineHeight: 16,
  },
  overline: {
    fontSize: 10,
    fontFamily: 'Lato-Regular',
    lineHeight: 14,
    textTransform: 'uppercase',
  },
};

export default { colors, paperTheme, rneuiTheme, spacing, typography };