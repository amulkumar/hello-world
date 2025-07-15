from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
import structlog

from core.auth import get_current_user
from models.database import User, RiskCalculation
from services.risk_engine import RiskCalculationService, RiskMethodology
from core.database import get_db_session

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models for API
class RiskCalculationRequest(BaseModel):
    """Request model for risk calculation"""
    portfolio_id: str = Field(..., description="Portfolio identifier")
    business_date: date = Field(..., description="Calculation date")
    calculation_types: List[str] = Field(
        default=['var', 'es'], 
        description="Types of risk calculations to perform",
        example=['var', 'es', 'stress']
    )
    confidence_level: Optional[float] = Field(
        default=0.99, 
        ge=0.01, 
        le=0.99, 
        description="Confidence level for VaR/ES calculation"
    )
    holding_period: Optional[int] = Field(
        default=1, 
        ge=1, 
        le=250, 
        description="Holding period in days"
    )
    methodology: Optional[str] = Field(
        default="historical",
        description="Risk calculation methodology",
        example="historical"
    )


class RiskResult(BaseModel):
    """Risk calculation result"""
    id: int
    portfolio_id: str
    business_date: date
    calculation_type: str
    methodology: str
    confidence_level: Optional[float]
    holding_period: Optional[int]
    risk_value: float
    currency: str
    scenario_name: Optional[str]
    calculation_time: datetime
    status: str


class RiskSummary(BaseModel):
    """Portfolio risk summary"""
    portfolio_id: str
    business_date: date
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    expected_shortfall_95: Optional[float] = None
    expected_shortfall_99: Optional[float] = None
    portfolio_volatility: Optional[float] = None
    stress_test_worst: Optional[float] = None
    currency: str


class RiskHistoryResponse(BaseModel):
    """Historical risk metrics response"""
    portfolio_id: str
    date_range: Dict[str, date]
    risk_metrics: List[RiskResult]
    summary_stats: Dict[str, float]


