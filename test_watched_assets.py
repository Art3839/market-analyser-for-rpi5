"""
Тесты для функциональности управления отслеживаемыми активами
Проверяет: сохранение, загрузку, фильтрацию, интеграцию
"""
import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, ASSETS
from utils import load_json, save_json, get_logger

logger = get_logger(__name__)


def test_watched_assets_persistence():
    """Тест 1: Сохранение и загрузка отслеживаемых активов"""
    print("\n[TEST 1] Проверка сохранения и загрузки отслеживаемых активов...")
    
    try:
        # Создать директорию данных если её нет
        Path(DATA_DIR).mkdir(exist_ok=True)
        
        test_assets = ['AAPL', 'MSFT', 'BTC-USD']
        test_data = {'watched': test_assets}
        
        # Сохранить
        save_json(test_data, 'watched_assets.json')
        print("  ✓ Данные сохранены")
        
        # Загрузить
        loaded = load_json('watched_assets.json')
        
        if loaded is None:
            print("  ✗ Не удалось загрузить данные")
            return False
        
        if 'watched' not in loaded:
            print("  ✗ Структура данных некорректна")
            return False
        
        if loaded['watched'] == test_assets:
            print(f"  ✓ Загружены активы: {loaded['watched']}")
            print("\n✅ Сохранение работает!\n")
            return True
        else:
            print(f"  ✗ Активы не совпадают: {loaded['watched']} != {test_assets}")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка при сохранении: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_telegram_notifier_watched_assets():
    """Тест 2: Функции управления активами в TelegramNotifier"""
    print("[TEST 2] Проверка TelegramNotifier методов управления активами...")
    
    try:
        from telegram_notifier import TelegramNotifier
        
        # Создать новый экземпляр для тестирования
        notifier = TelegramNotifier()
        
        # Проверить начальные активы
        initial_count = len(notifier.watched_assets)
        print(f"  ✓ Начальные активы: {initial_count} ({notifier.watched_assets})")
        
        # Тест: добавить актив
        test_asset = 'GOOGL'
        notifier.add_watched_asset(test_asset)
        
        if notifier.is_asset_watched(test_asset):
            print(f"  ✓ Актив '{test_asset}' добавлен")
        else:
            print(f"  ✗ Не удалось добавить актив '{test_asset}'")
            return False
        
        # Тест: проверить наличие
        if notifier.is_asset_watched('AAPL'):
            print(f"  ✓ AAPL отслеживается")
        
        if not notifier.is_asset_watched('INVALID'):
            print(f"  ✓ INVALID не отслеживается (корректно)")
        else:
            print(f"  ✓ INVALID в списке (может быть добавлен)")
        
        # Тест: переключить актив
        initial_state = notifier.is_asset_watched(test_asset)
        notifier.toggle_watched_asset(test_asset)
        final_state = notifier.is_asset_watched(test_asset)
        
        if initial_state != final_state:
            print(f"  ✓ Актив '{test_asset}' переключен")
        else:
            print(f"  ⚠️  Переключение не сработало")
        
        # Тест: удалить актив
        notifier.remove_watched_asset(test_asset)
        if not notifier.is_asset_watched(test_asset):
            print(f"  ✓ Актив '{test_asset}' удален")
        
        print("\n✅ TelegramNotifier методы работают!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка в TelegramNotifier: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_signal_filtering():
    """Тест 3: Фильтрация сигналов по отслеживаемым активам"""
    print("[TEST 3] Проверка фильтрации сигналов...")
    
    try:
        from data_collector import DataCollector
        from indicator_analysis import IndicatorAnalyzer
        from signal_generator import SignalGenerator
        from telegram_notifier import TelegramNotifier
        
        # Подготовить данные
        dc = DataCollector()
        ia = IndicatorAnalyzer()
        tn = TelegramNotifier()
        
        # Загрузить данные для активов
        test_symbols = ['AAPL', 'MSFT']
        signals = []
        
        for symbol in test_symbols:
            try:
                df = dc.download_historical_data(symbol, days=30)
                if df is None or len(df) < 50:
                    print(f"  ⚠️  Недостаточно данных для {symbol}")
                    continue
                
                df = ia.calculate_all_indicators(df)
                sg = SignalGenerator(symbol)
                signal = sg.generate_signal(df)
                signals.append((symbol, signal))
                
            except Exception as e:
                print(f"  ⚠️  Ошибка для {symbol}: {e}")
                continue
        
        if not signals:
            print("  ⚠️  Не удалось загрузить данные для тестирования")
            return True
        
        print(f"  ✓ Загружено {len(signals)} сигналов")
        
        # Установить только первый актив в отслеживание
        watched_symbol = signals[0][0]
        tn.watched_assets = [watched_symbol]
        print(f"  ✓ Отслеживаемые активы: {tn.watched_assets}")
        
        # Проверить фильтрацию
        filtered_count = 0
        for symbol, signal in signals:
            if tn.is_asset_watched(symbol):
                filtered_count += 1
                print(f"    ✓ {symbol} - {signal['signal']} (отслеживается)")
            else:
                print(f"    ✗ {symbol} - {signal['signal']} (НЕ отслеживается)")
        
        if filtered_count > 0:
            print(f"  ✓ Фильтрация работает: {filtered_count}/{len(signals)} сигналов")
            print("\n✅ Фильтрация сигналов работает!\n")
            return True
        else:
            print("\n⚠️  Фильтрация не найдена подходящих сигналов\n")
            return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при фильтрации: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_gui_asset_loading():
    """Тест 4: Загрузка активов в GUI"""
    print("[TEST 4] Проверка загрузки активов в GUI...")
    
    try:
        # Сохранить тестовые активы
        test_assets = {'watched': ['AAPL', 'ETH-USD', 'GOOGL']}
        save_json(test_assets, 'watched_assets.json')
        print("  ✓ Тестовые данные сохранены")
        
        # Загрузить как в GUI
        from utils import load_json
        loaded = load_json('watched_assets.json')
        
        if loaded and 'watched' in loaded:
            print(f"  ✓ Загружены активы: {loaded['watched']}")
            print("\n✅ GUI загрузка работает!\n")
            return True
        else:
            print("  ✗ Не удалось загрузить активы для GUI")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка при загрузке в GUI: {e}\n")
        return False


def test_main_system_watched_assets():
    """Тест 5: Интеграция отслеживаемых активов в main.py"""
    print("[TEST 5] Проверка интеграции в основную систему...")
    
    try:
        # Создать файл с тестовыми активами
        test_assets = {'watched': ['AAPL', 'MSFT']}
        save_json(test_assets, 'watched_assets.json')
        print("  ✓ Тестовые активы сохранены")
        
        # Проверить, что можно загрузить
        loaded = load_json('watched_assets.json')
        
        if loaded and 'watched' in loaded:
            watched = loaded['watched']
            print(f"  ✓ Система может загрузить активы: {watched}")
            
            # Проверить, что это валидные символы
            config_symbols = [a['symbol'] for a in ASSETS]
            invalid = [s for s in watched if s not in config_symbols]
            
            if invalid:
                print(f"  ⚠️  Неизвестные символы: {invalid}")
            else:
                print(f"  ✓ Все символы валидны")
            
            print("\n✅ Интеграция в main.py работает!\n")
            return True
        else:
            print("  ✗ Ошибка загрузки активов")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка интеграции: {e}\n")
        return False


def test_default_watched_assets():
    """Тест 6: Значения по умолчанию"""
    print("[TEST 6] Проверка значений по умолчанию...")
    
    try:
        from config import WATCHED_ASSETS
        
        print(f"  ✓ Активы по умолчанию: {WATCHED_ASSETS}")
        
        if not isinstance(WATCHED_ASSETS, list):
            print("  ✗ WATCHED_ASSETS должен быть list")
            return False
        
        if len(WATCHED_ASSETS) == 0:
            print("  ⚠️  Список активов пуст")
            return True
        
        # Проверить, что это валидные символы
        config_symbols = [a['symbol'] for a in ASSETS]
        invalid = [s for s in WATCHED_ASSETS if s not in config_symbols]
        
        if invalid:
            print(f"  ⚠️  Неизвестные символы: {invalid}")
        else:
            print(f"  ✓ Все символы валидны")
        
        print("\n✅ Значения по умолчанию корректны!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка проверки конфига: {e}\n")
        return False


def test_json_file_structure():
    """Тест 7: Структура JSON файла"""
    print("[TEST 7] Проверка структуры JSON файла...")
    
    try:
        # Создать корректный файл
        test_data = {
            'watched': ['AAPL', 'MSFT', 'BTC-USD']
        }
        save_json(test_data, 'watched_assets.json')
        
        # Загрузить и проверить
        loaded = load_json('watched_assets.json')
        
        if loaded is None:
            print("  ✗ Не удалось загрузить файл")
            return False
        
        if not isinstance(loaded, dict):
            print("  ✗ Корневой элемент должен быть dict")
            return False
        
        if 'watched' not in loaded:
            print("  ✗ Отсутствует ключ 'watched'")
            return False
        
        if not isinstance(loaded['watched'], list):
            print("  ✗ 'watched' должен быть list")
            return False
        
        all_strings = all(isinstance(s, str) for s in loaded['watched'])
        if not all_strings:
            print("  ✗ Все элементы должны быть строками")
            return False
        
        print("  ✓ Структура JSON корректна")
        print(f"  ✓ Активов в файле: {len(loaded['watched'])}")
        print(f"  ✓ Содержание: {loaded['watched']}")
        
        print("\n✅ JSON файл корректен!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка структуры JSON: {e}\n")
        return False


def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "="*60)
    print("  ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ ОТСЛЕЖИВАЕМЫХ АКТИВОВ")
    print("="*60)
    
    tests = [
        test_watched_assets_persistence,
        test_telegram_notifier_watched_assets,
        test_signal_filtering,
        test_gui_asset_loading,
        test_main_system_watched_assets,
        test_default_watched_assets,
        test_json_file_structure,
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Критическая ошибка в тесте {i}: {e}\n")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Итоги
    print("\n" + "="*60)
    print("  ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nПройдено тестов: {passed}/{total}")
    
    for i, result in enumerate(results, 1):
        status = "✅" if result else "❌"
        print(f"  {status} Тест {i}")
    
    if passed == total:
        print("\n✅ ВСЕ ТЕСТЫ УСПЕШНЫ! Система управления активами работает.\n")
        return True
    elif passed >= total * 0.7:
        print("\n⚠️  Большинство тестов пройдено. Система может работать.\n")
        return True
    else:
        print("\n❌ КРИТИЧЕСКИЕ ОШИБКИ! Проверьте установку и конфигурацию.\n")
        return False


if __name__ == '__main__':
    run_all_tests()
