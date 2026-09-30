# config/config.py
import os, sys

# ═══════════════════════════════════════════════════════════════════
# ОСНОВНАЯ ПАПКА ПРОГРАММЫ
# ═══════════════════════════════════════════════════════════════════
# В exe-сборке папка программы определяется по exe-файлу.
# В source-режиме это корень репозитория RKNHS (desktop).
if getattr(sys, "frozen", False):
    MAIN_DIRECTORY = os.path.dirname(sys.executable)
else:
    MAIN_DIRECTORY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Канал сборки (для информации)
from config.build_info import CHANNEL

CHANNEL_STABLE = "stable"
CHANNEL_DEV = "dev"
INSTALL_DIR_STABLE = "Stable"
INSTALL_DIR_DEV = "Dev"

def get_system_drive() -> str:
    """Возвращает системный диск Windows, обычно `C:`."""
    return (os.environ.get("SystemDrive") or "C:").strip() or "C:"


def is_dev_build_channel() -> bool:
    """True для dev-канала сборки."""
    return str(CHANNEL or "").strip().lower() == CHANNEL_DEV


def get_install_dir_name() -> str:
    """Возвращает имя папки установки по каналу: `Dev` или `Stable`."""
    return INSTALL_DIR_DEV if is_dev_build_channel() else INSTALL_DIR_STABLE


def get_default_install_dir() -> str:
    """Возвращает базовый путь установки по каналу."""
    return os.path.join(get_system_drive(), "RKNHS", get_install_dir_name())


# Все папки относительно MAIN_DIRECTORY
BIN_FOLDER = os.path.join(MAIN_DIRECTORY, "bin")
INDEXJSON_FOLDER = os.path.join(MAIN_DIRECTORY, "json")
EXE_FOLDER = os.path.join(MAIN_DIRECTORY, "exe")
LUA_FOLDER = os.path.join(MAIN_DIRECTORY, "lua")  # Lua библиотеки для RKNHS
ICO_FOLDER = os.path.join(MAIN_DIRECTORY, "ico")
THEME_FOLDER = os.path.join(MAIN_DIRECTORY, "themes")
LOGS_FOLDER = os.path.join(MAIN_DIRECTORY, "logs")

# Настройка количества сохраняемых лог-файлов
MAX_LOG_FILES = 50           # основные логи приложения
MAX_DEBUG_LOG_FILES = 20     # debug логи winws2

WINDIVERT_FILTER = os.path.join(MAIN_DIRECTORY, "windivert.filter")

# ═══════════════════════════════════════════════════════════════════

ICON_FILE = "RKNHS.ico"
ICON_PATH = os.path.join(ICO_FOLDER, ICON_FILE)
ICON_DEV_PATH = ICON_PATH

# Discord TCP конфигурации

# DiscordFix (ALT v10)
Ankddev10_1 = ""

#$UDP6 = "--filter-udp=50000-65535 --dpi-desync=fake,split2 --dpi-desync-any-protocol --dpi-desync-cutoff=d2 --dpi-desync-fake-quic=quic_test_00.bin --new"

# Отладочная информация (можно убрать в продакшене)
if __name__ == "__main__":
    print(f"MAIN_DIRECTORY: {MAIN_DIRECTORY}")
    print(f"EXE_FOLDER: {EXE_FOLDER}")
    print(f"Существует EXE_FOLDER: {os.path.exists(EXE_FOLDER)}")
