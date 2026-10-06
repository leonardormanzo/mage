# 🏗️ Gerador de Cronograma Físico-Financeiro (IA)

Protótipo que transforma o escopo de uma obra, descrito em texto livre, em
um cronograma físico-financeiro estruturado (etapas, prazos, dependências
e % de orçamento), usando a API da Anthropic (Claude) e exibindo o
resultado como um gráfico de Gantt no Streamlit.

## Estrutura do projeto

```
.
├── app.py                  # Interface Streamlit (o que o usuário vê)
├── schedule_generator.py   # Chamada à API da Anthropic + parsing do JSON
├── cronograma_utils.py     # Cálculo de datas + montagem do gráfico Gantt
├── requirements.txt        # Dependências Python
└── README.md
```

## Como rodar localmente

1. Crie um ambiente virtual (opcional, mas recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate   # no Windows: venv\Scripts\activate
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Rode a aplicação:

   ```bash
   streamlit run app.py
   ```

4. O navegador vai abrir automaticamente em `http://localhost:8501`.

## Chave de API

Você precisa de uma chave de API da Anthropic. Crie uma em
[console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
e cole no campo "Chave da API Anthropic" na barra lateral da aplicação.
A chave não é salva em nenhum arquivo — fica só na sessão do navegador
enquanto o app está rodando.

## Como usar

1. Cole sua chave de API na barra lateral.
2. (Opcional) Ajuste a data de início da obra e o orçamento total em R$.
3. Descreva o escopo da obra em texto livre, por exemplo:
   > "Reforma comercial de 300m², prazo de 4 meses, com demolição,
   > elétrica, hidráulica e acabamento"
4. Clique em "Gerar cronograma".
5. Veja o Gantt, a tabela de etapas e baixe o JSON se quiser reaproveitar
   os dados em outra ferramenta (Excel, Project, Power BI etc.).

## Como funciona por baixo dos panos

1. `schedule_generator.py` monta um prompt de sistema com regras de bom
   senso de obra (ordem construtiva, faixas de duração típicas, como
   distribuir o orçamento) e pede ao Claude para responder **somente**
   em JSON.
2. A resposta é validada e, se vier com texto extra ou dentro de um
   bloco de markdown, o código tenta extrair o JSON mesmo assim antes
   de desistir e mostrar um erro amigável.
3. `cronograma_utils.py` pega a lista de etapas (com suas dependências)
   e calcula a data de início/fim de cada uma, respeitando a ordem
   lógica de dependências — depois monta um gráfico de Gantt com Plotly.
4. `app.py` só orquestra essas duas peças dentro da interface Streamlit.
