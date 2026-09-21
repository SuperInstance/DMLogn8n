#!/usr/bin/env python3
"""
Market Predictor - Economic and market trend forecasting system
Predicts market movements, price changes, and economic indicators in the game world
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    from scipy import stats
    from scipy.optimize import minimize
except ImportError:
    print("Warning: scikit-learn/scipy not available. Using simplified market prediction")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketType(Enum):
    """Types of markets in the game world"""
    PLAYER_GOODS = "player_goods"
    RESOURCES = "resources"
    CURRENCY = "currency"
    SERVICES = "services"
    REAL_ESTATE = "real_estate"
    STOCKS = "stocks"
    BONDS = "bonds"
    COMMODITIES = "commodities"


class MarketIndicator(Enum):
    """Market indicators for analysis"""
    PRICE = "price"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    MOMENTUM = "momentum"
    TREND = "trend"
    SUPPORT = "support"
    RESISTANCE = "resistance"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"


@dataclass
class MarketData:
    """Represents market data for a specific asset"""
    symbol: str
    market_type: MarketType
    timestamp: datetime
    price: float
    volume: float
    high: float
    low: float
    open_price: float
    close_price: float
    bid_ask_spread: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketPrediction:
    """Represents a market prediction"""
    symbol: str
    market_type: MarketType
    prediction_type: str  # price, volume, volatility, etc.
    timestamp: datetime
    prediction_horizon: int  # hours
    predicted_value: float
    confidence: float
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    technical_indicators: Dict[str, float] = field(default_factory=dict)
    risk_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class MarketSignal:
    """Represents a trading signal"""
    signal_id: str
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    strength: float  # 0-1
    timestamp: datetime
    entry_price: Optional[float]
    target_price: Optional[float]
    stop_loss: Optional[float]
    reasoning: str
    confidence: float
    expected_return: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


class TechnicalIndicators:
    """Calculate technical analysis indicators"""

    @staticmethod
    def sma(data: np.ndarray, window: int) -> np.ndarray:
        """Simple Moving Average"""
        if len(data) < window:
            return np.array([])
        return np.convolve(data, np.ones(window)/window, mode='valid')

    @staticmethod
    def ema(data: np.ndarray, window: int) -> np.ndarray:
        """Exponential Moving Average"""
        if len(data) < window:
            return np.array([])

        alpha = 2 / (window + 1)
        ema_values = np.zeros(len(data))
        ema_values[0] = data[0]

        for i in range(1, len(data)):
            ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i-1]

        return ema_values

    @staticmethod
    def rsi(data: np.ndarray, window: int = 14) -> np.ndarray:
        """Relative Strength Index"""
        if len(data) < window + 1:
            return np.array([])

        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = TechnicalIndicators.sma(gains, window)
        avg_loss = TechnicalIndicators.sma(losses, window)

        rs = avg_gain / (avg_loss + 1e-6)
        rsi_values = 100 - (100 / (1 + rs))

        return rsi_values

    @staticmethod
    def bollinger_bands(data: np.ndarray, window: int = 20, num_std: float = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands"""
        if len(data) < window:
            return np.array([]), np.array([]), np.array([])

        sma_values = TechnicalIndicators.sma(data, window)
        std_values = np.array([np.std(data[i:i+window]) for i in range(len(data) - window + 1)])

        upper_band = sma_values + (num_std * std_values)
        lower_band = sma_values - (num_std * std_values)

        return lower_band, sma_values, upper_band

    @staticmethod
    def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD (Moving Average Convergence Divergence)"""
        if len(data) < slow:
            return np.array([]), np.array([]), np.array([])

        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)

        macd_line = ema_fast[-len(ema_slow):] - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line[-len(signal_line):] - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def volatility(data: np.ndarray, window: int = 20) -> np.ndarray:
        """Calculate rolling volatility"""
        if len(data) < window:
            return np.array([])

        returns = np.diff(np.log(data + 1e-6))
        volatility_values = np.array([np.std(returns[i:i+window]) for i in range(len(returns) - window + 1)])

        return volatility_values

    @staticmethod
    def support_resistance(data: np.ndarray, window: int = 20) -> Tuple[List[float], List[float]]:
        """Identify support and resistance levels"""
        if len(data) < window:
            return [], []

        # Find local minima (support) and maxima (resistance)
        support_levels = []
        resistance_levels = []

        for i in range(window, len(data) - window):
            # Support: local minimum
            if data[i] == min(data[i-window:i+window+1]):
                support_levels.append(data[i])

            # Resistance: local maximum
            if data[i] == max(data[i-window:i+window+1]):
                resistance_levels.append(data[i])

        # Consolidate nearby levels
        support_levels = TechnicalIndicators._consolidate_levels(support_levels)
        resistance_levels = TechnicalIndicators._consolidate_levels(resistance_levels)

        return support_levels, resistance_levels

    @staticmethod
    def _consolidate_levels(levels: List[float], threshold: float = 0.02) -> List[float]:
        """Consolidate nearby price levels"""
        if not levels:
            return []

        levels = sorted(levels)
        consolidated = [levels[0]]

        for level in levels[1:]:
            if (level - consolidated[-1]) / consolidated[-1] > threshold:
                consolidated.append(level)
            else:
                # Average nearby levels
                consolidated[-1] = (consolidated[-1] + level) / 2

        return consolidated


class MarketModel:
    """Base class for market prediction models"""

    def __init__(self, name: str, market_type: MarketType):
        self.name = name
        self.market_type = market_type
        self.is_trained = False
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}

    def prepare_features(self, data: List[MarketData], lookback_window: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for model training"""
        if len(data) < lookback_window + 1:
            return np.array([]), np.array([])

        # Extract price data
        prices = np.array([d.close_price for d in data])
        volumes = np.array([d.volume for d in data])
        highs = np.array([d.high for d in data])
        lows = np.array([d.low for d in data])

        # Calculate technical indicators
        features = []

        for i in range(lookback_window, len(data)):
            window_data = prices[i-lookback_window:i+1]
            window_volume = volumes[i-lookback_window:i+1]

            # Price-based features
            features.append([
                window_data[-1],  # Current price
                np.mean(window_data),  # SMA
                np.std(window_data),  # Volatility
                (window_data[-1] - window_data[0]) / window_data[0],  # Return
                np.max(window_data) / window_data[-1] - 1,  # Distance from high
                window_data[-1] / np.min(window_data) - 1,  # Distance from low
                np.mean(window_volume),  # Average volume
                np.std(window_volume),  # Volume volatility
            ])

            # Add technical indicators if enough data
            if i >= 50:
                rsi_values = TechnicalIndicators.rsi(prices[:i+1])
                if len(rsi_values) > 0:
                    features[-1].append(rsi_values[-1])

                # MACD
                macd_line, signal_line, histogram = TechnicalIndicators.macd(prices[:i+1])
                if len(macd_line) > 0:
                    features[-1].append(macd_line[-1])
                    features[-1].append(signal_line[-1])

        features = np.array(features)
        targets = prices[lookback_window+1:] if len(prices) > lookback_window+1 else np.array([])

        return features, targets

    def train(self, training_data: List[MarketData]) -> bool:
        """Train the model on historical data"""
        raise NotImplementedError

    def predict(self, data: List[MarketData], horizon: int = 1) -> List[float]:
        """Make predictions for future time periods"""
        raise NotImplementedError


