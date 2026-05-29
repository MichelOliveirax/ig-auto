"""Gera UM conteudo (MENTALIDADE/CONTEUDO/CTA/CASE) viral via Claude.
Uso: python gerar.py MENTALIDADE
Salva: conteudo.json (1 conteudo so) + atualiza ganchos_usados.json
"""
import json
import os
import re
import sys
import urllib.request

TIPO = sys.argv[1].upper()
assert TIPO in ("MENTALIDADE", "CONTEUDO", "CTA", "CASE"), f"Tipo invalido: {TIPO}"

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

# carrega ganchos ja usados pra forcar variacao
HOOKS_FILE = "ganchos_usados.json"
ganchos_usados = []
if os.path.exists(HOOKS_FILE):
    try:
        ganchos_usados = json.load(open(HOOKS_FILE, encoding="utf-8"))
    except Exception:
        ganchos_usados = []

# historico rico (titulo + gancho) dos ultimos posts pra evitar conteudo repetido
HIST_FILE = "historico_posts.json"
historico = []
if os.path.exists(HIST_FILE):
    try:
        historico = json.load(open(HIST_FILE, encoding="utf-8"))
    except Exception:
        historico = []

# VERIFICA DIRETO NO INSTAGRAM: puxa legendas dos ultimos posts reais da conta
# pra detectar repeticao mesmo de posts feitos antes do historico local existir.
def buscar_posts_instagram():
    ig_id = os.environ.get("IG_USER_ID")
    token = os.environ.get("FB_TOKEN")
    if not ig_id or not token:
        print("  [instagram] IG_USER_ID/FB_TOKEN ausentes - pulando verificacao no IG")
        return []
    try:
        url = (
            f"https://graph.facebook.com/v19.0/{ig_id}/media"
            f"?fields=caption,timestamp&limit=50&access_token={token}"
        )
        with urllib.request.urlopen(url, timeout=30) as r:
            dados = json.loads(r.read().decode("utf-8"))
        posts = []
        for item in dados.get("data", []):
            cap = (item.get("caption") or "").strip()
            if not cap:
                continue
            # remove hashtags pra comparar so o conteudo
            cap_limpo = re.sub(r"#\S+", "", cap).strip()
            primeira_linha = cap_limpo.split("\n")[0].strip()
            posts.append({"titulo": primeira_linha, "slide1": cap_limpo[:200]})
        print(f"  [instagram] {len(posts)} posts reais carregados da conta pra comparacao")
        return posts
    except Exception as e:
        print(f"  [instagram] falha ao buscar posts (seguindo com historico local): {e}")
        return []


# historico_local = o que persiste no arquivo. historico = usado so pra comparar (local + IG)
historico_local = list(historico)
posts_ig = buscar_posts_instagram()
historico = historico + posts_ig

titulos_recentes = [h.get("titulo", "") for h in historico if h.get("titulo")][-50:]


def _palavras(s):
    """tokens significativos (>3 letras) em minusculo pra comparar similaridade."""
    s = (s or "").lower()
    s = re.sub(r"[^0-9a-zà-ÿ ]", " ", s)
    stop = {"para", "como", "esse", "essa", "isso", "voce", "seu", "sua", "que",
            "com", "uma", "dos", "das", "por", "mais", "imovel", "imoveis",
            "leilao", "caixa", "arrematar", "arrematacao"}
    return {w for w in s.split() if len(w) > 3 and w not in stop}


