import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import openai

def call_LLM_api(api_key, base_url, model_name, prompt):
    """
    使用 OpenAI SDK 调用模型，返回结果
    :param api_key: str, OpenAI API Key
    :param base_url: str, OpenAI API Base URL
    :param model_name: str, OpenAI Model Name (如 'gpt-3.5-turbo' 或 'gpt-4')
    :param prompt: str, 用户输入的 prompt
    :return: str, 返回模型输出内容
    """
    # 初始化 OpenAI 客户端参数
    openai.api_key = api_key
    openai.base_url = base_url

    # 调用 Chat Completion 接口
    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"调用 OpenAI API 出错: {str(e)}"
