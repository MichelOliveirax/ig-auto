"""Le publish_manifest.json e publica carrossel no Instagram.
Roda DEPOIS do commit das imagens (pra raw.githubusercontent funcionar).
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

IG_USER_ID = os.environ["IG_USER_ID"]
TOKEN = os.environ["FB_TOKEN"]

with open("publish_manifest.json", "r", encoding="utf-8") as f:
    m = json.load(f)

image_urls = m["image_urls"]
caption = m["caption"]
is_test = m.get("test", False)

def ig_post(url, params):
    body = urllib.parse.urlencode({**params, "access_token": TOKEN}, encoding="utf-8").encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        corpo = ""
        try:
            corpo = e.read().decode("utf-8")
        except Exception:
            pass
        print(f"ERRO Graph API ({e.code}): {corpo}")
        raise

# Espera as imagens estarem disponiveis no raw.githubusercontent (CDN cache)
print("Aguardando CDN do GitHub propagar imagens...")
for tentativa in range(12):
    ok = 0
    for u in image_urls:
        try:
            req = urllib.request.Request(u, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    ok += 1
        except Exception:
            pass
    print(f"   tentativa {tentativa+1}: {ok}/5 imagens disponiveis")
    if ok == 5:
        break
    time.sleep(5)

print("1. Criando 5 containers item...")
child_ids = []
for i, url in enumerate(image_urls, 1):
    resp = ig_post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        {"image_url": url, "is_carousel_item": "true"},
    )
    child_ids.append(resp["id"])
    print(f"   item {i}: {resp['id']}")

print("2. Criando container do carrossel...")
carousel = ig_post(
    f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
    {"media_type": "CAROUSEL", "children": ",".join(child_ids), "caption": caption},
)
cid = carousel["id"]
print(f"   carousel: {cid}")

time.sleep(8)

if is_test:
    print(f"TEST mode: container pronto sem publicar. ID={cid}")
    for u in image_urls:
        print(f"  {u}")
else:
    print("3. Publicando...")
    pub = ig_post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        {"creation_id": cid},
    )
    print(f"OK Carrossel publicado: {pub['id']}")
