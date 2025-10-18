import os
import re
from CardInfo import Cardinfo
from contextlib import contextmanager
from PyQt6.QtWidgets import (
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
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, Qt


# 新版面容器
def new_panel(path: str = "V") -> tuple[QWidget, QLayout]:
    panel: QWidget = QWidget()
    if path == "V":
        frame: QLayout = QVBoxLayout(panel)
    elif path == "H":
        frame: QLayout = QHBoxLayout(panel)
    elif path == "G":
        frame: QLayout = QGridLayout(panel)
    frame.setContentsMargins(0, 0, 0, 0)  # 去掉多餘邊距
    return [panel, frame]


# 卡圖容器
class ImageSet(QLabel):
    clicked = pyqtSignal()

    def __init__(self, frame: QVBoxLayout):
        super().__init__()
        self.setFixedSize(200, 285)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_path = "data/cover.jpg"
        self.set_image(self.default_path)

        frame.addWidget(self)

    def set_image(self, path: str = ""):
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.width(),
                    self.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.setPixmap(scaled_pixmap)
        else:
            self.setPixmap(QPixmap())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# 輸入組件
class IDSet(QWidget):
    def __init__(self, title: str, frame: QLayout):
        super().__init__()

        # 水平 layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 左側 Label
        self.label = QLabel(title)
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.label)

        # 右側 LineEdit
        self.text = QLineEdit("0")
        self.text.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.text.setFixedWidth(80)  # 固定寬度
        layout.addWidget(self.text)

        # 讓 LineEdit 拉伸填滿剩餘空間
        layout.setStretch(0, 0)  # label 不拉伸
        layout.setStretch(1, 1)  # lineedit 拉伸

        frame.addWidget(self)


# 下拉框組件
class ComboboxSet(QWidget):
    def __init__(
        self, info: tuple[str, dict[str, str]], default_val: str, frame: QLayout
    ):
        super().__init__()
        self.combobox: QComboBox = QComboBox()

        title, key_dict = info

        # 水平 layout
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 左側 Label
        label: QLabel = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label)

        # 右側 combobox
        self.combobox.setFixedWidth(80)  # 固定寬度
        layout.addWidget(self.combobox)
        for key, value in key_dict.items():
            self.combobox.addItem(key, value)
        index = self.combobox.findData(default_val)
        if index != -1:
            self.combobox.setCurrentIndex(index)

        # 讓 LineEdit 拉伸填滿剩餘空間
        layout.setStretch(0, 0)  # label 不拉伸
        layout.setStretch(1, 1)  # lineedit 拉伸

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
    def __init__(self, info: Cardinfo, frame: QLayout):
        super().__init__()

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_combobox: ComboboxSet = ComboboxSet(
            info.get_key("typ"), "monstyp", layout
        )
        self.sub_combobox: list[ComboboxSet] = []

        for magic_str in ["monstyp,0x1", "calltyp,0x2", "banetyp,0x4", "areatyp,0x8"]:
            key, default = magic_str.split(",")
            self.sub_combobox.append(ComboboxSet(info.get_key(key), default, layout))

        self._update_sub_combobox()
        self.main_combobox.combobox.currentIndexChanged.connect(
            self._update_sub_combobox
        )

        frame.addWidget(self)

    def _update_sub_combobox(self):
        show_ind = {
            "monstyp": 0,
            "calltyp": 1,
            "banetyp": 2,
            "areatyp": 3,
        }[self.main_combobox.get_value()]
        for i, combo in enumerate(self.sub_combobox):
            combo.setVisible(i == show_ind)


# 字段組件
class SetNameSet(QWidget):
    def __init__(self, info: tuple[str, dict[str, str]], frame: QLayout):
        super().__init__()
        self.comboboxs: list[QComboBox] = []
        self.lineedits: list[QLineEdit] = []
        self._updating = False

        setname_dict: dict[str, str] = info[1]
        names: list[str] = list(setname_dict.keys())
        values: list[str] = list(setname_dict.values())

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        for _ in range(4):
            # 水平 layout
            row_panel, row_frame = new_panel("H")
            row_frame.setSpacing(5)

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
            main_layout.addWidget(row_panel)
            self.comboboxs.append(combobox)
            self.lineedits.append(lineedit)

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

    def get_value(self) -> int:
        """get the sum of setname"""
        return sum([int(lineedit.text() or "0") for lineedit in self.lineedits])

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
            index = self.comboboxs[0].findData("0x0")
            val_str = "0"

        return (index, val_str)

    def set_unit(self, ind: int, val: str | int):
        ind, txt = self.get_key_val(val)
        self.comboboxs[ind].setText(txt)
        self.lineedits[ind].setCurrentIndex(ind)

    def set_value(self, value: int):
        vals_str: list[str] = ["0"] * 4
        if isinstance(value, int):
            for i in range(4):
                val = value & 0xFFFF
                vals_str[i] = f"{val:X}"
                value >>= 16

        for i in range(4):
            self.set_unit(i, vals_str[i])


# 移動標組件
class MoveSet(QWidget):
    def __init__(self, frame: QLayout):
        super().__init__()

        # 水平布局：左側 Label + 右側 3x3 Grid
        main_frame = QHBoxLayout(self)
        main_frame.setContentsMargins(0, 0, 0, 0)
        main_frame.setSpacing(5)

        # 左側 Label
        self.label = QLabel("移动/攻击方向")
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        main_frame.addWidget(self.label)

        # 右側 GridLayout
        grid_panel, grid_frame = new_panel("G")
        grid_frame.setSpacing(2)

        self.checkboxes: list[QCheckBox] = []

        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]

        for i, pos in enumerate(positions):
            cb = QCheckBox()
            self.checkboxes.append(cb)
            grid_frame.addWidget(cb, pos[0], pos[1])

        main_frame.addWidget(grid_panel)
        grid_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        frame.addWidget(self)


# 脚本提示列
class HintTextSet(QWidget):
    def __init__(self, title: str, frame: QLayout):
        super().__init__()

        # 水平 layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 左側 LineEdit
        self.text = QLineEdit("")
        self.text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.text)

        # 右側 Label
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedWidth(15)  # 固定寬度
        layout.addWidget(label)

        # 讓 LineEdit 拉伸填滿剩餘空間
        layout.setStretch(0, 0)  # label 不拉伸
        layout.setStretch(1, 1)  # lineedit 拉伸

        frame.addWidget(self)


# 脚本提示組件
class HintSet(QWidget):
    def __init__(self, frame: QLayout):
        super().__init__()
        self.lineedits: list[HintTextSet] = []

        main_frame = QVBoxLayout(self)
        main_frame.setContentsMargins(0, 0, 0, 0)
        main_frame.setSpacing(5)

        title = QLabel("脚本提示文字")
        title.setStyleSheet("""
            background-color: lightgray;
            color: black;
            padding: 2px;
        """)
        main_frame.addWidget(title)

        for i in range(16):
            le: HintTextSet = HintTextSet(f"{i}",  main_frame)
            self.lineedits.append(le)

        frame.addWidget(self)
