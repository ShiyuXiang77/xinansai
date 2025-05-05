import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from genguardian_backend.eval_core import Evaluator, Report
from genguardian_backend.app import ModelManager, ModelInfo
from fastapi.staticfiles import StaticFiles
from genguardian_backend.contextual_variator.contextual_variator import create_paraphrased_data
import time
from datetime import datetime, timedelta
import calendar

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.dirname(os.path.abspath(__file__))), name="static")

class AddModelRequest(BaseModel):
    username: str
    model_name: str
    api_key: str
    base_url: str

class EvalRequest(BaseModel):
    username: str
    model_names: list  # 支持多模型
    judge_model_name: str
    dimensions: list
    num_samples: int

def progress_evaluate(username, model_names, judge_model_name, dimensions, num_samples):
    # ModelManager and model loading
    model_manager = ModelManager(username)
    judge_model = model_manager.get_model(judge_model_name)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    
    # 获取当前日期信息
    now = datetime.now()
    month_str = f"{now.year}-{now.month:02d}"
    month_dir = os.path.join(reports_dir, month_str)
    
    # 确保月份目录存在
    if not os.path.exists(month_dir):
        os.makedirs(month_dir, exist_ok=True)
    
    timestamp = int(time.time())
    task_id = f"task_{now.year}_{now.month:02d}_{now.day:02d}_{now.hour:02d}{now.minute:02d}"
    report_path = os.path.join(month_dir, f"{task_id}.json")
    
    dataset_dir = os.path.join(base_dir, "dataset")
    all_results = {}
    total_models = len(model_names)
    
    for m_idx, model_name in enumerate(model_names):
        model = model_manager.get_model(model_name)
        if not model:
            yield f"data: {json.dumps({'progress': 0, 'model': model_name, 'error': 'Model not found'})}\n\n"
            continue
        results = {}
        total_steps = len(dimensions)
        for i, dim in enumerate(dimensions):
            # Evaluate one dimension at a time, yield progress
            partial_evaluator = Evaluator(model, judge_model, [dim], num_samples, dataset_dir=dataset_dir)
            dim_result = partial_evaluator.evaluate()
            results.update(dim_result)
            percent = int(((m_idx + i / total_steps) / total_models) * 100)
            yield f"data: {json.dumps({'progress': percent, 'current_model': model_name, 'current_dimension': dim, 'result': dim_result})}\n\n"
        all_results[model_name] = results
    
    # 创建报告
    report = {
        "task_id": task_id,
        "timestamp": timestamp,
        "username": username,
        "judge_model": judge_model_name,
        "dimensions": dimensions,
        "results": all_results
    }
    
    # 保存报告
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 更新或创建该月的tasks.json
    tasks_file = os.path.join(month_dir, "tasks.json")
    if os.path.exists(tasks_file):
        with open(tasks_file, 'r', encoding='utf-8') as f:
            month_tasks = json.load(f)
    else:
        month_tasks = {"month": month_str, "tasks": []}
    
    # 计算平均准确率
    total_accuracy = 0
    count = 0
    for model_results in all_results.values():
        for dim_stats in model_results.values():
            if "accuracy" in dim_stats:
                accuracy = float(str(dim_stats["accuracy"]).rstrip("%")) / 100
                total_accuracy += accuracy
                count += 1
    
    avg_accuracy = total_accuracy / count if count > 0 else 0
    
    # 添加任务到tasks.json
    task_data = {
        "task_id": task_id,
        "timestamp": timestamp,
        "models": model_names,
        "judge_model": judge_model_name,
        "dimensions": dimensions,
        "status": "completed",
        "username": username,
        "accuracy": avg_accuracy
    }
    
    # 检查是否已存在相同task_id的任务
    task_exists = False
    for i, task in enumerate(month_tasks["tasks"]):
        if task.get("task_id") == task_id:
            month_tasks["tasks"][i] = task_data
            task_exists = True
            break
    
    if not task_exists:
        month_tasks["tasks"].append(task_data)
    
    # 保存tasks.json
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(month_tasks, f, indent=2, ensure_ascii=False)
    
    yield f"data: {json.dumps({'progress': 100, 'status': 'done', 'report_path': report_path, 'timestamp': timestamp})}\n\n"

