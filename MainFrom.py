import os
import sys
import sqlite3
import csv
import DataBase as DB
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QFileDialog,
    QToolBar,
    QToolButton,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QListWidget,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QTableView,
    QStatusBar,
    QComboBox,
)
from PyQt6.QtGui import (
    QAction,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QStandardItemModel,
    QStandardItem,
    QGuiApplication,
)
from PyQt6.QtCore import Qt, QRegularExpression, QPoint


class FileButtonWidget(QWidget):
    def __init__(self, filepath, main):
        super().__init__()
        self.filepath: str = filepath
        self.main: MainWindow = main
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

        self.cdb: DB.CDB = DB.Load_Cdb(self.filepath)
        self.main.update_card_lst(self.cdb)

    def load_file(self):
        self.main.update_card_lst(self.cdb)

    def remove_self(self):
        self.main.clear_card_lst()
        self.main.cdb_list.removeAction(self.action)
        self.deleteLater()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eternal Field DataEditor")
        self.resize(1000, 700)

        # 資料庫連線物件與最近查詢結果
        self.conn = None
        self.last_result = ([], [])

        # 工具列
        main_toolbar = QToolBar("main")
        self.addToolBar(main_toolbar)

        # cdb 列表
        self.addToolBarBreak()  # 讓下一個工具列換行，放在主工具列下方
        self.cdb_list = QToolBar("cdb_list")
        self.cdb_list.setFixedHeight(30)  # 固定高度 50px
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.cdb_list)

        # 文件 按鈕
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

        # ---------------- 左側表格 ----------------
        self.card_lst = QTableWidget()
        self.card_lst.setColumnCount(2)
        self.card_lst.setHorizontalHeaderLabels(["ID", "Name"])
        self.card_lst.verticalHeader().setVisible(False)
        self.card_lst.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # 設定欄位寬度與拉伸
        self.card_lst.setColumnWidth(0, 80)  # ID 固定寬度
        self.card_lst.horizontalHeader().setStretchLastSection(
            True
        )  # Name 欄位拉伸填滿

        # ---------------- 中間 SQL 編輯器 ----------------
        self.editor = QPlainTextEdit()
        # ---------------- 垂直分割器 ----------------
        rightSplitter = QSplitter(Qt.Orientation.Vertical)
        rightSplitter.addWidget(self.editor)
        dummy_bottom = QWidget()  # 如果想加下方其他區塊可以放這裡
        rightSplitter.addWidget(dummy_bottom)
        rightSplitter.setStretchFactor(0, 3)
        rightSplitter.setStretchFactor(1, 1)

        # ---------------- 水平分割器 ----------------
        mainSplitter = QSplitter(Qt.Orientation.Horizontal)
        mainSplitter.addWidget(self.card_lst)  # 左側
        mainSplitter.addWidget(rightSplitter)  # 中右側
        mainSplitter.setStretchFactor(0, 1)  # 左側表格
        mainSplitter.setStretchFactor(1, 3)  # 右側編輯器 + 下方

        # ---------------- 設置中央 Widget ----------------
        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(mainSplitter)
        central.setLayout(layout)
        self.setCentralWidget(central)

    # --- 開啟資料庫檔案 ---
    def open_cdb(self, path=None):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CDB File", "", "CDB Files (*.cdb);;All Files (*)"
        )
        if not path:
            return
        FileButtonWidget(path, self)

    # --- 新建資料庫檔案 ---
    def new_cdb(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "New CDB File", "", "CDB Files (*.cdb)"
        )
        if not path:
            return
        DB.creat_new_cdb(path)
        # 建立 FileButtonWidget
        FileButtonWidget(path, self)

    # --- 清空左側表格 ---
    def clear_card_lst(self):
        self.card_lst.setRowCount(0)

    # --- 更新左側表格 ---
    def update_card_lst(self, cdb: DB.CDB):
        self.clear_card_lst()
        self.card_lst.setRowCount(len(cdb.cards))

        for row, id in enumerate(cdb.cards.keys()):
            card = cdb.cards[id]
            # 更新 ID
            id_item = self.card_lst.item(row, 0)
            if id_item is None:
                id_item = QTableWidgetItem()
                self.card_lst.setItem(row, 0, id_item)
            id_item.setText(str(card.id))
            id_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            # 更新 Name
            name_item = self.card_lst.item(row, 1)
            if name_item is None:
                name_item = QTableWidgetItem()
                self.card_lst.setItem(row, 1, name_item)
            name_item.setText(card.name)
            name_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
