import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from sklearn.decomposition import PCA
from typing import Dict, List, Optional, Tuple, Union
from datetime import date, datetime, timedelta
import asyncio
import structlog
from dataclasses import dataclass
from enum import Enum

from models.database import RiskCalculation, Position, MarketData, Instrument
from core.database import get_db_session
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


class RiskMethodology(Enum):
    """Risk calculation methodologies"""
    HISTORICAL_SIMULATION = "historical"
    MONTE_CARLO = "monte_carlo"
    PARAMETRIC = "parametric"
    EXTREME_VALUE_THEORY = "evt"


class StressScenario(Enum):
    """Predefined stress test scenarios"""
    FINANCIAL_CRISIS_2008 = "2008_financial_crisis"
    COVID19_SHOCK = "covid19_shock"
    EUROPEAN_SOVEREIGN = "european_sovereign_crisis"
    INTEREST_RATE_SHOCK = "interest_rate_shock"
    CREDIT_SPREAD_WIDENING = "credit_spread_widening"
    EQUITY_CRASH = "equity_crash"
    FX_VOLATILITY_SPIKE = "fx_volatility_spike"


@dataclass
class RiskMetrics:
    """Container for calculated risk metrics"""
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    expected_shortfall_95: Optional[float] = None
    expected_shortfall_99: Optional[float] = None
    incremental_risk_charge: Optional[float] = None
    comprehensive_risk_measure: Optional[float] = None
    stress_test_results: Optional[Dict[str, float]] = None
    component_var: Optional[Dict[str, float]] = None
    portfolio_volatility: Optional[float] = None
    maximum_drawdown: Optional[float] = None


@dataclass
class PortfolioData:
    """Portfolio data for risk calculations"""
    positions: pd.DataFrame
    market_data: pd.DataFrame
    instruments: pd.DataFrame
    business_date: date


