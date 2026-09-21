import { useState, useEffect, useRef } from 'react';
import { InteractionManager } from 'react-native';

interface UseLazyLoadOptions {
  threshold?: number;
  rootMargin?: string;
  triggerOnce?: boolean;
  delay?: number;
}

export const useLazyLoad = (
  options: UseLazyLoadOptions = {}
) => {
  const {
    threshold = 0.1,
    rootMargin = '0px',
    triggerOnce = true,
    delay = 0,
  } = options;

  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const elementRef = useRef<any>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting) {
          if (delay > 0) {
            timeoutRef.current = setTimeout(() => {
              setIsIntersecting(true);
              setHasIntersected(true);
            }, delay);
          } else {
            setIsIntersecting(true);
            setHasIntersected(true);
          }

          if (triggerOnce) {
            observer.unobserve(element);
          }
        } else if (!triggerOnce) {
          setIsIntersecting(false);
        }
      },
      {
        threshold,
        rootMargin,
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [threshold, rootMargin, triggerOnce, delay]);

  return {
    ref: elementRef,
    isIntersecting: triggerOnce ? hasIntersected : isIntersecting,
    hasIntersected,
  };
};

// Hook for lazy loading heavy components
export const useLazyComponent = <T extends React.ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options: UseLazyLoadOptions = {}
) => {
  const [Component, setComponent] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { ref, isIntersecting } = useLazyLoad(options);

  useEffect(() => {
    if (!isIntersecting) return;

    const loadComponent = async () => {
      try {
        setIsLoading(true);
        const module = await importFunc();
        setComponent(() => module.default);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load component'));
      } finally {
        setIsLoading(false);
      }
    };

    // Run after interactions to avoid blocking UI
    InteractionManager.runAfterInteractions(loadComponent);
  }, [isIntersecting, importFunc]);

  return {
    ref,
    Component,
    isLoading,
    error,
  };
};

// Hook for lazy loading data
export const useLazyData = <T>(
  fetchData: () => Promise<T>,
  dependencies: any[] = [],
  options: UseLazyLoadOptions = {}
) => {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { ref, isIntersecting } = useLazyLoad(options);

  useEffect(() => {
    if (!isIntersecting) return;

    const loadData = async () => {
      try {
        setIsLoading(true);
        const result = await fetchData();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load data'));
      } finally {
        setIsLoading(false);
      }
    };

    InteractionManager.runAfterInteractions(loadData);
  }, [isIntersecting, fetchData, ...dependencies]);

  return {
    ref,
    data,
    isLoading,
    error,
    refetch: () => {
      if (isIntersecting) {
        fetchData().then(setData).catch(setError);
      }
    },
  };
};

// Hook for progressive image loading
export const useProgressiveImage = (
  lowQualitySrc: string,
  highQualitySrc: string
) => {
  const [src, setSrc] = useState(lowQualitySrc);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const img = new Image();
    img.src = highQualitySrc;
    img.onload = () => {
      setSrc(highQualitySrc);
      setIsLoading(false);
    };
  }, [highQualitySrc]);

  return { src, isLoading };
};