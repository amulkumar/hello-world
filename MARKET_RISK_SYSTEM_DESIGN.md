# Market Risk Management System - Design & Implementation

## Executive Summary

This document outlines the design and implementation of an end-to-end market risk management application compliant with Basel 2.5 regulatory requirements. The system encompasses data processing, analytical engines for risk metrics calculation, comprehensive reporting with sign-off features, and robust limit management capabilities.

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Message Queue  │    │   Frontend UI   │
│   - Market Data │────┤   (Redis/RMQ)   │    │   - React App   │
│   - Position    │    └──────────────────┘    │   - Risk Dash   │
│   - Reference   │             │              │   - Reports     │
└─────────────────┘             │              └─────────────────┘
         │                      │                       │
         │                      ▼                       │
         │           ┌──────────────────┐               │
         │           │  API Gateway     │◄──────────────┘
         │           │  (FastAPI)       │
         │           └──────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌──────────────────┐
│ Data Ingestion  │    │  Authentication  │
│ Service         │    │  & Authorization │
│ - ETL Pipeline  │    │  Service         │
│ - Data Quality  │    └──────────────────┘
└─────────────────┘             │
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Risk Calculation│    │  User Management │    │   Reporting     │
│ Engine          │    │  & Workflow      │    │   Service       │
│ - VaR           │    │  Service         │    │ - PDF Reports   │
│ - ES/CVaR       │    └──────────────────┘    │ - Excel Export  │
│ - Stress Tests  │             │              │ - Dashboards    │
└─────────────────┘             │              └─────────────────┘
         │                      │                       │
         ▼                      ▼                       │
┌─────────────────┐    ┌──────────────────┐             │
│ Limit Management│    │   Sign-off       │◄────────────┘
│ Service         │    │   Workflow       │
│ - Breach Alert  │    │   Service        │
│ - Escalation    │    └──────────────────┘
└─────────────────┘             │
         │                      │
         └──────┬───────────────┘
                ▼
       ┌──────────────────┐
       │   Database       │
       │ - PostgreSQL     │
       │ - TimescaleDB    │
       │ - Redis Cache    │
       └──────────────────┘
```

### 1.2 Technology Stack

- **Backend**: Python 3.11+, FastAPI, Celery
- **Database**: PostgreSQL, TimescaleDB, Redis
- **Frontend**: React 18, TypeScript, Material-UI
- **Message Queue**: Redis/RabbitMQ
- **Containerization**: Docker, Docker Compose
- **Monitoring**: Prometheus, Grafana
- **Documentation**: OpenAPI/Swagger

## 2. Basel 2.5 Compliance Framework

### 2.1 Key Requirements

#### Market Risk Metrics (Basel 2.5)
- **Value at Risk (VaR)**: 99% confidence, 1-day holding period
- **Expected Shortfall (ES/CVaR)**: Coherent risk measure
- **Incremental Risk Charge (IRC)**: Default and migration risk
- **Comprehensive Risk Measure (CRM)**: For correlation trading
- **Stress Testing**: Regulatory and internal scenarios

#### Data Requirements
- **Minimum 1 year** of historical market data
- **Daily P&L attribution**
- **Position-level granularity**
- **Risk factor mapping**

### 2.2 Calculation Methodologies

#### 2.2.1 Historical Simulation VaR
```python
# Pseudo-code for Historical Simulation
def calculate_historical_var(positions, market_data, confidence_level=0.99):
    # 1. Calculate historical returns
    returns = calculate_returns(market_data)
    
    # 2. Revalue portfolio for each scenario
    portfolio_pnl = []
    for scenario in returns:
        pnl = revalue_portfolio(positions, scenario)
        portfolio_pnl.append(pnl)
    
    # 3. Calculate VaR
    var = np.percentile(portfolio_pnl, (1 - confidence_level) * 100)
    return var
```

#### 2.2.2 Expected Shortfall
```python
def calculate_expected_shortfall(pnl_distribution, confidence_level=0.99):
    var_threshold = np.percentile(pnl_distribution, (1 - confidence_level) * 100)
    tail_losses = pnl_distribution[pnl_distribution <= var_threshold]
    return np.mean(tail_losses)
```

## 3. System Components Design

### 3.1 Data Processing Layer

#### 3.1.1 Data Ingestion Service
```yaml
Market Data Sources:
  - Bloomberg API
  - Reuters Eikon
  - FIX Protocol feeds
  - CSV/Excel uploads
  - Internal trading systems

Data Types:
  - Equity prices
  - FX rates
  - Interest rate curves
  - Credit spreads
  - Volatility surfaces
  - Position data
