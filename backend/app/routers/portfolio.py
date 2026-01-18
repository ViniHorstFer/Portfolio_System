"""
Portfolio-related API endpoints.
Handles portfolio analysis, optimization, and saved portfolios.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from datetime import datetime

from app.dependencies import get_data_cache, get_supabase, DataCache
from app.models import (
    PortfolioAllocation,
    PortfolioRequest,
    PortfolioMetricsResponse,
    PortfolioReturns,
    PortfolioAnalysis,
    CategoryBreakdown,
    LiquidityBreakdown,
    SavedPortfolio,
    SavePortfolioRequest,
    OptimizationRequest,
    OptimizationResult,
)
from app.core import (
    get_fund_returns_by_name,
    calculate_portfolio_returns,
    PortfolioMetrics,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_fund_metadata(fund_name: str, fund_metrics: pd.DataFrame) -> dict:
    """Get fund category, subcategory, and liquidity info."""
    fund_row = fund_metrics[fund_metrics['FUNDO DE INVESTIMENTO'] == fund_name]
    
    if len(fund_row) == 0:
        return {
            'category': 'Unknown',
            'subcategory': 'Unknown',
            'liquidity': 'Unknown',
            'liquidity_days': 0,
        }
    
    row = fund_row.iloc[0]
    
    liquidity = row.get('LIQUIDEZ', 'Unknown')
    liquidity_days = row.get('LIQUIDEZ_DAYS', 0)
    
    # Try to extract days from liquidity string if LIQUIDEZ_DAYS not available
    if pd.isna(liquidity_days) or liquidity_days == 0:
        if isinstance(liquidity, str) and liquidity.startswith('D+'):
            try:
                liquidity_days = int(liquidity.replace('D+', '').strip())
            except:
                liquidity_days = 0
    
    return {
        'category': row.get('CATEGORIA BTG', 'Unknown'),
        'subcategory': row.get('SUBCATEGORIA BTG', 'Unknown'),
        'liquidity': liquidity,
        'liquidity_days': int(liquidity_days) if pd.notna(liquidity_days) else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO ANALYSIS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/analyze")
async def analyze_portfolio(
    request: PortfolioRequest,
    benchmark_name: Optional[str] = "CDI",
    cache: DataCache = Depends(get_data_cache)
):
    """
    Analyze a portfolio and return comprehensive metrics.
    """
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    # Build weights dict
    weights = {a.fund_name: a.weight for a in request.allocations}
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise HTTPException(status_code=400, detail="Total weight cannot be zero")
    
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Get returns for each fund
    fund_returns_dict = {}
    for fund_name in weights.keys():
        returns = get_fund_returns_by_name(
            fund_name,
            cache.fund_metrics,
            cache.fund_details,
            request.period_months
        )
        if returns is not None and len(returns) > 0:
            fund_returns_dict[fund_name] = returns
    
    if not fund_returns_dict:
        raise HTTPException(status_code=404, detail="No valid returns data found")
    
    # Calculate portfolio returns
    portfolio_returns = calculate_portfolio_returns(fund_returns_dict, normalized_weights)
    
    if portfolio_returns is None or len(portfolio_returns) == 0:
        raise HTTPException(status_code=500, detail="Failed to calculate portfolio returns")
    
    # Calculate metrics
    metrics = PortfolioMetricsResponse(
        total_return=float((1 + portfolio_returns).prod() - 1),
        annualized_return=float(PortfolioMetrics.annualized_return(portfolio_returns)),
        volatility=float(PortfolioMetrics.volatility(portfolio_returns)),
        sharpe_ratio=float(PortfolioMetrics.sharpe_ratio(portfolio_returns)),
        max_drawdown=float(PortfolioMetrics.max_drawdown(portfolio_returns)),
        var_95=float(PortfolioMetrics.var(portfolio_returns, 0.95)),
        cvar_95=float(PortfolioMetrics.cvar(portfolio_returns, 0.95)),
        omega_ratio=float(PortfolioMetrics.omega_ratio(portfolio_returns)),
        rachev_ratio=float(PortfolioMetrics.rachev_ratio(portfolio_returns)),
    )
    
    # Calculate cumulative returns
    cumulative = PortfolioMetrics.cumulative_returns(portfolio_returns)
    
    # Get benchmark if available
    benchmark_cumulative = None
    if cache.benchmarks is not None and benchmark_name in cache.benchmarks.columns:
        bench_returns = cache.benchmarks[benchmark_name]
        # Align to portfolio dates
        bench_aligned = bench_returns.reindex(portfolio_returns.index, method='ffill').fillna(0)
        benchmark_cumulative = {
            benchmark_name: PortfolioMetrics.cumulative_returns(bench_aligned).tolist()
        }
    
    returns_data = PortfolioReturns(
        dates=[d.strftime('%Y-%m-%d') for d in portfolio_returns.index],
        returns=portfolio_returns.tolist(),
        cumulative_returns=cumulative.tolist(),
        benchmark_cumulative=benchmark_cumulative,
    )
    
    # Calculate breakdowns
    category_weights = {}
    subcategory_weights = {}
    liquidity_weights = {}
    total_liquidity_days = 0.0
    
    for fund_name, weight in normalized_weights.items():
        if fund_name not in fund_returns_dict:
            continue
        
        metadata = get_fund_metadata(fund_name, cache.fund_metrics)
        
        # Category breakdown
        cat = metadata['category']
        category_weights[cat] = category_weights.get(cat, 0) + weight
        
        # Subcategory breakdown
        subcat = metadata['subcategory']
        subcategory_weights[subcat] = subcategory_weights.get(subcat, 0) + weight
        
        # Liquidity breakdown
        liq = metadata['liquidity']
        liquidity_weights[liq] = liquidity_weights.get(liq, 0) + weight
        total_liquidity_days += metadata['liquidity_days'] * weight
    
    # Build response
    return PortfolioAnalysis(
        metrics=metrics,
        returns=returns_data,
        category_breakdown=[
            CategoryBreakdown(category=k, weight=v)
            for k, v in sorted(category_weights.items(), key=lambda x: -x[1])
        ],
        subcategory_breakdown=[
            CategoryBreakdown(category=k, weight=v)
            for k, v in sorted(subcategory_weights.items(), key=lambda x: -x[1])
        ],
        fund_breakdown=[
            PortfolioAllocation(fund_name=k, weight=v)
            for k, v in sorted(normalized_weights.items(), key=lambda x: -x[1])
            if k in fund_returns_dict
        ],
        liquidity_breakdown=[
            LiquidityBreakdown(
                liquidity=k,
                weight=v,
                days=int(k.replace('D+', '').strip()) if isinstance(k, str) and k.startswith('D+') else 0
            )
            for k, v in sorted(
                liquidity_weights.items(),
                key=lambda x: int(x[0].replace('D+', '').strip()) if isinstance(x[0], str) and x[0].startswith('D+') and x[0].replace('D+', '').strip().isdigit() else 9999
            )
        ],
        average_liquidity_days=round(total_liquidity_days),
    )


@router.post("/returns")
async def get_portfolio_returns(
    allocations: Dict[str, float],
    period_months: Optional[int] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Get portfolio returns time series."""
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    # Get returns for each fund
    fund_returns_dict = {}
    for fund_name in allocations.keys():
        returns = get_fund_returns_by_name(
            fund_name,
            cache.fund_metrics,
            cache.fund_details,
            period_months
        )
        if returns is not None:
            fund_returns_dict[fund_name] = returns
    
    if not fund_returns_dict:
        raise HTTPException(status_code=404, detail="No valid returns data found")
    
    # Calculate portfolio returns
    portfolio_returns = calculate_portfolio_returns(fund_returns_dict, allocations)
    
    if portfolio_returns is None:
        raise HTTPException(status_code=500, detail="Failed to calculate portfolio returns")
    
    cumulative = PortfolioMetrics.cumulative_returns(portfolio_returns)
    
    return {
        'dates': [d.strftime('%Y-%m-%d') for d in portfolio_returns.index],
        'returns': portfolio_returns.tolist(),
        'cumulative_returns': cumulative.tolist(),
    }


