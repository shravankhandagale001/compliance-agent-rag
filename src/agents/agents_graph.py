import os
import json
from typing import TypedDict, List
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

load_dotenv()

# Configuration
CHROMA_PATH = "./chroma_db"

# ---------------------------------------------------------------------------
# 1. STATE DEFINITION
# ---------------------------------------------------------------------------
class ComplianceState(TypedDict):
    proposal_text: str
    retrieved_docs: List[str]
    audit_findings: str
    final_report: dict

# ---------------------------------------------------------------------------
# 2. HELPER FUNCTIONS & LLM INITIALIZATION
# ---------------------------------------------------------------------------
def get_vectorstore():
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)

# Initialize LLM (Uses OPENAI_API_KEY from .env; can be swapped for Groq/Ollama)
llm = ChatOllama(model="llama3", temperature=0)

# ---------------------------------------------------------------------------
# 3. AGENT NODES
# ---------------------------------------------------------------------------

def retriever_node(state: ComplianceState) -> dict:
    """Agent 1: Queries ChromaDB for regulations matching the proposal context."""
    print("--- AGENT 1: RETRIEVING REGULATIONS ---")
    proposal = state["proposal_text"]
    
    vectorstore = get_vectorstore()
    # Search top 4 most relevant regulatory clauses
    docs = vectorstore.similarity_search(proposal, k=4)
    retrieved_texts = [doc.page_content for doc in docs]
    
    print(f"Retrieved {len(retrieved_texts)} relevant regulatory clauses.")
    return {"retrieved_docs": retrieved_texts}


def auditor_node(state: ComplianceState) -> dict:
    """Agent 2: Audits proposal against retrieved regulatory context."""
    print("--- AGENT 2: AUDITING PROPOSAL ---")
    proposal = state["proposal_text"]
    regulations = "\n\n---\n\n".join(state["retrieved_docs"])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Financial Regulatory Compliance Auditor. 
Your sole task is to evaluate a business proposal against provided regulatory circulars.
For every potential issue you identify:
1. Quote or reference the specific regulatory requirement.
2. Explain clearly why the proposal breaches or risks breaching it.
3. Assign an overall Risk Level: HIGH, MEDIUM, LOW, or PASS.

Be strict, precise, and ground your answer ENTIRELY in the provided regulatory context."""),
        ("user", "REGULATORY CONTEXT:\n{regulations}\n\nPROPOSAL TO AUDIT:\n{proposal}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"regulations": regulations, "proposal": proposal})
    
    return {"audit_findings": response.content}


def reporter_node(state: ComplianceState) -> dict:
    """Agent 3: Formats raw findings into a strict JSON audit report."""
    print("--- AGENT 3: GENERATING STRUCTURED REPORT ---")
    findings = state["audit_findings"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Enterprise Compliance Reporting Agent.
Transform the provided audit findings into a valid JSON object matching this schema:
{{
  "status": "APPROVED" | "REJECTED" | "REQUIRES_REVIEW",
  "risk_level": "HIGH" | "MEDIUM" | "LOW" | "NONE",
  "summary": "<1-2 sentence executive summary>",
  "violations": [
    {{
      "clause": "<referenced regulation clause or section>",
      "description": "<explanation of the compliance breach>"
    }}
  ]
}}
Do NOT include markdown backticks or extra text outside the JSON object."""),
        ("user", "AUDIT FINDINGS:\n{findings}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"findings": findings})
    
    # Clean up and parse JSON output
    cleaned_output = response.content.strip().replace("```json", "").replace("```", "")
    try:
        report_json = json.loads(cleaned_output)
    except json.JSONDecodeError:
        report_json = {
            "status": "REQUIRES_REVIEW",
            "risk_level": "UNKNOWN",
            "summary": "Report parsing failed.",
            "raw_findings": findings
        }
        
    return {"final_report": report_json}

# ---------------------------------------------------------------------------
# 4. WORKFLOW GRAPH CONSTRUCTION
# ---------------------------------------------------------------------------

def build_compliance_graph():
    workflow = StateGraph(ComplianceState)
    
    # Add Nodes
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("reporter", reporter_node)
    
    # Define Edges (Sequential Multi-Agent Pipeline)
    workflow.set_entry_point("retriever")
    workflow.add_edge("retriever", "auditor")
    workflow.add_edge("auditor", "reporter")
    workflow.add_edge("reporter", END)
    
    return workflow.compile()

# Master function to run the compliance audit
def run_compliance_audit(proposal_text: str) -> dict:
    app = build_compliance_graph()
    initial_state = {
        "proposal_text": proposal_text,
        "retrieved_docs": [],
        "audit_findings": "",
        "final_report": {}
    }
    result = app.invoke(initial_state)
    return result["final_report"]