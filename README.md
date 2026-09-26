# 🌐 Happ / VLESS Google GeoIP & Gemini Checker

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Android%20(Termux)%20%7C%20Windows%20%7C%20Linux-green.svg)]()
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Standard%20Library)-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Happ / VLESS Google GeoIP Checker** — высокоскоростная многопоточная утилита для проверки узлов вашей VPN/VLESS-подписки на чистоту определения в **Google Search** и доступность **Google Gemini AI** без разрыва текущего соединения.

---

## ❓ В чем проблема?

Многие пользователи VLESS / Happ / Hiddify / Marzban сталкиваются с ситуацией:
* Вы подключаетесь к серверу Великобритании, Германии или Нидерландов;
* Заходите на `google.com`, а внизу страницы отображается **«Россия»** (`utm_source=google-RU`);
* Google выдаёт бесконечные капчи (`429 Too Many Requests`), заблокирован **Google Gemini**, а в YouTube включается российский режим без премиум-функций.

### Почему это происходит?
Google **не использует** публичные базы GeoIP (MaxMind, Whois). Алгоритмы машинного обучения Google анализируют совокупность сигналов (тысячи русскоязычных пользователей со смартфонами и включенным GPS на одном IP) и ошибочно **перепривязывают IP зарубежного дата-центра к России**.

Данная утилита **за 15 секунд опрашивает все серверы подписки** и находит узлы с «чистыми» IP, которые Google видит как настоящую Европу, Азию или Америку.

---

## ✨ Возможности

* ⚡️ **Многопоточное сканирование (15 потоков)**: опрос 300+ нод за 15–20 секунд.
* 🛡 **Не прерывает основной VPN**: проверка идёт через временные изолированные порты Xray, ваше активное соединение в Happ/Hiddify продолжает работать.
* 📱 **Полная поддержка Android (Termux)**: запуск прямо со смартфона в 1 клик через виджет на рабочем столе.
* ⭐️ **Проверка Google Gemini AI**: флаг `--gemini` тестирует прямую доступность нейросети Google.
* 📦 **Zero-Dependency**: работает на стандартной библиотеке Python 3 без `pip install`.
* 🔒 **Безопасность**: ваша ссылка на подписку хранится локально в `config.json` и никогда не утечёт в сеть.

---

## 📱 Установка на Android (Termux)

> Рекомендуется использовать **[Termux из F-Droid](https://f-droid.org/packages/com.termux/)** или GitHub (версия в Google Play не обновляется).

### 1. Установка в одну команду:
Откройте Termux и вставьте команду:

```bash
curl -sSL https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/install.sh | bash
```

Скрипт автоматически установит `python`, `xray`, скачает утилиту и создаст команду `happ-check`.

### 2. Запуск проверки:
```bash
happ-check
```
*(При первом запуске скрипт попросит ввести ссылку на подписку и предложит сохранить её для удобства).*

### 🚀 Запуск в 1 тап с рабочего стола Android (Виджет):
1. Установите дополнение **[Termux:Widget](https://f-droid.org/packages/com.termux.widget/)** с F-Droid;
2. Добавьте виджет Termux на рабочий стол вашего смартфона;
3. Выберите ярлык **`happ-check`**;
4. Теперь проверку можно запускать одним касанием экрана!

---

## 💻 Установка на Windows

1. Убедитесь, что у вас установлен **Python 3.8+** и приложение **Happ** (или Xray).
2. Склонируйте репозиторий или скачайте архив:
   ```cmd
   git clone https://github.com/metallicgunp/happ-google-checker.git
   cd happ-google-checker
   ```
3. Запустите двойным кликом файл **`run_windows.bat`** или выполните в консоли:
   ```cmd
   python check_nodes.py
   ```

---

## 🛠 Параметры командной строки

```text
Использование: python check_nodes.py [ПАРАМЕТРЫ]

Опции:
  -s, --sub URL       Указать ссылку на подписку напрямую (иначе берется из config.json)
  -g, --gemini        Дополнительно проверять доступность Google Gemini AI
  -l, --limit N       Проверить только первые N зарубежных нод (например: -l 20)
  -w, --workers N     Количество параллельных потоков (по умолчанию: 15)
  -a, --all           Проверять абсолютно все ноды, включая российские
  -j, --json          Вывести результат в формате чистого JSON
```

### Примеры:
```bash
# Обычная быстрая проверка
happ-check

# Проверка первых 30 нод с тестом Gemini
happ-check --gemini --limit 30

# Проверка по новой ссылке без изменения сохраненного конфига
happ-check --sub "https://your-domain.com/token"
```

---

## 🔒 Конфиденциальность

Файл `config.json`, в котором сохраняется ссылка на вашу персональную подписку, добавлен в `.gitignore` и **никогда не будет отправлен на GitHub**.

---

## 📄 Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE).
Автор: **[@metallicgunp](https://github.com/metallicgunp)**
