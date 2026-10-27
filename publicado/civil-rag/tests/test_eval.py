from eval.run_eval import BM25, avaliar, carregar_corpus, carregar_golden, trecho_correto


def test_toda_pergunta_tem_evidencia_no_corpus():
    trechos = carregar_corpus()
    for item in carregar_golden():
        assert any(trecho_correto(t, item) for t in trechos), item["id"]


def test_ids_unicos():
    ids = [i["id"] for i in carregar_golden()]
    assert len(ids) == len(set(ids))


class RecuperadorFixo:
    def __init__(self, ranking):
        self._ranking = ranking

    def ranking(self, pergunta):
        return self._ranking


def test_metricas_com_posicao_conhecida():
    trechos = [
        {"arquivo": "a.txt", "texto": "outra coisa"},
        {"arquivo": "a.txt", "texto": "concreto fck = 40 MPa"},
    ]
    golden = [{"id": "x", "pergunta": "?", "arquivo": "a.txt", "evidencia": "fck = 40 MPa"}]
    r = avaliar("fixo", RecuperadorFixo([0, 1]), trechos, golden)
    assert r["por_pergunta"][0]["posicao"] == 2
    assert r["metricas"]["hit@1"] == 0
    assert r["metricas"]["hit@3"] == 1
    assert r["metricas"]["MRR@5"] == 0.5


def test_arquivo_errado_nao_conta_como_acerto():
    trecho = {"arquivo": "b.txt", "texto": "fck = 40 MPa"}
    item = {"arquivo": "a.txt", "evidencia": "fck = 40 MPa"}
    assert not trecho_correto(trecho, item)


def test_bm25_acha_pergunta_literal_em_primeiro():
    trechos = carregar_corpus()
    alvo = next(t for t in trechos if "manta asfáltica" in t["texto"])
    primeiro = BM25(trechos).ranking("manta asfáltica de 4 mm na cobertura")[0]
    assert trechos[primeiro] is alvo
