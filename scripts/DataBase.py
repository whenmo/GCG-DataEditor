import sqlite3

DATAS_SQL_SET: str = """
    CREATE TABLE IF NOT EXISTS datas (
        id INTEGER PRIMARY KEY,
        alias INTEGER,
        setcode INTEGER,
        type INTEGER,
        value INTEGER,
        atk INTEGER,
        move INTEGER,
        race INTEGER,
        [from] INTEGER
    )
    """

TEXTS_SQL_SET: str = """
    CREATE TABLE IF NOT EXISTS texts (
        id INTEGER PRIMARY KEY,
        name TEXT,
        desc TEXT,
        hint1 TEXT,
        hint2 TEXT,
        hint3 TEXT,
        hint4 TEXT,
        hint5 TEXT,
        hint6 TEXT,
        hint7 TEXT,
        hint8 TEXT,
        hint9 TEXT,
        hint10 TEXT,
        hint11 TEXT,
        hint12 TEXT,
        hint13 TEXT,
        hint14 TEXT,
        hint15 TEXT,
        hint16 TEXT
    )
    """


# 建立新的 CDB 資料庫檔案，包含 datas 與 texts 兩個表
def creat_new_cdb(file_path: str):
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    # 建立 data & texts 表
    cursor.execute(DATAS_SQL_SET)
    cursor.execute(TEXTS_SQL_SET)
    conn.commit()
    conn.close()


class Card:
    id: int
    alias: int
    setcode: int
    type: int
    value: int
    atk: int
    move: int
    race: int
    from_: int
    name: str
    desc: str
    hints: list[str]

    def __init__(self, id: int):
        self.id = id
        self.alias = 0
        self.setcode = 0
        self.type = 0
        self.value = 0
        self.atk = 0
        self.move = 0
        self.race = 0
        self.from_ = 0
        self.name = ""
        self.desc = ""
        self.hints = []

    def set_id(self, id: int):
        self.id = id

    def set_data(self, data: list[int]):
        self.alias = data[1]
        self.setcode = data[2]
        self.type = data[3]
        self.value = data[4]
        self.atk = data[5]
        self.move = data[6]
        self.race = data[7]
        self.from_ = data[8]

    def set_text(self, text: list[str]):
        self.name = text[1]
        self.desc = text[2]
        self.hints = text[3:]


class CDB:
    path: str
    cards: dict[int, Card]

    def __init__(self, path: str):
        self.path = path
        self.cards = {}
        try:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.cursor()
            cursor.execute("SELECT * FROM datas")
            datas = cursor.fetchall()
            cursor.execute("SELECT * FROM texts")
            texts = cursor.fetchall()

            self.index: int = datas[0][0] if datas else 0
            for data, text in zip(datas, texts):
                card = Card(data[0])
                card.set_data(data)
                card.set_text(text)
                self.cards[data[0]] = card
        except Exception:
            return None

    def get_first_id(self) -> int:
        if not self.cards:
            return 0
        return next(iter(self.cards))

    # 回傳指定 id 的 Card 輸入可為 int/str/None 找不到對應 id 也回傳 None
    def get_card(self, id: int | str | None) -> Card | None:
        if not id:
            return None
        try:
            key = int(id)
        except (TypeError, ValueError):
            return None
        return self.cards.get(key)

    def has_id(self, id: int) -> bool:
        if id in self.cards:
            return True
        return False

    def add_card(self, c: Card):
        self.cards[c.id] = c
        self.save()

    def del_card(self, id: int):
        del self.cards[id]
        self.save()

    def save(self):
        conn = sqlite3.connect(self.path)
        try:
            cur = conn.cursor()
            cur.execute(DATAS_SQL_SET)
            cur.execute(TEXTS_SQL_SET)
            cur.execute("DELETE FROM datas")
            cur.execute("DELETE FROM texts")
            for _, card in self.cards.items():
                data_row = (
                    card.id,
                    card.alias,
                    card.setcode,
                    card.type,
                    card.value,
                    card.atk,
                    card.move,
                    card.race,
                    card.from_,
                )
                cur.execute(
                    "INSERT INTO datas VALUES (?,?,?,?,?,?,?,?,?)",
                    data_row,
                )
                hints = card.hints
                if len(hints) < 16:
                    hints += [""] * (16 - len(hints))
                else:
                    hints = hints[:16]
                text_row = (int(card.id), card.name or "", card.desc or "", *hints)
                cur.execute(
                    "INSERT INTO texts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    text_row,
                )

            conn.commit()
        finally:
            conn.close()
