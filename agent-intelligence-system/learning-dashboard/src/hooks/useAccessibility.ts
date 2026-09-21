import { useEffect, useState } from 'react';

interface AccessibilitySettings {
  reducedMotion: boolean;
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  screenReader: boolean;
}

export const useAccessibility = () => {
  const [settings, setSettings] = useState<AccessibilitySettings>({
    reducedMotion: false,
    highContrast: false,
    fontSize: 'medium',
    screenReader: false
  });

  useEffect(() => {
    // Check for reduced motion preference
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setSettings(prev => ({ ...prev, reducedMotion: motionQuery.matches }));

    const handleMotionChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({ ...prev, reducedMotion: e.matches }));
    };

    motionQuery.addEventListener('change', handleMotionChange);

    // Check for high contrast preference
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    setSettings(prev => ({ ...prev, highContrast: contrastQuery.matches }));

    const handleContrastChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({ ...prev, highContrast: e.matches }));
    };

    contrastQuery.addEventListener('change', handleContrastChange);

    // Check for screen reader
    const screenReaderCheck = () => {
      const hasScreenReader = window.speechSynthesis !== undefined ||
                              window.navigator.userAgent.includes('NVDA') ||
                              window.navigator.userAgent.includes('JAWS');
      setSettings(prev => ({ ...prev, screenReader: hasScreenReader }));
    };

    screenReaderCheck();

    // Load saved font size preference
    const savedFontSize = localStorage.getItem('accessibility-fontSize') as AccessibilitySettings['fontSize'];
    if (savedFontSize && ['small', 'medium', 'large'].includes(savedFontSize)) {
      setSettings(prev => ({ ...prev, fontSize: savedFontSize }));
    }

    return () => {
      motionQuery.removeEventListener('change', handleMotionChange);
      contrastQuery.removeEventListener('change', handleContrastChange);
    };
  }, []);

  const updateFontSize = (size: AccessibilitySettings['fontSize']) => {
    setSettings(prev => ({ ...prev, fontSize: size }));
    localStorage.setItem('accessibility-fontSize', size);

    // Apply font size to root element
    const root = document.documentElement;
    switch (size) {
      case 'small':
        root.style.fontSize = '14px';
        break;
      case 'medium':
        root.style.fontSize = '16px';
        break;
      case 'large':
        root.style.fontSize = '18px';
        break;
    }
  };

  const announceToScreenReader = (message: string) => {
    if (!settings.screenReader) return;

    // Create or find the live region
    let liveRegion = document.getElementById('screen-reader-announcements');
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'screen-reader-announcements';
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only';
      document.body.appendChild(liveRegion);
    }

    // Update the announcement
    liveRegion.textContent = message;

    // Clear after announcement
    setTimeout(() => {
      if (liveRegion) {
        liveRegion.textContent = '';
      }
    }, 1000);
  };

  const getAriaLabel = (label: string, context?: string) => {
    if (settings.screenReader && context) {
      return `${label}, ${context}`;
    }
    return label;
  };

  const getAnimationClass = (baseClass: string) => {
    if (settings.reducedMotion) {
      return `${baseClass} no-animation`;
    }
    return baseClass;
  };

  const getContrastClass = (baseClass: string) => {
    if (settings.highContrast) {
      return `${baseClass} high-contrast`;
    }
    return baseClass;
  };

  // Apply accessibility settings to document
  useEffect(() => {
    const root = document.documentElement;

    if (settings.reducedMotion) {
      root.classList.add('reduce-motion');
    } else {
      root.classList.remove('reduce-motion');
    }

    if (settings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Apply font size
    updateFontSize(settings.fontSize);
  }, [settings.reducedMotion, settings.highContrast, settings.fontSize]);

  return {
    settings,
    updateFontSize,
    announceToScreenReader,
    getAriaLabel,
    getAnimationClass,
    getContrastClass
  };
};