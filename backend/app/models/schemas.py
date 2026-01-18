"""
Pydantic models for request/response validation.
These define the API contract between frontend and backend.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class FrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class PeriodType(str, Enum):
    M3 = "3M"
    M6 = "6M"
    M12 = "12M"
    M24 = "24M"
    M36 = "36M"
    ALL = "All"


# ═══════════════════════════════════════════════════════════════════════════════
# FUND MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class FundBasic(BaseModel):
    """Basic fund information for listings."""
    name: str = Field(..., alias="FUNDO DE INVESTIMENTO")
    cnpj: Optional[str] = Field(None, alias="CNPJ")
    category: Optional[str] = Field(None, alias="CATEGORIA BTG")
    subcategory: Optional[str] = Field(None, alias="SUBCATEGORIA BTG")
    aum: Optional[float] = Field(None, alias="VL_PATRIM_LIQ")
    shareholders: Optional[int] = Field(None, alias="NR_COTST")
    liquidity: Optional[str] = Field(None, alias="LIQUIDEZ")
    
    class Config:
        populate_by_name = True


class FundMetrics(BaseModel):
    """Complete fund metrics for detailed analysis."""
    name: str
    cnpj: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    
    # Returns
    return_12m: Optional[float] = None
    return_24m: Optional[float] = None
    return_36m: Optional[float] = None
    
    # Risk metrics
    volatility_12m: Optional[float] = None
    sharpe_12m: Optional[float] = None
    max_drawdown: Optional[float] = None
    
    # Excess returns
    excess_12m: Optional[float] = None
    excess_24m: Optional[float] = None
    
    # Fund info
    aum: Optional[float] = None
    shareholders: Optional[int] = None
    liquidity: Optional[str] = None
    liquidity_days: Optional[int] = None
    inception_date: Optional[str] = None


class FundReturns(BaseModel):
    """Fund returns time series."""
    fund_name: str
    dates: List[str]
    returns: List[float]
    cumulative_returns: List[float]


class FundFilter(BaseModel):
    """Filters for fund search."""
    categories: Optional[List[str]] = None
    subcategories: Optional[List[str]] = None
    min_sharpe: Optional[float] = None
    max_sharpe: Optional[float] = None
    min_return_12m: Optional[float] = None
    max_return_12m: Optional[float] = None
    min_aum: Optional[float] = None
    max_aum: Optional[float] = None
    max_mdd: Optional[float] = None
    min_liquidity_days: Optional[int] = None
    max_liquidity_days: Optional[int] = None
    search_text: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# RISK MONITOR MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class RiskMetrics(BaseModel):
    """Risk metrics for a single frequency."""
    return_value: Optional[float] = Field(None, alias="return")
    var_95: Optional[float] = None
    var_5: Optional[float] = None
    cvar_95: Optional[float] = None
    cvar_5: Optional[float] = None
    z_score: Optional[float] = None
    
    class Config:
        populate_by_name = True


class FlowMetrics(BaseModel):
    """Fund flow metrics."""
    aum: Optional[float] = None
    shareholders: Optional[int] = None
    daily_transfers: Optional[float] = None
    daily_transfers_pct: Optional[float] = None
    daily_investors: Optional[int] = None
    daily_investors_pct: Optional[float] = None
    weekly_transfers: Optional[float] = None
    weekly_transfers_pct: Optional[float] = None
    weekly_investors: Optional[int] = None
    weekly_investors_pct: Optional[float] = None
    monthly_transfers: Optional[float] = None
    monthly_transfers_pct: Optional[float] = None
    monthly_investors: Optional[int] = None
    monthly_investors_pct: Optional[float] = None


class FundRiskData(BaseModel):
    """Complete risk data for a fund."""
    fund_name: str
    subcategory: Optional[str] = None
    daily: Optional[RiskMetrics] = None
    weekly: Optional[RiskMetrics] = None
    monthly: Optional[RiskMetrics] = None
    flows: Optional[FlowMetrics] = None
    
    # For distribution charts
    daily_returns: Optional[List[float]] = None
    weekly_returns: Optional[List[float]] = None
    monthly_returns: Optional[List[float]] = None


class RiskMonitorRequest(BaseModel):
    """Request for risk monitor data."""
    fund_names: List[str]


class RiskMonitorResponse(BaseModel):
    """Response with risk monitor data."""
    funds: List[FundRiskData]
    updated_at: str


class SavedMonitor(BaseModel):
    """Saved risk monitor configuration."""
    monitor_name: str
    user_id: str
    funds: List[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class PortfolioAllocation(BaseModel):
    """Single fund allocation in portfolio."""
    fund_name: str
    weight: float  # 0.0 to 1.0


class PortfolioRequest(BaseModel):
    """Request for portfolio analysis."""
    allocations: List[PortfolioAllocation]
    period_months: Optional[int] = None


class PortfolioMetricsResponse(BaseModel):
    """Portfolio performance metrics."""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    omega_ratio: Optional[float] = None
    rachev_ratio: Optional[float] = None


class PortfolioReturns(BaseModel):
    """Portfolio returns time series."""
    dates: List[str]
    returns: List[float]
    cumulative_returns: List[float]
    benchmark_cumulative: Optional[Dict[str, List[float]]] = None


class CategoryBreakdown(BaseModel):
    """Portfolio breakdown by category."""
    category: str
    weight: float


class LiquidityBreakdown(BaseModel):
    """Portfolio breakdown by liquidity."""
    liquidity: str
    weight: float
    days: int


class PortfolioAnalysis(BaseModel):
    """Complete portfolio analysis response."""
    metrics: PortfolioMetricsResponse
    returns: PortfolioReturns
    category_breakdown: List[CategoryBreakdown]
    subcategory_breakdown: List[CategoryBreakdown]
    fund_breakdown: List[PortfolioAllocation]
    liquidity_breakdown: List[LiquidityBreakdown]
    average_liquidity_days: int


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO OPTIMIZATION MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class OptimizationConstraints(BaseModel):
    """Constraints for portfolio optimization."""
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_funds: Optional[int] = None
    category_constraints: Optional[Dict[str, Dict[str, float]]] = None


class OptimizationRequest(BaseModel):
    """Request for portfolio optimization."""
    fund_names: List[str]
    constraints: Optional[OptimizationConstraints] = None
    risk_aversion: float = 1.0
    radius: float = 0.1  # Wasserstein ball radius


class OptimizationResult(BaseModel):
    """Result of portfolio optimization."""
    weights: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    status: str
    iterations: Optional[int] = None


# ═══════════════════════════════════════════════════════════════════════════════
# SAVED PORTFOLIO MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class SavedPortfolio(BaseModel):
    """Saved portfolio configuration."""
    portfolio_name: str
    user_id: str
    allocations: Dict[str, float]  # fund_name -> weight
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SavePortfolioRequest(BaseModel):
    """Request to save a portfolio."""
    portfolio_name: str
    allocations: Dict[str, float]


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class BenchmarkInfo(BaseModel):
    """Benchmark information."""
    name: str
    dates: List[str]
    returns: List[float]
    cumulative_returns: List[float]


class BenchmarkList(BaseModel):
    """List of available benchmarks."""
    benchmarks: List[str]


# ═══════════════════════════════════════════════════════════════════════════════
# MONTHLY RETURNS MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class MonthlyReturn(BaseModel):
    """Single month return."""
    year: int
    month: int
    return_value: float
    benchmark_value: Optional[float] = None
    excess: Optional[float] = None


class MonthlyReturnsTable(BaseModel):
    """Monthly returns calendar data."""
    fund_name: str
    data: List[MonthlyReturn]
    ytd_by_year: Dict[int, float]
    total_return: float


# ═══════════════════════════════════════════════════════════════════════════════
# CHART DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ChartDataPoint(BaseModel):
    """Single data point for charts."""
    date: str
    value: float
    label: Optional[str] = None


class DistributionData(BaseModel):
    """Data for distribution charts."""
    fund_name: str
    frequency: FrequencyType
    returns: List[float]
    kde_x: List[float]
    kde_y: List[float]
    var_95: float
    var_5: float
    cvar_95: float
    cvar_5: float
    latest_return: float


# ═══════════════════════════════════════════════════════════════════════════════
# API RESPONSE WRAPPERS
# ═══════════════════════════════════════════════════════════════════════════════

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class User(BaseModel):
    """User information."""
    id: str
    username: str
    role: str = "viewer"  # viewer, banker, trader, manager, admin


class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    user: User
    token: str
