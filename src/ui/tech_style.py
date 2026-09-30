"""Ultra-tech dark chrome via Fluent setCustomStyleSheet + paint patches (DESIGN.md)."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from ui.theme import ThemeTokens, get_theme_tokens
from ui.tech_fluent_patches import (
    apply_tech_card_radii,
    apply_tech_nav_indicators,
    force_void_window_background,
    install_tech_fluent_patches,
)

_TECH_STYLE_MARKER = "/* __RKNHS_TECH_STYLE__ */"
_CARD_GROUP_SPACING = 8
_PAGE_SECTION_SPACING = 16
_LAST_APPLIED_TECH_KEY: tuple | None = None
_TECH_TREE_WALK_DONE = False


def resolve_tech_tokens(tokens: ThemeTokens | None = None) -> ThemeTokens:
    """Dark-safe tokens for tech chrome (never light fg on void bg)."""
    if tokens is not None and not tokens.is_light:
        return tokens
    try:
        from settings.appearance import load_display_mode

        mode = str(load_display_mode() or "dark").strip().lower()
    except Exception:
        mode = "dark"
    if mode == "light":
        return tokens or get_theme_tokens("light")
    return get_theme_tokens("dark")


def build_window_chrome_qss(tokens: ThemeTokens | None = None) -> str:
    """Additive Fluent overrides (appended via setCustomStyleSheet)."""
    t = resolve_tech_tokens(tokens)
    accent = t.accent_hex
    accent_hover = t.accent_hover_hex
    accent_pressed = t.accent_pressed_hex
    accent_fg = t.accent_fg
    soft = t.accent_soft_bg
    soft_hover = t.accent_soft_bg_hover
    void_bg = t.void_bg
    panel = t.panel_bg
    fg = t.fg
    fg_muted = t.fg_muted
    fg_faint = t.fg_faint
    border = t.border_hairline
    border_hover = t.surface_border_hover
    radius_sm = t.radius_sm
    mono = t.font_mono_qss
    ui = t.font_family_qss
    content = "#0E1117" if not t.is_light else "#F3F5F8"

    return f"""
{_TECH_STYLE_MARKER}
FluentWindow, FluentWindow > QWidget {{
    background-color: {void_bg};
    color: {fg};
    font-family: {ui};
    font-size: 13px;
}}
NavigationInterface {{
    background-color: {void_bg};
    border: none;
    border-right: 1px solid {border};
}}
NavigationPanel[menu=false], NavigationPanel[menu=true] {{
    background-color: {void_bg};
    border: none;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
}}
NavigationPanel[transparent=true] {{
    background-color: {void_bg};
}}
NavigationInterface QScrollArea,
NavigationInterface #scrollWidget {{
    background-color: {void_bg};
    border: none;
}}
StackedWidget, StackedWidget[isTransparent=true] {{
    background-color: {content};
    border: none;
}}
FluentTitleBar, SplitTitleBar {{
    background-color: {void_bg};
    border-bottom: 1px solid {border};
}}
FluentTitleBar > QLabel#titleLabel,
SplitTitleBar > QLabel#titleLabel {{
    color: {fg};
    font-family: {mono};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
}}
/* High-contrast text — prevents Fluent light-palette black-on-void */
QLabel, FluentLabelBase, BodyLabel, CaptionLabel, StrongBodyLabel,
SubtitleLabel, TitleLabel, CheckBox {{
    color: {fg};
}}
CaptionLabel {{
    color: {fg_muted};
    font-family: {mono};
    font-size: 11px;
    background: transparent;
}}
SettingCardGroup > QLabel {{
    color: {fg};
    background-color: transparent;
    border: none;
}}
HeaderCardWidget #headerLabel {{
    color: {fg};
    background: transparent;
}}
SettingCard QLabel#titleLabel,
ExpandSettingCard QLabel#titleLabel {{
    color: {fg};
    background: transparent;
}}
SettingCard QLabel#contentLabel,
ExpandSettingCard QLabel#contentLabel {{
    color: {fg_muted};
    background: transparent;
}}
SearchLineEdit, LineEdit, TextEdit, PlainTextEdit {{
    background-color: {panel};
    color: {fg};
    border: 1px solid {border};
    border-bottom: 1px solid {border};
    border-radius: {radius_sm};
    padding: 4px 10px;
    selection-background-color: {soft_hover};
    font-family: {ui};
}}
SearchLineEdit:hover, LineEdit:hover {{
    background-color: {panel};
    border: 1px solid {border_hover};
}}
SearchLineEdit:focus, LineEdit:focus,
LineEdit:focus[transparent=true], LineEdit[transparent=false]:focus {{
    background-color: {panel};
    border: 1px solid {accent};
    border-bottom: 1px solid {accent};
}}
PushButton, ToolButton, ToggleButton, ToggleToolButton {{
    background-color: transparent;
    color: {fg};
    border: 1px solid {border};
    border-top: 1px solid {border};
    border-radius: {radius_sm};
    padding: 6px 14px;
    font-family: {ui};
    font-size: 13px;
    min-height: 32px;
    outline: none;
}}
PushButton:hover, ToolButton:hover {{
    background-color: {soft};
    border: 1px solid {border_hover};
    border-top: 1px solid {border_hover};
}}
PushButton:pressed, ToolButton:pressed {{
    background-color: {soft_hover};
}}
PrimaryPushButton, PrimaryToolButton,
ToggleButton:checked, ToggleToolButton:checked {{
    color: {accent_fg};
    background-color: {accent};
    border: 1px solid {accent};
    border-bottom: 1px solid {accent};
    border-radius: {radius_sm};
    font-weight: 600;
}}
PrimaryPushButton:hover, PrimaryToolButton:hover,
ToggleButton:checked:hover, ToggleToolButton:checked:hover {{
    color: {accent_fg};
    background-color: {accent_hover};
    border: 1px solid {accent_hover};
    border-bottom: 1px solid {accent_hover};
}}
PrimaryPushButton:pressed, PrimaryToolButton:pressed,
ToggleButton:checked:pressed, ToggleToolButton:checked:pressed {{
    color: {accent_fg};
    background-color: {accent_pressed};
    border: 1px solid {accent_pressed};
}}
TransparentPushButton {{
    background-color: transparent;
    color: {fg_muted};
    border: 1px solid transparent;
    border-radius: {radius_sm};
}}
TransparentPushButton:hover {{
    color: {fg};
    border: 1px solid {border};
    background-color: {soft};
}}
ComboBox, ModelComboBox {{
    background-color: {panel};
    color: {fg};
    border: 1px solid {border};
    border-top: 1px solid {border};
    border-radius: {radius_sm};
    padding: 5px 31px 6px 11px;
    outline: none;
}}
ComboBox:hover, ModelComboBox:hover {{
    background-color: {panel};
    border: 1px solid {border_hover};
}}
StrongBodyLabel, SubtitleLabel, TitleLabel, BodyLabel {{
    color: {fg};
    font-family: {ui};
    background: transparent;
}}
ScrollArea, SmoothScrollArea, QScrollArea {{
    background-color: transparent;
    border: none;
}}
Pivot {{
    background-color: transparent;
    border-bottom: 1px solid {border};
}}
QScrollBar:vertical {{
    background: {void_bg};
    width: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {t.scrollbar_handle};
    min-height: 28px;
    border-radius: 0px;
    border: 1px solid transparent;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.scrollbar_handle_hover};
    border: 1px solid {accent};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
    border: none;
}}
QScrollBar:horizontal {{
    background: {void_bg};
    height: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {t.scrollbar_handle};
    min-width: 28px;
    border-radius: 0px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {t.scrollbar_handle_hover};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    width: 0;
    background: transparent;
    border: none;
}}
""".strip()


def _set_fluent_custom_sheet(widget, qss: str) -> None:
    if widget is None:
        return
    try:
        from qfluentwidgets import setCustomStyleSheet

        setCustomStyleSheet(widget, qss, qss)
    except Exception:
        try:
            current = str(widget.styleSheet() or "")
            if _TECH_STYLE_MARKER in current:
                begin = current.find(_TECH_STYLE_MARKER)
                prefix = current[:begin].rstrip()
                merged = f"{prefix}\n{qss}".strip() if prefix else qss
            else:
                merged = f"{current}\n{qss}".strip() if current.strip() else qss
            widget.setStyleSheet(merged)
        except Exception:
            pass


def apply_setting_card_group_spacing(window_or_root, spacing: int = _CARD_GROUP_SPACING) -> None:
    """Unstick bordered SettingCard rows (Fluent default spacing is 2px)."""
    if window_or_root is None:
        return
    try:
        from qfluentwidgets import SettingCardGroup
        from PyQt6.QtWidgets import QLabel
    except Exception:
        return
    t = resolve_tech_tokens()
    title_qss = (
        f"color: {t.fg}; background: transparent; border: none; "
        f"font-family: {t.font_family_qss}; font-size: 15px; font-weight: 600;"
    )
    try:
        groups = window_or_root.findChildren(SettingCardGroup)
    except Exception:
        groups = ()
    for group in groups:
        try:
            layout = getattr(group, "cardLayout", None)
            if layout is not None and hasattr(layout, "setSpacing"):
                layout.setSpacing(int(spacing))
            title = getattr(group, "titleLabel", None)
            if isinstance(title, QLabel):
                title.setStyleSheet(title_qss)
            group.adjustSize()
        except Exception:
            continue


def apply_tech_style_to_window(window, tokens: ThemeTokens | None = None) -> None:
    """Force void chrome + Fluent paint patches + custom QSS overrides."""
    global _LAST_APPLIED_TECH_KEY, _TECH_TREE_WALK_DONE
    if window is None:
        return

    install_tech_fluent_patches()
    t = resolve_tech_tokens(tokens)
    tech_key = (t.theme_name, t.accent_hex, t.void_bg, t.panel_bg, t.fg)
    style_unchanged = tech_key == _LAST_APPLIED_TECH_KEY

    if not style_unchanged:
        tech = build_window_chrome_qss(t)
        force_void_window_background(window, t.void_bg)

        _set_fluent_custom_sheet(window, tech)
        nav = getattr(window, "navigationInterface", None)
        _set_fluent_custom_sheet(nav, tech)
        if nav is not None:
            panel = getattr(nav, "panel", None)
            _set_fluent_custom_sheet(panel, tech)
            scroll = getattr(nav, "scrollWidget", None) or getattr(panel, "scrollWidget", None)
            _set_fluent_custom_sheet(scroll, tech)
        stacked = getattr(window, "stackedWidget", None)
        _set_fluent_custom_sheet(stacked, tech)
        title_bar = getattr(window, "titleBar", None)
        _set_fluent_custom_sheet(title_bar, tech)
        _LAST_APPLIED_TECH_KEY = tech_key
    else:
        nav = getattr(window, "navigationInterface", None)

    # Tree walks (findChildren) are expensive — only on first apply / token change.
    need_tree_walk = (not _TECH_TREE_WALK_DONE) or (not style_unchanged)
    if need_tree_walk:
        accent = QColor(t.accent_hex)
        if not accent.isValid():
            accent = QColor(0x5C, 0xD6, 0xFF)
        apply_tech_nav_indicators(window, accent)
        apply_tech_card_radii(window)
        apply_setting_card_group_spacing(window)
        try:
            from qfluentwidgets.components.navigation.navigation_widget import NavigationWidget

            for widget in window.findChildren(NavigationWidget):
                try:
                    widget.setTextColor(QColor(20, 24, 32), QColor(235, 242, 250))
                except Exception:
                    continue
        except Exception:
            pass
        _TECH_TREE_WALK_DONE = True

    try:
        if not style_unchanged:
            window.update()
            if nav is not None:
                nav.update()
    except Exception:
        pass


def invalidate_tech_style_cache() -> None:
    """Call when sidebar gains new items so nav colors/spacing re-apply."""
    global _LAST_APPLIED_TECH_KEY, _TECH_TREE_WALK_DONE
    _LAST_APPLIED_TECH_KEY = None
    _TECH_TREE_WALK_DONE = False


def build_settings_card_qss(tokens: ThemeTokens | None = None) -> str:
    """Full card QSS — must keep header/label colors (setStyleSheet replaces Fluent sheet)."""
    t = resolve_tech_tokens(tokens)
    return f"""
