"""
Модуль для отправки уведомлений через Telegram с интерактивным ботом
"""
import asyncio
import json
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import error

from config import TELEGRAM_CONFIG, ASSETS, DATA_DIR
from utils import get_logger, signal_to_emoji, format_price

logger = get_logger('TelegramNotifier')

class TelegramNotifier:
    """Отправитель уведомлений через Telegram с интерактивным ботом"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_CONFIG['BOT_TOKEN']
        self.chat_id = TELEGRAM_CONFIG['CHAT_ID']
        self.enabled = bool(self.bot_token and self.chat_id)
        self.logger = get_logger('TelegramNotifier')
        self.watched_assets_file = DATA_DIR / 'watched_assets.json'
        self.watched_assets = self._load_watched_assets()
        
        if self.enabled:
            try:
                self.bot = Bot(token=self.bot_token)
                self.app = None  # Инициализируется в start_bot()
                self.logger.info("Telegram бот инициализирован")
            except Exception as e:
                self.logger.error(f"Ошибка при инициализации бота: {e}")
                self.enabled = False
        else:
            self.logger.warning("Telegram не настроен (BOT_TOKEN или CHAT_ID не установлены)")
    
    def _load_watched_assets(self):
        """Загрузить список отслеживаемых активов"""
        try:
            if self.watched_assets_file.exists():
                with open(self.watched_assets_file, 'r') as f:
                    data = json.load(f)
                    return data.get('watched', ['AAPL', 'BTC-USD'])
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке watched_assets: {e}")
        
        return ['AAPL', 'BTC-USD']  # День по умолчанию
    
    def _save_watched_assets(self):
        """Сохранить список отслеживаемых активов"""
        try:
            with open(self.watched_assets_file, 'w') as f:
                json.dump({'watched': self.watched_assets}, f, indent=2)
            self.logger.debug("Отслеживаемые активы сохранены")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении watched_assets: {e}")
    
    def is_asset_watched(self, symbol):
        """Проверить, отслеживается ли актив"""
        return symbol in self.watched_assets
    
    def add_watched_asset(self, symbol):
        """Добавить актив в отслеживание"""
        if symbol not in self.watched_assets:
            self.watched_assets.append(symbol)
            self._save_watched_assets()
            self.logger.info(f"Добавлен {symbol} в отслеживание")
            return True
        return False
    
    def remove_watched_asset(self, symbol):
        """Удалить актив из отслеживания"""
        if symbol in self.watched_assets:
            self.watched_assets.remove(symbol)
            self._save_watched_assets()
            self.logger.info(f"Удален {symbol} из отслеживания")
            return True
        return False
    
    def toggle_watched_asset(self, symbol):
        """Переключить отслеживание актива"""
        if self.is_asset_watched(symbol):
            return self.remove_watched_asset(symbol)
        else:
            return self.add_watched_asset(symbol)
    
    def send_signal(self, signal_data):
        """
        Отправить сигнал торговли
        
        Args:
            signal_data: dict с данными сигнала от SignalGenerator
        """
        if not self.enabled or not TELEGRAM_CONFIG['SEND_SIGNALS']:
            return False
        
        # Проверить, отслеживается ли актив
        symbol = signal_data.get('symbol')
        if not self.is_asset_watched(symbol):
            self.logger.debug(f"Актив {symbol} не в списке отслеживания, сигнал не отправлен")
            return False
        
        try:
            message = self._format_signal_message(signal_data)
            keyboard = self._create_signal_keyboard(symbol)
            return self._send_message(message, parse_mode='HTML', reply_markup=keyboard)
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сигнала: {e}")
            return False
    
    def send_status(self, status_text):
        """Отправить статус сообщение"""
        if not self.enabled:
            return False
        
        try:
            message = f"📊 <b>Статус системы</b>\n{status_text}"
            return self._send_message(message, parse_mode='HTML')
        except Exception as e:
            self.logger.error(f"Ошибка при отправке статуса: {e}")
            return False
    
    def send_error(self, error_text):
        """Отправить сообщение об ошибке"""
        if not self.enabled or not TELEGRAM_CONFIG['SEND_ERRORS']:
            return False
        
        try:
            message = f"⚠️ <b>ОШИБКА</b>\n{error_text}"
            return self._send_message(message, parse_mode='HTML')
        except Exception as e:
            self.logger.error(f"Ошибка при отправке ошибки: {e}")
            return False
    
    def send_daily_report(self, report_data):
        """Отправить ежедневный отчет"""
        if not self.enabled:
            return False
        
        try:
            message = self._format_daily_report(report_data)
            return self._send_message(message, parse_mode='HTML')
        except Exception as e:
            self.logger.error(f"Ошибка при отправке отчета: {e}")
            return False
    
    def _create_signal_keyboard(self, symbol):
        """Создать клавиатуру для сигнала с кнопкой отслеживания"""
        watched = self.is_asset_watched(symbol)
        btn_text = f"✓ Отслеживаем {symbol}" if watched else f"➕ Следить за {symbol}"
        
        keyboard = [
            [InlineKeyboardButton(btn_text, callback_data=f"watch_{symbol}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _create_assets_menu_keyboard(self):
        """Создать клавиатуру меню управления активами"""
        keyboard = []
        
        for asset in ASSETS:
            symbol = asset['symbol']
            watched = self.is_asset_watched(symbol)
            emoji = "✓" if watched else "✗"
            btn_text = f"{emoji} {symbol} - {asset['name']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"toggle_{symbol}")])
        
        # Кнопка сохранить
        keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="done")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def _format_signal_message(self, signal_data):
        """Форматировать сообщение сигнала"""
        symbol = signal_data.get('symbol', 'N/A')
        signal = signal_data.get('signal', 'HOLD')
        confidence = signal_data.get('confidence', 0)
        price = signal_data.get('price', 0)
        recommendation = signal_data.get('recommendation', '')
        
        emoji = signal_to_emoji(signal)
        
        # Основная информация
        message = (
            f"{emoji} <b>{symbol}</b> - {signal}\n"
            f"Уверенность: <b>{confidence*100:.1f}%</b>\n"
            f"Цена: <b>{format_price(price)}</b>\n"
            f"Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
        )
        
        # Рекомендация
        if recommendation:
            message += f"📋 {recommendation}\n\n"
        
        # Причины сигнала
        buy_reasons = signal_data.get('buy_reasons', [])
        sell_reasons = signal_data.get('sell_reasons', [])
        
        if buy_reasons:
            message += "✅ Причины покупки:\n"
            for reason in buy_reasons[:3]:  # Максимум 3 причины
                message += f"  • {reason}\n"
        
        if sell_reasons:
            message += "❌ Причины продажи:\n"
            for reason in sell_reasons[:3]:
                message += f"  • {reason}\n"
        
        # Уровни
        stop_loss = signal_data.get('stop_loss')
        take_profit = signal_data.get('take_profit')
        
        if stop_loss:
            message += f"\n🛑 Stop Loss: {format_price(stop_loss)}\n"
        if take_profit:
            message += f"🎯 Take Profit: {format_price(take_profit)}\n"
        
        return message
    
    def _format_daily_report(self, report_data):
        """Форматировать ежедневный отчет"""
        message = "📊 <b>ЕЖЕДНЕВНЫЙ ОТЧЕТ</b>\n"
        message += f"Дата: {datetime.now().strftime('%d.%m.%Y')}\n\n"
        
        # Сигналы
        buy_signals = report_data.get('buy_signals', [])
        sell_signals = report_data.get('sell_signals', [])
        
        if buy_signals:
            message += f"📈 Сигналы на покупку: {len(buy_signals)}\n"
            for symbol in buy_signals[:5]:
                message += f"  • {symbol}\n"
        
        if sell_signals:
            message += f"\n📉 Сигналы на продажу: {len(sell_signals)}\n"
            for symbol in sell_signals[:5]:
                message += f"  • {symbol}\n"
        
        # Статистика
        if 'total_assets' in report_data:
            message += f"\nВсего активов проанализировано: {report_data['total_assets']}\n"
        
        if 'profit_loss' in report_data:
            pl = report_data['profit_loss']
            emoji = "📈" if pl > 0 else "📉"
            message += f"{emoji} P/L: {pl:+.2f}%\n"
        
        return message
    
    def _send_message(self, text, parse_mode='HTML'):
        """Отправить сообщение"""
        if not self.enabled:
            self.logger.debug("Telegram отключен, сообщение не отправлено")
            return False
        
        try:
            # Использовать синхронный запрос через loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode=parse_mode
                )
            )
            
            loop.close()
            
            self.logger.debug(f"Сообщение отправлено в Telegram")
            return True
            
        except error.TelegramError as e:
            self.logger.error(f"Telegram ошибка: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка при отправке: {e}")
            return False
    
    def _send_message(self, text, parse_mode='HTML', reply_markup=None):
        """Отправить сообщение"""
        if not self.enabled:
            self.logger.debug("Telegram отключен, сообщение не отправлено")
            return False
        
        try:
            # Использовать синхронный запрос через loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            )
            
            loop.close()
            
            self.logger.debug(f"Сообщение отправлено в Telegram")
            return True
            
        except error.TelegramError as e:
            self.logger.error(f"Telegram ошибка: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка при отправке: {e}")
            return False
    
    def show_assets_menu(self):
        """Отправить меню управления активами"""
        if not self.enabled:
            return False
        
        try:
            message = "📊 <b>Управление отслеживаемыми активами</b>\n\n"
            message += "Выберите активы, сигналы которых хотите получать:\n"
            message += f"(Отслеживается: {len(self.watched_assets)} активов)\n\n"
            
            for asset in ASSETS:
                watched = self.is_asset_watched(asset['symbol'])
                emoji = "✓" if watched else "✗"
                message += f"{emoji} {asset['symbol']} - {asset['name']}\n"
            
            keyboard = self._create_assets_menu_keyboard()
            return self._send_message(message, parse_mode='HTML', reply_markup=keyboard)
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке меню активов: {e}")
            return False
    
    def show_status(self):
        """Отправить статус текущих отслеживаемых активов"""
        if not self.enabled:
            return False
        
        try:
            message = "📈 <b>Текущие отслеживаемые активы</b>\n\n"
            
            if not self.watched_assets:
                message += "❌ Нет отслеживаемых активов\n\n"
            else:
                message += f"✓ Отслеживаемые активы ({len(self.watched_assets)}):\n"
                for symbol in self.watched_assets:
                    for asset in ASSETS:
                        if asset['symbol'] == symbol:
                            message += f"  • {symbol} - {asset['name']}\n"
                            break
            
            message += f"\nВсего активов доступно: {len(ASSETS)}\n"
            
            # Кнопка управления
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Управлять активами", callback_data="manage_assets")]
            ])
            
            return self._send_message(message, parse_mode='HTML', reply_markup=keyboard)
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке статуса: {e}")
            return False
    
    def test_connection(self):
        """Проверить подключение к Telegram"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self.bot.get_me())
            loop.close()
            
            self.logger.info(f"Подключение к Telegram успешно: {result.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при проверке подключения: {e}")
            return False


