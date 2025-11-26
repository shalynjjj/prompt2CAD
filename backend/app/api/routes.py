import os
from typing import Optional
import traceback
import uuid
from fastapi import APIRouter,Depends, File, Form, HTTPException,UploadFile
from app.models.schema import AppResponse,Generate2DResponse, Edit2DResponse, Generate3DResponse
from app.services.workflow import workflow
from app.services.file_manager import FileManager

router = APIRouter()

@router.get("/")
async def home():
    return {"message": "API is running."}

@router.post('/generate2d', response_model=Generate2DResponse, summary="generate 2d sketch", description="upload image and generate silhouette, and analyze proprotions")
async def generate_2d(file: UploadFile= File(..., description="uploaded file(png/jpg/jpeg/webp)"), session_id: Optional[str]=Form(None, description="session id(optional)")):
    """
    generate initial version of small product, e.g., keychain
    """
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only png, jpg, jpeg, webp are allowed.")
    try:
        result=await workflow.generate_2d_from_upload(image_file=file, session_id_in=session_id)
    except Exception as e:
        error_msg = traceback.format_exc()
        print("---------------- CRITICAL ERROR ----------------")
        print(error_msg)
        print("------------------------------------------------")
        # 为了方便调试，暂时把错误返给前端
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Failed to generate 2D silhouette.")
    return result

@router.post('/edit2d', response_model=Edit2DResponse, summary="edit 2d sketch based on user prompt", description="edit previously generated 2d sketch based on user instructions")
async def edit_endpoint(
    session_id: str=Form(..., description="session id"),
    prompt: str=Form(..., description="edit instructions"),
    image: UploadFile=File(..., description="2D Sketch Image file"),
    version: int=Form(2, description="version number of the silhouette to edit, default is 2")
):
    try:
        content=await image.read()
        print(f"Image size: {len(content)} bytes")

        temp_filenam=f"{session_id}_user_edited_{uuid.uuid4().hex[:8]}.png"
        temp_path=os.path.join("static","uploads",temp_filenam)

        os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(content)
        print(f"Saved uploaded image to {temp_path}")

        result = await workflow.edit_silhouette(session_id=session_id, prompt=prompt, image_path=temp_path, version=version)
        if not result.success:  
            raise HTTPException(status_code=500, detail=result.error or "Failed to edit 2D silhouette.")
        return result
    except Exception as e:
        error_msg = traceback.format_exc()
        print("---------------- EDIT ERROR ----------------")
        print(error_msg)
        print("--------------------------------------------")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")     
    

@router.post('/generate3D', response_model=Generate3DResponse, summary="generate 3d model based on 2d sketch and user instructions", description="generate 3d model(stl and render) based on previously generated 2d sketch and user instructions")
async def generate3D_endpoint(session_id: str=Form(..., description="session id"), depth_div_width: float=Form(..., description="depth divided by width ratio"), aspect_ratio: float=Form(1.0, description="aspect ratio")):
    """
    generate 3D model based on 2D sketch and user instructions
    """
    result=await workflow.generate_3d_model(session_id=session_id, depth_div_width=depth_div_width, aspect_ratio=aspect_ratio)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Failed to generate 3D model.")
    return result
