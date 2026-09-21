// Accessibility utility functions

/**
 * Generate a unique ID for accessibility purposes
 */
export const generateId = (prefix: string = 'id'): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Create a keyboard navigation handler
 */
export const createKeyboardHandler = (
  onEnter: () => void,
  onSpace?: () => void,
  onEscape?: () => void,
  onArrow?: (direction: 'up' | 'down' | 'left' | 'right') => void
) => {
  return (event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'Enter':
        event.preventDefault();
        onEnter();
        break;
      case ' ':
        if (onSpace) {
          event.preventDefault();
          onSpace();
        }
        break;
      case 'Escape':
        if (onEscape) {
          event.preventDefault();
          onEscape();
        }
        break;
      case 'ArrowUp':
        if (onArrow) {
          event.preventDefault();
          onArrow('up');
        }
        break;
      case 'ArrowDown':
        if (onArrow) {
          event.preventDefault();
          onArrow('down');
        }
        break;
      case 'ArrowLeft':
        if (onArrow) {
          event.preventDefault();
          onArrow('left');
        }
        break;
      case 'ArrowRight':
        if (onArrow) {
          event.preventDefault();
          onArrow('right');
        }
        break;
    }
  };
};

/**
 * Trap focus within a container
 */
export const createFocusTrap = (container: HTMLElement) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ) as NodeListOf<HTMLElement>;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    }
  };

  container.addEventListener('keydown', handleTabKey);

  // Focus the first element
  firstElement?.focus();

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleTabKey);
  };
};

/**
 * Announce messages to screen readers
 */
export const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Check if an element is visible in the viewport
 */
export const isElementVisible = (element: HTMLElement): boolean => {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
};

/**
 * Scroll an element into view smoothly
 */
export const scrollIntoView = (element: HTMLElement, options: ScrollIntoViewOptions = {}) => {
  const defaultOptions: ScrollIntoViewOptions = {
    behavior: 'smooth',
    block: 'start',
    inline: 'nearest',
    ...options
  };

  element.scrollIntoView(defaultOptions);
};

/**
 * Create a skip link for accessibility
 */
export const createSkipLink = (targetId: string, text: string = 'Skip to main content') => {
  const skipLink = document.createElement('a');
  skipLink.href = `#${targetId}`;
  skipLink.textContent = text;
  skipLink.className = 'skip-link';
  skipLink.style.cssText = `
    position: absolute;
    top: -40px;
    left: 6px;
    background: #007bff;
    color: white;
    padding: 8px;
    text-decoration: none;
    border-radius: 4px;
    z-index: 1000;
    transition: top 0.2s ease;
  `;

  skipLink.addEventListener('focus', () => {
    skipLink.style.top = '6px';
  });

  skipLink.addEventListener('blur', () => {
    skipLink.style.top = '-40px';
  });

  return skipLink;
};

/**
 * Add ARIA attributes to interactive elements
 */
export const addAriaAttributes = (
  element: HTMLElement,
  attributes: Record<string, string>
) => {
  Object.entries(attributes).forEach(([key, value]) => {
    element.setAttribute(key, value);
  });
};

/**
 * Create a live region for dynamic content
 */
export const createLiveRegion = (type: 'polite' | 'assertive' = 'polite') => {
  const liveRegion = document.createElement('div');
  liveRegion.setAttribute('aria-live', type);
  liveRegion.setAttribute('aria-atomic', 'true');
  liveRegion.className = 'sr-only';
  liveRegion.id = generateId('live-region');

  document.body.appendChild(liveRegion);

  return {
    announce: (message: string) => {
      liveRegion.textContent = message;
      // Clear after announcement
      setTimeout(() => {
        liveRegion.textContent = '';
      }, 1000);
    },
    remove: () => {
      document.body.removeChild(liveRegion);
    }
  };
};

/**
 * Check if user prefers reduced motion
 */
export const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Check if user prefers high contrast
 */
export const prefersHighContrast = (): boolean => {
  return window.matchMedia('(prefers-contrast: high)').matches;
};

/**
 * Get appropriate animation duration based on user preferences
 */
export const getAnimationDuration = (defaultDuration: number): number => {
  return prefersReducedMotion() ? 0 : defaultDuration;
};

/**
 * Create a responsive table for screen readers
 */
export const createAccessibleTable = (data: any[][], headers: string[]) => {
  const table = document.createElement('table');
  table.setAttribute('role', 'table');

  // Create header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');

  headers.forEach((header, index) => {
    const th = document.createElement('th');
    th.textContent = header;
    th.setAttribute('scope', 'col');
    th.setAttribute('aria-sort', 'none');
    headerRow.appendChild(th);
  });

  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Create body
  const tbody = document.createElement('tbody');

  data.forEach((row, rowIndex) => {
    const tr = document.createElement('tr');
    tr.setAttribute('role', 'row');

    row.forEach((cell, cellIndex) => {
      const td = document.createElement('td');
      td.textContent = cell;
      td.setAttribute('aria-label', `${headers[cellIndex]}: ${cell}`);
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });

  table.appendChild(tbody);

  return table;
};

/**
 * Add keyboard navigation to a custom component
 */
export const addKeyboardNavigation = (
  container: HTMLElement,
  items: HTMLElement[],
  onSelect?: (index: number) => void,
  orientation: 'horizontal' | 'vertical' = 'vertical'
) => {
  let currentIndex = 0;

  const handleKeyDown = (e: KeyboardEvent) => {
    let newIndex = currentIndex;

    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault();
        newIndex = (currentIndex + 1) % items.length;
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        e.preventDefault();
        newIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1;
        break;
      case 'Home':
        e.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        newIndex = items.length - 1;
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (onSelect) {
          onSelect(currentIndex);
        }
        return;
      default:
        return;
    }

    // Update current index and focus
    currentIndex = newIndex;
    items[currentIndex]?.focus();
  };

  container.addEventListener('keydown', handleKeyDown);

  // Set initial focus
  items[0]?.focus();

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
};

/**
 * Validate color contrast for accessibility
 */
export const validateColorContrast = (foreground: string, background: string): boolean => {
  // Simple contrast check - in a real implementation, you'd use a proper contrast ratio calculation
  const getLuminance = (color: string): number => {
    // Convert hex to RGB
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16) / 255;
    const g = parseInt(hex.substr(2, 2), 16) / 255;
    const b = parseInt(hex.substr(4, 2), 16) / 255;

    // Calculate luminance
    const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
    return luminance;
  };

  const fgLuminance = getLuminance(foreground);
  const bgLuminance = getLuminance(background);

  // Simple contrast check (would need proper WCAG calculation in production)
  return Math.abs(fgLuminance - bgLuminance) > 0.5;
};