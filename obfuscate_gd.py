#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


TOP_LEVEL_SYMBOL_RE = re.compile(
    r"^\s*(?:@[\w_]+(?:\([^)]*\))?\s*)*(?:static\s+)?(var|const)\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)
FUNC_DEF_RE = re.compile(
    r"^\s*(?:static\s+)?func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)"
)
LOCAL_VAR_RE = re.compile(r"\b(?:var|const)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
FOR_VAR_RE = re.compile(r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b")
STRING_METHOD_REF_PATTERNS = [
    re.compile(r'\bcall_deferred\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'\bcall\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'\bcallv\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'\bhas_method\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'\bCallable\(\s*self\s*,\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
]
KEYWORDS = {
    "and",
    "as",
    "assert",
    "await",
    "break",
    "breakpoint",
    "class",
    "class_name",
    "const",
    "continue",
    "elif",
    "else",
    "enum",
    "extends",
    "false",
    "for",
    "func",
    "if",
    "in",
    "is",
    "match",
    "namespace",
    "not",
    "null",
    "or",
    "pass",
    "preload",
    "return",
    "self",
    "signal",
    "static",
    "super",
    "true",
    "var",
    "void",
    "when",
    "while",
    "yield",
}
ENGINE_CALLBACKS = {
    "_draw",
    "_enter_tree",
    "_exit_tree",
    "_get",
    "_get_configuration_warnings",
    "_get_drag_data",
    "_get_minimum_size",
    "_get_property_list",
    "_gui_input",
    "_init",
    "_input",
    "_make_custom_tooltip",
    "_notification",
    "_physics_process",
    "_process",
    "_ready",
    "_set",
    "_shortcut_input",
    "_to_string",
    "_unhandled_input",
    "_unhandled_key_input",
}
MACOS_PRESET_TEMPLATE = """[preset.0]

name="macOS"
platform="macOS"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="builds/{project_name}.dmg"
patches=PackedStringArray()
encryption_include_filters=""
encryption_exclude_filters=""
seed=0
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.0.options]

export/distribution_type=1
binary_format/architecture="universal"
custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=1
application/icon=""
application/icon_interpolation=4
application/bundle_identifier="{bundle_identifier}"
application/signature=""
application/app_category="Games"
application/short_version=""
application/version=""
application/copyright=""
application/copyright_localized={{}}
application/min_macos_version_x86_64="10.12"
application/min_macos_version_arm64="11.00"
application/export_angle=0
display/high_res=true
application/additional_plist_content=""
xcode/platform_build="14C18"
xcode/sdk_version="13.1"
xcode/sdk_build="22C55"
xcode/sdk_name="macosx13.1"
xcode/xcode_version="1420"
xcode/xcode_build="14C18"
codesign/codesign=3
codesign/installer_identity=""
codesign/apple_team_id=""
codesign/identity=""
codesign/entitlements/custom_file=""
codesign/entitlements/allow_jit_code_execution=false
codesign/entitlements/allow_unsigned_executable_memory=false
codesign/entitlements/allow_dyld_environment_variables=false
codesign/entitlements/disable_library_validation=false
codesign/entitlements/audio_input=false
codesign/entitlements/camera=false
codesign/entitlements/location=false
codesign/entitlements/address_book=false
codesign/entitlements/calendars=false
codesign/entitlements/photos_library=false
codesign/entitlements/apple_events=false
codesign/entitlements/debugging=false
codesign/entitlements/app_sandbox/enabled=false
codesign/entitlements/app_sandbox/network_server=false
codesign/entitlements/app_sandbox/network_client=false
codesign/entitlements/app_sandbox/device_usb=false
codesign/entitlements/app_sandbox/device_bluetooth=false
codesign/entitlements/app_sandbox/files_downloads=0
codesign/entitlements/app_sandbox/files_pictures=0
codesign/entitlements/app_sandbox/files_music=0
codesign/entitlements/app_sandbox/files_movies=0
codesign/entitlements/app_sandbox/files_user_selected=0
codesign/entitlements/app_sandbox/helper_executables=[]
codesign/entitlements/additional=""
codesign/custom_options=PackedStringArray()
notarization/notarization=0
privacy/microphone_usage_description=""
privacy/microphone_usage_description_localized={{}}
privacy/camera_usage_description=""
privacy/camera_usage_description_localized={{}}
privacy/location_usage_description=""
privacy/location_usage_description_localized={{}}
privacy/address_book_usage_description=""
privacy/address_book_usage_description_localized={{}}
privacy/calendar_usage_description=""
privacy/calendar_usage_description_localized={{}}
privacy/photos_library_usage_description=""
privacy/photos_library_usage_description_localized={{}}
privacy/desktop_folder_usage_description=""
privacy/desktop_folder_usage_description_localized={{}}
privacy/documents_folder_usage_description=""
privacy/documents_folder_usage_description_localized={{}}
privacy/downloads_folder_usage_description=""
privacy/downloads_folder_usage_description_localized={{}}
privacy/network_volumes_usage_description=""
privacy/network_volumes_usage_description_localized={{}}
privacy/removable_volumes_usage_description=""
privacy/removable_volumes_usage_description_localized={{}}
privacy/tracking_enabled=false
privacy/tracking_domains=PackedStringArray()
privacy/collected_data/name/collected=false
privacy/collected_data/name/linked_to_user=false
privacy/collected_data/name/used_for_tracking=false
privacy/collected_data/name/collection_purposes=0
privacy/collected_data/email_address/collected=false
privacy/collected_data/email_address/linked_to_user=false
privacy/collected_data/email_address/used_for_tracking=false
privacy/collected_data/email_address/collection_purposes=0
privacy/collected_data/phone_number/collected=false
privacy/collected_data/phone_number/linked_to_user=false
privacy/collected_data/phone_number/used_for_tracking=false
privacy/collected_data/phone_number/collection_purposes=0
privacy/collected_data/physical_address/collected=false
privacy/collected_data/physical_address/linked_to_user=false
privacy/collected_data/physical_address/used_for_tracking=false
privacy/collected_data/physical_address/collection_purposes=0
privacy/collected_data/other_contact_info/collected=false
privacy/collected_data/other_contact_info/linked_to_user=false
privacy/collected_data/other_contact_info/used_for_tracking=false
privacy/collected_data/other_contact_info/collection_purposes=0
privacy/collected_data/health/collected=false
privacy/collected_data/health/linked_to_user=false
privacy/collected_data/health/used_for_tracking=false
privacy/collected_data/health/collection_purposes=0
privacy/collected_data/fitness/collected=false
privacy/collected_data/fitness/linked_to_user=false
privacy/collected_data/fitness/used_for_tracking=false
privacy/collected_data/fitness/collection_purposes=0
privacy/collected_data/payment_info/collected=false
privacy/collected_data/payment_info/linked_to_user=false
privacy/collected_data/payment_info/used_for_tracking=false
privacy/collected_data/payment_info/collection_purposes=0
privacy/collected_data/credit_info/collected=false
privacy/collected_data/credit_info/linked_to_user=false
privacy/collected_data/credit_info/used_for_tracking=false
privacy/collected_data/credit_info/collection_purposes=0
privacy/collected_data/other_financial_info/collected=false
privacy/collected_data/other_financial_info/linked_to_user=false
privacy/collected_data/other_financial_info/used_for_tracking=false
privacy/collected_data/other_financial_info/collection_purposes=0
privacy/collected_data/precise_location/collected=false
privacy/collected_data/precise_location/linked_to_user=false
privacy/collected_data/precise_location/used_for_tracking=false
privacy/collected_data/precise_location/collection_purposes=0
privacy/collected_data/coarse_location/collected=false
privacy/collected_data/coarse_location/linked_to_user=false
privacy/collected_data/coarse_location/used_for_tracking=false
privacy/collected_data/coarse_location/collection_purposes=0
privacy/collected_data/sensitive_info/collected=false
privacy/collected_data/sensitive_info/linked_to_user=false
privacy/collected_data/sensitive_info/used_for_tracking=false
privacy/collected_data/sensitive_info/collection_purposes=0
privacy/collected_data/contacts/collected=false
privacy/collected_data/contacts/linked_to_user=false
privacy/collected_data/contacts/used_for_tracking=false
privacy/collected_data/contacts/collection_purposes=0
privacy/collected_data/emails_or_text_messages/collected=false
privacy/collected_data/emails_or_text_messages/linked_to_user=false
privacy/collected_data/emails_or_text_messages/used_for_tracking=false
privacy/collected_data/emails_or_text_messages/collection_purposes=0
privacy/collected_data/photos_or_videos/collected=false
privacy/collected_data/photos_or_videos/linked_to_user=false
privacy/collected_data/photos_or_videos/used_for_tracking=false
privacy/collected_data/photos_or_videos/collection_purposes=0
privacy/collected_data/audio_data/collected=false
privacy/collected_data/audio_data/linked_to_user=false
privacy/collected_data/audio_data/used_for_tracking=false
privacy/collected_data/audio_data/collection_purposes=0
privacy/collected_data/gameplay_content/collected=false
privacy/collected_data/gameplay_content/linked_to_user=false
privacy/collected_data/gameplay_content/used_for_tracking=false
privacy/collected_data/gameplay_content/collection_purposes=0
privacy/collected_data/customer_support/collected=false
privacy/collected_data/customer_support/linked_to_user=false
privacy/collected_data/customer_support/used_for_tracking=false
privacy/collected_data/customer_support/collection_purposes=0
privacy/collected_data/other_user_content/collected=false
privacy/collected_data/other_user_content/linked_to_user=false
privacy/collected_data/other_user_content/used_for_tracking=false
privacy/collected_data/other_user_content/collection_purposes=0
privacy/collected_data/browsing_history/collected=false
privacy/collected_data/browsing_history/linked_to_user=false
privacy/collected_data/browsing_history/used_for_tracking=false
privacy/collected_data/browsing_history/collection_purposes=0
privacy/collected_data/search_hhistory/collected=false
privacy/collected_data/search_hhistory/linked_to_user=false
privacy/collected_data/search_hhistory/used_for_tracking=false
privacy/collected_data/search_hhistory/collection_purposes=0
privacy/collected_data/user_id/collected=false
privacy/collected_data/user_id/linked_to_user=false
privacy/collected_data/user_id/used_for_tracking=false
privacy/collected_data/user_id/collection_purposes=0
privacy/collected_data/device_id/collected=false
privacy/collected_data/device_id/linked_to_user=false
privacy/collected_data/device_id/used_for_tracking=false
privacy/collected_data/device_id/collection_purposes=0
privacy/collected_data/purchase_history/collected=false
privacy/collected_data/purchase_history/linked_to_user=false
privacy/collected_data/purchase_history/used_for_tracking=false
privacy/collected_data/purchase_history/collection_purposes=0
privacy/collected_data/product_interaction/collected=false
privacy/collected_data/product_interaction/linked_to_user=false
privacy/collected_data/product_interaction/used_for_tracking=false
privacy/collected_data/product_interaction/collection_purposes=0
privacy/collected_data/advertising_data/collected=false
privacy/collected_data/advertising_data/linked_to_user=false
privacy/collected_data/advertising_data/used_for_tracking=false
privacy/collected_data/advertising_data/collection_purposes=0
privacy/collected_data/other_usage_data/collected=false
privacy/collected_data/other_usage_data/linked_to_user=false
privacy/collected_data/other_usage_data/used_for_tracking=false
privacy/collected_data/other_usage_data/collection_purposes=0
privacy/collected_data/crash_data/collected=false
privacy/collected_data/crash_data/linked_to_user=false
privacy/collected_data/crash_data/used_for_tracking=false
privacy/collected_data/crash_data/collection_purposes=0
privacy/collected_data/performance_data/collected=false
privacy/collected_data/performance_data/linked_to_user=false
privacy/collected_data/performance_data/used_for_tracking=false
privacy/collected_data/performance_data/collection_purposes=0
privacy/collected_data/other_diagnostic_data/collected=false
privacy/collected_data/other_diagnostic_data/linked_to_user=false
privacy/collected_data/other_diagnostic_data/used_for_tracking=false
privacy/collected_data/other_diagnostic_data/collection_purposes=0
"""


@dataclass
class Token:
    kind: str
    text: str
    line: int


@dataclass
class FunctionInfo:
    name: str
    start_line: int
    end_line: int
    params: dict[str, str] = field(default_factory=dict)
    locals: dict[str, str] = field(default_factory=dict)


@dataclass
class ScriptInfo:
    path: Path
    rel_path: str
    text: str
    script_symbols: dict[str, str] = field(default_factory=dict)
    functions: list[FunctionInfo] = field(default_factory=list)

    def scope_for_line(self, line: int) -> FunctionInfo | None:
        for function in self.functions:
            if function.start_line <= line <= function.end_line:
                return function
        return None


class NameFactory:
    def __init__(self, seed: int):
        self.seed = seed

    def build(self, namespace: str, key: str, used: set[str]) -> str:
        digest = hashlib.sha1(f"{self.seed}:{namespace}:{key}".encode("utf-8")).hexdigest()
        for width in range(8, len(digest) + 1):
            candidate = f"{namespace}_{digest[:width]}"
            if candidate not in used and candidate not in KEYWORDS:
                used.add(candidate)
                return candidate
        raise RuntimeError(f"Could not generate unique symbol for {namespace}:{key}")


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    line = 1
    length = len(text)

    while i < length:
        ch = text[i]

        if ch == "\n":
            tokens.append(Token("newline", ch, line))
            line += 1
            i += 1
            continue

        if ch in " \t\r":
            start = i
            while i < length and text[i] in " \t\r":
                i += 1
            tokens.append(Token("ws", text[start:i], line))
            continue

        if ch == "#":
            start = i
            while i < length and text[i] != "\n":
                i += 1
            tokens.append(Token("comment", text[start:i], line))
            continue

        if text.startswith('"""', i) or text.startswith("'''", i):
            quote = text[i : i + 3]
            start = i
            i += 3
            while i < length and not text.startswith(quote, i):
                if text[i] == "\\" and i + 1 < length:
                    i += 2
                else:
                    if text[i] == "\n":
                        line += 1
                    i += 1
            i = min(length, i + 3)
            tokens.append(Token("string", text[start:i], line))
            continue

        if ch in {'"', "'"}:
            quote = ch
            start = i
            i += 1
            while i < length:
                if text[i] == "\\" and i + 1 < length:
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                if text[i] == "\n":
                    line += 1
                i += 1
            tokens.append(Token("string", text[start:i], line))
            continue

        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < length and (text[i].isalnum() or text[i] == "_"):
                i += 1
            tokens.append(Token("ident", text[start:i], line))
            continue

        if ch.isdigit():
            start = i
            i += 1
            while i < length and (text[i].isalnum() or text[i] in "._xX"):
                i += 1
            tokens.append(Token("number", text[start:i], line))
            continue

        tokens.append(Token("symbol", ch, line))
        i += 1

    return tokens


def mask_non_code(line: str) -> str:
    masked = []
    for token in tokenize(line):
        if token.kind in {"ident", "number", "symbol", "ws", "newline"}:
            masked.append(token.text)
        else:
            masked.append(" " * len(token.text))
    return "".join(masked)


def split_params(raw: str) -> list[str]:
    parts: list[str] = []
    current = []
    depth = 0
    for ch in raw:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def param_name(part: str) -> str | None:
    if part.startswith("..."):
        return None
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\b", part)
    return match.group(1) if match else None


def discover_scripts(project_dir: Path) -> list[ScriptInfo]:
    scripts: list[ScriptInfo] = []
    for path in sorted(project_dir.rglob("*.gd")):
        rel_path = path.relative_to(project_dir).as_posix()
        scripts.append(ScriptInfo(path=path, rel_path=rel_path, text=path.read_text(encoding="utf-8")))
    return scripts


def leading_indent(raw_line: str) -> int:
    return len(raw_line) - len(raw_line.lstrip(" \t"))


def discover_protected_function_names(text: str) -> set[str]:
    protected: set[str] = set()
    for pattern in STRING_METHOD_REF_PATTERNS:
        protected.update(pattern.findall(text))
    return protected


def discover_structure(scripts: list[ScriptInfo], name_factory: NameFactory) -> tuple[dict[str, str], dict]:
    global_function_names: set[str] = set()
    protected_function_names: set[str] = set()

    for script in scripts:
        lines = script.text.splitlines()
        function_headers: list[tuple[int, str, str]] = []
        protected_function_names.update(discover_protected_function_names(script.text))

        for line_number, raw_line in enumerate(lines, start=1):
            masked = mask_non_code(raw_line)
            if leading_indent(raw_line) == 0 and (match := FUNC_DEF_RE.match(masked)):
                function_name = match.group(1)
                if function_name not in ENGINE_CALLBACKS:
                    global_function_names.add(function_name)
                function_headers.append((line_number, function_name, match.group(2)))

        end_lines = [line_no for line_no, _, _ in function_headers[1:]] + [len(lines) + 1]
        for (line_no, function_name, params_raw), next_line_no in zip(function_headers, end_lines):
            script.functions.append(
                FunctionInfo(name=function_name, start_line=line_no, end_line=next_line_no - 1)
            )
            function = script.functions[-1]
            for part in split_params(params_raw):
                name = param_name(part)
                if name:
                    function.params[name] = ""

    used_global_names = set(KEYWORDS) | ENGINE_CALLBACKS
    function_map: dict[str, str] = {}
    script_symbol_map_manifest: dict[str, dict] = {}

    eligible_function_names = {
        name
        for name in global_function_names
        if name not in ENGINE_CALLBACKS and name not in protected_function_names
    }

    for function_name in sorted(eligible_function_names):
        if function_name in KEYWORDS:
            continue
        function_map[function_name] = name_factory.build("fn", function_name, used_global_names)

    for script in scripts:
        used_script_names = set(KEYWORDS) | set(function_map.values()) | ENGINE_CALLBACKS
        lines = script.text.splitlines()

        for line_number, raw_line in enumerate(lines, start=1):
            masked = mask_non_code(raw_line)
            if leading_indent(raw_line) == 0 and (match := TOP_LEVEL_SYMBOL_RE.match(masked)):
                symbol_name = match.group(2)
                if symbol_name not in KEYWORDS:
                    script.script_symbols[symbol_name] = name_factory.build(
                        "sv",
                        f"{script.rel_path}:{symbol_name}",
                        used_script_names,
                    )

        for function in script.functions:
            used_local_names = used_script_names | set(script.script_symbols.values())
            if function.name in function_map:
                used_local_names.add(function_map[function.name])

            for param in sorted(function.params):
                function.params[param] = name_factory.build(
                    "pa",
                    f"{script.rel_path}:{function.name}:{function.start_line}:param:{param}",
                    used_local_names,
                )

            for line_number in range(function.start_line, function.end_line + 1):
                masked = mask_non_code(lines[line_number - 1])
                for match in LOCAL_VAR_RE.finditer(masked):
                    symbol_name = match.group(1)
                    if symbol_name in KEYWORDS or symbol_name in function.params:
                        continue
                    function.locals.setdefault(
                        symbol_name,
                        name_factory.build(
                            "lv",
                            f"{script.rel_path}:{function.name}:{function.start_line}:local:{symbol_name}",
                            used_local_names,
                        ),
                    )
                for match in FOR_VAR_RE.finditer(masked):
                    symbol_name = match.group(1)
                    if symbol_name in KEYWORDS or symbol_name in function.params:
                        continue
                    function.locals.setdefault(
                        symbol_name,
                        name_factory.build(
                            "lv",
                            f"{script.rel_path}:{function.name}:{function.start_line}:for:{symbol_name}",
                            used_local_names,
                        ),
                    )

        script_symbol_map_manifest[script.rel_path] = {
            "script_symbols": script.script_symbols,
            "functions": {
                function.name: {
                    "start_line": function.start_line,
                    "params": function.params,
                    "locals": function.locals,
                }
                for function in script.functions
            },
        }

    return function_map, script_symbol_map_manifest


def previous_significant(tokens: list[Token], index: int) -> Token | None:
    for cursor in range(index - 1, -1, -1):
        if tokens[cursor].kind not in {"ws", "newline", "comment"}:
            return tokens[cursor]
    return None


def next_significant(tokens: list[Token], index: int) -> Token | None:
    for cursor in range(index + 1, len(tokens)):
        if tokens[cursor].kind not in {"ws", "newline", "comment"}:
            return tokens[cursor]
    return None


def second_previous_significant(tokens: list[Token], index: int) -> Token | None:
    seen = 0
    for cursor in range(index - 1, -1, -1):
        if tokens[cursor].kind in {"ws", "newline", "comment"}:
            continue
        seen += 1
        if seen == 2:
            return tokens[cursor]
    return None


def replace_identifiers(script: ScriptInfo, function_map: dict[str, str]) -> str:
    tokens = tokenize(script.text)
    rewritten: list[str] = []

    for index, token in enumerate(tokens):
        if token.kind != "ident":
            rewritten.append(token.text)
            continue

        replacement = None
        scope = script.scope_for_line(token.line)
        prev_token = previous_significant(tokens, index)
        next_token = next_significant(tokens, index)
        prev_prev = second_previous_significant(tokens, index)
        token_text = token.text

        if prev_token and prev_token.text == ".":
            if token_text in function_map and next_token and next_token.text == "(":
                replacement = function_map[token_text]
            elif prev_prev and prev_prev.text == "self" and token_text in script.script_symbols:
                replacement = script.script_symbols[token_text]
        else:
            if scope and token_text in scope.params:
                replacement = scope.params[token_text]
            elif scope and token_text in scope.locals:
                replacement = scope.locals[token_text]
            elif token_text in script.script_symbols:
                replacement = script.script_symbols[token_text]
            elif token_text in function_map:
                replacement = function_map[token_text]

        rewritten.append(replacement or token_text)

    return "".join(rewritten)


def build_bundle_identifier(project_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", project_name.lower())
    if not normalized:
        normalized = "game"
    return f"com.xrak.{normalized}"


def rewrite_export_paths(project_dir: Path, src_project_name: str, dst_project_name: str) -> None:
    preset_path = project_dir / "export_presets.cfg"
    if not preset_path.exists():
        return

    text = preset_path.read_text(encoding="utf-8")

    def replace_export_path(match: re.Match[str]) -> str:
        quote = match.group(1)
        raw_path = match.group(2)
        updated_path = raw_path.replace(src_project_name, dst_project_name)
        return f'export_path={quote}{updated_path}{quote}'

    updated = re.sub(r'export_path=(["\'])(.*?)\1', replace_export_path, text)
    if updated != text:
        preset_path.write_text(updated, encoding="utf-8")


def ensure_export_excludes(project_dir: Path, pattern: str = "_obfuscation/*") -> None:
    preset_path = project_dir / "export_presets.cfg"
    if not preset_path.exists():
        return

    lines = preset_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []

    for raw_line in lines:
        if raw_line.startswith("exclude_filter="):
            raw_value = raw_line.split("=", 1)[1].strip().strip('"')
            parts = [part for part in raw_value.split(",") if part]
            if pattern not in parts:
                parts.append(pattern)
            joined = ",".join(parts)
            updated_lines.append(f'exclude_filter="{joined}"')
        else:
            updated_lines.append(raw_line)

    preset_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def export_path_from_presets(project_dir: Path, preset_name: str) -> Path | None:
    preset_path = project_dir / "export_presets.cfg"
    if not preset_path.exists():
        return None

    current_section = None
    current_name = None
    current_export_path = None

    for raw_line in preset_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("[preset.") and line.endswith("]") and ".options" not in line:
            if current_name == preset_name and current_export_path:
                return (project_dir / current_export_path).resolve()
            current_section = line
            current_name = None
            current_export_path = None
            continue

        if current_section is None:
            continue

        if line.startswith("name="):
            current_name = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("export_path="):
            current_export_path = line.split("=", 1)[1].strip().strip('"')

    if current_name == preset_name and current_export_path:
        return (project_dir / current_export_path).resolve()

    return None


def custom_template_paths(project_dir: Path) -> list[Path]:
    preset_path = project_dir / "export_presets.cfg"
    if not preset_path.exists():
        return []

    templates: list[Path] = []
    for raw_line in preset_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("custom_template/debug=") or line.startswith("custom_template/release="):
            value = line.split("=", 1)[1].strip().strip('"')
            if value:
                templates.append(Path(value))
    return templates


def project_display_name(project_dir: Path) -> str:
    name = project_dir.name
    project_file = project_dir / "project.godot"
    if project_file.exists():
        for raw_line in project_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith('config/name="'):
                name = line.split("=", 1)[1].strip().strip('"')
                break
    return name


def exported_app_path(project_dir: Path, export_path: Path) -> Path | None:
    if export_path.suffix.lower() != ".dmg":
        return None

    return export_path.with_name(f"{project_display_name(project_dir)}.app")


def ensure_export_preset(project_dir: Path) -> Path:
    preset_path = project_dir / "export_presets.cfg"
    if preset_path.exists():
        return preset_path

    preset_path.write_text(
        MACOS_PRESET_TEMPLATE.format(
            project_name=project_dir.name,
            bundle_identifier=build_bundle_identifier(project_dir.name),
        ),
        encoding="utf-8",
    )
    return preset_path


def ensure_project_export_settings(project_dir: Path) -> None:
    project_path = project_dir / "project.godot"
    text = project_path.read_text(encoding="utf-8")
    required_line = "textures/vram_compression/import_etc2_astc=true"

    if required_line in text:
        return

    rendering_header = "[rendering]"
    if rendering_header not in text:
        updated = text.rstrip() + f"\n\n{rendering_header}\n\n{required_line}\n"
    else:
        section_start = text.index(rendering_header)
        insert_at = text.find("\n[", section_start + len(rendering_header))
        if insert_at == -1:
            insert_at = len(text)
        section_body = text[section_start:insert_at]
        if section_body.endswith("\n"):
            injected = section_body + required_line + "\n"
        else:
            injected = section_body + "\n" + required_line + "\n"
        updated = text[:section_start] + injected + text[insert_at:]

    project_path.write_text(updated, encoding="utf-8")


def run_godot(godot_bin: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    command = [str(godot_bin), *args]
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def default_godot_bin(project_dir: Path | None = None) -> Path:
    candidates: list[Path] = []

    if project_dir is not None:
        for template_path in custom_template_paths(project_dir):
            bin_dir = template_path.parent
            candidates.extend(
                [
                    bin_dir / "godot.macos.editor.arm64",
                    bin_dir / "godot.macos.editor.x86_64",
                    bin_dir / "Godot.app" / "Contents" / "MacOS" / "Godot",
                ]
            )

    candidates.extend([
        Path("/Applications/Godot4.6.app/Contents/MacOS/Godot"),
        Path("/Applications/Godot.app/Contents/MacOS/Godot"),
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    path = shutil.which("godot4") or shutil.which("godot")
    if path:
        return Path(path)
    raise FileNotFoundError("Could not locate a Godot executable. Pass --godot-bin explicitly.")


def copy_project(src: Path, dst: Path, force: bool) -> None:
    if dst.exists():
        if not force:
            raise FileExistsError(f"Destination already exists: {dst}")
        shutil.rmtree(dst)

    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(".git"),
    )


def write_manifest(
    manifest_path: Path,
    src: Path,
    dst: Path,
    seed: int,
    function_map: dict[str, str],
    file_manifest: dict,
) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "seed": seed,
                "source": str(src),
                "destination": str(dst),
                "functions": function_map,
                "files": file_manifest,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def obfuscate_project(src: Path, dst: Path, seed: int, mapping_out: Path, force: bool) -> tuple[dict[str, str], dict]:
    copy_project(src, dst, force=force)
    scripts = discover_scripts(dst)
    name_factory = NameFactory(seed)
    function_map, file_manifest = discover_structure(scripts, name_factory)

    for script in scripts:
        obfuscated = replace_identifiers(script, function_map)
        script.path.write_text(obfuscated, encoding="utf-8")

    ensure_project_export_settings(dst)
    ensure_export_preset(dst)
    rewrite_export_paths(dst, src.name, dst.name)
    ensure_export_excludes(dst)
    write_manifest(mapping_out, src, dst, seed, function_map, file_manifest)
    return function_map, file_manifest


def copy_runtime_dylibs(app_path: Path) -> None:
    export_dir = app_path.parent
    app_macos_dir = app_path / "Contents" / "MacOS"
    if not app_macos_dir.exists():
        return

    for dylib in export_dir.glob("*.dylib"):
        target = app_macos_dir / dylib.name
        shutil.copy2(dylib, target)


def codesign_app(app_path: Path) -> None:
    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
        capture_output=True,
        text=True,
        check=True,
    )


def build_dmg_from_app(app_path: Path, dmg_path: Path) -> None:
    if dmg_path.exists():
        dmg_path.unlink()

    subprocess.run(
        [
            "hdiutil",
            "create",
            "-volname",
            app_path.stem,
            "-srcfolder",
            str(app_path),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy and obfuscate GDScript internals in a Godot project.")
    parser.add_argument("--src", required=True, type=Path, help="Source Godot project directory.")
    parser.add_argument("--dst", required=True, type=Path, help="Destination project directory.")
    parser.add_argument("--seed", type=int, default=1337, help="Stable seed for symbol generation.")
    parser.add_argument(
        "--mapping-out",
        type=Path,
        default=None,
        help="Path for the private mapping manifest. Defaults to <dst>/_obfuscation/mapping.json.",
    )
    parser.add_argument("--force", action="store_true", help="Replace the destination directory if it already exists.")
    parser.add_argument("--validate", action="store_true", help="Run Godot headless validation on the ugly project.")
    parser.add_argument("--export-macos", action="store_true", help="Run a macOS export after validation.")
    parser.add_argument(
        "--godot-bin",
        type=Path,
        default=None,
        help="Path to the Godot editor binary used for validation/export.",
    )
    parser.add_argument(
        "--export-path",
        type=Path,
        default=None,
        help="Optional export output path. Defaults to <dst>/builds/<dst.name>.dmg.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    src = args.src.resolve()
    dst = args.dst.resolve()
    mapping_out = (
        args.mapping_out.resolve()
        if args.mapping_out
        else (dst / "_obfuscation" / "mapping.json").resolve()
    )

    if not (src / "project.godot").exists():
        print(f"Source does not look like a Godot project: {src}", file=sys.stderr)
        return 2

    function_map, file_manifest = obfuscate_project(
        src=src,
        dst=dst,
        seed=args.seed,
        mapping_out=mapping_out,
        force=args.force,
    )

    print(f"Obfuscated {len(file_manifest)} scripts into {dst}")
    print(f"Function symbols remapped: {len(function_map)}")
    print(f"Mapping manifest: {mapping_out}")

    if args.validate or args.export_macos:
        godot_bin = args.godot_bin.resolve() if args.godot_bin else default_godot_bin(dst)

    if args.validate:
        validation = run_godot(godot_bin, ["--headless", "--path", str(dst), "--quit"], cwd=dst)
        sys.stdout.write(validation.stdout)
        sys.stderr.write(validation.stderr)
        if validation.returncode != 0:
            return validation.returncode

    if args.export_macos:
        export_path = (
            args.export_path.resolve()
            if args.export_path
            else export_path_from_presets(dst, "macOS")
            or (dst / "builds" / f"{dst.name}.dmg").resolve()
        )
        export_path.parent.mkdir(parents=True, exist_ok=True)
        app_path = exported_app_path(dst, export_path) if export_path.suffix.lower() == ".dmg" else export_path
        if app_path.exists():
            shutil.rmtree(app_path)

        export = run_godot(
            godot_bin,
            ["--headless", "--path", str(dst), "--export-release", "macOS", str(app_path)],
            cwd=dst,
        )
        sys.stdout.write(export.stdout)
        sys.stderr.write(export.stderr)
        if export.returncode != 0:
            return export.returncode

        if app_path.suffix.lower() == ".app":
            copy_runtime_dylibs(app_path)
            codesign_app(app_path)

        if export_path.suffix.lower() == ".dmg":
            build_dmg_from_app(app_path, export_path)

        print(f"Export created at {export_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
