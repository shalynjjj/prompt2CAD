import uuid
import time
import shutil
import os
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings



class FileManagerService:

    def __init__(self):
        # In docker, Working directory is /app, so static files are in /app/static
        self.base_dir = Path("static")

        self.dirs = {
            "upload": self.base_dir / "uploads",
            "processed": self.base_dir / "processed",
            "images": self.base_dir / "images",
            "stl": self.base_dir / "stls",
            "codes": self.base_dir / "codes"
        }
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # TODO
    def _generate_filename(self, session_id: str, extension: str, prefix: str = "gen") -> str:
        timestamp = int(time.time())
        unique_suffix = str(uuid.uuid4())[:4]

        # eg. session123_user_1701301234_abcd.png
        return f"{session_id}_{prefix}_{timestamp}_{unique_suffix}.{extension}"   

    async def save_upload_file(self, file: UploadFile, session_id: str) -> str:
        if not file:
            return None
        
        ext = file.filename.split(".")[-1] if "." in file.filename else "png"
        filename = self._generate_filename(session_id, ext, prefix="user")
        file_path = self.dirs["upload"] / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # return the url path to the file
        return f"/static/uploads/{filename}"
    
    async def save_generated_code(self,code:str,session_id:str) -> str:
        filename=self._generate_filename(session_id,"scad")
        file_path=self.dirs["codes"]/filename

        with open(file_path,"w",encoding="utf-8") as f:
            f.write(code)
        
        return {
            # absolute path for rendering service
            # url for frontend access
            "absolute_path":str(file_path.absolute()),
            "url":f"/static/codes/{filename}"
        }
    
    def get_generated_file_paths(self, session_id: str):
        """预生成输出文件的路径"""
        base_name = self._generate_filename(session_id, "").replace(".", "")
        png_name = f"{base_name}.png"
        stl_name = f"{base_name}.stl"
        
        return {
            "png_absolute": str((self.dirs["images"] / png_name).absolute()),
            "stl_absolute": str((self.dirs["stl"] / stl_name).absolute()),
            "png_url": f"/static/images/{png_name}",
            "stl_url": f"/static/stls/{stl_name}"
        }
    
    
    
        

file_manager = FileManagerService()
