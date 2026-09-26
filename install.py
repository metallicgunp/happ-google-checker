#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Happ / VLESS Google GeoIP Checker — Pure Python Installer
"""

import os
import sys
import platform
import urllib.request
import zipfile
import io

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

print(f"\n{CYAN}======================================================{RESET}")
print(f"{CYAN}   Happ / VLESS Google GeoIP Checker Installer        {RESET}")
print(f"{CYAN}======================================================{RESET}")

install_dir = os.path.expanduser("~/happ-google-checker")
os.makedirs(install_dir, exist_ok=True)

# Определение префикса Termux
prefix = os.environ.get("PREFIX", "")
is_termux = bool(prefix and "com.termux" in prefix)
bin_dir = os.path.join(prefix, "bin") if is_termux else "/usr/local/bin"

# 1. Скачивание Xray
machine = platform.machine().lower()
print(f"{YELLOW}[1/3] Загрузка ядра Xray для архитектуры ({machine})...{RESET}")

if "aarch64" in machine or "arm64" in machine:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm64-v8a.zip"
elif "arm" in machine:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm32-v7a.zip"
elif "x86_64" in machine or "amd64" in machine:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
else:
    xray_url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm64-v8a.zip"

xray_bin = os.path.join(install_dir, "xray")
headers = {"User-Agent": "Mozilla/5.0"}

try:
    req = urllib.request.Request(xray_url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        zip_bytes = resp.read()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for member in z.namelist():
            if member in ("xray", "xray.exe"):
                with open(xray_bin, "wb") as f:
                    f.write(z.read(member))
                break
    os.chmod(xray_bin, 0o755)
    print(f"  {GREEN}Xray-core успешно установлен в {xray_bin}{RESET}")
except Exception as e:
    print(f"  Ошибка загрузки Xray: {e}")

# 2. Скачивание check_nodes.py
print(f"{YELLOW}[2/3] Загрузка скрипта check_nodes.py...{RESET}")
script_url = "https://raw.githubusercontent.com/metallicgunp/happ-google-checker/main/check_nodes.py"
req_script = urllib.request.Request(script_url, headers=headers)
with urllib.request.urlopen(req_script, timeout=15) as resp:
    script_code = resp.read().decode('utf-8')

check_nodes_path = os.path.join(install_dir, "check_nodes.py")
with open(check_nodes_path, "w", encoding="utf-8") as f:
    f.write(script_code)
os.chmod(check_nodes_path, 0o755)

# 3. Настройка глобальной команды happ-check
print(f"{YELLOW}[3/3] Настройка команды happ-check...{RESET}")
wrapper_path = os.path.join(bin_dir, "happ-check")
wrapper_content = f"""#!/bin/bash
cd "{install_dir}"
python3 check_nodes.py "$@"
"""

try:
    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(wrapper_content)
    os.chmod(wrapper_path, 0o755)
except Exception:
    pass

# Настройка Termux:Widget
if is_termux:
    shortcut_dir = os.path.expanduser("~/.shortcuts")
    os.makedirs(shortcut_dir, exist_ok=True)
    shortcut_path = os.path.join(shortcut_dir, "happ-check")
    shortcut_content = f"""#!/bin/bash
cd "{install_dir}"
python3 check_nodes.py
echo ""
echo "Нажмите Enter для выхода..."
read
"""
    try:
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write(shortcut_content)
        os.chmod(shortcut_path, 0o755)
    except Exception:
        pass

print(f"\n{GREEN}======================================================{RESET}")
print(f"{GREEN}   Установка успешно завершена!                      {RESET}")
print(f"{GREEN}======================================================{RESET}")
print(f"Для запуска введите: {CYAN}happ-check{RESET}\n")
