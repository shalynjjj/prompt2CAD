import uuid
import time
from app.models.schema import ChatRequest, ChatResponse, GeneratedArtifacts

from app.services.history import history_service
from app.services.file_manager import file_manager
from app.services.llm_coder import llm_coder
from app.services.render import render_service

from app.core.config import settings

class WorkflowService:

    def __init__(self):
        self.processing_locks = {}
    
    async def handle_chat(self, request: ChatRequest) -> ChatResponse:

        # session ID
        session_id=request.session_id or str(uuid.uuid4())
        file_id=f"{session_id}_{int(time.time())}"

        if self.processing_locks.get(session_id, False):
            raise Exception("A request is already being processed for this session. Please wait.")

        self.processing_locks[session_id] = True

        try:
            last_code=history_service.get_latest_code(session_id)


        # image upload
            upload_path=None
            if request.image:
                upload_path=await file_manager.save_upload_file(request.image,session_id=session_id)
            
            history_service.add_user_message(session_id, request.prompt, image_path=upload_path)

            last_code=history_service.get_latest_code(session_id)


            print(f" calling LLM for session:{session_id}")
            scad_code=await llm_coder.generate_code(
                prompt=request.prompt,
                previous_code=last_code,
                image_path=upload_path
            )
            print(f"scad_code:{scad_code}")

            code_file_info= await file_manager.save_generated_code(
                code=scad_code,
                session_id=session_id
            )

            # preview & STL
            print(f"Rendering code for session:{session_id}")
            render_result=render_service.render(
                scad_path=code_file_info['absolute_path'],
                session_id=session_id
            )

            files_data={
                "preview": render_result["preview_url"],
                "stl": render_result["stl_url"],
                "scad": code_file_info["url"]
            }   

            # TODO, prompt versioning & versioning
            history_service.add_ai_message(
                session_id=session_id,
                message="Generated 3D model based on your prompt.",
                scad_code=scad_code,
                file_paths=files_data,
                prompt_version="v1"
                )

            return ChatResponse(
                message="Code generated and rendered successfully.",
                session_id=session_id,
                data=GeneratedArtifacts(
                    preview_image_url=render_result["preview_url"],
                    stl_file_url=render_result["stl_url"],
                    scad_code_url=code_file_info["url"],
                    scad_content=scad_code
            ))
        except Exception as e:
            print(f"Error in workflow for session {session_id}: {e}")
            raise e
        finally:
            if session_id in self.processing_locks:
                del self.processing_locks[session_id]



workflow = WorkflowService()