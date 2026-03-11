# ugly_godot

Utility scripts for building an obfuscated Godot project from a source project while keeping the exported game runnable.

The tool can now read defaults from per-project config files under `configs/`, so one tool checkout can drive multiple Godot projects.

## Included tool

### `obfuscate_gd.py`

Copies a Godot project, obfuscates internal GDScript identifiers, validates the copied project, and exports a macOS build.

Current behavior:

- Copies a source project into a destination project
- Obfuscates internal `*.gd` variables and regular function names
- Preserves Godot lifecycle callbacks such as `_ready` and `_process`
- Preserves string-based method references such as `call_deferred("...")`
- Reuses the source project's `export_presets.cfg`
- Leaves `export_presets.cfg` export paths unchanged by default
- Can optionally append a suffix to the export directory name via config
- Excludes `_obfuscation/*` from export output
- Reads project/export/runtime defaults from `configs/<project>.ini`
- For macOS export:
  - prefers the configured Godot editor binary from `ugly.ini` or `--godot-bin`
  - exports an `.app`
  - copies configured runtime `.dylib` files into the app bundle
  - re-signs the app
  - builds the final `.dmg`

## Requirements

- Python 3
- A Godot editor binary installed locally
- A valid `export_presets.cfg` in the source project if you want export behavior to match the source project
- macOS export templates available if you export for macOS

## Usage

Recommended config layout:

```ini
tools/
  obfuscate_gd.py
  configs/
    frog_mini.ini
    another_game.ini
```

Example `configs/frog_mini.ini`:

```ini
[project]
src = /Users/xrak/jams/ugly/frog_mini
dst = /Users/xrak/jams/ugly/frog_mini_ugly
seed = 1337
force = true
validate = true

[export]
macos = false
directory_suffix = _ugly

[godot]
bin = /Users/xrak/dev/godot_dev_4.4/bin/godot.macos.editor.arm64

[runtime]
dylibs =
    /Users/xrak/dev/godot_dev_4.4/bin/libsteam_api.dylib
```

Run with a named project config:

```bash
python3 obfuscate_gd.py --project frog_mini
```

Set `[export] macos = true` only for configs that should actually export. If it is omitted or set to `false`, the tool will stop after obfuscation and validation.

If `configs/` contains exactly one `*.ini`, `python3 obfuscate_gd.py` will use it automatically.

Or override specific values:

```bash
python3 obfuscate_gd.py \
  --project frog_mini \
  --seed 2026 \
  --export-path /Users/xrak/godot_export/frog_mini_ugly/frog_mini_ugly.dmg
```

## Main options

- `--project`: load `configs/<project>.ini`
- `--config`: path to an INI config file, overrides `--project`
- `--src`: source Godot project directory
- `--dst`: destination project directory
- `--seed`: stable seed for reproducible obfuscation
- `--force`: replace the destination project if it already exists
- `--mapping-out`: write the private symbol mapping to a custom path
- `--validate`: run Godot headless validation on the obfuscated project
- `--export-macos`: export the obfuscated project for macOS
- `--godot-bin`: explicitly provide the Godot editor binary
- `--export-path`: override the final export output path
- `--runtime-dylib`: append a runtime dylib to copy into the macOS app bundle

## Output

Running the tool typically produces:

- an obfuscated Godot project at `--dst`
- a private mapping file at `--dst/_obfuscation/mapping.json`
- a macOS `.app` and `.dmg` in the export path configured by the project's `export_presets.cfg`

If you want the obfuscated project to export into a different folder without replacing the full path, add this to the config:

```ini
[export]
directory_suffix = _ugly
```

Example:

- source preset path: `../../../godot_export/frog_mini/frog_mini.dmg`
- obfuscated preset path: `../../../godot_export/frog_mini_ugly/frog_mini.dmg`

This only changes the export directory name. The export file name itself stays the same unless you explicitly set `export_path`.

## Notes

- This tool currently focuses on safe identifier obfuscation, not maximum protection.
- It does not currently obfuscate arbitrary string constants or dynamic runtime-generated paths.
- It is designed around the current Godot/GDScript workflow used in this repository.
- CLI values override config file values.
