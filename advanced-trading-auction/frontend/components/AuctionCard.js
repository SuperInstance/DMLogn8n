import React, { useState, useEffect } from 'react';
import { Card, Badge, Button, Row, Col, Statistic, Timer, Avatar, Tooltip } from 'antd';
import {
  ClockCircleOutlined,
  UserOutlined,
  EyeOutlined,
  GavelOutlined,
  TrophyOutlined,
  FireOutlined
} from '@ant-design/icons';
import { formatPrice, formatTimeRemaining, getItemRarityColor } from '../utils/formatters';
import { useSocket } from '../hooks/useSocket';

const { Meta } = Card;

const AuctionCard = ({
  auction,
  onBidClick,
  onViewDetails,
  compact = false,
  showSellerInfo = true,
  currentUserId
}) => {
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [currentBid, setCurrentBid] = useState(auction.current_bid);
  const [bidCount, setBidCount] = useState(auction.bid_count);
  const socket = useSocket();

  useEffect(() => {
    // Calculate initial time remaining
    updateTimeRemaining();

    // Set up timer for countdown
    const timer = setInterval(updateTimeRemaining, 1000);

    return () => clearInterval(timer);
  }, [auction.end_time]);

  useEffect(() => {
    // Listen for real-time auction updates
    if (socket) {
      socket.on('auction_updated', handleAuctionUpdate);
      socket.on('bid_placed', handleBidPlaced);

      return () => {
        socket.off('auction_updated', handleAuctionUpdate);
        socket.off('bid_placed', handleBidPlaced);
      };
    }
  }, [socket, auction.id]);

  const updateTimeRemaining = () => {
    const now = new Date();
    const endTime = new Date(auction.end_time);
    const remaining = endTime - now;

    setTimeRemaining(remaining);
  };

  const handleAuctionUpdate = (data) => {
    if (data.auctionId === auction.id) {
      setCurrentBid(data.current_bid);
      setBidCount(data.bid_count);
    }
  };

  const handleBidPlaced = (data) => {
    if (data.auctionId === auction.id) {
      setCurrentBid(data.amount);
      setBidCount(prev => prev + 1);
    }
  };

  const isAuctionEnded = timeRemaining <= 0;
  const isOwner = auction.seller_id === currentUserId;
  const isWinningBidder = auction.bidder_id === currentUserId && !isAuctionEnded;
  const hasReservePrice = auction.reserve_price && parseFloat(auction.reserve_price) > 0;
  const meetsReserve = hasReservePrice && currentBid >= parseFloat(auction.reserve_price);
  const hasBuyout = auction.buyout_price && parseFloat(auction.buyout_price) > 0;
  const buyoutPrice = hasBuyout ? parseFloat(auction.buyout_price) : null;

  const getAuctionStatus = () => {
    if (isAuctionEnded) {
      return {
        status: auction.status === 'sold' ? 'Sold' : 'Expired',
        color: auction.status === 'sold' ? 'success' : 'default',
        icon: auction.status === 'sold' ? <TrophyOutlined /> : <ClockCircleOutlined />
      };
    }

    if (isWinningBidder) {
      return {
        status: 'Winning',
        color: 'success',
        icon: <TrophyOutlined />
      };
    }

    return {
      status: 'Active',
      color: 'processing',
      icon: <GavelOutlined />
    };
  };

  const auctionStatus = getAuctionStatus();

  const actions = [];

  if (!isAuctionEnded && !isOwner) {
    actions.push(
      <Button
        type="primary"
        icon={<GavelOutlined />}
        onClick={() => onBidClick(auction)}
        disabled={isOwner}
      >
        Place Bid
      </Button>
    );
  }

  if (hasBuyout && !isAuctionEnded && !isOwner) {
    actions.push(
      <Button
        type="default"
        onClick={() => onBidClick(auction, true)}
      >
        Buyout {formatPrice(buyoutPrice)}
      </Button>
    );
  }

  actions.push(
    <Button
      type="link"
      icon={<EyeOutlined />}
      onClick={() => onViewDetails(auction)}
    >
      View Details
    </Button>
  );

  const cardTitle = (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span
        style={{
          color: getItemRarityColor(auction.item_rarity),
          fontWeight: 'bold'
        }}
      >
        {auction.item_name}
      </span>
      <Badge
        count={auctionStatus.status}
        style={{ backgroundColor: getStatusColor(auctionStatus.color) }}
      />
    </div>
  );

  return (
    <Card
      hoverable
      className={`auction-card ${compact ? 'compact' : ''}`}
      cover={
        !compact && (
          <div style={{
            height: 200,
            background: `url(${auction.item_icon || '/api/placeholder/item'}) center/cover`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{
              background: 'rgba(0,0,0,0.7)',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', marginBottom: '4px' }}>
                {auction.item_name}
              </div>
              <div style={{ fontSize: '12px', opacity: 0.8 }}>
                {auction.item_rarity?.toUpperCase()}
              </div>
            </div>
          </div>
        )
      }
      actions={actions}
    >
      <Meta
        title={cardTitle}
        description={
          <div>
            {/* Time Remaining */}
            <Row justify="space-between" align="middle" style={{ marginBottom: 12 }}>
              <Col>
                <ClockCircleOutlined style={{ marginRight: 4 }} />
                {isAuctionEnded ? (
                  <span style={{ color: '#ff4d4f' }}>Ended</span>
                ) : (
                  <Timer
                    value={timeRemaining}
                    format="HH:mm:ss"
                    onFinish={() => updateTimeRemaining()}
                  />
                )}
              </Col>
              <Col>
                <Badge count={bidCount} showZero>
                  <GavelOutlined />
                </Badge>
              </Col>
            </Row>

            {/* Current Bid */}
            <Row gutter={16} style={{ marginBottom: 12 }}>
              <Col span={12}>
                <Statistic
                  title="Current Bid"
                  value={currentBid}
                  formatter={(value) => formatPrice(value)}
                  valueStyle={{
                    color: isWinningBidder ? '#52c41a' : '#1890ff',
                    fontSize: compact ? '16px' : '20px'
                  }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Buyout"
                  value={buyoutPrice || '---'}
                  formatter={(value) =>
                    typeof value === 'number' ? formatPrice(value) : value
                  }
                  valueStyle={{ fontSize: compact ? '14px' : '16px' }}
                />
              </Col>
            </Row>

            {/* Reserve Price Indicator */}
            {hasReservePrice && (
              <div style={{ marginBottom: 8 }}>
                <Tooltip
                  title={meetsReserve ? 'Reserve price met' : 'Reserve price not met'}
                >
                  <Badge
                    status={meetsReserve ? 'success' : 'warning'}
                    text={`Reserve: ${hasReservePrice ? 'Set' : 'Not set'}`}
                  />
                </Tooltip>
              </div>
            )}

            {/* Item Details */}
            <Row gutter={8} style={{ fontSize: '12px', color: '#666' }}>
              <Col span={8}>
                Quantity: {auction.quantity}
              </Col>
              <Col span={8}>
                {auction.min_bid_increment && (
                  <span>Min bid: +{(auction.min_bid_increment * 100).toFixed(0)}%</span>
                )}
              </Col>
              <Col span={8}>
                <FireOutlined /> {auction.views || 0} views
              </Col>
            </Row>

            {/* Seller Information */}
            {showSellerInfo && !compact && (
              <div style={{
                marginTop: 12,
                paddingTop: 12,
                borderTop: '1px solid #f0f0f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar size="small" icon={<UserOutlined />} />
                  <span style={{ marginLeft: 8 }}>
                    {auction.anonymous ? 'Anonymous' : auction.seller_username}
                  </span>
                </div>
                <Badge
                  count={auction.region_id?.toUpperCase()}
                  style={{ backgroundColor: '#52c41a' }}
                />
              </div>
            )}
          </div>
        }
      />
    </Card>
  );
};

const getStatusColor = (status) => {
  const colors = {
    success: '#52c41a',
    processing: '#1890ff',
    default: '#d9d9d9',
    error: '#ff4d4f',
    warning: '#faad14'
  };
  return colors[status] || colors.default;
};

export default AuctionCard;