class RiskCalculationEngine:
    """Basel 2.5 compliant risk calculation engine"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logger.bind(component="RiskEngine")
        
        # Basel 2.5 parameters
        self.confidence_levels = [0.95, 0.99]
        self.holding_period = 1  # days
        self.lookback_period = 250  # trading days
        self.min_observations = 125  # minimum for valid calculation
        
        # Stress test scenarios (market shocks in %)
        self.stress_scenarios = {
            StressScenario.FINANCIAL_CRISIS_2008: {
                'equity': -0.35,
                'credit_spread': 0.03,
                'fx_volatility': 2.0,
                'interest_rate': -0.02
            },
            StressScenario.COVID19_SHOCK: {
                'equity': -0.30,
                'credit_spread': 0.025,
                'fx_volatility': 1.8,
                'oil': -0.60
            },
            StressScenario.EUROPEAN_SOVEREIGN: {
                'government_bond': 0.02,
                'credit_spread': 0.015,
                'euro_fx': -0.15
            },
            StressScenario.INTEREST_RATE_SHOCK: {
                'interest_rate': 0.02,
                'bond': -0.08,
                'bank_equity': -0.12
            }
        }

    async def calculate_portfolio_risk(
        self,
        portfolio_id: str,
        business_date: date,
        methodologies: List[RiskMethodology] = None,
        confidence_levels: List[float] = None
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a portfolio
        
        Args:
            portfolio_id: Portfolio identifier
            business_date: Calculation date
            methodologies: Risk calculation methods to use
            confidence_levels: Confidence levels for VaR/ES calculation
            
        Returns:
            RiskMetrics object with calculated values
        """
        self.logger.info(
            "Starting portfolio risk calculation",
            portfolio_id=portfolio_id,
            business_date=business_date
        )
        
        if methodologies is None:
            methodologies = [RiskMethodology.HISTORICAL_SIMULATION]
        
        if confidence_levels is None:
            confidence_levels = self.confidence_levels
        
        try:
            # Load portfolio data
            portfolio_data = await self._load_portfolio_data(portfolio_id, business_date)
            
            # Calculate returns time series
            returns = await self._calculate_returns(portfolio_data)
            
            # Initialize risk metrics
            risk_metrics = RiskMetrics()
            
            # Calculate VaR and Expected Shortfall
            for methodology in methodologies:
                var_results, es_results = await self._calculate_var_es(
                    returns, methodology, confidence_levels
                )
                
                # Store results based on confidence levels
                if 0.95 in confidence_levels:
                    risk_metrics.var_95 = var_results.get(0.95)
                    risk_metrics.expected_shortfall_95 = es_results.get(0.95)
                
                if 0.99 in confidence_levels:
                    risk_metrics.var_99 = var_results.get(0.99)
                    risk_metrics.expected_shortfall_99 = es_results.get(0.99)
            
            # Calculate stress test results
            risk_metrics.stress_test_results = await self._calculate_stress_tests(
                portfolio_data, returns
            )
            
            # Calculate component VaR
            risk_metrics.component_var = await self._calculate_component_var(
                portfolio_data, returns
            )
            
            # Calculate additional metrics
            risk_metrics.portfolio_volatility = np.std(returns) * np.sqrt(252)
            risk_metrics.maximum_drawdown = self._calculate_max_drawdown(returns)
            
            # Basel 2.5 specific calculations
            if await self._has_credit_instruments(portfolio_data):
                risk_metrics.incremental_risk_charge = await self._calculate_irc(
                    portfolio_data
                )
            
            if await self._has_correlation_trading(portfolio_data):
                risk_metrics.comprehensive_risk_measure = await self._calculate_crm(
                    portfolio_data, returns
                )
            
            self.logger.info(
                "Portfolio risk calculation completed",
                portfolio_id=portfolio_id,
                var_99=risk_metrics.var_99,
                es_99=risk_metrics.expected_shortfall_99
            )
            
            return risk_metrics
            
        except Exception as e:
            self.logger.error(
                "Risk calculation failed",
                portfolio_id=portfolio_id,
                error=str(e),
                exc_info=True
            )
            raise

    async def _load_portfolio_data(self, portfolio_id: str, business_date: date) -> PortfolioData:
        """Load portfolio positions and market data"""
        async with get_db_session() as session:
            # Load positions
            positions_query = session.query(Position).filter(
                Position.portfolio_id == portfolio_id,
                Position.business_date == business_date
            )
            positions_df = pd.read_sql(positions_query.statement, session.bind)
            
            # Load instruments
            instrument_ids = positions_df['instrument_id'].unique()
            instruments_query = session.query(Instrument).filter(
                Instrument.id.in_(instrument_ids)
            )
            instruments_df = pd.read_sql(instruments_query.statement, session.bind)
            
            # Load historical market data
            end_date = business_date
            start_date = end_date - timedelta(days=self.lookback_period + 50)  # Buffer for holidays
            
            market_data_query = session.query(MarketData).filter(
                MarketData.instrument_id.in_(instrument_ids),
                MarketData.business_date.between(start_date, end_date),
                MarketData.data_type == 'price'
            ).order_by(MarketData.business_date)
            
            market_data_df = pd.read_sql(market_data_query.statement, session.bind)
            
            return PortfolioData(
                positions=positions_df,
                market_data=market_data_df,
                instruments=instruments_df,
                business_date=business_date
            )

    async def _calculate_returns(self, portfolio_data: PortfolioData) -> pd.Series:
        """Calculate portfolio P&L time series"""
        # Pivot market data to get price matrix
        price_matrix = portfolio_data.market_data.pivot(
            index='business_date',
            columns='instrument_id',
            values='value'
        ).fillna(method='ffill')
        
        # Calculate returns
        returns_matrix = price_matrix.pct_change().dropna()
        
        # Get position weights on calculation date
        positions = portfolio_data.positions.set_index('instrument_id')
        
        # Calculate portfolio returns
        portfolio_returns = []
        for date_idx, returns_row in returns_matrix.iterrows():
            portfolio_return = 0
            total_value = positions['market_value'].sum()
            
            for instrument_id, instrument_return in returns_row.items():
                if instrument_id in positions.index and not pd.isna(instrument_return):
                    weight = positions.loc[instrument_id, 'market_value'] / total_value
                    portfolio_return += weight * instrument_return
            
            portfolio_returns.append(portfolio_return)
        
        return pd.Series(portfolio_returns, index=returns_matrix.index)

    async def _calculate_var_es(
        self,
        returns: pd.Series,
        methodology: RiskMethodology,
        confidence_levels: List[float]
    ) -> Tuple[Dict[float, float], Dict[float, float]]:
        """Calculate VaR and Expected Shortfall"""
        
        var_results = {}
        es_results = {}
        
        if len(returns) < self.min_observations:
            self.logger.warning(
                "Insufficient data for reliable VaR calculation",
                observations=len(returns),
                minimum_required=self.min_observations
            )
            return var_results, es_results
        
        for confidence_level in confidence_levels:
            if methodology == RiskMethodology.HISTORICAL_SIMULATION:
                var, es = self._historical_simulation_var_es(returns, confidence_level)
            elif methodology == RiskMethodology.MONTE_CARLO:
                var, es = await self._monte_carlo_var_es(returns, confidence_level)
            elif methodology == RiskMethodology.PARAMETRIC:
                var, es = self._parametric_var_es(returns, confidence_level)
            elif methodology == RiskMethodology.EXTREME_VALUE_THEORY:
                var, es = self._evt_var_es(returns, confidence_level)
            else:
                raise ValueError(f"Unknown methodology: {methodology}")
            
            var_results[confidence_level] = var
            es_results[confidence_level] = es
        
        return var_results, es_results

    def _historical_simulation_var_es(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> Tuple[float, float]:
        """Historical simulation VaR and Expected Shortfall"""
        # Sort returns in ascending order
        sorted_returns = np.sort(returns.values)
        
        # Calculate VaR
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(sorted_returns, var_percentile)
        
        # Calculate Expected Shortfall (average of tail losses)
        tail_losses = sorted_returns[sorted_returns <= var]
        es = np.mean(tail_losses) if len(tail_losses) > 0 else var
        
        return abs(var), abs(es)

    async def _monte_carlo_var_es(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> Tuple[float, float]:
        """Monte Carlo simulation VaR and Expected Shortfall"""
        # Fit returns to normal distribution
        mu = np.mean(returns)
        sigma = np.std(returns)
        
        # Generate scenarios
        num_simulations = self.settings.MAX_MONTE_CARLO_SIMULATIONS
        scenarios = np.random.normal(mu, sigma, num_simulations)
        
        # Calculate VaR and ES
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(scenarios, var_percentile)
        
        tail_losses = scenarios[scenarios <= var]
        es = np.mean(tail_losses) if len(tail_losses) > 0 else var
        
        return abs(var), abs(es)

    def _parametric_var_es(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> Tuple[float, float]:
        """Parametric (Delta-Normal) VaR and Expected Shortfall"""
        mu = np.mean(returns)
        sigma = np.std(returns)
        
        # Calculate VaR using normal distribution
        z_score = stats.norm.ppf(1 - confidence_level)
        var = abs(mu + z_score * sigma)
        
        # Calculate Expected Shortfall
        # ES = μ + σ * φ(z) / (1 - α) where φ is the standard normal PDF
        phi_z = stats.norm.pdf(z_score)
        es = abs(mu + sigma * phi_z / (1 - confidence_level))
        
        return var, es

    def _evt_var_es(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> Tuple[float, float]:
        """Extreme Value Theory VaR and Expected Shortfall"""
        # Use Generalized Pareto Distribution for tail modeling
        # This is a simplified implementation
        
        # Define threshold (e.g., 10th percentile)
        threshold = np.percentile(returns, 10)
        exceedances = returns[returns < threshold] - threshold
        
        if len(exceedances) < 10:
            # Fall back to historical simulation if insufficient tail data
            return self._historical_simulation_var_es(returns, confidence_level)
        
        # Fit GPD parameters (simplified method)
        shape = 0.1  # Simplified assumption
        scale = np.std(exceedances)
        
        # Calculate VaR and ES using GPD
        n = len(returns)
        n_u = len(exceedances)
        
        var_prob = (1 - confidence_level) * n / n_u
        var = threshold + (scale / shape) * (var_prob ** (-shape) - 1)
        
        es = (var + scale - shape * threshold) / (1 - shape)
        
        return abs(var), abs(es)

    async def _calculate_stress_tests(
        self,
        portfolio_data: PortfolioData,
        returns: pd.Series
    ) -> Dict[str, float]:
        """Calculate stress test scenarios"""
        stress_results = {}
        
        for scenario, shocks in self.stress_scenarios.items():
            portfolio_shock = await self._apply_stress_scenario(
                portfolio_data, shocks
            )
            stress_results[scenario.value] = portfolio_shock
        
        return stress_results

    async def _apply_stress_scenario(
        self,
        portfolio_data: PortfolioData,
        shocks: Dict[str, float]
    ) -> float:
        """Apply stress scenario to portfolio"""
        total_shock = 0
        total_value = portfolio_data.positions['market_value'].sum()
        
        # Map instruments to risk factors
        for _, position in portfolio_data.positions.iterrows():
            instrument = portfolio_data.instruments[
                portfolio_data.instruments['id'] == position['instrument_id']
            ].iloc[0]
            
            # Determine applicable shock based on instrument type
            shock_factor = 0
            if instrument['instrument_type'] == 'equity':
                shock_factor = shocks.get('equity', 0)
            elif instrument['instrument_type'] == 'bond':
                shock_factor = shocks.get('bond', shocks.get('interest_rate', 0))
            elif instrument['instrument_type'] == 'fx':
                shock_factor = shocks.get('fx_volatility', 0)
            # Add more instrument type mappings as needed
            
            position_shock = position['market_value'] * shock_factor
            total_shock += position_shock
        
        return total_shock

    async def _calculate_component_var(
        self,
        portfolio_data: PortfolioData,
        returns: pd.Series
    ) -> Dict[str, float]:
        """Calculate component VaR for risk attribution"""
        component_vars = {}
        
        # This is a simplified implementation
        # In practice, you'd calculate marginal VaR for each position
        
        total_value = portfolio_data.positions['market_value'].sum()
        portfolio_var = abs(np.percentile(returns, 1))  # 99% VaR
        
        for _, position in portfolio_data.positions.iterrows():
            weight = position['market_value'] / total_value
            # Simplified: component VaR proportional to weight
            component_vars[position['instrument_id']] = portfolio_var * weight
        
        return component_vars

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        return abs(drawdown.min())

    async def _has_credit_instruments(self, portfolio_data: PortfolioData) -> bool:
        """Check if portfolio contains credit instruments"""
        credit_types = ['bond', 'credit_default_swap', 'loan']
        return any(
            portfolio_data.instruments['instrument_type'].isin(credit_types)
        )

    async def _has_correlation_trading(self, portfolio_data: PortfolioData) -> bool:
        """Check if portfolio has correlation trading positions"""
        # Simplified check - in practice would be more sophisticated
        return len(portfolio_data.positions) > 5  # Multiple positions

    async def _calculate_irc(self, portfolio_data: PortfolioData) -> float:
        """Calculate Incremental Risk Charge for credit portfolios"""
        # Simplified IRC calculation
        # In practice, this would involve complex credit migration modeling
        
        credit_positions = portfolio_data.positions[
            portfolio_data.positions['instrument_id'].isin(
                portfolio_data.instruments[
                    portfolio_data.instruments['instrument_type'].isin(['bond'])
                ]['id']
            )
        ]
        
        total_credit_exposure = credit_positions['market_value'].sum()
        
        # Simplified: 1% of credit exposure as IRC
        return total_credit_exposure * 0.01

    async def _calculate_crm(
        self,
        portfolio_data: PortfolioData,
        returns: pd.Series
    ) -> float:
        """Calculate Comprehensive Risk Measure for correlation trading"""
        # Simplified CRM calculation
        # In practice, this would involve sophisticated correlation modeling
        
        # Use a multiple of VaR as a proxy for CRM
        var_99 = abs(np.percentile(returns, 1))
        crm_multiplier = 3.0  # Regulatory multiplier
        
        return var_99 * crm_multiplier


# Risk calculation service functions
class RiskCalculationService:
    """Service for managing risk calculations"""
    
    def __init__(self):
        self.engine = RiskCalculationEngine()
        self.logger = logger.bind(component="RiskCalculationService")

    async def calculate_and_store_risk(
        self,
        portfolio_id: str,
        business_date: date,
        calculation_types: List[str] = None,
        methodology: RiskMethodology = RiskMethodology.HISTORICAL_SIMULATION
    ) -> List[RiskCalculation]:
        """Calculate risk metrics and store in database"""
        
        if calculation_types is None:
            calculation_types = ['var', 'es', 'stress']
        
        # Calculate risk metrics
        risk_metrics = await self.engine.calculate_portfolio_risk(
            portfolio_id, business_date, [methodology]
        )
        
        # Store results in database
        risk_calculations = []
        async with get_db_session() as session:
            # VaR calculations
            if 'var' in calculation_types:
                if risk_metrics.var_99 is not None:
                    var_calc = RiskCalculation(
                        portfolio_id=portfolio_id,
                        business_date=business_date,
                        calculation_type='var',
                        methodology=methodology.value,
                        confidence_level=0.99,
                        holding_period=1,
                        risk_value=risk_metrics.var_99,
                        currency='USD',  # Should be dynamic
                        status='completed'
                    )
                    session.add(var_calc)
                    risk_calculations.append(var_calc)
            
            # Expected Shortfall calculations
            if 'es' in calculation_types:
                if risk_metrics.expected_shortfall_99 is not None:
                    es_calc = RiskCalculation(
                        portfolio_id=portfolio_id,
                        business_date=business_date,
                        calculation_type='es',
                        methodology=methodology.value,
                        confidence_level=0.99,
                        holding_period=1,
                        risk_value=risk_metrics.expected_shortfall_99,
                        currency='USD',
                        status='completed'
                    )
                    session.add(es_calc)
                    risk_calculations.append(es_calc)
            
            # Stress test calculations
            if 'stress' in calculation_types and risk_metrics.stress_test_results:
                for scenario, value in risk_metrics.stress_test_results.items():
                    stress_calc = RiskCalculation(
                        portfolio_id=portfolio_id,
                        business_date=business_date,
                        calculation_type='stress',
                        methodology=methodology.value,
                        risk_value=abs(value),
                        currency='USD',
                        scenario_name=scenario,
                        status='completed'
                    )
                    session.add(stress_calc)
                    risk_calculations.append(stress_calc)
            
            await session.commit()
        
        self.logger.info(
            "Risk calculations stored",
            portfolio_id=portfolio_id,
            business_date=business_date,
            calculations_count=len(risk_calculations)
        )
        
        return risk_calculations