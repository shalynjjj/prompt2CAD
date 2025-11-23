from fastapi import FastAPI
from app.api.routes import router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
app = FastAPI()


app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    # 允许前端开发端口 (Vite 默认是 5173) 和 生产环境
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000,reload=True)