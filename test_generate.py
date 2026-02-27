"""Тест: генерация PDF из Markdown с дефолтными токенами."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from content_parser import parse_markdown
from pdf_generator import generate_pdf_to_file

TEST_MARKDOWN = """# Africa's {accent}$120 Billion{/accent} Dollar Crisis
## The structural USD liquidity deficit

The structural USD liquidity deficit blocking Sub-Saharan Africa's growth — and the stablecoin infrastructure opportunity it creates.

**$120B** — Trade finance — gap annually
**34.2%** — CBR decline — (2011-2022)
**$4T** — Trapped in — prefunding

# The Problem
## Why traditional banking fails Africa

Sub-Saharan Africa faces a chronic dollar shortage. Central bank reserves have declined by 34.2% since 2011, while trade finance gaps exceed $120 billion annually.

The region's dependence on commodity exports creates structural trade imbalances that conventional banking infrastructure cannot resolve.

# Our Solution
## Stablecoin infrastructure for cross-border payments

A decentralized liquidity layer that connects African businesses directly to global dollar markets, bypassing traditional correspondent banking bottlenecks.
"""

# Дефолтные токены
tokens = {
    "colors": {
        "background": "#2c2c2c",
        "text_primary": "#f5f5f5",
        "text_muted": "rgba(255,255,255,0.6)",
        "border": "#383838",
        "accent_primary": "#4F9EF8",
        "factoid_red": "#E85D5D",
        "factoid_yellow": "#F0A500",
        "factoid_cyan": "#4DD0E1",
        "factoid_green": "#14ae5c",
        "factoid_purple": "#A78BFA",
    },
    "typography": {
        "title_hero": {"family": "Inter", "weight": 800, "size": 88, "line_height": 1.1, "letter_spacing": -2.5},
        "subtitle": {"family": "Inter", "weight": 400, "size": 26, "line_height": 1.55, "letter_spacing": 0},
        "body": {"family": "Inter", "weight": 400, "size": 16, "line_height": 1.4, "letter_spacing": 0},
        "factoid_number": {"family": "Inter", "weight": 800, "size": 72, "line_height": 1.0, "letter_spacing": -2},
        "factoid_label": {"family": "Inter", "weight": 500, "size": 18, "line_height": 1.4, "letter_spacing": 0},
    },
    "layout": {"slide_width": 1920, "slide_height": 1080, "margin": 64},
}

# Парсим
slides = parse_markdown(TEST_MARKDOWN)
print(f"Слайдов: {len(slides)}")
for i, s in enumerate(slides):
    print(f"  [{i+1}] layout={s.layout}, title='{s.title[:40]}...', factoids={len(s.factoids)}")

# Генерируем PDF
output = os.path.join(os.path.dirname(__file__), "..", "remide_test_presentation.pdf")
generate_pdf_to_file(slides, tokens, output)
print(f"\nPDF создан: {output}")
