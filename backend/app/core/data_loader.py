"""
Data loading utilities.
Handles loading fund data from various sources (Supabase, GitHub, local files).
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import io
import httpx

from app.config import settings
from app.dependencies import get_supabase, data_cache


# ═══════════════════════════════════════════════════════════════════════════════
# GITHUB DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

async def load_from_github_releases(
    repo: str,
    asset_name: str,
    token: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Load data file from GitHub Releases.
    
    Args:
        repo: Repository in format 'owner/repo'
        asset_name: Name of the asset file (e.g., 'fund_metrics.pkl')
        token: GitHub token for private repos
    
    Returns:
        DataFrame loaded from the asset
    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'token {token}'
        
        async with httpx.AsyncClient() as client:
            # Get latest release
            api_url = f'https://api.github.com/repos/{repo}/releases/latest'
            response = await client.get(api_url, headers=headers)
            
            if response.status_code != 200:
                print(f"Failed to get releases: {response.status_code}")
                return None
            
            release_data = response.json()
            
            # Find the asset
            asset_url = None
            for asset in release_data.get('assets', []):
                if asset['name'] == asset_name:
                    asset_url = asset['browser_download_url']
                    break
            
            if not asset_url:
                print(f"Asset {asset_name} not found in release")
                return None
            
            # Download asset
            response = await client.get(asset_url, headers=headers, follow_redirects=True)
            
            if response.status_code != 200:
                print(f"Failed to download asset: {response.status_code}")
                return None
            
            # Load based on file type
            content = io.BytesIO(response.content)
            
            if asset_name.endswith('.pkl'):
                return pd.read_pickle(content)
            elif asset_name.endswith('.xlsx'):
                return pd.read_excel(content)
            elif asset_name.endswith('.csv'):
                return pd.read_csv(content)
            else:
                print(f"Unsupported file type: {asset_name}")
                return None
                
    except Exception as e:
        print(f"Error loading from GitHub: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def load_fund_metrics() -> Optional[pd.DataFrame]:
    """Load fund metrics data."""
    # Check cache first
    if data_cache.fund_metrics is not None:
        return data_cache.fund_metrics
    
    # Try GitHub Releases
    if settings.github_repo and settings.github_token:
        df = await load_from_github_releases(
            settings.github_repo,
            'fund_metrics.pkl',
            settings.github_token
        )
        if df is not None:
            data_cache.fund_metrics = df
            return df
    
    # Fallback to demo data
    print("No external data source configured, using demo data...")
    from app.core.demo_data import load_demo_data
    demo = load_demo_data()
    data_cache.fund_metrics = demo['fund_metrics']
    data_cache.fund_details = demo['fund_details']
    data_cache.benchmarks = demo['benchmarks']
    return data_cache.fund_metrics


async def load_fund_details() -> Optional[pd.DataFrame]:
    """Load fund details (daily data)."""
    if data_cache.fund_details is not None:
        return data_cache.fund_details
    
    if settings.github_repo and settings.github_token:
        df = await load_from_github_releases(
            settings.github_repo,
            'fund_details.pkl',
            settings.github_token
        )
        if df is not None:
            data_cache.fund_details = df
            return df
    
    # Demo data would have been loaded by load_fund_metrics
    if data_cache.fund_details is None:
        await load_fund_metrics()  # This will load demo data
    
    return data_cache.fund_details


async def load_benchmarks() -> Optional[pd.DataFrame]:
    """Load benchmark data."""
    if data_cache.benchmarks is not None:
        return data_cache.benchmarks
    
    if settings.github_repo and settings.github_token:
        df = await load_from_github_releases(
            settings.github_repo,
            'benchmarks.pkl',
            settings.github_token
        )
        if df is not None:
            data_cache.benchmarks = df
            return df
    
    # Demo data would have been loaded by load_fund_metrics
    if data_cache.benchmarks is None:
        await load_fund_metrics()  # This will load demo data
    
    return data_cache.benchmarks


async def load_all_data() -> Dict[str, Optional[pd.DataFrame]]:
    """Load all data files."""
    return {
        'fund_metrics': await load_fund_metrics(),
        'fund_details': await load_fund_details(),
        'benchmarks': await load_benchmarks(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FUND DATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def standardize_cnpj(cnpj: str) -> Optional[str]:
    """Standardize CNPJ format."""
    if cnpj is None:
        return None
    
    # Remove all non-numeric characters
    cnpj_clean = ''.join(filter(str.isdigit, str(cnpj)))
    
    if len(cnpj_clean) == 14:
        return cnpj_clean
    elif len(cnpj_clean) < 14:
        return cnpj_clean.zfill(14)
    else:
        return cnpj_clean[:14]


def get_fund_returns(
    fund_details: pd.DataFrame,
    cnpj_standard: str,
    period_months: Optional[int] = None
) -> Optional[Tuple[pd.Series, pd.Series]]:
    """
    Get daily returns for a fund.
    
    Args:
        fund_details: DataFrame with daily fund data
        cnpj_standard: Standardized CNPJ
        period_months: Optional period filter in months
    
    Returns:
        Tuple of (filtered_returns, full_returns) or None
    """
    if fund_details is None or cnpj_standard is None:
        return None
    
    # Check for CNPJ_STANDARD column
    if 'CNPJ_STANDARD' not in fund_details.columns:
        # Try to create it
        if 'CNPJ' in fund_details.columns:
            fund_details['CNPJ_STANDARD'] = fund_details['CNPJ'].apply(standardize_cnpj)
        else:
            return None
    
    # Filter by CNPJ
    fund_data = fund_details[fund_details['CNPJ_STANDARD'] == cnpj_standard]
    
    if len(fund_data) == 0:
        return None
    
    # Get returns column
    returns_col = None
    for col in ['DAILY_RETURN', 'RENTABILIDADE', 'RETURN', 'RET']:
        if col in fund_data.columns:
            returns_col = col
            break
    
    if returns_col is None:
        # Try to calculate from quota
        quota_col = None
        for col in ['VL_QUOTA', 'QUOTA', 'NAV']:
            if col in fund_data.columns:
                quota_col = col
                break
        
        if quota_col is None:
            return None
        
        # Ensure date index
        if not isinstance(fund_data.index, pd.DatetimeIndex):
            date_col = fund_data.columns[0]
            fund_data = fund_data.set_index(date_col)
            fund_data.index = pd.to_datetime(fund_data.index)
        
        fund_data = fund_data.sort_index()
        returns = fund_data[quota_col].pct_change().dropna()
    else:
        # Use existing returns column
        if not isinstance(fund_data.index, pd.DatetimeIndex):
            date_col = fund_data.columns[0]
            fund_data = fund_data.set_index(date_col)
            fund_data.index = pd.to_datetime(fund_data.index)
        
        fund_data = fund_data.sort_index()
        returns = fund_data[returns_col].dropna()
    
    # Remove duplicates
    returns = returns[~returns.index.duplicated(keep='first')]
    
    if len(returns) == 0:
        return None
    
    # Filter by period
    if period_months is not None:
        cutoff_date = returns.index[-1] - pd.DateOffset(months=period_months)
        filtered_returns = returns[returns.index >= cutoff_date]
    else:
        filtered_returns = returns
    
    return filtered_returns, returns


def get_fund_returns_by_name(
    fund_name: str,
    fund_metrics: pd.DataFrame,
    fund_details: pd.DataFrame,
    period_months: Optional[int] = None
) -> Optional[pd.Series]:
    """
    Get fund returns by fund name.
    
    Args:
        fund_name: Name of the fund
        fund_metrics: Fund metrics DataFrame
        fund_details: Fund details DataFrame
        period_months: Optional period filter
    
    Returns:
        Returns series or None
    """
    if fund_metrics is None or fund_details is None:
        return None
    
    # Find fund row
    fund_row = fund_metrics[fund_metrics['FUNDO DE INVESTIMENTO'] == fund_name]
    
    if len(fund_row) == 0:
        return None
    
    # Get CNPJ
    cnpj = None
    if 'CNPJ_STANDARD' in fund_row.columns:
        cnpj = fund_row['CNPJ_STANDARD'].iloc[0]
    elif 'CNPJ' in fund_row.columns:
        cnpj = standardize_cnpj(fund_row['CNPJ'].iloc[0])
    
    if cnpj is None:
        return None
    
    # Get returns
    result = get_fund_returns(fund_details, cnpj, period_months)
    
    if result is None:
        return None
    
    return result[0]  # Return filtered returns


# ═══════════════════════════════════════════════════════════════════════════════
# FUND FLOW CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_fund_flow_metrics(
    fund_details: pd.DataFrame,
    cnpj_standard: str
) -> Optional[Dict[str, Any]]:
    """
    Calculate fund flow metrics (AUM changes, shareholder changes).
    
    Args:
        fund_details: Fund details DataFrame
        cnpj_standard: Standardized CNPJ
    
    Returns:
        Dictionary of flow metrics
    """
    if fund_details is None or cnpj_standard is None:
        return None
    
    # Filter fund data
    if 'CNPJ_STANDARD' in fund_details.columns:
        fund_data = fund_details[fund_details['CNPJ_STANDARD'] == cnpj_standard].copy()
    else:
        return None
    
    if len(fund_data) == 0:
        return None
    
    # Ensure date index
    if not isinstance(fund_data.index, pd.DatetimeIndex):
        date_col = fund_data.columns[0]
        fund_data = fund_data.reset_index()
        fund_data[date_col] = pd.to_datetime(fund_data[date_col])
        fund_data = fund_data.set_index(date_col)
    
    # Handle duplicates
    if 'NR_COTST' in fund_data.columns:
        fund_data = fund_data.sort_values('NR_COTST', ascending=False)
        fund_data = fund_data[~fund_data.index.duplicated(keep='first')]
    
    fund_data = fund_data.sort_index()
    
    if len(fund_data) < 2:
        return None
    
    # Check required columns
    has_aum = 'VL_PATRIM_LIQ' in fund_data.columns
    has_shareholders = 'NR_COTST' in fund_data.columns
    has_transfers = 'MOVIMENTACAO' in fund_data.columns
    
    if not has_aum and not has_shareholders:
        return None
    
    # Current values
    current_aum = fund_data['VL_PATRIM_LIQ'].iloc[-1] if has_aum else None
    current_shareholders = int(fund_data['NR_COTST'].iloc[-1]) if has_shareholders else None
    
    # Daily variations
    daily_transfers = fund_data['MOVIMENTACAO'].iloc[-1] if has_transfers else 0
    daily_investors_change = (
        fund_data['NR_COTST'].iloc[-1] - fund_data['NR_COTST'].iloc[-2]
    ) if has_shareholders and len(fund_data) >= 2 else 0
    
    # Weekly variations (last 5 days)
    if len(fund_data) >= 5 and has_transfers:
        weekly_transfers = fund_data['MOVIMENTACAO'].iloc[-5:].sum()
    else:
        weekly_transfers = daily_transfers
    
    if len(fund_data) >= 6 and has_shareholders:
        weekly_investors_change = fund_data['NR_COTST'].iloc[-1] - fund_data['NR_COTST'].iloc[-6]
    else:
        weekly_investors_change = daily_investors_change
    
    # Monthly variations (last 22 days)
    if len(fund_data) >= 22 and has_transfers:
        monthly_transfers = fund_data['MOVIMENTACAO'].iloc[-22:].sum()
    else:
        monthly_transfers = weekly_transfers
    
    if len(fund_data) >= 23 and has_shareholders:
        monthly_investors_change = fund_data['NR_COTST'].iloc[-1] - fund_data['NR_COTST'].iloc[-23]
    else:
        monthly_investors_change = weekly_investors_change
    
    # Calculate percentages
    def safe_pct(value, base):
        if base and base != 0:
            return (value / base) * 100
        return 0
    
    return {
        'aum': current_aum,
        'shareholders': current_shareholders,
        'daily_transfers': daily_transfers,
        'daily_transfers_pct': safe_pct(daily_transfers, current_aum),
        'daily_investors': int(daily_investors_change) if daily_investors_change else 0,
        'daily_investors_pct': safe_pct(daily_investors_change, current_shareholders),
        'weekly_transfers': weekly_transfers,
        'weekly_transfers_pct': safe_pct(weekly_transfers, current_aum),
        'weekly_investors': int(weekly_investors_change) if weekly_investors_change else 0,
        'weekly_investors_pct': safe_pct(weekly_investors_change, current_shareholders),
        'monthly_transfers': monthly_transfers,
        'monthly_transfers_pct': safe_pct(monthly_transfers, current_aum),
        'monthly_investors': int(monthly_investors_change) if monthly_investors_change else 0,
        'monthly_investors_pct': safe_pct(monthly_investors_change, current_shareholders),
    }
