import pytest

from civil_rag_saas.chunking import fatiar_texto


def test_texto_curto_vira_um_trecho():
    assert fatiar_texto("fck = 40 MPa") == ["fck = 40 MPa"]


def test_trechos_consecutivos_compartilham_sobreposicao():
    texto = "".join(str(i % 10) for i in range(1500))
    trechos = fatiar_texto(texto, tamanho_chunk=600, overlap=100)
    assert all(len(t) <= 600 for t in trechos)
    for anterior, atual in zip(trechos, trechos[1:]):
        assert anterior[-100:] == atual[:100]


def test_nenhum_caractere_se_perde():
    texto = "".join(chr(65 + i % 26) for i in range(2345))
    trechos = fatiar_texto(texto, tamanho_chunk=500, overlap=50)
    remontado = trechos[0] + "".join(t[50:] for t in trechos[1:])
    assert remontado.startswith(texto)


def test_texto_vazio_nao_gera_trechos():
    assert fatiar_texto("   ") == []


@pytest.mark.parametrize("tamanho, overlap", [(0, 0), (100, 100), (100, -1)])
def test_parametros_invalidos(tamanho, overlap):
    with pytest.raises(ValueError):
        fatiar_texto("abc", tamanho_chunk=tamanho, overlap=overlap)
