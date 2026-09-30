"""Короткие тексты страницы Telegram Proxy."""

from __future__ import annotations

from dataclasses import astuple, dataclass


@dataclass(frozen=True, slots=True)
class TelegramProxySettingsText:
    page_subtitle: str
    setup_title: str
    setup_description: str
    setup_fallback: str
    settings_title: str
    proxy_mode_title: str
    proxy_mode_description: str
    auto_setup_title: str
    auto_setup_description: str
    upstream_title: str
    upstream_toggle_title: str
    upstream_toggle_description: str
    upstream_preset_title: str
    upstream_preset_description: str
    upstream_catalog_missing: str
    upstream_mode_title: str
    upstream_mode_description: str
    upstream_udp_title: str
    upstream_udp_description: str
    cloudflare_toggle_title: str
    cloudflare_toggle_description: str
    cloudflare_worker_toggle_title: str
    cloudflare_worker_toggle_description: str
    advanced_title: str
    advanced_description: str
    fake_tls_domain_title: str
    fake_tls_domain_description: str
    dc_ip_title: str
    dc_ip_description: str
    performance_title: str
    performance_description: str
    proxy_protocol_title: str
    proxy_protocol_description: str
    manual_hidden_title: str
    manual_path: str
    diag_description: str

    def __iter__(self):
        return iter(astuple(self))


TELEGRAM_PROXY_SETTINGS_TEXT = TelegramProxySettingsText(
    page_subtitle=(
        "Если Telegram тормозит или не заходит — включите локальный прокси и откройте ссылку ниже."
    ),
    setup_title="Подключить Telegram",
    setup_description=(
        "Нажмите «Открыть» — Telegram сам предложит добавить прокси. "
        "Если окно не открылось, скопируйте ссылку и отправьте её себе в чат."
    ),
    setup_fallback="",
    settings_title="Основные настройки",
    proxy_mode_title="Режим прокси",
    proxy_mode_description=(
        "Обычно достаточно SOCKS5. MTProxy нужен только для секрета, Fake TLS и Cloudflare."
    ),
    auto_setup_title="Авто-настройка Telegram",
    auto_setup_description="Открывать ссылку при первом запуске прокси",
    upstream_title="Дополнительно",
    upstream_toggle_title="Внешний прокси",
    upstream_toggle_description=(
        "Запасной сервер, если провайдер режет IP Telegram напрямую."
    ),
    upstream_preset_title="Сервер",
    upstream_preset_description="Выберите сервер из списка или переключитесь на ручной ввод",
    upstream_catalog_missing=(
        "В этой сборке нет готового списка прокси. Можно указать сервер вручную ниже."
    ),
    upstream_mode_title="Весь TCP через SOCKS5",
    upstream_mode_description=(
        "Если выключено — через внешний прокси идут только проблемные серверы Telegram."
    ),
    upstream_udp_title="Пробовать звонки через SOCKS5 UDP",
    upstream_udp_description=(
        "Экспериментально. Поможет только если Telegram и выбранный сервер умеют UDP через SOCKS5."
    ),
    cloudflare_toggle_title="Cloudflare fallback",
    cloudflare_toggle_description=(
        "Запасной путь через Cloudflare-домены. Если поле доменов пустое — берётся авто-список."
    ),
    cloudflare_worker_toggle_title="Cloudflare Worker fallback",
    cloudflare_worker_toggle_description="Отдельный запасной путь через Worker-домены.",
    advanced_title="Продвинутый режим",
    advanced_description="Cloudflare, Fake TLS, ручные DC→IP. Обычно менять не нужно.",
    fake_tls_domain_title="Fake TLS домен",
    fake_tls_domain_description="Только для своего домена и Nginx с MTProxy Fake TLS.",
    dc_ip_title="DC → IP",
    dc_ip_description="Ручная таблица дата-центр → IP, например 4:149.154.167.220.",
    performance_title="Производительность",
    performance_description="Размер пула и буфер. Меняйте только при явных проблемах.",
    proxy_protocol_title="Proxy protocol для Nginx",
    proxy_protocol_description="Включайте только если Nginx отдаёт MTProxy через proxy_protocol.",
    manual_hidden_title="Ручная настройка",
    manual_path="Telegram → Настройки → Продвинутые → Тип соединения → Прокси",
    diag_description=(
        "Проверяет доступ к серверам Telegram, ваш локальный прокси и типичные сбои маршрута."
    ),
)
