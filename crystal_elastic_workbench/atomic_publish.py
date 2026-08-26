"""Transactional publication of a small, same-directory file set."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class _PublishRecord:
    staged: Path
    target: Path
    backup: Path
    had_old: bool
    installed: bool = False


def path_exists(path: Path) -> bool:
    """Return whether a path exists, including a dangling symlink."""

    return path.exists() or path.is_symlink()


def _remove_entry(path: Path) -> None:
    if not path_exists(path):
        return
    if path.is_dir() and not path.is_symlink():
        raise IsADirectoryError(f"Refusing to remove a directory while rolling back an output file: {path}")
    path.unlink()


def _restore_entry(backup: Path, target: Path) -> None:
    try:
        os.replace(backup, target)
    except OSError as replace_error:
        try:
            _remove_entry(target)
            os.rename(backup, target)
        except OSError as rename_error:
            raise rename_error from replace_error


def _validate_pairs(pairs: Sequence[tuple[Path, Path]]) -> tuple[Path, Path]:
    staging_dir = pairs[0][0].parent
    output_dir = pairs[0][1].parent
    targets: set[Path] = set()
    for staged, target in pairs:
        if staged.parent != staging_dir:
            raise ValueError("All staged files must share one directory.")
        if target.parent != output_dir:
            raise ValueError("All published files must share one output directory.")
        if target in targets:
            raise ValueError(f"Duplicate publish target: {target}")
        targets.add(target)
        if not staged.is_file() or staged.is_symlink():
            raise FileNotFoundError(f"Staged output is missing or is not a regular file: {staged}")
        if path_exists(target) and target.is_dir() and not target.is_symlink():
            raise IsADirectoryError(f"Refusing to replace a directory with an output file: {target}")
    return staging_dir, output_dir


def publish_staged_files(pairs: Sequence[tuple[Path, Path]]) -> None:
    """Publish a complete file set and restore prior entries if publication fails.

    Existing targets are moved as directory entries, so symlink and hard-link
    destinations are never opened for writing. Only the explicit targets are
    touched; unrelated files in the output directory remain in place.
    """

    if not pairs:
        return
    staging_dir, output_dir = _validate_pairs(pairs)
    output_preexisted = path_exists(output_dir)
    if output_preexisted and not output_dir.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = staging_dir / ".previous"
    records: list[_PublishRecord] = []
    try:
        for staged, target in pairs:
            had_old = path_exists(target)
            backup = backup_dir / target.name
            record = _PublishRecord(staged, target, backup, had_old)
            records.append(record)
            if had_old:
                backup_dir.mkdir(parents=True, exist_ok=True)
                os.replace(target, backup)

        for record in records:
            os.replace(record.staged, record.target)
            record.installed = True
    except BaseException as publish_error:
        rollback_errors: list[OSError] = []
        for record in reversed(records):
            if record.installed or not path_exists(record.staged):
                try:
                    _remove_entry(record.target)
                except OSError as error:
                    rollback_errors.append(error)
            if record.had_old and path_exists(record.backup):
                try:
                    _restore_entry(record.backup, record.target)
                except OSError as error:
                    rollback_errors.append(error)
        if not output_preexisted:
            try:
                output_dir.rmdir()
            except OSError:
                pass
        if rollback_errors and hasattr(publish_error, "add_note"):
            publish_error.add_note(
                "Rollback also encountered: "
                + "; ".join(str(error) for error in rollback_errors)
            )
        raise