@app.post("/api/evaluate")
def api_evaluate(req: EvalRequest):
    def event_stream():
        yield from progress_evaluate(
            req.username,
            req.model_names,
            req.judge_model_name,
            req.dimensions,
            req.num_samples
        )
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/api/report")
def get_report(username: str = None, year: int = None, month: int = None, task_id: str = None):
    """
    获取报告，支持按月份和任务ID筛选
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    
    if not os.path.exists(reports_dir):
        return JSONResponse({"error": "No report found."}, status_code=404)
    
    # 如果指定了任务ID
    if task_id:
        # 尝试从任务ID中提取年月信息
        parts = task_id.split('_')
        if len(parts) >= 3:
            year_from_id = int(parts[1])
            month_from_id = int(parts[2])
            month_str = f"{year_from_id}-{month_from_id:02d}"
            month_dir = os.path.join(reports_dir, month_str)
            report_path = os.path.join(month_dir, f"{task_id}.json")
            
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    return JSONResponse(json.load(f))
        
        # 如果无法从ID中提取年月或文件不存在，遍历所有月份目录
        for month_dir in os.listdir(reports_dir):
            if os.path.isdir(os.path.join(reports_dir, month_dir)):
                report_path = os.path.join(reports_dir, month_dir, f"{task_id}.json")
                if os.path.exists(report_path):
                    with open(report_path, "r", encoding="utf-8") as f:
                        return JSONResponse(json.load(f))
        
        return JSONResponse({"error": f"Report not found for task ID: {task_id}"}, status_code=404)
    
    # 如果指定了年月
    if year and month:
        month_str = f"{year}-{month:02d}"
        month_dir = os.path.join(reports_dir, month_str)
        
        if not os.path.exists(month_dir):
            return JSONResponse({"error": f"No reports found for {month_str}"}, status_code=404)
        
        tasks_file = os.path.join(month_dir, "tasks.json")
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f:
                month_tasks = json.load(f)
                
                # 如果指定了用户，过滤该用户的任务
                if username:
                    tasks = [task for task in month_tasks.get("tasks", []) if task.get("username") == username]
                    if not tasks:
                        return JSONResponse({"error": f"No reports found for user {username} in {month_str}"}, status_code=404)
                    
                    # 获取该用户的最新任务
                    latest_task = sorted(tasks, key=lambda x: x.get("timestamp", 0), reverse=True)[0]
                    task_id = latest_task.get("task_id")
                    report_path = os.path.join(month_dir, f"{task_id}.json")
                    
                    if os.path.exists(report_path):
                        with open(report_path, "r", encoding="utf-8") as f:
                            return JSONResponse(json.load(f))
                else:
                    # 返回该月的最新任务
                    if month_tasks.get("tasks"):
                        latest_task = sorted(month_tasks.get("tasks", []), key=lambda x: x.get("timestamp", 0), reverse=True)[0]
                        task_id = latest_task.get("task_id")
                        report_path = os.path.join(month_dir, f"{task_id}.json")
                        
                        if os.path.exists(report_path):
                            with open(report_path, "r", encoding="utf-8") as f:
                                return JSONResponse(json.load(f))
                                
        return JSONResponse({"error": f"No reports found for {month_str}"}, status_code=404)
    
    # 如果只指定了用户名，寻找该用户最新的报告
    if username:
        # 寻找所有月份目录
        month_dirs = [d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))]
        
        # 按月份排序，最近的月份优先
        month_dirs.sort(reverse=True)
        
        for month_dir in month_dirs:
            month_path = os.path.join(reports_dir, month_dir)
            tasks_file = os.path.join(month_path, "tasks.json")
            
            if os.path.exists(tasks_file):
                with open(tasks_file, "r", encoding="utf-8") as f:
                    month_tasks = json.load(f)
                    
                # 过滤该用户的任务
                user_tasks = [task for task in month_tasks.get("tasks", []) if task.get("username") == username]
                
                if user_tasks:
                    # 获取该用户最新的任务
                    latest_task = sorted(user_tasks, key=lambda x: x.get("timestamp", 0), reverse=True)[0]
                    task_id = latest_task.get("task_id")
                    report_path = os.path.join(month_path, f"{task_id}.json")
                    
                    if os.path.exists(report_path):
                        with open(report_path, "r", encoding="utf-8") as f:
                            return JSONResponse(json.load(f))
        
            return JSONResponse({"error": f"No report found for user {username}."}, status_code=404)
    
    # 如果没有任何参数，返回最新的报告
    month_dirs = [d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))]
    month_dirs.sort(reverse=True)
    
    for month_dir in month_dirs:
        month_path = os.path.join(reports_dir, month_dir)
        tasks_file = os.path.join(month_path, "tasks.json")
        
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f:
                month_tasks = json.load(f)
                
            if month_tasks.get("tasks"):
                latest_task = sorted(month_tasks.get("tasks", []), key=lambda x: x.get("timestamp", 0), reverse=True)[0]
                task_id = latest_task.get("task_id")
                report_path = os.path.join(month_path, f"{task_id}.json")
                
                if os.path.exists(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
                        return JSONResponse(json.load(f))
    
    return JSONResponse({"error": "No report found."}, status_code=404)

@app.get("/api/reports")
def get_reports(username: str = None, year: int = None, month: int = None):
    """
    获取报告列表，支持按用户名和月份筛选
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    
    if not os.path.exists(reports_dir):
        return JSONResponse({"error": "No report found."}, status_code=404)
    
    all_reports = []
    
    # 如果指定了年月
    if year and month:
        month_str = f"{year}-{month:02d}"
        month_dir = os.path.join(reports_dir, month_str)
        
        if not os.path.exists(month_dir):
            return JSONResponse({"reports": [], "count": 0})
        
        tasks_file = os.path.join(month_dir, "tasks.json")
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f:
                month_tasks = json.load(f)
                tasks = month_tasks.get("tasks", [])
                
                # 如果指定了用户名，过滤该用户的任务
                if username:
                    tasks = [task for task in tasks if task.get("username") == username]
                
                for task in tasks:
                    task_id = task.get("task_id")
                    report_path = os.path.join(month_dir, f"{task_id}.json")
                    
                    if os.path.exists(report_path):
                        with open(report_path, "r", encoding="utf-8") as f:
                            report = json.load(f)
                            all_reports.append(report)
        
        return JSONResponse({"reports": all_reports, "count": len(all_reports)})
    
    # 如果没有指定年月，遍历所有月份目录
    month_dirs = [d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))]
    
    for month_dir in month_dirs:
        month_path = os.path.join(reports_dir, month_dir)
        tasks_file = os.path.join(month_path, "tasks.json")
        
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f:
                month_tasks = json.load(f)
                tasks = month_tasks.get("tasks", [])
                
                # 如果指定了用户名，过滤该用户的任务
                if username:
                    tasks = [task for task in tasks if task.get("username") == username]
                
                for task in tasks:
                    task_id = task.get("task_id")
                    report_path = os.path.join(month_path, f"{task_id}.json")
                    
                    if os.path.exists(report_path):
                        with open(report_path, "r", encoding="utf-8") as f:
                            report = json.load(f)
                            all_reports.append(report)
    
    return JSONResponse({"reports": all_reports, "count": len(all_reports)})

