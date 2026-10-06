# Prospecção de Leads sem Site (Osasco)

CLI Python que busca empresas locais na Google Places API e exporta em CSV as que
não têm site cadastrado no Google — para prospecção comercial (ex: vender criação
de sites).

## Como funciona

Para cada categoria informada (ex: "salão de beleza"), o script monta a busca
`"<categoria> em <cidade>"`, consulta a Text Search da Google Places API (New) e
classifica cada resultado como "tem site" ou "sem site" com base no campo
`websiteUri` retornado pela API. Depois grava tudo (ou só as sem site, por
padrão) em um CSV com nome, endereço, telefone, avaliação e link do Google Maps.

## Pré-requisitos

- Python 3.10+
- Uma chave de API do Google Cloud com a **Places API (New)** habilitada e
  faturamento ativo no projeto (a API é paga — veja "Custos" abaixo). Crie em
  [console.cloud.google.com](https://console.cloud.google.com/) → APIs e
  Serviços → Credenciais.

## Executar

```bash
cd publicado/prospeccao-leads-osasco
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # depois edite e cole sua chave em GOOGLE_PLACES_API_KEY
python -m prospeccao.main
```

Isso busca a lista padrão de categorias genéricas de comércio local em
"Osasco, SP" e grava `leads_sem_site.csv` na pasta atual.

### Opções

```bash
python -m prospeccao.main --cidade "Osasco, SP" ^
  --categorias "salão de beleza" "oficina mecânica" "clínica odontológica" ^
  --max-paginas 3 ^
  --saida leads_osasco.csv
```

- `--categorias`: lista de segmentos a buscar (cada um vira uma busca separada).
- `--max-paginas`: até 20 resultados por página; controla quanto cada categoria
  aprofunda (e quanto custa).
- `--incluir-com-site`: grava todas as empresas encontradas, não só as sem site
  (útil para conferir a base completa).

## Testes

```bash
python -m unittest discover tests
```

Os testes cobrem só a normalização/filtro (lógica pura); não fazem chamada real
à API.

## Custos

A Places API (New) é paga por requisição — cada categoria buscada com
`--max-paginas 3` gera até 3 chamadas de Text Search. Confira o preço vigente em
[cloud.google.com/maps-platform/pricing](https://cloud.google.com/maps-platform/pricing)
antes de rodar em volume, e configure limite de orçamento no Google Cloud para
evitar surpresa na fatura.

## Falta para terminar / limites do MVP

- "Sem site" significa apenas que a ficha do Google não tem `websiteUri`
  preenchido — não confirma que a empresa realmente não tem site (pode não ter
  atualizado a ficha, ou usar só Instagram/WhatsApp como "site").
- Sem deduplicação robusta entre categorias que se sobrepõem (usa nome+endereço
  como chave, pode deixar passar grafias diferentes do mesmo endereço).
- Sem retry/backoff em erro de rede ou limite de taxa da API — falha na
  categoria é só avisada no console e o script segue para a próxima.
- Sem persistência entre execuções (cada rodada gera um CSV novo, não sabe quais
  leads já foram contatados).
- Lista de categorias padrão é genérica; ajuste via `--categorias` para o nicho
  que você quer prospectar.
- Sem interface gráfica — é uma ferramenta de linha de comando.
