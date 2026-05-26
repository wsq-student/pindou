import os
import base64
import requests
from dotenv import load_dotenv

# 加载 .env 中的环境变量
load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY")

URL = "https://api.deepseek.com/v1/chat/completions"


def encode_image(image_path):
    """将本地图片转为 Base64 字符串"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def recognize_image(image_path, prompt="请识别图片中的内容，用中文回答。"):
    """调用 DeepSeek 视觉模型识别图片"""
    # 自动判断 MIME 类型
    if image_path.lower().endswith(".png"):
        mime = "image/png"
    else:
        mime = "image/jpeg"

    base64_img = encode_image(image_path)
    image_url = f"data:{mime};base64,{base64_img}"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",  # 支持视觉的模型
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }

    resp = requests.post(URL, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        print(f"请求失败，状态码：{resp.status_code}")
        print(f"响应内容：{resp.text}")
        resp.raise_for_status()

    result = resp.json()
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # 替换为你的图片路径
    image_file = "test.png"

    # 可选：自定义提示词
    question = "提取图片中所有的字母+数字组合及其对应的数值，用JSON格式输出。"

    try:
        answer = recognize_image(image_file, question)
        print("\n识别结果：")
        print(answer)
    except Exception as e:
        print(f"调用出错：{e}")