def _similaridade(a, b):
    sa, sb = _palavras(a), _palavras(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# palavras que identificam o TEMA do post. Se uma delas aparecer no post novo
# E em qualquer post recente, e o mesmo assunto -> bloqueia.
TOKENS_TEMA = {
    "entrada", "financiamento", "financiar", "fgts", "sinal", "iptu",
    "condominio", "cronometro", "comissao", "leiloeiro", "ocupado",
    "desocupacao", "despejo", "hipoteca", "penhora", "vistoria", "matricula",
}


# TRAVA JUDICIAL: REGRA ABSOLUTA - nenhum post pode falar de leilao judicial.
TERMOS_JUDICIAL = [
    "judicial", "judiciais", "praca", "praça", "1a praca", "2a praca",
    "hasta publica", "hasta pública", "cpc", "codigo de processo civil",
    "vara civel", "vara cível", "execucao fiscal", "execução fiscal",
    "penhora judicial", "leilao do juiz", "leilão do juiz", "edital do juiz",
]


def _tem_judicial(data):
    """Retorna o termo judicial encontrado em qualquer campo, ou None."""
    texto = " ".join(str(data.get(c, "")) for c in
                      ["titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda", "cta"])
    texto = texto.lower()
    # remove "extrajudicial"/"extrajudiciais" pra nao dar falso positivo com "judicial"
    texto = texto.replace("extrajudiciais", " ").replace("extrajudicial", " ")
    for termo in TERMOS_JUDICIAL:
        if termo in texto:
            return termo
    return None


def _e_repetido(titulo, slide1):
    """True se titulo/gancho forem parecidos OU tratarem do mesmo tema ja postado."""
    tok_novo = _palavras(titulo) | _palavras(slide1)
    temas_novos = tok_novo & TOKENS_TEMA
    for h in historico:
        ht = h.get("titulo", "")
        hg = h.get("slide1", "")
        # 1) similaridade alta de texto (limiar rigido)
        if _similaridade(titulo, ht) >= 0.34:
            return True, ht
        if _similaridade(slide1, hg) >= 0.45:
            return True, hg
        # 2) mesmo TEMA distintivo (ex: entrada, financiamento, iptu...)
        tok_hist = _palavras(ht) | _palavras(hg)
        temas_comuns = temas_novos & tok_hist
        if temas_comuns:
            return True, f"{ht or hg[:40]} (mesmo tema: {', '.join(sorted(temas_comuns))})"
        # 3) compartilham 2+ palavras significativas no titulo
        if len(_palavras(titulo) & _palavras(ht)) >= 2:
            return True, ht
    return False, None

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
================ ESCOPO DOS POSTS (REGRA FIXA - NUNCA VIOLAR) ================
TRABALHAMOS APENAS COM LEILAO EXTRAJUDICIAL E APENAS IMOVEIS CAIXA.
- PROIBIDO falar de leilao JUDICIAL nos posts (nada de praca, CPC, multa 20% judicial, etc).
- Todo conteudo deve girar em torno das modalidades CAIXA extrajudicial:
  1o/2o Leilao SFI, Licitacao Aberta, Venda Online, Compra/Venda Direta.
- As regras de leilao judicial abaixo servem SO como referencia interna para NAO confundir.
  NUNCA cite regra judicial num post. Se um tema so se aplica a judicial, NAO use.
=============================================================================

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
- Multa por desistencia (LEILAO JUDICIAL generico, NAO Caixa): 20% do lance + perda do sinal
- Imovel ocupado: arrematante assume a desocupacao

================ MULTA POR MODALIDADE (REGRA CRITICA - NUNCA ERRAR) ================
ANTES de afirmar QUALQUER multa/penalidade num post, confira EXATAMENTE a modalidade:

1) LEILAO SFI (1o e 2o Leilao) e LICITACAO ABERTA (extrajudicial Caixa):
   - TEM multa por desistencia = 5% do lance + perda da comissao paga ao leiloeiro
   - Pode haver impedimento de participar de futuros leiloes Caixa
   - NAO TEM direito de arrependimento
2) VENDA ONLINE (Caixa):
   - Segue Regras da Venda Online. Confirmar no documento antes de citar valor de multa.
   - NAO afirmar "multa de 20%" - isso e leilao judicial, NAO Caixa.
3) COMPRA DIRETA / VENDA DIRETA (Lei 13.303/2016):
   - Regras proprias. NAO assumir a mesma multa do leilao SFI.
4) LEILAO JUDICIAL (fora Caixa):
   - Multa pode chegar a 20% do lance + perda do sinal (CPC). NUNCA misturar com Caixa.

REGRA: o numero "20%" NUNCA pode aparecer associado a imovel CAIXA. Caixa = 5%.
Se nao tiver certeza da multa daquela modalidade especifica, NAO cite numero de multa no post.
====================================================================================
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

=== IMOVEIS CAIXA - 5 MODALIDADES (FONTE: CARTILHA OFICIAL CAIXA JUN/2024) ===
PRIORIZE conteudo sobre Imoveis Caixa - publico ama. Site oficial: caixa.gov.br/imoveiscaixa

1) 1o LEILAO SFI (Lei 9.514/97 art 27):
   - Valor minimo: garantia atualizada OU avaliacao prefeitura (o maior)
   - Comissao leiloeiro: 5% (pago separado, NAO entra no lance)
   - IPTU/condominio atrasado: ARREMATANTE PAGA (Caixa nao quita)
   - Onde: site do leiloeiro (edital)
   - Tem imobiliaria credenciada gratis (Caixa paga)

2) 2o LEILAO SFI:
   - Valor minimo: divida do contrato + despesas de consolidacao
   - Comissao 5% pago separado
   - IPTU/condominio: ARREMATANTE PAGA
   - Geralmente mais barato que 1o leilao

