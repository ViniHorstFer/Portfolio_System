/**
 * Utility functions for the Fund Analytics Platform
 */

// ═══════════════════════════════════════════════════════════════════════════════
// NUMBER FORMATTING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Format number as percentage
 */
export function formatPercent(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format number as currency (BRL)
 */
export function formatCurrencyBRL(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  
  if (Math.abs(value) >= 1e9) {
    return `R$ ${(value / 1e9).toFixed(2)}B`;
  }
  if (Math.abs(value) >= 1e6) {
    return `R$ ${(value / 1e6).toFixed(2)}M`;
  }
  if (Math.abs(value) >= 1e3) {
    return `R$ ${(value / 1e3).toFixed(2)}K`;
  }
  
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

/**
 * Format large numbers with abbreviations
 */
export function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  
  if (Math.abs(value) >= 1e9) {
    return `${(value / 1e9).toFixed(decimals)}B`;
  }
  if (Math.abs(value) >= 1e6) {
    return `${(value / 1e6).toFixed(decimals)}M`;
  }
  if (Math.abs(value) >= 1e3) {
    return `${(value / 1e3).toFixed(decimals)}K`;
  }
  
  return value.toFixed(decimals);
}

/**
 * Format integer with thousand separators
 */
export function formatInteger(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return new Intl.NumberFormat('pt-BR').format(Math.round(value));
}

// ═══════════════════════════════════════════════════════════════════════════════
// COLOR UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get color for return value based on VaR range
 */
export function getReturnColor(value, var95, var5) {
  if (value === null || value === undefined) {
    return '#888888';
  }
  
  // Normalize value between 0 and 1 based on VaR range
  const range = var5 - var95;
  if (range === 0) return '#888888';
  
  const normalized = Math.max(0, Math.min(1, (value - var95) / range));
  
  // Interpolate between red and green
  const red = Math.round(255 * (1 - normalized));
  const green = Math.round(255 * normalized);
  
  return `rgb(${red}, ${green}, 80)`;
}

/**
 * Get color for flow percentage based on threshold
 */
export function getFlowColor(value, threshold = 2.5) {
  if (value === null || value === undefined) {
    return '#888888';
  }
  
  if (value <= -threshold) {
    return '#F44336'; // Red
  }
  if (value >= threshold) {
    return '#4CAF50'; // Green
  }
  
  // Interpolate
  const normalized = (value + threshold) / (2 * threshold);
  const red = Math.round(244 * (1 - normalized) + 76 * normalized);
  const green = Math.round(67 * (1 - normalized) + 175 * normalized);
  
  return `rgb(${red}, ${green}, 80)`;
}

/**
 * Get status emoji based on conditions
 */
export function getStatusEmoji(statuses) {
  if (statuses.includes('bad')) return '‼️';
  if (statuses.includes('good')) return '✅';
  return '🆗';
}

// ═══════════════════════════════════════════════════════════════════════════════
// DATE UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Format date string
 */
export function formatDate(dateString, format = 'short') {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  
  if (format === 'short') {
    return date.toLocaleDateString('pt-BR');
  }
  if (format === 'long') {
    return date.toLocaleDateString('pt-BR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }
  if (format === 'iso') {
    return date.toISOString().split('T')[0];
  }
  
  return dateString;
}

/**
 * Get period months from label
 */
export function getPeriodMonths(period) {
  const map = {
    '3M': 3,
    '6M': 6,
    '12M': 12,
    '24M': 24,
    '36M': 36,
    'All': null,
  };
  return map[period] ?? null;
}

// ═══════════════════════════════════════════════════════════════════════════════
// DATA UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Sort array of objects by key
 */
export function sortBy(array, key, descending = false) {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (aVal === null || aVal === undefined) return 1;
    if (bVal === null || bVal === undefined) return -1;
    
    if (descending) {
      return bVal > aVal ? 1 : -1;
    }
    return aVal > bVal ? 1 : -1;
  });
}

/**
 * Group array by key
 */
export function groupBy(array, key) {
  return array.reduce((groups, item) => {
    const value = item[key] || 'Other';
    groups[value] = groups[value] || [];
    groups[value].push(item);
    return groups;
  }, {});
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function
 */
export function throttle(func, limit) {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// CHART UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create Plotly layout with dark theme
 */
export function createPlotlyLayout(title, options = {}) {
  return {
    title: {
      text: title,
      font: { color: '#D4AF37', size: 16 },
    },
    paper_bgcolor: '#0a0a0a',
    plot_bgcolor: '#0a0a0a',
    font: { color: '#ffffff' },
    xaxis: {
      gridcolor: '#2a2a2a',
      zerolinecolor: '#3a3a3a',
      ...options.xaxis,
    },
    yaxis: {
      gridcolor: '#2a2a2a',
      zerolinecolor: '#3a3a3a',
      ...options.yaxis,
    },
    legend: {
      bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#ffffff' },
      ...options.legend,
    },
    margin: { l: 60, r: 30, t: 50, b: 50 },
    ...options,
  };
}

/**
 * Brand colors for charts
 */
export const chartColors = {
  gold: '#D4AF37',
  goldLight: '#E5C76B',
  green: '#4CAF50',
  red: '#F44336',
  blue: '#2196F3',
  orange: '#FF9800',
  purple: '#9C27B0',
  cyan: '#00BCD4',
  gray: '#888888',
};

/**
 * Color palette for multiple series
 */
export const colorPalette = [
  '#D4AF37', // Gold
  '#4CAF50', // Green
  '#2196F3', // Blue
  '#F44336', // Red
  '#FF9800', // Orange
  '#9C27B0', // Purple
  '#00BCD4', // Cyan
  '#E91E63', // Pink
  '#CDDC39', // Lime
  '#607D8B', // Blue Gray
];

// ═══════════════════════════════════════════════════════════════════════════════
// VALIDATION UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Validate email
 */
export function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Validate CNPJ
 */
export function isValidCNPJ(cnpj) {
  const cleaned = cnpj.replace(/\D/g, '');
  return cleaned.length === 14;
}

/**
 * Check if value is empty
 */
export function isEmpty(value) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXPORT UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Download data as CSV
 */
export function downloadCSV(data, filename = 'export.csv') {
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map((row) =>
      headers.map((h) => {
        const val = row[h];
        if (typeof val === 'string' && val.includes(',')) {
          return `"${val}"`;
        }
        return val ?? '';
      }).join(',')
    ),
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}

/**
 * Download data as JSON
 */
export function downloadJSON(data, filename = 'export.json') {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}
