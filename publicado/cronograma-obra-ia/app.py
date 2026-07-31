"""
Interface Streamlit do Gerador de Cronograma Físico-Financeiro.

Como rodar:
    1. pip install -r requirements.txt
    2. streamlit run app.py

Você vai precisar de uma chave de API da Anthropic
(https://console.anthropic.com/settings/keys).
"""

import json
from datetime import date

import streamlit as st

from schedule_generator import gerar_cronograma
from cronograma_utils import calcular_datas, montar_grafico_gantt


st.set_page_config(page_title="Cronograma Físico-Financeiro IA", page_icon="🏗️", layout="wide")

st.title("🏗️ Gerador de Cronograma Físico-Financeiro")
st.caption(
    "Descreva o escopo da obra em texto livre e a IA monta um cronograma "
    "com etapas, prazos, dependências e distribuição de orçamento."
)

# --- Barra lateral: configuração da API -------------------------------
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input(
        "Chave da API Anthropic",
        type="password",
        help="Sua chave não é salva em disco, fica só nesta sessão do navegador.",
    )
    data_inicio_obra = st.date_input("Data de início da obra", value=date.today())
    orcamento_total = st.number_input(
        r"Orçamento total da obra (R\$) — opcional, só para exibir valores em R\$",
        min_value=0.0,
        value=0.0,
        step=1000.0,
        format="%.2f",
    )
    st.markdown("---")
    st.caption(
        "Não tem uma chave? Crie uma em "
        "[console.anthropic.com](https://console.anthropic.com/settings/keys)."
    )

# --- Entrada principal: escopo da obra ---------------------------------
escopo_obra = st.text_area(
    "Escopo da obra",
    placeholder="Ex: reforma comercial de 300m², prazo de 4 meses, com demolição, "
    "elétrica, hidráulica e acabamento",
    height=120,
)

gerar = st.button("Gerar cronograma", type="primary")

# Guardamos o resultado no "session_state" do Streamlit para que ele não
# desapareça da tela quando o usuário interagir com outros componentes
# (como o seletor de data) depois de já ter gerado o cronograma.
if "cronograma" not in st.session_state:
    st.session_state.cronograma = None

if gerar:
    with st.spinner("Consultando a IA e montando o cronograma..."):
        try:
            st.session_state.cronograma = gerar_cronograma(api_key, escopo_obra)
        except RuntimeError as erro:
            st.session_state.cronograma = None
            st.error(str(erro))

# --- Exibição do resultado ----------------------------------------------
cronograma = st.session_state.cronograma

if cronograma:
    st.success(f"Cronograma gerado: {cronograma.get('obra', escopo_obra)}")

    col1, col2 = st.columns(2)
    col1.metric("Duração total estimada", f"{cronograma.get('duracao_total_dias', '—')} dias")
    soma_percentual = sum(e.get("percentual_orcamento", 0) for e in cronograma["etapas"])
    col2.metric("Soma dos % de orçamento", f"{soma_percentual:.1f}%")

    try:
        df = calcular_datas(cronograma["etapas"], data_inicio_obra)
    except RuntimeError as erro:
        st.error(str(erro))
        st.stop()

    # Se o usuário informou um orçamento total, calculamos o valor em R$
    # de cada etapa para deixar a tabela mais completa.
    if orcamento_total > 0:
        df["Valor (R$)"] = (df["% Orçamento"] / 100 * orcamento_total).round(2)

    st.subheader("Cronograma visual (Gantt)")
    st.plotly_chart(montar_grafico_gantt(df), use_container_width=True)

    st.subheader("Tabela de etapas")
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("Ver JSON bruto retornado pela IA"):
        st.code(json.dumps(cronograma, indent=2, ensure_ascii=False), language="json")

    st.download_button(
        "Baixar cronograma em JSON",
        data=json.dumps(cronograma, indent=2, ensure_ascii=False),
        file_name="cronograma_obra.json",
        mime="application/json",
    )
else:
    st.info("Preencha o escopo da obra e clique em 'Gerar cronograma' para começar.")
