import os
from CardInfo import Cardinfo, load_cardinfo
from DataBase import CDB, Card
from ItemLib import (
    new_frame,
    new_panel,
    CardListSet,
    CardDataSet,
    CardTextSet,
)
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainFrom import MainWindow


class DataEditor(QWidget):
    main: "MainWindow"
    card_list: CardListSet
    card_data: CardDataSet
    card_text: CardTextSet

    def __init__(self, main: "MainWindow"):
        super().__init__()
        self.main = main

        # cardinfo
        cardinfo: Cardinfo = load_cardinfo()

        # 卡片列表
        self.card_list = CardListSet()

        # ---------------- 中央容器 ----------------
        mid_panel, mid_frame = new_panel("V")

        # 卡片文本編輯區
        self.card_text = CardTextSet(main, mid_frame)

        # 搜索 & 重置 & 脚本 按鈕
        btn_frame = new_frame("H", mid_frame)
        self.search_btn = QPushButton("搜索")
        self.reset_btn = QPushButton("重置")
        self.script_btn = QPushButton("脚本")
        btn_frame.addWidget(self.search_btn)
        btn_frame.addWidget(self.reset_btn)
        btn_frame.addWidget(self.script_btn)
        btn_frame.addStretch()

        # ---------------- 右側容器 ----------------
        right_panel, right_frame = new_panel("V")
        right_frame.setAlignment(Qt.AlignmentFlag.AlignTop)  # 所有子組件靠上對齊

        # 卡片數據編輯區
        self.card_data = CardDataSet(cardinfo, right_frame)
        right_frame.addStretch()

        # 添加 & 修改 & 删除 按鈕
        btn_frame = new_frame("H", right_frame)
        self.addcard_btn = QPushButton("添加")
        self.setcard_btn = QPushButton("修改")
        self.delcard_btn = QPushButton("删除")
        self.delcard_btn.setStyleSheet("background-color: #d9534f; color: black;")
        btn_frame.addWidget(self.addcard_btn)
        btn_frame.addWidget(self.setcard_btn)
        btn_frame.addWidget(self.delcard_btn)
        self.addcard_btn.clicked.connect(self.add_card)
        btn_frame.addStretch()

        # ---------------- 設置中央 Widget ----------------
        main_frame: QHBoxLayout = new_frame("H", self, None, False)
        main_frame.addWidget(self.card_list)  # 左側容器
        main_frame.addWidget(mid_panel)  # 中央容器
        main_frame.addWidget(right_panel)  # 右側容器
        self.setVisible(False)  # 初始隱藏

    # 設定 cdb
    def set_cdb(self, cdb: CDB | None = None, ind: int | None = None):
        self.card_list.update(cdb, ind)
        self.updata()

    # 更新
    def updata(self):
        if not (card := self.card_list.get_now_card()):
            return
        self.card_data.load_card(card)
        self.card_text.load_card(card)
        # 以 cdb 檔案所在目錄為基底，載入 pics/c<id>.jpg
        img_dir = os.path.dirname(self.main.file_list.get_file_btn().cdb.path)
        img_path = os.path.join(img_dir, "pics", f"c{int(card.id)}.jpg")
        self.card_text.image.set_image(img_path)

    # 將當前編輯器內容打包成 Card 並返回
    def pack_card_data(self) -> Card:
        id, alias = self.card_data.get_code()
        data_list = [id, alias, *self.card_data.get_data_list()]
        text_lst = [id]
        text_lst.append(self.name.text())
        desc = self.desc.toPlainText()
        is_mons = data_list[2] & 0x1 == 0x1
        if is_mons and (gene := self.gene_desc.toPlainText()):
            desc += "\n【进化元效果】\n" + gene
        text_lst.append(desc)
        text_lst += self.hint.get_hints()

        c = Card(id)
        c.set_data(data_list)
        c.set_text(text_lst)
        return c

    # 添加卡片
    def add_card(self):
        id, _ = self.card_data.get_code()
        if (fb := self.main.file_list.get_file_btn()) is None:
            return
        if id == 0:
            QMessageBox.warning(self.main, "ID 错误", "ID 不能為 0")
            return
        cdb = fb.cdb
        if cdb.has_id(id):
            QMessageBox.warning(self.main, "ID 错误", "ID 已经存在")
            return
        cdb.add_card(self.pack_card_data())
        self.card_list.update(cdb, id)
        cdb.save()

    # 保存卡片
    def save_card(self):
        id, _ = self.card_data.get_code()
        if (fb := self.main.file_list.get_file_btn()) is None:
            return
        if id == 0:
            QMessageBox.warning(self.main, "ID 错误", "ID 不能為 0")
            return
        cdb = fb.cdb
        # now_c = self.main.dataeditor.card_list.get_now_card()
        if cdb.has_id(id):
            QMessageBox.warning(self.main, "ID 错误", "ID 已经存在")
            return
        cdb.add_card(self.pack_card_data())
        self.card_list.update(cdb, id)
        cdb.save()

    # 刪除卡片
    def delete_card(self):
        id, _ = self.card_data.get_code()
