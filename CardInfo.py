class Cardinfo:
    def __init__(self):
        super().__init__()
        self.title: dict[str, str] = {}

    def set_key_dict(self, key: str, title: str, key_dict: dict[str, str]):
        self.title[key] = title
        setattr(self, key, key_dict)

    def get_key(self, key: str) -> tuple[str, dict[str, str]]:
        return (self.title[key], getattr(self, key))


# 讀取 cardinfo.txt
def load_cardinfo() -> dict[str, dict[str, str]]:
    info: Cardinfo = Cardinfo()
    info_key: str = ""
    info_title: str = ""
    item_dict: dict[str, str] = {}
    with open("data/cardinfo.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.lstrip("\ufeff").strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@"):
                if info_key:
                    info.set_key_dict(info_key, info_title, item_dict)
                parts = line[1:].split("\t")
                if len(parts) == 2:
                    info_key, info_title = parts
                item_dict = {}
            else:
                parts = line.split("\t")
                if len(parts) == 2:
                    item_value, item_key = parts
                    item_dict[item_key] = item_value.lower()

    if info_key:
        info.set_key_dict(info_key, info_title, item_dict)

    return info
