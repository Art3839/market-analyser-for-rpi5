"""
Файл конфигурации для торговой системы анализа рынка
"""
import os
from pathlib import Path

# Директория проекта
PROJECT_DIR = Path(__file__).parent

# Директория для хранения данных
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Директория для моделей
MODELS_DIR = PROJECT_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# === ПАРАМЕТРЫ СБОРА ДАННЫХ ===
# Период истории для загрузки (в днях)
HISTORY_DAYS = 365

# Период обновления цен (в минутах)
UPDATE_INTERVAL_MINUTES = 5

# === ПАРАМЕТРЫ ИНДИКАТОРОВ ===
INDICATORS_CONFIG = {
    'SMA_FAST': 20,      # Короткая скользящая средняя
    'SMA_SLOW': 50,      # Длинная скользящая средняя
    'EMA_FAST': 12,      # Экспоненциальная СА (быстрая)
    'EMA_SLOW': 26,      # Экспоненциальная СА (медленная)
    'RSI_PERIOD': 14,    # Период RSI
    'RSI_OVERBOUGHT': 70, # RSI - перекупленность
    'RSI_OVERSOLD': 30,  # RSI - перепроданность
    'MACD_FAST': 12,     # MACD - быстрая EMA
    'MACD_SLOW': 26,     # MACD - медленная EMA
    'MACD_SIGNAL': 9,    # MACD - сигнальная линия
    'BB_PERIOD': 20,     # Bollinger Bands - период
    'BB_STD': 2,         # Bollinger Bands - стандартные отклонения
    'ATR_PERIOD': 14,    # ATR - период
}

# === ПАРАМЕТРЫ ГЕНЕРАЦИИ СИГНАЛОВ ===
SIGNAL_CONFIG = {
    'SIGNAL_STRENGTH_BUY': 0.65,    # Сила сигнала на покупку (0-1)
    'SIGNAL_STRENGTH_SELL': 0.65,   # Сила сигнала на продажу (0-1)
    'MIN_CONFIDENCE': 0.55,          # Минимальная уверенность
    'USE_ML_MODEL': True,            # Использовать ML модель
}

# === ПАРАМЕТРЫ УПРАВЛЕНИЯ РИСКАМИ ===
RISK_CONFIG = {
    'MAX_LOSS_PERCENT': 5.0,        # Макс потерь в процентах
    'MIN_PROFIT_PERCENT': 1.5,      # Мин целевая прибыль в процентах
    'MAX_POSITION_SIZE_PERCENT': 10.0, # Макс размер позиции
    'STOP_LOSS_PERCENT': 3.0,       # Stop-loss в процентах
}

# === ПАРАМЕТРЫ TELEGRAM БОТА ===
TELEGRAM_CONFIG = {
    'BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),  # Получить из переменной окружения
    'CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),      # Получить из переменной окружения
    'SEND_SIGNALS': True,            # Отправлять ли сигналы
    'SEND_ERRORS': True,             # Отправлять ли ошибки
    'NOTIFY_ON_START': True,         # Уведомить при запуске
}

# === АКТИВЫ ДЛЯ АНАЛИЗА ===
ASSETS = [
    # Акции (US)
    {'symbol': 'AAPL', 'type': 'stock', 'name': 'Apple'},
    {'symbol': 'GOOGL', 'type': 'stock', 'name': 'Google'},
    {'symbol': 'MSFT', 'type': 'stock', 'name': 'Microsoft'},
    {'symbol': 'TSLA', 'type': 'stock', 'name': 'Tesla'},
    # Криптовалюты
    {'symbol': 'BTC-USD', 'type': 'crypto', 'name': 'Bitcoin'},
    {'symbol': 'ETH-USD', 'type': 'crypto', 'name': 'Ethereum'},
    # Индексы
    {'symbol': '^GSPC', 'type': 'index', 'name': 'S&P 500'},
]

# === ПАРАМЕТРЫ GUI ===
GUI_CONFIG = {
    'WINDOW_WIDTH': 1400,
    'WINDOW_HEIGHT': 900,
    'THEME': 'light',              # 'light' или 'dark'
    'UPDATE_GUI_INTERVAL': 5000,   # Интервал обновления GUI (мс)
    'SHOW_CHARTS': True,            # Показывать графики
}

# === ПАРАМЕТРЫ ЛОГИРОВАНИЯ ===
LOG_CONFIG = {
    'LOG_FILE': PROJECT_DIR / 'logs' / 'market_analyzer.log',
    'LOG_LEVEL': 'INFO',
    'MAX_LOG_FILE_SIZE': 10 * 1024 * 1024,  # 10 MB
}

# Создать директорию логов
Path(LOG_CONFIG['LOG_FILE']).parent.mkdir(exist_ok=True)

# === ПАРАМЕТРЫ ML МОДЕЛИ ===
ML_CONFIG = {
    'MODEL_TYPE': 'lightgbm',  # 'random_forest' или 'lightgbm'
    'TEST_SIZE': 0.2,
    'RANDOM_STATE': 42,
    'HYPERPARAMETERS': {
        'n_estimators': 100,
        'max_depth': 10,
        'learning_rate': 0.05,
        'num_leaves': 31,
    }
}
# === ОТСЛЕЖИВАЕМЫЕ АКТИВЫ ===
# Активы, для которых отправляются сигналы в Telegram
WATCHED_ASSETS = ['AAPL', 'MSFT', 'BTC-USD', 'ETH-USD']  # Будет сохранено в data/watched.json