```

#### 3.1.2 Data Quality Framework
- **Completeness checks**: Missing data detection
- **Consistency validation**: Cross-source verification
- **Timeliness monitoring**: Data freshness alerts
- **Accuracy testing**: Outlier detection

### 3.2 Risk Calculation Engine

#### 3.2.1 Core Risk Metrics

##### VaR Calculation Methods
1. **Historical Simulation**
   - Non-parametric approach
   - Full revaluation
   - 250+ day lookback period

2. **Monte Carlo Simulation**
   - Stochastic modeling
   - Path-dependent instruments
   - Scenario generation

3. **Parametric VaR**
   - Delta-normal approach
   - Correlation matrices
   - Volatility modeling

##### Expected Shortfall (CVaR)
- Conditional tail expectation
- Coherent risk measure
- Regulatory requirement under Basel 2.5

#### 3.2.2 Stress Testing Framework
```yaml
Stress Test Types:
  Regulatory Scenarios:
    - 2008 Financial Crisis
    - COVID-19 Market Shock
    - European Sovereign Crisis
  
  Internal Scenarios:
    - Interest rate shocks
    - Credit spread widening
    - Equity market crashes
    - FX volatility spikes
  
  Reverse Stress Tests:
    - Portfolio loss thresholds
    - Capital adequacy limits
```

### 3.3 Database Schema Design

#### 3.3.1 Market Data Tables
```sql
-- Market data time series
CREATE TABLE market_data (
    id BIGSERIAL PRIMARY KEY,
    instrument_id VARCHAR(50) NOT NULL,
    data_type VARCHAR(20) NOT NULL, -- 'price', 'rate', 'volatility'
    business_date DATE NOT NULL,
    value DECIMAL(15,8) NOT NULL,
    currency VARCHAR(3),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(instrument_id, data_type, business_date)
);

