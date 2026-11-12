#!/usr/bin/env python3
"""BMS VIP 3.0 — professional, offline-first Termux toolkit.
Standard-library only. Network actions are limited to user-requested DNS,
single-host TCP checks, HTTP GET checks, and authorized API GET requests.
"""
from __future__ import annotations

import csv
import getpass
import json
import os
import platform
import re
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

APP_NAME = "BMS VIP"
VERSION = "3.0.0"
BASE = Path.home() / ".bms_vip"
WORKSPACE = BASE / "workspace"
BACKUPS = BASE / "backups"
LOG_FILE = BASE / "activity.json"
SETTINGS_FILE = BASE / "settings.json"
MAX_READ = 1_000_000
TIMEOUT = 8

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
MAGENTA = "\033[95m"

def init_dirs() -> None:
    for p in (BASE, WORKSPACE, BACKUPS):
        p.mkdir(parents=True, exist_ok=True)

def color_enabled() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM", "dumb") != "dumb"

def paint(value: str, color: str) -> str:
    return f"{color}{value}{RESET}" if color_enabled() else value

def term_width() -> int:
    return max(48, min(shutil.get_terminal_size((72, 24)).columns, 88))

def rule(char: str = "─") -> None:
    print(paint(char * term_width(), CYAN))

def clear() -> None:
    os.system("clear" if os.name == "posix" else "cls")

def pause() -> None:
    input(paint("\n  Press ENTER to continue...", DIM))

def log_event(action: str, detail: str = "") -> None:
    init_dirs()
    try:
        rows = json.loads(LOG_FILE.read_text(encoding="utf-8")) if LOG_FILE.exists() else []
        if not isinstance(rows, list):
            rows = []
    except (OSError, json.JSONDecodeError):
        rows = []
    rows.append({"time": datetime.now().isoformat(timespec="seconds"),
                 "action": action, "detail": detail[:300]})
    LOG_FILE.write_text(json.dumps(rows[-500:], indent=2), encoding="utf-8")

def read_settings() -> dict[str, Any]:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def write_settings(data: dict[str, Any]) -> None:
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def safe_workspace_path(name: str) -> Path | None:
    name = name.strip()
    if not name:
        return None
    candidate = (WORKSPACE / name).resolve()
    try:
        candidate.relative_to(WORKSPACE.resolve())
    except ValueError:
        return None
    return candidate

def banner() -> None:
    width = term_width()
    logo = [
        "██████╗ ███╗   ███╗███████╗",
        "██╔══██╗████╗ ████║██╔════╝",
        "██████╔╝██╔████╔██║███████╗",
        "██╔══██╗██║╚██╔╝██║╚════██║",
        "██████╔╝██║ ╚═╝ ██║███████║",
        "╚═════╝ ╚═╝     ╚═╝╚══════╝",
    ]
    for row in logo:
        print(paint(row.center(width), BOLD + CYAN))
    print(paint("PROFESSIONAL TERMUX TOOLKIT  •  NIGERIA EDITION".center(width), RED + BOLD))
    print(paint(f"{APP_NAME}  v{VERSION}".center(width), DIM))
    rule("═")
    print(f"  {paint('● READY', GREEN + BOLD)}  {paint(datetime.now().strftime('%a %d %b %Y  %H:%M:%S'), DIM)}")
    print(f"  Profile: BMS   |   Workspace: {WORKSPACE}")
    rule("─")

def section(title: str) -> None:
    print("\n" + paint(title.upper(), WHITE + BOLD))
    rule("─")

def ask(prompt: str) -> str:
    return input(paint("  " + prompt + " ", CYAN + BOLD)).strip()

def show_result(label: str, value: Any) -> None:
    print(f"  {paint(label + ':', CYAN):<28} {value}")

