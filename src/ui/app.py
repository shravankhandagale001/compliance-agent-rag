import streamlit as st
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Sentinel AI | Enterprise Regulatory Compliance Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 25px;
    }
    .card-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .sar-box {
        background-color: #FFF1F2;
        border-left: 4px solid #E11D48;
        padding: 15px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
    }
    .badge-high {
        background-color: #FFE4E6;
        color: #9F1239;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-pass {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SIDEBAR: SYSTEM DIAGNOSTICS & METRICS
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/shield.png", width=60)
    st.title("Sentinel AI Node")
    st.caption("Automated Regulatory Audit Engine")
    st.divider()
    
    st.subheader("System Status")
    st.success("🟢 API Gateway: Active")
    st.info("🧠 Model: Llama 3.2 (Local)")
    st.info("📚 Vector Store: ChromaDB")
    st.info("⚡ Parser: PyMuPDF4LLM")
    st.info("🛡️ HITL State Engine: Active")
    
    st.divider()
    st.caption("Compliance Frameworks Loaded:")
    st.markdown("- RBI Digital Lending Guidelines 2022")
    st.markdown("- RBI KYC Master Directions")
    st.markdown("- SEBI / Financial Crime Standards")

# ---------------------------------------------------------------------------
# MAIN INTERFACE
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">🛡️ Sentinel Compliance Audit Workstation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated Multi-Agent Document Verification & Suspicious Activity Reporting (SAR) System</div>', unsafe_allow_html=True)

# Initialize Session States
if "audit_state" not in st.session_state:
    st.session_state.audit_state = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Upload Section
uploaded_file = st.file_uploader("Upload Product Proposal Document (PDF)", type=["pdf"], help="Supports multi-page business proposals, PRDs, or product sheets.")

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    start_audit = st.button("Initiate AI Audit", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# 1. TRIGGER AUDIT
# ---------------------------------------------------------------------------
if start_audit:
    if not uploaded_file:
        st.warning("Please attach a proposal PDF file before initiating the audit.")
    else:
        with st.spinner("Processing document layout, extracting vector embeddings, and running multi-agent graph..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                res = requests.post(f"{API_BASE_URL}/audit/file", files=files)
                
                if res.status_code == 200:
                    st.session_state.audit_state = res.json()
                    st.rerun()
                else:
                    st.error(f"Execution Error: {res.text}")
            except Exception as e:
                st.error(f"Failed to communicate with agent engine: {e}")

# ---------------------------------------------------------------------------
# 2. DISPLAY AUDIT STATE / HITL INTERRUPT
# ---------------------------------------------------------------------------
state = st.session_state.audit_state

if state:
    st.divider()
    
    # CASE A: PAUSED FOR HUMAN REVIEW (HIGH RISK / SAR GENERATED)
    if state.get("status") == "PAUSED_FOR_HUMAN_REVIEW":
        st.error("🚨 CRITICAL RISK DETECTED — ACTION REQUIRED")
        
        st.markdown(f"""
        <div class="card-box">
            <h4>Workflow Interrupted for Compliance Officer Review</h4>
            <p>The <b>Auditor Agent</b> evaluated this document as <span class="badge-high">HIGH RISK</span>. 
            The <b>SAR Drafter Agent</b> has automatically compiled a draft <b>Suspicious Activity Report (SAR)</b>. 
            Review the findings below and authorize or reject the official filing to finalize the report.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Drafted Suspicious Activity Report (SAR)")
        st.markdown(f'<div class="sar-box">{state.get("sar_draft")}</div>', unsafe_allow_html=True)
        
        st.write(" ")
        st.subheader("Compliance Officer Decision")
        
        c1, c2, c3 = st.columns([1, 1, 2])
        
        with c1:
            if st.button("✅ Approve & Sign SAR", type="primary", use_container_width=True):
                with st.spinner("Signing SAR and resuming agent execution..."):
                    payload = {"thread_id": state["thread_id"], "approved": True}
                    res = requests.post(f"{API_BASE_URL}/audit/resume", json=payload)
                    if res.status_code == 200:
                        st.session_state.audit_state = res.json()
                        st.rerun()
                    else:
                        st.error("Failed to resume state.")
                        
        with c2:
            if st.button("❌ Reject SAR Filing", use_container_width=True):
                with st.spinner("Logging rejection and finalizing report..."):
                    payload = {"thread_id": state["thread_id"], "approved": False}
                    res = requests.post(f"{API_BASE_URL}/audit/resume", json=payload)
                    if res.status_code == 200:
                        st.session_state.audit_state = res.json()
                        st.rerun()
                    else:
                        st.error("Failed to resume state.")

    # CASE B: WORKFLOW COMPLETED (FINAL AUDIT REPORT DISPLAY)
    elif state.get("status") == "COMPLETED":
        report = state.get("report", {})
        
        st.success("✅ Compliance Audit Completed Successfully")
        
        # Top Dashboard Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Final Status", report.get("status", "N/A"))
        m2.metric("Assigned Risk Level", report.get("risk_level", "N/A"))
        m3.metric("Human Reviewed", "Yes" if report.get("human_reviewed") else "No")
        m4.metric("SAR Generated", "Yes" if report.get("sar_generated") == "true" else "No")
        
        st.divider()
        
        # Executive Summary
        st.subheader("Executive Audit Summary")
        st.info(report.get("summary", "No summary provided."))
        
        # Specific Violations Table/Cards
        st.subheader("Identified Regulatory Breaches")
        violations = report.get("violations", [])
        
        if violations:
            for idx, v in enumerate(violations):
                with st.expander(f"Violation {idx+1}: {v.get('clause', 'General Section')}", expanded=True):
                    st.write(v.get("description", "No description provided."))
        else:
            st.success("No critical regulatory breaches detected. Document meets foundational compliance standards.")
            
        # Display Final SAR Document if present
        if report.get("sar_content"):
            st.divider()
            st.subheader("Attached Suspicious Activity Report (SAR)")
            st.code(report.get("sar_content"), language="text")
            
        st.divider()
        
        # JSON Export Feature
        st.download_button(
            label="📥 Export Full Audit Package (JSON)",
            data=json.dumps(report, indent=2),
            file_name="compliance_audit_report.json",
            mime="application/json"
        )