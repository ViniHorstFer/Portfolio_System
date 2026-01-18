"""
Portfolio metrics calculations.
Migrated from the original Streamlit components.py.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar
from typing import Optional, Tuple, List, Dict, Any


class PortfolioMetrics:
    """
    Class containing all portfolio metric calculation methods.
    All methods are static for easy use across the application.
    """
    
    @staticmethod
    def cumulative_returns(returns: pd.Series) -> pd.Series:
        """Calculate cumulative returns from a series of returns."""
        return (1 + returns).cumprod() - 1
    
    @staticmethod
    def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate annualized return."""
        if len(returns) == 0:
            return 0.0
        total_return = (1 + returns).prod() - 1
        n_periods = len(returns)
        years = n_periods / periods_per_year
        if years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / years) - 1
    
    @staticmethod
    def volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate annualized volatility."""
        if len(returns) < 2:
            return 0.0
        return returns.std() * np.sqrt(periods_per_year)
    
    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, 
                     periods_per_year: int = 252) -> float:
        """Calculate Sharpe ratio."""
        ann_ret = PortfolioMetrics.annualized_return(returns, periods_per_year)
        ann_vol = PortfolioMetrics.volatility(returns, periods_per_year)
        if ann_vol == 0:
            return 0.0
        return (ann_ret - risk_free_rate) / ann_vol
    
    @staticmethod
    def max_drawdown(returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        if len(returns) == 0:
            return 0.0
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    @staticmethod
    def underwater_series(returns: pd.Series) -> pd.Series:
        """Calculate underwater (drawdown) series."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        return (cumulative - running_max) / running_max
    
    @staticmethod
    def var(returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)."""
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)
    
    @staticmethod
    def cvar(returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR / Expected Shortfall)."""
        if len(returns) == 0:
            return 0.0
        var_value = PortfolioMetrics.var(returns, confidence)
        return returns[returns <= var_value].mean()
    
    @staticmethod
    def var_upper(returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate upper VaR (best returns threshold)."""
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, confidence * 100)
    
    @staticmethod
    def cvar_upper(returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate upper CVaR (expected gain in best scenarios)."""
        if len(returns) == 0:
            return 0.0
        var_upper = PortfolioMetrics.var_upper(returns, confidence)
        return returns[returns >= var_upper].mean()
    
    @staticmethod
    def omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
        """
        Calculate Omega ratio.
        Ratio of probability-weighted gains to probability-weighted losses.
        """
        if len(returns) == 0:
            return 1.0
        
        excess = returns - threshold
        gains = excess[excess > 0].sum()
        losses = abs(excess[excess < 0].sum())
        
        if losses == 0:
            return float('inf') if gains > 0 else 1.0
        
        return gains / losses
    
    @staticmethod
    def rachev_ratio(returns: pd.Series, alpha: float = 0.05) -> float:
        """
        Calculate Rachev ratio.
        Ratio of expected gain in best alpha% to expected loss in worst alpha%.
        """
        if len(returns) == 0:
            return 1.0
        
        upper_threshold = np.percentile(returns, (1 - alpha) * 100)
        lower_threshold = np.percentile(returns, alpha * 100)
        
        expected_gain = returns[returns >= upper_threshold].mean()
        expected_loss = abs(returns[returns <= lower_threshold].mean())
        
        if expected_loss == 0:
            return float('inf') if expected_gain > 0 else 1.0
        
        return expected_gain / expected_loss
    
    @staticmethod
    def sortino_ratio(returns: pd.Series, target_return: float = 0.0,
                      periods_per_year: int = 252) -> float:
        """Calculate Sortino ratio using downside deviation."""
        if len(returns) < 2:
            return 0.0
        
        ann_ret = PortfolioMetrics.annualized_return(returns, periods_per_year)
        
        # Calculate downside deviation
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            return float('inf') if ann_ret > target_return else 0.0
        
        downside_std = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(periods_per_year)
        
        if downside_std == 0:
            return float('inf') if ann_ret > target_return else 0.0
        
        return (ann_ret - target_return) / downside_std
    
    @staticmethod
    def calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate Calmar ratio (annualized return / max drawdown)."""
        ann_ret = PortfolioMetrics.annualized_return(returns, periods_per_year)
        mdd = abs(PortfolioMetrics.max_drawdown(returns))
        
        if mdd == 0:
            return float('inf') if ann_ret > 0 else 0.0
        
        return ann_ret / mdd
    
    @staticmethod
    def rolling_sharpe(returns: pd.Series, window: int = 252,
                       risk_free_rate: float = 0.0) -> pd.Series:
        """Calculate rolling Sharpe ratio."""
        def calc_sharpe(r):
            if len(r) < 2:
                return np.nan
            ann_ret = (1 + r.mean()) ** 252 - 1
            ann_vol = r.std() * np.sqrt(252)
            if ann_vol == 0:
                return np.nan
            return (ann_ret - risk_free_rate) / ann_vol
        
        return returns.rolling(window=window).apply(calc_sharpe, raw=False)
    
    @staticmethod
    def rolling_volatility(returns: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling volatility."""
        return returns.rolling(window=window).std() * np.sqrt(252)
    
    @staticmethod
    def information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate Information Ratio."""
        if len(returns) == 0 or len(benchmark_returns) == 0:
            return 0.0
        
        # Align series
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) < 2:
            return 0.0
        
        excess_returns = aligned.iloc[:, 0] - aligned.iloc[:, 1]
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        if tracking_error == 0:
            return 0.0
        
        return excess_returns.mean() * 252 / tracking_error
    
    @staticmethod
    def beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta relative to benchmark."""
        if len(returns) == 0 or len(benchmark_returns) == 0:
            return 1.0
        
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) < 2:
            return 1.0
        
        covariance = aligned.cov().iloc[0, 1]
        benchmark_variance = aligned.iloc[:, 1].var()
        
        if benchmark_variance == 0:
            return 1.0
        
        return covariance / benchmark_variance
    
    @staticmethod
    def alpha(returns: pd.Series, benchmark_returns: pd.Series,
              risk_free_rate: float = 0.0) -> float:
        """Calculate Jensen's alpha."""
        if len(returns) == 0 or len(benchmark_returns) == 0:
            return 0.0
        
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) < 2:
            return 0.0
        
        beta_value = PortfolioMetrics.beta(returns, benchmark_returns)
        
        port_return = PortfolioMetrics.annualized_return(aligned.iloc[:, 0])
        bench_return = PortfolioMetrics.annualized_return(aligned.iloc[:, 1])
        
        return port_return - (risk_free_rate + beta_value * (bench_return - risk_free_rate))
    
    @staticmethod
    def z_score(value: float, mean: float, std: float) -> float:
        """Calculate z-score."""
        if std == 0:
            return 0.0
        return (value - mean) / std
    
    @staticmethod
    def monthly_returns(daily_returns: pd.Series) -> pd.Series:
        """Aggregate daily returns to monthly."""
        return daily_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
    
    @staticmethod
    def weekly_returns(daily_returns: pd.Series) -> pd.Series:
        """Aggregate daily returns to weekly."""
        return daily_returns.resample('W').apply(lambda x: (1 + x).prod() - 1)


