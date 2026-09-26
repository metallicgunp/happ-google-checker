#!/bin/bash
# ==============================================================================
# Happ / VLESS Google GeoIP Checker — Installer for Android (Termux) & Linux
# Author: metallicgunp
# Repository: https://github.com/metallicgunp/happ-google-checker
# ==============================================================================

set -e

# Цвета для терминала
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   Happ / VLESS Google GeoIP Checker Installer        ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Определение среды (Termux на Android vs стандартный Linux)
if [ -d "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
    IS_TERMUX=true
    INSTALL_DIR="$HOME/happ-google-checker"
    BIN_DIR="$PREFIX/bin"
else
    IS_TERMUX=false
    INSTALL_DIR="$HOME/.happ-google-checker"
    BIN_DIR="/usr/local/bin"
fi

echo -e "${YELLOW}[1/4] Установка базовых пакетов (Python, Unzip, Curl)...${NC}"
if [ "$IS_TERMUX" = true ]; then
    pkg update -y
    pkg install python unzip curl git -y
else
    if command -v apt &> /dev/null; then
        sudo apt update -y && sudo apt install python3 unzip curl git -y || true
    fi
fi

# Установка Xray Core бинарника под архитектуру устройства
echo -e "${YELLOW}[2/4] Проверка и загрузка ядра Xray-core...${NC}"
mkdir -p "$INSTALL_DIR"

if ! command -v xray &> /dev/null && [ ! -f "$INSTALL_DIR/xray" ]; then
    ARCH=$(uname -m)
    echo -e "Определена архитектура процессора: ${CYAN}${ARCH}${NC}"
    
    if [ "$IS_TERMUX" = true ]; then
        case "$ARCH" in
            aarch64|arm64)
                XRAY_ZIP_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm64-v8a.zip"
                ;;
            armv7l|arm)
                XRAY_ZIP_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm32-v7a.zip"
                ;;
            x86_64|amd64)
                XRAY_ZIP_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-amd64.zip"
                ;;
            *)
                XRAY_ZIP_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-arm64-v8a.zip"
                ;;
        esac
    else
        case "$ARCH" in
            aarch64|arm64)
                XRAY_ZIP_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-arm64-v8a.zip"
                ;;
            x86_64|amd64)
                XRAY_ZIP_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
                ;;
            *)
                XRAY_ZIP_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
                ;;
        esac
    fi

    echo -e "Загрузка Xray-core с GitHub Releases..."
    TEMP_ZIP="/tmp/xray_temp.zip"
    [ "$IS_TERMUX" = true ] && TEMP_ZIP="$PREFIX/tmp/xray_temp.zip"
    mkdir -p "$(dirname "$TEMP_ZIP")"

    curl -L -s "$XRAY_ZIP_URL" -o "$TEMP_ZIP"
    unzip -q -o "$TEMP_ZIP" xray -d "$INSTALL_DIR/" || unzip -q -o "$TEMP_ZIP" -d "$INSTALL_DIR/"
    rm -f "$TEMP_ZIP"
    chmod +x "$INSTALL_DIR/xray"
    
    # Копируем или линкуем в bin
    if [ -w "$BIN_DIR" ]; then
        cp -f "$INSTALL_DIR/xray" "$BIN_DIR/xray" 2>/dev/null || true
    fi
fi

echo -e "${YELLOW}[3/4] Загрузка скриптов утилиты...${NC}"
curl -sSL "https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/check_nodes.py" -o "$INSTALL_DIR/check_nodes.py"
curl -sSL "https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/config.example.json" -o "$INSTALL_DIR/config.example.json"
chmod +x "$INSTALL_DIR/check_nodes.py"

echo -e "${YELLOW}[4/4] Создание глобальной команды 'happ-check'...${NC}"
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

chmod +x "$WRAPPER_SCRIPT" 2>/dev/null || chmod +x "$INSTALL_DIR/check_nodes.py"

# Настройка ярлыка для Termux:Widget (Android)
if [ "$IS_TERMUX" = true ]; then
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
echo -e "Для запуска проверки введите команду:"
echo -e "  ${CYAN}happ-check${NC}"
echo ""
if [ "$IS_TERMUX" = true ]; then
    echo -e "${YELLOW}Для виджета на главном экране Android:${NC}"
    echo -e "1. Установите приложение ${CYAN}Termux:Widget${NC} (с F-Droid);"
    echo -e "2. Добавьте виджет на рабочий стол телефона и выберите ${CYAN}happ-check${NC}."
fi
echo ""
