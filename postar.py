"""Posta CARROSSEL de 5 slides no Instagram.
Renderiza HTML->PNG via Playwright (local, free, unlimited).
Imagens commitadas no /img do proprio repo, servidas via raw.githubusercontent.com.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

IG_USER_ID = os.environ["IG_USER_ID"]
TOKEN = os.environ["FB_TOKEN"]
REPO = os.environ.get("GITHUB_REPOSITORY", "MichelOliveirax/ig-auto")
BRANCH = "main"

with open("conteudo.json", "r", encoding="utf-8") as f:
    p = json.load(f)

# --- TEMPLATES DE SLIDE (1080x1080, mesmo design da v1) ---

CSS_BASE = """
html,body{margin:0;padding:0;background:#fff;color:#000;color-scheme:light}
*{box-sizing:border-box;font-family:'Poppins',Arial,sans-serif}
.wrap{width:1080px;height:1080px;display:flex;flex-direction:column;background:#fff;color:#000;padding:150px 140px;position:relative;text-align:center;align-items:center}
.brand{position:absolute;bottom:70px;left:0;right:0;text-align:center;font-size:22px;font-weight:700;color:#000;opacity:0.55;letter-spacing:1px}
"""

def slide_capa(titulo, hook):
    return f"""<html><head><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet"><style>{CSS_BASE}
.capa{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%}}
.eyebrow{{font-size:22px;font-weight:600;color:#000;opacity:0.55;text-transform:uppercase;letter-spacing:3px;margin-bottom:30px}}
.titulo-capa{{font-size:82px;font-weight:900;line-height:1.05;color:#000;margin:0 0 30px 0;letter-spacing:-2px;max-width:100%}}
.hook-capa{{font-size:32px;font-weight:600;color:#000;line-height:1.3;opacity:0.85;max-width:90%}}
.linha{{width:100px;height:6px;background:#000;margin:30px auto}}
</style></head><body><div class="wrap"><div class="capa">
<div class="eyebrow">@EUSOUMICHELOLIVEIRA</div>
<div class="titulo-capa">{titulo}</div>
<div class="linha"></div>
<div class="hook-capa">{hook}</div>
</div>
<div class="brand">ARRASTA &rarr;</div>
</div></body></html>"""

def slide_texto(numero, total, label, texto):
    return f"""<html><head><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet"><style>{CSS_BASE}
.body-slide{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%}}
.label{{font-size:22px;font-weight:700;color:#000;opacity:0.45;text-transform:uppercase;letter-spacing:3px;margin-bottom:30px}}
.texto-slide{{font-size:48px;font-weight:700;color:#000;line-height:1.25;letter-spacing:-1px;max-width:95%}}
.barra{{width:60px;height:5px;background:#000;margin:0 auto 30px}}
</style></head><body><div class="wrap"><div class="body-slide">
<div class="barra"></div>
<div class="label">{label}</div>
<div class="texto-slide">{texto}</div>
</div>
<div class="brand">@eusoumicheloliveira  &middot;  {numero:02d}/{total:02d}</div>
</div></body></html>"""

def slide_destaque(numero, total, texto):
    return f"""<html><head><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet"><style>
html,body{{margin:0;padding:0;background:#000;color:#fff}}
*{{box-sizing:border-box;font-family:'Poppins',Arial,sans-serif}}
.wrap{{width:1080px;height:1080px;display:flex;flex-direction:column;background:#000;color:#fff;padding:150px 140px;position:relative;text-align:center;align-items:center}}
.body-slide{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%}}
.label{{font-size:22px;font-weight:700;color:#fff;opacity:0.6;text-transform:uppercase;letter-spacing:3px;margin-bottom:30px}}
.texto-slide{{font-size:52px;font-weight:800;color:#fff;line-height:1.2;letter-spacing:-1px;max-width:95%}}
.barra{{width:80px;height:6px;background:#fff;margin:0 auto 30px}}
.brand{{position:absolute;bottom:70px;left:0;right:0;text-align:center;font-size:22px;font-weight:700;color:#fff;opacity:0.55;letter-spacing:1px}}
</style></head><body><div class="wrap"><div class="body-slide">
<div class="barra"></div>
<div class="label">EXEMPLO REAL</div>
<div class="texto-slide">{texto}</div>
</div>
<div class="brand">@eusoumicheloliveira  &middot;  {numero:02d}/{total:02d}</div>
</div></body></html>"""

def slide_cta(numero, total, texto, cta):
    return f"""<html><head><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet"><style>{CSS_BASE}
.body-slide{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%}}
.label{{font-size:22px;font-weight:700;color:#000;opacity:0.45;text-transform:uppercase;letter-spacing:3px;margin-bottom:30px}}
.texto-slide{{font-size:42px;font-weight:700;color:#000;line-height:1.25;letter-spacing:-1px;margin-bottom:40px;max-width:95%}}
.barra{{width:60px;height:5px;background:#000;margin:0 auto 30px}}
.cta-box{{background:#000;color:#fff;padding:32px 40px;border-radius:14px;font-size:28px;font-weight:700;line-height:1.3;margin-top:30px;max-width:95%}}
</style></head><body><div class="wrap"><div class="body-slide">
<div class="barra"></div>
<div class="label">AGORA &Eacute; COM VOC&Ecirc;</div>
<div class="texto-slide">{texto}</div>
<div class="cta-box">{cta}</div>
</div>
<div class="brand">@eusoumicheloliveira  &middot;  {numero:02d}/{total:02d}</div>
</div></body></html>"""

SLIDES_HTML = [
    slide_capa(p["titulo"], p["slide1"]),
    slide_texto(2, 5, "O CONTEXTO", p["slide2"]),
    slide_texto(3, 5, "A VIRADA", p["slide3"]),
    slide_destaque(4, 5, p["slide4"]),
    slide_cta(5, 5, p["slide5"], p.get("cta", "Salva esse post.")),
]

# --- Renderiza com Playwright ---
ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
img_dir = Path("img")
img_dir.mkdir(exist_ok=True)
png_paths = []

print("1. Renderizando 5 slides via Playwright...")
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1080, "height": 1080}, device_scale_factor=1)
    for i, html in enumerate(SLIDES_HTML, 1):
        page = ctx.new_page()
        page.set_content(html, wait_until="networkidle")
        png_path = img_dir / f"{ts}_{i}.png"
        page.screenshot(path=str(png_path), type="png", clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
        page.close()
        print(f"   slide {i}: {png_path}")
        png_paths.append(png_path)
    browser.close()

# --- Commit imagens no repo (workflow faz isso) ---
# Os PNGs ficam em img/ e serao commitados pelo step seguinte do workflow

# Constroi URLs raw.githubusercontent
image_urls = [
    f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/img/{ts}_{i}.png"
    for i in range(1, 6)
]
print("URLs que serao usadas:")
for u in image_urls:
    print(f"   {u}")

# Salva manifest pra etapa seguinte
with open("publish_manifest.json", "w", encoding="utf-8") as f:
    json.dump({
        "image_urls": image_urls,
        "caption": p["legenda"],
        "test": os.environ.get("TEST") == "1",
        "png_files": [str(x) for x in png_paths],
    }, f, ensure_ascii=False, indent=2)

print("Manifest salvo. Etapa de commit + publicacao IG na sequencia.")
