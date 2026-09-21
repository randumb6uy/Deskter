"""File search and directory opening tools restricted to allowed roots."""

import os
from pathlib import Path
from typing import List, Optional
from jarvis.actions.registry import ToolResult, tool


@tool(
    name="open_folder",
    description="Open a folder in Windows File Explorer (e.g. 'Downloads', 'Documents', 'Desktop', or a specific subfolder).",
    params={"path": {"type": "string", "description": "Folder name or path: 'downloads', 'documents', 'desktop', or subfolder"}},
    risk="low",
)
def open_folder(path: str) -> ToolResult:
    """Open folder in Windows Explorer."""
    path_lower = path.lower().strip()
    home = Path.home()

    target_map = {
        "downloads": home / "Downloads",
        "download": home / "Downloads",
        "documents": home / "Documents",
        "document": home / "Documents",
        "desktop": home / "Desktop",
        "pictures": home / "Pictures",
        "music": home / "Music",
        "videos": home / "Videos",
    }

    if path_lower in target_map:
        target_path = target_map[path_lower]
    else:
        # Resolve path
        target_path = Path(os.path.expanduser(os.path.expandvars(path))).resolve()

    if not target_path.exists():
        return ToolResult(ok=False, message=f"The folder '{path}' does not exist.")

    if not target_path.is_dir():
        target_path = target_path.parent

    try:
        os.startfile(str(target_path))
        return ToolResult(
            ok=True,
            message=f"Opening {target_path.name or 'folder'}.",
            data={"path": str(target_path)},
        )
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to open folder: {e}")


@tool(
    name="find_file",
    description="Search for a file by name within Documents, Downloads, or Desktop.",
    params={
        "filename": {"type": "string", "description": "Name or pattern of the file to search for"},
        "root": {"type": "string", "description": "Optional search location: 'documents', 'downloads', or 'desktop'", "required": False},
    },
    risk="low",
)
def find_file(filename: str, root: Optional[str] = None) -> ToolResult:
    """Search for matching files in allowed directories."""
    home = Path.home()
    roots = [home / "Documents", home / "Downloads", home / "Desktop"]

    if root:
        r_lower = root.lower().strip()
        if r_lower in ["documents", "doc", "docs"]:
            roots = [home / "Documents"]
        elif r_lower in ["downloads", "download"]:
            roots = [home / "Downloads"]
        elif r_lower in ["desktop"]:
            roots = [home / "Desktop"]

    matches: List[Path] = []
    target_query = filename.lower().strip()

    for search_root in roots:
        if not search_root.exists():
            continue
        try:
            for dirpath, _, filenames in os.walk(search_root):
                for f in filenames:
                    if target_query in f.lower():
                        matches.append(Path(dirpath) / f)
                        if len(matches) >= 5:
                            break
                if len(matches) >= 5:
                    break
        except Exception:
            continue

    if not matches:
        return ToolResult(
            ok=False,
            message=f"No files matching '{filename}' were found in your standard folders.",
        )

    file_names = [m.name for m in matches]
    summary = ", ".join(file_names)
    return ToolResult(
        ok=True,
        message=f"Found {len(matches)} matching files: {summary}.",
        data={"files": [str(m) for m in matches]},
    )
