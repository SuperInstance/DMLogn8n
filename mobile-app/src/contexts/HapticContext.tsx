import React, { createContext, useContext, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { hapticService } from '../services/hapticService';

interface HapticContextType {
  isEnabled: boolean;
  light: () => void;
  medium: () => void;
  heavy: () => void;
  success: () => void;
  warning: () => void;
  error: () => void;
  selection: () => void;
  notification: () => void;
  diceRoll: () => void;
  combat: () => void;
  achievement: () => void;
  criticalHit: () => void;
  levelUp: () => void;
}

const HapticContext = createContext<HapticContextType | undefined>(undefined);

interface HapticProviderProps {
  children: React.ReactNode;
}

export const HapticProvider: React.FC<HapticProviderProps> = ({ children }) => {
  const [isEnabled, setIsEnabled] = useState(true);
  const { settings } = useSelector((state: RootState) => state.settings);

  useEffect(() => {
    if (settings?.gameplay?.hapticFeedback !== undefined) {
      setIsEnabled(settings.gameplay.hapticFeedback);
    }
  }, [settings]);

  const light = () => {
    if (isEnabled) hapticService.light();
  };

  const medium = () => {
    if (isEnabled) hapticService.medium();
  };

  const heavy = () => {
    if (isEnabled) hapticService.heavy();
  };

  const success = () => {
    if (isEnabled) hapticService.success();
  };

  const warning = () => {
    if (isEnabled) hapticService.warning();
  };

  const error = () => {
    if (isEnabled) hapticService.error();
  };

  const selection = () => {
    if (isEnabled) hapticService.selection();
  };

  const notification = () => {
    if (isEnabled) hapticService.notification();
  };

  const diceRoll = () => {
    if (isEnabled) hapticService.diceRoll();
  };

  const combat = () => {
    if (isEnabled) hapticService.combat();
  };

  const achievement = () => {
    if (isEnabled) hapticService.achievement();
  };

  const criticalHit = () => {
    if (isEnabled) hapticService.criticalHit();
  };

  const levelUp = () => {
    if (isEnabled) hapticService.levelUp();
  };

  return (
    <HapticContext.Provider
      value={{
        isEnabled,
        light,
        medium,
        heavy,
        success,
        warning,
        error,
        selection,
        notification,
        diceRoll,
        combat,
        achievement,
        criticalHit,
        levelUp,
      }}
    >
      {children}
    </HapticContext.Provider>
  );
};

export const useHaptic = () => {
  const context = useContext(HapticContext);
  if (!context) {
    throw new Error('useHaptic must be used within a HapticProvider');
  }
  return context;
};