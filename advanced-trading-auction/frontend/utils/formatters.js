/**
 * Utility functions for formatting various data types
 */

/**
 * Format currency values with appropriate symbol and decimal places
 */
export const formatPrice = (price, currency = 'Gold', decimalPlaces = 2) => {
  if (price === null || price === undefined) return '---';

  const numPrice = typeof price === 'string' ? parseFloat(price) : price;

  if (isNaN(numPrice)) return 'Invalid';

  // Handle large numbers with appropriate suffixes
  if (numPrice >= 1000000) {
    return `${(numPrice / 1000000).toFixed(decimalPlaces)}M ${currency}`;
  } else if (numPrice >= 1000) {
    return `${(numPrice / 1000).toFixed(decimalPlaces)}K ${currency}`;
  } else {
    return `${numPrice.toFixed(decimalPlaces)} ${currency}`;
  }
};

/**
 * Format large numbers with thousands separators
 */
export const formatNumber = (num, decimalPlaces = 0) => {
  if (num === null || num === undefined) return '---';

  const numValue = typeof num === 'string' ? parseFloat(num) : num;

  if (isNaN(numValue)) return 'Invalid';

  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces
  }).format(numValue);
};

/**
 * Format time remaining in human-readable format
 */
export const formatTimeRemaining = (milliseconds) => {
  if (!milliseconds || milliseconds <= 0) {
    return 'Ended';
  }

  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
};

/**
 * Format duration in a more readable format
 */
export const formatDuration = (milliseconds) => {
  if (!milliseconds) return '0s';

  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  const parts = [];

  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours % 24}h`);
  if (minutes > 0) parts.push(`${minutes % 60}m`);
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds % 60}s`);

  return parts.join(' ');
};

/**
 * Format dates in various formats
 */
export const formatDate = (date, format = 'medium') => {
  if (!date) return '---';

  const dateObj = new Date(date);
  if (isNaN(dateObj.getTime())) return 'Invalid Date';

  const options = {
    full: {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    },
    long: {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    },
    medium: {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    },
    short: {
      year: '2-digit',
      month: 'short',
      day: 'numeric'
    },
    time: {
      hour: '2-digit',
      minute: '2-digit'
    }
  };

  return dateObj.toLocaleString('en-US', options[format] || options.medium);
};

/**
 * Format relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (date) => {
  if (!date) return '---';

  const dateObj = new Date(date);
  if (isNaN(dateObj.getTime())) return 'Invalid Date';

  const now = new Date();
  const diffMs = now - dateObj;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  } else if (diffHours > 0) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  } else if (diffMinutes > 0) {
    return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
  } else if (diffSeconds > 0) {
    return `${diffSeconds} second${diffSeconds > 1 ? 's' : ''} ago`;
  } else {
    return 'Just now';
  }
};

/**
 * Get rarity color for items
 */
export const getItemRarityColor = (rarity) => {
  const colors = {
    common: '#8c8c8c',
    uncommon: '#52c41a',
    rare: '#1890ff',
    epic: '#722ed1',
    legendary: '#fa8c16'
  };
  return colors[rarity?.toLowerCase()] || '#8c8c8c';
};

/**
 * Format item rarity display
 */
export const formatItemRarity = (rarity) => {
  return rarity ? rarity.charAt(0).toUpperCase() + rarity.slice(1) : 'Common';
};

/**
 * Format percentage values
 */
export const formatPercentage = (value, decimalPlaces = 2) => {
  if (value === null || value === undefined) return '---';

  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(numValue)) return 'Invalid';

  return `${numValue.toFixed(decimalPlaces)}%`;
};

/**
 * Format change indicators with color coding
 */
export const formatChange = (value, decimalPlaces = 2) => {
  if (value === null || value === undefined) return { text: '---', color: '#666' };

  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(numValue)) return { text: 'Invalid', color: '#ff4d4f' };

  const isPositive = numValue > 0;
  const color = isPositive ? '#52c41a' : '#ff4d4f';
  const symbol = isPositive ? '+' : '';
  const text = `${symbol}${numValue.toFixed(decimalPlaces)}%`;

  return { text, color, isPositive };
};

/**
 * Format auction status
 */
export const formatAuctionStatus = (status) => {
  const statusConfig = {
    active: { text: 'Active', color: '#1890ff', icon: '⏱️' },
    sold: { text: 'Sold', color: '#52c41a', icon: '✅' },
    expired: { text: 'Expired', color: '#8c8c8c', icon: '⏰' },
    cancelled: { text: 'Cancelled', color: '#ff4d4f', icon: '❌' }
  };

  return statusConfig[status] || { text: status, color: '#666', icon: '❓' };
};

/**
 * Format listing type
 */
export const formatListingType = (type) => {
  const types = {
    fixed: 'Fixed Price',
    negotiable: 'Negotiable'
  };
  return types[type] || type;
};

/**
 * Format region display
 */
export const formatRegion = (regionId) => {
  const regions = {
    global: 'Global',
    north: 'North',
    south: 'South',
    east: 'East',
    west: 'West'
  };
  return regions[regionId] || regionId;
};

/**
 * Format player reputation level
 */
export const formatReputationLevel = (reputation) => {
  if (reputation >= 100) return { level: 'Legendary', color: '#fa8c16' };
  if (reputation >= 50) return { level: 'Esteemed', color: '#722ed1' };
  if (reputation >= 25) return { level: 'Trusted', color: '#1890ff' };
  if (reputation >= 10) return { level: 'Reliable', color: '#52c41a' };
  if (reputation >= 0) return { level: 'Neutral', color: '#8c8c8c' };
  if (reputation >= -10) return { level: 'Unreliable', color: '#ff7a45' };
  return { level: 'Dishonorable', color: '#ff4d4f' };
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * Format file sizes
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format player usernames with anonymization
 */
export const formatPlayerName = (username, anonymous = false) => {
  if (anonymous) return 'Anonymous';
  if (!username) return 'Unknown';

  // Show only first 3 characters and last 3 characters for privacy
  if (username.length > 6) {
    return `${username.substring(0, 3)}...${username.substring(username.length - 3)}`;
  }

  return username;
};

/**
 * Format search highlights
 */
export const highlightSearchText = (text, searchTerm) => {
  if (!searchTerm || !text) return text;

  const regex = new RegExp(`(${searchTerm})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) =>
    regex.test(part) ? <mark key={index}>{part}</mark> : part
  );
};