class ARIMAMarketModel(MarketModel):
    """ARIMA model for market prediction"""

    def __init__(self, market_type: MarketType, order: Tuple[int, int, int] = (1, 1, 1)):
        super().__init__("arima_model", market_type)
        self.order = order

    def train(self, training_data: List[MarketData]) -> bool:
        """Train ARIMA model"""
        try:
            if len(training_data) < 50:
                logger.warning("Insufficient data for ARIMA training")
                return False

            prices = np.array([d.close_price for d in training_data])

            # Use linear regression as simplified ARIMA
            self.model = LinearRegression()
            X = np.arange(len(prices)).reshape(-1, 1)
            self.model.fit(X, prices)

            self.is_trained = True
            logger.info(f"ARIMA model trained for {self.market_type.value}")
            return True

        except Exception as e:
            logger.error(f"Error training ARIMA model: {e}")
            return False

    def predict(self, data: List[MarketData], horizon: int = 1) -> List[float]:
        """Make ARIMA predictions"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")

        predictions = []
        last_index = len(data)

        for h in range(horizon):
            future_index = np.array([[last_index + h]])
            pred = self.model.predict(future_index)[0]
            predictions.append(pred)

        return predictions


class MLMarketModel(MarketModel):
    """Machine Learning model for market prediction"""

    def __init__(self, market_type: MarketType):
        super().__init__("ml_model", market_type)
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)

    def train(self, training_data: List[MarketData]) -> bool:
        """Train ML model"""
        try:
            if len(training_data) < 100:
                logger.warning("Insufficient data for ML training")
                return False

            features, targets = self.prepare_features(training_data)

            if len(features) == 0 or len(targets) == 0:
                return False

            # Scale features
            features_scaled = self.scaler.fit_transform(features)

            # Train model
            self.model.fit(features_scaled, targets)

            # Calculate feature importance
            feature_names = [
                'price', 'sma', 'volatility', 'return', 'dist_from_high',
                'dist_from_low', 'avg_volume', 'volume_volatility'
            ]

            if features_scaled.shape[1] > 8:
                feature_names.extend(['rsi', 'macd', 'signal'])

            importance_dict = dict(zip(feature_names, self.model.feature_importances_))
            self.feature_importance = importance_dict

            self.is_trained = True
            logger.info(f"ML model trained for {self.market_type.value}")
            return True

        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            return False

    def predict(self, data: List[MarketData], horizon: int = 1) -> List[float]:
        """Make ML predictions"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")

        features, _ = self.prepare_features(data)

        if len(features) == 0:
            return []

        features_scaled = self.scaler.transform(features)
        predictions = self.model.predict(features_scaled)

        # Return predictions for the specified horizon
        return predictions[-horizon:].tolist() if len(predictions) >= horizon else predictions.tolist()


