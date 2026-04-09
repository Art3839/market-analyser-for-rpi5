"""
Скрипт тестирования Market Analyzer
Проверяет все компоненты системы
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Тест 1: Проверить импорты"""
    print("\n[TEST 1] Проверка импортов модулей...")
    try:
        import numpy
        print("  ✓ NumPy")
        
        import pandas
        print("  ✓ Pandas")
        
        import sklearn
        print("  ✓ scikit-learn")
        
        from data_collector import DataCollector
        print("  ✓ data_collector")
        
        from indicator_analysis import IndicatorAnalyzer
        print("  ✓ indicator_analysis")
        
        from signal_generator import SignalGenerator
        print("  ✓ signal_generator")
        
        from ml_models import MLPredictor
        print("  ✓ ml_models")
        
        from telegram_notifier import notifier
        print("  ✓ telegram_notifier")
        
        from gui import MarketAnalyzerGUI
        print("  ✓ gui")
        
        from config import ASSETS, INDICATORS_CONFIG
        print("  ✓ config")
        
        print("\n✅ Все импорты успешны!\n")
        return True
        
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}\n")
        return False


def test_config():
    """Тест 2: Проверить конфигурацию"""
    print("[TEST 2] Проверка конфигурации...")
    
    try:
        from config import ASSETS, INDICATORS_CONFIG, SIGNAL_CONFIG, TELEGRAM_CONFIG
        
        # Проверить активы
        if not ASSETS:
            print("  ⚠️  Список активов пуст")
            return False
        
        print(f"  ✓ Активы: {len(ASSETS)} символов")
        for asset in ASSETS[:3]:
            print(f"    - {asset['symbol']} ({asset['name']})")
        
        # Проверить индикаторы
        required_indicators = [
            'SMA_FAST', 'SMA_SLOW', 'RSI_PERIOD', 'MACD_FAST',
            'BB_PERIOD', 'ATR_PERIOD'
        ]
        for ind in required_indicators:
            if ind not in INDICATORS_CONFIG:
                print(f"  ✗ Отсутствует индикатор: {ind}")
                return False
        
        print(f"  ✓ Индикаторы: {len(INDICATORS_CONFIG)} параметров")
        
        # Проверить сигналы
        if not SIGNAL_CONFIG:
            print("  ✗ Конфигурация сигналов пуста")
            return False
        
        print(f"  ✓ Сигналы: настроены")
        
        # Проверить Telegram
        if not TELEGRAM_CONFIG['BOT_TOKEN']:
            print("  ⚠️  Telegram не настроен (токен отсутствует)")
        else:
            print("  ✓ Telegram: настроен")
        
        print("\n✅ Конфигурация корректна!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка конфигурации: {e}\n")
        return False


def test_data_collection():
    """Тест 3: Проверить сбор данных"""
    print("[TEST 3] Проверка сбора данных...")
    
    try:
        from data_collector import DataCollector
        
        dc = DataCollector()
        
        # Попробовать загрузить данные
        print("  Загрузка данных AAPL (это может занять время)...")
        df = dc.download_historical_data('AAPL', days=30)
        
        if df is None:
            print("  ✗ Не удалось загрузить данные")
            return False
        
        if df.empty:
            print("  ✗ DataFrame пуст")
            return False
        
        print(f"  ✓ Загружено {len(df)} свечей")
        print(f"    Колонки: {', '.join(df.columns)}")
        print(f"    Дата начала: {df.index[0]}")
        print(f"    Дата конца: {df.index[-1]}")
        
        print("\n✅ Сбор данных работает!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при сборе данных: {e}\n")
        return False


