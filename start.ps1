# start.ps1
$ErrorActionPreference = "Stop"

# Convertir .env de formato CRLF a LF (solo si necesario)
if (Test-Path ".env") {
    (Get-Content ".env") | ForEach-Object { $_ -replace "`r", "" } | Set-Content ".env"
} else {
    Write-Host ">> Archivo .env no encontrado"
    exit 1
}

# Cargar variables de entorno desde .env
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        $key = $matches[1].Trim()
        $val = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $val)
    }
}

# Crear entorno virtual si no existe
if (-Not (Test-Path "venv")) {
    Write-Host ">> Creating virtual environment..."
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host ">> Installing dependencies..."
    pip install -r requirements.txt
} else {
    Write-Host ">> Virtual environment already exists. Skipping requirements installation."
    .\venv\Scripts\Activate.ps1
}

# Asegurar carpeta mongo_database
if (-Not (Test-Path "mongo_database")) {
    Write-Host ">> Creating mongo_database directory..."
    New-Item -ItemType Directory -Path "mongo_database" | Out-Null
}

$CONTAINER_NAME = "mongodb"
$IMAGE_NAME = "mongo:latest"
$LOCAL_VOLUME = "$(Get-Location)\mongo_database:/data/db"
$DOCKER_VOLUME = "mongodb_database:/data/db"

function Is-ContainerFailed($name) {
    $status = docker inspect -f '{{.State.Status}}' $name 2>$null
    return $status -in @("exited", "dead", "created")
}

# Verificar si el contenedor existe
$containerExists = docker ps -a -q -f "name=^$CONTAINER_NAME$"

if (-Not $containerExists) {
    Write-Host ">> MongoDB container not found. Creating with local volume..."
    docker run --name $CONTAINER_NAME -d -p 27017:27017 -v "$LOCAL_VOLUME" $IMAGE_NAME
    Start-Sleep -Seconds 2
    if (Is-ContainerFailed $CONTAINER_NAME) {
        Write-Host ">> Container failed after creation. Recreating with Docker volume..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        docker run --name $CONTAINER_NAME -d -p 27017:27017 -v $DOCKER_VOLUME $IMAGE_NAME
    }
} else {
    Write-Host ">> MongoDB container exists. Checking status..."
    docker start $CONTAINER_NAME | Out-Null
    Start-Sleep -Seconds 2
    if (Is-ContainerFailed $CONTAINER_NAME) {
        Write-Host ">> Container is in a failed state. Recreating with Docker volume..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        docker run --name $CONTAINER_NAME -d -p 27017:27017 -v $DOCKER_VOLUME $IMAGE_NAME
    } else {
        Write-Host ">> MongoDB container is running or started successfully."
    }
}

# Obtener variable de entorno
$persistDir = [Environment]::GetEnvironmentVariable("CHROMADB_PERSIST_DIRECTORY")

# Ejecutar provision.py si el directorio no existe
if (-Not (Test-Path $persistDir)) {
    Write-Host ">> Directory $persistDir does not exist. Running provision.py..."
    python provision.py
} else {
    Write-Host ">> Directory $persistDir already exists. Skipping provision."
}

# Ejecutar app.py
Write-Host ">> Starting app.py..."
python app.py
