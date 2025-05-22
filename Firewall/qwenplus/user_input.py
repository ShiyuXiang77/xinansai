import json
import shutil
import pandas as pd
from vectorstore import VectorStore
from config import Config
from embedding import get_embedding_model
from prompts import prompt_user,second_judge,LLM_judge
from utils import filter_json
import re
import os
from openai import OpenAI
threshold=0.6

#input,前端给
user_input=""
all_result={}
all_result["user_input"]=user_input
def run_deepseek(prompt: str) -> str:
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="06af1a7b94a042c2b43b7f036e54f4fb.KjbhEF4evnFzQdKQ",
        base_url="https://open.bigmodel.cn/api/paas/v4/",
    )
    completion = client.chat.completions.create(
        model="glm-4-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return completion.choices[0].message.content

#提取用户本质
formatted_prompt =prompt_user.format(prompt=user_input)
result = run_deepseek(formatted_prompt)
parsed_result = json.loads(result )
user_essence=parsed_result.get("pattern", "")
all_result["user_essence"]=user_essence

#本质数据库检索
vectorstore = VectorStore()
k=5
results = vectorstore.similarity_search(user_essence,k)
similar_prompts = []
similar_patterns = []
scores = []
for result, score in results:
    similar_patterns.append(result.page_content)
    similar_prompt = result.metadata.get("prompt", "")
    similar_prompts.append(similar_prompt)
    scores.append(score)
# 更新数据项
all_result['scores'] = scores
all_result['similar_pattern'] = similar_patterns
all_result['similar_prompt'] = similar_prompts

#细粒度判断
if scores[0] > threshold:
    formatted_prompt = LLM_judge.format(prompt_user=user_input, query_essence=user_essence)
    result = run_deepseek(formatted_prompt)
    parsed_result = json.loads(result)
    is_harmful = parsed_result["is_harmful"] if "is_harmful" in parsed_result else False
    reasoning = parsed_result["reasoning"] if "reasoning" in parsed_result else ""
    all_result['second result'] = result
    all_result['judge'] = True
    all_result["is harmful"] = is_harmful
    all_result["reasoning"] = reasoning
    all_result["second judge"] = False
else:
    # 遍历 similar_scores，将大于阈值的 corresponding similar_prompt 和 similar_pattern 置为空
    for a in range(len(scores)):
        if scores[a] > threshold:
            similar_prompts[a] = ""
            similar_patterns[a] = ""
    formatted_prompt = second_judge.format(prompt_user=user_input, query_essence=user_essence, p1=similar_prompts[0],
                                           e1=similar_patterns[0], p2=similar_prompts[1], e2=similar_patterns[1],
                                           p3=similar_prompts[2], e3=similar_patterns[2], p4=similar_prompts[3],
                                           e4=similar_patterns[3], p5=similar_prompts[4], e5=similar_patterns[4])
    result = run_deepseek(formatted_prompt)
    parsed_result = json.loads(result)
    is_harmful = parsed_result["is_harmful"] if "is_harmful" in parsed_result else False
    reasoning = parsed_result["reasoning"] if "reasoning" in parsed_result else ""
    all_result['second result'] = result
    all_result['judge'] = True
    all_result["is harmful"] = is_harmful
    all_result["reasoning"] = reasoning
    all_result["second judge"] = True

# 前端展示返回is_harmful和reasoning即可