3) LICITACAO ABERTA (Lei 13.303/2017):
   - Valor: avaliacao Caixa COM desconto
   - Comissao 5%
   - IPTU/condominio atrasado: DEPENDE DO ANUNCIO/EDITAL. A Caixa NAO esta quitando IPTU. NUNCA afirme que a Caixa paga - mande consultar o anuncio do imovel e o edital.
   - Site do leiloeiro

4) VENDA ONLINE (cronometro ativo):
   - Direto no site da Caixa (sem leiloeiro)
   - SEM comissao de 5%
   - Vence a MAIOR proposta quando o cronometro zerar
   - IPTU/condominio atrasado: DEPENDE DO ANUNCIO do imovel. NUNCA afirme que a Caixa quita - cada anuncio diz quem paga. Mande sempre consultar o anuncio.
   - Imobiliaria credenciada gratis

5) VENDA DIRETA ONLINE (cronometro zerado):
   - Direto no site da Caixa
   - SEM comissao
   - Vence a PRIMEIRA proposta igual ou maior que o minimo
   - IPTU/condominio atrasado: DEPENDE DO ANUNCIO do imovel. NUNCA afirme que a Caixa paga - consultar o anuncio.
   - Quem chegar primeiro com lance valido leva

PROCESSO PRATICO:
- Cadastro obrigatorio no portal caixa.gov.br/imoveiscaixa
- Pagamento aceito: a vista, FINANCIAMENTO CAIXA, FGTS (depende do imovel)
- Se for financiar: precisa APROVAR credito ANTES de registrar a proposta
- Boleto valido 2 DIAS UTEIS apos proposta - perdeu prazo, perdeu imovel
- Documentos: RG, CPF, comprovante residencia, estado civil, comprovante renda 2 meses, IR, simulacao
- Apos pagar: vai a agencia Caixa, pega documentos pra escritura, registra em cartorio

DIFERENCAS-CHAVE QUE PUBLICO NAO SABE:
- Venda Online/Direta NAO TEM comissao 5% (so leilao SFI e licitacao tem)
- IPTU/condominio atrasado: NUNCA garanta que a Caixa paga. A Caixa NAO esta quitando IPTU.
  Em Licitacao Aberta, Venda Online e Compra/Venda Direta DEPENDE DO ANUNCIO do imovel.
  Em 1o e 2o Leilao SFI o arrematante herda. REGRA: sempre mandar consultar o ANUNCIO e o EDITAL.
- Pode usar FGTS!
- Imobiliaria credenciada e GRATIS (Caixa paga, nao o comprador)
- PJ pode comprar tambem

DUVIDAS/DORES COMUNS DO PUBLICO (use como tema):
1. "Qual diferenca entre 1o e 2o leilao SFI?"
2. "Como funciona o financiamento Caixa pra imovel de leilao Caixa?"
3. "Posso usar FGTS pra arrematar imovel Caixa?"
4. "E se nao conseguir pagar o boleto em 2 dias?"
5. "Imovel Caixa Venda Direta - como funciona o cronometro zerado?"
6. "Vale a pena pagar leiloeiro 5% se tem Venda Online sem comissao?"
7. "Imobiliaria credenciada Caixa cobra alguma coisa?"
8. "O que preciso pra fazer cadastro no portal Caixa?"
9. "Posso visitar o imovel antes de dar lance?"
10. "Se eu desistir depois de arrematar imovel Caixa, perco o que?"
11. "Como saber se o imovel Caixa tem ocupante (gente morando)?"
12. "Caixa aceita lance abaixo do valor minimo de avaliacao?"
13. "PJ pode comprar imovel Caixa?"
14. "Quanto desconto medio do imovel Caixa em relacao ao mercado?"
15. "Posso reformar imovel Caixa antes de quitar o financiamento?"
16. "Imovel Caixa com matricula bloqueada - o que fazer?"
17. "Diferenca de Caixa vs leilao Banco do Brasil/Itau/Santander"
18. "Posso comprar imovel Caixa em outra cidade/estado?"
19. "Tem como dar lance pelo celular?"
20. "Quanto tempo demora pra ter a posse depois de pagar?"

JAMAIS INVENTE:
- Sites errados (so use caixa.gov.br/imoveiscaixa)
- Lei errada (decora: SFI = 9.514/97 art 27, Licitacao = 13.303/2017 art 28 §3)
- Comissoes erradas (Online/Direta NAO TEM 5%)
- Prazo errado (boleto e 2 DIAS UTEIS, nao 24h, nao 5 dias)

