# chatbot_with_sales
chatbot_with_sales is a chatbot with a sales agent role engages with users, detects strong interest in products or services, and requests their contact information for future follow-up.

# MongoDB
You will have to install [MongoDB Community Server](https://www.mongodb.com/try/download/community).

Create MongoDB local Database->
mongod --dbpath "mongodb:root:folder\mongodb\data\"

Connect with Connection String-> Connect to localhost: mongodb://localhost

Para compilar app
$ docker compose build
Para correr
$ docker compose up -d


# MongoDB with docker

docker pull mongo:5.0
(this image docker.io/library/mongo:5.0)



si no esta creado:
docker run --name mongodb -d -p 27017:27017 docker.io/library/mongo:5.0
si ya esta creado, como iniciar: docker start mongodb
si ya esta creado como frenarlo: docker stop mongodb
si ya esta creado como eliminarlo: docker rm mongodb


docker run --name mongodb -d -p 27017:27017 -v /home/garza/Escritorio/chatbot_with_sales/mongo_database:/data/db docker.io/library/mongo:5.0

docker run --name mongodb -d -p 27017:27017 docker.io/library/mongo:5.0


#Comandos
activate venv: source venv/bin/activate
clean cache: sudo find . \( -name "__pycache__" -type d -o -name "*.pyc" -type f \) -exec rm -rf {} +
