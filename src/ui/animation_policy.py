from __future__ import annotations

from ui.window_ui_session import get_window_ui_session

_CANONICAL_ANIMATION_START = None


def _ensure_canonical_animation_start():
    """Сохраняет оригинальный QAbstractAnimation.start один раз."""
    global _CANONICAL_ANIMATION_START
    if _CANONICAL_ANIMATION_START is None:
        from PyQt6.QtCore import QAbstractAnimation

        _CANONICAL_ANIMATION_START = QAbstractAnimation.start
    return _CANONICAL_ANIMATION_START


def _animation_classes():
    from PyQt6.QtCore import (
        QAbstractAnimation,
        QParallelAnimationGroup,
        QPropertyAnimation,
        QSequentialAnimationGroup,
        QVariantAnimation,
    )

    return (
        QAbstractAnimation,
        QVariantAnimation,
        QPropertyAnimation,
        QSequentialAnimationGroup,
        QParallelAnimationGroup,
    )


def are_animations_enabled() -> bool:
    """Читает текущее пользовательское состояние мастер-переключателя анимаций."""
    try:
        from settings.appearance import peek_warmed_animations_enabled

        return bool(peek_warmed_animations_enabled())
    except Exception:
        return False


def register_managed_animation(animation, duration_ms: int | None = None):
    """Запоминает базовую длительность анимации и сразу применяет текущую policy."""
    try:
        if duration_ms is not None:
            animation.setDuration(int(duration_ms))
            base_duration = int(duration_ms)
        else:
            base_duration = int(animation.duration())

        animation._zapret_base_duration = max(0, base_duration)
    except Exception:
        pass

    apply_animation_policy(animation)
    return animation


def apply_animation_policy(animation) -> None:
    """Применяет текущую policy к конкретной анимации без её запуска."""
    try:
        base_duration = int(getattr(animation, "_zapret_base_duration", animation.duration()))
    except Exception:
        return

    try:
        animation.setDuration(base_duration if are_animations_enabled() else 0)
    except Exception:
        pass


def start_managed_animation(animation, policy=None) -> None:
    """Запускает анимацию после применения локальной policy по длительности."""
    apply_animation_policy(animation)

    try:
        if policy is None:
            animation.start()
        else:
            animation.start(policy)
    except Exception:
        pass


def apply_window_animation_policy(window, enabled: bool) -> None:
    """Применяет мастер-политику анимаций и пересчитывает зависимую прокрутку редакторов."""
    apply_process_animation_fallback(enabled)

    try:
        from settings.appearance import peek_warmed_editor_smooth_scroll_enabled

        apply_window_editor_smooth_scroll_policy(window, bool(peek_warmed_editor_smooth_scroll_enabled()))
    except Exception:
        pass


def apply_process_animation_fallback(enabled: bool) -> None:
    """Временно включает или отключает глобальный fallback для QPropertyAnimation."""
    try:
        from PyQt6.QtCore import QAbstractAnimation
    except Exception:
        return

    canonical = _ensure_canonical_animation_start()
    deletion_policy = QAbstractAnimation.DeletionPolicy

    def _normal_start(self, policy=deletion_policy.KeepWhenStopped):
        canonical(self, policy)

    def _instant_start(self, policy=deletion_policy.KeepWhenStopped):
        try:
            self.setDuration(0)
        except Exception:
            pass
        canonical(self, policy)

    target = _normal_start if enabled else _instant_start
    for cls in _animation_classes():
        try:
            if hasattr(cls, "start"):
                setattr(cls, "start", target)
        except Exception:
            pass


def apply_window_smooth_scroll_policy(window, enabled: bool) -> None:
    """Переключает плавную прокрутку страниц, списков и деревьев, но не редакторов."""
    try:
        from ui.smooth_scroll import apply_smooth_scroll_mode, is_editor_smooth_scroll_target

        def _apply_smooth_mode(target) -> None:
            if is_editor_smooth_scroll_target(target):
                return

            apply_smooth_scroll_mode(target, enabled)
            custom_setter = getattr(target, "set_smooth_scroll_enabled", None)
            if callable(custom_setter):
                try:
                    custom_setter(enabled)
                except Exception:
                    pass

        for target in _iter_window_pages_and_children(window):
            _apply_smooth_mode(target)
    except Exception:
        pass


def apply_window_editor_smooth_scroll_policy(window, enabled: bool) -> None:
    """Переключает плавную прокрутку только у текстовых редакторов."""
    try:
        from ui.smooth_scroll import (
            apply_smooth_scroll_mode,
            get_effective_editor_smooth_scroll_enabled,
            is_editor_smooth_scroll_target,
        )

        effective_enabled = get_effective_editor_smooth_scroll_enabled(enabled)

        def _apply_editor_smooth_mode(target) -> None:
            if not is_editor_smooth_scroll_target(target):
                return

            apply_smooth_scroll_mode(target, effective_enabled)

            custom_setter = getattr(target, "set_smooth_scroll_enabled", None)
            if callable(custom_setter):
                try:
                    custom_setter(effective_enabled)
                except Exception:
                    pass

        for target in _iter_window_pages_and_children(window):
            _apply_editor_smooth_mode(target)
    except Exception:
        pass


def _iter_window_pages_and_children(window):
    """Итерирует по страницам окна и всем их дочерним QWidget-элементам."""
    try:
        from PyQt6.QtWidgets import QWidget
    except Exception:
        return

    session = get_window_ui_session(window)
    pages = [] if session is None else list(session.pages.values())
    for page in pages:
        yield page
        for child in page.findChildren(QWidget):
            yield child


PAGE_ENTER_MS = 90
BUTTON_PRESS_MS = 110


def run_page_enter_animation(widget) -> None:
    """Opacity 0→1 page enter (~150ms). No-op when animations are disabled."""
    if widget is None or not are_animations_enabled():
        return
    try:
        from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
        from PyQt6.QtWidgets import QGraphicsOpacityEffect

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(PAGE_ENTER_MS)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        register_managed_animation(anim, PAGE_ENTER_MS)

        def _clear() -> None:
            try:
                widget.setGraphicsEffect(None)
            except Exception:
                pass

        anim.finished.connect(_clear)
        start_managed_animation(anim)
        widget._rknhs_page_enter_anim = anim  # type: ignore[attr-defined]
    except Exception:
        pass


def run_press_feedback(widget) -> None:
    """Brief opacity dip on primary press (≤120ms)."""
    if widget is None or not are_animations_enabled():
        return
    try:
        from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup
        from PyQt6.QtWidgets import QGraphicsOpacityEffect

        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect.setOpacity(1.0)
        down = QPropertyAnimation(effect, b"opacity", widget)
        down.setStartValue(1.0)
        down.setEndValue(0.86)
        down.setDuration(max(1, BUTTON_PRESS_MS // 2))
        down.setEasingCurve(QEasingCurve.Type.OutCubic)
        up = QPropertyAnimation(effect, b"opacity", widget)
        up.setStartValue(0.86)
        up.setEndValue(1.0)
        up.setDuration(max(1, BUTTON_PRESS_MS // 2))
        up.setEasingCurve(QEasingCurve.Type.OutCubic)
        group = QSequentialAnimationGroup(widget)
        group.addAnimation(down)
        group.addAnimation(up)
        register_managed_animation(down, BUTTON_PRESS_MS // 2)
        register_managed_animation(up, BUTTON_PRESS_MS // 2)
        start_managed_animation(group)
        widget._rknhs_press_anim = group  # type: ignore[attr-defined]
    except Exception:
        pass
