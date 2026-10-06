"""
Funções auxiliares para transformar a lista de etapas (com duração e
dependências) em datas de início/fim, e para desenhar isso como um
gráfico de Gantt usando Plotly.
"""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px


def calcular_datas(etapas: list, data_inicio_obra: date) -> pd.DataFrame:
    """
    Recebe a lista de etapas (cada uma com "nome", "duracao_dias" e
    "dependencias") e calcula a data de início e fim de cada etapa.

    A regra usada é simples e propositalmente didática (não é um
    algoritmo de caminho crítico completo, mas já resolve bem o caso de
    uso de um cronograma de obra):

    - Uma etapa sem dependências começa na data de início da obra.
    - Uma etapa com dependências começa no dia seguinte ao término da
      dependência que terminar mais tarde (assumindo que todas as suas
      dependências precisam estar prontas antes de ela começar).
    """

    # Guardamos a data de fim de cada etapa já calculada, para servir de
    # referência para as etapas seguintes que dependem dela.
    fim_por_etapa = {}
    linhas = []

    # Como uma etapa pode depender de outra que ainda não processamos,
    # fazemos várias passadas até que todas as datas sejam calculadas.
    # Para um cronograma de obra (normalmente algumas dezenas de etapas),
    # isso é rápido o suficiente sem precisar de um algoritmo mais
    # sofisticado de ordenação topológica.
    pendentes = list(etapas)
    tentativas_maximas = len(etapas) * len(etapas) + 5  # margem de segurança
    tentativas = 0

    while pendentes and tentativas < tentativas_maximas:
        tentativas += 1
        etapa = pendentes.pop(0)
        deps = etapa.get("dependencias", [])

        # Se alguma dependência ainda não foi calculada, devolvemos essa
        # etapa para o final da fila e tentamos de novo depois.
        if any(dep not in fim_por_etapa for dep in deps):
            pendentes.append(etapa)
            continue

        if deps:
            inicio = max(fim_por_etapa[dep] for dep in deps) + timedelta(days=1)
        else:
            inicio = data_inicio_obra

        duracao = max(int(etapa.get("duracao_dias", 1)), 1)
        fim = inicio + timedelta(days=duracao - 1)

        fim_por_etapa[etapa["nome"]] = fim
        linhas.append(
            {
                "Etapa": etapa["nome"],
                "Início": pd.Timestamp(inicio),
                # +1 dia no fim só para o Plotly desenhar a barra até o
                # fim do último dia (senão a barra "some" no mesmo dia).
                "Fim": pd.Timestamp(fim) + pd.Timedelta(days=1),
                "Duração (dias)": duracao,
                "% Orçamento": etapa.get("percentual_orcamento", 0),
                "Dependências": ", ".join(deps) if deps else "—",
            }
        )

    if pendentes:
        # Isso só aconteceria se houvesse uma dependência "circular" ou
        # um nome de dependência que não bate com nenhuma etapa — um
        # sinal de que a IA retornou algo inconsistente.
        nomes_com_problema = ", ".join(e["nome"] for e in pendentes)
        raise RuntimeError(
            "Não foi possível calcular as datas de algumas etapas "
            f"(possível dependência inválida ou circular): {nomes_com_problema}"
        )

    return pd.DataFrame(linhas)


def montar_grafico_gantt(df: pd.DataFrame):
    """
    Recebe o DataFrame já com Início/Fim calculados e devolve uma figura
    Plotly do tipo Gantt (implementado com px.timeline, o jeito mais
    simples de fazer um Gantt em Python).
    """

    figura = px.timeline(
        df,
        x_start="Início",
        x_end="Fim",
        y="Etapa",
        color="% Orçamento",
        color_continuous_scale="Blues",
        hover_data={"Duração (dias)": True, "Dependências": True, "% Orçamento": ":.1f"},
        title="Cronograma Físico-Financeiro",
    )

    # Por padrão, o Plotly ordena as barras de baixo para cima; para um
    # cronograma de obra é mais natural ler de cima para baixo, na ordem
    # em que as etapas acontecem — então invertemos o eixo Y.
    figura.update_yaxes(autorange="reversed")
    figura.update_layout(
        xaxis_title="Data",
        yaxis_title="Etapa construtiva",
        height=120 + 40 * len(df),
    )

    return figura
