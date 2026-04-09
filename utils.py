"""
Утилиты для торговой системы
"""
import logging
import json
from pathlib import Path
from datetime import datetime
import pytz

from config import LOG_CONFIG, DATA_DIR

# Настройка логирования
def setup_logging():
    """Инициализировать систему логирования"""
    logger = logging.getLogger('MarketAnalyzer')
    logger.setLevel(LOG_CONFIG['LOG_LEVEL'])
    
    # Файловый обработчик
    fh = logging.FileHandler(LOG_CONFIG['LOG_FILE'])
    fh.setLevel(logging.DEBUG)
    
    # Обработчик консоли
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logging()

def get_logger(name=None):
    """Получить логгер"""
    if name:
        return logging.getLogger(f'MarketAnalyzer.{name}')
    return logging.getLogger('MarketAnalyzer')

def get_utc_time():
    """Получить текущее UTC время"""
    return datetime.now(pytz.UTC)

def timestamp_to_datetime(ts):
    """Конвертировать timestamp в datetime"""
    return datetime.fromtimestamp(ts, tz=pytz.UTC)

def save_json(data, filename):
    """Сохранить данные в JSON файл"""
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.debug(f"Данные сохранены в {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении {filename}: {e}")

def load_json(filename):
    """Загрузить данные из JSON файла"""
    filepath = DATA_DIR / filename
    try:
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Ошибка при загрузке {filename}: {e}")
        return {}

def format_price(price):
    """Форматировать цену"""
    if price is None:
        return "N/A"
    if price > 1000:
        return f"${price:,.2f}"
    return f"${price:.2f}"

def format_percent(percent):
    """Форматировать процент"""
    if percent is None:
        return "N/A"
    if percent > 0:
        return f"+{percent:.2f}%"
    return f"{percent:.2f}%"

def signal_to_emoji(signal):
    """Конвертировать сигнал в эмодзи"""
    signal_map = {
        'BUY': '📈',
        'SELL': '📉',
        'HOLD': '➡️',
        'STRONG_BUY': '🚀',
        'STRONG_SELL': '💥',
    }
    return signal_map.get(signal, '❓')

def calculate_rsi(prices, period=14):
    """Вычислить RSI (в indicator_analysis.py есть полная реализация)"""
    if len(prices) < period:
        return None
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100 if avg_gain > 0 else 0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

class DataCache:
    """Кэш для хранения данных индикаторов"""
    def __init__(self):
        self.cache = {}
    
    def set(self, key, value, ttl=300):
        """Сохранить значение в кэш"""
        self.cache[key] = {
            'value': value,
            'timestamp': get_utc_time().timestamp(),
            'ttl': ttl
        }
    
    def get(self, key):
        """Получить значение из кэша"""
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        elapsed = get_utc_time().timestamp() - item['timestamp']
        
        if elapsed > item['ttl']:
            del self.cache[key]
            return None
        
        return item['value']
    
    def clear(self):
        """Очистить кэш"""
        self.cache.clear()

# Глобальный кэш
data_cache = DataCache()

class RateLimiter:
    """Ограничитель частоты запросов"""
    def __init__(self, max_calls=10, time_period=60):
        self.max_calls = max_calls
        self.time_period = time_period
        self.calls = []
    
    def is_allowed(self):
        """Проверить, разрешен ли запрос"""
        now = get_utc_time().timestamp()
        # Удалить старые вызовы
        self.calls = [c for c in self.calls if now - c < self.time_period]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

def create_signal_message(asset, signal_data):
    """Создать сообщение сигнала для Telegram"""
    symbol = asset['symbol']
    name = asset['name']
    signal = signal_data['signal']
    confidence = signal_data['confidence']
    price = signal_data['price']
    
    emoji = signal_to_emoji(signal)
    
    message = (
        f"{emoji} <b>{name} ({symbol})</b>\n"
        f"Сигнал: <b>{signal}</b>\n"
        f"Уверенность: {confidence*100:.1f}%\n"
        f"Цена: {format_price(price)}\n"
    )
    
    if 'recommendation' in signal_data:
        message += f"Рекомендация: {signal_data['recommendation']}\n"
    
    return message
