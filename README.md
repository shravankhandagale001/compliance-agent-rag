# 🛡️ Sentinel AI - Regulatory Compliance Audit System

Sentinel AI is a production-grade, multi-agent AI system that automates pre-launch regulatory compliance reviews for financial products, cross-referencing Product Requirements Documents (PRDs) against regulatory guidelines to flag potential violations before launch.

## 📋 Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [License](#license)

## 🚀 Features
* **1-Million Token Context Window:** Powered by the `gemini-2.5-flash` model, allowing entire regulatory documents to be processed in a single pass.
* **Vision-Language Parsing:** Replaces standard PyPDF text scraping with `PyMuPDF4LLM` for higher-fidelity document understanding.
* **Human-in-the-Loop (HITL) Workflow:** Built with `LangGraph` state memory (`MemorySaver`) to pause for human review before finalizing reports.
* **Enterprise Dashboard:** A custom-styled `Streamlit` interface featuring real-time audit tracking and reporting.

## 🏗️ Architecture
1. **Ingestion Phase:** Regulatory PDFs are parsed via structural Markdown and embedded into a vector store.
2. **Retriever Agent:** Extracts key technical entities from the PRD and runs a semantic search against the regulatory knowledge base.
3. **Auditor Agent:** Cross-references the extracted regulations against the PRD. If violations are detected, they are flagged for review.
4. **SAR Drafter Agent (HITL):** Automatically writes a Suspicious Activity Report. This step requires human approval before proceeding.
5. **Reporter Agent:** Once a human approves the SAR, this agent formats the final compliance report.

## 🛠️ Tech Stack
* **AI & Orchestration:** LangGraph, LangChain, Gemini 2.5 Flash (`langchain-google-genai`)
* **Vector Database & Embeddings:** ChromaDB, HuggingFace (`sentence-transformers`)
* **Document Processing:** PyMuPDF4LLM
* **Backend:** FastAPI, Uvicorn
* **Frontend:** Streamlit

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shravankhandagale001/compliance-agent-rag.git
   cd compliance-agent-rag
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your Google AI Studio API key:
   ```
   GEMINI_API_KEY="your_api_key_here"
   ```

5. **Ingest Regulatory Data:**
   Place your regulatory PDFs (e.g., RBI guidelines) in the `data/` folder, then run the ingestion script:
   ```bash
   python src/retrieval/ingest.py
   ```

## 💻 Usage

1. **Start the FastAPI Backend:**
   ```bash
   python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Start the Streamlit Frontend:**
   Open a new terminal window, activate the virtual environment, and run:
   ```bash
   streamlit run src/ui/app.py
   ```

3. **Audit a Document:**
   Upload a Product Requirements Document (PDF) via the Streamlit UI to initiate the multi-agent audit and review the generated compliance report.

## 📄 License

This project is licensed under the MIT License.
