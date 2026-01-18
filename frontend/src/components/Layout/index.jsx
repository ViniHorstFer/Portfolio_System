/**
 * Main layout components
 */

import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { clsx } from 'clsx';
import { Toaster } from 'react-hot-toast';

// Navigation items
const navItems = [
  { path: '/', label: 'Fund Database', icon: '📋' },
  { path: '/analysis', label: 'Detailed Analysis', icon: '📊' },
  { path: '/comparison', label: 'Advanced Comparison', icon: '🔍' },
  { path: '/portfolio', label: 'Portfolio Construction', icon: '🎯' },
  { path: '/recommended', label: 'Recommended Portfolio', icon: '💼' },
  { path: '/risk-monitor', label: 'Risk Monitor', icon: '⚠️' },
];

/**
 * Sidebar navigation
 */
function Sidebar({ isOpen, onToggle }) {
  const location = useLocation();
  
  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 h-full bg-dark-100 border-r border-dark-300',
        'transition-all duration-300 z-40',
        isOpen ? 'w-64' : 'w-16'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-dark-300">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-2xl">📈</span>
          {isOpen && (
            <span className="text-gold font-bold text-lg">Fund Analytics</span>
          )}
        </Link>
      </div>
      
      {/* Navigation */}
      <nav className="p-2 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg',
                'transition-all duration-200',
                isActive
                  ? 'bg-gold/10 text-gold border border-gold/30'
                  : 'text-gray-400 hover:bg-dark-200 hover:text-white'
              )}
            >
              <span className="text-lg">{item.icon}</span>
              {isOpen && (
                <span className="font-medium truncate">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>
      
      {/* Toggle button */}
      <button
        onClick={onToggle}
        className={clsx(
          'absolute bottom-4 right-0 transform translate-x-1/2',
          'w-6 h-6 bg-dark-200 border border-dark-300 rounded-full',
          'flex items-center justify-center text-gray-400',
          'hover:bg-dark-300 hover:text-white transition-colors'
        )}
      >
        {isOpen ? '‹' : '›'}
      </button>
    </aside>
  );
}

/**
 * Header bar
 */
function Header({ sidebarOpen }) {
  return (
    <header
      className={clsx(
        'fixed top-0 right-0 h-16 bg-dark-100 border-b border-dark-300',
        'flex items-center justify-between px-6 z-30',
        'transition-all duration-300',
        sidebarOpen ? 'left-64' : 'left-16'
      )}
    >
      {/* Page title - will be set by pages */}
      <div id="page-title" className="text-xl font-semibold text-white" />
      
      {/* Right side actions */}
      <div className="flex items-center gap-4">
        {/* Period selector (global) */}
        <select className="select bg-dark-200 text-sm py-1.5">
          <option value="All">All Time</option>
          <option value="36M">36 Months</option>
          <option value="24M">24 Months</option>
          <option value="12M">12 Months</option>
          <option value="6M">6 Months</option>
          <option value="3M">3 Months</option>
        </select>
        
        {/* User menu */}
        <div className="flex items-center gap-2 text-gray-400">
          <span className="w-8 h-8 bg-gold/20 rounded-full flex items-center justify-center text-gold">
            👤
          </span>
        </div>
      </div>
    </header>
  );
}

/**
 * Main layout wrapper
 */
export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  return (
    <div className="min-h-screen bg-dark">
      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          className: 'bg-dark-200 text-white border border-dark-300',
          duration: 4000,
        }}
      />
      
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      {/* Header */}
      <Header sidebarOpen={sidebarOpen} />
      
      {/* Main content */}
      <main
        className={clsx(
          'pt-16 min-h-screen transition-all duration-300',
          sidebarOpen ? 'pl-64' : 'pl-16'
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

/**
 * Page wrapper component
 */
export function PageWrapper({ title, children, actions }) {
  return (
    <div className="animate-fade-in">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gold">{title}</h1>
        {actions && <div className="flex items-center gap-3">{actions}</div>}
      </div>
      
      {/* Page content */}
      {children}
    </div>
  );
}

/**
 * Loading spinner
 */
export function LoadingSpinner({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };
  
  return (
    <div
      className={clsx(
        'border-gold border-t-transparent rounded-full animate-spin',
        sizeClasses[size],
        className
      )}
    />
  );
}

/**
 * Loading overlay
 */
export function LoadingOverlay({ message = 'Loading...' }) {
  return (
    <div className="fixed inset-0 bg-dark/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-gray-400">{message}</p>
      </div>
    </div>
  );
}

/**
 * Empty state
 */
export function EmptyState({ icon = '📭', title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <span className="text-6xl mb-4">{icon}</span>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      {description && <p className="text-gray-400 mb-6 max-w-md">{description}</p>}
      {action}
    </div>
  );
}

/**
 * Error state
 */
export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <span className="text-6xl mb-4">❌</span>
      <h3 className="text-xl font-semibold text-white mb-2">Something went wrong</h3>
      <p className="text-gray-400 mb-6 max-w-md">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary">
          Try Again
        </button>
      )}
    </div>
  );
}

export default Layout;
