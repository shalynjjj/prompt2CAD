from openai import OpenAI
import re

from app.core.config import settings
from app.core.prompt import build_prompt



class LLMService:

    def __init__(self):
        try:
            print("Initializing OpenAI client...")
            print(f"api_key: {settings.OPENAI_API_KEY}", flush=True)
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.client = None

    async def generate_code(self, prompt: str, previous_code: str = None, image_path: str = None) -> str:
        if not self.client:
            print(f"openai client is not initialized")
            return "//error: NO API client"
        final_prompt = build_prompt(prompt, previous_code)
    
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": final_prompt}
        ]

        # TODO: handle image input if needed in future

        try:
            print("Sending request to LLM...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1500,
                temperature=0.1,
            )
            code_output = response.choices[0].message.content
            cleaned_code = self._clean_markdown(code_output)
            return cleaned_code

        except Exception as e:
            print(f"Error during LLM call: {e}")
            raise
    

    def _clean_markdown(self, text: str) -> str:
        """
        remove ```openscad and ``` markers, keep only code content
        """
        # remove the starting ```openscad or ```scad or ```
        text = re.sub(r"^```[a-zA-Z]*\n", "", text.strip())
        # remove the ending ```
        text = re.sub(r"\n```$", "", text.strip())
        return text.strip()


llm_coder= LLMService()