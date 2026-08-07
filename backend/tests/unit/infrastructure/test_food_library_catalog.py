"""FR-LIB-001 contract for the built-in 70-food preset catalog."""

from dataclasses import FrozenInstanceError
from decimal import Decimal
from types import MappingProxyType

import pytest
from app.infrastructure.db.food_library_catalog import FOOD_LIBRARY_CATALOG

EXPECTED_KEYS = {
    "spinach",
    "broccoli",
    "carrots",
    "tomatoes",
    "onion",
    "garlic",
    "mushrooms",
    "frozen-peas",
    "potato",
    "sweet-potato",
    "white-radish",
    "lotus-root",
    "chinese-yam",
    "chinese-cabbage",
    "baby-cabbage",
    "bok-choy",
    "lettuce",
    "chinese-leaf-lettuce",
    "cabbage",
    "celery",
    "celtuce",
    "cucumber",
    "eggplant",
    "green-pepper",
    "cauliflower",
    "pumpkin",
    "winter-melon",
    "green-beans",
    "shiitake",
    "enoki",
    "ginger",
    "scallion",
    "chives",
    "zucchini",
    "loofah",
    "bitter-melon",
    "corn",
    "bean-sprouts",
    "apple",
    "banana",
    "orange",
    "mandarin",
    "pear",
    "grapes",
    "watermelon",
    "cantaloupe",
    "strawberry",
    "blueberries",
    "peach",
    "mango",
    "kiwi",
    "dragon-fruit",
    "pineapple",
    "pomelo",
    "lychee",
    "lemon",
    "eggs",
    "chicken-breast",
    "chicken-thigh",
    "pork",
    "beef",
    "lamb",
    "duck",
    "fish",
    "shrimp",
    "crab",
    "tofu",
    "dried-tofu",
    "milk",
    "yogurt",
}

APPROVED_CATEGORIES = {"vegetable", "fruit", "meat", "egg", "aquatic", "soy", "dairy"}
CANONICAL_UNITS = {"g", "kg", "ml", "l", "piece"}
UNIT_DIMENSIONS = {
    "g": "mass",
    "kg": "mass",
    "ml": "volume",
    "l": "volume",
    "piece": "count",
}
STORAGE_LOCATIONS = {"FRIDGE", "FREEZER", "PANTRY"}