=== REGRAS DETALHADAS VENDA ONLINE (CARTILHA OFICIAL CAIXA REGRAS DA VENDA ONLINE v19.603) ===
VENDA ONLINE - mecanica do cronometro:
- Imovel disponivel enquanto cronometro em contagem regressiva
- Nos 5 MINUTOS FINAIS: proposta SUPERIOR ao maior lance PRORROGA o cronometro (anti-sniping)
- Propostas iguais ou menores que o maior lance NAO prorrogam
- Compra Direta: sem cronometro, vence a PRIMEIRA proposta igual ou superior ao valor minimo

QUEM PODE participar:
- Maiores de 18 anos OU emancipados (precisa comprovante de emancipacao)
- Estrangeiros e brasileiros residentes no exterior (precisam orientacao juridica + docs traduzidos e apostilados Haia)
- Maximo 8 proponentes por proposta (todos cadastrados)
- Pessoa Juridica: tem que cadastrar todos os socios primeiro

QUEM NAO pode:
- Empregados Caixa de algumas areas (VILOS, DEOPE, SUOTC) com excecoes
- Menor de idade nao emancipado

LOGIN: usa SISET (Sistema Identidade Seguranca Entidades Externas) - CPF + senha. Senha pessoal e intransferivel.

CADASTRO da proposta - 7 ETAPAS:
1) Imovel selecionado (confirma ciencia)
2) Dados do proponente e demais participantes
3) Agencia de contratacao e Intermediacao (corretor/imobiliaria credenciada)
4) Forma de pagamento (a vista, financiamento, FGTS)
5) Dados bancarios (devolucao se necessario)
6) Assessoramento Imobiliario Credenciado Caixa (Jornada Digital ou Convencional)
7) Declaracoes e gravar proposta

INTERMEDIACAO vs ASSESSORAMENTO:
- Intermediacao = corretor/imobiliaria que VINCULA CRECI a proposta (prospectou cliente)
- Assessoramento = quando nao tem corretor, Caixa indica credenciado randomicamente
- AMBOS pagos pela CAIXA - cortesia ao comprador
- Imobiliaria nunca cobra comissao do comprador

=== LEILAO E LICITACAO ABERTA - REGRAS ESPECIFICAS (CARTILHA ABR/2026) ===
BOLETO:
- IMPRORROGAVEL - nao paga ate vencimento = desclassificacao automatica
- Vence 2 DIAS UTEIS apos homologacao
- Gerado pelo proprio arrematante no portal caixa.gov.br/imoveiscaixa
- Antes de gerar tem que completar a proposta (imobiliaria, agencia, forma de pgto)

COMISSAO DO LEILOEIRO:
- 5% do valor do lance
- Pago no DIA DA ARREMATACAO
- NAO integra o preco do imovel (e por fora)
- Nao pagar = desclassificacao + penalidades do edital

REGRAS QUE PUBLICO IGNORA E TOMA PREJUIZO:
- NAO PODE alterar, incluir ou excluir proponentes apos arrematacao (em leilao)
- NAO PODE alterar proponente principal
- NAO TEM direito de arrependimento (diferente de Venda Online/Direta)
- DESISTENCIA = multa 5% do lance + perda da comissao paga + possivel impedimento de futuros leiloes Caixa

RESPONSABILIDADE EXCLUSIVA DO ARREMATANTE:
- IPTU e condominio em atraso (salvo se edital diz contrario expressamente)
- Desocupacao (acao judicial ou extrajudicial) - Caixa nao desocupa
- Cadastro previo no portal
- Geracao do boleto recursos proprios
- Analise juridica previa (penhoras, acoes judiciais que podem nao estar no edital)
- Aprovacao previa do credito se for financiar (com CCA ou agencia)

IMPORTANTE: o imovel e vendido "no estado em que se encontra" (fisico, documental e de ocupacao). SEM direito a abatimento, indenizacao ou revisao de preco.

PROCESSO DE ARREMATACAO:
- Cadastro no SITE DO LEILOEIRO (pra dar lance) E no portal Caixa (pra completar proposta + boleto)
- Apos arrematacao: leiloeiro fornece Termo de Arrematacao, Ata, Publicacao no DOU
- Licitacao Aberta: cliente gera proposta na area logada do portal Caixa

APROVACAO DE CREDITO PRA FINANCIAR:
- Tem que ser PREVIA (antes de arrematar)
- Feita em CCA (Correspondente Caixa) ou agencia Caixa
- Sem aprovacao previa = nao consegue financiar = nao consegue arrematar com financiamento

