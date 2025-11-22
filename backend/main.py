from fastapi import FastAPI
from app.api.routes import router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
app = FastAPI()


app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000,reload=True)