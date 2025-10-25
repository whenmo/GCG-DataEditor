from DataBase import CDB, Card
from ItemLib import (
    new_frame,
    new_panel,
    new_btn,
    CardListSet,
    CardDataSet,
    CardTextSet,
)
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from Global import get_main
import os
import subprocess
import platform


class DataEditor(QWidget):
    card_list: CardListSet
    card_data: CardDataSet
    card_text: CardTextSet
    copy_card: dict[int, Card]

    def __init__(self):
        super().__init__()
        # 卡片列表
        self.card_list = CardListSet()
        self.copy_card = {}
        # ---------------- 中央容器 ----------------
        mid_panel, mid_frame = new_panel("V")
        # 卡片文本編輯區
        self.card_text = CardTextSet(mid_frame)
        # 搜索 & 重置 & 脚本 按鈕
        btn_frame: QHBoxLayout = new_frame("H", mid_frame)
        btn_frame.addStretch()
        new_btn("重置列表", btn_frame, self.card_list.clear_filter)
        new_btn("脚本", btn_frame, self.open_script)
        new_btn("重置资料", btn_frame, self.clear)
        btn_frame.addStretch()
        # ---------------- 右側容器 ----------------
        right_panel, right_frame = new_panel("V")
        right_frame.setAlignment(Qt.AlignmentFlag.AlignTop)  # 所有子組件靠上對齊
        # 卡片數據編輯區
        self.card_data = CardDataSet(right_frame)
        right_frame.addStretch()
        # 添加 & 修改 & 删除 按鈕
        btn_frame: QHBoxLayout = new_frame("H", right_frame)
        btn_frame.addStretch()
        new_btn("添加", btn_frame, self.add_card)
        savcard_btn = new_btn("保存 Ctrl + S", btn_frame, self.save_card)
        new_btn(
            "删除",
            btn_frame,
            self.delete_card,
            "background-color: #d9534f; color: black;",
        )
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(savcard_btn.click)  # 按下時模擬按鈕點擊
        btn_frame.addStretch()
        # ---------------- 設置中央 Widget ----------------
        main_frame: QHBoxLayout = new_frame("H", self, None, False)
        main_frame.addWidget(self.card_list)  # 左側容器
        main_frame.addWidget(mid_panel)  # 中央容器
        main_frame.addWidget(right_panel)  # 右側容器
        self.setVisible(False)  # 初始隱藏

    # 設定 cdb
    def set_cdb(self, cdb: CDB | None = None):
        self.card_list.set_data_source(cdb)
        self.card_list.refresh_view()
        self.updata()

    # 更新
    def updata(self):
        if (card := self.card_list.get_now_card()) is None:
            return
        self.card_data.load_card(card)
        self.card_text.load_card(card)

    # 刷新卡片列表
    def clear(self):
        self.card_data.clear()
        self.card_text.clear()

    # 將當前編輯器內容打包成 Card 並返回
    def pack_card_data(self) -> Card:
        id, alias = self.card_data.get_code()
        ot, setcode = 3, 0
        data_list = [id, ot, alias, setcode, *self.card_data.get_data_list(), 0]
        text_lst = [id, *self.card_text.get_text_list()]
        c = Card(id)
        c.set_data(data_list)
        c.set_text(text_lst)
        return c

    # 添加卡片
    def add_card(self):
        main = get_main()
        id, _ = self.card_data.get_code()
        if (fb := main.file_list.get_file_btn()) is None:
            return
        if id == 0:
            main.show_error("ID 不能為 0")
            return
        if fb.cdb.has_id(id) and not main.show_quest(f"{id} 已存在, 是否覆盖"):
            return
        # 儲存新卡
        self.card_list.add_card(self.pack_card_data())
        self.updata()

    # 保存卡片
    def save_card(self):
        main = get_main()
        id, _ = self.card_data.get_code()
        if (fb := main.file_list.get_file_btn()) is None:
            return
        if id == 0:
            main.show_error("ID 不能為 0")
            return
        if (now_c := self.card_list.get_now_card()) is None:
            main.show_error("当前没有可编辑的卡片, 请使用 添加")
            return
        cdb = fb.cdb
        if now_c.id != id:
            if cdb.has_id(id) and not main.show_quest(f"{id} 已存在, 是否覆盖"):
                return
            if main.show_quest(f"是否刪除 {now_c.id}"):
                cdb.del_card(now_c.id)

        cdb.add_card(self.pack_card_data())
        self.card_list.set_data_source(cdb)
        self.card_list.refresh_view()
        main.show_msg("修改成功")

        self.updata()

    # 刪除卡片
    def delete_card(self):
        main = get_main()
        if (fb := main.file_list.get_file_btn()) is None:
            return
        cdb = fb.cdb
        if not cdb.select_id_lst:
            return
        msg = "是否刪除\n" + "\n".join([str(id) for id in cdb.select_id_lst])
        now_c = self.card_list.get_now_card()
        if main.show_quest(msg):
            cdb.del_card(now_c.id)
            self.card_list.set_data_source(cdb)
            self.card_list.refresh_view()
            self.updata()

    def copy_id_list(self, id_list: list[int]):
        """將指定 ID 的卡片複製到內部剪貼簿"""
        if (cdb := self.card_list.cdb) is None:
            return
        main = get_main()
        if not id_list:
            main.show_msg("没有卡片可复制")
            return
        self.copy_card = {}
        copy_ct = 0
        for id in id_list:
            if id in cdb.card_dict:
                card = cdb.card_dict[id]
                self.copy_card[id] = card
                copy_ct += 1
        main.show_msg(f"已复制 {copy_ct} 张卡片")
        main.update_paste_action_text(copy_ct)

    # 复制选中卡片
    def copy_select_card(self):
        if self.card_list.cdb is None:
            return
        id_list = list(self.card_list.cdb.select_id_lst)
        self.copy_id_list(id_list)

    # 复制所有卡片
    def copy_all_card(self):
        if self.card_list.cdb is None:
            return
        id_list = sorted(self.card_list.cdb.card_dict.keys(), key=lambda k: int(k))
        self.copy_id_list(id_list)

    # 粘贴卡片
    def paste_cards(self):
        main = get_main()
        if not self.copy_card:
            return
        if self.card_list.cdb is None:
            return
        cdb = self.card_list.cdb
        paste_ct = 0
        last_id = None
        for card in self.copy_card.values():
            id = card.id
            try:
                if cdb.has_id(id):
                    if not main.show_quest(f"ID {id} 已存在, 是否覆蓋"):
                        continue
                cdb.add_card(card)
                last_id = id
                paste_ct += 1
            except Exception:
                continue
        if paste_ct > 0:
            if last_id:
                cdb.now_id = last_id
            self.card_list.set_data_source(cdb)
            self.card_list.refresh_view()
            self.updata()
            main.show_msg(f"已贴上 {paste_ct} 张卡片")

    # 腳本
    def open_script(self):
        cdb = self.card_list.cdb
        if not cdb or not cdb.path:
            return
        id = cdb.now_id
        if id == 0 or id not in cdb.card_dict:
            return
        cdb_dir = os.path.dirname(cdb.path)
        script_dir = os.path.join(cdb_dir, "script")
        script_path = os.path.join(script_dir, f"c{id}.lua")

        card = cdb.card_dict[id]
        default_lua = f"--{card.name} {id}\nlocal cm, m = GetID()\nfunction cm.initial_effect(c)\n\nend\n"

        if not os.path.exists(script_dir):
            try:
                os.makedirs(script_dir)
            except Exception:
                return

        if not os.path.exists(script_path):
            try:
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(default_lua)
            except Exception:
                return
        try:
            system = platform.system()
            if system == "Windows":
                # Windows 使用 os.startfile
                os.startfile(script_path)
            elif system == "Darwin":  # macOS
                # macOS 使用 'open' 命令
                subprocess.Popen(["open", script_path])
            else:  # Linux, XDG standard
                # Linux 使用 'xdg-open' 命令
                subprocess.Popen(["xdg-open", script_path])
        except Exception:
            pass