HeaderCardWidget, CardWidget, SimpleCardWidget {{
    background-color: {t.panel_bg};
    border: 1px solid {t.border_hairline};
    border-radius: {t.radius_sm};
}}
HeaderCardWidget #headerLabel {{
    color: {t.fg};
    background: transparent;
}}
HeaderCardWidget > #headerView,
HeaderCardWidget > #view {{
    background-color: transparent;
}}
QLabel {{
    color: {t.fg};
    background: transparent;
}}
""".strip()


def build_hud_caption_qss(tokens: ThemeTokens | None = None) -> str:
    t = resolve_tech_tokens(tokens)
    return (
        f"color: {t.fg_muted}; "
        f"font-family: {t.font_mono_qss}; "
        "font-size: 10px; "
        "font-weight: 600; "
        "letter-spacing: 1px; "
        "background: transparent;"
    )


def build_hud_cell_qss(tokens: ThemeTokens | None = None) -> str:
    t = tokens or get_theme_tokens()
    return (
        f"QFrame#hudCell {{"
        f"background-color: {t.panel_bg}; "
        f"border: 1px solid {t.border_hairline}; "
        f"border-top: 1px solid {t.surface_border_hover}; "
        f"border-radius: {t.radius_sm};"
        f"}}"
        f"QFrame#hudCell:hover {{"
        f"border: 1px solid {t.accent_hex};"
        f"}}"
    )


def build_hud_strip_qss(tokens: ThemeTokens | None = None) -> str:
    """Outer strip stays frameless so cells don't double-border."""
    t = tokens or get_theme_tokens()
    return (
        f"QFrame#hudStrip {{"
        f"background-color: transparent; "
        f"border: none;"
        f"}}"
    )


