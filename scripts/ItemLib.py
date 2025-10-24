import os
import re
from ConfigLoader import CardInfo, load_cardinfo
from DataBase import CDB, Card
from contextlib import contextmanager
from PyQt6.QtWidgets import (
    QToolBar,
    QSizePolicy,
    QLabel,
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QGridLayout,
    QCheckBox,
    QVBoxLayout,
    QLayout,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QFileDialog,
    QApplication,
)
import shutil
from PyQt6.QtGui import QPixmap, QTextCursor, QColor, QPainter, QBrush, QAction
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QTimer
from Global import get_main


# ---------- MainWindow item ----------
# 檔案分頁按鈕
class CdbFileBtn(QWidget):
    filepath: str
    fileBtn: QPushButton
    closeBtn: QPushButton
    cdb: CDB
    act: QAction
    style_select: str
    style_unselect: str

    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath
        self.style_select = "text-align: left; padding-left: 5px; background-color: rgb(180,200,255); color: black;"
        self.style_unselect = "text-align: left; padding-left: 5px;"

        # 檔案按鈕
        self.fileBtn = QPushButton(os.path.basename(self.filepath), self)
        self.fileBtn.setGeometry(0, 0, 100, 30)
        self.fileBtn.clicked.connect(self.on_clicked)

        # X 按鈕疊加在右上角
        self.closeBtn = QPushButton("X", self)
        self.closeBtn.setGeometry(75, 5, 20, 20)
        self.closeBtn.clicked.connect(self.remove_self)

        self.select()
        self.setFixedSize(100, 30)  # 容器大小
        QTimer.singleShot(0, self._ensure_main_visible)

    # 載入 cdb
    def set_cdb(self):
        self.cdb = CDB(self.filepath)
        main = get_main()
        if main:
            main.dataeditor.set_cdb(self.cdb)
        else:
            QTimer.singleShot(0, self._delayed_set_cdb)

    def _ensure_main_visible(self):
        main = get_main()
        if main:
            main.dataeditor.setVisible(True)

    def _delayed_set_cdb(self):
        main = get_main()
        if main:
            main.dataeditor.set_cdb(self.cdb)

    def set_action(self, action: QAction):
        self.act = action

    def on_clicked(self):
        """被點擊時：載入檔案並在 toolbar 中設為選中項。"""
        main = get_main()
        if main is None:
            return
        editor = main.dataeditor
        # 載入資料編輯器
        editor.set_cdb(self.cdb)
        editor.setVisible(True)
        # 設定 toolbar 選中
        try:
            tb: FileBtnToolBar = main.file_list
            idx = tb.file_list.index(self)
            tb.set_selected_index(idx)
        except Exception:
            pass

    def load_file(self):
        main = get_main()
        if main:
            main.dataeditor.set_cdb(self.cdb)

    def remove_self(self):
        main = get_main()
        if main:
            main.dataeditor.set_cdb()
        # 通知 toolbar 移除此 action
        try:
            main.file_list.remove_action(self.act)
        except Exception:
            # fallback
            try:
                main.file_list.removeAction(self.act)
            except Exception:
                pass
        self.deleteLater()

    def select(self):
        """將自己標為選中狀態（淺藍底、黑字）。"""
        self.fileBtn.setStyleSheet(self.style_select)
        self.closeBtn.setStyleSheet(self.style_select)
        main = get_main()
        if main:
            main.setWindowTitle(self.filepath)

    def deselect(self):
        """恢復預設樣式。"""
        main = get_main()
        self.fileBtn.setStyleSheet(self.style_unselect)
        self.closeBtn.setStyleSheet(self.style_unselect)
        if main:
            main.setWindowTitle(main.title)


