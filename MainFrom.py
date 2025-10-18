import os
import sys
import DataBase as DB
from CardInfo import Cardinfo, load_cardinfo
from ItemLib import (
    new_panel,
    ImageSet,
    IDSet,
    ComboboxSet,
    TypeSet,
    SetNameSet,
    MoveSet,
    HintSet,
)
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
    QSizePolicy,
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
    QPixmap,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QStandardItemModel,
    QStandardItem,
    QGuiApplication,
)
from PyQt6.QtCore import pyqtSignal, Qt, QRegularExpression, QPoint


# 檔案分頁按鈕
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
        self.main.update_left_widget(self.cdb)

    def load_file(self):
        self.main.update_left_widget(self.cdb)

    def remove_self(self):
        self.main.update_left_widget()
        self.main.cdb_list.removeAction(self.action)
        self.deleteLater()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eternal Field DataEditor")
        self.resize(850, 700)

        # 工具列
        main_toolbar = QToolBar("main")
        self.addToolBar(main_toolbar)

        # ---------------- 文件 ----------------
        file_btn: QToolButton = QToolButton()
        file_btn.setText("文件")
        main_toolbar.addWidget(file_btn)

        # 文件 選單
        file_menu: QMenu = QMenu()
        file_btn.setMenu(file_menu)
        file_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # 文件 選單內按鈕
        openfile_act: QAction = QAction("打開", self)
        file_menu.addAction(openfile_act)
        openfile_act.triggered.connect(self.open_cdb)

        newfile_act: QAction = QAction("新建", self)
        file_menu.addAction(newfile_act)
        newfile_act.triggered.connect(self.new_cdb)

        savefile_act: QAction = QAction("保存", self)
        file_menu.addAction(savefile_act)
        savefile_act.triggered.connect(lambda: print("保存被點擊"))

        # ---------------- cdb 列表 ----------------
        self.addToolBarBreak()  # 讓下一個工具列換行，放在主工具列下方
        self.cdb_list: QToolBar = QToolBar("cdb_list")
        self.cdb_list.setFixedHeight(30)  # 固定高度 50px
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.cdb_list)

        # ---------------- 左側容器 ----------------
        left_panel, left_frame = new_panel("V")

        # 卡片列表
        self.card_lst: QTableWidget = QTableWidget()
        self.card_lst.setColumnCount(2)
        self.card_lst.setHorizontalHeaderLabels(["ID", "Name"])
        self.card_lst.verticalHeader().setVisible(False)
        self.card_lst.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.card_lst.setColumnWidth(0, 80)
        self.card_lst.horizontalHeader().setStretchLastSection(True)
        left_frame.addWidget(self.card_lst)

        # 按鈕控制區
        down_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一頁")
        self.page_text = QLineEdit("1")
        self.page_text.setFixedWidth(40)
        self.page_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label = QLabel("/ 1")
        self.next_btn = QPushButton("下一頁")
        down_layout.addWidget(self.prev_btn)
        down_layout.addWidget(self.page_text)
        down_layout.addWidget(self.page_label)
        down_layout.addWidget(self.next_btn)
        down_layout.addStretch()
        left_frame.addLayout(down_layout)

        # ---------------- cardinfo ----------------
        self.cardinfo: Cardinfo = load_cardinfo()

        # ---------------- 中央容器 ----------------
        mid_panel, mid_frame = new_panel("V")

        # 卡名
        self.name = QLineEdit()
        mid_frame.addWidget(self.name)

        # ---------------- 中央子容器 ----------------
        # 包含 卡圖 以及 卡名 以外的 卡片細項
        mid_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 卡圖
        self.image: ImageSet = ImageSet(mid_splitter)

        # 卡片細項 widget
        detail_panel, detail_frame = new_panel("V")
        detail_frame.setAlignment(Qt.AlignmentFlag.AlignTop)  # 所有子組件靠上對齊
        mid_splitter.addWidget(detail_panel)

        # 卡片类型
        self.typ: TypeSet = TypeSet(self.cardinfo, detail_frame)

        # 字段
        self.setname: SetNameSet = SetNameSet(
            self.cardinfo.get_key("setname"), detail_frame
        )

        # id & alias
        self.id: IDSet = IDSet("ID", detail_frame)
        self.alias: IDSet = IDSet("同名卡", detail_frame)

        # 設定伸縮比例
        mid_splitter.setStretchFactor(0, 1)  # 卡圖
        mid_splitter.setStretchFactor(1, 2)  # 卡片細項

        # 將 splitter 加到中間 layout
        mid_frame.addWidget(mid_splitter)

        # 卡片描述
        self.desc = QPlainTextEdit()
        mid_frame.addWidget(self.desc)

        # 按鈕控制區
        down_layout = QHBoxLayout()
        self.search_btn = QPushButton("搜索")
        self.reset_btn = QPushButton("重置")
        self.script_btn = QPushButton("脚本")
        down_layout.addWidget(self.search_btn)
        down_layout.addWidget(self.reset_btn)
        down_layout.addWidget(self.script_btn)
        down_layout.addStretch()
        mid_frame.addLayout(down_layout)

        # ---------------- 右側容器 ----------------
        right_panel, right_frame = new_panel("V")

        # 卡片类型細項
        detail_label = QLabel("卡片细节")
        detail_label.setStyleSheet("""
            background-color: lightgray;
            color: black;
            padding: 2px;
        """)
        right_frame.addWidget(detail_label)

        # 生命
        self.life: ComboboxSet = ComboboxSet(
            self.cardinfo.get_key("life"), "0", right_frame
        )

        # 攻擊力 & 費用 & 陣營 & 種族
        self.atk: ComboboxSet = ComboboxSet(
            self.cardinfo.get_key("atk"), "0", right_frame
        )
        self.cost: ComboboxSet = ComboboxSet(
            self.cardinfo.get_key("cost"), "0", right_frame
        )
        self.from_: ComboboxSet = ComboboxSet(
            self.cardinfo.get_key("from"), "N/A", right_frame
        )
        self.race: ComboboxSet = ComboboxSet(
            self.cardinfo.get_key("race"), "N/A", right_frame
        )

        # 移動箭頭
        self.moveset: MoveSet = MoveSet(right_frame)
        right_frame.addStretch()

        # 脚本提示文字
        self.hint: HintSet = HintSet(right_frame)

        # 按鈕控制區
        down_layout = QHBoxLayout()
        self.addcard_btn = QPushButton("添加")
        self.setcard_btn = QPushButton("修改")
        self.delcard_btn = QPushButton("删除")
        down_layout.addWidget(self.addcard_btn)
        down_layout.addWidget(self.setcard_btn)
        down_layout.addWidget(self.delcard_btn)
        down_layout.addStretch()
        right_frame.addLayout(down_layout)

        # ---------------- 水平分割器 ----------------
        mainSplitter = QSplitter(Qt.Orientation.Horizontal)
        mainSplitter.addWidget(left_panel)  # 左側容器
        mainSplitter.addWidget(mid_panel)  # 中央容器
        mainSplitter.addWidget(right_panel)  # 右側容器
        mainSplitter.setStretchFactor(0, 1)  # 左側容器
        mainSplitter.setStretchFactor(1, 2)  # 中央容器
        mainSplitter.setStretchFactor(2, 3)  # 右側容器

        # ---------------- 設置中央 Widget ----------------
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(mainSplitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

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

    # --- 更新左側表格 ---
    def update_left_widget(self, cdb: DB.CDB | None = None):
        self.card_lst.setRowCount(0)
        if cdb is None:
            return

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