def build_status_hero_qss(tokens: ThemeTokens | None = None) -> str:
    t = tokens or get_theme_tokens()
    return (
        f"QFrame#statusHero {{"
        f"background-color: {t.panel_bg}; "
        f"border: 1px solid {t.border_hairline}; "
        f"border-left: 3px solid {t.accent_hex}; "
        f"border-radius: {t.radius_sm};"
        f"}}"
    )


def apply_page_header_styles(page, tokens: ThemeTokens | None = None) -> None:
    """Terminal // HEADING look for BasePage title / subtitle / sections."""
    t = resolve_tech_tokens(tokens)
    title = getattr(page, "title_label", None)
    subtitle = getattr(page, "subtitle_label", None)
    title_qss = (
        f"color: {t.accent_hex}; "
        f"font-family: {t.font_mono_qss}; "
        "font-size: 16px; font-weight: 600; "
        "letter-spacing: 1px; background: transparent;"
    )
    subtitle_qss = (
        f"color: {t.fg_muted}; "
        f"font-family: {t.font_mono_qss}; "
        "font-size: 12px; background: transparent;"
    )
    section_qss = build_section_heading_qss(t)
    try:
        if title is not None:
            title.setStyleSheet(title_qss)
        if subtitle is not None:
            subtitle.setStyleSheet(subtitle_qss)
        for binding in getattr(page, "_section_title_bindings", None) or []:
            label = binding[0] if isinstance(binding, tuple) else binding
            try:
                label.setStyleSheet(section_qss)
            except Exception:
                continue
    except Exception:
        pass


