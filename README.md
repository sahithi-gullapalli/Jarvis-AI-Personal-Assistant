# ⚡ Jarvis AI Personal Assistant

> **An AI-powered personal assistant for Windows that combines voice commands, conversational AI, intelligent memory, and desktop automation.**

Jarvis is a personal AI assistant designed to make everyday computer tasks easier through natural voice commands and chatbot interactions. It integrates Groq-powered LLMs, a LangGraph agent workflow, ChromaDB-based semantic memory, FastAPI, and a Streamlit dashboard.

---

## 🚀 Key Features

### 🧠 AI-Powered Conversations
- Groq API integration for intelligent responses.
- LangGraph-based agent workflow.
- Multiple model configurations with fallback handling.
- Conversational history management.

### 💾 AI Memory
- ChromaDB for persistent local vector storage.
- Sentence Transformers for semantic embeddings.
- Stores previous conversations and user notes.
- Retrieves relevant information from previous interactions.

### 🎙️ Voice-Controlled Assistant
- Interact with Jarvis using voice commands.
- Launch desktop applications.
- Open websites and play YouTube content.
- Perform supported WhatsApp automation.
- Control system volume.
- Request stock market updates.

### 💬 Chatbot Dashboard
- Interactive Streamlit-based chat interface.
- Ask questions and receive AI-generated responses.
- Access the assistant through a browser.
- Interact with the AI memory functionality.

### 🌐 FastAPI Backend
- REST API for interacting with Jarvis.
- Health-check endpoint.
- AI query endpoint.
- API documentation through Swagger UI.

### 📈 Stock Market Assistant
- Market information and stock analysis.
- Supports Nifty, Reliance, Nvidia, and cryptocurrency queries.
- Provides market-related insights.

### 🛡️ Hybrid AI Failover
- Detects API rate limits.
- Implements automatic cooldown handling.
- Supports model fallback and local command handling.
- Helps maintain functionality when cloud AI is unavailable.

### 🖥️ Holographic Iron Man HUD
Open `jarvis_workplace.html` in your browser to explore the animated Jarvis interface, featuring a cyber-inspired reactor core, globe visualization, audio visualizer, and market information.

---

## 🏗️ Architecture

```text
                 USER
                  |
          +-------+-------+
          |               |
       Voice           Chatbot
     Assistant        Dashboard
          |               |
          +-------+-------+
                  |
             Jarvis Brain
                  |
          +-------+-------+
          |               |
       Local Actions    AI Workflow
                          |
                       LangGraph
                          |
                    Groq LLM API
                          |
                    ChromaDB Memory
                  |
              FastAPI Backend
```

*The current LangGraph implementation provides the foundation for expanding Jarvis into a specialized multi-agent system.*

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| AI / LLM | Groq API, OpenAI-compatible API |
| Agent Workflow | LangGraph |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| Backend | FastAPI, Pydantic |
| Frontend | Streamlit, HTML, CSS, JavaScript |
| Voice & Automation | Python, Windows automation |
| Testing | pytest |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
Jarvis-AI-Personal-Assistant/
│
├── jarvis_brain.py
├── jarvis_agents.py
├── jarvis_memory.py
├── jarvis_actions.py
├── jarvis_voice.py
├── jarvis_market.py
│
├── api_server.py
├── dashboard.py
│
├── jarvis_workplace.html
├── requirements.txt
├── requirements-additions.txt
│
├── install.bat
├── install.sh
│
├── README.md
├── INDEX.md
│
└── data/                  # Local ChromaDB storage (not committed)
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/sahithi-gullapalli/Jarvis-AI-Personal-Assistant.git
cd Jarvis-AI-Personal-Assistant
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-additions.txt
```

### 4. Configure Groq API

Set your Groq API key as an environment variable.

Windows Command Prompt:

```cmd
set GROQ_API_KEY=your_groq_api_key
```

For persistent configuration, add `GROQ_API_KEY` to your Windows environment variables.

Keep your API key private. Never commit it to GitHub.

### 5. Run Jarvis

**Voice assistant:**

```cmd
python jarvis_voice.py
```

**Chatbot dashboard:**

```cmd
streamlit run dashboard.py
```

Open:

```text
http://localhost:8501
```

**FastAPI backend:**

```cmd
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Run each service in a separate terminal when using them simultaneously.

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API health |
| POST | `/ask` | Send a query to Jarvis |

Explore the interactive API documentation at `/docs`.

---

## 🎙️ Example Voice Commands

| Command | Action |
|---|---|
| Open VS Code | Launches Visual Studio Code |
| Play lofi on YouTube | Opens YouTube and plays music |
| Stock market report | Provides market information |
| Check my unread emails | Provides an email briefing, where configured |
| Send WhatsApp message to Pallavi | Opens WhatsApp and drafts a message |
| Volume up / Mute | Controls system volume |

---

## 🔐 Security & Privacy

- API keys are stored outside the source code.
- `.env` and credential files are excluded through `.gitignore`.
- ChromaDB conversation storage remains local.
- The FastAPI server is configured for local access by default.

**Note:** Additional authentication, access controls, and production security hardening are required before exposing the API publicly.

---

## 🚧 Future Enhancements

- Specialized multi-agent architecture.
- Research, Coding, Analysis, and Personal Assistant agents.
- Advanced RAG and knowledge retrieval.
- Improved response speed and optimized memory retrieval.
- Enhanced voice interaction and natural language processing.
- Secure authentication and database protection.
- Automated testing and evaluation.
- Cloud deployment and scalable infrastructure.

---

## 👩‍💻 Developer

**Sahithi Gullapalli**

GitHub: [@sahithi-gullapalli](https://github.com/sahithi-gullapalli)

Project: [Jarvis AI Personal Assistant](https://github.com/sahithi-gullapalli/Jarvis-AI-Personal-Assistant)

---

> *"Your personal AI assistant — built to think, remember, assist, and automate."*

