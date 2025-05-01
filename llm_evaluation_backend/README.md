# LLM Evaluation System

This project provides a backend and test frontend for evaluating LLMs (Large Language Models) across multiple dimensions, managing user models, generating paraphrased data, and storing/retrieving evaluation reports.

## Directory Structure

- `llm_evaluation_backend/`
  - `api.py` — FastAPI backend, all API endpoints
  - `app.py` — Model management logic
  - `eval_core.py` — Evaluation logic
  - `LLM_helper.py` — LLM API call helper
  - `contextual_variator/` — Paraphrase logic
  - `dataset/` — Test data for each dimension
  - `user_data/` — All user-related data (models, reports, etc.)
- `llm_evaluation_backend/test_frontend.html` — Test frontend for all features

## API Endpoints

### 1. Add Model

**POST** `/api/add_model`

**Request JSON:**
```json
{
  "username": "your_username",
  "model_name": "your_model_name",
  "api_key": "your_api_key",
  "base_url": "your_base_url"
}
```

**Response:**
- `{"status": "success", "message": "..."}`
- or error message

---

### 2. List Models

**GET** `/api/list_models?username=your_username`

**Response:**
```json
{
  "models": ["model1", "model2", ...]
}
```

---

### 3. Start Evaluation

**POST** `/api/evaluate`

**Request JSON:**
```json
{
  "username": "your_username",
  "model_names": ["model1", "model2"],
  "judge_model_name": "judge_model",
  "dimensions": ["fairness", "safety", ...],
  "num_samples": 2
}
```

**Response:**  
SSE (Server-Sent Events) streaming progress and results.  
On completion, a report is saved in `user_data/reports/report_{username}_{timestamp}.json`.

---

### 4. Fetch Latest Report

**GET** `/api/report?username=your_username`

**Response:**  
Returns the latest report for the user.

---

### 5. Fetch All Reports for User

**GET** `/api/reports?username=your_username`

**Response:**
```json
{
  "reports": [
    {
      "model": "...",
      "judge_model": "...",
      "results": {...},
      "username": "...",
      "timestamp": ...,
      "_filename": "report_xxx_xxx.json"
    },
    ...
  ],
  "count": N
}
```

---

### 6. Paraphrase Data Generation

**POST** `/api/paraphrase_data`

**Request JSON:**
```json
{
  "username": "your_username",
  "model_name": "your_model_name",
  "dimension": "fairness",
  "num_samples": 2,
  "extra_instructions": "optional string"
}
```

**Response:**
```json
{
  "status": "success",
  "created": 2,
  "data": [ ... ],
  "timestamp": 1710000000
}
```

---

## Test Frontend

Open `llm_evaluation_backend/test_frontend.html` in your browser (via `/static/test_frontend.html` if using FastAPI).

- Add models, list models
- Create paraphrased data
- Start evaluation (multi-model, multi-dimension)
- Fetch latest report
- Fetch all reports for a user

## Data Storage

- All user models: `llm_evaluation_backend/user_data/models_{username}.json`
- All reports: `llm_evaluation_backend/user_data/reports/report_{username}_{timestamp}.json`
- Paraphrased/generated data: appended to the corresponding `llm_evaluation_backend/dataset/{dimension}_test.json`

## Notes

- All API endpoints require the correct username for user-specific data.
- Reports are never overwritten; each evaluation creates a new report file with a timestamp.
- All features can be tested via the provided test frontend.

---
写了个简单的测试前端
要测试直接
```bash
(base) youmu@youmusPC:~/project/xinansai$ uvicorn llm_evaluation_backend.api:app --reload --host 0.0.0.0 --port 8000
```
然后导航到 http://localhost:8000/static/test_frontend.html
