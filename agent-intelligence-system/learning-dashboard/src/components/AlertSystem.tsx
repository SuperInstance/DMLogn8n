import React, { useState, useEffect } from 'react';
import { AlertThreshold, AgentLearningMetrics } from '../types';

interface AlertSystemProps {
  thresholds: AlertThreshold[];
  metrics: AgentLearningMetrics;
  className?: string;
}

interface Alert {
  id: string;
  threshold: AlertThreshold;
  currentValue: number;
  timestamp: Date;
  acknowledged: boolean;
}

export const AlertSystem: React.FC<AlertSystemProps> = ({
  thresholds,
  metrics,
  className = ''
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  // Check for threshold violations
  useEffect(() => {
    const newAlerts: Alert[] = [];

    thresholds.forEach(threshold => {
      let currentValue = 0;

      // Extract current value based on metric path
      switch (threshold.metric) {
        case 'learningVelocity':
          currentValue = metrics.intelligenceMetrics.learningVelocity;
          break;
        case 'memoryUtilization':
          currentValue = metrics.memoryMetrics.memoryUtilization;
          break;
        case 'iqImprovement':
          currentValue = metrics.intelligenceMetrics.currentIQ - metrics.intelligenceMetrics.baselineIQ;
          break;
        case 'retentionRate':
          currentValue = metrics.intelligenceMetrics.retentionRate;
          break;
        case 'skillVelocity':
          currentValue = metrics.skillMetrics.skillVelocity;
          break;
        default:
          // Handle nested properties
          const pathParts = threshold.metric.split('.');
          let value: any = metrics;
          for (const part of pathParts) {
            value = value?.[part];
          }
          currentValue = typeof value === 'number' ? value : 0;
      }

      // Check if threshold is violated
      let isViolated = false;
      switch (threshold.condition) {
        case 'greater_than':
          isViolated = currentValue > threshold.value;
          break;
        case 'less_than':
          isViolated = currentValue < threshold.value;
          break;
        case 'equals':
          isViolated = Math.abs(currentValue - threshold.value) < 0.001;
          break;
      }

      if (isViolated) {
        const alertId = `${threshold.metric}-${threshold.condition}-${threshold.value}`;
        if (!dismissedAlerts.has(alertId)) {
          newAlerts.push({
            id: alertId,
            threshold,
            currentValue,
            timestamp: new Date(),
            acknowledged: false
          });
        }
      }
    });

    setAlerts(prev => {
      // Merge new alerts with existing ones, avoiding duplicates
      const existingIds = new Set(prev.map(a => a.id));
      const uniqueNewAlerts = newAlerts.filter(a => !existingIds.has(a.id));
      return [...prev, ...uniqueNewAlerts];
    });
  }, [thresholds, metrics, dismissedAlerts]);

  const dismissAlert = (alertId: string) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ));
  };

  const getAlertIcon = (severity: string) => {
    const icons = {
      info: 'ℹ️',
      warning: '⚠️',
      critical: '🚨'
    };
    return icons[severity as keyof typeof icons] || '📢';
  };

  const getAlertColor = (severity: string) => {
    const colors = {
      info: 'border-blue-500 bg-blue-900/20 text-blue-400',
      warning: 'border-yellow-500 bg-yellow-900/20 text-yellow-400',
      critical: 'border-red-500 bg-red-900/20 text-red-400'
    };
    return colors[severity as keyof typeof colors] || colors.info;
  };

  const formatMetricValue = (metric: string, value: number) => {
    switch (metric) {
      case 'memoryUtilization':
        return `${(value * 100).toFixed(1)}%`;
      case 'learningVelocity':
        return `${value.toFixed(3)} pts/hr`;
      case 'retentionRate':
        return `${(value * 100).toFixed(1)}%`;
      case 'iqImprovement':
        return `+${value.toFixed(1)} IQ points`;
      default:
        return value.toFixed(2);
    }
  };

  const getMetricDisplayName = (metric: string) => {
    return metric.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
  };

  const activeAlerts = alerts.filter(alert => !alert.acknowledged);
  const acknowledgedAlerts = alerts.filter(alert => alert.acknowledged);

  if (alerts.length === 0) {
    return null;
  }

  return (
    <div className={className}>
      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <div className="space-y-2">
          {activeAlerts.map(alert => (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border ${getAlertColor(alert.threshold.severity)} transition-all duration-300 animate-pulse`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <span className="text-lg">{getAlertIcon(alert.threshold.severity)}</span>
                  <div>
                    <h4 className="font-semibold mb-1">
                      {alert.threshold.severity.toUpperCase()}: {getMetricDisplayName(alert.threshold.metric)}
                    </h4>
                    <p className="text-sm opacity-90 mb-2">{alert.threshold.message}</p>
                    <div className="flex items-center space-x-4 text-xs">
                      <span>Current: {formatMetricValue(alert.threshold.metric, alert.currentValue)}</span>
                      <span>Threshold: {formatMetricValue(alert.threshold.metric, alert.threshold.value)}</span>
                      <span>• {new Date(alert.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => acknowledgeAlert(alert.id)}
                    className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                  >
                    Acknowledge
                  </button>
                  <button
                    onClick={() => dismissAlert(alert.id)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Acknowledged Alerts (collapsible) */}
      {acknowledgedAlerts.length > 0 && (
        <div className="mt-4">
          <details className="group">
            <summary className="cursor-pointer text-sm text-gray-400 hover:text-white transition-colors flex items-center">
              <span>{acknowledgedAlerts.length} acknowledged alert{acknowledgedAlerts.length > 1 ? 's' : ''}</span>
              <svg className="w-4 h-4 ml-1 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="mt-2 space-y-2">
              {acknowledgedAlerts.map(alert => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border ${getAlertColor(alert.threshold.severity)} opacity-60`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span>{getAlertIcon(alert.threshold.severity)}</span>
                      <span className="text-sm">{getMetricDisplayName(alert.threshold.metric)}</span>
                      <span className="text-xs opacity-75">
                        {formatMetricValue(alert.threshold.metric, alert.currentValue)}
                      </span>
                    </div>
                    <button
                      onClick={() => dismissAlert(alert.id)}
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}

      {/* Alert Summary Badge */}
      <div className="fixed bottom-4 right-4 z-40">
        {activeAlerts.length > 0 && (
          <div className="bg-red-600 text-white px-3 py-2 rounded-full shadow-lg animate-bounce">
            <span className="font-medium">{activeAlerts.length}</span>
            <span className="ml-1">active alert{activeAlerts.length > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
};