# Market Analyzer - Техническая документация

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Market Analyzer System                    │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
         ┌──────▼──────┐ ┌────▼────┐ ┌────▼────┐
         │    GUI      │ │   CLI   │ │ Telegram│
         │ (Tkinter)   │ │ (Daemon)│ │ (Async) │
         └──────┬──────┘ └────┬────┘ └────┬────┘
                │             │             │
                └─────────────┼─────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐  ┌──────▼──────┐  ┌───▼─────────┐
        │ Data       │  │  Signal     │  │  ML Models  │
        │ Collector  │  │  Generator  │  │  & ML       │
        └─────┬─────┘  └──────┬──────┘  │  Predictor  │
              │               │         └───┬─────────┘
              │               │             │
        ┌─────▼────────────────▼─────────────▼──────┐
        │   Indicator Analysis Engine                │
        │  (SMA, EMA, RSI, MACD, BB, ATR, etc)      │
        └─────┬──────────────────────────────────────┘
              │
        ┌─────▼────────────────────────────┐
        │   Local Data Storage (CSV)        │
        │   - Historical prices             │
        │   - Indicators cache              │
        │   - Models (PKL files)            │
        └───────────────────────────────────┘
```

## 📦 Модули системы

### 1. **config.py** - Конфигурация
- Параметры индикаторов
- Пороги сигналов
- Активы для анализа
- Параметры ML моделей
- Настройки Telegram
- Параметры GUI

```python
# Пример обращения
from config import ASSETS, INDICATORS_CONFIG, SIGNAL_CONFIG
assets = ASSETS  # Список активов
periods = INDICATORS_CONFIG['SMA_FAST']  # Период SMA
```

### 2. **utils.py** - Утилиты
- Логирование
- Работа с датами/временем
- Форматирование данных
- Кэширование
- Rate limiting

```python
# Пример обращения
from utils import get_logger, format_price, data_cache
logger = get_logger('MyModule')
logger.info("Сообщение")
price_str = format_price(150.25)  # "$150.25"
```

### 3. **data_collector.py** - Сборщик данных
Отвечает за:
- Загрузку исторических данных с yfinance
- Обновление данных
- Локальное сохранение (CSV)
- Подготовка признаков для ML

```python
# Пример использования
from data_collector import DataCollector

dc = DataCollector()

# Загрузить данные
df = dc.download_historical_data('AAPL', days=365)

# Обновить последние данные
df = dc.update_data('AAPL')

# Получить цену
price = dc.get_latest_price('AAPL')

# Подготовить признаки для ML
features = dc.prepare_features('AAPL', lookback=100)
```

### 4. **indicator_analysis.py** - Технические индикаторы
Реализует 17+ индикаторов:

```python
# Пример использования
from indicator_analysis import IndicatorAnalyzer

ia = IndicatorAnalyzer()

# Скользящие средние
sma = ia.calculate_sma(prices, period=20)
ema = ia.calculate_ema(prices, period=12)

# Momentum индикаторы
rsi = ia.calculate_rsi(prices, period=14)
macd = ia.calculate_macd(prices)

# Волатильность
bb = ia.calculate_bollinger_bands(prices)
atr = ia.calculate_atr(high, low, close)

# Рассчитать все сразу
df = ia.calculate_all_indicators(df)
```

**Поддерживаемые индикаторы:**
- SMA, EMA (скользящие средние)
- RSI (индекс относительной силы)
- MACD (схождение-расхождение)
- Stochastic (стохастический осциллятор)
- Bollinger Bands (ленты Боллинджера)
- ATR (средний истинный диапазон)
- OBV, A/D Line (объемные индикаторы)
- ADX (индекс направленного движения)

### 5. **signal_generator.py** - Генератор сигналов
Комбинирует индикаторы для создания торговых сигналов:

```python
# Пример использования
from signal_generator import SignalGenerator

sg = SignalGenerator('AAPL')
signal = sg.generate_signal(df, features=None)