class MarketPredictor:
    """Main market prediction system"""

    def __init__(self):
        self.models: Dict[str, MarketModel] = {}
        self.market_data: Dict[str, List[MarketData]] = defaultdict(list)
        self.predictions: List[MarketPrediction] = []
        self.signals: List[MarketSignal] = []
        self.technical_analyzer = TechnicalIndicators()

    def add_market_data(self, data: MarketData):
        """Add new market data point"""
        symbol_key = f"{data.symbol}_{data.market_type.value}"
        self.market_data[symbol_key].append(data)

        # Keep only recent data (last 1000 points)
        if len(self.market_data[symbol_key]) > 1000:
            self.market_data[symbol_key] = self.market_data[symbol_key][-1000:]

    def train_model(self, symbol: str, market_type: MarketType, model_type: str = "ml") -> bool:
        """Train a prediction model for a specific market"""
        symbol_key = f"{symbol}_{market_type.value}"

        if symbol_key not in self.market_data:
            logger.error(f"No data available for {symbol}")
            return False

        # Create model
        if model_type == "arima":
            model = ARIMAMarketModel(market_type)
        else:
            model = MLMarketModel(market_type)

        # Train model
        success = model.train(self.market_data[symbol_key])

        if success:
            model_key = f"{symbol}_{market_type.value}_{model_type}"
            self.models[model_key] = model
            logger.info(f"Model trained successfully for {symbol}")

        return success

    async def predict_market(self, symbol: str, market_type: MarketType,
                           horizon: int = 24, model_type: str = "ml") -> List[MarketPrediction]:
        """Predict market movements"""
        symbol_key = f"{symbol}_{market_type.value}"
        model_key = f"{symbol}_{market_type.value}_{model_type}"

        if model_key not in self.models:
            logger.error(f"Model not trained for {symbol}")
            return []

        if symbol_key not in self.market_data:
            logger.error(f"No data available for {symbol}")
            return []

        model = self.models[model_key]
        data = self.market_data[symbol_key]

        try:
            # Make price predictions
            price_predictions = model.predict(data, horizon)

            predictions = []
            current_price = data[-1].close_price

            for i, pred_price in enumerate(price_predictions):
                # Calculate confidence based on model performance
                confidence = self._calculate_confidence(model, data)

                # Calculate support and resistance
                prices = np.array([d.close_price for d in data])
                support_levels, resistance_levels = TechnicalIndicators.support_resistance(prices)

                # Calculate risk metrics
                volatility = TechnicalIndicators.volatility(prices)[-1] if len(prices) > 20 else 0.1
                expected_return = (pred_price - current_price) / current_price

                prediction = MarketPrediction(
                    symbol=symbol,
                    market_type=market_type,
                    prediction_type="price",
                    timestamp=datetime.now(),
                    prediction_horizon=horizon,
                    predicted_value=pred_price,
                    confidence=confidence,
                    support_level=min(support_levels) if support_levels else current_price * 0.95,
                    resistance_level=max(resistance_levels) if resistance_levels else current_price * 1.05,
                    stop_loss=current_price * (1 - 2 * volatility),
                    take_profit=pred_price if expected_return > 0 else current_price * 1.02,
                    technical_indicators=self._get_current_indicators(prices),
                    risk_metrics={
                        "volatility": volatility,
                        "expected_return": expected_return,
                        "var_95": current_price * (1 - 1.96 * volatility)
                    }
                )

                predictions.append(prediction)

            # Store predictions
            self.predictions.extend(predictions)

            return predictions

        except Exception as e:
            logger.error(f"Error predicting market for {symbol}: {e}")
            return []

    def generate_trading_signals(self, predictions: List[MarketPrediction]) -> List[MarketSignal]:
        """Generate trading signals from predictions"""
        signals = []

        for pred in predictions:
            current_price = pred.predicted_value / (1 + pred.risk_metrics.get("expected_return", 0))
            expected_return = pred.risk_metrics.get("expected_return", 0)
            confidence = pred.confidence

            # Determine signal type
            if expected_return > 0.02 and confidence > 0.7:  # Strong buy
                signal_type = "BUY"
                strength = min(confidence * (expected_return / 0.1), 1.0)
            elif expected_return > 0.005 and confidence > 0.5:  # Weak buy
                signal_type = "BUY"
                strength = confidence * 0.5
            elif expected_return < -0.02 and confidence > 0.7:  # Strong sell
                signal_type = "SELL"
                strength = min(confidence * (abs(expected_return) / 0.1), 1.0)
            elif expected_return < -0.005 and confidence > 0.5:  # Weak sell
                signal_type = "SELL"
                strength = confidence * 0.5
            else:  # Hold
                signal_type = "HOLD"
                strength = confidence * 0.3

            # Calculate risk-reward ratio
            risk = abs(current_price - pred.stop_loss) if pred.stop_loss else abs(current_price) * 0.05
            reward = abs(pred.take_profit - current_price) if pred.take_profit else abs(current_price) * 0.05
            risk_reward_ratio = reward / risk if risk > 0 else 1.0

            signal = MarketSignal(
                signal_id=f"signal_{pred.symbol}_{datetime.now().timestamp()}",
                symbol=pred.symbol,
                signal_type=signal_type,
                strength=strength,
                timestamp=datetime.now(),
                entry_price=current_price,
                target_price=pred.take_profit,
                stop_loss=pred.stop_loss,
                reasoning=self._generate_signal_reasoning(pred),
                confidence=confidence,
                expected_return=expected_return,
                risk_reward_ratio=risk_reward_ratio
            )

            signals.append(signal)

        # Store signals
        self.signals.extend(signals)

        return signals

    def get_market_summary(self, symbol: str, market_type: MarketType) -> Dict[str, Any]:
        """Get comprehensive market summary"""
        symbol_key = f"{symbol}_{market_type.value}"

        if symbol_key not in self.market_data or not self.market_data[symbol_key]:
            return {}

        data = self.market_data[symbol_key]
        prices = [d.close_price for d in data]
        volumes = [d.volume for d in data]

        # Calculate basic statistics
        current_price = prices[-1]
        price_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) > 1 else 0
        volume = volumes[-1] if volumes else 0
        avg_volume = np.mean(volumes) if volumes else 0

        # Technical indicators
        volatility = TechnicalIndicators.volatility(np.array(prices))[-1] if len(prices) > 20 else 0
        rsi_values = TechnicalIndicators.rsi(np.array(prices))
        current_rsi = rsi_values[-1] if len(rsi_values) > 0 else 50

        # Support and resistance
        support_levels, resistance_levels = TechnicalIndicators.support_resistance(np.array(prices))
        nearest_support = max(support_levels) if support_levels else current_price * 0.95
        nearest_resistance = min(resistance_levels) if resistance_levels else current_price * 1.05

        # Recent predictions
        recent_predictions = [p for p in self.predictions
                            if p.symbol == symbol and p.market_type == market_type
                            and (datetime.now() - p.timestamp).total_seconds() < 3600]

        summary = {
            "symbol": symbol,
            "market_type": market_type.value,
            "current_price": current_price,
            "price_change": price_change,
            "volume": volume,
            "avg_volume": avg_volume,
            "volatility": volatility,
            "rsi": current_rsi,
            "support_level": nearest_support,
            "resistance_level": nearest_resistance,
            "price_to_support": (current_price - nearest_support) / nearest_support,
            "resistance_to_price": (nearest_resistance - current_price) / current_price,
            "recent_predictions": len(recent_predictions),
            "prediction_trend": "bullish" if recent_predictions and
                               np.mean([p.predicted_value for p in recent_predictions]) > current_price else "bearish"
        }

        return summary

    def _calculate_confidence(self, model: MarketModel, data: List[MarketData]) -> float:
        """Calculate prediction confidence"""
        try:
            if len(data) < 50:
                return 0.5

            # Simple confidence based on recent accuracy
            features, targets = model.prepare_features(data[-50:])

            if len(features) == 0 or len(targets) == 0:
                return 0.5

            features_scaled = model.scaler.transform(features)
            predictions = model.model.predict(features_scaled)

            # Calculate accuracy
            mae = mean_absolute_error(targets, predictions)
            target_range = np.max(targets) - np.min(targets)

            if target_range > 0:
                accuracy = max(0, 1 - (mae / target_range))
                return accuracy

        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")

        return 0.5

    def _get_current_indicators(self, prices: np.ndarray) -> Dict[str, float]:
        """Get current technical indicator values"""
        indicators = {}

        try:
            if len(prices) > 14:
                rsi_values = TechnicalIndicators.rsi(prices)
                if len(rsi_values) > 0:
                    indicators["rsi"] = rsi_values[-1]

            if len(prices) > 26:
                macd_line, signal_line, histogram = TechnicalIndicators.macd(prices)
                if len(macd_line) > 0:
                    indicators["macd"] = macd_line[-1]
                    indicators["signal"] = signal_line[-1]
                    indicators["histogram"] = histogram[-1]

            if len(prices) > 20:
                bb_lower, bb_middle, bb_upper = TechnicalIndicators.bollinger_bands(prices)
                if len(bb_middle) > 0:
                    indicators["bb_upper"] = bb_upper[-1]
                    indicators["bb_middle"] = bb_middle[-1]
                    indicators["bb_lower"] = bb_lower[-1]

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")

        return indicators

    def _generate_signal_reasoning(self, prediction: MarketPrediction) -> str:
        """Generate reasoning for trading signal"""
        reasons = []

        expected_return = prediction.risk_metrics.get("expected_return", 0)
        volatility = prediction.risk_metrics.get("volatility", 0)

        if expected_return > 0.05:
            reasons.append("Strong positive expected return")
        elif expected_return > 0.02:
            reasons.append("Moderate positive expected return")
        elif expected_return < -0.02:
            reasons.append("Negative expected return")

        if volatility > 0.3:
            reasons.append("High volatility - increased risk")
        elif volatility < 0.1:
            reasons.append("Low volatility - stable conditions")

        if prediction.confidence > 0.8:
            reasons.append("High model confidence")
        elif prediction.confidence < 0.5:
            reasons.append("Low model confidence")

        # Technical indicators
        rsi = prediction.technical_indicators.get("rsi", 50)
        if rsi < 30:
            reasons.append("Oversold conditions (RSI)")
        elif rsi > 70:
            reasons.append("Overbought conditions (RSI)")

        return "; ".join(reasons) if reasons else "Based on model prediction"


