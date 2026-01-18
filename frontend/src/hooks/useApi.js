/**
 * React Query hooks for data fetching
 * Provides caching, background refetching, and loading states
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fundsApi, riskApi, portfolioApi, benchmarksApi } from '../api/client';

// ═══════════════════════════════════════════════════════════════════════════════
// FUNDS HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get paginated funds list
 */
export function useFunds(params = {}) {
  return useQuery({
    queryKey: ['funds', params],
    queryFn: () => fundsApi.getFunds(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    keepPreviousData: true,
  });
}

/**
 * Get fund categories
 */
export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: fundsApi.getCategories,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
}

/**
 * Get fund subcategories
 */
export function useSubcategories(category = null) {
  return useQuery({
    queryKey: ['subcategories', category],
    queryFn: () => fundsApi.getSubcategories(category),
    staleTime: 30 * 60 * 1000,
  });
}

/**
 * Get fund names for autocomplete
 */
export function useFundNames(search = '', enabled = true) {
  return useQuery({
    queryKey: ['fundNames', search],
    queryFn: () => fundsApi.getFundNames(search),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && search.length >= 2,
  });
}

/**
 * Get fund detail
 */
export function useFundDetail(fundName, enabled = true) {
  return useQuery({
    queryKey: ['fundDetail', fundName],
    queryFn: () => fundsApi.getFundDetail(fundName),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!fundName,
  });
}

/**
 * Get fund returns
 */
export function useFundReturns(fundName, periodMonths = null, enabled = true) {
  return useQuery({
    queryKey: ['fundReturns', fundName, periodMonths],
    queryFn: () => fundsApi.getFundReturns(fundName, periodMonths),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!fundName,
  });
}

/**
 * Get fund metrics
 */
export function useFundMetrics(fundName, periodMonths = null, enabled = true) {
  return useQuery({
    queryKey: ['fundMetrics', fundName, periodMonths],
    queryFn: () => fundsApi.getFundMetrics(fundName, periodMonths),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!fundName,
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// RISK MONITOR HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get risk monitor data for selected funds
 */
export function useRiskMonitorData(fundNames, enabled = true) {
  return useQuery({
    queryKey: ['riskMonitor', fundNames],
    queryFn: () => riskApi.getRiskMonitorData(fundNames),
    staleTime: 60 * 1000, // 1 minute - risk data should be fresher
    enabled: enabled && fundNames.length > 0,
  });
}

/**
 * Get saved risk monitors
 */
export function useSavedMonitors(userId, enabled = true) {
  return useQuery({
    queryKey: ['savedMonitors', userId],
    queryFn: () => riskApi.getSavedMonitors(userId),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!userId,
  });
}

/**
 * Get specific saved monitor
 */
export function useSavedMonitor(userId, monitorName, enabled = true) {
  return useQuery({
    queryKey: ['savedMonitor', userId, monitorName],
    queryFn: () => riskApi.getSavedMonitor(userId, monitorName),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!userId && !!monitorName,
  });
}

/**
 * Save monitor mutation
 */
export function useSaveMonitor() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ monitorName, userId, funds }) =>
      riskApi.saveMonitor(monitorName, userId, funds),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries(['savedMonitors', userId]);
    },
  });
}

/**
 * Delete monitor mutation
 */
export function useDeleteMonitor() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, monitorName }) =>
      riskApi.deleteMonitor(userId, monitorName),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries(['savedMonitors', userId]);
    },
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// PORTFOLIO HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Analyze portfolio
 */
export function usePortfolioAnalysis(allocations, periodMonths = null, benchmark = 'CDI', enabled = true) {
  return useQuery({
    queryKey: ['portfolioAnalysis', allocations, periodMonths, benchmark],
    queryFn: () => portfolioApi.analyzePortfolio(allocations, periodMonths, benchmark),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && allocations.length > 0,
  });
}

/**
 * Optimize portfolio mutation
 */
export function useOptimizePortfolio() {
  return useMutation({
    mutationFn: ({ fundNames, constraints, riskAversion }) =>
      portfolioApi.optimizePortfolio(fundNames, constraints, riskAversion),
  });
}

/**
 * Get saved portfolios
 */
export function useSavedPortfolios(userId, enabled = true) {
  return useQuery({
    queryKey: ['savedPortfolios', userId],
    queryFn: () => portfolioApi.getSavedPortfolios(userId),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!userId,
  });
}

/**
 * Save portfolio mutation
 */
export function useSavePortfolio() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, portfolioName, allocations }) =>
      portfolioApi.savePortfolio(userId, portfolioName, allocations),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries(['savedPortfolios', userId]);
    },
  });
}

/**
 * Delete portfolio mutation
 */
export function useDeletePortfolio() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, portfolioName }) =>
      portfolioApi.deletePortfolio(userId, portfolioName),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries(['savedPortfolios', userId]);
    },
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// BENCHMARKS HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get available benchmarks
 */
export function useBenchmarks() {
  return useQuery({
    queryKey: ['benchmarks'],
    queryFn: benchmarksApi.getBenchmarks,
    staleTime: 30 * 60 * 1000,
  });
}

/**
 * Get benchmark data
 */
export function useBenchmarkData(benchmarkName, periodMonths = null, enabled = true) {
  return useQuery({
    queryKey: ['benchmarkData', benchmarkName, periodMonths],
    queryFn: () => benchmarksApi.getBenchmarkData(benchmarkName, periodMonths),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!benchmarkName,
  });
}
