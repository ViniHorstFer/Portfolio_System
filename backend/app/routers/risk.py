"""
Risk monitoring API endpoints.
Handles risk metrics calculation and saved monitor configurations.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import gaussian_kde

from app.dependencies import get_data_cache, get_supabase, DataCache
from app.models import (
    RiskMonitorRequest,
    RiskMonitorResponse,
    FundRiskData,
    RiskMetrics,
    FlowMetrics,
    SavedMonitor,
    DistributionData,
    FrequencyType,
)
from app.core import (
    get_fund_returns,
    get_returns_for_frequency,
    calculate_risk_metrics,
    calculate_fund_flow_metrics,
    standardize_cnpj,
    PortfolioMetrics,
)

router = APIRouter(prefix="/risk", tags=["risk"])


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_distribution_data(
    returns: pd.Series,
    frequency: str
) -> Optional[dict]:
    """Calculate KDE and risk metrics for distribution chart."""
    if returns is None or len(returns) < 20:
        return None
    
    returns_clean = returns.dropna()
    
    try:
        # Calculate KDE
        kde = gaussian_kde(returns_clean)
        x_range = np.linspace(
            returns_clean.min() - returns_clean.std(),
            returns_clean.max() + returns_clean.std(),
            200
        )
        kde_y = kde(x_range)
        
        return {
            'returns': returns_clean.tolist(),
            'kde_x': x_range.tolist(),
            'kde_y': kde_y.tolist(),
            'var_95': float(np.percentile(returns_clean, 5)),
            'var_5': float(np.percentile(returns_clean, 95)),
            'cvar_95': float(returns_clean[returns_clean <= np.percentile(returns_clean, 5)].mean()),
            'cvar_5': float(returns_clean[returns_clean >= np.percentile(returns_clean, 95)].mean()),
            'latest_return': float(returns_clean.iloc[-1]),
        }
    except Exception as e:
        print(f"Error calculating distribution: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# RISK MONITOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/monitor")
async def get_risk_monitor_data(
    request: RiskMonitorRequest,
    cache: DataCache = Depends(get_data_cache)
):
    """
    Calculate risk metrics for a list of funds.
    Returns comprehensive data for Summary, Returns, and Flows views.
    """
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    results = []
    
    for fund_name in request.fund_names:
        # Get fund info
        fund_row = cache.fund_metrics[
            cache.fund_metrics['FUNDO DE INVESTIMENTO'] == fund_name
        ]
        
        if len(fund_row) == 0:
            continue
        
        row = fund_row.iloc[0]
        subcategory = row.get('SUBCATEGORIA BTG', 'Other')
        if pd.isna(subcategory) or subcategory == '-' or subcategory == '':
            subcategory = 'Multimercado'
        
        # Get CNPJ
        cnpj_standard = row.get('CNPJ_STANDARD')
        if pd.isna(cnpj_standard) and 'CNPJ' in row.index:
            cnpj_standard = standardize_cnpj(row['CNPJ'])
        
        fund_data = FundRiskData(
            fund_name=fund_name,
            subcategory=subcategory,
        )
        
        # Get returns and calculate risk metrics
        if cnpj_standard:
            returns_result = get_fund_returns(cache.fund_details, cnpj_standard)
            
            if returns_result is not None:
                daily_returns = returns_result[0]
                
                # Daily metrics (1-day returns)
                daily_tuple = get_returns_for_frequency(daily_returns, 'daily')
                daily_metrics = calculate_risk_metrics(daily_tuple[0])
                if daily_metrics:
                    fund_data.daily = RiskMetrics(
                        return_value=daily_metrics.get('return'),
                        var_95=daily_metrics.get('var_95'),
                        var_5=daily_metrics.get('var_5'),
                        cvar_95=daily_metrics.get('cvar_95'),
                        cvar_5=daily_metrics.get('cvar_5'),
                        z_score=daily_metrics.get('z_score'),
                    )
                    # Store returns for distribution chart
                    fund_data.daily_returns = daily_tuple[0].dropna().tolist()[-500:]  # Last 500 points
                
                # Weekly metrics (5-day rolling)
                weekly_tuple = get_returns_for_frequency(daily_returns, 'weekly')
                weekly_metrics = calculate_risk_metrics(weekly_tuple[0])
                if weekly_metrics:
                    fund_data.weekly = RiskMetrics(
                        return_value=weekly_metrics.get('return'),
                        var_95=weekly_metrics.get('var_95'),
                        var_5=weekly_metrics.get('var_5'),
                        cvar_95=weekly_metrics.get('cvar_95'),
                        cvar_5=weekly_metrics.get('cvar_5'),
                        z_score=weekly_metrics.get('z_score'),
                    )
                    fund_data.weekly_returns = weekly_tuple[0].dropna().tolist()[-500:]
                
                # Monthly metrics (22-day rolling)
                monthly_tuple = get_returns_for_frequency(daily_returns, 'monthly')
                monthly_metrics = calculate_risk_metrics(monthly_tuple[0])
                if monthly_metrics:
                    fund_data.monthly = RiskMetrics(
                        return_value=monthly_metrics.get('return'),
                        var_95=monthly_metrics.get('var_95'),
                        var_5=monthly_metrics.get('var_5'),
                        cvar_95=monthly_metrics.get('cvar_95'),
                        cvar_5=monthly_metrics.get('cvar_5'),
                        z_score=monthly_metrics.get('z_score'),
                    )
                    fund_data.monthly_returns = monthly_tuple[0].dropna().tolist()[-500:]
            
            # Calculate flow metrics
            flow_metrics = calculate_fund_flow_metrics(cache.fund_details, cnpj_standard)
            if flow_metrics:
                fund_data.flows = FlowMetrics(**flow_metrics)
        
        results.append(fund_data)
    
    return RiskMonitorResponse(
        funds=results,
        updated_at=datetime.now().isoformat()
    )


@router.post("/monitor/distribution")
async def get_distribution_data(
    fund_name: str,
    frequency: FrequencyType,
    cache: DataCache = Depends(get_data_cache)
):
    """Get distribution chart data for a specific fund and frequency."""
    if cache.fund_metrics is None or cache.fund_details is None:
        raise HTTPException(status_code=503, detail="Fund data not loaded")
    
    # Get fund CNPJ
    fund_row = cache.fund_metrics[
        cache.fund_metrics['FUNDO DE INVESTIMENTO'] == fund_name
    ]
    
    if len(fund_row) == 0:
        raise HTTPException(status_code=404, detail=f"Fund '{fund_name}' not found")
    
    row = fund_row.iloc[0]
    cnpj_standard = row.get('CNPJ_STANDARD')
    if pd.isna(cnpj_standard) and 'CNPJ' in row.index:
        cnpj_standard = standardize_cnpj(row['CNPJ'])
    
    if not cnpj_standard:
        raise HTTPException(status_code=404, detail="CNPJ not found for fund")
    
    # Get returns
    returns_result = get_fund_returns(cache.fund_details, cnpj_standard)
    if returns_result is None:
        raise HTTPException(status_code=404, detail="Returns not found")
    
    daily_returns = returns_result[0]
    
    # Get frequency-specific returns
    returns_tuple = get_returns_for_frequency(daily_returns, frequency.value)
    
    # Calculate distribution data
    dist_data = calculate_distribution_data(returns_tuple[0], frequency.value)
    
    if dist_data is None:
        raise HTTPException(status_code=404, detail="Insufficient data for distribution")
    
    return DistributionData(
        fund_name=fund_name,
        frequency=frequency,
        **dist_data
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SAVED MONITORS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/monitor/saved/{user_id}")
async def get_saved_monitors(user_id: str):
    """Get list of saved risk monitor configurations for a user."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = client.table("risk_monitor_funds").select(
            "monitor_name, created_at, updated_at"
        ).eq("user_id", user_id).execute()
        
        monitors = []
        seen = set()
        
        for row in result.data:
            name = row['monitor_name']
            if name not in seen:
                monitors.append({
                    'monitor_name': name,
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                })
                seen.add(name)
        
        return {'monitors': monitors}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/saved/{user_id}/{monitor_name}")