# Singleton instance
_market_predictor = None

def get_market_predictor() -> MarketPredictor:
    """Get the singleton market predictor instance"""
    global _market_predictor
    if _market_predictor is None:
        _market_predictor = MarketPredictor()
    return _market_predictor


async def main():
    """Example usage of the market predictor"""
    predictor = get_market_predictor()

    # Generate sample market data
    base_price = 100
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]

    for i, ts in enumerate(timestamps):
        # Simulate price movement with trend and volatility
        trend = 0.001 * i  # Slight upward trend
        noise = np.random.normal(0, 2)
        price = base_price + trend + noise

        # Simulate volume
        volume = np.random.lognormal(10, 1)

        market_data = MarketData(
            symbol="GOLD",
            market_type=MarketType.COMMODITIES,
            timestamp=ts,
            price=price,
            volume=volume,
            high=price * 1.02,
            low=price * 0.98,
            open_price=price,
            close_price=price,
            bid_ask_spread=price * 0.001
        )

        predictor.add_market_data(market_data)

    print("Training market model...")
    success = predictor.train_model("GOLD", MarketType.COMMODITIES, "ml")
    print(f"Training successful: {success}")

    if success:
        print("\nMaking market predictions...")
        predictions = await predictor.predict_market("GOLD", MarketType.COMMODITIES, horizon=12)

        for pred in predictions[:5]:  # Show first 5 predictions
            print(f"{pred.symbol} ({pred.market_type.value}): "
                  f"${pred.predicted_value:.2f} in {pred.prediction_horizon}h "
                  f"(confidence: {pred.confidence:.2f})")

        print("\nGenerating trading signals...")
        signals = predictor.generate_trading_signals(predictions)
        for signal in signals[:3]:  # Show first 3 signals
            print(f"{signal.signal_type} {signal.symbol}: "
                  f"strength={signal.strength:.2f}, confidence={signal.confidence:.2f}")

        print("\nMarket summary:")
        summary = predictor.get_market_summary("GOLD", MarketType.COMMODITIES)
        for key, value in summary.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())