@router.post("/metrics")
async def get_portfolio_metrics(
    allocations: Dict[str, float],
    period_months: Optional[int] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Get portfolio metrics only (lighter endpoint)."""
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    # Get returns for each fund
    fund_returns_dict = {}
    for fund_name in allocations.keys():
        returns = get_fund_returns_by_name(
            fund_name,
            cache.fund_metrics,
            cache.fund_details,
            period_months
        )
        if returns is not None:
            fund_returns_dict[fund_name] = returns
    
    if not fund_returns_dict:
        raise HTTPException(status_code=404, detail="No valid returns data found")
    
    # Calculate portfolio returns
    portfolio_returns = calculate_portfolio_returns(fund_returns_dict, allocations)
    
    if portfolio_returns is None or len(portfolio_returns) < 10:
        raise HTTPException(status_code=500, detail="Insufficient data")
    
    return {
        'total_return': float((1 + portfolio_returns).prod() - 1),
        'annualized_return': float(PortfolioMetrics.annualized_return(portfolio_returns)),
        'volatility': float(PortfolioMetrics.volatility(portfolio_returns)),
        'sharpe_ratio': float(PortfolioMetrics.sharpe_ratio(portfolio_returns)),
        'max_drawdown': float(PortfolioMetrics.max_drawdown(portfolio_returns)),
        'var_95': float(PortfolioMetrics.var(portfolio_returns, 0.95)),
        'cvar_95': float(PortfolioMetrics.cvar(portfolio_returns, 0.95)),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SAVED PORTFOLIOS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/saved/{user_id}")
async def get_saved_portfolios(user_id: str):
    """Get list of saved portfolios for a user."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = client.table("portfolios").select(
            "portfolio_name, created_at, updated_at"
        ).eq("user_id", user_id).execute()
        
        portfolios = [
            {
                'portfolio_name': row['portfolio_name'],
                'created_at': row.get('created_at'),
                'updated_at': row.get('updated_at'),
            }
            for row in result.data
        ]
        
        return {'portfolios': portfolios}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved/{user_id}/{portfolio_name}")
