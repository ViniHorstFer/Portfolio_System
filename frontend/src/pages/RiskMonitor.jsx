/**
 * Risk Monitor Page
 * Real-time monitoring of fund risk metrics
 */

import { useState, useEffect, useMemo } from 'react';
import { clsx } from 'clsx';
import Select from 'react-select';
import toast from 'react-hot-toast';
import Plot from 'react-plotly.js';

import { PageWrapper, LoadingSpinner, EmptyState } from '../components/Layout';
import { useRiskMonitorData, useFundNames, useSavedMonitor, useSaveMonitor } from '../hooks/useApi';
import { useRiskMonitorStore, useAuthStore } from '../store';
import { formatPercent, getReturnColor, getFlowColor, getStatusEmoji, groupBy, createPlotlyLayout } from '../utils';

// View tabs
const VIEW_TABS = [
  { id: 'summary', label: '📊 Summary', icon: '📊' },
  { id: 'returns', label: '📈 Returns', icon: '📈' },
  { id: 'flows', label: '💰 Flows', icon: '💰' },
];

// Thresholds for flow status
const FLOW_THRESHOLDS = {
  daily: 2.5,
  weekly: 5.0,
  monthly: 7.5,
};

/**
 * Summary Table Component
 */
function SummaryTable({ data }) {
  // Group by subcategory
  const grouped = useMemo(() => groupBy(data.funds, 'subcategory'), [data]);
  
  return (
    <div className="overflow-x-auto">
      <table className="table w-full">
        <thead>
          <tr>
            <th rowSpan={2} className="text-left">Investment Fund</th>
            <th rowSpan={2}>RET</th>
            <th rowSpan={2}>NNM</th>
            <th colSpan={2} className="text-center border-l border-dark-300">Daily</th>
            <th colSpan={2} className="text-center border-l border-dark-300">Weekly</th>
            <th colSpan={2} className="text-center border-l border-dark-300">Monthly</th>
          </tr>
          <tr>
            <th className="border-l border-dark-300">Return</th>
            <th>NNM%</th>
            <th className="border-l border-dark-300">Return</th>
            <th>NNM%</th>
            <th className="border-l border-dark-300">Return</th>
            <th>NNM%</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(grouped).map(([subcategory, funds]) => (
            <>
              {/* Category header */}
              <tr key={`cat-${subcategory}`} className="bg-dark-200">
                <td colSpan={9} className="font-semibold text-gold py-2">
                  {subcategory || 'Other'}
                </td>
              </tr>
              
              {/* Fund rows */}
              {funds.map((fund) => {
                // Calculate return status
                const returnStatuses = ['daily', 'weekly', 'monthly'].map(freq => {
                  const d = fund[freq];
                  if (!d) return 'normal';
                  if (d.return_value <= d.var_95) return 'bad';
                  if (d.return_value >= d.var_5) return 'good';
                  return 'normal';
                });
                
                // Calculate NNM status
                const nnmStatuses = ['daily', 'weekly', 'monthly'].map(freq => {
                  const pct = fund.flows?.[`${freq}_transfers_pct`];
                  const threshold = FLOW_THRESHOLDS[freq];
                  if (pct === null || pct === undefined) return 'normal';
                  if (pct <= -threshold) return 'bad';
                  if (pct >= threshold) return 'good';
                  return 'normal';
                });
                
                return (
                  <tr key={fund.fund_name} className="hover:bg-dark-200/50">
                    <td className="font-medium">{fund.fund_name}</td>
                    <td className="text-center text-lg">{getStatusEmoji(returnStatuses)}</td>
                    <td className="text-center text-lg">{getStatusEmoji(nnmStatuses)}</td>
                    
                    {['daily', 'weekly', 'monthly'].map(freq => {
                      const d = fund[freq];
                      const flowPct = fund.flows?.[`${freq}_transfers_pct`];
                      const threshold = FLOW_THRESHOLDS[freq];
                      
                      return (
                        <>
                          <td
                            key={`${fund.fund_name}-${freq}-ret`}
                            className="border-l border-dark-300/50"
                            style={{ color: d ? getReturnColor(d.return_value, d.var_95, d.var_5) : '#888' }}
                          >
                            {d ? formatPercent(d.return_value, 2) : 'N/A'}
                          </td>
                          <td
                            key={`${fund.fund_name}-${freq}-nnm`}
                            style={{ color: flowPct !== null ? getFlowColor(flowPct, threshold) : '#888' }}
                          >
                            {flowPct !== null ? `${flowPct >= 0 ? '+' : ''}${flowPct.toFixed(2)}%` : 'N/A'}
                          </td>
                        </>
                      );
                    })}
                  </tr>
                );
              })}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Returns Distribution Charts Component
 */
function ReturnsCharts({ data }) {
  const { chartsExpanded, setChartsExpanded } = useRiskMonitorStore();
  const grouped = useMemo(() => groupBy(data.funds, 'subcategory'), [data]);
  
  const createDistributionChart = (fund, frequency) => {
    const returns = fund[`${frequency}_returns`];
    const metrics = fund[frequency];
    
    if (!returns || returns.length < 20 || !metrics) {
      return null;
    }
    
    // Simple histogram
    return {
      data: [
        {
          x: returns,
          type: 'histogram',
          name: 'Returns',
          marker: { color: '#D4AF37', opacity: 0.7 },
          nbinsx: 30,
        },
        // VaR lines
        {
          x: [metrics.var_95, metrics.var_95],
          y: [0, 100],
          type: 'scatter',
          mode: 'lines',
          name: 'VaR(95)',
          line: { color: '#F44336', dash: 'dash', width: 2 },
        },
        {
          x: [metrics.var_5, metrics.var_5],
          y: [0, 100],
          type: 'scatter',
          mode: 'lines',
          name: 'VaR(5)',
          line: { color: '#4CAF50', dash: 'dash', width: 2 },
        },
        // Latest return point
        {
          x: [metrics.return_value],
          y: [5],
          type: 'scatter',
          mode: 'markers',
          name: 'Latest',
          marker: { color: '#2196F3', size: 12, symbol: 'diamond' },
        },
      ],
      layout: createPlotlyLayout(`${frequency.charAt(0).toUpperCase() + frequency.slice(1)} Returns`, {
        showlegend: false,
        height: 200,
        margin: { l: 40, r: 20, t: 30, b: 30 },
        xaxis: { tickformat: '.2%' },
      }),
    };
  };
  
  return (
    <div>
      {/* Expand/Collapse buttons */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setChartsExpanded(true)}
          className="btn-secondary btn-sm"
        >
          ⊕ Expand
        </button>
        <button
          onClick={() => setChartsExpanded(false)}
          className="btn-secondary btn-sm"
        >
          ⊖ Collapse
        </button>
      </div>
      
      {/* Charts by subcategory */}
      {Object.entries(grouped).map(([subcategory, funds]) => (
        <div key={subcategory} className="mb-6">
          <h3 className="text-lg font-semibold text-gold mb-3">{subcategory || 'Other'}</h3>
          
          {funds.map((fund) => {
            // Calculate status for icon
            const statuses = ['daily', 'weekly', 'monthly'].map(freq => {
              const d = fund[freq];
              if (!d) return 'normal';
              if (d.return_value <= d.var_95) return 'bad';
              if (d.return_value >= d.var_5) return 'good';
              return 'normal';
            });
            const statusEmoji = getStatusEmoji(statuses);
            
            return (
              <details
                key={fund.fund_name}
                open={chartsExpanded}
                className="card mb-2"
              >
                <summary className="cursor-pointer font-medium flex items-center gap-2">
                  <span>{statusEmoji}</span>
                  <span>{fund.fund_name}</span>
                </summary>
                
                <div className="grid grid-cols-3 gap-4 mt-4">
                  {['daily', 'weekly', 'monthly'].map(freq => {
                    const chart = createDistributionChart(fund, freq);
                    if (!chart) {
                      return (
                        <div key={freq} className="text-center text-gray-500 py-8">
                          No data
                        </div>
                      );
                    }
                    return (
                      <Plot
                        key={freq}
                        data={chart.data}
                        layout={chart.layout}
                        config={{ displayModeBar: false, responsive: true }}
                        style={{ width: '100%', height: '200px' }}
                      />
                    );
                  })}
                </div>
              </details>
            );
          })}
        </div>
      ))}
    </div>
  );
}

/**
 * Flows Table Component
 */
function FlowsTable({ data }) {
  const grouped = useMemo(() => groupBy(data.funds, 'subcategory'), [data]);
  
  const formatFlow = (value, pct, threshold) => {
    if (value === null || value === undefined) return { text: 'N/A', color: '#888' };
    
    const sign = value >= 0 ? '+' : '';
    const absVal = Math.abs(value);
    let text;
    
    if (absVal >= 1e9) text = `${sign}R$ ${(value / 1e9).toFixed(1)}B`;
    else if (absVal >= 1e6) text = `${sign}R$ ${(value / 1e6).toFixed(1)}M`;
    else if (absVal >= 1e3) text = `${sign}R$ ${(value / 1e3).toFixed(1)}K`;
    else text = `${sign}R$ ${value.toFixed(0)}`;
    
    if (pct !== null) {
      text += ` (${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%)`;
    }
    
    return { text, color: getFlowColor(pct || 0, threshold) };
  };
  
  return (
    <div className="overflow-x-auto">
      <table className="table w-full">
        <thead>
          <tr>
            <th rowSpan={2}>Investment Fund</th>
            <th rowSpan={2}>Status</th>
            <th rowSpan={2}>AUM</th>
            <th rowSpan={2}>Shareholders</th>
            <th colSpan={2} className="text-center border-l border-dark-300">Daily</th>
            <th colSpan={2} className="text-center border-l border-dark-300">Weekly</th>
            <th colSpan={2} className="text-center border-l border-dark-300">Monthly</th>
          </tr>
          <tr>
            <th className="border-l border-dark-300">NNM</th>
            <th>ΔInvestors</th>
            <th className="border-l border-dark-300">NNM</th>
            <th>ΔInvestors</th>
            <th className="border-l border-dark-300">NNM</th>
            <th>ΔInvestors</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(grouped).map(([subcategory, funds]) => (
            <>
              <tr key={`cat-${subcategory}`} className="bg-dark-200">
                <td colSpan={10} className="font-semibold text-gold py-2">
                  {subcategory || 'Other'}
                </td>
              </tr>
              
              {funds.map((fund) => {
                const flows = fund.flows || {};
                
                // Calculate status
                const statuses = ['daily', 'weekly', 'monthly'].map(freq => {
                  const pct = flows[`${freq}_transfers_pct`];
                  const threshold = FLOW_THRESHOLDS[freq];
                  if (pct === null || pct === undefined) return 'normal';
                  if (pct <= -threshold) return 'bad';
                  if (pct >= threshold) return 'good';
                  return 'normal';
                });
                
                return (
                  <tr key={fund.fund_name} className="hover:bg-dark-200/50">
                    <td className="font-medium">{fund.fund_name}</td>
                    <td className="text-center text-lg">{getStatusEmoji(statuses)}</td>
                    <td>
                      {flows.aum
                        ? `R$ ${(flows.aum / 1e6).toFixed(1)}M`
                        : 'N/A'}
                    </td>
                    <td>{flows.shareholders?.toLocaleString() || 'N/A'}</td>
                    
                    {['daily', 'weekly', 'monthly'].map(freq => {
                      const threshold = FLOW_THRESHOLDS[freq];
                      const transfers = formatFlow(
                        flows[`${freq}_transfers`],
                        flows[`${freq}_transfers_pct`],
                        threshold
                      );
                      const investors = flows[`${freq}_investors`];
                      const investorsPct = flows[`${freq}_investors_pct`];
                      
                      return (
                        <>
                          <td
                            key={`${fund.fund_name}-${freq}-nnm`}
                            className="border-l border-dark-300/50"
                            style={{ color: transfers.color }}
                          >
                            {transfers.text}
                          </td>
                          <td
                            key={`${fund.fund_name}-${freq}-inv`}
                            style={{
                              color: investorsPct !== null
                                ? getFlowColor(investorsPct || 0, threshold)
                                : '#888',
                            }}
                          >
                            {investors !== null
                              ? `${investors >= 0 ? '+' : ''}${investors.toLocaleString()}`
                              : 'N/A'}
                          </td>
                        </>
                      );
                    })}
                  </tr>
                );
              })}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Fund Selector Component
 */
function FundSelector({ selected, onChange }) {
  const [search, setSearch] = useState('');
  const { data: fundNames, isLoading } = useFundNames(search, search.length >= 2);
  
  const options = useMemo(() => {
    if (!fundNames) return [];
    return fundNames.map(name => ({ value: name, label: name }));
  }, [fundNames]);
  
  const selectedOptions = useMemo(() => {
    return selected.map(name => ({ value: name, label: name }));
  }, [selected]);
  
  return (
    <Select
      isMulti
      options={options}
      value={selectedOptions}
      onChange={(opts) => onChange(opts.map(o => o.value))}
      onInputChange={setSearch}
      isLoading={isLoading}
      placeholder="Search and select funds..."
      className="react-select-container"
      classNamePrefix="react-select"
      noOptionsMessage={() => search.length < 2 ? 'Type to search...' : 'No funds found'}
    />
  );
}

/**
 * Main Risk Monitor Page Component
 */
export default function RiskMonitorPage() {
  const { user } = useAuthStore();
  const {
    monitoredFunds,
    setMonitoredFunds,
    activeView,
    setActiveView,
  } = useRiskMonitorStore();
  
  const userId = user?.username || 'manager';
  
  // Load saved monitor on mount
  const { data: savedMonitor } = useSavedMonitor(userId, 'RiskMonitor', true);
  
  useEffect(() => {
    if (savedMonitor?.funds && monitoredFunds.length === 0) {
      setMonitoredFunds(savedMonitor.funds);
    }
  }, [savedMonitor, monitoredFunds.length, setMonitoredFunds]);
  
  // Fetch risk data
  const { data: riskData, isLoading, error, refetch } = useRiskMonitorData(
    monitoredFunds,
    monitoredFunds.length > 0
  );
  
  // Save monitor mutation
  const saveMutation = useSaveMonitor();
  
  const handleSave = async (name) => {
    try {
      await saveMutation.mutateAsync({
        monitorName: name,
        userId,
        funds: monitoredFunds,
      });
      toast.success(`Saved "${name}"`);
    } catch (err) {
      toast.error('Failed to save');
    }
  };
  
  return (
    <PageWrapper
      title="⚠️ Risk Monitor"
      actions={
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="btn-secondary btn-sm"
            disabled={isLoading}
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => handleSave('RiskMonitor')}
            className="btn-primary btn-sm"
            disabled={monitoredFunds.length === 0}
          >
            💾 Save
          </button>
        </div>
      }
    >
      {/* Fund selector */}
      <div className="card mb-6">
        <h3 className="text-lg font-semibold mb-3">Select Funds to Monitor</h3>
        <FundSelector
          selected={monitoredFunds}
          onChange={setMonitoredFunds}
        />
        <p className="text-sm text-gray-500 mt-2">
          {monitoredFunds.length} fund(s) selected
        </p>
      </div>
      
      {/* View tabs */}
      {monitoredFunds.length > 0 && (
        <div className="flex gap-2 mb-6">
          {VIEW_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={clsx(
                'px-4 py-2 rounded-lg font-medium transition-all',
                activeView === tab.id
                  ? 'bg-gold text-dark'
                  : 'bg-dark-200 text-gray-400 hover:bg-dark-300 hover:text-white'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}
      
      {/* Content */}
      {monitoredFunds.length === 0 ? (
        <EmptyState
          icon="👆"
          title="No funds selected"
          description="Select funds above to monitor their risk metrics"
        />
      ) : isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : error ? (
        <div className="text-center text-red-400 py-16">
          Error loading data: {error.message}
        </div>
      ) : riskData ? (
        <div className="card">
          {activeView === 'summary' && <SummaryTable data={riskData} />}
          {activeView === 'returns' && <ReturnsCharts data={riskData} />}
          {activeView === 'flows' && <FlowsTable data={riskData} />}
        </div>
      ) : null}
      
      {/* Legend */}
      {riskData && activeView === 'summary' && (
        <div className="mt-4 text-sm text-gray-400">
          <p><strong>Legend:</strong></p>
          <ul className="list-disc list-inside mt-1 space-y-1">
            <li><strong>RET (Returns Status):</strong> ‼️ any return ≤ VaR(95) | ✅ any return ≥ VaR(5) | 🆗 all within range</li>
            <li><strong>NNM (Net New Money Status):</strong> ‼️ any NNM% ≤ -threshold | ✅ any NNM% ≥ +threshold | 🆗 all within thresholds</li>
            <li><strong>Thresholds:</strong> Daily ±2.5% | Weekly ±5.0% | Monthly ±7.5%</li>
          </ul>
        </div>
      )}
    </PageWrapper>
  );
}
