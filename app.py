import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app)

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "sk-uzdvurtsnnxxdrkyomuokdxqdxkojwpjbbzwcvkqjatqmmpw")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_MODEL = "Qwen/Qwen2.5-7B-Instruct"
WEATHER_API_KEY = "S8dydN8cELoZWA54O"


# ===================== 内置工具函数 =====================
def weather_query(city: str) -> str:
    url = f"https://api.seniverse.com/v3/weather/now.json?key={WEATHER_API_KEY}&location={city}&language=zh-Hans&unit=c"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            weather = data["results"][0]["now"]["text"]
            temp = data["results"][0]["now"]["temperature"]
            return f"{city}天气：{weather}，气温 {temp}°C"
        return f"天气查询失败，状态码：{resp.status_code}"
    except Exception as e:
        return f"天气查询出错：{str(e)}"


def ip_details(ip: str) -> str:
    url = "https://api.pearktrue.cn/api/ip/details/"
    try:
        resp = requests.get(url, params={"ip": ip}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200 and isinstance(data.get("data"), dict):
                d = data["data"]
                return f"IP {ip} 归属：{d.get('country', '')}{d.get('region', '')}{d.get('city', '')}，经纬度：{d.get('lat', '')},{d.get('lon', '')}"
            return f"查询失败：{data.get('msg', '未知错误')}"
        return f"HTTP {resp.status_code}"
    except Exception as e:
        return f"IP查询出错：{str(e)}"


def answers_book(question: str) -> str:
    url = "https://api.pearktrue.cn/api/answersbook/"
    try:
        resp = requests.get(url, params={"question": question}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                title = data.get("title_zh", "")
                desc = data.get("description_zh", "")
                return f"答案：{title}\n解读：{desc}"
            return f"查询失败：{data.get('msg', '未知错误')}"
        return f"HTTP {resp.status_code}"
    except Exception as e:
        return f"答案之书出错：{str(e)}"


def city_travel_routes(from_city: str, to_city: str) -> str:
    url = "https://api.pearktrue.cn/api/citytravelroutes/"
    try:
        resp = requests.get(url, params={"from": from_city, "to": to_city}, timeout=10)
        print(f"[DEBUG] 城际路线 API 响应状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"[DEBUG] 完整返回数据: {data}")  # 打印到控制台便于调试
            if data.get("code") == 200:
                # 检查必要字段是否存在且非空
                corese = data.get('corese', '').strip()
                distance = data.get('distance', '').strip()
                time = data.get('time', '').strip()
                fuelcosts = data.get('fuelcosts', '').strip()
                bridgetoll = data.get('bridgetoll', '').strip()
                totalcost = data.get('totalcost', '').strip()
                roadconditions = data.get('roadconditions', '').strip()

                if not corese and not distance and not time:
                    return f"查询成功但未返回路线详情（可能该路线暂不支持）。原始数据：{data}"

                result = f"{from_city} → {to_city}\n"
                if corese:
                    result += f"路线：{corese}\n"
                if distance:
                    result += f"距离：{distance}\n"
                if time:
                    result += f"耗时：{time}\n"
                if fuelcosts:
                    result += f"油费：{fuelcosts}\n"
                if bridgetoll:
                    result += f"过路费：{bridgetoll}\n"
                if totalcost:
                    result += f"总费用：{totalcost}\n"
                if roadconditions:
                    result += f"路况：{roadconditions}\n"
                return result.strip()
            else:
                return f"查询失败：{data.get('msg', '未知错误')}（code={data.get('code')}）"
        else:
            return f"API 请求失败，HTTP {resp.status_code}"
    except Exception as e:
        return f"路线查询出错：{str(e)}"


BUILTIN_TOOLS = {
    "weather_query": weather_query,
    "ip_details": ip_details,
    "answers_book": answers_book,
    "city_travel_routes": city_travel_routes,
}

BUILTIN_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "weather_query",
            "description": "查询指定城市的实时天气状况和气温",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名称"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ip_details",
            "description": "根据IP地址查询归属地、国家、城市、经纬度",
            "parameters": {
                "type": "object",
                "properties": {"ip": {"type": "string", "description": "IP地址"}},
                "required": ["ip"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "answers_book",
            "description": "答案之书：根据用户的问题给出一个启发性的答案",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string", "description": "用户的问题"}},
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "city_travel_routes",
            "description": "查询两个城市之间的出行路线、距离、耗时、油费、过路费、总费用和路况",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_city": {"type": "string", "description": "出发城市"},
                    "to_city": {"type": "string", "description": "目的城市"}
                },
                "required": ["from_city", "to_city"]
            }
        }
    }
]

# ===================== 自定义工具存储 =====================
custom_tools = []


