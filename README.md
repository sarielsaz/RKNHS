# RKNHS

**Windows-приложение для обхода DPI-блокировок и split-туннелирования трафика.**

Собственная модификация на базе экосистемы Zapret / winws2. Сделана для личного использования и как портфолио-проект: современный Fluent UI, VPN Split с AmneziaWG, Telegram Proxy, установщик и аккуратный DX.

> **© All rights reserved.**  
> Код публикуется для ознакомления (портфолио).  
> Копирование, распространение и **коммерческое использование / продажа запрещены** без письменного разрешения автора.

---

## Зачем это

РКН и провайдеры режут сервисы через DPI. RKNHS собирает в одном окне:

- запуск DPI-движка (**winws2**) с пресетами;
- **VPN Split** — только нужные домены/подсети через AmneziaWG, остальное мимо туннеля;
- **Telegram Proxy** (SOCKS5 / MTProxy / WSS), когда прямой доступ к DC недоступен;
- hosts, диагностика, автозапуск, трей.

Цель UI: операторский «консоль»-workbench — быстро увидеть статус и одно главное действие, без маркетингового шума.

---

## Возможности

| Модуль | Что делает |
| --- | --- |
| **DPI / Zapret2** | Пресеты winws2, сценарии (YouTube / Discord / широкий охват), карта трафика |
| **VPN Split** | Домены и wildcards (`*.cursor.sh`), резолв IP → `AllowedIPs`, DPI-исключения, CLI-служба туннеля |
| **Telegram** | Локальный прокси + авто-hosts на WSS relay; при жёстком блоке IP — маршрут через VPN |
| **Трей** | Старт/стоп и переключение профилей без открытия окна |
| **Установщик** | Inno Setup: обновление поверх старой версии, `settings.json` не затирается |
| **Лицензирование** | Опциональный gate на машину (модификация для дистрибуции) |
| **UI** | PyQt6 + QFluentWidgets, ultra-tech dark тема (`DESIGN.md`) |

---

## Стек

- **Python 3.13**, **PyQt6**, **PyQt6-Fluent-Widgets**
- DPI: **winws2** / WinDivert
- VPN: **AmneziaWG** (WireGuard + obfuscation)
- Сборка: **PyInstaller** (onedir) + **Inno Setup 6**
- Тесты: `unittest`

---

## Структура репозитория

```text
src/                 # приложение (точка входа main.py)
  vpn_split/         # split-туннель AmneziaWG
  telegram_proxy/    # локальный TG-прокси
  presets/           # UI и сценарии DPI
  ui/                # оболочка, тема, навигация
installer/           # Inno Setup + stage-скрипт
tests/               # регрессии
DESIGN.md            # визуальный контракт UI
```

---

## Сборка (Windows)

```bat
python build_pyinstaller.py
cd src
python -m PyInstaller --noconfirm Zapret.local.spec
cd ..
python installer\build_installer.py
```

Готовый setup: `dist\installer\RKNHS_Setup_*.exe`  
Локальный GUI после PyInstaller: `src\dist\RKNHS\RKNHS.exe`

Переменные (опционально):

- `RKNHS_DEV_REFERENCE` — эталон данных (по умолчанию `K:\rep\Dev`)
- `INNO_SETUP_COMPILER` — путь к `ISCC.exe`

---

## VPN Split (кратко)

1. Экспорт `.conf` из AmneziaWG → лучше хранить как `base.conf` (не `active.conf`).
2. В `AllowedIPs` — статика (например подсети Telegram).
3. Домены (Cursor и т.д.) — во вкладке VPN Split / импорт `cursor.txt`.
4. **Применить** пересобирает `active.conf` + `ipset-vpn` (исключения DPI).

Подробности — в UI-гайде на странице VPN Split.

---

## Правовой статус / происхождение

Проект **основан** на идеях и наработках открытой экосистемы Zapret / связанных GUI, но это **отдельная модификация** (брендинг RKNHS, VPN Split, установщик, UI, лицензирование).

Публикация на GitHub — для демонстрации навыков (UI, Windows networking, packaging).  
**Не open-source лицензия:** без явного разрешения автора использование ограничено просмотром.

Автор форка: **Sazzero** (`sarielsaz`).

---

## Контакты

GitHub: [github.com/sarielsaz/RKNHS](https://github.com/sarielsaz/RKNHS)
