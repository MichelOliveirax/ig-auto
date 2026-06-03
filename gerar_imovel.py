"""Imovel da semana: busca um imovel real (Compra Direta / Venda Online, COM financiamento)
no agregador, calcula os custos e escreve conteudo_imovel.json pra renderizacao.
Fonte de dados: imoveiscaixaleilao.com.br (fotos vem do site oficial da Caixa).
Numeros calculados (sem alucinacao). Avaliacao = avaliacao Caixa (NAO e preco de mercado).
"""
import html as ihtml
import json
import os
import re
import ssl
import urllib.request

BASE = "https://www.imoveiscaixaleilao.com.br/imoveis?type=Casa%2CApartamento&modality=Compra+Direta%2CVenda+Online&allowFinancing=true&orderBy=price_asc"
POSTADOS_FILE = "imoveis_postados.json"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def _num(s):
    return float(s.replace(".", "").replace(",", "."))


def _br(v):
    return f"R$ {v:,.0f}".replace(",", ".")


# Estados que NUNCA devem ser postados (regra do usuario)
UF_BLOQUEADAS = {"rj"}


def buscar(paginas=3):
    imoveis = []
    for pg in range(1, paginas + 1):
        url = f"{BASE}&page={pg}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            src = urllib.request.urlopen(req, timeout=40, context=ctx).read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"  [imovel] falha pagina {pg}: {e}")
            continue
        # cada imovel e um <a href="/imoveis/<slug>-<uf>-<id>"> ... </a>
        for c in re.split(r'(?=<a [^>]*href="/imoveis/)', src):
            href = re.search(r'href="(/imoveis/[^"]+)"', c)
            foto = re.search(r'(https://venda-imoveis\.caixa\.gov\.br/fotos/\S+?\.jpg)', c)
            aval = re.search(r'line-through[^>]*>R\$\xa0?([\d\.]+,\d{2})', c)
            lance = re.search(r'font-black[^>]*>R\$\xa0?([\d\.]+,\d{2})', c)
            titulo = re.search(r'<h2[^>]*>(.*?)</h2>', c, re.S)
            if not (href and foto and aval and lance):
                continue
            uf_m = re.search(r'-([a-z]{2})-\d+', href.group(1))
            uf = uf_m.group(1) if uf_m else ""
            if uf in UF_BLOQUEADAS:
                continue  # NUNCA postar imovel do RJ
            av, la = _num(aval.group(1)), _num(lance.group(1))
            if av <= 0 or la <= 0 or la >= av:
                continue
            local = re.sub(r'<[^>]+>', ' ', titulo.group(1)).strip() if titulo else ""
            imoveis.append({
                "foto": foto.group(1),
                "foto_id": foto.group(1).rsplit("/", 1)[-1],
                "uf": uf.upper(),
                "avaliacao": av,
                "lance": la,
                "desconto": round((1 - la / av) * 100),
                "local": ihtml.unescape(re.sub(r"\s+", " ", local)),
            })
    return imoveis


def escolher(imoveis):
    """Pega o maior desconto ainda nao postado (evita repetir imovel)."""
    postados = []
    if os.path.exists(POSTADOS_FILE):
        try:
            postados = json.load(open(POSTADOS_FILE, encoding="utf-8"))
        except Exception:
            postados = []
    candidatos = [i for i in imoveis if i["foto_id"] not in postados]
    if not candidatos:
        candidatos = imoveis
    candidatos.sort(key=lambda i: i["desconto"], reverse=True)
    escolhido = candidatos[0]
    postados.append(escolhido["foto_id"])
    json.dump(postados[-60:], open(POSTADOS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return escolhido


def montar(im):
    lance = im["lance"]
    entrada = round(lance * 0.05)
    financia = round(lance - entrada)
    itbi = round(lance * 0.03)
    registro = round(lance * 0.025)
    de_bolso = entrada + itbi + registro  # custos iniciais aproximados (fora taxa de contrato/desocupacao/reforma)

    local_uf = f"{im['local']} - {im.get('uf','')}".strip(" -")
    im["local"] = local_uf
    dados = {
        "imovel": {
            "foto": im["foto"],
            "local": local_uf,
            "lance": _br(lance),
            "avaliacao": _br(im["avaliacao"]),
            "desconto": f"-{im['desconto']}%",
        },
        "titulo": f"Casa por {_br(lance)} (avaliada {_br(im['avaliacao'])})",
        "slide1": f"Imóvel avaliado em {_br(im['avaliacao'])} com lance de {_br(lance)}. Quanto sai do seu bolso?",
        "slide2": f"Entrada de 5% = {_br(entrada)}. Você financia o restante ({_br(financia)}). Não precisa do valor todo à vista.",
        "slide3": f"Custos que somam: ITBI 3% ≈ {_br(itbi)} | Registro ≈ {_br(registro)} (varia por estado) | Taxa de contrato (conforme Caixa) | Desocupação e reforma se houver.",
        "slide4": f"De bolso pra arrematar: a partir de ≈ {_br(de_bolso)} + parcelas. Na revenda: corretagem ≈ 6% e ganho de capital 15% sobre o lucro (há casos de isenção).",
        "slide5": "Esse imóvel te interessou? Quer aprender a achar e calcular oportunidades assim? Comenta QUERO.",
        "cta": "Curso no link da bio. Assessoria? Chama no direct.",
        "legenda": (
            f"🏠 {im['local']}\n"
            f"💰 Lance: {_br(lance)} | Avaliação Caixa: {_br(im['avaliacao'])} ({im['desconto']}% abaixo da avaliação)\n\n"
            f"Pra arrematar financiando você precisa de POUCO de bolso:\n"
            f"• Entrada 5%: {_br(entrada)}\n"
            f"• ITBI 3%: ≈ {_br(itbi)}\n"
            f"• Registro: ≈ {_br(registro)} (varia por estado)\n"
            f"• Taxa de contrato (conforme Caixa), desocupação e reforma se houver\n"
            f"• Na revenda: corretagem ≈ 6% e ganho de capital 15% sobre o lucro\n\n"
            f"⚠️ A avaliação da Caixa NÃO é o preço de mercado garantido — confira o valor real de revenda na região (imóveis parecidos).\n"
            f"⚠️ Confira sempre o EDITAL e o ANÚNCIO do imóvel: ocupação, dívidas (IPTU/condomínio dependem do anúncio) e estado.\n"
            f"O lucro é potencial, não garantido.\n\n"
            f"Quer aprender a achar e analisar imóveis assim? 🎓 Curso no link. 🤝 Assessoria: chama no direct.\n\n"
            f"#leilaodeimoveis #imoveiscaixa #leilaocaixa #compradireta #investimentoimobiliario "
            f"#imoveis #arrematacao #leilao #financiamentocaixa #rendaextra"
        ),
    }
    return dados


if __name__ == "__main__":
    imoveis = buscar()
    print(f"  [imovel] {len(imoveis)} imoveis com financiamento encontrados")
    if not imoveis:
        raise SystemExit("ABORTADO: nenhum imovel encontrado no site (nada sera publicado).")
    escolhido = escolher(imoveis)
    print(f"  [imovel] escolhido: {escolhido['local'][:50]} | lance {_br(escolhido['lance'])} | -{escolhido['desconto']}%")
    dados = montar(escolhido)
    with open("conteudo.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  [imovel] conteudo.json gravado. Titulo: {dados['titulo']}")