# Independent golden data: food key, English name, Chinese name, category,
# base unit, recommended storage, shelf-life days, and package amount/unit pairs.
GOLDEN_CATALOG = {
    row[0]: row[1:]
    for row in (
        ("spinach", "Spinach", "菠菜", "vegetable", "g", "FRIDGE", 3, (("250", "g"), ("500", "g"))),
        (
            "broccoli",
            "Broccoli",
            "西兰花",
            "vegetable",
            "g",
            "FRIDGE",
            4,
            (("300", "g"), ("500", "g")),
        ),
        (
            "carrots",
            "Carrots",
            "胡萝卜",
            "vegetable",
            "g",
            "FRIDGE",
            14,
            (("300", "g"), ("500", "g")),
        ),
        (
            "tomatoes",
            "Tomatoes",
            "西红柿",
            "vegetable",
            "g",
            "PANTRY",
            5,
            (("400", "g"), ("800", "g")),
        ),
        ("onion", "Onion", "洋葱", "vegetable", "g", "PANTRY", 30, (("300", "g"), ("600", "g"))),
        ("garlic", "Garlic", "大蒜", "vegetable", "g", "PANTRY", 30, (("100", "g"), ("250", "g"))),
        (
            "mushrooms",
            "Button mushrooms",
            "口蘑",
            "vegetable",
            "g",
            "FRIDGE",
            3,
            (("200", "g"), ("400", "g")),
        ),
        (
            "frozen-peas",
            "Peas",
            "豌豆",
            "vegetable",
            "g",
            "FREEZER",
            180,
            (("300", "g"), ("500", "g")),
        ),
        ("potato", "Potato", "土豆", "vegetable", "g", "PANTRY", 21, (("500", "g"), ("1000", "g"))),
        (
            "sweet-potato",
            "Sweet potato",
            "红薯",
            "vegetable",
            "g",
            "PANTRY",
            14,
            (("500", "g"), ("1000", "g")),
        ),
        (
            "white-radish",
            "White radish",
            "白萝卜",
            "vegetable",
            "g",
            "FRIDGE",
            7,
            (("500", "g"), ("1000", "g")),
        ),
        (
            "lotus-root",
            "Lotus root",
            "莲藕",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("400", "g"), ("800", "g")),
        ),
        (
            "chinese-yam",
            "Chinese yam",
            "山药",
            "vegetable",
            "g",
            "FRIDGE",
            10,
            (("400", "g"), ("800", "g")),
        ),
        (
            "chinese-cabbage",
            "Chinese cabbage",
            "大白菜",
            "vegetable",
            "g",
            "FRIDGE",
            7,
            (("500", "g"), ("1000", "g")),
        ),
        (
            "baby-cabbage",
            "Baby cabbage",
            "娃娃菜",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("300", "g"), ("600", "g")),
        ),
        (
            "bok-choy",
            "Bok choy",
            "上海青",
            "vegetable",
            "g",
            "FRIDGE",
            3,
            (("300", "g"), ("500", "g")),
        ),
        ("lettuce", "Lettuce", "生菜", "vegetable", "g", "FRIDGE", 3, (("250", "g"), ("500", "g"))),
        (
            "chinese-leaf-lettuce",
            "Chinese leaf lettuce",
            "油麦菜",
            "vegetable",
            "g",
            "FRIDGE",
            3,
            (("300", "g"), ("500", "g")),
        ),
        (
            "cabbage",
            "Cabbage",
            "卷心菜",
            "vegetable",
            "g",
            "FRIDGE",
            10,
            (("500", "g"), ("1000", "g")),
        ),
        ("celery", "Celery", "芹菜", "vegetable", "g", "FRIDGE", 5, (("300", "g"), ("600", "g"))),
        ("celtuce", "Celtuce", "莴笋", "vegetable", "g", "FRIDGE", 7, (("400", "g"), ("800", "g"))),
        (
            "cucumber",
            "Cucumber",
            "黄瓜",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("400", "g"), ("800", "g")),
        ),
        (
            "eggplant",
            "Eggplant",
            "茄子",
            "vegetable",
            "g",
            "FRIDGE",
            4,
            (("400", "g"), ("800", "g")),
        ),
        (
            "green-pepper",
            "Green pepper",
            "青椒",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("300", "g"), ("600", "g")),
        ),
        (
            "cauliflower",
            "Cauliflower",
            "菜花",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("400", "g"), ("800", "g")),
        ),
        (
            "pumpkin",
            "Pumpkin",
            "南瓜",
            "vegetable",
            "g",
            "PANTRY",
            30,
            (("500", "g"), ("1000", "g")),
        ),
        (
            "winter-melon",
            "Winter melon",
            "冬瓜",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("500", "g"), ("1000", "g")),
        ),
        (
            "green-beans",
            "Green beans",
            "四季豆",
            "vegetable",
            "g",
            "FRIDGE",
            4,
            (("300", "g"), ("500", "g")),
        ),
        (
            "shiitake",
            "Shiitake",
            "香菇",
            "vegetable",
            "g",
            "FRIDGE",
            4,
            (("200", "g"), ("400", "g")),
        ),
        ("enoki", "Enoki", "金针菇", "vegetable", "g", "FRIDGE", 3, (("200", "g"), ("400", "g"))),
        ("ginger", "Ginger", "生姜", "vegetable", "g", "FRIDGE", 14, (("100", "g"), ("250", "g"))),
        (
            "scallion",
            "Scallion",
            "大葱",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("100", "g"), ("250", "g")),
        ),
        (
            "chives",
            "Chinese chives",
            "韭菜",
            "vegetable",
            "g",
            "FRIDGE",
            3,
            (("200", "g"), ("400", "g")),
        ),
        (
            "zucchini",
            "Zucchini",
            "西葫芦",
            "vegetable",
            "g",
            "FRIDGE",
            5,
            (("400", "g"), ("800", "g")),
        ),
        ("loofah", "Loofah", "丝瓜", "vegetable", "g", "FRIDGE", 4, (("400", "g"), ("800", "g"))),
        (
            "bitter-melon",
            "Bitter melon",
            "苦瓜",
            "vegetable",
            "g",
            "FRIDGE",
            4,
            (("400", "g"), ("800", "g")),
        ),
        (
            "corn",
            "Fresh corn",
            "鲜玉米",
            "vegetable",
            "g",
            "FRIDGE",
            3,
            (("400", "g"), ("800", "g")),
        ),
        (
            "bean-sprouts",
            "Bean sprouts",
            "豆芽",
            "vegetable",
            "g",
            "FRIDGE",
            2,
            (("250", "g"), ("500", "g")),
        ),
        (
            "apple",
            "Apple",
            "苹果",
            "fruit",
            "piece",
            "FRIDGE",
            14,
            (("4", "piece"), ("8", "piece")),
        ),
        (
            "banana",
            "Banana",
            "香蕉",
            "fruit",
            "piece",
            "PANTRY",
            4,
            (("4", "piece"), ("8", "piece")),
        ),
        (
            "orange",
            "Orange",
            "橙子",
            "fruit",
            "piece",
            "FRIDGE",
            14,
            (("4", "piece"), ("8", "piece")),
        ),
        (
            "mandarin",
            "Mandarin",
            "橘子",
            "fruit",
            "piece",
            "FRIDGE",
            10,
            (("6", "piece"), ("12", "piece")),
        ),
        ("pear", "Pear", "梨", "fruit", "piece", "FRIDGE", 10, (("4", "piece"), ("8", "piece"))),
        ("grapes", "Grapes", "葡萄", "fruit", "g", "FRIDGE", 5, (("500", "g"), ("1000", "g"))),
        (
            "watermelon",
            "Watermelon",
            "西瓜",
            "fruit",
            "g",
            "PANTRY",
            5,
            (("1000", "g"), ("2000", "g")),
        ),
        (
            "cantaloupe",
            "Cantaloupe",
            "哈密瓜",
            "fruit",
            "g",
            "PANTRY",
            5,
            (("1000", "g"), ("2000", "g")),
        ),
        (
            "strawberry",
            "Strawberry",
            "草莓",
            "fruit",
            "g",
            "FRIDGE",
            2,
            (("250", "g"), ("500", "g")),
        ),
        (
            "blueberries",
            "Blueberries",
            "蓝莓",
            "fruit",
            "g",
            "FRIDGE",
            5,
            (("125", "g"), ("250", "g")),
        ),
        ("peach", "Peach", "桃", "fruit", "piece", "FRIDGE", 3, (("4", "piece"), ("8", "piece"))),
        ("mango", "Mango", "芒果", "fruit", "piece", "PANTRY", 4, (("2", "piece"), ("4", "piece"))),
        ("kiwi", "Kiwi", "猕猴桃", "fruit", "piece", "FRIDGE", 7, (("4", "piece"), ("8", "piece"))),
        (
            "dragon-fruit",
            "Dragon fruit",
            "火龙果",
            "fruit",
            "piece",
            "PANTRY",
            5,
            (("2", "piece"), ("4", "piece")),
        ),
        (
            "pineapple",
            "Pineapple",
            "菠萝",
            "fruit",
            "piece",
            "PANTRY",
            3,
            (("1", "piece"), ("2", "piece")),
        ),
        (
            "pomelo",
            "Pomelo",
            "柚子",
            "fruit",
            "piece",
            "PANTRY",
            14,
            (("1", "piece"), ("2", "piece")),
        ),
        ("lychee", "Lychee", "荔枝", "fruit", "g", "PANTRY", 2, (("500", "g"), ("1000", "g"))),
        (
            "lemon",
            "Lemon",
            "柠檬",
            "fruit",
            "piece",
            "FRIDGE",
            14,
            (("3", "piece"), ("6", "piece")),
        ),
        ("eggs", "Eggs", "鸡蛋", "egg", "piece", "FRIDGE", 21, (("6", "piece"), ("12", "piece"))),
        (
            "chicken-breast",
            "Chicken breast",
            "鸡胸肉",
            "meat",
            "g",
            "FRIDGE",
            1,
            (("300", "g"), ("600", "g")),
        ),
        (
            "chicken-thigh",
            "Chicken thigh",
            "鸡腿",
            "meat",
            "g",
            "FRIDGE",
            1,
            (("400", "g"), ("800", "g")),
        ),
        ("pork", "Pork", "猪肉", "meat", "g", "FRIDGE", 1, (("500", "g"), ("1000", "g"))),
        ("beef", "Beef", "牛肉", "meat", "g", "FRIDGE", 1, (("500", "g"), ("1000", "g"))),
        ("lamb", "Lamb", "羊肉", "meat", "g", "FRIDGE", 1, (("500", "g"), ("1000", "g"))),
        ("duck", "Duck", "鸭肉", "meat", "g", "FRIDGE", 1, (("500", "g"), ("1000", "g"))),
        ("fish", "Fish", "鱼", "aquatic", "g", "FRIDGE", 1, (("500", "g"), ("1000", "g"))),
        ("shrimp", "Shrimp", "虾", "aquatic", "g", "FRIDGE", 3, (("300", "g"), ("500", "g"))),
        ("crab", "Crab", "螃蟹", "aquatic", "g", "FRIDGE", 1, (("500", "g"), ("1000", "g"))),
        ("tofu", "Tofu", "豆腐", "soy", "g", "FRIDGE", 3, (("300", "g"), ("500", "g"))),
        ("dried-tofu", "Dried tofu", "豆干", "soy", "g", "FRIDGE", 5, (("200", "g"), ("400", "g"))),
        ("milk", "Milk", "牛奶", "dairy", "ml", "FRIDGE", 5, (("500", "ml"), ("1000", "ml"))),
        ("yogurt", "Yogurt", "酸奶", "dairy", "g", "FRIDGE", 5, (("200", "g"), ("500", "g"))),
    )
}


