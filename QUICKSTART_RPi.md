# Quick Start Guide - Raspberry Pi 5

## 🚀 Быстрый старт (5 минут)

### Шаг 1: Подготовка Raspberry Pi

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить необходимые пакеты
sudo apt install -y python3 python3-pip python3-venv git
```

### Шаг 2: Загрузить проект

```bash
# Перейти в домашнюю директорию
cd ~

# Клонировать или скопировать проект
git clone <URL проекта>
cd market-analyzer

# Или если скопировали вручную
cd /path/to/market-analyzer
```

### Шаг 3: Инициализировать окружение

```bash
# Запустить скрипт установки
bash setup.sh

# Или вручную
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 4: Настроить Telegram (опционально)

```bash
# Установить переменные окружения
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export TELEGRAM_CHAT_ID="987654321"

# Или отредактировать config.py вручную
nano config.py
```

### Шаг 5: Запустить первый анализ

```bash
# Активировать окружение
source venv/bin/activate

# Запустить тесты
python test_system.py

# Запустить примеры
python examples.py

# Запустить основную программу
python main.py          # CLI режим
python main.py --gui    # GUI режим
```

## 📖 Пошаговая установка на Raspberry Pi

### Требования
- Raspberry Pi 5 (минимум 2GB RAM)
- MicroSD карта 32GB+
- Интернет соединение
- Питание 5V/5A

### Детальные шаги

#### 1. Установить Raspbian OS

1. Скачать Raspberry Pi Imager
2. Выбрать Raspberry Pi 5
3. Выбрать "Raspberry Pi OS Lite" (минимальная версия)
4. Записать на SD карту

#### 2. Первый запуск

```bash
# После загрузки, подключиться по SSH
ssh pi@raspberrypi.local

# Или используя монитор и клавиатуру локально
# Пароль по умолчанию: raspberry
```

#### 3. Расширить файловую систему

```bash
# Запустить конфигурацию
sudo raspi-config

# Выбрать: 6 Advanced Options → A1 Expand Filesystem
# Перезагрузиться: sudo reboot
```

#### 4. Установить Git и Python

```bash
# Обновить репозитории
sudo apt update && sudo apt upgrade -y

# Установить зависимости
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    libatlas-base-dev \
    libjasper-dev \
    libtiff5 \
    libjasper1 \
    libharfbuzz0b \
    libwebp6
```

#### 5. Клонировать проект

```bash
# Перейти в домашнюю директорию
cd ~

# Клонировать репозиторий
git clone https://github.com/your-username/market-analyzer.git
cd market-analyzer

# Или скопировать вручную через SCP:
# scp -r /path/to/market-analyzer pi@raspberrypi.local:~/
```

#### 6. Создать виртуальное окружение

```bash
# Создать окружение (может занять 3-5 минут!)
python3 -m venv venv

# Активировать
source venv/bin/activate

# Обновить pip
pip install --upgrade pip
```

#### 7. Установить зависимости

```bash
# Это может занять 10-20 минут на RPi 5!
pip install -r requirements.txt

# Если возникают проблемы, использовать:
pip install --only-binary :all: -r requirements.txt
```

#### 8. Настроить конфигурацию

```bash
# Отредактировать основную конфигурацию
nano config.py

# Ключевые параметры для RPi:
# - Уменьшить ASSETS до 5-10 активов
# - Увеличить UPDATE_INTERVAL_MINUTES до 15-30
# - Включить USE_ML_MODEL = True
```

#### 9. Установить Telegram (опционально)

```bash
# Установить переменные окружения
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Или добавить в ~/.bashrc для постоянного использования:
echo "export TELEGRAM_BOT_TOKEN='your_token'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your_chat_id'" >> ~/.bashrc
source ~/.bashrc
```

#### 10. Проверить установку

```bash
# Активировать окружение
source venv/bin/activate

# Запустить тесты
python test_system.py

# Все тесты должны пройти!
```