def build_section_heading_qss(tokens: ThemeTokens | None = None) -> str:
    t = resolve_tech_tokens(tokens)
    return (
        f"color: {t.fg_muted}; "
        f"font-family: {t.font_mono_qss}; "
        "font-size: 11px; font-weight: 600; "
        "letter-spacing: 1px; background: transparent; "
        f"padding-top: 4px; border-bottom: 1px solid {t.border_hairline}; "
        "padding-bottom: 4px;"
    )


def build_inline_section_heading_qss(tokens: ThemeTokens | None = None) -> str:
    """Mono // SECTION style for titles inside cards (no divider line)."""
    t = resolve_tech_tokens(tokens)
    return (
        f"color: {t.fg_muted}; "
        f"font-family: {t.font_mono_qss}; "
        "font-size: 11px; font-weight: 600; "
        "letter-spacing: 1px; background: transparent;"
    )


def style_inline_section_label(label, text: str | None = None, *, tokens: ThemeTokens | None = None) -> None:
    """Apply // SECTION mono caption to an in-card heading label."""
    try:
        from ui.tech_type import format_terminal_heading

        if text is not None:
            label.setText(format_terminal_heading(text))
        label.setStyleSheet(build_inline_section_heading_qss(tokens))
    except Exception:
        if text is not None:
            try:
                label.setText(str(text))
            except Exception:
                pass


def build_primary_button_qss(tokens: ThemeTokens | None = None) -> str:
    t = resolve_tech_tokens(tokens)
    return (
        f"QPushButton{{background-color:{t.accent_hex};color:{t.accent_fg};"
        f"border:1px solid {t.accent_hex};border-radius:{t.radius_sm};"
        f"padding:6px 14px;font-weight:600;min-height:32px;}}"
        f"QPushButton:hover{{background-color:{t.accent_hover_hex};}}"
        f"QPushButton:pressed{{background-color:{t.accent_pressed_hex};}}"
    )


def build_ghost_button_qss(tokens: ThemeTokens | None = None) -> str:
    t = resolve_tech_tokens(tokens)
    return (
        f"QPushButton{{background-color:transparent;color:{t.fg};"
        f"border:1px solid {t.border_hairline};border-radius:{t.radius_sm};"
        f"padding:6px 14px;min-height:32px;}}"
        f"QPushButton:hover{{background-color:{t.accent_soft_bg};"
        f"border-color:{t.surface_border_hover};}}"
    )


__all__ = [
    "apply_page_header_styles",
    "apply_setting_card_group_spacing",
    "apply_tech_style_to_window",
    "build_ghost_button_qss",
    "build_hud_caption_qss",
    "build_hud_cell_qss",
    "build_hud_strip_qss",
    "build_inline_section_heading_qss",
    "build_primary_button_qss",
    "build_section_heading_qss",
    "build_settings_card_qss",
    "build_status_hero_qss",
    "build_window_chrome_qss",
    "invalidate_tech_style_cache",
    "resolve_tech_tokens",
    "style_inline_section_label",
]
