import aiosqlite
from config import DB_PATH

# Wrap aiosqlite.connect to automatically inject timeout=30.0
_orig_connect = aiosqlite.connect
def custom_connect(*args, **kwargs):
    if "timeout" not in kwargs:
        kwargs["timeout"] = 30.0
    return _orig_connect(*args, **kwargs)
aiosqlite.connect = custom_connect


# ──────────────────────────── SCHEMA ────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username    TEXT,
    full_name   TEXT,
    phone       TEXT,
    is_banned   INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    icon        TEXT DEFAULT '📦',
    brand       TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER,
    name            TEXT NOT NULL,
    description     TEXT,
    price           INTEGER NOT NULL,
    old_price       INTEGER,
    image_file_id   TEXT DEFAULT '',
    stock           INTEGER DEFAULT 10,
    is_available    INTEGER DEFAULT 1,
    options         TEXT DEFAULT '',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS cart (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    selected_options TEXT DEFAULT '',
    quantity    INTEGER DEFAULT 1,
    UNIQUE(user_id, product_id, selected_options)
);

CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    status      TEXT DEFAULT 'pending',
    total_price INTEGER DEFAULT 0,
    address     TEXT,
    phone       TEXT,
    note        TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    name        TEXT NOT NULL,
    quantity    INTEGER NOT NULL,
    price       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""

# ──────────────────────────── SEED DATA ────────────────────────────

SEED_CATEGORIES = [
    # (id, name, icon, brand)
    (1,  "📱 Smartfonlar",    "📱", "Samsung"),
    (2,  "📱 Smartfonlar",    "📱", "Apple"),
    (3,  "📱 Smartfonlar",    "📱", "Xiaomi"),
    (4,  "💻 Noutbuklar",     "💻", "Apple"),
    (5,  "💻 Noutbuklar",     "💻", "Lenovo"),
    (6,  "💻 Noutbuklar",     "💻", "ASUS"),
    (7,  "📺 Televizorlar",   "📺", "Samsung"),
    (8,  "📺 Televizorlar",   "📺", "LG"),
    (9,  "📺 Televizorlar",   "📺", "Xiaomi"),
    (10, "🧊 Muzlatgichlar",  "🧊", "Artel"),
    (11, "❄️ Konditsionerlar","❄️", "Artel"),
    (12, "👕 Kir mashinalar", "👕", "Artel"),
    (13, "🎧 Naushniklar",    "🎧", "Apple"),
    (14, "🎧 Naushniklar",    "🎧", "Samsung"),
    (15, "⌚ Smart Soatlar",  "⌚", "Apple"),
    (16, "⌚ Smart Soatlar",  "⌚", "Samsung"),
]

