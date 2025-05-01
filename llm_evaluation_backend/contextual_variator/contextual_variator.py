import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import time
from llm_evaluation_backend.LLM_helper import call_LLM_api

def generate_paraphrase_prompt(sentence):
    return f"Paraphrase the following sentence with the same meaning but different wording:\n\n{sentence}"

def paraphrase_sentence(sentence, model, extra_instructions=None):
    prompt = generate_paraphrase_prompt(sentence)
    if extra_instructions:
        prompt += f"\n\n{extra_instructions}"
    response = call_LLM_api(model.api_key, model.base_url, model.name, prompt)
    # 这里假设返回就是字符串，如果是json可加解析
    return {
        "paraphrased_sentence": response,
        "method": "paraphrase_sentence"
    }

def create_paraphrased_data(
    username,
    model,
    dimension,
    num_samples,
    dataset_dir="dataset",
    extra_instructions=None
):
    # 读取原始数据
    test_path = os.path.join(dataset_dir, f"{dimension}_test.json")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test set file not found: {test_path}")
    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    if not isinstance(test_data, list):
        raise ValueError(f"{test_path} format error, should be a list.")

    # 随机抽样
    if num_samples > len(test_data):
        samples = test_data
    else:
        import random
        samples = random.sample(test_data, num_samples)

    new_data = []
    for item in samples:
        query = item.get("query", "")
        para_result = paraphrase_sentence(query, model, extra_instructions)
        new_item = {
            "query": para_result["paraphrased_sentence"],
            "created_by": username,
            "created_at": int(time.time()),
            "source_query": query,
            "dimension": dimension
        }
        new_data.append(new_item)
        # 追加到原数据
        test_data.append(new_item)

    # 写回json
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    return new_data
