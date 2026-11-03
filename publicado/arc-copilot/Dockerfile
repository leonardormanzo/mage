FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY . .
ENV PORT=8000
EXPOSE 8000
# Plataformas como Render e Fly definem PORT; localmente vale 8000.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
