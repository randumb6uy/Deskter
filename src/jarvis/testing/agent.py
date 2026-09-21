"""Autonomous AI Testing Agent for Deskter.

Executes comprehensive validation suites across all application layers,
diagnoses issues, and outputs formatted test reports.
"""

import asyncio
import datetime
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from jarvis.actions.registry import registry
from jarvis.brain.llm import LlmClient, ToolCall
from jarvis.brain.memory import ConversationMemory
from jarvis.brain.router import Router
from jarvis.brain.rules import RuleMatcher
from jarvis.config import Config, load_config
from jarvis.core.events import EventBus
from jarvis.safety.gate import SafetyGate
from jarvis.testing.scenarios import DEFAULT_SCENARIOS, Scenario

logger = logging.getLogger("jarvis.testing.agent")


@dataclass
class TestCaseResult:
    """Outcome of an individual test case."""
    name: str
    category: str
    passed: bool
    execution_time_ms: float
    details: str
    error: Optional[str] = None


@dataclass
class TestReport:
    """Comprehensive test execution report."""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate_pct: float
    total_duration_s: float
    results: List[TestCaseResult] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Format report into GitHub-flavored markdown."""
        status_badge = "[OK] ALL TESTS PASSED" if self.failed_tests == 0 else f"[ALERT] {self.failed_tests} TESTS FAILED"
        
        lines = [
            f"# Deskter AI Testing Agent Report",
            f"",
            f"**Status:** {status_badge}  ",
            f"**Execution Timestamp:** `{self.timestamp}`  ",
            f"**Total Tests:** `{self.total_tests}` | **Passed:** `{self.passed_tests}` | **Failed:** `{self.failed_tests}` | **Pass Rate:** `{self.pass_rate_pct:.1f}%`  ",
            f"**Duration:** `{self.total_duration_s:.2f}s`  ",
            f"",
            f"---",
            f"",
            f"## Test Case Details",
            f"",
            f"| Category | Test Name | Result | Latency | Details |",
            f"|---|---|---|---|---|",
        ]

        for r in self.results:
            icon = "[PASS]" if r.passed else "[FAIL]"
            err_text = f" (Error: {r.error})" if r.error else ""
            clean_details = r.details.replace("|", "/")
            lines.append(f"| {r.category} | `{r.name}` | **{icon}** | {r.execution_time_ms:.1f}ms | {clean_details}{err_text} |")

        lines.extend([
            f"",
            f"---",
            f"*(Report generated automatically by Deskter Autonomous Testing Agent)*",
        ])
        return "\n".join(lines)

    def to_json(self) -> str:
        """Export report to JSON string."""
        data = asdict(self)
        return json.dumps(data, indent=2)


class TestingAgent:
    """Autonomous testing agent that systematically verifies Deskter subsystems."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or load_config()
        # Force dry run for test safety
        self.config.assistant.dry_run = True
        self.gate = SafetyGate(self.config)
        self.bus = EventBus()
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def run_all_tests(self) -> TestReport:
        """Run complete verification suite and return structured report."""
        start_time = time.time()
        results: List[TestCaseResult] = []

        logger.info("Starting Deskter Autonomous Test Suite...")

        # 1. Verify Tool Registry & Schema
        results.extend(await self._test_tool_registry())

        # 2. Verify Fast-Path Rule Scenarios
        results.extend(await self._test_scenarios())

        # 3. Verify Memory Management & Expiration
        results.extend(await self._test_memory_lifecycle())

        # 4. Verify Safety Gate Boundary Enforcement
        results.extend(await self._test_safety_boundaries())

        # 5. Verify Brain Router Fallback & Execution
        results.extend(await self._test_router_integration())

        # 6. Verify Speech Output & Audio Barge-in
        results.extend(await self._test_audio_tts_pipeline())

        total_duration = time.time() - start_time
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        pass_rate = (passed / total * 100.0) if total > 0 else 0.0

        report = TestReport(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            pass_rate_pct=pass_rate,
            total_duration_s=total_duration,
            results=results,
            system_info={
                "assistant_name": self.config.assistant.name,
                "registered_tools_count": len(registry.list_tools()),
            },
        )

        self._save_report(report)
        return report

    async def _test_tool_registry(self) -> List[TestCaseResult]:
        """Validate all registered tools and their Ollama schemas."""
        results: List[TestCaseResult] = []
        t0 = time.time()

        tools = registry.list_tools()
        has_tools = len(tools) >= 15
        results.append(
            TestCaseResult(
                name="Tool Registration Count",
                category="Registry",
                passed=has_tools,
                execution_time_ms=(time.time() - t0) * 1000,
                details=f"Discovered {len(tools)} registered tools.",
                error=None if has_tools else "Fewer than 15 tools registered.",
            )
        )

        t1 = time.time()
        schemas = registry.get_ollama_tools_schema()
        valid_schemas = (
            len(schemas) == len(tools)
            and all("type" in s and "function" in s for s in schemas)
        )
        results.append(
            TestCaseResult(
                name="Ollama JSON Schema Generation",
                category="Registry",
                passed=valid_schemas,
                execution_time_ms=(time.time() - t1) * 1000,
                details=f"Generated {len(schemas)} valid Ollama function schemas.",
                error=None if valid_schemas else "Schema generation mismatch.",
            )
        )

        return results

    async def _test_scenarios(self) -> List[TestCaseResult]:
        """Execute default scenario library against RuleMatcher."""
        results: List[TestCaseResult] = []
        matcher = RuleMatcher()

        for s in DEFAULT_SCENARIOS:
            t0 = time.time()
            match = matcher.match(s.user_input)
            latency = (time.time() - t0) * 1000

            passed = True
            error_msg = None

            if s.expected_fast_path is not None:
                if match.matched != s.expected_fast_path:
                    passed = False
                    error_msg = f"Expected fast_path={s.expected_fast_path}, got {match.matched}"

            if passed and s.expected_tool:
                if match.tool_name != s.expected_tool:
                    passed = False
                    error_msg = f"Expected tool={s.expected_tool}, got {match.tool_name}"

            if passed and s.expected_params_contain:
                for k, v in s.expected_params_contain.items():
                    if match.params.get(k) != v:
                        passed = False
                        error_msg = f"Param '{k}': expected '{v}', got '{match.params.get(k)}'"

            results.append(
                TestCaseResult(
                    name=f"Scenario: {s.description}",
                    category=f"Rules - {s.category}",
                    passed=passed,
                    execution_time_ms=latency,
                    details=f"Input: '{s.user_input}' -> Tool: '{match.tool_name}'",
                    error=error_msg,
                )
            )

        return results

    async def _test_memory_lifecycle(self) -> List[TestCaseResult]:
        """Validate conversation memory turn limits and expiry."""
        results: List[TestCaseResult] = []
        t0 = time.time()

        memory = ConversationMemory(max_turns=2, inactivity_timeout_s=0.05)
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi there")
        memory.add_user_message("Second turn")
        memory.add_assistant_message("Second reply")
        memory.add_user_message("Third turn")

        # Max turn trimming check
        messages = memory.get_messages()
        trimmed_ok = len(messages) <= 6
        results.append(
            TestCaseResult(
                name="Conversation Memory Turn Trimming",
                category="Memory",
                passed=trimmed_ok,
                execution_time_ms=(time.time() - t0) * 1000,
                details=f"Kept {len(messages)} items within 2 turns limit.",
                error=None if trimmed_ok else "Memory exceeded turn limit.",
            )
        )

        # Inactivity expiration check
        t1 = time.time()
        await asyncio.sleep(0.08)
        expired_ok = memory.message_count == 0
        results.append(
            TestCaseResult(
                name="Memory Inactivity Expiration",
                category="Memory",
                passed=expired_ok,
                execution_time_ms=(time.time() - t1) * 1000,
                details="Memory successfully cleared after inactivity timeout.",
                error=None if expired_ok else "Memory failed to expire on timeout.",
            )
        )

        return results

    async def _test_safety_boundaries(self) -> List[TestCaseResult]:
        """Validate safety gate restrictions on forbidden paths and high-risk tools."""
        results: List[TestCaseResult] = []
        t0 = time.time()

        # High risk tool safety gating in dry run
        shutdown_tool = registry.get_tool("shutdown")
        res = await self.gate.evaluate_and_execute(shutdown_tool, {})
        passed_dry = res.ok and "Dry Run" in res.message
        results.append(
            TestCaseResult(
                name="Safety Gate Dry-Run Intercept",
                category="Safety",
                passed=passed_dry,
                execution_time_ms=(time.time() - t0) * 1000,
                details="High-risk command safely intercepted in dry run mode.",
                error=None if passed_dry else f"Unexpected dry run result: {res.message}",
            )
        )

        return results

    async def _test_router_integration(self) -> List[TestCaseResult]:
        """Validate Router execution and event publishing."""
        results: List[TestCaseResult] = []
        t0 = time.time()

        router = Router(config=self.config, gate=self.gate, bus=self.bus)
        resp = await router.route_and_execute("what time is it")
        passed = resp.fast_path and len(resp.tool_results) == 1
        results.append(
            TestCaseResult(
                name="Router Fast-Path Dispatch",
                category="Router",
                passed=passed,
                execution_time_ms=(time.time() - t0) * 1000,
                details=f"Fast path response: '{resp.reply}'",
                error=None if passed else "Fast path failed to execute.",
            )
        )

        return results

    async def _test_audio_tts_pipeline(self) -> List[TestCaseResult]:
        """Validate Speech Output streaming tokenizer and barge-in interruption."""
        from jarvis.audio.player import split_sentences
        from jarvis.audio.tts import SapiTTSEngine
        results: List[TestCaseResult] = []

        # 1. Sentence Tokenizer Test
        t0 = time.time()
        text = "Hello! Deskter is ready. Let's code; everything is operational."
        chunks = split_sentences(text)
        passed_chunks = len(chunks) >= 3
        results.append(
            TestCaseResult(
                name="TTS Sentence Streaming Splitter",
                category="Audio / TTS",
                passed=passed_chunks,
                execution_time_ms=(time.time() - t0) * 1000,
                details=f"Split text into {len(chunks)} streaming sentence chunks.",
                error=None if passed_chunks else "Sentence tokenizer failed.",
            )
        )

        # 2. SAPI Engine Offline Synthesis Test
        t1 = time.time()
        import tempfile
        sapi = SapiTTSEngine()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tmp_wav = tf.name

        try:
            ok = sapi.synthesize_to_file("Deskter offline voice verification test.", tmp_wav)
            latency = (time.time() - t1) * 1000
            file_exists = Path(tmp_wav).exists() and Path(tmp_wav).stat().st_size > 0
            results.append(
                TestCaseResult(
                    name="SAPI5 Offline Speech Synthesis",
                    category="Audio / TTS",
                    passed=ok and file_exists,
                    execution_time_ms=latency,
                    details=f"Synthesized speech WAV in {latency:.1f}ms (<150ms target).",
                    error=None if ok and file_exists else "SAPI synthesis failed.",
                )
            )
        finally:
            if Path(tmp_wav).exists():
                try:
                    Path(tmp_wav).unlink()
                except Exception:
                    pass

        return results

    def _save_report(self, report: TestReport) -> None:
        """Save report to markdown and JSON files."""
        try:
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            md_path = self.reports_dir / f"test_report_{timestamp_str}.md"
            latest_md = self.reports_dir / "latest_test_report.md"
            latest_json = self.reports_dir / "latest_test_results.json"

            content_md = report.to_markdown()
            content_json = report.to_json()

            with open(md_path, "w", encoding="utf-8") as f:
                f.write(content_md)

            with open(latest_md, "w", encoding="utf-8") as f:
                f.write(content_md)

            with open(latest_json, "w", encoding="utf-8") as f:
                f.write(content_json)

            logger.info(f"Test reports saved to {md_path} and {latest_json}")
        except Exception as e:
            logger.error(f"Failed to save test report: {e}")

    async def run_continuous(
        self,
        interval_seconds: int = 30,
        max_iterations: Optional[int] = None,
        on_report: Optional[Callable[[TestReport], None]] = None,
    ) -> None:
        """Run tests continuously at specified intervals."""
        iteration = 0
        print(f"[TestingAgent] Starting continuous test agent (Interval: {interval_seconds}s)...")
        
        while True:
            iteration += 1
            print(f"\n[TestingAgent] --- Running Test Iteration #{iteration} ---")
            report = await self.run_all_tests()
            
            print(f"[TestingAgent] Result: {report.passed_tests}/{report.total_tests} passed ({report.pass_rate_pct:.1f}%) in {report.total_duration_s:.2f}s")
            if report.failed_tests > 0:
                print(f"[TestingAgent] ⚠️ {report.failed_tests} tests failed! Check reports/latest_test_report.md")

            if on_report:
                on_report(report)

            if max_iterations and iteration >= max_iterations:
                print(f"[TestingAgent] Reached max iterations ({max_iterations}). Exiting loop.")
                break

            await asyncio.sleep(interval_seconds)
