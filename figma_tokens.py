"""
Модуль для чтения дизайн-токенов из Figma REST API.
Опционально кеширует токены, чтобы не дёргать API каждый запрос.
"""

import time
import httpx
from typing import Optional

# Кеш токенов: {file_key: {"tokens": {...}, "timestamp": float}}
_cache: dict = {}


def fetch_design_tokens(file_key: str, figma_token: str, cache_ttl_seconds: int = 0) -> dict:
    """
    Получает дизайн-токены из Figma API.
    Возвращает словарь с цветами, типографикой и метаданными.

    cache_ttl_seconds:
    - 0 или меньше: без кеша (всегда свежие стили)
    - >0: использовать кеш в секундах
    """
    ttl = max(0, int(cache_ttl_seconds))

    # Проверяем кеш
    if ttl > 0 and file_key in _cache:
        cached = _cache[file_key]
        if time.time() - cached["timestamp"] < ttl:
            return cached["tokens"]

    headers = {"X-Figma-Token": figma_token}
    base_url = f"https://api.figma.com/v1/files/{file_key}"

    # Запрашиваем файл и стили
    with httpx.Client(timeout=30) as client:
        # Получаем стили файла
        resp = client.get(base_url, headers=headers)
        resp.raise_for_status()
        file_data = resp.json()

        # Получаем опубликованные стили
        styles_resp = client.get(f"{base_url}/styles", headers=headers)
        styles_data = styles_resp.json() if styles_resp.status_code == 200 else {}

    tokens = _parse_tokens(file_data, styles_data)

    # Кешируем только при включенном TTL
    if ttl > 0:
        _cache[file_key] = {"tokens": tokens, "timestamp": time.time()}
    else:
        _cache.pop(file_key, None)

    return tokens


def _parse_tokens(file_data: dict, styles_data: dict) -> dict:
    """
    Парсит данные Figma и извлекает токены дизайн-системы.
    """
    tokens = {
        "colors": {},
        "typography": {},
        "layout": {
            "slide_width": 1920,
            "slide_height": 1080,
            "margin": 64,
            "footer_height": 40,
            "footer_y": 1016,
        },
        "zones": {},
    }

    # Обходим дерево документа
    document = file_data.get("document", {})
    _walk_tree(document, tokens, file_data.get("styles", {}))

    # Дефолтные токены, если из Figma ничего не пришло
    if not tokens["colors"]:
        tokens["colors"] = {
            "background": "#2c2c2c",
            "text_primary": "#f5f5f5",
            "text_muted": "rgba(255,255,255,0.6)",
            "border": "#383838",
            "accent_primary": "#4F9EF8",
            "factoid_red": "#E85D5D",
            "factoid_yellow": "#F0A500",
            "factoid_cyan": "#4DD0E1",
        }

    if not tokens["typography"]:
        tokens["typography"] = {
            "title_hero": {
                "family": "Inter",
                "weight": 800,
                "size": 88,
                "line_height": 1.1,
                "letter_spacing": -2.5,
            },
            "subtitle": {
                "family": "Inter",
                "weight": 400,
                "size": 26,
                "line_height": 1.55,
                "letter_spacing": 0,
            },
            "body": {
                "family": "Inter",
                "weight": 400,
                "size": 16,
                "line_height": 1.4,
                "letter_spacing": 0,
            },
            "factoid_number": {
                "family": "Inter",
                "weight": 800,
                "size": 72,
                "line_height": 1.0,
                "letter_spacing": -2,
            },
            "factoid_label": {
                "family": "Inter",
                "weight": 500,
                "size": 18,
                "line_height": 1.4,
                "letter_spacing": 0,
            },
        }

    return tokens


def _walk_tree(node: dict, tokens: dict, styles_map: dict):
    """
    Рекурсивно обходит дерево документа Figma,
    извлекая цвета, типографику и зоны.
    """
    node_name = node.get("name", "")
    node_type = node.get("type", "")

    # Извлекаем зоны (Frame с именем Zone/...)
    if node_name.startswith("Zone/") and node_type == "FRAME":
        zone_name = node_name.split("/")[1].lower()
        bbox = node.get("absoluteBoundingBox", {})
        tokens["zones"][zone_name] = {
            "x": bbox.get("x", 0),
            "y": bbox.get("y", 0),
            "width": bbox.get("width", 0),
            "height": bbox.get("height", 0),
        }

    # Извлекаем цвета из стилей
    if "fills" in node:
        for fill in node.get("fills", []):
            if fill.get("type") == "SOLID":
                color_data = fill.get("color", {})
                r = int(color_data.get("r", 0) * 255)
                g = int(color_data.get("g", 0) * 255)
                b = int(color_data.get("b", 0) * 255)
                hex_color = f"#{r:02x}{g:02x}{b:02x}"

                # Проверяем, есть ли стиль для этого элемента
                style_id = node.get("styles", {}).get("fill")
                if style_id and style_id in styles_map:
                    style_info = styles_map[style_id]
                    style_name = style_info.get("name", "").lower().replace("/", "_").replace(" ", "_")
                    if style_name:
                        tokens["colors"][style_name] = hex_color

    # Извлекаем типографику
    if "style" in node and node_type == "TEXT":
        text_style = node["style"]
        style_id = node.get("styles", {}).get("text")
        style_name = None

        if style_id and style_id in styles_map:
            style_info = styles_map[style_id]
            style_name = style_info.get("name", "").lower().replace("/", "_").replace(" ", "_")

        if style_name:
            tokens["typography"][style_name] = {
                "family": text_style.get("fontFamily", "Inter"),
                "weight": text_style.get("fontWeight", 400),
                "size": text_style.get("fontSize", 16),
                "line_height": text_style.get("lineHeightPercentFontSize", 140) / 100,
                "letter_spacing": text_style.get("letterSpacing", 0),
            }

    # Рекурсия по дочерним элементам
    for child in node.get("children", []):
        _walk_tree(child, tokens, styles_map)


def invalidate_cache(file_key: Optional[str] = None):
    """Очищает кеш токенов."""
    if file_key:
        _cache.pop(file_key, None)
    else:
        _cache.clear()
