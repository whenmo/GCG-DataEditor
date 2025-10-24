import os
import json

PATH_CARDINFO: str = "data/cardinfo.txt"
PATH_CONFIG: str = "data/config.json"
DEFAULT_CONFIG = {"DATABASE_HISTORY": {"max_record": 10, "history_paths": []}}


# ---------------- CardInfo ----------------
class CardInfo:
    def __init__(self):
        super().__init__()
        self.title: dict[str, str] = {}
        self.default: dict[str, str] = {}

    def set_key_dict(
        self, key: str, title: str, key_dict: dict[str, str], default: str
    ):
        self.title[key] = title
        setattr(self, key, key_dict)
        self.default[key] = default

    def get_key(self, key: str) -> tuple[str, dict[str, str], str]:
        "return title dict default"
        return (self.title[key], getattr(self, key), self.default[key])


# 讀取 cardinfo.txt
def load_cardinfo() -> dict[str, dict[str, str]]:
    info: CardInfo = CardInfo()
    info_key: str = ""
    info_title: str = ""
    info_default: str = ""
    item_dict: dict[str, str] = {}
    with open(PATH_CARDINFO, "r", encoding="utf-8") as f:
        for line in f:
            line = line.lstrip("\ufeff").strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@"):
                if info_key:
                    info.set_key_dict(info_key, info_title, item_dict, info_default)
                parts = line[1:].split("\t")
                if len(parts) == 3:
                    info_key, info_title, info_default = parts
                item_dict = {}
            else:
                parts = line.split("\t")
                if len(parts) == 2:
                    item_value, item_key = parts
                    if item_key.startswith("~"):
                        for i in range(int(item_value), int(item_key[1:]) + 1):
                            i = str(i)
                            item_dict[i] = i
                    else:
                        item_dict[item_key] = item_value.lower()

    if info_key:
        info.set_key_dict(info_key, info_title, item_dict, info_default)

    return info


# ---------------- Config ----------------
def load_config() -> dict:
    """載入配置檔, 如果不存在或載入失敗則建立預設配置"""
    if not os.path.exists(PATH_CONFIG):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(PATH_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]

            if "DATABASE_HISTORY" not in config:
                config["DATABASE_HISTORY"] = DEFAULT_CONFIG["DATABASE_HISTORY"]

            return config
    except Exception:
        return DEFAULT_CONFIG


def save_config(config: dict):
    """將當前配置儲存到配置檔"""
    try:
        # 確保配置目錄存在 (如果配置檔不在執行目錄而是子目錄)
        os.makedirs(os.path.dirname(PATH_CONFIG), exist_ok=True)
        with open(PATH_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def update_history(config: dict, path: str) -> dict:
    """更新歷史路徑列表"""
    hist_set = config.get("DATABASE_HISTORY", {})
    hist_lst: list = hist_set.get("history_paths", [])
    max_record = hist_set.get("max_record", 10)
    if path in hist_lst:
        hist_lst.remove(path)
    hist_lst.insert(0, path)
    hist_lst = hist_lst[:max_record]
    hist_set["history_paths"] = hist_lst
    config["DATABASE_HISTORY"] = hist_set
    save_config(config)
    return config