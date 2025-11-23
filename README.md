# run backend
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# run frontend

npm install 
npm run dev

