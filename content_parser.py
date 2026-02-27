"""
Парсер Markdown-контента → структура слайдов.

Правила:
- # Заголовок  → новый слайд, title
- ## Подзаголовок → subtitle текущего слайда
- Обычный текст → body
- **$120B** — описание → factoid
- --- layout: name → override лейаута
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Factoid:
    number: str
    label: str
    sublabel: str = ""
    color: str = ""  # будет назначен автоматически


@dataclass
class Slide:
    title: str = ""
    title_accent: str = ""  # часть заголовка с акцентным цветом
    subtitle: str = ""
    body: list[str] = field(default_factory=list)
    factoids: list[Factoid] = field(default_factory=list)
    layout: str = "auto"  # auto, default, title_hero, factoid


# Цвета для факт-карточек по умолчанию (циклятся)
FACTOID_COLORS = ["red", "yellow", "cyan", "green", "purple"]

# Паттерны
FACTOID_PATTERN = re.compile(
    r"\*\*([^*]+)\*\*\s*[—–-]\s*(.+?)(?:\s*[—–-]\s*(.+))?$"
)
LAYOUT_OVERRIDE = re.compile(r"^---\s*\nlayout:\s*(\w+)\s*\n---", re.MULTILINE)
ACCENT_PATTERN = re.compile(r"\{accent\}(.+?)\{/accent\}")


def parse_markdown(markdown: str) -> list[Slide]:
    """
    Принимает Markdown-строку, возвращает список слайдов.
    """
    slides: list[Slide] = []
    current_slide: Optional[Slide] = None

    # Убираем глобальный layout override
    lines = markdown.strip().split("\n")

    for line in lines:
        stripped = line.strip()

        # Пустая строка — пропускаем
        if not stripped:
            continue

        # Layout override
        if stripped.startswith("---"):
            layout_match = re.match(r"---\s*layout:\s*(\w+)\s*---", stripped)
            if layout_match and current_slide:
                current_slide.layout = layout_match.group(1)
            continue

        # H1 — новый слайд
        if stripped.startswith("# ") and not stripped.startswith("## "):
            current_slide = Slide()
            title_text = stripped[2:].strip()

            # Проверяем акцентную часть {accent}..{/accent}
            accent_match = ACCENT_PATTERN.search(title_text)
            if accent_match:
                current_slide.title_accent = accent_match.group(1)
                current_slide.title = ACCENT_PATTERN.sub("", title_text).strip()
            else:
                current_slide.title = title_text

            slides.append(current_slide)
            continue

        # Если слайда ещё нет — создаём дефолтный
        if current_slide is None:
            current_slide = Slide()
            slides.append(current_slide)

        # H2 — subtitle
        if stripped.startswith("## "):
            current_slide.subtitle = stripped[3:].strip()
            continue

        # Factoid: **$120B** — описание — подробности
        factoid_match = FACTOID_PATTERN.match(stripped)
        if factoid_match:
            factoid = Factoid(
                number=factoid_match.group(1),
                label=factoid_match.group(2),
                sublabel=factoid_match.group(3) or "",
            )
            current_slide.factoids.append(factoid)
            continue

        # Всё остальное — body text
        current_slide.body.append(stripped)

    # Авто-выбор лейаутов
    for slide in slides:
        if slide.layout == "auto":
            slide.layout = _auto_layout(slide)

        # Назначаем цвета факт-карточкам
        for i, factoid in enumerate(slide.factoids):
            if not factoid.color:
                factoid.color = FACTOID_COLORS[i % len(FACTOID_COLORS)]

    return slides


def _auto_layout(slide: Slide) -> str:
    """
    Автоматически выбирает лейаут по содержимому слайда.
    """
    has_factoids = len(slide.factoids) > 0
    has_body = len(slide.body) > 0
    body_length = sum(len(line) for line in slide.body)

    if has_factoids:
        return "factoid"
    elif not has_body and not slide.subtitle:
        return "title_hero"
    elif body_length > 500:
        return "default"  # text-heavy
    else:
        return "default"
