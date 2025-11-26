import os
import base64
from PIL import Image
import io
from app.core.database import Database


class FileManager:
    """Manages file operations with session_id based naming."""
    
    def __init__(self):
        self.base_dir = "static"
        self.upload_dir = os.path.join(self.base_dir, "uploads")
        self.processed_dir = os.path.join(self.base_dir, "processed")
        self.stl_dir = os.path.join(self.base_dir, "stl")
        self.render_dir = os.path.join(self.base_dir, "renders")
        
        self.db = Database()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories."""
        for directory in [self.upload_dir, self.processed_dir, self.stl_dir, self.render_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def save_uploaded_image(self, session_id: str, file_content: bytes) -> dict:
        """Save uploaded image as {session_id}_original.png"""
        try:
            image = Image.open(io.BytesIO(file_content))
            filename = f"{session_id}_original.png"
            file_path = os.path.join(self.upload_dir, filename)
            
            image.convert('RGBA').save(file_path, 'PNG')
            url_path = f"/static/uploads/{filename}"
            
            # Save to database
            self.db.save_file(session_id, "original", file_path, url_path)
            
            return {"file_path": file_path, "url_path": url_path}
        except Exception as e:
            raise ValueError(f"Failed to save image: {str(e)}")
    
    def save_2d_silhouette(self, session_id: str, image_b64: str, version: str = "v1") -> dict:
        """Save 2D silhouette as {session_id}_2d_{version}.png"""
        try:
            print(f"Saving 2D silhouette for session: {session_id}, version: {version}")
            image_bytes = base64.b64decode(image_b64)

            print(f"Decoded image bytes length: {len(image_bytes)}")
            filename = f"{session_id}_2d_{version}.png"

            print(f"Generated filename: {filename}")
            file_path = os.path.join(self.processed_dir, filename)
            

            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            print(f"Saved silhouette to path: {file_path}")
            url_path = f"/static/processed/{filename}"
            
            # Save to database
            self.db.save_file(session_id, f"2d_{version}", file_path, url_path)
            
            print(f"Saved file info to database for session: {session_id}, type: 2d_{version}")
            return {"file_path": file_path, "url_path": url_path}
        except Exception as e:
            raise ValueError(f"Failed to save 2D silhouette: {str(e)}")
    
    def save_stl_file(self, session_id: str, stl_bytes: bytes) -> dict:
        """Save STL file as {session_id}_3d.stl"""
        try:
            filename = f"{session_id}_3d.stl"
            file_path = os.path.join(self.stl_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(stl_bytes)
            
            url_path = f"/static/stl/{filename}"
            
            # Save to database
            self.db.save_file(session_id, "stl", file_path, url_path)
            
            return {"file_path": file_path, "url_path": url_path}
        except Exception as e:
            raise ValueError(f"Failed to save STL: {str(e)}")
    
    def save_3d_render(self, session_id: str, render_b64: str) -> dict:
        """Save 3D render as {session_id}_render.png"""
        try:
            image_bytes = base64.b64decode(render_b64)
            filename = f"{session_id}_render.png"
            file_path = os.path.join(self.render_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            url_path = f"/static/renders/{filename}"
            
            # Save to database
            self.db.save_file(session_id, "render", file_path, url_path)
            
            return {"file_path": file_path, "url_path": url_path}
        except Exception as e:
            raise ValueError(f"Failed to save render: {str(e)}")
    
    def get_file_path(self, session_id: str, file_type: str) -> str:
        """Get file path from database."""
        file_info = self.db.get_file(session_id, file_type)
        if not file_info:
            raise FileNotFoundError(f"File not found: {session_id}/{file_type}")
        return file_info["file_path"]
    
    def encode_image_to_base64(self, file_path: str) -> str:
        """Encode image to base64."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
        

FileManager = FileManager()