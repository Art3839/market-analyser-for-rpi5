"""
Главная программа для системы анализа рынка
Объединяет сборщик данных, индикаторы, сигналы и Telegram уведомления
"""
import time
import schedule
import threading
from datetime import datetime
import traceback
import json

from config import ASSETS, UPDATE_INTERVAL_MINUTES, TELEGRAM_CONFIG, SIGNAL_CONFIG, DATA_DIR
from data_collector import DataCollector
from indicator_analysis import IndicatorAnalyzer
from signal_generator import SignalGenerator
from telegram_notifier import notifier, send_signal, send_status, send_error
from ml_models import EnsemblePredictor
from utils import get_logger, load_json, save_json

logger = get_logger('Main')

class MarketAnalyzerSystem:
    """Главная система анализа рынка"""
    
    def __init__(self, use_gui=False):
        self.data_collector = DataCollector()
        self.indicator_analyzer = IndicatorAnalyzer()
        self.signal_generators = {}
        self.ml_predictor = EnsemblePredictor([a['symbol'] for a in ASSETS])
        
        self.use_gui = use_gui
        self.running = False
        self.last_signals = {}
        
        self.logger = get_logger('MarketAnalyzerSystem')
        
        # Загрузить список отслеживаемых активов
        self._load_watched_assets()
        
        # Инициализировать генераторы сигналов
        for asset in ASSETS:
            self.signal_generators[asset['symbol']] = SignalGenerator(asset['symbol'])
        
        self.logger.info("=== Market Analyzer System Initialized ===")
    
    def _load_watched_assets(self):
        """Загрузить список отслеживаемых активов"""
        try:
            watched_file = DATA_DIR / 'watched_assets.json'
            if watched_file.exists():
                with open(watched_file, 'r') as f:
                    data = json.load(f)
                    self.watched_assets = data.get('watched', ['AAPL', 'BTC-USD'])
            else:
                self.watched_assets = ['AAPL', 'BTC-USD']
            
            self.logger.info(f"Отслеживаемые активы: {', '.join(self.watched_assets)}")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке watched_assets: {e}")
            self.watched_assets = ['AAPL', 'BTC-USD']
    
    def initialize(self):
        """Инициализировать систему"""
        try:
            self.logger.info("Инициализация системы...")
            
            # Загрузить исторические данные
            self._load_historical_data()
            
            # Обучить ML модели
            self._train_ml_models()
            
            # Отправить начальное уведомление
            if TELEGRAM_CONFIG['NOTIFY_ON_START']:
                send_status("✅ Система анализа рынка запущена и готова к работе")
            
            self.logger.info("Система инициализирована успешно")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации: {e}")
            send_error(f"Ошибка инициализации: {e}")
            return False
    
    def _load_historical_data(self):
        """Загрузить исторические данные"""
        self.logger.info("Загрузка исторических данных...")
        
        for asset in ASSETS:
            try:
                symbol = asset['symbol']
                self.logger.info(f"  Загрузка {symbol}...")
                
                # Попытка загрузить локальные данные
                df = self.data_collector.load_local_data(symbol)
                
                # Если нет локальных или они старые - загрузить с yfinance
                if df is None or len(df) < 100:
                    df = self.data_collector.download_historical_data(symbol)
                
                if df is not None:
                    self.logger.info(f"  ✓ {symbol}: {len(df)} свечей")
                else:
                    self.logger.warning(f"  ✗ Не удалось загрузить {symbol}")
                    
            except Exception as e:
                self.logger.error(f"  Ошибка при загрузке {symbol}: {e}")
    
    def _train_ml_models(self):
        """Обучить ML модели на исторических данных"""
        if not SIGNAL_CONFIG.get('USE_ML_MODEL', False):
            self.logger.info("ML модели отключены в конфигурации")
            return
        
        self.logger.info("Обучение ML моделей...")
        
        data_dict = {}
        for asset in ASSETS:
            symbol = asset['symbol']
            df = self.data_collector.get_data(symbol, lookback=200)
            
            if not df.empty and len(df) > 50:
                # Рассчитать индикаторы
                df = self.indicator_analyzer.calculate_all_indicators(df)
                data_dict[symbol] = df
        
        if data_dict:
            self.ml_predictor.train_all(data_dict)
            self.logger.info(f"ML модели обучены для {len(data_dict)} активов")
    
    def run(self):
        """Запустить систему"""
        self.running = True
        self.logger.info("Система запущена")
        
        # Расписание задач
        schedule.every(UPDATE_INTERVAL_MINUTES).minutes.do(self.update_and_analyze)
        schedule.every().day.at("08:00").do(self.send_daily_summary)
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Проверять каждую минуту
                
        except KeyboardInterrupt:
            self.logger.info("Получен сигнал выхода")
            self.stop()
        except Exception as e:
            self.logger.error(f"Ошибка в основном цикле: {e}")
            send_error(f"Ошибка в основном цикле: {e}")
    
    def update_and_analyze(self):
        """Обновить данные и проанализировать"""
        try:
            self.logger.info("=== Цикл обновления и анализа ===")
            
            # Перезагрузить список отслеживаемых активов
            self._load_watched_assets()
            
            # Обновить данные для каждого актива
            for asset in ASSETS:
                try:
                    symbol = asset['symbol']
                    
                    # Пролистать если не в отслеживаемом списке
                    if symbol not in self.watched_assets:
                        self.logger.debug(f"{symbol} не в отслеживаемом списке, пропускаем")
                        continue
                    
                    self.logger.info(f"Обновление {symbol}...")
                    
                    # Обновить данные
                    df = self.data_collector.update_data(symbol)
                    
                    if df is None or df.empty:
                        self.logger.warning(f"Не удалось обновить {symbol}")
                        continue
                    
                    # Рассчитать индикаторы
                    df = self.indicator_analyzer.calculate_all_indicators(df)
                    
                    # Подготовить признаки для ML
                    features = self.data_collector.prepare_features(symbol, lookback=100)
                    
                    # Генерировать сигнал
                    signal_data = self.signal_generators[symbol].generate_signal(df, features)
                    
                    # Проверить, изменился ли сигнал
                    prev_signal = self.last_signals.get(symbol)
                    current_signal = signal_data['signal']
                    
                    if current_signal != prev_signal or current_signal in ['STRONG_BUY', 'STRONG_SELL']:
                        self.logger.info(f"{symbol}: {current_signal} (Уверенность: {signal_data['confidence']*100:.1f}%)")
                        
                        # Отправить сигнал в Telegram (проверка отслеживаемости уже в notifier)
                        send_signal(signal_data)
                    
                    # Сохранить сигнал
                    self.last_signals[symbol] = current_signal
                    
                except Exception as e:
                    self.logger.error(f"Ошибка при анализе {symbol}: {e}")
                    traceback.print_exc()
            
            self.logger.info("=== Цикл завершен ===\n")
            
        except Exception as e:
            self.logger.error(f"Ошибка в update_and_analyze: {e}")
            send_error(f"Ошибка анализа: {e}")
    
    def send_daily_summary(self):
        """Отправить ежедневный отчет"""
        try:
            self.logger.info("Подготовка ежедневного отчета...")
            
            # Перезагрузить список отслеживаемых активов
            self._load_watched_assets()
            
            report_data = {
                'total_assets': len(self.watched_assets),
                'watched_assets': self.watched_assets,
                'buy_signals': [],
                'sell_signals': [],
            }
            
            # Собрать текущие сигналы только по отслеживаемым активам
            for symbol, signal in self.last_signals.items():
                if symbol not in self.watched_assets:
                    continue
                
                if signal in ['BUY', 'STRONG_BUY']:
                    report_data['buy_signals'].append(symbol)
                elif signal in ['SELL', 'STRONG_SELL']:
                    report_data['sell_signals'].append(symbol)
            
            # Отправить отчет
            from telegram_notifier import send_daily_report
            send_daily_report(report_data)
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке отчета: {e}")
    
    def stop(self):
        """Остановить систему"""
        self.running = False
        self.logger.info("Система остановлена")
        send_status("⛔ Система анализа рынка остановлена")


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Market Analyzer for Raspberry Pi 5')
    parser.add_argument('--gui', action='store_true', help='Запустить с графическим интерфейсом')
    parser.add_argument('--no-init', action='store_true', help='Пропустить инициализацию')
    parser.add_argument('--config', help='Путь к файлу конфигурации')
    
    args = parser.parse_args()
    
    logger.info("╔════════════════════════════════════════╗")
    logger.info("║  Market Analyzer v1.0 - Raspberry Pi 5 ║")
    logger.info("║  Local Trading Signal Generator        ║")
    logger.info("╚════════════════════════════════════════╝")
    
    # Создать систему
    system = MarketAnalyzerSystem(use_gui=args.gui)
    
    # Инициализировать
    if not args.no_init:
        if not system.initialize():
            logger.error("Не удалось инициализировать систему")
            return
    
    # Запустить в отдельном потоке если используется GUI
    if args.gui:
        import threading
        analysis_thread = threading.Thread(target=system.run, daemon=True)
        analysis_thread.start()
        
        # Запустить GUI в основном потоке
        from gui import run_gui
        run_gui()
    else:
        # CLI режим - запустить анализ в цикле
        system.run()


if __name__ == '__main__':
    main()
