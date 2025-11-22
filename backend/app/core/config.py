import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # 渲染器开关：True=返回假文件(开发用), False=调用真实OpenSCAD
    USE_MOCK_RENDERER = os.getenv("USE_MOCK_RENDERER", "True").lower() == "true"

settings = Settings()