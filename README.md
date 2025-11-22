# prompt2CAD
# api
```
backend/
├── main.py
├── static/                 # 静态资源 (对外公开)
│   ├── images/             # .png
│   ├── stls/               # .stl
│   ├── codes/              # .scad (新增)
│   └── uploads/            # 用户上传的参考图
└── app/
    ├── core/
    │   ├── config.py
    │   └── prompts.py      # 【核心】Prompt 模板 (System Prompt + Few-shot examples)
    ├── models/
    │   └── schema.py       # 定义 API 数据结构
    ├── services/
    │   ├── workflow.py     # 【总管】协调全流程
    │   ├── llm_coder.py    # 【大脑】负责与 LLM 交互，生成/修改代码
    │   ├── renderer.py     # 【工匠】调用 OpenSCAD 编译代码 -> STL/PNG
    │   ├── file_manager.py # 【管家】负责存图、存代码文件
    │   └── history.py      # 【记忆】管理会话上下文 (简单的内存或文件存储)
    └── api/
        └── routes.py       # 接口层
```
# TODO
1. file(image, stl, code), store, transfer
