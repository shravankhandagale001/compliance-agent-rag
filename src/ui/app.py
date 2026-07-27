import streamlit as st
import requests

# Point to our new FastAPI file upload endpoint
API_URL_FILE = "http://127.0.0.1:8000/audit/file"

st.set_page_config(page_title="Enterprise Compliance Auditor", page_icon="🏦", layout="centered")

st.title("🏦 Enterprise Compliance Auditor")
st.markdown("Upload your business proposal document (PDF). Our AI agents will extract the text, analyze the context, and audit it against regulatory frameworks.")

# NEW: File Uploader Widget
uploaded_file = st.file_uploader("Upload Proposal Document", type=["pdf"])

if st.button("Run Document Audit", type="primary"):
    if uploaded_file is None:
        st.warning("Please upload a PDF document to begin the audit.")
    else:
        with st.spinner("Agents are reading the document and analyzing compliance. This may take a moment running locally..."):
            try:
                # Prepare the file for sending via HTTP POST
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                
                # Send the file to FastAPI
                response = requests.post(API_URL_FILE, files=files)
                
                if response.status_code == 200:
                    report = response.json()
                    
                    st.divider()
                    st.subheader(f"Audit Results: {uploaded_file.name}")
                    
                    # Display top-level metrics
                    col1, col2 = st.columns(2)
                    col1.metric("Approval Status", report.get("status", "UNKNOWN"))
                    col2.metric("Assigned Risk Level", report.get("risk_level", "UNKNOWN"))
                    
                    st.write("**Executive Summary:**")
                    st.info(report.get("summary", "No summary provided."))
                    
                    # Display specific violations
                    violations = report.get("violations", [])
                    if violations:
                        st.error(f"Found {len(violations)} Compliance Violation(s)")
                        for v in violations:
                            with st.expander(v.get("clause", "Unknown Clause")):
                                st.write(v.get("description", "No description provided."))
                    else:
                        st.success("No compliance violations detected! The proposal meets regulatory standards.")
                else:
                    st.error(f"API Error: {response.json().get('detail', response.text)}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to the backend. Is your FastAPI server still running?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")