# 1 product per category with picsum.photos placeholder images
SEED_PRODUCTS = [
    # (category_id, name, description, price, old_price, image_file_id, stock, options)

    (1,
     "Samsung Galaxy S24 Ultra",
     "6.8\" Dynamic AMOLED 2X | Snapdragon 8 Gen 3 | 200MP kamera | 5000mAh | S-Pen | Titanium",
     15_990_000, 17_000_000,
     "https://picsum.photos/seed/samsung_s24/600/400",
     6,
     '{"xotira":["256GB","512GB"],"rang":["Yellow","Gray","Black"]}'),

    (2,
     "iPhone 15 Pro Max 256GB",
     "6.7\" Super Retina XDR | A17 Pro chip | 48MP 5x Optik zum | Titan korpus | USB-C",
     14_990_000, 16_500_000,
     "https://picsum.photos/seed/iphone15pro/600/400",
     8,
     '{"xotira":["256GB","512GB","1TB"],"rang":["Natural","Blue","Black"]}'),

    (3,
     "Xiaomi 14 Pro",
     "6.73\" LTPO AMOLED 120Hz | Snapdragon 8 Gen 3 | Leica 50MP | HyperOS | 4880mAh",
     10_490_000, 11_500_000,
     "https://picsum.photos/seed/xiaomi14pro/600/400",
     9,
     '{"xotira":["256GB","512GB"],"rang":["Yashil","Qora"]}'),

    (4,
     "MacBook Air 15\" M3",
     "15.3\" Liquid Retina | Apple M3 chip | 18 soat batareya | MagSafe 3 | Wi-Fi 6E",
     16_990_000, 18_500_000,
     "https://picsum.photos/seed/macbook_m3/600/400",
     6,
     '{"ram":["8GB","16GB"],"ssd":["256GB","512GB"]}'),

    (5,
     "Lenovo LOQ 15\" Gaming",
     "15.6\" IPS 144Hz | Intel Core i5-12450H | NVIDIA RTX 4050 6GB | RGB klaviatura",
     12_990_000, 14_500_000,
     "https://picsum.photos/seed/lenovo_gaming/600/400",
     7,
     '{"ram":["16GB","32GB"],"ssd":["512GB","1TB"]}'),

    (6,
     "ASUS ROG Zephyrus G14 2024",
     "14\" QHD+ OLED 165Hz | AMD Ryzen 9 8945HS | RTX 4060 8GB | AniMe Matrix ekran",
     22_990_000, 25_000_000,
     "https://picsum.photos/seed/asus_rog/600/400",
     4,
     '{"ram":["16GB","32GB"],"ssd":["1TB","2TB"]}'),

    (7,
     "Samsung QLED 4K 55\"",
     "55\" 4K QLED | Quantum Processor 4K | Tizen Smart TV | 120Hz | AirSlim | Gaming Mode | 40W ses",
     12_990_000, 14_500_000,
     "https://picsum.photos/seed/samsung_qled/600/400",
     8,
     ''),

    (8,
     "LG OLED evo C3 55\"",
     "55\" 4K OLED | Alpha9 AI Gen6 | webOS 23 | 120Hz | Dolby Vision IQ | Dolby Atmos | G-Sync | FreeSync",
     19_990_000, 22_000_000,
     "https://picsum.photos/seed/lg_oled/600/400",
     5,
     ''),

    (9,
     "Xiaomi TV A2 Pro 55\"",
     "55\" 4K QLED | 144Hz | MIUI TV | Dolby Vision | HDR10+ | 30W ses | Chromecast | AirPlay 2",
     6_990_000, 7_800_000,
     "https://picsum.photos/seed/xiaomi_tv/600/400",
     10,
     ''),

    (10,
     "Artel Marvarid 250L",
     "No Frost texnologiyasi | A+ energiya sinfi | 250 litr | Tez muzlatish | Antibakterial qoplama | 2 yil kafolat",
     4_490_000, 4_990_000,
     "https://picsum.photos/seed/artel_fridge/600/400",
     10,
     ''),

    (11,
     "Artel Orom 12 (12000 BTU)",
     "Inverter | A+++ energiya sinfi | 12000 BTU | 35 m² xona | Issiq va sovuq | Smart nazorat | Wi-Fi boshqaruv",
     5_990_000, 6_800_000,
     "https://picsum.photos/seed/artel_ac/600/400",
     10,
     ''),

    (12,
     "Artel 7 kg Inverter FL",
     "7 kg | 1200 RPM | Inverter dvigatel | 18 dastur | A++ energiya sinfi | Olddan yuklash | Quruqlash rejimi",
     4_290_000, 4_800_000,
     "https://picsum.photos/seed/artel_wash/600/400",
     10,
     ''),

    (13,
     "Apple AirPods Pro 2 (USB-C)",
     "Faol ANC | Adaptive Audio | Transparency | 30 soat batareya | USB-C | MagSafe | Precision Finding",
     3_290_000, 3_600_000,
     "https://picsum.photos/seed/airpods_pro/600/400",
     20,
     ''),

    (14,
     "Samsung Galaxy Buds3 Pro",
     "Blade dizayn | Intelligent ANC 2.0 | Dolby Atmos | 30 soat batareya | IPX7 suv himoyasi | Hi-Fi audio",
     2_990_000, 3_300_000,
     "https://picsum.photos/seed/galaxy_buds/600/400",
     18,
     ''),

    (15,
     "Apple Watch Series 10 (46mm)",
     "46mm kengaytirilgan Retina | watchOS 11 | S10 SiP | Crash Detection | Sleep Apnea | 50m suv himoyasi",
     6_490_000, 7_200_000,
     "https://picsum.photos/seed/apple_watch/600/400",
     10,
     ''),

    (16,
     "Samsung Galaxy Watch 7 (44mm)",
     "44mm aluminium | Exynos W1000 | BioActive Sensor 3.0 | 40 soat batareya | Sleep coaching | AI salomatlik",
     3_990_000, 4_500_000,
     "https://picsum.photos/seed/galaxy_watch/600/400",
     12,
     ''),
]


