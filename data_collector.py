"""
Модуль для сбора и управления рыночными данными
Загружает исторические данные и обновляет цены
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import pytz

from config import DATA_DIR, HISTORY_DAYS, ASSETS
from utils import get_logger, get_utc_time, save_json, load_json

logger = get_logger('DataCollector')

class DataCollector:
    """Сборщик рыночных данных"""
    
    def __init__(self):
        self.data = {}
        self.last_update = {}
        self.logger = get_logger('DataCollector')
    
    def download_historical_data(self, symbol, days=HISTORY_DAYS, interval='1d'):
        """
        Загрузить исторические данные для активов
        
        Args:
            symbol: Тикер актива (например, 'AAPL', 'BTC-USD')
            days: Количество дней истории
            interval: Интервал (1d, 1h, 15m и т.д.)
        
        Returns:
            pd.DataFrame с историческими данными или None
        """
        try:
            self.logger.info(f"Загрузка данных для {symbol}...")
            
            # Установить период
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Загрузить данные с yfinance
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False,
                timeout=30
            )
            
            if df.empty:
                self.logger.error(f"Не удалось загрузить данные для {symbol}")
                return None
            
            # Переименовать колонки
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
            
            # Сохранить локально
            self._save_data(symbol, df)
            
            self.data[symbol] = df
            self.last_update[symbol] = get_utc_time()
            
            self.logger.info(f"Загружено {len(df)} записей для {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке данных {symbol}: {e}")
            return None
    
    def get_latest_price(self, symbol):
        """
        Получить последнюю цену актива
        
        Args:
            symbol: Тикер актива
        
        Returns:
            float - последняя цена или None
        """
        try:
            # Попытаться получить из кэшированных данных
            if symbol in self.data and not self.data[symbol].empty:
                return float(self.data[symbol]['Close'].iloc[-1])
            
            # Иначе загрузить минимум данных
            df = yf.download(symbol, periods=1, progress=False, timeout=10)
            if not df.empty:
                price = float(df['Close'].iloc[-1])
                self.logger.debug(f"Последняя цена {symbol}: ${price:.2f}")
                return price
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении цены {symbol}: {e}")
            return None
    
    def update_data(self, symbol, interval='1d'):
        """
        Обновить данные для символа (добавить новые свечи)
        
        Args:
            symbol: Тикер актива
            interval: Интервал данных
        """
        try:
            # Если данные не загружены, загрузить полную историю
            if symbol not in self.data or self.data[symbol].empty:
                return self.download_historical_data(symbol)
            
            # Иначе обновить последние данные
            last_date = self.data[symbol].index[-1]
            df_new = yf.download(
                symbol,
                start=last_date,
                end=datetime.now(),
                interval=interval,
                progress=False,
                timeout=30
            )
            
            if not df_new.empty:
                df_new.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
                # Объединить данные, удалить дубликаты
                self.data[symbol] = pd.concat([self.data[symbol], df_new])
                self.data[symbol] = self.data[symbol][~self.data[symbol].index.duplicated(keep='last')]
                self.last_update[symbol] = get_utc_time()
                
                self.logger.info(f"Данные для {symbol} обновлены")
                self._save_data(symbol, self.data[symbol])
            
            return self.data[symbol]
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении {symbol}: {e}")
            return None
    
    def get_data(self, symbol, lookback=None):
        """
        Получить данные для символа
        
        Args:
            symbol: Тикер актива
            lookback: Количество последних свечей (или None для всех)
        
        Returns:
            pd.DataFrame с данными
        """
        if symbol not in self.data or self.data[symbol].empty:
            self.download_historical_data(symbol)
        
        if symbol in self.data:
            df = self.data[symbol].copy()
            if lookback:
                return df.tail(lookback)
            return df
        
        return pd.DataFrame()
    
    def _save_data(self, symbol, df):
        """Сохранить данные в CSV локально"""
        try:
            filename = DATA_DIR / f"{symbol.replace('-', '_')}.csv"
            df.to_csv(filename)
            self.logger.debug(f"Данные {symbol} сохранены в {filename}")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении данных {symbol}: {e}")
    
    def load_local_data(self, symbol):
        """Загрузить локально сохраненные данные"""
        try:
            filename = DATA_DIR / f"{symbol.replace('-', '_')}.csv"
            if filename.exists():
                df = pd.read_csv(filename, index_col=0, parse_dates=True)
                self.data[symbol] = df
                self.logger.info(f"Локальные данные {symbol} загружены")
                return df
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке локальных данных {symbol}: {e}")
        
        return None
    
    def prepare_features(self, symbol, lookback=100):
        """
        Подготовить признаки для ML модели
        
        Args:
            symbol: Тикер актива
            lookback: Количество предыдущих свечей
        
        Returns:
            list - список признаков
        """
        try:
            df = self.get_data(symbol, lookback=lookback)
            
            if df.empty or len(df) < 20:
                return None
            
            features = []
            
            # Базовые признаки
            close_prices = df['Close'].values
            high_prices = df['High'].values
            low_prices = df['Low'].values
            volumes = df['Volume'].values
            
            # 1. Процент изменения цены за разные периоды
            for period in [1, 5, 10, 20]:
                if len(close_prices) > period:
                    pct_change = (close_prices[-1] - close_prices[-period-1]) / close_prices[-period-1]
                    features.append(pct_change)
            
            # 2. Волатильность
            returns = np.diff(close_prices) / close_prices[:-1]
            volatility = np.std(returns[-20:])
            features.append(volatility)
            
            # 3. Volume trend
            vol_ma = np.mean(volumes[-20:])
            current_vol = volumes[-1]
            features.append(current_vol / vol_ma if vol_ma > 0 else 1)
            
            # 4. Поддержка и сопротивление
            recent_high = np.max(high_prices[-20:])
            recent_low = np.min(low_prices[-20:])
            current_price = close_prices[-1]
            features.append((current_price - recent_low) / (recent_high - recent_low))
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"Ошибка при подготовке признаков {symbol}: {e}")
            return None
    
    def get_multiframe_analysis(self, symbol):
        """
        Получить мультифреймовый анализ (дневные и часовые данные)
        
        Args:
            symbol: Тикер актива
        
        Returns:
            dict с данными по разным интервалам
        """
        try:
            analysis = {}
            
            # Дневные данные
            daily = self.get_data(symbol, lookback=100)
            if not daily.empty:
                analysis['daily'] = daily
            
            # Часовые данные (если возможно)
            try:
                end = datetime.now()
                start = end - timedelta(days=7)
                hourly = yf.download(
                    symbol,
                    start=start,
                    end=end,
                    interval='1h',
                    progress=False,
                    timeout=30
                )
                if not hourly.empty:
                    hourly.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
                    analysis['hourly'] = hourly
            except:
                pass
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении мультифреймовых данных {symbol}: {e}")
            return {}
    
    def get_price_statistics(self, symbol, period=100):
        """Получить статистику цены"""
        try:
            df = self.get_data(symbol, lookback=period)
            if df.empty:
                return None
            
            closes = df['Close'].values
            
            stats = {
                'current': float(closes[-1]),
                'high_period': float(np.max(closes)),
                'low_period': float(np.min(closes)),
                'avg_period': float(np.mean(closes)),
                'volatility': float(np.std(closes) / np.mean(closes)),
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка при расчете статистики {symbol}: {e}")
            return None