def test_catalog_contains_exactly_the_approved_fresh_food_keys() -> None:
    actual_keys = {food.food_key for food in FOOD_LIBRARY_CATALOG}

    assert len(FOOD_LIBRARY_CATALOG) == 70
    assert actual_keys == EXPECTED_KEYS
    assert "rice" not in actual_keys
    assert "pasta" not in actual_keys


def test_catalog_matches_the_reviewed_golden_metadata() -> None:
    actual = {
        food.food_key: (
            food.names["en"],
            food.names["zh-CN"],
            food.category,
            food.base_unit,
            food.recommended_storage,
            food.shelf_life[0].duration_days,
            tuple((str(preset.amount), preset.unit) for preset in food.package_presets),
        )
        for food in FOOD_LIBRARY_CATALOG
    }

    assert actual == GOLDEN_CATALOG


def test_every_preset_has_complete_bilingual_and_storage_metadata() -> None:
    for food in FOOD_LIBRARY_CATALOG:
        assert food.names["en"].strip(), food.food_key
        assert food.names["zh-CN"].strip(), food.food_key
        for locale in ("en", "zh-CN"):
            assert food.aliases[locale], (food.food_key, locale)
            assert all(alias.strip() for alias in food.aliases[locale]), (food.food_key, locale)

        assert food.category in APPROVED_CATEGORIES, food.food_key
        assert food.visual_key == food.food_key
        assert food.base_unit in CANONICAL_UNITS, food.food_key
        assert isinstance(food.rounding_increment, Decimal)
        assert food.rounding_increment > 0
        assert food.recommended_storage in STORAGE_LOCATIONS

        assert 1 <= len(food.package_presets) <= 2, food.food_key
        for preset in food.package_presets:
            assert preset.label["en"].strip(), food.food_key
            assert preset.label["zh-CN"].strip(), food.food_key
            assert isinstance(preset.amount, Decimal)
            assert preset.amount > 0
            assert preset.unit in CANONICAL_UNITS
            assert UNIT_DIMENSIONS[preset.unit] == UNIT_DIMENSIONS[food.base_unit]
            if preset.unit == food.base_unit:
                assert preset.amount % food.rounding_increment == 0, food.food_key

        assert len(food.shelf_life) == 1, food.food_key
        rule = food.shelf_life[0]
        assert rule.storage_location == food.recommended_storage
        assert isinstance(rule.duration_days, int) and not isinstance(rule.duration_days, bool)
        assert rule.duration_days > 0
        assert "editable" in rule.source_note.lower(), food.food_key


