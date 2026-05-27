"""
Extractive prompt compressor — scores retrieved context sentences by TF-IDF
relevance to the query and retains only the top-k, reducing LLM input tokens
without extra API calls or heavy ML dependencies.
"""
import re
import math
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "this", "that", "it", "its", "as", "so", "if", "not", "no", "can",
    "will", "may", "has", "have", "had", "do", "does", "did", "would",
    "could", "should", "also", "more", "than", "up", "out",
}


@dataclass
class CompressionStats:
    original_chars: int = 0
    compressed_chars: int = 0
    original_sentences: int = 0
    compressed_sentences: int = 0
    agent: str = ""

    @property
    def char_reduction_pct(self) -> float:
        if self.original_chars == 0:
            return 0.0
        return (1 - self.compressed_chars / self.original_chars) * 100

    def __str__(self) -> str:
        return (
            f"[{self.agent}] {self.original_sentences}→{self.compressed_sentences} sentences, "
            f"{self.original_chars}→{self.compressed_chars} chars "
            f"({self.char_reduction_pct:.0f}% reduction)"
        )


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"\b[a-z]{2,}\b", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _split_sentences(text: str) -> list[str]:
    # Split on sentence boundaries and newlines; drop very short fragments
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [s.strip() for s in parts if len(s.strip()) > 15]


def _tfidf_scores(query_tokens: list[str], sentences: list[str]) -> list[float]:
    """Score each sentence against the query using TF-IDF."""
    N = len(sentences)
    tokenized = [_tokenize(s) for s in sentences]
    query_set = set(query_tokens)
    scores = []

    for sent_tokens in tokenized:
        if not sent_tokens:
            scores.append(0.0)
            continue
        score = 0.0
        for term in query_set:
            tf = sent_tokens.count(term) / len(sent_tokens)
            df = sum(1 for t in tokenized if term in t)
            idf = math.log((N + 1) / (df + 1)) + 1.0
            score += tf * idf
        scores.append(score)

    return scores


class PromptCompressor:
    """
    Compresses retrieved context by keeping only the most query-relevant
    sentences. Uses TF-IDF scoring — no API calls, no extra dependencies.

    Args:
        compression_ratio: Fraction of sentences to drop (0.5 = keep 50%).
        min_sentences:     Always keep at least this many sentences.
    """

    def __init__(self, compression_ratio: float = 0.5, min_sentences: int = 2):
        self.compression_ratio = compression_ratio
        self.min_sentences = min_sentences

    def compress(self, query: str, context: str, agent: str = "") -> tuple[str, CompressionStats]:
        """
        Compress a context string.

        Returns:
            (compressed_text, CompressionStats)
        """
        sentences = _split_sentences(context)
        stats = CompressionStats(
            original_chars=len(context),
            original_sentences=len(sentences),
            agent=agent,
        )

        if len(sentences) <= self.min_sentences:
            stats.compressed_chars = len(context)
            stats.compressed_sentences = len(sentences)
            return context, stats

        query_tokens = _tokenize(query)
        if not query_tokens:
            stats.compressed_chars = len(context)
            stats.compressed_sentences = len(sentences)
            return context, stats

        scores = _tfidf_scores(query_tokens, sentences)
        k = max(self.min_sentences, round(len(sentences) * (1 - self.compression_ratio)))

        # Sort by score descending, take top-k, restore original order
        top_indices = sorted(
            sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        )

        compressed = " ".join(sentences[i] for i in top_indices)
        stats.compressed_chars = len(compressed)
        stats.compressed_sentences = k

        logger.debug("Compressed context: %s", stats)
        return compressed, stats

    def compress_many(self, query: str, documents: list[str], agent: str = "") -> tuple[list[str], list[CompressionStats]]:
        """Compress each document independently and return results + stats."""
        results, all_stats = [], []
        for doc in documents:
            if not doc.strip():
                continue
            compressed, stats = self.compress(query, doc, agent=agent)
            results.append(compressed)
            all_stats.append(stats)
        return results, all_stats
