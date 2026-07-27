from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import PyPDF2
import io
from src.agents.agents_graph import run_compliance_audit

# 1. Initialize FastAPI Application
app = FastAPI(
    title="Compliance Multi-Agent API",
    description="An API that runs a multi-agent workflow to audit financial proposals.",
    version="1.1.0"
)

# 2. Define Data Models
class Violation(BaseModel):
    clause: str
    description: str

class AuditResponse(BaseModel):
    status: str
    risk_level: str
    summary: str
    violations: list[Violation]

class AuditRequest(BaseModel):
    proposal_text: str

# 3. Create API Endpoints
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Multi-Agent Compliance API is running"}

# Legacy text endpoint (kept for testing)
@app.post("/audit", response_model=AuditResponse)
async def audit_proposal(request: AuditRequest):
    if not request.proposal_text.strip():
        raise HTTPException(status_code=400, detail="Proposal text cannot be empty.")
    try:
        return run_compliance_audit(request.proposal_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")

# NEW: Document Upload Endpoint
@app.post("/audit/file", response_model=AuditResponse)
async def audit_proposal_file(file: UploadFile = File(...)):
    """Receives a PDF file, extracts text, and runs the compliance audit."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        # Read file content into memory
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        
        # Extract text from all pages
        proposal_text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                proposal_text += extracted + "\n"
                
        if not proposal_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF. It might be a scanned image.")
            
        print(f"Extracted {len(proposal_text)} characters from {file.filename}. Starting audit...")
        
        # Pass the extracted text to our existing LangGraph system
        report = run_compliance_audit(proposal_text)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File audit failed: {str(e)}")