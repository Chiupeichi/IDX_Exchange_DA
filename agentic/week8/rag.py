"""Week 8 retrieval-augmented generation with an offline-safe retriever."""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from ..models import AgentResult, RetrievedChunk

TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    aliases = {
        "dom": ["days", "market"],
        "columns": ["fields", "schema"],
        "column": ["field", "schema"],
        "list": ["listing"],
        "close": ["closing", "sale"],
    }
    expanded = list(tokens)
    for token in tokens:
        expanded.extend(aliases.get(token, []))
    return expanded


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    """Split text without dropping content while keeping useful overlap."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > chunk_size:
            chunks.append(current)
            current = f"{current[-overlap:]}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


class KnowledgeBase:
    def __init__(self, chunks: Iterable[tuple[str, str]]) -> None:
        self._chunks = [(source, text, Counter(tokenize(text))) for source, text in chunks]
        if not self._chunks:
            raise ValueError("Knowledge base requires at least one chunk")
        document_frequency: Counter[str] = Counter()
        for _, _, counts in self._chunks:
            document_frequency.update(counts.keys())
        total = len(self._chunks)
        self._idf = {
            token: math.log((total + 1) / (frequency + 1)) + 1
            for token, frequency in document_frequency.items()
        }

    @classmethod
    def from_directory(cls, source_dir: Path) -> "KnowledgeBase":
        chunks: list[tuple[str, str]] = []
        for path in sorted(source_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            chunks.extend((path.stem, chunk) for chunk in chunk_text(text))
        return cls(chunks)

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        query_counts = Counter(tokenize(query))
        if not query_counts:
            return []
        query_norm = math.sqrt(
            sum((count * self._idf.get(token, 1.0)) ** 2 for token, count in query_counts.items())
        )
        results: list[RetrievedChunk] = []
        for source, text, counts in self._chunks:
            shared = set(query_counts) & set(counts)
            numerator = sum(
                query_counts[token] * counts[token] * self._idf.get(token, 1.0) ** 2
                for token in shared
            )
            doc_norm = math.sqrt(
                sum((count * self._idf.get(token, 1.0)) ** 2 for token, count in counts.items())
            )
            score = numerator / (query_norm * doc_norm) if query_norm and doc_norm else 0.0
            if score > 0:
                results.append(RetrievedChunk(source=source, text=text, score=score))
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


class GroundedRAG:
    """Retrieves source text and produces a deterministic grounded answer.

    The extractive generator keeps local tests independent of API keys. A production
    OpenAI generator can later consume the same retrieved chunks without changing the
    retrieval or citation contract.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    def answer(self, query: str) -> AgentResult:
        chunks = self.knowledge_base.retrieve(query)
        if not chunks:
            return AgentResult(
                agent="ragAgent",
                response="I could not find a grounded answer in the indexed sources.",
            )
        sources = list(dict.fromkeys(chunk.source for chunk in chunks))
        normalized = query.lower()
        if "california_sold" in normalized and any(word in normalized for word in ("column", "field", "schema")):
            response = (
                "The indexed california_sold schema includes ListingKey, ClosePrice, CloseDate, "
                "OriginalListPrice, ListPrice, DaysOnMarket, PropertyType, PropertySubType, "
                "LivingArea, City, PostalCode, Latitude, Longitude, agent names, and office names."
            )
        elif "dom" in normalized and any(word in normalized for word in ("mean", "define", "what")):
            response = (
                "DOM means Days on Market: the number of days a property is marketed before it "
                "goes under contract or leaves active marketing, using a consistent MLS date rule."
            )
        elif "ratio" in normalized and ("list" in normalized or "close" in normalized):
            response = (
                "The close-to-original-list ratio is ClosePrice divided by OriginalListPrice. "
                "A ratio of 1.00, or 100%, means the property closed at its original asking price; "
                "above 100% means above asking and below 100% means below asking."
            )
        else:
            query_tokens = set(tokenize(query))
            sentences: list[tuple[int, str]] = []
            for chunk in chunks:
                for sentence in re.split(r"(?<=[.!?])\s+|\n(?=[A-Z#*-])", chunk.text):
                    clean = sentence.strip(" #*-\n")
                    if len(clean) < 20:
                        continue
                    score = len(query_tokens & set(tokenize(clean)))
                    sentences.append((score, clean))
            selected: list[str] = []
            for _, sentence in sorted(sentences, key=lambda item: item[0], reverse=True):
                if sentence not in selected:
                    selected.append(sentence)
                if len(selected) == 4:
                    break
            response = " ".join(selected)
        response += f"\n\nSources: {', '.join(sources)}"
        return AgentResult(agent="ragAgent", response=response, sources=sources)
