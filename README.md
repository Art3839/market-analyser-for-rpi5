# Market Analyzer - Локальная система анализа рынка для Raspberry Pi 5

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Полнофункциональная локальная программа для анализа рынка акций и криптовалют на Raspberry Pi 5 с использованием технических индикаторов, машинного обучения и отправкой сигналов через Telegram.

## 🎯 Возможности

✅ **Локальность**: Полностью автономная работа без облачных сервисов
✅ **Технические индикаторы**: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic и другие
✅ **ML-предсказания**: Локальные модели Random Forest и LightGBM для прогнозирования
✅ **Торговые сигналы**: Автоматическая генерация сигналов BUY/SELL/HOLD
✅ **Telegram интеграция**: Уведомления о сигналах в реальном времени
✅ **GUI интерфейс**: Легковесный Tkinter интерфейс для диагностики
✅ **Управление рисками**: Расчет Stop Loss и Take Profit уровней
✅ **Локальное хранение**: CSV базы данных на SD карте Raspberry Pi
✅ **Оптимизация**: Работает на Raspberry Pi 5 без зависания

## 📋 Требования

- Raspberry Pi 5 (или любой Linux/Windows/Mac с Python)
- Python 3.8+
- pip (менеджер пакетов)
- 2GB+ свободной памяти
- Интернет соединение для загрузки данных
- Telegram бот (для уведомлений, опционально)

## 🚀 Установка

### 1. Клонирование/Загрузка проекта

```bash
cd /path/to/market-analyzer
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

**Примечание для Raspberry Pi**: На RPi установка может занять время. Рекомендуется:
- Обновить pip: `pip install --upgrade pip`
- Использовать бинарные пакеты: `pip install --only-binary :all: numpy pandas`

## ⚙️ Конфигурация

### 1. Основные параметры (config.py)

Отредактируйте `config.py` для настройки:

```python
# Активы для анализа
ASSETS = [
    {'symbol': 'AAPL', 'type': 'stock', 'name': 'Apple'},
    {'symbol': 'BTC-USD', 'type': 'crypto', 'name': 'Bitcoin'},
    # ... добавьте свои активы
]

# Параметры индикаторов
INDICATORS_CONFIG = {
    'SMA_FAST': 20,
    'SMA_SLOW': 50,
    # ... другие параметры
}

# Параметры сигналов
SIGNAL_CONFIG = {
    'SIGNAL_STRENGTH_BUY': 0.65,
    'SIGNAL_STRENGTH_SELL': 0.65,
    'USE_ML_MODEL': True,
}

