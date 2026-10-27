"""Cria ou revoga links secretos de campo.

  python -m scripts.create_field_link --list
  python -m scripts.create_field_link --project-code CODIGO --label "Equipe Osasco"
  python -m scripts.create_field_link --revoke LINK_ID

O token completo só é exibido na criação (no banco fica apenas o hash).
"""

from __future__ import annotations

import argparse
import secrets

from sqlalchemy import select

from app.core.security import hash_password
from app.database.models import FieldLink, Project, ProjectUser, User
from app.database.session import Base, SessionLocal, engine
from app.field import hash_token


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-code")
    parser.add_argument("--label", default="Campo")
    parser.add_argument("--revoke")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if args.list:
            for link in db.scalars(select(FieldLink)):
                project = db.get(Project, link.project_id)
                state = "ativo" if link.active else "REVOGADO"
                print(f"{link.id}  {state:8}  {project.code}  {link.label}")
            return
        if args.revoke:
            link = db.get(FieldLink, args.revoke)
            if not link:
                raise SystemExit("Link não encontrado")
            link.active = False
            db.commit()
            print("Link revogado.")
            return
        if not args.project_code:
            raise SystemExit("Informe --project-code (ou --list / --revoke)")
        projects = db.scalars(select(Project).where(Project.code == args.project_code)).all()
        if len(projects) != 1:
            raise SystemExit(f"Esperava 1 obra com código {args.project_code}, achei {len(projects)}")
        project = projects[0]
        link = FieldLink(
            company_id=project.company_id,
            project_id=project.id,
            user_id="pending",
            token_hash="pending",
            label=args.label[:80],
        )
        db.add(link)
        db.flush()
        user = User(
            company_id=project.company_id,
            name=f"Campo · {args.label}"[:120],
            email=f"campo-{link.id}@link.invalid",
            password_hash=hash_password(secrets.token_urlsafe(32)),
            role="worker",
        )
        db.add(user)
        db.flush()
        db.add(ProjectUser(company_id=project.company_id, project_id=project.id, user_id=user.id))
        token = secrets.token_urlsafe(32)
        link.user_id = user.id
        link.token_hash = hash_token(token)
        db.commit()
        print(f"Link criado (id {link.id}) para {project.name}:")
        print(f"{args.base_url.rstrip('/')}/e/{token}")
        print("Guarde agora: o token não pode ser recuperado depois.")


if __name__ == "__main__":
    main()
