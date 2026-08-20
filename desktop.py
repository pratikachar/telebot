import io
import os
import subprocess


def list_dir(path, recursive=False, limit=60):
    path = path or os.getcwd()
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Not a folder: {path}")
    lines = []
    if not recursive:
        entries = sorted(os.listdir(path))
        lines.append(f"\U0001F4C1 {os.path.abspath(path)}")
        for e in entries[:limit]:
            full = os.path.join(path, e)
            marker = "\U0001F4C1" if os.path.isdir(full) else "\U0001F4C4"
            lines.append(f"{marker} {e}")
        if len(entries) > limit:
            lines.append(f"... and {len(entries) - limit} more")
        return "\n".join(lines)
    lines.append(f"\U0001F4C1 {os.path.abspath(path)}")
    count = 0
    for root, dirs, files in os.walk(path):
        dirs.sort()
        files.sort()
        level = root.replace(path, "").count(os.sep)
        indent = "  " * level
        if level > 0:
            lines.append(f"{indent}\U0001F4C1 {os.path.basename(root)}/")
        for f in files[:limit]:
            lines.append(f"{indent}  \U0001F4C4 {f}")
            count += 1
            if count >= limit:
                lines.append(f"... and more (limited to {limit} files)")
                return "\n".join(lines)
    return "\n".join(lines)


def read_file(path, max_lines=100):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Not a file: {path}")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()[:max_lines]
    return "".join(lines) or "(empty file)"


