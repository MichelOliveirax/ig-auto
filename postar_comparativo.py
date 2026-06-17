"""Post ONE-OFF comparativo: 2 prints reais de anuncios Caixa mostrando que a regra de
divida (IPTU/condominio) MUDA de imovel pra imovel. Embute os prints (base64) em slides 1080x1350.
Renderiza 5 PNGs + publish_manifest.json. Publicado pelo publicar_ig.py.
"""
import base64
import json
import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = os.environ.get("GITHUB_REPOSITORY", "MichelOliveirax/ig-auto")
BRANCH = "main"
W, H = 1080, 1350

FONT = '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet">'
NAVY = "#0E2A47"
GOLD = "#C2912C"


def b64(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()


PRINT1 = b64("assets/print_imovel1.png")
PRINT2 = b64("assets/print_imovel2.png")

CSS = f"""
html,body{{margin:0;padding:0;background:#fff;color:{NAVY}}}
*{{box-sizing:border-box;font-family:'Poppins',Arial,sans-serif}}
.wrap{{width:{W}px;height:{H}px;background:#fff;color:{NAVY};position:relative;display:flex;flex-direction:column;align-items:center}}
.topbar{{position:absolute;top:0;left:0;right:0;height:12px;background:{GOLD}}}
.brand{{position:absolute;bottom:48px;left:0;right:0;text-align:center;font-size:22px;font-weight:700;color:{NAVY};opacity:0.5}}
.pad{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:150px 110px}}
.eyebrow{{font-size:24px;font-weight:800;color:{GOLD};text-transform:uppercase;letter-spacing:4px;margin-bottom:30px}}
.tit{{font-size:74px;font-weight:900;line-height:1.06;letter-spacing:-2px}}
.sub{{font-size:34px;font-weight:600;opacity:0.8;margin-top:30px;line-height:1.3}}
.linha{{width:110px;height:6px;background:{GOLD};margin:34px auto}}
.label{{font-size:26px;font-weight:800;color:{GOLD};text-transform:uppercase;letter-spacing:3px;margin:130px 0 26px}}
.shot{{width:{W-120}px;border:3px solid {NAVY};border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.12)}}
.cap{{font-size:36px;font-weight:800;color:{NAVY};margin:34px 70px 0;line-height:1.3}}
.cap b{{color:{GOLD}}}
.txt{{font-size:46px;font-weight:700;line-height:1.28;letter-spacing:-1px;max-width:96%}}
.cta-box{{background:{NAVY};color:#fff;padding:34px 44px;border-radius:16px;font-size:30px;font-weight:800;line-height:1.3;margin-top:34px;max-width:96%}}
"""


def slide_capa():
    return f"""<html><head>{FONT}<style>{CSS}</style></head><body><div class="wrap"><div class="topbar"></div>
<div class="pad">
<div class="eyebrow">LEILÃO DE IMÓVEIS CAIXA</div>
<div class="tit">Mesmo site.<br/>2 regras de dívida diferentes.</div>
<div class="linha"></div>
<div class="sub">Por que você TEM que ler o anúncio antes de dar lance 👇</div>
</div>
<div class="brand">@eusoumicheloliveira &middot; ARRASTA &rarr;</div></div></body></html>"""


def slide_print(numero, img, label, cap):
    return f"""<html><head>{FONT}<style>{CSS}</style></head><body><div class="wrap"><div class="topbar"></div>
<div class="pad" style="padding:120px 60px">
<div class="label" style="margin-top:0">{label}</div>
<img class="shot" src="{img}"/>
<div class="cap">{cap}</div>
</div>
<div class="brand">@eusoumicheloliveira &middot; {numero:02d}/05</div></div></body></html>"""


def slide_txt(numero, label, t):
    return f"""<html><head>{FONT}<style>{CSS}</style></head><body><div class="wrap"><div class="topbar"></div>
<div class="pad"><div class="label" style="margin-top:0">{label}</div><div class="txt">{t}</div></div>
<div class="brand">@eusoumicheloliveira &middot; {numero:02d}/05</div></div></body></html>"""


def slide_cta(numero, t, c):
    return f"""<html><head>{FONT}<style>{CSS}</style></head><body><div class="wrap"><div class="topbar"></div>
<div class="pad"><div class="label" style="margin-top:0">AGORA &Eacute; COM VOC&Ecirc;</div>
<div class="txt" style="font-size:40px">{t}</div><div class="cta-box">{c}</div></div>
<div class="brand">@eusoumicheloliveira &middot; {numero:02d}/05</div></div></body></html>"""


SLIDES = [
    slide_capa(),
    slide_print(2, PRINT1, "IMÓVEL 1 · SÃO PAULO-SP", "IPTU: você paga se a dívida for menor que 10%. <b>Acima de 10%, a CAIXA paga.</b>"),
    slide_print(3, PRINT2, "IMÓVEL 2 · CARAPICUÍBA-SP", "IPTU: <b>100% por sua conta.</b> Sem a regra dos 10%. E ainda tem gravame na matrícula."),
    slide_txt(4, "A LIÇÃO", "Mesma despesa, regra diferente em cada imóvel. Quem paga está nas “Regras para pagamento das despesas”, no anúncio."),
    slide_cta(5, "Antes de dar lance, leia SEMPRE o anúncio e o edital. Comenta LEILÃO que eu te mando o passo a passo.",
              "Curso no link. Assessoria? Chama no direct."),
]

CAPTION = (
    "🚨 Mesmo site da Caixa, 2 imóveis, 2 regras de dívida TOTALMENTE diferentes.\n\n"
    "🏠 Imóvel 1 (São Paulo-SP): IPTU é seu se a dívida for menor que 10% da avaliação — acima de 10%, a CAIXA paga.\n"
    "🏠 Imóvel 2 (Carapicuíba-SP): IPTU é 100% por sua conta. E ainda tem gravame na matrícula (regularização por sua conta).\n\n"
    "👉 A regra de quem paga as dívidas MUDA de imóvel pra imóvel. Ela está escrita nas “Regras para pagamento das despesas”, no anúncio de cada imóvel.\n\n"
    "⚠️ Por isso NUNCA confie em regra única. SEMPRE leia o anúncio e o edital antes de dar lance — é assim que você evita herdar dívida que não esperava.\n\n"
    "Comenta LEILÃO que eu te mando o passo a passo de como analisar um anúncio. 🎓 Curso no link. 🤝 Assessoria: chama no direct.\n\n"
    "#leilaodeimoveis #imoveiscaixa #leilaocaixa #compradireta #vendaonline #investimentoimobiliario #imoveis #arrematacao #iptu #leilao"
)

ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
img_dir = Path("img")
img_dir.mkdir(exist_ok=True)
png_paths = []
print("Renderizando carrossel comparativo...")
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
    for i, html in enumerate(SLIDES, 1):
        pg = ctx.new_page()
        pg.set_content(html, wait_until="networkidle")
        pg.wait_for_timeout(500)
        out = img_dir / f"{ts}_{i}.png"
        pg.screenshot(path=str(out), type="png", clip={"x": 0, "y": 0, "width": W, "height": H})
        pg.close()
        png_paths.append(out)
        print(f"   slide {i}: {out}")
    b.close()

image_urls = [f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/img/{ts}_{i}.png" for i in range(1, 6)]
with open("publish_manifest.json", "w", encoding="utf-8") as f:
    json.dump({"image_urls": image_urls, "caption": CAPTION,
               "test": os.environ.get("TEST") == "1",
               "png_files": [str(x) for x in png_paths]}, f, ensure_ascii=False, indent=2)
print("Manifest salvo.")
