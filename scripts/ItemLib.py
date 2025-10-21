import os
import re
from CardInfo import Cardinfo
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
    QMessageBox,
)
import shutil
from PyQt6.QtGui import QPixmap, QTextCursor, QColor, QPainter, QBrush, QAction
from PyQt6.QtCore import pyqtSignal, Qt, QRect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainFrom import MainWindow


# ---------- MainWindow item ----------
# 檔案分頁按鈕
class CdbFileBtn(QWidget):
    main: "MainWindow"
    filepath: str
    fileBtn: QPushButton
    closeBtn: QPushButton
    cdb: CDB
    card_index: int
    act: QAction
    style_select: str
    style_unselect: str

    def __init__(self, filepath: str, main: "MainWindow"):
        super().__init__()
        self.filepath = filepath
        self.main = main
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
        self.main.dataeditor.setVisible(True)

    # 載入 cdb
    def set_cdb(self):
        self.cdb = CDB(self.filepath)
        self.card_index = self.cdb.get_first_id()
        self.main.dataeditor.set_cdb(self.cdb, self.card_index)

    def set_action(self, action: QAction):
        self.act = action

    def on_clicked(self):
        """被點擊時：載入檔案並在 toolbar 中設為選中項。"""
        # 載入資料編輯器
        self.main.dataeditor.set_cdb(self.cdb, self.card_index)
        self.main.dataeditor.setVisible(True)
        # 設定 toolbar 選中
        try:
            tb: FileBtnToolBar = self.main.file_list
            idx = tb.file_list.index(self)
            tb.set_selected_index(idx)
        except Exception:
            pass

    def load_file(self):
        self.main.dataeditor.set_cdb(self.cdb, self.card_index)

    def remove_self(self):
        self.main.dataeditor.set_cdb()
        # 通知 toolbar 移除此 action
        try:
            self.main.file_list.remove_action(self.act)
        except Exception:
            # fallback
            try:
                self.main.file_list.removeAction(self.act)
            except Exception:
                pass
        self.deleteLater()

    def select(self):
        """將自己標為選中狀態（淺藍底、黑字）。"""
        self.fileBtn.setStyleSheet(self.style_select)
        self.closeBtn.setStyleSheet(self.style_select)
        self.main.setWindowTitle(self.filepath)

    def deselect(self):
        """恢復預設樣式。"""
        self.fileBtn.setStyleSheet(self.style_unselect)
        self.closeBtn.setStyleSheet(self.style_unselect)
        self.main.setWindowTitle(self.main.title)


# 檔案分頁列表
class FileBtnToolBar(QToolBar):
    main: "MainWindow"
    index: int
    count: int
    file_list: list[CdbFileBtn]

    def __init__(self, main: "MainWindow"):
        super().__init__("file_list")
        self.main = main
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
            QMessageBox.warning(self.main, "檔案不存在", f"路径无效{filepath}")
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

        cdb_file: CdbFileBtn = CdbFileBtn(filepath, self.main)
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
            self.main.dataeditor.setVisible(False)

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

    # 根據 card 設定卡片ID
    def load_card(self, card: Card):
        id = card.id
        alias = card.alias if card.alias != 0 else ""
        self.id.setText(str(id))
        self.alias.setText(str(alias))

    # 獲取 id 與 同名卡
    def get_code(self):
        id = self.id.text() or "0"
        if not re.fullmatch(r"[0-9]+", id):
            id = "0"
        alias = self.id.text() or "0"
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

    def __init__(self, info: Cardinfo, frame: QLayout):
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

    # 根據 card 設定卡片ID
    def load_card(self, card: Card):
        typ = card.type
        main_typ = {
            0x1: "monstyp",
            0x2: "calltyp",
            0x4: "banetyp",
            0x8: "areatyp",
        }[typ & 0xF]
        # sub_typ = typ & 0xFF0
        self.main.setCurrentIndex(self.main.findData(main_typ))

    def get_type(self) -> int:
        return int(self.sub.currentData(), 16)