## 🔄 Запуск на Raspberry Pi

### Вариант 1: Ручной запуск (разработка)

```bash
# Активировать окружение
source ~/market-analyzer/venv/bin/activate

# Запустить в фоне
cd ~/market-analyzer
nohup python main.py > log.txt 2>&1 &

# Проверить логи
tail -f log.txt
```

### Вариант 2: Systemd сервис (продакшн)

```bash
# Отредактировать пути в market-analyzer.service
sudo nano market-analyzer.service

# Скопировать сервис
sudo cp market-analyzer.service /etc/systemd/system/

# Включить и запустить
sudo systemctl daemon-reload
sudo systemctl enable market-analyzer
sudo systemctl start market-analyzer

# Проверить статус
sudo systemctl status market-analyzer

# Просмотреть логи
sudo journalctl -u market-analyzer -f
```

### Вариант 3: Запланированный запуск (cron)

```bash
# Открыть crontab
crontab -e

# Добавить строку для ежедневного запуска в 8:00
0 8 * * * cd /home/pi/market-analyzer && source venv/bin/activate && python main.py >> cron.log 2>&1

# Сохранить (Ctrl+X, Y, Enter)
```

### Вариант 4: GUI режим (если есть монитор)

```bash
# Если подключен монитор и клавиатура
source ~/market-analyzer/venv/bin/activate
cd ~/market-analyzer
python main.py --gui
```

## 🛠️ Отладка на RPi

### Проверить использование ресурсов

```bash
# Монитор системы
top -p $(pgrep -f "python main.py")

# Или более компактный формат
watch -n 1 'ps aux | grep python'

# Проверить память
free -h

# Проверить диск
df -h
```

### Если программа зависает

```bash
# Найти процесс
ps aux | grep python

# Завершить процесс
kill -9 <PID>

# Перезапустить
nohup python main.py &
```

### Если слабая интернет связь

```python
# В config.py увеличить таймауты
# В data_collector.py добавить retry логику

HISTORY_DAYS = 50  # Вместо 365 - меньше данных
UPDATE_INTERVAL_MINUTES = 30  # Вместо 5 - реже обновлять
```

### Если нехватает памяти

```python
# В config.py оптимизировать:
ASSETS = ASSETS[:5]  # Максимум 5 активов
HISTORY_DAYS = 100   # Вместо 365

# Отключить GUI (если запущен)
python main.py  # Вместо --gui
```

## 📊 Мониторинг на RPi

### Проверить статус сервиса

```bash
# Если используется systemd
sudo systemctl status market-analyzer

# Если запущено вручную
ps aux | grep "python main.py"

# Проверить, прослушивается ли порт (если есть API)
netstat -tuln | grep LISTEN
```

### Просмотреть логи

```bash
# Последние 20 строк логов
tail -20 logs/market_analyzer.log

# Следить за логами в реальном времени
tail -f logs/market_analyzer.log

# Поиск ошибок
grep ERROR logs/market_analyzer.log

# Последние критические ошибки
tail -100 logs/market_analyzer.log | grep ERROR
```

### Резервная копия данных

```bash
# Архивировать данные
tar -czf market-analyzer-backup-$(date +%Y%m%d).tar.gz \
    ~/market-analyzer/data/ \
    ~/market-analyzer/models/

# Скопировать на другую машину
scp market-analyzer-backup-*.tar.gz user@external-server:/backups/

# Восстановить из бэкапа
tar -xzf market-analyzer-backup-*.tar.gz
```

## ⚡ Оптимизация производительности на RPi 5

### 1. Использовать SSD вместо SD карты

```bash
# Установить SSD через USB
# Загрузить с SSD вместо SD


# Перебросить данные на SSD
sudo mv /var/log /mnt/ssd/log
sudo mv ~/market-analyzer/data /mnt/ssd/data

# Создать сим-линки
sudo ln -s /mnt/ssd/log /var/log
sudo ln -s /mnt/ssd/data ~/market-analyzer/data
```