def add_custom_tool(tool_def: dict):
    custom_tools.append(tool_def)


def remove_custom_tool(tool_name: str):
    global custom_tools
    custom_tools = [t for t in custom_tools if t["name"] != tool_name]


def get_all_tools_schema():
    schemas = BUILTIN_TOOLS_SCHEMA.copy()
    for tool in custom_tools:
        schemas.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        })
    return schemas


def call_custom_tool(tool_name: str, arguments: dict) -> str:
    tool = next((t for t in custom_tools if t["name"] == tool_name), None)
    if not tool:
        return f"错误：未找到自定义工具 {tool_name}"
    url = tool["api_url"]
    method = tool.get("method", "GET").upper()
    try:
        if method == "GET":
            resp = requests.get(url, params=arguments, timeout=15)
        elif method == "POST":
            resp = requests.post(url, json=arguments, timeout=15)
        else:
            return f"不支持的请求方法: {method}"
        if resp.status_code == 200:
            try:
                data = resp.json()
                return json.dumps(data, ensure_ascii=False, indent=2)
            except:
                return resp.text
        else:
            return f"API 返回状态码 {resp.status_code}，内容：{resp.text[:200]}"
    except Exception as e:
        return f"调用自定义工具失败：{str(e)}"


# ===================== LLM 调用 =====================
def chat_completion(messages: List[Dict], tools_schema: List[Dict]) -> Dict:
    headers = {"Authorization": f"Bearer {SILICONFLOW_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": SILICONFLOW_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
        "tools": tools_schema,
        "tool_choice": "auto"
    }
    resp = requests.post(f"{SILICONFLOW_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"硅基流动 API 错误: {resp.status_code} - {resp.text}")
    return resp.json()


# ===================== Agent 执行器 =====================
def run_agent(user_input: str, conversation_history: List[Dict] = None) -> Dict:
    if conversation_history is None:
        messages = [{"role": "user", "content": user_input}]
    else:
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": user_input})

    max_iterations = 5
    for _ in range(max_iterations):
        tools_schema = get_all_tools_schema()
        resp = chat_completion(messages, tools_schema)
        assistant_msg = resp["choices"][0]["message"]
        messages.append(assistant_msg)

        tool_calls = assistant_msg.get("tool_calls")
        if not tool_calls:
            return {"answer": assistant_msg.get("content", ""), "history": messages}

        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            raw_args = tool_call["function"]["arguments"]
            # 解析参数
            try:
                if isinstance(raw_args, dict):
                    arguments = raw_args
                else:
                    arguments = json.loads(raw_args)
            except json.JSONDecodeError as e:
                result = f"参数解析错误：{str(e)}，原始参数：{raw_args}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })
                continue

            if func_name in BUILTIN_TOOLS:
                try:
                    result = BUILTIN_TOOLS[func_name](**arguments)
                except Exception as e:
                    result = f"工具 {func_name} 执行出错：{str(e)}"
            else:
                result = call_custom_tool(func_name, arguments)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result
            })

    return {"answer": "达到最大迭代次数，未获得最终答案", "history": messages}


# ===================== Flask 路由 =====================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    history = data.get("history", [])
    if not user_input:
        return jsonify({"error": "消息不能为空"}), 400
    try:
        result = run_agent(user_input, history)
        return jsonify({"answer": result["answer"], "history": result["history"]})
    except Exception as e:
        app.logger.exception("Agent 执行失败")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools", methods=["GET"])
def list_tools():
    builtin_names = [t["function"]["name"] for t in BUILTIN_TOOLS_SCHEMA]
    custom_list = [{"name": t["name"], "description": t["description"], "parameters": t["parameters"]} for t in
                   custom_tools]
    return jsonify({"builtin": builtin_names, "custom": custom_list})


@app.route("/api/tools", methods=["POST"])
def add_tool():
    tool = request.get_json()
    required_fields = ["name", "description", "parameters", "api_url"]
    if not all(f in tool for f in required_fields):
        return jsonify({"error": "缺少必填字段"}), 400
    if tool["name"] in BUILTIN_TOOLS:
        return jsonify({"error": "工具名称与内置工具冲突"}), 400
    if any(t["name"] == tool["name"] for t in custom_tools):
        return jsonify({"error": "工具名称已存在"}), 400
    tool.setdefault("method", "GET")
    add_custom_tool(tool)
    return jsonify({"status": "ok", "tool": tool})


@app.route("/api/tools/<tool_name>", methods=["DELETE"])
def delete_tool(tool_name):
    if tool_name in BUILTIN_TOOLS:
        return jsonify({"error": "不能删除内置工具"}), 400
    remove_custom_tool(tool_name)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)