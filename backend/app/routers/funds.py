"""
Fund-related API endpoints.
Handles fund listing, filtering, details, and returns.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
import pandas as pd
import numpy as np

from app.dependencies import get_data_cache, DataCache
from app.models import (
    FundBasic,
    FundMetrics,
    FundReturns,
    FundFilter,
    APIResponse,
    PaginatedResponse,
)
from app.core import (
    get_fund_returns_by_name,
    PortfolioMetrics,
    standardize_cnpj,
)

router = APIRouter(prefix="/funds", tags=["funds"])


# ═══════════════════════════════════════════════════════════════════════════════
# FUND LISTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/")
async def get_funds(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    min_sharpe: Optional[float] = None,
    max_mdd: Optional[float] = None,
    min_aum: Optional[float] = None,
    max_liquidity_days: Optional[int] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=200),
    sort_by: Optional[str] = None,
    sort_desc: bool = True,
    cache: DataCache = Depends(get_data_cache),
):
    """
    Get paginated list of funds with optional filters.
    """
    if cache.fund_metrics is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    df = cache.fund_metrics.copy()
    
    # Apply filters
    if category:
        df = df[df['CATEGORIA BTG'] == category]
    
    if subcategory:
        df = df[df['SUBCATEGORIA BTG'] == subcategory]
    
    if search:
        search_lower = search.lower()
        df = df[df['FUNDO DE INVESTIMENTO'].str.lower().str.contains(search_lower, na=False)]
    
    if min_sharpe is not None and 'SHARPE_12M' in df.columns:
        df = df[df['SHARPE_12M'] >= min_sharpe]
    
    if max_mdd is not None and 'MDD' in df.columns:
        df = df[df['MDD'] >= max_mdd]  # MDD is negative
    
    if min_aum is not None and 'VL_PATRIM_LIQ' in df.columns:
        df = df[df['VL_PATRIM_LIQ'] >= min_aum]
    
    if max_liquidity_days is not None and 'LIQUIDEZ_DAYS' in df.columns:
        df = df[df['LIQUIDEZ_DAYS'] <= max_liquidity_days]
    
    # Sort
    if sort_by and sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=not sort_desc)
    
    # Paginate
    total = len(df)
    total_pages = (total + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    df_page = df.iloc[start_idx:end_idx]
    
    # Convert to list of dicts
    funds = []
    for _, row in df_page.iterrows():
        fund = {
            'name': row.get('FUNDO DE INVESTIMENTO'),
            'cnpj': row.get('CNPJ'),
            'category': row.get('CATEGORIA BTG'),
            'subcategory': row.get('SUBCATEGORIA BTG'),
            'aum': row.get('VL_PATRIM_LIQ'),
            'shareholders': row.get('NR_COTST'),
            'liquidity': row.get('LIQUIDEZ'),
            'return_12m': row.get('RETURN_12M'),
            'sharpe_12m': row.get('SHARPE_12M'),
            'volatility_12m': row.get('VOL_12M'),
            'max_drawdown': row.get('MDD'),
        }
        funds.append(fund)
    
    return {
        'items': funds,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }


@router.get("/categories")
async def get_categories(cache: DataCache = Depends(get_data_cache)):
    """Get list of unique categories."""
    if cache.fund_metrics is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    categories = cache.fund_metrics['CATEGORIA BTG'].dropna().unique().tolist()
    return {'categories': sorted(categories)}


@router.get("/subcategories")
async def get_subcategories(
    category: Optional[str] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Get list of unique subcategories, optionally filtered by category."""
    if cache.fund_metrics is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    df = cache.fund_metrics
    
    if category:
        df = df[df['CATEGORIA BTG'] == category]
    
    subcategories = df['SUBCATEGORIA BTG'].dropna().unique().tolist()
    return {'subcategories': sorted(subcategories)}


@router.get("/names")
async def get_fund_names(
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    cache: DataCache = Depends(get_data_cache)
):
    """Get list of fund names for autocomplete."""
    if cache.fund_metrics is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    names = cache.fund_metrics['FUNDO DE INVESTIMENTO'].dropna().unique().tolist()
    
    if search:
        search_lower = search.lower()
        names = [n for n in names if search_lower in n.lower()]
    
    return {'names': sorted(names)[:limit]}


