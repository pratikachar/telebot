import io
import os
import subprocess


def list_dir(path):
    path = path or os.getcwd()
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Not a folder: {path}")
    entries = sorted(os.listdir(path))
    lines = [f"\U0001F4C1 {os.path.abspath(path)}"]
    for e in entries[:60]:
        full = os.path.join(path, e)
        marker = "\U0001F4C1" if os.path.isdir(full) else "\U0001F4C4"
        lines.append(f"{marker} {e}")
    if len(entries) > 60:
        lines.append(f"... and {len(entries) - 60} more")
    return "\n".join(lines)


def read_file(path, max_lines=100):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Not a file: {path}")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()[:max_lines]
    return "".join(lines) or "(empty file)"


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
