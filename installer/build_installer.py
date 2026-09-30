#!/usr/bin/env python3
"""Сборка установщика RKNHS (Inno Setup).

Шаги:
  1. PyInstaller: python build_pyinstaller.py && cd src && pyinstaller --noconfirm Zapret.local.spec
  2. Установщик:   python installer/build_installer.py

Переменные окружения:
  RKNHS_DEV_REFERENCE  — эталон установки (по умолчанию K:\\rep\\Dev)
  RKNHS_ZAPRET_DATA    — движок zapret2 (по умолчанию ..\\zapret2-youtube-discord)
  INNO_SETUP_COMPILER  — путь к ISCC.exe
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_DIR = Path(__file__).resolve().parent
DEFAULTS_DIR = INSTALLER_DIR / "defaults"
GUI_DIST = ROOT / "src" / "dist" / "RKNHS"
STAGE = ROOT / "dist" / "installer_stage"
ISS_FILE = INSTALLER_DIR / "RKNHS_setup.iss"
OUT_DIR = ROOT / "dist" / "installer"

DEV_REFERENCE = Path(os.environ.get("RKNHS_DEV_REFERENCE", r"K:\rep\Dev"))
ZAPRET_DATA = Path(os.environ.get("RKNHS_ZAPRET_DATA", ROOT.parent / "zapret2-youtube-discord"))

ENGINE_FOLDERS = ("bin", "exe", "lua", "lists", "presets", "windivert.filter")
EXTRA_FOLDERS = ("profile", "json", "themes", "sos", "ico")

DEV_SKIP_NAMES = frozenset(
    {
        "logs",
        "tmp",
        "settings",
        "config",
        "unins000.exe",
        "unins000.dat",
        "RKNHS.exe",
        "_internal",
    }
)


def _read_app_version() -> str:
    build_info = ROOT / "src" / "config" / "build_info.py"
    text = build_info.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("APP_VERSION="):
            return line.split("=", 1)[1].strip().strip("'\"")
    return "0.0.0.0"


def _write_default_settings(target: Path) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from settings.schema import build_default_settings

        data = build_default_settings()
    finally:
        if sys.path[0] == str(ROOT / "src"):
            sys.path.pop(0)

    program = data.setdefault("program", {})
    program["gui_autostart_enabled"] = False
    program["strategy_launch_method"] = "zapret2_mode"
    program["selected_source_preset_file_name_winws2"] = "Default (game filter).txt"
    program["selected_source_preset_file_name_winws1"] = "Default v1.txt"
    program["isp_auto_preset_applied"] = False

    appearance = data.setdefault("appearance", {})
    appearance["ui_language"] = "ru"

    data["vpn_split"] = {
        "enabled": False,
        "config_path": "",
        "refresh_interval_minutes": 30,
        "cli_tunnel_installed": False,
        "rules": [],
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    if src.is_dir():
        _copy_tree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return True


def _resolve_engine_folder(name: str) -> Path | None:
    dev_path = DEV_REFERENCE / name
    if dev_path.exists():
        return dev_path
    zapret_path = ZAPRET_DATA / name
    if zapret_path.exists():
        return zapret_path
    return None


def _resolve_extra_folder(name: str) -> Path | None:
    dev_path = DEV_REFERENCE / name
    if dev_path.exists():
        return dev_path
    local = ROOT / name
    if local.exists():
        return local
    return None


def stage_payload() -> None:
    if not GUI_DIST.joinpath("RKNHS.exe").is_file():
        raise SystemExit(
            "Не найден собранный GUI. Сначала выполните:\n"
            "  python build_pyinstaller.py\n"
            "  cd src && pyinstaller --noconfirm Zapret.local.spec"
        )

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    print(f"Копируем GUI из {GUI_DIST}")
    shutil.copy2(GUI_DIST / "RKNHS.exe", STAGE / "RKNHS.exe")
    _copy_tree(GUI_DIST / "_internal", STAGE / "_internal")

    for folder in ENGINE_FOLDERS:
        source = _resolve_engine_folder(folder)
        if source is None:
            raise SystemExit(f"Не найдена папка движка: {folder} (ни в {DEV_REFERENCE}, ни в {ZAPRET_DATA})")
        print(f"Копируем {folder} из {source}")
        _copy_tree(source, STAGE / folder)

    for folder in EXTRA_FOLDERS:
        source = _resolve_extra_folder(folder)
        if source is None:
            print(f"Пропускаем {folder}: источник не найден")
            continue
        print(f"Копируем {folder} из {source}")
        _copy_tree(source, STAGE / folder)

    if not (STAGE / "ico" / "RKNHS.ico").is_file():
        ico_src = ROOT / "ico" / "RKNHS.ico"
        if ico_src.is_file():
            (STAGE / "ico").mkdir(parents=True, exist_ok=True)
            shutil.copy2(ico_src, STAGE / "ico" / "RKNHS.ico")

    (STAGE / "settings").mkdir(parents=True, exist_ok=True)
    (STAGE / "settings" / "vpn").mkdir(parents=True, exist_ok=True)
    _write_default_settings(STAGE / "settings" / "settings.json")

    config_src = DEFAULTS_DIR / "config.json"
    (STAGE / "config").mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_src, STAGE / "config" / "config.json")

    (STAGE / "logs").mkdir(exist_ok=True)
    (STAGE / "tmp").mkdir(exist_ok=True)

    print(f"Стадия установщика готова: {STAGE}")


def _find_iscc() -> Path | None:
    env = os.environ.get("INNO_SETUP_COMPILER", "").strip()
    if env:
        path = Path(env)
        if path.is_file():
            return path

    candidates = [
        Path(r"C:\InnoSetup6\ISCC.exe"),
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    found = shutil.which("ISCC")
    return Path(found) if found else None


def compile_installer() -> Path | None:
    iscc = _find_iscc()
    if iscc is None:
        print(
            "Inno Setup не найден. Установите Inno Setup 6 и добавьте ISCC.exe в PATH,\n"
            "либо задайте INNO_SETUP_COMPILER=C:\\Path\\To\\ISCC.exe\n"
            f"Затем вручную: \"{ISS_FILE}\""
        )
        return None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    version = _read_app_version()
    version_file = "".join(ch if ch.isalnum() or ch in "._" else "_" for ch in version)
    cmd = [
        str(iscc),
        f"/DAppVersion={version}",
        f"/DAppVersionFile={version_file}",
        str(ISS_FILE),
    ]
    print("Запуск:", " ".join(cmd))
    subprocess.run(cmd, cwd=str(INSTALLER_DIR), check=True)

    setups = sorted(OUT_DIR.glob("RKNHS_Setup_*.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
    if setups:
        print(f"Готово: {setups[0]}")
        return setups[0]
    return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Собрать установщик RKNHS")
    parser.add_argument("--stage-only", action="store_true", help="Только подготовить dist/installer_stage")
    parser.add_argument("--skip-compile", action="store_true", help="Не запускать ISCC")
    args = parser.parse_args()

    stage_payload()
    if args.stage_only:
        return 0
    if args.skip_compile:
        return 0
    compile_installer()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