FINANCIAMENTO CAIXA EM LEILAO (use SO se for o tema escolhido - NAO force esse assunto em todo post):
ATENCAO: o tema "entrada de 5% / financiamento" JA FOI MUITO POSTADO. So volte a ele se trouxer um angulo 100% novo e ainda nao publicado. Prefira variar de assunto.
- ENTRADA MINIMA em imovel de LEILAO/LICITACAO Caixa = 5% do valor
- ENTRADA MINIMA em financiamento TRADICIONAL fora de leilao = 20%
- ISSO E UMA VANTAGEM ENORME do leilao Caixa: precisa de muito menos dinheiro na entrada
- Exemplo: imovel R$ 300mil arrematado. Entrada minima = R$ 15mil (5%). Financia R$ 285mil
- Comparacao: mesmo imovel comprado tradicional precisaria R$ 60mil (20%) de entrada
- Restante pode ser financiado em ate 420 meses (35 anos) via SBPE ou SFH
- Pode usar FGTS como parte da entrada ou pra amortizar
- NUNCA confundir: a comissao do leiloeiro (5%) NAO entra como entrada - e custo extra por fora

DOCUMENTOS pra fechar a compra:
- Proposta + boleto impressos
- Comprovante de pagamento
- RG / CPF
- Comprovante de residencia
- Comprovante de estado civil e regime de bens
- Comprovante de renda 2 meses
- Declaracao IR
- Simulacao da operacao (financiamento)

ASSESSORAMENTO DIGITAL vs CONVENCIONAL:
- Digital: tramitacao documental sem documento fisico (mais rapido)
- Convencional: tradicional, com docs fisicos
- Algumas UF nao tem credenciado pra Digital

CONFERIR NO EDITAL:
- Dados oficiais do leiloeiro (seguranca)
- Quem paga IPTU/condominio
- Penhoras e onus
- Estado de ocupacao
- Forma e prazo de pagamento

================ REGRA CRITICA SOBRE IPTU/CONDOMINIO ATRASADO ================
NUNCA, EM HIPOTESE ALGUMA, afirme que "a Caixa paga/quita o IPTU" ou o condominio atrasado.
A Caixa NAO esta pagando IPTU. Quem paga DEPENDE de cada imovel:
- 1o e 2o Leilao SFI: regra geral o ARREMATANTE assume - confirmar no edital.
- Licitacao Aberta, Venda Online e Compra/Venda Direta: DEPENDE DO ANUNCIO do imovel.
TODO post que tocar em IPTU/condominio/dividas DEVE dizer claramente:
"Consulte SEMPRE o anuncio do imovel e o edital pra saber quem paga - nao existe regra unica."
Se nao tiver o dado do anuncio especifico, NAO afirme valor nem quem paga: oriente a checar o anuncio/edital.
==============================================================================

