# Market Risk Management System

A comprehensive end-to-end market risk management application designed for financial institutions to calculate, monitor, and report risk metrics in compliance with Basel 2.5 regulatory requirements.

## 🏦 System Overview

This enterprise-grade market risk platform provides:

- **Risk Calculation Engine**: VaR, Expected Shortfall, Stress Testing, and Incremental Risk Charge calculations
- **Basel 2.5 Compliance**: Full regulatory compliance with backtesting and model validation
- **Real-time Monitoring**: Live risk dashboards with limit monitoring and breach alerting
- **Workflow Management**: Multi-level approval workflows for reports and limit changes
- **Comprehensive Reporting**: Automated regulatory and management reporting with sign-off capabilities
- **Data Integration**: Support for multiple market data sources (Bloomberg, Reuters, manual uploads)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           Frontend (React)                      │
│  Dashboard | Risk Calc | Portfolios | Limits | Reports | Admin │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway (FastAPI)                    │
│         Authentication | Rate Limiting | Request Routing        │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────┬─────────────────┬─────────────────┬───────────┐
│  Risk Engine    │ Data Ingestion  │  Limit Monitor  │ Reporting │
│  - VaR          │ - Market Data   │ - Breach Alert  │ - PDF Gen │
│  - ES/CVaR      │ - Positions     │ - Escalation    │ - Excel   │
│  - Stress Tests │ - Validation    │ - Workflows     │ - Sign-off│
└─────────────────┴─────────────────┴─────────────────┴───────────┘
                                    │
┌─────────────────┬─────────────────┬─────────────────┬───────────┐
│   PostgreSQL    │   TimescaleDB   │      Redis      │ RabbitMQ  │
│   - Metadata    │   - Time Series │   - Caching     │ - Async   │
│   - Users       │   - Market Data │   - Sessions    │ - Tasks   │
│   - Portfolios  │   - Calculations│   - Rate Limit  │ - Queues  │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- 8GB+ RAM recommended
- 10GB+ disk space

### Launch the System

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd market-risk-system
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - **Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **Grafana Monitoring**: http://localhost:3001 (admin/admin)
   - **RabbitMQ Management**: http://localhost:15672 (risk_queue/queue_password)

4. **Default Login**
   - Email: `admin@company.com`
   - Password: `admin123`

## 📊 Key Features

### Risk Calculation Engine

#### VaR Methodologies
- **Historical Simulation**: Non-parametric, full revaluation
- **Monte Carlo**: Stochastic modeling with scenario generation
- **Parametric**: Delta-normal analytical approach
- **Extreme Value Theory**: Advanced tail risk modeling

#### Basel 2.5 Metrics
- **Value at Risk (VaR)**: 99% confidence, 1-day holding period
- **Expected Shortfall (ES)**: Coherent tail risk measure
- **Incremental Risk Charge (IRC)**: Credit migration and default risk
- **Comprehensive Risk Measure (CRM)**: Correlation trading portfolios

#### Stress Testing
- **Regulatory Scenarios**: 2008 Crisis, COVID-19, European Sovereign
- **Internal Scenarios**: Interest rate shocks, credit spread widening
- **Reverse Stress Tests**: Portfolio loss threshold analysis

### Limit Management

- **Hierarchical Limits**: Portfolio, trader, and desk level limits
- **Real-time Monitoring**: Continuous limit utilization tracking
- **Breach Alerting**: Automatic notifications and escalation
- **Approval Workflows**: Multi-level approval for limit changes

### Reporting & Analytics

- **Daily Risk Reports**: Portfolio VaR, ES, and P&L attribution
- **Regulatory Reports**: Basel 2.5 capital requirements and backtesting
- **Management Dashboards**: Risk appetite and business line analysis
- **Sign-off Workflows**: Electronic approval with audit trails

## 🛠️ Development Setup

### Backend Development

1. **Setup Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database setup**
   ```bash
   # Start databases only
   docker-compose up -d postgres timescaledb redis
   
   # Run migrations
   alembic upgrade head
   ```

3. **Run development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Development

1. **Setup Node.js environment**
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**
   ```bash
   npm start
   ```

3. **Build for production**
   ```bash
   npm run build
   ```

## 📁 Project Structure

```
market-risk-system/
├── 📄 MARKET_RISK_SYSTEM_DESIGN.md    # Comprehensive system design
├── 🐳 docker-compose.yml              # Infrastructure orchestration
├── 📊 monitoring/                      # Prometheus & Grafana configs
├── 🗄️ database/                       # Database schemas and migrations
├── 🔧 backend/                         # Python/FastAPI backend
│   ├── 📋 requirements.txt             # Python dependencies
│   ├── 🚀 main.py                      # FastAPI application
│   ├── ⚙️ config/                      # Configuration management
│   ├── 🎯 api/v1/                      # REST API endpoints
│   ├── 🧮 services/                    # Business logic services
│   │   └── 🎲 risk_engine.py          # Basel 2.5 risk calculations
│   ├── 🗃️ models/                      # Database models
│   └── 🔐 core/                        # Authentication & utilities
└── 🎨 frontend/                        # React/TypeScript frontend
    ├── 📦 package.json                 # Node.js dependencies
    ├── 🏠 src/App.tsx                  # Main React application
    ├── 📊 src/pages/Dashboard/         # Risk dashboard
    ├── 🧩 src/components/              # Reusable UI components
    └── 🔌 src/services/                # API client services
```

## 🔧 Configuration

### Environment Variables

