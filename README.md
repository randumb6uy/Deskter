# Deskter 🎙️💻
> **Offline Desktop Voice Assistant & Google Antigravity Voice Bridge for Windows**

Deskter is a fast, privacy-respecting, fully offline voice-controlled desktop assistant engineered for Windows 10/11. Powered by local Ollama LLMs (`qwen2.5:3b` / `llama3.1:8b`), ONNX speech synthesis, and an instant sub-millisecond rule-routing engine, Deskter provides complete hands-free desktop control and direct voice bridging into Google Antigravity.

---

## 🌟 Key Features

- 🧠 **LLM-First Cognitive Brain (Zero Hardcoded Commands Required)**:
  - **Dynamic Natural Language Intent Comprehension**: Speak naturally, casually, or implicitly (e.g. *"it's way too loud in here"*, *"my eyes hurt, dim the display"*, *"I'm stepping away, lock up"*).
  - **Multi-Action Sequencing & Chaining**: Execute compound requests in a single breath (e.g. *"dim the screen to 30 and open notepad"*).
  - **Contextual Pronoun Memory**: Resolves pronouns across dialogue turns (e.g. *"open notepad"* ➔ *"now close it"*).
  - **Pure Conversational QA**: Direct voice answers for knowledge, coding questions, and explanations with zero unwanted tool invocations.
  - **Emergency Override**: Instant sub-millisecond fast-path for emergency stops (*"stop"*, *"cancel"*).
- 🗣️ **Ultra-Low Latency Offline Speech**:
  - Sentence-streamed TTS (<150ms time-to-first-audio) with Piper Neural ONNX and SAPI5 fallback.
  - Immediate barge-in support (<15ms cancellation when user interrupts).
- 🌉 **Google Antigravity Voice Bridge**:
  - Voice-controlled token usage tracking, quota queries, model information, and cost estimates.
  - Real-time Antigravity prompt dispatching, mode switching (`accept_edits`, `plan_review`, `ask_question`), and `/goal` slash commands.
- 🛡️ **Three-Tier Safety Gate**:
  - Safe, Sensitive, and High-Risk tier classification with dry-run support, path confinement, and confirmation checks.
- 🤖 **Autonomous AI Testing Agent**:
  - Self-diagnosing continuous testing engine executing 63+ automated end-to-end scenarios.

---

## 🚀 Quick Start

### Prerequisites
- Windows 10 / 11 Pro
- Python 3.11+
- [Ollama](https://ollama.com) (installed with `qwen2.5:3b` or `llama3.1:8b`)

### Installation
```bash
# Clone the repository
git clone https://github.com/randumb6uy/Deskter.git
cd Deskter

# Install dependencies
pip install -e .
```

### Running Deskter
Double-click `run.bat` or run via terminal:
```powershell
# Interactive Cognitive Mode (Voice + Text + Auto Ollama Server)
python main.py

# Safe Dry-Run Simulation Mode
python main.py --dry-run

# Run Autonomous AI Testing Agent (63 Scenarios)
python main.py --run-agent-tests

# Run Full Pytest Suite (59 Unit Tests)
python -m pytest
```

---

## 🛠️ Registered Tools & Capabilities

Deskter includes **39 registered tools** across 7 major domains:

| Category | Tools Included | Example Natural Prompts |
|---|---|---|
| **System Controls** | `get_time`, `get_date`, `set_volume`, `mute`, `set_brightness`, `get_battery`, `screenshot`, `lock_screen`, `shutdown`, `restart` | *"it's too loud in here"*, *"my eyes hurt, dim screen"*, *"how much battery juice is left"* |
| **App Management** | `open_app`, `close_app`, `list_running_apps`, `focus_window` | *"open visual studio code"*, *"now close it"*, *"what apps are running"* |
| **Files & Storage** | `open_folder`, `search_files`, `get_recent_files` | *"let me see my downloads folder"*, *"find my python script"* |
| **Web & Browser** | `open_site`, `web_search`, `open_browser` | *"search for async python tutorials in browser"*, *"open youtube for me"* |
| **Media Playback** | `media_play_pause`, `media_next`, `media_previous`, `media_stop` | *"pause the video"*, *"skip to the next track"*, *"mute audio"* |
| **Notes & Timers** | `take_note`, `get_notes`, `set_timer`, `help` | *"take note that meeting is at 4 PM"*, *"read my saved notes"* |
| **Antigravity Bridge** | `antigravity_token_usage`, `antigravity_quota`, `antigravity_model_info`, `antigravity_cost_estimate`, `antigravity_prompt`, `antigravity_set_mode`, `antigravity_status`, `antigravity_slash_command`, `antigravity_compact_context`, `antigravity_list_subagents`, `antigravity_clear_history` | *"how many tokens have I used so far"*, *"what model is loaded"*, *"check my remaining quota"* |

---

## 🧪 Testing & Diagnostics

Deskter has a built-in comprehensive verification suite:
- **Unit Tests**: **59/59 pytest unit tests passing** (100%).
- **AI Testing Agent**: **63/63 end-to-end scenarios passing** (100%).

```powershell
python -m pytest
python main.py --run-agent-tests
```

---

## 📄 License
MIT License. Built for offline desktop productivity and seamless AI pairing.

