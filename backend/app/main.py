from fastapi import FastAPI

app = FastAPI()
@app.get("/")       # decorator for GET requests to the root path
def root():
    return {"message": "Backend is running"}