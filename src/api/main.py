from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agents.agents_graph import run_compliance_audit

# 1. Initialize FastAPI Application
app = FastAPI(
    title="Compliance Multi-Agent API",
    description="An API that runs a multi-agent workflow to audit financial proposals.",
    version="1.0.0"
)

# 2. Define Data Models (Pydantic Schema Validation)
class AuditRequest(BaseModel):
    proposal_text: str

class Violation(BaseModel):
    clause: str
    description: str

class AuditResponse(BaseModel):
    status: str
    risk_level: str
    summary: str
    violations: list[Violation]

# 3. Create API Endpoints
@app.get("/")
async def health_check():
    """Simple endpoint to verify the server is running."""
    return {"status": "ok", "message": "Multi-Agent Compliance API is running"}

@app.post("/audit", response_model=AuditResponse)
async def audit_proposal(request: AuditRequest):
    """
    Receives a business proposal, runs it through the LangGraph agents, 
    and returns a structured JSON compliance report.
    """
    if not request.proposal_text.strip():
        raise HTTPException(status_code=400, detail="Proposal text cannot be empty.")
    
    try:
        # Trigger the LangGraph multi-agent workflow
        report = run_compliance_audit(request.proposal_text)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")