### 2. Отключить ненужные сервисы

```bash
# Список сервисов
sudo systemctl list-unit-files

# Отключить bluetooth (если не нужен)
sudo systemctl disable bluetooth

# Отключить avahi (bonjour)
sudo systemctl disable avahi-daemon

# Перезагрузиться
sudo reboot
```

### 3. Увеличить swap память

```bash
# Отредактировать dphys-swapfile
sudo nano /etc/dphys-swapfile

# Найти CONF_SWAPSIZE и изменить на:
# CONF_SWAPSIZE=2048  (вместо 100)

# Перезагрузить swap
sudo /etc/init.d/dphys-swapfile restart
```

### 4. Разогнать CPU (осторожно!)

```bash
# Отредактировать конфигурацию ядра
sudo nano /boot/firmware/config.txt

# Добавить в конец:
# over_voltage=2
# arm_freq=2800

# Перезагрузиться
sudo reboot
```

## 🎯 Рекомендуемые параметры для RPi 5

```python
# config.py - оптимальные настройки для Raspberry Pi 5

ASSETS = [
    {'symbol': 'AAPL', 'type': 'stock', 'name': 'Apple'},
    {'symbol': 'MSFT', 'type': 'stock', 'name': 'Microsoft'},
    {'symbol': 'TSLA', 'type': 'stock', 'name': 'Tesla'},
    {'symbol': 'BTC-USD', 'type': 'crypto', 'name': 'Bitcoin'},
    {'symbol': 'ETH-USD', 'type': 'crypto', 'name': 'Ethereum'},
]  # Максимум 5-10 активов

HISTORY_DAYS = 100  # Вместо 365
UPDATE_INTERVAL_MINUTES = 15  # Вместо 5

ML_CONFIG = {
    'MODEL_TYPE': 'lightgbm',
    'HYPERPARAMETERS': {
        'n_estimators': 50,  # Вместо 100
        'max_depth': 5,      # Вместо 10
    }
}

GUI_CONFIG = {
    'SHOW_CHARTS': False,  # Отключить графики для экономии памяти
}
```

## 📲 Интеграция с мобильным телефоном

Вы можете получать сигналы на мобильный через Telegram:

1. Создайте бота в Telegram (@BotFather)
2. Получите токен и chat_id
3. Установите переменные окружения
4. Получайте уведомления в реальном времени

```bash
# Пример сообщения в Telegram:
🚀 AAPL - STRONG_BUY
Уверенность: 82.5%
Цена: $150.25
Рекомендация: СИЛЬНЫЙ СИГНАЛ ПОКУПКИ!
Входить на $150.25, SL: $147.50, TP: $153.00
```

## ❓ FAQ

**В: Как обновить проект?**
```bash
cd ~/market-analyzer
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart market-analyzer
```

**В: Как изменить активы?**
```bash
nano config.py
# Отредактировать ASSETS список
# Перезагрузить программу
```

**В: Как отменить обновление интервала?**
```python
# В config.py
UPDATE_INTERVAL_MINUTES = 5  # Вернуть на 5 минут
```

**В: Программа часто падает?**
```bash
# Проверить память
free -h

# Уменьшить количество активов или HISTORY_DAYS
# Увеличить UPDATE_INTERVAL_MINUTES

# Перезапустить
sudo systemctl restart market-analyzer
```

**В: Как удалить программу?**
```bash
sudo systemctl stop market-analyzer
sudo systemctl disable market-analyzer
sudo rm /etc/systemd/system/market-analyzer.service
rm -rf ~/market-analyzer
```

---

**Готово!** Система запущена и работает на вашем Raspberry Pi 5! 🎉

Для дополнительной информации смотрите:
- [README.md](README.md) - Полная документация
- [TECHNICAL.md](TECHNICAL.md) - Техническая справка
- [examples.py](examples.py) - Примеры использования
