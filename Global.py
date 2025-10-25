import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 避免在執行時循環匯入，僅在型別檢查階段匯入 MainWindow
    from MainFrom import MainWindow

# ---------------- APP_ID ----------------
APP_ID = "GCGDataEditor"

# ---------------- 主視窗 ----------------
_MAIN: "MainWindow | None" = None


def set_main(m: "MainWindow | None") -> None:
    global _MAIN
    _MAIN = m


def get_main() -> "MainWindow | None":
    return _MAIN


# ---------------- 路徑 ----------------
def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_path()
PATH_CARDINFO: str = os.path.join(BASE_DIR, "data", "cardinfo.txt")
PATH_CONFIG: str = os.path.join(BASE_DIR, "data", "config.json")
PATH_COVER: str = os.path.join(BASE_DIR, "data", "cover.jpg")
PATH_ICON: str = os.path.join(BASE_DIR, "data", "app_icon.png")

# ---------------- 資料庫 ----------------
SQL_DATA_KEYS: str = "ot,alias,setcode,type,atk,def,level,race,attribute,category"
SQL_TEXT_KEYS: str = "name,desc,str1,str2,str3,str4,str5,str6,str7,str8,str9,str10,str11,str12,str13,str14,str15,str16"


def get_sql_code_data() -> tuple[str, str]:
    keys_list = SQL_DATA_KEYS.split(",")
    key_type_list = [f"{key} INTEGER" for key in keys_list]
    column_str = ",\n        ".join(key_type_list)
    set_code = f"""
        CREATE TABLE IF NOT EXISTS datas (
            id INTEGER PRIMARY KEY,
            {column_str}
        )
        """
    key_ct = len(keys_list) + 1
    insert_str = ",".join(["?"] * key_ct)
    insert_code = f"INSERT INTO datas VALUES ({insert_str})"
    return (set_code, insert_code)


def get_sql_code_text() -> tuple[str, str]:
    keys_list = SQL_TEXT_KEYS.split(",")
    key_type_list = [f"{key} TEXT" for key in keys_list]
    column_str = ",\n        ".join(key_type_list)
    set_code = f"""
        CREATE TABLE IF NOT EXISTS texts (
            id INTEGER PRIMARY KEY,
            {column_str}
        )
        """
    key_ct = len(keys_list) + 1
    insert_str = ",".join(["?"] * key_ct)
    insert_code = f"INSERT INTO texts VALUES ({insert_str})"
    return (set_code, insert_code)
