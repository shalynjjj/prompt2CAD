import uuid
import time
import threading
from fastapi import UploadFile
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
            instructions=prompt          # ← 使用用户的文字描述
            )
            new_version = f"v{version}"
            edited_info = self.file_manager.save_2d_silhouette(
                session_id=session_id,
                image_b64=edited_b64,
                version=new_version
            )
            print(f"Edited silhouette saved: {edited_info}")  # ← 新增：日志
        
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

    async def generate_3d_model(self, session_id: str, prompt: str) -> Generate3DResponse:
        self._acquire_lock(session_id)
        try:
            silhouette_path=None
            for v in range(10,0,-1):
                try:
                    silhouette_path=self.file_manager.get_file_path(
                        session_id=session_id,
                        file_type=f"2d_v{v}")
                    break
                except FileNotFoundError:
                    continue
            if not silhouette_path:
                return AppResponse(
                    success=False,
                    session_id=session_id,
                    error="No 2D silhouette found for 3D generation."
                )
            
            analysis=self.file_manager.db.get_analysis(session_id=session_id)
            if not analysis:
                return AppResponse(
                    success=False,
                    session_id=session_id,
                    error="No analysis data found for 3D generation."
                )
            
            stl_bytes=self.model_3d_service.generate_stl_from_2d(silhouette_path=silhouette_path,proportions=analysis)
            stl_info=self.file_manager.save_stl_file(session_id=session_id,stl_bytes=stl_bytes)

            render_b64=self.model_3d_service.render_stl_to_image(stl_info['file_path'])
            render_info=self.file_manager.save_3d_render(session_id=session_id,render_b64=render_b64)

            return AppResponse(
                success=True,
                session_id=session_id,
                data={
                    "stl_file": stl_info,
                    "render_image": render_info,
                    "proportions": analysis
                },
                message="3D model generated successfully."
            )
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