def system_dashboard() -> None:
    section("System dashboard")
    print(paint("Collecting local device information...", DIM))
    uname = platform.uname()
    show_result("Operating system", f"{uname.system} {uname.release}")
    show_result("Device / machine", uname.machine or "Not reported")
    show_result("Python", platform.python_version())
    show_result("Processor", platform.processor() or "Not reported")
    show_result("Terminal", f"{shutil.get_terminal_size((80,24)).columns} × {shutil.get_terminal_size((80,24)).lines}")
    show_result("Current directory", Path.cwd())
    try:
        usage = shutil.disk_usage(Path.home())
        gb = 1024 ** 3
        show_result("Home storage", f"{usage.used/gb:.2f} GB used / {usage.total/gb:.2f} GB")
        show_result("Free storage", f"{usage.free/gb:.2f} GB")
    except OSError:
        show_result("Home storage", "Unavailable")
    log_event("system_dashboard", "viewed")

def resolve_dns() -> None:
    section("DNS lookup")
    host = ask("Hostname (e.g. example.com):")
    if not host or "/" in host or " " in host:
        print(paint("Invalid hostname.", RED)); return
    try:
        results = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        addresses = sorted({r[4][0] for r in results})
        for ip in addresses:
            print("  " + paint("• ", GREEN) + ip)
        print(paint(f"\n  Resolved {len(addresses)} address(es).", GREEN))
        log_event("dns_lookup", host)
    except socket.gaierror as exc:
        print(paint(f"DNS lookup failed: {exc}", RED))
        log_event("dns_lookup_failed", host)

def tcp_check() -> None:
    section("Single-host connection test")
    host = ask("Host to test:")
    port_text = ask("Port (1–65535):")
    if not host or "/" in host or " " in host:
        print(paint("Enter a hostname or IP address, not a URL.", RED)); return
    if not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
        print(paint("Port must be between 1 and 65535.", RED)); return
    port = int(port_text)
    try:
        start = time.perf_counter()
        with socket.create_connection((host, port), timeout=TIMEOUT):
            ms = (time.perf_counter() - start) * 1000
        print(paint(f"  ✓ {host}:{port} accepted a TCP connection ({ms:.1f} ms).", GREEN))
        log_event("tcp_check", f"{host}:{port} open")
    except OSError as exc:
        print(paint(f"  ✗ Connection failed: {exc}", YELLOW))
        log_event("tcp_check", f"{host}:{port} failed")

