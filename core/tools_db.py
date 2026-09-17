import shutil
import os
import re

def sanitize_target(target: str) -> str:
    """Strips dangerous shell metacharacters to prevent command injection and system corruption."""
    if not target:
        return ""
    # Strip dangerous characters: ; & | $ ` \ \n \r < > ( ) { } !
    clean = re.sub(r'[;&|\$`\\\n\r<>\(\)\{\}!]', '', target).strip()
    return clean

def check_binary_or_fallback(binary: str, install_pkg: str = None) -> str:
    """Checks if binary is installed. Returns missing notice if not."""
    if shutil.which(binary):
        return None
    pkg = install_pkg or binary
    return f"[!] Инструмент '{binary}' не найден в PATH.\n[i] Вы можете установить его командой: sudo apt update && sudo apt install {pkg}"

TOOLS_DATABASE = {
    # --- SOCIAL MEDIA TOOLS ---
    "sherlock": {
        "name": "Sherlock",
        "category": "social",
        "subcategory": "Социальные сети",
        "binary": "sherlock",
        "description": "Поиск никнеймов по 400+ социальным сетям.",
        "sudo_recommended": False,
        "input_label": "Никнейм (Username)",
        "default_target": "target_user",
        "options": [
            {"flag": "--timeout", "label": "Таймаут (сек)", "type": "int", "default": 10},
            {"flag": "--print-found", "label": "Показывать только найденные", "type": "bool", "default": True},
            {"flag": "--folderoutput", "label": "Сохранять в папку sherlock_results", "type": "bool", "default": True},
            {"flag": "--site", "label": "Фильтр по сайту (например: twitter,github)", "type": "str", "default": ""}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("sherlock")] if not shutil.which("sherlock") else
            ["sherlock", sanitize_target(target)] +
            (["--timeout", str(opts["--timeout"])] if opts.get("--timeout") else []) +
            (["--print-found"] if opts.get("--print-found") else []) +
            (["--folderoutput", "sherlock_results"] if opts.get("--folderoutput") else []) +
            (["--site", sanitize_target(opts["--site"])] if opts.get("--site") else [])
        )
    },
    "maigret": {
        "name": "Maigret",
        "category": "social",
        "subcategory": "Социальные сети",
        "binary": "maigret",
        "description": "Расширенный аналог Sherlock, мощный поиск с генерацией подробных отчетов.",
        "sudo_recommended": False,
        "input_label": "Никнейм (Username)",
        "default_target": "target_user",
        "options": [
            {"flag": "--pdf", "label": "Экспорт отчета в PDF", "type": "bool", "default": False},
            {"flag": "--html", "label": "Экспорт отчета в HTML", "type": "bool", "default": True},
            {"flag": "--txt", "label": "Экспорт отчета в TXT", "type": "bool", "default": True},
            {"flag": "--timeout", "label": "Таймаут запроса (сек)", "type": "int", "default": 15},
            {"flag": "--site", "label": "Конкретная платформа", "type": "str", "default": ""}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("maigret", "python3-maigret")] if not shutil.which("maigret") else
            ["maigret", sanitize_target(target)] +
            (["--pdf"] if opts.get("--pdf") else []) +
            (["--html"] if opts.get("--html") else []) +
            (["--txt"] if opts.get("--txt") else []) +
            (["--timeout", str(opts["--timeout"])] if opts.get("--timeout") else []) +
            (["--site", sanitize_target(opts["--site"])] if opts.get("--site") else [])
        )
    },
    "social-analyzer": {
        "name": "Social Analyzer",
        "category": "social",
        "subcategory": "Социальные сети",
        "binary": "social-analyzer",
        "description": "Анализ профилей и активности в социальных сетях.",
        "sudo_recommended": False,
        "input_label": "Никнейм (Username)",
        "default_target": "target_user",
        "options": [
            {"flag": "--logs", "label": "Подробные логи", "type": "bool", "default": True},
            {"flag": "--mode", "label": "Режим анализа (fast, slow)", "type": "str", "default": "fast"}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("social-analyzer")] if not shutil.which("social-analyzer") else
            ["social-analyzer", "--username", sanitize_target(target)] +
            (["--mode", sanitize_target(opts.get("--mode", "fast"))] if opts.get("--mode") else [])
        )
    },
    "twint": {
        "name": "Twint",
        "category": "social",
        "subcategory": "Социальные сети",
        "binary": "twint",
        "description": "Парсинг Twitter без API-ключей (сбор твитов, хэштегов, профилей).",
        "sudo_recommended": False,
        "input_label": "Юзернейм или Запрос",
        "default_target": "target_user",
        "options": [
            {"flag": "-u", "label": "Поиск по пользователю", "type": "bool", "default": True},
            {"flag": "--limit", "label": "Лимит твитов", "type": "int", "default": 100},
            {"flag": "--stats", "label": "Показывать статистику", "type": "bool", "default": True}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("twint")] if not shutil.which("twint") else
            ["twint", "-u" if opts.get("-u") else "-s", sanitize_target(target)] +
            (["--limit", str(opts["--limit"])] if opts.get("--limit") else []) +
            (["--stats"] if opts.get("--stats") else [])
        )
    },
    "instalooter": {
        "name": "InstaLooter",
        "category": "social",
        "subcategory": "Социальные сети",
        "binary": "instalooter",
        "description": "Выгрузка фото и постов из Instagram.",
        "sudo_recommended": False,
        "input_label": "Instagram Профиль",
        "default_target": "target_user",
        "options": [
            {"flag": "--num", "label": "Количество постов", "type": "int", "default": 20},
            {"flag": "--quiet", "label": "Тихий режим", "type": "bool", "default": False}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("instalooter")] if not shutil.which("instalooter") else
            ["instalooter", "user", sanitize_target(target), f"./insta_{sanitize_target(target)}"] +
            (["-n", str(opts["--num"])] if opts.get("--num") else [])
        )
    },
    "yt-dlp": {
        "name": "yt-dlp / YouTube-DL",
        "category": "social",
        "subcategory": "Социальные сети",
        "binary": "yt-dlp",
        "description": "Анализ метаданных и скачивание видео с YouTube и 1000+ медиаплатформ.",
        "sudo_recommended": False,
        "input_label": "URL Видео или Канала",
        "default_target": "https://www.youtube.com/watch?v=example",
        "options": [
            {"flag": "--dump-json", "label": "Вывести только JSON-метаданные", "type": "bool", "default": True},
            {"flag": "--no-warnings", "label": "Скрыть предупреждения", "type": "bool", "default": True},
            {"flag": "--flat-playlist", "label": "Только список видео без скачивания", "type": "bool", "default": True}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            (["yt-dlp"] if shutil.which("yt-dlp") else (["youtube-dl"] if shutil.which("youtube-dl") else ["echo", check_binary_or_fallback("yt-dlp")])) +
            [sanitize_target(target)] +
            (["--dump-json"] if opts.get("--dump-json") else []) +
            (["--no-warnings"] if opts.get("--no-warnings") else []) +
            (["--flat-playlist"] if opts.get("--flat-playlist") else [])
        )
    },

    # --- ACCOUNTS / USERNAME / EMAIL ---
    "theHarvester": {
        "name": "theHarvester",
        "category": "accounts",
        "subcategory": "Аккаунты",
        "binary": "theHarvester",
        "description": "Классика для сбора Email, субдоменов, IP, SSL и DNS-записей.",
        "sudo_recommended": False,
        "input_label": "Домен или Имя компании",
        "default_target": "example.com",
        "options": [
            {"flag": "-b", "label": "Источники (all, google, bing, duckduckgo)", "type": "str", "default": "all"},
            {"flag": "-l", "label": "Лимит результатов", "type": "int", "default": 500},
            {"flag": "-v", "label": "Проверка виртуальных хостов", "type": "bool", "default": False},
            {"flag": "-n", "label": "DNS lookup", "type": "bool", "default": True}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("theHarvester")] if not shutil.which("theHarvester") else
            ["theHarvester", "-d", sanitize_target(target), "-b", sanitize_target(opts.get("-b", "all"))] +
            (["-l", str(opts["-l"])] if opts.get("-l") else []) +
            (["-v"] if opts.get("-v") else []) +
            (["-n"] if opts.get("-n") else [])
        )
    },

    # --- OTHER RECON TOOLS & METADATA ---
    "exiftool": {
        "name": "ExifTool",
        "category": "other",
        "subcategory": "Другие",
        "binary": "exiftool",
        "description": "Глубокий анализ метаданных фото, видео и документов (GPS, камера, софт, даты).",
        "sudo_recommended": False,
        "input_label": "Путь к файлу или директории",
        "default_target": "/home/red/projects/OSINT/red_ice.png",
        "options": [
            {"flag": "-all", "label": "Показать ВСЕ теги (-all)", "type": "bool", "default": True},
            {"flag": "-gps:all", "label": "Извлечь GPS координаты", "type": "bool", "default": True},
            {"flag": "-ee", "label": "Извлечь встроенные данные (Extract Embedded)", "type": "bool", "default": False},
            {"flag": "-json", "label": "Формат JSON", "type": "bool", "default": False}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("exiftool")] if not shutil.which("exiftool") else
            ["exiftool"] +
            (["-all"] if opts.get("-all") else []) +
            (["-gps:all"] if opts.get("-gps:all") else []) +
            (["-ee"] if opts.get("-ee") else []) +
            (["-json"] if opts.get("-json") else []) +
            [sanitize_target(target)]
        )
    },
    "spiderfoot": {
        "name": "SpiderFoot",
        "category": "other",
        "subcategory": "Другие",
        "binary": "spiderfoot",
        "description": "Автоматизированный OSINT фреймворк (IP, домены, email, утечки, сертификаты).",
        "sudo_recommended": False,
        "input_label": "Цель (Домен / IP / Email)",
        "default_target": "example.com",
        "options": [
            {"flag": "-s", "label": "CLI Режим сканирования", "type": "bool", "default": True},
            {"flag": "-m", "label": "Модули (sfp_dnsresolve,sfp_whois)", "type": "str", "default": "sfp_dnsresolve,sfp_whois,sfp_spider"},
            {"flag": "-l", "label": "Запустить локальный Web-UI (127.0.0.1:5001)", "type": "bool", "default": False}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("spiderfoot")] if not shutil.which("spiderfoot") else
            (["spiderfoot", "-l", "127.0.0.1:5001"] if opts.get("-l") else
             ["spiderfoot", "-s", sanitize_target(target)] + (["-m", sanitize_target(opts["-m"])] if opts.get("-m") else []))
        )
    },
    "recon-ng": {
        "name": "Recon-ng",
        "category": "other",
        "subcategory": "Другие",
        "binary": "recon-ng",
        "description": "Модульная платформа для разведки в стиле Metasploit.",
        "sudo_recommended": False,
        "input_label": "Имя WorkSpace (Рабочей области)",
        "default_target": "default",
        "options": [
            {"flag": "-w", "label": "Workspace Имя", "type": "str", "default": "osint_scan"}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("recon-ng")] if not shutil.which("recon-ng") else
            ["recon-ng", "-w", sanitize_target(target or opts.get("-w", "default"))]
        )
    },
    "maltego": {
        "name": "Maltego CE",
        "category": "other",
        "subcategory": "Другие",
        "binary": "maltego",
        "description": "Интерактивная визуализация связей и графов данных.",
        "sudo_recommended": False,
        "input_label": "Запуск GUI Maltego",
        "default_target": "",
        "options": [
            {"flag": "--help", "label": "Показать справку CLI", "type": "bool", "default": False}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("maltego")] if not shutil.which("maltego") else
            ["maltego"]
        )
    },
    "foca": {
        "name": "FOCA",
        "category": "other",
        "subcategory": "Другие",
        "binary": "foca",
        "description": "Анализ документов (PDF, DOCX) и поиск скрытых метаданных.",
        "sudo_recommended": False,
        "input_label": "Файл или Директория документов",
        "default_target": "/tmp/docs",
        "options": [
            {"flag": "-extract", "label": "Извлечь метаданные", "type": "bool", "default": True}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["foca", sanitize_target(target)] if shutil.which("foca") else
            (["exiftool", "-ext", "pdf", "-ext", "docx", sanitize_target(target)] if shutil.which("exiftool") else ["echo", check_binary_or_fallback("foca")])
        )
    },

    # --- NMAP & NETWORK SCANNERS ---
    "nmap": {
        "name": "Nmap",
        "category": "network",
        "subcategory": "Сетевое сканирование",
        "binary": "nmap",
        "description": "Основной инструмент для сканирования портов, сервисов, версий и детекции ОС.",
        "sudo_recommended": True,
        "input_label": "Целевой IP / Хост / Подсеть",
        "default_target": "127.0.0.1",
        "options": [
            {"flag": "-sS", "label": "TCP SYN Сканирование (Требует Sudo)", "type": "bool", "default": True},
            {"flag": "-sV", "label": "Определение версий сервисов (-sV)", "type": "bool", "default": True},
            {"flag": "-O", "label": "Определение операционной системы (-O)", "type": "bool", "default": True},
            {"flag": "-A", "label": "Агрессивное сканирование (-A)", "type": "bool", "default": False},
            {"flag": "-p", "label": "Порты (например: 80,443,22 или 1-65535)", "type": "str", "default": "80,443,22,21,25,8080,8443"},
            {"flag": "-T4", "label": "Скорость сканирования (-T4)", "type": "bool", "default": True},
            {"flag": "--script", "label": "NSE Скрипты (vuln, default, safe)", "type": "str", "default": "default"}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("nmap")] if not shutil.which("nmap") else
            ["nmap"] +
            (["-sS"] if opts.get("-sS") and sudo else (["-sT"] if opts.get("-sS") else [])) +
            (["-sV"] if opts.get("-sV") else []) +
            (["-O"] if opts.get("-O") and sudo else []) +
            (["-A"] if opts.get("-A") else []) +
            (["-T4"] if opts.get("-T4") else []) +
            (["-p", sanitize_target(opts["-p"])] if opts.get("-p") else []) +
            (["--script", sanitize_target(opts["--script"])] if opts.get("--script") else []) +
            [sanitize_target(target)]
        )
    },
    "masscan": {
        "name": "Masscan",
        "category": "network",
        "subcategory": "Сетевое сканирование",
        "binary": "masscan",
        "description": "Ультра-быстрый сканер портов для больших сетей (требует Sudo).",
        "sudo_recommended": True,
        "input_label": "Целевая сеть / IP",
        "default_target": "192.168.1.0/24",
        "options": [
            {"flag": "-p", "label": "Порты (1-65535, 80,443)", "type": "str", "default": "80,443,22,8080"},
            {"flag": "--rate", "label": "Скорость (пакетов/сек)", "type": "int", "default": 1000}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("masscan")] if not shutil.which("masscan") else
            ["masscan", sanitize_target(target), "-p", sanitize_target(opts.get("-p", "80,443"))] +
            (["--rate", str(opts["--rate"])] if opts.get("--rate") else [])
        )
    },
    "zmap": {
        "name": "Zmap",
        "category": "network",
        "subcategory": "Сетевое сканирование",
        "binary": "zmap",
        "description": "Сканер для интернет-масштабных исследований (один порт по IPv4).",
        "sudo_recommended": True,
        "input_label": "Целевая подсеть или IP",
        "default_target": "192.168.1.0/24",
        "options": [
            {"flag": "-p", "label": "Порт", "type": "int", "default": 80},
            {"flag": "-B", "label": "Пропускная способность (1M, 10M)", "type": "str", "default": "1M"}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("zmap")] if not shutil.which("zmap") else
            ["zmap", "-p", str(opts.get("-p", 80)), "-B", sanitize_target(opts.get("-B", "1M")), sanitize_target(target)]
        )
    },
    "amass": {
        "name": "Amass",
        "category": "network",
        "subcategory": "Сетевое сканирование",
        "binary": "amass",
        "description": "Разведка субдоменов, DNS-картирование и визуализация связей.",
        "sudo_recommended": False,
        "input_label": "Домен (Domain)",
        "default_target": "example.com",
        "options": [
            {"flag": "-passive", "label": "Пассивный режим (пассивный DNS)", "type": "bool", "default": True},
            {"flag": "-active", "label": "Активный режим (DNS проверки)", "type": "bool", "default": False}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("amass")] if not shutil.which("amass") else
            ["amass", "enum", "-d", sanitize_target(target)] +
            (["-passive"] if opts.get("-passive") else []) +
            (["-active"] if opts.get("-active") else [])
        )
    },
    "shodan": {
        "name": "Shodan CLI",
        "category": "network",
        "subcategory": "Сетевое сканирование",
        "binary": "shodan",
        "description": "Поиск подключенных устройств, баннеров и открытых портов в сети Shodan.",
        "sudo_recommended": False,
        "input_label": "IP адрес или Поисковый запрос",
        "default_target": "8.8.8.8",
        "options": [
            {"flag": "host", "label": "Запрос информации о хосте (host)", "type": "bool", "default": True},
            {"flag": "search", "label": "Поисковый запрос (search)", "type": "bool", "default": False},
            {"flag": "myip", "label": "Показать мой публичный IP", "type": "bool", "default": False}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("shodan")] if not shutil.which("shodan") else
            (["shodan", "myip"] if opts.get("myip") else
             (["shodan", "search", sanitize_target(target)] if opts.get("search") else
              ["shodan", "host", sanitize_target(target)]))
        )
    },
    "whatweb": {
        "name": "WhatWeb",
        "category": "network",
        "subcategory": "Сетевое сканирование",
        "binary": "whatweb",
        "description": "Определение технологий веб-сайта (CMS, веб-сервер, языки, плагины).",
        "sudo_recommended": False,
        "input_label": "URL или Домен веб-сайта",
        "default_target": "https://example.com",
        "options": [
            {"flag": "-a", "label": "Уровень агрессивности (1-Stealth, 3-Aggressive)", "type": "int", "default": 3},
            {"flag": "--log-brief", "label": "Краткий лог", "type": "bool", "default": True}
        ],
        "cmd_builder": lambda target, opts, sudo: (
            ["echo", check_binary_or_fallback("whatweb")] if not shutil.which("whatweb") else
            ["whatweb", sanitize_target(target), "-a", str(opts.get("-a", 3)), "--color=never"]
        )
    }
}

def is_tool_installed(binary_name: str) -> bool:
    """Checks if a tool binary exists in PATH."""
    return shutil.which(binary_name) is not None

def get_tool_path(binary_name: str) -> str:
    """Gets absolute path to binary."""
    path = shutil.which(binary_name)
    return path if path else f"[Не найдено в PATH: {binary_name}]"
