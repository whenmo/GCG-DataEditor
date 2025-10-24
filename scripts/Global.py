import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 避免在執行時循環匯入，僅在型別檢查階段匯入 MainWindow
    from MainFrom import MainWindow


_MAIN: "MainWindow | None" = None


def set_main(m: "MainWindow | None") -> None:
    global _MAIN
    _MAIN = m


def get_main() -> "MainWindow | None":
    return _MAIN


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
