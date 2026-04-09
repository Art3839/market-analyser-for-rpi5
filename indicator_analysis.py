"""
Модуль для расчета технических индикаторов
Реализует SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic и др.
"""
import pandas as pd
import numpy as np
from config import INDICATORS_CONFIG
from utils import get_logger

logger = get_logger('IndicatorAnalysis')

class IndicatorAnalyzer:
    """Анализатор технических индикаторов"""
    
    def __init__(self, config=None):
        self.config = config or INDICATORS_CONFIG
        self.logger = get_logger('IndicatorAnalyzer')
    
    # ===== СКОЛЬЗЯЩИЕ СРЕДНИЕ =====
    
    def calculate_sma(self, prices, period):
        """
        Вычислить простую скользящую среднюю (SMA)
        
        Args:
            prices: array-like объект цен
            period: период SMA
        
        Returns:
            array с SMA значениями
        """
        prices = np.array(prices)
        if len(prices) < period:
            return np.full_like(prices, np.nan)
        
        sma = np.convolve(prices, np.ones(period)/period, mode='valid')
        # Добавить NaN в начало для выравнивания длины
        return np.concatenate([np.full(period-1, np.nan), sma])
    
    def calculate_ema(self, prices, period):
        """
        Вычислить экспоненциальную скользящую среднюю (EMA)
        
        Args:
            prices: array-like объект цен
            period: период EMA
        
        Returns:
            array с EMA значениями
        """
        prices = np.array(prices, dtype=float)
        if len(prices) < period:
            return np.full_like(prices, np.nan)
        
        ema = np.zeros_like(prices)
        ema[period-1] = np.mean(prices[:period])  # Первое значение - простая средняя
        
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(prices)):
            ema[i] = prices[i] * multiplier + ema[i-1] * (1 - multiplier)
        
        # Заполнить NaN для начальных значений
        ema[:period-1] = np.nan
        return ema
    
    # ===== MOMENTUM ИНДИКАТОРЫ =====
    
    def calculate_rsi(self, prices, period=None):
        """
        Вычислить Relative Strength Index (RSI)
        
        Args:
            prices: array-like объект цен
            period: период RSI (default из конфига)
        
        Returns:
            array с RSI значениями
        """
        period = period or self.config['RSI_PERIOD']
        prices = np.array(prices, dtype=float)
        
        if len(prices) < period + 1:
            return np.full_like(prices, np.nan)
        
        # Вычислить изменения
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        
        # Найти gains и losses
        up = np.where(seed > 0, seed, 0)
        down = np.where(seed < 0, -seed, 0)
        
        # Вычислить средние
        rs = np.zeros_like(prices)
        rs[period] = 100. - 100. / (1. + (np.sum(up) / np.sum(down)))
        
        for i in range(period+1, len(prices)):
            delta = deltas[i-1]
            
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            rs[i] = 100. - 100. / (1. + (upval/downval))
        
        # Заполнить NaN для начальных значений
        rs[:period] = np.nan
        
        return rs
    
    def calculate_macd(self, prices, fast=None, slow=None, signal=None):
        """
        Рассчитать MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: array-like объект цен
            fast, slow, signal: периоды (из конфига если не указаны)
        
        Returns:
            dict с MACD, Signal line и Histogram
        """
        fast = fast or self.config['MACD_FAST']
        slow = slow or self.config['MACD_SLOW']
        signal = signal or self.config['MACD_SIGNAL']
        
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_stochastic(self, high, low, close, k_period=14, d_period=3):
        """
        Рассчитать Stochastic Oscillator
        
        Args:
            high: array с максимальными ценами
            low: array с минимальными ценами
            close: array с ценами закрытия
            k_period: период %K
            d_period: период %D
        
        Returns:
            dict с %K и %D
        """
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        
        if len(close) < k_period:
            return {'k': np.full_like(close, np.nan), 'd': np.full_like(close, np.nan)}
        
        # Вычислить %K
        k = np.zeros_like(close)
        for i in range(k_period-1, len(close)):
            min_low = np.min(low[i-k_period+1:i+1])
            max_high = np.max(high[i-k_period+1:i+1])
            
            if max_high - min_low > 0:
                k[i] = 100 * (close[i] - min_low) / (max_high - min_low)
            else:
                k[i] = 50
        
        k[:k_period-1] = np.nan
        
        # Вычислить %D (SMA от %K)
        d = self.calculate_sma(k, d_period)
        
        return {'k': k, 'd': d}
    
    # ===== ВОЛАТИЛЬНОСТЬ =====
    
    def calculate_bollinger_bands(self, prices, period=None, std_dev=None):
        """
        Рассчитать Bollinger Bands
        
        Args:
            prices: array-like объект цен
            period: период для SMA (из конфига если не указан)
            std_dev: количество стандартных отклонений (из конфига если не указан)
        
        Returns:
            dict с upper, middle и lower bands
        """
        period = period or self.config['BB_PERIOD']
        std_dev = std_dev or self.config['BB_STD']
        
        prices = np.array(prices, dtype=float)
        
        if len(prices) < period:
            return {
                'upper': np.full_like(prices, np.nan),
                'middle': np.full_like(prices, np.nan),
                'lower': np.full_like(prices, np.nan),
                'width': np.full_like(prices, np.nan)
            }
        
        middle = self.calculate_sma(prices, period)
        
        std = np.zeros_like(prices)
        for i in range(period-1, len(prices)):
            std[i] = np.std(prices[i-period+1:i+1])
        std[:period-1] = np.nan
        
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        width = upper - lower
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'width': width
        }
    
    def calculate_atr(self, high, low, close, period=None):
        """
        Рассчитать Average True Range (ATR)
        
        Args:
            high: array с максимальными ценами
            low: array с минимальными ценами
            close: array с ценами закрытия
            period: период ATR (из конфига если не указан)
        
        Returns:
            array с ATR значениями
        """
        period = period or self.config['ATR_PERIOD']
        
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        close = np.array(close, dtype=float)
        
        if len(high) < period + 1:
            return np.full_like(close, np.nan)
        
        # Вычислить True Range
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        tr[0] = np.nan
        
        # Вычислить ATR как SMA от TR
        atr = self.calculate_sma(tr, period)
        
        return atr
    
    # ===== VOLUME индикаторы =====
    
    def calculate_obv(self, close, volume):
        """
        Рассчитать On-Balance Volume (OBV)
        
        Args:
            close: array с ценами закрытия
            volume: array с объемами
        
        Returns:
            array с OBV значениями
        """
        close = np.array(close, dtype=float)
        volume = np.array(volume, dtype=float)
        
        obv = np.zeros_like(close)
        obv[0] = volume[0]
        
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]
        
        return obv
    
    def calculate_ad_line(self, high, low, close, volume):
        """
        Рассчитать Accumulation/Distribution Line
        
        Args:
            high: array с максимальными ценами
            low: array с минимальными ценами
            close: array с ценами закрытия
            volume: array с объемами
        
        Returns:
            array с A/D значениями
        """
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        close = np.array(close, dtype=float)
        volume = np.array(volume, dtype=float)
        
        clv = ((close - low) - (high - close)) / (high - low + 1e-10)
        ad = np.cumsum(clv * volume)
        
        return ad
    
    # ===== ТРЕНД =====
    
    def identify_trend(self, prices, fast_period=None, slow_period=None):
        """
        Определить тренд на основе скользящих средних
        
        Args:
            prices: array-like объект цен
            fast_period: период быстрой SMA
            slow_period: период медленной SMA
        
        Returns:
            str - 'uptrend', 'downtrend' или 'sideways'
        """
        fast_period = fast_period or self.config['SMA_FAST']
        slow_period = slow_period or self.config['SMA_SLOW']
        
        prices = np.array(prices)
        
        sma_fast = self.calculate_sma(prices, fast_period)
        sma_slow = self.calculate_sma(prices, slow_period)
        
        # Использовать последние значения
        current_price = prices[-1]
        fast_val = sma_fast[-1]
        slow_val = sma_slow[-1]
        
        if fast_val > slow_val and current_price > fast_val:
            return 'uptrend'
        elif fast_val < slow_val and current_price < fast_val:
            return 'downtrend'
        else:
            return 'sideways'
    
    def calculate_adx(self, high, low, close, period=14):
        """
        Рассчитать Average Directional Index (ADX)
        
        Args:
            high: array с максимальными ценами
            low: array с минимальными ценами
            close: array с ценами закрытия
            period: период ADX
        
        Returns:
            array с ADX значениями
        """
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        
        if len(high) < period:
            return np.full_like(high, np.nan)
        
        # Вычислить направленные движения
        plus_dm = np.zeros_like(high)
        minus_dm = np.zeros_like(high)
        
        for i in range(1, len(high)):
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
        
        # Вычислить ATR
        atr = self.calculate_atr(high, low, close, period)
        
        # Вычислить DI+, DI-
        di_plus = 100 * self.calculate_sma(plus_dm, period) / (atr + 1e-10)
        di_minus = 100 * self.calculate_sma(minus_dm, period) / (atr + 1e-10)
        
        # Вычислить DX
        dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        
        # Вычислить ADX
        adx = self.calculate_sma(dx, period)
        
        return adx
    
    # ===== АНАЛИЗ УРОВНЕЙ ПОДДЕРЖКИ/СОПРОТИВЛЕНИЯ =====
    
    def find_support_resistance(self, prices, window=20):
        """
        Найти уровни поддержки и сопротивления
        
        Args:
            prices: array-like объект цен
            window: размер окна для анализа
        
        Returns:
            dict с уровнями support и resistance
        """
        prices = np.array(prices)
        
        if len(prices) < window:
            return {'support': None, 'resistance': None}
        
        recent_prices = prices[-window:]
        
        support = np.percentile(recent_prices, 20)
        resistance = np.percentile(recent_prices, 80)
        
        return {
            'support': float(support),
            'resistance': float(resistance),
            'current': float(prices[-1]),
            'distance_to_support': float((prices[-1] - support) / support * 100),
            'distance_to_resistance': float((resistance - prices[-1]) / prices[-1] * 100)
        }
    
    # ===== ИНТЕГРАЛЬНЫЙ АНАЛИЗ =====
    
    def calculate_all_indicators(self, df):
        """
        Рассчитать все индикаторы для DataFrame
        
        Args:
            df: DataFrame с OHLCV данными
        
        Returns:
            DataFrame с добавленными индикаторами
        """
        try:
            df = df.copy()
            
            close = df['Close'].values
            high = df['High'].values
            low = df['Low'].values
            volume = df['Volume'].values
            
            # Скользящие средние
            df['SMA_FAST'] = self.calculate_sma(close, self.config['SMA_FAST'])
            df['SMA_SLOW'] = self.calculate_sma(close, self.config['SMA_SLOW'])
            df['EMA_FAST'] = self.calculate_ema(close, self.config['EMA_FAST'])
            df['EMA_SLOW'] = self.calculate_ema(close, self.config['EMA_SLOW'])
            
            # RSI
            df['RSI'] = self.calculate_rsi(close)
            
            # MACD
            macd_data = self.calculate_macd(close)
            df['MACD'] = macd_data['macd']
            df['MACD_SIGNAL'] = macd_data['signal']
            df['MACD_HISTOGRAM'] = macd_data['histogram']
            
            # Stochastic
            stoch = self.calculate_stochastic(high, low, close)
            df['STOCH_K'] = stoch['k']
            df['STOCH_D'] = stoch['d']
            
            # Bollinger Bands
            bb = self.calculate_bollinger_bands(close)
            df['BB_UPPER'] = bb['upper']
            df['BB_MIDDLE'] = bb['middle']
            df['BB_LOWER'] = bb['lower']
            df['BB_WIDTH'] = bb['width']
            
            # ATR
            df['ATR'] = self.calculate_atr(high, low, close)
            
            # Volume indicators
            df['OBV'] = self.calculate_obv(close, volume)
            df['AD_LINE'] = self.calculate_ad_line(high, low, close, volume)
            
            # ADX
            df['ADX'] = self.calculate_adx(high, low, close)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Ошибка при расчете индикаторов: {e}")
            return df