# Управление рисками
RISK_CONFIG = {
    'MAX_LOSS_PERCENT': 5.0,
    'MIN_PROFIT_PERCENT': 1.5,
    'STOP_LOSS_PERCENT': 3.0,
}
```

### 2. Настройка Telegram уведомлений

Если хотите получать уведомления в Telegram:

1. Создайте бота у @BotFather в Telegram
2. Получите BOT_TOKEN and CHAT_ID
3. Установите переменные окружения:

```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id"
```

Или отредактируйте `config.py`:

```python
TELEGRAM_CONFIG = {
    'BOT_TOKEN': 'your_token',
    'CHAT_ID': 'your_chat_id',
    'SEND_SIGNALS': True,
}
```

## 💻 Использование

### Режим command-line (непрерывный анализ)

```bash
python main.py
```

Система будет:
- Загружать данные каждые 5 минут (настраивается)
- Анализировать индикаторы
- Генерировать сигналы
- Отправлять уведомления в Telegram

### Режим GUI (интерактивный)

```bash
python main.py --gui
```

Откроется окно с:
- Таблицей текущих сигналов
- Детальным анализом активов
- Логами системы
- Кнопками для ручного обновления и анализа

### Пропуск инициализации (для тестирования)

```bash
python main.py --no-init
```

## 📊 Структура проекта

```
market-analyzer/
├── config.py                 # Конфигурация параметров
├── utils.py                 # Утилиты и логирование
├── data_collector.py        # Загрузка и управление данными
├── indicator_analysis.py    # Технические индикаторы
├── ml_models.py            # ML модели (LightGBM, Random Forest)
├── signal_generator.py     # Генерация торговых сигналов
├── telegram_notifier.py    # Отправка уведомлений
├── gui.py                  # Графический интерфейс
├── main.py                 # Главная программа
├── requirements.txt        # Зависимости
├── data/                   # Локальные данные (CSV)
├── models/                 # Сохраненные ML модели
└── logs/                   # Файлы логов
```

## 🔧 Технические индикаторы

Система рассчитывает следующие индикаторы:

### Скользящие средние
- **SMA** (Simple Moving Average) - простые скользящие средние
- **EMA** (Exponential Moving Average) - экспоненциальные средние

### Momentum
- **RSI** (Relative Strength Index) - индекс относительной силы
- **MACD** (Moving Average Convergence Divergence) - схождение-расхождение МА
- **Stochastic** - стохастический осциллятор

### Волатильность
- **Bollinger Bands** - ленты Боллинджера
- **ATR** (Average True Range) - средний истинный диапазон

### Volume
- **OBV** (On-Balance Volume) - объем с учетом баланса
- **A/D Line** (Accumulation/Distribution) - линия накопления/распределения

### Тренд
- **ADX** (Average Directional Index) - индекс направленного движения

## 🤖 Машинное обучение

### Поддерживаемые модели
- **LightGBM** (рекомендуется для RPi - быстро и эффективно)
- **Random Forest** (альтернатива)

### Процесс обучения
1. Система загружает исторические данные
2. Подготавливает признаки из технических индикаторов
3. Обучает модель предсказывать ценовое движение на 5 свечей
4. Сохраняет обученную модель локально

### Использование
- Модель используется как дополнительный источник сигнала
- Комбинируется с техническими индикаторами
- Настраивается через `SIGNAL_CONFIG['USE_ML_MODEL']`

## 📈 Генерация сигналов

Система использует мультикомпонентный подход:

### Компоненты сигнала
1. **Скользящие средние** (2.0x) - основной тренд
2. **RSI** (2.0x) - перекупленность/перепроданность
3. **MACD** (2.0x) - импульс и разворот
4. **Stochastic** (1.5x) - критические точки
5. **Bollinger Bands** (1.5x) - экстремумы
6. **Тренд** (2.0x) - направление
7. **Объем** (1.5x) - подтверждение
8. **ML модель** (1.5x) - предсказание
9. **Риски** (1.0x) - волатильность и уровни

### Типы сигналов
- **STRONG_BUY** (🚀) - очень сильный сигнал покупки
- **BUY** (📈) - сигнал покупки
- **HOLD** (➡️) - нейтральный сигнал
- **SELL** (📉) - сигнал продажи
- **STRONG_SELL** (💥) - очень сильный сигнал продажи

## 🛡️ Управление рисками

### Автоматические уровни
- **Stop Loss** - уровень выхода из позиции при убытках (по умолчанию 2x ATR ниже входной цены)
- **Take Profit** - уровень фиксации прибыли (по умолчанию 2x ATR выше входной цены)

### Ограничения позиций
- Максимальный размер позиции от портфеля
- Максимальные потери от капитала

## 📱 Telegram уведомления

### Что отправляется
- **Сигналы** - когда возникает новый сигнал BUY/SELL/STRONG
- **Ошибки** - критические проблемы в системе
- **Статус** - запуск/остановка системы
- **Отчеты** - ежедневный отчет

### Формат сообщений
```
🚀 AAPL - STRONG_BUY
Уверенность: 82.5%
Цена: $150.25
Время: 14:32:15

📋 Рекомендация: СИЛЬНЫЙ СИГНАЛ ПОКУПКИ! 
Входить на $150.25, SL: $147.50, TP: $153.00

✅ Причины покупки:
  • Цена выше быстрой MA, быстрая выше медленной
  • RSI перепроданность (28.5)
  • ...
