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
