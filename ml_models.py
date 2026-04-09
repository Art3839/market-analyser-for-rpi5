"""
Модуль для машинного обучения и предсказания ценовых движений
Использует LightGBM и Random Forest локально
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path

from config import MODELS_DIR, ML_CONFIG
from utils import get_logger

logger = get_logger('MLModels')

class MLPredictor:
    """
    Предсказатель ценовых движений с использованием ML
    Обучается локально на исторических данных
    """
    
    def __init__(self, symbol, model_type=None):
        self.symbol = symbol
        self.model_type = model_type or ML_CONFIG['MODEL_TYPE']
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.logger = get_logger(f'MLPredictor.{symbol}')
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Загрузить или создать новую модель"""
        model_path = MODELS_DIR / f"{self.symbol}_{self.model_type}.pkl"
        
        try:
            if model_path.exists():
                self.model = joblib.load(model_path)
                self.logger.info(f"Модель {self.symbol} загружена из {model_path}")
            else:
                self.logger.info(f"Новая модель будет создана при обучении")
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить модель: {e}")
    
    def prepare_training_data(self, df, lookback=50):
        """
        Подготовить данные для обучения
        
        Args:
            df: DataFrame с техническими индикаторами
            lookback: количество предыдущих свечей для анализа
        
        Returns:
            (X, Y) - признаки и целевые значения
        """
        try:
            X = []
            Y = []
            
            close_prices = df['Close'].values
            
            for i in range(lookback, len(df) - 5):  # 5 свечей для целевого окна
                # Окно признаков
                window = df.iloc[i-lookback:i]
                
                features = self._extract_features(window, close_prices[i])
                if features is None:
                    continue
                
                # Целевая переменная: цена выросла на 5 свечах?
                future_price = close_prices[i+5]
                current_price = close_prices[i]
                
                # 1 = ценовой рост, 0 = ценовое падение
                target = 1 if future_price > current_price * 1.01 else 0
                
                X.append(features)
                Y.append(target)
            
            if not X:
                self.logger.warning("Не удалось подготовить данные для обучения")
                return None, None
            
            X = np.array(X)
            Y = np.array(Y)
            
            self.logger.info(f"Подготовлено {len(X)} примеров для обучения")
            return X, Y
            
        except Exception as e:
            self.logger.error(f"Ошибка при подготовке данных: {e}")
            return None, None
    
    def _extract_features(self, window, current_price):
        """Извлечь признаки из окна данных"""
        try:
            close = window['Close'].values
            high = window['High'].values
            low = window['Low'].values
            volume = window['Volume'].values
            
            features = []
            
            # Технические индикаторы из окна
            # Ценовые признаки
            features.append(close[-1] / close[0])  # Price ratio
            features.append(np.mean(close))  # Average price
            features.append(np.std(close))  # Price volatility
            
            # Максимумы и минимумы
            features.append(np.max(high) - np.min(low))  # Range
            features.append((close[-1] - np.min(low)) / (np.max(high) - np.min(low)))  # Position in range
            
            # Индикаторы из DataFrame
            if 'RSI' in window.columns and not pd.isna(window['RSI'].iloc[-1]):
                features.append(window['RSI'].iloc[-1])
            else:
                features.append(50)  # Default neutral value
            
            if 'SMA_FAST' in window.columns and not pd.isna(window['SMA_FAST'].iloc[-1]):
                features.append((close[-1] - window['SMA_FAST'].iloc[-1]) / window['SMA_FAST'].iloc[-1])
            else:
                features.append(0)
            
            if 'SMA_SLOW' in window.columns and not pd.isna(window['SMA_SLOW'].iloc[-1]):
                features.append((close[-1] - window['SMA_SLOW'].iloc[-1]) / window['SMA_SLOW'].iloc[-1])
            else:
                features.append(0)
            
            if 'MACD' in window.columns and not pd.isna(window['MACD'].iloc[-1]):
                features.append(window['MACD'].iloc[-1] / close[-1])
            else:
                features.append(0)
            
            # Volume признаки
            features.append(np.mean(volume[-10:]) / (np.mean(volume) + 1e-10))
            
            return np.array(features)
            
        except Exception as e:
            self.logger.debug(f"Ошибка при извлечении признаков: {e}")
            return None
    
    def train(self, df):
        """
        Обучить модель на исторических данных
        
        Args:
            df: DataFrame с техническими индикаторами и OHLCV
        """
        try:
            self.logger.info(f"Начало обучения модели {self.symbol}...")
            
            X, Y = self.prepare_training_data(df)
            
            if X is None or len(X) < 10:
                self.logger.warning("Недостаточно данных для обучения модели")
                return False
            
            # Разделить данные
            X_train, X_test, Y_train, Y_test = train_test_split(
                X, Y,
                test_size=ML_CONFIG['TEST_SIZE'],
                random_state=ML_CONFIG['RANDOM_STATE']
            )
            
            # Масштабировать признаки
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Создать и обучить модель
            if self.model_type == 'lightgbm':
                try:
                    import lightgbm as lgb
                    self.model = lgb.LGBMClassifier(**ML_CONFIG['HYPERPARAMETERS'])
                except ImportError:
                    self.logger.warning("LightGBM не установлен, используется Random Forest")
                    self.model = RandomForestClassifier(**ML_CONFIG['HYPERPARAMETERS'])
            else:
                self.model = RandomForestClassifier(**ML_CONFIG['HYPERPARAMETERS'])
            
            # Обучить
            self.model.fit(X_train_scaled, Y_train)
            
            # Оценить
            train_score = self.model.score(X_train_scaled, Y_train)
            test_score = self.model.score(X_test_scaled, Y_test)
            
            self.logger.info(f"Обучение завершено. Train Score: {train_score:.3f}, Test Score: {test_score:.3f}")
            
            # Сохранить модель
            self._save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при обучении модели: {e}")
            return False
    
    def predict_direction(self, X):
        """
        Предсказать направление ценового движения
        
        Args:
            X: array с признаками
        
        Returns:
            dict с предсказанием и вероятностью
        """
        try:
            if self.model is None:
                return {'direction': 'unknown', 'probability': 0, 'confidence': 0}
            
            X_scaled = self.scaler.transform(X.reshape(1, -1))
            
            # Предсказание
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # 0 = down, 1 = up
            direction = 'up' if prediction == 1 else 'down'
            confidence = max(probabilities)
            
            return {
                'direction': direction,
                'probability': float(probabilities[prediction]),
                'confidence': float(confidence)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при предсказании: {e}")
            return {'direction': 'unknown', 'probability': 0, 'confidence': 0}
    
    def _save_model(self):
        """Сохранить модель локально"""
        try:
            model_path = MODELS_DIR / f"{self.symbol}_{self.model_type}.pkl"
            joblib.dump(self.model, model_path)
            
            # Также сохранить scaler
            scaler_path = MODELS_DIR / f"{self.symbol}_scaler.pkl"
            joblib.dump(self.scaler, scaler_path)
            
            self.logger.info(f"Модель сохранена в {model_path}")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении модели: {e}")
    
    def load_scaler(self):
        """Загрузить масштабировщик"""
        try:
            scaler_path = MODELS_DIR / f"{self.symbol}_scaler.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                return True
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке scaler: {e}")
        return False


class EnsemblePredictor:
    """
    Ансамблевый предсказатель, комбинирующий несколько моделей
    """
    
    def __init__(self, symbols):
        self.predictors = {}
        self.logger = get_logger('EnsemblePredictor')
        
        for symbol in symbols:
            self.predictors[symbol] = MLPredictor(symbol)
    
    def train_all(self, data_dict):
        """
        Обучить все модели
        
        Args:
            data_dict: dict {symbol: df с индикаторами}
        """
        for symbol, df in data_dict.items():
            if symbol in self.predictors:
                self.predictors[symbol].train(df)
    
    def predict_ensemble(self, symbol, features):
        """
        Получить ансамблевое предсказание
        Комбинирует несколько моделей
        
        Args:
            symbol: тикер актива
            features: array с признаками
        
        Returns:
            dict с предсказанием
        """
        try:
            if symbol not in self.predictors:
                return {'direction': 'unknown', 'confidence': 0}
            
            prediction = self.predictors[symbol].predict_direction(features)
            return prediction
            
        except Exception as e:
            self.logger.error(f"Ошибка при ансамблевом предсказании {symbol}: {e}")
            return {'direction': 'unknown', 'confidence': 0}


class TrendPredictor:
    """
    Простой предсказатель тренда на основе статистического анализа
    """
    
    @staticmethod
    def predict_trend_direction(prices, lookback=20):
        """
        Предсказать направление тренда
        
        Args:
            prices: array с ценами
            lookback: количество периодов для анализа
        
        Returns:
            dict с предсказанием
        """
        try:
            prices = np.array(prices)
            recent = prices[-lookback:]
            
            # Вычислить линейный тренд
            x = np.arange(len(recent))
            coefficients = np.polyfit(x, recent, 1)
            slope = coefficients[0]
            
            # Вычислить R-squared
            y_pred = np.polyval(coefficients, x)
            ss_res = np.sum((recent - y_pred) ** 2)
            ss_tot = np.sum((recent - np.mean(recent)) ** 2)
            r_squared = 1 - (ss_res / (ss_tot + 1e-10))
            
            # Определить направление
            if slope > 0.001:
                direction = 'uptrend'
                strength = min(abs(slope) * prices[-1], 100)
            elif slope < -0.001:
                direction = 'downtrend'
                strength = min(abs(slope) * prices[-1], 100)
            else:
                direction = 'sideways'
                strength = 0
            
            return {
                'direction': direction,
                'slope': float(slope),
                'r_squared': float(r_squared),
                'strength': float(strength / prices[-1] * 100)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при предсказании тренда: {e}")
            return {'direction': 'unknown', 'slope': 0, 'r_squared': 0, 'strength': 0}
