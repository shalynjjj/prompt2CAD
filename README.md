
download docker before run backend
# run backend(cd backend)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# run frontend(cd frontend)
npm install 
npm run dev