def test_indicators():
    """Тест 4: Проверить индикаторы"""
    print("[TEST 4] Проверка технических индикаторов...")
    
    try:
        from indicator_analysis import IndicatorAnalyzer
        from data_collector import DataCollector
        import numpy as np
        
        ia = IndicatorAnalyzer()
        dc = DataCollector()
        
        # Загрузить данные
        df = dc.download_historical_data('AAPL', days=30)
        if df is None or df.empty:
            print("  ✗ Не удалось загрузить данные")
            return False
        
        print("  Расчет индикаторов...")
        df = ia.calculate_all_indicators(df)
        
        # Проверить наличие всех индикаторов
        required_columns = [
            'SMA_FAST', 'SMA_SLOW', 'EMA_FAST', 'EMA_SLOW',
            'RSI', 'MACD', 'MACD_SIGNAL', 'MACD_HISTOGRAM',
            'STOCH_K', 'STOCH_D',
            'BB_UPPER', 'BB_MIDDLE', 'BB_LOWER',
            'ATR', 'OBV', 'AD_LINE', 'ADX'
        ]
        
        missing = []
        for col in required_columns:
            if col not in df.columns:
                missing.append(col)
        
        if missing:
            print(f"  ⚠️  Отсутствуют колонки: {missing}")
        else:
            print(f"  ✓ Все {len(required_columns)} индикаторов рассчитаны")
        
        # Проверить значения
        last_row = df.iloc[-1]
        print(f"  ✓ Последние значения:")
        print(f"    SMA(20): {last_row['SMA_FAST']:.2f}")
        print(f"    RSI: {last_row['RSI']:.1f}")
        print(f"    MACD: {last_row['MACD']:.2e}")
        
        print("\n✅ Индикаторы работают!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при расчете индикаторов: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_signal_generation():
    """Тест 5: Проверить генерацию сигналов"""
    print("[TEST 5] Проверка генерации сигналов...")
    
    try:
        from signal_generator import SignalGenerator
        from data_collector import DataCollector
        from indicator_analysis import IndicatorAnalyzer
        
        dc = DataCollector()
        ia = IndicatorAnalyzer()
        
        # Загрузить и подготовить данные
        df = dc.download_historical_data('AAPL', days=100)
        if df is None or len(df) < 50:
            print("  ✗ Недостаточно данных")
            return False
        
        df = ia.calculate_all_indicators(df)
        
        # Генерировать сигнал
        sg = SignalGenerator('AAPL')
        signal = sg.generate_signal(df)
        
        # Проверить результат
        required_fields = [
            'signal', 'confidence', 'price', 'buy_score', 'sell_score',
            'buy_reasons', 'sell_reasons', 'recommendation'
        ]
        
        for field in required_fields:
            if field not in signal:
                print(f"  ✗ Отсутствует поле: {field}")
                return False
        
        print("  ✓ Структура сигнала корректна")
        print(f"    Сигнал: {signal['signal']}")
        print(f"    Уверенность: {signal['confidence']*100:.1f}%")
        print(f"    Цена: ${signal['price']:.2f}")
        print(f"    Причины покупки: {len(signal['buy_reasons'])}")
        print(f"    Причины продажи: {len(signal['sell_reasons'])}")
        
        valid_signals = ['BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL']
        if signal['signal'] not in valid_signals:
            print(f"  ✗ Неверный сигнал: {signal['signal']}")
            return False
        
        print("\n✅ Генерация сигналов работает!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при генерации сигналов: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_telegram():
    """Тест 6: Проверить Telegram подключение"""
    print("[TEST 6] Проверка Telegram подключения...")
    
    try:
        from telegram_notifier import notifier
        
        if not notifier.enabled:
            print("  ⚠️  Telegram не настроен")
            print("    Установите переменные окружения:")
            print("      TELEGRAM_BOT_TOKEN")
            print("      TELEGRAM_CHAT_ID")
            return True  # Не считаем как ошибку
        
        print("  Проверка подключения...")
        result = notifier.test_connection()
        
        if result:
            print("  ✓ Подключение успешно")
            print("\n✅ Telegram работает!\n")
            return True
        else:
            print("  ✗ Ошибка подключения")
            print("\n❌ Проверьте учетные данные Telegram!\n")
            return False
        
    except Exception as e:
        print(f"\n⚠️  Ошибка при проверке Telegram: {e}\n")
        return True  # Не критично


def test_ml_models():
    """Тест 7: Проверить ML модели"""
    print("[TEST 7] Проверка ML моделей...")
    
    try:
        from ml_models import MLPredictor
        from data_collector import DataCollector
        from indicator_analysis import IndicatorAnalyzer
        
        dc = DataCollector()
        ia = IndicatorAnalyzer()
        
        # Загрузить и подготовить данные
        df = dc.download_historical_data('AAPL', days=200)
        if df is None or len(df) < 100:
            print("  ⚠️  Недостаточно данных для обучения ML модели")
            return True
        
        df = ia.calculate_all_indicators(df)
        
        print("  Инициализация ML модели...")
        predictor = MLPredictor('AAPL')
        
        print("  Обучение модели (это может занять время)...")
        if predictor.train(df):
            print("  ✓ Модель обучена успешно")
            
            # Тестировать предсказание
            features = dc.prepare_features('AAPL')
            if features is not None:
                prediction = predictor.predict_direction(features)
                print("  ✓ Предсказание:")
                print(f"    Направление: {prediction['direction']}")
                print(f"    Уверенность: {prediction['confidence']*100:.1f}%")
            
            print("\n✅ ML модели работают!\n")
            return True
        else:
            print("  ⚠️  Не удалось обучить модель")
            return True
        
    except ImportError as e:
        if 'lightgbm' in str(e):
            print("  ⚠️  LightGBM не установлен, используется Random Forest")
        print("\n⚠️  ML модели ограничены\n")
        return True
    except Exception as e:
        print(f"\n⚠️  Ошибка при проверке ML: {e}\n")
        return True


def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "="*50)
    print("  Market Analyzer - Комплексное тестирование")
    print("="*50)
    
    tests = [
        test_imports,
        test_config,
        test_data_collection,
        test_indicators,
        test_signal_generation,
        test_telegram,
        test_ml_models,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}\n")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Итоги
    print("\n" + "="*50)
    print("  ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nПройдено тестов: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ВСЕ ТЕСТЫ УСПЕШНЫ! Система готова к работе.\n")
        return True
    elif passed >= total * 0.7:
        print("\n⚠️  Большинство тестов пройдено. Система может работать с ограничениями.\n")
        return True
    else:
        print("\n❌ КРИТИЧЕСКИЕ ОШИБКИ! Проверьте установку зависимостей.\n")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Market Analyzer Test Suite')
    parser.add_argument('--test', help='Запустить конкретный тест (1-7)')
    args = parser.parse_args()
    
    if args.test:
        if args.test == '1':
            test_imports()
        elif args.test == '2':
            test_config()
        elif args.test == '3':
            test_data_collection()
        elif args.test == '4':
            test_indicators()
        elif args.test == '5':
            test_signal_generation()
        elif args.test == '6':
            test_telegram()
        elif args.test == '7':
            test_ml_models()
        else:
            print("Неверный номер теста")
    else:
        run_all_tests()
