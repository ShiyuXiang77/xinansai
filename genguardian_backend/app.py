import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import calendar
from datetime import datetime
# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import json
from flask import Flask, jsonify, request, send_from_directory, redirect, url_for
from flask_cors import CORS
from eval_core import Evaluator, Report

app = Flask(__name__, 
    static_folder=None  # 禁用默认的static文件夹
)
CORS(app)  # 启用CORS支持

# 配置日志
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('应用启动')

# 添加错误处理
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({
        "error": "页面不存在",
        "code": 404,
        "available_pages": list_html_pages()
    }), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        "error": "服务器内部错误",
        "code": 500
    }), 500

# API路由
@app.route('/api/monthly_task_stats', methods=['GET'])
def get_monthly_task_stats():
    """
    获取指定月份的每日任务统计数据
    """
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(base_dir, "user_data")
        reports_dir = os.path.join(user_data_dir, "reports")
        
        if not os.path.exists(reports_dir):
            app.logger.error(f"Reports directory not found: {reports_dir}")
            return jsonify({"error": "No reports found."}), 404
            
        # 获取该月的所有天数
        _, days_in_month = calendar.monthrange(year, month)
        
        # 初始化每日数据
        daily_stats = {str(day): {"pass": 0, "improve": 0} for day in range(1, days_in_month + 1)}
        
        # 构建月份字符串 (格式: YYYY-MM)
        month_str = f"{year}-{month:02d}"
        month_dir = os.path.join(reports_dir, month_str)
        
        # 如果该月份的目录不存在，返回空数据
        if not os.path.exists(month_dir):
            app.logger.warning(f"Month directory not found: {month_dir}")
            result = {
                "dates": list(range(1, days_in_month + 1)),
                "pass": [0] * days_in_month,
                "improve": [0] * days_in_month
            }
            return jsonify(result)
            
        # 获取该月的任务概览文件
        tasks_file = os.path.join(month_dir, "tasks.json")
        if not os.path.exists(tasks_file):
            app.logger.warning(f"Tasks file not found: {tasks_file}")
            result = {
                "dates": list(range(1, days_in_month + 1)),
                "pass": [0] * days_in_month,
                "improve": [0] * days_in_month
            }
            return jsonify(result)
            
        # 读取任务概览
        with open(tasks_file, "r", encoding="utf-8") as f:
            month_tasks = json.load(f)
                    
        # 处理每个任务
        for task in month_tasks.get("tasks", []):
                # 解析时间戳
            report_time = datetime.fromtimestamp(task["timestamp"])
            day = str(report_time.day)
                    
            # 判断是否通过（平均准确率>=80%）
            accuracy = task.get("accuracy", 0)
            if accuracy >= 0.8:
                daily_stats[day]["pass"] += 1
            else:
                daily_stats[day]["improve"] += 1
        
        # 转换为前端所需的格式
        result = {
            "dates": list(range(1, days_in_month + 1)),
            "pass": [daily_stats[str(day)]["pass"] for day in range(1, days_in_month + 1)],
            "improve": [daily_stats[str(day)]["improve"] for day in range(1, days_in_month + 1)]
        }
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in get_monthly_task_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/monthly_model_stats', methods=['GET'])
def get_monthly_model_stats():
    """
    获取指定月份的每日模型统计数据
    """
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(base_dir, "user_data")
        reports_dir = os.path.join(user_data_dir, "reports")
        
        if not os.path.exists(reports_dir):
            app.logger.error(f"Reports directory not found: {reports_dir}")
            return jsonify({"error": "No reports found."}), 404
            
        # 获取该月的所有天数
        _, days_in_month = calendar.monthrange(year, month)
        
        # 初始化每日数据
        daily_stats = {str(day): {"pass": set(), "improve": set()} for day in range(1, days_in_month + 1)}
        
        # 构建月份字符串 (格式: YYYY-MM)
        month_str = f"{year}-{month:02d}"
        month_dir = os.path.join(reports_dir, month_str)
        
        # 如果该月份的目录不存在，返回空数据
        if not os.path.exists(month_dir):
            app.logger.warning(f"Month directory not found: {month_dir}")
            result = {
                "dates": list(range(1, days_in_month + 1)),
                "pass": [0] * days_in_month,
                "improve": [0] * days_in_month
            }
            return jsonify(result)
            
        # 获取该月的任务概览文件
        tasks_file = os.path.join(month_dir, "tasks.json")
        if not os.path.exists(tasks_file):
            app.logger.warning(f"Tasks file not found: {tasks_file}")
            result = {
                "dates": list(range(1, days_in_month + 1)),
                "pass": [0] * days_in_month,
                "improve": [0] * days_in_month
            }
            return jsonify(result)
            
        # 读取任务概览
        with open(tasks_file, "r", encoding="utf-8") as f:
            month_tasks = json.load(f)
                    
        # 处理每个任务
        for task in month_tasks.get("tasks", []):
                # 解析时间戳
            report_time = datetime.fromtimestamp(task["timestamp"])
            day = str(report_time.day)
                    
            # 判断每个模型是否通过（使用任务中记录的整体准确率）
            accuracy = task.get("accuracy", 0)
            models = task.get("models", [])
            
            if accuracy >= 0.8:
                for model in models:
                    daily_stats[day]["pass"].add(model)
            else:
                for model in models:
                    daily_stats[day]["improve"].add(model)
        
        # 转换为前端所需的格式
        result = {
            "dates": list(range(1, days_in_month + 1)),
            "pass": [len(daily_stats[str(day)]["pass"]) for day in range(1, days_in_month + 1)],
            "improve": [len(daily_stats[str(day)]["improve"]) for day in range(1, days_in_month + 1)]
        }
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in get_monthly_model_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 页面路由
@app.route('/')
def root():
    return redirect(url_for('serve_html', filename='index'))

