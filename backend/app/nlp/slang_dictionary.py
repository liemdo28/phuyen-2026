from __future__ import annotations


SLANG_PATTERNS: list[tuple[str, str]] = [
    ("bill", "hoa don"),
    ("task", "cong viec"),
    ("deal", "giao dich"),
    ("cafe nào chill", "ca phe quan yen tinh"),
    ("cafe nao chill", "ca phe quan yen tinh"),
    ("cà phê nào chill", "ca phe quan yen tinh"),
    ("quan chill", "quan yen tinh"),
    ("quan nào chill", "quan yen tinh"),
    ("quán nào chill", "quan yen tinh"),
    ("chill", "thu gian"),
    ("local local", "dia phuong"),
    ("cafe dep dep", "cafe dep"),
    ("luôn", "cung mot ngu canh"),
    ("cafe", "ca phe"),
    ("quan khuya", "quan mo khuya"),
    ("luon", "cung mot ngu canh"),
    ("cai tren", "ban ghi truoc do"),
    ("cái trên", "ban ghi truoc do"),
    ("cai hom qua", "ban ghi hom qua"),
    ("cái hôm qua", "ban ghi hom qua"),
    ("task kia", "cong viec truoc do"),
    ("2 cu", "2 trieu"),
    ("2 củ", "2 trieu"),
    ("cu", "trieu"),
    ("củ", "trieu"),
]


CANONICAL_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "utilities_electricity": ["dien", "bill dien", "hoa don dien"],
    "utilities_water": ["nuoc", "bill nuoc", "hoa don nuoc"],
    "materials_paint": ["son", "tien son", "chi phi son"],
    "food_and_beverage": ["an", "uong", "ca phe", "quan an", "quan mo khuya"],
    "transport": ["xang", "grab", "taxi", "ve", "di chuyen"],
}
