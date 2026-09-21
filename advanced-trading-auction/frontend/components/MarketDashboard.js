import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Progress,
  Tag,
  Button,
  Space,
  Tabs,
  Alert,
  Spin
} from 'antd';
import {
  TrendingUpOutlined,
  TrendingDownOutlined,
  DollarOutlined,
  ShoppingOutlined,
  BarChartOutlined,
  TrophyOutlined,
  AlertOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { Line, Column, Pie } from '@ant-design/plots';
import { formatPrice, formatNumber } from '../utils/formatters';
import { useWebSocket } from '../hooks/useWebSocket';

const { TabPane } = Tabs;

const MarketDashboard = ({ regionId = 'global', timeRange = 7 }) => {
  const [loading, setLoading] = useState(true);
  const [marketOverview, setMarketOverview] = useState(null);
  const [topItems, setTopItems] = useState([]);
  const [marketTrends, setMarketTrends] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [risks, setRisks] = useState([]);
  const [priceHistory, setPriceHistory] = useState([]);
  const ws = useWebSocket('/api/market/realtime');

  useEffect(() => {
    loadMarketData();

    // Set up real-time updates
    if (ws) {
      ws.on('market_update', handleMarketUpdate);
      ws.on('price_alert', handlePriceAlert);

      return () => {
        ws.off('market_update', handleMarketUpdate);
        ws.off('price_alert', handlePriceAlert);
      };
    }
  }, [regionId, timeRange, ws]);

  const loadMarketData = async () => {
    setLoading(true);
    try {
      const [
        overviewData,
        topItemsData,
        trendsData,
        opportunitiesData,
        risksData,
        priceHistoryData
      ] = await Promise.all([
        fetchMarketOverview(),
        fetchTopItems(),
        fetchMarketTrends(),
        fetchOpportunities(),
        fetchRisks(),
        fetchPriceHistory()
      ]);

      setMarketOverview(overviewData);
      setTopItems(topItemsData);
      setMarketTrends(trendsData);
      setOpportunities(opportunitiesData);
      setRisks(risksData);
      setPriceHistory(priceHistoryData);
    } catch (error) {
      console.error('Failed to load market data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarketUpdate = (data) => {
    setMarketOverview(prev => ({
      ...prev,
      ...data.overview
    }));
  };

  const handlePriceAlert = (alert) => {
    // Handle price alerts (show notification, update data, etc.)
    console.log('Price alert received:', alert);
  };

  const fetchMarketOverview = async () => {
    const response = await fetch(`/api/marketplace/stats?regionId=${regionId}&timeRange=${timeRange}`);
    return response.json();
  };

  const fetchTopItems = async () => {
    const response = await fetch(`/api/analytics/top-items?regionId=${regionId}&timeRange=${timeRange}`);
    return response.json();
  };

  const fetchMarketTrends = async () => {
    const response = await fetch(`/api/marketplace/trends?regionId=${regionId}&timeRange=${timeRange}`);
    return response.json();
  };

  const fetchOpportunities = async () => {
    const response = await fetch(`/api/analytics/opportunities?regionId=${regionId}&timeRange=${timeRange}`);
    return response.json();
  };

  const fetchRisks = async () => {
    const response = await fetch(`/api/analytics/risks?regionId=${regionId}&timeRange=${timeRange}`);
    return response.json();
  };

  const fetchPriceHistory = async () => {
    const response = await fetch(`/api/market/price-history?regionId=${regionId}&timeRange=${timeRange}`);
    return response.json();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading market data...</div>
      </div>
    );
  }

  // Chart configurations
  const volumeChartConfig = {
    data: priceHistory.map(item => ({
      date: item.date,
      volume: parseFloat(item.volume),
      price: parseFloat(item.price)
    })),
    xField: 'date',
    yField: 'volume',
    smooth: true,
    color: '#1890ff',
    point: {
      size: 3,
      shape: 'circle',
    },
    tooltip: {
      formatter: (datum) => ({
        name: 'Volume',
        value: formatPrice(datum.volume)
      })
    }
  };

  const priceTrendConfig = {
    data: priceHistory.map(item => ({
      date: item.date,
      price: parseFloat(item.price)
    })),
    xField: 'date',
    yField: 'price',
    smooth: true,
    color: '#52c41a',
    point: {
      size: 3,
      shape: 'circle',
    },
    tooltip: {
      formatter: (datum) => ({
        name: 'Price',
        value: formatPrice(datum.price)
      })
    }
  };

  const categoryDistributionConfig = {
    data: marketTrends?.categoryTrends?.map(cat => ({
      type: cat.name,
      value: parseFloat(cat.volume || 0)
    })) || [],
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
  };

  const topItemsColumns = [
    {
      title: 'Item',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span style={{
            color: getRarityColor(record.rarity),
            fontWeight: 'bold'
          }}>
            {text}
          </span>
          <Tag color={getRarityColor(record.rarity)}>
            {record.rarity}
          </Tag>
        </Space>
      )
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => formatPrice(price),
      sorter: (a, b) => a.price - b.price
    },
    {
      title: 'Volume',
      dataIndex: 'volume',
      key: 'volume',
      render: (volume) => formatNumber(volume),
      sorter: (a, b) => a.volume - b.volume
    },
    {
      title: 'Change',
      dataIndex: 'changePercent',
      key: 'changePercent',
      render: (change) => (
        <Space>
          {change > 0 ? (
            <TrendingUpOutlined style={{ color: '#52c41a' }} />
          ) : (
            <TrendingDownOutlined style={{ color: '#ff4d4f' }} />
          )}
          <span style={{ color: change > 0 ? '#52c41a' : '#ff4d4f' }}>
            {change > 0 ? '+' : ''}{change.toFixed(2)}%
          </span>
        </Space>
      ),
      sorter: (a, b) => a.changePercent - b.changePercent
    }
  ];

  const getRarityColor = (rarity) => {
    const colors = {
      common: '#8c8c8c',
      uncommon: '#52c41a',
      rare: '#1890ff',
      epic: '#722ed1',
      legendary: '#fa8c16'
    };
    return colors[rarity] || '#8c8c8c';
  };

  return (
    <div className="market-dashboard">
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <h1>Market Dashboard</h1>
          <Space>
            <Tag color="blue">{regionId.toUpperCase()}</Tag>
            <Tag>Last {timeRange} days</Tag>
          </Space>
        </Col>
        <Col>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadMarketData}
            loading={loading}
          >
            Refresh
          </Button>
        </Col>
      </Row>

      {/* Market Overview */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Volume"
              value={marketOverview?.totalVolume || 0}
              formatter={(value) => formatPrice(value)}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Transactions"
              value={marketOverview?.totalTransactions || 0}
              formatter={(value) => formatNumber(value)}
              prefix={<ShoppingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Average Price"
              value={marketOverview?.avgPrice || 0}
              formatter={(value) => formatPrice(value)}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={marketOverview?.successRate || 0}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{
                color: (marketOverview?.successRate || 0) > 70 ? '#52c41a' : '#ff4d4f'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Card title="Volume Trends" style={{ height: 400 }}>
            <Line {...volumeChartConfig} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Category Distribution" style={{ height: 400 }}>
            <Pie {...categoryDistributionConfig} />
          </Card>
        </Col>
      </Row>

      {/* Main Content Tabs */}
      <Tabs defaultActiveKey="trends">
        <TabPane tab="Market Trends" key="trends">
          <Row gutter={16}>
            <Col span={24}>
              <Card title="Price Trends" style={{ height: 400, marginBottom: 16 }}>
                <Line {...priceTrendConfig} />
              </Card>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}>
              <Card title="Top Performing Items">
                <Table
                  columns={topItemsColumns}
                  dataSource={topItems}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Opportunities" key="opportunities">
          <Row gutter={16}>
            <Col span={24}>
              <Card>
                <div style={{ marginBottom: 16 }}>
                  <Alert
                    message="Investment Opportunities"
                    description="Based on market analysis, these items show potential for profitable trades."
                    type="info"
                    showIcon
                  />
                </div>
                <Table
                  columns={[
                    {
                      title: 'Item',
                      dataIndex: 'itemName',
                      key: 'itemName',
                      render: (text, record) => (
                        <Space>
                          <span style={{ fontWeight: 'bold' }}>{text}</span>
                          <Tag color={getRarityColor(record.rarity)}>
                            {record.rarity}
                          </Tag>
                        </Space>
                      )
                    },
                    {
                      title: 'Current Price',
                      dataIndex: 'currentPrice',
                      key: 'currentPrice',
                      render: (price) => formatPrice(price)
                    },
                    {
                      title: 'Predicted Price',
                      dataIndex: 'predictedPrice',
                      key: 'predictedPrice',
                      render: (price) => formatPrice(price)
                    },
                    {
                      title: 'Potential Gain',
                      dataIndex: 'potentialGain',
                      key: 'potentialGain',
                      render: (gain) => (
                        <span style={{ color: gain > 0 ? '#52c41a' : '#ff4d4f' }}>
                          {gain > 0 ? '+' : ''}{gain.toFixed(2)}%
                        </span>
                      )
                    },
                    {
                      title: 'Confidence',
                      dataIndex: 'confidence',
                      key: 'confidence',
                      render: (confidence) => (
                        <Progress
                          percent={confidence * 100}
                          size="small"
                          status={confidence > 0.7 ? 'success' : 'normal'}
                        />
                      )
                    }
                  ]}
                  dataSource={opportunities}
                  rowKey="itemId"
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Market Risks" key="risks">
          <Row gutter={16}>
            <Col span={24}>
              <Card>
                <div style={{ marginBottom: 16 }}>
                  <Alert
                    message="Market Risk Analysis"
                    description="Identified potential risks that may affect market stability."
                    type="warning"
                    showIcon
                  />
                </div>
                <Table
                  columns={[
                    {
                      title: 'Risk Type',
                      dataIndex: 'type',
                      key: 'type',
                      render: (type) => (
                        <Tag color="red">{type.replace(/_/g, ' ').toUpperCase()}</Tag>
                      )
                    },
                    {
                      title: 'Item/Region',
                      dataIndex: 'target',
                      key: 'target'
                    },
                    {
                      title: 'Severity',
                      dataIndex: 'severity',
                      key: 'severity',
                      render: (severity) => (
                        <Progress
                          percent={severity * 100}
                          size="small"
                          status={severity > 0.8 ? 'exception' : severity > 0.5 ? 'warning' : 'normal'}
                        />
                      )
                    },
                    {
                      title: 'Description',
                      dataIndex: 'description',
                      key: 'description'
                    }
                  ]}
                  dataSource={risks}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default MarketDashboard;