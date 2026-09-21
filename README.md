# Deskter 🎙️💻
> **Offline Desktop Voice Assistant & Google Antigravity Voice Bridge for Windows**

Deskter is a fast, privacy-respecting, fully offline voice-controlled desktop assistant engineered for Windows 10/11. Powered by local Ollama LLMs (`qwen2.5:3b` / `llama3.1:8b`), ONNX speech synthesis, and an instant sub-millisecond rule-routing engine, Deskter provides complete hands-free desktop control and direct voice bridging into Google Antigravity.

---

## 🌟 Key Features

- ⚡ **Dual-Engine Brain Architecture**:
  - **Fast-Path Rule Matcher (<5ms latency)**: Regex and fuzzy matching for instant system controls, app launches, and queries.
  - **Local Ollama LLM with Tool Calling**: Auto-spawning background Ollama daemon for complex requests, reasoning, and multi-step actions.
- 🗣️ **Ultra-Low Latency Offline Speech**:
  - Sentence-streamed TTS (<150ms time-to-first-audio) with Piper Neural ONNX and SAPI5 fallback.
  - Immediate barge-in support (<15ms cancellation when user interrupts).
- 🌉 **Google Antigravity Voice Bridge**:
  - Voice-controlled token usage tracking, quota queries, model information, and cost estimates.
  - Real-time Antigravity prompt dispatching, mode switching (`accept_edits`, `plan_review`, `ask_question`), and `/goal` slash commands.
- 🛡️ **Three-Tier Safety Gate**:
  - Safe, Sensitive, and High-Risk tier classification with dry-run support and explicit confirmation checks.
- 🤖 **Autonomous AI Testing Agent**:
  - Self-diagnosing continuous testing engine executing 41+ automated scenarios across all system actions.

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
# Interactive mode (Voice + Text + Auto Ollama Server)
python main.py

# Safe Dry-Run Simulation Mode
python main.py --dry-run

# Run Autonomous AI Testing Agent
python main.py --run-agent-tests

# Run Unit Tests
python -m pytest
```

---

## 🛠️ Registered Tools & Capabilities

Deskter includes **39 registered tools** across 7 major domains:

| Category | Tools Included | Example Voice Prompts |
|---|---|---|
| **System Controls** | `get_time`, `get_date`, `set_volume`, `mute`, `set_brightness`, `get_battery`, `screenshot`, `lock_screen`, `shutdown`, `restart` | *"volume 50"*, *"what time is it"*, *"take a screenshot"* |
| **App Management** | `open_app`, `close_app`, `list_running_apps`, `focus_window` | *"open notepad"*, *"open vscode"*, *"close chrome"* |
| **Files & Storage** | `open_folder`, `search_files`, `get_recent_files` | *"open downloads"*, *"open documents"* |
| **Web & Browser** | `open_site`, `web_search`, `open_browser` | *"search for latest AI news"*, *"open youtube"* |
| **Media Playback** | `media_play_pause`, `media_next`, `media_previous`, `media_stop` | *"play music"*, *"next song"*, *"mute audio"* |
| **Notes & Timers** | `take_note`, `get_notes`, `set_timer`, `help` | *"take note buy coffee"*, *"set timer for 5 minutes"* |
| **Antigravity Bridge** | `antigravity_token_usage`, `antigravity_quota`, `antigravity_model_info`, `antigravity_cost_estimate`, `antigravity_prompt`, `antigravity_set_mode`, `antigravity_status`, `antigravity_slash_command`, `antigravity_compact_context`, `antigravity_list_subagents`, `antigravity_clear_history` | *"how much quota do i have"*, *"check token usage"*, *"what model is running"* |

---

## 🧪 Testing & Diagnostics

Deskter has a built-in comprehensive verification suite:
- **Unit Tests**: 51/51 pytest unit tests passing.
- **AI Testing Agent**: 41/41 end-to-end scenarios passing.

```powershell
python -m pytest
python main.py --run-agent-tests
```

---

## 📄 License
MIT License. Built for offline desktop productivity and seamless AI pairing.
