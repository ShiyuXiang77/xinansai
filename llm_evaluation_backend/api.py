import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from llm_evaluation_backend.eval_core import Evaluator, Report
from llm_evaluation_backend.app import ModelManager, ModelInfo
from fastapi.staticfiles import StaticFiles
from llm_evaluation_backend.contextual_variator.contextual_variator import create_paraphrased_data
import time

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
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir, exist_ok=True)
    dataset_dir = os.path.join(base_dir, "dataset")
    timestamp = int(time.time())
    report_filename = f"report_{username}_{timestamp}.json"
    report_path = os.path.join(reports_dir, report_filename)
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
    # Save report with username and timestamp
    report = Report(",".join(model_names), judge_model_name, all_results, output_path=report_path, username=username, timestamp=timestamp)
    report.save()
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
def get_report(username: str = None):
    """
    获取最新一份report（兼容老接口），可选username参数，若有则取该用户最新report，否则取所有用户最新report
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    if not os.path.exists(reports_dir):
        return JSONResponse({"error": "No report found."}, status_code=404)
    report_files = sorted([f for f in os.listdir(reports_dir) if f.endswith(".json")])
    if not report_files:
        return JSONResponse({"error": "No report found."}, status_code=404)
    # 过滤用户
    if username:
        user_reports = [f for f in report_files if f"_{username}_" in f]
        if not user_reports:
            return JSONResponse({"error": f"No report found for user {username}."}, status_code=404)
        latest_report = sorted(user_reports)[-1]
    else:
        latest_report = report_files[-1]
    report_path = os.path.join(reports_dir, latest_report)
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(data)

@app.get("/api/reports")
def get_reports(username: str):
    """
    获取当前用户所有评测报告
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(base_dir, "user_data")
    reports_dir = os.path.join(user_data_dir, "reports")
    if not os.path.exists(reports_dir):
        return JSONResponse({"error": "No report found."}, status_code=404)
    report_files = sorted([f for f in os.listdir(reports_dir) if f.endswith(".json") and f"_{username}_" in f])
    if not report_files:
        return JSONResponse({"error": f"No report found for user {username}."}, status_code=404)
    reports = []
    for fname in report_files:
        fpath = os.path.join(reports_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["_filename"] = fname
        reports.append(data)
    return JSONResponse({"reports": reports, "count": len(reports)})

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
