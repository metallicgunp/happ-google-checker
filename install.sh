#!/bin/bash
# ==============================================================================
# Happ / VLESS Google GeoIP Checker — Installer for Android (Termux) & Linux
# Author: metallicgunp
# Repository: https://github.com/metallicgunp/happ-google-checker
# ==============================================================================

set -e

# Цвета для красивого вывода
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   Happ / VLESS Google GeoIP Checker Installer        ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Проверка окружения (Termux на Android vs стандартный Linux)
if [ -d "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
    IS_TERMUX=true
    INSTALL_DIR="$HOME/happ-google-checker"
    BIN_DIR="$PREFIX/bin"
else
    IS_TERMUX=false
    INSTALL_DIR="$HOME/.happ-google-checker"
    BIN_DIR="/usr/local/bin"
fi

echo -e "${YELLOW}[1/4] Проверка и установка зависимостей (Python, Xray)...${NC}"
if [ "$IS_TERMUX" = true ]; then
    pkg update -y
    pkg install python xray git -y
else
    if command -v apt &> /dev/null; then
        sudo apt update -y && sudo apt install python3 xray git -y || true
    fi
fi

# Проверка наличия xray
if ! command -v xray &> /dev/null; then
    echo -e "${RED}Ошибка: xray не установлен автоматически.${NC}"
    echo -e "Пожалуйста, установите xray вручную: pkg install xray"
    exit 1
fi

echo -e "${YELLOW}[2/4] Загрузка файлов утилиты в ${INSTALL_DIR}...${NC}"
mkdir -p "$INSTALL_DIR"

# Если запуск происходит из локального репозитория
if [ -f "check_nodes.py" ]; then
    cp -f check_nodes.py "$INSTALL_DIR/"
    [ -f "config.example.json" ] && cp -f config.example.json "$INSTALL_DIR/"
else
    # Скачивание напрямую с GitHub
    curl -sSL "https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/check_nodes.py" -o "$INSTALL_DIR/check_nodes.py"
    curl -sSL "https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/config.example.json" -o "$INSTALL_DIR/config.example.json"
fi

chmod +x "$INSTALL_DIR/check_nodes.py"

echo -e "${YELLOW}[3/4] Создание глобальной команды 'happ-check'...${NC}"
WRAPPER_SCRIPT="${BIN_DIR}/happ-check"

cat << 'EOF' > "$WRAPPER_SCRIPT"
#!/bin/bash
DIR="$HOME/happ-google-checker"
if [ ! -d "$DIR" ]; then
    DIR="$HOME/.happ-google-checker"
fi
cd "$DIR"
python3 check_nodes.py "$@"
EOF

chmod +x "$WRAPPER_SCRIPT"

# Настройка ярлыка для Termux:Widget (Android)
if [ "$IS_TERMUX" = true ]; then
    echo -e "${YELLOW}[4/4] Создание виджета для рабочего стола Android...${NC}"
    SHORTCUT_DIR="$HOME/.shortcuts"
    mkdir -p "$SHORTCUT_DIR"
    
    cat << 'EOF' > "$SHORTCUT_DIR/happ-check"
#!/bin/bash
cd "$HOME/happ-google-checker"
python3 check_nodes.py
echo ""
echo "Нажмите Enter для выхода..."
read
EOF
    chmod +x "$SHORTCUT_DIR/happ-check"
fi

echo ""
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}   Установка успешно завершена!                      ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "Для запуска проверки введите в любом месте терминала:"
echo -e "  ${CYAN}happ-check${NC}"
echo ""
if [ "$IS_TERMUX" = true ]; then
    echo -e "${YELLOW}Для запуска с рабочего стола Android:${NC}"
    echo -e "1. Установите приложение ${CYAN}Termux:Widget${NC} (с F-Droid);"
    echo -e "2. Добавьте виджет на рабочий стол вашего телефона;"
    echo -e "3. Выберите скрипт ${CYAN}happ-check${NC} — и запускайте проверку в 1 тап!"
fi
echo ""
