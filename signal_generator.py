"""
Модуль для генерации торговых сигналов
Комбинирует технические индикаторы для выработки рекомендаций
"""
import numpy as np
import pandas as pd
from config import SIGNAL_CONFIG, RISK_CONFIG, INDICATORS_CONFIG
from indicator_analysis import IndicatorAnalyzer
from ml_models import MLPredictor, TrendPredictor
from utils import get_logger

logger = get_logger('SignalGenerator')

class SignalGenerator:
    """
    Генератор торговых сигналов на основе множества признаков
    """
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.indicator_analyzer = IndicatorAnalyzer()
        self.ml_predictor = MLPredictor(symbol)
        self.logger = get_logger(f'SignalGenerator.{symbol}')
    
    def generate_signal(self, df, features=None):
        """
        Сгенерировать торговый сигнал
        
        Args:
            df: DataFrame с OHLCV и индикаторами
            features: опционально, признаки для ML модели
        
        Returns:
            dict с сигналом и доп. информацией
        """
        try:
            if df.empty or len(df) < 50:
                self.logger.warning(f"Недостаточно данных для {self.symbol}")
                return self._create_hold_signal()
            
            # Рассчитать компоненты сигнала
            components = self._analyze_indicators(df)
            
            # Добавить ML предсказание если доступно
            if features is not None and SIGNAL_CONFIG['USE_ML_MODEL']:
                ml_prediction = self.ml_predictor.predict_direction(features)
                components['ml_direction'] = ml_prediction['direction']
                components['ml_confidence'] = ml_prediction['confidence']
            
            # Комбинировать сигналы
            signal = self._combine_signals(components, df)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации сигнала: {e}")
            return self._create_hold_signal()
    
    def _analyze_indicators(self, df):
        """Проанализировать технические индикаторы"""
        components = {}
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values
        
        # === ТРЕНД АНАЛИЗ ===
        trend = self.indicator_analyzer.identify_trend(close)
        components['trend'] = trend
        
        # === СКОЛЬЗЯЩИЕ СРЕДНИЕ ===
        sma_fast = df['SMA_FAST'].iloc[-1] if 'SMA_FAST' in df else None
        sma_slow = df['SMA_SLOW'].iloc[-1] if 'SMA_SLOW' in df else None
        current_price = close[-1]
        
        if sma_fast and sma_slow:
            components['price_above_fast_ma'] = current_price > sma_fast
            components['price_above_slow_ma'] = current_price > sma_slow
            components['fast_ma_above_slow'] = sma_fast > sma_slow
        
        # === RSI АНАЛИЗ ===
        rsi = df['RSI'].iloc[-1] if 'RSI' in df else None
        if rsi:
            components['rsi_value'] = rsi
            if rsi > INDICATORS_CONFIG['RSI_OVERBOUGHT']:
                components['rsi_signal'] = 'overbought'
            elif rsi < INDICATORS_CONFIG['RSI_OVERSOLD']:
                components['rsi_signal'] = 'oversold'
            else:
                components['rsi_signal'] = 'neutral'
        
        # === MACD АНАЛИЗ ===
        macd = df['MACD'].iloc[-1] if 'MACD' in df else None
        macd_signal = df['MACD_SIGNAL'].iloc[-1] if 'MACD_SIGNAL' in df else None
        macd_hist = df['MACD_HISTOGRAM'].iloc[-1] if 'MACD_HISTOGRAM' in df else None
        
        if macd and macd_signal:
            components['macd_above_signal'] = macd > macd_signal
            if macd_hist and len(df) > 2:
                prev_hist = df['MACD_HISTOGRAM'].iloc[-2]
                components['macd_histogram_turning'] = (
                    (macd_hist > 0 and prev_hist < 0) or  # Going positive
                    (macd_hist < 0 and prev_hist > 0)     # Going negative
                )
        
        # === BOLLINGER BANDS АНАЛИЗ ===
        bb_upper = df['BB_UPPER'].iloc[-1] if 'BB_UPPER' in df else None
        bb_lower = df['BB_LOWER'].iloc[-1] if 'BB_LOWER' in df else None
        bb_middle = df['BB_MIDDLE'].iloc[-1] if 'BB_MIDDLE' in df else None
        
        if bb_upper and bb_lower:
            components['price_at_bb_upper'] = current_price > bb_upper
            components['price_at_bb_lower'] = current_price < bb_lower
            if bb_middle:
                components['price_above_bb_middle'] = current_price > bb_middle
        
        # === STOCHASTIC АНАЛИЗ ===
        stoch_k = df['STOCH_K'].iloc[-1] if 'STOCH_K' in df else None
        stoch_d = df['STOCH_D'].iloc[-1] if 'STOCH_D' in df else None
        
        if stoch_k and stoch_d:
            components['stoch_k'] = stoch_k
            if stoch_k > 80:
                components['stoch_signal'] = 'overbought'
            elif stoch_k < 20:
                components['stoch_signal'] = 'oversold'
            else:
                components['stoch_signal'] = 'neutral'
            
            if len(df) > 1:
                prev_k = df['STOCH_K'].iloc[-2]
                prev_d = df['STOCH_D'].iloc[-2]
                # Проверить пересечение
                if prev_k < prev_d and stoch_k > stoch_d:
                    components['stoch_bullish_cross'] = True
                elif prev_k > prev_d and stoch_k < stoch_d:
                    components['stoch_bearish_cross'] = True
        
        # === ATR АНАЛИЗ (Волатильность) ===
        atr = df['ATR'].iloc[-1] if 'ATR' in df else None
        if atr:
            atr_percent = (atr / current_price) * 100
            components['volatility'] = atr_percent
            components['high_volatility'] = atr_percent > 3
        
        # === VOLUME АНАЛИЗ ===
        volume = df['Volume'].values
        if len(volume) > 20:
            avg_volume = np.mean(volume[-20:])
            current_volume = volume[-1]
            components['volume_above_avg'] = current_volume > avg_volume * 1.2
        
        # === OBV АНАЛИЗ ===
        obv = df['OBV'].iloc[-1] if 'OBV' in df else None
        if obv and len(df) > 1:
            prev_obv = df['OBV'].iloc[-2]
            components['obv_increasing'] = obv > prev_obv
        
        # === Поддержка/Сопротивление ===
        support_resistance = self.indicator_analyzer.find_support_resistance(close)
        components['support'] = support_resistance['support']
        components['resistance'] = support_resistance['resistance']
        components['distance_to_support_pct'] = support_resistance['distance_to_support']
        components['distance_to_resistance_pct'] = support_resistance['distance_to_resistance']
        
        return components
    
    def _combine_signals(self, components, df):
        """Комбинировать компоненты в финальный сигнал"""
        
        buy_score = 0
        sell_score = 0
        total_components = 0
        
        reasons_buy = []
        reasons_sell = []
        
        # Вес каждого компонента
        weights = {
            'moving_averages': 2.0,
            'momentum': 2.0,
            'volume': 1.5,
            'volatility': 1.0,
            'trend': 2.0,
            'ml_model': 1.5,
        }
        
        # === СКОЛЬЗЯЩИЕ СРЕДНИЕ (Вес: 2.0) ===
        if components.get('price_above_fast_ma') and components.get('fast_ma_above_slow'):
            buy_score += weights['moving_averages']
            reasons_buy.append("Цена выше быстрой MA, быстрая выше медленной")
        elif not components.get('price_above_fast_ma') and not components.get('fast_ma_above_slow'):
            sell_score += weights['moving_averages']
            reasons_sell.append("Цена ниже быстрой MA, быстрая ниже медленной")
        
        # === RSI (Вес: 2.0) ===
        if components.get('rsi_signal') == 'oversold':
            buy_score += weights['momentum']
            reasons_buy.append(f"RSI перепроданность ({components['rsi_value']:.1f})")
        elif components.get('rsi_signal') == 'overbought':
            sell_score += weights['momentum']
            reasons_sell.append(f"RSI перекупленность ({components['rsi_value']:.1f})")
        
        # === MACD (Вес: 2.0) ===
        if components.get('macd_above_signal'):
            buy_score += weights['momentum'] * 0.7
            reasons_buy.append("MACD выше сигнальной линии")
        else:
            sell_score += weights['momentum'] * 0.7
            reasons_sell.append("MACD ниже сигнальной линии")
        
        if components.get('macd_histogram_turning'):
            if components.get('macd_above_signal'):
                buy_score += 1
                reasons_buy.append("MACD гистограмма разворачивается вверх")
            else:
                sell_score += 1
                reasons_sell.append("MACD гистограмма разворачивается вниз")
        
        # === STOCHASTIC (Вес: 1.5) ===
        if components.get('stoch_bullish_cross'):
            buy_score += weights['momentum'] * 0.5
            reasons_buy.append("Stochastic бычий кросс")
        elif components.get('stoch_bearish_cross'):
            sell_score += weights['momentum'] * 0.5
            reasons_sell.append("Stochastic медвежий кросс")
        
        # === ТРЕНД (Вес: 2.0) ===
        if components.get('trend') == 'uptrend':
            buy_score += weights['trend']
            reasons_buy.append("Выявлен восходящий тренд")
        elif components.get('trend') == 'downtrend':
            sell_score += weights['trend']
            reasons_sell.append("Выявлен нисходящий тренд")
        
        # === BOLLINGER BANDS (Вес: 1.5) ===
        if components.get('price_at_bb_lower') and components.get('price_above_bb_middle'):
            buy_score += 1.5
            reasons_buy.append("Цена отскочила от нижней BB")
        elif components.get('price_at_bb_upper') and not components.get('price_above_bb_middle'):
            sell_score += 1.5
            reasons_sell.append("Цена достигла верхней BB")
        
        # === ОБЪЕМ (Вес: 1.5) ===
        if components.get('volume_above_avg') and components.get('trend') in ['uptrend']:
            buy_score += weights['volume'] * 0.5
            reasons_buy.append("Объем выше среднего на растущем тренде")
        
        # === ML МОДЕЛЬ (Вес: 1.5) ===
        if components.get('ml_direction') == 'up':
            buy_score += weights['ml_model'] * (components.get('ml_confidence', 0.5))
            reasons_buy.append(f"ML предсказывает рост ({components.get('ml_confidence', 0)*100:.0f}%)")
        elif components.get('ml_direction') == 'down':
            sell_score += weights['ml_model'] * (components.get('ml_confidence', 0.5))
            reasons_sell.append(f"ML предсказывает падение ({components.get('ml_confidence', 0)*100:.0f}%)")
        
        # === ОЦЕНКА ВОЛАТИЛЬНОСТИ (Вес: 1.0) ===
        if components.get('high_volatility'):
            # При высокой волатильности быть осторожнее
            buy_score *= 0.8
            sell_score *= 0.8
        
        # === РАССТОЯНИЕ ДО УРОВНЕЙ (Вес: 1.0) ===
        if components.get('distance_to_support_pct', 100) < 2:
            # Близко к поддержке
            buy_score += weights['volatility'] * 0.5
            reasons_buy.append(f"Близко к поддержке ({components['distance_to_support_pct']:.1f}%)")
        
        if components.get('distance_to_resistance_pct', 100) < 2:
            # Близко к сопротивлению
            sell_score += weights['volatility'] * 0.5
            reasons_sell.append(f"Близко к сопротивлению ({components['distance_to_resistance_pct']:.1f}%)")
        
        # === НОРМАЛИЗАЦИЯ === 
        total_score = buy_score + sell_score
        
        if total_score > 0:
            buy_confidence = buy_score / total_score
            sell_confidence = sell_score / total_score
        else:
            buy_confidence = 0.5
            sell_confidence = 0.5
        
        # === ИТОГОВЫЙ СИГНАЛ ===
        if buy_confidence >= SIGNAL_CONFIG['SIGNAL_STRENGTH_BUY']:
            if buy_confidence >= 0.8:
                signal = 'STRONG_BUY'
            else:
                signal = 'BUY'
        elif sell_confidence >= SIGNAL_CONFIG['SIGNAL_STRENGTH_SELL']:
            if sell_confidence >= 0.8:
                signal = 'STRONG_SELL'
            else:
                signal = 'SELL'
        else:
            signal = 'HOLD'
        
        # === УПРАВЛЕНИЕ РИСКАМИ ===
        current_price = df['Close'].iloc[-1]
        atr = df['ATR'].iloc[-1] if 'ATR' in df else None
        
        stop_loss = None
        take_profit = None
        
        if atr:
            if signal in ['BUY', 'STRONG_BUY']:
                stop_loss = current_price - atr * 2
                take_profit = current_price + atr * 2
            elif signal in ['SELL', 'STRONG_SELL']:
                stop_loss = current_price + atr * 2
                take_profit = current_price - atr * 2
        
        # === ФОРМИРОВАНИЕ ОТВЕТА ===
        return {
            'symbol': self.symbol,
            'signal': signal,
            'confidence': max(buy_confidence, sell_confidence),
            'price': float(current_price),
            'timestamp': pd.Timestamp.now(),
            'buy_score': float(buy_score),
            'sell_score': float(sell_score),
            'buy_reasons': reasons_buy,
            'sell_reasons': reasons_sell,
            'stop_loss': float(stop_loss) if stop_loss else None,
            'take_profit': float(take_profit) if take_profit else None,
            'components': components,
            'recommendation': self._create_recommendation(signal, current_price, stop_loss, take_profit)
        }
    
    def _create_recommendation(self, signal, price, stop_loss, take_profit):
        """Создать текстовую рекомендацию"""
        if signal == 'STRONG_BUY':
            return f"СИЛЬНЫЙ СИГНАЛ ПОКУПКИ! Входить на {price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}"
        elif signal == 'BUY':
            return f"Сигнал покупки. Цена: {price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}"
        elif signal == 'STRONG_SELL':
            return f"СИЛЬНЫЙ СИГНАЛ ПРОДАЖИ! Выходить на {price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}"
        elif signal == 'SELL':
            return f"Сигнал продажи. Цена: {price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}"
        else:
            return f"Нейтральный сигнал. Текущая цена: {price:.2f}"
    
    def _create_hold_signal(self):
        """Создать нейтральный сигнал HOLD"""
        return {
            'symbol': self.symbol,
            'signal': 'HOLD',
            'confidence': 0.5,
            'price': None,
            'timestamp': pd.Timestamp.now(),
            'buy_score': 0,
            'sell_score': 0,
            'buy_reasons': [],
            'sell_reasons': [],
            'stop_loss': None,
            'take_profit': None,
            'recommendation': 'Недостаточно данных для анализа'
        }