def http_check() -> None:
    section("Website availability")
    url = ask("HTTPS/HTTP URL:")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        print(paint("Enter a complete http:// or https:// URL.", RED)); return
    req = urllib.request.Request(url, headers={"User-Agent": "BMS-VIP/3.0 (website-check)"}, method="GET")
    try:
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as resp:
            body = resp.read(1024)
            ms = (time.perf_counter() - start) * 1000
            show_result("HTTP status", resp.status)
            show_result("Final URL", resp.geturl())
            show_result("Response time", f"{ms:.1f} ms")
            show_result("Content type", resp.headers.get("Content-Type", "unknown"))
            print(paint(f"  ✓ Website responded. Sample received: {len(body)} bytes.", GREEN))
        log_event("website_check", url)
    except urllib.error.HTTPError as exc:
        print(paint(f"Website responded with HTTP {exc.code}.", YELLOW))
        log_event("website_check", f"{url} -> {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        print(paint(f"Check failed: {exc}", RED))
        log_event("website_check_failed", url)

def network_center() -> None:
    while True:
        section("Network centre")
        print("  [1] DNS lookup")
        print("  [2] Single-host TCP connection test")
        print("  [3] Website availability (one URL)")
        print("  [0] Back")
        choice = ask("BMS/network >")
        if choice == "1": resolve_dns(); pause()
        elif choice == "2": tcp_check(); pause()
        elif choice == "3": http_check(); pause()
        elif choice == "0": return
        else: print(paint("Invalid choice.", RED))

def api_get() -> None:
    section("Authorized API GET tester")
    print(paint("Use only an API you own or are authorized to access.", YELLOW))
    url = ask("API endpoint URL:")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        print(paint("For safety, API tester accepts HTTPS URLs only.", RED)); return
    header_name = ask("Optional header name (ENTER to skip):")
    headers = {"User-Agent": "BMS-VIP/3.0"}
    if header_name:
        if not re.fullmatch(r"[A-Za-z0-9-]{1,60}", header_name):
            print(paint("Invalid header name.", RED)); return
        secret = getpass.getpass("  Header value (hidden; not saved): ")
        if not secret:
            print(paint("Empty header value; cancelled.", YELLOW)); return
        headers[header_name] = secret
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as resp:
            raw = resp.read(MAX_READ + 1)
            if len(raw) > MAX_READ:
                print(paint("Response exceeded 1 MB and was truncated.", YELLOW))
                raw = raw[:MAX_READ]
            show_result("HTTP status", resp.status)
            show_result("Content type", resp.headers.get("Content-Type", "unknown"))
            print("\nResponse preview:")
            text = raw.decode("utf-8", errors="replace")
            try:
                obj = json.loads(text)
                text = json.dumps(obj, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
            print(text[:MAX_READ])
            log_event("api_get", parsed.hostname)
    except urllib.error.HTTPError as exc:
        print(paint(f"API returned HTTP {exc.code}: {exc.reason}", YELLOW))
        log_event("api_get_http_error", f"{parsed.hostname} {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        print(paint(f"API request failed: {exc}", RED))
        log_event("api_get_failed", parsed.hostname)

def json_formatter() -> None:
    section("JSON formatter / validator")
    print("Paste JSON on one line, or enter a file name inside the BMS workspace.")
    value = ask("JSON text or workspace filename:")
    candidate = safe_workspace_path(value)
    try:
        if candidate and candidate.is_file():
            raw = candidate.read_text(encoding="utf-8")
        else:
            raw = value
        parsed = json.loads(raw)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        print(paint("\n✓ Valid JSON\n", GREEN))
        print(formatted)
        if ask("Save formatted output to workspace? (y/N):").lower() == "y":
            name = ask("Output filename (e.g. formatted.json):")
            target = safe_workspace_path(name)
            if not target or target.exists() and target.is_dir():
                print(paint("Invalid output path.", RED)); return
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(formatted + "\n", encoding="utf-8")
            print(paint(f"Saved: {target}", GREEN))
        log_event("json_format", "valid")
    except (json.JSONDecodeError, OSError) as exc:
        print(paint(f"Invalid JSON or file error: {exc}", RED))
        log_event("json_format_failed", str(exc))

def text_tools() -> None:
    section("Text utilities")
    text = ask("Enter text:")
    print(f"\n  Characters: {len(text)}")
    print(f"  Words:      {len(text.split())}")
    print(f"  Lines:      {len(text.splitlines()) or (1 if text else 0)}")
    print(f"  UTF-8 size: {len(text.encode('utf-8'))} bytes")
    print("\n  UPPERCASE:", text.upper())
    print("  lowercase:", text.lower())
    log_event("text_tools", f"{len(text)} characters")

def workspace_manager() -> None:
    while True:
        section("Workspace file manager")
        print(f"  Root: {WORKSPACE}")
        for p in sorted(WORKSPACE.iterdir())[:30]:
            marker = "/" if p.is_dir() else ""
            size = "" if p.is_dir() else f"  ({p.stat().st_size} bytes)"
            print(f"  {'[DIR]' if p.is_dir() else '[FILE]'} {p.name}{marker}{size}")
        print("\n  [1] Create text file   [2] Read text file   [3] Delete file   [0] Back")
        choice = ask("BMS/files >")
        if choice == "0": return
        if choice == "1":
            name = ask("New filename (inside workspace):")
            p = safe_workspace_path(name)
            if not p or p.exists():
                print(paint("Invalid name or file already exists.", RED)); continue
            p.parent.mkdir(parents=True, exist_ok=True)
            content = input("  Text content: ")
            p.write_text(content + "\n", encoding="utf-8")
            print(paint("File created.", GREEN)); log_event("file_create", name)
        elif choice == "2":
            name = ask("Filename to read:")
            p = safe_workspace_path(name)
            if not p or not p.is_file():
                print(paint("File not found.", RED)); continue
            if p.stat().st_size > MAX_READ:
                print(paint("File is larger than 1 MB; refusing to print it.", YELLOW)); continue
            try: print(p.read_text(encoding="utf-8"))
            except UnicodeDecodeError: print(paint("Not a UTF-8 text file.", RED))
        elif choice == "3":
            name = ask("Filename to delete:")
            p = safe_workspace_path(name)
            if not p or not p.is_file():
                print(paint("Only existing files can be deleted here.", RED)); continue
            if ask(f"Confirm deletion of {p.name}? (yes/no):").lower() == "yes":
                p.unlink(); print(paint("Deleted.", GREEN)); log_event("file_delete", name)
        else:
            print(paint("Invalid choice.", RED))

def make_backup() -> None:
    section("Workspace backup")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUPS / f"workspace-{stamp}.zip"
    try:
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
            for p in WORKSPACE.rglob("*"):
                if p.is_file():
                    archive.write(p, p.relative_to(WORKSPACE))
        print(paint(f"✓ Backup created: {dest}", GREEN))
        print(f"  Size: {dest.stat().st_size} bytes")
        log_event("backup_created", dest.name)
    except OSError as exc:
        print(paint(f"Backup failed: {exc}", RED))

def view_activity() -> None:
    section("Activity analytics")
    try:
        rows = json.loads(LOG_FILE.read_text(encoding="utf-8")) if LOG_FILE.exists() else []
    except (OSError, json.JSONDecodeError):
        rows = []
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("action", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    show_result("Recorded actions", len(rows))
    print("\n  Action summary:")
    if not counts: print("  No activity recorded yet.")
    for key, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {key:<28} {count:>4}")
    print("\n  [1] Export CSV   [2] View recent events   [0] Back")
    choice = ask("BMS/analytics >")
    if choice == "1":
        out = BASE / "activity-export.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["time", "action", "detail"])
            writer.writeheader(); writer.writerows(rows)
        print(paint(f"Exported: {out}", GREEN))
        log_event("analytics_export", out.name)
    elif choice == "2":
        for row in rows[-15:]:
            print(f"  {row.get('time','')}  {row.get('action','')}  {row.get('detail','')}")
    pause()

def appearance() -> None:
    section("Appearance settings")
    settings = read_settings()
    compact = bool(settings.get("compact", False))
    print(f"  Current display density: {'Compact' if compact else 'Standard'}")
    if ask("Toggle compact display preference? (y/N):").lower() == "y":
        settings["compact"] = not compact
        write_settings(settings)
        print(paint("Preference saved.", GREEN))
        log_event("appearance_setting", "compact" if settings["compact"] else "standard")
    print(paint("Note: Standard-library terminal layout remains responsive to screen width.", DIM))

def about() -> None:
    section("About BMS VIP")
    print(f"  {APP_NAME} {VERSION}")
    print("  Professional, offline-first command-line toolkit for Termux.")
    print("  Standard-library Python; no pip packages required.")
    print("  Network checks are user-initiated and limited to one host/URL at a time.")
    print("  API tester uses HTTPS GET only; secrets are entered hidden and not saved.")
    print("  File manager is sandboxed to the BMS workspace.")
    print("  WhatsApp account access, ban/unban, scraping and mass reporting are not included.")
    print(f"\n  Data directory: {BASE}")
    log_event("about", "viewed")

def main_menu() -> None:
    init_dirs()
    while True:
        clear()
        banner()
        print(paint("\n  MAIN MENU", WHITE + BOLD))
        options = [
            ("1", "System dashboard"),
            ("2", "Network centre"),
            ("3", "Authorized API GET tester"),
            ("4", "JSON formatter / validator"),
            ("5", "Text utilities"),
            ("6", "Workspace file manager"),
            ("7", "Backup workspace"),
            ("8", "Activity analytics / CSV export"),
            ("9", "Appearance settings"),
            ("A", "About BMS VIP"),
            ("0", "Exit"),
        ]
        for key, label in options:
            print(f"  {paint('['+key+']', CYAN + BOLD)}  {label}")
        rule()
        choice = ask("BMS@Termux >").upper()
        actions = {
            "1": system_dashboard, "2": network_center, "3": api_get,
            "4": json_formatter, "5": text_tools, "6": workspace_manager,
            "7": make_backup, "8": view_activity, "9": appearance, "A": about
        }
        if choice == "0":
            print(paint("\nBMS VIP closed safely. Thank you.", CYAN))
            break
        action = actions.get(choice)
        if action:
            action()
            if choice not in ("2", "6", "8"):
                pause()
        else:
            print(paint("Invalid menu option.", RED))
            time.sleep(0.8)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n" + paint("BMS VIP interrupted safely.", YELLOW))
        sys.exit(0)
