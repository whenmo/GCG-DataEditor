import sys
from DataBase import creat_new_cdb
from DataEditorFrom import DataEditor
from ItemLib import FileBtnToolBar
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QToolBar,
    QToolButton,
    QMenu,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    file_list: FileBtnToolBar
    dataeditor: DataEditor
    title: str

    def __init__(self):
        super().__init__()
        self.title = "Eternal Field DataEditor"
        self.setWindowTitle(self.title)
        self.resize(850, 650)

        # 工具列
        main_toolbar = QToolBar("main")
        self.addToolBar(main_toolbar)

        # ---------------- 文件 ----------------
        file_btn = QToolButton()
        file_btn.setText("文件")
        main_toolbar.addWidget(file_btn)

        # 文件 選單
        file_menu = QMenu()
        file_btn.setMenu(file_menu)
        file_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # 文件 選單內按鈕
        openfile_act = QAction("打開", self)
        file_menu.addAction(openfile_act)
        openfile_act.triggered.connect(self.open_cdb)

        newfile_act = QAction("新建", self)
        file_menu.addAction(newfile_act)
        newfile_act.triggered.connect(self.new_cdb)

        # ---------------- 檔案列表 ----------------
        self.addToolBarBreak()  # 讓下一個工具列換行，放在主工具列下方
        self.file_list = FileBtnToolBar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.file_list)

        # ---------------- 數據編輯器 ----------------
        self.dataeditor = DataEditor(self)
        self.setCentralWidget(self.dataeditor)

    # 開啟 cdb
    def open_cdb(self, path=None):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CDB File", "", "CDB Files (*.cdb)"
        )
        if not path:
            return
        self.file_list.add_cdbfile(path)

    # 新建 cdb
    def new_cdb(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "New CDB File", "", "CDB Files (*.cdb)"
        )
        if not path:
            return
        creat_new_cdb(path)
        # 建立 FileButtonWidget
        self.file_list.add_cdbfile(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow().show()
    sys.exit(app.exec())
