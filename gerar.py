"""Gera 3 conteudos (MENTALIDADE/CONTEUDO/CTA) via Claude API e salva em conteudos_gerados.json."""
import json
import os
import urllib.request

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

PROMPT = """Voce e copywriter especialista em leilao de imoveis no Instagram (@eusoumicheloliveira).

Gere 3 conteudos em JSON puro (sem markdown, sem comentarios), com esta estrutura EXATA:

{
  "MENTALIDADE": {
    "titulo": "...",
    "slide1": "...",
    "slide2": "...",
    "slide3": "...",
    "slide4": "...",
    "slide5": "...",
    "legenda": "... com emojis e hashtags ...",
    "cta": "..."
  },
  "CONTEUDO": { mesma estrutura },
  "CTA": { mesma estrutura }
}

Regras:
- MENTALIDADE: post sobre mentalidade de investidor / por que agir agora
- CONTEUDO: post tecnico/educativo sobre leilao de imoveis
- CTA: post chamando pro curso "Arremate em 30 Dias"
- titulo: 5-8 palavras impactantes
- slide1: pergunta ou afirmacao gancho (max 20 palavras)
- slide2/slide3: explicacao em 1 frase cada (max 25 palavras)
- slide4: exemplo numerico concreto (R$ valor arrematado vs valor mercado)
- slide5: fechamento + chamada (max 25 palavras)
- legenda: 6-10 paragrafos curtos com emojis, terminando com 10 hashtags
- Tom: direto, brasileiro, vendedor

Retorne SOMENTE o JSON, comecando com { e terminando com }."""

body = json.dumps({
    "model": "claude-sonnet-4-5",
    "max_tokens": 4000,
    "messages": [{"role": "user", "content": PROMPT}],
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=body,
    headers={
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=120) as r:
    resp = json.loads(r.read().decode("utf-8"))

texto = resp["content"][0]["text"].strip()
# remove cercas markdown se vierem
if texto.startswith("```"):
    texto = texto.split("```")[1]
    if texto.startswith("json"):
        texto = texto[4:]
texto = texto.strip()

data = json.loads(texto)

# valida estrutura
for tipo in ["MENTALIDADE", "CONTEUDO", "CTA"]:
    p = data[tipo]
    for campo in ["titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda"]:
        assert p.get(campo), f"Campo vazio: {tipo}.{campo}"

with open("conteudos_gerados.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Conteudos gerados com sucesso")
for tipo in data:
    print(f"  {tipo}: {data[tipo]['titulo']}")