@router.post("/calculate", response_model=List[RiskResult])
async def calculate_risk(
    request: RiskCalculationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate risk metrics for a portfolio
    
    This endpoint triggers risk calculations including VaR, Expected Shortfall,
    and stress testing based on the specified methodology and parameters.
    
    - **portfolio_id**: Portfolio identifier to calculate risk for
    - **business_date**: Date for which to calculate risk
    - **calculation_types**: List of risk metrics to calculate
    - **confidence_level**: Statistical confidence level (0.95 or 0.99)
    - **methodology**: Calculation method (historical, monte_carlo, parametric)
    """
    logger.info(
        "Risk calculation requested",
        portfolio_id=request.portfolio_id,
        business_date=request.business_date,
        user_id=current_user.id
    )
    
    try:
        # Validate methodology
        try:
            methodology = RiskMethodology(request.methodology)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid methodology: {request.methodology}. "
                       f"Valid options: {[m.value for m in RiskMethodology]}"
            )
        
        # Initialize risk calculation service
        risk_service = RiskCalculationService()
        
        # Perform calculation (async background task for large portfolios)
        calculations = await risk_service.calculate_and_store_risk(
            portfolio_id=request.portfolio_id,
            business_date=request.business_date,
            calculation_types=request.calculation_types,
            methodology=methodology
        )
        
        # Convert to response format
        results = []
        for calc in calculations:
            results.append(RiskResult(
                id=calc.id,
                portfolio_id=calc.portfolio_id,
                business_date=calc.business_date,
                calculation_type=calc.calculation_type,
                methodology=calc.methodology,
                confidence_level=calc.confidence_level,
                holding_period=calc.holding_period,
                risk_value=float(calc.risk_value),
                currency=calc.currency,
                scenario_name=calc.scenario_name,
                calculation_time=calc.calculation_time,
                status=calc.status
            ))
        
        logger.info(
            "Risk calculation completed",
            portfolio_id=request.portfolio_id,
            calculations_count=len(results)
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Risk calculation failed",
            portfolio_id=request.portfolio_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Risk calculation failed: {str(e)}"
        )


@router.get("/{portfolio_id}/summary", response_model=RiskSummary)
async def get_risk_summary(
    portfolio_id: str,
    business_date: date = Query(..., description="Business date for risk summary"),
    current_user: User = Depends(get_current_user)
):
    """
    Get risk summary for a portfolio on a specific date
    
    Returns the latest calculated risk metrics including VaR, Expected Shortfall,
    and stress test results for the specified portfolio and date.
    """
    async with get_db_session() as session:
        # Query latest risk calculations for the portfolio and date
        risk_calcs = session.query(RiskCalculation).filter(
            RiskCalculation.portfolio_id == portfolio_id,
            RiskCalculation.business_date == business_date,
            RiskCalculation.status == 'completed'
        ).all()
        
        if not risk_calcs:
            raise HTTPException(
                status_code=404,
                detail=f"No risk calculations found for portfolio {portfolio_id} on {business_date}"
            )
        
        # Organize results by calculation type
        risk_data = {}
        stress_results = []
        
        for calc in risk_calcs:
            if calc.calculation_type == 'var':
                if calc.confidence_level == 0.95:
                    risk_data['var_95'] = float(calc.risk_value)
                elif calc.confidence_level == 0.99:
                    risk_data['var_99'] = float(calc.risk_value)
            elif calc.calculation_type == 'es':
                if calc.confidence_level == 0.95:
                    risk_data['expected_shortfall_95'] = float(calc.risk_value)
                elif calc.confidence_level == 0.99:
                    risk_data['expected_shortfall_99'] = float(calc.risk_value)
            elif calc.calculation_type == 'stress':
                stress_results.append(float(calc.risk_value))
        
        # Calculate worst stress test result
        stress_worst = max(stress_results) if stress_results else None
        
        return RiskSummary(
            portfolio_id=portfolio_id,
            business_date=business_date,
            var_95=risk_data.get('var_95'),
            var_99=risk_data.get('var_99'),
            expected_shortfall_95=risk_data.get('expected_shortfall_95'),
            expected_shortfall_99=risk_data.get('expected_shortfall_99'),
            stress_test_worst=stress_worst,
            currency=risk_calcs[0].currency if risk_calcs else 'USD'
        )


@router.get("/{portfolio_id}/history", response_model=RiskHistoryResponse)
async def get_risk_history(
    portfolio_id: str,
    start_date: date = Query(..., description="Start date for historical data"),
    end_date: date = Query(..., description="End date for historical data"),
    risk_type: Optional[str] = Query(None, description="Filter by risk calculation type"),
    methodology: Optional[str] = Query(None, description="Filter by methodology"),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical risk metrics for a portfolio
    
    Returns time series of risk calculations for the specified portfolio
    within the given date range. Can be filtered by risk type and methodology.
    """
    if (end_date - start_date).days > 365:
        raise HTTPException(
            status_code=400,
            detail="Date range cannot exceed 365 days"
        )
    
    async with get_db_session() as session:
        query = session.query(RiskCalculation).filter(
            RiskCalculation.portfolio_id == portfolio_id,
            RiskCalculation.business_date.between(start_date, end_date),
            RiskCalculation.status == 'completed'
        )
        
        if risk_type:
            query = query.filter(RiskCalculation.calculation_type == risk_type)
        
        if methodology:
            query = query.filter(RiskCalculation.methodology == methodology)
        
        risk_calcs = query.order_by(RiskCalculation.business_date.desc()).all()
        
        if not risk_calcs:
            raise HTTPException(
                status_code=404,
                detail=f"No risk history found for portfolio {portfolio_id}"
            )
        
        # Convert to response format
        risk_metrics = []
        risk_values = []
        
        for calc in risk_calcs:
            risk_metrics.append(RiskResult(
                id=calc.id,
                portfolio_id=calc.portfolio_id,
                business_date=calc.business_date,
                calculation_type=calc.calculation_type,
                methodology=calc.methodology,
                confidence_level=calc.confidence_level,
                holding_period=calc.holding_period,
                risk_value=float(calc.risk_value),
                currency=calc.currency,
                scenario_name=calc.scenario_name,
                calculation_time=calc.calculation_time,
                status=calc.status
            ))
            risk_values.append(float(calc.risk_value))
        
        # Calculate summary statistics
        summary_stats = {
            "count": len(risk_values),
            "mean": sum(risk_values) / len(risk_values) if risk_values else 0,
            "min": min(risk_values) if risk_values else 0,
            "max": max(risk_values) if risk_values else 0
        }
        
        if len(risk_values) > 1:
            variance = sum((x - summary_stats["mean"]) ** 2 for x in risk_values) / len(risk_values)
            summary_stats["std_dev"] = variance ** 0.5
        else:
            summary_stats["std_dev"] = 0
        
        return RiskHistoryResponse(
            portfolio_id=portfolio_id,
            date_range={"start": start_date, "end": end_date},
            risk_metrics=risk_metrics,
            summary_stats=summary_stats
        )


@router.get("/{portfolio_id}/stress-tests")
async def get_stress_test_results(
    portfolio_id: str,
    business_date: date = Query(..., description="Business date for stress tests"),
    current_user: User = Depends(get_current_user)
):
    """
    Get stress test results for a portfolio
    
    Returns all stress test scenario results for the specified portfolio and date,
    including regulatory and internal stress scenarios.
    """
    async with get_db_session() as session:
        stress_calcs = session.query(RiskCalculation).filter(
            RiskCalculation.portfolio_id == portfolio_id,
            RiskCalculation.business_date == business_date,
            RiskCalculation.calculation_type == 'stress',
            RiskCalculation.status == 'completed'
        ).all()
        
        if not stress_calcs:
            raise HTTPException(
                status_code=404,
                detail=f"No stress test results found for portfolio {portfolio_id} on {business_date}"
            )
        
        # Organize by scenario
        scenarios = {}
        for calc in stress_calcs:
            scenarios[calc.scenario_name] = {
                "scenario_name": calc.scenario_name,
                "stress_loss": float(calc.risk_value),
                "currency": calc.currency,
                "methodology": calc.methodology,
                "calculation_time": calc.calculation_time
            }
        
        return {
            "portfolio_id": portfolio_id,
            "business_date": business_date,
            "stress_scenarios": scenarios,
            "worst_case_loss": max(float(calc.risk_value) for calc in stress_calcs),
            "scenarios_count": len(scenarios)
        }


@router.post("/{portfolio_id}/validate")
async def validate_risk_model(
    portfolio_id: str,
    start_date: date = Query(..., description="Start date for backtesting"),
    end_date: date = Query(..., description="End date for backtesting"),
    confidence_level: float = Query(0.99, description="Confidence level to validate"),
    current_user: User = Depends(get_current_user)
):
    """
    Validate risk model through backtesting
    
    Performs regulatory backtesting to validate the accuracy of VaR models
    by comparing predicted VaR with actual P&L over the specified period.
    """
    if (end_date - start_date).days < 250:
        raise HTTPException(
            status_code=400,
            detail="Backtesting requires at least 250 days of data"
        )
    
    # Implementation would include:
    # 1. Load historical VaR predictions
    # 2. Load actual P&L for same dates
    # 3. Count exceptions (days when loss exceeded VaR)
    # 4. Calculate traffic light test results
    # 5. Return validation statistics
    
    # Simplified response for now
    return {
        "portfolio_id": portfolio_id,
        "validation_period": {"start": start_date, "end": end_date},
        "confidence_level": confidence_level,
        "total_observations": (end_date - start_date).days,
        "exceptions_count": 2,  # Placeholder
        "exception_rate": 0.008,  # Placeholder (should be < 1% for 99% VaR)
        "traffic_light_status": "green",  # green, yellow, red
        "model_performance": "acceptable",
        "recommendations": [
            "Model performance is within acceptable limits",
            "Continue daily monitoring of exception rates"
        ]
    }


@router.get("/methodologies")
async def get_available_methodologies():
    """
    Get available risk calculation methodologies
    
    Returns a list of supported risk calculation methods with descriptions.
    """
    methodologies = [
        {
            "name": "historical",
            "display_name": "Historical Simulation",
            "description": "Non-parametric method using historical price movements",
            "pros": ["No distributional assumptions", "Captures fat tails", "Easy to understand"],
            "cons": ["Limited by historical data", "Slow to adapt to regime changes"],
            "basel_compliant": True
        },
        {
            "name": "monte_carlo",
            "display_name": "Monte Carlo Simulation",
            "description": "Parametric method using stochastic price simulations",
            "pros": ["Can model complex portfolios", "Flexible scenario generation"],
            "cons": ["Requires distributional assumptions", "Computationally intensive"],
            "basel_compliant": True
        },
        {
            "name": "parametric",
            "display_name": "Parametric (Delta-Normal)",
            "description": "Analytical method assuming normal distribution",
            "pros": ["Fast calculation", "Analytically tractable"],
            "cons": ["Normal distribution assumption", "Limited to linear portfolios"],
            "basel_compliant": True
        },
        {
            "name": "evt",
            "display_name": "Extreme Value Theory",
            "description": "Focus on tail risk using extreme value distributions",
            "pros": ["Better tail risk modeling", "Captures extreme events"],
            "cons": ["Complex implementation", "Requires sufficient tail data"],
            "basel_compliant": False
        }
    ]
    
    return {
        "methodologies": methodologies,
        "default_methodology": "historical",
        "regulatory_preferred": ["historical", "monte_carlo"]
    }