# 檔案分頁列表
class FileBtnToolBar(QToolBar):
    index: int
    count: int
    file_list: list[CdbFileBtn]

    def __init__(self):
        super().__init__("file_list")
        self.setFixedHeight(30)
        self.index = -1
        self.count = 0
        self.file_list = []

    def add_cdbfile(self, filepath: str):
        """根據傳入路徑新增一個 cdb 檔案分頁（若已存在則不新增）"""
        # 基本路徑檢查
        if not (
            filepath
            and isinstance(filepath, str)
            and os.path.exists(filepath)
            and filepath.lower().endswith(".cdb")
        ):
            get_main().show_error(f"路径无效 {filepath}")
            return
        # 已存在相同路徑的分頁則指向該分頁
        for i, f in enumerate(self.file_list):
            if f.filepath == filepath:
                self.set_selected_index(i)
                self.file_list[i].load_file()
                return
        # 新增分頁
        if self.index != -1:
            self.file_list[self.index].deselect()

        cdb_file: CdbFileBtn = CdbFileBtn(filepath)
        self.index = self.count
        self.count += 1
        self.file_list.append(cdb_file)
        cdb_file.set_cdb()
        cdb_file.select()
        cdb_file.set_action(self.addWidget(cdb_file))

    def remove_action(self, action: QAction):
        # 找出要移除的 file_list 索引（若不存在則為 -1）
        removed_idx = next(
            (i for i, f in enumerate(self.file_list) if f.act == action), -1
        )
        # 先從工具列移除 QAction（若存在）
        try:
            self.removeAction(action)
        except Exception:
            pass

        # 從 internal list 移除對應 CdbFileBtn
        if removed_idx != -1:
            # 若被移除的是目前選中，先撤銷其樣式
            old_index = self.index
            if removed_idx == old_index and 0 <= old_index < len(self.file_list):
                try:
                    self.file_list[old_index].deselect()
                except Exception:
                    pass
            del self.file_list[removed_idx]
        else:
            # fallback：若找不到 index，過濾 list
            self.file_list = [f for f in self.file_list if f.act != action]

        # 更新計數
        old_index = self.index
        self.count = len(self.file_list)

        # 調整 self.index
        if removed_idx == -1:
            if self.index >= self.count:
                self.index = self.count - 1 if self.count > 0 else -1
        else:
            if removed_idx < old_index:
                self.index = old_index - 1
            elif removed_idx == old_index:
                if self.count == 0:
                    self.index = -1
                elif removed_idx - 1 >= 0:
                    self.index = removed_idx - 1
                else:
                    self.index = 0

        # 若有有效選中索引，載入該檔案
        if 0 <= self.index < self.count:
            try:
                # 確保樣式為選中
                self.file_list[self.index].select()
                self.file_list[self.index].load_file()
            except Exception:
                pass
        # 若沒有項目，隱藏 dataeditor
        if self.count == 0:
            get_main().dataeditor.setVisible(False)

    def set_selected_index(self, idx: int):
        """設定 toolbar 的選中項（會處理樣式與 index 更新）。"""
        if idx == self.index:
            return
        # 取消先前選中樣式
        if 0 <= self.index < len(self.file_list):
            try:
                self.file_list[self.index].deselect()
            except Exception:
                pass
        # 設定新選中（若有效）
        if 0 <= idx < len(self.file_list):
            self.index = idx
            try:
                self.file_list[self.index].select()
            except Exception:
                pass
        else:
            self.index = -1

    def get_file_btn(self) -> CdbFileBtn | None:
        """獲取當前指向的檔案按鈕"""
        if self.index == -1:
            return None
        return self.file_list[self.index]


# ---------- base item ----------
# frame組件
def new_frame(
    path: str, parent: QWidget | QLayout, space: int | None = None, cut: bool = True
) -> QLayout:
    if path == "V":
        frame: QLayout = QVBoxLayout()
    elif path == "H":
        frame: QLayout = QHBoxLayout()
    elif path == "G":
        frame: QLayout = QGridLayout()

    if cut:
        frame.setContentsMargins(0, 0, 0, 0)  # 去掉多餘邊距

    if space is not None:
        frame.setSpacing(space)

    if isinstance(parent, QLayout):
        parent.addLayout(frame)
    else:  # QWidget
        parent.setLayout(frame)

    return frame


# 新版面容器
def new_panel(path: str = "V", space: int | None = None) -> tuple[QWidget, QLayout]:
    panel: QWidget = QWidget()
    frame = new_frame(path, panel, space)
    return [panel, frame]


# 标题組件
def new_title(title: str, frame: QLayout):
    lab = QLabel(title)
    lab.setStyleSheet("""
        background-color: lightgray;
        color: black;
        padding: 2px;
    """)
    size_policy = lab.sizePolicy()
    size_policy.setVerticalPolicy(QSizePolicy.Policy.Fixed)  # 禁止垂直拉伸
    lab.setSizePolicy(size_policy)
    frame.addWidget(lab)


# 按鈕組件
def new_btn(
    title: str, frame: QLayout, clicked_func=None, style: str = ""
) -> QPushButton:
    btn = QPushButton(title)
    style = f"""
        QPushButton {{
            min-width: 100px;
            font-size: 12px;
            {style}
        }}
    """
    btn.setStyleSheet(style)
    btn.setFixedHeight(30)
    frame.addWidget(btn)
    if clicked_func:
        btn.clicked.connect(clicked_func)
    return btn


