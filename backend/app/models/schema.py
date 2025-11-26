from pydantic import BaseModel, Field
from fastapi import UploadFile, File, Form
from typing import Dict, Optional,Union, Any
from dataclasses import dataclass

class Aritifacts(BaseModel):
    silhouette_url: Optional[str] = None 
    preview_image_url: str
    stl_file_url: str


class AppResponse(BaseModel):
    success: bool
    session_id: str
    data: Optional[Dict] = None
    message: Optional[str] = None
    error: Optional[str] = None

class Generate2DRequest(BaseModel):
    session_id: Optional[str]=Field(None, description="session id, automaticcaly generate")
    class Config:
        schema_extra = {
            "example": {
                "session_id": "abc123"
            }
        }
class Edit2DRequest(BaseModel):
    session_id: str =Field(..., description="session id")
    prompt: str =Field(..., description="edit instructions")
    version: int =Field(2, description="version number of the silhouette to edit, default is 2")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "abc123",
                "prompt": "make it more rectangular",
                "version": 2
            }
        }
class Generate3DRequest(BaseModel):
    session_id: str =Field(..., description="session id")
    prompt: Optional[str]=Field(None, description="additional instructions for 3D generation, e.g., 'make it thicker'")
    depth_div_width: Optional[float] = Field(None, description="depth to width ratio for 3D model scaling")
    aspect_ratio: Optional[float] = Field(1.0, description="aspect ratio for 3D model scaling, default is 1.0")
    class Config:
        schema_extra = {
            "example": {
                "session_id": "abc123",
                "prompt": "make it thicker"
            }
        }

class Generate2DResponse(BaseModel):
    """生成2D轮廓的响应"""
    success: bool
    session_id: str
    data: Optional[Dict[str, Any]] = Field(None, description="包含 original, analysis, silhouette_2d")
    message: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "session_id": "abc-123-def",
                "data": {
                    "original": {
                        "file_path": "static/uploads/abc-123-def_original.png",
                        "url_path": "/static/uploads/abc-123-def_original.png"
                    },
                    "analysis": {
                        "success": True,
                        "data": {
                            "width": 1.0,
                            "length": 1.5,
                            "thickness": 0.3,
                            "complexity": "moderate"
                        },
                        "ratio_string": "1.5:1.0:0.3"
                    },
                    "silhouette_2d": {
                        "file_path": "static/processed/abc-123-def_2d_v1.png",
                        "url_path": "/static/processed/abc-123-def_2d_v1.png"
                    }
                },
                "message": "2D silhouette generated successfully"
            }
        }

class Edit2DResponse(BaseModel):
    """编辑2D轮廓的响应"""
    success: bool
    session_id: str
    data: Optional[Dict[str, Any]] = Field(None, description="包含 silhouette_2d, version")
    message: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "session_id": "abc-123-def",
                "data": {
                    "silhouette_2d": {
                        "file_path": "static/processed/abc-123-def_2d_v2.png",
                        "url_path": "/static/processed/abc-123-def_2d_v2.png"
                    },
                    "version": "v2"
                },
                "message": "2D silhouette edited (version v2)"
            }
        }


class Generate3DResponse(BaseModel):
    """生成3D模型的响应"""
    success: bool
    session_id: str
    data: Optional[Dict[str, Any]] = Field(None, description="包含 stl_file, render_preview")
    message: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "session_id": "abc-123-def",
                "data": {
                    "stl_file": {
                        "file_path": "static/stl/abc-123-def_3d.stl",
                        "url_path": "/static/stl/abc-123-def_3d.stl"
                    },
                    "render_preview": {
                        "file_path": "static/renders/abc-123-def_render.png",
                        "url_path": "/static/renders/abc-123-def_render.png"
                    },
                    "proportions": {
                        "width": 1.0,
                        "length": 1.5,
                        "thickness": 0.3,
                        "complexity": "moderate",
                        "ratio_string": "1.5:1.0:0.3"
                    }
                },
                "message": "3D model generated successfully"
            }
        }