async def get_saved_portfolio(user_id: str, portfolio_name: str):
    """Load a specific saved portfolio."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = client.table("portfolios").select("*").eq(
            "user_id", user_id
        ).eq(
            "portfolio_name", portfolio_name
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        row = result.data[0]
        
        return SavedPortfolio(
            portfolio_name=row['portfolio_name'],
            user_id=row['user_id'],
            allocations=row.get('allocations', {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save/{user_id}")
async def save_portfolio(
    user_id: str,
    request: SavePortfolioRequest
):
    """Save a portfolio configuration."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        data = {
            'portfolio_name': request.portfolio_name,
            'user_id': user_id,
            'allocations': request.allocations,
            'updated_at': datetime.now().isoformat(),
        }
        
        result = client.table("portfolios").upsert(
            data,
            on_conflict='portfolio_name,user_id'
        ).execute()
        
        return {'success': True, 'message': f"Portfolio '{request.portfolio_name}' saved"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved/{user_id}/{portfolio_name}")
async def delete_portfolio(user_id: str, portfolio_name: str):
    """Delete a saved portfolio."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        client.table("portfolios").delete().eq(
            "user_id", user_id
        ).eq(
            "portfolio_name", portfolio_name
        ).execute()
        
        return {'success': True, 'message': f"Portfolio '{portfolio_name}' deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO OPTIMIZATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/optimize")
async def optimize_portfolio(
    request: OptimizationRequest,
    cache: DataCache = Depends(get_data_cache)
):
    """
    Optimize portfolio using mean-variance or DRO optimization.
    """
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    # Get returns for all funds
    returns_dict = {}
    for fund_name in request.fund_names:
        returns = get_fund_returns_by_name(
            fund_name,
            cache.fund_metrics,
            cache.fund_details,
            period_months=36  # Use 3 years for optimization
        )
        if returns is not None and len(returns) >= 252:  # At least 1 year
            returns_dict[fund_name] = returns
    
    if len(returns_dict) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 funds with sufficient data for optimization"
        )
    
    # Build returns matrix
    returns_df = pd.DataFrame(returns_dict).dropna()
    
    if len(returns_df) < 252:
        raise HTTPException(status_code=400, detail="Insufficient overlapping data")
    
    fund_names = list(returns_df.columns)
    n_assets = len(fund_names)
    
    # Calculate expected returns and covariance
    mean_returns = returns_df.mean() * 252  # Annualized
    cov_matrix = returns_df.cov() * 252  # Annualized
    
    # Simple mean-variance optimization (maximize Sharpe)
    from scipy.optimize import minimize
    
    def neg_sharpe(weights):
        port_return = np.dot(weights, mean_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        if port_vol == 0:
            return 0
        return -port_return / port_vol
    
    # Constraints
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Weights sum to 1
    ]
    
    # Bounds
    min_weight = request.constraints.min_weight if request.constraints else 0.0
    max_weight = request.constraints.max_weight if request.constraints else 1.0
    bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
    
    # Initial guess (equal weights)
    initial_weights = np.array([1.0 / n_assets] * n_assets)
    
    # Optimize
    result = minimize(
        neg_sharpe,
        initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000}
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail="Optimization failed to converge")
    
    optimal_weights = result.x
    
    # Filter small weights
    threshold = 0.01  # 1%
    optimal_weights[optimal_weights < threshold] = 0
    optimal_weights = optimal_weights / optimal_weights.sum()  # Renormalize
    
    # Calculate resulting metrics
    opt_return = np.dot(optimal_weights, mean_returns)
    opt_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
    opt_sharpe = opt_return / opt_vol if opt_vol > 0 else 0
    
    # Build result
    weights_dict = {
        fund_names[i]: float(optimal_weights[i])
        for i in range(n_assets)
        if optimal_weights[i] > 0
    }
    
    return OptimizationResult(
        weights=weights_dict,
        expected_return=float(opt_return),
        expected_risk=float(opt_vol),
        sharpe_ratio=float(opt_sharpe),
        status="success",
        iterations=result.nit,
    )
