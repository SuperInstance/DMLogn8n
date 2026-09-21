import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, ActivityIndicator } from 'react-native-elements';
import { useTheme } from '@react-navigation/native';
import Animated, { FadeIn, BounceIn } from 'react-native-reanimated';

const LoadingScreen: React.FC = () => {
  const theme = useTheme();

  return (
    <Animated.View
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      entering={FadeIn.duration(500)}
    >
      <View style={styles.content}>
        <Animated.View
          style={styles.logoContainer}
          entering={BounceIn.duration(1000).delay(200)}
        >
          <Text h1 style={[styles.logo, { color: theme.colors.primary }]}>
            DMLogn8n
          </Text>
          <Text h4 style={[styles.tagline, { color: theme.colors.textSecondary }]}>
            Mobile Adventure Awaits
          </Text>
        </Animated.View>

        <Animated.View
          style={styles.loadingContainer}
          entering={FadeIn.duration(500).delay(600)}
        >
          <ActivityIndicator
            size="large"
            color={theme.colors.primary}
            style={styles.indicator}
          />
          <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
            Loading your adventure...
          </Text>
        </Animated.View>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 64,
  },
  logo: {
    fontSize: 48,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  tagline: {
    textAlign: 'center',
    fontSize: 16,
    fontWeight: '500',
  },
  loadingContainer: {
    alignItems: 'center',
    marginTop: 32,
  },
  indicator: {
    marginBottom: 16,
  },
  loadingText: {
    fontSize: 16,
    textAlign: 'center',
  },
});

export default LoadingScreen;