# Глобальный экземпляр отправителя
notifier = TelegramNotifier()

def send_signal(signal_data):
    """Отправить сигнал"""
    return notifier.send_signal(signal_data)

def send_status(status_text):
    """Отправить статус"""
    return notifier.send_status(status_text)

def send_error(error_text):
    """Отправить ошибку"""
    return notifier.send_error(error_text)

def send_daily_report(report_data):
    """Отправить отчет"""
    return notifier.send_daily_report(report_data)

def show_assets_menu():
    """Показать меню управления активами"""
    return notifier.show_assets_menu()

def show_status():
    """Показать статус отслеживаемых активов"""
    return notifier.show_status()

def is_asset_watched(symbol):
    """Проверить, отслеживается ли актив"""
    return notifier.is_asset_watched(symbol)

# === АСИНХРОННЫЕ ОБРАБОТЧИКИ КОМАНД ===

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    message = (
        "👋 <b>Добро пожаловать в Market Analyzer!</b>\n\n"
        "🤖 Этот бот отправляет сигналы торговли по выбранным активам.\n\n"
        "<b>Доступные команды:</b>\n"
        "/status - Статус отслеживаемых активов\n"
        "/manage - Управление активами\n"
        "/help - Справка\n\n"
        "Используйте кнопки ниже для управления активами."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Управлять активами", callback_data="manage_assets")],
        [InlineKeyboardButton("📊 Статус", callback_data="status")]
    ])
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    message = (
        "<b>📖 Справка Market Analyzer</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/status - Показать статус\n"
        "/manage - Управлять активами\n"
        "/help - Эта справка\n\n"
        "<b>Как использовать:</b>\n"
        "1️⃣ Нажмите /manage для выбора активов\n"
        "2️⃣ Выберите активы кнопками\n"
        "3️⃣ Нажмите ✅ Готово\n"
        "4️⃣ Система начнет отправлять сигналы\n\n"
        "<b>Типы сигналов:</b>\n"
        "🚀 STRONG_BUY - Очень сильный сигнал покупки\n"
        "📈 BUY - Сигнал покупки\n"
        "➡️ HOLD - Нейтральный сигнал\n"
        "📉 SELL - Сигнал продажи\n"
        "💥 STRONG_SELL - Очень сильный сигнал продажи\n"
    )
    await update.message.reply_text(message, parse_mode='HTML')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "manage_assets":
        # Показать меню управления активами
        message = (
            "📊 <b>Управление отслеживаемыми активами</b>\n\n"
            "Выберите активы, сигналы которых хотите получать:\n"
            f"(Отслеживается: {len(notifier.watched_assets)} активов)\n"
        )
        keyboard = notifier._create_assets_menu_keyboard()
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
    
    elif data == "status":
        # Показать статус
        message = "📈 <b>Текущие отслеживаемые активы</b>\n\n"
        
        if not notifier.watched_assets:
            message += "❌ Нет отслеживаемых активов\n\n"
        else:
            message += f"✓ Отслеживаемые активы ({len(notifier.watched_assets)}):\n"
            for symbol in notifier.watched_assets:
                for asset in ASSETS:
                    if asset['symbol'] == symbol:
                        message += f"  • {symbol} - {asset['name']}\n"
                        break
        
        message += f"\nВсего активов доступно: {len(ASSETS)}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Управлять активами", callback_data="manage_assets")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu")]
        ])
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
    
    elif data == "menu":
        # Главное меню
        message = (
            "👋 <b>Market Analyzer Главное меню</b>\n\n"
            "Выберите действие:"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Управлять активами", callback_data="manage_assets")],
            [InlineKeyboardButton("📊 Статус", callback_data="status")]
        ])
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
    
    elif data == "done":
        # Сохранить выбор
        message = (
            "✅ <b>Сохранено!</b>\n\n"
            f"Отслеживаемые активы ({len(notifier.watched_assets)}):\n"
        )
        for symbol in notifier.watched_assets:
            for asset in ASSETS:
                if asset['symbol'] == symbol:
                    message += f"  • {symbol} - {asset['name']}\n"
                    break
        
        message += "\n🔔 Будут отправляться только сигналы по этим активам."
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Меню", callback_data="menu")]
        ])
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
    
    elif data.startswith("toggle_"):
        # Переключить актив
        symbol = data.replace("toggle_", "")
        notifier.toggle_watched_asset(symbol)
        
        # Перерисовать меню
        message = (
            "📊 <b>Управление отслеживаемыми активами</b>\n\n"
            "Выберите активы, сигналы которых хотите получать:\n"
            f"(Отслеживается: {len(notifier.watched_assets)} активов)\n"
        )
        keyboard = notifier._create_assets_menu_keyboard()
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
    
    elif data.startswith("watch_"):
        # Кнопка отслеживания из сигнала
        symbol = data.replace("watch_", "")
        notifier.toggle_watched_asset(symbol)
        
        watched = notifier.is_asset_watched(symbol)
        status = "✓ Добавлен" if watched else "✗ Удален"
        message = f"{status} в отслеживание: <b>{symbol}</b>"
        
        await query.answer(message)

def get_telegram_handlers():
    """Получить список обработчиков команд для регистрации"""
    return [
        ("start", start_handler),
        ("help", help_handler),
        ("callback", callback_handler)
    ]