-- Instrument reference data
CREATE TABLE instruments (
    id VARCHAR(50) PRIMARY KEY,
    instrument_type VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    currency VARCHAR(3),
    sector VARCHAR(50),
    country VARCHAR(3),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3.3.2 Position and Risk Tables
```sql
-- Portfolio positions
CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL,
    instrument_id VARCHAR(50) NOT NULL,
    business_date DATE NOT NULL,
    quantity DECIMAL(15,2) NOT NULL,
    market_value DECIMAL(15,2),
    currency VARCHAR(3),
    trader_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (instrument_id) REFERENCES instruments(id)
);

-- Risk calculations
CREATE TABLE risk_calculations (
    id BIGSERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL,
    business_date DATE NOT NULL,
    calculation_type VARCHAR(20) NOT NULL, -- 'var', 'es', 'stress'
    methodology VARCHAR(20), -- 'historical', 'monte_carlo', 'parametric'
    confidence_level DECIMAL(4,3),
    holding_period INTEGER,
    risk_value DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3),
    calculation_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed'
);
```

#### 3.3.3 Limit Management Tables
```sql
-- Risk limits
CREATE TABLE risk_limits (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL, -- 'portfolio', 'trader', 'desk'
    entity_id VARCHAR(50) NOT NULL,
    limit_type VARCHAR(20) NOT NULL, -- 'var', 'es', 'notional'
    limit_value DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50),
    approved_by VARCHAR(50),
    approval_date TIMESTAMP
);

-- Limit breaches
CREATE TABLE limit_breaches (
    id BIGSERIAL PRIMARY KEY,
    limit_id BIGINT NOT NULL,
    business_date DATE NOT NULL,
    actual_value DECIMAL(15,2) NOT NULL,
    limit_value DECIMAL(15,2) NOT NULL,
    breach_percentage DECIMAL(5,2),
    severity VARCHAR(20), -- 'warning', 'breach', 'critical'
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'acknowledged', 'resolved'
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (limit_id) REFERENCES risk_limits(id)
);
```

### 3.4 API Design

#### 3.4.1 Risk Calculation API
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

app = FastAPI(title="Market Risk API", version="1.0.0")

class RiskCalculationRequest(BaseModel):
    portfolio_id: str
    business_date: date
    calculation_types: List[str]  # ['var', 'es', 'stress']
    confidence_level: Optional[float] = 0.99
    holding_period: Optional[int] = 1

class RiskResult(BaseModel):
    portfolio_id: str
    business_date: date
    calculation_type: str
    risk_value: float
    currency: str
    methodology: str
    confidence_level: float

@app.post("/api/v1/risk/calculate", response_model=List[RiskResult])
async def calculate_risk(
    request: RiskCalculationRequest,
    current_user: User = Depends(get_current_user)
):
    """Calculate risk metrics for a portfolio"""
    # Implementation here
    pass

@app.get("/api/v1/risk/{portfolio_id}/history")
async def get_risk_history(
    portfolio_id: str,
    start_date: date,
    end_date: date,
    risk_type: Optional[str] = None
):
    """Get historical risk metrics for a portfolio"""
    # Implementation here
    pass
```

#### 3.4.2 Limit Management API
```python
@app.post("/api/v1/limits/")
async def create_limit(limit: RiskLimitCreate):
    """Create a new risk limit"""
    pass

@app.get("/api/v1/limits/breaches")
async def get_breaches(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None
):
    """Get limit breaches"""
    pass

@app.post("/api/v1/limits/breaches/{breach_id}/acknowledge")
async def acknowledge_breach(breach_id: int):
    """Acknowledge a limit breach"""
    pass
```

### 3.5 Reporting Framework

#### 3.5.1 Report Types

##### Daily Risk Report
- Portfolio VaR and ES by desk/trader
- Limit utilization dashboard
- P&L attribution analysis
- Risk factor sensitivities

##### Regulatory Reports
- Basel 2.5 market risk capital requirements
- Model validation backtesting results
- Stress testing summaries
- Exception reporting

##### Management Reports
- Risk appetite utilization
- Limit breach summaries
- Model performance metrics
- Business line risk profiles

#### 3.5.2 Sign-off Workflow
```python
class ReportSignOff(BaseModel):
    report_id: str
    report_type: str
    business_date: date
    prepared_by: str
    reviewed_by: Optional[str]
    approved_by: Optional[str]
    status: str  # 'draft', 'review', 'approved', 'rejected'
    comments: Optional[str]
    deadline: datetime

@app.post("/api/v1/reports/{report_id}/sign-off")
async def sign_off_report(
    report_id: str,
    action: str,  # 'review', 'approve', 'reject'
    comments: Optional[str] = None
):
    """Sign off on a report"""
    # Implementation with workflow engine
    pass
```

### 3.6 Frontend Design

#### 3.6.1 Dashboard Components

##### Risk Dashboard
```typescript
interface RiskDashboardProps {
  portfolioId: string;
  businessDate: string;
}

const RiskDashboard: React.FC<RiskDashboardProps> = ({ portfolioId, businessDate }) => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <VaRChart portfolioId={portfolioId} />
      </Grid>
      <Grid item xs={12} md={6}>
        <LimitUtilization portfolioId={portfolioId} />
      </Grid>
      <Grid item xs={12}>
        <RiskBreakdown portfolioId={portfolioId} />
      </Grid>
    </Grid>
  );
};
```

##### Limit Management Interface
```typescript
const LimitManagement: React.FC = () => {
  return (
    <Box>
      <LimitGrid />
      <BreachAlerts />
      <ApprovalWorkflow />
    </Box>
  );
};
```

## 4. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [ ] Set up development environment
- [ ] Database schema implementation
- [ ] Basic API framework
- [ ] Authentication system
- [ ] Data ingestion pipeline

### Phase 2: Core Risk Engine (Weeks 5-8)
- [ ] Historical simulation VaR
- [ ] Expected Shortfall calculation
- [ ] Monte Carlo framework
- [ ] Stress testing engine
- [ ] Model validation tools

### Phase 3: Business Logic (Weeks 9-12)
- [ ] Portfolio aggregation
- [ ] Risk factor mapping
- [ ] P&L attribution
- [ ] Limit management system
- [ ] Alert and notification system

### Phase 4: Reporting & UI (Weeks 13-16)
- [ ] Report generation engine
- [ ] Frontend dashboard
- [ ] Sign-off workflow
- [ ] User management
- [ ] Export capabilities

### Phase 5: Production Ready (Weeks 17-20)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Monitoring and logging
- [ ] Documentation
- [ ] User training

## 5. Regulatory Compliance Checklist

### Basel 2.5 Requirements
- [ ] VaR models with 99% confidence level
- [ ] Expected Shortfall implementation
- [ ] Incremental Risk Charge for credit portfolios
- [ ] Comprehensive Risk Measure for correlation trading
- [ ] Stress testing framework
- [ ] Model validation and backtesting
- [ ] Documentation and governance

### Operational Requirements
- [ ] Daily risk calculation and reporting
- [ ] Limit monitoring and breach management
- [ ] Model governance framework
- [ ] Audit trail and data lineage
- [ ] Business continuity planning
- [ ] Regulatory reporting capabilities

## 6. Risk and Mitigation Strategies

### Technical Risks
- **Data Quality**: Implement comprehensive validation
- **Performance**: Use caching and parallel processing
- **Scalability**: Microservices architecture
- **Security**: OAuth2, encryption, audit logs

### Business Risks
- **Model Risk**: Regular validation and backtesting
- **Operational Risk**: Automated processes and alerts
- **Regulatory Risk**: Compliance monitoring
- **Reputational Risk**: Robust testing and controls

## 7. Success Metrics

### Technical KPIs
- 99.9% system uptime
- < 30 minutes risk calculation time
- < 5 second dashboard load time
- Zero data breaches

### Business KPIs
- 100% regulatory report accuracy
- < 1 hour breach notification time
- 90% user satisfaction score
- 50% reduction in manual processes

---

This comprehensive design provides a robust foundation for building an enterprise-grade market risk management system that meets Basel 2.5 requirements while providing modern user experience and operational efficiency.