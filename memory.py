import os

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MEMORY.md")


def memory_read(limit=4000):
    if not os.path.isfile(MEMORY_FILE):
        return ""
    with open(MEMORY_FILE, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return text.strip()[:limit]


def memory_add(text):
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    return True