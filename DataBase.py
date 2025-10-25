import sqlite3
from Global import get_sql_code_data, get_sql_code_text

sql_set_datas, sql_insert_datas = get_sql_code_data()
sql_set_texts, sql_insert_texts = get_sql_code_text()


# 建立新的 CDB 資料庫檔案, 包含 datas 與 texts 兩個表
def creat_new_cdb(file_path: str):
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    # 建立 data & texts 表
    cursor.execute(sql_set_datas)
    cursor.execute(sql_set_texts)
    conn.commit()
    conn.close()


class Card:
    id: int
    ot: int
    alias: int
    setcode: int
    type: int
    atk: int
    def_: int
    level: int
    race: int
    attribute: int
    category: int
    name: str
    desc: str
    strs: list[str]

    def __init__(self, id: int):
        self.id = id
        self.ot = 3
        self.alias = 0
        self.setcode = 0
        self.type = 0
        self.atk = 0
        self.def_ = 0
        self.level = 0
        self.race = 0
        self.attribute = 0
        self.category = 0
        self.name = ""
        self.desc = ""
        self.strs = []

    def set_data(self, data: list[int]):
        self.alias = data[2]
        self.type = data[4]
        self.atk = data[5]
        self.def_ = data[6]
        self.level = data[7]
        self.race = data[8]
        self.attribute = data[9]

    def set_text(self, text: list[str]):
        self.name = text[1]
        self.desc = text[2]
        self.strs = text[3:]


class CDB:
    path: str
    card_dict: dict[int, Card]
    now_id: int
    show_id_lst: list[int]
    select_id_lst: set[int]

    def __init__(self, path: str):
        # 初始化
        self.path = path
        self.card_dict = {}
        self.now_id = 0
        self.show_id_lst = []
        self.select_id_lst = set()
        # 設定 card_dict
        try:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM datas")
                datas = cursor.fetchall()
                cursor.execute("SELECT * FROM texts")
                texts = cursor.fetchall()
            for data, text in zip(datas, texts):
                card = Card(data[0])
                card.set_data(data)
                card.set_text(text)
                self.card_dict[data[0]] = card
        except Exception:
            pass
        # 初始化顯示
        if self.card_dict:
            self.show_id_lst = sorted(self.card_dict.keys(), key=lambda k: int(k))
            self.now_id = self.show_id_lst[0]
            self.select_id_lst.add(self.now_id)

    # ---------------- 設定數據 ----------------
    def add_card(self, c: Card):
        """增加一張卡"""
        self.card_dict[c.id] = c
        self.save()

        self.show_id_lst = sorted(self.card_dict.keys(), key=lambda k: int(k))

        self.now_id = c.id
        self.select_id_lst.clear()
        self.select_id_lst.add(self.now_id)

    def del_card(self, id: int):
        """刪除 id 的卡"""
        if id in self.card_dict:
            del self.card_dict[id]
            self.save()

    def save(self):
        """將 cdb 保存到 path"""
        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.cursor()
                cur.execute(sql_set_datas)
                cur.execute(sql_set_texts)
                cur.execute("DELETE FROM datas")
                cur.execute("DELETE FROM texts")
                sorted_cards = sorted(self.card_dict.values(), key=lambda card: card.id)
                for card in sorted_cards:
                    data_row = (
                        card.id,
                        card.ot,
                        card.alias,
                        card.setcode,
                        card.type,
                        card.atk,
                        card.def_,
                        card.level,
                        card.race,
                        card.attribute,
                        card.category,
                    )
                    cur.execute(sql_insert_datas, data_row)
                    hints = card.strs
                    if len(hints) < 16:
                        hints += [""] * (16 - len(hints))
                    else:
                        hints = hints[:16]
                    text_row = (int(card.id), card.name or "", card.desc or "", *hints)
                    cur.execute(sql_insert_texts, text_row)

                conn.commit()
        except Exception:
            pass

    # ---------------- 獲取數據 ----------------
    def get_first_id(self) -> int:
        """獲取第一張卡的 id"""
        if not self.card_dict:
            return 0
        return next(iter(self.card_dict))

    def get_card(self, id: int | str | None) -> Card | None:
        """回傳指定 id 的 Card, 找不到對應 id 回傳 None"""
        if not id:
            return None
        try:
            key = int(id)
        except (TypeError, ValueError):
            return None
        return self.card_dict.get(key)

    def has_id(self, id: int) -> bool:
        """檢查是否存在 id"""
        if id in self.card_dict:
            return True
        return False

    def search_id(self, id_prefix: str):
        """
        根據 id 篩選卡片, 如果為空則顯示所有卡片, 同時清空已選中的卡
        不會回傳值, 只會更新內部的 now_id, show_id_lst 和 select_id_lst
        """
        if id_prefix:
            match_id_lst = [
                id for id in self.card_dict.keys() if str(id).startswith(id_prefix)
            ]
            self.show_id_lst = match_id_lst
        else:
            self.show_id_lst = sorted(self.card_dict.keys(), key=lambda k: int(k))

        if self.now_id in self.show_id_lst:
            pass
        elif self.show_id_lst:
            self.now_id = self.show_id_lst[0]
        else:
            self.now_id = 0
        self.select_id_lst.clear()
        self.select_id_lst.add(self.now_id)

    def search_name(self, name: str):
        """
        根據 name 篩選卡片, 如果為空則顯示所有卡片, 同時清空已選中的卡
        不會回傳值, 只會更新內部的 now_id, show_id_lst 和 select_id_lst
        """
        if name:
            name_lower = name.lower()  # 進行不區分大小寫的匹配
            match_id_lst = [
                key
                for key, card in self.card_dict.items()
                if card.name and name_lower in card.name.lower()
            ]
            self.show_id_lst = match_id_lst
        else:
            self.show_id_lst = sorted(self.card_dict.keys(), key=lambda k: int(k))

        if self.now_id in self.show_id_lst:
            pass
        elif self.show_id_lst:
            self.now_id = self.show_id_lst[0]
        else:
            self.now_id = 0
        self.select_id_lst.clear()
        self.select_id_lst.add(self.now_id)

    def del_select_card(self):
        """刪除 self.select_id_lst 中選中的所有卡片, 然後更新 now_id, show_id_lst 和 select_id_lst"""
        if not self.select_id_lst:
            return

        del_id_lst = self.select_id_lst.copy()
        for id in del_id_lst:
            if id in self.card_dict:
                del self.card_dict[id]

        self.save()

        self.show_id_lst = [id for id in self.show_id_lst if id not in del_id_lst]
        self.select_id_lst.clear()

        if self.show_id_lst:
            new_now_id = self.show_id_lst[0]
            self.select_id_lst.add(new_now_id)
        else:
            new_now_id = 0
        self.now_id = new_now_id
