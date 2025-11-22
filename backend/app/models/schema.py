from pydantic import BaseModel
from fastapi import UploadFile, File, Form
from typing import Optional,Union
from dataclasses import dataclass

class GeneratedArtifacts(BaseModel):
    preview_image_url: str
    stl_file_url: str
    scad_code_url: str
    scad_content: str 

class ChatResponse(BaseModel):
    message: str
    session_id: str
    data: GeneratedArtifacts

@dataclass
class ChatRequest:
    prompt: str = Form(...,description="User prompt for code generation or refinement")
    session_id: Optional[str] = Form(None, description="Session ID")
    image: Union[UploadFile, str, None] = File(None, description="Optional image file")