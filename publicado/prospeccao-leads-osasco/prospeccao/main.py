"""CLI: busca empresas por categoria/cidade e exporta as que não têm site em CSV.

Uso:
    python -m prospeccao.main --cidade "Osasco, SP" --categorias "salão de beleza" "oficina mecânica"
"""

import argparse
import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from prospeccao.filtros import filtrar_sem_site, normalizar_lugar
from prospeccao.places_client import PlacesApiError, buscar_empresas

CATEGORIAS_PADRAO = [
    "salão de beleza",
    "oficina mecânica",
    "clínica odontológica",
    "restaurante",
    "loja de roupas",
    "barbearia",
    "pet shop",
    "academia",
    "contabilidade",
    "advocacia",
]


def montar_query(categoria: str, cidade: str) -> str:
    return f"{categoria} em {cidade}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Busca empresas no Google Places e lista as que não têm site cadastrado."
    )
    parser.add_argument("--cidade", default="Osasco, SP", help="Cidade/região de busca (padrão: Osasco, SP)")
    parser.add_argument(
        "--categorias",
        nargs="+",
        default=CATEGORIAS_PADRAO,
        help="Lista de categorias/segmentos a buscar (padrão: comércio local genérico)",
    )
    parser.add_argument(
        "--max-paginas",
        type=int,
        default=3,
        help="Máximo de páginas por categoria (até 20 resultados por página)",
    )
    parser.add_argument("--saida", default="leads_sem_site.csv", help="Arquivo CSV de saída")
    parser.add_argument(
        "--incluir-com-site",
        action="store_true",
        help="Inclui no CSV também as empresas que já têm site (por padrão só as sem site saem)",
    )
    args = parser.parse_args(argv)

    load_dotenv()
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print(
            "Erro: defina GOOGLE_PLACES_API_KEY no .env (veja .env.example) ou como variável de ambiente.",
            file=sys.stderr,
        )
        return 1

    todas_empresas = []
    vistos = set()

    for categoria in args.categorias:
        query = montar_query(categoria, args.cidade)
        print(f"Buscando: {query}")
        try:
            for lugar in buscar_empresas(query, api_key, max_paginas=args.max_paginas):
                empresa = normalizar_lugar(lugar)
                chave = (empresa.nome, empresa.endereco)
                if chave in vistos:
                    continue
                vistos.add(chave)
                todas_empresas.append(empresa)
        except PlacesApiError as exc:
            print(f"  Aviso: falha ao buscar '{query}': {exc}", file=sys.stderr)

    resultado = todas_empresas if args.incluir_com_site else filtrar_sem_site(todas_empresas)

    caminho_saida = Path(args.saida)
    with caminho_saida.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["nome", "endereco", "telefone", "rating", "avaliacoes", "tem_site", "site", "google_maps_url", "status"]
        )
        for e in resultado:
            writer.writerow(
                [
                    e.nome,
                    e.endereco,
                    e.telefone or "",
                    e.rating or "",
                    e.avaliacoes or "",
                    "sim" if e.tem_site else "não",
                    e.site or "",
                    e.google_maps_url or "",
                    e.status or "",
                ]
            )

    print(f"\n{len(resultado)} empresas gravadas em {caminho_saida.resolve()}")
    if not args.incluir_com_site:
        print(f"(de {len(todas_empresas)} empresas encontradas no total, {len(resultado)} sem site cadastrado)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
