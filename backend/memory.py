import json
import os

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_message(history, role, content):
    history.append({"role": role, "content": content})
    save_history(history)
    return history


def clear_history():
    save_history([])
    return []