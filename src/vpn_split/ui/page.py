"""VPN Split page — domain rules for AmneziaWG + winws2 coexistence."""

from __future__ import annotations

import os

from PyQt6.QtCore import QThread, QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    IndeterminateProgressBar,
    LineEdit,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SwitchButton,
    TableWidget,
)

from log.log import log
from settings.store import (
    add_vpn_split_rule,
    clear_vpn_split_rules,
    get_vpn_split_config_path,
    get_vpn_split_enabled,
    get_vpn_split_rules,
    remove_vpn_split_rule,
    remove_vpn_split_rules,
    set_vpn_split_config_path,
    set_vpn_split_enabled,
    set_vpn_split_rules,
)
from ui.message_box_accessibility import set_message_box_button_accessibility
from ui.pages.base_page import BasePage
from vpn_split.sync import (
    active_config_path,
    apply_vpn_split_sync,
    disable_vpn_split,
    import_config_file,
    import_vpn_split_domains,
    refresh_all_domain_ips,
    resolve_domain_rule,
    stop_vpn_system_tunnel,
)
from vpn_split.tunnel import format_tunnel_status, get_tunnel_status
from vpn_split.ui.config_guide import VPN_SPLIT_CONF_GUIDE_EXAMPLE, VPN_SPLIT_CONF_GUIDE_STEPS
from vpn_split.ui.domain_import_dialog import DomainListImportDialog


class _VpnSyncWorker(QThread):
    completed = pyqtSignal(object)

    def __init__(self, *, reload_tunnel: bool, parent=None):
        super().__init__(parent)
        self._reload_tunnel = bool(reload_tunnel)

    def run(self) -> None:
        self.completed.emit(apply_vpn_split_sync(reload_tunnel_service=self._reload_tunnel))


class _RefreshIpsWorker(QThread):
    completed = pyqtSignal(object)

    def run(self) -> None:
        self.completed.emit(refresh_all_domain_ips())


class _ImportDomainsWorker(QThread):
    completed = pyqtSignal(object)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = str(text or "")

    def run(self) -> None:
        self.completed.emit(import_vpn_split_domains(self._text))