Create `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://risk_user:risk_password@localhost:5432/market_risk
TIMESCALE_URL=postgresql://ts_user:ts_password@localhost:5433/timeseries_risk

# Security
SECRET_KEY=your-super-secure-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
BLOOMBERG_API_URL=https://api.bloomberg.com
BLOOMBERG_API_KEY=your-bloomberg-api-key

# Email notifications
SMTP_SERVER=smtp.company.com
SMTP_USERNAME=risk-system@company.com
SMTP_PASSWORD=your-email-password

# Risk calculation settings
DEFAULT_CONFIDENCE_LEVEL=0.99
HISTORICAL_LOOKBACK_DAYS=250
MAX_MONTE_CARLO_SIMULATIONS=10000
```

### Basel 2.5 Compliance Settings

Key regulatory parameters are configured in `backend/config/settings.py`:

- **VaR Confidence Levels**: 95% and 99%
- **Holding Period**: 1 day (regulatory minimum)
- **Historical Lookback**: 250 trading days
- **Stress Scenarios**: Regulatory and internal scenarios
- **Model Validation**: Backtesting parameters

## 📈 API Documentation

### Risk Calculation Endpoints

```bash
# Calculate portfolio risk
POST /api/v1/risk/calculate
{
  "portfolio_id": "EQUITY_DESK_1",
  "business_date": "2024-01-15",
  "calculation_types": ["var", "es", "stress"],
  "confidence_level": 0.99,
  "methodology": "historical"
}

# Get risk summary
GET /api/v1/risk/EQUITY_DESK_1/summary?business_date=2024-01-15

# Get risk history
GET /api/v1/risk/EQUITY_DESK_1/history?start_date=2024-01-01&end_date=2024-01-15

# Get stress test results
GET /api/v1/risk/EQUITY_DESK_1/stress-tests?business_date=2024-01-15
```

### Limit Management Endpoints

```bash
# Create risk limit
POST /api/v1/limits/
{
  "entity_type": "portfolio",
  "entity_id": "EQUITY_DESK_1",
  "limit_type": "var",
  "limit_value": 5000000,
  "currency": "USD"
}

# Get limit breaches
GET /api/v1/limits/breaches?severity=critical&status=open

# Acknowledge breach
POST /api/v1/limits/breaches/123/acknowledge
```

## 🚀 Production Deployment

### Docker Swarm Deployment

1. **Initialize swarm**
   ```bash
   docker swarm init
   ```

2. **Deploy stack**
   ```bash
   docker stack deploy -c docker-compose.prod.yml market-risk
   ```

### Kubernetes Deployment

1. **Apply configurations**
   ```bash
   kubectl apply -f k8s/
   ```

2. **Scale services**
   ```bash
   kubectl scale deployment risk-engine --replicas=3
   ```

### Security Considerations

- **TLS/SSL**: Enable HTTPS in production
- **Secrets Management**: Use Docker secrets or Kubernetes secrets
- **Network Security**: Implement proper firewall rules
- **Database Security**: Enable encryption at rest and in transit
- **Access Control**: Implement role-based access control (RBAC)

## 📊 Monitoring & Observability

### Built-in Monitoring

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: Application and database health monitoring

### Key Metrics

- **Risk Calculation Performance**: Calculation time and throughput
- **API Response Times**: Request latency and error rates
- **Database Performance**: Query execution times and connection pools
- **System Resources**: CPU, memory, and disk utilization

### Alerting Rules

- VaR calculation failures
- Limit breaches requiring escalation
- System performance degradation
- Database connection issues

## 🧪 Testing

### Backend Testing

```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Testing

```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Testing

```bash
# Run full system tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📚 Basel 2.5 Compliance Guide

### Model Validation Requirements

1. **Backtesting**: Daily comparison of VaR predictions vs. actual P&L
2. **Traffic Light Tests**: Exception rate monitoring (Green: <5, Yellow: 5-9, Red: 10+ exceptions)
3. **Model Documentation**: Comprehensive methodology documentation
4. **Independent Validation**: Separate validation framework

### Regulatory Reporting

- **Daily Risk Reports**: Portfolio VaR and ES calculations
- **Monthly Capital Reports**: Market risk capital requirements
- **Quarterly Model Validation**: Backtesting and performance metrics
- **Annual Model Review**: Comprehensive model assessment

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Commit changes**: `git commit -am 'Add new feature'`
4. **Push to branch**: `git push origin feature/new-feature`
5. **Create Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Comprehensive guides in `/docs`
- **API Reference**: Interactive docs at `/docs` endpoint
- **Issue Tracker**: GitHub issues for bugs and feature requests

### Common Issues

#### Database Connection Errors
```bash
# Check database status
docker-compose ps postgres

# View logs
docker-compose logs postgres
```

#### Risk Calculation Failures
```bash
# Check risk engine logs
docker-compose logs risk-engine

# Verify data quality
docker-compose exec postgres psql -U risk_user -d market_risk -c "SELECT COUNT(*) FROM market_data WHERE business_date = CURRENT_DATE;"
```

#### Frontend Build Issues
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

## 🏢 Enterprise Features

For enterprise deployments, additional features include:

- **Active Directory Integration**: LDAP/AD authentication
- **Advanced Reporting**: Custom report templates and scheduling
- **Data Lineage**: Complete audit trail for regulatory compliance
- **High Availability**: Multi-region deployment with failover
- **Performance Optimization**: Distributed computing for large portfolios

---

**Built with ❤️ for the financial industry**

*This system provides a robust foundation for market risk management while maintaining flexibility for customization to specific institutional requirements.*