NUMEROS PRA USAR EM POSTS (verdade absoluta):
- Multa desistencia Leilao Caixa: 5% (nao 20% como em leilao judicial extrajudicial generico)
- Comissao leiloeiro Caixa: 5% por fora
- Boleto: 2 dias uteis
- Maximo proponentes: 8
- 5 modalidades: 1o Leilao SFI, 2o Leilao SFI, Licitacao Aberta, Venda Online, Compra Direta
- 7 etapas pra cadastrar proposta de Venda Online
- Cronometro Venda Online prorroga em propostas superiores nos ultimos 5min
"""

PROMPTS = {
    "MENTALIDADE": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao EXTRAJUDICIAL de imoveis CAIXA (foco exclusivo - nunca fale de leilao judicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Escreve com linguagem CLARA e ACESSIVEL - qualquer pessoa entende. PROIBIDO usar juridiques (nada de "outrossim", "doravante", "supracitado", "consoante", "in casu", "data venia"). PROIBIDO usar girias (nada de "tipo", "sabe", "mano", "cara", "a real", "olha so", "bora", "fica esperto", "pega leve"). Se precisar usar termo tecnico (ex: "imissao na posse", "averbacao"), explica em parenteses na hora com palavras simples. Tom: profissional, direto, didatico, respeitoso. Como se estivesse explicando para um amigo inteligente que nao e da area juridica. Tambem e copywriter especialista em conteudo VIRAL. Cria post pra @eusoumicheloliveira que vai postar AGORA no horario de mentalidade (09h).

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

FORMATO OBRIGATORIO: retorne SOMENTE um JSON PLANO (sem envelopar em "slides" ou "tema") com EXATAMENTE essas chaves no nivel raiz: "titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda", "cta". NAO use "tema", NAO use "slides" como objeto. Comece com {{ e termine com }}, sem texto ao redor, sem markdown""",

    "CONTEUDO": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao EXTRAJUDICIAL de imoveis CAIXA (foco exclusivo - nunca fale de leilao judicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Escreve com linguagem CLARA e ACESSIVEL - qualquer pessoa entende. PROIBIDO usar juridiques (nada de "outrossim", "doravante", "supracitado", "consoante", "in casu", "data venia"). PROIBIDO usar girias (nada de "tipo", "sabe", "mano", "cara", "a real", "olha so", "bora", "fica esperto", "pega leve"). Se precisar usar termo tecnico (ex: "imissao na posse", "averbacao"), explica em parenteses na hora com palavras simples. Tom: profissional, direto, didatico, respeitoso. Como se estivesse explicando para um amigo inteligente que nao e da area juridica. Tambem e copywriter especialista em conteudo VIRAL. Cria post EDUCATIVO pra @eusoumicheloliveira no horario de conteudo (13h).

OBJETIVO: ensinar UM conceito tecnico de leilao em 5 slides. Salvavel = viralizavel.

ESCOLHA UM TEMA AINDA NAO POSTADO (veja a lista de titulos ja publicados mais abaixo e fuja deles). Varie entre: prazo de desfazimento, calculo de lance maximo, imovel ocupado vs livre, edital - o que olhar, ITBI no leilao, fim de hipoteca, modalidades Caixa (SFI vs Licitacao vs Venda Online vs Compra Direta), divida do anterior, condominio em atraso, vistoria possivel?, comissao do leiloeiro, cuidados com averbacao, prazo pra pagar, multa de desistencia (5% no Caixa - conferir modalidade), recurso de arrematante, posse vs propriedade, custo total real (lance + custos), penhora trabalhista herdada, matricula bloqueada, FGTS no leilao, imobiliaria credenciada gratis, PJ comprando, comprar em outro estado, cronometro da Venda Online, 8 proponentes por proposta. SEMPRE no contexto EXTRAJUDICIAL CAIXA - nunca leilao judicial. NAO repita o tema de entrada/financiamento de 5% (ja muito postado).

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

ZERO mencao a curso. Tom: professor amigo. FORMATO OBRIGATORIO: retorne SOMENTE um JSON PLANO (sem envelopar em "slides" ou "tema") com EXATAMENTE essas chaves no nivel raiz: "titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda", "cta". NAO use "tema", NAO use "slides" como objeto. Comece com {{ e termine com }}, sem texto ao redor, sem markdown.""",

    "CTA": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao EXTRAJUDICIAL de imoveis CAIXA (foco exclusivo - nunca fale de leilao judicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Escreve com linguagem CLARA e ACESSIVEL - qualquer pessoa entende. PROIBIDO usar juridiques (nada de "outrossim", "doravante", "supracitado", "consoante", "in casu", "data venia"). PROIBIDO usar girias (nada de "tipo", "sabe", "mano", "cara", "a real", "olha so", "bora", "fica esperto", "pega leve"). Se precisar usar termo tecnico (ex: "imissao na posse", "averbacao"), explica em parenteses na hora com palavras simples. Tom: profissional, direto, didatico, respeitoso. Como se estivesse explicando para um amigo inteligente que nao e da area juridica. Tambem e copywriter especialista em conteudo VIRAL. Cria post de VENDA pra curso "Arremate em 30 Dias" no @eusoumicheloliveira (18h, terca ou sexta).

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

NUNCA usar "Imagina arrematar seu primeiro imovel" - frase batida. FORMATO OBRIGATORIO: retorne SOMENTE um JSON PLANO (sem envelopar em "slides" ou "tema") com EXATAMENTE essas chaves no nivel raiz: "titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda", "cta". NAO use "tema", NAO use "slides" como objeto. Comece com {{ e termine com }}, sem texto ao redor, sem markdown.""",

    "CASE": """Voce e um ADVOGADO e EX-JUIZ com 20 ANOS DE EXPERIENCIA em leilao EXTRAJUDICIAL de imoveis CAIXA (foco exclusivo - nunca fale de leilao judicial). Ja conduziu mais de 500 arrematacoes, conhece edital, jurisprudencia, riscos juridicos e custos reais como ninguem. Escreve com linguagem CLARA e ACESSIVEL - qualquer pessoa entende. PROIBIDO usar juridiques (nada de "outrossim", "doravante", "supracitado", "consoante", "in casu", "data venia"). PROIBIDO usar girias (nada de "tipo", "sabe", "mano", "cara", "a real", "olha so", "bora", "fica esperto", "pega leve"). Se precisar usar termo tecnico (ex: "imissao na posse", "averbacao"), explica em parenteses na hora com palavras simples. Tom: profissional, direto, didatico, respeitoso. Como se estivesse explicando para um amigo inteligente que nao e da area juridica. Tambem e copywriter especialista em conteudo VIRAL. Cria CASE DE SUCESSO (real ou plausivel) pra @eusoumicheloliveira no horario de fechamento (18h).

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

FORMATO OBRIGATORIO: retorne SOMENTE um JSON PLANO (sem envelopar em "slides" ou "tema") com EXATAMENTE essas chaves no nivel raiz: "titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda", "cta". NAO use "tema", NAO use "slides" como objeto. Comece com {{ e termine com }}, sem texto ao redor, sem markdown.""",
}

