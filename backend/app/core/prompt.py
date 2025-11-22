# 系统提示词：设定 LLM 的角色和编程规范
SYSTEM_PROMPT_CODER = """
You are an expert OpenSCAD programmer.
Your task is to write OpenSCAD code based on user requirements.

Rules:
1. Output ONLY the raw OpenSCAD code. 
2. Do NOT output conversational text, markdown blocks (```), or explanations.
3. Always use '$fn=100;' for spheres and cylinders to ensure smoothness.
4. Use module-based design.
5. Ensure the code is valid and compilable.
"""

def build_prompt(user_text: str, previous_code: str = None) -> str:
    """
    构造 Prompt。
    - 如果有 previous_code，说明用户想修改现有模型。
    - 如果没有，说明用户想从头创建。
    """
    if previous_code:
        return f"""
{SYSTEM_PROMPT_CODER}

Here is the EXISTING OpenSCAD code:
----------------
{previous_code}
----------------

User Feedback/Modification Request: "{user_text}"

Task: Rewrite the code to implement the feedback. Keep the rest of the model structure intact.
Output ONLY the full valid OpenSCAD code.
"""
    else:
        return f"""
{SYSTEM_PROMPT_CODER}

User Request: "{user_text}"

Task: Write OpenSCAD code to create this object.
Output ONLY the code.
"""