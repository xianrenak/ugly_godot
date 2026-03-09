# ugly_godot

Utility scripts for building an obfuscated Godot project from a source project while keeping the exported game runnable.

## Included tool

### `obfuscate_gd.py`

Copies a Godot project, obfuscates internal GDScript identifiers, validates the copied project, and exports a macOS build.

Current behavior:

- Copies a source project into a destination project
- Obfuscates internal `*.gd` variables and regular function names
- Preserves Godot lifecycle callbacks such as `_ready` and `_process`
- Preserves string-based method references such as `call_deferred("...")`
- Reuses the source project's `export_presets.cfg`
- Rewrites export paths from the source project name to the destination project name
- Excludes `_obfuscation/*` from export output
- For macOS export:
  - uses the Godot editor version that matches the configured custom template when possible
  - exports an `.app`
  - copies runtime `.dylib` files into the app bundle
  - re-signs the app
  - builds the final `.dmg`

## Requirements

- Python 3
- A Godot editor binary installed locally
- A valid `export_presets.cfg` in the source project if you want export behavior to match the source project
- macOS export templates available if you export for macOS

## Usage

Example:

```bash
python3 obfuscate_gd.py \
  --src /Users/xrak/jams/ugly/frog_mini \
  --dst /Users/xrak/jams/ugly/frog_mini_ugly \
  --seed 1337 \
  --force \
  --validate \
  --export-macos
```

## Main options

- `--src`: source Godot project directory
- `--dst`: destination project directory
- `--seed`: stable seed for reproducible obfuscation
- `--force`: replace the destination project if it already exists
- `--mapping-out`: write the private symbol mapping to a custom path
- `--validate`: run Godot headless validation on the obfuscated project
- `--export-macos`: export the obfuscated project for macOS
- `--godot-bin`: explicitly provide the Godot editor binary
- `--export-path`: override the final export output path

## Output

Running the tool typically produces:

- an obfuscated Godot project at `--dst`
- a private mapping file at `--dst/_obfuscation/mapping.json`
- a macOS `.app` and `.dmg` in the export path configured by the project's `export_presets.cfg`

## Notes

- This tool currently focuses on safe identifier obfuscation, not maximum protection.
- It does not rename resource files, scene paths, or string constants.
- It is designed around the current Godot/GDScript workflow used in this repository.