# Результат:
# {
#     'signal': 'BUY',              # или SELL, HOLD, STRONG_BUY, STRONG_SELL
#     'confidence': 0.75,           # 0-1
#     'price': 150.25,
#     'buy_score': 8.5,
#     'sell_score': 2.3,
#     'buy_reasons': [...],
#     'sell_reasons': [...],
#     'stop_loss': 145.50,
#     'take_profit': 155.00,
#     'recommendation': "..."
# }
```

**Компоненты сигнала (с весами):**
- Скользящие средние (2.0x)
- RSI (2.0x)
- MACD (2.0x)
- Stochastic (1.5x)
- Bollinger Bands (1.5x)
- Тренд (2.0x)
- Объем (1.5x)
- ML модель (1.5x)
- Риски (1.0x)

### 6. **ml_models.py** - Машинное обучение
Локальные ML модели для прогнозирования:

```python
# Пример использования
from ml_models import MLPredictor, TrendPredictor, EnsemblePredictor

# Одиночная модель
predictor = MLPredictor('AAPL')
predictor.train(df)  # Обучить на исторических данных
prediction = predictor.predict_direction(features)  # Предсказать

# Ансамблевый предсказатель
ensemble = EnsemblePredictor(['AAPL', 'MSFT', 'GOOGL'])
ensemble.train_all(data_dict)

# Анализ тренда
trend = TrendPredictor.predict_trend_direction(prices)
```

**Модели:**
- LightGBM (рекомендуется на RPi)
- Random Forest

### 7. **telegram_notifier.py** - Telegram уведомления
Отправка сигналов и уведомлений:

```python
# Пример использования
from telegram_notifier import send_signal, send_status, send_error

# Отправить сигнал
send_signal(signal_data)

# Отправить статус
send_status("Система запущена")

# Отправить ошибку
send_error("Критическая ошибка!")

# Или через объект
from telegram_notifier import notifier
notifier.send_daily_report(report_data)
notifier.test_connection()
```

### 8. **gui.py** - Графический интерфейс
Легковесный Tkinter интерфейс:

```python
# Запуск GUI
from gui import run_gui
run_gui()

# Или из главной программы
python main.py --gui
```

**Функции GUI:**
- Таблица текущих сигналов
- Детальный анализ активов
- Логи системы
- Ручное обновление данных

### 9. **main.py** - Главная программа
Оркестратор всех компонентов:

```bash
# CLI режим (непрерывный анализ)
python main.py

# GUI режим
python main.py --gui

# Без инициализации
python main.py --no-init
```

## 🔄 Процесс работы системы

### Инициализация
1. Загрузка конфигурации
2. Загрузка исторических данных для всех активов
3. Обучение ML моделей
4. Подготовка к анализу

### Основной цикл (каждые 5 минут)
1. Обновить данные для каждого актива
2. Рассчитать технические индикаторы
3. Подготовить признаки для ML
4. Генерировать сигналы
5. Сравнить с предыдущим сигналом
6. Если сигнал изменился → отправить Telegram
7. Сохранить результат

### Ежедневный отчет
- Количество сигналов BUY/SELL
- Статистика активов
- Отправка результатов

## 📊 Формат данных

### DataFrame с OHLCV
```
                 Open      High       Low     Close        Volume
Date                                                               
2024-01-01  150.2200  151.5300  149.8500  151.0100  60000000.0
2024-01-02  151.1200  152.3400  150.9100  151.9900  65000000.0
...
```

### DataFrame с индикаторами (после `calculate_all_indicators`)
```
                 Open      High       Low     Close     Volume
                SMA_FAST  SMA_SLOW   EMA_FAST  EMA_SLOW
                RSI       MACD      MACD_SIGNAL  MACD_HISTOGRAM
                STOCH_K   STOCH_D
                BB_UPPER  BB_MIDDLE  BB_LOWER  BB_WIDTH
                ATR       OBV        AD_LINE    ADX
...
```

### Сигнал (структура)
```python
{
    'symbol': str,                    # Тикер
    'signal': str,                    # BUY/SELL/HOLD/STRONG_BUY/STRONG_SELL
    'confidence': float,              # 0.0 - 1.0
    'price': float,                   # Текущая цена
    'timestamp': datetime,            # Время сигнала
    'buy_score': float,              # Сумма весов покупки
    'sell_score': float,             # Сумма весов продажи
    'buy_reasons': list[str],        # Причины покупки
    'sell_reasons': list[str],       # Причины продажи
    'stop_loss': float,              # Уровень SL
    'take_profit': float,            # Уровень TP
    'components': dict,              # Детали индикаторов
    'recommendation': str            # Текстовая рекомендация
}
```

## 🗂️ Локальное хранилище

```
data/
├── AAPL.csv           # Исторические данные
├── MSFT.csv
├── BTC_USD.csv
└── ...

