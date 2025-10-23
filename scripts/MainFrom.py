import sys
import os
from DataBase import creat_new_cdb
from DataEditorFrom import DataEditor
from ItemLib import FileBtnToolBar
from Global import set_main
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QToolBar,
    QToolButton,
    QMenu,
    QMessageBox,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


def new_toolbtn(title: str, toolbar: QToolBar) -> QMenu:
    btn = QToolButton()
    btn.setText(title)
    toolbar.addWidget(btn)
    menu = QMenu()
    btn.setMenu(menu)
    btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    return menu


def new_action(title: str, frame, menu: QMenu, func):
    act = QAction(title, frame)
    menu.addAction(act)
    if func:
        act.triggered.connect(func)


def load_hist() -> list[str]:
    res = []
    with open("data/history.txt", "a+", encoding="utf-8") as f:
        f.seek(0)
        res = f.read().splitlines()
    return res


def set_hist(hist_lst: list[str]):
    path = "data/history.txt"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(hist_lst))


class MainWindow(QMainWindow):
    file_list: FileBtnToolBar
    dataeditor: DataEditor
    title: str
    hist_menu: QMenu
    hist_list: list[str]

    def __init__(self):
        super().__init__()
        # 註冊到 AppContext，避免循環匯入
        set_main(self)
        self.title = "Eternal Field DataEditor"
        self.setWindowTitle(self.title)
        self.resize(850, 650)
        # 工具列
        main_toolbar = QToolBar("main")
        self.addToolBar(main_toolbar)
        # ---------------- 文件 ----------------
        file_menu = new_toolbtn("文件", main_toolbar)
        new_action("打开", self, file_menu, self.open_cdb)
        new_action("新建", self, file_menu, self.new_cdb)
        # ---------------- 歷史 ----------------
        self.hist_menu = new_toolbtn("数据库历史", main_toolbar)
        self.hist_list = load_hist()
        self.updata_hist_btn()
        # ---------------- 檔案列表 ----------------
        self.addToolBarBreak()  # 讓下一個工具列換行，放在主工具列下方
        self.file_list = FileBtnToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.file_list)
        # ---------------- 數據編輯器 ----------------
        self.dataeditor = DataEditor()
        self.setCentralWidget(self.dataeditor)

    # ---------------- 彈窗 ----------------
    # 詢問組件
    def show_quest(self, msg: str, can_cancel: bool = False) -> bool | None:
        yes = QMessageBox.StandardButton.Yes
        no = QMessageBox.StandardButton.No
        cancel = QMessageBox.StandardButton.Cancel
        if can_cancel:
            res = QMessageBox.question(self, "询问", msg, yes | no | cancel)
        else:
            res = QMessageBox.question(self, "询问", msg, yes | no)
        if res == yes:
            return True
        if res == no:
            return False
        return None

    # 錯誤組件
    def show_error(self, msg: str):
        QMessageBox.warning(self, "错误", msg)

    # 提示組件
    def show_msg(self, msg: str):
        QMessageBox.information(self, "提示", msg)

    # ---------------- 歷史 ----------------
    # 更新歷史欄
    def updata_hist_btn(self):
        self.hist_menu.clear()
        for path in self.hist_list:
            new_action(
                path,
                self,
                self.hist_menu,
                lambda c, p=path: self.file_list.add_cdbfile(p),
            )
        self.hist_menu.addSeparator()
        new_action("清空历史纪录", self, self.hist_menu, self.del_hist)

    # 增加歷史
    def add_hist(self, path: str):
        if path in self.hist_list:
            self.hist_list.remove(path)
        self.hist_list.insert(0, path)
        if len(self.hist_list) > 10:
            self.hist_list = self.hist_list[:10]
        set_hist(self.hist_list)

    # 刪除歷史
    def del_hist(self):
        self.hist_list = []
        set_hist(self.hist_list)
        self.updata_hist_btn()

    # ---------------- 文件 ----------------
    # 根據路徑打開 cdb
    def open_path(self, path: str):
        self.add_hist(path)
        self.updata_hist_btn()
        self.file_list.add_cdbfile(path)

    # 開啟 cdb
    def open_cdb(self, path=None):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CDB File", "", "CDB Files (*.cdb)"
        )
        if not path:
            return
        self.open_path(path)

    # 新建 cdb
    def new_cdb(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "New CDB File", "", "CDB Files (*.cdb)"
        )
        if not path:
            return
        creat_new_cdb(path)
        self.open_path(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow().show()
    sys.exit(app.exec())
