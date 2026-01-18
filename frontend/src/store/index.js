/**
 * Global state management using Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════════════════════
// AUTH STORE
// ═══════════════════════════════════════════════════════════════════════════════

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: (user, token) => set({
        user,
        token,
        isAuthenticated: true,
      }),
      
      logout: () => set({
        user: null,
        token: null,
        isAuthenticated: false,
      }),
      
      updateUser: (updates) => set((state) => ({
        user: { ...state.user, ...updates },
      })),
    }),
    {
      name: 'auth-storage',
    }
  )
);

// ═══════════════════════════════════════════════════════════════════════════════
// APP STORE
// ═══════════════════════════════════════════════════════════════════════════════

export const useAppStore = create((set) => ({
  // Sidebar state
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  // Loading states
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
  
  // Selected fund for detailed analysis
  selectedFund: null,
  setSelectedFund: (fund) => set({ selectedFund: fund }),
  
  // Period filter (global)
  selectedPeriod: 'All',
  setSelectedPeriod: (period) => set({ selectedPeriod: period }),
  
  // Theme
  theme: 'dark',
  toggleTheme: () => set((state) => ({
    theme: state.theme === 'dark' ? 'light' : 'dark',
  })),
}));

// ═══════════════════════════════════════════════════════════════════════════════
// RISK MONITOR STORE
// ═══════════════════════════════════════════════════════════════════════════════

export const useRiskMonitorStore = create(
  persist(
    (set, get) => ({
      // Selected funds for monitoring
      monitoredFunds: [],
      
      // Add fund to monitor
      addFund: (fundName) => set((state) => ({
        monitoredFunds: state.monitoredFunds.includes(fundName)
          ? state.monitoredFunds
          : [...state.monitoredFunds, fundName],
      })),
      
      // Remove fund from monitor
      removeFund: (fundName) => set((state) => ({
        monitoredFunds: state.monitoredFunds.filter((f) => f !== fundName),
      })),
      
      // Set all monitored funds
      setMonitoredFunds: (funds) => set({ monitoredFunds: funds }),
      
      // Clear all
      clearAll: () => set({ monitoredFunds: [] }),
      
      // View state
      activeView: 'summary', // 'summary' | 'returns' | 'flows'
      setActiveView: (view) => set({ activeView: view }),
      
      // Charts expanded state
      chartsExpanded: false,
      toggleChartsExpanded: () => set((state) => ({
        chartsExpanded: !state.chartsExpanded,
      })),
      setChartsExpanded: (expanded) => set({ chartsExpanded: expanded }),
    }),
    {
      name: 'risk-monitor-storage',
    }
  )
);

// ═══════════════════════════════════════════════════════════════════════════════
// PORTFOLIO STORE
// ═══════════════════════════════════════════════════════════════════════════════

export const usePortfolioStore = create(
  persist(
    (set, get) => ({
      // Portfolio allocations
      allocations: [], // [{ fundName, weight }]
      
      // Add allocation
      addAllocation: (fundName, weight = 0) => set((state) => {
        const existing = state.allocations.find((a) => a.fundName === fundName);
        if (existing) {
          return state;
        }
        return {
          allocations: [...state.allocations, { fundName, weight }],
        };
      }),
      
      // Update allocation weight
      updateWeight: (fundName, weight) => set((state) => ({
        allocations: state.allocations.map((a) =>
          a.fundName === fundName ? { ...a, weight } : a
        ),
      })),
      
      // Remove allocation
      removeAllocation: (fundName) => set((state) => ({
        allocations: state.allocations.filter((a) => a.fundName !== fundName),
      })),
      
      // Set all allocations
      setAllocations: (allocations) => set({ allocations }),
      
      // Clear all
      clearAllocations: () => set({ allocations: [] }),
      
      // Normalize weights to sum to 1
      normalizeWeights: () => set((state) => {
        const total = state.allocations.reduce((sum, a) => sum + a.weight, 0);
        if (total === 0) return state;
        return {
          allocations: state.allocations.map((a) => ({
            ...a,
            weight: a.weight / total,
          })),
        };
      }),
      
      // Get total weight
      getTotalWeight: () => {
        return get().allocations.reduce((sum, a) => sum + a.weight, 0);
      },
    }),
    {
      name: 'portfolio-storage',
    }
  )
);

// ═══════════════════════════════════════════════════════════════════════════════
// COMPARISON STORE
// ═══════════════════════════════════════════════════════════════════════════════

export const useComparisonStore = create((set) => ({
  // Selected funds for comparison
  comparedFunds: [],
  
  // Selected metrics
  selectedMetrics: [
    'RETURN_12M',
    'VOL_12M',
    'SHARPE_12M',
    'MDD',
    'VL_PATRIM_LIQ',
  ],
  
  // Filters
  filters: {
    categories: [],
    subcategories: [],
    minSharpe: null,
    maxMdd: null,
    minAum: null,
    maxLiquidityDays: null,
  },
  
  // Actions
  addFundToCompare: (fundName) => set((state) => ({
    comparedFunds: state.comparedFunds.includes(fundName)
      ? state.comparedFunds
      : [...state.comparedFunds, fundName],
  })),
  
  removeFundFromCompare: (fundName) => set((state) => ({
    comparedFunds: state.comparedFunds.filter((f) => f !== fundName),
  })),
  
  setComparedFunds: (funds) => set({ comparedFunds: funds }),
  
  clearComparedFunds: () => set({ comparedFunds: [] }),
  
  setSelectedMetrics: (metrics) => set({ selectedMetrics: metrics }),
  
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
  })),
  
  clearFilters: () => set({
    filters: {
      categories: [],
      subcategories: [],
      minSharpe: null,
      maxMdd: null,
      minAum: null,
      maxLiquidityDays: null,
    },
  }),
}));