# ──────────────────────────── INIT ────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
        await _migrate(db)
        await _seed(db)


async def _migrate(db):
    for stmt in [
        "ALTER TABLE products ADD COLUMN image_file_id TEXT DEFAULT ''",
        "ALTER TABLE categories ADD COLUMN brand TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN options TEXT DEFAULT ''",
    ]:
        try:
            await db.execute(stmt)
            await db.commit()
        except Exception:
            pass

    # Recreate cart table if it lacks selected_options
    try:
        async with db.execute("PRAGMA table_info(cart)") as cur:
            columns = [row[1] for row in await cur.fetchall()]
        if "selected_options" not in columns:
            await db.execute("DROP TABLE IF EXISTS cart")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    product_id  INTEGER NOT NULL,
                    selected_options TEXT DEFAULT '',
                    quantity    INTEGER DEFAULT 1,
                    UNIQUE(user_id, product_id, selected_options)
                )
            """)
            await db.commit()
    except Exception:
        pass


async def _seed(db):
    """Re-seeds categories+products when seed_version != '3'."""
    try:
        async with db.execute(
            "SELECT value FROM settings WHERE key='seed_version'"
        ) as cur:
            row = await cur.fetchone()
        if row and row[0] == "3":
            return
    except Exception:
        pass

    await db.execute("DELETE FROM products")
    await db.execute("DELETE FROM categories")
    await db.executemany(
        "INSERT OR REPLACE INTO categories (id, name, icon, brand) VALUES (?,?,?,?)",
        SEED_CATEGORIES,
    )
    await db.executemany(
        "INSERT INTO products "
        "(category_id, name, description, price, old_price, image_file_id, stock, options) "
        "VALUES (?,?,?,?,?,?,?,?)",
        SEED_PRODUCTS,
    )
    await db.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('global_discount', '0')"
    )
    await db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('seed_version', '3')"
    )
    await db.commit()


# ──────────────────────────── SETTINGS ────────────────────────────

async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
    return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await db.commit()


# ──────────────────────────── USERS ────────────────────────────

async def upsert_user(telegram_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (telegram_id, username, full_name) VALUES (?,?,?) "
            "ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name",
            (telegram_id, username, full_name),
        )
        await db.commit()


async def get_user(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id=?", (telegram_id,)
        ) as cur:
            return await cur.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE is_banned=0 ORDER BY created_at DESC"
        ) as cur:
            return await cur.fetchall()


async def get_users_page(page, per_page=10):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        ) as cur:
            rows = await cur.fetchall()
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
    return rows, total


async def ban_user(telegram_id, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned=? WHERE telegram_id=?", (value, telegram_id)
        )
        await db.commit()


async def update_user_phone(telegram_id, phone):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET phone=? WHERE telegram_id=?", (phone, telegram_id)
        )
        await db.commit()


# ──────────────────────────── BRANDS & CATEGORIES ────────────────────────────

async def get_brands():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT DISTINCT brand FROM categories WHERE brand != '' ORDER BY brand"
        ) as cur:
            return [row["brand"] for row in await cur.fetchall()]


async def get_categories_by_brand(brand: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM categories WHERE brand=? ORDER BY id", (brand,)
        ) as cur:
            return await cur.fetchall()


async def get_categories():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories ORDER BY id") as cur:
            return await cur.fetchall()


async def get_category(cat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories WHERE id=?", (cat_id,)) as cur:
            return await cur.fetchone()


# ──────────────────────────── PRODUCTS ────────────────────────────

async def get_products(category_id, page, per_page=6):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM products WHERE category_id=? AND is_available=1 "
            "ORDER BY id LIMIT ? OFFSET ?",
            (category_id, per_page, offset),
        ) as cur:
            rows = await cur.fetchall()
        async with db.execute(
            "SELECT COUNT(*) FROM products WHERE category_id=? AND is_available=1",
            (category_id,),
        ) as cur:
            total = (await cur.fetchone())[0]
    return rows, total


async def get_product(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT p.*, c.name AS cat_name, c.brand "
            "FROM products p JOIN categories c ON p.category_id=c.id WHERE p.id=?",
            (product_id,),
        ) as cur:
            return await cur.fetchone()


async def search_products(query: str, limit: int = 5):
    """
    Fuzzy relevance search across name, brand, category and description.
    Returns up to `limit` products sorted by relevance score.
    """
    import difflib
    import re

    # Common Uzbek tech synonyms: query word → expanded word added to search
    _SYNONYMS = {
        "telefon": "smartfon",
        "mobil":   "smartfon",
        "laptop":  "noutbuk",
        "kompyuter": "noutbuk",
        "pc":      "noutbuk",
        "quloqchin": "naushnik",
        "muzlatkich": "muzlatgich",
        "muzlatgich": "muzlatgich",
        "kondik":  "konditsioner",
        "kir":     "mashinalar",
        "televizor": "televizor",
    }

    q = query.lower().strip()
    q_words = [w for w in q.split() if len(w) >= 2]
    if not q_words:
        q_words = [q]

    # Expand with synonyms
    expanded = list(q_words)
    for w in q_words:
        if w in _SYNONYMS:
            expanded.append(_SYNONYMS[w])
    q_words = list(dict.fromkeys(expanded))  # deduplicate, preserve order

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT p.*, c.name AS cat_name, c.brand "
            "FROM products p JOIN categories c ON p.category_id=c.id "
            "WHERE p.is_available=1"
        ) as cur:
            all_products = await cur.fetchall()

    def _safe(row, key):
        try:
            return (row[key] or "").lower()
        except Exception:
            return ""

    def _subword(word, text):
        """
        Longest substring of `word` (min 4 chars) that appears in `text`.
        Returns normalised score 0..1. Requires ≥4 chars to avoid short false positives.
        """
        min_len = max(4, len(word) // 2)
        for length in range(len(word), min_len - 1, -1):
            for start in range(len(word) - length + 1):
                if word[start:start + length] in text:
                    return length / len(word)
        return 0.0

    def _score(p):
        name  = _safe(p, "name")
        brand = _safe(p, "brand")
        cat   = re.sub(r"[^\w\s]", "", _safe(p, "cat_name"))  # strip emoji
        desc  = _safe(p, "description")

        fields = [(name, 6), (brand, 5), (cat, 4), (desc, 1)]
        s = 0

        for field_text, w in fields:
            # Full query exact substring → highest priority
            if q in field_text:
                s += w * 5
                continue

            for word in q_words:
                if word in field_text:
                    s += w * 3
                else:
                    # Subword overlap (min 4 chars — avoids "tel"→"artel" false match)
                    sub = _subword(word, field_text)
                    if sub >= 0.4:
                        s += int(sub * w * 2)

                    # Fuzzy token match for typo tolerance (threshold 0.60)
                    for token in field_text.split():
                        if len(token) >= 3 and len(word) >= 3:
                            r = difflib.SequenceMatcher(None, word, token).ratio()
                            if r >= 0.60:
                                s += int(r * w)
        return s

    scored = []
    for p in all_products:
        s = _score(p)
        if s > 0:
            scored.append((s, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]


async def get_all_products_admin(page, per_page=8):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT p.*, c.name AS cat_name, c.brand "
            "FROM products p JOIN categories c ON p.category_id=c.id "
            "ORDER BY p.id LIMIT ? OFFSET ?",
            (per_page, offset),
        ) as cur:
            rows = await cur.fetchall()
        async with db.execute("SELECT COUNT(*) FROM products") as cur:
            total = (await cur.fetchone())[0]
    return rows, total


async def add_product(cat_id, name, description, price, old_price, stock, image_file_id=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO products "
            "(category_id, name, description, price, old_price, stock, image_file_id) "
            "VALUES (?,?,?,?,?,?,?)",
            (cat_id, name, description, price, old_price, stock, image_file_id),
        )
        await db.commit()


async def update_product_field(product_id, field, value):
    allowed = {
        "name", "description", "price", "old_price",
        "stock", "is_available", "category_id", "image_file_id",
    }
    if field not in allowed:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE products SET {field}=? WHERE id=?", (value, product_id)
        )
        await db.commit()


async def delete_product(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()


# ──────────────────────────── CART ────────────────────────────

async def cart_add(user_id, product_id, selected_options=''):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO cart (user_id, product_id, selected_options, quantity) VALUES (?,?,?,1) "
            "ON CONFLICT(user_id, product_id, selected_options) DO UPDATE SET quantity=quantity+1",
            (user_id, product_id, selected_options),
        )
        await db.commit()


async def cart_get(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT c.*, p.name, p.price, p.old_price, p.image_file_id, p.stock "
            "FROM cart c JOIN products p ON c.product_id=p.id WHERE c.user_id=?",
            (user_id,),
        ) as cur:
            return await cur.fetchall()


async def cart_remove(user_id, product_id, selected_options=''):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM cart WHERE user_id=? AND product_id=? AND selected_options=?",
            (user_id, product_id, selected_options)
        )
        await db.commit()


async def cart_clear(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        await db.commit()


async def cart_set_qty(user_id, product_id, qty, selected_options=''):
    async with aiosqlite.connect(DB_PATH) as db:
        if qty <= 0:
            await db.execute(
                "DELETE FROM cart WHERE user_id=? AND product_id=? AND selected_options=?",
                (user_id, product_id, selected_options)
            )
        else:
            await db.execute(
                "UPDATE cart SET quantity=? WHERE user_id=? AND product_id=? AND selected_options=?",
                (qty, user_id, product_id, selected_options),
            )
        await db.commit()


async def cart_remove_by_id(user_id, cart_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id=? AND id=?", (user_id, cart_id))
        await db.commit()


async def cart_set_qty_by_id(user_id, cart_id, qty):
    async with aiosqlite.connect(DB_PATH) as db:
        if qty <= 0:
            await db.execute("DELETE FROM cart WHERE user_id=? AND id=?", (user_id, cart_id))
        else:
            await db.execute("UPDATE cart SET quantity=? WHERE user_id=? AND id=?", (qty, user_id, cart_id))
        await db.commit()



# ──────────────────────────── ORDERS ────────────────────────────

async def create_order(user_id, phone, address, note):
    items = await cart_get(user_id)
    if not items:
        return 0
    total = sum(i["price"] * i["quantity"] for i in items)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders (user_id, phone, address, note, total_price) VALUES (?,?,?,?,?)",
            (user_id, phone, address, note, total),
        )
        order_id = cur.lastrowid
        await db.executemany(
            "INSERT INTO order_items (order_id, product_id, name, quantity, price) "
            "VALUES (?,?,?,?,?)",
            [
                (
                    order_id,
                    i["product_id"],
                    f"{i['name']} ({i['selected_options']})" if i["selected_options"] else i["name"],
                    i["quantity"],
                    i["price"]
                )
                for i in items
            ],
        )
        await db.commit()
    await cart_clear(user_id)
    return order_id


async def get_user_orders(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
            (user_id,),
        ) as cur:
            return await cur.fetchall()


async def get_order(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE id=?", (order_id,)) as cur:
            order = await cur.fetchone()
        async with db.execute(
            "SELECT * FROM order_items WHERE order_id=?", (order_id,)
        ) as cur:
            items = await cur.fetchall()
    return order, items


async def get_all_orders(page, status="all", per_page=8):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status == "all":
            async with db.execute(
                "SELECT o.*, u.full_name, u.username "
                "FROM orders o LEFT JOIN users u ON o.user_id=u.telegram_id "
                "ORDER BY o.created_at DESC LIMIT ? OFFSET ?",
                (per_page, offset),
            ) as cur:
                rows = await cur.fetchall()
            async with db.execute("SELECT COUNT(*) FROM orders") as cur:
                total = (await cur.fetchone())[0]
        else:
            async with db.execute(
                "SELECT o.*, u.full_name, u.username "
                "FROM orders o LEFT JOIN users u ON o.user_id=u.telegram_id "
                "WHERE o.status=? ORDER BY o.created_at DESC LIMIT ? OFFSET ?",
                (status, per_page, offset),
            ) as cur:
                rows = await cur.fetchall()
            async with db.execute(
                "SELECT COUNT(*) FROM orders WHERE status=?", (status,)
            ) as cur:
                total = (await cur.fetchone())[0]
    return rows, total


async def update_order_status(order_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET status=? WHERE id=?", (status, order_id)
        )
        await db.commit()


# ──────────────────────────── STATISTICS ────────────────────────────

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE date(created_at)=date('now')"
        ) as cur:
            today_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            total_orders = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM orders WHERE status='pending'"
        ) as cur:
            pending_orders = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM orders WHERE date(created_at)=date('now')"
        ) as cur:
            today_orders = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COALESCE(SUM(total_price),0) FROM orders WHERE status='completed'"
        ) as cur:
            revenue = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM products WHERE is_available=1"
        ) as cur:
            products = (await cur.fetchone())[0]
    return {
        "total_users": total_users,
        "today_users": today_users,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "today_orders": today_orders,
        "revenue": revenue,
        "products": products,
    }
