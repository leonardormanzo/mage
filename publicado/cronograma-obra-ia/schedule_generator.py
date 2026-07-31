"""
Módulo responsável por conversar com a API da Anthropic (Claude) e
transformar um escopo de obra em texto livre em um cronograma estruturado.

Este arquivo cuida de:
- Montar o prompt que instrui o Claude a responder SOMENTE em JSON
- Chamar a API
- Tratar erros de rede/API
- Extrair e validar o JSON da resposta (mesmo se vier com texto extra)
"""

import json
import re
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError


# Nome do modelo usado nas chamadas. Pode ser trocado por outro modelo
# disponível na sua conta (ex: "claude-opus-4-8" para respostas mais
# elaboradas, ou "claude-haiku-4-5-20251001" para respostas mais rápidas
# e baratas — bom para testar durante o desenvolvimento).
MODEL_NAME = "claude-sonnet-5"


# Este é o "manual de instruções" que damos ao Claude antes de cada pedido.
# Colocamos aqui o conhecimento de obra (ordem das etapas, bom senso de
# duração) para o modelo não "inventar" uma sequência construtiva errada.
SYSTEM_PROMPT = """Você é um engenheiro civil sênior especialista em planejamento de obras.

Sua tarefa é transformar a descrição de uma obra em um cronograma físico-financeiro.

REGRAS DE SEQUÊNCIA CONSTRUTIVA (respeite sempre esta ordem lógica):
1. Mobilização / canteiro de obras
2. Demolição (se houver reforma)
3. Fundação / estrutura (se houver obra nova ou reforço estrutural)
4. Instalações embutidas (elétrica, hidráulica, ar-condicionado - "fase suja")
5. Alvenaria / vedação / drywall
6. Revestimentos (piso, parede, forro)
7. Instalações de acabamento (louças, metais, tomadas, luminárias)
8. Pintura
9. Limpeza final e entrega

REGRAS DE BOM SENSO PARA DURAÇÃO (ajuste proporcionalmente à metragem e à
complexidade descrita, mas use estes valores como referência de mercado):
- Demolição: aproximadamente 3 a 5 dias a cada 100m²
- Instalações (elétrica + hidráulica): 15 a 25% do prazo total da obra
- Revestimentos e acabamento: costuma ser a fase mais longa, 30 a 40% do prazo
- Pintura: geralmente as últimas 2 a 3 semanas, pode rodar em paralelo com acabamentos finais
- Limpeza final: 2 a 5 dias

REGRAS DE ORÇAMENTO:
- Distribua o percentual do orçamento total entre as etapas de forma realista
  (ex: instalações e estrutura costumam consumir mais orçamento por m² do que
  pintura e limpeza).
- A soma de "percentual_orcamento" de todas as etapas DEVE fechar em 100.

FORMATO DE SAÍDA (MUITO IMPORTANTE):
Responda SOMENTE com um JSON válido, sem nenhum texto antes ou depois, sem
usar blocos de markdown (```). O JSON deve seguir exatamente este formato:

{
  "obra": "resumo curto do escopo recebido",
  "duracao_total_dias": <número inteiro>,
  "etapas": [
    {
      "nome": "Nome da etapa",
      "duracao_dias": <número inteiro>,
      "dependencias": ["Nome de outra etapa que precisa terminar antes", ...],
      "percentual_orcamento": <número, pode ter casas decimais>
    }
  ]
}

Se uma etapa não depende de nenhuma outra, use uma lista vazia: "dependencias": [].
Os nomes em "dependencias" devem ser IDÊNTICOS aos nomes usados em "nome" de outra etapa.
"""


