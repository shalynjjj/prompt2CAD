from fastapi import APIRouter,Depends
from app.models.schema import ChatRequest, ChatResponse
from app.services.workflow import workflow

router = APIRouter()

@router.get("/")
async def home():
    return {"message": "API is running."}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest = Depends()):
    """
    handle user chat requests, generate or modify OpenSCAD code, and return rendering results.
    """
    response = await workflow.handle_chat(request)
    return response