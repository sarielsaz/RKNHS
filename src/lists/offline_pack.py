"""Atomic offline pack for lists: update without breaking live finals mid-download."""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lists.core.layered_files import rebuild_all_layered_list_files, safe_list_file_name
from lists.core.paths import get_lists_dir


@dataclass(frozen=True, slots=True)
class OfflinePackResult:
    ok: bool
    message: str
    updated_files: tuple[str, ...] = ()


def _lists_root() -> Path:
    return Path(get_lists_dir())


def pack_cache_dir() -> Path:
    path = _lists_root() / "pack_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def staging_dir() -> Path:
    path = _lists_root() / "staging"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_dir() -> Path:
    path = _lists_root() / "base"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _iter_list_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        [
            path
            for path in folder.iterdir()
            if path.is_file() and safe_list_file_name(path.name)
        ],
        key=lambda item: item.name.lower(),
    )


def snapshot_current_base() -> OfflinePackResult:
    """Copy current base lists into pack_cache so updates can be rolled back."""
    base = _base_dir()
    cache = pack_cache_dir()
    copied: list[str] = []
    try:
        for path in _iter_list_files(base):
            target = cache / path.name
            shutil.copy2(path, target)
            copied.append(path.name)
        if not copied:
            return OfflinePackResult(False, "Нет базовых списков для снимка")
        return OfflinePackResult(True, f"Снимок сохранён: {len(copied)} файл(ов)", tuple(copied))
    except Exception as exc:
        return OfflinePackResult(False, f"Не удалось сохранить снимок: {exc}")


def _atomic_replace(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    try:
        if tmp.exists():
            tmp.unlink()
    except Exception:
        pass
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def apply_staged_base_files(source_dir: Path | str) -> OfflinePackResult:
    """
    Replace base lists from a prepared folder, then rebuild finals.

    Current final list files stay intact until the whole base set is written,
    so a running DPI process never sees a half-updated folder.
    """
    source = Path(source_dir)
    if not source.is_dir():
        return OfflinePackResult(False, "Папка пакета не найдена")

    files = _iter_list_files(source)
    if not files:
        return OfflinePackResult(False, "В пакете нет файлов списков")

    snapshot = snapshot_current_base()
    if not snapshot.ok and "Нет базовых" not in snapshot.message:
        return snapshot

    updated: list[str] = []
    try:
        for path in files:
            _atomic_replace(path, _base_dir() / path.name)
            updated.append(path.name)
        rebuild_all_layered_list_files(_lists_root())
        return OfflinePackResult(
            True,
            f"Списки обновлены без простоя: {len(updated)} файл(ов)",
            tuple(updated),
        )
    except Exception as exc:
        restore_from_cache()
        return OfflinePackResult(False, f"Обновление прервано, откат: {exc}")


def restore_from_cache() -> OfflinePackResult:
    cache = pack_cache_dir()
    files = _iter_list_files(cache)
    if not files:
        return OfflinePackResult(False, "Нет сохранённого снимка для отката")
    updated: list[str] = []
    try:
        for path in files:
            _atomic_replace(path, _base_dir() / path.name)
            updated.append(path.name)
        rebuild_all_layered_list_files(_lists_root())
        return OfflinePackResult(True, f"Списки откачены: {len(updated)} файл(ов)", tuple(updated))
    except Exception as exc:
        return OfflinePackResult(False, f"Откат не удался: {exc}")


def import_zip_pack(zip_path: str | Path) -> OfflinePackResult:
    """Import an offline zip pack into staging, then apply atomically."""
    archive = Path(zip_path)
    if not archive.is_file():
        return OfflinePackResult(False, "Файл пакета не найден")

    stage = staging_dir()
    try:
        for old in _iter_list_files(stage):
            old.unlink(missing_ok=True)
    except Exception:
        pass

    try:
        with zipfile.ZipFile(archive, "r") as zf:
            members = [
                name
                for name in zf.namelist()
                if not name.endswith("/") and safe_list_file_name(Path(name).name)
            ]
            if not members:
                return OfflinePackResult(False, "В архиве нет файлов списков")
            with tempfile.TemporaryDirectory(prefix="rknhs_lists_") as tmp:
                tmp_root = Path(tmp)
                zf.extractall(tmp_root)
                extracted: list[Path] = []
                for path in tmp_root.rglob("*"):
                    if path.is_file() and safe_list_file_name(path.name):
                        target = stage / path.name
                        shutil.copy2(path, target)
                        extracted.append(target)
                if not extracted:
                    return OfflinePackResult(False, "После распаковки файлы списков не найдены")
        return apply_staged_base_files(stage)
    except zipfile.BadZipFile:
        return OfflinePackResult(False, "Повреждённый zip-пакет")
    except Exception as exc:
        return OfflinePackResult(False, f"Не удалось применить пакет: {exc}")


def export_current_base_zip(destination: str | Path) -> OfflinePackResult:
    dest = Path(destination)
    files = _iter_list_files(_base_dir())
    if not files:
        return OfflinePackResult(False, "Нет базовых списков для экспорта")
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in files:
                zf.write(path, arcname=path.name)
        return OfflinePackResult(True, f"Пакет сохранён: {dest.name}", tuple(p.name for p in files))
    except Exception as exc:
        return OfflinePackResult(False, f"Экспорт не удался: {exc}")


__all__ = [
    "OfflinePackResult",
    "apply_staged_base_files",
    "export_current_base_zip",
    "import_zip_pack",
    "pack_cache_dir",
    "restore_from_cache",
    "snapshot_current_base",
    "staging_dir",
]