# 字段組件
class SetNameSet(QWidget):
    comboboxs: list[QComboBox]
    lineedits: list[QLineEdit]
    _updating: bool

    def __init__(self, info: tuple[str, dict[str, str]], frame: QLayout):
        super().__init__()
        self.comboboxs: list[QComboBox] = []
        self.lineedits: list[QLineEdit] = []
        self._updating = False

        setname_dict: dict[str, str] = info[1]
        names: list[str] = list(setname_dict.keys())
        values: list[str] = list(setname_dict.values())

        main_frame: QVBoxLayout = new_frame("V", self)

        new_title("卡片字段", main_frame)

        for _ in range(4):
            # 水平 layout
            row_panel, row_frame = new_panel("H")

            # 左側 combobox 初始化
            combobox = QComboBox()
            row_frame.addWidget(combobox)
            for setname, value in zip(names, values):
                combobox.addItem(setname, value)

            # 右側 LineEdit
            lineedit = QLineEdit("0")
            lineedit.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            lineedit.setFixedWidth(80)  # 固定寬度
            row_frame.addWidget(lineedit)

            combobox.currentIndexChanged.connect(
                lambda idx, le=lineedit, cb=combobox: self._combobox_changed(cb, le)
            )
            lineedit.returnPressed.connect(
                lambda le=lineedit, cb=combobox: self._lineedit_changed(le, cb)
            )
            main_frame.addWidget(row_panel)
            self.comboboxs.append(combobox)
            self.lineedits.append(lineedit)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        frame.addWidget(self)

    @contextmanager
    def updating_block(self):
        if self._updating:
            yield
            return
        self._updating = True
        try:
            yield
        finally:
            self._updating = False

    def _combobox_changed(self, combobox: QComboBox, lineedit: QLineEdit):
        with self.updating_block():
            value: str = combobox.currentData()
            lineedit.setText(value[2:].lower())

    def _lineedit_changed(self, lineedit: QLineEdit, combobox: QComboBox):
        with self.updating_block():
            ind, txt = self.get_key_val(lineedit.text())
            lineedit.setText(txt)
            combobox.setCurrentIndex(ind)

    def get_setname(self) -> int:
        """get the sum of setname"""
        return sum([int(lineedit.text() or "0") for lineedit in self.lineedits])

    # 獲取字段值對應的 combobox 索引與標準化十六進制字串
    def get_key_val(self, val: str | int) -> tuple[int, str]:
        val_str: str = "0"
        if isinstance(val, int):
            val_str = f"{val:x}"
        elif isinstance(val, str):
            val_str = val.lower()
            if val_str.startswith("0x"):
                val_str = val_str[2:]
            if len(val_str) > 4 or not re.fullmatch(r"[0-9a-f]+", val_str):
                val_str = "0"

        index = self.comboboxs[0].findData("0x" + val_str)
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
        lab = QLabel("移动/攻击方向")
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


