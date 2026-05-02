"""Install Void Shipwright into Blender as a linked development add-on.

Run with Blender, not system Python:

    blender --background --python tools/install_linked_addon.py

This creates a symlink from Blender's user add-ons directory to this repo's
`void_shipwright` folder. After that, edit files in this repo and use
Blender's `F3 > Reload Scripts` instead of reinstalling a zip.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import bpy


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "void_shipwright"
    addons_dir = Path(bpy.utils.user_resource("SCRIPTS", path="addons", create=True))
    target = addons_dir / "void_shipwright"

    if not source.exists():
        raise RuntimeError(f"Missing source add-on folder: {source}")

    if target.is_symlink():
        if target.resolve() == source:
            print(f"Void Shipwright already linked: {target} -> {source}")
            return
        target.unlink()
    elif target.exists():
        backup = target.with_name("void_shipwright.backup")
        if backup.exists():
            shutil.rmtree(backup)
        target.rename(backup)
        print(f"Moved existing add-on to backup: {backup}")

    target.symlink_to(source, target_is_directory=True)
    print(f"Linked Void Shipwright: {target} -> {source}")
    print("Restart Blender once, enable the add-on, then use F3 > Reload Scripts after code changes.")


if __name__ == "__main__":
    main()
