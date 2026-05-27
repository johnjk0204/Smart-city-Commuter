import time
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentTrace:
    agent_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunMetrics:
    run_id: str
    query: str
    agent_traces: list[AgentTrace] = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    pii_detected: bool = False
    pii_risk_level: str = "NONE"
    evaluation_scores: dict[str, float] = field(default_factory=dict)

    def add_trace(self, trace: AgentTrace):
        self.agent_traces.append(trace)
        self.total_tokens += trace.input_tokens + trace.output_tokens
        self.total_latency_ms += trace.latency_ms

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_agents": len(self.agent_traces),
            "total_latency_ms": round(self.total_latency_ms, 2),
            "total_tokens": self.total_tokens,
            "pii_risk": self.pii_risk_level,
            "agents": [
                {
                    "name": t.agent_name,
                    "latency_ms": round(t.latency_ms, 2),
                    "tokens": t.input_tokens + t.output_tokens,
                    "success": t.success,
                }
                for t in self.agent_traces
            ],
            "evaluation": self.evaluation_scores,
        }


class MonitoringManager:
    """
    Unified monitoring: logs to console + optionally to LangSmith and/or MLflow.
    Gracefully degrades if neither is configured.
    """

    def __init__(self, use_mlflow: bool = False, use_langsmith: bool = False):
        self.use_mlflow = use_mlflow
        self.use_langsmith = use_langsmith
        self._mlflow = None
        self._current_run: Optional[RunMetrics] = None

        if use_mlflow:
            self._init_mlflow()

    def _init_mlflow(self):
        try:
            import mlflow
            from config import MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
            self._mlflow = mlflow
            logger.info("MLflow initialized: %s", MLFLOW_TRACKING_URI)
        except Exception as e:
            logger.warning("MLflow init failed (continuing without): %s", e)
            self._mlflow = None

    def start_run(self, run_id: str, query: str) -> RunMetrics:
        self._current_run = RunMetrics(run_id=run_id, query=query)
        logger.info("[Run %s] Started | Query: %s", run_id, query[:80])
        return self._current_run

    def record_agent(self, trace: AgentTrace):
        if self._current_run:
            self._current_run.add_trace(trace)
        status = "OK" if trace.success else f"ERROR: {trace.error}"
        logger.info(
            "[Agent: %s] latency=%.0fms tokens=%d status=%s",
            trace.agent_name,
            trace.latency_ms,
            trace.input_tokens + trace.output_tokens,
            status,
        )

    def record_pii(self, risk_level: str, detected: bool):
        if self._current_run:
            self._current_run.pii_detected = detected
            self._current_run.pii_risk_level = risk_level

    def record_evaluation(self, scores: dict[str, float]):
        if self._current_run:
            self._current_run.evaluation_scores = scores

    def end_run(self):
        if not self._current_run:
            return

        summary = self._current_run.summary
        logger.info("[Run %s] Complete | %s", self._current_run.run_id, summary)

        if self._mlflow:
            self._log_to_mlflow(summary)

        self._current_run = None

    def _log_to_mlflow(self, summary: dict):
        try:
            with self._mlflow.start_run(run_name=summary["run_id"]):
                self._mlflow.log_param("query_length", len(summary.get("run_id", "")))
                self._mlflow.log_metric("total_latency_ms", summary["total_latency_ms"])
                self._mlflow.log_metric("total_tokens", summary["total_tokens"])
                self._mlflow.log_metric("agent_count", summary["total_agents"])
                for metric, val in summary.get("evaluation", {}).items():
                    self._mlflow.log_metric(f"eval_{metric}", val)
        except Exception as e:
            logger.warning("MLflow logging failed: %s", e)

    @contextmanager
    def trace_agent(self, agent_name: str):
        """Context manager for timing an agent call."""
        start = time.perf_counter()
        trace = AgentTrace(agent_name=agent_name)
        try:
            yield trace
            trace.success = True
        except Exception as e:
            trace.success = False
            trace.error = str(e)
            raise
        finally:
            trace.latency_ms = (time.perf_counter() - start) * 1000
            self.record_agent(trace)