def create_file(path, content=""):
    """Create a new file (overwrites if exists). Returns success message."""
    try:
        if os.path.isdir(path):
            return f"Path is a directory, not a file: {path}"
        parent = os.path.dirname(path) or "."
        os.makedirs(parent, exist_ok=True)
        abs_path = os.path.abspath(path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        if not os.path.exists(abs_path):
            return f"Write reported success but file not found: {abs_path}"
        return f"File created: {abs_path}"
    except PermissionError:
        return (
            f"Permission denied: cannot write to '{path}'.\n"
            "Avoid system-protected locations like C:\\ root. Use your Desktop, e.g.:\n"
            "C:\\Users\\Pratik\\Desktop\\test.txt  (or just: test.txt)"
        )
    except Exception as exc:
        return f"Failed to create file: {exc}"


def append_file(path, content=""):
    """Append text to a file (creates it if missing). Returns status message."""
    try:
        abs_path = os.path.abspath(path)
        prefix = ""
        if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(os.path.getsize(abs_path) - 1)
                last = f.read(1)
            if last and last != "\n":
                prefix = "\n"
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(prefix + content + "\n")
        return f"Appended to: {abs_path}"
    except Exception as exc:
        return f"Failed to append: {exc}"


def delete_file(path):
    """Delete a file. Refuses directories and missing paths. Returns status message."""
    try:
        abs_path = os.path.abspath(path)
        if os.path.isdir(abs_path):
            return f"Refused: '{path}' is a directory, not a file."
        if not os.path.exists(abs_path):
            return f"File not found: {path}"
        os.remove(abs_path)
        return f"Deleted: {abs_path}"
    except Exception as exc:
        return f"Failed to delete: {exc}"


APPS = {
    "notepad": "notepad",
    "calc": "calc",
    "paint": "mspaint",
    "chrome": "chrome",
    "edge": "msedge",
    "explorer": "explorer",
    "cmd": "cmd",
    "terminal": "wt",
}


def open_app(app):
    app = app.strip().lower()
    target = APPS.get(app, app)
    if os.path.isfile(app):
        os.startfile(app)
        return f"Opened file: {app}"
    if "\\" in app or "/" in app:
        os.startfile(app)
        return f"Opened: {app}"
    os.startfile(target)
    return f"Launched: {target}"


def close_app(app):
    """Close an app by name (maps friendly names) or by process name."""
    app = app.strip().lower()
    proc = APPS.get(app, app)
    if not proc.endswith(".exe"):
        proc += ".exe"
    result = subprocess.run(
        ["taskkill", "/IM", proc, "/F"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if "SUCCESS" in output or "successfully" in output.lower():
        return f"Closed: {proc}"
    return f"Could not close {proc}:\n{output[-500:]}"


def uninstall(app):
    """Uninstall via winget using the same allowlist as /install."""
    name = app.strip().lower()
    if name not in INSTALL_ALLOWLIST:
        return (
            f"'{app}' is not on the allowlist. Allowed: {', '.join(INSTALL_ALLOWLIST)}"
        )
    pkg = PACKAGE_MAP.get(name, name)
    result = subprocess.run(
        ["winget", "uninstall", "--id", pkg, "--accept-source-agreements"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return f"winget uninstall {pkg}:\n{output[-1500:]}"


def screenshot():
    from PIL import ImageGrab

    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return buf


INSTALL_ALLOWLIST = [
    "node", "nodejs", "git", "python", "python3", "notepadplusplus", "7zip",
    "vlc", "spotify", "discord", "obs", "ffmpeg", "code", "gcc", "docker",
]

PACKAGE_MAP = {
    "node": "OpenJS.NodeJS.LTS",
    "nodejs": "OpenJS.NodeJS.LTS",
    "python": "Python.Python.3.13",
    "python3": "Python.Python.3.13",
    "code": "Microsoft.VisualStudioCode",
    "git": "Git.Git",
    "notepadplusplus": "Notepad++.Notepad++",
    "7zip": "7zip.7zip",
    "vlc": "VideoLAN.VLC",
    "spotify": "Spotify.Spotify",
    "discord": "Discord.Discord",
    "obs": "OBSProject.OBSStudio",
    "ffmpeg": "Gyan.FFmpeg",
    "docker": "Docker.DockerDesktop",
    "gcc": "GCC",
}


def install(app):
    name = app.strip().lower()
    if name not in INSTALL_ALLOWLIST:
        return (
            f"'{app}' is not on the allowlist. Allowed: {', '.join(INSTALL_ALLOWLIST)}"
        )
    pkg = PACKAGE_MAP.get(name, name)
    result = subprocess.run(
        ["winget", "install", "--id", pkg, "--accept-package-agreements", "--accept-source-agreements"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return f"winget {pkg}:\n{output[-1500:]}"


# ---- allowlisted command execution (commands.txt) ----

COMMANDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commands.txt")


def _load_commands():
    """Load {name: command} from commands.txt. Lines: name = command  (# comments / blanks skipped)."""
    cmds = {}
    if not os.path.isfile(COMMANDS_FILE):
        return cmds
    with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                name, _, cmd = line.partition("=")
                cmds[name.strip()] = cmd.strip()
    return cmds


def run_command(name):
    """Run an allowlisted command from commands.txt by name. No shell wildcards."""
    cmds = _load_commands()
    if not cmds:
        return "commands.txt is empty or missing. Add lines like:\nping = ping google.com -n 4"
    if name not in cmds:
        return f"Unknown command '{name}'. Available: {', '.join(sorted(cmds))}"
    try:
        result = subprocess.run(
            cmds[name],
            shell=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout or "") + (result.stderr or "")
        if not output.strip():
            output = "(no output)"
        return f"$ {cmds[name]}\n{output[-1500:]}"
    except subprocess.TimeoutExpired:
        return f"Command '{name}' timed out after 60s."
    except Exception as exc:
        return f"Failed to run '{name}': {exc}"


# ---- UI automation (pyautogui) ----

def _pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.2
    return pyautogui


def type_text(text):
    py = _pyautogui()
    py.write(text, interval=0.02)
    return f"Typed: {text[:200]}"


def key_press(key):
    py = _pyautogui()
    py.press(key)
    return f"Pressed key: {key}"


def click(x, y, button="left"):
    py = _pyautogui()
    py.click(int(x), int(y), button=button)
    return f"Clicked ({int(x)}, {int(y)}) with {button}"


def scroll(clicks):
    py = _pyautogui()
    py.scroll(int(clicks))
    return f"Scrolled {clicks}"


def move_mouse(x, y):
    py = _pyautogui()
    py.moveTo(int(x), int(y), duration=0.2)
    return f"Moved mouse to ({int(x)}, {int(y)})"


def get_mouse_pos():
    py = _pyautogui()
    x, y = py.position()
    return f"Mouse at ({x}, {y})"


# ---- sandboxed code execution ----

CODE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code_sandbox")


def code_exec(code, timeout=30):
    """Run Python code in a sandboxed temp folder. Returns (text, list_of_png_paths)."""
    import shutil
    import tempfile

    sandbox = tempfile.mkdtemp(prefix="botcode_", dir=CODE_DIR if os.path.isdir(CODE_DIR) else tempfile.gettempdir())
    script = os.path.join(sandbox, "main.py")
    with open(script, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run(
            [sys_executable(), script],
            cwd=sandbox,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout or "") + (result.stderr or "")
        pngs = [os.path.join(sandbox, p) for p in os.listdir(sandbox) if p.lower().endswith(".png")]
        if not output.strip():
            output = "(no output)"
        return output[-4000:], pngs
    except subprocess.TimeoutExpired:
        return "Code timed out.", []
    except Exception as exc:
        return f"Failed to run code: {exc}", []
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def sys_executable():
    import sys
    return sys.executable