@app.route('/<path:filename>.html')
def serve_html(filename):
    # 检查文件是否存在
    file_path = os.path.join(parent_dir, f'{filename}.html')
    if os.path.exists(file_path):
        return send_from_directory(parent_dir, f'{filename}.html')
    else:
        return "页面不存在", 404

# 处理static路径下的文件
@app.route('/static/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(parent_dir, 'static')
    try:
        if not os.path.exists(os.path.join(static_dir, filename)):
            app.logger.error(f"Static file not found: {filename}")
            return "文件不存在", 404
        response = send_from_directory(static_dir, filename)
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        app.logger.info(f"Serving static file: {filename}")
        return response
    except Exception as e:
        app.logger.error(f"Error serving static file {filename}: {str(e)}")
        return str(e), 500

# 处理assets路径下的文件
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.join(parent_dir, 'assets')
    if not os.path.exists(os.path.join(assets_dir, filename)):
        return "文件不存在", 404
    response = send_from_directory(assets_dir, filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

# 处理trustgen路径下的文件
@app.route('/trustgen/<path:filename>')
def serve_trustgen(filename):
    trustgen_dir = os.path.join(parent_dir, 'trustgen')
    if not os.path.exists(os.path.join(trustgen_dir, filename)):
        return "文件不存在", 404
    response = send_from_directory(trustgen_dir, filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

# API路由
@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        reports_dir = os.path.dirname(os.path.abspath(__file__))
        report_files = [f for f in os.listdir(reports_dir) if f.endswith('_report.json')]
        reports = []
        
        for rf in report_files:
            with open(os.path.join(reports_dir, rf), 'r', encoding='utf-8') as f:
                report = json.load(f)
                # 添加时间戳（如果没有）
                if 'timestamp' not in report:
                    report['timestamp'] = datetime.fromtimestamp(
                        os.path.getctime(os.path.join(reports_dir, rf))
                    ).strftime('%Y/%m/%d')
                reports.append(report)
        
        # 按时间戳降序排序
        reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify(reports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly-tasks', methods=['GET'])
def get_monthly_tasks():
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(base_dir, "user_data")
        reports_dir = os.path.join(user_data_dir, "reports")
        
        # 构建月份字符串 (格式: YYYY-MM)
        month_str = f"{year}-{month:02d}"
        month_dir = os.path.join(reports_dir, month_str)
        
        if not os.path.exists(month_dir):
            app.logger.error(f"Month directory not found: {month_dir}")
            return jsonify([])

        # 获取该月的任务概览文件
        tasks_file = os.path.join(month_dir, "tasks.json")
        if not os.path.exists(tasks_file):
            app.logger.error(f"Tasks file not found: {tasks_file}")
            return jsonify([])

        # 读取任务概览
        with open(tasks_file, "r", encoding="utf-8") as f:
            month_tasks = json.load(f)
            
        # 提取任务列表并添加前端需要的格式
        tasks = []
        for task in month_tasks.get("tasks", []):
            task_data = {
                'task_id': task.get('task_id', ''),
                'timestamp': task.get('timestamp', 0),
                'model_name': ', '.join(task.get('models', ['未知'])),
                'dimensions': task.get('dimensions', []),
                'accuracy': task.get('accuracy', 0),
                'status': '评估完成' if task.get('accuracy', 0) >= 0.8 else '需要改进'
            }
            tasks.append(task_data)
        
        return jsonify(tasks)
    except Exception as e:
        app.logger.error(f"Error in get_monthly_tasks: {str(e)}")
        return jsonify([])

# 获取单个报告详情
@app.route('/api/reports/<task_id>', methods=['GET'])
def get_report_detail(task_id):
    try:
        # 从task_id中提取年月信息 (格式: task_YYYY_MM_XXX)
        parts = task_id.split('_')
        if len(parts) >= 3:
            year = parts[1]
            month = parts[2]
            month_str = f"{year}-{month}"
        else:
            # 如果无法从task_id中提取月份信息，遍历所有月份目录查找
            base_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(base_dir, "user_data")
            reports_dir = os.path.join(user_data_dir, "reports")
            
            for month_dir in os.listdir(reports_dir):
                if os.path.isdir(os.path.join(reports_dir, month_dir)):
                    file_path = os.path.join(reports_dir, month_dir, f"{task_id}.json")
                    if os.path.exists(file_path):
                        month_str = month_dir
                        break
            else:
                return jsonify({"error": "报告不存在"}), 404
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(base_dir, "user_data")
        reports_dir = os.path.join(user_data_dir, "reports")
        
        # 构建文件路径
        file_path = os.path.join(reports_dir, month_str, f"{task_id}.json")
        
        if not os.path.exists(file_path):
            return jsonify({"error": "报告不存在"}), 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
            return jsonify(report)
            
    except Exception as e:
        app.logger.error(f"Error getting report detail: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 列出所有可用的HTML页面
def list_html_pages():
    html_files = []
    for file in os.listdir(parent_dir):
        if file.endswith('.html'):
            html_files.append(file[:-5])  # 移除.html后缀
    return html_files

# 创建必要的目录
def ensure_directories():
    directories = [
        os.path.join(parent_dir, 'assets'),
        os.path.join(parent_dir, 'trustgen'),
        os.path.join(parent_dir, 'static'),
        os.path.join(parent_dir, 'trustgen/css'),
        os.path.join(parent_dir, 'assets/css'),
        os.path.join(parent_dir, 'assets/js'),
        os.path.join(parent_dir, 'assets/images'),
        os.path.join(parent_dir, 'assets/vendor'),
        os.path.join(parent_dir, 'static/css'),
        os.path.join(parent_dir, 'static/js')
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 在应用启动时创建目录
ensure_directories()

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

def organize_reports_by_month():
    """将现有的报告文件按月份整理到相应文件夹中"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    
    if not os.path.exists(reports_dir):
        print("Reports directory not found")
        return
    
    # 获取所有json文件
    report_files = [f for f in os.listdir(reports_dir) if f.endswith('.json') and os.path.isfile(os.path.join(reports_dir, f))]
    
    for rf in report_files:
        file_path = os.path.join(reports_dir, rf)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # 跳过已经是tasks.json的文件
            if "tasks" in report:
                continue
                
            # 获取时间戳
            timestamp = report.get('timestamp', 0)
            if timestamp > 0:
                report_date = datetime.fromtimestamp(timestamp)
                month_str = f"{report_date.year}-{report_date.month:02d}"
                
                # 创建月份目录
                month_dir = os.path.join(reports_dir, month_str)
                os.makedirs(month_dir, exist_ok=True)
            
                # 创建任务ID (如果没有)
                if "task_id" not in report:
                    task_id = f"task_{report_date.year}_{report_date.month:02d}_{report_date.day:02d}_{report_date.hour:02d}{report_date.minute:02d}"
                    report["task_id"] = task_id
                
                # 将报告移动到月份目录
                new_path = os.path.join(month_dir, f"{report['task_id']}.json")
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            
                    # 更新或创建该月的tasks.json
                    tasks_file = os.path.join(month_dir, "tasks.json")
                if os.path.exists(tasks_file):
                    with open(tasks_file, 'r', encoding='utf-8') as f:
                        month_tasks = json.load(f)
                else:
                    month_tasks = {"month": month_str, "tasks": []}
                
                # 添加任务到tasks.json
                task_data = {
                    "task_id": report["task_id"],
                    "timestamp": timestamp,
                    "models": [model_name for model_name in report.get("results", {}).keys()],
                    "judge_model": report.get("judge_model", "未知"),
                    "dimensions": report.get("dimensions", []),
                    "status": "completed",
                    "username": report.get("username", "未知")
                }
                
                # 计算平均准确率
                results = report.get("results", {})
                total_accuracy = 0
                count = 0
                
                for model_results in results.values():
                    for dim_stats in model_results.values():
                        if "accuracy" in dim_stats:
                            accuracy = float(str(dim_stats["accuracy"]).rstrip("%")) / 100
                            total_accuracy += accuracy
                            count += 1
                
                if count > 0:
                    task_data["accuracy"] = total_accuracy / count
                
                # 检查是否已存在相同task_id的任务
                task_exists = False
                for i, task in enumerate(month_tasks["tasks"]):
                    if task.get("task_id") == task_data["task_id"]:
                        month_tasks["tasks"][i] = task_data
                        task_exists = True
                        break
                
                if not task_exists:
                    month_tasks["tasks"].append(task_data)
                
                # 保存tasks.json
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(month_tasks, f, indent=2, ensure_ascii=False)
                
                print(f"Processed {rf} -> {month_str}/{report['task_id']}.json")
                
            else:
                print(f"Skipping {rf} - no timestamp")
            
        except Exception as e:
            print(f"Error processing {rf}: {str(e)}")

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
    organize_reports_by_month()
    setup_logging()
    print("可用页面:")
    pages = list_html_pages()
    for page in pages:
        print(f"http://localhost:5000/{page}.html")
    app.logger.info(f"发现 {len(pages)} 个可用页面")
    app.run(host='0.0.0.0', port=5000)
