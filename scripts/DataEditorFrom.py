from DataBase import CDB, Card
from ItemLib import (
    new_frame,
    new_panel,
    CardListSet,
    CardDataSet,
    CardTextSet,
)
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from Global import get_main


class DataEditor(QWidget):
    card_list: CardListSet
    card_data: CardDataSet
    card_text: CardTextSet

    def __init__(self):
        super().__init__()
        # 卡片列表
        self.card_list = CardListSet()
        # ---------------- 中央容器 ----------------
        mid_panel, mid_frame = new_panel("V")
        # 卡片文本編輯區
        self.card_text = CardTextSet(mid_frame)
        # 搜索 & 重置 & 脚本 按鈕
        btn_frame = new_frame("H", mid_frame)
        self.search_btn = QPushButton("搜索")
        self.script_btn = QPushButton("脚本")
        btn_frame.addWidget(self.search_btn)
        btn_frame.addWidget(self.script_btn)
        btn_frame.addStretch()
        # ---------------- 右側容器 ----------------
        right_panel, right_frame = new_panel("V")
        right_frame.setAlignment(Qt.AlignmentFlag.AlignTop)  # 所有子組件靠上對齊
        # 卡片數據編輯區
        self.card_data = CardDataSet(right_frame)
        right_frame.addStretch()
        # 添加 & 修改 & 删除 按鈕
        btn_frame = new_frame("H", right_frame)
        self.savecard_btn = QPushButton("保存")
        self.resetcard_btn = QPushButton("重置")
        self.delcard_btn = QPushButton("删除")
        self.delcard_btn.setStyleSheet("background-color: #d9534f; color: black;")
        btn_frame.addWidget(self.savecard_btn)
        btn_frame.addWidget(self.resetcard_btn)
        btn_frame.addWidget(self.delcard_btn)
        self.savecard_btn.clicked.connect(self.save_card)
        self.resetcard_btn.clicked.connect(self.clear)
        self.delcard_btn.clicked.connect(self.delete_card)
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
        if (card := self.card_list.get_now_card()) is None:
            return
        self.card_data.load_card(card)
        self.card_text.load_card(card)

    # 清空當前內容
    def clear(self):
        self.card_data.clear()
        self.card_text.clear()

    # 將當前編輯器內容打包成 Card 並返回
    def pack_card_data(self) -> Card:
        id, alias = self.card_data.get_code()
        data_list = [id, alias, *self.card_data.get_data_list()]

        is_mons = data_list[3] & 0x1 == 0x1
        text_lst = [id, *self.card_text.get_text_list(is_mons)]

        c = Card(id)
        c.set_data(data_list)
        c.set_text(text_lst)
        return c

    # 保存卡片
    def save_card(self):
        main = get_main()
        id, _ = self.card_data.get_code()
        if (fb := main.file_list.get_file_btn()) is None:
            return
        if id == 0:
            main.show_error("ID 不能為 0")
            return
        now_c = self.card_list.get_now_card()
        cdb = fb.cdb
        if now_c.id != id:
            if cdb.has_id(id) and not main.show_quest(f"{id} 已存在, 是否覆盖"):
                return
            if main.show_quest(f"是否刪除 {now_c.id}"):
                cdb.del_card(now_c.id)
        # 儲存新卡
        cdb.add_card(self.pack_card_data())
        self.card_list.update(cdb, id)

    # 刪除卡片
    def delete_card(self):
        main = get_main()
        if (fb := main.file_list.get_file_btn()) is None:
            return
        cdb = fb.cdb
        now_c = self.card_list.get_now_card()
        if main.show_quest(f"是否刪除 {now_c.id}"):
            cdb.del_card(now_c.id)
        self.card_list.update(cdb, cdb.get_first_id())
        self.updata()
