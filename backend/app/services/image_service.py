import os
import json
import base64
import httpx
from openai import OpenAI
from app.core.prompt import PROMPTS
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url="https://api.openai.com/v1")


class ImageService:
    """Handles OpenAI image operations."""
    def __init__(self):
        self.processed_dir = os.path.join("static", "processed")
        os.makedirs(self.processed_dir, exist_ok=True)
        self

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_proportions(self, image_b64: str, model: str = "gpt-4o") -> dict:
        """Analyze image proportions."""
        function_schema = [{
            'name': 'extract_keychain_proportions',
            'description': 'Extract dimensional proportions from keychain image',
            'parameters': {
                'type': 'object',
                'properties': {
                    'width': {'type': 'number', 'description': 'Width (baseline 1.0)'},
                    'length': {'type': 'number', 'description': 'Length relative to width'},
                    'thickness': {'type': 'number', 'description': 'Thickness/depth'},
                    'complexity': {
                        'type': 'string',
                        'enum': ['simple', 'moderate', 'complex'],
                        'description': 'Visual complexity'
                    }
                },
                'required': ['width', 'length', 'thickness', 'complexity']
            }
        }]

        try:
            print("Sending image for proportion analysis...")
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPTS.RATIO_ANALYSIS},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                        }
                    ]
                }],
                functions=function_schema,
                function_call={"name": "extract_keychain_proportions"}
            )
            print("Received response from model.")

            if response.choices[0].message.function_call:
                args = json.loads(response.choices[0].message.function_call.arguments)
                return {
                    "success": True,
                    "data": args,
                    "ratio_string": f"{args['length']}:{args['width']}:{args['thickness']}"
                }
            
            return {"success": False, "error": "No function call returned"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_2d_silhouette(self, image_path: str, model="gpt-image-1") -> str:
        """Generates a silhouette from the original image."""
        try:
            with open(image_path, "rb") as img_file:
                response = client.images.edit(
                    model=model,
                    image=img_file,
                    prompt=PROMPTS.SILHOUETTE_EXTRACTION,
                    n=1                )
            
            # Handle Base64 response

            if not response.data:
                raise ValueError("No image data returned")
            image_data = response.data[0]
            
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                return image_data.b64_json
            else:
                raise ValueError("API response did not contain base64 data")
        except Exception as e:
            print(f"Error generating silhouette: {e}")
            raise e
    def edit_silhouette(self, image_path: str="", model="gpt-image-1", instructions: str="") -> str:
        """Edits a silhouette based on red marks and instructions."""
        try:
            if not os.path.exists(image_path):
                raise ValueError(f"Image path does not exist: {image_path}")
            
            combined_prompt = PROMPTS.SILHOUETTE_EDIT_PROMPT.format(user_instruction=instructions)

            with open(image_path, "rb") as img_file:
                result = client.images.edit(
                    model=model,
                    image=img_file,
                    prompt=combined_prompt,
                    n=1,
                )
            if not result.data:
                raise ValueError("No image data returned from edit")
            
            image_b64 = result.data[0].b64_json
            return image_b64
        except Exception as e:
            raise ValueError(f"Error editing silhouette: {str(e)}")

        # if not image_path:
        #     combined_prompt = PROMPTS.SILHOUETTE_TEXT_PROMPT.format(user_instruction=instructions)
        # else:
        #     combined_prompt = PROMPTS.SILHOUETTE_EDIT_PROMPT.format(user_instruction=instructions)
        
        # try:
        #     if not image_path:
        #         result = client.images.edit(
        #             model="gpt-image-1",
        #             image=open(image_path, "rb"),
        #             prompt=combined_prompt,
        #             n=1,
        #         )
        #     else:
        #         result = client.images.edit(
        #             model=model,
        #             image=open(image_path, "rb"),
        #             prompt=combined_prompt,
        #             n=1,
        #         )
            
        #     filename = os.path.basename(image_path).split('.')[0] + '_updated.png'
        #     output_path = os.path.join(self.processed_dir, filename)
            
        #     image_bytes = base64.b64decode(result.data[0].b64_json)
        #     with open(output_path, "wb") as f:
        #         f.write(image_bytes)
                
        #     return output_path
        # except Exception as e:
        #     raise ValueError(f"Error editing silhouette: {str(e)}")

    def _download_or_save_image(self, image_data, output_path):
        """Helper to handle OpenAI image response (URL or B64)."""
        image_b64 = image_data.b64_json
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
        return output_path
        
ImageService = ImageService()