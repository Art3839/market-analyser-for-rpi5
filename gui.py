"""
Графический интерфейс для системы анализа рынка
Легковесный GUI с использованием Tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import pandas as pd
import numpy as np
from datetime import datetime
import queue

from config import GUI_CONFIG, ASSETS, DATA_DIR
from utils import get_logger, format_price, format_percent, signal_to_emoji, load_json, save_json
from data_collector import DataCollector
from indicator_analysis import IndicatorAnalyzer
from signal_generator import SignalGenerator

logger = get_logger('GUI')

class MarketAnalyzerGUI:
    """Главный класс графического интерфейса"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Market Analyzer - Raspberry Pi 5")
        self.root.geometry(f"{GUI_CONFIG['WINDOW_WIDTH']}x{GUI_CONFIG['WINDOW_HEIGHT']}")
        
        self.data_collector = DataCollector()
        self.signal_generators = {}
        self.indicator_analyzer = IndicatorAnalyzer()
        
        self.logger = get_logger('GUI')
        self.data_queue = queue.Queue()
        self.running = True
        
        # Загрузить отслеживаемые активы
        watched_file = DATA_DIR / 'watched_assets.json'
        if watched_file.exists():
            data = load_json('watched_assets.json')
            self.watched_assets = data.get('watched', ['AAPL', 'BTC-USD'])
        else:
            self.watched_assets = ['AAPL', 'BTC-USD']
        
        # Инициализировать генераторы сигналов
        for asset in ASSETS:
            self.signal_generators[asset['symbol']] = SignalGenerator(asset['symbol'])
        
        self._setup_styles()
        self._create_widgets()
        self._start_background_tasks()
    
    def _setup_styles(self):
        """Настроить стили"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цвета
        self.bg_color = '#f0f0f0' if GUI_CONFIG['THEME'] == 'light' else '#1e1e1e'
        self.fg_color = '#000000' if GUI_CONFIG['THEME'] == 'light' else '#ffffff'
        self.accent_color = '#2196F3'
        
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton', background=self.accent_color)
    
    def _create_widgets(self):
        """Создать виджеты интерфейса"""
        
        # === ГЛАВНОЕ МЕНЮ ===
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self._show_settings)
        file_menu.add_command(label="Refresh Data", command=self._refresh_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
        # === ВЕРХНЯЯ ПАНЕЛЬ (Управление) ===
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(top_frame, text="Market Analyzer", font=('Arial', 18, 'bold')).pack(side='left')
        
        # Блок выбора активов
        asset_frame = ttk.LabelFrame(top_frame, text="Watched Assets")
        asset_frame.pack(side='left', padx=10)
        
        ttk.Label(asset_frame, text="Select:").pack(side='left', padx=5)
        
        self.watched_var = tk.StringVar()
        self.watched_combo = ttk.Combobox(
            asset_frame,
            textvariable=self.watched_var,
            values=self.watched_assets,
            width=15,
            state='readonly'
        )
        self.watched_combo.pack(side='left', padx=5)
        if self.watched_assets:
            self.watched_combo.current(0)
        
        ttk.Button(
            asset_frame,
            text="📋 Manage",
            command=self._show_asset_manager
        ).pack(side='left', padx=5)
        
        # Кнопки управления
        btn_refresh = ttk.Button(top_frame, text="🔄 Refresh", command=self._refresh_all_data)
        btn_refresh.pack(side='right', padx=5)
        
        btn_analyze = ttk.Button(top_frame, text="📊 Analyze", command=self._analyze_all)
        btn_analyze.pack(side='right', padx=5)
        
        # === ОСНОВНОЙ КОНТЕНТ (Ноутбук) ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка: Обзор сигналов
        self._create_signals_tab()
        
        # Вкладка: Детальный анализ
        self._create_analysis_tab()
        
        # Вкладка: Логи
        self._create_logs_tab()
        
        # === НИЖНЯЯ ПАНЕЛЬ (Статус) ===
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill='x', padx=10, pady=10)
        
        self.status_label = ttk.Label(
            bottom_frame,
            text="Инициализация...",
            relief='sunken'
        )
        self.status_label.pack(fill='x')
    
    def _create_signals_tab(self):
        """Создать вкладку с сигналами"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Signals Overview")
        
        # Таблица сигналов
        columns = ('Symbol', 'Signal', 'Price', 'Confidence', 'Status')
        self.signals_tree = ttk.Treeview(frame, columns=columns, height=20)
        
        self.signals_tree.column('#0', width=0, stretch=tk.NO)
        self.signals_tree.column('Symbol', anchor=tk.W, width=100)
        self.signals_tree.column('Signal', anchor=tk.CENTER, width=100)
        self.signals_tree.column('Price', anchor=tk.E, width=100)
        self.signals_tree.column('Confidence', anchor=tk.CENTER, width=100)
        self.signals_tree.column('Status', anchor=tk.W, width=150)
        
        self.signals_tree.heading('#0', text='', anchor=tk.W)
        self.signals_tree.heading('Symbol', text='Symbol', anchor=tk.W)
        self.signals_tree.heading('Signal', text='Signal', anchor=tk.CENTER)
        self.signals_tree.heading('Price', text='Price', anchor=tk.E)
        self.signals_tree.heading('Confidence', text='Confidence', anchor=tk.CENTER)
        self.signals_tree.heading('Status', text='Reason', anchor=tk.W)
        
        # Скролбар
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.signals_tree.yview)
        self.signals_tree.configure(yscroll=scrollbar.set)
        
        self.signals_tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
    
    def _create_analysis_tab(self):
        """Создать вкладку детального анализа"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Detailed Analysis")
        
        # Выбор актива
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(select_frame, text="Select Asset:").pack(side='left')
        
        self.asset_var = tk.StringVar()
        asset_symbols = [a['symbol'] for a in ASSETS]
        asset_combo = ttk.Combobox(
            select_frame,
            textvariable=self.asset_var,
            values=asset_symbols,
            state='readonly'
        )
        asset_combo.pack(side='left', padx=5)
        if asset_symbols:
            asset_combo.current(0)
        
        ttk.Button(
            select_frame,
            text="Load",
            command=self._load_asset_details
        ).pack(side='left', padx=5)
        
        # Текстовое поле с деталями
        self.details_text = scrolledtext.ScrolledText(frame, height=25, width=100)
        self.details_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def _create_logs_tab(self):
        """Создать вкладку логов"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Logs")
        
        self.logs_text = scrolledtext.ScrolledText(frame, height=25, width=100)
        self.logs_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Добавить первое сообщение
        self._add_log("System started")
    
    def _refresh_all_data(self):
        """Обновить данные для всех активов"""
        self._update_status("Обновление данных...")
        
        thread = threading.Thread(target=self._refresh_data_thread, daemon=True)
        thread.start()
    
    def _refresh_data_thread(self):
        """Поток для обновления данных"""
        try:
            for asset in ASSETS:
                symbol = asset['symbol']
                self._add_log(f"Обновление {symbol}...")
                
                # Загрузить или обновить данные
                df = self.data_collector.download_historical_data(symbol)
                
                if df is not None:
                    # Рассчитать индикаторы
                    df = self.indicator_analyzer.calculate_all_indicators(df)
                    self._add_log(f"✓ {symbol} обновлен ({len(df)} свечей)")
            
            self._update_status("Data updated successfully")
            
        except Exception as e:
            self._add_log(f"❌ Error: {e}")
            self._update_status(f"Error: {e}")
    
    def _analyze_all(self):
        """Проанализировать все активы"""
        self._update_status("Analyzing all assets...")
        
        thread = threading.Thread(target=self._analyze_thread, daemon=True)
        thread.start()
    
    def _analyze_thread(self):
        """Поток для анализа"""
        try:
            # Очистить таблицу сигналов
            for item in self.signals_tree.get_children():
                self.signals_tree.delete(item)
            
            # Получить выбранные активы или использовать все отслеживаемые
            selected_symbol = self.watched_var.get()
            if selected_symbol:
                # Анализировать только выбранный актив
                symbols_to_analyze = [selected_symbol]
            else:
                # Анализировать все отслеживаемые
                symbols_to_analyze = self.watched_assets if self.watched_assets else [a['symbol'] for a in ASSETS]
            
            for asset in ASSETS:
                symbol = asset['symbol']
                name = asset['name']
                
                # Пролистать если не в отслеживаемом списке
                if symbol not in symbols_to_analyze:
                    continue
                
                # Получить данные
                df = self.data_collector.get_data(symbol, lookback=200)
                
                if df.empty or len(df) < 50:
                    continue
                
                try:
                    # Рассчитать индикаторы если нет
                    if 'RSI' not in df.columns:
                        df = self.indicator_analyzer.calculate_all_indicators(df)
                    
                    # Генерировать сигнал
                    signal_gen = self.signal_generators[symbol]
                    signal_data = signal_gen.generate_signal(df)
                    
                    # Добавить в таблицу
                    signal = signal_data['signal']
                    confidence = signal_data['confidence']
                    price = signal_data['price']
                    reason = signal_data['buy_reasons'][0] if signal_data['buy_reasons'] else \
                             signal_data['sell_reasons'][0] if signal_data['sell_reasons'] else 'N/A'
                    
                    # Теговать цвет
                    tags = []
                    if signal == 'BUY':
                        tags.append('buy')
                    elif signal == 'SELL':
                        tags.append('sell')
                    elif signal == 'STRONG_BUY':
                        tags.append('strong_buy')
                    elif signal == 'STRONG_SELL':
                        tags.append('strong_sell')
                    
                    # Настроить теги
                    if not hasattr(self, 'tags_configured'):
                        self.signals_tree.tag_configure('buy', foreground='green')
                        self.signals_tree.tag_configure('sell', foreground='red')
                        self.signals_tree.tag_configure('strong_buy', foreground='darkgreen')
                        self.signals_tree.tag_configure('strong_sell', foreground='darkred')
                        self.tags_configured = True
                    
                    self.signals_tree.insert(
                        '',
                        'end',
                        values=(
                            f"{name} ({symbol})",
                            signal,
                            format_price(price),
                            f"{confidence*100:.1f}%",
                            reason[:50]
                        ),
                        tags=tags
                    )
                    
                    self._add_log(f"{symbol}: {signal} ({confidence*100:.1f}%)")
                    
                except Exception as e:
                    self._add_log(f"Error analyzing {symbol}: {e}")
            
            self._update_status("Analysis complete")
            
        except Exception as e:
            self._add_log(f"❌ Analysis error: {e}")
            self._update_status(f"Error: {e}")
    
    def _load_asset_details(self):
        """Загрузить детали актива"""
        symbol = self.asset_var.get()
        if not symbol:
            return
        
        thread = threading.Thread(
            target=self._load_asset_details_thread,
            args=(symbol,),
            daemon=True
        )
        thread.start()
    
    def _load_asset_details_thread(self, symbol):
        """Поток для загрузки деталей"""
        try:
            df = self.data_collector.get_data(symbol, lookback=200)
            
            if df.empty:
                self.details_text.delete('1.0', tk.END)
                self.details_text.insert(tk.END, f"No data for {symbol}")
                return
            
            # Рассчитать индикаторы
            if 'RSI' not in df.columns:
                df = self.indicator_analyzer.calculate_all_indicators(df)
            
            # Генерировать сигнал
            signal_gen = self.signal_generators[symbol]
            signal_data = signal_gen.generate_signal(df)
            
            # Форматировать информацию
            text = f"=== {symbol} Analysis ===\n\n"
            text += f"Signal: {signal_data['signal']}\n"
            text += f"Confidence: {signal_data['confidence']*100:.1f}%\n"
            text += f"Price: {format_price(signal_data['price'])}\n\n"
            
            text += "=== Indicators ===\n"
            close = df['Close'].iloc[-1]
            
            if 'SMA_FAST' in df.columns:
                text += f"SMA(20): {df['SMA_FAST'].iloc[-1]:.2f}\n"
            if 'SMA_SLOW' in df.columns:
                text += f"SMA(50): {df['SMA_SLOW'].iloc[-1]:.2f}\n"
            if 'RSI' in df.columns:
                text += f"RSI(14): {df['RSI'].iloc[-1]:.1f}\n"
            if 'MACD' in df.columns:
                text += f"MACD: {df['MACD'].iloc[-1]:.2e}\n"
            if 'BB_UPPER' in df.columns:
                text += f"BB Upper: {df['BB_UPPER'].iloc[-1]:.2f}\n"
                text += f"BB Middle: {df['BB_MIDDLE'].iloc[-1]:.2f}\n"
                text += f"BB Lower: {df['BB_LOWER'].iloc[-1]:.2f}\n"
            if 'ATR' in df.columns:
                text += f"ATR: {df['ATR'].iloc[-1]:.2f}\n"
            
            text += "\n=== Recommendation ===\n"
            text += signal_data['recommendation'] + "\n"
            
            text += "\n=== Buy Reasons ===\n"
            for reason in signal_data['buy_reasons']:
                text += f"• {reason}\n"
            
            text += "\n=== Sell Reasons ===\n"
            for reason in signal_data['sell_reasons']:
                text += f"• {reason}\n"
            
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert(tk.END, text)
            
        except Exception as e:
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert(tk.END, f"Error: {e}")
    
    def _add_log(self, message):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        self.logs_text.insert(tk.END, log_message)
        self.logs_text.see(tk.END)
        self.root.update()
    
    def _update_status(self, status):
        """Обновить статус"""
        self.status_label.config(text=status)
        self.root.update()
    
    def _show_settings(self):
        """Показать окно настроек"""
        messagebox.showinfo(
            "Settings",
            "Settings dialog will be implemented.\n"
            "For now, edit config.py directly."
        )
    
    def _show_about(self):
        """Показать информацию о программе"""
        messagebox.showinfo(
            "About Market Analyzer",
            "Market Analyzer v1.0\n\n"
            "Local market analysis system for Raspberry Pi 5\n"
            "with technical indicators and ML-based signals\n\n"
            "© 2025"
        )
    
    def _show_asset_manager(self):
        """Показать менеджер активов"""
        manager_window = tk.Toplevel(self.root)
        manager_window.title("Manage Watched Assets")
        manager_window.geometry("400x500")
        
        # Заголовок
        ttk.Label(
            manager_window,
            text="Select assets to watch",
            font=('Arial', 12, 'bold')
        ).pack(padx=10, pady=10)
        
        # Frame для чекбоксов
        checkbox_frame = ttk.Frame(manager_window)
        checkbox_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Скролл
        canvas = tk.Canvas(checkbox_frame)
        scrollbar = ttk.Scrollbar(checkbox_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Переменные для чекбоксов
        self.asset_vars = {}
        
        for asset in ASSETS:
            symbol = asset['symbol']
            var = tk.BooleanVar(value=symbol in self.watched_assets)
            self.asset_vars[symbol] = var
            
            chk = ttk.Checkbutton(
                scrollable_frame,
                text=f"{symbol} - {asset['name']}",
                variable=var
            )
            chk.pack(anchor='w', pady=2)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Кнопки
        btn_frame = ttk.Frame(manager_window)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        def save_watched():
            self.watched_assets = [sym for sym, var in self.asset_vars.items() if var.get()]
            
            if not self.watched_assets:
                messagebox.showwarning("Warning", "Please select at least one asset")
                return
            
            # Сохранить в файл
            save_json({'watched': self.watched_assets}, 'watched_assets.json')
            
            # Обновить комбобокс
            self.watched_combo['values'] = self.watched_assets
            if self.watched_assets:
                self.watched_combo.current(0)
            
            self._add_log(f"✓ Отслеживаемые активы обновлены: {len(self.watched_assets)} активов")
            messagebox.showinfo("Success", f"Saved {len(self.watched_assets)} watched assets")
            manager_window.destroy()
        
        ttk.Button(btn_frame, text="✅ Save", command=save_watched).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❌ Cancel", command=manager_window.destroy).pack(side='left', padx=5)
    
    def _start_background_tasks(self):
        """Запустить фоновые задачи"""
        thread = threading.Thread(target=self._background_update_loop, daemon=True)
        thread.start()
    
    def _background_update_loop(self):
        """Цикл фонового обновления"""
        while self.running:
            try:
                # Периодическое обновление можно добавить здесь
                import time
                time.sleep(GUI_CONFIG['UPDATE_GUI_INTERVAL'] / 1000)
            except Exception as e:
                self._add_log(f"Background error: {e}")
    
    def _on_closing(self):
        """Завершить программу"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            self.root.destroy()


def run_gui():
    """Запустить GUI"""
    root = tk.Tk()
    gui = MarketAnalyzerGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui._on_closing)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