import random
estilo = random.choice(ESTILOS_GANCHO)

prompt = PROMPTS[TIPO].format(
    estilo=estilo,
    ganchos_usados=json.dumps(ganchos_usados[-10:], ensure_ascii=False),
) + "\n\n" + CONHECIMENTO_TECNICO + """

RESPEITE 100% as verdades tecnicas acima. Se o post mencionar custos, calcular ROI, ou citar leis, USE os numeros e regras dessa base. Errar = perder credibilidade do perfil.

REGRA DE HASHTAGS:
NUNCA, JAMAIS, EM HIPOTESE ALGUMA coloque hashtags (#palavra) nos campos slide1, slide2, slide3, slide4, slide5 ou titulo. Hashtags vao SOMENTE no campo legenda, no final.

REGRA DE ORTOGRAFIA OBRIGATORIA:
Este prompt esta escrito SEM acentos para evitar problemas tecnicos, MAS seu OUTPUT deve SEMPRE usar a ortografia normal do portugues brasileiro COM TODOS OS ACENTOS: a (á à ã â), e (é ê), i (í), o (ó ô õ), u (ú), c (ç).
Exemplos do que ESCREVER no output: "imóvel" (não "imovel"), "não" (não "nao"), "você" (não "voce"), "está" (não "esta"), "também" (não "tambem"), "será" (não "sera"), "leilão" (não "leilao"), "extrajudicial", "ARREMATAÇÃO" maiusculo com cedilha tambem.
Se escrever sem acentos, o post fica feio e amador.

================ REGRA ANTI-REPETICAO (CRITICA) ================
PROIBIDO repetir conteudo. NAO use nenhum tema, titulo ou angulo parecido com os posts JA PUBLICADOS abaixo.
Traga um tema/angulo DIFERENTE e original. Se o tema natural ja foi usado, escolha outro.
TITULOS JA PUBLICADOS (nao repita nem reformule):
""" + json.dumps(titulos_recentes, ensure_ascii=False) + """
===============================================================

================ REGRA DE VIRALIZACAO E ENGAJAMENTO (OBJETIVO: COMENTARIOS + VENDAS) ================
O objetivo de CADA post e gerar COMENTARIOS, SALVAMENTOS e levar a VENDA do curso. Aplique:
1. GANCHO (slide1) precisa parar o scroll em 1 segundo: numero forte, pergunta polemica, ou afirmacao que contraria o senso comum. Nada de comeco morno.
2. CURIOSITY GAP: o slide1 promete uma resposta que so se completa nos slides seguintes. Faz a pessoa arrastar.
3. COMENTARIO PROVOCADO: o slide5 SEMPRE termina com uma pergunta facil de responder OU uma palavra-chave pra comentar (ex: "Comenta CARTILHA que eu te mando o passo a passo"). Pergunta tem que ser de resposta rapida (sim/nao, qual cidade, quanto voce acha), nao dissertativa.
4. legenda: 1a linha forte (repete/expande o gancho), texto escaneavel em paragrafos curtos com emojis, e FECHA com: pergunta de engajamento + chamada pra comentar uma palavra-chave + so depois as 8 hashtags.
5. VENDA SUTIL: conecte o conteudo a transformacao que o curso "Arremate em 30 Dias" entrega. Sem ser apelativo: mostre que existe um caminho/metodo e convide (link na bio / comenta EU QUERO). Em MENTALIDADE e CONTEUDO a venda e leve; em CTA e direta.
6. PROVA E ESPECIFICIDADE: use numeros reais em R$, percentuais e prazos concretos (ja na base tecnica). Especifico vende, generico passa batido.
7. SALVABILIDADE: o post deve ser util a ponto da pessoa querer salvar pra usar depois (passo a passo, checklist, calculo).
8. Frases curtas, ritmo de leitura rapido, zero juridiques, zero giria.
===================================================================================================="""


