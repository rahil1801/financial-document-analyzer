import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from tools import (
    FinancialDocumentTool,
    InvestmentTool,
    RiskTool,
)

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:
    AsyncIOMotorClient = None


app = FastAPI(title="Financial Document Analyzer", version="4.0.0")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "2"))
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "financial_analyzer")

job_queue: asyncio.Queue = asyncio.Queue()
workers: list[asyncio.Task] = []
job_store: dict[str, dict[str, Any]] = {}

mongo_client = None
mongo_db = None

class AnalyzeResponse(BaseModel):
    status: str
    job_id: str
    message: str

async def init_db() -> None:
    global mongo_client, mongo_db

    if not MONGODB_URI:
        print("⚠️ MONGODB_URI not set. Running without persistence.")
        return

    if AsyncIOMotorClient is None:
        raise RuntimeError("Motor driver not installed. Install with: pip install motor")

    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    mongo_db = mongo_client[MONGODB_DB_NAME]


async def persist_analysis(job: dict[str, Any]) -> None:
    if mongo_db is None:
        return

    await mongo_db.analyses.update_one(
        {"job_id": job["job_id"]},
        {"$set": job},
        upsert=True,
    )


async def run_single_analysis(job: dict[str, Any]) -> dict[str, Any]:
    """
    Uses separated tool classes in deterministic pipeline.
    """

    loop = asyncio.get_event_loop()

    # Run blocking PDF read in thread pool
    text = await loop.run_in_executor(
        None,
        FinancialDocumentTool.read_data_tool,
        job["file_path"],
    )

    if not text.strip():
        raise ValueError("Document contains no readable text.")

    investment_result = InvestmentTool.analyze_investment_tool(
        text=text,
        query=job["query"],
    )

    risk_result = RiskTool.create_risk_assessment_tool(text=text)

    return {
        "investment_analysis": investment_result,
        "risk_assessment": risk_result,
    }


async def worker_loop(worker_name: str) -> None:
    while True:
        job_id = await job_queue.get()

        job = job_store.get(job_id)
        if not job:
            job_queue.task_done()
            continue

        job["status"] = "processing"
        job["worker"] = worker_name
        job["updated_at"] = datetime.now(timezone.utc).isoformat()

        try:
            analysis = await run_single_analysis(job)
            job["status"] = "completed"
            job["analysis"] = analysis
        except Exception as exc:
            job["status"] = "failed"
            job["error"] = str(exc)
        finally:
            job["updated_at"] = datetime.now(timezone.utc).isoformat()
            await persist_analysis(job)

            try:
                os.remove(job["file_path"])
            except OSError:
                pass

            job_queue.task_done()


@app.on_event("startup")
async def startup_event() -> None:
    await init_db()
    for i in range(WORKER_CONCURRENCY):
        workers.append(
            asyncio.create_task(worker_loop(f"worker-{i+1}"))
        )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    for task in workers:
        task.cancel()

    if mongo_client is not None:
        mongo_client.close()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Financial Document Analyzer API is running"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_financial_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights."),
) -> AnalyzeResponse:

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    job_id = str(uuid.uuid4())
    file_path = DATA_DIR / f"financial_document_{job_id}.pdf"

    with file_path.open("wb") as f:
        f.write(await file.read())

    job_store[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "query": query.strip(),
        "file_name": file.filename,
        "file_path": str(file_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await persist_analysis(job_store[job_id])
    await job_queue.put(job_id)

    return AnalyzeResponse(
        status="queued",
        job_id=job_id,
        message="Document queued for analysis",
    )


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict[str, Any]:
    job = job_store.get(job_id)

    if not job and mongo_db is not None:
        job = await mongo_db.analyses.find_one(
            {"job_id": job_id},
            {"_id": 0},
        )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.post("/analyze/sync")
async def analyze_sync(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document."),
) -> dict[str, Any]:

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_path = DATA_DIR / f"sync_{uuid.uuid4()}.pdf"

    with file_path.open("wb") as f:
        f.write(await file.read())

    try:
        loop = asyncio.get_event_loop()

        text = await loop.run_in_executor(
            None,
            FinancialDocumentTool.read_data_tool,
            str(file_path),
        )

        if not text.strip():
            raise ValueError("Document contains no readable text.")

        investment_result = InvestmentTool.analyze_investment_tool(
            text=text,
            query=query.strip(),
        )

        risk_result = RiskTool.create_risk_assessment_tool(text=text)

        return {
            "status": "completed",
            "file_processed": file.filename,
            "investment_analysis": investment_result,
            "risk_assessment": risk_result,
        }

    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)