"""Posta UM tipo (MENTALIDADE/CONTEUDO/CTA) no Instagram preservando UTF-8.
Uso: python postar.py MENTALIDADE
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

TIPO = sys.argv[1].upper()
assert TIPO in ("MENTALIDADE", "CONTEUDO", "CTA"), f"Tipo invalido: {TIPO}"

HCTI_USER = os.environ["HCTI_USER"]
HCTI_KEY = os.environ["HCTI_KEY"]
IG_USER_ID = os.environ["IG_USER_ID"]
TOKEN = os.environ["FB_TOKEN"]

with open("conteudos_gerados.json", "r", encoding="utf-8") as f:
    p = json.load(f)[TIPO]

html = (
    "<html><head><style>"
    "html,body{margin:0;padding:0;background:#fff;color:#000;color-scheme:light}*{box-sizing:border-box}"
    ".wrap{width:1080px;height:1080px;display:flex;align-items:center;justify-content:center;background:#fff;font-family:'Poppins',Arial,sans-serif;padding:80px 160px}"
    ".card{width:100%;text-align:center;color:#000}"
    ".titulo{font-size:42px;font-weight:800;line-height:1.2;margin:0 0 28px 0;color:#000}"
    ".hr{width:80px;height:3px;background:#000;border:0;margin:28px auto}"
    ".slide1{font-size:24px;font-weight:700;margin:0 0 36px 0;color:#000;line-height:1.35}"
    ".slidep{font-size:17px;font-weight:500;line-height:1.5;margin:0 0 22px 0;color:#000}"
    ".destaque{background:#F0F0F0;padding:24px 28px;border-radius:10px;margin:30px 0;font-size:18px;font-weight:700;line-height:1.4;color:#000}"
    ".slide5{font-size:15px;font-weight:500;line-height:1.5;margin:28px 0 0 0;color:#000}"
    "</style></head><body><div class='wrap'><div class='card'>"
    f"<h1 class='titulo'>{p['titulo']}</h1>"
    "<hr class='hr'>"
    f"<div class='slide1'>{p['slide1']}</div>"
    f"<p class='slidep'>{p['slide2']}</p>"
    f"<p class='slidep'>{p['slide3']}</p>"
    f"<div class='destaque'>{p['slide4']}</div>"
    f"<p class='slide5'>{p['slide5']}</p>"
    "</div></div></body></html>"
)

print(f"=== {TIPO} ===")
print("1. Gerando imagem HCTI...")
with open("_tmp.html", "w", encoding="utf-8") as f:
    f.write(html)
r = subprocess.run([
    "curl", "-s",
    "-u", f"{HCTI_USER}:{HCTI_KEY}",
    "-X", "POST", "https://hcti.io/v1/image",
    "--data-urlencode", "html@_tmp.html",
    "--data-urlencode", "google_fonts=Poppins",
    "--data-urlencode", "viewport_width=1080",
    "--data-urlencode", "viewport_height=1080",
    "--data-urlencode", "device_scale=1",
    "--data-urlencode", "ms_delay=500",
], capture_output=True, text=True, encoding="utf-8")
image_url = json.loads(r.stdout)["url"]
print(f"   URL: {image_url}")

print("2. Criando container IG...")
body = urllib.parse.urlencode({
    "image_url": image_url,
    "caption": p["legenda"],
    "access_token": TOKEN,
}, encoding="utf-8").encode("utf-8")
req = urllib.request.Request(
    f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
    data=body,
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
)
with urllib.request.urlopen(req, timeout=60) as r:
    cid = json.loads(r.read().decode("utf-8"))["id"]
print(f"   Container: {cid}")

time.sleep(5)

print("3. Publicando...")
body = urllib.parse.urlencode({"creation_id": cid, "access_token": TOKEN}).encode("utf-8")
req = urllib.request.Request(
    f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
    data=body,
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(req, timeout=60) as r:
    post_id = json.loads(r.read().decode("utf-8"))["id"]
print(f"   POST ID: {post_id}")
print(f"OK {TIPO} publicado: {post_id}")
