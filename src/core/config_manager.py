import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def _load_full_config():
        if not os.path.exists(CONFIG_FILE):
            return {"shortcuts": [], "settings": {"theme_whiteness": 0}}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"shortcuts": [], "settings": {"theme_whiteness": 0}}

    @staticmethod
    def _save_full_config(config):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    @staticmethod
    def load_shortcuts():
        config = ConfigManager._load_full_config()
        return config.get("shortcuts", [])

    @staticmethod
    def save_shortcuts(shortcuts):
        config = ConfigManager._load_full_config()
        config["shortcuts"] = shortcuts
        ConfigManager._save_full_config(config)

    @staticmethod
    def add_shortcut(path, name=None):
        shortcuts = ConfigManager.load_shortcuts()
        # Prevent duplicates
        for s in shortcuts:
            if s["path"] == path:
                return False

        if not name:
            name = os.path.basename(path)
            if not name:
                name = path

        shortcuts.append({
            "path": path,
            "name": name
        })
        ConfigManager.save_shortcuts(shortcuts)
        return True

    @staticmethod
    def remove_shortcut(path):
        shortcuts = ConfigManager.load_shortcuts()
        new_shortcuts = [s for s in shortcuts if s["path"] != path]
        if len(new_shortcuts) != len(shortcuts):
            ConfigManager.save_shortcuts(new_shortcuts)
            return True
        return False

    @staticmethod
    def update_shortcut(path, updates):
        """Update fields on an existing shortcut (e.g. custom_icon, custom_name).
        The whole entry is replaced for the matching path so any keys not in
        `updates` are preserved, while keys explicitly set to None are removed
        (used to clear custom values).
        """
        config = ConfigManager._load_full_config()
        shortcuts = config.get("shortcuts", [])
        for i, s in enumerate(shortcuts):
            if s.get("path") == path:
                for key, value in updates.items():
                    if value is None:
                        s.pop(key, None)
                    else:
                        s[key] = value
                shortcuts[i] = s
                config["shortcuts"] = shortcuts
                ConfigManager._save_full_config(config)
                return True
        return False

    @staticmethod
    def get_setting(key, default=None):
        config = ConfigManager._load_full_config()
        settings = config.get("settings", {})
        return settings.get(key, default)

    @staticmethod
    def set_setting(key, value):
        config = ConfigManager._load_full_config()
        if "settings" not in config:
            config["settings"] = {}
        config["settings"][key] = value
        ConfigManager._save_full_config(config)
