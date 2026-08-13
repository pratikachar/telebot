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
    except PermissionError:
        return (
            f"Permission denied: cannot write to '{path}'.\n"
            "Avoid system-protected locations like C:\\ root. Use your Desktop, e.g.:\n"
            "C:\\Users\\Pratik\\Desktop\\test.txt  (or just: test.txt)"
        )
    except Exception as exc:
        return f"Failed to create file: {exc}"


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


def screenshot():
    from PIL import ImageGrab

    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return buf


def install(app):
    allowed = ["node", "nodejs", "git", "python", "python3", "notepadplusplus", "7zip",
               "vlc", "spotify", "discord", "obs", "ffmpeg", "code", "gcc", "docker"]
    name = app.strip().lower()
    if name not in allowed:
        return (
            f"'{app}' is not on the allowlist. Allowed: {', '.join(allowed)}"
        )
    if name in ("node", "nodejs"):
        pkg = "OpenJS.NodeJS.LTS"
    elif name == "python":
        pkg = "Python.Python.3.13"
    elif name == "code":
        pkg = "Microsoft.VisualStudioCode"
    elif name == "git":
        pkg = "Git.Git"
    elif name == "notepadplusplus":
        pkg = "Notepad++.Notepad++"
    elif name == "7zip":
        pkg = "7zip.7zip"
    elif name == "vlc":
        pkg = "VideoLAN.VLC"
    elif name == "spotify":
        pkg = "Spotify.Spotify"
    elif name == "discord":
        pkg = "Discord.Discord"
    elif name == "obs":
        pkg = "OBSProject.OBSStudio"
    elif name == "ffmpeg":
        pkg = "Gyan.FFmpeg"
    elif name == "docker":
        pkg = "Docker.DockerDesktop"
    else:
        pkg = name
    result = subprocess.run(
        ["winget", "install", "--id", pkg, "--accept-package-agreements", "--accept-source-agreements"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return f"winget {pkg}:\n{output[-1500:]}"