def calculate_portfolio_returns(
    fund_returns_dict: Dict[str, pd.Series],
    weights: Dict[str, float]
) -> Optional[pd.Series]:
    """
    Calculate weighted portfolio returns.
    
    Args:
        fund_returns_dict: Dictionary of fund_name -> returns series
        weights: Dictionary of fund_name -> weight (should sum to 1.0 or be normalized)
    
    Returns:
        Portfolio returns series
    """
    if not fund_returns_dict or not weights:
        return None
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight == 0:
        return None
    
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Align all returns to common dates
    returns_df = pd.DataFrame(fund_returns_dict)
    returns_df = returns_df.dropna()
    
    if len(returns_df) == 0:
        return None
    
    # Calculate weighted returns
    portfolio_returns = pd.Series(0.0, index=returns_df.index)
    
    for fund_name, weight in normalized_weights.items():
        if fund_name in returns_df.columns:
            portfolio_returns += returns_df[fund_name] * weight
    
    return portfolio_returns


def get_returns_for_frequency(
    daily_returns: pd.Series,
    frequency: str
) -> Tuple[pd.Series, float, float, float]:
    """
    Get returns for specified frequency with statistics.
    
    Args:
        daily_returns: Daily returns series
        frequency: 'daily', 'weekly', or 'monthly'
    
    Returns:
        Tuple of (returns_series, mean, std, latest_return)
    """
    if frequency == 'daily':
        returns = daily_returns
    elif frequency == 'weekly':
        returns = daily_returns.rolling(window=5).apply(
            lambda x: (1 + x).prod() - 1, raw=False
        ).dropna()
    elif frequency == 'monthly':
        returns = daily_returns.rolling(window=22).apply(
            lambda x: (1 + x).prod() - 1, raw=False
        ).dropna()
    else:
        returns = daily_returns
    
    if len(returns) == 0:
        return returns, 0.0, 0.0, 0.0
    
    mean = returns.mean()
    std = returns.std()
    latest = returns.iloc[-1] if len(returns) > 0 else 0.0
    
    return returns, mean, std, latest


def calculate_risk_metrics(returns: pd.Series) -> Dict[str, Any]:
    """
    Calculate comprehensive risk metrics for a returns series.
    
    Args:
        returns: Returns series (daily, weekly, or monthly)
    
    Returns:
        Dictionary of risk metrics
    """
    if returns is None or len(returns) == 0:
        return None
    
    returns_clean = returns.dropna()
    if len(returns_clean) < 10:
        return None
    
    latest_return = returns_clean.iloc[-1]
    mean = returns_clean.mean()
    std = returns_clean.std()
    
    return {
        'return': latest_return,
        'mean': mean,
        'std': std,
        'z_score': (latest_return - mean) / std if std > 0 else 0.0,
        'var_95': PortfolioMetrics.var(returns_clean, 0.95),
        'var_5': PortfolioMetrics.var_upper(returns_clean, 0.95),
        'cvar_95': PortfolioMetrics.cvar(returns_clean, 0.95),
        'cvar_5': PortfolioMetrics.cvar_upper(returns_clean, 0.95),
        'min': returns_clean.min(),
        'max': returns_clean.max(),
        'skewness': returns_clean.skew(),
        'kurtosis': returns_clean.kurtosis(),
    }
