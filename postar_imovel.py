"""Renderiza o CARROSSEL do 'imovel da semana' (capa com FOTO real + slides da conta).
Le conteudo.json (gerado por gerar_imovel.py, com bloco 'imovel'), renderiza 5 PNGs e
escreve publish_manifest.json. Mantem o visual do feed (branco/preto). Nao altera postar.py.
"""
import json
import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = os.environ.get("GITHUB_REPOSITORY", "MichelOliveirax/ig-auto")
BRANCH = "main"

with open("conteudo.json", "r", encoding="utf-8") as f:
    p = json.load(f)

im = p["imovel"]
FONT = '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet">'

CSS = """
html,body{margin:0;padding:0;background:#fff;color:#000;color-scheme:light}
*{box-sizing:border-box;font-family:'Poppins',Arial,sans-serif}
.wrap{width:1080px;height:1080px;display:flex;flex-direction:column;background:#fff;color:#000;position:relative}
.pad{padding:150px 140px;flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.brand{position:absolute;bottom:64px;left:0;right:0;text-align:center;font-size:21px;font-weight:700;color:#000;opacity:0.5;letter-spacing:1px}
.label{font-size:22px;font-weight:800;color:#000;opacity:0.45;text-transform:uppercase;letter-spacing:3px;margin-bottom:28px}
.barra{width:64px;height:5px;background:#000;margin:0 auto 28px}
.texto{font-size:46px;font-weight:700;color:#000;line-height:1.25;letter-spacing:-1px;max-width:95%}
"""


def capa():
    return f"""<html><head>{FONT}<style>{CSS}
.foto{{width:1080px;height:600px;object-fit:cover;display:block;background:#0E2A47}}
.info{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:46px 90px 0}}
.local{{font-size:34px;font-weight:800;color:#000;line-height:1.2;margin-bottom:24px;max-width:96%}}
.linha-val{{display:flex;align-items:flex-end;justify-content:center;gap:28px}}
.aval{{font-size:28px;font-weight:600;color:#888;text-decoration:line-through}}
.lance{{font-size:60px;font-weight:900;color:#000;letter-spacing:-2px}}
.desc{{display:inline-block;margin-top:18px;background:#0E2A47;color:#fff;font-size:26px;font-weight:800;padding:10px 26px;border-radius:30px}}
.arr{{position:absolute;bottom:36px;left:0;right:0;text-align:center;font-size:20px;font-weight:700;color:#000;opacity:0.55;letter-spacing:1px}}
</style></head><body><div class="wrap">
<img class="foto" src="{im['foto']}"/>
<div class="info">
<div class="local">{im['local']}</div>
<div class="linha-val"><span class="aval">{im['avaliacao']}</span><span class="lance">{im['lance']}</span></div>
<div class="desc">{im['desconto']} da avaliação</div>
</div>
<div class="arr">@eusoumicheloliveira &middot; ARRASTA &rarr;</div>
</div></body></html>"""


def texto(numero, label, t):
    return f"""<html><head>{FONT}<style>{CSS}</style></head><body><div class="wrap"><div class="pad">
<div class="barra"></div><div class="label">{label}</div><div class="texto">{t}</div>
</div><div class="brand">@eusoumicheloliveira &middot; {numero:02d}/05</div></div></body></html>"""


def cta(numero, t, c):
    return f"""<html><head>{FONT}<style>{CSS}
.cta-box{{background:#0E2A47;color:#fff;padding:32px 40px;border-radius:16px;font-size:28px;font-weight:800;line-height:1.3;margin-top:28px;max-width:95%}}
</style></head><body><div class="wrap"><div class="pad">
<div class="barra"></div><div class="label">AGORA &Eacute; COM VOC&Ecirc;</div>
<div class="texto" style="font-size:40px">{t}</div>
<div class="cta-box">{c}</div>
</div><div class="brand">@eusoumicheloliveira &middot; {numero:02d}/05</div></div></body></html>"""


SLIDES = [
    capa(),
    texto(2, "QUANTO SAI DO BOLSO", p["slide2"]),
    texto(3, "OS CUSTOS", p["slide3"]),
    texto(4, "NA REVENDA", p["slide4"]),
    cta(5, p["slide5"], p.get("cta", "Curso no link. Assessoria no direct.")),
]

ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
img_dir = Path("img")
img_dir.mkdir(exist_ok=True)
png_paths = []
print("Renderizando carrossel do imovel...")
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1080, "height": 1080}, device_scale_factor=1)
    for i, html in enumerate(SLIDES, 1):
        page = ctx.new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(800)  # garante a foto carregar
        png = img_dir / f"{ts}_{i}.png"
        page.screenshot(path=str(png), type="png", clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
        page.close()
        png_paths.append(png)
        print(f"   slide {i}: {png}")
    browser.close()

image_urls = [f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/img/{ts}_{i}.png" for i in range(1, 6)]
with open("publish_manifest.json", "w", encoding="utf-8") as f:
    json.dump({
        "image_urls": image_urls,
        "caption": p["legenda"],
        "test": os.environ.get("TEST") == "1",
        "png_files": [str(x) for x in png_paths],
    }, f, ensure_ascii=False, indent=2)
print("Manifest salvo.")