@app.post("/api/add_model")
def add_model(req: AddModelRequest):
    model_manager = ModelManager(req.username)
    if req.model_name in model_manager.list_models():
        return JSONResponse({"status": "error", "message": f"Model {req.model_name} already exists for user {req.username}."}, status_code=400)
    model_manager.add_model(req.model_name, req.api_key, req.base_url)
    return {"status": "success", "message": f"Model {req.model_name} added for user {req.username}."}

@app.get("/api/list_models")
def list_models(username: str):
    model_manager = ModelManager(username)
    return {"models": model_manager.list_models()}

from pydantic import BaseModel

class ParaphraseRequest(BaseModel):
    username: str
    model_name: str
    dimension: str
    num_samples: int
    extra_instructions: str = None

@app.post("/api/paraphrase_data")
def paraphrase_data(req: ParaphraseRequest):
    model_manager = ModelManager(req.username)
    model = model_manager.get_model(req.model_name)
    if not model:
        return JSONResponse({"error": f"Model {req.model_name} not found for user {req.username}."}, status_code=404)
    try:
        new_data = create_paraphrased_data(
            username=req.username,
            model=model,
            dimension=req.dimension,
            num_samples=req.num_samples,
            dataset_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset"),
            extra_instructions=req.extra_instructions
        )
        return {"status": "success", "created": len(new_data), "data": new_data, "timestamp": int(time.time())}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/monthly_task_stats")
