# Deskter AI Testing Agent Report

**Status:** [OK] ALL TESTS PASSED  
**Execution Timestamp:** `2026-09-21 12:56:01`  
**Total Tests:** `41` | **Passed:** `41` | **Failed:** `0` | **Pass Rate:** `100.0%`  
**Duration:** `2.36s`  

---

## Test Case Details

| Category | Test Name | Result | Latency | Details |
|---|---|---|---|---|
| Registry | `Tool Registration Count` | **[PASS]** | 1.0ms | Discovered 39 registered tools. |
| Registry | `Ollama JSON Schema Generation` | **[PASS]** | 0.0ms | Generated 39 valid Ollama function schemas. |
| Rules - Time & Date | `Scenario: Fast-path current time query` | **[PASS]** | 2.3ms | Input: 'what time is it' -> Tool: 'get_time' |
| Rules - Time & Date | `Scenario: Fast-path current date query` | **[PASS]** | 0.5ms | Input: 'what is today's date' -> Tool: 'get_date' |
| Rules - Time & Date | `Scenario: Fast-path day query with wakeword prefix` | **[PASS]** | 0.0ms | Input: 'Hey Deskter what day is today' -> Tool: 'get_date' |
| Rules - System Controls | `Scenario: Volume adjustment percentage` | **[PASS]** | 1.1ms | Input: 'volume 75' -> Tool: 'set_volume' |
| Rules - System Controls | `Scenario: Relative volume up` | **[PASS]** | 0.0ms | Input: 'volume up' -> Tool: 'set_volume' |
| Rules - System Controls | `Scenario: Mute toggle` | **[PASS]** | 0.0ms | Input: 'mute audio' -> Tool: 'mute' |
| Rules - System Controls | `Scenario: Brightness level adjustment` | **[PASS]** | 0.6ms | Input: 'set brightness to 60' -> Tool: 'set_brightness' |
| Rules - System Controls | `Scenario: Battery status check` | **[PASS]** | 0.0ms | Input: 'check battery percentage' -> Tool: 'get_battery' |
| Rules - System Controls | `Scenario: Screenshot capture` | **[PASS]** | 0.0ms | Input: 'take a screenshot' -> Tool: 'screenshot' |
| Rules - System Controls | `Scenario: Lock workstation` | **[PASS]** | 0.0ms | Input: 'lock workstation' -> Tool: 'lock_screen' |
| Rules - Media | `Scenario: Media play pause toggle` | **[PASS]** | 0.0ms | Input: 'play pause' -> Tool: 'media_play_pause' |
| Rules - Media | `Scenario: Media next track` | **[PASS]** | 0.0ms | Input: 'next song' -> Tool: 'media_next' |
| Rules - Web & Browser | `Scenario: Web search query` | **[PASS]** | 4.0ms | Input: 'search for local weather forecast' -> Tool: 'web_search' |
| Rules - Web & Browser | `Scenario: Open well known site` | **[PASS]** | 0.0ms | Input: 'open youtube' -> Tool: 'open_site' |
| Rules - Web & Browser | `Scenario: Launch default browser` | **[PASS]** | 0.0ms | Input: 'open browser' -> Tool: 'open_browser' |
| Rules - Apps & Files | `Scenario: Launch application by name` | **[PASS]** | 0.5ms | Input: 'open notepad' -> Tool: 'open_app' |
| Rules - Apps & Files | `Scenario: Close running application` | **[PASS]** | 0.0ms | Input: 'close notepad' -> Tool: 'close_app' |
| Rules - Apps & Files | `Scenario: Open Downloads folder` | **[PASS]** | 0.0ms | Input: 'open downloads' -> Tool: 'open_folder' |
| Rules - Utility | `Scenario: Save quick note` | **[PASS]** | 0.0ms | Input: 'take note test autonomous agent scenario' -> Tool: 'take_note' |
| Rules - Utility | `Scenario: Retrieve saved notes` | **[PASS]** | 0.0ms | Input: 'get notes' -> Tool: 'get_notes' |
| Rules - Utility | `Scenario: Set countdown timer` | **[PASS]** | 0.0ms | Input: 'set timer for 2 minutes' -> Tool: 'set_timer' |
| Rules - Utility | `Scenario: Display help information` | **[PASS]** | 0.0ms | Input: 'help' -> Tool: 'help' |
| Rules - Brain Routing | `Scenario: Multi-step command with conjunction` | **[PASS]** | 0.0ms | Input: 'Open Chrome and then search for quantum computing' -> Tool: 'None' |
| Rules - Brain Routing | `Scenario: Conversational knowledge question` | **[PASS]** | 0.0ms | Input: 'Explain how neural networks learn in simple terms' -> Tool: 'None' |
| Rules - Security & Safety | `Scenario: High risk shutdown command` | **[PASS]** | 0.0ms | Input: 'shutdown computer' -> Tool: 'shutdown' |
| Rules - Antigravity | `Scenario: Check token usage` | **[PASS]** | 0.0ms | Input: 'check the usage of tokens' -> Tool: 'antigravity_token_usage' |
| Rules - Antigravity | `Scenario: Change mode to accept edits` | **[PASS]** | 0.0ms | Input: 'change mode to accept edits' -> Tool: 'antigravity_set_mode' |
| Rules - Antigravity | `Scenario: Send voice coding prompt` | **[PASS]** | 0.0ms | Input: 'ask Antigravity to create a login component' -> Tool: 'antigravity_prompt' |
| Rules - Antigravity | `Scenario: Check Antigravity status` | **[PASS]** | 0.0ms | Input: 'antigravity status' -> Tool: 'antigravity_status' |
| Rules - Antigravity | `Scenario: Trigger /goal slash command` | **[PASS]** | 0.0ms | Input: '/goal' -> Tool: 'antigravity_slash_command' |
| Rules - Antigravity | `Scenario: Compact conversation context` | **[PASS]** | 0.0ms | Input: 'compact context' -> Tool: 'antigravity_compact_context' |
| Rules - Antigravity | `Scenario: Check remaining quota and limits` | **[PASS]** | 0.0ms | Input: 'how much quota do i have' -> Tool: 'antigravity_quota' |
| Rules - Antigravity | `Scenario: Check active model information` | **[PASS]** | 0.0ms | Input: 'what model is running' -> Tool: 'antigravity_model_info' |
| Memory | `Conversation Memory Turn Trimming` | **[PASS]** | 0.0ms | Kept 5 items within 2 turns limit. |
| Memory | `Memory Inactivity Expiration` | **[PASS]** | 81.8ms | Memory successfully cleared after inactivity timeout. |
| Safety | `Safety Gate Dry-Run Intercept` | **[PASS]** | 0.6ms | High-risk command safely intercepted in dry run mode. |
| Router | `Router Fast-Path Dispatch` | **[PASS]** | 1898.7ms | Fast path response: '[Dry Run] I would execute get_time with {}.' |
| Audio / TTS | `TTS Sentence Streaming Splitter` | **[PASS]** | 0.5ms | Split text into 3 streaming sentence chunks. |
| Audio / TTS | `SAPI5 Offline Speech Synthesis` | **[PASS]** | 360.5ms | Synthesized speech WAV in 360.5ms (<150ms target). |

---
*(Report generated automatically by Deskter Autonomous Testing Agent)*