models/
├── AAPL_lightgbm.pkl  # ML модель
├── AAPL_scaler.pkl    # Масштабировщик признаков
├── MSFT_lightgbm.pkl
└── ...

logs/
└── market_analyzer.log  # Логи системы
```

## ⚙️ Параметры настройки

### Для более чувствительных сигналов
```python
INDICATORS_CONFIG = {
    'SMA_FAST': 10,    # Было 20
    'SMA_SLOW': 30,    # Было 50
    'RSI_PERIOD': 7,   # Было 14
}

SIGNAL_CONFIG = {
    'SIGNAL_STRENGTH_BUY': 0.55,   # Было 0.65
    'SIGNAL_STRENGTH_SELL': 0.55,
}
```

### Для менее чувствительных сигналов
```python
INDICATORS_CONFIG = {
    'SMA_FAST': 30,    # Было 20
    'SMA_SLOW': 100,   # Было 50
    'RSI_PERIOD': 21,  # Было 14
}

SIGNAL_CONFIG = {
    'SIGNAL_STRENGTH_BUY': 0.75,   # Было 0.65
    'SIGNAL_STRENGTH_SELL': 0.75,
}
```

### Для Raspberry Pi (оптимизированные)
```python
ASSETS = ASSETS[:10]  # Максимум 10 активов

UPDATE_INTERVAL_MINUTES = 30  # Вместо 5

HISTORY_DAYS = 100  # Вместо 365

ML_CONFIG = {
    'MODEL_TYPE': 'lightgbm',  # Быстрее на RPi
    'HYPERPARAMETERS': {
        'n_estimators': 50,    # Было 100
        'max_depth': 5,        # Было 10
    }
}
```

## 🧪 Тестирование

```bash
# Запустить все тесты
python test_system.py

# Запустить конкретный тест
python test_system.py --test 1  # Импорты
python test_system.py --test 3  # Сбор данных
python test_system.py --test 5  # Сигналы

# Запустить примеры
python examples.py
```

## 📈 Производительность

### Время обработки (на Raspberry Pi 5)
- Загрузка 1 года данных: 2-5 сек
- Расчет индикаторов: 0.5-1 сек
- Генерация сигнала: 0.1-0.2 сек
- Обработка 10 активов: 30-50 сек
- Обучение ML модели: 10-20 сек

### Использование памяти
- Базовая система: ~150 MB
- С 10 активами: ~300 MB
- Пик при обучении ML: ~500 MB

## 🔐 Безопасность

- Все вычисления локальные (нет передачи данных в облако)
- Telegram токен хранится в переменных окружения
- Логи содержат только неприватные данные
- CSV файлы хранят только публичные данные о ценах

## 🐛 Отладка

### Включить подробное логирование
```python
# В utils.py
LOG_CONFIG = {
    'LOG_LEVEL': 'DEBUG',  # Было 'INFO'
}
```

### Массив отладочной информации
```python
from signal_generator import SignalGenerator
signal = sg.generate_signal(df)
print(signal['components'])  # Все индикаторы
```

## 📚 Расширение функционала

### Добавить новый индикатор
```python
# В indicator_analysis.py
def calculate_my_indicator(self, prices, period):
    # Логика расчета
    return indicator_values

# Использовать
df['MY_INDICATOR'] = ia.calculate_my_indicator(df['Close'], 20)
```

### Добавить новый источник данных
```python
# В data_collector.py
def download_from_custom_source(self, symbol):
    # Логика загрузки
    return df
```

### Кастомная стратегия сигналов
```python
# Создать новый класс
class CustomSignalGenerator(SignalGenerator):
    def _combine_signals(self, components, df):
        # Своя логика комбинирования
        return signal
```

---

**Версия документации**: 1.0  
**Последнее обновление**: 2025