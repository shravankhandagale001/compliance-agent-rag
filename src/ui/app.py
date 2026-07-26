import streamlit as st
import requests

# Point to our local FastAPI server
API_URL = "http://127.0.0.1:8000/audit"

# Configure the page layout
st.set_page_config(page_title="AI Compliance Auditor", page_icon="🏦", layout="centered")

st.title("🏦 Multi-Agent Compliance Auditor")
st.markdown("Upload your business proposal text below. Our AI agents will audit it against financial regulations.")

# Input area for the user's proposal
proposal_text = st.text_area("Business Proposal", height=200, placeholder="Paste the proposal text here...")

if st.button("Run Audit", type="primary"):
    if not proposal_text.strip():
        st.warning("Please enter a proposal to audit.")
    else:
        with st.spinner("Agents are analyzing the proposal. This may take a moment running locally..."):
            try:
                # Send the text to our FastAPI backend
                response = requests.post(API_URL, json={"proposal_text": proposal_text})
                
                if response.status_code == 200:
                    report = response.json()
                    
                    st.divider()
                    st.subheader("Audit Results")
                    
                    # Display top-level metrics
                    col1, col2 = st.columns(2)
                    col1.metric("Approval Status", report.get("status", "UNKNOWN"))
                    col2.metric("Assigned Risk Level", report.get("risk_level", "UNKNOWN"))
                    
                    st.write("**Executive Summary:**")
                    st.info(report.get("summary", "No summary provided."))
                    
                    # Display specific violations if they exist
                    violations = report.get("violations", [])
                    if violations:
                        st.error(f"Found {len(violations)} Compliance Violation(s)")
                        for v in violations:
                            with st.expander(v.get("clause", "Unknown Clause")):
                                st.write(v.get("description", "No description provided."))
                    else:
                        st.success("No compliance violations detected! The proposal meets regulatory standards.")
                else:
                    st.error(f"API Error: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to the backend. Is your FastAPI server still running?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")