# ---------- DataEditor unit item ----------
# 不在從空白區按下並拖曳時產生高亮的 QTableWidget 子類
class CardTable(QTableWidget):
    def __init__(self, frame: QVBoxLayout):
        super().__init__()
        self._press_on_empty = False
        self._press_index = None

        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ID", "Name"])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.setColumnWidth(0, 80)
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁編輯
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # 禁選中
        self.setDragDropMode(QTableWidget.DragDropMode.NoDragDrop)  # 禁拖放
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: transparent;
                color: black;
            }
        """)
        frame.addWidget(self)

    def mousePressEvent(self, event):
        idx = self.indexAt(
            event.position().toPoint() if hasattr(event, "position") else event.pos()
        )
        if not idx.isValid():
            # 點在空白處：記錄並吞掉事件（不傳給父類以避免啟動選取/拖曳）
            self._press_on_empty = True
            self._press_index = None
            # 立即清除任何存在的選取（避免殘留高亮）
            self.clearSelection()
            return

        # 點在項目上：記錄索引，保留不啟動拖曳的行為，但允許產生 click
        self._press_on_empty = False
        self._press_index = idx
        # 仍然呼叫父類以確保 click 相關的內部狀態（但我們會在 move 時忽略拖曳）
        super().mousePressEvent(event)

    # 如果按住的是空白處或是從項目開始，忽略移動事件以避免高亮/選取改變
    def mouseMoveEvent(self, event):
        if self._press_on_empty or self._press_index is not None:
            return
        super().mouseMoveEvent(event)

    # 如果是從空白處開始按住，釋放時重置狀態並吞掉事件
    def mouseReleaseEvent(self, event):
        if self._press_on_empty:
            self._press_on_empty = False
            self._press_index = None
            return

        # 如果是從項目上按下（即使期間有移動），在放開時強制發出 itemClicked 以模擬 click
        if self._press_index is not None:
            row = self._press_index.row()
            col = self._press_index.column()
            item = self.item(row, col)
            if item is not None:
                # 手動發出信號（保持行為一致）
                try:
                    self.itemClicked.emit(item)
                except Exception:
                    pass
            # 重置狀態，並且不要呼叫父類以避免造成選取/高亮
            self._press_index = None
            return

        super().mouseReleaseEvent(event)


# 卡圖容器
class ImageSet(QLabel):
    default_path: str
    clicked = pyqtSignal()

    def __init__(self, frame: QLayout):
        super().__init__()
        self.setFixedSize(200, 285)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_path = "data/cover.jpg"
        self.set_image(self.default_path)

        frame.addWidget(self)

    def set_image(self, path: str = ""):
        # 只接受 .jpg 檔案，否則使用 default_path
        try:
            is_jpg = isinstance(path, str) and path.lower().endswith(".jpg")
        except Exception:
            is_jpg = False

        if not (is_jpg and os.path.exists(path)):
            path = self.default_path

        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.width(),
                self.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled_pixmap)

    # 讀取卡片並更新卡片文本
    def load_card(self, card: Card):
        # 以 cdb 檔案所在目錄為基底，載入 pics/c<id>.jpg
        img_dir = os.path.dirname(get_main().file_list.get_file_btn().cdb.path)
        img_path = os.path.join(img_dir, "pics", f"c{int(card.id)}.jpg")
        self.set_image(img_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ID組件
class IDSet(QWidget):
    id: QLineEdit
    alias: QLineEdit

    def __init__(self, frame: QLayout):
        super().__init__()
        main_frame: QVBoxLayout = new_frame("V", self)
        new_title("卡片ID", main_frame)

        id_panel, id_frame = new_panel("H")

        # 左側 id
        self.id = QLineEdit()
        self.id.setPlaceholderText("ID")
        self.id.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.id.returnPressed.connect(self.search_id)
        id_frame.addWidget(self.id)

        # 右側 alias
        self.alias = QLineEdit()
        self.alias.setPlaceholderText("规则上当作ID")
        self.alias.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        id_frame.addWidget(self.alias)

        main_frame.addWidget(id_panel)
        frame.addWidget(self)

    # 搜索 ID 開頭的卡
    def search_id(self):
        id = self.id.text()
        if not re.fullmatch(r"[0-9]+", id):
            id = ""
        main = get_main()
        main.dataeditor.card_list.search_id(id)
        main.dataeditor.updata()

    # 根據 card 設定卡片ID
    def load_card(self, card: Card):
        id = card.id
        alias = card.alias if card.alias != 0 else ""
        self.id.setText(str(id))
        self.alias.setText(str(alias))

    # 清空當前內容
    def clear(self):
        self.id.setText("")
        self.alias.setText("")

    # 獲取 id 與 同名卡
    def get_code(self):
        id = self.id.text() or "0"
        if not re.fullmatch(r"[0-9]+", id):
            id = "0"
        alias = self.alias.text() or "0"
        if not re.fullmatch(r"[0-9]+", alias):
            alias = "0"
        if id == alias and alias != "0":
            alias = "0"
        return int(id, 0), int(alias, 0)


# 下拉框組件
class ComboboxSet(QWidget):
    combobox: QComboBox

    def __init__(self, info: tuple[str, dict[str, str], str], frame: QLayout):
        super().__init__()
        self.combobox: QComboBox = QComboBox()

        title, key_dict, default = info

        main_frame: QHBoxLayout = new_frame("H", self)

        # 左側 Label
        lab: QLabel = QLabel(title)
        lab.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_frame.addWidget(lab)

        # 右側 combobox
        # self.combobox.setFixedWidth(80)  # 固定寬度
        main_frame.addWidget(self.combobox)
        for key, value in key_dict.items():
            self.combobox.addItem(key, value)
        index = self.combobox.findData(default)
        if index != -1:
            self.combobox.setCurrentIndex(index)

        # 讓 LineEdit 拉伸填滿剩餘空間
        main_frame.setStretch(0, 0)  # label 不拉伸
        main_frame.setStretch(1, 1)  # lineedit 拉伸

        frame.addWidget(self)

    def get_value(self) -> str:
        return self.combobox.currentData()

    def get_value_int(self) -> int:
        data = self.combobox.currentData()
        return int(data, 0) if isinstance(data, str) else int(data)

    def set_value(self, value: str):
        index = self.combobox.findData(value)
        if index != -1:
            self.combobox.setCurrentIndex(index)


# 卡片类型組件
class TypeSet(QWidget):
    main: QComboBox
    sub: QComboBox
    sub_data: dict[str, tuple[str, dict[str, str], str]]

    def __init__(self, info: CardInfo, frame: QLayout):
        super().__init__()
        self.sub_data = {}
        for key in ["monstyp", "calltyp", "banetyp", "areatyp"]:
            self.sub_data[key] = info.get_key(key)

        main_frame: QVBoxLayout = new_frame("V", self)
        new_title("卡片类型", main_frame)

        typ_panel, typ_frame = new_panel("H")

        # 左側 子类型 QComboBox
        self.sub = QComboBox()
        _, key_dict, default = self.sub_data["monstyp"]
        for key, value in key_dict.items():
            self.sub.addItem(key, value)
        index = self.sub.findData(default)
        if index != -1:
            self.sub.setCurrentIndex(index)
        typ_frame.addWidget(self.sub)

        # 右側 类型 QComboBox
        self.main = QComboBox()
        _, key_dict, default = info.get_key("typ")
        for key, value in key_dict.items():
            self.main.addItem(key, value)
        index = self.main.findData(default)
        if index != -1:
            self.main.setCurrentIndex(index)
        typ_frame.addWidget(self.main)

        main_frame.addWidget(typ_panel)
        frame.addWidget(self)

        self._update_sub_combobox()
        self.main.currentIndexChanged.connect(self._update_sub_combobox)

        frame.addWidget(self)

    def _update_sub_combobox(self):
        _, key_dict, default = self.sub_data[self.main.currentData()]
        self.sub.clear()
        for key, value in key_dict.items():
            self.sub.addItem(key, value)
        index = self.sub.findData(default)
        if index != -1:
            self.sub.setCurrentIndex(index)

    def celear(self):
        self.main.setCurrentIndex(self.main.findData("monstyp"))
        self.sub.setCurrentIndex(self.sub.findData("0x1"))

    # 根據 card 設定卡片ID
    def load_card(self, card: Card):
        typ = card.type
        main_typ = {
            0x1: "monstyp",
            0x2: "calltyp",
            0x4: "banetyp",
            0x8: "areatyp",
        }[typ & 0xF]
        self.main.setCurrentIndex(self.main.findData(main_typ))
        sub_typ = f"0x{typ:X}"
        self.sub.setCurrentIndex(self.sub.findData(sub_typ))

    def get_type(self) -> int:
        return int(self.sub.currentData(), 16)


# 字段組件
class SetNameSet(QWidget):
    comboboxs: list[QComboBox]
    lineedits: list[QLineEdit]
    copybtns: list[QPushButton]
    _updating: bool

    def __init__(self, info: tuple[str, dict[str, str]], frame: QLayout):
        super().__init__()
        self.comboboxs: list[QComboBox] = []
        self.lineedits: list[QLineEdit] = []
        self._updating = False

        setname_dict: dict[str, str] = info[1]
        names: list[str] = setname_dict.keys()
        values: list[str] = setname_dict.values()

        main_frame: QVBoxLayout = new_frame("V", self)
        new_title("卡片字段", main_frame)
        for _ in range(4):
            # 水平 layout
            row_panel, row_frame = new_panel("H")
            # 左側 combobox 初始化
            set_cb = QComboBox()
            row_frame.addWidget(set_cb)
            for setname, value in zip(names, values):
                set_cb.addItem(setname, value.upper())
            # 中央 LineEdit
            set_le = QLineEdit("0")
            set_le.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            set_le.setFixedWidth(80)  # 固定寬度
            row_frame.addWidget(set_le)
            # 右側 copy buttom
            copy_btn = QPushButton("复制")
            copy_btn.setFixedWidth(50)
            row_frame.addWidget(copy_btn)
            # 綁定事件
            set_cb.currentIndexChanged.connect(
                lambda idx, le=set_le, cb=set_cb: self._combobox_changed(cb, le)
            )
            set_le.textChanged.connect(
                lambda text, le=set_le, cb=set_cb: self._lineedit_changed(le, cb)
            )
            copy_btn.clicked.connect(lambda chk, le=set_le: self._copy_value(le))
            main_frame.addWidget(row_panel)
            self.comboboxs.append(set_cb)
            self.lineedits.append(set_le)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        frame.addWidget(self)

    @contextmanager
    def updating_block(self):
        self._updating = True
        try:
            yield
        finally:
            self._updating = False

    def _combobox_changed(self, combobox: QComboBox, lineedit: QLineEdit):
        if self._updating:
            return
        with self.updating_block():
            val_str: str = str(combobox.currentData())
            if val_str == "-1" or val_str == "None":
                val_str = "FFFF"
            else:
                val_str = val_str[2:].upper()
            lineedit.setText(val_str)

    def _lineedit_changed(self, lineedit: QLineEdit, combobox: QComboBox):
        if self._updating:
            return
        with self.updating_block():
            ind, _ = self.get_key_val(lineedit.text())
            combobox.setCurrentIndex(ind)

    def _copy_value(self, le: QLineEdit):
        val = le.text().upper()
        if not val.startswith("0X"):
            val = f"0X{val}"
        QApplication.clipboard().setText(val)

    def get_setname(self) -> int:
        res = 0
        for i, lineedit in enumerate(self.lineedits):
            val_str = (lineedit.text() or "0").upper()
            if val_str.startswith("0X"):
                val_str = val_str[2:]
            if re.fullmatch(r"[0-9A-F]+", val_str):
                res += int(val_str, 16) << (i * 16)
        return res

    # 獲取字段值對應的 combobox 索引與標準化十六進制字串
    def get_key_val(self, val: str | int) -> tuple[int, str]:
        val_str: str = "0"
        if isinstance(val, int):
            val_str = f"{val:X}"
        elif isinstance(val, str):
            val_str = val.upper()
            if val_str.startswith("0X"):
                val_str = val_str[2:]
            if len(val_str) > 4 or not re.fullmatch(r"[0-9A-F]+", val_str):
                val_str = "0"
        # 沒有則為 -1 (自定義
        index = self.comboboxs[0].findData("0X" + val_str)
        if index == -1:
            index = self.comboboxs[0].findData("-1")
        return (index, val_str)

    # 設定單個字段組件
    def set_unit(self, ind: int, val: str | int):
        index, txt = self.get_key_val(val)
        self.comboboxs[ind].setCurrentIndex(index)
        self.lineedits[ind].setText(txt)

    # 設定整個字段組件
    def set_value(self, setcode: int):
        vals_str: list[str] = ["0"] * 4
        if isinstance(setcode, int):
            for i in range(4):
                val = setcode & 0xFFFF
                vals_str[i] = f"{val:X}"
                setcode >>= 16
        for i in range(4):
            self.set_unit(i, vals_str[i])

    # 根據 card 設定卡片字段
    def load_card(self, card: Card):
        self.set_value(card.setcode)


# 移動標組件
class MoveSet(QWidget):
    checkboxes: list[QCheckBox]

    def __init__(self, frame: QLayout):
        super().__init__()
        main_frame: QHBoxLayout = new_frame("H", self)

        # 左側 Label
        lab = QLabel("移动方向")
        lab.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_frame.addWidget(lab)

        # 右側 GridLayout
        grid_panel, grid_frame = new_panel("G", 2)

        self.checkboxes = []
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
        for i, pos in enumerate(positions):
            cb = QCheckBox()
            self.checkboxes.append(cb)
            grid_frame.addWidget(cb, pos[0], pos[1])

        main_frame.addWidget(grid_panel)
        grid_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        frame.addWidget(self)

    def get_move(self) -> int:
        value = 0
        for i, cb in enumerate(self.checkboxes):
            if cb.isChecked():
                value |= 1 << i
        return value

    def clear(self):
        for _, cb in enumerate(self.checkboxes):
            cb.setChecked(False)

    # 讀取卡片並更新卡片資料
    def load_card(self, card: Card):
        move = card.move
        for i, cb in enumerate(self.checkboxes):
            cb.setChecked((move & (1 << i)) != 0)


class HintSetTextArea(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        # 禁止自動換行
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        # 設定字體
        font = self.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.setFont(font)
        # 開始打字的位置
        self.setViewportMargins(17, 0, 0, 0)
        # 繪製行號欄
        cr = self.contentsRect()
        HintSetLineArea(self).setGeometry(QRect(cr.left(), cr.top(), 17, cr.height()))
        # 預設內容
        self.setPlainText("\n" * 15)


class HintSetLineArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)

    def paintEvent(self, event):
        painter = QPainter(self)
        top, offset = 4, 15
        for i in range(16):
            painter.drawText(
                0,
                top,
                self.width() - 1,
                15,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(i),
            )
            top += offset

        # 分隔線
        painter.setPen(QColor(180, 180, 180))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


# 脚本提示組件
class HintSet(QWidget):
    hint: HintSetTextArea

    def __init__(self, frame: QLayout):
        super().__init__()
        self.hint = HintSetTextArea()
        main_frame: QVBoxLayout = new_frame("V", self)
        new_title("脚本提示文字", main_frame)
        # 脚本提示
        self.hint.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        main_frame.addWidget(self.hint)
        # 禁用滾動條
        self.hint.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 監聽文字變動
        self.hint.textChanged.connect(self._on_text_changed)

        frame.addWidget(self)

    def _on_text_changed(self):
        cursor = self.hint.textCursor()
        block_num = cursor.blockNumber()  # 行號
        col = cursor.positionInBlock()  # 列號

        text = self.hint.toPlainText()
        lines = text.splitlines()

        if len(lines) < 16:
            lines += [""] * (16 - len(lines))
        elif len(lines) > 16:
            lines = lines[:16]

        corrected = "\n".join(lines)

        if corrected != text:
            self.hint.blockSignals(True)
            self.hint.setPlainText(corrected)
            # 恢復光標到原行列
            new_cursor = self.hint.textCursor()
            new_cursor.movePosition(QTextCursor.MoveOperation.Start)
            new_cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.MoveAnchor,
                block_num,
            )
            new_cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.MoveAnchor,
                col,
            )
            self.hint.setTextCursor(new_cursor)
            self.hint.blockSignals(False)

    def get_hints(self) -> list[str]:
        text = self.hint.toPlainText()
        lines = text.splitlines()
        return lines[:16]

    def clear(self):
        self.hint.setPlainText("\n" * 15)

    def load_card(self, card: Card):
        self.hint.setPlainText("\n".join(card.hints))


# ---------- DataEditor item ----------
# 卡片列表組件
class CardListSet(QWidget):
    # 控件
    card_lst: QTableWidget
    prev_btn: QPushButton
    page_text: QLineEdit
    page_label: QLabel
    next_btn: QPushButton
    # 卡片列表屬性
    cdb: CDB | None
    id_to_row: dict[int, int]
    # 前後頁屬性
    rows_per_page: int = 10  # 默認值，可被自動覆蓋
    now_page: int = 1
    total_page: int = 1

    def __init__(self):
        super().__init__()
        self.id_to_row = {}
        self.cdb = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        main_frame = new_frame("V", self)
        # 卡片列表
        self.card_lst = CardTable(main_frame)
        self.card_lst.itemClicked.connect(self.on_item_clicked)
        # 按鈕控制區
        page_frame: QHBoxLayout = new_frame("H", main_frame)
        page_frame.addStretch()
        self.prev_btn = new_btn("上一頁", page_frame, self.prev_page)
        self.page_text = QLineEdit("1")
        self.page_text.setStyleSheet("font-size: 12px;")
        self.page_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_text.returnPressed.connect(self.goto_page)
        page_frame.addWidget(self.page_text)
        self.page_label = QLabel("/ 1")
        self.page_label.setStyleSheet("font-size: 12px;")
        page_frame.addWidget(self.page_label)
        self.next_btn = new_btn("下一頁", page_frame, self.next_page)
        page_frame.addStretch()

    # ---------------- 內部事件 ----------------
    def showEvent(self, event):
        super().showEvent(event)
        self.calc_rows_per_page()
        self.refresh_view()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_view()

    # 上一頁
    def prev_page(self):
        if self.now_page > 1:
            self.now_page -= 1
            self.refresh_view()

    # 下一頁
    def next_page(self):
        if self.now_page < self.total_page:
            self.now_page += 1
            self.refresh_view()

    # 跳轉到指定頁
    def goto_page(self):
        try:
            page = int(self.page_text.text())
        except ValueError:
            page = self.now_page
        if 1 <= page <= self.total_page:
            self.now_page = page
            self.refresh_view()
        else:
            self.page_text.setText(str(self.now_page))

    # 點擊時事件
    def on_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        id_item = self.card_lst.item(row, 0)
        clicked_id = int(id_item.text())
        modifiers = QApplication.keyboardModifiers()
        # ------------------ 處理 Shift 範圍選擇 ------------------
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            pre_id = self.cdb.now_id
            keys = self.cdb.show_id_lst
            if keys and pre_id != 0:
                try:
                    ind_st = keys.index(pre_id)
                    ind_ed = keys.index(clicked_id)
                except ValueError:  # 如果 ID 不在當前列表
                    ind_st, ind_ed = -1, -1
                if ind_st != -1:
                    range_st = min(ind_st, ind_ed)
                    range_ed = max(ind_st, ind_ed)
                    self.cdb.select_id_lst.clear()
                    for i in range(range_st, range_ed + 1):
                        self.cdb.select_id_lst.add(keys[i])
        # ------------------ 處理 Ctrl 選擇 ------------------
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            if clicked_id in self.cdb.select_id_lst:
                if len(self.cdb.select_id_lst) > 1:
                    self.cdb.select_id_lst.remove(clicked_id)
            else:
                self.cdb.select_id_lst.add(clicked_id)
        # ------------------ 單擊 ------------------
        else:
            self.cdb.select_id_lst.clear()
            self.cdb.select_id_lst.add(clicked_id)

        self.cdb.now_id = clicked_id
        self.refresh_view()
        get_main().dataeditor.updata()

    # 處理上下鍵移動 now_ind 到前一個/下一個
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Up:
            self._move_index(-1)
            return
        elif key == Qt.Key.Key_Down:
            self._move_index(1)
            return
        super().keyPressEvent(event)

    def _move_index(self, delta: int):
        """根據目前 self.cdb.show_id_lst 的順序移動 now_ind 並觸發 on_item_clicked。"""
        if self.cdb is None or not self.cdb.show_id_lst:
            return
        keys = self.cdb.show_id_lst
        try:
            cur_idx = keys.index(self.cdb.now_id)
        except ValueError:  # 若沒有選擇，從 -1 開始
            cur_idx = -1
        new_idx = cur_idx + delta
        if new_idx < 0 or new_idx >= len(keys):
            return  # 超出範圍則不動作
        new_page = (new_idx // self.rows_per_page) + 1
        # 目標行在當前頁，直接觸發 on_item_clicked
        if new_page == self.now_page:
            cur_row = new_idx % self.rows_per_page
        else:
            self.now_page = new_page
            self.refresh_view()
            if delta == 1:
                cur_row = 0
            else:
                cur_row = self.card_lst.rowCount() - 1

        self.on_item_clicked(self.card_lst.item(cur_row, 0))
        self.setFocus()

    def calc_rows_per_page(self):
        # 顯示欄數 = 卡片列表 widget 高度 / 單行高度
        show_row = self.card_lst.viewport().height() // 30
        self.rows_per_page = max(1, show_row)

    def clear_filter(self):
        if self.cdb is None:
            return
        all_ids = sorted(self.cdb.card_dict.keys(), key=lambda k: int(k))
        self.cdb.show_id_lst = all_ids
        if self.cdb.now_id not in self.cdb.show_id_lst and self.cdb.show_id_lst:
            self.cdb.now_id = self.cdb.show_id_lst[0]
        try:
            now_idx = self.cdb.show_id_lst.index(self.cdb.now_id)
            self.current_page = (now_idx // self.rows_per_page) + 1
        except ValueError:
            self.current_page = 1
        self.refresh_view()

    def search_id(self, id: str):
        if self.cdb is None:
            return
        self.cdb.search_id(id)
        self.now_page = 1
        self.refresh_view()

    def search_name(self, name: str):
        if self.cdb is None:
            return
        self.cdb.search_name(name)
        self.now_page = 1
        self.refresh_view()

    def refresh_view(self):
        """根據當前的 cdb 和過濾列表刷新 QTableWidget 的內容"""
        self.card_lst.setRowCount(0)
        if self.cdb is None:
            self.total_page = 1
            self.page_text.setText(str(self.now_page))
            self.page_label.setText(f"/ {self.total_page}")
            return

        keys = self.cdb.show_id_lst if self.cdb else []
        self.calc_rows_per_page()
        self.total_page = max(
            1, (len(keys) + self.rows_per_page - 1) // self.rows_per_page
        )
        # 頁碼校正
        if self.now_page > self.total_page:
            self.now_page = self.total_page
        # 更新 page_text 與 page_label
        self.page_text.setText(str(self.now_page))
        self.page_label.setText(f"/ {self.total_page}")
        # 計算當前頁的索引範圍
        st_ind = (self.now_page - 1) * self.rows_per_page
        ed_ind = min(st_ind + self.rows_per_page, len(keys))
        self.card_lst.setRowCount(ed_ind - st_ind)
        self.id_to_row.clear()
        # 填充表格
        for row, key_idx in enumerate(range(st_ind, ed_ind)):
            card_id = keys[key_idx]
            card = self.cdb.card_dict[card_id]
            self.id_to_row[int(card.id)] = row
            is_selected = card_id in self.cdb.select_id_lst
            for col, txt in enumerate([str(card.id), card.name]):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                if is_selected:  # 使用淺藍色作為選中高亮
                    item.setBackground(QColor(180, 200, 255))
                    item.setForeground(QColor(0, 0, 0))
                else:  # 重置為預設背景
                    item.setBackground(QBrush())
                    item.setForeground(QBrush())
                self.card_lst.setItem(row, col, item)

    # ---------------- 設定數據 ----------------
    def set_data_source(self, cdb: CDB | None = None):
        """設定卡片資料庫 (CDB) 並初始化卡片索引和過濾列表"""
        self.cdb = cdb
        if cdb is None:
            self.now_page = 1
            return
        try:
            now_idx = self.cdb.show_id_lst.index(self.cdb.now_id)
            self.now_page = (now_idx // self.rows_per_page) + 1
        except (ValueError, AttributeError):
            self.now_page = 1

    # 增加卡片
    def add_card(self, card: Card):
        if self.cdb:
            self.cdb.add_card(card)
            try:
                now_idx = self.cdb.show_id_lst.index(self.cdb.now_id)
                self.current_page = (now_idx // self.rows_per_page) + 1
            except ValueError:
                self.current_page = 1

            self.refresh_view()
            get_main().dataeditor.updata()

    # ---------------- 獲取數據 ----------------
    # 傳回當前卡片
    def get_now_card(self) -> Card | None:
        if self.cdb is None or self.cdb.now_id == 0:
            return None
        return self.cdb.get_card(self.cdb.now_id)


# 卡片資料組件
class CardDataSet(QWidget):
    code: IDSet
    setname: SetNameSet
    typ: TypeSet
    life: ComboboxSet
    atk: ComboboxSet
    cost: ComboboxSet
    from_: ComboboxSet
    race: ComboboxSet
    moveset: MoveSet

    def __init__(self, frame: QLayout):
        super().__init__()
        # cardinfo
        cardinfo: CardInfo = load_cardinfo()
        # id & alias
        self.code = IDSet(frame)
        # 字段
        self.setname = SetNameSet(cardinfo.get_key("setname"), frame)
        # 卡片类型
        self.typ = TypeSet(cardinfo, frame)
        new_title("卡片细节", frame)
        # 生命
        self.life: ComboboxSet = ComboboxSet(cardinfo.get_key("life"), frame)
        # 費用 & 攻擊力 & 陣營 & 種族
        self.cost: ComboboxSet = ComboboxSet(cardinfo.get_key("cost"), frame)
        self.atk: ComboboxSet = ComboboxSet(cardinfo.get_key("atk"), frame)
        self.from_: ComboboxSet = ComboboxSet(cardinfo.get_key("from"), frame)
        self.race: ComboboxSet = ComboboxSet(cardinfo.get_key("race"), frame)
        # 移動箭頭
        self.moveset: MoveSet = MoveSet(frame)

    # ---------------- 設定數據 ----------------
    # 讀取卡片並更新卡片資料
    def load_card(self, card: Card):
        self.code.load_card(card)
        self.setname.load_card(card)
        self.typ.load_card(card)
        life, cost = 0, card.value
        if card.type & 0x8:
            life, cost = cost, life
        self.life.set_value(f"{life}")
        self.cost.set_value(f"{cost}")
        self.atk.set_value(f"{card.atk}")
        self.from_.set_value(f"0x{card.from_:X}")
        self.race.set_value(f"0x{card.race:X}")
        self.moveset.load_card(card)

    # 清空當前內容
    def clear(self):
        self.code.clear()
        self.setname.set_value(0)
        self.typ.celear()
        self.life.set_value("0")
        self.cost.set_value("0")
        self.atk.set_value("0")
        self.from_.set_value("0x0")
        self.race.set_value("0x0")
        self.moveset.clear()

    # ---------------- 獲取數據 ----------------
    # code
    def get_code(self) -> tuple[int, int]:
        id, alias = self.code.get_code()
        return (id, alias)

    # setname
    def get_setname(self) -> int:
        return self.setname.get_setname()

    # data list (no alias
    def get_data_list(self) -> list[int]:
        res_lst = []
        res_lst.append(self.get_setname())
        typ = self.typ.get_type()
        res_lst.append(typ)
        value = 0
        if typ & 0x8:  # area
            value = self.life.get_value_int()
        else:
            value = self.cost.get_value_int()
        res_lst.append(value)
        res_lst.append(self.atk.get_value_int())
        res_lst.append(self.moveset.get_move())
        res_lst.append(self.race.get_value_int())
        res_lst.append(self.from_.get_value_int())
        return res_lst


# 卡片文本組件
class CardTextSet(QWidget):
    name: QLineEdit
    image: ImageSet
    hint: HintSet
    desc: QPlainTextEdit
    gene_desc: QPlainTextEdit

    def __init__(self, frame: QLayout):
        super().__init__()
        # 卡名
        self.name = QLineEdit()
        self.name.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 文字置中
        self.name.returnPressed.connect(self.search_name)
        frame.addWidget(self.name)

        # 卡圖 & 脚本提示文字
        image_panel, image_frame = new_panel("H")
        image_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        frame.addWidget(image_panel)

        self.image = ImageSet(image_frame)
        self.image.clicked.connect(self._on_image_clicked)
        self.hint = HintSet(image_frame)
        self.hint.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # 卡片描述
        self.desc = QPlainTextEdit()
        self.desc.setPlaceholderText("卡片描述")
        frame.addWidget(self.desc)
        # 進化元效果
        self.gene_desc = QPlainTextEdit()
        self.gene_desc.setPlaceholderText("进化元效果")
        font_metrics = self.gene_desc.fontMetrics()
        line_height = font_metrics.lineSpacing()  # 每行行高（含間距）
        self.gene_desc.setFixedHeight(line_height * 5 + 8)  # 顯示約5行，+8留邊距
        frame.addWidget(self.gene_desc)

    # ---------------- 內部事件 ----------------
    # 搜索 name 開頭的卡
    def search_name(self):
        name = self.name.text()
        main = get_main()
        main.dataeditor.card_list.search_name(name)
        main.dataeditor.updata()

    # 點擊時導入卡圖
    def _on_image_clicked(self):
        # 檢查是否存在當前卡
        main = get_main()
        if (card := main.dataeditor.card_list.get_now_card()) is None:
            return
        # 選擇檔案
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择卡图", "", "Images (*.jpg);;All Files (*)"
        )
        if not file_path:
            return

        cdb_dir = os.path.dirname(main.windowTitle())
        pics_dir = os.path.join(cdb_dir, "pics")
        os.makedirs(pics_dir, exist_ok=True)
        img_path = os.path.join(pics_dir, f"c{int(card.id)}.jpg")

        shutil.copyfile(file_path, img_path)
        self.image.set_image(img_path)

    # ---------------- 設定數據 ----------------
    # 讀取卡片並更新卡片文本
    def load_card(self, card: Card):
        self.name.setText(card.name)
        self.hint.load_card(card)
        self.image.load_card(card)
        desc = card.desc
        gene_desc = ""
        desc_lst = desc.splitlines()
        for i, line in enumerate(desc_lst):
            if line.startswith("【进化元效果】"):
                desc = "\n".join(desc_lst[:i])
                gene_desc = "\n".join(desc_lst[i + 1 :])
        self.desc.setPlainText(desc)
        self.gene_desc.setPlainText(gene_desc)

    # 清空當前內容
    def clear(self):
        self.name.setText("")
        self.hint.clear()
        self.desc.setPlainText("")
        self.gene_desc.setPlainText("")
        self.image.set_image("")

    # ---------------- 獲取數據 ----------------
    # text list
    def get_text_list(self, is_mons: bool) -> list[str]:
        res_lst = [self.name.text()]
        desc = self.desc.toPlainText()
        if is_mons and (gene := self.gene_desc.toPlainText()):
            desc += "\n【进化元效果】\n" + gene
        res_lst.append(desc)
        res_lst += self.hint.get_hints()

        return res_lst
