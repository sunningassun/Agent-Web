# 智能 Agent 对话系统 - 自定义工具助手

一个基于 Flask 和 LLM（大语言模型）的智能对话系统，支持用户动态添加自定义 HTTP API 工具，Agent 会根据用户问题自动调用合适的工具并生成回答。

## ✨ 特性

- 🤖 **智能对话**：集成 LLM 的 function calling 能力，自动判断并调用工具
- 🛠️ **动态工具管理**：用户可通过界面添加/删除自定义 HTTP API 工具（GET/POST）
- 🌐 **内置工具**：IP 归属地查询、答案之书、城际路线查询、实时天气
- 💬 **对话历史**：支持多轮对话上下文
- 🎨 **可视化界面**：聊天界面 + 工具管理面板
- 🔌 **灵活模型配置**：支持本地模型（OLLAMA）或云端 API（硅基流动）

## 📦 环境要求

- Python 3.8+
- pip

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd agent_web
```

### 2. 安装依赖

```bash
pip install flask flask-cors requests
```

### 3. 配置模型

系统支持两种模型调用方式，根据需求选择一种即可。

#### 方式一：使用硅基流动 API（云端）

- 注册 [硅基流动](https://siliconflow.cn/) 获取 API Key
- 设置环境变量：

```bash
export SILICONFLOW_API_KEY="your-api-key-here"
```

- 模型默认：`Qwen/Qwen2.5-7B-Instruct`（可在代码中修改）

#### 方式二：使用 OLLAMA 本地模型

需要先安装并运行 [OLLAMA](https://ollama.com/)，并拉取一个支持 function calling 的模型（如 `llama3.1`、`qwen2.5`、`mistral` 等）。

```bash
ollama pull qwen2.5:7b
ollama serve   # 启动服务，默认监听 11434 端口
```

然后修改 `app.py` 中的模型调用部分（具体修改见下文“模型适配”章节）。

### 4. 启动服务

```bash
python app.py
```

访问 `http://localhost:5000` 即可使用。

---

## 🔧 模型适配详解

### 默认代码（硅基流动）

原 `app.py` 中的 `chat_completion` 函数使用硅基流动 API（OpenAI 兼容格式）：

```python
def chat_completion(messages, tools_schema):
    headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}", ...}
    payload = {
        "model": SILICONFLOW_MODEL,
        "messages": messages,
        "tools": tools_schema,
        "tool_choice": "auto"
    }
    resp = requests.post("https://api.siliconflow.cn/v1/chat/completions", json=payload, headers=headers)
    return resp.json()
```

### 切换到 OLLAMA

OLLAMA 也提供了 OpenAI 兼容的 API 端点（默认 `http://localhost:11434/v1`），因此只需修改 `chat_completion` 中的 URL 和认证头即可。

**修改步骤：**

1. 注释或删除原有的硅基流动相关配置
2. 添加 OLLAMA 配置：

```python
# OLLAMA 配置
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:7b"   # 确保已 pull 该模型
```

3. 重写 `chat_completion` 函数（或保留原函数，修改内部请求地址和 header）：

```python
def chat_completion(messages, tools_schema):
    headers = {
        "Content-Type": "application/json"
        # OLLAMA 默认不需要 API Key
    }
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": tools_schema,
        "tool_choice": "auto"
    }
    resp = requests.post(f"{OLLAMA_BASE_URL}/chat/completions", json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        raise Exception(f"OLLAMA 调用失败: {resp.status_code} - {resp.text}")
    return resp.json()
```

> **注意**：OLLAMA 的 `/v1/chat/completions` 端点需要 OLLAMA 版本 0.3.0 以上，且模型本身需支持 function calling。部分模型（如 llama3.1）支持较好。

4. 移除 `SILICONFLOW_API_KEY` 环境变量要求。

### 其他 API（如 OpenAI、DeepSeek 等）

只需修改 `chat_completion` 中的 `headers` 和 `base_url` 即可，格式均为 OpenAI 兼容。

---

## 📖 API 接口说明

### 1. 聊天接口

- **URL**：`POST /api/chat`
- **请求体**：
```json
{
  "message": "用户问题",
  "history": []   // 可选，之前对话的消息数组
}
```
- **响应**：
```json
{
  "answer": "Agent 的回答",
  "history": [...]   // 更新后的完整对话历史
}
```

### 2. 工具管理

- **获取所有工具**：`GET /api/tools`
- **添加自定义工具**：`POST /api/tools`
  ```json
  {
    "name": "tool_name",
    "description": "工具描述",
    "parameters": { ... },   // JSON Schema
    "api_url": "https://...",
    "method": "GET" 或 "POST"
  }
  ```
- **删除自定义工具**：`DELETE /api/tools/{tool_name}`

---

## 🛠️ 自定义工具示例

### 示例：添加一个获取新闻头条的工具

1. 在“工具管理”面板填写：
   - **名称**：`get_news`
   - **描述**：获取最新新闻头条
   - **参数 Schema**：
     ```json
     {
       "type": "object",
       "properties": {
         "category": {
           "type": "string",
           "description": "新闻类别，如 tech、sports"
         }
       },
       "required": ["category"]
     }
     ```
   - **API URL**：`https://api.example.com/news`
   - **方法**：GET

2. 之后用户问“给我科技新闻”，Agent 会自动调用 `get_news(category="tech")` 并将结果显示在回答中。

### 注意事项

- 参数 Schema 必须符合 [JSON Schema 草案 07](https://json-schema.org/draft-07/) 规范
- GET 请求：参数会作为 Query String 附加到 URL
- POST 请求：参数会作为 JSON Body 发送
- 自定义工具 API 应返回可直接展示的文本或简单 JSON（系统会自动格式化）

---

## 🐛 常见问题

### 1. 城际路线查询返回空数据

- 该公开 API 可能对某些城市（如省级单位“新疆”）不支持，建议使用更具体的地名（如“乌鲁木齐”）
- 可查看终端打印的 `[DEBUG]` 日志，了解实际返回结构

### 2. OLLAMA 调用时工具调用失败

- 确保 OLLAMA 版本 ≥ 0.3.0
- 使用支持 function calling 的模型（`qwen2.5`、`llama3.1`、`mistral` 等）
- 检查 OLLAMA 服务是否正常运行：`curl http://localhost:11434/api/tags`

### 3. 前端报错 “Failed to fetch”

- 检查后端是否正常运行（`python app.py` 无报错）
- 查看浏览器控制台和 Flask 终端输出的错误信息

### 4. 自定义工具添加后未被调用

- 检查工具描述是否清晰，让 LLM 能理解何时使用
- 测试时明确提问：“请使用 [工具名] 查询 xxx”
