import sqlite3


def creat_new_cdb(file_path: str) -> sqlite3.Connection:
    """
    建立新的 CDB 資料庫檔案，包含 datas 與 texts 兩個表
    """
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()

    # 建立 datas 表
    cursor.execute("""
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
    """)

    # 建立 texts 表
    cursor.execute("""
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
    """)

    conn.commit()
    return conn


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

    def __init__(self):
        pass

    def Set_Data(self, data: list[int]):
        self.id: int = data[0]
        self.alias: int = data[1]
        self.setcode: int = data[2]
        self.type: int = data[3]
        self.value: int = data[4]
        self.atk: int = data[5]
        self.move: int = data[6]
        self.race: int = data[7]
        self.from_: int = data[8]

    def Set_Text(self, text: list[str]):
        self.name: str = text[1]
        self.desc: str = text[2]
        self.hints: list[str] = text[3:]


class CDB:
    path: str
    cards: dict[int, Card]

    def __init__(self, path: str, cursor: sqlite3.Cursor):
        self.path = path
        self.cards = {}

        cursor.execute("SELECT * FROM datas")
        datas = cursor.fetchall()
        cursor.execute("SELECT * FROM texts")
        texts = cursor.fetchall()

        self.index: int = datas[0][0] if datas else 0
        for data, text in zip(datas, texts):
            card = Card()
            card.Set_Data(data)
            card.Set_Text(text)
            self.cards[data[0]] = card

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


def load_cdb(cdb_path: str) -> CDB | None:
    """加載 cdb 文件中的數據"""
    try:
        with sqlite3.connect(cdb_path) as cdb:
            cdb_cursor = cdb.cursor()
            cdb_data = CDB(cdb_path, cdb_cursor)
            return cdb_data
    except Exception as e:
        print(e)
        return None
