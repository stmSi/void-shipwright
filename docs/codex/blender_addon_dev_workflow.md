# Blender Add-on Development Workflow

For day-to-day iteration, do not reinstall the zip each time.

## Linked Install

Run this from the repository root:

```bash
blender --background --python tools/install_linked_addon.py
```

Then restart Blender once and enable `Void Shipwright`.

After that:

1. Edit files in this repository.
2. In Blender, press `F3`.
3. Run `Reload Scripts`.
4. Generate again.

Use the zip in `dist/` only when you want a packaged install.