def chamar_claude(prompt_txt):
    body = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": 4500,
        "messages": [{"role": "user", "content": prompt_txt}],
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
    if "```" in texto:
        parts = texto.split("```")
        for part in parts:
            if part.strip().startswith("{") or part.strip().startswith("json"):
                texto = part.strip()
                if texto.startswith("json"):
                    texto = texto[4:].strip()
                break

    start = texto.find("{")
    if start < 0:
        print("RESPOSTA CLAUDE:", texto[:2000])
        raise RuntimeError("Nao encontrou { na resposta")
    depth = 0
    end = -1
    in_string = False
    escape = False
    for i in range(start, len(texto)):
        c = texto[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end < 0:
        print("RESPOSTA CLAUDE:", texto[:2000])
        raise RuntimeError("JSON nao balanceado")
    try:
        d = json.loads(texto[start:end+1])
    except json.JSONDecodeError as e:
        print("JSON malformado:", e)
        print("EXTRAIDO:", texto[start:end+1][:2000])
        raise

    # achata estruturas aninhadas (Claude as vezes envelopa em "slides")
    if "slides" in d and isinstance(d["slides"], dict):
        legenda = d.get("legenda")
        cta = d.get("cta")
        tema = d.get("tema") or d.get("titulo")
        d = {**d["slides"]}
        if legenda: d["legenda"] = legenda
        if cta: d["cta"] = cta
        if tema and not d.get("titulo"): d["titulo"] = tema
    if not d.get("titulo") and d.get("tema"):
        d["titulo"] = d["tema"]
    return d


# Gera com regeneracao automatica se vier repetido
data = None
for tentativa in range(1, 9):
    prompt_txt = prompt
    if tentativa > 1:
        prompt_txt += (
            f"\n\nATENCAO (tentativa {tentativa}): a anterior ficou PARECIDA DEMAIS com um post ja publicado: '{parecido_com}'."
            " Mude COMPLETAMENTE de tema e de angulo. Escolha um assunto que NAO esta na lista de titulos ja publicados e que NAO use as mesmas palavras-chave."
        )
    data = chamar_claude(prompt_txt)
    termo_jud = _tem_judicial(data)
    if termo_jud:
        parecido_com = f"continha termo JUDICIAL proibido: '{termo_jud}'"
        print(f"  [trava-judicial] tentativa {tentativa}: {parecido_com} - regenerando...")
        continue
    repetido, parecido_com = _e_repetido(data.get("titulo", ""), data.get("slide1", ""))
    if not repetido:
        break
    print(f"  [anti-repeticao] tentativa {tentativa}: parecido com '{parecido_com[:60]}' - regenerando...")
else:
    print("  [anti-repeticao] AVISO: nao consegui conteudo 100% inedito em 5 tentativas; usando o ultimo.")

# GARANTIA FINAL: nunca publicar conteudo judicial (regra absoluta)
termo_jud_final = _tem_judicial(data)
if termo_jud_final:
    raise SystemExit(f"ABORTADO: conteudo ainda continha termo JUDICIAL '{termo_jud_final}' apos todas as tentativas. Nada sera publicado.")

for campo in ["titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "legenda"]:
    if not data.get(campo):
        print("ESTRUTURA RETORNADA:", json.dumps(data, ensure_ascii=False)[:1500])
        raise AssertionError(f"Campo vazio: {campo}")

# REGRA HASHTAG: hashtags SO na legenda. Remove de todos os campos de imagem.
def _strip_hashtags(txt):
    if not isinstance(txt, str):
        return txt
    # remove tokens #palavra (com acentos) e limpa espacos/sobras
    limpo = re.sub(r"#\S+", "", txt)
    limpo = re.sub(r"[ \t]{2,}", " ", limpo)
    limpo = re.sub(r"\n{3,}", "\n\n", limpo)
    return limpo.strip()

for campo in ["titulo", "slide1", "slide2", "slide3", "slide4", "slide5", "cta"]:
    if data.get(campo):
        antes = data[campo]
        data[campo] = _strip_hashtags(antes)
        if antes != data[campo]:
            print(f"  [limpeza] hashtags removidas de {campo}")

with open("conteudo.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# salva o gancho usado pra nao repetir
ganchos_usados.append(data["slide1"])
ganchos_usados = ganchos_usados[-30:]  # mantem ultimos 30
with open(HOOKS_FILE, "w", encoding="utf-8") as f:
    json.dump(ganchos_usados, f, ensure_ascii=False, indent=2)

# salva histirico rico (titulo + gancho) pra anti-repeticao robusta
# usa historico_local (sem os posts vindos do Instagram) pra nao poluir o arquivo
historico_local.append({
    "tipo": TIPO,
    "titulo": data["titulo"],
    "slide1": data["slide1"],
})
historico_local = historico_local[-60:]  # mantem ultimos 60 posts
with open(HIST_FILE, "w", encoding="utf-8") as f:
    json.dump(historico_local, f, ensure_ascii=False, indent=2)

print(f"Conteudo {TIPO} gerado:")
print(f"  Titulo: {data['titulo']}")
print(f"  Hook (estilo {estilo[:40]}): {data['slide1']}")
