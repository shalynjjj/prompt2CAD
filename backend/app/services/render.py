import subprocess
import os
import shutil
from app.core.config import settings
from app.services.file_manager import FileManager


class RenderService:

    def render(self,scad_path: str, session_id:str):
        
        paths=FileManager.get_generated_file_paths(session_id)

        abs_scad=os.path.abspath(scad_path)
        abs_png=paths['png_absolute']
        abs_stl=paths['stl_absolute']

        print(f"Starting OpenSCAD rendering")
        try:
            cmd_png = [
                "xvfb-run",
                "-a",
                "openscad", 
                "-o", abs_png,
                abs_scad,
                "--imgsize=800,600"
            ]
            result_png=subprocess.run(cmd_png, capture_output=True, text=True)
            if result_png.returncode !=0:
                print(f"OpenSCAD PNG rendering error: {result_png.stderr}")
                raise Exception("Rendering PNG failed")
            
            cmd_stl=[
                "openscad",
                "-o", abs_stl,
                abs_scad
            ]
            result_stl=subprocess.run(cmd_stl, capture_output=True, text=True)
            if result_stl.returncode !=0:
                print(f"OpenSCAD STL rendering error: {result_stl.stderr}")
                raise Exception("Rendering STL failed")
            
            if not os.path.exists(abs_png):
                print("Rendered PNG file not found")
            
            if not os.path.exists(abs_stl):
                print("Rendered STL file not found")
            
            return{
                "preview_url": paths['png_url'],
                "stl_url": paths['stl_url']
            }
        except Exception as e:
            print(f"Exception during rendering: {e}")
            return {
                "preview_url": "",
                "stl_url": ""
            }
            
render_service= RenderService()