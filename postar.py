"""Posta CARROSSEL de 5 slides no Instagram (UTF-8 preservado).
Uso: python postar.py
Le conteudo.json gerado pelo gerar.py.
"""
import base64
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

HCTI_USER = os.environ["HCTI_USER"]
HCTI_KEY = os.environ["HCTI_KEY"]
IG_USER_ID = os.environ["IG_USER_ID"]
TOKEN = os.environ["FB_TOKEN"]

with open("conteudo.json", "r", encoding="utf-8") as f:
    p = json.load(f)

# --- 5 TEMPLATES DE SLIDE (1080x1080 cada, design viral) ---

CSS_BASE = """
html,body{margin:0;padding:0;background:#fff;color:#000;color-scheme:light}
*{box-sizing:border-box;font-family:'Poppins',Arial,sans-serif}
.wrap{width:1080px;height:1080px;display:flex;flex-direction:column;background:#fff;color:#000;padding:150px 140px;position:relative;text-align:center;align-items:center}
.brand{position:absolute;bottom:70px;left:0;right:0;text-align:center;font-size:22px;font-weight:700;color:#000;opacity:0.55;letter-spacing:1px}
.pageno{position:absolute;top:70px;right:0;left:0;text-align:center;font-size:22px;font-weight:700;color:#000;opacity:0.45}
.arrow{position:absolute;bottom:140px;left:0;right:0;text-align:center;font-size:48px;color:#000;opacity:0.4}
"""

def slide_capa(titulo, hook):
    return f"""<html><head><style>{CSS_BASE}
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
<div class="brand">ARRASTA →</div>
</div></body></html>"""

def slide_texto(numero, total, label, texto):
    return f"""<html><head><style>{CSS_BASE}
.body-slide{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%}}
.label{{font-size:22px;font-weight:700;color:#000;opacity:0.45;text-transform:uppercase;letter-spacing:3px;margin-bottom:30px}}
.texto-slide{{font-size:48px;font-weight:700;color:#000;line-height:1.25;letter-spacing:-1px;max-width:95%}}
.barra{{width:60px;height:5px;background:#000;margin:0 auto 30px}}
</style></head><body><div class="wrap"><div class="body-slide">
<div class="barra"></div>
<div class="label">{label}</div>
<div class="texto-slide">{texto}</div>
</div>
<div class="brand">@eusoumicheloliveira  ·  {numero:02d}/{total:02d}</div>
</div></body></html>"""

def slide_destaque(numero, total, texto):
    """Slide com fundo preto + numeros - usado pro slide 4 (exemplo R$)"""
    return f"""<html><head><style>
html,body{{margin:0;padding:0;background:#000;color:#fff;color-scheme:dark}}
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
<div class="brand">@eusoumicheloliveira  ·  {numero:02d}/{total:02d}</div>
</div></body></html>"""

def slide_cta(numero, total, texto, cta):
    return f"""<html><head><style>{CSS_BASE}
.body-slide{{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%}}
.label{{font-size:22px;font-weight:700;color:#000;opacity:0.45;text-transform:uppercase;letter-spacing:3px;margin-bottom:30px}}
.texto-slide{{font-size:42px;font-weight:700;color:#000;line-height:1.25;letter-spacing:-1px;margin-bottom:40px;max-width:95%}}
.barra{{width:60px;height:5px;background:#000;margin:0 auto 30px}}
.cta-box{{background:#000;color:#fff;padding:32px 40px;border-radius:14px;font-size:28px;font-weight:700;line-height:1.3;margin-top:30px;max-width:95%}}
</style></head><body><div class="wrap"><div class="body-slide">
<div class="barra"></div>
<div class="label">AGORA E COM VOCE</div>
<div class="texto-slide">{texto}</div>
<div class="cta-box">{cta}</div>
</div>
<div class="brand">@eusoumicheloliveira  ·  {numero:02d}/{total:02d}</div>
</div></body></html>"""

SLIDES_HTML = [
    slide_capa(p["titulo"], p["slide1"]),
    slide_texto(2, 5, "O CONTEXTO", p["slide2"]),
    slide_texto(3, 5, "A VIRADA", p["slide3"]),
    slide_destaque(4, 5, p["slide4"]),
    slide_cta(5, 5, p["slide5"], p.get("cta", "Salva esse post.")),
]


def hcti_image(html, idx):
    path = f"_slide_{idx}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    for tentativa in range(3):
        r = subprocess.run([
            "curl", "-s",
            "-u", f"{HCTI_USER}:{HCTI_KEY}",
            "-X", "POST", "https://hcti.io/v1/image",
            "--data-urlencode", f"html@{path}",
            "--data-urlencode", "google_fonts=Poppins",
            "--data-urlencode", "viewport_width=1080",
            "--data-urlencode", "viewport_height=1080",
            "--data-urlencode", "device_scale=1",
            "--data-urlencode", "ms_delay=500",
        ], capture_output=True, text=True, encoding="utf-8")
        try:
            resp = json.loads(r.stdout)
            if resp.get("url"):
                return resp["url"]
            print(f"   HCTI tentativa {tentativa+1} sem url: {r.stdout[:300]}")
        except json.JSONDecodeError:
            print(f"   HCTI tentativa {tentativa+1} resposta invalida: {r.stdout[:300]}")
        time.sleep(3)
    raise RuntimeError(f"HCTI falhou apos 3 tentativas no slide {idx}")


def ig_post(url, params):
    body = urllib.parse.urlencode({**params, "access_token": TOKEN}, encoding="utf-8").encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


print("1. Gerando 5 imagens HCTI...")
image_urls = []
for i, html in enumerate(SLIDES_HTML, 1):
    url = hcti_image(html, i)
    print(f"   slide {i}: {url}")
    image_urls.append(url)

print("2. Criando 5 containers item (IS_CAROUSEL_ITEM)...")
child_ids = []
for i, url in enumerate(image_urls, 1):
    resp = ig_post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        {"image_url": url, "is_carousel_item": "true"},
    )
    child_ids.append(resp["id"])
    print(f"   item {i}: {resp['id']}")

print("3. Criando container do carrossel...")
carousel = ig_post(
    f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
    {
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "caption": p["legenda"],
    },
)
cid = carousel["id"]
print(f"   carousel: {cid}")

time.sleep(8)

# se TEST=1, NAO publica, so deixa o container pronto
if os.environ.get("TEST") == "1":
    print(f"TEST mode: container pronto sem publicar. ID={cid}")
    print("Imagens pra preview:")
    for u in image_urls:
        print(f"  {u}")
else:
    print("4. Publicando...")
    pub = ig_post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        {"creation_id": cid},
    )
    print(f"   POST ID: {pub['id']}")
    print(f"OK Carrossel publicado: {pub['id']}")
