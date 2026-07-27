import os
import json
from typing import TypedDict, List, Optional
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

CHROMA_PATH = "./chroma_db"

# ---------------------------------------------------------------------------
# 1. STATE DEFINITION
# ---------------------------------------------------------------------------
class ComplianceState(TypedDict):
    proposal_text: str
    retrieved_docs: List[str]
    audit_findings: str
    risk_level: str
    sar_draft: Optional[str]
    human_approved: bool
    final_report: dict

# ---------------------------------------------------------------------------
# 2. HELPER & LLM INITIALIZATION
# ---------------------------------------------------------------------------
def get_vectorstore():
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)

# Initialize the free Gemini 1.5 Flash model
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0
)

# ---------------------------------------------------------------------------
# 3. AGENT NODES
# ---------------------------------------------------------------------------

def retriever_node(state: ComplianceState) -> dict:
    """Agent 1: Queries ChromaDB for regulatory context using semantic search."""
    print("\n--- AGENT 1: RETRIEVING REGULATORY CONTEXT ---")
    proposal = state["proposal_text"]
    
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(proposal, k=5)
    retrieved_texts = [doc.page_content for doc in docs]
    
    print(f"Retrieved {len(retrieved_texts)} relevant regulatory clauses.")
    return {"retrieved_docs": retrieved_texts}


def auditor_node(state: ComplianceState) -> dict:
    """Agent 2: Audits Markdown document against retrieved regulations."""
    print("\n--- AGENT 2: AUDITING PROPOSAL FOR COMPLIANCE BREACHES ---")
    proposal = state["proposal_text"]
    regulations = "\n\n---\n\n".join(state["retrieved_docs"])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Enterprise Financial Compliance Auditor. 
Evaluate the business proposal against the retrieved regulatory circulars.

Your task:
1. Identify all potential regulatory breaches or non-compliance risks.
2. Quote or cite the exact paragraph or section of the regulation violated.
3. Clearly assign an overall Risk Classification: HIGH, MEDIUM, or LOW.

