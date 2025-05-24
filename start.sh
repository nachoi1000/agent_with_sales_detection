#!/bin/bash
set -e

# Convertir .env de formato Windows (CRLF) a Unix (LF) automáticamente
if [ -f .env ]; then
  # Usar sed para eliminar retornos de carro \r (caracter ^M)
  sed -i 's/\r$//' .env
else
  echo ">> Archivo .env no encontrado"
  exit 1
fi

# Cargar variables de entorno desde .env
set -a  # exportar automáticamente
source .env
set +a

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo ">> Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo ">> Installing dependencies..."
    pip install -r requirements.txt
else
    echo ">> Virtual environment already exists. Skipping requirements installation."
    source venv/bin/activate
fi

# Asegurar carpeta mongo_database con permisos correctos
if [ ! -d "mongo_database" ]; then
    echo ">> Creating mongo_database directory..."
    mkdir -p mongo_database
fi


CONTAINER_NAME="mongodb"
IMAGE_NAME="mongo:latest"
LOCAL_VOLUME="$(pwd)/mongo_database:/data/db"
DOCKER_VOLUME="mongodb_database:/data/db"

# Función para verificar si el contenedor está fallando
is_container_failed() {
    STATUS=$(docker inspect -f '{{.State.Status}}' $1 2>/dev/null)
    [[ "$STATUS" == "exited" || "$STATUS" == "dead" || "$STATUS" == "created" ]]
}

# Si el contenedor no existe
if [ ! "$(docker ps -a -q -f name=^${CONTAINER_NAME}$)" ]; then
    echo ">> MongoDB container not found. Creating with local volume..."
    docker run --name $CONTAINER_NAME -d -p 27017:27017 -v "$LOCAL_VOLUME" $IMAGE_NAME
    sleep 2  # Esperamos un poco para que se inicie
    if is_container_failed $CONTAINER_NAME; then
        echo ">> Container failed after creation. Recreating with Docker volume..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        docker run --name $CONTAINER_NAME -d -p 27017:27017 -v $DOCKER_VOLUME $IMAGE_NAME
    fi
else
    # Contenedor ya existe
    echo ">> MongoDB container exists. Checking status..."
    docker start $CONTAINER_NAME >/dev/null 2>&1

    sleep 2  # Esperamos un poco para asegurar estado actualizado

    if is_container_failed $CONTAINER_NAME; then
        echo ">> Container is in a failed state. Recreating with Docker volume..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        docker run --name $CONTAINER_NAME -d -p 27017:27017 -v $DOCKER_VOLUME $IMAGE_NAME
    else
        echo ">> MongoDB container is running or started successfully."
    fi
fi

# Ejecutar provision.py si el directorio de persistencia no existe
if [ ! -d "$CHROMADB_PERSIST_DIRECTORY" ]; then
    echo ">> Directory $CHROMADB_PERSIST_DIRECTORY does not exist. Running provision.py..."
    python provision.py
else
    echo ">> Directory $CHROMADB_PERSIST_DIRECTORY already exists. Skipping provision."
fi

# Ejecutar aplicación
echo ">> Starting app.py..."
python app.py

