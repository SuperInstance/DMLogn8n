import React, { useState } from 'react';

interface ExportPanelProps {
  formats: string[];
  onExport: (format: string) => void;
  className?: string;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({
  formats,
  onExport,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState<string | null>(null);

  const handleExport = async (format: string) => {
    setIsExporting(format);
    try {
      await onExport(format);
      setIsOpen(false);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(null);
    }
  };

  const getFormatIcon = (format: string) => {
    const icons = {
      pdf: '📄',
      csv: '📊',
      json: '🗂️',
      xlsx: '📈',
      png: '🖼️',
      svg: '🎨'
    };
    return icons[format as keyof typeof icons] || '📁';
  };

  const getFormatDescription = (format: string) => {
    const descriptions = {
      pdf: 'Complete report with charts and analysis',
      csv: 'Raw data for spreadsheet analysis',
      json: 'Structured data for developers',
      xlsx: 'Excel-compatible data tables',
      png: 'High-resolution dashboard screenshot',
      svg: 'Vector graphics for presentations'
    };
    return descriptions[format as keyof typeof descriptions] || 'Export data';
  };

  return (
    <div className={`relative ${className}`}>
      {/* Export Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors flex items-center space-x-2"
      >
        <span>📤</span>
        <span>Export</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Export Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown Panel */}
          <div className="absolute right-0 top-full mt-2 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-20">
            <div className="p-4">
              <h3 className="text-white font-semibold mb-3">Export Progress Report</h3>
              <p className="text-gray-400 text-sm mb-4">
                Choose a format to export the agent's learning progress and performance data.
              </p>

              <div className="space-y-2">
                {formats.map((format) => (
                  <button
                    key={format}
                    onClick={() => handleExport(format)}
                    disabled={isExporting === format}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isExporting === format
                        ? 'bg-gray-700 border-gray-600 cursor-not-allowed opacity-50'
                        : 'bg-gray-900 border-gray-700 hover:border-blue-500 hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{getFormatIcon(format)}</span>
                        <div>
                          <p className="text-white font-medium uppercase">{format}</p>
                          <p className="text-gray-400 text-xs">{getFormatDescription(format)}</p>
                        </div>
                      </div>
                      {isExporting === format ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                      ) : (
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>

              {/* Export Options */}
              <div className="mt-4 pt-4 border-t border-gray-700">
                <h4 className="text-white font-medium mb-2">Export Options</h4>
                <div className="space-y-2 text-sm">
                  <label className="flex items-center space-x-2">
                    <input type="checkbox" defaultChecked className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-0" />
                    <span className="text-gray-300">Include charts and visualizations</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input type="checkbox" defaultChecked className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-0" />
                    <span className="text-gray-300">Include detailed analytics</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input type="checkbox" className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-0" />
                    <span className="text-gray-300">Include raw data tables</span>
                  </label>
                </div>
              </div>

              {/* Schedule Export */}
              <div className="mt-4 pt-4 border-t border-gray-700">
                <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium">
                  Schedule Regular Reports
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="px-4 py-3 bg-gray-900 border-t border-gray-700 rounded-b-lg">
              <p className="text-gray-500 text-xs">
                Reports are generated with data from the selected timeframe and may take a few moments to prepare.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};