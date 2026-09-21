import React from 'react';
import {
  TouchableOpacity,
  StyleSheet,
  Animated,
  ViewStyle,
  TextStyle,
} from 'react-native';
import {
  Text,
  Icon,
  ActivityIndicator,
} from 'react-native-elements';
import { useTheme } from '@react-navigation/native';

interface ActionButtonProps {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'outline';
  size?: 'small' | 'medium' | 'large';
  icon?: string;
  iconType?: 'ionicon' | 'material' | 'material-community' | 'font-awesome';
  fullWidth?: boolean;
  rounded?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  animated?: boolean;
}

const ActionButton: React.FC<ActionButtonProps> = ({
  title,
  onPress,
  disabled = false,
  loading = false,
  variant = 'primary',
  size = 'medium',
  icon,
  iconType = 'ionicon',
  fullWidth = false,
  rounded = false,
  style,
  textStyle,
  animated = true,
}) => {
  const theme = useTheme();
  const scaleValue = React.useRef(new Animated.Value(1)).current;
  const opacityValue = React.useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    if (animated && !disabled && !loading) {
      Animated.parallel([
        Animated.spring(scaleValue, {
          toValue: 0.95,
          useNativeDriver: true,
        }),
        Animated.timing(opacityValue, {
          toValue: 0.8,
          duration: 100,
          useNativeDriver: true,
        }),
      ]).start();
    }
  };

  const handlePressOut = () => {
    if (animated && !disabled && !loading) {
      Animated.parallel([
        Animated.spring(scaleValue, {
          toValue: 1,
          useNativeDriver: true,
        }),
        Animated.timing(opacityValue, {
          toValue: 1,
          duration: 100,
          useNativeDriver: true,
        }),
      ]).start();
    }
  };

  const handlePress = () => {
    if (!disabled && !loading) {
      onPress();
    }
  };

  const getButtonStyle = () => {
    const baseStyle: ViewStyle[] = [styles.button];

    // Size styles
    switch (size) {
      case 'small':
        baseStyle.push(styles.smallButton);
        break;
      case 'medium':
        baseStyle.push(styles.mediumButton);
        break;
      case 'large':
        baseStyle.push(styles.largeButton);
        break;
    }

    // Variant styles
    switch (variant) {
      case 'primary':
        baseStyle.push({
          backgroundColor: theme.colors.primary,
        });
        break;
      case 'secondary':
        baseStyle.push({
          backgroundColor: theme.colors.secondary,
        });
        break;
      case 'danger':
        baseStyle.push({
          backgroundColor: theme.colors.error,
        });
        break;
      case 'success':
        baseStyle.push({
          backgroundColor: theme.colors.success,
        });
        break;
      case 'warning':
        baseStyle.push({
          backgroundColor: theme.colors.warning,
        });
        break;
      case 'outline':
        baseStyle.push([
          styles.outlineButton,
          {
            backgroundColor: 'transparent',
            borderColor: theme.colors.primary,
            borderWidth: 2,
          },
        ]);
        break;
    }

    // Shape styles
    if (rounded) {
      baseStyle.push(styles.roundedButton);
    } else {
      baseStyle.push(styles.squaredButton);
    }

    // Width styles
    if (fullWidth) {
      baseStyle.push(styles.fullWidthButton);
    }

    // State styles
    if (disabled) {
      baseStyle.push({
        opacity: 0.5,
      });
    }

    // Custom styles
    if (style) {
      baseStyle.push(style);
    }

    return baseStyle;
  };

  const getTextStyle = () => {
    const baseStyle: TextStyle[] = [styles.text];

    // Size styles
    switch (size) {
      case 'small':
        baseStyle.push(styles.smallText);
        break;
      case 'medium':
        baseStyle.push(styles.mediumText);
        break;
      case 'large':
        baseStyle.push(styles.largeText);
        break;
    }

    // Variant text styles
    switch (variant) {
      case 'outline':
        baseStyle.push({
          color: theme.colors.primary,
        });
        break;
      default:
        baseStyle.push({
          color: '#FFFFFF',
        });
    }

    // Custom text styles
    if (textStyle) {
      baseStyle.push(textStyle);
    }

    return baseStyle;
  };

  const getIconSize = () => {
    switch (size) {
      case 'small':
        return 16;
      case 'medium':
        return 20;
      case 'large':
        return 24;
      default:
        return 20;
    }
  };

  const getIconColor = () => {
    switch (variant) {
      case 'outline':
        return theme.colors.primary;
      default:
        return '#FFFFFF';
    }
  };

  const buttonStyle = getButtonStyle();
  const textStyle = getTextStyle();
  const iconSize = getIconSize();
  const iconColor = getIconColor();

  const ButtonContent = (
    <Animated.View
      style={[
        buttonStyle,
        {
          transform: [{ scale: scaleValue }],
          opacity: opacityValue,
        },
      ]}
    >
      {loading ? (
        <ActivityIndicator
          size={size === 'small' ? 'small' : 'large'}
          color={variant === 'outline' ? theme.colors.primary : '#FFFFFF'}
        />
      ) : (
        <>
          {icon && (
            <Icon
              name={icon}
              type={iconType}
              size={iconSize}
              color={iconColor}
              containerStyle={styles.iconContainer}
            />
          )}
          <Text style={textStyle}>{title}</Text>
        </>
      )}
    </Animated.View>
  );

  return (
    <TouchableOpacity
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={disabled || loading}
      activeOpacity={0.8}
      style={[styles.touchable, fullWidth && styles.fullWidthTouchable]}
    >
      {ButtonContent}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  touchable: {
    alignSelf: 'flex-start',
  },
  fullWidthTouchable: {
    alignSelf: 'stretch',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  smallButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    minHeight: 36,
  },
  mediumButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    minHeight: 48,
  },
  largeButton: {
    paddingHorizontal: 32,
    paddingVertical: 16,
    minHeight: 56,
  },
  outlineButton: {
    elevation: 0,
    shadowOpacity: 0,
  },
  roundedButton: {
    borderRadius: 9999,
  },
  squaredButton: {
    borderRadius: 8,
  },
  fullWidthButton: {
    alignSelf: 'stretch',
  },
  text: {
    fontWeight: '600',
    textAlign: 'center',
  },
  smallText: {
    fontSize: 14,
  },
  mediumText: {
    fontSize: 16,
  },
  largeText: {
    fontSize: 18,
  },
  iconContainer: {
    marginRight: 8,
  },
});

export default ActionButton;