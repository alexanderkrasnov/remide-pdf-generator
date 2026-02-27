"""
RemiDe PDF Generator — веб-приложение.
Команда вставляет Markdown → получает PDF по дизайн-системе из Figma.
"""

import os
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from figma_tokens import fetch_design_tokens
from content_parser import parse_markdown
from pdf_generator import generate_pdf

app = FastAPI(title="RemiDe PDF Generator")

# Конфиг из переменных окружения
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN", "")
FIGMA_FILE_KEY = os.getenv("FIGMA_FILE_KEY", "evlu7PLuBtbw5unD8NmU9d")

# Статические файлы
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


FRONTEND_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RemiDe PDF Generator</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', sans-serif;
    background: #0f0f0f;
    color: #f5f5f5;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60px 24px;
  }

  h1 {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .subtitle {
    font-size: 16px;
    color: rgba(255,255,255,0.5);
    margin-bottom: 48px;
  }

  .container {
    width: 100%;
    max-width: 800px;
  }

  textarea {
    width: 100%;
    min-height: 400px;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 24px;
    color: #f5f5f5;
    font-family: 'Inter', monospace;
    font-size: 14px;
    line-height: 1.6;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
  }

  textarea:focus { border-color: #4F9EF8; }

  textarea::placeholder { color: rgba(255,255,255,0.25); }

  .actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
  }

  button {
    background: #4F9EF8;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 14px 32px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  button:hover { background: #3d8de0; }

  button:disabled {
    background: #333;
    cursor: not-allowed;
  }

  .hint {
    font-size: 13px;
    color: rgba(255,255,255,0.35);
  }

  .example {
    margin-top: 32px;
    padding: 20px;
    background: #141414;
    border-radius: 8px;
    border: 1px solid #222;
  }

  .example h3 {
    font-size: 14px;
    color: rgba(255,255,255,0.4);
    margin-bottom: 12px;
    font-weight: 500;
  }

  .example pre {
    font-size: 13px;
    color: rgba(255,255,255,0.6);
    line-height: 1.5;
    white-space: pre-wrap;
  }

  .spinner {
    display: none;
    width: 20px;
    height: 20px;
    border: 2px solid transparent;
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    margin-right: 8px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
  <h1>RemiDe PDF Generator</h1>
  <p class="subtitle">Вставьте Markdown — получите PDF по дизайн-системе</p>

  <div class="container">
    <form id="form" action="/generate" method="post">
      <textarea
        name="markdown"
        required
        placeholder="# Заголовок слайда&#10;## Подзаголовок&#10;&#10;Текст слайда...&#10;&#10;**$120B** — Trade finance — gap annually"
      ></textarea>

      <div class="actions">
        <span class="hint">Каждый # создаёт новый слайд</span>
        <button type="submit" id="btn">
          <span class="spinner" id="spinner"></span>
          Сгенерировать PDF
        </button>
      </div>
    </form>

    <div class="example">
      <h3>ПРИМЕР MARKDOWN:</h3>
      <pre># Africa's {accent}$120 Billion{/accent} Dollar Crisis
## The structural USD liquidity deficit

The structural USD liquidity deficit blocking
Sub-Saharan Africa's growth.

**$120B** — Trade finance — gap annually
**34.2%** — CBR decline — (2011-2022)
**$4T** — Trapped in — prefunding</pre>
    </div>
  </div>

  <script>
    document.getElementById('form').addEventListener('submit', function(e) {
      e.preventDefault();
      const btn = document.getElementById('btn');
      const spinner = document.getElementById('spinner');
      btn.disabled = true;
      spinner.style.display = 'inline-block';

      const formData = new FormData(this);
      const markdown = (formData.get('markdown') || '').toString().trim();
      if (!markdown) {
        alert('Вставьте Markdown перед генерацией');
        btn.disabled = false;
        spinner.style.display = 'none';
        return;
      }

      fetch('/generate', { method: 'POST', body: formData })
        .then(async (r) => {
          const contentType = r.headers.get('content-type') || '';
          if (!r.ok || !contentType.includes('application/pdf')) {
            const errorText = await r.text();
            throw new Error(errorText || 'Не удалось сгенерировать PDF');
          }
          return r.blob();
        })
        .then(blob => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'presentation.pdf';
          a.click();
          URL.revokeObjectURL(url);
        })
        .catch(err => alert('Ошибка: ' + err.message))
        .finally(() => {
          btn.disabled = false;
          spinner.style.display = 'none';
        });
    });
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return FRONTEND_HTML


@app.post("/generate")
async def generate(markdown: str = Form(...)):
    """Генерирует PDF из Markdown."""
    markdown = markdown.strip()
    if not markdown:
        return PlainTextResponse("Вставьте Markdown перед генерацией", status_code=400)

    # 1. Читаем токены из Figma (с кешем)
    try:
        if FIGMA_TOKEN:
            tokens = fetch_design_tokens(FIGMA_FILE_KEY, FIGMA_TOKEN)
        else:
            # Фолбэк: дефолтные токены
            tokens = _default_tokens()
    except Exception:
        # Если Figma недоступна или токен невалидный, используем дефолтные токены
        tokens = _default_tokens()

    # 2. Парсим Markdown
    slides = parse_markdown(markdown)

    if not slides:
        return PlainTextResponse("Нет слайдов для генерации", status_code=400)

    # 3. Генерируем PDF
    try:
        pdf_bytes = generate_pdf(slides, tokens)
    except Exception:
        return PlainTextResponse("Ошибка генерации PDF", status_code=500)

    if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
        return PlainTextResponse("Сгенерирован некорректный PDF", status_code=500)

    # 4. Отдаём файл
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=presentation.pdf"},
    )


def _default_tokens() -> dict:
    """Дефолтные токены если нет подключения к Figma."""
    return {
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