class VpnSplitPage(BasePage):
    def __init__(self, parent=None, *, restart_winws=None):
        super().__init__(
            "VPN Split",
            "Домены через AmneziaWG, остальное — winws2 DPI",
            parent,
            title_key="page.vpn_split.title",
            subtitle_key="page.vpn_split.subtitle",
        )
        self._sync_worker: _VpnSyncWorker | None = None
        self._refresh_worker: _RefreshIpsWorker | None = None
        self._import_worker: _ImportDomainsWorker | None = None
        self._restart_winws = restart_winws
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(4000)
        self._status_timer.timeout.connect(self._refresh_tunnel_status)
        self._build_ui()
        self._reload_table()
        self._refresh_tunnel_status()
        self._status_timer.start()

    def _build_ui(self) -> None:
        self._hint_toggle = PushButton("Как это работает ▼", self.content)
        self._hint_toggle.clicked.connect(self._toggle_hint)
        self.add_widget(self._hint_toggle)

        self._hint_body = CaptionLabel(
            "1) Укажите ваш .conf из AmneziaWG (ключи остаются там же — RKNHS только читает файл).\n"
            "2) Добавляйте домены (grok.com) — RKNHS резолвит IP.\n"
            "3) «Применить» → обновляет DPI-исключения и active.conf.\n"
            "4) «Обновить IP всех доменов» — только DNS, без полного Apply.\n"
            "5) Обновите туннель в AmneziaWG при необходимости.\n\n"
            "Не используйте «CLI туннель», если управляете VPN только через AmneziaWG — "
            "эта кнопка создаёт Windows-службу, которую GUI Amnezia не отключает.\n\n"
            "YouTube идёт через DPI, не через VPN. RKNHS сам перезапускает winws2 при "
            "включении/выключении VPN — DPI-исключения действуют только пока туннель подключён.",
            self.content,
        )
        self._hint_body.setWordWrap(True)
        self._hint_body.setVisible(False)
        self.add_widget(self._hint_body)

        self._conf_guide_toggle = PushButton("Как настроить .conf ▼", self.content)
        self._conf_guide_toggle.clicked.connect(self._toggle_conf_guide)
        self.add_widget(self._conf_guide_toggle)

        self._conf_guide_body = CaptionLabel(VPN_SPLIT_CONF_GUIDE_STEPS, self.content)
        self._conf_guide_body.setWordWrap(True)
        self._conf_guide_body.setVisible(False)
        self.add_widget(self._conf_guide_body)

        self._conf_guide_example = QLabel(VPN_SPLIT_CONF_GUIDE_EXAMPLE, self.content)
        self._conf_guide_example.setWordWrap(True)
        self._conf_guide_example.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._conf_guide_example.setStyleSheet(
            "QLabel { font-family: 'Cascadia Mono', 'Consolas', monospace; font-size: 11px; }"
        )
        self._conf_guide_example.setVisible(False)
        self.add_widget(self._conf_guide_example)
        self.add_spacing(8)

        toggle_card = CardWidget(self.content)
        toggle_layout = QHBoxLayout(toggle_card)
        toggle_layout.setContentsMargins(16, 12, 16, 12)
        toggle_layout.addWidget(StrongBodyLabel("VPN Split включён", toggle_card))
        self._enabled_switch = SwitchButton(toggle_card)
        self._enabled_switch.setChecked(get_vpn_split_enabled())
        self._enabled_switch.checkedChanged.connect(self._on_enabled_changed)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self._enabled_switch)
        self.add_widget(toggle_card)
        self.add_spacing(10)

        tunnel_card = CardWidget(self.content)
        tunnel_layout = QVBoxLayout(tunnel_card)
        tunnel_layout.setContentsMargins(16, 12, 16, 12)
        tunnel_layout.setSpacing(8)
        tunnel_layout.addWidget(StrongBodyLabel("Состояние системного туннеля", tunnel_card))
        self._tunnel_status_label = BodyLabel("", tunnel_card)
        self._tunnel_status_label.setWordWrap(True)
        tunnel_layout.addWidget(self._tunnel_status_label)
        stop_row = QHBoxLayout()
        self._stop_tunnel_btn = PushButton("Остановить системный туннель", tunnel_card)
        self._stop_tunnel_btn.clicked.connect(self._stop_system_tunnel)
        stop_row.addWidget(self._stop_tunnel_btn)
        stop_row.addStretch()
        tunnel_layout.addLayout(stop_row)
        self.add_widget(tunnel_card)
        self.add_spacing(10)

        config_card = CardWidget(self.content)
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(16, 12, 16, 12)
        config_layout.setSpacing(8)
        config_layout.addWidget(StrongBodyLabel("Ваш конфиг AmneziaWG (.conf)", config_card))
        config_layout.addWidget(
            CaptionLabel(
                "Путь к файлу, который уже используете в AmneziaWG. «Сохранить копию» — необязательно.",
                config_card,
            )
        )
        row = QHBoxLayout()
        self._config_path_edit = LineEdit(config_card)
        self._config_path_edit.setPlaceholderText("C:\\Users\\…\\my_laptop_rknhs.conf")
        self._config_path_edit.setText(get_vpn_split_config_path())
        row.addWidget(self._config_path_edit, 1)
        browse_btn = PushButton("Обзор", config_card)
        browse_btn.clicked.connect(self._browse_config)
        import_btn = PushButton("Сохранить копию", config_card)
        import_btn.clicked.connect(self._import_config)
        open_active_btn = PushButton("active.conf", config_card)
        open_active_btn.clicked.connect(self._open_active_config)
        row.addWidget(browse_btn)
        row.addWidget(import_btn)
        row.addWidget(open_active_btn)
        config_layout.addLayout(row)
        self.add_widget(config_card)
        self.add_spacing(10)

        rules_card = CardWidget(self.content)
        rules_layout = QVBoxLayout(rules_card)
        rules_layout.setContentsMargins(16, 12, 16, 12)
        rules_layout.setSpacing(8)
        rules_layout.addWidget(StrongBodyLabel("Правила по доменам (через VPN, не DPI)", rules_card))

        add_row = QHBoxLayout()
        self._domain_edit = LineEdit(rules_card)
        self._domain_edit.setPlaceholderText("grok.com  или  *.cursor.sh")
        self._domain_edit.returnPressed.connect(self._add_domain)
        add_btn = PrimaryPushButton("Добавить домен", rules_card)
        add_btn.clicked.connect(self._add_domain)
        resolve_btn = PushButton("Резолв", rules_card)
        resolve_btn.clicked.connect(self._resolve_selected)
        add_row.addWidget(self._domain_edit, 1)
        add_row.addWidget(add_btn)
        add_row.addWidget(resolve_btn)
        rules_layout.addLayout(add_row)

        bulk_row = QHBoxLayout()
        self._refresh_all_ips_btn = PushButton("Обновить IP всех доменов", rules_card)
        self._refresh_all_ips_btn.setToolTip("DNS-резолв всех правил без «Применить»")
        self._refresh_all_ips_btn.clicked.connect(self._refresh_all_ips)
        paste_btn = PushButton("Вставить список", rules_card)
        paste_btn.clicked.connect(self._import_domains_paste)
        import_txt_btn = PushButton("Импорт .txt", rules_card)
        import_txt_btn.clicked.connect(self._import_domains_file)
        bulk_row.addWidget(self._refresh_all_ips_btn)
        bulk_row.addWidget(paste_btn)
        bulk_row.addWidget(import_txt_btn)
        bulk_row.addStretch()
        rules_layout.addLayout(bulk_row)

        self._table = TableWidget(rules_card)
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Домен", "IP (шт.)", "Последние IP"])
        self._table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(TableWidget.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self._configure_rules_table()
        rules_layout.addWidget(self._table, 1)

        remove_row = QHBoxLayout()
        remove_btn = PushButton("Удалить выбранные", rules_card)
        remove_btn.setToolTip("Ctrl/Shift — несколько строк. Del тоже удаляет.")
        remove_btn.clicked.connect(self._remove_selected)
        clear_btn = PushButton("Очистить весь список", rules_card)
        clear_btn.setToolTip("Удаляет все домены VPN Split")
        clear_btn.clicked.connect(self._clear_all_domains)
        remove_row.addWidget(remove_btn)
        remove_row.addWidget(clear_btn)
        remove_row.addStretch()
        rules_layout.addLayout(remove_row)
        self._table.setShortcutEnabled(True)
        QShortcut(QKeySequence.StandardKey.Delete, self._table, activated=self._remove_selected)
        self.add_widget(rules_card)
        self.add_spacing(10)

        actions_row = QWidget(self.content)
        actions = QHBoxLayout(actions_row)
        actions.setContentsMargins(0, 0, 0, 0)
        self._sync_btn = PrimaryPushButton("Применить", actions_row)
        self._sync_btn.clicked.connect(lambda: self._run_sync(reload_tunnel=False))
        self._sync_tunnel_btn = PushButton("Применить + CLI туннель", actions_row)
        self._sync_tunnel_btn.setToolTip(
            "Создаёт Windows-службу AmneziaWGTunnel — AmneziaWG GUI её не отключает. "
            "Предпочтительно обновлять active.conf вручную в AmneziaWG."
        )
        self._sync_tunnel_btn.clicked.connect(self._run_sync_with_cli_confirm)
        actions.addWidget(self._sync_btn)
        actions.addWidget(self._sync_tunnel_btn)
        actions.addStretch()
        self.add_widget(actions_row)

        self._progress = IndeterminateProgressBar(self.content)
        self._progress.hide()
        self.add_widget(self._progress)

        self._status_label = BodyLabel("", self.content)
        self._status_label.setWordWrap(True)
        self.add_widget(self._status_label)

    def _configure_rules_table(self) -> None:
        table = self._table
        try:
            table.setBorderVisible(True)
            table.setBorderRadius(8)
        except Exception:
            pass
        table.setMinimumHeight(280)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table.setAlternatingRowColors(True)
        table.setWordWrap(True)
        table.setTextElideMode(Qt.TextElideMode.ElideNone)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(40)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(1, 88)

    def _resize_rules_table_columns(self) -> None:
        table = self._table
        if table.rowCount() <= 0:
            return
        table.resizeColumnToContents(0)
        table.resizeRowsToContents()

    def _toggle_hint(self) -> None:
        expanded = not self._hint_body.isVisible()
        self._hint_body.setVisible(expanded)
        self._hint_toggle.setText("Как это работает ▲" if expanded else "Как это работает ▼")

    def _toggle_conf_guide(self) -> None:
        expanded = not self._conf_guide_body.isVisible()
        self._conf_guide_body.setVisible(expanded)
        self._conf_guide_example.setVisible(expanded)
        self._conf_guide_toggle.setText("Как настроить .conf ▲" if expanded else "Как настроить .conf ▼")

    def _set_busy(self, busy: bool) -> None:
        self._sync_btn.setEnabled(not busy)
        self._sync_tunnel_btn.setEnabled(not busy)
        self._refresh_all_ips_btn.setEnabled(not busy)
        if busy:
            self._progress.show()
        else:
            self._progress.hide()

    def _refresh_tunnel_status(self) -> None:
        status = get_tunnel_status()
        self._tunnel_status_label.setText(format_tunnel_status(status))
        self._stop_tunnel_btn.setEnabled(status.is_active)

    def _stop_system_tunnel(self) -> None:
        result = stop_vpn_system_tunnel()
        self._refresh_tunnel_status()
        message = str(result.message or "")
        if result.ok and callable(self._restart_winws):
            if self._restart_winws():
                message += " winws2 перезапущен."
        self._status_label.setText(message)

    def _run_sync_with_cli_confirm(self) -> None:
        body = (
            "Будет создана Windows-служба туннеля (AmneziaWGTunnel). "
            "AmneziaWG может показывать «нет активных туннелей», хотя VPN реально работает. "
            "Останавливать — кнопкой «Остановить системный туннель» или выключением VPN Split.\n\n"
            "Продолжить?"
        )
        box = MessageBox("CLI туннель", body, self)
        box.yesButton.setText("Создать службу")
        box.cancelButton.setText("Отмена")
        set_message_box_button_accessibility(
            box,
            yes_name="Создать Windows-службу туннеля",
            yes_description=body,
            cancel_name="Отменить создание службы",
            cancel_description="Закрывает диалог без создания Windows-службы.",
        )
        if box.exec():
            self._run_sync(reload_tunnel=True)

    def _on_enabled_changed(self, checked: bool) -> None:
        set_vpn_split_enabled(bool(checked))
        if not checked:
            result = disable_vpn_split()
            message = str(result.message or "")
            if callable(self._restart_winws) and self._restart_winws():
                message += " winws2 перезапущен."
            self._status_label.setText(message)
        self._refresh_tunnel_status()

    def _open_active_config(self) -> None:
        path = active_config_path()
        if os.path.isfile(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            self._status_label.setText(f"Файл ещё не создан. Нажмите «Применить». Будет: {path}")

    def _browse_config(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Выберите AmneziaWG конфиг", "", "WireGuard (*.conf);;All (*.*)")
        if path:
            self._config_path_edit.setText(path)
            set_vpn_split_config_path(path)

    def _import_config(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Импорт AmneziaWG конфиг", "", "WireGuard (*.conf);;All (*.*)")
        if not path:
            return
        try:
            target = import_config_file(path)
            self._config_path_edit.setText(target)
            set_vpn_split_config_path(target)
            self._status_label.setText(f"Конфиг скопирован в {target}")
        except OSError as exc:
            self._status_label.setText(f"Ошибка импорта: {exc}")

    def _reload_table(self) -> None:
        rules = get_vpn_split_rules()
        self._table.setRowCount(len(rules))
        if not rules:
            self._table.setMinimumHeight(160)
        else:
            self._table.setMinimumHeight(max(280, min(420, 56 + len(rules) * 40)))
        for row, item in enumerate(rules):
            domain = str(item.get("domain") or "")
            ips = list(item.get("ips") or [])
            preview = ", ".join(ips[:6])
            if len(ips) > 6:
                preview += f" … (+{len(ips) - 6})"
            domain_item = QTableWidgetItem(domain)
            count_item = QTableWidgetItem(str(len(ips)))
            preview_item = QTableWidgetItem(preview)
            if ips:
                preview_item.setToolTip("\n".join(ips))
            count_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            self._table.setItem(row, 0, domain_item)
            self._table.setItem(row, 1, count_item)
            self._table.setItem(row, 2, preview_item)
        self._resize_rules_table_columns()

    def _selected_domain(self) -> str:
        domains = self._selected_domains()
        return domains[0] if domains else ""

    def _selected_domains(self) -> list[str]:
        rows = sorted({index.row() for index in self._table.selectedIndexes()})
        domains: list[str] = []
        seen: set[str] = set()
        for row in rows:
            item = self._table.item(row, 0)
            domain = str(item.text() if item else "").strip()
            if not domain or domain in seen:
                continue
            seen.add(domain)
            domains.append(domain)
        return domains

    def _update_rule_ips(self, domain: str, ips: list[str]) -> None:
        clean = str(domain or "").strip().lower()
        rules = get_vpn_split_rules()
        for item in rules:
            if str(item.get("domain") or "").lower() == clean:
                item["ips"] = ips
        set_vpn_split_rules(rules)

    def _add_domain(self) -> None:
        from vpn_split.domain_patterns import normalize_domain_pattern

        domain = normalize_domain_pattern(str(self._domain_edit.text() or ""))
        if not domain:
            self._status_label.setText("Некорректный домен. Пример: grok.com или *.cursor.sh")
            return
        if add_vpn_split_rule(domain):
            _, ips = resolve_domain_rule(domain)
            self._update_rule_ips(domain, ips)
            self._status_label.setText(f"Добавлено {domain}: {len(ips)} IP")
        else:
            self._status_label.setText(f"Уже есть: {domain}")
        self._domain_edit.clear()
        self._reload_table()

    def _resolve_selected(self) -> None:
        from vpn_split.domain_patterns import normalize_domain_pattern

        selected = self._selected_domains()
        if selected:
            total_ips = 0
            for domain in selected:
                clean = normalize_domain_pattern(domain) or domain
                _, ips = resolve_domain_rule(clean)
                self._update_rule_ips(clean, ips)
                total_ips += len(ips)
            self._reload_table()
            self._status_label.setText(f"Резолв: {len(selected)} домен(ов), {total_ips} IP")
            return

        domain = normalize_domain_pattern(str(self._domain_edit.text() or ""))
        if not domain:
            self._status_label.setText("Выберите домены (Ctrl/Shift) или введите *.cursor.sh")
            return
        _, ips = resolve_domain_rule(domain)
        self._update_rule_ips(domain, ips)
        self._reload_table()
        self._status_label.setText(f"{domain}: {len(ips)} IP")

    def _remove_selected(self) -> None:
        domains = self._selected_domains()
        if not domains:
            self._status_label.setText("Выберите одну или несколько строк (Ctrl / Shift)")
            return
        if len(domains) == 1:
            remove_vpn_split_rule(domains[0])
            self._status_label.setText(f"Удалено: {domains[0]}")
        else:
            removed = remove_vpn_split_rules(domains)
            self._status_label.setText(f"Удалено доменов: {removed}")
        self._reload_table()

    def _clear_all_domains(self) -> None:
        rules = get_vpn_split_rules()
        count = len(rules)
        if count <= 0:
            self._status_label.setText("Список доменов уже пуст")
            return
        body = (
            f"Удалить все {count} домен(ов) из VPN Split?\n"
            "Это только правила программы; .conf AmneziaWG не трогаем."
        )
        box = MessageBox("Очистить все домены", body, self)
        box.yesButton.setText("Удалить все")
        box.cancelButton.setText("Отмена")
        set_message_box_button_accessibility(
            box,
            yes_name="Удалить все домены VPN Split",
            yes_description=body,
            cancel_name="Отменить очистку",
            cancel_description="Закрывает диалог без удаления доменов.",
        )
        if not box.exec():
            return
        removed = clear_vpn_split_rules()
        self._reload_table()
        self._status_label.setText(f"Очищено доменов: {removed}")

    def _refresh_all_ips(self) -> None:
        if self._refresh_worker is not None and self._refresh_worker.isRunning():
            return
        self._set_busy(True)
        worker = _RefreshIpsWorker(parent=self)
        worker.completed.connect(self._on_refresh_ips_done)
        worker.finished.connect(lambda: self._set_busy(False))
        self._refresh_worker = worker
        worker.start()

    def _on_refresh_ips_done(self, result) -> None:
        self._reload_table()
        message = str(getattr(result, "message", result) or "")
        self._status_label.setText(message)
        if getattr(result, "ok", False):
            log(message, "INFO")
        else:
            log(message, "WARNING")

    def _import_domains_paste(self) -> None:
        dialog = DomainListImportDialog(self)
        if dialog.exec():
            self._run_import(dialog.text())

    def _import_domains_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт доменов",
            "",
            "Text (*.txt);;All (*.*)",
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            self._status_label.setText(f"Ошибка чтения файла: {exc}")
            return
        self._run_import(text)

    def _run_import(self, text: str) -> None:
        if not str(text or "").strip():
            return
        if self._import_worker is not None and self._import_worker.isRunning():
            return
        self._set_busy(True)
        worker = _ImportDomainsWorker(text, parent=self)
        worker.completed.connect(self._on_import_done)
        worker.finished.connect(lambda: self._set_busy(False))
        self._import_worker = worker
        worker.start()

    def _on_import_done(self, result) -> None:
        self._reload_table()
        message = str(getattr(result, "message", result) or "")
        self._status_label.setText(message)
        if getattr(result, "ok", False):
            log(message, "INFO")
        else:
            log(message, "WARNING")

    def _run_sync(self, *, reload_tunnel: bool) -> None:
        path = str(self._config_path_edit.text() or "").strip()
        set_vpn_split_config_path(path)
        set_vpn_split_enabled(self._enabled_switch.isChecked())
        if self._sync_worker is not None and self._sync_worker.isRunning():
            return
        self._set_busy(True)
        worker = _VpnSyncWorker(reload_tunnel=reload_tunnel, parent=self)
        worker.completed.connect(self._on_sync_done)
        worker.finished.connect(lambda: self._set_busy(False))
        self._sync_worker = worker
        worker.start()

    def _on_sync_done(self, result) -> None:
        self._reload_table()
        message = str(getattr(result, "message", result) or "")
        if getattr(result, "ok", False) and callable(self._restart_winws):
            if self._restart_winws():
                message += " winws2 перезапущен."
            else:
                message += " Перезапустите winws2 вручную на главной странице."
        self._status_label.setText(message)
        self._refresh_tunnel_status()
        if getattr(result, "ok", False):
            log(message, "INFO")
        else:
            log(message, "WARNING")
