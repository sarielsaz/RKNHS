from __future__ import annotations

from qfluentwidgets import BodyLabel, MessageBoxBase, PlainTextEdit, SubtitleLabel


class DomainListImportDialog(MessageBoxBase):
    """Dialog to paste multiple domains (one per line)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Импорт доменов", self)
        self.contentLabel = BodyLabel(
            "По одному домену на строку. Строки с # игнорируются. "
            "Можно вставлять URL — будет взят только хост.",
            self,
        )
        self.contentLabel.setWordWrap(True)
        self._editor = PlainTextEdit(self)
        self._editor.setPlaceholderText("grok.com\nchatgpt.com\nx.com")
        self._editor.setMinimumHeight(180)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        self.viewLayout.addWidget(self._editor)

        self.yesButton.setText("Импортировать")
        self.cancelButton.setText("Отмена")
        self.widget.setMinimumWidth(480)

    def text(self) -> str:
        return str(self._editor.toPlainText() or "")
