import io
import uuid
import time
import threading
from fastapi import UploadFile
import glob
import cv2
import numpy as np
import os
from stl import mesh
from app.models.schema import AppResponse, Aritifacts, Edit2DResponse, Generate3DResponse

from app.services.file_manager import FileManager
from app.services.render import render_service
from app.services.image_service import ImageService
from app.services.model_3d_service import Model3DService

from app.core.config import settings

class WorkflowService:

    def __init__(self):
        self.processing_locks = {}
        self.lock_manager=threading.Lock()

        self.file_manager = FileManager
        self.image_service = ImageService
        self.model_3d_service = Model3DService
    
    def _acquire_lock(self, session_id: str):
        with self.lock_manager:
            if session_id not in self.processing_locks:
                self.processing_locks[session_id] = threading.Lock()
        self.processing_locks[session_id].acquire()
    
    def _release_lock(self, session_id: str):
        if session_id in self.processing_locks:
            self.processing_locks[session_id].release()
    
    
    async def generate_2d_from_upload(self, image_file: UploadFile,session_id_in: str=None) -> AppResponse:
        session_id=session_id_in or str(uuid.uuid4())
        self._acquire_lock(session_id)
        try:
            print(f"Processing image for session: {session_id}")

            #1.save upload pic
            content=await image_file.read()
            upload_info=self.file_manager.save_uploaded_image(session_id=session_id,file_content=content)
            
            print(f"Uploaded image saved at: {upload_info['file_path']}")

            #2.analyze proportions
            image_b64=self.image_service.encode_image_to_base64(upload_info['file_path'])
            print(f"Image encoded to base64 for session: {session_id}")
            anlaysis=self.image_service.analyze_proportions(image_b64=image_b64)

            print(f"Image analysis result: {anlaysis}")
            if not anlaysis['success']:
                return AppResponse(
                    success=False,
                    session_id=session_id,
                    error=anlaysis.get('error','Failed to analyze image proportions.')
                )
            
            self.file_manager.db.save_analysis(
                session_id=session_id,
                analysis_data=anlaysis['data']
            )
            print(f"Analysis data saved for session: {session_id}") 
            #3.generate 2d silhouette
            silhouette_b64=self.image_service.generate_2d_silhouette(image_path=upload_info['file_path'])
            silhouette_info=self.file_manager.save_2d_silhouette(
                session_id=session_id,
                image_b64=silhouette_b64,
                version="v1"
            )
            print(f"2D silhouette saved for session: {session_id}")

            return AppResponse(
                success=True,
                session_id=session_id,
                data={
                    "original": upload_info['url_path'],
                    "analysis": anlaysis,
                    "silhouette_2d": silhouette_info
                },
                message="2D silhouette generated successfully."
            )
        except Exception as e:
            return AppResponse(
                success=False,
                session_id=session_id,
                error=str(e)
            )
        finally:
            self._release_lock(session_id)



        pass

    async def edit_silhouette(self, session_id: str, prompt: str, image_path: str,version: int=2) -> Edit2DResponse:
        self._acquire_lock(session_id)
        try:
            print(f"Editing silhouette for session: {session_id}")
            print(f"User image path: {image_path}")  
            print(f"User prompt: {prompt}")  

            edited_b64 = self.image_service.edit_silhouette(
            image_path=image_path,      # ← 使用用户上传的图片（含红色标记）
            instructions=prompt          # user requirements 
            )
            new_version = f"v{version}"
            edited_info = self.file_manager.save_2d_silhouette(
                session_id=session_id,
                image_b64=edited_b64,
                version=new_version
            )
            print(f"Edited silhouette saved: {edited_info}")  # log 
        
            return Edit2DResponse(
                success=True,
                session_id=session_id,
                data={
                    "silhouette_2d": edited_info,
                    "version": new_version
                },
                message=f"2D silhouette edited successfully (version {new_version})."
            )
        except Exception as e:
            print(f"Error in edit_silhouette: {str(e)}")
            return AppResponse(
                success=False,
                session_id=session_id,
                error=str(e)
            )
        finally:
            self._release_lock(session_id)

    async def generate_3d_model(self, session_id: str,depth_div_width: float, aspect_ratio: float) -> Generate3DResponse:
        self._acquire_lock(session_id)
        """
        session_id: find 2d silhouette and analysis data by session_id
        """
        try:
            files=glob.glob(f"static/processed/{session_id}_2d_*.png")
            latest_silhouette_path=max(files, key=os.path.getctime)
            with open(latest_silhouette_path, "rb") as f:
                image_path=f.read()
            aspect_ratio=1.0
            nparr = np.frombuffer(image_path, np.uint8)
            im = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
            if im is None:
                raise ValueError(f"Failed to read image from {image_path}")
            
            # Process image array
            im_array = np.array(im)
            im_array = 255 - im_array
            im_array = np.rot90(im_array, -1, (0, 1))
            
            mesh_size = [im_array.shape[0], im_array.shape[1]]
            mesh_max = np.max(im_array)
            
            if mesh_max == 0:
                raise ValueError("Image contains no depth information (all pixels are black)")
            
            # Scale mesh based on depth information
            if len(im_array.shape) == 3:
                # Color image - use first channel
                scaled_mesh = mesh_size[0] * depth_div_width * im_array[:, :, 0] / mesh_max
            else:
                # Grayscale image
                scaled_mesh = mesh_size[0] * depth_div_width * im_array / mesh_max
            
            # Create mesh
            mesh_shape = mesh.Mesh(
                np.zeros((mesh_size[0] - 1) * (mesh_size[1] - 1) * 2, dtype=mesh.Mesh.dtype)
            )
            
            # Generate triangles for the mesh
            for i in range(0, mesh_size[0] - 1):
                for j in range(0, mesh_size[1] - 1):
                    mesh_num = i * (mesh_size[1] - 1) + j
                    
                    # Apply aspect ratio to i coordinate (height)
                    i_scaled = i * aspect_ratio
                    i1_scaled = (i + 1) * aspect_ratio
                    
                    # First triangle
                    mesh_shape.vectors[2 * mesh_num][2] = [i_scaled, j, scaled_mesh[i, j]]
                    mesh_shape.vectors[2 * mesh_num][1] = [i_scaled, j + 1, scaled_mesh[i, j + 1]]
                    mesh_shape.vectors[2 * mesh_num][0] = [i1_scaled, j, scaled_mesh[i + 1, j]]
                    
                    # Second triangle
                    mesh_shape.vectors[2 * mesh_num + 1][0] = [i1_scaled, j + 1, scaled_mesh[i + 1, j + 1]]
                    mesh_shape.vectors[2 * mesh_num + 1][1] = [i_scaled, j + 1, scaled_mesh[i, j + 1]]
                    mesh_shape.vectors[2 * mesh_num + 1][2] = [i1_scaled, j, scaled_mesh[i + 1, j]]
            
            # Generate output filename
            stl_buffer = io.BytesIO()
            mesh_shape.save('temp', fh=stl_buffer)  # 保存到内存
            stl_bytes = stl_buffer.getvalue()

            stl_info = self.file_manager.save_stl_file(session_id, stl_bytes)
            render_b64=self.model_3d_service.render_stl_to_image(stl_info['file_path'])
            print(f"Render b64 length: {len(render_b64)}")
            render_info=self.file_manager.save_3d_render(session_id=session_id,render_b64=render_b64)
            print(f"Render info: {render_info}")
            
            # base_name = os.path.splitext(os.path.basename(image_path))[0]
            # output_filename = f"{base_name}_3d.stl"
            # output_path = os.path.join("static/stls", output_filename)
            
            # Save mesh to file
            # mesh_shape.save(output_path)
            return Generate3DResponse(
                success=True,
                session_id=session_id,
                data={
                    "stl_file": stl_info,
                    "render_image": render_info,
                },
                message="3D model generated successfully."
            )
            return output_path
            # silhouette_path=None
            # for v in range(10,0,-1):
            #     try:
            #         silhouette_path=self.file_manager.get_file_path(
            #             session_id=session_id,
            #             file_type=f"2d_v{v}")
            #         break
            #     except FileNotFoundError:
            #         continue
            # if not silhouette_path:
            #     return AppResponse(
            #         success=False,
            #         session_id=session_id,
            #         error="No 2D silhouette found for 3D generation."
            #     )
            
            # analysis=self.file_manager.db.get_analysis(session_id=session_id)
            # if not analysis:
            #     return AppResponse(
            #         success=False,
            #         session_id=session_id,
            #         error="No analysis data found for 3D generation."
            #     )
            
            # stl_bytes=self.model_3d_service.generate_stl_from_2d(silhouette_path=silhouette_path,proportions=analysis)
            # stl_info=self.file_manager.save_stl_file(session_id=session_id,stl_bytes=stl_bytes)

            # render_b64=self.model_3d_service.render_stl_to_image(stl_info['file_path'])
            # render_info=self.file_manager.save_3d_render(session_id=session_id,render_b64=render_b64)

            # return AppResponse(
            #     success=True,
            #     session_id=session_id,
            #     data={
            #         "stl_file": stl_info,
            #         "render_image": render_info,
            #         "proportions": analysis
            #     },
            #     message="3D model generated successfully."
            # )
        except Exception as e:
            return AppResponse(success=False,session_id=session_id,error=str(e))
        
        finally:
            self._release_lock(session_id)



    
    # async def handle_chat(self, request: ChatRequest) -> ChatResponse:

    #     # session ID
    #     session_id=request.session_id or str(uuid.uuid4())

    #     if self.processing_locks.get(session_id, False):
    #         raise Exception("A request is already being processed for this session. Please wait.")

    #     self.processing_locks[session_id] = True

    #     try:
    #         last_code=history_service.get_latest_code(session_id)
    #         file_id=f"{session_id}_{int(time.time())}"


    #     # image upload
    #         upload_path=None
    #         if request.image:
    #             upload_path=await file_manager.save_upload_file(request.image,session_id=session_id)
            
    #         history_service.add_user_message(session_id, request.prompt, image_path=upload_path)

    #         last_code=history_service.get_latest_code(session_id)


    #         print(f" calling LLM for session:{session_id}")
    #         scad_code=await llm_coder.generate_code(
    #             prompt=request.prompt,
    #             previous_code=last_code,
    #             image_path=upload_path
    #         )
    #         print(f"scad_code:{scad_code}")

    #         code_file_info= await file_manager.save_generated_code(
    #             code=scad_code,
    #             session_id=session_id
    #         )

    #         # preview & STL
    #         print(f"Rendering code for session:{session_id}")
    #         render_result=render_service.render(
    #             scad_path=code_file_info['absolute_path'],
    #             session_id=session_id
    #         )

    #         files_data={
    #             "preview": render_result["preview_url"],
    #             "stl": render_result["stl_url"],
    #             "scad": code_file_info["url"]
    #         }   

    #         # TODO, prompt versioning & versioning
    #         history_service.add_ai_message(
    #             session_id=session_id,
    #             message="Generated 3D model based on your prompt.",
    #             scad_code=scad_code,
    #             file_paths=files_data,
    #             prompt_version="v1"
    #             )

    #         return ChatResponse(
    #             message="Code generated and rendered successfully.",
    #             session_id=session_id,
    #             data=GeneratedArtifacts(
    #                 preview_image_url=render_result["preview_url"],
    #                 stl_file_url=render_result["stl_url"],
    #                 scad_code_url=code_file_info["url"],
    #                 scad_content=scad_code
    #         ))
    #     except Exception as e:
    #         print(f"Error in workflow for session {session_id}: {e}")
    #         raise e
    #     finally:
    #         if session_id in self.processing_locks:
    #             del self.processing_locks[session_id]



workflow = WorkflowService()