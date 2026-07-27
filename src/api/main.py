import os
import uuid
import tempfile
import pymupdf4llm
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel

from src.agents.agents_graph import start_compliance_audit, resume_compliance_audit

app = FastAPI(
    title="Enterprise Multi-Agent Compliance Engine",
    description="Production-grade AI Multi-Agent Compliance System with HITL & SAR Generation",
    version="2.0.0"
)

class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool

@app.get("/")
async def health_check():
    return {"status": "ok", "engine": "Enterprise Multi-Agent Compliance Engine v2.0"}

@app.post("/audit/file")
async def audit_file(file: UploadFile = File(...)):
    """Accepts PDF, converts to structural Markdown, and kicks off stateful agent graph."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
    
    try:
        # Save temp file for PyMuPDF4LLM parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # Extract structural markdown (preserves tables and headers)
        proposal_markdown = pymupdf4llm.to_markdown(tmp_path)
        os.remove(tmp_path)

        if not proposal_markdown.strip():
            raise HTTPException(status_code=400, detail="Document appears empty or unparseable.")
            
        thread_id = str(uuid.uuid4())
        result = start_compliance_audit(proposal_markdown, thread_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit execution failed: {str(e)}")


@app.post("/audit/resume")
async def resume_audit(request: ResumeRequest):
    """Resumes a paused workflow after human compliance officer approval/rejection."""
    try:
        result = resume_compliance_audit(request.thread_id, request.approved)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume audit thread: {str(e)}")