def test_high_risk_refrigerated_foods_use_the_approved_conservative_days() -> None:
    rules = {
        food.food_key: (food.recommended_storage, food.shelf_life[0].duration_days)
        for food in FOOD_LIBRARY_CATALOG
    }

    assert rules["chicken-breast"] == ("FRIDGE", 1)
    assert rules["chicken-thigh"] == ("FRIDGE", 1)
    assert rules["duck"] == ("FRIDGE", 1)
    assert rules["fish"] == ("FRIDGE", 1)
    assert rules["pork"] == ("FRIDGE", 1)
    assert rules["beef"] == ("FRIDGE", 1)
    assert rules["lamb"] == ("FRIDGE", 1)
    assert rules["shrimp"] == ("FRIDGE", 3)
    assert rules["crab"] == ("FRIDGE", 1)
    assert rules["eggs"] == ("FRIDGE", 21)


def test_packaged_chilled_food_notes_defer_to_package_instructions() -> None:
    foods = {food.food_key: food for food in FOOD_LIBRARY_CATALOG}

    for food_key in ("milk", "yogurt"):
        note = foods[food_key].shelf_life[0].source_note.lower()
        assert "package" in note
        assert "editable" in note


def test_catalog_metadata_is_deeply_immutable() -> None:
    food = FOOD_LIBRARY_CATALOG[0]
    preset = food.package_presets[0]
    proxy_type = type(MappingProxyType({}))

    assert isinstance(food.names, proxy_type)
    assert isinstance(food.aliases, proxy_type)
    assert isinstance(preset.label, proxy_type)
    with pytest.raises(TypeError):
        food.names["en"] = "Changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        food.aliases["en"] = ("changed",)  # type: ignore[index]
    with pytest.raises(TypeError):
        preset.label["en"] = "Changed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        food.food_key = "changed"  # type: ignore[misc]


def test_reviewed_aliases_are_real_search_terms() -> None:
    foods = {food.food_key: food for food in FOOD_LIBRARY_CATALOG}
    expected_zh_aliases = {
        "apple": ("红富士苹果", "pingguo"),
        "chives": ("细叶韭菜", "jiucai"),
        "strawberry": ("士多啤梨", "caomei"),
        "lychee": ("鲜荔枝", "lizhi"),
        "lemon": ("黄柠檬", "ningmeng"),
    }

    for food_key, aliases in expected_zh_aliases.items():
        assert foods[food_key].aliases["zh-CN"] == aliases

    assert foods["dried-tofu"].aliases["en"] == ("dried bean curd", "pressed tofu")
    assert "tofu sheets" not in foods["dried-tofu"].aliases["en"]


def test_generic_meat_note_covers_ground_or_minced_products() -> None:
    foods = {food.food_key: food for food in FOOD_LIBRARY_CATALOG}

    for food_key in ("pork", "beef", "lamb"):
        note = foods[food_key].shelf_life[0].source_note.lower()
        assert "ground" in note or "minced" in note
