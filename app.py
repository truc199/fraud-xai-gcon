import os
import subprocess
import json
import csv
from typing import Generator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Advanced Cohort Fraud xAI Dashboard")

# Ensure static directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("data/exports", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/exports")
async def get_exports():
    """Scan and list all historical pipeline runs along with parsed CSV rows."""
    runs = []
    
    # 1. Check for the "latest" run
    latest_csv = "data/anomaly_alerts_latest.csv"
    latest_json = "data/anomaly_alerts_latest_metadata.json"
    if os.path.exists(latest_csv) and os.path.exists(latest_json):
        runs.append(parse_run_files("latest", latest_csv, latest_json))
        
    # 2. Check for timestamped exports
    export_dir = "data/exports"
    files = os.listdir(export_dir)
    csv_files = sorted([f for f in files if f.endswith(".csv")], reverse=True)
    
    for f_csv in csv_files:
        base_name = os.path.splitext(f_csv)[0]
        f_json = f"{base_name}_metadata.json"
        json_path = os.path.join(export_dir, f_json)
        csv_path = os.path.join(export_dir, f_csv)
        
        if os.path.exists(json_path):
            runs.append(parse_run_files(base_name, csv_path, json_path))
            
    return runs

def parse_run_files(run_id: str, csv_path: str, json_path: str) -> dict:
    """Parse a companion CSV and JSON metadata pair into a structured dict."""
    # Load JSON metadata
    metadata = {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        metadata = {"error": f"Failed to load metadata: {str(e)}"}
        
    # Parse CSV anomalies
    anomalies = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                anomalies.append(row)
    except Exception as e:
        pass
        
    return {
        "id": run_id,
        "csv_file": csv_path,
        "json_file": json_path,
        "metadata": metadata,
        "anomalies": anomalies
    }

@app.get("/api/run/stream")
def stream_pipeline_run() -> StreamingResponse:
    """Runs run_pipeline.py and yields terminal output line-by-line via Server-Sent Events (SSE)."""
    def run_generator() -> Generator[str, None, None]:
        cmd = ["uv", "run", "run_pipeline.py"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        yield "data: [SERVER] Launching pipeline: uv run run_pipeline.py\n\n"
        
        # Read process output line-by-line
        while True:
            line = process.stdout.readline()
            if not line:
                break
            # Send SSE encoded message
            yield f"data: {line.strip()}\n\n"
            
        process.stdout.close()
        return_code = process.wait()
        yield f"data: [SERVER] Pipeline execution completed with code {return_code}\n\n"
        
    return StreamingResponse(run_generator(), media_type="text/event-stream")

@app.get("/api/confirmed_frauds")
async def get_confirmed_frauds():
    fraud_file = "data/confirmed_frauds.json"
    if os.path.exists(fraud_file):
        try:
            with open(fraud_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"confirmed_transactions": []}

class ConfirmFraudRequest(BaseModel):
    transaction_id: str

@app.post("/api/confirm_fraud")
async def confirm_fraud(req: ConfirmFraudRequest):
    fraud_file = "data/confirmed_frauds.json"
    data = {"confirmed_transactions": []}
    if os.path.exists(fraud_file):
        try:
            with open(fraud_file, "r") as f:
                data = json.load(f)
        except Exception:
            pass
            
    if "confirmed_transactions" not in data:
        data["confirmed_transactions"] = []
        
    tx_id = str(req.transaction_id).strip()
    if tx_id and tx_id not in data["confirmed_transactions"]:
        data["confirmed_transactions"].append(tx_id)
        with open(fraud_file, "w") as f:
            json.dump(data, f, indent=4)
            
    return {"status": "success", "confirmed_transactions": data["confirmed_transactions"]}
