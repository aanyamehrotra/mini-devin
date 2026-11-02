"""Validate generated paths before writing any project files."""

from pathlib import Path, PurePosixPath, PureWindowsPath


def resolve_project_files(project_dir: Path, files) -> list[tuple[Path, str]]:
    root = project_dir.resolve()
    resolved = []
    seen = set()
    for file in files:
        path = file.path
        posix = PurePosixPath(path)
        windows = PureWindowsPath(path)
        if (
            not path.strip()
            or "\x00" in path
            or "\\" in path
            or posix.is_absolute()
            or windows.drive
            or ".." in posix.parts
            or not posix.parts
        ):
            raise ValueError(f"Invalid generated file path: {path!r}")
        target = (root / path).resolve()
        if not target.is_relative_to(root) or target == root:
            raise ValueError(f"Generated file escapes workspace: {path!r}")
        if target in seen:
            raise ValueError(f"Duplicate generated file path: {path!r}")
        seen.add(target)
        resolved.append((target, file.content))
    for target, _ in resolved:
        if any(parent in seen for parent in target.parents):
            raise ValueError("Generated paths conflict as file and directory")
    return resolved
