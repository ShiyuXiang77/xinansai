import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
from llm_evaluation_backend.eval_core import Evaluator, Report

# 模型信息结构
class ModelInfo:
    def __init__(self, name, api_key, base_url):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url

# 模型管理
class ModelManager:
    def __init__(self, username):
        self.models = {}
        self.username = username
        # Store user model config in user_data directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(base_dir, "user_data")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir, exist_ok=True)
        self.config_path = os.path.join(user_data_dir, f"models_{self.username}.json")
        self.load_models()

    def load_models(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for name, info in data.items():
                    self.models[name] = ModelInfo(
                        name, info["api_key"], info["base_url"]
                    )
            except Exception as e:
                print(f"加载模型配置失败: {e}")

    def save_models(self):
        try:
            data = {
                name: {
                    "api_key": model.api_key,
                    "base_url": model.base_url
                }
                for name, model in self.models.items()
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存模型配置失败: {e}")

    def add_model(self, name, api_key, base_url):
        self.models[name] = ModelInfo(name, api_key, base_url)
        self.save_models()

    def list_models(self):
        return list(self.models.keys())

    def get_model(self, name):
        return self.models.get(name, None)

def main():
    username = input("Please enter your username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return
    model_manager = ModelManager(username)
    print("=== LLM Evaluation System CLI ===")
    while True:
        print("\nSelect an action:")
        print("1. Add a model")
        print("2. List models")
        print("3. Create evaluation task")
        print("0. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            name = input("Model name: ").strip()
            api_key = input("API Key: ").strip()
            base_url = input("Base URL: ").strip()
            model_manager.add_model(name, api_key, base_url)
            print(f"Model {name} added.")
        elif choice == "2":
            models = model_manager.list_models()
            if not models:
                print("No models added yet.")
            else:
                print("Models:")
                for m in models:
                    print(f"- {m}")
        elif choice == "3":
            models = model_manager.list_models()
            if not models:
                print("Please add at least one model first.")
                continue
            print("Available models:", ", ".join(models))
            model_name = input("Enter the model name to evaluate: ").strip()
            if model_name not in models:
                print("Model does not exist.")
                continue
            dimensions = ["fairness", "honesty", "jailbreak", "privacy", "robustness", "safety"]
            print("Available evaluation dimensions:", ", ".join(dimensions))
            dim_input = input("Enter dimensions to evaluate (comma separated): ").strip()
            selected_dims = [d.strip() for d in dim_input.split(",") if d.strip() in dimensions]
            if not selected_dims:
                print("No valid dimension selected.")
                continue
            try:
                num_samples = int(input("Number of samples per dimension: ").strip())
                if num_samples <= 0:
                    raise ValueError
            except ValueError:
                print("Please enter a valid positive integer.")
                continue
            judge_models = model_manager.list_models()
            print("Available judge models:", ", ".join(judge_models))
            judge_model_name = input("Enter judge model name: ").strip()
            if judge_model_name not in judge_models:
                print("Judge model does not exist.")
                continue
            judge_model = model_manager.get_model(judge_model_name)
            model = model_manager.get_model(model_name)
            # Ensure dataset directory exists
            dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")
            if not os.path.exists(dataset_dir):
                os.makedirs(dataset_dir, exist_ok=True)
            # Ensure report path is absolute and writable
            report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_report.json")
            evaluator = Evaluator(model, judge_model, selected_dims, num_samples, dataset_dir=dataset_dir)
            results = evaluator.evaluate()
            report = Report(model_name, judge_model_name, results, output_path=report_path)
            report.save()
            print("\n=== Evaluation Results ===")
            for dim, stats in results.items():
                print(f"\nDimension: {dim}")
                print(f"  Correct: {stats['correct']}")
                print(f"  Incorrect: {stats['incorrect']}")
                print(f"  Accuracy: {stats['accuracy']}")
                print(f"  Error case: {stats['error_case']}")
            print("Evaluation finished.")
        elif choice == "0":
            print("Exit.")
            break
        else:
            print("Invalid option, please try again.")

if __name__ == "__main__":
    main()