def gerar_cronograma(api_key: str, escopo_obra: str) -> dict:
    """
    Envia o escopo da obra para o Claude e retorna o cronograma já
    convertido em dicionário Python (a partir do JSON de resposta).

    Parâmetros:
        api_key: chave da API da Anthropic, fornecida pelo usuário.
        escopo_obra: texto livre descrevendo a obra (ex: "reforma comercial
                     de 300m², 4 meses...").

    Retorna:
        Um dicionário Python com as chaves "obra", "duracao_total_dias" e
        "etapas" (lista de dicionários).

    Lança:
        RuntimeError com uma mensagem amigável caso algo dê errado (API
        fora do ar, chave inválida, JSON malformado, etc). Preferimos
        lançar um erro "traduzido" para que a interface (app.py) possa
        simplesmente mostrar essa mensagem ao usuário sem se preocupar
        com os detalhes técnicos de cada tipo de exceção.
    """

    if not api_key or not api_key.strip():
        raise RuntimeError(
            "Chave da API não informada. Cole sua chave da Anthropic no campo lateral."
        )

    if not escopo_obra or not escopo_obra.strip():
        raise RuntimeError("Descreva o escopo da obra antes de gerar o cronograma.")

    cliente = Anthropic(api_key=api_key)

    try:
        resposta = cliente.messages.create(
            model=MODEL_NAME,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Escopo da obra: {escopo_obra}",
                }
            ],
        )
    except RateLimitError:
        raise RuntimeError(
            "Limite de requisições da API atingido. Aguarde um pouco e tente novamente."
        )
    except APIConnectionError:
        raise RuntimeError(
            "Não foi possível conectar à API da Anthropic. Verifique sua internet."
        )
    except APIError as erro:
        raise RuntimeError(f"A API da Anthropic retornou um erro: {erro}")
    except Exception as erro:  # qualquer outro erro inesperado
        raise RuntimeError(f"Erro inesperado ao chamar a API: {erro}")

    # A resposta da API vem como uma lista de "blocos" de conteúdo.
    # Para uma resposta em texto simples, pegamos o texto do primeiro bloco.
    texto_resposta = resposta.content[0].text

    return _extrair_json(texto_resposta)


def _extrair_json(texto: str) -> dict:
    """
    Tenta converter o texto retornado pelo Claude em um dicionário Python.

    Mesmo pedindo "responda SOMENTE em JSON", às vezes o modelo pode
    devolver o JSON dentro de um bloco ```json ... ``` ou com espaços/
    textos extras. Esta função tenta ser tolerante a isso antes de desistir.
    """

    texto = texto.strip()

    # Tentativa 1: o texto já é um JSON puro
    try:
        return _validar_estrutura(json.loads(texto))
    except json.JSONDecodeError:
        pass

    # Tentativa 2: procurar um bloco ```json ... ``` ou ``` ... ```
    bloco = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if bloco:
        try:
            return _validar_estrutura(json.loads(bloco.group(1)))
        except json.JSONDecodeError:
            pass

    # Tentativa 3: pegar o primeiro "{" até o último "}" da resposta
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        try:
            return _validar_estrutura(json.loads(texto[inicio : fim + 1]))
        except json.JSONDecodeError:
            pass

    # Se nada funcionou, avisamos o usuário de forma clara em vez de
    # deixar o erro técnico do json.JSONDecodeError vazar para a tela.
    raise RuntimeError(
        "A resposta da IA não veio em um formato JSON válido. "
        "Tente gerar o cronograma novamente ou reformular o escopo."
    )


def _validar_estrutura(dados: dict) -> dict:
    """
    Confere se o dicionário tem as chaves mínimas esperadas antes de
    devolvê-lo para o resto da aplicação. Isso evita que um JSON
    "tecnicamente válido", mas incompleto, quebre a tela do Streamlit
    mais adiante com um erro confuso de "KeyError".
    """

    if "etapas" not in dados or not isinstance(dados["etapas"], list):
        raise RuntimeError("O JSON retornado não contém a lista 'etapas'.")

    if len(dados["etapas"]) == 0:
        raise RuntimeError("A IA não retornou nenhuma etapa para este escopo.")

    campos_obrigatorios = {"nome", "duracao_dias", "dependencias", "percentual_orcamento"}
    for i, etapa in enumerate(dados["etapas"]):
        faltando = campos_obrigatorios - set(etapa.keys())
        if faltando:
            raise RuntimeError(
                f"A etapa {i + 1} do JSON está incompleta (faltam os campos: {faltando})."
            )

    return dados
