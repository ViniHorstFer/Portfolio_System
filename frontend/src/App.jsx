/**
 * Main Application Entry Point
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { Layout } from './components/Layout';
import FundDatabasePage from './pages/FundDatabase';
import RiskMonitorPage from './pages/RiskMonitor';

// Lazy load other pages
import { lazy, Suspense } from 'react';
import { LoadingSpinner } from './components/Layout';

// Placeholder pages (to be implemented)
const DetailedAnalysisPage = lazy(() => import('./pages/DetailedAnalysis'));
const AdvancedComparisonPage = lazy(() => import('./pages/AdvancedComparison'));
const PortfolioConstructionPage = lazy(() => import('./pages/PortfolioConstruction'));
const RecommendedPortfolioPage = lazy(() => import('./pages/RecommendedPortfolio'));

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Loading fallback
function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <LoadingSpinner size="lg" />
    </div>
  );
}

// Placeholder component for pages not yet implemented
function PlaceholderPage({ title }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh]">
      <span className="text-6xl mb-4">🚧</span>
      <h2 className="text-2xl font-bold text-gold mb-2">{title}</h2>
      <p className="text-gray-400">This page is under construction</p>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<FundDatabasePage />} />
            <Route
              path="analysis"
              element={
                <Suspense fallback={<PageLoader />}>
                  <PlaceholderPage title="Detailed Analysis" />
                </Suspense>
              }
            />
            <Route
              path="comparison"
              element={
                <Suspense fallback={<PageLoader />}>
                  <PlaceholderPage title="Advanced Comparison" />
                </Suspense>
              }
            />
            <Route
              path="portfolio"
              element={
                <Suspense fallback={<PageLoader />}>
                  <PlaceholderPage title="Portfolio Construction" />
                </Suspense>
              }
            />
            <Route
              path="recommended"
              element={
                <Suspense fallback={<PageLoader />}>
                  <PlaceholderPage title="Recommended Portfolio" />
                </Suspense>
              }
            />
            <Route path="risk-monitor" element={<RiskMonitorPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