# ═══════════════════════════════════════════════════════════════════════════════
# FUND DETAIL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{fund_name}")
async def get_fund_detail(
    fund_name: str,
    cache: DataCache = Depends(get_data_cache)
):
    """Get detailed information for a specific fund."""
    if cache.fund_metrics is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    fund_row = cache.fund_metrics[
        cache.fund_metrics['FUNDO DE INVESTIMENTO'] == fund_name
    ]
    
    if len(fund_row) == 0:
        raise HTTPException(status_code=404, detail=f"Fund '{fund_name}' not found")
    
    row = fund_row.iloc[0]
    
    # Build response with all available metrics
    fund_data = {
        'name': fund_name,
        'cnpj': row.get('CNPJ'),
        'category': row.get('CATEGORIA BTG'),
        'subcategory': row.get('SUBCATEGORIA BTG'),
        'aum': row.get('VL_PATRIM_LIQ'),
        'shareholders': row.get('NR_COTST'),
        'liquidity': row.get('LIQUIDEZ'),
        'liquidity_days': row.get('LIQUIDEZ_DAYS'),
        'inception_date': str(row.get('INCEPTION_DATE')) if pd.notna(row.get('INCEPTION_DATE')) else None,
        
        # Returns
        'return_12m': row.get('RETURN_12M'),
        'return_24m': row.get('RETURN_24M'),
        'return_36m': row.get('RETURN_36M'),
        
        # Risk
        'volatility_12m': row.get('VOL_12M'),
        'sharpe_12m': row.get('SHARPE_12M'),
        'max_drawdown': row.get('MDD'),
        
        # Excess returns
        'excess_12m': row.get('EXCESS_12M'),
        'excess_24m': row.get('EXCESS_24M'),
        
        # Additional metrics
        'best_month': row.get('BEST_MONTH'),
        'worst_month': row.get('WORST_MONTH'),
    }
    
    return fund_data


@router.get("/{fund_name}/returns")
async def get_fund_returns_endpoint(
    fund_name: str,
    period_months: Optional[int] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Get returns time series for a fund."""
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    returns = get_fund_returns_by_name(
        fund_name,
        cache.fund_metrics,
        cache.fund_details,
        period_months
    )
    
    if returns is None:
        raise HTTPException(status_code=404, detail=f"Returns not found for '{fund_name}'")
    
    cumulative = PortfolioMetrics.cumulative_returns(returns)
    
    return {
        'fund_name': fund_name,
        'dates': [d.strftime('%Y-%m-%d') for d in returns.index],
        'returns': returns.tolist(),
        'cumulative_returns': cumulative.tolist(),
    }


@router.get("/{fund_name}/metrics")
async def get_fund_metrics_endpoint(
    fund_name: str,
    period_months: Optional[int] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Get calculated metrics for a fund."""
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    returns = get_fund_returns_by_name(
        fund_name,
        cache.fund_metrics,
        cache.fund_details,
        period_months
    )
    
    if returns is None or len(returns) < 10:
        raise HTTPException(status_code=404, detail=f"Insufficient data for '{fund_name}'")
    
    metrics = {
        'total_return': float((1 + returns).prod() - 1),
        'annualized_return': float(PortfolioMetrics.annualized_return(returns)),
        'volatility': float(PortfolioMetrics.volatility(returns)),
        'sharpe_ratio': float(PortfolioMetrics.sharpe_ratio(returns)),
        'max_drawdown': float(PortfolioMetrics.max_drawdown(returns)),
        'var_95': float(PortfolioMetrics.var(returns, 0.95)),
        'cvar_95': float(PortfolioMetrics.cvar(returns, 0.95)),
        'omega_ratio': float(PortfolioMetrics.omega_ratio(returns)),
        'sortino_ratio': float(PortfolioMetrics.sortino_ratio(returns)),
        'calmar_ratio': float(PortfolioMetrics.calmar_ratio(returns)),
    }
    
    return metrics


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARISON ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/compare")
async def compare_funds(
    fund_names: List[str],
    metrics: Optional[List[str]] = None,
    cache: DataCache = Depends(get_data_cache)
):
    """Compare multiple funds across selected metrics."""
    if cache.fund_metrics is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    if not metrics:
        metrics = [
            'RETURN_12M', 'VOL_12M', 'SHARPE_12M', 'MDD',
            'VL_PATRIM_LIQ', 'NR_COTST', 'LIQUIDEZ'
        ]
    
    result = []
    
    for name in fund_names:
        fund_row = cache.fund_metrics[
            cache.fund_metrics['FUNDO DE INVESTIMENTO'] == name
        ]
        
        if len(fund_row) > 0:
            row = fund_row.iloc[0]
            fund_data = {'name': name}
            
            for metric in metrics:
                if metric in row.index:
                    val = row[metric]
                    fund_data[metric] = val if pd.notna(val) else None
            
            result.append(fund_data)
    
    return {'comparison': result}
