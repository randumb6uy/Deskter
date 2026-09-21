"""App and browser discovery, indexing, fuzzy matching, and process management."""

import json
import logging
import os
import subprocess
import sys
import winreg
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import psutil
from rapidfuzz import fuzz, process

from jarvis.actions.com_utils import COMContext
from jarvis.actions.registry import ToolResult, tool

logger = logging.getLogger("jarvis.actions.apps")

APP_INDEX_FILE = Path("data/app_index.json")


class AppIndexer:
    """Discovers installed Windows applications from Start Menu, Registry, and config."""

    def __init__(self, aliases: Optional[Dict[str, str]] = None) -> None:
        self.aliases = aliases or {}
        self.index: Dict[str, str] = {}
        self.load_or_rebuild_index()

    def load_or_rebuild_index(self) -> None:
        """Load index from JSON cache if available, otherwise rebuild it."""
        if APP_INDEX_FILE.exists():
            try:
                with open(APP_INDEX_FILE, "r", encoding="utf-8") as f:
                    self.index = json.load(f)
                if self.index:
                    # Always merge aliases
                    for alias_name, alias_target in self.aliases.items():
                        self.index[alias_name.lower().strip()] = alias_target
                    return
            except Exception as e:
                logger.warning(f"Failed to load app index cache: {e}")

        self.rebuild_index()

    def rebuild_index(self) -> Dict[str, str]:
        """Scan Start Menu and Registry to build app index."""
        logger.info("Scanning installed applications...")
        apps: Dict[str, str] = {}

        # 1. Start Menu Shortcuts (.lnk)
        start_menu_dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        ]

        with COMContext():
            for sm_dir in start_menu_dirs:
                if not os.path.exists(sm_dir):
                    continue
                for root, _, files in os.walk(sm_dir):
                    for file in files:
                        if file.lower().endswith(".lnk"):
                            name = Path(file).stem.lower()
                            name = name.replace(" shortcut", "").strip()
                            lnk_path = os.path.join(root, file)

                            target_path = lnk_path
                            try:
                                import pythoncom
                                from win32com.shell import shell
                                shortcut = pythoncom.CoCreateInstance(
                                    shell.CLSID_ShellLink,
                                    None,
                                    pythoncom.CLSCTX_INPROC_SERVER,
                                    shell.IID_IShellLink,
                                )
                                persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                                persist_file.Load(lnk_path)
                                resolved_path, _ = shortcut.GetPath(shell.SLGP_UNCPRIORITY)
                                if resolved_path and os.path.exists(resolved_path):
                                    target_path = resolved_path
                            except Exception:
                                pass

                            if name and name not in apps:
                                apps[name] = target_path

        # 2. Registry App Paths
        reg_roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        ]

        for hkey, subkey_path in reg_roots:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            app_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, app_key_name) as app_key:
                                exe_path, _ = winreg.QueryValueEx(app_key, "")
                                clean_name = Path(app_key_name).stem.lower()
                                if clean_name and clean_name not in apps and os.path.exists(exe_path):
                                    apps[clean_name] = exe_path
                        except Exception:
                            continue
            except Exception:
                pass

        # 3. Common Windows built-ins
        builtins = {
            "notepad": "notepad.exe",
            "calc": "calc.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "terminal": "wt.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "paint": "mspaint.exe",
            "settings": "ms-settings:",
        }
        for b_name, b_path in builtins.items():
            if b_name not in apps:
                apps[b_name] = b_path

        # 4. Manual aliases from config
        for alias_name, alias_target in self.aliases.items():
            apps[alias_name.lower().strip()] = alias_target

        self.index = apps

        # Save cache
        try:
            APP_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(APP_INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(apps, f, indent=2)
            logger.info(f"Indexed {len(apps)} applications.")
        except Exception as e:
            logger.warning(f"Failed to save app index cache: {e}")

        return apps

    def resolve(self, query: str) -> Tuple[Optional[str], Optional[str], float]:
        """Fuzzy match query against indexed apps. Returns (app_name, path, score)."""
        query = query.lower().strip()
        if not self.index:
            self.load_or_rebuild_index()

        # Exact match
        if query in self.index:
            return query, self.index[query], 100.0

        # Fuzzy match
        choices = list(self.index.keys())
        if not choices:
            return None, None, 0.0

        match = process.extractOne(query, choices, scorer=fuzz.WRatio)
        if match:
            matched_name, score, _ = match
            return matched_name, self.index[matched_name], float(score)

        return None, None, 0.0


# App indexer instance
_indexer: Optional[AppIndexer] = None


def get_indexer() -> AppIndexer:
    global _indexer
    if _indexer is None:
        _indexer = AppIndexer()
    return _indexer


@tool(
    name="open_app",
    description="Open an installed desktop application by name (e.g. 'notepad', 'chrome', 'spotify', 'calculator').",
    params={"app_name": {"type": "string", "description": "The name of the application to open"}},
    risk="low",
)
def open_app(app_name: str) -> ToolResult:
    """Open an installed application."""
    indexer = get_indexer()
    matched_name, target_path, score = indexer.resolve(app_name)

    if not target_path or score < 60.0:
        return ToolResult(
            ok=False,
            message=f"I couldn't find an application named '{app_name}'.",
            data={"query": app_name, "score": score},
        )

    if score < 85.0:
        # Lower confidence match
        logger.info(f"Fuzzy match for '{app_name}' was '{matched_name}' with score {score:.1f}")

    try:
        if target_path.startswith("ms-settings:") or target_path.endswith(".exe"):
            os.startfile(target_path)
        elif os.path.exists(target_path):
            os.startfile(target_path)
        else:
            subprocess.Popen([target_path], shell=False)

        return ToolResult(
            ok=True,
            message=f"Opening {matched_name.title()}.",
            data={"app_name": matched_name, "path": target_path, "score": score},
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            message=f"Failed to open {matched_name}: {str(e)}",
            data={"error": str(e)},
        )


@tool(
    name="close_app",
    description="Close a running desktop application by name.",
    params={"app_name": {"type": "string", "description": "The name of the application to close"}},
    risk="medium",
)
def close_app(app_name: str) -> ToolResult:
    """Close running processes matching app name with robust termination."""
    import time

    indexer = get_indexer()
    matched_name, _, _ = indexer.resolve(app_name)
    target = (matched_name or app_name).lower().strip()

    # Also prepare the .exe variant for matching
    target_exe = target if target.endswith(".exe") else target + ".exe"

    closed = 0
    failed = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            p_name = proc.info["name"].lower()

            # Match: target substring in process name, or exact .exe match
            if not (target in p_name or p_name == target_exe):
                continue

            pid = proc.info["pid"]
            logger.info(f"Attempting to close process: {p_name} (PID {pid})")

            # Step 1: Try graceful terminate
            try:
                proc.terminate()
                proc.wait(timeout=3)
                closed += 1
                logger.info(f"Process {p_name} (PID {pid}) terminated gracefully.")
                continue
            except psutil.TimeoutExpired:
                logger.warning(f"Process {p_name} (PID {pid}) did not terminate in 3s, escalating to kill.")
            except psutil.NoSuchProcess:
                closed += 1
                continue

            # Step 2: Force kill
            try:
                proc.kill()
                proc.wait(timeout=3)
                closed += 1
                logger.info(f"Process {p_name} (PID {pid}) force-killed.")
                continue
            except psutil.TimeoutExpired:
                logger.warning(f"Process {p_name} (PID {pid}) survived kill(), trying taskkill.")
            except psutil.NoSuchProcess:
                closed += 1
                continue

            # Step 3: Last resort — Windows taskkill
            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True, timeout=5
                )
                time.sleep(0.5)
                if not psutil.pid_exists(pid):
                    closed += 1
                    logger.info(f"Process {p_name} (PID {pid}) closed via taskkill.")
                else:
                    failed += 1
                    logger.error(f"Process {p_name} (PID {pid}) could not be closed.")
            except Exception as e:
                failed += 1
                logger.error(f"taskkill failed for PID {pid}: {e}")

        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied:
            # Try taskkill as fallback for access-denied processes
            try:
                pid = proc.info["pid"]
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True, timeout=5
                )
                time.sleep(0.5)
                if not psutil.pid_exists(pid):
                    closed += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
            continue
        except Exception as e:
            logger.debug(f"Error checking process: {e}")
            continue

    if closed > 0:
        msg = f"Closed {app_name}."
        if failed > 0:
            msg += f" ({failed} instance(s) could not be closed.)"
        return ToolResult(
            ok=True,
            message=msg,
            data={"closed_count": closed, "failed_count": failed},
        )
    if failed > 0:
        return ToolResult(
            ok=False,
            message=f"Found {app_name} but could not close it (access denied or protected process).",
            data={"failed_count": failed},
        )
    return ToolResult(
        ok=False,
        message=f"No running instances of {app_name} were found.",
    )


@tool(
    name="list_running_apps",
    description="List active visible applications and processes running on the desktop.",
    params={},
    risk="low",
)
def list_running_apps() -> ToolResult:
    """List running desktop applications."""
    apps_found = set()
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info["name"]
            if name.lower().endswith(".exe") and name.lower() not in [
                "svchost.exe", "system", "registry", "services.exe", "lsass.exe",
                "explorer.exe", "dwm.exe", "conhost.exe", "runtimebroker.exe"
            ]:
                apps_found.add(Path(name).stem)
        except Exception:
            continue

    app_list = sorted(list(apps_found))[:10]
    summary = ", ".join(app_list) if app_list else "No third-party apps"
    return ToolResult(
        ok=True,
        message=f"Running applications include: {summary}.",
        data={"apps": app_list},
    )


@tool(
    name="refresh_apps",
    description="Rescan and rebuild the installed applications index.",
    params={},
    risk="low",
)
def refresh_apps() -> ToolResult:
    """Rebuild the local application index."""
    indexer = get_indexer()
    apps = indexer.rebuild_index()
    return ToolResult(
        ok=True,
        message=f"Application index refreshed. Found {len(apps)} apps.",
        data={"count": len(apps)},
    )
