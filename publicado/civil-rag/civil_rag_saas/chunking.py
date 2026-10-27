"""Divisão de texto em trechos (chunks) com sobreposição.

Fica separada de rag_engine.py para poder ser testada e usada pela avaliação
sem exigir chave de API nem banco de dados.
"""


def fatiar_texto(texto: str, tamanho_chunk: int = 600, overlap: int = 100) -> list[str]:
    """Divide o texto em trechos de até `tamanho_chunk` caracteres.

    Trechos consecutivos compartilham `overlap` caracteres, para que uma frase
    cortada no fim de um trecho apareça inteira no seguinte.
    """
    if tamanho_chunk <= 0:
        raise ValueError("tamanho_chunk deve ser positivo")
    if not 0 <= overlap < tamanho_chunk:
        raise ValueError("overlap deve estar entre 0 e tamanho_chunk - 1")

    chunks = []
    inicio = 0
    passo = tamanho_chunk - overlap
    while inicio < len(texto):
        chunk = texto[inicio:inicio + tamanho_chunk].strip()
        if chunk:
            chunks.append(chunk)
        inicio += passo
    return chunks
