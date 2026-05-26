"""Gera UM conteudo (MENTALIDADE/CONTEUDO/CTA/CASE) viral via Claude.
Uso: python gerar.py MENTALIDADE
Salva: conteudo.json (1 conteudo so) + atualiza ganchos_usados.json
"""
import json
import os
import sys
import urllib.request

TIPO = sys.argv[1].upper()
assert TIPO in ("MENTALIDADE", "CONTEUDO", "CTA", "CASE"), f"Tipo invalido: {TIPO}"

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

# carrega ganchos ja usados (ultimos 10) pra forcar variacao
HOOKS_FILE = "ganchos_usados.json"
ganchos_usados = []
if os.path.exists(HOOKS_FILE):
    try:
        ganchos_usados = json.load(open(HOOKS_FILE, encoding="utf-8"))
    except Exception:
        ganchos_usados = []

# 30 estilos de gancho para Claude escolher (rotaciona)
ESTILOS_GANCHO = [
    "pergunta provocativa que parece absurda mas tem resposta logica",
    "estatistica chocante com numero especifico (ex: 73% dos compradores...)",
    "verdade desconfortavel que ninguem fala",
    "comparacao inesperada entre 2 caminhos",
    "confissao pessoal que cria identificacao",
    "mito popular que voce vai derrubar",
    "cenario hipotetico vivido (Imagina que...)",
    "erro caro que pessoas cometem",
    "numero especifico do dia/mes/ano",
    "frase polemica que divide opinioes",
    "antes vs depois com transformacao real",
    "calculo simples revelador (R$ X / mes = Y em 1 ano)",
    "metafora visual forte",
    "segredo dos profissionais da area",
    "lista do que NAO fazer",
    "promessa especifica e mensuravel",
    "historia curta de 3 frases com twist",
    "pergunta retorica que so quem entende responde",
    "alerta urgente baseado em fato recente",
    "contradicao da industria",
    "termo tecnico explicado simples (jargao desmistificado)",
    "case anonimo: aluno X arrematou Y",
    "comparacao com investimento popular (poupanca, tesouro)",
    "checklist de 3 itens essenciais",
    "frase de impacto que dura na cabeca",
    "data limite real (proximo leilao em X dias)",
    "padrao que se repete (notei que...)",
    "exemplo numerico tangivel (imovel de R$ X arrematado por R$ Y)",
    "vies cognitivo do investidor leigo",
    "regra inversa: faca o oposto da maioria",
]

# CONHECIMENTO TECNICO OBRIGATORIO - injetado em todo prompt pra evitar alucinacao
CONHECIMENTO_TECNICO = """
=== VERDADES TECNICAS DO LEILAO DE IMOVEIS NO BRASIL (NUNCA CONTRADIGA) ===

CUSTOS REAIS de uma arrematacao (use SEMPRE quando falar de "lance + custos" ou calcular ROI):
1. Lance (valor pago no leilao)
2. Comissao do leiloeiro: 5% sobre o valor do lance (extrajudicial) ou 5% sobre o lance (judicial, fixada por lei)
3. ITBI: 2% a 3% do valor (varia por municipio) - SP=3%, RJ=2%, BH=3%
4. Registro do imovel no cartorio: ~1% do valor (taxa cartorial)
5. Dividas em atraso herdadas (CASO o edital nao quite):
   - IPTU atrasado
   - Condominio atrasado (em leilao extrajudicial NAO se transfere, em judicial pode)
   - Taxas de servico (lixo, agua)
6. Custo de desocupacao se imovel ocupado: acao de imissao na posse (R$ 3-15mil + 6-18 meses)
7. Reforma (variavel)
8. Documentacao: averbacao da carta de arrematacao (R$ 500-2000)
9. SE FINANCIADO: parcelas do financiamento + custos do contrato Caixa
10. Imposto sobre ganho de capital na venda: 15% sobre lucro (pessoa fisica) - 22.5% se >R$5mi

REGRAS LEGAIS:
- Carta de arrematacao = documento que comprova propriedade (sai em 30-60 dias)
- Prazo de pagamento: 24h apos arremate (extrajudicial) ou 15 dias (judicial)
- Sinal: 5% no ato, restante em ate 24h (extrajudicial)
- Multa por desistencia: 20% do lance + perda do sinal
- Imovel ocupado: arrematante assume a desocupacao
- Hipoteca: extinta automaticamente apos arrematacao (Lei 9.514)
- Penhora trabalhista: NAO se extingue, herdada pelo arrematante (CUIDADO)
- IPVA/multas: irrelevante (so imovel, nao veiculo)

NUMEROS REALISTAS (use como base):
- Desconto medio em leilao judicial 1a praca: 0% (avaliacao)
- Desconto em 2a praca: 25% a 50%
- Desconto em extrajudicial banco: 20% a 40%
- Tempo medio entre arremate e posse: 3 a 12 meses (livre) ou 6 a 24 meses (ocupado)
- Custo total real (lance + tudo): ~12% a 18% acima do lance

JAMAIS DIGA:
- "Custos = despejo + reforma" (incompleto e amador)
- "Ganho 50% garantido" (nao existe garantia)
- "Sem riscos" (sempre tem risco juridico)
- Valores impossiveis (apto SP centro arrematado por R$ 50mil)
- "Caixa devolve dinheiro se desistir" (nao devolve)

QUANDO FALAR EM EXEMPLO NUMERICO, use estrutura:
"Imovel avaliado R$ X | Lance R$ Y | + Custos (ITBI/registro/leiloeiro/desocupacao) ~12% = Investimento total R$ Z | Vende por R$ W | Lucro liquido R$ K apos IR 15%"
"""