async def get_saved_monitor(user_id: str, monitor_name: str):
    """Load a specific saved risk monitor configuration."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = client.table("risk_monitor_funds").select("*").eq(
            "user_id", user_id
        ).eq(
            "monitor_name", monitor_name
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        row = result.data[0]
        
        return SavedMonitor(
            monitor_name=row['monitor_name'],
            user_id=row['user_id'],
            funds=row.get('funds_list', []),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/save")
async def save_monitor(
    monitor_name: str,
    user_id: str,
    funds: List[str]
):
    """Save a risk monitor configuration."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        data = {
            'monitor_name': monitor_name,
            'user_id': user_id,
            'funds_list': funds,
            'updated_at': datetime.now().isoformat(),
        }
        
        result = client.table("risk_monitor_funds").upsert(
            data,
            on_conflict='monitor_name,user_id'
        ).execute()
        
        return {'success': True, 'message': f"Monitor '{monitor_name}' saved"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/monitor/saved/{user_id}/{monitor_name}")
async def delete_monitor(user_id: str, monitor_name: str):
    """Delete a saved risk monitor configuration."""
    client = get_supabase()
    
    if client is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        client.table("risk_monitor_funds").delete().eq(
            "user_id", user_id
        ).eq(
            "monitor_name", monitor_name
        ).execute()
        
        return {'success': True, 'message': f"Monitor '{monitor_name}' deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
