from CardInfo import Cardinfo, load_cardinfo
from DataBase import CDB
from ItemLib import (
    new_panel,
    new_title,
    CardListSet,
    ImageSet,
    IDSet,
    ComboboxSet,
    TypeSet,
    SetNameSet,
    MoveSet,
    HintSet,
    CardDataSet,
)
from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QSplitter,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
)
from PyQt6.QtCore import Qt


class DataEditor(QWidget):
    cardinfo: Cardinfo
    card_list: CardListSet
    card_data: CardDataSet

    name: QLineEdit
    image: ImageSet
    hint: HintSet
    desc: QPlainTextEdit
    gene_desc: QPlainTextEdit

    def __init__(self):
        super().__init__()

        # cardinfo
        self.cardinfo = load_cardinfo()

        # 卡片列表
        self.card_list = CardListSet()

        # ---------------- 中央容器 ----------------
        mid_panel, mid_frame = new_panel("V")

        # 卡名
        self.name = QLineEdit()
        mid_frame.addWidget(self.name)

        # 卡圖 & 脚本提示文字
        image_panel, image_frame = new_panel("H")
        image_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        mid_frame.addWidget(image_panel)

        self.image = ImageSet(image_frame)
        self.hint = HintSet(image_frame)
        self.hint.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # 卡片描述
        self.desc = QPlainTextEdit()
        self.desc.setPlaceholderText("卡片描述")
        mid_frame.addWidget(self.desc)

        # 進化元效果
        self.gene_desc = QPlainTextEdit()
        self.gene_desc.setPlaceholderText("进化元效果")
        font_metrics = self.gene_desc.fontMetrics()
        line_height = font_metrics.lineSpacing()  # 每行行高（含間距）
        self.gene_desc.setFixedHeight(line_height * 5 + 8)  # 顯示約5行，+8留邊距
        mid_frame.addWidget(self.gene_desc)

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
        right_frame.setAlignment(Qt.AlignmentFlag.AlignTop)  # 所有子組件靠上對齊

        self.card_data = CardDataSet(self.cardinfo, right_frame)
        right_frame.addStretch()

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
        mainSplitter.addWidget(self.card_list)  # 左側容器
        mainSplitter.addWidget(mid_panel)  # 中央容器
        mainSplitter.addWidget(right_panel)  # 右側容器
        mainSplitter.setStretchFactor(0, 1)  # 左側容器
        mainSplitter.setStretchFactor(1, 2)  # 中央容器
        mainSplitter.setStretchFactor(2, 3)  # 右側容器

        # ---------------- 設置中央 Widget ----------------
        main_frame = QVBoxLayout()
        main_frame.addWidget(mainSplitter)
        self.setLayout(main_frame)

    # 設定 cdb
    def set_cdb(self, cdb: CDB | None = None, ind: int | None = None):
        self.card_list.update(cdb, ind)
        self.updata()

    # 更新
    def updata(self):
        if not (card := self.card_list.get_now_card()):
            return
        self.card_data.update(card)
