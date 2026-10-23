"""Subprocess runner with background line streaming."""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

from sources import PROJECT_ROOT
from utils import strip_ansi

MAX_LOG_LINES = 1000


class SubprocessJob:
    """Runs main.py in a subprocess and collects stdout/stderr lines."""

    def __init__(self, env_overrides: dict[str, str]) -> None:
        self._env_overrides = env_overrides
        self._lines: list[str] = []
        self._lock = threading.Lock()
        self._proc: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self.done = False
        self.returncode: int | None = None
        self.stopped = False

    def start(self) -> None:
        env = {**dict(__import__("os").environ), **self._env_overrides}
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["NO_COLOR"] = "1"
        env.setdefault("TERM", "dumb")

        cmd = [sys.executable, "-u", "main.py"]
        self._proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        try:
            for raw in self._proc.stdout:
                line = strip_ansi(raw.rstrip("\r\n"))
                with self._lock:
                    self._lines.append(line)
                    if len(self._lines) > MAX_LOG_LINES:
                        self._lines = self._lines[-MAX_LOG_LINES:]
        finally:
            if self._proc.poll() is None:
                self._proc.wait()
            self.returncode = self._proc.returncode
            self.done = True

    def get_log_text(self) -> str:
        with self._lock:
            return "\n".join(self._lines)

    def stop(self) -> None:
        self.stopped = True
        if self._proc is None or self._proc.poll() is not None:
            return
        try:
            self._proc.terminate()
        except OSError:
            pass
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                self._proc.kill()
            except OSError:
                pass
            self._proc.wait(timeout=2)


def build_child_env(source_env: dict[str, str]) -> dict[str, str]:
    """Merge source flags into a subprocess environment."""
    import os

    env = dict(os.environ)
    env.update(source_env)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NO_COLOR"] = "1"
    return env


def run_blocking(
    env_overrides: dict[str, str],
    on_line: Callable[[str], None] | None = None,
) -> tuple[int, str]:
    """Run main.py synchronously; optional callback per line. Returns (exit_code, full_log)."""
    env = build_child_env(env_overrides)
    cmd = [sys.executable, "-u", "main.py"]
    lines: list[str] = []

    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = strip_ansi(raw.rstrip("\r\n"))
        lines.append(line)
        if len(lines) > MAX_LOG_LINES:
            lines = lines[-MAX_LOG_LINES:]
        if on_line:
            on_line("\n".join(lines))
    code = proc.wait()
    return code, "\n".join(lines)
