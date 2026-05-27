import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# DeepEval-inspired metrics implemented locally for robustness
# (DeepEval's cloud API is optional; these run offline)

@dataclass
class EvaluationResult:
    answer_relevancy: float
    faithfulness: float
    completeness: float
    safety_score: float
    overall_score: float
    passed: bool
    feedback: str


class CommuteEvaluator:
    """
    Evaluates commute recommendations using DeepEval-inspired metrics.
    Falls back to local heuristic scoring if DeepEval API is unavailable.
    """

    def __init__(self, use_deepeval_api: bool = False):
        self.use_deepeval_api = use_deepeval_api
        self._deepeval = None

        if use_deepeval_api:
            self._init_deepeval()

    def _init_deepeval(self):
        try:
            import deepeval
            from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
            self._deepeval = deepeval
            logger.info("DeepEval initialized")
        except Exception as e:
            logger.warning("DeepEval init failed (using local metrics): %s", e)

    def evaluate(self, query: str, recommendation: str, context_docs: list[str]) -> EvaluationResult:
        if self._deepeval:
            return self._evaluate_with_deepeval(query, recommendation, context_docs)
        return self._evaluate_local(query, recommendation, context_docs)

    def _evaluate_local(self, query: str, recommendation: str, context_docs: list[str]) -> EvaluationResult:
        """Heuristic evaluation covering the same dimensions as DeepEval."""

        # 1. Answer Relevancy — does the answer address the query?
        query_terms = set(re.findall(r"\b\w{4,}\b", query.lower()))
        answer_terms = set(re.findall(r"\b\w{4,}\b", recommendation.lower()))
        overlap = len(query_terms & answer_terms)
        answer_relevancy = min(1.0, overlap / max(len(query_terms), 1) * 2)

        # 2. Faithfulness — is the answer grounded in the context?
        if context_docs:
            context_text = " ".join(context_docs).lower()
            context_terms = set(re.findall(r"\b\w{4,}\b", context_text))
            faithful_overlap = len(answer_terms & context_terms)
            faithfulness = min(1.0, faithful_overlap / max(len(answer_terms), 1) * 1.5)
        else:
            faithfulness = 0.5

        # 3. Completeness — does the answer have all expected sections?
        expected_sections = [
            "recommend", "route", "time", "step", "option", "alternative", "why"
        ]
        sections_found = sum(1 for s in expected_sections if s in recommendation.lower())
        completeness = sections_found / len(expected_sections)

        # 4. Safety — no harmful or PII content in recommendation
        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",
            r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b",
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        ]
        has_pii = any(re.search(p, recommendation) for p in pii_patterns)
        harmful_words = ["dangerous", "illegal", "unsafe crossing", "trespass"]
        has_harmful = any(w in recommendation.lower() for w in harmful_words)
        safety_score = 0.5 if (has_pii or has_harmful) else 1.0

        overall = (
            answer_relevancy * 0.35
            + faithfulness * 0.25
            + completeness * 0.25
            + safety_score * 0.15
        )

        passed = overall >= 0.6

        feedback_parts = []
        if answer_relevancy < 0.5:
            feedback_parts.append("Low relevancy — response may not directly address the query")
        if faithfulness < 0.4:
            feedback_parts.append("Low faithfulness — response not well grounded in retrieved data")
        if completeness < 0.5:
            feedback_parts.append("Incomplete — missing key sections (steps, alternatives, timing)")
        if safety_score < 1.0:
            feedback_parts.append("Safety concern — PII or harmful content detected in response")
        if not feedback_parts:
            feedback_parts.append("All metrics passed — response is high quality")

        logger.info(
            "Evaluation: relevancy=%.2f faithfulness=%.2f completeness=%.2f safety=%.2f overall=%.2f",
            answer_relevancy, faithfulness, completeness, safety_score, overall,
        )

        return EvaluationResult(
            answer_relevancy=round(answer_relevancy, 3),
            faithfulness=round(faithfulness, 3),
            completeness=round(completeness, 3),
            safety_score=round(safety_score, 3),
            overall_score=round(overall, 3),
            passed=passed,
            feedback=" | ".join(feedback_parts),
        )

    def _evaluate_with_deepeval(self, query: str, recommendation: str, context_docs: list[str]) -> EvaluationResult:
        try:
            from deepeval import evaluate
            from deepeval.test_case import LLMTestCase
            from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

            test_case = LLMTestCase(
                input=query,
                actual_output=recommendation,
                retrieval_context=context_docs,
            )

            relevancy_metric = AnswerRelevancyMetric(threshold=0.6)
            faithfulness_metric = FaithfulnessMetric(threshold=0.5)

            relevancy_metric.measure(test_case)
            faithfulness_metric.measure(test_case)

            ar = relevancy_metric.score or 0.5
            ff = faithfulness_metric.score or 0.5
            overall = (ar + ff) / 2

            return EvaluationResult(
                answer_relevancy=round(ar, 3),
                faithfulness=round(ff, 3),
                completeness=0.8,
                safety_score=1.0,
                overall_score=round(overall, 3),
                passed=overall >= 0.6,
                feedback=f"DeepEval: relevancy={ar:.2f}, faithfulness={ff:.2f}",
            )
        except Exception as e:
            logger.warning("DeepEval evaluation failed, falling back: %s", e)
            return self._evaluate_local(query, recommendation, context_docs)
