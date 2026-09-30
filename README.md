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

## Версия и история изменений

- Текущая версия: файл [`src/config/build_info.py`](src/config/build_info.py) (`APP_VERSION`, `CHANNEL`)
- Журнал релизов с **21.1.0.19**: [`CHANGELOG.md`](CHANGELOG.md)
- На GitHub Releases — установщики и краткие release notes к каждому тегу

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

## Что нужно для работы

| Функция | Что нужно |
| --- | --- |
| Обход блокировок (DPI) | Достаточно установить **RKNHS** и нажать «Запуск» |
| **VPN Split** | Обязательно отдельно установить программу **[AmneziaWG](https://github.com/amnezia-vpn/amneziawg-windows-client/releases)** и иметь свой VPN-конфиг (`.conf`) |

Без AmneziaWG вкладка VPN Split **не поднимет туннель**: RKNHS только управляет списками доменов и подсетями, а сам VPN делает AmneziaWG.

Обычный обход сайтов через DPI от AmneziaWG **не зависит** — он работает и без VPN Split.

---

## VPN Split простыми словами

**Зачем:** пустить через VPN только нужное (например Cursor или Telegram), а YouTube и остальной интернет оставить на обычном DPI.

**Как пользоваться:**

1. Установи **AmneziaWG** с официального сайта / GitHub релизов.  
2. Импортируй в AmneziaWG свой сервер и **экспортируй файл `.conf`**.  
3. В RKNHS открой вкладку **VPN Split**, укажи путь к этому `.conf` (лучше копия `base.conf`, не выходной `active.conf`).  
4. Добавь домены (можно списком, поддерживаются маски вроде `*.cursor.sh`) или подсети.  
5. Нажми **«Применить»** — программа пропишет IP в конфиг и исключения DPI.  
6. Подключи туннель в AmneziaWG (или через кнопку службы в RKNHS, если пользуешься системным туннелем).

Если AmneziaWG не установлен или `.conf` не указан — VPN Split просто не заработает; остальная программа при этом остаётся рабочей.

Подсказки по настройке `.conf` есть прямо в интерфейсе на странице VPN Split.

---

## Правовой статус / происхождение

Проект **основан** на идеях и наработках открытой экосистемы Zapret / связанных GUI, но это **отдельная модификация** (брендинг RKNHS, VPN Split, установщик, UI, лицензирование).

Публикация на GitHub — для демонстрации навыков (UI, Windows networking, packaging).  
**Не open-source лицензия:** без явного разрешения автора использование ограничено просмотром.

Автор форка: **Sazzero** (`sarielsaz`).

---

## Контакты

- GitHub: [github.com/sarielsaz/RKNHS](https://github.com/sarielsaz/RKNHS)
- Telegram автора: [t.me/Alybion](https://t.me/Alybion) — можно написать по вопросам проекта
