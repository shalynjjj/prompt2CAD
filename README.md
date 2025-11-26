
download docker before run backend
# run backend(cd backend)
## Current version
```
cd backend
# install system dependencies
brew install openscad glib

# create virtual environment 
python3 -m venv venv
source venv/bin/activate # enter virtual environment
pip3 install -r requirements.txt

# exit virtual environment
deactivate

# run 
```
## Docker
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# run frontend(cd frontend)
npm install 
npm run dev


