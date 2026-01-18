"""
Demo data generator for testing deployment.
Creates sample fund data when no external data source is available.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_demo_fund_metrics(n_funds: int = 50) -> pd.DataFrame:
    """Generate demo fund metrics data."""
    np.random.seed(42)
    
    categories = ['Renda Fixa', 'Multimercado', 'Ações', 'Cambial']
    subcategories = {
        'Renda Fixa': ['Pós-Fixado', 'Inflação', 'Crédito Privado', 'Duration'],
        'Multimercado': ['Macro', 'Long Short', 'Quantitativo', 'Livre'],
        'Ações': ['Long Only', 'Small Caps', 'Dividendos', 'Value'],
        'Cambial': ['Dólar', 'Euro', 'Cesta'],
    }
    
    liquidity_options = ['D+0', 'D+1', 'D+5', 'D+10', 'D+30', 'D+60']
    
    funds = []
    for i in range(n_funds):
        category = np.random.choice(categories)
        subcategory = np.random.choice(subcategories[category])
        
        # Generate realistic metrics
        base_return = np.random.normal(0.12, 0.08)  # 12% mean, 8% std
        volatility = abs(np.random.normal(0.08, 0.05))  # 8% mean volatility
        
        fund = {
            'FUNDO DE INVESTIMENTO': f'Fundo Demo {i+1:03d} - {subcategory}',
            'CNPJ': f'{np.random.randint(10, 99)}.{np.random.randint(100, 999)}.{np.random.randint(100, 999)}/0001-{np.random.randint(10, 99)}',
            'CNPJ_STANDARD': f'{np.random.randint(10000000000000, 99999999999999)}',
            'CATEGORIA BTG': category,
            'SUBCATEGORIA BTG': subcategory,
            'VL_PATRIM_LIQ': np.random.exponential(500_000_000),  # AUM
            'NR_COTST': np.random.randint(100, 50000),  # Shareholders
            'LIQUIDEZ': np.random.choice(liquidity_options),
            'LIQUIDEZ_DAYS': int(np.random.choice([0, 1, 5, 10, 30, 60])),
            'RETURN_12M': base_return,
            'RETURN_24M': base_return * 1.8 + np.random.normal(0, 0.05),
            'RETURN_36M': base_return * 2.5 + np.random.normal(0, 0.08),
            'VOL_12M': volatility,
            'SHARPE_12M': base_return / volatility if volatility > 0 else 0,
            'MDD': -abs(np.random.exponential(0.08)),  # Max Drawdown
            'EXCESS_12M': base_return - 0.10,  # vs CDI
            'EXCESS_24M': (base_return * 1.8) - 0.20,
            'BEST_MONTH': abs(np.random.normal(0.03, 0.02)),
            'WORST_MONTH': -abs(np.random.normal(0.02, 0.015)),
            'INCEPTION_DATE': datetime.now() - timedelta(days=np.random.randint(365, 3650)),
        }
        funds.append(fund)
    
    return pd.DataFrame(funds)


def generate_demo_fund_details(fund_metrics: pd.DataFrame, days: int = 756) -> pd.DataFrame:
    """Generate demo daily fund data."""
    np.random.seed(42)
    
    all_data = []
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')  # Business days
    
    for _, fund in fund_metrics.iterrows():
        cnpj_standard = fund['CNPJ_STANDARD']
        base_aum = fund['VL_PATRIM_LIQ']
        base_shareholders = fund['NR_COTST']
        volatility = fund['VOL_12M'] / np.sqrt(252)  # Daily vol
        
        # Generate daily returns
        returns = np.random.normal(0.0004, volatility, days)  # ~10% annual return
        
        # Generate quota values
        quota = 100 * np.exp(np.cumsum(returns))
        
        # Generate AUM with some drift
        aum_noise = np.random.normal(0, 0.02, days).cumsum()
        aum = base_aum * (1 + aum_noise)
        
        # Generate shareholders
        shareholders = (base_shareholders * (1 + np.random.normal(0, 0.01, days).cumsum())).astype(int)
        shareholders = np.maximum(shareholders, 10)
        
        # Generate movements (fund flows)
        movements = np.random.normal(0, base_aum * 0.01, days)
        
        for j, date in enumerate(dates):
            all_data.append({
                'DT_COMPTC': date,
                'CNPJ_STANDARD': cnpj_standard,
                'VL_QUOTA': quota[j],
                'VL_PATRIM_LIQ': aum[j],
                'NR_COTST': shareholders[j],
                'MOVIMENTACAO': movements[j],
                'DAILY_RETURN': returns[j],
            })
    
    df = pd.DataFrame(all_data)
    df = df.set_index('DT_COMPTC')
    return df


def generate_demo_benchmarks(days: int = 756) -> pd.DataFrame:
    """Generate demo benchmark data."""
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    
    # CDI - low volatility, ~10% annual
    cdi_returns = np.random.normal(0.0004, 0.0001, days)
    
    # IBOV - higher volatility, ~12% annual
    ibov_returns = np.random.normal(0.0005, 0.01, days)
    
    # IHFA - medium volatility
    ihfa_returns = np.random.normal(0.00045, 0.004, days)
    
    df = pd.DataFrame({
        'CDI': cdi_returns,
        'IBOV': ibov_returns,
        'IHFA': ihfa_returns,
    }, index=dates)
    
    return df


def load_demo_data():
    """Load all demo data."""
    print("Generating demo data...")
    
    fund_metrics = generate_demo_fund_metrics(50)
    fund_details = generate_demo_fund_details(fund_metrics, 756)
    benchmarks = generate_demo_benchmarks(756)
    
    print(f"Generated {len(fund_metrics)} funds with {len(fund_details)} daily records")
    
    return {
        'fund_metrics': fund_metrics,
        'fund_details': fund_details,
        'benchmarks': benchmarks,
    }
