FROM python:3.13-slim

WORKDIR /app

# Agrega las herramientas necesarias para compilar extensiones nativas como chroma-hnswlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpython3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Asegura que todos los archivos sean legibles
RUN chmod -R a+r /app

# Instala las dependencias desde el requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]
