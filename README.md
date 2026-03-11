# ugly_godot

中文说明，英文版请见：[README_EN.md](./README_EN.md)

这个目录提供了一套用于 Godot 项目的混淆工具。目标是从一个源项目复制出一个可运行、可验证、可按需导出的混淆项目，而不是只做静态文本替换。

目前主工具是 [obfuscate_gd.py](obfuscate_gd.py)。

**工具能力**
- 复制一个源 Godot 项目到目标目录
- 混淆 `*.gd` 脚本中的内部标识符
- 保留 Godot 生命周期回调，例如 `_ready`、`_process`
- 保留字符串形式的方法引用，例如 `call_deferred("...")`
- 复用源项目的 `export_presets.cfg`
- 默认不修改 `export_presets.cfg` 中的 `export_path`
- 可以通过配置给导出目录追加后缀
- 自动排除 `_obfuscation/*`，避免私有映射被导出
- 支持从 `configs/<project>.ini` 读取项目配置
- macOS 导出时可额外复制运行时 `.dylib` 到 `.app` 包内

**要求**
- Python 3
- 本地可用的 Godot 编辑器二进制
- 如果需要导出，源项目应提供有效的 `export_presets.cfg`
- 如果需要导出 macOS，机器上需要可用的 macOS export templates

**推荐目录结构**

```text
ugly/
  frog_mini/
  tools/
    obfuscate_gd.py
    ugly.ini
```

如果你准备从头搭环境，推荐像下面这样组织目录：

```bash
mkdir -p ~/jams/ugly
cd ~/jams/ugly
git clone https://github.com/xianrenak/frog_mini.git
git clone https://github.com/xianrenak/ugly_godot.git tools
```

这样目录会变成：

```text
~/jams/ugly/
  frog_mini/
  tools/
    obfuscate_gd.py
    ugly.ini
    configs/
```

如果你不想用默认目录，也可以自己放到别的位置，只要把 ini 里的 `src`、`dst`、`godot.bin` 等路径改成对应的绝对路径即可。

**配置示例**

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

**使用方式**

按项目配置运行：

```bash
python3 obfuscate_gd.py --project frog_mini
```

如果 `configs/` 下只有一个 `*.ini`，也可以直接运行：

```bash
python3 obfuscate_gd.py
```

覆盖部分参数时可以这样写：

```bash
python3 obfuscate_gd.py \
  --project frog_mini \
  --seed 2026 \
  --export-path /Users/xrak/godot_export/frog_mini_ugly/frog_mini_ugly.dmg
```

**测试流程**

建议至少做三类测试。

1. 先验证源项目本身能正常打开：

```bash
/Users/xrak/dev/godot_dev_4.4/bin/godot.macos.editor.arm64 \
  --headless \
  --path /Users/xrak/jams/ugly/frog_mini \
  --quit
```

2. 运行混淆工具，生成 `frog_mini_ugly`：

```bash
cd /Users/xrak/jams/ugly/tools
python3 obfuscate_gd.py
```

3. 再验证混淆后的项目：

```bash
/Users/xrak/dev/godot_dev_4.4/bin/godot.macos.editor.arm64 \
  --headless \
  --path /Users/xrak/jams/ugly/frog_mini_ugly \
  --quit
```

如果你要测试导出，把配置里的 `[export] macos` 改成 `true`，然后再运行一次工具。导出完成后，检查生成目录里是否有 `.app` 或 `.dmg`。

**导出行为**
- 默认不会自动导出
- 只有配置里显式写了 `[export] macos = true`，或者命令行显式传了 `--export-macos`，才会执行 macOS 导出
- `directory_suffix` 只会修改导出目录名，不会修改导出文件名

例如源项目 preset 里是：

```text
../../../godot_export/frog_mini/frog_mini.dmg
```

如果配置里写：

```ini
[export]
directory_suffix = _ugly
```

混淆项目里的导出路径会变成：

```text
../../../godot_export/frog_mini_ugly/frog_mini.dmg
```

如果你想完全指定导出路径，直接使用 `export_path` 即可。

**主要参数**
- `--project`: 读取 `configs/<project>.ini`
- `--config`: 显式指定 ini 文件路径，优先级高于 `--project`
- `--src`: 源 Godot 项目目录
- `--dst`: 输出项目目录
- `--seed`: 稳定种子，用于复现混淆结果
- `--force`: 目标目录已存在时覆盖
- `--mapping-out`: 指定私有映射文件输出路径
- `--validate`: 对混淆后的项目做 Godot 校验
- `--export-macos`: 执行 macOS 导出
- `--godot-bin`: 显式指定 Godot 编辑器路径
- `--export-path`: 显式指定最终导出产物路径
- `--runtime-dylib`: 追加需要复制进 `.app` 的运行时动态库

**产出**
- 一个混淆后的 Godot 项目目录，位于 `--dst`
- 一个私有映射文件，默认位于 `--dst/_obfuscation/mapping.json`
- 如果开启导出，会在配置的导出路径生成 `.app` 或 `.dmg`

**说明**
- 当前工具重点是“尽量安全地混淆”，不是“最大强度保护”
- 目前不处理任意字符串常量混淆，也不保证动态生成路径的场景都能自动改写
- CLI 参数优先级高于配置文件
