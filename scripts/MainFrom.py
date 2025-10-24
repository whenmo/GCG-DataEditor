import sys
import webbrowser
from ConfigLoader import load_config, update_history, save_config
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


def new_action(title: str, frame, menu: QMenu, func=None) -> QAction:
    act = QAction(title, frame)
    menu.addAction(act)
    if func:
        act.triggered.connect(func)
    return act


class MainWindow(QMainWindow):
    file_list: FileBtnToolBar
    dataeditor: DataEditor
    title: str
    act_paste: QAction
    hist_menu: QMenu
    config: dict

    def __init__(self):
        super().__init__()
        self.config = load_config()
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
        file_menu.addSeparator()
        act_copy_sel = new_action("复制选中卡片", self, file_menu)
        act_copy_all = new_action("复制所有卡片", self, file_menu)
        self.act_paste = new_action("粘贴卡片", self, file_menu)
        # ---------------- 歷史 ----------------
        self.hist_menu = new_toolbtn("数据库历史", main_toolbar)
        self.updata_hist_menu()
        # ---------------- 幫助 ----------------
        help_menu = new_toolbtn("帮助", main_toolbar)
        new_action("关于", self, help_menu, self.about_info)
        new_action("github", self, help_menu, self.go_github)
        # ---------------- 檔案列表 ----------------
        self.addToolBarBreak()  # 讓下一個工具列換行，放在主工具列下方
        self.file_list = FileBtnToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.file_list)
        # ---------------- 數據編輯器 ----------------
        self.dataeditor = DataEditor()
        self.setCentralWidget(self.dataeditor)
        # 綁定事件
        act_copy_sel.triggered.connect(self.dataeditor.copy_select_card)
        act_copy_all.triggered.connect(self.dataeditor.copy_all_card)
        self.act_paste.triggered.connect(self.dataeditor.paste_cards)

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

    # ---------------- 文件 ----------------
    # 根據路徑打開 cdb
    def open_path(self, path: str):
        self.add_hist_path(path)
        self.updata_hist_menu()
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

    # ---------------- 粘贴卡片 ----------------
    def update_paste_action_text(self, count: int):
        title = "粘贴卡片"
        if count > 0:
            title += f" ({count})"
        self.act_paste.setText(title)

    # ---------------- 歷史 ----------------
    # 獲取歷史列表
    def get_hist_list(self) -> list[str]:
        return self.config.get("DATABASE_HISTORY", {}).get("history_paths", [])

    # 更新歷史欄
    def updata_hist_menu(self):
        self.hist_menu.clear()
        hist_list = self.get_hist_list()
        for path in hist_list:
            new_action(
                path,
                self,
                self.hist_menu,
                lambda c, p=path: self.file_list.add_cdbfile(p),
            )
        self.hist_menu.addSeparator()
        new_action("清空历史纪录", self, self.hist_menu, self.clear_hist)

    # 增加歷史
    def add_hist_path(self, path: str):
        self.config = update_history(self.config, path)
        self.updata_hist_menu()

    # 刪除歷史
    def clear_hist(self):
        if "DATABASE_HISTORY" in self.config:
            self.config["DATABASE_HISTORY"]["history_paths"] = []
            save_config(self.config)
        self.updata_hist_menu()

    # ---------------- 幫助 ----------------
    # 關於
    def about_info(self):
        msg = "ver :  1.0\n作者 : whenmo"
        self.show_msg(msg)

    # github
    def go_github(self):
        url = "https://github.com/whenmo/Eternal-Field-DataEditor"
        webbrowser.open_new_tab(url)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow().show()
    sys.exit(app.exec())
