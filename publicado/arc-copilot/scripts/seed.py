from app.database.session import Base, SessionLocal, engine, ensure_pgvector
from app.seed import DEMO_PASSWORD, seed_demo


def main():
    ensure_pgvector(engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        result = seed_demo(db)
        action = "criados" if result["created"] else "já existentes"
        print(f"Dados de demonstração {action}.")
        print("Engenheiro: engenheiro@arc.local")
        print("Mestre: mestre@arc.local")
        print("Trabalhador: trabalhador@arc.local")
        print(f"Senha local: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