```

## 🔍 Диагностика

### Проверка логов
```bash
tail -f logs/market_analyzer.log
```

### Тестирование Telegram
```python
from telegram_notifier import notifier
notifier.test_connection()
```

### Проверка данных
```python
from data_collector import DataCollector
dc = DataCollector()
df = dc.download_historical_data('AAPL')
print(df.tail())
```

## ⚡ Оптимизация для Raspberry Pi

### Рекомендации
1. **Использовать SSD** вместо SD карты для логов и данных
2. **Ограничить количество активов** до 10-15
3. **Увеличить интервал обновления** до 15-30 минут
4. **Отключить GUI** на приложениях
5. **Использовать LightGBM** вместо Random Forest

### Примеры запуска на RPi

```bash
# Базовый запуск в фоне
nohup python main.py > market_analyzer.log 2>&1 &

# Запуск как systemd сервис
sudo systemctl start market-analyzer

# Мониторинг ресурсов
top -p $(pgrep -f "python main.py")
```

## 📝 Примеры использования

### Пример 1: Добавление нового актива

```python
# В config.py
ASSETS = [
    # ... существующие активы
    {'symbol': 'AAPL', 'type': 'stock', 'name': 'Apple'},
    {'symbol': 'NVDA', 'type': 'stock', 'name': 'NVIDIA'},  # Новый
]
```

### Пример 2: Изменение параметров индикаторов

```python
# Для более быстрых сигналов
INDICATORS_CONFIG = {
    'SMA_FAST': 10,      # Было 20
    'SMA_SLOW': 30,      # Было 50
    'RSI_PERIOD': 7,     # Было 14
}

# Для менее чувствительных сигналов
SIGNAL_CONFIG = {
    'SIGNAL_STRENGTH_BUY': 0.75,   # Было 0.65
    'SIGNAL_STRENGTH_SELL': 0.75,  # Было 0.65
}
```

### Пример 3: Собственный анализ

```python
from data_collector import DataCollector
from indicator_analysis import IndicatorAnalyzer
from signal_generator import SignalGenerator

# Загрузить данные
dc = DataCollector()
df = dc.download_historical_data('AAPL')

# Рассчитать индикаторы
ia = IndicatorAnalyzer()
df = ia.calculate_all_indicators(df)

# Генерировать сигнал
sg = SignalGenerator('AAPL')
signal = sg.generate_signal(df)

print(f"Signal: {signal['signal']}")
print(f"Confidence: {signal['confidence']*100}%")
print(f"Reasons: {signal['buy_reasons']}")
```

## 🐛 Решение проблем

### Проблема: "yfinance: No data found"
**Решение**: Проверьте тикер и интернет соединение
```bash
python -c "import yfinance as yf; print(yf.download('AAPL', periods=1))"
```

### Проблема: Telegram не отправляет
**Решение**: Проверьте токен и chat_id
```python
from telegram_notifier import notifier
notifier.test_connection()
```

### Проблема: ML модель не обучается
**Решение**: Проверьте наличие доста­точно данных
```bash
python -c "
from data_collector import DataCollector
dc = DataCollector()
df = dc.download_historical_data('AAPL')
print(f'Rows: {len(df)}')
"
```

### Проблема: Высокое использование памяти
**Решение**: Уменьшите `HISTORY_DAYS` в config.py с 365 до 100

## 📚 Дополнительные ресурсы

- [Документация Pandas](https://pandas.pydata.org/docs/)
- [Scikit-learn ML](https://scikit-learn.org/)
- [LightGBM Docs](https://lightgbm.readthedocs.io/)
- [yfinance Github](https://github.com/ranaroussi/yfinance)

## 📄 Лицензия

MIT License - Используйте свободно, но на свой риск.

## ⚠️ Оговорка

Эта система разработана в образовательных целях. Торговля на финансовых рынках связана с рисками. 
**Используйте эту систему только как дополнительный инструмент анализа**. 
Перед торговлей проведите собственное исследование и консультируйтесь с финансовым советником.

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте логи в `logs/market_analyzer.log`
2. Убедитесь что все зависимости установлены
3. Попробуйте запустить примеры тестирования

## 🎓 Обучение

Система демонстрирует следующие концепции:
- Техническая аналитика и торговля
- Обработка временных рядов
- Машинное обучение для финансов
- Системное проектирование
- Работа с асинхронными операциями
- Создание GUI в Python

---

**Версия**: 1.0  
**Дата**: 2025  
**Автор**: Market Analyzer Team

Приятного анализа! 📈😊
