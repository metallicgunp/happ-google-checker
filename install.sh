#!/bin/bash
# ==============================================================================
# Happ / VLESS Google GeoIP Checker — Installer for Android (Termux) & Linux
# Author: metallicgunp
# Repository: https://github.com/metallicgunp/happ-google-checker
# ==============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   Happ / VLESS Google GeoIP Checker Installer        ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Проверка окружения
if [ -d "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
    IS_TERMUX=true
    INSTALL_DIR="$HOME/happ-google-checker"
    BIN_DIR="$PREFIX/bin"
else
    IS_TERMUX=false
    INSTALL_DIR="$HOME/.happ-google-checker"
    BIN_DIR="/usr/local/bin"
fi

echo -e "${YELLOW}[1/3] Проверка Python 3...${NC}"
if [ "$IS_TERMUX" = true ]; then
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        pkg install python -y
    fi
fi

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

mkdir -p "$INSTALL_DIR"

echo -e "${YELLOW}[2/3] Загрузка Xray-core и скриптов (через Python)...${NC}"
$PYTHON_CMD - << 'EOF'
import urllib.request
import zipfile
import io
import os
import sys
import platform

install_dir = os.path.expanduser("~/happ-google-checker")
if not os.path.exists(install_dir):
    os.makedirs(install_dir, exist_ok=True)

# 1. Определение архитектуры
machine = platform.machine().lower()
print(f"  Процессор: {machine}")

# Ссылки на релизы Xray
if "aarch64" in machine or "arm64" in machine:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm64-v8a.zip"
elif "arm" in machine:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm32-v7a.zip"
elif "x86_64" in machine or "amd64" in machine:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
else:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm64-v8a.zip"

xray_bin = os.path.join(install_dir, "xray")

if not os.path.exists(xray_bin):
    print(f"  Скачивание Xray-core...")
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(xray_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            zip_bytes = resp.read()
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for member in z.namelist():
                if member in ("xray", "xray.exe"):
                    with open(xray_bin, "wb") as f:
                        f.write(z.read(member))
                    break
        os.chmod(xray_bin, 0o755)
        print("  Xray-core успешно установлен!")
    except Exception as e:
        print(f"  Предупреждение при загрузке Xray: {e}")

# 2. Скачивание check_nodes.py
print("  Скачивание check_nodes.py...")
script_url = "https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/check_nodes.py"
req_script = urllib.request.Request(script_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_script, timeout=15) as resp:
    script_code = resp.read().decode('utf-8')

check_nodes_path = os.path.join(install_dir, "check_nodes.py")
with open(check_nodes_path, "w", encoding="utf-8") as f:
    f.write(script_code)
os.chmod(check_nodes_path, 0o755)

# 3. Скачивание config.example.json
cfg_url = "https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/config.example.json"
try:
    req_cfg = urllib.request.Request(cfg_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req_cfg, timeout=10) as resp:
        cfg_code = resp.read().decode('utf-8')
    with open(os.path.join(install_dir, "config.example.json"), "w", encoding="utf-8") as f:
        f.write(cfg_code)
except Exception:
    pass

print("  Все файлы успешно распакованы.")
EOF

echo -e "${YELLOW}[3/3] Настройка команд и виджета...${NC}"
WRAPPER_SCRIPT="${BIN_DIR}/happ-check"

cat << 'EOF' > "$WRAPPER_SCRIPT"
#!/bin/bash
DIR="$HOME/happ-google-checker"
cd "$DIR"
python3 check_nodes.py "$@"
EOF

chmod +x "$WRAPPER_SCRIPT" 2>/dev/null || true

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
    echo -e "${YELLOW}Для запуска в 1 тап с рабочего стола Android:${NC}"
    echo -e "1. Установите приложение ${CYAN}Termux:Widget${NC} (с F-Droid);"
    echo -e "2. Добавьте виджет Termux на рабочий стол и выберите ${CYAN}happ-check${NC}."
fi
echo ""
