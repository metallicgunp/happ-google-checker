#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
 Happ / VLESS Google GeoIP & Gemini Checker
 Standalone tool for testing VPN / VLESS subscription nodes against Google GeoIP
 and AI availability without breaking active VPN connections.
 
 Author: metallicgunp
 License: MIT
 Repository: https://github.com/metallicgunp/happ-google-checker
==============================================================================
"""

import argparse
import http.cookiejar
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Включение UTF-8 и ANSI цветов в терминале Windows 10/11
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        os.system("")
    except Exception:
        pass

# ANSI Цвета
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
GRAY = "\033[90m"
BRIGHT = "\033[1m"
RESET = "\033[0m"

CONFIG_FILE = "config.json"
DEFAULT_WORKERS = 15
PORT_START = 26000

def find_xray_binary():
    """Автоматический поиск бинарного файла xray для Linux/Termux/Windows."""
    # 1. Проверка в системном PATH (стандарт для Termux / Linux)
    in_path = shutil.which("xray")
    if in_path:
        return in_path
        
    # 2. Проверка в локальной папке проекта и домашних каталогах (Termux / Linux)
    local_linux_candidates = [
        "./xray",
        os.path.expanduser("~/happ-google-checker/xray"),
        os.path.expanduser("~/.happ-google-checker/xray"),
        os.path.expandvars("$PREFIX/bin/xray"),
        "/data/data/com.termux/files/usr/bin/xray",
        "/usr/local/bin/xray",
        "/usr/bin/xray"
    ]
    for p in local_linux_candidates:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    
    if sys.platform == "win32":
        # 3. Стандартные пути установки Happ / v2ray в Windows
        candidates = [
            r"C:\Program Files\FlyFrogLLC\Happ\core\xray.exe",
            r"C:\Program Files (x86)\FlyFrogLLC\Happ\core\xray.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Happ\core\xray.exe"),
            os.path.expandvars(r"%APPDATA%\Happ\core\xray.exe"),
            r"C:\Program Files\v2ray\xray.exe",
            r"C:\Program Files\Xray\xray.exe"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
                
    return None

def load_or_prompt_sub_url(cli_url=None):
    """Загрузка ссылки подписки из аргументов, config.json или интерактивного ввода."""
    if cli_url:
        return cli_url
        
    # Проверяем локальный config.json
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("subscription_url")
                if url:
                    return url
        except Exception:
            pass

    # Интерактивный запрос, если нет конфига
    print(f"{YELLOW}Ссылка на подписку не найдена в {CONFIG_FILE}.{RESET}")
    try:
        url = input(f"{BRIGHT}Введите ссылку на вашу подписку (Happ / VLESS): {RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{RED}Отменено пользователем.{RESET}")
        sys.exit(1)
        
    if not url.startswith("http"):
        print(f"{RED}Ошибка: некорректная ссылка!{RESET}")
        sys.exit(1)
        
    # Предлагаем сохранить
    try:
        save = input(f"Сохранить эту ссылку в {CONFIG_FILE} для будущих запусков? (y/n, по умолчанию y): ").strip().lower()
        if save in ("", "y", "yes", "д", "да"):
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"subscription_url": url}, f, indent=2)
            print(f"{GREEN}Ссылка сохранена в {CONFIG_FILE}{RESET}\n")
    except Exception:
        pass
        
    return url

def test_node(idx, profile, xray_path, available_ports, port_lock, check_gemini=False):
    """Тестирование одной ноды через изолированный временный процесс Xray."""
    remark = profile.get("remarks", f"Profile #{idx+1}")
    outbounds = profile.get("outbounds", [])
    proxy_ob = None
    for ob in outbounds:
        if ob.get("protocol") not in ("freedom", "blackhole", "dns", "direct", "block"):
            proxy_ob = ob
            break
            
    res = {
        "idx": idx + 1,
        "remark": remark,
        "proto": proxy_ob.get("protocol") if proxy_ob else "unknown",
        "ip": None,
        "isp_country": None,
        "google_loc": None,
        "google_source": None,
        "gemini_ok": None,
        "google_status": None,
        "is_russia": False
    }

    if not proxy_ob or proxy_ob.get("protocol") != "vless":
        res["google_status"] = "skipped"
        return res

    with port_lock:
        port = available_ports.pop()

    cfg_file = f"temp_chk_{idx}_{port}.json"
    temp_cfg = {
        "log": {"loglevel": "none"},
        "inbounds": [{
            "tag": "http-in",
            "port": port,
            "listen": "127.0.0.1",
            "protocol": "http",
            "settings": {"allowTransparent": False}
        }],
        "outbounds": [
            proxy_ob,
            {"tag": "direct", "protocol": "freedom"}
        ]
    }
    
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(temp_cfg, f)
        
    proc = subprocess.Popen([xray_path, "run", "-c", cfg_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.6)
    
    try:
        cj = http.cookiejar.CookieJar()
        proxy_handler = urllib.request.ProxyHandler({"http": f"http://127.0.0.1:{port}", "https": f"http://127.0.0.1:{port}"})
        opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPCookieProcessor(cj))
        
        # 1. Реальный IP и страна дата-центра
        try:
            with opener.open("http://ip-api.com/json?fields=query,country,city", timeout=3.0) as ip_resp:
                ip_data = json.loads(ip_resp.read().decode())
                res["ip"] = ip_data.get("query")
                res["isp_country"] = f"{ip_data.get('country')} ({ip_data.get('city')})"
        except Exception:
            pass

        # 2. Проверка Google Search GeoIP
        try:
            g_req = urllib.request.Request(
                "https://www.google.com/?hl=en",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
            with opener.open(g_req, timeout=3.5) as g_resp:
                html = g_resp.read().decode("utf-8", errors="ignore")
                res["google_status"] = "200 OK"
                
                # Поиск футера геолокации Google
                loc_matches = re.findall(r'<div[^>]*class="[^"]*(?:O3yKUb|uU7dJb)[^"]*"[^>]*>([^<]+)</div>', html)
                if loc_matches:
                    res["google_loc"] = loc_matches[0].strip()
                else:
                    res["google_loc"] = "Unknown"

                # Код страны в utm_source
                src_match = re.findall(r"utm_source=google-([A-Za-z]{2,5})", html)
                if src_match:
                    res["google_source"] = src_match[0].upper()

                gloc = str(res["google_loc"]).lower()
                gsrc = str(res["google_source"]).lower()
                if "russia" in gloc or "россия" in gloc or gsrc == "ru":
                    res["is_russia"] = True

        except urllib.error.HTTPError as e:
            if e.code == 429:
                res["google_status"] = "429 Captcha"
                res["google_loc"] = "BLOCKED (429)"
            else:
                res["google_status"] = f"HTTP {e.code}"
                res["google_loc"] = f"HTTP {e.code}"
        except Exception:
            res["google_status"] = "Timeout"
            res["google_loc"] = "Timeout"

        # 3. Опциональная проверка доступности Google Gemini AI
        if check_gemini and res["google_status"] == "200 OK" and not res["is_russia"]:
            try:
                gem_req = urllib.request.Request(
                    "https://gemini.google.com/",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with opener.open(gem_req, timeout=3.0) as gem_resp:
                    res["gemini_ok"] = (gem_resp.status == 200)
            except Exception:
                res["gemini_ok"] = False

    finally:
        proc.terminate()
        proc.wait()
        with port_lock:
            available_ports.append(port)
        if os.path.exists(cfg_file):
            try:
                os.remove(cfg_file)
            except Exception:
                pass
            
    return res

def main():
    parser = argparse.ArgumentParser(
        description="Happ / VLESS Google GeoIP & Gemini Checker — Сканер нод подписки на чистоту IP в Google",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Примеры использования:\n"
               "  python check_nodes.py\n"
               "  python check_nodes.py --sub \"https://auth.provider.com/sub_token\"\n"
               "  python check_nodes.py --gemini --limit 30\n"
               "  python check_nodes.py --json > clean_nodes.json"
    )
    parser.add_argument("--sub", "-s", help="URL ссылка на подписку (если не задана, берется из config.json)")
    parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS, help=f"Количество потоков проверки (по умолчанию {DEFAULT_WORKERS})")
    parser.add_argument("--limit", "-l", type=int, default=0, help="Ограничить количество проверяемых нод (0 = проверить все)")
    parser.add_argument("--all", "-a", action="store_true", help="Проверять абсолютно все ноды, включая российские")
    parser.add_argument("--gemini", "-g", action="store_true", help="Дополнительно проверять прямую доступность Google Gemini AI")
    parser.add_argument("--json", "-j", action="store_true", help="Вывести чистый результат в формате JSON")
    args = parser.parse_args()

    # 1. Поиск бинарника Xray
    xray_path = find_xray_binary()
    if not xray_path:
        if not args.json:
            print(f"{RED}Ошибка: Не найден исполняемый файл xray!{RESET}")
            if sys.platform == "win32":
                print("Убедитесь, что установлено приложение Happ или Xray добавлен в PATH.")
            else:
                print("В Termux/Linux установите его командой: pkg install xray (или apt install xray)")
        sys.exit(1)

    # 2. Получение ссылки
    sub_url = load_or_prompt_sub_url(args.sub)

    if not args.json:
        print(f"\n{BRIGHT}{CYAN}==========================================================================================")
        print(f"{BRIGHT}{CYAN}         HAPP / VLESS: СКАНИРОВАНИЕ ГЕОЛОКАЦИИ GOOGLE (GEOIP & AI CHECKER)")
        print(f"{BRIGHT}{CYAN}=========================================================================================={RESET}")
        print(f"{GRAY}Ядро Xray:{RESET} {xray_path}")
        print(f"{GRAY}Подписка:{RESET} {sub_url[:50]}...\n", flush=True)

    # 3. Скачивание подписки
    headers = {"User-Agent": "Happ/3.0.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(sub_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_data = resp.read().decode("utf-8", errors="ignore")
            parsed = json.loads(raw_data)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"{RED}Ошибка скачивания подписки: {e}{RESET}")
        sys.exit(1)

    if not isinstance(parsed, list):
        print(f"{RED}Ошибка: Неверный формат подписки (ожидался список профилей).{RESET}")
        sys.exit(1)

    # 4. Отбор нод для проверки
    targets = []
    for i, p in enumerate(parsed):
        remark = p.get("remarks", "")
        if args.all or not any(ru in remark for ru in ["Россия", "Москва", "Хабаровск", "Питер", "Екатеринбург"]):
            targets.append((i, p))

    if args.limit > 0:
        targets = targets[:args.limit]

    total = len(targets)
    if not args.json:
        print(f"Всего профилей: {len(parsed)} | Отобрано для проверки: {total}")
        print(f"Запуск тестирования в {args.workers} параллельных потоков (Happ не прерывается)...\n", flush=True)

    port_lock = threading.Lock()
    available_ports = list(range(PORT_START + 1, PORT_START + args.workers + 10))

    # 5. Многопоточное сканирование
    results = []
    done_count = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(test_node, i, p, xray_path, available_ports, port_lock, args.gemini): (i, p) for (i, p) in targets}
        for f in as_completed(futures):
            done_count += 1
            if not args.json:
                percent = int((done_count / total) * 100)
                sys.stdout.write(f"\rПрогресс проверки: [{done_count}/{total}] ({percent}%) ")
                sys.stdout.flush()
            try:
                r = f.result()
                if r.get("google_status") != "skipped":
                    results.append(r)
            except Exception:
                pass

    results.sort(key=lambda x: x.get("idx", 0))

    clean_nodes = [r for r in results if r.get("google_status") == "200 OK" and not r.get("is_russia")]
    russia_nodes = [r for r in results if r.get("is_russia")]
    blocked_nodes = [r for r in results if "429" in str(r.get("google_status"))]

    # 6. Вывод результатов
    if args.json:
        output_data = {
            "subscription_url": sub_url,
            "total_tested": total,
            "clean_nodes_count": len(clean_nodes),
            "clean_nodes": clean_nodes,
            "russia_nodes": russia_nodes,
            "blocked_nodes": blocked_nodes
        }
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
        return

    print("\n")
    print(f"{BRIGHT}{GREEN}==========================================================================================")
    print(f"{BRIGHT}{GREEN}  ЧИСТЫЕ СЕРВЕРЫ (GOOGLE ОПРЕДЕЛЯЕТ НЕ КАК РОССИЮ) — НАЙДЕНО: {len(clean_nodes)}")
    print(f"{BRIGHT}{GREEN}==========================================================================================")
    
    gemini_header = " | Gemini" if args.gemini else ""
    print(f"{'№':<6} {'Название в Happ':<38} | {'Реальный IP / Дата-центр':<26} | {'Google Location'}{gemini_header}")
    print("-" * 94)
    for c in clean_nodes:
        g_tag = f"{c['google_loc']}" + (f" ({c['google_source']})" if c.get("google_source") else "")
        gem_str = ""
        if args.gemini:
            gem_str = f" | {GREEN}Доступен{RESET}" if c.get("gemini_ok") else f" | {RED}Нет{RESET}"
        print(f"[{c['idx']:03d}] {c['remark']:<38} | {c.get('isp_country') or 'N/A':<26} | {BRIGHT}{GREEN}{g_tag}{RESET}{gem_str}")

    print(f"\n{YELLOW}Сводная статистика:")
    print(f"  • ✅ Чистые зарубежные серверы: {len(clean_nodes)}")
    print(f"  • ❌ Серверы с «загрязненным» IP (Google видит Россию): {len(russia_nodes)}")
    print(f"  • ⚠️ Серверы с капчей/ограничением Google (429): {len(blocked_nodes)}")
    print(f"{CYAN}=========================================================================================={RESET}")

if __name__ == "__main__":
    main()
