/**
 * Fund Database Page
 * Browse and filter investment funds
 */

import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';

import { PageWrapper, LoadingSpinner, EmptyState } from '../components/Layout';
import { useFunds, useCategories, useSubcategories } from '../hooks/useApi';
import { formatPercent, formatCurrencyBRL, formatInteger, debounce } from '../utils';

/**
 * Filters sidebar
 */
function Filters({ filters, onFilterChange }) {
  const { data: categories } = useCategories();
  const { data: subcategories } = useSubcategories(filters.category);
  
  return (
    <div className="space-y-4">
      {/* Search */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Search
        </label>
        <input
          type="text"
          className="input"
          placeholder="Fund name..."
          value={filters.search || ''}
          onChange={(e) => onFilterChange({ search: e.target.value })}
        />
      </div>
      
      {/* Category */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Category
        </label>
        <select
          className="select w-full"
          value={filters.category || ''}
          onChange={(e) => onFilterChange({ category: e.target.value || null, subcategory: null })}
        >
          <option value="">All Categories</option>
          {categories?.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>
      
      {/* Subcategory */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Subcategory
        </label>
        <select
          className="select w-full"
          value={filters.subcategory || ''}
          onChange={(e) => onFilterChange({ subcategory: e.target.value || null })}
        >
          <option value="">All Subcategories</option>
          {subcategories?.map((sub) => (
            <option key={sub} value={sub}>{sub}</option>
          ))}
        </select>
      </div>
      
      {/* Min Sharpe */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Min Sharpe (12M)
        </label>
        <input
          type="number"
          step="0.1"
          className="input"
          placeholder="e.g., 0.5"
          value={filters.min_sharpe ?? ''}
          onChange={(e) => onFilterChange({ min_sharpe: e.target.value ? parseFloat(e.target.value) : null })}
        />
      </div>
      
      {/* Max MDD */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Max Drawdown (%)
        </label>
        <input
          type="number"
          step="1"
          className="input"
          placeholder="e.g., -10"
          value={filters.max_mdd ?? ''}
          onChange={(e) => onFilterChange({ max_mdd: e.target.value ? parseFloat(e.target.value) / 100 : null })}
        />
      </div>
      
      {/* Min AUM */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Min AUM (R$ M)
        </label>
        <input
          type="number"
          step="10"
          className="input"
          placeholder="e.g., 100"
          value={filters.min_aum ? filters.min_aum / 1e6 : ''}
          onChange={(e) => onFilterChange({ min_aum: e.target.value ? parseFloat(e.target.value) * 1e6 : null })}
        />
      </div>
      
      {/* Max Liquidity */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Max Liquidity (days)
        </label>
        <input
          type="number"
          step="1"
          className="input"
          placeholder="e.g., 30"
          value={filters.max_liquidity_days ?? ''}
          onChange={(e) => onFilterChange({ max_liquidity_days: e.target.value ? parseInt(e.target.value) : null })}
        />
      </div>
      
      {/* Clear filters */}
      <button
        onClick={() => onFilterChange({
          search: '',
          category: null,
          subcategory: null,
          min_sharpe: null,
          max_mdd: null,
          min_aum: null,
          max_liquidity_days: null,
        })}
        className="btn-ghost w-full"
      >
        Clear Filters
      </button>
    </div>
  );
}

/**
 * Funds table
 */
function FundsTable({ funds, onSelectFund, sortBy, sortDesc, onSort }) {
  const columns = [
    { key: 'name', label: 'Fund Name', sortable: true },
    { key: 'category', label: 'Category', sortable: true },
    { key: 'return_12m', label: 'Return 12M', sortable: true, format: (v) => formatPercent(v) },
    { key: 'sharpe_12m', label: 'Sharpe', sortable: true, format: (v) => v?.toFixed(2) || 'N/A' },
    { key: 'volatility_12m', label: 'Vol 12M', sortable: true, format: (v) => formatPercent(v) },
    { key: 'max_drawdown', label: 'MDD', sortable: true, format: (v) => formatPercent(v) },
    { key: 'aum', label: 'AUM', sortable: true, format: formatCurrencyBRL },
    { key: 'liquidity', label: 'Liquidity', sortable: false },
  ];
  
  const handleSort = (key) => {
    if (sortBy === key) {
      onSort(key, !sortDesc);
    } else {
      onSort(key, true);
    }
  };
  
  return (
    <div className="overflow-x-auto">
      <table className="table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                onClick={() => col.sortable && handleSort(col.key)}
                className={clsx(
                  col.sortable && 'cursor-pointer hover:text-white',
                  sortBy === col.key && 'text-gold'
                )}
              >
                {col.label}
                {sortBy === col.key && (
                  <span className="ml-1">{sortDesc ? '↓' : '↑'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {funds.map((fund) => (
            <tr
              key={fund.name}
              onClick={() => onSelectFund(fund)}
              className="cursor-pointer hover:bg-dark-200"
            >
              {columns.map((col) => (
                <td key={col.key}>
                  {col.format ? col.format(fund[col.key]) : fund[col.key] || 'N/A'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Pagination
 */
function Pagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;
  
  const pages = [];
  const showPages = 5;
  let start = Math.max(1, page - Math.floor(showPages / 2));
  let end = Math.min(totalPages, start + showPages - 1);
  
  if (end - start < showPages - 1) {
    start = Math.max(1, end - showPages + 1);
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  
  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(1)}
        disabled={page === 1}
        className="btn-ghost btn-sm"
      >
        ««
      </button>
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="btn-ghost btn-sm"
      >
        «
      </button>
      
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={clsx(
            'btn-sm',
            p === page ? 'btn-primary' : 'btn-ghost'
          )}
        >
          {p}
        </button>
      ))}
      
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="btn-ghost btn-sm"
      >
        »
      </button>
      <button
        onClick={() => onPageChange(totalPages)}
        disabled={page === totalPages}
        className="btn-ghost btn-sm"
      >
        »»
      </button>
    </div>
  );
}

/**
 * Main Fund Database Page
 */
export default function FundDatabasePage() {
  const navigate = useNavigate();
  
  const [filters, setFilters] = useState({
    search: '',
    category: null,
    subcategory: null,
    min_sharpe: null,
    max_mdd: null,
    min_aum: null,
    max_liquidity_days: null,
  });
  
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('aum');
  const [sortDesc, setSortDesc] = useState(true);
  
  // Build query params
  const queryParams = useMemo(() => ({
    page,
    page_size: 50,
    sort_by: sortBy,
    sort_desc: sortDesc,
    ...Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== null && v !== '')
    ),
  }), [page, sortBy, sortDesc, filters]);
  
  // Fetch funds
  const { data, isLoading, error } = useFunds(queryParams);
  
  const handleFilterChange = (newFilters) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setPage(1); // Reset to first page when filters change
  };
  
  const handleSort = (key, desc) => {
    setSortBy(key);
    setSortDesc(desc);
  };
  
  const handleSelectFund = (fund) => {
    navigate(`/analysis?fund=${encodeURIComponent(fund.name)}`);
  };
  
  return (
    <PageWrapper title="📋 Fund Database">
      <div className="flex gap-6">
        {/* Filters sidebar */}
        <div className="w-64 flex-shrink-0">
          <div className="card sticky top-24">
            <h3 className="text-lg font-semibold text-gold mb-4">Filters</h3>
            <Filters filters={filters} onFilterChange={handleFilterChange} />
          </div>
        </div>
        
        {/* Main content */}
        <div className="flex-1">
          {/* Results count */}
          {data && (
            <div className="flex justify-between items-center mb-4">
              <p className="text-gray-400">
                Showing {data.items.length} of {data.total} funds
              </p>
            </div>
          )}
          
          {/* Table */}
          <div className="card">
            {isLoading ? (
              <div className="flex justify-center py-16">
                <LoadingSpinner size="lg" />
              </div>
            ) : error ? (
              <div className="text-center text-red-400 py-16">
                Error loading funds: {error.message}
              </div>
            ) : data?.items.length === 0 ? (
              <EmptyState
                icon="🔍"
                title="No funds found"
                description="Try adjusting your filters"
              />
            ) : (
              <>
                <FundsTable
                  funds={data.items}
                  onSelectFund={handleSelectFund}
                  sortBy={sortBy}
                  sortDesc={sortDesc}
                  onSort={handleSort}
                />
                
                <Pagination
                  page={data.page}
                  totalPages={data.total_pages}
                  onPageChange={setPage}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
