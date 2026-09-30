from __future__ import annotations

import time
from typing import Dict, List

from log.log import log
from winws_runtime.runtime.system_ops import kill_process_by_pid_runtime
from utils.windows_process_probe import iter_process_records_winapi


CONFLICTING_PROCESSES = {
    "ProcessHacker.exe": {
        "name": "Process Hacker",
        "reason": "Перехватывает системные вызовы и может блокировать WinDivert",
        "solution": "Закройте Process Hacker и повторите запуск RKNHS",
    },
    "procexp.exe": {
        "name": "Process Explorer",
        "reason": "Может конфликтовать с WinDivert",
        "solution": "Закройте Process Explorer и повторите запуск RKNHS",
    },
    "procexp64.exe": {
        "name": "Process Explorer (64-bit)",
        "reason": "Может конфликтовать с WinDivert",
        "solution": "Закройте Process Explorer и повторите запуск RKNHS",
    },
    "GoodbyeDPI.exe": {
        "name": "GoodbyeDPI",
        "reason": "Конфликт с другим DPI-bypass инструментом",
        "solution": "Используйте только один DPI-bypass инструмент",
    },
    "SpoofDPI.exe": {
        "name": "SpoofDPI",
        "reason": "Конфликт с другим DPI-bypass инструментом",
        "solution": "Используйте только один DPI-bypass инструмент",
    },
}

_CONFLICTING_PROCESS_BY_NAME = {
    str(exe_name or "").strip().lower(): dict(info or {})
    for exe_name, info in CONFLICTING_PROCESSES.items()
}


def check_conflicting_processes() -> List[Dict[str, str]]:
    """Ищет программы, которые могут мешать WinDivert."""
    found_conflicts: list[dict] = []
    try:
        for pid, proc_name in iter_process_records_winapi():
            normalized = str(proc_name or "").strip().lower()
            info = _CONFLICTING_PROCESS_BY_NAME.get(normalized)
            if not info:
                continue

            found_conflicts.append(
                {
                    "exe": normalized,
                    "name": info.get("name", normalized),
                    "reason": info.get("reason", ""),
                    "solution": info.get("solution", ""),
                    "pid": int(pid),
                }
            )
            log(
                f"Обнаружен конфликтующий процесс: {info.get('name', normalized)} ({normalized}, PID: {pid})",
                "WARNING",
            )
    except Exception as e:
        log(f"Ошибка WinAPI-проверки конфликтующих процессов: {e}", "DEBUG")

    return found_conflicts


def build_launch_conflict_advice() -> tuple[str, str] | None:
    """Возвращает подсказку только после неудачного запуска RKNHS."""
    conflicting = check_conflicting_processes()
    if not conflicting:
        return None

    names = ", ".join(
        str(item.get("name") or item.get("exe") or "неизвестная программа")
        for item in conflicting
    )
    solutions = []
    for item in conflicting:
        solution = str(item.get("solution") or "").strip()
        if solution and solution not in solutions:
            solutions.append(solution)

    cause = f"{names}, похоже, помешал запуску RKNHS: WinDivert не смог открыться"
    solution = "\n".join(solutions) or "Закройте конфликтующую программу и повторите запуск RKNHS"
    return cause, solution


def try_kill_conflicting_processes(auto_kill: bool = False) -> bool:
    """Пытается закрыть конфликтующие процессы."""
    conflicting = check_conflicting_processes()

    if not conflicting:
        return True

    if not auto_kill:
        log(f"Обнаружено конфликтующих процессов: {len(conflicting)}", "WARNING")
        return False

    log("Попытка закрыть конфликтующие процессы...", "INFO")

    success_count = 0
    for conflict in conflicting:
        try:
            pid = int(conflict.get("pid") or 0)
            if pid <= 0:
                log(f"У конфликтующего процесса {conflict['name']} нет корректного PID", "ERROR")
                continue

            if kill_process_by_pid_runtime(pid, wait_timeout_ms=5000):
                log(f"Процесс {conflict['name']} (PID {pid}) закрыт через WinAPI", "SUCCESS")
                success_count += 1
            else:
                log(f"Не удалось закрыть {conflict['name']} (PID {pid}) через WinAPI", "ERROR")
        except Exception as e:
            log(f"Ошибка при закрытии {conflict['name']}: {e}", "ERROR")

    if success_count == len(conflicting):
        log(f"Все конфликтующие процессы ({success_count}) закрыты", "SUCCESS")
        time.sleep(1)
        return True

    log(f"Закрыто {success_count}/{len(conflicting)} конфликтующих процессов", "WARNING")
    return False


def get_conflicting_processes_report() -> str:
    """Готовит текстовый отчёт для логов."""
    conflicting = check_conflicting_processes()

    if not conflicting:
        return ""

    lines = ["ОБНАРУЖЕНЫ КОНФЛИКТУЮЩИЕ ПРОГРАММЫ:", ""]

    for i, conflict in enumerate(conflicting, 1):
        pid_info = f" (PID: {conflict['pid']})" if conflict.get("pid") else ""
        lines.append(f"{i}. {conflict['name']}{pid_info}")
        lines.append(f"   Файл: {conflict['exe']}")
        lines.append(f"   Проблема: {conflict['reason']}")
        lines.append(f"   Решение: {conflict['solution']}")
        lines.append("")

    lines.append("Закройте эти программы, если запуск RKNHS завершился ошибкой.")
    return "\n".join(lines)
