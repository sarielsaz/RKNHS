from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class ListsFeature:
    startup_lists_check: Callable
    import_zip_pack: Callable
    restore_from_cache: Callable
    snapshot_current_base: Callable
    export_current_base_zip: Callable


def build_lists_feature() -> ListsFeature:
    def _public():
        from lists import public as lists_public

        return lists_public

    return ListsFeature(
        startup_lists_check=lambda *args, **kwargs: _public().startup_lists_check(*args, **kwargs),
        import_zip_pack=lambda *args, **kwargs: _public().import_zip_pack(*args, **kwargs),
        restore_from_cache=lambda *args, **kwargs: _public().restore_from_cache(*args, **kwargs),
        snapshot_current_base=lambda *args, **kwargs: _public().snapshot_current_base(*args, **kwargs),
        export_current_base_zip=lambda *args, **kwargs: _public().export_current_base_zip(*args, **kwargs),
    )