Be rigorous, strict, and ground your evaluation strictly in the provided regulatory context."""),
        ("user", "REGULATORY CONTEXT:\n{regulations}\n\nPROPOSAL DOCUMENT:\n{proposal}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"regulations": regulations, "proposal": proposal})
    findings = response.content
    
    # Determine risk level from auditor output
    findings_upper = findings.upper()
    if "HIGH" in findings_upper:
        assigned_risk = "HIGH"
    elif "MEDIUM" in findings_upper:
        assigned_risk = "MEDIUM"
    else:
        assigned_risk = "LOW"
        
    print(f"Audit completed. Risk Level evaluated as: {assigned_risk}")
    return {"audit_findings": findings, "risk_level": assigned_risk}


def sar_drafter_node(state: ComplianceState) -> dict:
    """Agent 3: Drafts a formal Suspicious Activity Report (SAR) for High-Risk findings."""
    print("\n--- AGENT 3: DRAFTING SUSPICIOUS ACTIVITY REPORT (SAR) ---")
    findings = state["audit_findings"]
    proposal = state["proposal_text"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Regulatory Reporting Agent specializing in Anti-Money Laundering (AML) and Financial Crime Compliance.
Draft a formal Suspicious Activity Report (SAR) based on the audit findings.

Structure the SAR as follows:
1. SUMMARY OF SUSPICIOUS ACTIVITY
2. SPECIFIC REGULATORY VIOLATIONS (citing RBI/SEBI guidelines)
3. ENTITY & OPERATIONAL DETAILS (extracted from proposal)
4. RECOMMENDED REGULATORY ACTIONS & MITIGATION

Keep the language professional, objective, and audit-ready."""),
        ("user", "AUDIT FINDINGS:\n{findings}\n\nORIGINAL PROPOSAL:\n{proposal}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"findings": findings, "proposal": proposal})
    return {"sar_draft": response.content}


def human_review_node(state: ComplianceState) -> dict:
    """HITL Node: Placeholder node where the workflow pauses for human compliance officer review."""
    print("\n--- HITL NODE: WORKFLOW INTERRUPTED FOR HUMAN REVIEW ---")
    return {}


def reporter_node(state: ComplianceState) -> dict:
    """Agent 4: Formats raw findings and human-reviewed SAR into a structured JSON report."""
    print("\n--- AGENT 4: GENERATING FINAL STRUCTURED JSON REPORT ---")
    findings = state["audit_findings"]
    sar = state.get("sar_draft") or "N/A - No SAR Required"
    risk_level = state.get("risk_level", "LOW")
    approved = state.get("human_approved", False)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Enterprise Compliance Reporting System.
Transform the audit findings and SAR into a clean JSON object matching this schema:
{{
  "status": "APPROVED" | "REJECTED" | "REQUIRES_REVIEW",
  "risk_level": "{risk_level}",
  "human_reviewed": {approved_str},
  "summary": "<1-2 sentence executive summary>",
  "violations": [
    {{
      "clause": "<referenced regulation clause>",
      "description": "<explanation of breach>"
    }}
  ],
  "sar_generated": "{sar_gen}"
}}
Do NOT include markdown backticks or extra prose outside the raw JSON object."""),
        ("user", "FINDINGS:\n{findings}\n\nSAR DRAFT:\n{sar}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "findings": findings, 
        "sar": sar, 
        "risk_level": risk_level,
        "approved_str": "true" if approved else "false",
        "sar_gen": "true" if sar != "N/A - No SAR Required" else "false"
    })
    
    cleaned = response.content.strip().replace("```json", "").replace("```", "")
    try:
        report_json = json.loads(cleaned)
    except json.JSONDecodeError:
        report_json = {
            "status": "REQUIRES_REVIEW",
            "risk_level": risk_level,
            "human_reviewed": approved,
            "summary": "Completed audit analysis.",
            "violations": [{"clause": "General Compliance", "description": findings}],
            "sar_generated": "true" if sar != "N/A - No SAR Required" else "false"
        }
        
    if sar != "N/A - No SAR Required":
        report_json["sar_content"] = sar
        
    return {"final_report": report_json}

# ---------------------------------------------------------------------------
# 4. CONDITIONAL ROUTING LOGIC
# ---------------------------------------------------------------------------

def risk_routing_logic(state: ComplianceState) -> str:
    """Routes state based on risk level evaluated by the Auditor."""
    if state["risk_level"] == "HIGH":
        return "sar_drafter"
    return "reporter"

# ---------------------------------------------------------------------------
# 5. GRAPH CONSTRUCTION & COMPILATION
# ---------------------------------------------------------------------------

# Global in-memory checkpointer to persist state across pause points
memory = MemorySaver()

def build_compliance_graph():
    workflow = StateGraph(ComplianceState)
    
    # Add Nodes
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("sar_drafter", sar_drafter_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("reporter", reporter_node)
    
    # Define Entry Point & Sequential Edges
    workflow.set_entry_point("retriever")
    workflow.add_edge("retriever", "auditor")
    
    # Conditional Edge based on Risk Level
    workflow.add_conditional_edges(
        "auditor",
        risk_routing_logic,
        {
            "sar_drafter": "sar_drafter",
            "reporter": "reporter"
        }
    )
    
    workflow.add_edge("sar_drafter", "human_review")
    workflow.add_edge("human_review", "reporter")
    workflow.add_edge("reporter", END)
    
    # Pause execution BEFORE the human_review node
    return workflow.compile(checkpointer=memory, interrupt_before=["human_review"])

# Global compiled application instance
app = build_compliance_graph()

# ---------------------------------------------------------------------------
# 6. WORKFLOW RUNNERS (INITIAL & RESUME)
# ---------------------------------------------------------------------------

def start_compliance_audit(proposal_text: str, thread_id: str) -> dict:
    """
    Executes the workflow up to the pause point (if High Risk) or to completion (if Low/Med).
    """
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "proposal_text": proposal_text,
        "retrieved_docs": [],
        "audit_findings": "",
        "risk_level": "LOW",
        "sar_draft": None,
        "human_approved": False,
        "final_report": {}
    }
    
    # Execute graph until completion or interrupt point
    app.invoke(initial_state, config)
    
    # Inspect state snapshot
    state_snapshot = app.get_state(config)
    
    # Check if workflow was interrupted before human_review (High Risk path)
    if state_snapshot.next:
        current_values = state_snapshot.values
        return {
            "status": "PAUSED_FOR_HUMAN_REVIEW",
            "risk_level": current_values.get("risk_level", "HIGH"),
            "sar_draft": current_values.get("sar_draft"),
            "thread_id": thread_id
        }
    else:
        return {
            "status": "COMPLETED",
            "report": state_snapshot.values.get("final_report", {})
        }


def resume_compliance_audit(thread_id: str, approved: bool) -> dict:
    """
    Resumes a paused workflow after a human compliance officer approves or rejects the SAR.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Inject human decision into state
    app.update_state(config, {"human_approved": approved})
    
    # Resume execution
    app.invoke(None, config)
    
    # Retrieve final state report
    state_snapshot = app.get_state(config)
    return {
        "status": "COMPLETED",
        "report": state_snapshot.values.get("final_report", {})
    }