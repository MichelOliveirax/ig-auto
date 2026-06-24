"""Post ONE-OFF: promocao 'Arraia da Casa Nova' (Caixa paga IPTU+condominio integral).
Carrossel 1080x1350: capa sensacional + print oficial + termos + CTA. Templado (sem Claude).
Renderiza PNGs + publish_manifest.json. Publica via publicar_ig.py.
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
AZUL = "#0B3D91"
AMARELO = "#F2B705"


def b64(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


PROMO = b64("assets/promo_arraia.jpg")

CSS = f"""
html,body{{margin:0;padding:0}}
*{{box-sizing:border-box;font-family:'Poppins',Arial,sans-serif}}
.wrap{{width:{W}px;height:{H}px;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
.brand{{position:absolute;bottom:46px;left:0;right:0;text-align:center;font-size:22px;font-weight:700;opacity:0.65}}
"""


def capa():
    return f"""<html><head>{FONT}<style>{CSS}
.wrap{{background:{AZUL};color:#fff;padding:120px 90px}}
.alerta{{font-size:30px;font-weight:800;color:{AMARELO};letter-spacing:4px;margin-bottom:24px}}
.tit{{font-size:84px;font-weight:900;line-height:1.02;letter-spacing:-2px}}
.tit span{{color:{AMARELO}}}
.sub{{font-size:40px;font-weight:800;line-height:1.25;margin-top:34px}}
.sub b{{color:{AMARELO}}}
.ag{{font-size:32px;font-weight:700;margin-top:30px;opacity:.95}}
.brand{{color:#fff}}
</style></head><body><div class="wrap">
<div class="alerta">🚨 ATENÇÃO 🚨</div>
<div class="tit">A Caixa liberou o <span>Arraiá da Casa Nova</span></div>
<div class="sub">Imóveis de leilão com <b>IPTU e condomínio 100% pagos pela CAIXA</b></div>
<div class="ag">A hora é AGORA 👇</div>
<div class="brand">@eusoumicheloliveira &middot; ARRASTA &rarr;</div></div></body></html>"""


def slide_print():
    return f"""<html><head>{FONT}<style>{CSS}
.wrap{{background:{AZUL}}}
img{{height:{H-120}px;border-radius:14px;box-shadow:0 12px 34px rgba(0,0,0,.35)}}
.brand{{color:#fff}}
</style></head><body><div class="wrap"><img src="{PROMO}"/>
<div class="brand">@eusoumicheloliveira &middot; 02/05</div></div></body></html>"""


def termos():
    return f"""<html><head>{FONT}<style>{CSS}
.wrap{{background:#fff;color:{AZUL};padding:120px 100px;justify-content:center}}
.label{{font-size:26px;font-weight:800;color:{AMARELO};text-transform:uppercase;letter-spacing:3px;margin-bottom:30px}}
.item{{font-size:42px;font-weight:700;line-height:1.35;margin:18px 0;text-align:left}}
.item b{{color:{AMARELO}}}
.val{{font-size:30px;font-weight:700;margin-top:36px;opacity:.85}}
.brand{{color:{AZUL}}}
</style></head><body><div class="wrap">
<div class="label">O que você ganha</div>
<div class="item">✅ IPTU/ITR e condomínio vencidos <b>pagos pela CAIXA</b></div>
<div class="item">✅ Pode usar <b>FGTS</b></div>
<div class="item">✅ Proposta <b>100% online</b>, com apoio gratuito de imobiliária credenciada</div>
<div class="val">📅 Campanha válida até 20/07/2026 · Lista no portal caixa.gov.br/imoveiscaixa</div>
<div class="brand">@eusoumicheloliveira &middot; 03/05</div></div></body></html>"""


def aviso():
    return f"""<html><head>{FONT}<style>{CSS}
.wrap{{background:#fff;color:{AZUL};padding:120px 100px}}
.label{{font-size:26px;font-weight:800;color:{AMARELO};text-transform:uppercase;letter-spacing:3px;margin-bottom:26px}}
.txt{{font-size:42px;font-weight:700;line-height:1.32;max-width:96%}}
.brand{{color:{AZUL}}}
</style></head><body><div class="wrap">
<div class="label">Antes de dar lance</div>
<div class="txt">A regra de cada imóvel está nas “Regras da Venda Online” e no ANÚNCIO do imóvel. Confira sempre se o imóvel participa da campanha e leia o edital.</div>
<div class="brand">@eusoumicheloliveira &middot; 04/05</div></div></body></html>"""


def cta():
    return f"""<html><head>{FONT}<style>{CSS}
.wrap{{background:{AZUL};color:#fff;padding:120px 100px}}
.label{{font-size:26px;font-weight:800;color:{AMARELO};text-transform:uppercase;letter-spacing:3px;margin-bottom:26px}}
.txt{{font-size:46px;font-weight:800;line-height:1.28}}
.box{{background:{AMARELO};color:{AZUL};padding:34px 44px;border-radius:16px;font-size:32px;font-weight:800;line-height:1.3;margin-top:34px}}
.brand{{color:#fff}}
</style></head><body><div class="wrap">
<div class="label">Agora é com você</div>
<div class="txt">Quer ajuda pra achar e arrematar um imóvel da campanha?</div>
<div class="box">🎓 Curso no link da bio · 🤝 Assessoria? Chama no direct</div>
<div class="brand">@eusoumicheloliveira &middot; 05/05</div></div></body></html>"""


SLIDES = [capa(), slide_print(), termos(), aviso(), cta()]

CAPTION = (
    "🚨 ATENÇÃO! A Caixa acabou de liberar a promoção ARRAIÁ DA CASA NOVA! 🎉\n\n"
    "Imóveis de leilão Caixa com as dívidas de IPTU/ITR e condomínio vencidas "
    "PAGAS 100% PELA CAIXA. Sim, você leu certo. 💰\n\n"
    "✅ Pagamento integral, pela Caixa, das despesas vencidas de condomínio e tributos (IPTU/ITR)\n"
    "✅ Pode usar FGTS\n"
    "✅ Proposta 100% online com apoio gratuito de imobiliária credenciada\n\n"
    "📅 Campanha válida até 20/07/2026. A lista de imóveis participantes é atualizada no portal "
    "caixa.gov.br/imoveiscaixa.\n\n"
    "⚠️ Importante: confira SEMPRE se o imóvel participa da campanha, leia as Regras da Venda Online "
    "e o anúncio/edital do imóvel antes de dar o lance.\n\n"
    "Quer ajuda pra achar e arrematar? 🎓 Curso no link da bio. 🤝 Assessoria: chama no direct. "
    "Comenta ARRAIÁ que eu te ajudo. 👇\n\n"
    "#leilaodeimoveis #imoveiscaixa #leilaocaixa #arraiadacasanova #compradireta #vendaonline "
    "#investimentoimobiliario #imoveis #arrematacao #fgts #casapropria"
)

ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
img_dir = Path("img")
img_dir.mkdir(exist_ok=True)
png_paths = []
print("Renderizando carrossel da promocao...")
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
