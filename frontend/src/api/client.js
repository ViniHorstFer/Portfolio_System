/**
 * API Client for Fund Analytics Platform
 * Handles all HTTP requests to the FastAPI backend
 */

import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ═══════════════════════════════════════════════════════════════════════════════
// FUNDS API
// ═══════════════════════════════════════════════════════════════════════════════

export const fundsApi = {
  /**
   * Get paginated list of funds
   */
  getFunds: async (params = {}) => {
    const response = await api.get('/funds/', { params });
    return response.data;
  },

  /**
   * Get fund categories
   */
  getCategories: async () => {
    const response = await api.get('/funds/categories');
    return response.data.categories;
  },

  /**
   * Get fund subcategories
   */
  getSubcategories: async (category = null) => {
    const params = category ? { category } : {};
    const response = await api.get('/funds/subcategories', { params });
    return response.data.subcategories;
  },

  /**
   * Get fund names for autocomplete
   */
  getFundNames: async (search = '', limit = 50) => {
    const response = await api.get('/funds/names', { params: { search, limit } });
    return response.data.names;
  },

  /**
   * Get detailed fund information
   */
  getFundDetail: async (fundName) => {
    const response = await api.get(`/funds/${encodeURIComponent(fundName)}`);
    return response.data;
  },

  /**
   * Get fund returns time series
   */
  getFundReturns: async (fundName, periodMonths = null) => {
    const params = periodMonths ? { period_months: periodMonths } : {};
    const response = await api.get(`/funds/${encodeURIComponent(fundName)}/returns`, { params });
    return response.data;
  },

  /**
   * Get fund metrics
   */
  getFundMetrics: async (fundName, periodMonths = null) => {
    const params = periodMonths ? { period_months: periodMonths } : {};
    const response = await api.get(`/funds/${encodeURIComponent(fundName)}/metrics`, { params });
    return response.data;
  },

  /**
   * Compare multiple funds
   */
  compareFunds: async (fundNames, metrics = null) => {
    const response = await api.post('/funds/compare', {
      fund_names: fundNames,
      metrics,
    });
    return response.data.comparison;
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// RISK MONITOR API
// ═══════════════════════════════════════════════════════════════════════════════

export const riskApi = {
  /**
   * Get risk monitor data for funds
   */
  getRiskMonitorData: async (fundNames) => {
    const response = await api.post('/risk/monitor', {
      fund_names: fundNames,
    });
    return response.data;
  },

  /**
   * Get distribution chart data
   */
  getDistributionData: async (fundName, frequency) => {
    const response = await api.post('/risk/monitor/distribution', null, {
      params: { fund_name: fundName, frequency },
    });
    return response.data;
  },

  /**
   * Get saved monitors for user
   */
  getSavedMonitors: async (userId) => {
    const response = await api.get(`/risk/monitor/saved/${userId}`);
    return response.data.monitors;
  },

  /**
   * Get specific saved monitor
   */
  getSavedMonitor: async (userId, monitorName) => {
    const response = await api.get(`/risk/monitor/saved/${userId}/${encodeURIComponent(monitorName)}`);
    return response.data;
  },

  /**
   * Save risk monitor configuration
   */
  saveMonitor: async (monitorName, userId, funds) => {
    const response = await api.post('/risk/monitor/save', null, {
      params: { monitor_name: monitorName, user_id: userId },
      data: funds,
    });
    return response.data;
  },

  /**
   * Delete saved monitor
   */
  deleteMonitor: async (userId, monitorName) => {
    const response = await api.delete(`/risk/monitor/saved/${userId}/${encodeURIComponent(monitorName)}`);
    return response.data;
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// PORTFOLIO API
// ═══════════════════════════════════════════════════════════════════════════════

export const portfolioApi = {
  /**
   * Analyze portfolio
   */
  analyzePortfolio: async (allocations, periodMonths = null, benchmark = 'CDI') => {
    const response = await api.post('/portfolio/analyze', {
      allocations: allocations.map(a => ({
        fund_name: a.fundName,
        weight: a.weight,
      })),
      period_months: periodMonths,
    }, {
      params: { benchmark_name: benchmark },
    });
    return response.data;
  },

  /**
   * Get portfolio returns
   */
  getPortfolioReturns: async (allocations, periodMonths = null) => {
    const response = await api.post('/portfolio/returns', allocations, {
      params: { period_months: periodMonths },
    });
    return response.data;
  },

  /**
   * Get portfolio metrics
   */
  getPortfolioMetrics: async (allocations, periodMonths = null) => {
    const response = await api.post('/portfolio/metrics', allocations, {
      params: { period_months: periodMonths },
    });
    return response.data;
  },

  /**
   * Optimize portfolio
   */
  optimizePortfolio: async (fundNames, constraints = null, riskAversion = 1.0) => {
    const response = await api.post('/portfolio/optimize', {
      fund_names: fundNames,
      constraints,
      risk_aversion: riskAversion,
    });
    return response.data;
  },

  /**
   * Get saved portfolios
   */
  getSavedPortfolios: async (userId) => {
    const response = await api.get(`/portfolio/saved/${userId}`);
    return response.data.portfolios;
  },

  /**
   * Get specific saved portfolio
   */
  getSavedPortfolio: async (userId, portfolioName) => {
    const response = await api.get(`/portfolio/saved/${userId}/${encodeURIComponent(portfolioName)}`);
    return response.data;
  },

  /**
   * Save portfolio
   */
  savePortfolio: async (userId, portfolioName, allocations) => {
    const response = await api.post(`/portfolio/save/${userId}`, {
      portfolio_name: portfolioName,
      allocations,
    });
    return response.data;
  },

  /**
   * Delete saved portfolio
   */
  deletePortfolio: async (userId, portfolioName) => {
    const response = await api.delete(`/portfolio/saved/${userId}/${encodeURIComponent(portfolioName)}`);
    return response.data;
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// BENCHMARKS API
// ═══════════════════════════════════════════════════════════════════════════════

export const benchmarksApi = {
  /**
   * Get list of benchmarks
   */
  getBenchmarks: async () => {
    const response = await api.get('/benchmarks/');
    return response.data.benchmarks;
  },

  /**
   * Get benchmark data
   */
  getBenchmarkData: async (benchmarkName, periodMonths = null) => {
    const params = periodMonths ? { period_months: periodMonths } : {};
    const response = await api.get(`/benchmarks/${encodeURIComponent(benchmarkName)}`, { params });
    return response.data;
  },

  /**
   * Compare benchmarks
   */
  compareBenchmarks: async (benchmarkNames, periodMonths = null) => {
    const response = await api.post('/benchmarks/compare', benchmarkNames, {
      params: { period_months: periodMonths },
    });
    return response.data;
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// HEALTH & SYSTEM
// ═══════════════════════════════════════════════════════════════════════════════

export const systemApi = {
  /**
   * Health check
   */
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  /**
   * Reload data
   */
  reloadData: async () => {
    const response = await api.post('/reload-data');
    return response.data;
  },
};

export default api;
