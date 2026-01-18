"""
Benchmark-related API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List

from app.dependencies import get_data_cache, DataCache
from app.core import PortfolioMetrics

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.get("/")
async def get_benchmarks(cache: DataCache = Depends(get_data_cache)):
    """Get list of available benchmarks."""
    if cache.benchmarks is None:
        raise HTTPException(status_code=503, detail="Benchmark data not loaded")
    
    return {'benchmarks': cache.benchmarks.columns.tolist()}


@router.get("/{benchmark_name}")
async def get_benchmark_data(
    benchmark_name: str,
    period_months: Optional[int] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Get benchmark returns data."""
    if cache.benchmarks is None:
        raise HTTPException(status_code=503, detail="Benchmark data not loaded")
    
    if benchmark_name not in cache.benchmarks.columns:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_name}' not found")
    
    returns = cache.benchmarks[benchmark_name].dropna()
    
    if period_months:
        import pandas as pd
        cutoff = returns.index[-1] - pd.DateOffset(months=period_months)
        returns = returns[returns.index >= cutoff]
    
    cumulative = PortfolioMetrics.cumulative_returns(returns)
    
    return {
        'name': benchmark_name,
        'dates': [d.strftime('%Y-%m-%d') for d in returns.index],
        'returns': returns.tolist(),
        'cumulative_returns': cumulative.tolist(),
    }


@router.post("/compare")
async def compare_benchmarks(
    benchmark_names: List[str],
    period_months: Optional[int] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Compare multiple benchmarks."""
    if cache.benchmarks is None:
        raise HTTPException(status_code=503, detail="Benchmark data not loaded")
    
    result = {}
    
    for name in benchmark_names:
        if name not in cache.benchmarks.columns:
            continue
        
        returns = cache.benchmarks[name].dropna()
        
        if period_months:
            import pandas as pd
            cutoff = returns.index[-1] - pd.DateOffset(months=period_months)
            returns = returns[returns.index >= cutoff]
        
        if len(returns) > 0:
            cumulative = PortfolioMetrics.cumulative_returns(returns)
            result[name] = {
                'dates': [d.strftime('%Y-%m-%d') for d in returns.index],
                'cumulative_returns': cumulative.tolist(),
                'total_return': float((1 + returns).prod() - 1),
                'annualized_return': float(PortfolioMetrics.annualized_return(returns)),
                'volatility': float(PortfolioMetrics.volatility(returns)),
            }
    
    return result