def get_monthly_task_stats(year: int, month: int):
    """
    获取指定月份的每日任务统计数据
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    
    if not os.path.exists(reports_dir):
        return JSONResponse({"error": "No reports found."}, status_code=404)
        
    # 获取该月的所有天数
    _, days_in_month = calendar.monthrange(year, month)
    
    # 初始化每日数据
    daily_stats = {str(day): {"pass": 0, "improve": 0} for day in range(1, days_in_month + 1)}
    
    # 构建月份字符串 (格式: YYYY-MM)
    month_str = f"{year}-{month:02d}"
    month_dir = os.path.join(reports_dir, month_str)
    
    # 如果该月份的目录不存在，返回空数据
    if not os.path.exists(month_dir):
        result = {
            "dates": list(range(1, days_in_month + 1)),
            "pass": [0] * days_in_month,
            "improve": [0] * days_in_month
        }
        return JSONResponse(result)
        
    # 获取该月的任务概览文件
    tasks_file = os.path.join(month_dir, "tasks.json")
    if not os.path.exists(tasks_file):
        result = {
            "dates": list(range(1, days_in_month + 1)),
            "pass": [0] * days_in_month,
            "improve": [0] * days_in_month
        }
        return JSONResponse(result)
        
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
    
    return JSONResponse(result)

@app.get("/api/monthly_model_stats")
def get_monthly_model_stats(year: int, month: int):
    """
    获取指定月份的每日模型统计数据
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    
    if not os.path.exists(reports_dir):
        return JSONResponse({"error": "No reports found."}, status_code=404)
        
    # 获取该月的所有天数
    _, days_in_month = calendar.monthrange(year, month)
    
    # 初始化每日数据
    daily_stats = {str(day): {"pass": set(), "improve": set()} for day in range(1, days_in_month + 1)}
    
    # 构建月份字符串 (格式: YYYY-MM)
    month_str = f"{year}-{month:02d}"
    month_dir = os.path.join(reports_dir, month_str)
    
    # 如果该月份的目录不存在，返回空数据
    if not os.path.exists(month_dir):
        result = {
            "dates": list(range(1, days_in_month + 1)),
            "pass": [0] * days_in_month,
            "improve": [0] * days_in_month
        }
        return JSONResponse(result)
        
    # 获取该月的任务概览文件
    tasks_file = os.path.join(month_dir, "tasks.json")
    if not os.path.exists(tasks_file):
        result = {
            "dates": list(range(1, days_in_month + 1)),
            "pass": [0] * days_in_month,
            "improve": [0] * days_in_month
        }
        return JSONResponse(result)
        
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
    
    return JSONResponse(result)

@app.get("/api/monthly-tasks")
def get_monthly_tasks(year: int = None, month: int = None):
    """
    获取指定月份的任务列表
    """
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    
    # 构建月份字符串 (格式: YYYY-MM)
    month_str = f"{year}-{month:02d}"
    month_dir = os.path.join(reports_dir, month_str)
    
    if not os.path.exists(month_dir):
        return JSONResponse([])
        
    # 获取该月的任务概览文件
    tasks_file = os.path.join(month_dir, "tasks.json")
    if not os.path.exists(tasks_file):
        return JSONResponse([])
        
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
        
    return JSONResponse(tasks)
