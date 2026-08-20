import json
import os

SKILLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.json")


def _load():
    if not os.path.isfile(SKILLS_FILE):
        return {}
    try:
        with open(SKILLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data):
    with open(SKILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def skill_list():
    return sorted(_load().keys())


def skill_get(name):
    return _load().get(name)


def skill_add(name, steps):
    data = _load()
    data[name] = {"steps": steps}
    _save(data)


def skill_delete(name):
    data = _load()
    if name in data:
        del data[name]
        _save(data)
        return True
    return False