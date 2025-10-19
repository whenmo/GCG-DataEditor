import os
import sys
from DataBase import CDB, load_cdb, creat_new_cdb
from DataEditorFrom import DataEditor
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QFileDialog,
    QToolBar,
    QToolButton,
    QMenu,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    cdb_list: QToolBar
    dataeditor: DataEditor

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eternal Field DataEditor")
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

        savefile_act = QAction("保存", self)
        file_menu.addAction(savefile_act)
        savefile_act.triggered.connect(lambda: print("保存被點擊"))

        # ---------------- cdb 列表 ----------------
        self.addToolBarBreak()  # 讓下一個工具列換行，放在主工具列下方
        self.cdb_list = QToolBar("cdb_list")
        self.cdb_list.setFixedHeight(30)  # 固定高度 50px
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.cdb_list)

        # ---------------- 數據編輯器 ----------------
        self.dataeditor = DataEditor()
        self.setCentralWidget(self.dataeditor)

    # --- 開啟資料庫檔案 ---
    def open_cdb(self, path=None):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CDB File", "", "CDB Files (*.cdb);;All Files (*)"
        )
        if not path:
            return
        CdbFileBtn(path, self)

    # --- 新建資料庫檔案 ---
    def new_cdb(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "New CDB File", "", "CDB Files (*.cdb)"
        )
        if not path:
            return
        creat_new_cdb(path)
        # 建立 FileButtonWidget
        CdbFileBtn(path, self)


# 檔案分頁按鈕
class CdbFileBtn(QWidget):
    filepath: str
    main: MainWindow
    fileBtn: QPushButton
    closeBtn: QPushButton
    action: QAction
    cdb: CDB
    now_ind: int

    def __init__(self, filepath: str, main: MainWindow):
        super().__init__()
        self.filepath = filepath
        self.main = main
        self.setFixedSize(100, 30)  # 容器大小

        # 檔案按鈕
        self.fileBtn = QPushButton(os.path.basename(self.filepath), self)
        self.fileBtn.setGeometry(0, 0, 100, 30)
        self.fileBtn.setStyleSheet("text-align: left; padding-left: 5px;")
        self.fileBtn.clicked.connect(self.load_file)

        # X 按鈕疊加在右上角
        self.closeBtn = QPushButton("X", self)
        self.closeBtn.setGeometry(75, 5, 20, 20)
        self.closeBtn.clicked.connect(self.remove_self)

        # 將 widget 加到工具列
        self.action = self.main.cdb_list.addWidget(self)

        self.cdb = load_cdb(self.filepath)
        self.now_ind = self.cdb.get_first_id()
        self.main.dataeditor.set_cdb(self.cdb, self.now_ind)

    def load_file(self):
        self.main.dataeditor.set_cdb(self.cdb, self.now_ind)

    def remove_self(self):
        self.main.dataeditor.set_cdb()
        self.main.cdb_list.removeAction(self.action)
        self.deleteLater()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
