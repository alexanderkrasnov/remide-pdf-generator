"""
Генератор PDF: рендерит Jinja2-шаблоны и конвертирует в PDF через WeasyPrint.
"""

import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from content_parser import Slide

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def generate_pdf(slides: list[Slide], tokens: dict) -> bytes:
    """
    Принимает список слайдов и дизайн-токены.
    Возвращает байты PDF-файла.
    """
    # Настройка Jinja2
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )

    template = env.get_template("base_slide.html")

    # Путь к логотипу
    logo_path = STATIC_DIR / "logo.svg"
    logo_uri = logo_path.as_uri() if logo_path.exists() else ""

    # Рендерим HTML
    html_content = template.render(
        slides=slides,
        tokens=tokens,
        logo_path=logo_uri,
    )

    # Конвертируем в PDF
    font_config = FontConfiguration()

    page_css = CSS(
        string="""
        @page {
            size: 1920px 1080px;
            margin: 0;
        }
        html, body {
            margin: 0;
            padding: 0;
        }
        """,
        font_config=font_config,
    )

    pdf_bytes = HTML(
        string=html_content,
        base_url=str(TEMPLATES_DIR),
    ).write_pdf(
        stylesheets=[page_css],
        font_config=font_config,
        presentational_hints=True,
    )

    return pdf_bytes


def generate_pdf_to_file(slides: list[Slide], tokens: dict, output_path: str):
    """Генерирует PDF и сохраняет в файл."""
    pdf_bytes = generate_pdf(slides, tokens)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    return output_path
