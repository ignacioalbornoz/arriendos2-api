FROM python:3.11-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV TZ=America/Santiago

WORKDIR /app

# Instalar curl
RUN apt-get update && apt-get install -y curl

# Instalar dependencias necesarias para compilar psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY ./app /app

# Install dependencies
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Asegurar que alembic esté instalado
RUN pip install alembic

# Verificar que alembic está instalado correctamente
RUN alembic --version

# Instalar Node.js para Pyright
# RUN apt-get update && \
#     apt-get install -y curl && \
#     curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
#     apt-get install -y nodejs && \
#     npm install -g pyright

# Ejecutar Pyright para análisis estático de tipos
# RUN pyright /app

EXPOSE 8080

# chmod the entrypoint script
RUN chmod +x /app/entrypoint.sh

CMD ["/bin/bash", "/app/entrypoint.sh"]


