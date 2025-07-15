import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  Assessment,
  AccountBalance,
  Speed,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { format, subDays } from 'date-fns';

import { useQuery } from 'react-query';
import { riskApi } from '../../services/api';
import { formatCurrency, formatPercentage } from '../../utils/formatters';

interface RiskMetric {
  portfolioId: string;
  portfolioName: string;
  var99: number;
  expectedShortfall99: number;
  currency: string;
  lastUpdated: string;
  trend: 'up' | 'down' | 'stable';
  trendPercentage: number;
}

interface LimitUtilization {
  portfolioId: string;
  portfolioName: string;
  limitType: string;
  limitValue: number;
  currentValue: number;
  utilization: number;
  status: 'normal' | 'warning' | 'breach';
}

interface StressTestResult {
  scenario: string;
  loss: number;
  portfolioCount: number;
  severity: 'low' | 'medium' | 'high';
}

const Dashboard: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch dashboard data
  const { data: riskSummary, isLoading: isLoadingRisk, error: riskError } = useQuery(
    ['dashboardRisk', selectedDate, refreshKey],
    () => riskApi.getDashboardSummary(format(selectedDate, 'yyyy-MM-dd')),
    {
      refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    }
  );

  const { data: limitBreaches, isLoading: isLoadingBreaches } = useQuery(
    ['limitBreaches', refreshKey],
    () => riskApi.getLimitBreaches({ status: 'open' }),
  );

  const { data: stressTests, isLoading: isLoadingStress } = useQuery(
    ['stressTests', selectedDate, refreshKey],
    () => riskApi.getStressTestSummary(format(selectedDate, 'yyyy-MM-dd')),
  );

  // Mock data for demonstration
  const mockRiskMetrics: RiskMetric[] = [
    {
      portfolioId: 'EQUITY_DESK_1',
      portfolioName: 'Equity Trading Desk 1',
      var99: 2500000,
      expectedShortfall99: 3200000,
      currency: 'USD',
      lastUpdated: '2024-01-15T09:30:00Z',
      trend: 'up',
      trendPercentage: 5.2,
    },
    {
      portfolioId: 'FIXED_INCOME_1',
      portfolioName: 'Fixed Income Portfolio',
      var99: 1800000,
      expectedShortfall99: 2100000,
      currency: 'USD',
      lastUpdated: '2024-01-15T09:30:00Z',
      trend: 'down',
      trendPercentage: -2.1,
    },
    {
      portfolioId: 'FX_TRADING',
      portfolioName: 'FX Trading Desk',
      var99: 950000,
      expectedShortfall99: 1200000,
      currency: 'USD',
      lastUpdated: '2024-01-15T09:30:00Z',
      trend: 'stable',
      trendPercentage: 0.3,
    },
  ];

  const mockLimitUtilization: LimitUtilization[] = [
    {
      portfolioId: 'EQUITY_DESK_1',
      portfolioName: 'Equity Trading Desk 1',
      limitType: 'VaR',
      limitValue: 3000000,
      currentValue: 2500000,
      utilization: 83.3,
      status: 'warning',
    },
    {
      portfolioId: 'FIXED_INCOME_1',
      portfolioName: 'Fixed Income Portfolio',
      limitType: 'VaR',
      limitValue: 2500000,
      currentValue: 1800000,
      utilization: 72.0,
      status: 'normal',
    },
    {
      portfolioId: 'FX_TRADING',
      portfolioName: 'FX Trading Desk',
      limitType: 'VaR',
      limitValue: 1500000,
      currentValue: 950000,
      utilization: 63.3,
      status: 'normal',
    },
  ];

  const mockStressResults: StressTestResult[] = [
    { scenario: '2008 Financial Crisis', loss: 15000000, portfolioCount: 8, severity: 'high' },
    { scenario: 'COVID-19 Shock', loss: 12000000, portfolioCount: 8, severity: 'high' },
    { scenario: 'Interest Rate Shock', loss: 8500000, portfolioCount: 6, severity: 'medium' },
    { scenario: 'Credit Spread Widening', loss: 6200000, portfolioCount: 5, severity: 'medium' },
  ];

  // Historical VaR data for chart
  const historicalVaRData = Array.from({ length: 30 }, (_, i) => ({
    date: format(subDays(selectedDate, 29 - i), 'MM/dd'),
    var99: 2500000 + (Math.random() - 0.5) * 500000,
    expectedShortfall: 3200000 + (Math.random() - 0.5) * 600000,
    actualPnL: (Math.random() - 0.5) * 1000000,
  }));

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp color="error" />;
      case 'down':
        return <TrendingDown color="success" />;
      default:
        return <Assessment color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'success';
      case 'warning':
        return 'warning';
      case 'breach':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return '#4caf50';
      case 'medium':
        return '#ff9800';
      case 'high':
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  if (isLoadingRisk) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Risk Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Last Updated: {format(new Date(), 'MMM dd, yyyy HH:mm')}
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<Refresh />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Alert Banner */}
      {limitBreaches && limitBreaches.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {limitBreaches.length} active limit breach(es) require attention
          </Typography>
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Total VaR (99%)
                  </Typography>
                  <Typography variant="h4">
                    {formatCurrency(mockRiskMetrics.reduce((sum, m) => sum + m.var99, 0))}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    vs. yesterday: +2.3%
                  </Typography>
                </Box>
                <Assessment sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Expected Shortfall
                  </Typography>
                  <Typography variant="h4">
                    {formatCurrency(mockRiskMetrics.reduce((sum, m) => sum + m.expectedShortfall99, 0))}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    99% confidence level
                  </Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 40, color: 'error.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Limit Utilization
                  </Typography>
                  <Typography variant="h4">
                    73%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average across portfolios
                  </Typography>
                </Box>
                <Speed sx={{ fontSize: 40, color: 'warning.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Active Portfolios
                  </Typography>
                  <Typography variant="h4">
                    {mockRiskMetrics.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Calculated today
                  </Typography>
                </Box>
                <AccountBalance sx={{ fontSize: 40, color: 'success.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Historical VaR Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                VaR vs Actual P&L (30 Days)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={historicalVaRData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis tickFormatter={(value) => formatCurrency(value, 0)} />
                  <RechartsTooltip formatter={(value, name) => [formatCurrency(Number(value)), name]} />
                  <Line 
                    type="monotone" 
                    dataKey="var99" 
                    stroke="#f44336" 
                    name="VaR 99%" 
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="expectedShortfall" 
                    stroke="#ff9800" 
                    name="Expected Shortfall" 
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="actualPnL" 
                    stroke="#2196f3" 
                    name="Actual P&L" 
                    strokeWidth={1}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Stress Test Results */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stress Test Results
              </Typography>
              <Box sx={{ mb: 2 }}>
                {mockStressResults.map((result, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      borderBottom: index < mockStressResults.length - 1 ? '1px solid #f0f0f0' : 'none',
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight="medium">
                        {result.scenario}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {result.portfolioCount} portfolios
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" fontWeight="bold" color="error.main">
                        {formatCurrency(result.loss)}
                      </Typography>
                      <Chip
                        label={result.severity}
                        size="small"
                        sx={{
                          backgroundColor: getSeverityColor(result.severity),
                          color: 'white',
                          fontSize: '0.7rem',
                        }}
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Portfolio Risk Metrics */}
        <Grid item xs={12} lg={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portfolio Risk Metrics
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Portfolio</TableCell>
                      <TableCell align="right">VaR (99%)</TableCell>
                      <TableCell align="right">Expected Shortfall</TableCell>
                      <TableCell align="center">Trend</TableCell>
                      <TableCell align="center">Last Updated</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockRiskMetrics.map((metric) => (
                      <TableRow key={metric.portfolioId}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {metric.portfolioName}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {metric.portfolioId}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="bold">
                            {formatCurrency(metric.var99)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {formatCurrency(metric.expectedShortfall99)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            {getTrendIcon(metric.trend)}
                            <Typography variant="caption" sx={{ ml: 0.5 }}>
                              {formatPercentage(metric.trendPercentage / 100)}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="caption">
                            {format(new Date(metric.lastUpdated), 'HH:mm')}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Limit Utilization */}
        <Grid item xs={12} lg={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Limit Utilization
              </Typography>
              <Box sx={{ mb: 2 }}>
                {mockLimitUtilization.map((limit, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" fontWeight="medium">
                        {limit.portfolioName}
                      </Typography>
                      <Chip
                        label={`${limit.utilization.toFixed(1)}%`}
                        size="small"
                        color={getStatusColor(limit.status) as any}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box
                        sx={{
                          flex: 1,
                          height: 8,
                          backgroundColor: '#f0f0f0',
                          borderRadius: 4,
                          overflow: 'hidden',
                        }}
                      >
                        <Box
                          sx={{
                            width: `${Math.min(limit.utilization, 100)}%`,
                            height: '100%',
                            backgroundColor: 
                              limit.status === 'breach' ? '#f44336' :
                              limit.status === 'warning' ? '#ff9800' : '#4caf50',
                            transition: 'width 0.3s ease-in-out',
                          }}
                        />
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="caption" color="text.secondary">
                        Current: {formatCurrency(limit.currentValue)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Limit: {formatCurrency(limit.limitValue)}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;