PROMPTS = {
    "MENTALIDADE": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao de imoveis (judicial e extrajudicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Tom: autoridade tecnica + linguagem direta de quem ja viu tudo. Tambem e copywriter VIRAL. Cria post pra @eusoumicheloliveira que vai postar AGORA no horario de mentalidade (09h).

OBJETIVO: gerar identificacao + insight de mentalidade de investidor. NAO vender curso.

ESTRUTURA OBRIGATORIA (carrossel 5 slides):
- titulo (5-8 palavras, impactante, vira capa do slide 1)
- slide1: HOOK gancho (max 12 palavras, formato pergunta/afirmacao chocante)
- slide2: o problema/contexto (max 20 palavras)
- slide3: a virada/insight (max 25 palavras)
- slide4: exemplo numerico CONCRETO com R$ (max 25 palavras)
- slide5: pergunta que gera comentario + chamada pra salvar (max 22 palavras)
- legenda: 4-6 paragrafos curtos com emojis. Final OBRIGATORIO: pergunta direta + "Comenta aqui embaixo 👇" + linha em branco + 8 hashtags relevantes
- cta: literal "Salva esse post se voce vai arrematar seu 1o imovel em 2026."

REGRA DE GANCHO: usa estilo "{estilo}". NUNCA repetir esses ganchos ja usados: {ganchos_usados}

REGRA DE VIRALIZACAO:
- Numeros especificos (nao "muito barato", mas "R$ 180.000")
- Tom direto, brasileiro, sem palavra dificil
- Frases curtas (max 15 palavras cada)
- ZERO mencao ao curso

Retorne SOMENTE JSON, comecando com {{""",

    "CONTEUDO": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao de imoveis (judicial e extrajudicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Tom: autoridade tecnica + linguagem direta de quem ja viu tudo. Tambem e copywriter VIRAL. Cria post EDUCATIVO pra @eusoumicheloliveira no horario de conteudo (13h).

OBJETIVO: ensinar UM conceito tecnico de leilao em 5 slides. Salvavel = viralizavel.

ESCOLHA UM TEMA dessa lista (varie a cada vez): prazo de desfazimento, calculo de lance maximo, imovel ocupado vs livre, edital - o que olhar, ITBI no leilao, sinal de 5%, fim de hipoteca, leilao judicial vs extrajudicial, divida do anterior, condominio em atraso, vistoria possivel?, financiamento direto Caixa, comissao do leiloeiro, cuidados com averbacao, prazo pra pagar, multa de 20%, recurso de arrematante, posse vs propriedade, registrar com decisao judicial, custo total real (lance + custos).

ESTRUTURA (carrossel 5 slides):
- titulo (titulo do tema, 5-8 palavras)
- slide1: gancho-pergunta que provoca curiosidade (max 14 palavras)
- slide2: a definicao em 1 frase clara (max 22 palavras)
- slide3: como funciona na pratica (max 25 palavras)
- slide4: exemplo numerico real com R$ (max 25 palavras)
- slide5: dica pratica + pergunta (max 22 palavras)
- legenda: 4-6 paragrafos com emojis. Final OBRIGATORIO: pergunta + "Conta aqui 👇" + 8 hashtags
- cta: "Comenta QUERO SABER MAIS pra eu fazer mais conteudos desses."

REGRA DE GANCHO: usa estilo "{estilo}". NAO repetir: {ganchos_usados}

ZERO mencao a curso. Tom: professor amigo. Retorne SOMENTE JSON.""",

    "CTA": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao de imoveis (judicial e extrajudicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Tom: autoridade tecnica + linguagem direta de quem ja viu tudo. Tambem e copywriter VIRAL. Cria post de VENDA pra curso "Arremate em 30 Dias" no @eusoumicheloliveira (18h, terca ou sexta).

OBJETIVO: vender curso SEM parecer venda agressiva. Promessa especifica + prova social + escassez sutil.

ESTRUTURA (carrossel 5 slides):
- titulo (titulo do post, 5-8 palavras)
- slide1: gancho que cria desejo (max 14 palavras)
- slide2: dor do nao-investidor (max 22 palavras)
- slide3: ponte: o que muda quando entende leilao (max 25 palavras)
- slide4: prova: numeros de aluno real ou seus (R$ arrematado, % desconto) max 25 palavras
- slide5: convite suave + pergunta (max 22 palavras)
- legenda: 5-7 paragrafos com emojis. Final OBRIGATORIO: pergunta + "Comenta EU QUERO ou link na bio" + linha em branco + 8 hashtags
- cta: "Comenta EU QUERO ou acessa o link da bio. Arremate em 30 Dias."

REGRA DE GANCHO: usa estilo "{estilo}". NAO repetir: {ganchos_usados}

NUNCA usar "Imagina arrematar seu primeiro imovel" - frase batida. Retorne SOMENTE JSON.""",

    "CASE": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao de imoveis (judicial e extrajudicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Tom: autoridade tecnica + linguagem direta de quem ja viu tudo. Tambem e copywriter VIRAL. Cria CASE DE SUCESSO (real ou plausivel) pra @eusoumicheloliveira no horario de fechamento (18h).

OBJETIVO: contar UMA historia curta de arrematacao bem-sucedida com numeros reais. Prova social = converte.

INVENTE um case plausivel (apto/casa/sala comercial, cidade brasileira, valor de mercado, valor arrematado, lucro/economia). Use nome fictio ("Carlos, sao paulo, 38 anos").

ESTRUTURA (carrossel 5 slides):
- titulo (resumo do case, 5-8 palavras)
- slide1: gancho com numero do case (max 14 palavras)
- slide2: contexto: quem era a pessoa antes (max 22 palavras)
- slide3: o que ela fez (acao especifica) (max 25 palavras)
- slide4: numeros: avaliacao R$ X, lance R$ Y, economia R$ Z (max 25 palavras)
- slide5: licao aprendida + pergunta (max 22 palavras)
- legenda: 5-7 paragrafos narrativos com emojis. Final OBRIGATORIO: pergunta + "Comenta aqui 👇" + 8 hashtags
- cta: "Salva esse case pra inspirar sua proxima arrematacao."

REGRA DE GANCHO: usa estilo "{estilo}". NAO repetir: {ganchos_usados}

Retorne SOMENTE JSON.""",
}

import random
estilo = random.choice(ESTILOS_GANCHO)

prompt = PROMPTS[TIPO].format(
    estilo=estilo,
    ganchos_usados=json.dumps(ganchos_usados[-10:], ensure_ascii=False),
) + "\n\n" + CONHECIMENTO_TECNICO + "\n\nRESPEITE 100% as verdades tecnicas acima. Se o post mencionar custos, calcular ROI, ou citar leis, USE os numeros e regras dessa base. Errar = perder credibilidade do perfil."

body = json.dumps({
    "model": "claude-sonnet-4-5",
    "max_tokens": 3000,
    "messages": [{"role": "user", "content": prompt}],
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
if texto.startswith("```"):
    texto = texto.split("```")[1]
    if texto.startswith("json"):
        texto = texto[4:]
texto = texto.strip()

data = json.loads(texto)

for campo in ["titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda"]:
    assert data.get(campo), f"Campo vazio: {campo}"

with open("conteudo.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# salva o gancho usado pra nao repetir
ganchos_usados.append(data["slide1"])
ganchos_usados = ganchos_usados[-30:]  # mantem ultimos 30
with open(HOOKS_FILE, "w", encoding="utf-8") as f:
    json.dump(ganchos_usados, f, ensure_ascii=False, indent=2)

print(f"Conteudo {TIPO} gerado:")
print(f"  Titulo: {data['titulo']}")
print(f"  Hook (estilo {estilo[:40]}): {data['slide1']}")
