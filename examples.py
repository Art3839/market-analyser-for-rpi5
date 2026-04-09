"""
Примеры использования Market Analyzer
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from data_collector import DataCollector
from indicator_analysis import IndicatorAnalyzer
from signal_generator import SignalGenerator
from telegram_notifier import notifier
from utils import get_logger

logger = get_logger('Examples')

def example_1_load_and_analyze():
    """Пример 1: Загрузить данные и проанализировать"""
    print("\n=== Пример 1: Загрузить и проанализировать ===\n")
    
    # Инициализировать
    dc = DataCollector()
    ia = IndicatorAnalyzer()
    
    # Загрузить данные
    symbol = 'AAPL'
    print(f"Загрузка данных для {symbol}...")
    df = dc.download_historical_data(symbol, days=100)
    
    if df is None:
        print("Ошибка при загрузке данных")
        return
    
    print(f"Загружено {len(df)} свечей")
    print(f"Период: {df.index[0]} - {df.index[-1]}")
    print(f"Цена текущая: ${df['Close'].iloc[-1]:.2f}")
    
    # Рассчитать индикаторы
    print("\nРасчет индикаторов...")
    df = ia.calculate_all_indicators(df)
    
    # Вывести последние значения индикаторов
    print("\nПоследние значения индикаторов:")
    print(f"  SMA(20): {df['SMA_FAST'].iloc[-1]:.2f}")
    print(f"  SMA(50): {df['SMA_SLOW'].iloc[-1]:.2f}")
    print(f"  RSI(14): {df['RSI'].iloc[-1]:.1f}")
    print(f"  MACD: {df['MACD'].iloc[-1]:.2e}")
    print(f"  ATR: {df['ATR'].iloc[-1]:.2f}")
    print(f"  BB Upper: {df['BB_UPPER'].iloc[-1]:.2f}")
    print(f"  BB Lower: {df['BB_LOWER'].iloc[-1]:.2f}")


def example_2_generate_signals():
    """Пример 2: Генерировать торговые сигналы"""
    print("\n=== Пример 2: Генерировать сигналы ===\n")
    
    dc = DataCollector()
    ia = IndicatorAnalyzer()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in symbols:
        print(f"\nАнализ {symbol}...")
        
        # Загрузить и подготовить данные
        df = dc.download_historical_data(symbol, days=100)
        if df is None:
            print(f"  ✗ Не удалось загрузить {symbol}")
            continue
        
        df = ia.calculate_all_indicators(df)
        
        # Генерировать сигнал
        sg = SignalGenerator(symbol)
        signal = sg.generate_signal(df)
        
        # Вывести результат
        print(f"  Сигнал: {signal['signal']}")
        print(f"  Уверенность: {signal['confidence']*100:.1f}%")
        print(f"  Цена: ${signal['price']:.2f}")
        print(f"  Рекомендация: {signal['recommendation']}")


def example_3_test_telegram():
    """Пример 3: Тестировать Telegram подключение"""
    print("\n=== Пример 3: Тестировать Telegram ===\n")
    
    if not notifier.enabled:
        print("⚠️  Telegram не настроен")
        print("Установите переменные окружения:")
        print("  export TELEGRAM_BOT_TOKEN='your_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        return
    
    print("Проверка подключения к Telegram...")
    if notifier.test_connection():
        print("✓ Подключение успешно")
        
        # Отправить тестовое сообщение
        print("Отправка тестового сообщения...")
        notifier.send_status("✅ Тест подключения Market Analyzer успешен!")
        print("✓ Сообщение отправлено")
    else:
        print("✗ Ошибка подключения")


def example_4_ml_prediction():
    """Пример 4: ML предсказание"""
    print("\n=== Пример 4: ML Предсказание ===\n")
    
    from ml_models import MLPredictor, TrendPredictor
    
    dc = DataCollector()
    ia = IndicatorAnalyzer()
    
    symbol = 'AAPL'
    
    # Загрузить и подготовить данные
    print(f"Загрузка данных для {symbol}...")
    df = dc.download_historical_data(symbol, days=365)
    if df is None:
        print("Ошибка при загрузке")
        return
    
    df = ia.calculate_all_indicators(df)
    
    # Обучить ML модель
    print("Обучение ML модели...")
    predictor = MLPredictor(symbol)
    if predictor.train(df):
        print("✓ Модель обучена")
        
        # Получить признаки для предсказания
        features = dc.prepare_features(symbol)
        if features is not None:
            # Предсказать
            prediction = predictor.predict_direction(features)
            print(f"\nML Предсказание:")
            print(f"  Направление: {prediction['direction']}")
            print(f"  Вероятность: {prediction['probability']*100:.1f}%")
            print(f"  Уверенность: {prediction['confidence']*100:.1f}%")
    else:
        print("✗ Не удалось обучить модель")
    
    # Тренд анализ
    print(f"\nАнализ тренда {symbol}:")
    trend = TrendPredictor.predict_trend_direction(df['Close'].values)
    print(f"  Направление: {trend['direction']}")
    print(f"  Наклон: {trend['slope']:.4f}")
    print(f"  R²: {trend['r_squared']:.3f}")
    print(f"  Сила тренда: {trend['strength']:.2f}%")


def example_5_portfolio_analysis():
    """Пример 5: Анализ портфеля активов"""
    print("\n=== Пример 5: Анализ портфеля ===\n")
    
    from config import ASSETS
    
    dc = DataCollector()
    ia = IndicatorAnalyzer()
    
    print(f"Анализ {len(ASSETS)} активов...")
    print("=" * 70)
    
    results = []
    
    for asset in ASSETS:
        symbol = asset['symbol']
        name = asset['name']
        
        try:
            # Загрузить данные
            df = dc.download_historical_data(symbol, days=100)
            if df is None:
                print(f"{symbol:10} | ✗ Ошибка загрузки")
                continue
            
            df = ia.calculate_all_indicators(df)
            
            # Генерировать сигнал
            sg = SignalGenerator(symbol)
            signal = sg.generate_signal(df)
            
            # Сохранить результат
            results.append({
                'symbol': symbol,
                'name': name,
                'signal': signal['signal'],
                'confidence': signal['confidence'],
                'price': signal['price']
            })
            
            print(f"{symbol:10} | {signal['signal']:12} | {signal['confidence']*100:5.1f}% | ${signal['price']:8.2f}")
            
        except Exception as e:
            print(f"{symbol:10} | ✗ {str(e)[:20]}")
    
    print("=" * 70)
    
    # Статистика
    buy_signals = sum(1 for r in results if r['signal'] in ['BUY', 'STRONG_BUY'])
    sell_signals = sum(1 for r in results if r['signal'] in ['SELL', 'STRONG_SELL'])
    
    print(f"\nСтатистика:")
    print(f"  Сигналов на покупку: {buy_signals}")
    print(f"  Сигналов на продажу: {sell_signals}")
    print(f"  Нейтральных: {len(results) - buy_signals - sell_signals}")


def example_6_stress_test():
    """Пример 6: Стресс-тест системы"""
    print("\n=== Пример 6: Стресс-тест системы ===\n")
    
    import time
    from config import ASSETS
    
    dc = DataCollector()
    ia = IndicatorAnalyzer()
    
    print(f"Нагрузочное тестирование на {len(ASSETS)} активах...")
    
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    for asset in ASSETS:
        symbol = asset['symbol']
        try:
            df = dc.download_historical_data(symbol)
            if df is not None:
                df = ia.calculate_all_indicators(df)
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing {symbol}: {e}")
    
    elapsed = time.time() - start_time
    
    print(f"\nРезультаты:")
    print(f"  Успешно: {success_count}")
    print(f"  Ошибок: {error_count}")
    print(f"  Время: {elapsed:.2f} сек")
    print(f"  Среднее время на актив: {elapsed/len(ASSETS):.2f} сек")


def main():
    """Главная функция примеров"""
    examples = {
        '1': ('Загрузить и проанализировать', example_1_load_and_analyze),
        '2': ('Генерировать сигналы', example_2_generate_signals),
        '3': ('Тестировать Telegram', example_3_test_telegram),
        '4': ('ML предсказание', example_4_ml_prediction),
        '5': ('Анализ портфеля', example_5_portfolio_analysis),
        '6': ('Стресс-тест', example_6_stress_test),
    }
    
    print("\n╔════════════════════════════════════════╗")
    print("║  Market Analyzer - Примеры использования ║")
    print("╚════════════════════════════════════════╝\n")
    
    print("Доступные примеры:\n")
    for key, (description, _) in examples.items():
        print(f"  {key}. {description}")
    
    print("\nВыберите пример (1-6) или 'all' для всех:")
    choice = input("> ").strip().lower()
    
    if choice == 'all':
        for func in examples.values():
            func[1]()
            input("\nНажмите Enter для продолжения...")
    elif choice in examples:
        examples[choice][1]()
    else:
        print("❌ Неверный выбор")


if __name__ == '__main__':
    main()