# ---------- DataEditor item ----------
# 卡片列表組件
class CardListSet(QWidget):
    cdb: CDB | None
    card_lst: QTableWidget
    prev_btn: QPushButton
    page_text: QLineEdit
    page_label: QLabel
    next_btn: QPushButton
    id_index: int

    def __init__(self):
        super().__init__()
        self.id_index = 0
        self.cdb: CDB | None = None  # 儲存目前的資料來源

        # 允許接收鍵盤事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        main_frame = new_frame("V", self)
        # 卡片列表
        self.card_lst = CardTable(main_frame)
        self.card_lst.itemClicked.connect(self.on_item_clicked)
        # 按鈕控制區
        page_frame: QHBoxLayout = new_frame("H", main_frame)
        self.prev_btn = QPushButton("上一頁")
        self.page_text = QLineEdit("1")
        self.page_text.setFixedWidth(40)
        self.page_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label = QLabel("/ 1")
        self.next_btn = QPushButton("下一頁")
        page_frame.addWidget(self.prev_btn)
        page_frame.addWidget(self.page_text)
        page_frame.addWidget(self.page_label)
        page_frame.addWidget(self.next_btn)
        page_frame.addStretch()

    # 點擊時事件
    def on_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        id_item = self.card_lst.item(row, 0)
        pre_id, self.id_index = self.id_index, int(id_item.text())

        if pre_id == self.id_index:
            return

        # 將該行所有列設置背景色
        for col in range(self.card_lst.columnCount()):
            cell = self.card_lst.item(row, col)
            if cell:
                cell.setBackground(QColor(180, 200, 255))  # 淺藍色
                cell.setForeground(QColor(0, 0, 0))  # 字體顏色設為黑色

        # 可選：將其他行背景重置
        for r in range(self.card_lst.rowCount()):
            id_item = self.card_lst.item(r, 0)
            if id_item and int(id_item.text()) == pre_id:
                for col in range(self.card_lst.columnCount()):
                    cell = self.card_lst.item(r, col)
                    if cell:
                        cell.setBackground(QBrush())  # 重置為預設背景
                        cell.setForeground(QBrush())  # 重置為預設字色
                break

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
        """根據目前 self._cdb 的順序移動 now_ind 並觸發 on_item_clicked。"""
        if not self.cdb or not self.cdb.cards:
            return

        keys = list(self.cdb.cards.keys())
        # 嘗試找到目前 now_ind 的索引
        try:
            cur_idx = keys.index(self.id_index)
        except ValueError:
            # 若目前沒有選擇（now_ind 不在列表內），從 -1 開始
            cur_idx = -1

        new_idx = cur_idx + delta
        if new_idx < 0 or new_idx >= len(keys):
            return  # 超出範圍則不動作

        new_id = keys[new_idx]

        # 找到對應的 row，並呼叫 on_item_clicked（模擬點擊）
        for row, id in enumerate(keys):
            if id == new_id:
                item = self.card_lst.item(row, 0)
                if item is not None:
                    # 直接呼叫 on_item_clicked，會更新 now_ind 與外觀
                    self.on_item_clicked(item)
                    # 讓 CardListSet 保持焦點以持續接收鍵盤事件
                    self.setFocus()
                break

    # 更新卡片列表
    def update(self, cdb: CDB | None = None, ind: int | None = None):
        # 儲存 cdb 以供鍵盤導覽使用
        self.cdb = cdb

        self.card_lst.setRowCount(0)
        self.id_index = 0 if ind is None else ind
        if cdb is None:
            return

        self.card_lst.setRowCount(len(cdb.cards))
        for row, id in enumerate(cdb.cards.keys()):
            card = cdb.cards[id]
            is_selected = card.id == self.id_index
            # 更新 ID & Name
            for col, txt in enumerate([str(card.id), card.name]):
                item = self.card_lst.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                    self.card_lst.setItem(row, col, item)
                item.setText(txt)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                if is_selected:
                    item.setBackground(QColor(180, 200, 255))  # 淺藍色
                    item.setForeground(QColor(0, 0, 0))  # 字體顏色設為黑色

    # 傳回當前卡片
    def get_now_card(self) -> Card | None:
        if self.cdb is None or self.id_index == 0:
            return None
        return self.cdb.get_card(self.id_index)

    # 傳回當前卡片
    def add_card(self, c: Card):
        self.cdb.add_card(c)


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

    def __init__(self, cardinfo: Cardinfo, frame: QLayout):
        super().__init__()
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

    # 讀取卡片並更新卡片資料
    def load_card(self, card: Card):
        self.code.load_card(card)
        self.setname.load_card(card)

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
    main: "MainWindow"
    name: QLineEdit
    image: ImageSet
    hint: HintSet
    desc: QPlainTextEdit
    gene_desc: QPlainTextEdit

    def __init__(self, main: "MainWindow", frame: QLayout):
        super().__init__()
        self.main = main

        # 卡名
        self.name = QLineEdit()
        frame.addWidget(self.name)

        # 卡圖 & 脚本提示文字
        image_panel, image_frame = new_panel("H")
        image_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        frame.addWidget(image_panel)

        self.image = ImageSet(image_frame)
        # 點擊 Image 可導入卡圖（需由 DataEditor 傳入 main 才能儲存至 cdb 資料夾）
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

    # 讀取卡片並更新卡片文本
    def load_card(self, card: Card):
        self.name.setText(card.name)

    # 點擊時導入卡圖
    def _on_image_clicked(self):
        # 檢查是否存在當前卡
        if (c := self.main.dataeditor.card_list.get_now_card()) is None:
            return
        # 選擇檔案
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择卡图", "", "Images (*.jpg);;All Files (*)"
        )
        if not file_path:
            return

        cdb_dir = os.path.dirname(self.main.windowTitle())
        pics_dir = os.path.join(cdb_dir, "pics")
        os.makedirs(pics_dir, exist_ok=True)
        img_path = os.path.join(pics_dir, f"c{int(c.id)}.jpg")

        shutil.copyfile(file_path, img_path)
        self.image.set_image(img_path)
